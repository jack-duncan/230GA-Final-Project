"""Independent verification of M1b_alt_signals (does NOT import modules/M1b_alt_signals/helpers.py or run.py).

Run: cd /home/hashim/projects/GA/project/research && uv run python modules/M1b_alt_signals/verify/verify_m1b.py

Allowed dependencies: lib/common.py (loaders, TABLES path) and lib/team_pipeline.py (verified port). Everything else is
rebuilt here: raw-file parsing of the measures, the CPI fix, the real-time lag, the Brown-leg residual, an independent
from-scratch Original-3m engine (z, past-only p80, crossings, holds, vol target, hedged P&L, turnover costs), a numpy
Newey-West regression, small-sample p-values, return-aligned ICs, Holm, the placebo rule, crossings and overlap.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, "/home/hashim/projects/GA/project/research/lib")
from common import load_team, RAW, TABLES  # noqa: E402
from team_pipeline import run_pipeline, team_controls  # noqa: E402

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
PFX = "M1b_alt_signals_"
ME = pd.offsets.MonthEnd(0)
VAL = ("2010-01-31", "2022-07-31")
HOLD0 = "2022-08-31"
COVID = ("2020-01-31", "2021-12-31")
SAMPLE_END = pd.Timestamp("2026-07-31")
FF3 = ["Mkt-RF", "SMB", "HML"]
SN = {"O3": "Original | Short Brown hold 3m", "P3": "Pure | Short Brown hold 3m", "O6": "Original | Short Brown hold 6m",
      "P6": "Pure | Short Brown hold 6m", "CR": "Continuous | raw attention", "CP": "Continuous | pure attention"}
SIGKEY = {"O3": "raw", "O6": "raw", "P3": "pure", "P6": "pure", "CR": "w_raw", "CP": "w_pure"}
ROWS = []


def rec(claim, name, mine, reported, tol, note=""):
    """Record one check. mine/reported numeric (or str/bool); tol absolute."""
    if isinstance(mine, (str, bool, np.bool_)) or isinstance(reported, (str, bool, np.bool_)):
        ok = str(mine) == str(reported)
        diff = np.nan
    elif not np.isfinite(float(reported)):
        diff, ok = np.nan, "info"
    else:
        diff = float(mine) - float(reported)
        ok = bool(np.isfinite(diff) and abs(diff) <= tol)
    ROWS.append({"claim": claim, "check": name, "mine": mine, "reported": reported, "abs_diff": diff, "tol": tol,
                 "ok": ok, "note": note})


# ============================================================================ 1. measures from raw files
def fred_raw(sid, how):
    d = pd.read_csv(RAW / f"fred_{sid}.csv")
    d.columns = ["date", "v"]
    d["v"] = pd.to_numeric(d["v"], errors="coerce")
    d["m"] = pd.to_datetime(d["date"]).dt.to_period("M")
    g = d.groupby("m")["v"].mean() if how == "mean" else d.dropna().groupby("m")["v"].last()
    g.index = g.index.to_timestamp(how="end").normalize()
    return g.astype(float)


mc = pd.read_csv(RAW / "mccc_monthly.csv", usecols=["Date", "Aggregate"])
MCCC = pd.Series(mc["Aggregate"].to_numpy(float), index=pd.to_datetime(mc["Date"]) + ME)
cpu_raw = pd.read_csv(RAW / "cpu_index.csv", header=None, skiprows=5, usecols=[0, 1], names=["d", "v"]).dropna()
CPU = pd.Series(cpu_raw["v"].to_numpy(float), index=pd.to_datetime(cpu_raw["d"], format="%b-%y") + ME)
MEAS = {"EMV_env": fred_raw("EMVENRGYENVREG", "last"), "MCCC": MCCC, "CPU": CPU, "VIX": fred_raw("VIXCLS", "mean"),
        "EMV_overall": fred_raw("EMVOVERALLEMV", "last")}
MEAS = {k: v.loc[:"2026-08-31"].dropna() for k, v in MEAS.items()}

rep_meas = pd.read_csv(TABLES / f"{PFX}measures_monthly.csv", parse_dates=["date"]).set_index("date")
for k, s in MEAS.items():
    r = rep_meas[k].dropna()
    rec("data", f"{k} range", f"{s.index.min():%Y-%m}..{s.index.max():%Y-%m}", f"{r.index.min():%Y-%m}..{r.index.max():%Y-%m}", 0)
    rec("data", f"{k} max abs diff vs measures_monthly.csv", float((s - r).abs().max()), 0.0, 1e-9)
T = load_team()
rec("data", "EMV_env == team attention (max abs diff)", float((MEAS["EMV_env"] - T["macro"]["attention"]).dropna().abs().max()), 0.0, 1e-9)
hz = MEAS["EMV_env"].loc[HOLD0:"2026-07-31"]
rec("data", "EMV_env zero share in holdout (claim 65%)", float((hz == 0).mean()), 0.65, 0.005)
for k in ("MCCC", "CPU", "VIX", "EMV_overall"):
    rec("data", f"{k} zero months (claim none)", int((MEAS[k] == 0).sum()), 0, 0)

# ============================================================================ 2. corrected-baseline inputs
MAC = T["macro"].copy()
cpi = MAC["cpi"].copy()
gap = cpi.loc["1990":].index[cpi.loc["1990":].isna()]
rec("timing", "number of CPI gaps after 1990 (claim 1: 2025-10)", len(gap), 1, 0, ", ".join(f"{d:%Y-%m}" for d in gap))
for d in gap:  # linear interpolation between neighbours (equal spacing)
    i = cpi.index.get_loc(d)
    cpi.iloc[i] = 0.5 * (cpi.iloc[i - 1] + cpi.iloc[i + 1])
MAC["cpi"] = cpi
GRID = pd.date_range("1985-01-31", "2026-08-31", freq="ME")


def inputs(m, timing):
    a = MEAS[m].reindex(pd.date_range(MEAS[m].index.min(), "2026-08-31", freq="ME"))
    a = a.loc[:MEAS[m].index.max()]
    ctrl = team_controls(MAC)
    if timing == "realtime":  # value for month t-1 known at the close of t; controls lagged too
        a = a.copy()
        a.index = a.index + pd.offsets.MonthEnd(1)
        ctrl = ctrl.shift(1)
    return a, ctrl


CHEAP = dict(bootstrap_reps=0, extras=False, paired=False, macro_states=False)
RUNS = {}
for m in MEAS:
    for tm in ("realtime", "same_month"):
        a, c = inputs(m, tm)
        RUNS[(m, tm)] = run_pipeline(macro=MAC, attention=a, controls=c, **CHEAP)
FF = T["ff3"]


# ============================================================================ 3. independent engine for Original-hold rules
def brown_model():
    ind, f = T["industries"], T["ff3"]
    y = ind[["Util", "Ships", "Aero", "Steel", "BldMt"]].mean(axis=1) - f["RF"]
    d = pd.concat([y.rename("y"), f[FF3]], axis=1).dropna()
    Y, X = d["y"].to_numpy(), d[FF3].to_numpy()
    n = len(d)
    B = np.full((n, 3), np.nan)
    A = np.full(n, np.nan)
    for e in range(59, n):
        Z = np.column_stack([np.ones(60), X[e - 59:e + 1]])
        c = np.linalg.lstsq(Z, Y[e - 59:e + 1], rcond=None)[0]
        A[e], B[e] = c[0], c[1:]
    B = pd.DataFrame(B, index=d.index, columns=FF3)
    A = pd.Series(A, index=d.index)
    hedged = d["y"] - (B.shift(1) * d[FF3]).sum(axis=1, min_count=3)
    eps = hedged - A.shift(1)
    return d["y"], B, hedged, eps


Y, BETA, HEDGED, EPS = brown_model()
EPS_P = RUNS[("EMV_env", "realtime")]["models"]["Brown leg"]["epsilon"]
rec("engine", "Brown-leg residual, mine vs pipeline (max abs diff)", float((EPS - EPS_P).dropna().abs().max()), 0.0, 1e-10)


def my_z(att):
    x = np.log1p(att.reindex(pd.date_range(att.index.min(), "2026-08-31", freq="ME")))
    mu = x.rolling(60, min_periods=36).mean()
    sd = x.rolling(60, min_periods=36).std(ddof=1).replace(0, np.nan)
    return (x - mu) / sd


def my_state(z):
    v = z.to_numpy()
    st = np.zeros(len(v), bool)
    thr = np.full(len(v), np.nan)
    for i in range(len(v)):
        past = v[:i][~np.isnan(v[:i])]
        if len(past) >= 60:
            thr[i] = np.quantile(past, 0.80)
            st[i] = (not np.isnan(v[i])) and v[i] > thr[i]
    return pd.Series(st, index=z.index), pd.Series(thr, index=z.index)


def my_original(att, hold):
    z = my_z(att)
    st, _ = my_state(z)
    cross = st & ~st.shift(1, fill_value=False)
    holdS = cross.astype(int).rolling(hold, min_periods=1).max().astype(bool)
    sig = EPS.rolling(36, min_periods=36).std(ddof=1)
    mag = np.minimum(1.0, 0.05 / (np.sqrt(12) * sig))
    idx = EPS.index[EPS.index >= sig.first_valid_index()]
    h = pd.Series(np.where(holdS.reindex(idx, fill_value=False), -mag.reindex(idx), 0.0), index=idx)
    b = BETA.reindex(idx)
    f = FF[FF3].reindex(idx)
    gross = h.shift(1) * (Y.reindex(idx) - (b.shift(1) * f).sum(axis=1))
    ov = -b.mul(h, axis=0)
    ato = h.diff().abs().fillna(h.abs())
    oto = ov.diff().abs().fillna(ov.abs())
    cost = 10e-4 * ato + 5e-4 * oto["Mkt-RF"] + 25e-4 * (oto["SMB"] + oto["HML"])
    net = gross - cost.shift(1).fillna(0)
    return pd.DataFrame({"position": h, "net": net, "cross": cross.reindex(idx, fill_value=False)}), z, cross


MY = {}
for m in ("MCCC", "CPU", "EMV_env", "VIX", "EMV_overall"):
    a, _ = inputs(m, "realtime")
    for hold, code in ((3, "O3"), (6, "O6")):
        df, z, cr = my_original(a, hold)
        MY[(m, code)] = df
        pipe = RUNS[(m, "realtime")]["strategies"][SN[code]]["net_return"]
        dd = (df["net"] - pipe).loc["1990":"2026-07"].abs().max()
        rec("engine", f"{m} {code} realtime net return, from-scratch engine vs pipeline (max abs diff)", float(dd), 0.0, 1e-10)
    zp = RUNS[(m, "realtime")]["signals"]["raw"]
    rec("engine", f"{m} realtime z, mine vs pipeline (max abs diff)", float((z - zp).dropna().abs().max()), 0.0, 1e-10)
    # look-ahead: my realtime z at t must equal same-month z at t-1
    zs = RUNS[(m, "same_month")]["signals"]["raw"]
    rec("timing", f"{m} realtime z_t == same-month z_(t-1) (max abs diff)", float((zp - zs.shift(1)).dropna().abs().max()), 0.0, 1e-10)


# ============================================================================ 4. statistics (own NW, own p-values)
def nw(y, X, lags=6):
    d = pd.concat([y.rename("y"), X], axis=1).dropna()
    Z = np.column_stack([np.ones(len(d)), d[X.columns].to_numpy()])
    yy = d["y"].to_numpy()
    inv = np.linalg.pinv(Z.T @ Z)
    b = inv @ Z.T @ yy
    u = yy - Z @ b
    xu = Z * u[:, None]
    S = xu.T @ xu
    for L in range(1, min(lags, len(d) - 1) + 1):
        G = xu[L:].T @ xu[:-L]
        S += (1 - L / (lags + 1)) * (G + G.T)
    se = np.sqrt(np.diag(inv @ S @ inv))
    return b, b / se, len(d)


def pval(t, n, k):
    return 2 * stats.t.sf(abs(t), n - k) if n < 60 else 2 * stats.norm.sf(abs(t))


def alpha(r, a, b):
    s = r.loc[a:b].dropna()
    bb, tt, n = nw(s, FF[FF3].reindex(s.index))
    return 12 * bb[0], tt[0], n, pval(tt[0], n, 4), 12 * s.mean()


def ic(sig, a, b):
    """(signal_t, eps_{t+1}) with t+1 in [a, b]."""
    d = pd.concat([sig.rename("x"), EPS.shift(-1).rename("y")], axis=1).dropna()
    d = d.loc[pd.Timestamp(a) - pd.offsets.MonthEnd(1):pd.Timestamp(b) - pd.offsets.MonthEnd(1)]
    zx = (d["x"] - d["x"].mean()) / d["x"].std(ddof=1)
    zy = (d["y"] - d["y"].mean()) / d["y"].std(ddof=1)
    bb, tt, n = nw(zy, zx.to_frame("x"))
    return bb[1], tt[1], n, pval(tt[1], n, 2)


def holm(p):
    p = np.asarray(p, float)
    o = np.argsort(p)
    adj = np.empty_like(p)
    run = 0.0
    for r, i in enumerate(o):
        run = max(run, (len(p) - r) * p[i])
        adj[i] = min(run, 1.0)
    return adj


END = {m: min(MEAS[m].index.max() + pd.offsets.MonthEnd(1), SAMPLE_END) for m in MEAS}
rec("windows", "MCCC holdout end (claim 2025-07)", f"{END['MCCC']:%Y-%m}", "2025-07", 0)
rec("windows", "CPU holdout end (claim 2025-10)", f"{END['CPU']:%Y-%m}", "2025-10", 0)


def net(m, tm, code):
    return RUNS[(m, tm)]["strategies"][SN[code]]["net_return"]


# ---- 4a. Q1 primary family (40 tests)
prim_rep = pd.read_csv(TABLES / f"{PFX}primary.csv")
prim_rep = prim_rep[prim_rep.family == "primary"].set_index("test_id")
P = []
for m in ("MCCC", "CPU"):
    for code in SN:
        for per, (a, b) in (("validation", VAL), ("holdout", (HOLD0, END[m]))):
            al, t, n, p, _ = alpha(net(m, "realtime", code), a, b)
            P.append((f"Q1_{m}_realtime_{code}_{per}_alpha", al, t, n, p, "alpha", per))
    for key in ("raw", "pure", "w_raw", "w_pure"):
        for per, (a, b) in (("validation", VAL), ("holdout", (HOLD0, END[m]))):
            c, t, n, p = ic(RUNS[(m, "realtime")]["signals"][key], a, b)
            P.append((f"Q1_{m}_realtime_{key}_{per}_IC", c, t, n, p, "IC", per))
PR = pd.DataFrame(P, columns=["test_id", "est", "t", "n", "p", "kind", "per"]).set_index("test_id")
PR["holm"] = holm(PR["p"])
rec("Q1", "primary family size", len(PR), len(prim_rep), 0)
j = PR.join(prim_rep[["estimate", "t", "p", "n", "holm_p"]], rsuffix="_rep")
rec("Q1", "max |estimate diff| over 40 primary tests", float((j.est - j.estimate).abs().max()), 0.0, 1e-9)
rec("Q1", "max |t diff| over 40 primary tests", float((j.t - j.t_rep).abs().max()), 0.0, 1e-8)
rec("Q1", "max |p diff| over 40 primary tests", float((j.p - j.p_rep).abs().max()), 0.0, 1e-8)
rec("Q1", "n matches for all 40 tests", bool((j.n == j.n_rep).all()), True, 0)
rec("Q1", "min Holm p (claim 1.00)", float(PR.holm.min()), 1.0, 1e-9)
rec("Q1", "min raw p (claim 0.033, MCCC purified holdout IC)", float(PR.p.min()), 0.033, 0.0005, PR.p.idxmin())
x = PR.loc["Q1_MCCC_realtime_pure_holdout_IC"]
rec("Q1", "MCCC purified holdout IC (claim +0.163)", x.est, 0.163, 0.0005)
rec("Q1", "MCCC purified holdout IC t (claim 2.22)", x.t, 2.22, 0.005)
dec = PR[(PR.kind == "alpha") & (PR.per == "holdout") & (PR.est > 0) & (PR.holm < 0.05)]
rec("Q1", "decision (claim unchanged)", "changes" if len(dec) else "unchanged", "unchanged", 0)
mh = PR[(PR.kind == "alpha") & (PR.per == "holdout") & PR.index.str.contains("MCCC")]
rec("Q1", "MCCC holdout alphas all negative (6 of 6)", int((mh.est < 0).sum()), 6, 0)
rec("Q1", "MCCC holdout alpha min (claim -2.91%)", 100 * mh.est.min(), -2.91, 0.005)
rec("Q1", "MCCC holdout alpha max (claim -0.56%)", 100 * mh.est.max(), -0.56, 0.005)
rec("Q1", "MCCC holdout t min (claim -1.95)", mh.t.min(), -1.95, 0.005)
rec("Q1", "MCCC holdout t max (claim -1.31)", mh.t.max(), -1.31, 0.005)
ch = PR[(PR.kind == "alpha") & (PR.per == "holdout") & PR.index.str.contains("CPU")]
rec("Q1", "CPU holdout alpha min (claim -1.62%)", 100 * ch.est.min(), -1.62, 0.005)
rec("Q1", "CPU holdout alpha max (claim +0.36%)", 100 * ch.est.max(), 0.36, 0.005)
rec("Q1", "CPU holdout n (claim 39)", int(ch.n.iloc[0]), 39, 0)
rec("Q1", "MCCC holdout n (claim 36)", int(mh.n.iloc[0]), 36, 0)

# ---- 4b. validation counts incl. EMV_env reference
for m, claim in (("EMV_env", 4), ("MCCC", 0), ("CPU", 0)):
    ts = [alpha(net(m, "realtime", c), *VAL) for c in SN]
    rec("Q1", f"{m} validation alphas with t>=1.96 (claim {claim})", sum(1 for r in ts if r[0] > 0 and r[1] >= 1.96), claim, 0)
    rec("Q1", f"{m} mean validation alpha (%)", 100 * np.mean([r[0] for r in ts]),
        {"EMV_env": 1.45, "MCCC": 0.34, "CPU": 0.88}[m], 0.005)
al, t, *_ = alpha(net("CPU", "realtime", "O6"), *VAL)
rec("Q1", "CPU O6 validation alpha (claim 1.81%)", 100 * al, 1.81, 0.005)
rec("Q1", "CPU O6 validation t (claim 1.73)", t, 1.73, 0.005)
al, t, *_ = alpha(net("EMV_env", "realtime", "O3"), *VAL)
rec("Q1", "EMV_env O3 validation alpha, corrected baseline (claim 1.62%)", 100 * al, 1.62, 0.005)
rec("Q1", "EMV_env O3 validation t, corrected baseline (claim 1.97)", t, 1.97, 0.005)
for m, a, b, ca, ct in (("EMV_env", HOLD0, "2025-07-31", -1.17, -2.08), ("EMV_env", HOLD0, "2025-10-31", -1.04, -1.97),
                        ("EMV_env", HOLD0, "2026-07-31", -2.16, -1.90)):
    al, t, n, *_ = alpha(net(m, "realtime", "O3"), a, b)
    rec("Q1", f"EMV_env O3 alpha {a[:7]}..{b[:7]} (claim {ca}%)", 100 * al, ca, 0.005)
    rec("Q1", f"EMV_env O3 t {a[:7]}..{b[:7]} (claim {ct})", t, ct, 0.005)

# ---- 4c. z correlations (realtime z vs EMV_env realtime z, 2010 onward)
ze = RUNS[("EMV_env", "realtime")]["signals"]["raw"]
for m, claim in (("MCCC", -0.07), ("CPU", 0.10), ("VIX", 0.14), ("EMV_overall", 0.39)):
    zz = pd.concat([RUNS[(m, "realtime")]["signals"]["raw"], ze], axis=1).loc["2010-01-31":MEAS[m].index.max()].dropna()
    rec("Q1", f"corr(z_{m}, z_EMV_env) post-2010 (claim {claim})", float(zz.corr().iloc[0, 1]), claim, 0.005)

# ============================================================================ 5. Q2 placebo / COVID
cov = {}
for tm in ("realtime", "same_month"):
    for m in ("EMV_env", "VIX", "EMV_overall", "CPU", "MCCC"):
        for code in SN:
            cov[(tm, m, code)] = alpha(net(m, tm, code), *COVID)
REPC = pd.read_csv(TABLES / f"{PFX}placebo_covid.csv")
mx = 0.0
for (tm, m, code), r in cov.items():
    q = REPC[(REPC.timing == tm) & (REPC.measure == m) & (REPC.strategy == code)].iloc[0]
    mx = max(mx, abs(r[0] - q.alpha_ann), abs(r[1] - q.t) / 100)
rec("Q2", "max diff COVID alpha (and t/100) over 60 cells vs placebo_covid.csv", mx, 0.0, 1e-9)
for tm, claims in (("realtime", {"VIX": 3, "EMV_overall": 4}), ("same_month", {"VIX": 3, "EMV_overall": 6})):
    for m, cl in claims.items():
        k = 0
        for code in SN:
            e, pl = cov[(tm, "EMV_env", code)][0], cov[(tm, m, code)][0]
            k += int(e > 0 and pl > 0 and pl >= 0.5 * e)
        rec("Q2", f"{m} reproduces COVID gain, {tm} (claim {cl} of 6)", k, cl, 0)
for m, ca, ct in (("EMV_env", 6.38, 3.62), ("VIX", 2.41, 2.03), ("EMV_overall", 1.65, 1.29), ("CPU", 6.44, 4.46)):
    r = cov[("realtime", m, "O3")]
    rec("Q2", f"{m} O3 COVID alpha realtime (claim {ca}%)", 100 * r[0], ca, 0.005)
    rec("Q2", f"{m} O3 COVID t realtime (claim {ct})", r[1], ct, 0.005)
rec("Q2", "COVID n and df (claim 24, t(20))", cov[("realtime", "EMV_env", "O3")][2], 24, 0)
# paired tests and Holm within the 12 realtime paired placebo tests
pp = []
for m in ("VIX", "EMV_overall"):
    for code in SN:
        d = (net("EMV_env", "realtime", code) - net(m, "realtime", code)).loc[COVID[0]:COVID[1]]
        b, t, n = nw(d, FF[FF3].reindex(d.index))
        pp.append((m, code, 12 * b[0], t[0], pval(t[0], n, 4)))
pp = pd.DataFrame(pp, columns=["m", "code", "a", "t", "p"])
pp["holm"] = holm(pp.p)
rec("Q2", "min Holm p, 12 realtime paired placebo tests (claim 0.051)", float(pp.holm.min()), 0.051, 0.0005)
x = pp[(pp.m == "EMV_overall") & (pp.code == "O3")].iloc[0]
rec("Q2", "EMV_env - EMV_overall O3 COVID diff alpha t (claim 3.22)", x.t, 3.22, 0.005)
# always-short benchmark (from scratch)
sig = EPS.rolling(36, min_periods=36).std(ddof=1)
mag = np.minimum(1.0, 0.05 / (np.sqrt(12) * sig))
idx = EPS.index[EPS.index >= sig.first_valid_index()]
h = -mag.reindex(idx)
bf = BETA.reindex(idx)
gross = h.shift(1) * HEDGED.reindex(idx)
ov = -bf.mul(h, axis=0)
cost = 10e-4 * h.diff().abs().fillna(h.abs()) + 5e-4 * ov["Mkt-RF"].diff().abs().fillna(ov["Mkt-RF"].abs()) \
    + 25e-4 * (ov[["SMB", "HML"]].diff().abs().fillna(ov[["SMB", "HML"]].abs()).sum(axis=1))
bench = gross - cost.shift(1).fillna(0)
ba, bt, bn, bp, bnet = alpha(bench, *COVID)
rec("Q2", "always-short Brown COVID alpha (claim 4.54%)", 100 * ba, 4.54, 0.005)
rec("Q2", "always-short Brown COVID t (claim 1.96)", bt, 1.96, 0.005)
rec("Q2", "always-short Brown COVID net (claim 6.87%)", 100 * bnet, 6.87, 0.005)
rec("Q2", "benchmark alpha / EMV_env O3 realtime alpha (claim 71%)", ba / cov[("realtime", "EMV_env", "O3")][0], 0.71, 0.005)
# team baseline reference (write-up)
tb = run_pipeline(**CHEAP)["strategies"][SN["O3"]]["net_return"]
a_, t_, n_, p_, net_ = alpha(tb, *COVID)
rec("Q2", "team baseline O3 COVID alpha (write-up 6.03%)", 100 * a_, 6.03, 0.005)
rec("Q2", "team baseline O3 COVID t (write-up 3.21)", t_, 3.21, 0.005)
rec("Q2", "team baseline O3 COVID p with t(20) (not in FINDINGS; audit says none survive)", p_, np.nan, np.inf)

# ---- Mar-Apr 2020
rec("Q2", "Brown residual 2020-03 (claim -3.33%)", 100 * EPS.loc["2020-03-31"], -3.33, 0.005)
rec("Q2", "Brown residual 2020-04 (claim -5.91%)", 100 * EPS.loc["2020-04-30"], -5.91, 0.005)
eo3 = net("EMV_env", "realtime", "O3").loc[COVID[0]:COVID[1]]
crash = eo3.loc[["2020-03-31", "2020-04-30"]].sum()
rec("Q2", "EMV_env O3 COVID summed net (claim 16.08%)", 100 * eo3.sum(), 16.08, 0.005)
rec("Q2", "EMV_env O3 Mar+Apr 2020 net (claim 7.93%)", 100 * crash, 7.93, 0.005)
rec("Q2", "share Mar-Apr (claim 49%)", crash / eo3.sum(), 0.49, 0.005)
for m, ca, ct in (("EMV_env", 3.48, 2.68), ("CPU", 3.81, 2.44), ("VIX", 2.20, 1.25), ("EMV_overall", 1.18, 0.67)):
    r = net(m, "realtime", "O3").drop(pd.to_datetime(["2020-03-31", "2020-04-30"]))
    al, t, n, *_ = alpha(r, *COVID)
    rec("Q2", f"{m} O3 COVID alpha ex Mar-Apr (claim {ca}%)", 100 * al, ca, 0.005)
    rec("Q2", f"{m} O3 COVID t ex Mar-Apr (claim {ct})", t, ct, 0.005)
# which months did EMV_env O3 hold during COVID, realtime
held = MY[("EMV_env", "O3")]["position"].shift(1).loc[COVID[0]:COVID[1]]
rec("Q2", "EMV_env O3 realtime months held in COVID (placebo caveat says 13)", int((held != 0).sum()), 13, 0)
heldv = MY[("VIX", "O3")]["position"].shift(1).loc[COVID[0]:COVID[1]]
rec("Q2", "VIX O3 realtime months held in COVID (caveat says 6)", int((heldv != 0).sum()), 6, 0)
hw = held.loc["2020-01-31":"2020-06-30"]
rec("Q2", "EMV_env O3 realtime earned months Jan-Jun 2020 (claim: Dec-2019 crossing, traded close of Jan, held through Apr)",
    ",".join(f"{d:%Y-%m}" for d in hw.index[hw != 0]), "2020-01,2020-02,2020-03,2020-04", 0,
    "Jan-2020 is earned from the earlier Sep-2019 data-month crossing; the Dec-2019 crossing adds Feb-Apr")

# ============================================================================ 6. crossings (same-month runs, data month)
cr_rep = pd.read_csv(TABLES / f"{PFX}crossings.csv").set_index("measure")


def xdates(m, key="cross_raw"):
    c = RUNS[(m, "same_month")]["signals"][key]
    dend = min(MEAS[m].index.max(), SAMPLE_END)
    c = c.loc["2010-01-31":dend]
    return c.index[c.astype(bool)], dend


team, _ = xdates("EMV_env")
mi = lambda ix: np.asarray(ix.year * 12 + ix.month)  # noqa: E731
for m in ("EMV_env", "MCCC", "CPU", "VIX", "EMV_overall"):
    x, dend = xdates(m)
    tr = team[team <= dend]
    exact = int(np.isin(x, tr).sum())
    pm1 = int(sum(np.any(np.abs(mi(tr) - v) <= 1) for v in mi(x)))
    months = len(pd.date_range("2010-01-31", dend, freq="ME"))
    q = 1 - (1 - len(tr) / months) ** 3
    q_edge = np.mean([np.any(np.abs(mi(tr) - v) <= 1) for v in mi(pd.date_range("2010-01-31", dend, freq="ME"))])
    r = cr_rep.loc[m]
    rec("crossings", f"{m} raw crossings", len(x), int(r.n_cross_raw), 0)
    rec("crossings", f"{m} exact overlap", exact, int(r.overlap_exact), 0)
    rec("crossings", f"{m} +/-1m overlap", pm1, int(r.overlap_pm1), 0)
    rec("crossings", f"{m} chance +/-1m (module formula)", len(x) * q, float(r.expected_overlap_pm1_if_independent), 0.01)
    if m != "EMV_env":
        p1 = stats.binom.sf(pm1 - 1, len(x), q)
        p2 = stats.binom.sf(pm1 - 1, len(x), q_edge)
        rec("crossings", f"{m} binomial p (module formula)", p1, float(r.p_overlap_ge_observed_if_independent), 1e-6)
        rec("crossings", f"{m} binomial p with exact coverage share {q_edge:.3f} (sensitivity)", p2,
            float(r.p_overlap_ge_observed_if_independent), 0.02, "sensitivity only")
    cv = [d.strftime("%Y-%m") for d in x if pd.Timestamp("2019-11-30") <= d <= pd.Timestamp("2021-12-31")]
    rec("crossings", f"{m} crossings 2019-11..2021-12", ", ".join(cv), r.covid_crossings, 0)
# my own engine's crossings equal the pipeline's (same-month)
for m in ("MCCC", "CPU"):
    a, _ = inputs(m, "same_month")
    _, _, crs = my_original(a, 3)
    c1 = crs.loc["2010-01-31":].astype(bool)
    c2 = RUNS[(m, "same_month")]["signals"]["cross_raw"].reindex(c1.index).fillna(False).astype(bool)
    rec("crossings", f"{m} crossing dates, from-scratch vs pipeline (mismatches)", int((c1 != c2).sum()), 0, 0)

# ============================================================================ 7. text vs CSV spot checks
L = pd.read_csv(TABLES / f"{PFX}results_long.csv")


def g(m, tm, code, per, tr="log1p"):
    x = L[(L.measure == m) & (L.timing == tm) & (L.strategy == code) & (L.period == per) & (L["transform"] == tr)]
    return x.iloc[0]


x = g("MCCC", "realtime", "O3", "validation_live")
rec("text", "MCCC O3 validation_live alpha (claim 0.54%)", 100 * x.alpha_ann, 0.54, 0.005)
rec("text", "MCCC O3 validation_live n (claim 138)", x.n_months, 138, 0)
x = g("MCCC", "realtime", "P6", "validation_live")
rec("text", "MCCC P6 validation_live n (claim 78)", x.n_months, 78, 0)
rec("text", "MCCC P6 validation_live t (claim 0.10)", x.alpha_t_hac6, 0.10, 0.005)
sm = L[(L.timing == "same_month") & (L["transform"] == "log1p") & (L.measure == "MCCC") & (L.period == "holdout")]
rec("text", "MCCC same-month holdout alphas all negative", int((sm.alpha_ann < 0).sum()), 6, 0)
rec("text", "MCCC same-month P3 holdout t (claim -2.39)", g("MCCC", "same_month", "P3", "holdout").alpha_t_hac6, -2.39, 0.005)
eo = L[(L.measure == "EMV_overall") & (L.timing == "realtime") & (L["transform"] == "log1p") & (L.period == "validation")]
rec("text", "EMV_overall mean validation alpha (claim 1.07%)", 100 * eo.alpha_ann.mean(), 1.07, 0.005)
ph = L[L.measure.isin(["VIX", "EMV_overall"]) & (L.timing == "realtime") & (L["transform"] == "log1p") & (L.period == "holdout")]
rec("text", "VIX/EMV_overall holdout max |t| (claim 1.01)", float(ph.alpha_t_hac6.abs().max()), 1.01, 0.005)
p10 = L[(L.timing == "realtime") & (L["transform"] == "log1p") & (L.period == "post2010")]
for m, lo, hi, tmax in (("EMV_env", 0.24, 1.42, 1.65), ("MCCC", -0.27, 0.35, 0.51), ("CPU", -0.21, 1.23, 1.43)):
    s = p10[p10.measure == m]
    rec("text", f"{m} post2010 alpha min (claim {lo}%)", 100 * s.alpha_ann.min(), lo, 0.005)
    rec("text", f"{m} post2010 alpha max (claim {hi}%)", 100 * s.alpha_ann.max(), hi, 0.005)
    rec("text", f"{m} post2010 max |t| (claim {tmax})", float(s.alpha_t_hac6.abs().max()), tmax, 0.005)
for m, code, ca, cc in (("EMV_env", "O3", 5.1, 0.6), ("MCCC", "O3", 3.8, 0.4), ("CPU", "O3", 4.9, 0.5)):
    x = g(m, "realtime", code, "validation")
    rec("text", f"{m} {code} validation turnover x/yr (claim {ca})", x.annual_turnover, ca, 0.05)
    rec("text", f"{m} {code} validation cost drag % (claim {cc})", 100 * x.ann_cost_drag, cc, 0.05)
# recent windows reported? (brief requirement)
for m in ("EMV_env", "VIX", "EMV_overall"):
    for per in ("last12", "last18"):
        x = g(m, "realtime", "O3", per)
        rec("text", f"{m} O3 {per} realtime alpha % (NOT in FINDINGS text)", 100 * x.alpha_ann, np.nan, np.inf,
            f"t={x.alpha_t_hac6:.2f}, n={int(x.n_months)}, p={x.p_alpha:.3f}")
fp = pd.read_csv(TABLES / f"{PFX}full_mode_paired.csv")
print(fp[fp.measure == "MCCC"].to_string())

# ============================================================================ 7b. look-ahead fuzz and more timing checks
for m in ("MCCC", "CPU"):
    for key in ("pure", "w_raw", "w_pure"):
        rt = RUNS[(m, "realtime")]["signals"][key]
        sm_ = RUNS[(m, "same_month")]["signals"][key]
        rec("timing", f"{m} realtime {key}_t == same-month {key}_(t-1) (max abs diff)",
            float((rt - sm_.shift(1)).dropna().abs().max()), 0.0, 1e-9)
rng = np.random.default_rng(7)
for m in ("MCCC", "CPU"):
    for cut in ("2014-06-30", "2018-01-31", "2021-03-31"):
        a, c = inputs(m, "realtime")
        # perturb the measure for data months >= cut (realtime index is data month + 1) and all macro inputs >= cut
        a2 = a.copy()
        msk = a2.index >= pd.Timestamp(cut) + pd.offsets.MonthEnd(1)
        a2[msk] = a2[msk] * rng.uniform(0.2, 5.0, msk.sum())
        mac2 = MAC.copy()
        mm = mac2.index >= pd.Timestamp(cut)
        for col in ("rate10y", "wti", "cpi", "activity"):
            mac2.loc[mm, col] = mac2.loc[mm, col] * rng.uniform(0.8, 1.25, mm.sum())
        c2 = team_controls(mac2).shift(1)
        r2 = run_pipeline(macro=mac2, attention=a2, controls=c2, **CHEAP)
        # data through cut-1 month is unchanged -> positions through close of cut unchanged -> returns through cut+1 unchanged
        lim = pd.Timestamp(cut) + pd.offsets.MonthEnd(1)
        mx_ = 0.0
        for code in SN:
            d_ = (r2["strategies"][SN[code]]["net_return"] - net(m, "realtime", code)).loc[:lim].abs().max()
            mx_ = max(mx_, float(d_))
        rec("timing", f"{m} fuzz after {cut[:7]}: max change in net returns through {lim:%Y-%m}, 6 strategies", mx_, 0.0, 0.0)
        after = max(float((r2["strategies"][SN[c_]]["net_return"] - net(m, "realtime", c_)).loc[lim + pd.offsets.MonthEnd(1):END[m]].abs().max()) for c_ in SN)
        rec("timing", f"{m} fuzz after {cut[:7]}: returns after {lim:%Y-%m} do change (non-vacuous test)", bool(after > 0), True, 0)

# ---- COVID decomposition under team timing and the signal-free benchmark ex-crash (context the text omits)
CR2 = pd.to_datetime(["2020-03-31", "2020-04-30"])
e_sm = net("EMV_env", "same_month", "O3").loc[COVID[0]:COVID[1]]
rec("Q2", "team-timing EMV_env O3: Mar+Apr share of COVID net (not in FINDINGS)", float(e_sm.loc[CR2].sum() / e_sm.sum()), np.nan, np.inf,
    "under team timing only Mar-2020 is held")
al, t, n, *_ = alpha(net("EMV_env", "same_month", "O3").drop(CR2), *COVID)
rec("Q2", "team-timing EMV_env O3 COVID alpha ex Mar-Apr (not in FINDINGS)", 100 * al, np.nan, np.inf, f"t={t:.2f}, n={n}")
al, t, n, *_ = alpha(bench.drop(CR2), *COVID)
rec("Q2", "always-short Brown COVID alpha ex Mar-Apr (not in FINDINGS)", 100 * al, np.nan, np.inf, f"t={t:.2f}, n={n}")

# ---- more text-vs-CSV checks (robustness paragraphs)
def rng_(m, tm, per, tr="log1p", col="alpha_ann"):
    x = L[(L.measure == m) & (L.timing == tm) & (L.period == per) & (L["transform"] == tr)]
    return x[col]
rec("text", "MCCC same-month validation max t (claim 1.59)", float(rng_("MCCC", "same_month", "validation", col="alpha_t_hac6").max()), 1.59, 0.005)
rec("text", "CPU same-month validation O6 alpha (claim 1.86%)", 100 * g("CPU", "same_month", "O6", "validation").alpha_ann, 1.86, 0.005)
rec("text", "CPU same-month holdout max |t| (claim < 0.82)", float(rng_("CPU", "same_month", "holdout", col="alpha_t_hac6").abs().max()), 0.81, 0.01)
rec("text", "MCCC level validation max t (claim 0.62)", float(rng_("MCCC", "realtime", "validation", "none", "alpha_t_hac6").max()), 0.62, 0.005)
rec("text", "MCCC level holdout alpha min (claim -2.48%)", 100 * float(rng_("MCCC", "realtime", "holdout", "none").min()), -2.48, 0.005)
rec("text", "MCCC level holdout alpha max (claim -0.65%)", 100 * float(rng_("MCCC", "realtime", "holdout", "none").max()), -0.65, 0.005)
rec("text", "CPU level validation max t (claim 1.66)", float(rng_("CPU", "realtime", "validation", "none", "alpha_t_hac6").max()), 1.66, 0.005)
rec("text", "MCCC transition validation max |t| (claim 0.99)", float(rng_("MCCC_transition", "realtime", "validation", col="alpha_t_hac6").abs().max()), 0.99, 0.005)
rec("text", "EMV_env_share P6 validation t (claim 2.19)", g("EMV_env_share", "realtime", "P6", "validation").alpha_t_hac6, 2.19, 0.005)
rec("text", "EMV_overall O6 validation t (claim 2.05)", g("EMV_overall", "realtime", "O6", "validation").alpha_t_hac6, 2.05, 0.005)
rec("text", "EMV_env O3 full_live alpha (claim 0.44%)", 100 * g("EMV_env", "realtime", "O3", "full_live").alpha_ann, 0.44, 0.005)
rec("text", "CPU O3 full_live t (claim 0.52)", g("CPU", "realtime", "O3", "full_live").alpha_t_hac6, 0.52, 0.005)
dv = L[(L.period == "validation") & (L.timing == "realtime") & (L["transform"] == "log1p") & L.strategy.isin(["O3", "P3", "O6", "P6"])]
rec("text", "discrete-rule validation turnover min x/yr (claim 2)", float(dv.annual_turnover.min()), 2.0, 0.05, "all measures incl. robustness variants")
rec("text", "discrete-rule validation cost drag max % (claim <= 0.6)", 100 * float(dv.ann_cost_drag.max()), 0.6, 0.005)
BT = pd.read_csv(TABLES / f"{PFX}bootstrap.csv")
x = BT[(BT.measure == "MCCC") & (BT.strategy == "O3") & (BT.period == "holdout")].iloc[0]
rec("text", "MCCC O3 holdout bootstrap CI low (claim -5.41%)", 100 * x.ci_low, -5.41, 0.005)
rec("text", "MCCC O3 holdout bootstrap CI high (claim -0.29%)", 100 * x.ci_high, -0.29, 0.005)
x = BT[(BT.measure == "EMV_env") & (BT.strategy == "O3") & (BT.period == "holdout")].iloc[0]
rec("text", "EMV_env O3 holdout bootstrap mean (claim -2.57%)", 100 * x.mean_ann, -2.57, 0.005)
x = fp[(fp.measure == "MCCC") & fp.new.str.startswith("Continuous | raw") & fp.benchmark.str.contains("hold 3m")].iloc[0]
rec("text", "MCCC CR minus O3 holdout paired bootstrap (claim +1.82%, Holm 0.048)", 100 * x.mean_ann, 1.82, 0.005, f"holm={x.holm_p}")
FMC = pd.read_csv(TABLES / f"{PFX}full_mode_comparison.csv")
flag = FMC[FMC.significant_after_multiple_testing.astype(str) == "True"]
rec("outputs", "rows flagged significant_after_multiple_testing in full_mode_comparison.csv (normal-p COVID Holm, audit item 3)",
    len(flag), 0, 0, "; ".join(flag.measure + " " + flag.strategy))

# ============================================================================ 8. ledger
LED = pd.read_csv(TABLES / f"{PFX}tests_ledger.csv")
rec("ledger", "rows (claim 1664)", len(LED), 1664, 0)
vc = LED.primary_or_exploratory.value_counts().to_dict()
for k, v in (("primary", 40), ("placebo", 88), ("reference", 70), ("robustness", 1052), ("exploratory", 414)):
    rec("ledger", f"kind {k} count (claim {v})", vc.get(k, 0), v, 0)
rec("ledger", "all 40 primary test ids present", int(LED.test_id.isin(PR.index).sum()), 40, 0)
rec("ledger", "paired-bootstrap (full-mode) tests in ledger; FINDINGS 8 cites MCCC CR-O3 Holm p 0.048",
    int(LED.statistic_name.str.contains("paired", case=False).sum()), len(fp), 0,
    "full_mode_paired.csv rows vs ledger rows with a paired-bootstrap statistic")
rec("ledger", "p-values non-missing for all rows", int(LED.p_value_two_sided.isna().sum()), 0, 0)

OUT = pd.DataFrame(ROWS)
OUT.to_csv(HERE / "verify_results.csv", index=False)
pd.set_option("display.width", 250)
pd.set_option("display.max_colwidth", 90)
pd.set_option("display.max_rows", 400)
print(OUT[["claim", "check", "mine", "reported", "ok", "note"]].to_string())
print(f"\n{int((OUT.ok == True).sum())} of {int((OUT.ok != 'info').sum())} checks within tolerance; {int((OUT.ok == 'info').sum())} info rows")
print(pp.round(4).to_string())
