"""V5: Ferson-Schadt conditional-beta model and the joint test that all 20 beta-instrument interactions are zero.
Instruments rebuilt from raw FRED files; own expanding standardization; own HAC Wald; own fixed-design block bootstrap
(the M3 scheme) AND a wild block bootstrap (Rademacher per block of 12) that keeps heteroskedasticity tied to X."""
import numpy as np
import pandas as pd
from scipy import stats
from vlib import (build_bond_independent, factor_panel, pipelines, load_team, load_fred, OUT, END, POST10, HOLD, COVID, STRATS, BENCH, SH,
                  FF3UB)
from team_pipeline import TEAM_GREEN, TEAM_BROWN

T = load_team(); rf = T["ff3"]["RF"]
F = factor_panel(build_bond_independent(rf)["BOND"])
team, corr = pipelines()
ind = T["industries"]
GB = ind[TEAM_GREEN].mean(axis=1) - ind[TEAM_BROWN].mean(axis=1)

# ---- instruments, information date t (known at end of t)
gs10, tb3, baa, aaa = (load_fred(s) for s in ("GS10", "TB3MS", "BAA", "AAA"))
cpi = load_fred("CPIAUCSL").interpolate(limit_area="inside"); cfnai = load_fred("CFNAI")
z = pd.DataFrame({"TERM": gs10 - tb3, "CREDIT": baa - aaa, "Y10": gs10,
                  "INFL": 100 * (np.log(cpi.shift(1)) - np.log(cpi.shift(13))), "CFNAI": cfnai.shift(1)})
Zl = z.shift(1)                                              # z_{t-1} on the row of return month t
Zs = (Zl - Zl.expanding(24).mean()) / Zl.expanding(24).std()  # past-only moments (row t uses z_{..t-1})
# look-ahead check on the standardization: perturb instruments after 2015-06; rows <= 2015-07 must not change
Zp = Zl.copy(); Zp.loc["2015-07-31":] += 5.0
Zps = (Zp - Zp.expanding(24).mean()) / Zp.expanding(24).std()
print("instrument standardization look-ahead: max change rows <= 2015-06:", float((Zps - Zs).loc[:"2015-06-30"].abs().max().max()))
pub = pd.read_csv("/home/hashim/projects/GA/project/research/outputs/tables/M3_alpha_beta_instruments_lagged.csv", index_col=0, parse_dates=True)
pz = pub[[c for c in pub.columns if c.endswith("_lag1_expstd")]]; pz.columns = [c.replace("_lag1_expstd", "") for c in pz.columns]
print("max |my standardized z - M3 published| 1970-2026:", float((Zs[pz.columns] - pz).loc["1970":END].abs().max().max()))
COND = ["Mkt-RF", "HML", "UMD", "BOND"]


def hac_V(X, u, XXi, L=6):
    g = X * u[:, None]; S = g.T @ g
    for l in range(1, L + 1):
        G = g[l:].T @ g[:-l]; S += (1 - l / (L + 1)) * (G + G.T)
    return XXi @ S @ XXi


