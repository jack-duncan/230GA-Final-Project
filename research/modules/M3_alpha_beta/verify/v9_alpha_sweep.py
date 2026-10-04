"""V9: 'no alpha anywhere' sweep (GB in 7 models x 8 periods; strategies post-2010 and validation, both baselines),
plus the BOND_eom and centered-window variants of the Lewellen-Nagel timing term."""
import numpy as np
import pandas as pd
from vlib import (build_bond_independent, factor_panel, pipelines, load_team, nw, roll_backward, ln_terms, boot_timing, OUT, END,
                  POST10, STRATS, SH, FF3, FF3UB, FF5UB)
from team_pipeline import TEAM_GREEN, TEAM_BROWN

T = load_team(); rf = T["ff3"]["RF"]
F = factor_panel(build_bond_independent(rf)["BOND"])
team, corr = pipelines()
ind = T["industries"]
GB = ind[TEAM_GREEN].mean(axis=1) - ind[TEAM_BROWN].mean(axis=1)
MODELS = {"CAPM": ["Mkt-RF"], "FF3": FF3, "FF3+BOND": FF3 + ["BOND"], "FF3+UMD+BOND": FF3UB,
          "FF5": FF5UB[:5], "FF5+UMD": FF5UB[:6], "FF5+UMD+BOND": FF5UB}
PER = {"full": ("1970-01-31", END), "post2010": POST10, "validation": ("2010-01-31", "2022-07-31"), "holdout": ("2022-08-31", END),
       "covid": ("2020-01-31", "2021-12-31"), "inflation_rates": ("2022-01-31", "2024-12-31"), "last18": ("2025-02-28", END),
       "last12": ("2025-08-31", END)}
rows = []
for per, (a, e) in PER.items():
    for m, cols in MODELS.items():
        f = nw(GB.loc[a:e], F[cols])
        rows.append({"period": per, "model": m, "n": f["n"], "df": f["n"] - f["k"], "alpha": 12 * f["b"]["const"], "t": f["t"]["const"], "p": f["p"]["const"]})
G = pd.DataFrame(rows)
print("GB: min p over all periods/models:", G.p.min().round(3), G.loc[G.p.idxmin()].to_dict())
print(G[G.period.isin(["full", "post2010", "holdout"])].round(3).to_string())

srows = []
for bl, res in (("team", team), ("corrected", corr)):
    for s in STRATS:
        y = res["strategies"][s]["net_return"]
        for per in ("post2010", "validation"):
            a, e = PER[per]
            for m in ("FF3", "FF3+UMD+BOND", "FF5+UMD+BOND"):
                f = nw(y.loc[a:e], F[MODELS[m]])
                srows.append({"baseline": bl, "s": SH[s], "period": per, "model": m, "alpha": 12 * f["b"]["const"], "t": f["t"]["const"]})
S = pd.DataFrame(srows)
for per in ("post2010", "validation"):
    x = S[S.period == per]
    print(f"strategies {per}: alpha {x.alpha.min():.4f}..{x.alpha.max():.4f}, t {x.t.min():.2f}..{x.t.max():.2f}; rows with t>2: "
          f"{x[x.t > 2][['baseline', 's', 'model', 'alpha', 't']].round(3).values.tolist()}")

# BOND_eom and centered-window LN timing terms for the corrected strategies
be = build_bond_independent(rf, "eom")["BOND"]
Fe = F[FF3UB].copy(); Fe["BOND"] = be.reindex(Fe.index)
for s in STRATS:
    y = corr["strategies"][s]["net_return"]
    B = roll_backward(y, Fe, 36); d = ln_terms(y, B, Fe, *POST10); bt = boot_timing(d["_R"], d["_B"], d["_F"], reps=5000)
    print(f"{SH[s]:9s} BOND_eom backward-36 timing {100*d['timing']:.2f}% p {bt['p']:.3f}")
