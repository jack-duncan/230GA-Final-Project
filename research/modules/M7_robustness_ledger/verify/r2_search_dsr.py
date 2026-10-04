"""Round-2 adversarial verification of M7 checks 4 to 8 and 10 (independent code).

Members are regenerated from the saved module tables and the modules' own library calls, following the spec's
membership list and the arguments in M5's and M1b's run.py (not M7's code). Everything statistical is my own numpy
code: OLS, Newey-West (Bartlett, 6 lags, no small-sample scaling), unbiased skew and kurtosis, the stationary
bootstrap, Romano-Wolf stepdown, Hansen's consistent SPA, Nyholt and Li-Ji, the cluster V and the deflated ratio from
Bailey and Lopez de Prado (2014):
    E[max_N] = (1 - g) Phi^-1(1 - 1/N) + g Phi^-1(1 - 1/(N e)),  SR0 = sqrt(V) E[max_N]
    z = (SR - SR0) sqrt(T - 1) / sqrt(1 - g3 SR + (g4 - 1)/4 SR^2),  DSR = Phi(z)
Factors are parsed from the raw Ken French CSVs with my own parser and checked against lib/common.

Run: cd /home/hashim/projects/GA/project/research && uv run python modules/M7_robustness_ledger/verify/r2_search_dsr.py
"""
from __future__ import annotations

import math
import pathlib
import re
import sys
import warnings

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import squareform
from scipy.stats import norm, t as tdist

warnings.filterwarnings("ignore")
ROOT = pathlib.Path(__file__).resolve().parents[3]
T = ROOT / "outputs" / "tables"
RAW = ROOT / "data" / "raw"
OUT = pathlib.Path(__file__).resolve().parent / "out_r2"
OUT.mkdir(exist_ok=True)
LOG = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LOG.append(s)


def check(name, ok, detail=""):
    say(f"[{'OK ' if ok else 'BAD'}] {name}" + (f": {detail}" if detail else ""))
    return ok


# ------------------------------------------------------------------ factors, own parser
def kf_first_monthly(path):
    rows, started = [], False
    for ln in pathlib.Path(path).read_text(errors="ignore").splitlines():
        m = re.match(r"^\s*(\d{6})\s*,(.*)$", ln)
        if m:
            started = True
            rows.append([m.group(1)] + [float(x) for x in m.group(2).split(",")])
        elif started:
            break
        elif ln.strip().startswith(","):
            hdr = [c.strip() for c in ln.split(",")[1:]]
    df = pd.DataFrame([r[1:] for r in rows], columns=hdr,
                      index=pd.to_datetime([r[0] for r in rows], format="%Y%m") + pd.offsets.MonthEnd(0))
    return df.replace([-99.99, -999.0], np.nan) / 100


ff5raw = kf_first_monthly(RAW / "kf_F-F_Research_Data_5_Factors_2x3.csv")
ff3raw = kf_first_monthly(RAW / "kf_F-F_Research_Data_Factors.csv")
umd = kf_first_monthly(RAW / "kf_F-F_Momentum_Factor.csv").iloc[:, 0].rename("UMD")
X6 = ff5raw[["Mkt-RF", "SMB", "HML", "RMW", "CMA"]].join(umd, how="left")
KF3 = ff3raw[["Mkt-RF", "SMB", "HML"]]
X4 = KF3.join(umd, how="left")
sys.path.insert(0, str(ROOT / "lib"))
import common as C  # noqa: E402

ref6 = C.load_ff5_mom()[["Mkt-RF", "SMB", "HML", "RMW", "CMA", "UMD"]]
d6 = float((X6.loc[ref6.index] - ref6).abs().max().max())
d3 = float((KF3 - C.load_kf_ff3()[["Mkt-RF", "SMB", "HML"]]).abs().max().max())
check("own factor parse equals lib/common (FF5+UMD, KF3)", d6 < 1e-15 and d3 < 1e-15, f"{d6:.1e}, {d3:.1e}; UMD from {umd.index[0]:%Y-%m}")


