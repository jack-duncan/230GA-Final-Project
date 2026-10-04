"""V2: primary (i) GB BOND loading in FF5+UMD+BOND (full 1970-2026, post-2010), leg split, rolling 60m BOND beta,
BOND_eom robustness. GB built from the team FF49 file directly (not from any M3 table)."""
import numpy as np
import pandas as pd
from vlib import (build_bond_independent, factor_panel, nw, holm, load_team, OUT, END, POST10, FF5UB, FF3UB, FF3)
from team_pipeline import TEAM_GREEN, TEAM_BROWN

T = load_team()
ind, rf = T["industries"], T["ff3"]["RF"]
g, br = ind[TEAM_GREEN].mean(axis=1), ind[TEAM_BROWN].mean(axis=1)
GB = g - br
bond = build_bond_independent(rf)["BOND"]
F = factor_panel(bond)
rows = []
for per, (a, e) in {"full_1970": ("1970-01-31", END), "post2010": POST10}.items():
    for nm, y in {"GB": GB, "Green": g - rf, "Brown": br - rf}.items():
        f = nw(y.loc[a:e], F[FF5UB])
        rows.append({"asset": nm, "period": per, "n": f["n"], "b_BOND": f["b"]["BOND"], "t_BOND": f["t"]["BOND"],
                     "p_t(n-k)": f["p"]["BOND"], "alpha_ann": 12 * f["b"]["const"], "t_alpha": f["t"]["const"],
                     "b_HML": f["b"]["HML_k"], "b_RMW": f["b"]["RMW_k"], "b_CMA": f["b"]["CMA_k"]})
R = pd.DataFrame(rows)
m = R.asset == "GB"
R.loc[m, "holm"] = holm(R.loc[m, "p_t(n-k)"])
print(R.round(4).to_string())

# FF3 HML of GB (claim -0.233 t -4.63 full; -0.298 t -5.74 post-2010)
for per, (a, e) in {"full": ("1970-01-31", END), "post2010": POST10}.items():
    f = nw(GB.loc[a:e], F[FF3])
    print(f"GB FF3 HML {per}: {f['b']['HML']:.3f} (t {f['t']['HML']:.2f}); FF3 alpha {12*f['b']['const']:.4f} (t {f['t']['const']:.2f})")

# rolling 60m BOND beta, FF3+UMD+BOND, window ending t (claim means 0.134 / -0.203 / +0.380; min -0.60 at 2020-01; max 0.65 at 2022-05)
d = pd.concat([GB.rename("y"), F[FF3UB]], axis=1).loc["1965":END].dropna()
bb = pd.Series(np.nan, index=d.index)
for j in range(59, len(d)):
    w = d.iloc[j - 59:j + 1]
    Z = np.column_stack([np.ones(60), w[FF3UB].to_numpy()])
    bb.iloc[j] = np.linalg.lstsq(Z, w["y"].to_numpy(), rcond=None)[0][-1]
bb = bb.dropna()
for lab, sl in (("1970-2009", slice("1970", "2009")), ("2010-2021", slice("2010", "2021")), ("2022-2026", slice("2022", END))):
    x = bb.loc[sl]
    print(f"rolling60 BOND beta windows ending {lab}: mean {x.mean():.3f}, min {x.min():.2f} ({x.idxmin():%Y-%m}), max {x.max():.2f} ({x.idxmax():%Y-%m})")

# BOND_eom robustness over 1990-2026 (claim 0.082 t 1.19 vs GS10 BOND 0.129 t 1.65 same months)
be = build_bond_independent(rf, "eom")["BOND"]
Fe = F.copy(); Fe["BOND"] = be.reindex(Fe.index)
e0 = be.first_valid_index()
f1 = nw(GB.loc[e0:END], Fe[FF5UB]); f2 = nw(GB.loc[e0:END], F[FF5UB])
print(f"GB 1990-2026 FF5+UMD+BOND_eom: {f1['b']['BOND']:.3f} (t {f1['t']['BOND']:.2f}); GS10 BOND same months {f2['b']['BOND']:.3f} (t {f2['t']['BOND']:.2f}); n {f1['n']}")
# sub-period 1970-1989 to see where the full-sample loading comes from
f3 = nw(GB.loc["1970-01-31":"1989-12-31"], F[FF5UB]); f4 = nw(GB.loc["1970-01-31":"2009-12-31"], F[FF5UB])
print(f"GB 1970-1989 BOND {f3['b']['BOND']:.3f} (t {f3['t']['BOND']:.2f}); 1970-2009 {f4['b']['BOND']:.3f} (t {f4['t']['BOND']:.2f})")
# lag sensitivity for the primary t
for L in (3, 6, 12, 18):
    f = nw(GB.loc["1970-01-31":END], F[FF5UB], lags=L)
    print(f"full-sample GB BOND t with NW({L}): {f['t']['BOND']:.2f}")

pub = pd.read_csv("/home/hashim/projects/GA/project/research/outputs/tables/M3_alpha_beta_primary_i.csv")
print(pub[["period", "n", "b_BOND", "t_BOND", "p_BOND", "holm_p_BOND"]].to_string())
R.to_csv(OUT / "v2_gb_bond.csv", index=False)
