"""M7 adversarial verification, part 2: search families, deflated appraisal ratio (own implementation), holdout,
cost stress, frozen-run statistics from the saved returns.

Member series are regenerated with the modules' library calls (m5lib, team_pipeline, M1b helpers) as M5 / M1b build
them; every statistic is computed with code written here: numpy OLS with a hand-rolled Newey-West (Bartlett, 6 lags,
no small-sample scaling), Nyholt / Li-Ji from residual eigenvalues, the Bailey and Lopez de Prado (2014) expected
maximum and deflated Sharpe ratio, a separate stationary bootstrap (two draw orders) for Romano-Wolf and SPA.
Writes only to verify/out/.

Run: cd /home/hashim/projects/GA/project/research && uv run python modules/M7_robustness_ledger/verify/v2_search_dsr.py
"""
import pathlib
import sys
import warnings

import numpy as np
import pandas as pd
from scipy import stats
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import squareform

warnings.filterwarnings("ignore")
ROOT = pathlib.Path(__file__).resolve().parents[3]
T = ROOT / "outputs" / "tables"
OUT = pathlib.Path(__file__).resolve().parent / "out"
OUT.mkdir(exist_ok=True)
sys.path.insert(0, str(ROOT / "lib"))
sys.path.insert(0, str(ROOT / "modules" / "M5_industry_momentum"))
sys.path.insert(0, str(ROOT / "modules" / "M1b_alt_signals"))
import common as C  # noqa: E402
import m5lib as L5  # noqa: E402

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 40)
C6 = ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "UMD"]
EULER = 0.5772156649015329


# ------------------------------------------------------------------ own estimators
def ols_nw(y, X, L=6):
    """OLS with constant; NW (Bartlett, L lags, no df scaling) and classic OLS SEs. Returns dict."""
    y = np.asarray(y, float); X = np.column_stack([np.ones(len(y)), np.asarray(X, float)])
    n, k = X.shape
    XtXi = np.linalg.inv(X.T @ X)
    b = XtXi @ X.T @ y
    e = y - X @ b
    u = X * e[:, None]
    S = u.T @ u
    for l in range(1, L + 1):
        G = u[l:].T @ u[:-l]
        S += (1 - l / (L + 1)) * (G + G.T)
    V = XtXi @ S @ XtXi
    se = np.sqrt(np.diag(V))
    s2 = e @ e / (n - k)
    se_ols = np.sqrt(np.diag(s2 * XtXi))
    s_e = np.sqrt(e @ e / (n - k))
    t = b[0] / se[0]
    return {"n": n, "k": k, "df": n - k, "a_m": b[0], "alpha": 12 * b[0], "se_m": se[0], "se": 12 * se[0], "t": t,
            "t_ols": b[0] / se_ols[0], "p1": stats.t.sf(t, n - k), "s_e": s_e, "resid_vol": np.sqrt(12) * s_e,
            "ar_m": b[0] / s_e, "skew": stats.skew(e, bias=False), "kurt": stats.kurtosis(e, fisher=False, bias=False),
            "resid": e, "b": b, "tb": b / se, "r2": 1 - e @ e / np.sum((y - y.mean()) ** 2)}


def expected_max(N):
    """Bailey and Lopez de Prado (2014), eq. for E[max_N] of N iid standard normals (false-strategy theorem)."""
    if N <= 1:
        return 0.0
    return (1 - EULER) * stats.norm.ppf(1 - 1.0 / N) + EULER * stats.norm.ppf(1 - 1.0 / (N * np.e))


def deflated_sr(sr, T_, skew, kurt, N, V, scale=1.0):
    """DSR = Phi( (SR - SR0) sqrt(T-1) / sqrt(1 - g3 SR + (g4-1)/4 SR^2) ), SR0 = sqrt(V) E[max_N]."""
    sr0 = np.sqrt(V) * expected_max(N)
    den = np.sqrt(1.0 - skew * sr + (kurt - 1.0) / 4.0 * sr ** 2)
    z = (sr - sr0) * np.sqrt(T_ - 1.0) / den
    return stats.norm.cdf(z * scale), sr0, z


def nyholt(R):
    lam = np.linalg.eigvalsh(R); M = len(lam)
    return 1 + (M - 1) * (1 - np.var(lam, ddof=1) / M)