# ------------------------------------------------------------------ my OLS / NW / moments
def ols_nw(y, X, lags=6):
    y = np.asarray(y, float); Xc = np.column_stack([np.ones(len(y)), np.asarray(X, float)])
    n, k = Xc.shape
    Q, Rr = np.linalg.qr(Xc)
    b = np.linalg.solve(Rr, Q.T @ y)
    e = y - Xc @ b
    XtXi = np.linalg.inv(Xc.T @ Xc)
    u = Xc * e[:, None]
    S = u.T @ u
    for L in range(1, lags + 1):
        w = 1 - L / (lags + 1)
        G = u[L:].T @ u[:-L]
        S += w * (G + G.T)
    V = XtXi @ S @ XtXi
    se = np.sqrt(np.diag(V))
    s2 = e @ e / (n - k)
    se_ols = np.sqrt(np.diag(XtXi) * s2)
    sd_e = np.sqrt(e @ e / (n - k))                 # ddof = k
    m2, m3, m4 = np.mean((e - e.mean()) ** 2), np.mean((e - e.mean()) ** 3), np.mean((e - e.mean()) ** 4)
    g1 = m3 / m2 ** 1.5; g2 = m4 / m2 ** 2 - 3
    G1 = math.sqrt(n * (n - 1)) / (n - 2) * g1
    G2 = ((n + 1) * g2 + 6) * (n - 1) / ((n - 2) * (n - 3))
    return {"n": n, "k": k, "df": n - k, "b": b, "a_m": b[0], "alpha": 12 * b[0], "se_m": se[0], "se": 12 * se[0],
            "t": b[0] / se[0], "t_ols": b[0] / se_ols[0], "p1": float(tdist.sf(b[0] / se[0], n - k)),
            "e": e, "sd_e": sd_e, "ar_m": b[0] / sd_e, "ar": math.sqrt(12) * b[0] / sd_e, "skew": G1, "kurt": G2 + 3,
            "resid_vol": math.sqrt(12) * sd_e, "tb": b / se, "r2": 1 - (e @ e) / np.sum((y - y.mean()) ** 2)}


def fitw(s, Xf, a, b):
    y = s.loc[a:b]
    return ols_nw(y.values, Xf.loc[y.index].values)


# ------------------------------------------------------------------ members
say("building members ...")
opt = pd.read_csv(T / "M5_industry_momentum_optimizer_returns_monthly.csv", index_col=0, parse_dates=True)
ew = pd.read_csv(T / "M5_industry_momentum_returns_monthly.csv", index_col=0, parse_dates=True)
gb = pd.read_csv(T / "M4_emissions_gb_monthly_returns.csv", index_col=0, parse_dates=True)
sys.path.insert(0, str(ROOT / "modules" / "M5_industry_momentum"))
import m5lib as L5  # noqa: E402

D = L5.load_inputs(); R, cap, emis = D["R"], D["cap"], D["emis"]
sig = L5.mom_signal(R, 11, 1)
covered = L5.carbon_maps(emis, R.columns)["covered"]
top_emit = list(emis.sort_values(ascending=False).index); top5, top8 = top_emit[:5], top_emit[:8]
all_ind = list(R.columns)
rob = pd.read_csv(T / "M5_industry_momentum_robustness.csv").set_index("variant")
scr = pd.read_csv(T / "M5_industry_momentum_carbon_screens.csv").set_index("book")
m5 = {}
rep = []
VAR = {"window_1-0": (1, 0, 8, 0, 0), "window_6-1": (6, 1, 8, 0, 0), "window_12-1": (12, 1, 8, 0, 0), "no_skip_12-0": (12, 0, 8, 0, 0),
       "n5_per_leg": (11, 1, 5, 0, 0), "n10_per_leg": (11, 1, 10, 0, 0), "cap_weighted_legs": (11, 1, 8, 1, 0),
       "KF_Aug2026_vintage": (11, 1, 8, 0, 1)}
check("my EW variant list = non-primary rows of M5 robustness table", set(VAR) == set(rob.index) - {"primary_11-1_n8_EW"})
for nm, (Lk, Sk, nk, cp, kf) in VAR.items():
    Rv = D["R_kf"] if kf else R
    b_ = L5.backtest(L5.rank_weights(L5.mom_signal(Rv, Lk, Sk), Rv, nk, cap=cap if cp else None), Rv, L5.BASE_COST)
    s = b_["net"]; w = s.loc["1970-01-31":"2026-07-31"]
    sh = math.sqrt(12) * w.mean() / w.std(ddof=1); al = fitw(s, X6, "1970-01-31", "2026-07-31")["alpha"]
    rep.append(max(abs(sh - rob.loc[nm, "sharpe_full_1970"]), abs(al - rob.loc[nm, "alpha_full_1970"])))
    m5[f"EWvar:{nm}"] = s