def fs(y, a, e, reps=999, seed=7, dummies=None):
    d = pd.concat([y.rename("y"), F[FF3UB], Zs], axis=1, sort=True).loc[a:e].dropna()
    base = d[FF3UB].copy()
    inter = pd.DataFrame({f"{k}x{j}": d[k] * d[j] for k in COND for j in Zs.columns}, index=d.index)
    X = pd.concat([base, inter], axis=1)
    if dummies is not None:
        X = pd.concat([X, dummies.reindex(d.index)], axis=1)
    Xu = np.column_stack([np.ones(len(d)), X.to_numpy()])
    Xr = np.column_stack([np.ones(len(d)), X.drop(columns=inter.columns).to_numpy()])
    Y = d["y"].to_numpy(); n = len(Y)
    XXi = np.linalg.inv(Xu.T @ Xu); XXr = np.linalg.inv(Xr.T @ Xr)
    idx = np.arange(1 + base.shape[1], 1 + base.shape[1] + inter.shape[1])

    def W(yv):
        b = XXi @ Xu.T @ yv; u = yv - Xu @ b; V = hac_V(Xu, u, XXi)
        return float(b[idx] @ np.linalg.solve(V[np.ix_(idx, idx)], b[idx])), b, V, u
    W0, b, V, u = W(Y)
    br = XXr @ Xr.T @ Y; ur = Y - Xr @ br; fr = Xr @ br
    rng = np.random.default_rng(seed)
    nb = -(-n // 12)
    d_fixed, d_wild = np.empty(reps), np.empty(reps)
    for i in range(reps):
        s = rng.integers(0, n, nb); ix = ((s[:, None] + np.arange(12)).reshape(-1)[:n]) % n
        d_fixed[i] = W(fr + ur[ix])[0]
        eta = np.repeat(rng.choice([-1.0, 1.0], nb), 12)[:n]
        d_wild[i] = W(fr + ur * eta)[0]
    q = len(idx); k = Xu.shape[1]
    ssr_u, ssr_r = (u ** 2).sum(), (ur ** 2).sum()
    Fc = ((ssr_r - ssr_u) / q) / (ssr_u / (n - k))
    se = np.sqrt(np.diag(V))
    out = {"n": n, "W": W0, "p_chi2": stats.chi2.sf(W0, q), "p_boot_fixed": (1 + (d_fixed >= W0).sum()) / (1 + reps),
           "q95_fixed": np.quantile(d_fixed, .95) if reps else np.nan, "p_boot_wild": (1 + (d_wild >= W0).sum()) / (1 + reps),
           "q95_wild": np.quantile(d_wild, .95) if reps else np.nan, "p_olsF": stats.f.sf(Fc, q, n - k),
           "alpha_cond": 12 * b[0], "t_alpha_cond": b[0] / se[0], "p_alpha_cond": 2 * stats.t.sf(abs(b[0] / se[0]), n - k)}
    if dummies is not None:
        cols = ["const"] + list(X.columns)
        for dn in dummies.columns:
            j = cols.index(dn); w = np.zeros(k); w[0] = 1; w[j] = 1
            est = w @ b; sev = np.sqrt(w @ V @ w)
            out[f"alpha_{dn}"] = 12 * est; out[f"p_{dn}"] = 2 * stats.t.sf(abs(est / sev), n - k)
    return out


if __name__ == "__main__":
    rows = []
    targets = [("GB", "legs", GB, ("1970-01-31", END)), ("GB", "legs", GB, POST10)]
    for s in STRATS:
        targets.append((SH[s], "corrected", corr["strategies"][s]["net_return"], POST10))
    for nm, bl, y, (a, e) in targets:
        rows.append({"asset": nm, "baseline": bl, "start": a, **fs(y, a, e)})
    # holdout / covid intercept dummies, post-2010 model (claims: team Orig 3m -4.4% p .013; team Pure 3m -2.8% p .039;
    # corrected -1.4%..+0.1% p>=.27; COVID Pure 6m 7.2% p .002 (baseline?), benchmark 6.1% p .026)
    dum = pd.DataFrame(index=F.index)
    dum["D_covid"] = ((F.index >= COVID[0]) & (F.index <= COVID[1])).astype(float)
    dum["D_holdout"] = (F.index >= HOLD[0]).astype(float)
    for bl, res in (("team", team), ("corrected", corr)):
        for s in STRATS + [BENCH]:
            o = fs(res["strategies"][s]["net_return"], *POST10, reps=0, dummies=dum)
            rows.append({"asset": SH[s], "baseline": bl, "start": "dummies", **{k: v for k, v in o.items() if k.startswith(("alpha_D", "p_D", "n"))}})
    R = pd.DataFrame(rows)
    pd.set_option("display.width", 260)
    print(R.round(4).to_string())
    print("chi2(20) 95% critical value:", stats.chi2.ppf(.95, 20))
    R.to_csv(OUT / "v5_ferson_schadt.csv", index=False)