def liji(R):
    lam = np.clip(np.linalg.eigvalsh(R), 0, None)
    return float(np.sum((lam >= 1) + (lam - np.floor(lam))))


def boot_idx(T_, B, rng, order="block"):
    """Stationary bootstrap, p = 1/12. order='block' draws all starts then all switches (M7's order);
    order='row' draws draw-by-draw (a different but equally valid order)."""
    if order == "block":
        st = rng.integers(0, T_, size=(B, T_)); sw = rng.random((B, T_)) < 1 / 12
    else:
        st = np.empty((B, T_), dtype=np.int64); sw = np.empty((B, T_), dtype=bool)
        for b in range(B):
            st[b] = rng.integers(0, T_, size=T_); sw[b] = rng.random(T_) < 1 / 12
    idx = np.empty((B, T_), dtype=np.int64)
    idx[:, 0] = st[:, 0]
    for t in range(1, T_):
        idx[:, t] = np.where(sw[:, t], st[:, t], (idx[:, t - 1] + 1) % T_)
    return idx


# ------------------------------------------------------------------ data
FAC = C.load_ff5_mom(); X6 = FAC[C6]
KF3 = C.load_kf_ff3()
umd_raw = C._kf_monthly(list(C._kf_sections(C.RAW / "kf_F-F_Momentum_Factor.csv").values())[0]).iloc[:, 0] / 100
X4 = KF3[["Mkt-RF", "SMB", "HML"]].join(umd_raw.rename("UMD"))
rd = lambda n: pd.read_csv(T / n, index_col=0, parse_dates=True)  # noqa: E731
opt, ew, gb = rd("M5_industry_momentum_optimizer_returns_monthly.csv"), rd("M5_industry_momentum_returns_monthly.csv"), rd("M4_emissions_gb_monthly_returns.csv")

# M5 regenerations (arguments from M5 run.py lines 211-229 and 317-329)
D5 = L5.load_inputs(); R5 = D5["R"]
sig = L5.mom_signal(R5, 11, 1)
mem_full = {f"opt:{c}": opt[c] for c in opt.columns}
mem_full["EW:primary"] = ew["net"]
for name, L, S, n, cap, kf in [("window_1-0", 1, 0, 8, 0, 0), ("window_6-1", 6, 1, 8, 0, 0), ("window_12-1", 12, 1, 8, 0, 0),
                               ("no_skip_12-0", 12, 0, 8, 0, 0), ("n5_per_leg", 11, 1, 5, 0, 0), ("n10_per_leg", 11, 1, 10, 0, 0),
                               ("cap_weighted_legs", 11, 1, 8, 1, 0), ("KF_Aug2026_vintage", 11, 1, 8, 0, 1)]:
    Rv = D5["R_kf"] if kf else R5
    W = L5.rank_weights(L5.mom_signal(Rv, L, S), Rv, n, cap=D5["cap"] if cap else None)
    mem_full[f"EWvar:{name}"] = L5.backtest(W, Rv, L5.BASE_COST)["net"]
cm = L5.carbon_maps(D5["emis"], R5.columns); cov = cm["covered"]
emis_rank = list(D5["emis"].sort_values(ascending=False).index)
t5, t8, alli = emis_rank[:5], emis_rank[:8], list(R5.columns)
ex = lambda base, drop: [c for c in base if c not in drop]  # noqa: E731
scr = {"A0X_long_covered_only": (cov, None), "A5X_long_excl_top5": (ex(cov, t5), None), "A8X_long_excl_top8": (ex(cov, t8), None),
       "B0X_both_covered_only": (cov, cov), "B5X_both_excl_top5": (ex(cov, t5), ex(cov, t5)), "B8X_both_excl_top8": (ex(cov, t8), ex(cov, t8)),
       "A5M_long_excl_top5": (ex(alli, t5), None), "A8M_long_excl_top8": (ex(alli, t8), None),
       "B5M_both_excl_top5": (ex(alli, t5), ex(alli, t5)), "B8M_both_excl_top8": (ex(alli, t8), ex(alli, t8))}
for name, (lu, su) in scr.items():
    W = L5.rank_weights(sig, R5, 8, long_universe=lu, short_universe=su)
    mem_full[f"screen:{name}"] = L5.backtest(W, R5, L5.BASE_COST)["net"]