SCR = {"A0X_long_covered_only": (covered, None), "A5X_long_excl_top5": ([c for c in covered if c not in top5], None),
       "A8X_long_excl_top8": ([c for c in covered if c not in top8], None), "B0X_both_covered_only": (covered, covered),
       "B5X_both_excl_top5": ([c for c in covered if c not in top5],) * 2, "B8X_both_excl_top8": ([c for c in covered if c not in top8],) * 2,
       "A5M_long_excl_top5": ([c for c in all_ind if c not in top5], None), "A8M_long_excl_top8": ([c for c in all_ind if c not in top8], None),
       "B5M_both_excl_top5": ([c for c in all_ind if c not in top5],) * 2, "B8M_both_excl_top8": ([c for c in all_ind if c not in top8],) * 2}
check("my screen list = non-primary rows of M5 screens table", set(SCR) == set(scr.index) - {"primary"})
for nm, (lu, su) in SCR.items():
    b_ = L5.backtest(L5.rank_weights(sig, R, 8, long_universe=lu, short_universe=su), R, L5.BASE_COST)
    s = b_["net"]; w = s.loc["1970-01-31":"2026-07-31"]
    sh = math.sqrt(12) * w.mean() / w.std(ddof=1); al = fitw(s, X6, "1970-01-31", "2026-07-31")["alpha"]
    rep.append(max(abs(sh - scr.loc[nm, "sharpe_full_1970"]), abs(al - scr.loc[nm, "alpha_full_1970"])))
    m5[f"screen:{nm}"] = s
check("18 M5 regenerations reproduce Sharpe and FF5+UMD alpha to 1e-6", max(rep) < 1e-6, f"max diff {max(rep):.1e}")

from team_pipeline import run_pipeline  # noqa: E402

TP = run_pipeline(bootstrap_reps=0)
team = {k: v["net_return"] for k, v in TP["strategies"].items() if not k.startswith("Benchmark")}
always_short = TP["strategies"]["Benchmark | Always-short Brown"]["net_return"]
say("team rules:", list(team))
sys.path.insert(0, str(ROOT / "modules" / "M1b_alt_signals"))
import helpers as H  # noqa: E402

MEAS, MAC = H.build_measures(), H.macro_fixed()
led1b = pd.read_csv(T / "M1b_alt_signals_tests_ledger.csv").set_index("test_id")
m1b, rep1b, zeroed = {}, [], {}
for m in ("MCCC", "CPU"):
    res = H.run_measure(MEAS[m], MAC, "realtime", "log1p")
    end = H.eval_end(MEAS[m])
    for code, sname in H.STRATS.items():
        s = res["strategies"][sname]["net_return"].copy()
        st = H.window_stats(res["strategies"][sname], "2010-01-31", "2022-07-31", C.load_team()["ff3"])
        rep1b.append(abs(st["alpha_t_hac6"] - led1b.loc[f"Q1_{m}_realtime_{code}_validation_alpha", "statistic"]))
        aft = (s.index > end) & (s.index <= "2026-07-31")
        zeroed[f"{m} {code}"] = int((s[aft].fillna(0) != 0).sum())
        s[s.index > end] = 0.0
        m1b[f"M1b:{m}:{code}"] = s
    say(f"  {m} eval_end {end:%Y-%m}")
say("  nonzero months zeroed after eval_end:", zeroed)
check("12 M1b rules reproduce validation alpha t to 1e-6", max(rep1b) < 1e-6, f"{max(rep1b):.1e}")
m6 = pd.read_csv(T / "M6_factor_timing_portfolio_returns.csv", index_col=0, parse_dates=True)
m6r = pd.read_csv(T / "M6_factor_timing_rotation_returns.csv", index_col=0, parse_dates=True)
m6s = {f"M6:{c[:-4]}": m6[c] for c in m6.columns if c.endswith(":net") and c.split(":")[1] in
       ("timing_ridgecv", "timing_ols_lambda0", "timing_combination", "lmn_sign", "lmn_raw")}
m6s["M6:rotation_ridge"] = m6r["rotation_ridge"]
say(f"  M6 series: {len(m6s)}")

full = {**{f"opt:{c}": opt[c] for c in opt.columns}, "EW:primary": ew["net"], **m5,
        **{f"GB:{c}": gb[c] for c in gb.columns if c != "epa5_minus_team5"}}
post = {**full, **{f"team:{k}": v for k, v in team.items()}, **m1b, **m6s}
FAMW = {"S-full": (full, "1970-01-31", "2026-07-31", 679), "S-post": (post, "2010-01-31", "2026-07-31", 199)}
Y = {}
for fam, (mem, a, b, n) in FAMW.items():
    Yf = pd.DataFrame({k: v.loc[a:b] for k, v in mem.items()})
    check(f"{fam}: {Yf.shape} with no missing month", Yf.shape == (n, 58 if fam == "S-full" else 89) and not Yf.isna().any().any())
    Y[fam] = Yf

