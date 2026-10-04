"""Fact-check C01: ChatGPT critique #1 and proposal E.

Claims checked
- "timing beats always-on Short-Brown by roughly 0.3% a year (1.3% vs 1.0%)"
- "Timed returns are tested against zero" (does the team test timed vs always-on anywhere?)
- Fix: alpha of (timed - always-on), or regress hedged Brown on an in-position dummy
- Proposal E pass bar: "Timed - always-on alpha significant after FF5+UMD"
Runs only on 2010-2026 (already seen data). No pre-2010 returns are used.
"""
import sys
sys.path.insert(0, "/home/hashim/projects/GA/project/research/lib")
import numpy as np
import pandas as pd
from common import load_ff5_mom, nw_ols
from team_pipeline import run_pipeline

pd.set_option("display.width", 220)
pd.set_option("display.max_columns", 30)

res = run_pipeline(bootstrap_reps=0)
S = res["strategies"]
ff5 = load_ff5_mom()
ff3cols = ["Mkt-RF", "SMB", "HML"]
ff6cols = ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "UMD"]
AO = "Benchmark | Always-short Brown"
timed = ["Original | Short Brown hold 3m", "Pure | Short Brown hold 3m",
         "Original | Short Brown hold 6m", "Pure | Short Brown hold 6m",
         "Continuous | raw attention", "Continuous | pure attention"]
periods = {"2010-2026": ("2010-01-31", "2026-07-31"), "validation": ("2010-01-31", "2022-07-31"),
           "holdout": ("2022-08-31", "2026-07-31")}

rows = []
for name in timed + [AO]:
    net = S[name]["net_return"]
    pos = S[name]["position"]
    for p, (a, b) in periods.items():
        r = net.loc[a:b].dropna()
        row = {"strategy": name, "period": p, "n": len(r), "ann_net": 12 * r.mean(),
               "ann_vol": np.sqrt(12) * r.std(ddof=1), "sharpe": np.sqrt(12) * r.mean() / r.std(ddof=1),
               "mean_abs_pos": pos.loc[a:b].abs().mean()}
        if name != AO:
            d = (net - S[AO]["net_return"]).loc[a:b].dropna()
            for lab, cols in (("ff3", ff3cols), ("ff6", ff6cols)):
                f = nw_ols(d, ff5[cols].reindex(d.index), lags=6)
                row[f"diff_alpha_{lab}"] = 12 * f.params["const"]
                row[f"diff_t_{lab}"] = f.tvalues["const"]
            f0 = nw_ols(d, None, lags=6)
            row["diff_mean"] = 12 * d.mean()
            row["diff_t_mean"] = f0.tvalues["const"]
        rows.append(row)
tab = pd.DataFrame(rows)
print("=== Timed vs always-short Brown (net of team costs) ===")
print(tab.round(4).to_string(index=False))

# In-position dummy regression: short-Brown hedged return (per unit position) on a dummy for "in timed state at t-1".
hedged = res["models"]["Brown leg"]["hedged"]         # Brown excess - lagged beta'F (includes Brown's alpha)
short_hedged = -hedged
rows = []
for key, lab in (("raw", "Original"), ("pure", "Pure")):
    for h in (3, 6):
        state = res["signals"][f"hold_{key}"][h].astype(float)
        dummy = state.shift(1).reindex(short_hedged.index)          # position set at t-1 earns return at t
        for p, (a, b) in list(periods.items()) + [("2010-2026 ex Mar2020-Dec2021", ("2010-01-31", "2026-07-31"))]:
            y = short_hedged.loc[a:b]
            X = dummy.loc[a:b].to_frame("in_state")
            if "ex" in p:
                keep = ~((y.index >= "2020-03-31") & (y.index <= "2021-12-31"))
                y, X = y[keep], X[keep]
            for lags in (6, h + 6):
                f = nw_ols(y, X, lags=lags)
                rows.append({"signal": f"{lab} {h}m", "period": p, "nw_lags": lags, "n": int(f.nobs),
                             "months_in_state": int(X["in_state"].sum()),
                             "ann_short_hedged_out": 12 * f.params["const"],
                             "ann_in_minus_out": 12 * f.params["in_state"], "t_in_minus_out": f.tvalues["in_state"]})
dt = pd.DataFrame(rows)
print("\n=== Short-Brown hedged return on in-state dummy (unit position, no vol scaling, gross) ===")
print(dt.round(4).to_string(index=False))

# Does the team compare timed vs always-on anywhere? Paired table pairs:
print("\n=== Team paired bootstrap pairs ===")
print(res["paired_table"][["new", "benchmark"]].to_string(index=False))

out = "/home/hashim/projects/GA/project/research/exchange/01_idea_generation/checks/"
tab.to_csv(out + "c01_timed_vs_always_on.csv", index=False)
dt.to_csv(out + "c01_in_state_dummy.csv", index=False)
