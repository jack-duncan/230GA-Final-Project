"""V10 (round 2): independent re-derivation of every number that the round-1 fixes introduced or changed.
Own code only (vlib); M3 tables are read for comparison, never imported.

Covers: Fix 1 (GB short-window alphas under NW(6)/NW(2)/OLS; GB alpha in all long windows), Fix 2 (COVID factor means
and per-factor contributions under three methods), Fix 3 (holdout BOND contribution b x mean(f)), Fix 6 (labels),
zero-position month count, D (strategy - pi x benchmark) mean tests, holdout ranges quoted in 4(ii)."""
import numpy as np
import pandas as pd
from scipy import stats
from vlib import (build_bond_independent, factor_panel, pipelines, load_team, nw, m3_table, OUT, END, HOLD, COVID, POST10,
                  STRATS, BENCH, SH, FF3, FF3UB, FF5UB)
from team_pipeline import TEAM_GREEN, TEAM_BROWN

pd.set_option("display.width", 260); pd.set_option("display.max_columns", 40)
T = load_team(); rf = T["ff3"]["RF"]
F = factor_panel(build_bond_independent(rf)["BOND"])
team, corr = pipelines()
ind = T["industries"]
GB = ind[TEAM_GREEN].mean(axis=1) - ind[TEAM_BROWN].mean(axis=1)
MODELS = {"CAPM": ["Mkt-RF"], "FF3": FF3, "FF3+BOND": FF3 + ["BOND"], "FF3+UMD+BOND": FF3UB,
          "FF5": FF5UB[:5], "FF5+UMD": FF5UB[:6], "FF5+UMD+BOND": FF5UB}
PER = {"full": ("1970-01-31", END), "post2010": POST10, "validation": ("2010-01-31", "2022-07-31"), "holdout": HOLD,
       "covid": COVID, "inflation_rates": ("2022-01-31", "2024-12-31"), "last18": ("2025-02-28", END), "last12": ("2025-08-31", END)}


def ols_classical(y, X):
    d = pd.concat([y.rename("_y"), X], axis=1, sort=True).dropna()
    Z = np.column_stack([np.ones(len(d)), d[X.columns].to_numpy(float)]); Y = d["_y"].to_numpy(float)
    n, k = Z.shape; b = np.linalg.lstsq(Z, Y, rcond=None)[0]; e = Y - Z @ b
    V = (e @ e / (n - k)) * np.linalg.inv(Z.T @ Z); t = b[0] / np.sqrt(V[0, 0])
    return t, 2 * stats.t.sf(abs(t), n - k)


print("=" * 30, "FIX 1: GB short windows")
rows = []
for per in ("last18", "last12"):
    a, e = PER[per]
    y = GB.loc[a:e]
    m6, m2 = nw(y, None, 6), nw(y, None, 2)
    tc = m6["b"]["const"] / (y.std(ddof=1) / np.sqrt(len(y)))
    rows.append({"period": per, "model": "mean", "n": len(y), "df": len(y) - 1, "alpha": 12 * y.mean(), "t6": m6["t"]["const"], "p6": m6["p"]["const"],
                 "t2": m2["t"]["const"], "p2": m2["p"]["const"], "t_ols": tc, "p_ols": 2 * stats.t.sf(abs(tc), len(y) - 1)})
    for m, cols in MODELS.items():
        f6, f2 = nw(y, F[cols], 6), nw(y, F[cols], 2); to, po = ols_classical(y, F[cols])
        rows.append({"period": per, "model": m, "n": f6["n"], "df": f6["n"] - f6["k"], "alpha": 12 * f6["b"]["const"], "t6": f6["t"]["const"],
                     "p6": f6["p"]["const"], "t2": f2["t"]["const"], "p2": f2["p"]["const"], "t_ols": to, "p_ols": po})
S = pd.DataFrame(rows); print(S.round(4).to_string())
Sm = S[S.model != "mean"]
print(f"models p<.05: NW6 {int((Sm.p6 < .05).sum())}/14, NW2 {int((Sm.p2 < .05).sum())}/14, OLS {int((Sm.p_ols < .05).sum())}/14; "
      f"OLS |t| {Sm.t_ols.abs().min():.2f}..{Sm.t_ols.abs().max():.2f}, p {Sm.p_ols.min():.3f}..{Sm.p_ols.max():.3f}; df {Sm.df.min()}..{Sm.df.max()}")
pub = m3_table("gb_short_window_alpha")
mm = pub.merge(S.replace({"model": {"mean": "mean (no factors)"}}), on=["period", "model"])
print("max |diff| vs M3 gb_short_window_alpha: alpha", float((mm.alpha_ann - mm.alpha).abs().max()), "t_nw6", float((mm.t_nw6 - mm.t6).abs().max()),
      "t_nw2", float((mm.t_nw2 - mm.t2).abs().max()), "t_ols", float((mm.t_ols_x - mm.t_ols_y).abs().max()) if "t_ols_x" in mm else "n/a")
S.to_csv(OUT / "v10_gb_short_window.csv", index=False)

# GB in every longer window, 7 models
g = []
for per in ("full", "post2010", "validation", "holdout", "covid", "inflation_rates"):
    a, e = PER[per]
    for m, cols in MODELS.items():
        f = nw(GB.loc[a:e], F[cols]); g.append({"period": per, "model": m, "n": f["n"], "alpha": 12 * f["b"]["const"], "t": f["t"]["const"], "p": f["p"]["const"]})