# ------------------------------------------------------------------ member fits vs M7_search_members.csv
SMm = pd.read_csv(T / "M7_search_members.csv").set_index(["family", "member"])
FIT, RES = {}, {}
for fam, Yf in Y.items():
    Fm = X6.loc[Yf.index].values
    FIT[fam] = {c: ols_nw(Yf[c].values, Fm) for c in Yf.columns}
    RES[fam] = np.column_stack([FIT[fam][c]["e"] for c in Yf.columns])
    dt_ = max(abs(FIT[fam][c]["t"] - SMm.loc[(fam, c), "t"]) for c in Yf.columns)
    da_ = max(abs(FIT[fam][c]["alpha"] - SMm.loc[(fam, c), "alpha"]) for c in Yf.columns)
    check(f"{fam}: my NW t and alpha equal M7_search_members.csv for all members", dt_ < 1e-10 and da_ < 1e-12
          and set(Yf.columns) == set(SMm.loc[fam].index), f"t {dt_:.1e}, alpha {da_:.1e}")


# ------------------------------------------------------------------ stationary bootstrap, RW, SPA (own code)
def sb_index(Tn, Bn, seed, order="m7"):
    rng = np.random.default_rng(seed)
    if order == "m7":                     # B x T starts, then B x T restart uniforms (M7's documented order)
        st = rng.integers(0, Tn, size=(Bn, Tn)); u = rng.random((Bn, Tn))
    else:                                 # draw-by-draw: each draw takes its own starts then uniforms
        st = np.empty((Bn, Tn), np.int64); u = np.empty((Bn, Tn))
        for bb in range(Bn):
            st[bb] = rng.integers(0, Tn, size=Tn); u[bb] = rng.random(Tn)
    idx = np.empty((Bn, Tn), np.int64); idx[:, 0] = st[:, 0]
    for tt in range(1, Tn):
        idx[:, tt] = np.where(u[:, tt] < 1 / 12, st[:, tt], (idx[:, tt - 1] + 1) % Tn)
    return idx


def rw_spa(fam, seed=20260926, order="m7", Bn=5000):
    Yf = Y[fam]; cols = list(Yf.columns); Tn, M = Yf.shape
    Xc = np.column_stack([np.ones(Tn), X6.loc[Yf.index].values])
    a = np.array([FIT[fam][c]["a_m"] for c in cols]); s = np.array([FIT[fam][c]["se_m"] for c in cols])
    th = np.array([FIT[fam][c]["t"] for c in cols])
    Yd = Yf.values - a
    idx = sb_index(Tn, Bn, seed, order)
    tau = np.empty((Bn, M))
    for bb in range(Bn):
        Xb = Xc[idx[bb]]
        coef, *_ = np.linalg.lstsq(Xb, Yd[idx[bb]], rcond=None)
        tau[bb] = coef[0] / s
    order_ = sorted(range(M), key=lambda i: -th[i])
    padj = np.empty(M); run = 0.0
    for j, i in enumerate(order_):
        mx = tau[:, order_[j:]].max(axis=1)
        pt = (1 + np.sum(mx >= th[i])) / (Bn + 1)
        run = max(run, pt); padj[i] = run
    thr = math.sqrt(2 * math.log(math.log(Tn)))
    Tspa = max(0.0, th.max())
    Tb = np.maximum(0, (tau + np.where(th < -thr, th, 0.0)).max(axis=1))
    pspa = (1 + np.sum(Tb >= Tspa)) / (Bn + 1)
    return dict(zip(cols, padj)), pspa, float(np.quantile(tau.max(axis=1), 0.95))


RW = {}
for fam in Y:
    padj, pspa, c95 = rw_spa(fam)
    RW[fam] = padj
    d = max(abs(padj[c] - SMm.loc[(fam, c), "rw_adj_p"]) for c in padj)
    surv = sorted([(round(p, 4), c) for c, p in padj.items() if p <= 0.05])
    best = max(Y[fam].columns, key=lambda c: FIT[fam][c]["t"])
    say(f"{fam}: best {best} t {FIT[fam][best]['t']:.3f} RW {padj[best]:.4f}; SPA {pspa:.4f}; max-t 95% {c95:.3f}; "
        f"survivors {len(surv)}")
    for p, c in surv:
        say(f"    {c:22s} t {FIT[fam][c]['t']:.3f}  RW adj p {p:.4f}")
    check(f"{fam}: my RW adjusted p equal M7 for every member", d < 1e-12, f"max diff {d:.1e}")
    for cand in ("opt:X_unc", "GB:epa5"):
        say(f"    {cand}: alpha {100 * FIT[fam][cand]['alpha']:.2f}% t {FIT[fam][cand]['t']:.2f} RW {padj[cand]:.4f}")
