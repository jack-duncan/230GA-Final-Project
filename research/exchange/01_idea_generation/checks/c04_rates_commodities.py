"""Fact-check C04: ChatGPT critique #5 and proposals B / E.

Claims checked
- "Util, BldMt and Steel are rate- and commodity-sensitive."
- "A 2022-2026 holdout dominated by rates can lose money through unhedged duration, not climate."
- Fix: attribute ex post against FF5 + UMD + a rate factor (d10y) + a commodity return.
- B: "Alpha t falls below ~1.5 with a commodity factor"
Industry sensitivities use 1992-2026 (IMF commodity index starts 1992) and 2010-2026; strategy attribution 2010-2026.
"""
import sys
sys.path.insert(0, "/home/hashim/projects/GA/project/research/lib")
import numpy as np
import pandas as pd
from common import load_team, load_ff5_mom, load_fred, nw_ols
from team_pipeline import run_pipeline, TEAM_BROWN, TEAM_GREEN

pd.set_option("display.width", 220)
pd.set_option("display.max_columns", 30)
OUT = "/home/hashim/projects/GA/project/research/exchange/01_idea_generation/checks/"
T = load_team()
ind, ff3 = T["industries"], T["ff3"]
ff6 = load_ff5_mom()
d10 = load_fred("GS10").diff().rename("d10y")                         # pp change in 10y yield
com = load_fred("PALLFNFINDEXM").pct_change().rename("COM")           # IMF all-commodity index return
oil = load_fred("MCOILWTICO").pct_change().rename("OIL")
X = ff6.join(d10).join(com).join(oil)

# 1. Industry sensitivities: excess return on Mkt-RF + d10y + COM (and + OIL instead of COM)
rows = []
for i in TEAM_BROWN + TEAM_GREEN + ["Oil", "Coal"]:
    y = (ind[i] - ff3["RF"]).rename(i)
    for lab, (a, b) in (("1992-2026", ("1992-02-29", "2026-07-31")), ("2010-2026", ("2010-01-31", "2026-07-31"))):
        yy = y.loc[a:b]
        f = nw_ols(yy, X[["Mkt-RF", "d10y", "COM"]].reindex(yy.index), lags=6)
        rows.append({"industry": i, "sample": lab, "b_mkt": f.params["Mkt-RF"], "b_d10y": f.params["d10y"],
                     "t_d10y": f.tvalues["d10y"], "b_com": f.params["COM"], "t_com": f.tvalues["COM"], "n": int(f.nobs)})
sens = pd.DataFrame(rows)
print("=== Industry excess return on Mkt-RF + d10y (pp) + commodity return, NW6 ===")
print(sens.round(3).to_string(index=False))

# 2. Residual rate/commodity exposure of the FF3-hedged Brown leg (what the strategy actually trades)
res = run_pipeline(bootstrap_reps=0, extras=False, paired=False, macro_states=False)
bh = res["models"]["Brown leg"]["hedged"]
rows = []
for lab, (a, b) in (("validation", ("2010-01-31", "2022-07-31")), ("holdout", ("2022-08-31", "2026-07-31")),
                    ("2010-2026", ("2010-01-31", "2026-07-31"))):
    yy = bh.loc[a:b]
    f = nw_ols(yy, X[["d10y", "COM"]].reindex(yy.index), lags=6)
    rows.append({"series": "Brown leg FF3-hedged", "period": lab, "b_d10y": f.params["d10y"], "t_d10y": f.tvalues["d10y"],
                 "b_com": f.params["COM"], "t_com": f.tvalues["COM"], "sum_d10y_pp": X["d10y"].loc[a:b].sum(),
                 "ann_com": 12 * X["COM"].loc[a:b].mean()})
bres = pd.DataFrame(rows)
print("\n=== FF3-hedged Brown leg on d10y and commodity return ===")
print(bres.round(4).to_string(index=False))

# 3. Ex-post attribution of the strategies: FF3 vs FF5+UMD vs FF5+UMD+d10y+COM
specs = {"FF3": ["Mkt-RF", "SMB", "HML"], "FF6": ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "UMD"],
         "FF6+d10y+COM": ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "UMD", "d10y", "COM"]}
rows = []
for n in ["Original | Short Brown hold 3m", "Pure | Short Brown hold 3m", "Original | Short Brown hold 6m",
          "Pure | Short Brown hold 6m", "Continuous | raw attention", "Benchmark | Always-short Brown"]:
    net = res["strategies"][n]["net_return"]
    for lab, (a, b) in (("validation", ("2010-01-31", "2022-07-31")), ("holdout", ("2022-08-31", "2026-07-31")),
                        ("2010-2026", ("2010-01-31", "2026-07-31"))):
        r = net.loc[a:b]
        row = {"strategy": n, "period": lab}
        for sname, cols in specs.items():
            f = nw_ols(r, X[cols].reindex(r.index), lags=6)
            row[f"alpha_{sname}"] = 12 * f.params["const"]
            row[f"t_{sname}"] = f.tvalues["const"]
            if sname == "FF6+d10y+COM":
                row["b_d10y"], row["t_b_d10y"] = f.params["d10y"], f.tvalues["d10y"]
                row["b_com"], row["t_b_com"] = f.params["COM"], f.tvalues["COM"]
                row["t_HML"], row["t_RMW"], row["t_CMA"], row["t_UMD"] = (f.tvalues[c] for c in ("HML", "RMW", "CMA", "UMD"))
        rows.append(row)
att = pd.DataFrame(rows)
print("\n=== Ex-post attribution of net strategy returns (annualized alpha, NW6 t) ===")
print(att.round(3).to_string(index=False))

sens.to_csv(OUT + "c04_industry_rate_commodity.csv", index=False)
bres.to_csv(OUT + "c04_brown_hedged_rate_commodity.csv", index=False)
att.to_csv(OUT + "c04_attribution.csv", index=False)