for c in gb.columns:
    if c != "epa5_minus_team5":
        mem_full[f"GB:{c}"] = gb[c]

from team_pipeline import run_pipeline  # noqa: E402
import helpers as H  # noqa: E402

TP = run_pipeline(bootstrap_reps=0)
team = {k: v["net_return"] for k, v in TP["strategies"].items() if not k.startswith("Benchmark")}
aso = TP["strategies"]["Benchmark | Always-short Brown"]["net_return"]
MEAS, MAC = H.build_measures(), H.macro_fixed()
m1b = {}
for m in ("MCCC", "CPU"):
    res = H.run_measure(MEAS[m], MAC, "realtime", "log1p")
    end = H.eval_end(MEAS[m])
    for code, sname in H.STRATS.items():
        s = res["strategies"][sname]["net_return"].copy()
        s[s.index > end] = 0.0
        m1b[f"M1b:{m}:{code}"] = s
m6 = rd("M6_factor_timing_portfolio_returns.csv"); m6r = rd("M6_factor_timing_rotation_returns.csv")
m6s = {f"M6:{c[:-4]}": m6[c] for c in m6.columns if c.endswith(":net") and c.split(":")[1] in
       ("timing_ridgecv", "timing_ols_lambda0", "timing_combination", "lmn_sign", "lmn_raw")}
m6s["M6:rotation_ridge"] = m6r["rotation_ridge"]
mem_post = {**mem_full, **{f"team:{k}": v for k, v in team.items()}, **m1b, **m6s}

WIN = {"S-full": ("1970-01-31", "2026-07-31"), "S-post": ("2010-01-31", "2026-07-31")}
FAM = {}
for fam, mem in (("S-full", mem_full), ("S-post", mem_post)):
    a, b = WIN[fam]
    Y = pd.DataFrame({k: v.loc[a:b] for k, v in mem.items()})
    print(fam, Y.shape, "any NaN:", bool(Y.isna().any().any()))
    FAM[fam] = Y

# ------------------------------------------------------------------ search families: member t, RW, SPA
m7m = pd.read_csv(T / "M7_search_members.csv").set_index(["family", "member"])
FITS, SUM = {}, []
for fam, Y in FAM.items():
    Xf = X6.loc[Y.index].values
    fits = {c: ols_nw(Y[c].values, Xf) for c in Y.columns}
    FITS[fam] = fits
    th = np.array([fits[c]["t"] for c in Y.columns]); am = np.array([fits[c]["a_m"] for c in Y.columns])
    sm_ = np.array([fits[c]["se_m"] for c in Y.columns])
    dt_ = max(abs(th[j] - m7m.loc[(fam, c), "t"]) for j, c in enumerate(Y.columns))
    da_ = max(abs(12 * am[j] - m7m.loc[(fam, c), "alpha"]) for j, c in enumerate(Y.columns))
    print(f"{fam}: member t max diff vs M7 {dt_:.2e}; alpha max diff {da_:.2e}")
    Tn, M = Y.shape
    Xc = np.column_stack([np.ones(Tn), Xf]); Yd = Y.values - am[None, :]
    thr = np.sqrt(2 * np.log(np.log(Tn)))
    for label, order, seed in (("same order, seed 20260926", "block", 20260926), ("row order, seed 20260926", "row", 20260926),
                               ("block order, seed 12345", "block", 12345)):
        idx = boot_idx(Tn, 5000, np.random.default_rng(seed), order)
        tau = np.empty((5000, M))
        for bb in range(5000):
            ii = idx[bb]; Xb = Xc[ii]
            tau[bb] = np.linalg.lstsq(Xb, Yd[ii], rcond=None)[0][0] / sm_
        o = np.argsort(-th, kind="stable")
        # Romano-Wolf stepdown written from the spec formula
        padj_sorted = np.empty(M); run = 0.0
        for j in range(M):
            mx = tau[:, o[j:]].max(axis=1)
            pt = (1 + np.sum(mx >= th[o[j]])) / 5001
            run = max(run, pt); padj_sorted[j] = run
        padj = np.empty(M); padj[o] = padj_sorted
        Tspa = max(0.0, th.max())
        Tb = np.maximum(0.0, (tau + np.where(th < -thr, th, 0.0)[None, :]).max(axis=1))
        pspa = (1 + np.sum(Tb >= Tspa)) / 5001
        crit = np.quantile(tau.max(axis=1), 0.95)
        cols = list(Y.columns)
        row = {"family": fam, "boot": label, "best": cols[int(np.argmax(th))], "best_t": th.max(),
               "rw_best": padj[int(np.argmax(th))], "spa_p": pspa, "crit95": crit, "rw_survivors": int((padj <= 0.05).sum()),
               "rw_X_unc": padj[cols.index("opt:X_unc")], "rw_epa5": padj[cols.index("GB:epa5")]}
        if label.startswith("same"):
            dd = max(abs(padj[j] - m7m.loc[(fam, c), "rw_adj_p"]) for j, c in enumerate(cols))
            row["max_diff_rw_vs_M7"] = dd
            surv = [c for j, c in enumerate(cols) if padj[j] <= 0.05]
            print(fam, "RW survivors:", surv)
        SUM.append(row)
    R = np.corrcoef(np.column_stack([fits[c]["resid"] for c in Y.columns]), rowvar=False)
    FITS[fam + "_R"] = R
    print(f"{fam}: Nyholt {nyholt(R):.3f}, Li-Ji {liji(R):.3f}, Sidak best {np.log(0.95) / np.log(1 - stats.t.sf(th.max(), Tn - 7)):.1f}")