# sensitivity: another draw order and seed (spec fixes seed, B and law, not order)
for order, seed in (("draw", 20260926), ("m7", 777)):
    txt = []
    for fam in Y:
        padj, pspa, c95 = rw_spa(fam, seed, order)
        txt.append(f"{fam} book {padj['opt:X_unc']:.4f} epa5 {padj['GB:epa5']:.4f} survivors {sum(p <= 0.05 for p in padj.values())} "
                   f"best {min(padj.values()):.4f}")
    say(f"  RW sensitivity ({order}, seed {seed}): " + "; ".join(txt))


# ------------------------------------------------------------------ Nyholt, Li-Ji, clusters, DSR (own code)
def meff(E):
    Rm = np.corrcoef(E, rowvar=False)
    lam = np.linalg.eigvalsh(Rm); M = len(lam)
    ny = 1 + (M - 1) * (1 - np.var(lam, ddof=1) / M)
    lc = np.clip(lam, 0, None)
    lj = float(np.sum((lc >= 1) + (lc - np.floor(lc))))
    return ny, lj, Rm


EG = 0.5772156649


def e_max(N):
    if N <= 1:
        return 0.0
    return (1 - EG) * norm.ppf(1 - 1 / N) + EG * norm.ppf(1 - 1 / (N * math.e))


def dsr_blp(sr, Tn, g3, g4, N, V, scale=1.0):
    sr0 = math.sqrt(V) * e_max(N)
    z = (sr - sr0) * math.sqrt(Tn - 1) / math.sqrt(1 - g3 * sr + (g4 - 1) / 4 * sr ** 2)
    return norm.cdf(z * scale), sr0, z


# sanity of the E[max] approximation against simulation
rng = np.random.default_rng(1)
for N in (42, 75):
    sim = rng.standard_normal((20000, N)).max(axis=1).mean()
    say(f"E[max] check N={N}: formula {e_max(N):.4f}, simulated mean max of N iid N(0,1) {sim:.4f}")

