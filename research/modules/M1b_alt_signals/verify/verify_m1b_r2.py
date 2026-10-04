"""ROUND 2 independent verification of M1b_alt_signals (does NOT import modules/M1b_alt_signals/helpers.py or run.py).

Run: cd /home/hashim/projects/GA/project/research && uv run python modules/M1b_alt_signals/verify/verify_m1b_r2.py
Output: verify/verify_results_r2.csv (round-1 output verify_results.csv is left untouched).

Round 2 = the round-1 script (verify_m1b.py) with its claims updated to the corrected FINDINGS text and its column
names updated to the revised outputs, plus section 9 (new checks for every number that changed or was added).
Text tables of the corrected FINDINGS are parsed from a scratch copy (FINDINGS_TXT) and compared cell by cell.

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
# round 2: the two robustness variants, rebuilt from raw
_mt = pd.read_csv(RAW / "mccc_monthly.csv")
_TOP = ["Climate Legislation/Regulations", "Carbon Tax", "Carbon Credits Market", "Renewable Energy", "Agreements/Actions"]
MEAS["MCCC_transition"] = pd.Series(_mt[_TOP].mean(axis=1).to_numpy(float), index=pd.to_datetime(_mt["Date"]) + ME).dropna()
_sh = (MEAS["EMV_env"] / MEAS["EMV_overall"]).dropna()
MEAS["EMV_env_share"] = _sh.loc[:"2026-08-31"]

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


def binom_two_sided(k, n, p):
    """Exact two-sided binomial p: sum of P(X=j) over j with P(X=j) <= P(X=k) (own implementation)."""
    pm = stats.binom.pmf(np.arange(n + 1), n, p)
    return float(min(1.0, pm[pm <= pm[k] * (1 + 1e-7)].sum()))


CROSS_MINE = {}
for m in ("EMV_env", "MCCC", "CPU", "VIX", "EMV_overall", "EMV_env_share", "MCCC_transition"):
    x, dend = xdates(m)
    tr = team[team <= dend]
    exact = int(np.isin(x, tr).sum())
    pm1 = int(sum(np.any(np.abs(mi(tr) - v) <= 1) for v in mi(x)))
    grid = pd.date_range("2010-01-31", dend, freq="ME")
    months = len(grid)
    cover = np.array([np.any(np.abs(mi(tr) - v) <= 1) for v in mi(grid)])
    q_edge = float(cover.mean())
    # own circular shift: rotate the measure's crossing positions by s = 1..M-1 (module convention) and also with s = 0
    pos = np.searchsorted(grid, x)
    sh = np.array([cover[(pos + s) % months].sum() for s in range(months)])
    perm_excl, perm_incl = sh[1:], sh
    p_perm1 = float((perm_excl >= pm1).mean())
    p_perm1_incl = float((perm_incl >= pm1).mean())
    p_perm2 = float(min(1.0, 2 * min((perm_excl >= pm1).mean(), (perm_excl <= pm1).mean())))
    # own Jaccard of 3-month hold months (data-month holds), same-month runs
    c_m = RUNS[(m, "same_month")]["signals"]["cross_raw"].reindex(grid).fillna(False).astype(int)
    c_t = RUNS[("EMV_env", "same_month")]["signals"]["cross_raw"].reindex(grid).fillna(False).astype(int)
    h_m = c_m.rolling(3, min_periods=1).max().astype(bool)
    h_t = c_t.rolling(3, min_periods=1).max().astype(bool)
    jac = float((h_m & h_t).sum() / max((h_m | h_t).sum(), 1))
    r = cr_rep.loc[m]
    CROSS_MINE[m] = dict(n=len(x), exact=exact, pm1=pm1, chance=len(x) * q_edge, q=q_edge,
                         p1=float(stats.binom.sf(pm1 - 1, len(x), q_edge)), p2=binom_two_sided(pm1, len(x), q_edge),
                         pp1=p_perm1, pp1_incl=p_perm1_incl, pp2=p_perm2, jac=jac,
                         val=int(((x >= VAL[0]) & (x <= VAL[1])).sum()), hold=int((x >= HOLD0).sum()),
                         covid=int(((x >= COVID[0]) & (x <= COVID[1])).sum()))
    cm = CROSS_MINE[m]
    rec("crossings", f"{m} raw crossings", len(x), int(r.n_cross_raw), 0)
    rec("crossings", f"{m} exact overlap", exact, int(r.overlap_exact), 0)
    rec("crossings", f"{m} +/-1m overlap", pm1, int(r.overlap_pm1), 0)
    rec("crossings", f"{m} coverage share (exact, own)", q_edge, float(r.coverage_share_pm1), 1e-12)
    rec("crossings", f"{m} chance +/-1m (exact share, own)", cm["chance"], float(r.expected_overlap_pm1_if_independent), 1e-9)
    rec("crossings", f"{m} val/hold/covid crossing counts", f"{cm['val']}/{cm['hold']}/{cm['covid']}",
        f"{int(r.n_cross_validation)}/{int(r.n_cross_holdout)}/{int(r.n_cross_covid)}", 0)
    rec("crossings", f"{m} Jaccard of 3m hold months (own)", jac, float(r.jaccard_hold3_months), 1e-9)
    if m != "EMV_env":
        rec("crossings", f"{m} binomial p one-sided (exact share, own)", cm["p1"], float(r.p_one_sided_binomial), 1e-9)
        rec("crossings", f"{m} binomial p two-sided (own pmf sum)", cm["p2"], float(r.p_two_sided_binomial), 1e-9)
        rec("crossings", f"{m} circular-shift p one-sided (own, shifts 1..M-1)", p_perm1, float(r.p_one_sided_circular_shift), 1e-12,
            f"including the identity shift: {p_perm1_incl:.4f}")
        rec("crossings", f"{m} circular-shift p two-sided (own)", p_perm2, float(r.p_two_sided_circular_shift), 1e-12)
        rec("crossings", f"{m} circular-shift mean overlap (own)", float(perm_excl.mean()), float(r.expected_overlap_pm1_circular_shift), 1e-9)
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
for m, code, ca, cc in (("EMV_env", "O3", 5.1, 0.56), ("MCCC", "O3", 3.8, 0.43), ("CPU", "O3", 4.9, 0.52), ("EMV_env", "P3", 5.8, 0.63)):
    x = g(m, "realtime", code, "validation")
    rec("text", f"{m} {code} validation turnover x/yr (claim {ca})", x.annual_turnover, ca, 0.05)
    rec("text", f"{m} {code} validation cost drag % (claim {cc})", 100 * x.ann_cost_drag, cc, 0.005)
# recent windows reported? (brief requirement)
for m in ("EMV_env", "VIX", "EMV_overall"):
    for per in ("last12", "last18"):
        x = g(m, "realtime", "O3", per)
        rec("text", f"{m} O3 {per} realtime alpha % in results_long (r2: compared with the text in section 9)", 100 * x.alpha_ann, np.nan, np.inf,
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
rec("Q2", "team-timing EMV_env O3: Mar+Apr share of COVID net (r2 claim 23%)", float(e_sm.loc[CR2].sum() / e_sm.sum()), 0.23, 0.005,
    "under team timing only Mar-2020 is held")
al, t, n, *_ = alpha(net("EMV_env", "same_month", "O3").drop(CR2), *COVID)
rec("Q2", "team-timing EMV_env O3 COVID alpha ex Mar-Apr (r2 claim 4.25%)", 100 * al, 4.25, 0.005, f"t={t:.2f}, n={n}")
rec("Q2", "team-timing EMV_env O3 COVID t ex Mar-Apr (r2 claim 2.41)", t, 2.41, 0.005)
al, t, n, *_ = alpha(bench.drop(CR2), *COVID)
rec("Q2", "always-short Brown COVID alpha ex Mar-Apr (r2 claim 3.06%)", 100 * al, 3.06, 0.005, f"t={t:.2f}, n={n}")
rec("Q2", "always-short Brown COVID t ex Mar-Apr (r2 claim 1.05)", t, 1.05, 0.005)

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
rec("text", "discrete-rule validation turnover min x/yr (r2 claim 1.7)", float(dv.annual_turnover.min()), 1.7, 0.05, "all measures incl. robustness variants")
rec("text", "discrete-rule validation turnover max x/yr (r2 claim 5.8)", float(dv.annual_turnover.max()), 5.8, 0.05)
dv5 = dv[dv.measure.isin(["EMV_env", "MCCC", "CPU", "VIX", "EMV_overall"])]
rec("text", "discrete-rule validation turnover min x/yr, team+primary+placebo (r2 claim 1.8)", float(dv5.annual_turnover.min()), 1.8, 0.05)
rec("text", "discrete-rule validation turnover max x/yr, team+primary+placebo (r2 claim 5.8)", float(dv5.annual_turnover.max()), 5.8, 0.05)
rec("text", "discrete-rule validation cost drag max % (r2 claim 0.63)", 100 * float(dv.ann_cost_drag.max()), 0.63, 0.005,
    str(dv.loc[dv.ann_cost_drag.idxmax(), ["measure", "strategy"]].tolist()))
dc = L[(L.period == "validation") & (L.timing == "realtime") & (L["transform"] == "log1p") & L.strategy.isin(["CR", "CP"])]
rec("text", "continuous validation turnover min x/yr (r2 claim 0.7)", float(dc.annual_turnover.min()), 0.7, 0.05)
rec("text", "continuous validation turnover max x/yr (r2 claim 1.5)", float(dc.annual_turnover.max()), 1.5, 0.05)
rec("text", "continuous validation cost drag min % (r2 claim 0.07)", 100 * float(dc.ann_cost_drag.min()), 0.07, 0.005)
rec("text", "continuous validation cost drag max % (r2 claim 0.16)", 100 * float(dc.ann_cost_drag.max()), 0.16, 0.005)
BT = pd.read_csv(TABLES / f"{PFX}bootstrap.csv")
x = BT[(BT.measure == "MCCC") & (BT.strategy == "O3") & (BT.period == "holdout")].iloc[0]
rec("text", "MCCC O3 holdout bootstrap CI low (claim -5.41%)", 100 * x.ci_low, -5.41, 0.005)
rec("text", "MCCC O3 holdout bootstrap CI high (claim -0.29%)", 100 * x.ci_high, -0.29, 0.005)
x = BT[(BT.measure == "EMV_env") & (BT.strategy == "O3") & (BT.period == "holdout")].iloc[0]
rec("text", "EMV_env O3 holdout bootstrap mean (claim -2.57%)", 100 * x.mean_ann, -2.57, 0.005)
x = fp[(fp.measure == "MCCC") & fp.new.str.startswith("Continuous | raw") & fp.benchmark.str.contains("hold 3m")].iloc[0]
rec("text", "MCCC CR minus O3 holdout paired bootstrap (claim +1.82%, Holm 0.048)", 100 * x.mean_ann, 1.82, 0.005, f"holm={x.holm_p}")
FMC = pd.read_csv(TABLES / f"{PFX}full_mode_comparison.csv")
rec("outputs", "full_mode_comparison.csv: invalid pipeline columns dropped (significant_after_multiple_testing, active_months_full)",
    int(sum(c in FMC.columns for c in ("significant_after_multiple_testing", "active_months_full"))), 0, 0)
rec("outputs", "full_mode_comparison.csv: months_held_full present", "months_held_full" in FMC.columns, True, 0)

# ============================================================================ 8. ledger
LED = pd.read_csv(TABLES / f"{PFX}tests_ledger.csv")
rec("ledger", "rows (r2 claim 1900)", len(LED), 1900, 0)
vc = LED.primary_or_exploratory.value_counts().to_dict()
for k, v in (("primary", 40), ("placebo", 88), ("reference", 82), ("robustness", 1102), ("exploratory", 588)):
    rec("ledger", f"kind {k} count (claim {v})", vc.get(k, 0), v, 0)
rec("ledger", "all 40 primary test ids present", int(LED.test_id.isin(PR.index).sum()), 40, 0)
rec("ledger", "paired-bootstrap (full-mode) tests in ledger; FINDINGS 8 cites MCCC CR-O3 Holm p 0.048",
    int(LED.test_id.str.startswith("FULLPAIR_").sum()), len(fp), 0,
    "full_mode_paired.csv rows vs ledger rows with a paired-bootstrap statistic")
rec("ledger", "p-values non-missing for all rows", int(LED.p_value_two_sided.isna().sum()), 0, 0)

# ============================================================================ 9. ROUND 2: every changed or new number in the corrected FINDINGS
import re  # noqa: E402

FINDINGS_TXT = Path("/tmp/claude-1000/-home-hashim-projects-GA/5d56c5f1-d319-48cb-b466-4daeaca6ed67/scratchpad/m1b_r2_findings_text.txt")
TXT = FINDINGS_TXT.read_text()
CODE = {"Original 3m": "O3", "Pure 3m": "P3", "Original 6m": "O6", "Pure 6m": "P6", "Continuous raw": "CR", "Continuous pure": "CP"}
TOL2 = 0.00501  # text rounds to 2 decimals


def table(tag):
    lines = TXT.splitlines()
    i = next(k for k, l_ in enumerate(lines) if l_.startswith("## ") and tag in l_)
    rows = []
    for l_ in lines[i + 1:]:
        if l_.startswith("|"):
            rows.append([c.strip() for c in l_.strip().strip("|").split("|")])
        elif rows:
            break
    return rows[0], rows[2:]


def at(c):
    m_ = re.match(r"^(-?\d+\.\d+) \((-?\d+\.\d+)\)$", c)
    return float(m_.group(1)), float(m_.group(2))


def half_unit(s):
    d = len(s.split(".")[1]) if "." in s else 0
    return 0.5 * 10 ** (-d) + 1e-9


def paired(r1, r2, a, b, drop=None):
    d = (r1 - r2)
    if drop is not None:
        d = d.drop(drop)
    d = d.loc[a:b].dropna()
    bb, tt, n = nw(d, FF[FF3].reindex(d.index))
    return 12 * bb[0], tt[0], n, pval(tt[0], n, 4)


# ---- 9a. section 5 primary table, 36 cells, own NW on pipeline nets built from own inputs
hdr, rows = table("5. Primary results")
cols = [("EMV_env", "val"), ("EMV_env", "hold"), ("MCCC", "val"), ("MCCC", "hold"), ("CPU", "val"), ("CPU", "hold")]
mx_a = mx_t = 0.0
for r in rows:
    code = CODE[r[0]]
    for (m, per), c in zip(cols, r[1:]):
        a_t, t_t = at(c)
        a, b = VAL if per == "val" else (HOLD0, END[m])
        al, t, *_ = alpha(net(m, "realtime", code), a, b)
        mx_a, mx_t = max(mx_a, abs(100 * al - a_t)), max(mx_t, abs(t - t_t))
rec("r2_text", "section 5 primary table: 36 cells, max |alpha% diff| (text 2 dp)", mx_a, 0.0, TOL2)
rec("r2_text", "section 5 primary table: 36 cells, max |t diff| (text 2 dp)", mx_t, 0.0, TOL2)

# ---- 9b. section 6 real-time COVID table incl. paired columns (48 cells), and team-timing table (24 cells)
hdr, rows = table("6 realtime")
mx_a = mx_t = 0.0
for r in rows:
    code = CODE[r[0]]
    for m, c in zip(("EMV_env", "VIX", "EMV_overall", "CPU", "MCCC"), r[1:6]):
        a_t, t_t = at(c)
        al, t = cov[("realtime", m, code)][:2]
        mx_a, mx_t = max(mx_a, abs(100 * al - a_t)), max(mx_t, abs(t - t_t))
    for m, c in zip(("VIX", "EMV_overall"), r[6:8]):
        a_t, t_t = at(c)
        al, t, n, p = paired(net("EMV_env", "realtime", code), net(m, "realtime", code), *COVID)
        mx_a, mx_t = max(mx_a, abs(100 * al - a_t)), max(mx_t, abs(t - t_t))
rec("r2_text", "section 6 real-time COVID table: 42 cells, max |alpha% diff|", mx_a, 0.0, TOL2)
rec("r2_text", "section 6 real-time COVID table: 42 cells, max |t diff|", mx_t, 0.0, TOL2)
hdr, rows = table("6 team")
mx_a = mx_t = 0.0
for r in rows:
    code = CODE[r[0]]
    for m, c in zip(("EMV_env", "VIX", "EMV_overall", "CPU"), r[1:5]):
        a_t, t_t = at(c)
        al, t = cov[("same_month", m, code)][:2]
        mx_a, mx_t = max(mx_a, abs(100 * al - a_t)), max(mx_t, abs(t - t_t))
rec("r2_text", "section 6 team-timing COVID table: 24 cells, max |alpha% diff|", mx_a, 0.0, TOL2)
rec("r2_text", "section 6 team-timing COVID table: 24 cells, max |t diff|", mx_t, 0.0, TOL2)

# ---- 9c. placebo rule details, ratios, reproduced strategy lists
for tm in ("realtime", "same_month"):
    for m in ("VIX", "EMV_overall"):
        lst = [c for c in SN if cov[(tm, "EMV_env", c)][0] > 0 and cov[(tm, m, c)][0] > 0
               and cov[(tm, m, c)][0] >= 0.5 * cov[(tm, "EMV_env", c)][0]]
        claim = {("realtime", "VIX"): "P6, CR, CP", ("realtime", "EMV_overall"): "O6, P6, CR, CP",
                 ("same_month", "VIX"): "P6, CR, CP", ("same_month", "EMV_overall"): "O3, P3, O6, P6, CR, CP"}[(tm, m)]
        rec("r2_Q2", f"{m} reproduced strategies, {tm}", ", ".join(lst), claim, 0)
ratio = lambda tm, m, c: cov[(tm, m, c)][0] / cov[(tm, "EMV_env", c)][0]  # noqa: E731
for tm, m, c, cl in (("realtime", "VIX", "O3", 0.38), ("realtime", "EMV_overall", "O3", 0.26), ("realtime", "VIX", "P3", 0.08),
                     ("realtime", "EMV_overall", "P3", 0.40), ("same_month", "EMV_overall", "O3", 0.77),
                     ("same_month", "EMV_overall", "P3", 0.53), ("same_month", "VIX", "O3", 0.32), ("same_month", "VIX", "P3", 0.12),
                     ("same_month", "CPU", "O3", 1.05), ("realtime", "VIX", "CR", 0.62), ("realtime", "EMV_overall", "CR", 0.83),
                     ("realtime", "MCCC", "CR", 0.76), ("realtime", "CPU", "CR", 1.06)):
    rec("r2_Q2", f"ratio {m}/EMV_env COVID alpha, {c}, {tm} (claim {cl})", ratio(tm, m, c), cl, 0.005)
rec("r2_Q2", "VIX O6 same-month ratio (boundary case, not claimed)", ratio("same_month", "VIX", "O6"), np.nan, np.inf,
    "just below the 50% threshold")
for c, cl_t, cl_p in (("O6", 1.79, 0.089), ("P6", 1.96, 0.064)):
    r = cov[("realtime", "EMV_env", c)]
    rec("r2_Q2", f"EMV_env {c} realtime COVID t (claim {cl_t})", r[1], cl_t, 0.005)
    rec("r2_Q2", f"EMV_env {c} realtime COVID p t(20) (claim {cl_p})", r[3], cl_p, 0.0005)
rec("r2_Q2", "t(20) 97.5% critical value (claim 2.09)", stats.t.ppf(0.975, 20), 2.09, 0.005)
# team-timing paired tests (EMV env minus placebo) and the 'only under real-time timing' claim for the 3-month rules
ppt = []
for m in ("VIX", "EMV_overall"):
    for code in SN:
        al, t, n, p = paired(net("EMV_env", "same_month", code), net(m, "same_month", code), *COVID)
        ppt.append((m, code, al, t, p))
ppt = pd.DataFrame(ppt, columns=["m", "code", "a", "t", "p"])
x = ppt[(ppt.m == "EMV_overall") & (ppt.code == "O3")].iloc[0]
rec("r2_Q2", "team-timing EMV_env - EMV_overall O3 paired alpha (claim +1.39%)", 100 * x.a, 1.39, 0.005)
rec("r2_Q2", "team-timing EMV_env - EMV_overall O3 paired t (claim 0.87)", x.t, 0.87, 0.005)
s3 = ppt[ppt.code.isin(["O3", "P3"])]
rec("r2_Q2", "team-timing 3-month paired tests vs placebos with p < 0.05 (claim: none; significance only under real-time timing)",
    int((s3.p < 0.05).sum()), 0, 0, "; ".join(f"{a}-{b}: t={c:.2f}" for a, b, c in zip(s3.m, s3.code, s3.t)))
rec("r2_Q2", "team-timing paired tests, all 12, with p < 0.05 (info)", int((ppt.p < 0.05).sum()), np.nan, np.inf,
    "; ".join(f"{a}-{b}: t={c:.2f}" for a, b, c in zip(ppt.m, ppt.code, ppt.t)))
al, t, n, p = paired(net("EMV_env", "realtime", "O3"), net("CPU", "realtime", "O3"), *COVID)
rec("r2_Q2", "EMV_env - CPU O3 realtime COVID paired t (claim -0.06)", t, -0.06, 0.005)
rec("r2_Q2", "placebo_covid.csv holm_p_paired_placebo_family min (claim 0.051)", float(REPC.holm_p_paired_placebo_family.min()), 0.051, 0.0005)

# ---- 9d. always-short benchmark: paired tests (own benchmark, own NW) and share of EMV_env alpha
rec("r2_Q2", "always-short alpha / team-timing EMV_env O3 alpha (claim 75%)", ba / cov[("same_month", "EMV_env", "O3")][0], 0.75, 0.005)
for tm, m, per, cl_a, cl_t, cl_p in (("realtime", "EMV_env", "covid", 1.84, 0.87, 0.39), ("same_month", "EMV_env", "covid", 1.49, 0.45, None),
                                     ("realtime", "CPU", "covid", 1.90, 1.02, None), ("realtime", "EMV_env", "ex", 0.42, 0.18, None),
                                     ("realtime", "CPU", "ex", 0.75, 0.44, None)):
    al, t, n, p = paired(net(m, tm, "O3"), bench, *COVID, drop=CR2 if per == "ex" else None)
    rec("r2_Q2", f"{m} O3 {tm} minus always-short, {per}: alpha (claim {cl_a}%)", 100 * al, cl_a, 0.005, f"n={n}")
    rec("r2_Q2", f"{m} O3 {tm} minus always-short, {per}: t (claim {cl_t})", t, cl_t, 0.005)
    if cl_p is not None:
        rec("r2_Q2", f"{m} O3 {tm} minus always-short, {per}: p (claim {cl_p})", p, cl_p, 0.005)
# all 168 minus-benchmark cells in covid_decomposition.csv vs own
DEC = pd.read_csv(TABLES / f"{PFX}covid_decomposition.csv")
mxa = mxt = 0.0
nd = 0
ndeg = 0
for _, r in DEC[DEC.strategy != "AS"].iterrows():
    for per, drop in (("covid", None), ("ex_mar_apr", CR2)):
        d = (net(r.measure, r.timing, r.strategy) - bench)
        if drop is not None:
            d = d.drop(drop)
        d = d.loc[COVID[0]:COVID[1]].dropna()
        if float(d.abs().max()) < 1e-15:
            ndeg += 1
            ok_ = abs(r[f"minus_bench_alpha_{per}"]) < 1e-12 and not np.isfinite(r[f"minus_bench_t_{per}"])
            nd += 0 if ok_ else 1
            continue
        al, t, n, p = paired(net(r.measure, r.timing, r.strategy), bench, *COVID, drop=drop)
        mxa = max(mxa, abs(al - r[f"minus_bench_alpha_{per}"]))
        mxt = max(mxt, abs(t - r[f"minus_bench_t_{per}"]))
rec("r2_Q2", "covid_decomposition.csv minus-benchmark alphas, 168 cells, own vs CSV (max abs diff)", mxa, 0.0, 1e-10)
rec("r2_Q2", "covid_decomposition.csv minus-benchmark t, 168 cells, own vs CSV (max abs diff)", mxt, 0.0, 1e-8)
rec("r2_Q2", "degenerate minus-benchmark cells (identically 0 difference) (claim 2)", ndeg, 2, 0, f"mis-stored: {nd}")
# every covid_decomposition.csv row: summed net, Mar-Apr share, ex-crash alpha/t (feeds covid_attribution.tex)
mxd = 0.0
for _, r in DEC.iterrows():
    s_ = bench if r.strategy == "AS" else net(r.measure, r.timing, r.strategy)
    w_ = s_.loc[COVID[0]:COVID[1]]
    al, t, n, p, _ = alpha(s_.drop(CR2), *COVID)
    mxd = max(mxd, abs(w_.sum() - r.covid_sum_net), abs(w_.loc[CR2].sum() / w_.sum() - r.share_mar_apr),
              abs(al - r.alpha_ex_mar_apr), abs(t - r.t_ex_mar_apr) / 100, abs(n - r.n_ex))
rec("r2_Q2", "covid_decomposition.csv all 86 rows: sum, Mar-Apr share, ex-crash alpha/t/n own vs CSV (max scaled diff)", mxd, 0.0, 1e-10)
# EMV_env Pure 6m realtime is short in all 24 COVID months and identical to the benchmark
pos = RUNS[("EMV_env", "realtime")]["strategies"][SN["P6"]]["position"].shift(1).loc[COVID[0]:COVID[1]]
rec("r2_Q2", "EMV_env P6 realtime months short in COVID (claim 24)", int((pos != 0).sum()), 24, 0)
rec("r2_Q2", "EMV_env P6 realtime COVID net minus always-short (max abs diff)",
    float((net("EMV_env", "realtime", "P6") - bench).loc[COVID[0]:COVID[1]].abs().max()), 0.0, 1e-15)

# ---- 9e. attribution: held months, crossings, crash share under team timing, ex-crash table
held = MY[("EMV_env", "O3")]["position"].shift(1).loc["2019-10-31":"2020-06-30"]
rec("r2_Q2", "EMV_env O3 realtime return months held 2019-10..2020-06 (claim 2019-11..2020-04)",
    ",".join(f"{d:%Y-%m}" for d in held.index[held != 0]), "2019-11,2019-12,2020-01,2020-02,2020-03,2020-04", 0)
cr_rt = RUNS[("EMV_env", "same_month")]["signals"]["cross_raw"].loc["2019-06-30":"2020-03-31"]
rec("r2_Q2", "EMV_env crossings, data months 2019-06..2020-03 (claim 2019-09 and 2019-12)",
    ",".join(f"{d:%Y-%m}" for d in cr_rt.index[cr_rt.astype(bool)]), "2019-09,2019-12", 0)
p_sm = RUNS[("EMV_env", "same_month")]["strategies"][SN["O3"]]["position"].shift(1).loc["2019-10-31":"2020-06-30"]
rec("r2_Q2", "EMV_env O3 team timing return months held 2019-10..2020-05 (claim: Jan-Mar 2020 from the 2019-12 crossing)",
    ",".join(f"{d:%Y-%m}" for d in p_sm.loc[:"2020-05-31"].index[p_sm.loc[:"2020-05-31"] != 0]),
    "2019-10,2019-11,2019-12,2020-01,2020-02,2020-03", 0, "2019-09 crossing earns Oct-Dec 2019, 2019-12 crossing earns Jan-Mar 2020")
rec("r2_Q2", "EMV_env O3 team timing: Mar-2020 held, Apr-2020 not (claim)",
    f"{bool(p_sm.loc['2020-03-31'] != 0)},{bool(p_sm.loc['2020-04-30'] != 0)}", "True,False", 0)
e_sm = net("EMV_env", "same_month", "O3").loc[COVID[0]:COVID[1]]
rec("r2_Q2", "team timing EMV_env O3 Mar+Apr net (claim 2.71%)", 100 * e_sm.loc[CR2].sum(), 2.71, 0.005)
rec("r2_Q2", "team timing EMV_env O3 summed COVID net (claim 11.87%)", 100 * e_sm.sum(), 11.87, 0.005)
for m, tm, cl in (("VIX", "realtime", "False,True"), ("EMV_overall", "realtime", "False,True"), ("VIX", "same_month", "True,True"),
                  ("EMV_overall", "same_month", "True,True"), ("MCCC", "realtime", "True,True"), ("CPU", "realtime", "True,True")):
    pz = RUNS[(m, tm)]["strategies"][SN["O3"]]["position"].shift(1)
    rec("r2_Q2", f"{m} O3 {tm}: held Mar-2020, Apr-2020", f"{bool(pz.loc['2020-03-31'] != 0)},{bool(pz.loc['2020-04-30'] != 0)}", cl, 0)
for m, cl in (("CPU", "2019-12"), ("VIX", "2020-02"), ("EMV_overall", "2020-02")):
    cz = RUNS[(m, "same_month")]["signals"]["cross_raw"].loc["2019-10-31":"2020-02-29"]
    rec("r2_Q2", f"{m} first crossing data month 2019-10..2020-02 (claim {cl})",
        ",".join(f"{d:%Y-%m}" for d in cz.index[cz.astype(bool)]), cl, 0)
rec("r2_Q2", "MCCC O3 realtime COVID alpha (claim 1.63%)", 100 * cov[("realtime", "MCCC", "O3")][0], 1.63, 0.005)
rec("r2_Q2", "MCCC O3 realtime COVID t (claim 0.91)", cov[("realtime", "MCCC", "O3")][1], 0.91, 0.005)
hdr, rows = table("6 excrash")
mx_a = mx_t = 0.0
for r in rows:
    for tm, c in zip(("realtime", "same_month"), r[1:3]):
        a_t, t_t = at(c)
        if r[0].startswith("Always"):
            al, t, *_ = alpha(bench.drop(CR2), *COVID)
        else:
            m = {"EMV env.": "EMV_env", "CPU": "CPU", "VIX": "VIX", "EMV overall": "EMV_overall", "MCCC": "MCCC"}[r[0]]
            al, t, *_ = alpha(net(m, tm, "O3").drop(CR2), *COVID)
        mx_a, mx_t = max(mx_a, abs(100 * al - a_t)), max(mx_t, abs(t - t_t))
rec("r2_text", "section 6 ex-crash table: 12 cells, max |alpha% diff|", mx_a, 0.0, TOL2)
rec("r2_text", "section 6 ex-crash table: 12 cells, max |t diff|", mx_t, 0.0, TOL2)

# ---- 9f. covid_paths figure end values (own compounding 2020-01..2021-12)
cum = lambda s: float((1 + s.loc[COVID[0]:COVID[1]].fillna(0)).prod() - 1)  # noqa: E731
rec("r2_fig", "EMV_env O3 realtime COVID cumulative net (claim 17.09%)", 100 * cum(MY[("EMV_env", "O3")]["net"]), 17.09, 0.005)
rec("r2_fig", "VIX O3 realtime COVID cumulative net (claim 7.50%)", 100 * cum(MY[("VIX", "O3")]["net"]), 7.50, 0.005)
rec("r2_fig", "always-short COVID cumulative net (claim 14.21%)", 100 * cum(bench), 14.21, 0.005)
rec("r2_fig", "old buggy EMV_env O3 end value incl. Dec-2019 (round-1 20.55%)",
    100 * float((1 + MY[("EMV_env", "O3")]["net"].loc["2019-12-31":COVID[1]]).prod() - 1), 20.55, 0.005)
KN = pd.read_csv(TABLES / f"{PFX}key_numbers.csv").set_index("name")["value"]
for m, c in (("EMV_env", "O3"), ("EMV_env", "CR"), ("VIX", "O3"), ("VIX", "CR"), ("EMV_overall", "O3"), ("EMV_overall", "CR"),
             ("MCCC", "O3"), ("MCCC", "CR"), ("CPU", "O3"), ("CPU", "CR")):
    rec("r2_fig", f"key_numbers {m}_{c}_covid_cum_net_realtime vs own", cum(net(m, "realtime", c)), float(KN[f"{m}_{c}_covid_cum_net_realtime"]), 1e-12)
rec("r2_fig", "key_numbers bench_covid_cum_net vs own", cum(bench), float(KN["bench_covid_cum_net"]), 1e-12)

# ---- 9g. recent 12 / 18 months (own NW on pipeline nets; own benchmark)
REC = pd.read_csv(TABLES / f"{PFX}recent.csv")
WIN = {"last18": ("2025-02-28", "2026-07-31"), "last12": ("2025-08-31", "2026-07-31")}
mx = 0.0
big = []
for _, r in REC.iterrows():
    s = bench if r.strategy == "AS" else net(r.measure, "realtime", r.strategy)
    al, t, n, p, mn = alpha(s, *WIN[r.period])
    mx = max(mx, abs(al - r.alpha_ann), abs(t - r.t) / 100, abs(mn - r.ann_net), abs(p - r.p) / 100, abs(n - r.n))
    if abs(t) > 2 and r.strategy != "AS":
        big.append(f"{r.measure} {r.strategy} {r.period}: {100 * al:.2f}% (t {t:.2f}, p {p:.3f})")
rec("r2_recent", "recent.csv 50 rows: alpha, t, p, net, n own vs CSV (max scaled diff)", mx, 0.0, 1e-10)
rec("r2_recent", "recent-window cells with |t| > 2 (claim: only EMV_env CR last18)", len(big), 1, 0, " | ".join(big))
for m, per, ca, ct, cn in (("EMV_env", "last18", -4.05, -1.55, -4.51), ("EMV_env", "last12", 1.20, 0.30, -5.21),
                           ("VIX", "last18", 0.79, 0.86, 2.49), ("VIX", "last12", 0.82, 0.90, 4.43),
                           ("EMV_overall", "last18", -1.56, -0.45, 1.97), ("EMV_overall", "last12", 1.30, 0.18, 4.51),
                           ("AS", "last18", -6.25, -1.87, -1.07), ("AS", "last12", -3.39, -0.52, 1.35)):
    s = bench if m == "AS" else net(m, "realtime", "O3")
    al, t, n, p, mn = alpha(s, *WIN[per])
    rec("r2_recent", f"{m} O3 {per}: alpha/t/net (claim {ca}/{ct}/{cn})", f"{100 * al:.2f}/{t:.2f}/{100 * mn:.2f}",
        f"{ca:.2f}/{ct:.2f}/{cn:.2f}", 0, f"n={n}, p={p:.3f}")
al, t, n, p, mn = alpha(net("EMV_env", "realtime", "O3"), *WIN["last18"])
rec("r2_recent", "EMV_env O3 last18 p (claim 0.14) and n 18", f"{p:.2f},{n}", "0.14,18", 0)
al, t, n, p, mn = alpha(net("EMV_env", "realtime", "O3"), *WIN["last12"])
rec("r2_recent", "EMV_env O3 last12 p (claim 0.77)", round(p, 2), 0.77, 0.0)
al, t, n, p, mn = alpha(net("EMV_env", "realtime", "CR"), *WIN["last18"])
rec("r2_recent", "EMV_env CR last18 alpha/t/p (claim -1.74/-2.19/0.046)", f"{100 * al:.2f}/{t:.2f}/{p:.3f}", "-1.74/-2.19/0.046", 0)
for per in WIN:
    d_ = float((net("EMV_env_share", "realtime", "O3") - net("EMV_env", "realtime", "O3")).loc[WIN[per][0]:WIN[per][1]].abs().max())
    rec("r2_recent", f"EMV_env_share O3 identical to EMV_env O3, {per} (max abs diff)", d_, 0.0, 1e-15)
rec("r2_recent", "t(14) and t(8) critical values (claim 2.14, 2.31)", f"{stats.t.ppf(.975, 14):.2f},{stats.t.ppf(.975, 8):.2f}", "2.14,2.31", 0)
o3max = max(abs(alpha(net(m, tm, "O3"), *WIN[per])[1]) for m in ("EMV_env", "VIX", "EMV_overall", "EMV_env_share")
            for tm in ("realtime", "same_month") for per in WIN)
rec("r2_recent", "section 9: max |t| of Original 3m in last 12/18, 4 measures, both timings (claim below 1.6)", o3max, 1.6, 0.0,
    "passes if mine <= claim" if o3max <= 1.6 else "exceeds")
ROWS[-1]["ok"] = bool(o3max <= 1.6)
o3rt = max(abs(alpha(net(m, "realtime", "O3"), *WIN[per])[1]) for m in ("EMV_env", "VIX", "EMV_overall", "EMV_env_share") for per in WIN)
rec("r2_recent", "section 9: max |t| of Original 3m in last 12/18, real-time timing only (claim below 1.6)", o3rt, 1.6, 0.0)
ROWS[-1]["ok"] = bool(o3rt <= 1.6)
# team timing: own from-scratch engine (same-month inputs) and the team baseline
a_sm, _ = inputs("EMV_env", "same_month")
my_sm, _, _ = my_original(a_sm, 3)
for per, cl in (("last18", "-10.82/-4.75/0.0003"), ("last12", "-11.31/-2.68/0.028")):
    al, t, n, p, mn = alpha(my_sm["net"], *WIN[per])
    rec("r2_recent", f"EMV_env O3 team timing {per}, own engine: alpha/t/p (not in FINDINGS)", f"{100 * al:.2f}/{t:.2f}/{p:.4f}" if per == "last18" else f"{100 * al:.2f}/{t:.2f}/{p:.3f}", cl, 0, f"net {100 * mn:.2f}%")
    al2, t2, *_ = alpha(tb, *WIN[per])
    rec("r2_recent", f"EMV_env O3 team baseline {per} equals same-month (alpha diff)", 100 * (al2 - al), 0.0, 1e-9)
big_sm = []
for m in ("EMV_env", "VIX", "EMV_overall", "EMV_env_share"):
    for c in SN:
        for per in WIN:
            al, t, n, p, mn = alpha(net(m, "same_month", c), *WIN[per])
            if abs(t) > 2:
                big_sm.append(f"{m} {c} {per}: {100 * al:.2f}% (t {t:.2f}, p {p:.4f})")
rec("r2_recent", "team-timing recent cells with |t| > 2 (info; all negative?)", len(big_sm), np.nan, np.inf, " | ".join(big_sm))

# ---- 9h. section 3/5/8 figures not covered in round 1 or restated
zz = pd.concat([RUNS[("EMV_env_share", "realtime")]["signals"]["raw"], ze], axis=1).loc["2010-01-31":].dropna()
rec("r2_text", "corr(z_EMV_env_share, z_EMV_env) post-2010 (claim 0.88)", float(zz.corr().iloc[0, 1]), 0.88, 0.005)
rec("r2_text", "EMV_env holdout zero months (claim 31 of 48)", f"{int((hz == 0).sum())} of {len(hz)}", "31 of 48", 0)
rec("r2_text", "team baseline O3 COVID net (claim 5.94%)", 100 * net_, 5.94, 0.005)
ICS = {}
for m in ("EMV_env", "MCCC", "CPU", "MCCC_transition"):
    for key in ("raw", "pure", "w_raw", "w_pure"):
        for per, (a, b) in (("val", VAL), ("hold", (HOLD0, END[m]))):
            ICS[(m, key, per)] = ic(RUNS[(m, "realtime")]["signals"][key], a, b)
for key, ca, ct in (("raw", -0.024, -0.23), ("pure", -0.045, -0.41), ("w_raw", -0.147, -2.16), ("w_pure", -0.162, -2.19)):
    c, t, *_ = ICS[("EMV_env", key, "val")]
    rec("r2_text", f"EMV_env validation IC {key} (claim {ca}, t {ct})", f"{c:.3f}/{t:.2f}", f"{ca:.3f}/{ct:.2f}", 0)
rng_ic = lambda m, per: [ICS[(m, k, per)] for k in ("raw", "pure", "w_raw", "w_pure")]  # noqa: E731
v = rng_ic("MCCC", "val")
rec("r2_text", "MCCC validation IC range and max t (claim 0.030 to 0.092, t < 1.1)",
    f"{min(x[0] for x in v):.3f}..{max(x[0] for x in v):.3f}, maxt<1.1={max(x[1] for x in v) < 1.1}", "0.030..0.092, maxt<1.1=True", 0)
v = rng_ic("CPU", "val")
rec("r2_text", "CPU validation IC range and max |t| (claim -0.005 to 0.019, |t| < 0.32)",
    f"{min(x[0] for x in v):.3f}..{max(x[0] for x in v):.3f}, max|t|<0.32={max(abs(x[1]) for x in v) < 0.32}", "-0.005..0.019, max|t|<0.32=True", 0)
v = rng_ic("MCCC", "hold")
rec("r2_text", "MCCC holdout IC range and t range (claim 0.103 to 0.214; t 0.90 to 2.22)",
    f"{min(x[0] for x in v):.3f}..{max(x[0] for x in v):.3f}; {min(x[1] for x in v):.2f}..{max(x[1] for x in v):.2f}", "0.103..0.214; 0.90..2.22", 0)
v = rng_ic("CPU", "hold")
rec("r2_text", "CPU holdout IC range (claim -0.030 to 0.065)", f"{min(x[0] for x in v):.3f}..{max(x[0] for x in v):.3f}", "-0.030..0.065", 0)
v = rng_ic("MCCC_transition", "hold")
rec("r2_text", "MCCC transition holdout ICs all positive; purified (claim 0.267, t 2.92)",
    f"{all(x[0] > 0 for x in v)}; {ICS[('MCCC_transition', 'pure', 'hold')][0]:.3f}/{ICS[('MCCC_transition', 'pure', 'hold')][1]:.2f}", "True; 0.267/2.92", 0)
cw = [ICS[("MCCC_transition", k, "hold")] for k in ("w_raw", "w_pure")]
rec("r2_text", "MCCC transition continuous-weight holdout ICs (claim 0.244 to 0.248, t 2.53 to 2.80)",
    f"{min(x[0] for x in cw):.3f}..{max(x[0] for x in cw):.3f}; {min(x[1] for x in cw):.2f}..{max(x[1] for x in cw):.2f}", "0.244..0.248; 2.53..2.80", 0)
ah = [alpha(net("MCCC_transition", "realtime", c), HOLD0, END["MCCC_transition"])[0] for c in SN]
rec("r2_text", "MCCC transition holdout alpha range (claim -1.35% to +0.56%)", f"{100 * min(ah):.2f}..{100 * max(ah):.2f}", "-1.35..0.56", 0)
for c, per, ca, ct in (("P6", "val", 1.93, 2.19), ("O3", "val", 0.26, 0.32), ("O3", "hold", -2.16, -1.90)):
    a, b = VAL if per == "val" else (HOLD0, END["EMV_env_share"])
    al, t, *_ = alpha(net("EMV_env_share", "realtime", c), a, b)
    rec("r2_text", f"EMV_env_share {c} {per} alpha/t (claim {ca}/{ct})", f"{100 * al:.2f}/{t:.2f}", f"{ca:.2f}/{ct:.2f}", 0)
ah = [alpha(net("CPU", "same_month", c), HOLD0, END["CPU"])[0] for c in SN]
rec("r2_text", "CPU team-timing holdout alpha range (claim -1.20% to +0.50%)", f"{100 * min(ah):.2f}..{100 * max(ah):.2f}", "-1.20..0.50", 0)
al, t, *_ = alpha(net("MCCC", "same_month", "O6"), *VAL)
rec("r2_text", "MCCC team-timing O6 validation alpha/t (claim 1.57/1.59)", f"{100 * al:.2f}/{t:.2f}", "1.57/1.59", 0)
al, t, *_ = alpha(net("EMV_overall", "realtime", "O6"), *VAL)
rec("r2_text", "EMV_overall O6 validation alpha/t (claim 1.88/2.05)", f"{100 * al:.2f}/{t:.2f}", "1.88/2.05", 0)
# level transform (own runs with attention_transform='none')
LV = {}
for m in ("MCCC", "CPU"):
    a_, c_ = inputs(m, "realtime")
    LV[m] = run_pipeline(macro=MAC, attention=a_, controls=c_, attention_transform="none", **CHEAP)
v = [ic(LV["MCCC"]["signals"][k], HOLD0, END["MCCC"])[0] for k in ("raw", "pure", "w_raw", "w_pure")]
rec("r2_text", "MCCC level-transform holdout IC range (claim 0.121 to 0.216)", f"{min(v):.3f}..{max(v):.3f}", "0.121..0.216", 0)
ah = [alpha(LV["CPU"]["strategies"][SN[c]]["net_return"], HOLD0, END["CPU"])[0] for c in SN]
rec("r2_text", "CPU level-transform holdout alpha range (claim -1.62% to +0.36%)", f"{100 * min(ah):.2f}..{100 * max(ah):.2f}", "-1.62..0.36", 0)
ah = [alpha(LV["MCCC"]["strategies"][SN[c]]["net_return"], HOLD0, END["MCCC"])[0] for c in SN]
rec("r2_text", "MCCC level-transform holdout alpha range (claim -2.48% to -0.65%)", f"{100 * min(ah):.2f}..{100 * max(ah):.2f}", "-2.48..-0.65", 0)
# bootstrap (own re-implementation of the circular block bootstrap, same RNG stream)


def cbb(s, block=12, reps=5000, seed=230):
    v_ = s.dropna().to_numpy()
    n_ = len(v_)
    g_ = np.random.default_rng(seed)
    nb = int(np.ceil(n_ / block))
    dr = np.array([12 * v_[((g_.integers(0, n_, size=nb)[:, None] + np.arange(block)) % n_).ravel()[:n_]].mean() for _ in range(reps)])
    return 12 * v_.mean(), np.quantile(dr, .025), np.quantile(dr, .975), 2 * min((dr > 0).mean(), (dr < 0).mean())


for m, c, cl in (("MCCC", "O3", "-2.69 [-5.41, -0.29]"), ("MCCC", "O6", "-2.87 [-5.65, -0.47]"), ("CPU", "O3", "-0.37 [-1.81, 1.22]"),
                 ("EMV_env", "O3", "-2.57 [-4.72, -0.78]")):
    mu, lo, hi, p = cbb(net(m, "realtime", c).loc[HOLD0:END[m]])
    rec("r2_text", f"{m} {c} holdout bootstrap mean [CI] (own)", f"{100 * mu:.2f} [{100 * lo:.2f}, {100 * hi:.2f}]", cl, 0)
# full-mode table
FMC = pd.read_csv(TABLES / f"{PFX}full_mode_comparison.csv")
for m in ("EMV_env", "MCCC", "CPU", "VIX", "EMV_overall"):
    for c in ("O3", "O6"):
        held_n = int((MY[(m, c)]["position"].shift(1).loc[VAL[0]:END[m]].fillna(0) != 0).sum())
        rep_n = int(FMC[(FMC.measure == m) & (FMC.strategy == SN[c])].months_held_full.iloc[0])
        rec("r2_full", f"{m} {c} months_held_full, own engine vs CSV", held_n, rep_n, 0)
rec("r2_full", "EMV_env O3 months held of window (claim 75 of 199)",
    f"{int((MY[('EMV_env', 'O3')]['position'].shift(1).loc[VAL[0]:END['EMV_env']].fillna(0) != 0).sum())} of "
    f"{len(pd.date_range(VAL[0], END['EMV_env'], freq='ME'))}", "75 of 199", 0)
att = FMC[~FMC.strategy.str.startswith("Benchmark")]
rec("r2_full", "attention-strategy full-window bootstrap p < 0.05 (claim 0 of 30)", f"{int((att.bootstrap_p < 0.05).sum())} of {len(att)}", "0 of 30", 0)
xm = att.loc[att.bootstrap_p.idxmin()]
rec("r2_full", "smallest attention bootstrap p (claim EMV_overall O6 0.064)", f"{xm.measure} {xm.strategy} {xm.bootstrap_p:.3f}",
    "EMV_overall Original | Short Brown hold 6m 0.064", 0)
x = fp[(fp.measure == "MCCC") & fp.new.str.startswith("Continuous | raw") & fp.benchmark.str.contains("hold 3m")].iloc[0]
rec("r2_full", "MCCC CR-O3 holdout paired bootstrap p (claim 0.018)", float(x.p_two_sided), 0.018, 0.0005)
both = pd.concat([net("MCCC", "realtime", "CR").rename("a"), net("MCCC", "realtime", "O3").rename("b")], axis=1).loc[HOLD0:END["MCCC"]].dropna()
mu, lo, hi, p = cbb(both.a - both.b)
rec("r2_full", "MCCC CR-O3 holdout paired bootstrap, own (mean %, p)", f"{100 * mu:.2f}, {p:.3f}", f"{100 * x.mean_ann:.2f}, {x.p_two_sided:.3f}", 0)

# ---- 9i. crossings table in the text (parsed) vs own
hdr, rows = table("7 crossings")
NAME = {"EMV env. (team)": "EMV_env", "MCCC": "MCCC", "CPU": "CPU", "VIX": "VIX", "EMV overall": "EMV_overall",
        "EMV env. share": "EMV_env_share", "MCCC transition": "MCCC_transition"}
bad = []
for r in rows:
    cm = CROSS_MINE[NAME[r[0]]]
    ints = [cm["n"], cm["val"], cm["hold"], cm["covid"], cm["exact"], cm["pm1"]]
    for k_, (v_, s_) in enumerate(zip(ints, r[1:7])):
        if int(s_) != v_:
            bad.append(f"{r[0]} col{k_ + 1}: text {s_} vs {v_}")
    for key, s_ in (("chance", r[7]), ("p1", r[8]), ("pp1", r[9])):
        if s_ and abs(cm[key] - float(s_)) > half_unit(s_):
            bad.append(f"{r[0]} {key}: text {s_} vs {cm[key]:.4f}")
rec("r2_text", "section 7 crossings table, 7 rows x 9 columns vs own (mismatches)", len(bad), 0, 0, " | ".join(bad))
for m, cl in (("MCCC", 0.24), ("CPU", 0.34), ("EMV_overall", 0.34)):
    rec("r2_text", f"{m} Jaccard (claim {cl})", CROSS_MINE[m]["jac"], cl, 0.005)
rec("r2_text", "coverage share range (claim 0.376 to 0.381)",
    f"{min(v['q'] for v in CROSS_MINE.values()):.3f}..{max(v['q'] for v in CROSS_MINE.values()):.3f}", "0.376..0.381", 0)
rec("r2_text", "EMV_overall two-sided p binomial / circular shift (claim 0.052 / 0.071)",
    f"{CROSS_MINE['EMV_overall']['p2']:.3f} / {CROSS_MINE['EMV_overall']['pp2']:.3f}", "0.052 / 0.071", 0)
for m in ("MCCC", "CPU", "EMV_overall", "EMV_env_share"):
    rec("r2_text", f"{m} circular-shift one-sided p incl. identity shift (sensitivity, not claimed)", CROSS_MINE[m]["pp1_incl"],
        np.nan, np.inf, f"module (excl. identity) {CROSS_MINE[m]['pp1']:.4f}")
for m in ("EMV_env_share", "MCCC_transition"):
    a_, _ = inputs(m, "same_month")
    _, _, crs = my_original(a_, 3)
    c1 = crs.loc["2010-01-31":].astype(bool)
    c2 = RUNS[(m, "same_month")]["signals"]["cross_raw"].reindex(c1.index).fillna(False).astype(bool)
    rec("crossings", f"{m} crossing dates, from-scratch vs pipeline (mismatches)", int((c1 != c2).sum()), 0, 0)

# ---- 9j. ledger (round 2)
LED0 = pd.read_csv(Path("/tmp/claude-1000/-home-hashim-projects-GA/5d56c5f1-d319-48cb-b466-4daeaca6ed67/scratchpad/m1b_before")
                   / f"{PFX}tests_ledger.csv")
pref = LED.test_id.str.extract(r"^(COVIDB|FULLBOOT|FULLPAIR|CROSSPERM)_")[0]
rec("ledger", "new prefixed rows COVIDB/FULLBOOT/FULLPAIR/CROSSPERM (claim 168/40/20/6)",
    "/".join(str(int((pref == k).sum())) for k in ("COVIDB", "FULLBOOT", "FULLPAIR", "CROSSPERM")), "168/40/20/6", 0)
fb = LED[pref == "FULLBOOT"].primary_or_exploratory.value_counts().to_dict()
rec("ledger", "FULLBOOT kinds (claim 30 robustness, 10 reference)", f"{fb.get('robustness', 0)}/{fb.get('reference', 0)}", "30/10", 0)
rec("ledger", "missing statistic", int(LED.statistic.isna().sum()), 0, 0)
rec("ledger", "rows at bootstrap resolution bound 0.0004 (claim 3)", int((LED.p_value_two_sided == 0.0004).sum()), 3, 0)
rec("ledger", "round-1 rows all kept", int(LED0.test_id.isin(LED.test_id).sum()), len(LED0), 0)
j0 = LED0.merge(LED, on="test_id", suffixes=("_0", "_1"))
chg = j0[(j0.statistic_0 - j0.statistic_1).abs().gt(1e-12) | (j0.p_value_two_sided_0 - j0.p_value_two_sided_1).abs().gt(1e-12)]
rec("ledger", "round-1 rows whose statistic or p changed (expected: 6 CROSS + 1 BOOT p=0 row)", len(chg), 7, 0,
    ", ".join(chg.test_id))
pr0 = set(LED0[LED0.primary_or_exploratory == "primary"].test_id)
pr1 = set(LED[LED.primary_or_exploratory == "primary"].test_id)
rec("ledger", "primary test ids unchanged from round 1", pr0 == pr1, True, 0)
for m in ("MCCC", "CPU", "VIX", "EMV_overall", "EMV_env_share", "MCCC_transition"):
    rc = LED[LED.test_id == f"CROSS_{m}_overlap_pm1"].iloc[0]
    rp = LED[LED.test_id == f"CROSSPERM_{m}_overlap_pm1"].iloc[0]
    rec("ledger", f"CROSS/CROSSPERM {m} two-sided p vs own", f"{rc.p_value_two_sided:.6f}/{rp.p_value_two_sided:.6f}",
        f"{CROSS_MINE[m]['p2']:.6f}/{CROSS_MINE[m]['pp2']:.6f}", 0)
cb = LED[pref == "COVIDB"]
mxl = 0.0
for _, r in cb.iterrows():
    mm = re.match(r"COVIDB_(realtime|same_month)_(.+)_(O3|P3|O6|P6|CR|CP)_minus_always_short_(covid|ex_mar_apr)$", r.test_id)
    tm, m, c, per = mm.groups()
    d = net(m, tm, c) - bench
    if per != "covid":
        d = d.drop(CR2)
    if float(d.loc[COVID[0]:COVID[1]].abs().max()) < 1e-15:
        mxl = max(mxl, abs(r.statistic), abs(r.p_value_two_sided - 1))
        continue
    al, t, n, p = paired(net(m, tm, c), bench, *COVID, drop=CR2 if per != "covid" else None)
    mxl = max(mxl, abs(t - r.statistic), abs(p - r.p_value_two_sided), abs(n - r.n_obs))
rec("ledger", "COVIDB 168 rows: t, p, n own vs ledger (max abs diff)", mxl, 0.0, 1e-8)

OUT = pd.DataFrame(ROWS)
OUT.to_csv(HERE / "verify_results_r2.csv", index=False)
pd.set_option("display.width", 250)
pd.set_option("display.max_colwidth", 90)
pd.set_option("display.max_rows", 400)
print(OUT[["claim", "check", "mine", "reported", "ok", "note"]].to_string())
print(f"\n{int((OUT.ok == True).sum())} of {int((OUT.ok != 'info').sum())} checks within tolerance; {int((OUT.ok == 'info').sum())} info rows")
print(pp.round(4).to_string())