print(pd.DataFrame(SUM).to_string())

# ------------------------------------------------------------------ deflated appraisal ratio (own)
drows = []
for fam, Y in FAM.items():
    Tn, M = Y.shape
    R = FITS[fam + "_R"]
    Nn, Nl = nyholt(R), liji(R)
    K = int(round(Nn))
    Dm = np.sqrt(np.clip(0.5 * (1 - R), 0, None)); np.fill_diagonal(Dm, 0.0)
    lab = fcluster(linkage(squareform(Dm, checks=False), method="average"), t=K, criterion="maxclust")
    Xf = X6.loc[Y.index].values
    car = [ols_nw(Y.loc[:, lab == g].mean(axis=1).values, Xf)["ar_m"] for g in np.unique(lab)]
    csr = [Y.loc[:, lab == g].mean(axis=1).mean() / Y.loc[:, lab == g].mean(axis=1).std(ddof=1) for g in np.unique(lab)]
    Vcl = np.var(car, ddof=1); V = max(Vcl, 1 / (Tn - 1)); Vraw = max(np.var(csr, ddof=1), 1 / (Tn - 1))
    print(f"{fam}: K {K} (clusters formed {len(np.unique(lab))}), V_cl {Vcl:.5f}, floor {1 / (Tn - 1):.5f}, E_N {expected_max(Nn):.3f}, "
          f"SR0 annual {np.sqrt(12) * np.sqrt(V) * expected_max(Nn):.3f}")
    for cand, col in (("book", "opt:X_unc"), ("EPA 5v5", "GB:epa5")):
        f_ = FITS[fam][col]
        sr, g3, g4, sc = f_["ar_m"], f_["skew"], f_["kurt"], f_["t"] / f_["t_ols"]

        def gov(N, V_):
            d1, s0, z = deflated_sr(sr, Tn, g3, g4, N, V_)
            d2, _, _ = deflated_sr(sr, Tn, g3, g4, N, V_, sc)
            return min(d1, d2), d1, d2, s0

        g_, d_iid, d_nw, s0 = gov(Nn, V)
        maxN = max([n for n in range(1, 501) if gov(n, V)[0] >= 0.95], default=0)
        y = Y[col]; srm = y.mean() / y.std(ddof=1)
        rho = [y.autocorr(k) for k in range(1, 12)]
        eta = 12 / np.sqrt(12 + 2 * sum((12 - k) * rho[k - 1] for k in range(1, 12)))
        tm = ols_nw(y.values, np.empty((len(y), 0)))["t"]
        rg3, rg4 = stats.skew(y, bias=False), stats.kurtosis(y, fisher=False, bias=False)
        r1, _, _ = deflated_sr(srm, Tn, rg3, rg4, Nn, Vraw)
        r2, _, _ = deflated_sr(srm, Tn, rg3, rg4, Nn, Vraw, tm / (srm * np.sqrt(Tn)))
        drows.append({"family": fam, "cand": cand, "T": Tn, "AR_ann": np.sqrt(12) * sr, "t_nw": f_["t"], "t_ols": f_["t_ols"],
                      "skew": g3, "kurt": g4, "N_ny": Nn, "N_lj": Nl, "V": V, "DSR_iid": d_iid, "DSR_NW": d_nw, "DSR_gov": g_,
                      "LiJi": gov(Nl, V)[0], "rawM": gov(M, V)[0], "Vfloor": gov(Nn, 1 / (Tn - 1))[0],
                      "LiJi_Vfloor": gov(Nl, 1 / (Tn - 1))[0], "rawM_Vfloor": gov(M, 1 / (Tn - 1))[0],
                      "PSR0": gov(1, V)[0], "maxN": maxN, "raw_SR_ann": np.sqrt(12) * srm, "lo_SR_ann": eta * srm,
                      "raw_DSR": min(r1, r2)})