G = pd.DataFrame(g)
print(G.groupby("period").agg(n=("n", "first"), a_min=("alpha", "min"), a_max=("alpha", "max"), t_min=("t", "min"), t_max=("t", "max"), p_min=("p", "min")).round(4))
print("GB full CAPM:", G[(G.period == "full") & (G.model == "CAPM")].round(4).to_dict("records"))
print("GB post2010 FF3+BOND:", G[(G.period == "post2010") & (G.model == "FF3+BOND")].round(4).to_dict("records"))
for per, (a, e) in (("full", PER["full"]), ("post2010", POST10)):
    print(f"GB raw mean {per}: {12*GB.loc[a:e].mean():.4f}")

print("=" * 30, "FIX 6c: GB FF5 loadings, full")
for m in ("FF5", "FF5+UMD", "FF5+UMD+BOND"):
    f = nw(GB.loc[PER["full"][0]:END], F[MODELS[m]])
    print(m, {c: (round(f["b"][c], 3), round(f["t"][c], 2)) for c in ("HML_k", "RMW_k", "CMA_k")})

print("=" * 30, "FIX 2: COVID factor means and contributions (corrected Pure 6m)")
print("factor means %/yr COVID:", (1200 * F[FF3UB].loc[COVID[0]:COVID[1]].mean()).round(3).to_dict())
fmp = m3_table("factor_means"); print(fmp[fmp.period == "covid"].to_string())
y = corr["strategies"]["Pure | Short Brown hold 6m"]["net_return"].loc[COVID[0]:COVID[1]]
for nm, cols in (("FF3+UMD+BOND", FF3UB), ("FF5+UMD+BOND", FF5UB)):
    f = nw(y, F[cols]); fm = F[cols].loc[COVID[0]:COVID[1]].mean()
    print(nm, "alpha", round(1200 * f["b"]["const"], 2), "t", round(f["t"]["const"], 2),
          {c: (round(f["b"][c], 2), round(f["t"][c], 2), round(1200 * f["b"][c] * fm[c], 2)) for c in cols})
# gross version of the in-period regression (attribution splits the gross return; residual reported net?)
yg = corr["strategies"]["Pure | Short Brown hold 6m"]["gross_return"].loc[COVID[0]:COVID[1]]
f = nw(yg, F[FF3UB]); print("gross FF3+UMD+BOND COVID alpha", round(1200 * f["b"]["const"], 2), "t", round(f["t"]["const"], 2))

print("=" * 30, "FIX 3: holdout BOND and UMD contributions, FF3+UMD+BOND")
c = []
fm = F[FF3UB].loc[HOLD[0]:HOLD[1]].mean()
for bl, res in (("team", team), ("corrected", corr)):
    for s in STRATS:
        yy = res["strategies"][s]["net_return"].loc[HOLD[0]:HOLD[1]]
        f3, f5 = nw(yy, F[FF3]), nw(yy, F[FF3UB])
        c.append({"baseline": bl, "s": SH[s], "net": 1200 * yy.mean(), "a3": 1200 * f3["b"]["const"], "a5": 1200 * f5["b"]["const"],
                  "drop": 1200 * (f3["b"]["const"] - f5["b"]["const"]), "bBOND": f5["b"]["BOND"], "tBOND": f5["t"]["BOND"],
                  "cBOND": 1200 * f5["b"]["BOND"] * fm["BOND"], "cUMD": 1200 * f5["b"]["UMD"] * fm["UMD"]})
C = pd.DataFrame(c); print(C.round(3).to_string())
pha = m3_table("holdout_alpha")
mc = pha.merge(C, left_on=["baseline", "short"], right_on=["baseline", "s"])
print("max |contrib_BOND diff| (pp):", float((100 * mc["contrib_BOND_FF3+UMD+BOND"] - mc["cBOND"]).abs().max()))
print("BOND mean holdout %/yr:", round(1200 * fm["BOND"], 3), "UMD:", round(1200 * fm["UMD"], 3))

print("=" * 30, "zero-position months post-2010 (3m holds)")
for bl, res in (("team", team), ("corrected", corr)):
    for s in STRATS[:4]:
        p = res["strategies"][s]["position"]
        z_lag = int((p.shift(1).loc[POST10[0]:END] == 0).sum()); z_now = int((p.loc[POST10[0]:END] == 0).sum())
        print(f"{bl:9s} {SH[s]:8s} zero months: h_(t-1) {z_lag}, h_t {z_now}")
    nr = res["strategies"]["Pure | Short Brown hold 3m"]["net_return"].dropna()
    pos = res["strategies"]["Pure | Short Brown hold 3m"]["position"]
    print(bl, "first net return:", nr.index[0].date(), "first nonzero Pure position:", pos[pos != 0].index[0].date(),
          "n 1999-03..2026-07:", len(nr.loc["1999-03-31":END]))

print("=" * 30, "D = strategy - pi x benchmark: mean tests")
pv = m3_table("position_overlap")
dr = []
for s in STRATS:
    st = corr["strategies"][s]; bm = corr["strategies"][BENCH]
    h = st["position"].shift(1).loc[POST10[0]:END]; hb = bm["position"].shift(1).loc[POST10[0]:END]
    pi = h.abs().mean() / hb.abs().mean()
    D = st["net_return"] - pi * bm["net_return"]
    for per, (a, e) in (("post2010", POST10), ("covid", COVID), ("holdout", HOLD)):
        f = nw(D.loc[a:e]); dr.append({"s": SH[s], "pi": pi, "period": per, "D": 1200 * f["b"]["const"], "t": f["t"]["const"], "p": f["p"]["const"]})
Dt = pd.DataFrame(dr); print(Dt.round(3).to_string())
Dt.to_csv(OUT / "v10_D_means.csv", index=False)
C.to_csv(OUT / "v10_holdout_contrib.csv", index=False)
