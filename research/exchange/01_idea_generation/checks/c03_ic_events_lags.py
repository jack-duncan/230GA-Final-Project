"""Fact-check C03: ChatGPT critique #3 and #6.

Claims checked
- "with ~48 months the IC's standard error is roughly 1/sqrt(48) = 0.14 (... ignores overlap), so -0.08 -> +0.13 is
  about one standard error of the difference"
- "Overlapping 3-6-month holds, few independent crossings"; "report the count of independent events"
- "Too few Newey-West lags overstate t"; fix "NW lags >= hold length"
- "4+ variants"
2010-2026 only.
"""
import sys
sys.path.insert(0, "/home/hashim/projects/GA/project/research/lib")
import numpy as np
import pandas as pd
from scipy import stats
from common import load_team, nw_ols
from team_pipeline import run_pipeline

pd.set_option("display.width", 220)
OUT = "/home/hashim/projects/GA/project/research/exchange/01_idea_generation/checks/"
res = run_pipeline(bootstrap_reps=0, extras=False, paired=False, macro_states=False)
ic = res["ic_table"]
print(ic.round(4).to_string(index=False))

# 1. IC difference in standard errors, three ways
rows = []
for sig in ic["signal"].unique():
    v = ic[(ic.signal == sig) & ic.period.str.startswith("Validation")].iloc[0]
    h = ic[(ic.signal == sig) & ic.period.str.startswith("Holdout")].iloc[0]
    d = h.IC - v.IC
    se_naive_h = 1 / np.sqrt(h.n)
    se_naive = np.sqrt(1 / v.n + 1 / h.n)
    se_nw = np.sqrt((v.IC / v.t_hac6) ** 2 + (h.IC / h.t_hac6) ** 2)
    rows.append({"signal": sig, "ic_val": v.IC, "ic_hold": h.IC, "diff": d, "n_val": v.n, "n_hold": h.n,
                 "naive_se_holdout_only": se_naive_h, "diff_in_holdout_se": d / se_naive_h,
                 "naive_se_diff": se_naive, "diff_in_naive_se": d / se_naive,
                 "nw_se_diff": se_nw, "diff_in_nw_se": d / se_nw, "p_two_sided_nw": 2 * (1 - stats.norm.cdf(abs(d / se_nw)))})
icd = pd.DataFrame(rows)
print("\n=== IC change validation -> holdout, in standard errors ===")
print(icd.round(3).to_string(index=False))
print(f"\n1/sqrt(48) = {1/np.sqrt(48):.4f}; ChatGPT's own numbers: 0.21/0.14 = {0.21/0.1443:.2f}")
print("Team IC uses one-month-ahead residuals (forward_series.shift(-1)), so return overlap does not enter the IC.")

# 2. Crossings and independent events
rows = []
for key in ("raw", "pure"):
    cross = res["signals"][f"cross_{key}"]
    for lab, (a, b) in (("2010-2026", ("2010-01-31", "2026-07-31")), ("validation", ("2010-01-31", "2022-07-31")),
                        ("holdout", ("2022-08-31", "2026-07-31")), ("covid 2020-21", ("2020-01-31", "2021-12-31"))):
        c = cross.loc[a:b]
        dates = list(c[c].index)
        merged = []
        for d in dates:  # merge crossings within 6 months of the previous kept event
            if not merged or (d.to_period("M") - merged[-1].to_period("M")).n > 6:
                merged.append(d)
        rows.append({"signal": key, "period": lab, "crossings": len(dates), "events_merged_6m": len(merged),
                     "dates": ",".join(x.strftime("%Y-%m") for x in dates)})
ev = pd.DataFrame(rows)
print("\n=== Crossings (new entries into the p80 state) ===")
print(ev.to_string(index=False))

# 3. NW lag sensitivity of the headline t-stats
ff3 = load_team()["ff3"][["Mkt-RF", "SMB", "HML"]]
rows = []
for n in ["Original | Short Brown hold 3m", "Original | Short Brown hold 6m", "Pure | Short Brown hold 6m"]:
    net = res["strategies"][n]["net_return"]
    for lab, (a, b) in (("validation", ("2010-01-31", "2022-07-31")), ("covid", ("2020-01-31", "2021-12-31")),
                        ("holdout", ("2022-08-31", "2026-07-31"))):
        r = net.loc[a:b]
        row = {"strategy": n, "period": lab, "n": len(r)}
        for L in (0, 3, 6, 12, 18):
            row[f"t_L{L}"] = nw_ols(r, ff3.reindex(r.index), lags=L).tvalues["const"]
        rows.append(row)
lg = pd.DataFrame(rows)
print("\n=== FF3 alpha t by Newey-West lag ===")
print(lg.round(2).to_string(index=False))
print("\nNumber of strategy variants in the team comparison table:", len(res["strategies"]) - 2, "timed +", 2, "benchmarks")

icd.to_csv(OUT + "c03_ic_difference.csv", index=False)
ev.to_csv(OUT + "c03_crossings.csv", index=False)
lg.to_csv(OUT + "c03_nw_lags.csv", index=False)