M7D = pd.read_csv(T / "M7_dsr.csv").set_index(["candidate", "family"])
CAND = {"book (X_unc)": "opt:X_unc", "EPA 5v5 spread": "GB:epa5"}
mine_rows = []
maxdiff = 0.0
for fam in Y:
    Yf = Y[fam]; Tn, M = Yf.shape
    ny, lj, Rm = meff(RES[fam])
    K = int(round(ny))
    Dm = np.sqrt(np.clip(0.5 * (1 - Rm), 0, None)); np.fill_diagonal(Dm, 0)
    lab = fcluster(linkage(squareform(Dm, checks=False), method="average"), t=K, criterion="maxclust")
    Fm = X6.loc[Yf.index].values
    car, csr = [], []
    for k in sorted(set(lab)):
        cs = Yf.loc[:, lab == k].mean(axis=1).values
        car.append(ols_nw(cs, Fm)["ar_m"]); csr.append(cs.mean() / cs.std(ddof=1))
    Vcl = float(np.var(car, ddof=1)); floor = 1 / (Tn - 1); V = max(Vcl, floor)
    Vraw = max(float(np.var(csr, ddof=1)), floor)
    say(f"{fam}: Nyholt {ny:.3f} Li-Ji {lj:.3f} K {K} clusters formed {len(set(lab))} V_cl {Vcl:.5f} floor {floor:.5f} "
        f"E_N {e_max(ny):.4f} SR0 annual {math.sqrt(12) * math.sqrt(V) * e_max(ny):.3f}")
    for cn, col in CAND.items():
        f_ = FIT[fam][col]
        sc = f_["t"] / f_["t_ols"]

        def gov(N, VV):
            a_, _, _ = dsr_blp(f_["ar_m"], Tn, f_["skew"], f_["kurt"], N, VV)
            b_, _, _ = dsr_blp(f_["ar_m"], Tn, f_["skew"], f_["kurt"], N, VV, sc)
            return min(a_, b_), a_, b_
        g, di, dn = gov(ny, V)
        sens = {"N = Li-Ji": gov(lj, V)[0], "N = raw M": gov(M, V)[0], "V = 1/(T-1), N = Nyholt": gov(ny, floor)[0],
                "N = Li-Ji, V = 1/(T-1)": gov(lj, floor)[0], "N = raw M, V = 1/(T-1)": gov(M, floor)[0]}
        psr = gov(1, V)[0]
        maxN = max([n for n in range(1, 501) if gov(n, V)[0] >= 0.95], default=0)
        # raw-Sharpe context
        y = Yf[col].values; srm = y.mean() / y.std(ddof=1)
        yn = y - y.mean(); nn = len(y)
        m2, m3, m4 = np.mean(yn ** 2), np.mean(yn ** 3), np.mean(yn ** 4)
        G1 = math.sqrt(nn * (nn - 1)) / (nn - 2) * m3 / m2 ** 1.5
        G2 = ((nn + 1) * (m4 / m2 ** 2 - 3) + 6) * (nn - 1) / ((nn - 2) * (nn - 3)) + 3
        tnw_mean = ols_nw(y, np.empty((nn, 0)))["t"]
        r_i, _, _ = dsr_blp(srm, Tn, G1, G2, ny, Vraw)
        r_n, _, _ = dsr_blp(srm, Tn, G1, G2, ny, Vraw, tnw_mean / (srm * math.sqrt(Tn)))
        rho = [np.corrcoef(yn[kk:], yn[:-kk])[0, 1] for kk in range(1, 12)]
        # Lo's eta with pandas-style autocorrelation (Pearson of the lagged pair)
        eta = 12 / math.sqrt(12 + 2 * sum((12 - kk) * rho[kk - 1] for kk in range(1, 12)))
        row = {"candidate": cn, "family": fam, "AR_annual": f_["ar"], "t_NW": f_["t"], "t_OLS": f_["t_ols"], "skew": f_["skew"],
               "kurt": f_["kurt"], "DSR_iid": di, "DSR_NW": dn, "DSR_gov": g, **sens, "PSR0": psr, "maxN": maxN,
               "raw_SR": math.sqrt(12) * srm, "lo_SR": eta * srm, "raw_DSR": min(r_i, r_n)}
        mine_rows.append(row)
        m7 = M7D.loc[(cn, fam)]
        pairs = [(g, m7.DSR_gov), (di, m7.DSR_iid), (dn, m7.DSR_NW), (psr, m7.PSR0_gov), (f_["ar"], m7.AR_annual),
                 (f_["skew"], m7.resid_skew), (f_["kurt"], m7.resid_kurt), (ny, m7.N_nyholt), (lj, m7.N_liji), (Vcl, m7.V_cl),
                 (math.sqrt(12) * srm, m7.raw_SR_annual), (eta * srm, m7.lo_SR_annual), (min(r_i, r_n), m7.raw_DSR_gov)]
        pairs += [(sens[k], m7[f"DSR_gov[{k}]"]) for k in sens]
        maxdiff = max(maxdiff, max(abs(a - b) for a, b in pairs))
        check(f"{cn} {fam}: max N pass {maxN} equals M7 {int(m7.max_N_pass)}", maxN == int(m7.max_N_pass))
MD = pd.DataFrame(mine_rows)
MD.to_csv(OUT / "r2_dsr.csv", index=False)
with pd.option_context("display.width", 250, "display.max_columns", 30, "display.float_format", "{:.3f}".format):
    say(MD.to_string(index=False))
check("every DSR, sensitivity, PSR and context value equals M7_dsr.csv", maxdiff < 1e-9, f"max diff {maxdiff:.1e}")
check("both candidates fail 0.95 in both windows under every sensitivity",
      (MD[["DSR_gov", "N = Li-Ji", "N = raw M", "V = 1/(T-1), N = Nyholt", "N = Li-Ji, V = 1/(T-1)", "N = raw M, V = 1/(T-1)"]] < 0.95).all().all(),
      f"most lenient {MD[['N = Li-Ji, V = 1/(T-1)']].max().iloc[0]:.3f}")

# ------------------------------------------------------------------ holdout reading (check 6)
HO = pd.read_csv(T / "M7_holdout_reading.csv")
hs = {"optimizer book (X_unc)": opt["X_unc"], "EW momentum book": ew["net"], "EPA 5v5 spread": gb["epa5"],
      **{f"team: {k}": v for k, v in team.items()}, "reference: Always-short Brown": always_short}