DR = pd.DataFrame(drows)
print(DR.round(4).to_string())
m7d = pd.read_csv(T / "M7_dsr.csv")
for _, r in DR.iterrows():
    q = m7d[(m7d.family == r.family) & (m7d.member == ("opt:X_unc" if r.cand == "book" else "GB:epa5"))].iloc[0]
    print(r.family, r.cand, "diff DSR_gov", abs(r.DSR_gov - q.DSR_gov), "diff raw", abs(r.raw_DSR - q.raw_DSR_gov),
          "diff LiJi", abs(r.LiJi - q["DSR_gov[N = Li-Ji]"]), "diff Vfloor", abs(r.Vfloor - q["DSR_gov[V = 1/(T-1), N = Nyholt]"]),
          "maxN", r.maxN, q.max_N_pass, "lo", r.lo_SR_ann, q.lo_SR_annual)
DR.to_csv(OUT / "v2_dsr.csv", index=False)

# ------------------------------------------------------------------ holdout reading (own)
hs = {"book": opt["X_unc"], "EW": ew["net"], "EPA5": gb["epa5"], **{f"team:{k}": v for k, v in team.items()}, "always-short": aso}
hrows = []
for nm, s in hs.items():
    for model, Xm in (("FF5+UMD", X6), ("FF3", KF3[["Mkt-RF", "SMB", "HML"]])):
        if model == "FF3" and not nm.startswith("team"):
            continue
        y = s.loc["2022-08-31":"2026-07-31"]
        f_ = ols_nw(y.values, Xm.loc[y.index].values)
        tc = stats.t.ppf(0.95, f_["df"]); tp = stats.t.ppf(0.80, f_["df"])
        lo, hi, dl = f_["alpha"] - tc * f_["se"], f_["alpha"] + tc * f_["se"], 0.25 * f_["resid_vol"]
        rdg = ("positive but below" if lo > 0 and hi < dl else "confirms" if lo > 0 else "rejects" if hi < dl else "inconclusive")
        hrows.append({"series": nm, "model": model, "n": f_["n"], "alpha": f_["alpha"], "lo": lo, "hi": hi, "delta": dl,
                      "mde80": (tc + tp) * f_["se"], "reading": rdg})
print(pd.DataFrame(hrows).round(4).to_string())

# ------------------------------------------------------------------ cost stress (own)
P_ = pd.read_csv(T / "M5_industry_momentum_optimizer_paths_monthly.csv", header=[0, 1], index_col=0, skiprows=[2], parse_dates=True)
g, to = P_[("X_unc", "gross")].astype(float), P_[("X_unc", "turnover")].astype(float)
for w, (a, b) in {"full": ("1970-01-31", "2026-07-31"), "post2010": ("2010-01-31", "2026-07-31"),
                  "holdout": ("2022-08-31", "2026-07-31")}.items():
    Xw = X6.loc[a:b].values
    ag, at = ols_nw(g.loc[a:b].values, Xw), ols_nw(to.loc[a:b].values, Xw)
    line = [f"{c}bp {100 * ols_nw((g - c / 1e4 * to).loc[a:b].values, Xw)['alpha']:.2f}% "
            f"(t {ols_nw((g - c / 1e4 * to).loc[a:b].values, Xw)['t']:.2f})" for c in (0, 10, 25, 50)]
    print(w, "; ".join(line), f"; breakeven {1e4 * ag['a_m'] / at['a_m']:.0f} bp" if ag["a_m"] > 0 else "; gross alpha <= 0",
          f"; turnover {12 * to.loc[a:b].mean():.2f}")