hd, hread = 0.0, []
for nm, s in hs.items():
    for model, Xf in (("FF5+UMD", X6), ("FF3", KF3)):
        if model == "FF3" and not nm.startswith("team"):
            continue
        f_ = fitw(s, Xf, "2022-08-31", "2026-07-31")
        tc, tp = tdist.ppf(0.95, f_["df"]), tdist.ppf(0.80, f_["df"])
        lo, hi, dl = f_["alpha"] - tc * f_["se"], f_["alpha"] + tc * f_["se"], 0.25 * f_["resid_vol"]
        rd = ("positive but below the worthwhile margin" if lo > 0 and hi < dl else "confirms a positive alpha" if lo > 0
              else "rejects a worthwhile alpha" if hi < dl else "inconclusive")
        m7 = HO[(HO.series == nm) & (HO.model == model)].iloc[0]
        hd = max(hd, abs(f_["alpha"] - m7.alpha), abs(lo - m7.ci90_lo), abs(hi - m7.ci90_hi), abs(dl - m7.delta),
                 abs((tc + tp) * f_["se"] - m7.mde_80))
        hread.append(rd == m7.reading)
        say(f"  holdout {model:7s} {nm:45s} a {100 * f_['alpha']:6.2f}% [{100 * lo:6.2f}, {100 * hi:6.2f}] d {100 * dl:5.2f} "
            f"MDE {100 * (tc + tp) * f_['se']:5.2f} {rd}")
check("holdout: 16 rows equal M7_holdout_reading.csv, readings identical", hd < 1e-12 and all(hread) and len(hread) == 16, f"{hd:.1e}")

# ------------------------------------------------------------------ cost stress (check 8)
paths = pd.read_csv(T / "M5_industry_momentum_optimizer_paths_monthly.csv", header=[0, 1], index_col=0, skiprows=[2], parse_dates=True)
g_, to_ = paths[("X_unc", "gross")].astype(float), paths[("X_unc", "turnover")].astype(float)
KS = pd.read_csv(T / "M7_cost_stress.csv")
kd = 0.0
for w, (a, b) in {"full": ("1970-01-31", "2026-07-31"), "post2010": ("2010-01-31", "2026-07-31"),
                  "holdout": ("2022-08-31", "2026-07-31")}.items():
    ag, at = fitw(g_, X6, a, b), fitw(to_, X6, a, b)
    for c in (0, 10, 25, 50):
        f_ = fitw(g_ - c / 1e4 * to_, X6, a, b)
        m7 = KS[(KS.window == w) & (KS.cost_bp == c)].iloc[0]
        kd = max(kd, abs(f_["alpha"] - m7.alpha), abs(f_["t"] - m7.t))
    be = 1e4 * ag["a_m"] / at["a_m"] if ag["a_m"] > 0 else float("nan")
    say(f"  cost {w}: gross alpha {100 * ag['alpha']:.2f}% break-even {be:.0f} bp; turnover {12 * to_.loc[a:b].mean():.2f}")
check("cost stress 12 alphas and t equal M7_cost_stress.csv", kd < 1e-10, f"{kd:.1e}")

# ------------------------------------------------------------------ frozen run statistics from the saved returns (check 7)
fz = pd.read_csv(T / "M7_frozen_pre1970_returns_monthly.csv", index_col=0, parse_dates=True)
FZ = pd.read_csv(T / "M7_frozen_pre1970.csv").set_index("item")["value"]
net = fz["net"]
mn = fitw(net, X4, "1931-07-31", "1969-12-31")
h1 = fitw(net, X4, "1931-07-31", "1950-09-30"); h2 = fitw(net, X4, "1950-10-31", "1969-12-31")
tc = tdist.ppf(0.95, mn["df"]); U = mn["alpha"] + tc * mn["se"]; dl = 0.25 * mn["resid_vol"]
s1 = fitw(net, X6, "1963-07-31", "1969-12-31")
s4 = fitw(fz["gross"] - 0.0025 * fz["turnover"], X4, "1931-07-31", "1969-12-31")
verdict = "PASS" if (mn["alpha"] > 0 and mn["t"] >= 2 and h1["alpha"] > 0 and h2["alpha"] > 0) else ("REJECT" if U < dl else "INCONCLUSIVE")
say(f"frozen: n {mn['n']} alpha {100 * mn['alpha']:.3f}% SE {100 * mn['se']:.3f}% t {mn['t']:.4f} p1 {mn['p1']:.5f} df {mn['df']}; "
    f"halves {100 * h1['alpha']:.2f}% (t {h1['t']:.2f}, n {h1['n']}) / {100 * h2['alpha']:.2f}% (t {h2['t']:.2f}, n {h2['n']}); "
    f"CI90 [{100 * (mn['alpha'] - tc * mn['se']):.2f}, {100 * U:.2f}] delta {100 * dl:.2f} (resid vol {100 * mn['resid_vol']:.2f}); "
    f"UMD b {mn['b'][4]:.3f} t {mn['tb'][4]:.2f}; mkt b {mn['b'][1]:.3f}; R2 {mn['r2']:.3f}; AR {mn['ar']:.3f}; "
    f"S1 {100 * s1['alpha']:.2f}% SE {100 * s1['se']:.2f}% t {s1['t']:.2f} n {s1['n']}; S4 {100 * s4['alpha']:.2f}% t {s4['t']:.2f}; {verdict}")
check("frozen stats equal M7_frozen_pre1970.csv", abs(mn["t"] - float(FZ["t"])) < 1e-10 and abs(mn["alpha"] - float(FZ["alpha"])) < 1e-12
      and abs(h1["t"] - float(FZ["h1_t"])) < 1e-10 and abs(h2["t"] - float(FZ["h2_t"])) < 1e-10 and verdict == FZ["verdict"]
      and abs(s1["t"] - float(FZ["S1_t"])) < 1e-10 and abs(s4["t"] - float(FZ["S4_t_25bp"])) < 1e-10)
tdh = (h1["alpha"] - h2["alpha"]) / math.sqrt((h1["alpha"] / h1["t"]) ** 2 + (h2["alpha"] / h2["t"]) ** 2)
w = (1 + net).cumprod(); dd = (w / w.cummax() - 1)
r3 = (1 + net).rolling(3).apply(np.prod, raw=True) - 1
say(f"  halves diff t {tdh:.3f}; S3 worst {100 * net.min():.1f}% ({net.idxmin():%Y-%m}), worst 3m {100 * r3.min():.1f}% "
    f"(ends {r3.idxmin():%Y-%m}), max DD {100 * dd.min():.1f}% (trough {dd.idxmin():%Y-%m}); net {100 * 12 * net.mean():.2f}% "
    f"vol {100 * math.sqrt(12) * net.std(ddof=1):.2f}% turnover {12 * fz['turnover'].mean():.2f}; elig {fz.n_elig.min()}-{fz.n_elig.max()}; "
    f"TE range {fz.exante_te_ann.min():.6f}-{fz.exante_te_ann.max():.6f}; fallbacks {int(fz.fallback.sum())}, "
    f"inaccurate {int(fz.inaccurate.sum())}; b=-1 net IR diff check: {FZ['S2_d_ir']}")
for tag, Xc in (("kf3+umd", X4), ("ff5file ff3+umd", X6[["Mkt-RF", "SMB", "HML", "UMD"]])):
    f_ = fitw(opt["X_unc"], Xc, "1970-01-31", "2026-07-31")
    say(f"  post-1970 FF3+UMD ({tag}): {100 * f_['alpha']:.3f}% t {f_['t']:.3f}")
f_ = fitw(opt["X_unc"], X6, "1970-01-31", "2009-12-31")
say(f"  FF5+UMD 1970-2009: {100 * f_['alpha']:.3f}% t {f_['t']:.3f} n {f_['n']}")

# ------------------------------------------------------------------ verdict map from my own numbers (check 10)
HOi = HO[HO.model == "FF5+UMD"].set_index("series")
for cn, col, hn in (("book", "opt:X_unc", "optimizer book (X_unc)"), ("EPA 5v5", "GB:epa5", "EPA 5v5 spread")):
    a_ok = (col == "opt:X_unc") and verdict == "PASS"
    b_ok = RW["S-full"][col] <= 0.05 and RW["S-post"][col] <= 0.05
    dd_ = MD[MD.candidate == ("book (X_unc)" if col == "opt:X_unc" else "EPA 5v5 spread")].DSR_gov
    c_ok = bool((dd_ >= 0.95).all())
    h = HOi.loc[hn]; d_ok = h.alpha > 0 and h.reading != "rejects a worthwhile alpha"
    v = "Implement" if a_ok and b_ok and c_ok and d_ok else ("Paper-trade" if a_ok else "Do not implement")
    say(f"verdict {cn}: (a) {a_ok} (b) {b_ok} [{RW['S-full'][col]:.4f} / {RW['S-post'][col]:.4f}] (c) {c_ok} "
        f"[{', '.join(f'{x:.3f}' for x in dd_)}] (d) {d_ok} [{100 * h.alpha:.2f}%, {h.reading}] -> {v}")
(OUT / "r2_search_dsr_log.txt").write_text("\n".join(LOG) + "\n")