# ------------------------------------------------------------------ frozen run statistics from the saved returns (own)
fz = pd.read_csv(T / "M7_frozen_pre1970_returns_monthly.csv", index_col=0, parse_dates=True)
print("frozen months", len(fz), fz.index[0].date(), fz.index[-1].date())
Xz = X4.loc[fz.index]
f_ = ols_nw(fz["net"].values, Xz.values)
tc = stats.t.ppf(0.95, f_["df"])
h1 = ols_nw(fz["net"].loc[:"1950-09-30"].values, Xz.loc[:"1950-09-30"].values)
h2 = ols_nw(fz["net"].loc["1950-10-31":].values, Xz.loc["1950-10-31":].values)
print(f"frozen (i): alpha {100 * f_['alpha']:.3f}% se {100 * f_['se']:.3f}% t {f_['t']:.4f} p1 {f_['p1']:.5f} df {f_['df']}; "
      f"UMD beta {f_['b'][4]:.3f} (t {f_['tb'][4]:.2f}), mkt {f_['b'][1]:.3f}, R2 {f_['r2']:.3f}, AR {np.sqrt(12) * f_['ar_m']:.3f}")
print(f"  halves: {len(fz.loc[:'1950-09-30'])} m {100 * h1['alpha']:.2f}% (t {h1['t']:.2f}); {len(fz.loc['1950-10-31':])} m "
      f"{100 * h2['alpha']:.2f}% (t {h2['t']:.2f})")
print(f"  90% [{100 * (f_['alpha'] - tc * f_['se']):.2f}, {100 * (f_['alpha'] + tc * f_['se']):.2f}], delta {100 * 0.25 * f_['resid_vol']:.2f} "
      f"(resid vol {100 * f_['resid_vol']:.2f}); net {1200 * fz['net'].mean():.2f}% vol {100 * np.sqrt(12) * fz['net'].std():.2f}% "
      f"turnover {12 * fz['turnover'].mean():.2f}")
s4 = ols_nw(fz["net_25bp"].values, Xz.values)
print(f"  S4 25bp {100 * s4['alpha']:.2f}% t {s4['t']:.2f}; elig {fz['n_elig'].min()}-{fz['n_elig'].max()}; "
      f"te {fz['exante_te_ann'].min():.5f}-{fz['exante_te_ann'].max():.5f}; fallback {int(fz['fallback'].sum())}, inaccurate {int(fz['inaccurate'].sum())}")
w_ = (1 + fz["net"]).cumprod(); dd = w_ / w_.cummax() - 1
r3 = (1 + fz["net"]).rolling(3).apply(np.prod, raw=True) - 1
print(f"  S3 worst month {100 * fz['net'].min():.1f}% {fz['net'].idxmin():%Y-%m}; worst 3m {100 * r3.min():.1f}% end {r3.idxmin():%Y-%m}; "
      f"maxDD {100 * dd.min():.1f}% trough {dd.idxmin():%Y-%m}")
s1y = fz["net"].loc["1963-07-31":]
s1 = ols_nw(s1y.values, X6.loc[s1y.index].values)
print(f"  S1 {len(s1y)} m: {100 * s1['alpha']:.2f}% se {100 * s1['se']:.2f}% t {s1['t']:.2f}")
bk = opt["X_unc"].loc["1970-01-31":"2026-07-31"]
p4 = ols_nw(bk.values, X4.loc[bk.index].values)
print(f"post-1970 book FF3+UMD alpha {100 * p4['alpha']:.2f}% t {p4['t']:.2f}; resid vol {100 * p4['resid_vol']:.2f}%")
w2 = (1 + bk).cumprod(); dd2 = w2 / w2.cummax() - 1; r32 = (1 + bk).rolling(3).apply(np.prod, raw=True) - 1
print(f"post-1970 crash: worst {100 * bk.min():.1f}% {bk.idxmin():%Y-%m}; 3m {100 * r32.min():.1f}% end {r32.idxmin():%Y-%m}; "
      f"Mar-May 2009 {100 * ((1 + bk.loc['2009-03-31':'2009-05-31']).prod() - 1):.1f}%; maxDD {100 * dd2.min():.1f}% {dd2.idxmin():%Y-%m}")
