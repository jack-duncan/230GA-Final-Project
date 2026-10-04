"""Round-2 independent verification of M1_signal_audit (does NOT import run.py or helpers.py).

Covers what the fix round added or changed:
  - Q3 counterfactuals (frozen 2021-09 scaling, frozen + team threshold, zeros as missing x2), entry bars, base rate
  - direction-free correlation test: re-derived from raw moments by the delta method (not the builder's psi shortcut)
  - Q5 primary robustness (reverse direction, NW(24), direction-free, partial correlation, Holm)
  - Q4 dependence-robust p-values for every window, Q2 subsample claims, standardized-level claims, Q6a/Q6b robustness
  - ledger integrity after deduplication (no pair tested twice, p-values equal the tables, counts)
  - the round-2 FINDINGS text (fix agent's findings_draft.txt) against these numbers
Run: cd /home/hashim/projects/GA/project/research && uv run python modules/M1_signal_audit/verify/verify_m1_round2.py
Writes: modules/M1_signal_audit/verify/verify_results_round2.csv
"""
import sys, pathlib, re, itertools
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "lib"))

import warnings
import numpy as np
import pandas as pd
from scipy import stats
warnings.filterwarnings("ignore")
from common import load_team, load_mccc, load_cpu, TABLES, RAW  # loaders only

T = lambda name: pd.read_csv(TABLES / f"M1_signal_audit_{name}.csv")
RES = []


def check(claim, builder, mine, tol, note=""):
    try:
        ok = abs(float(builder) - float(mine)) <= tol
    except (TypeError, ValueError):
        ok = str(builder) == str(mine)
    RES.append(dict(claim=claim, builder=builder, verifier=mine, tol=tol, status="match" if ok else "MISMATCH", note=note))
    print(f"[{'ok ' if ok else 'BAD'}] {claim}: builder={builder} verifier={mine} {note}")


def info(claim, builder, mine, note=""):
    RES.append(dict(claim=claim, builder=builder, verifier=mine, tol=np.nan, status="info", note=note))
    print(f"[inf] {claim}: builder={builder} verifier={mine} {note}")


# ----------------------------------------------------------------------------- estimators (copied from verify_m1.py)
def nw_lrv(u, lags):
    u = u - u.mean(0)
    S = u.T @ u
    for j in range(1, lags + 1):
        G = u[j:].T @ u[:-j]
        S += (1 - j / (lags + 1)) * (G + G.T)
    return S


def ols_nw(y, X, lags=6):
    d = pd.concat([y.rename("__y"), X], axis=1).dropna()
    Y = d["__y"].to_numpy(float); Xm = np.column_stack([np.ones(len(d)), d.drop(columns="__y").to_numpy(float)])
    n, k = Xm.shape
    XtX_inv = np.linalg.inv(Xm.T @ Xm); b = XtX_inv @ Xm.T @ Y; e = Y - Xm @ b
    u = Xm * e[:, None]; S = u.T @ u
    for j in range(1, lags + 1):
        G = u[j:].T @ u[:-j]; S += (1 - j / (lags + 1)) * (G + G.T)
    V = XtX_inv @ S @ XtX_inv
    se = np.sqrt(np.diag(V)); t = b / se; p = 2 * stats.norm.sf(np.abs(t))
    r2 = 1 - (e @ e) / ((Y - Y.mean()) @ (Y - Y.mean()))
    names = ["const"] + list(d.columns.drop("__y"))
    return dict(b=dict(zip(names, b)), t=dict(zip(names, t)), p=dict(zip(names, p)), r2=r2, n=n, start=d.index[0], end=d.index[-1])


def zscore60(x, window=60, minp=36):
    x = x.dropna(); v = x.to_numpy(float); out = np.full(len(v), np.nan)
    for i in range(len(v)):
        w = v[max(0, i - window + 1): i + 1]
        if len(w) >= minp:
            sd = w.std(ddof=1); out[i] = (v[i] - w.mean()) / sd if sd > 0 else np.nan
    return pd.Series(out, index=x.index)


def past_q80(z, q=80, min_hist=60):
    out = pd.Series(np.nan, index=z.index); vals = z.to_numpy(float)
    for i in range(len(vals)):
        past = vals[:i]; past = past[~np.isnan(past)]
        if len(past) >= min_hist:
            out.iloc[i] = np.percentile(past, q)
    return out


def ar1_realtime(x, min_pairs=36):
    x = x.dropna(); v = x.to_numpy(float); out = np.full(len(v), np.nan)
    for i in range(1, len(v)):
        xp, xc = v[0:i - 1], v[1:i]
        if len(xc) < min_pairs:
            continue
        b = np.cov(xp, xc, ddof=1)[0, 1] / np.var(xp, ddof=1); a = xc.mean() - b * xp.mean()
        out[i] = v[i] - a - b * v[i - 1]
    return pd.Series(out, index=x.index)


def rolling_resid(y, F, window=60):
    d = pd.concat([y.rename("y"), F], axis=1).dropna()
    Y = d["y"].to_numpy(float); X = np.column_stack([np.ones(len(d)), d[F.columns].to_numpy(float)])
    out = np.full(len(d), np.nan)
    for i in range(window, len(d)):
        c = np.linalg.lstsq(X[i - window:i], Y[i - window:i], rcond=None)[0]; out[i] = Y[i] - X[i] @ c
    return pd.Series(out, index=d.index)


def ic(signal, outcome, start=None, end=None, lags=6):
    d = pd.concat([signal.rename("x"), outcome.shift(-1).rename("y")], axis=1).dropna()
    d = d.loc[start:end] if (start or end) else d
    zx = (d.x - d.x.mean()) / d.x.std(ddof=1); zy = (d.y - d.y.mean()) / d.y.std(ddof=1)
    r = ols_nw(zy, zx.to_frame("s"), lags)
    return dict(ic=r["b"]["s"], t=r["t"]["s"], p=r["p"]["s"], n=r["n"], start=d.index[0], end=d.index[-1])


def corr_moments(x, y, lags=6, start=None, end=None, ddof1=True):
    """Direction-free HAC test of a Pearson correlation from raw moments g_t = (x, y, x^2, y^2, xy):
    r = (m5 - m1 m2) / sqrt((m3 - m1^2)(m4 - m2^2)); var(r) = grad' LRV(g) grad / n (Bartlett NW).
    ddof1=True rescales t by n/(n-1), the builder's convention (its influence function uses ddof=1 z-scores);
    the asymptotic test is ddof1=False. The two differ by 1/n in t."""
    d = pd.concat([x.rename("x"), y.rename("y")], axis=1).dropna()
    d = d.loc[start:end] if (start or end) else d
    X, Y = d.x.to_numpy(float), d.y.to_numpy(float); n = len(d)
    g = np.column_stack([X, Y, X * X, Y * Y, X * Y]); m = g.mean(0)
    vx, vy, cxy = m[2] - m[0] ** 2, m[3] - m[1] ** 2, m[4] - m[0] * m[1]
    s = np.sqrt(vx * vy); r = cxy / s
    grad = np.array([-m[1] / s + r * m[0] / vx, -m[0] / s + r * m[1] / vy, -r / (2 * vx), -r / (2 * vy), 1 / s])
    var = grad @ nw_lrv(g, lags) @ grad / n ** 2
    t = r / np.sqrt(var) * (n / (n - 1) if ddof1 else 1.0)
    return dict(r=r, t=t, p=2 * stats.norm.sf(abs(t)), n=n, start=d.index[0], end=d.index[-1])


def slope_p(y, x, lags=6):
    """Builder's pre-specified test: NW t of the slope of standardized y on standardized x."""
    d = pd.concat([y.rename("y"), x.rename("x")], axis=1).dropna()
    zs = lambda v: (v - v.mean()) / v.std(ddof=1)
    return ols_nw(zs(d.y), zs(d.x).to_frame("x"), lags)["p"]["x"]


def holm(p):
    p = np.asarray(p, float); o = np.argsort(p); m = len(p); adj = np.empty(m); run = 0
    for r, i in enumerate(o):
        run = max(run, (m - r) * p[i]); adj[i] = min(1.0, run)
    return adj


def fred_raw(sid):
    df = pd.read_csv(RAW / f"fred_{sid}.csv"); df.columns = ["date", "v"]
    df["date"] = pd.to_datetime(df["date"]); df["v"] = pd.to_numeric(df["v"], errors="coerce")
    return df


def ym(t):
    return pd.Timestamp(t).strftime("%Y-%m")


def rule(z, thr=None):
    thr = past_q80(z) if thr is None else thr
    st = (z > thr) & thr.notna()
    return thr, st, st & ~st.shift(1, fill_value=False)


def months(mask, a, b):
    s = mask.loc[a:b]
    return [ym(t) for t in s[s].index]


# ----------------------------------------------------------------------------- data
team = load_team()
f = fred_raw("EMVENRGYENVREG"); emv_env = pd.Series(f.v.values, index=f.date + pd.offsets.MonthEnd(0))
f = fred_raw("EMVOVERALLEMV"); emv_all = pd.Series(f.v.values, index=f.date + pd.offsets.MonthEnd(0))
f = fred_raw("VIXCLS").dropna(); vix = f.groupby(f.date + pd.offsets.MonthEnd(0)).v.mean().loc[:"2026-08-31"]
f = fred_raw("GS10"); gs10 = pd.Series(f.v.values, index=f.date + pd.offsets.MonthEnd(0)); rate = -gs10.diff()
mccc = load_mccc("Aggregate"); cpu = load_cpu()
TOPICS = ["Climate Legislation/Regulations", "Carbon Tax", "Carbon Credits Market", "Renewable Energy", "Agreements/Actions"]
mccc_tr = pd.concat([load_mccc(c) for c in TOPICS], axis=1).mean(axis=1)
ind = team["industries"]; ff3 = team["ff3"][["Mkt-RF", "SMB", "HML"]]; rf = team["ff3"]["RF"]
G = ["Fun", "RlEst", "Drugs", "Telcm", "Fin"]; B = ["Util", "Ships", "Aero", "Steel", "BldMt"]
green, brown = ind[G].mean(axis=1), ind[B].mean(axis=1); gb = green - brown; brown_x = brown - rf; green_x = green - rf
share = emv_env / emv_all
zero = emv_env.eq(0); prevz = zero.shift(1, fill_value=False)
lz = np.log1p(emv_env)
z_env = zscore60(lz); z_vix = zscore60(np.log1p(vix)); z_all = zscore60(np.log1p(emv_all)); z_share = zscore60(np.log1p(share))
z_mccc = zscore60(np.log1p(mccc)); z_cpu = zscore60(np.log1p(cpu)); z_mtr = zscore60(np.log1p(mccc_tr))
sh = {k: ar1_realtime(v) for k, v in dict(EMV_env=emv_env, EMV_overall=emv_all, VIX=vix, EMV_env_share=share, MCCC=mccc,
                                             MCCC_transition=mccc_tr, CPU=cpu).items()}
thr, state, cross = rule(z_env)
H = ("2022-08-31", "2026-07-31"); V = ("2010-01-31", "2022-07-31"); POST = ("2021-10-31", "2026-08-31")

# ============================================================================= R1 counterfactuals (fix 1)
print("\n== R1 counterfactuals")
w = lz.loc[:"2021-09-30"].iloc[-60:]; m_pre, s_pre = w.mean(), w.std(ddof=1)
check("frozen window mean log1p (m*)", 0.281, round(m_pre, 3), 5e-4)
check("frozen window sd log1p (s*)", 0.171, round(s_pre, 3), 5e-4)
zF = z_env.copy(); zF.loc["2021-10-31":] = (lz.loc["2021-10-31":] - m_pre) / s_pre
thF, stF, crF = rule(zF)                                    # threshold rebuilt past-only on the frozen path
_, stFt, crFt = rule(zF, thr)                               # frozen z, team threshold path
lzn = lz.where(emv_env > 0)
# zeros missing, 60 calendar months (NaN-aware window, >= 12 nonzero values)
zC = pd.Series(np.nan, index=lz.index)
for i, t in enumerate(lz.index):
    wv = lzn.iloc[max(0, i - 59): i + 1].dropna()
    if not np.isnan(lzn.iloc[i]) and len(wv) >= 12:
        zC.iloc[i] = (lzn.iloc[i] - wv.mean()) / wv.std(ddof=1)
zO = zscore60(lzn.dropna(), minp=12).reindex(lz.index)     # last 60 nonzero observations
thC, stC, crC = rule(zC); thO, stO, crO = rule(zO)
base = dict(cross=months(cross, *H), state=months(state, *H))
check("team holdout entries", "2023-04 2024-06 2025-02 2025-09 2025-11", " ".join(base["cross"]), 0)
check("team holdout state months", 7, len(base["state"]), 0)
cfs = T("zero_counterfactual_summary").set_index(["variant", "window"])
for lab, st_, cr_ in (("frozen_2021-09_scaling", stF, crF), ("frozen_2021-09_scaling_team_threshold", stFt, crFt),
                      ("zeros_missing_60m_calendar", stC, crC), ("zeros_missing_last60_nonzero", stO, crO)):
    for win, (a, b) in (("holdout", H), ("post_2021-10", POST), ("validation", V)):
        row = cfs.loc[(lab, win)]
        check(f"CF {lab} {win} entries", row.crossing_months, " ".join(months(cr_, a, b)), 0)
        check(f"CF {lab} {win} n_state", row.n_state, int(st_.loc[a:b].sum()), 0)
        check(f"CF {lab} {win} state months differ", row.n_state_months_differ_from_team, int((st_.loc[a:b] != state.loc[a:b]).sum()), 0)
dropped = [ym(t) for t in state.loc[H[0]:H[1]].index if state.loc[t] and not stC.loc[t]]
check("zeros-missing 60m calendar: holdout state month that drops out", "2022-08", " ".join(dropped), 0)
t15 = pd.Timestamp("2015-07-31")
check("2015-07 team z (marginal validation crossing)", 0.801, round(z_env.loc[t15], 3), 5e-4)
check("2015-07 team threshold", 0.798, round(thr.loc[t15], 3), 5e-4)
info("2015-07 crossing under both zeros-missing variants", "dropped", f"cal {bool(crC.loc[t15])}, obs {bool(crO.loc[t15])}")

# entry bars for holdout nonzero months
hn = T("zero_counterfactual_holdout_nonzero")
bars_t, bars_f = [], []
for t in [pd.Timestamp(m) + pd.offsets.MonthEnd(0) for m in hn.month]:
    past = lz.loc[:t].iloc[-60:-1].to_numpy()
    lo, hi = 0.0, 5.0
    for _ in range(80):
        mid = (lo + hi) / 2; wv = np.r_[past, mid]; zt = (mid - wv.mean()) / wv.std(ddof=1)
        lo, hi = (lo, mid) if zt > thr.loc[t] else (mid, hi)
    bars_t.append(np.expm1(hi)); bars_f.append(np.expm1(m_pre + thF.loc[t] * s_pre))
bars_t, bars_f = np.array(bars_t), np.array(bars_f)
check("max |team bar - builder|", 0.0, float(np.abs(bars_t - hn.bar_team).max()), 1e-6)
check("max |frozen bar - builder|", 0.0, float(np.abs(bars_f - hn.bar_frozen).max()), 1e-9)
check("team bar range (text 0.37 to 0.53)", "0.37-0.53", f"{bars_t.min():.2f}-{bars_t.max():.2f}", 0)
check("frozen bar range (text 0.518 to 0.521)", "0.518-0.521", f"{bars_f.min():.3f}-{bars_f.max():.3f}", 0)
x_ = hn.EMV_env.to_numpy()
check("holdout readings between the two bars", 0, int(((x_ > np.minimum(bars_t, bars_f)) & (x_ <= np.maximum(bars_t, bars_f))).sum()), 0)
ent = hn[hn.crossing_team]
check("entry readings range (text 0.64 to 0.94)", "0.64-0.94", f"{ent.EMV_env.min():.2f}-{ent.EMV_env.max():.2f}", 0)
cand = hn[hn.prev_month_zero]
check("nonzero-after-zero holdout months", 11, len(cand), 0)
check("of which no entry", 6, int((~cand.crossing_team).sum()), 0)
check("no-entry readings range (text 0.16 to 0.36)", "0.16-0.36",
      f"{cand[~cand.crossing_team].EMV_env.min():.2f}-{cand[~cand.crossing_team].EMV_env.max():.2f}", 0)
# base rate
nz = emv_env.loc[H[0]:H[1]]; nz = nz[nz > 0]; pz = prevz.reindex(nz.index); stn = state.reindex(nz.index)
br = pz.mean()
check("base rate nonzero-after-zero among 17 holdout nonzero months", 11 / 17, br, 1e-12)
check("P(5 of 5) one-sided", 0.113, round(stats.binom.sf(4, 5, br), 3), 5e-4)
check("binomial two-sided p (text 0.169)", 0.169, round(stats.binomtest(5, 5, br).pvalue, 3), 5e-4)
o_, p_ = stats.fisher_exact([[int((stn & pz).sum()), int((~stn & pz).sum())], [int((stn & ~pz).sum()), int((~stn & ~pz).sum())]])
check("state after zero 5/11 vs after nonzero 2/6", "5/11 vs 2/6", f"{int((stn & pz).sum())}/{int(pz.sum())} vs {int((stn & ~pz).sum())}/{int((~pz).sum())}", 0)
check("Fisher p state|prev zero (text 1.0)", 1.0, round(p_, 3), 5e-4)
# window arithmetic and zero-month claims
wa = T("zero_window_arithmetic").set_index("month")
for m_, zs_, mu_, sd_, zz_, th_, bar_ in (("2021-09", 0.033, 0.281, 0.171, -1.58, 0.809, 0.526), ("2026-07", 0.633, 0.142, 0.241, -0.59, 0.800, 0.406)):
    t = pd.Timestamp(m_) + pd.offsets.MonthEnd(0); wv = lz.loc[:t].iloc[-60:]; past = wv.iloc[:-1].to_numpy()
    check(f"window {m_} zero share", zs_, round((wv == 0).mean(), 3), 5e-4)
    check(f"window {m_} mean log1p", mu_, round(wv.mean(), 3), 5e-4)
    check(f"window {m_} sd log1p", sd_, round(wv.std(ddof=1), 3), 5e-4)
    check(f"window {m_} z of a zero month", zz_, round((0 - np.r_[past, 0].mean()) / np.r_[past, 0].std(ddof=1), 2), 5e-3)
    check(f"window {m_} threshold", th_, round(thr.loc[t], 3), 5e-4)
    check(f"window {m_} min EMV_env to cross (builder CSV)", round(wa.loc[m_, "min_EMV_env_to_cross"], 3), bar_, 5e-4)
ts_ = thr.dropna()
check("threshold range over threshold sample (text 0.61 to 0.99)", "0.61-0.99", f"{ts_.loc[:'2026-08-31'].min():.2f}-{ts_.loc[:'2026-08-31'].max():.2f}", 0,
      f"{ym(ts_.index[0])}..")
zz_s = zero.loc[ts_.index[0]:"2026-08-31"]
check("zero months in threshold sample", 50, int(zz_s.sum()), 0)
check("zero months above threshold", 0, int((state.reindex(zz_s.index) & zz_s).sum()), 0)
for per, (a, b), cl in (("holdout", H, 0.79), ("validation", V, 0.42)):
    check(f"corr(z, 1{{nonzero}}) {per}", cl, round(z_env.loc[a:b].corr((~zero.loc[a:b]).astype(float)), 2), 0.005)

# ============================================================================= R2 direction-free correlation test (fix 6)
print("\n== R2 direction-free HAC correlation test")
led = T("tests_ledger"); lp = led.set_index("test_id")
dc = T("decomposition_correlations"); mc = T("measure_correlations")
# builder's HAC p should equal (up to the n/(n-1) standardization factor) my raw-moment delta method
lev = pd.DataFrame({"EMV_env": emv_env, "EMV_overall": emv_all, "VIX": vix, "EMV_env_share": share, "z_EMV_env": z_env,
                    "z_VIX": z_vix, "z_EMV_overall": z_all, "z_EMV_env_share": z_share})
lev["log_EMV_env_nonzero"] = np.log(emv_env.where(emv_env > 0)); lev["log_EMV_overall"] = np.log(emv_all); lev["log_VIX"] = np.log(vix)
dmax, rows_ = 0.0, 0
for _, r in dc.iterrows():
    a_ = pd.Timestamp(r.start) + pd.offsets.MonthEnd(0); b_ = pd.Timestamp(r.end) + pd.offsets.MonthEnd(0)
    c1 = corr_moments(lev[r.series_a], lev[r.series_b], 6, a_, b_); c2 = corr_moments(lev[r.series_b], lev[r.series_a], 6, a_, b_)
    assert abs(c1["p"] - c2["p"]) < 1e-12                     # symmetric by construction
    dmax = max(dmax, abs(c1["t"] - r.t_hac) / abs(r.t_hac)); rows_ += 1
    assert c1["n"] == r.n
check("decomposition_correlations: max relative diff of HAC t (mine, ddof=1 scaling, vs builder)", 0.0, dmax, 1e-6,
      f"{rows_} rows; without the n/(n-1) scaling the gap is exactly 1/n (largest 0.059 at n = 17)")
r_ = corr_moments(emv_env, vix)
check("EMV_env vs VIX level, direction-free p (text 0.0035)", 0.0035, round(r_["p"], 4), 1e-4, f"r={r_['r']:.3f} n={r_['n']}")
for a_, b_, cl_r, cl_n, cl_p in (("z_EMV_env", "z_EMV_overall", 0.39, 465, 1e-12), ("z_EMV_env", "z_VIX", 0.29, 405, 7e-5)):
    c = corr_moments(lev[a_], lev[b_])
    check(f"corr {a_} vs {b_}", cl_r, round(c["r"], 2), 0.005, f"n={c['n']}")
    check(f"n {a_} vs {b_}", cl_n, c["n"], 0)
    check(f"HAC p {a_} vs {b_} (order of magnitude)", round(np.log10(cl_p)), round(np.log10(c["p"])), 0.5, f"p={c['p']:.1e}")
c = corr_moments(z_env, z_vix, 6, "2021-10-31", None)
check("corr z_EMV_env vs z_VIX after 2021-10 (text -0.001, n 59)", -0.001, round(c["r"], 3), 5e-4, f"n={c['n']}")
for b_, cl_r, cl_p in (("z_VIX", -0.05, 0.36), ("z_EMV_overall", -0.03, 0.56)):
    c = corr_moments(z_share, lev[b_])
    check(f"share z vs {b_} r", cl_r, round(c["r"], 2), 0.005); check(f"share z vs {b_} HAC p", cl_p, round(c["p"], 2), 0.0051)
# ledger: no unordered pair tested twice on the same sample; ledger p equals the table's ledger p
pat = re.compile(r"Pearson r (?:\((\w+)\) )?(\S+) vs (\S+)")
keys = {}
for tid, r in lp.iterrows():
    m_ = pat.match(str(r.statistic_name))
    if not m_:
        continue
    tr, a_, b_ = m_.groups()
    nm = lambda s: s if tr in (None, "level") else f"{tr}_{s}" if not s.startswith(("RATE", "Mkt")) else s
    samp = re.findall(r"(\d{4}-\d{2})", str(r.note))[:2]
    k = (frozenset((nm(a_), nm(b_))), tuple(samp))
    keys.setdefault(k, []).append((tid, r.p_value_two_sided))
dups = {k: v for k, v in keys.items() if len(v) > 1}
# the Q5 primaries and their robustness rows are allowed to share a pair (different tests of the same pair, by design)
dups_bad = {k: v for k, v in dups.items() if not all(t.startswith(("Q5_primary", "Q5_corr_MCCC_z_EMV_env_overlap", "Q5_corr_CPU_z_EMV_env_overlap")) for t, _ in v)}
check("ledger correlation pairs recorded more than once (excluding Q5 primary robustness family)", 0, len(dups_bad), 0,
      "; ".join(f"{sorted(k[0])} {k[1]}: {[t for t, _ in v]}" for k, v in list(dups_bad.items())[:4]))
for tab, name in ((dc, "decomposition_correlations"), (mc, "measure_correlations")):
    mm = tab.merge(led[["test_id", "p_value_two_sided"]], left_on="ledger_test_id", right_on="test_id", how="left")
    pcol = "ledger_p" if "ledger_p" in tab.columns else "p_hac"
    check(f"{name}: every row has a ledger row", 0, int(mm.p_value_two_sided.isna().sum()), 0, f"{len(mm)} rows")
    check(f"{name}: ledger p = table p (max abs diff)", 0.0, float((mm[pcol] - mm.p_value_two_sided).abs().max()), 1e-12)
pic = T("predictive_ic").dropna(subset=["ic"])
mm = pic.merge(led[["test_id", "p_value_two_sided"]], left_on="ledger_test_id", right_on="test_id", how="left")
check("predictive_ic: ledger p = table p via ledger_test_id", 0.0, float((mm.p_nw - mm.p_value_two_sided).abs().max()), 1e-12,
      f"{len(mm)} rows, {int(mm.p_value_two_sided.isna().sum())} missing")
cv = T("crossings_vix_summary")
for suf, col in (("", "fisher_p"), ("_circshift", "p_circular_shift"), ("_lpm_nw12", "p_lpm_nw12")):
    ids = "Q4_" + cv.flag + "_" + cv.event + "_" + cv.window + suf
    check(f"ledger Q4{suf or ' Fisher'} p = table", 0.0, float((cv[col].values - lp.reindex(ids).p_value_two_sided.values).__abs__().max()), 1e-12)
check("ledger rows", 667, len(led), 0); check("ledger unique ids", True, bool(led.test_id.is_unique), 0)
kinds = led.primary_or_exploratory.value_counts()
check("ledger primary / robustness / exploratory", "15/217/435", f"{kinds.get('primary', 0)}/{kinds.get('robustness', 0)}/{kinds.get('exploratory', 0)}", 0)
n_alias = int(led.note.str.count("also reported as").sum())
n_alias_ic = int(led[led.test_id.str.startswith("Q6b")].note.str.count("also reported as").sum())
check("merged duplicates (corr + IC)", "17+4", f"{n_alias - n_alias_ic}+{n_alias_ic}", 0)
share_rows = [t for t in led.test_id if "EMV_env_share" in t and t.startswith("Q5_corr_") and ("MCCC" in t or "CPU" in t)]
check("ledger rows for share vs MCCC / CPU / MCCC_transition", 6, len(share_rows), 0)
# net change 632 -> 667: 6 share + 8 Q5 primary robustness + 40 Q4 + 2 Q3 = 56 added, 21 merged
added = 6 + int(led.test_id.str.startswith("Q5_primary").sum()) + int(led.test_id.str.contains("_circshift|_lpm_nw12").sum()) + \
        int(led.test_id.isin(["Q3_fisher_state_prevzero_holdout_nonzero", "Q3_binom_entries_after_zero_holdout"]).sum())
check("rows added in fix round (text lists 6+8+40+2)", 56, added, 0, "text says '35 rows were added'; 35 is the net change after 21 merges")
check("632 + added - merged", 667, 632 + added - n_alias, 0)

# ============================================================================= R3 Q5 primary robustness (fixes 6, 7)
print("\n== R3 Q5 primaries")
q5 = T("q5_primary_robustness").set_index("measure")
pp = {}
for nm, zc in (("MCCC", z_mccc), ("CPU", z_cpu)):
    d = pd.concat([zc.rename("m"), z_env.rename("e"), z_all.rename("o")], axis=1).dropna(subset=["m", "e"])
    pp[nm] = slope_p(d.m, d.e)
    check(f"{nm} primary p (slope, measure on EMV_env)", q5.loc[nm, "p_primary"], pp[nm], 1e-6)
    check(f"{nm} reverse-direction p", q5.loc[nm, "p_reverse_direction"], slope_p(d.e, d.m), 1e-6)
    check(f"{nm} NW(24) p", q5.loc[nm, "p_slope_nw24"], slope_p(d.m, d.e, 24), 1e-6)
    c = corr_moments(d.m, d.e)
    check(f"{nm} direction-free p", round(q5.loc[nm, "p_hac_direction_free"], 3), round(c["p"], 3), 2e-3)
    dd = d.dropna()
    rm = dd.m - np.polyval(np.polyfit(dd.o, dd.m, 1), dd.o); re_ = dd.e - np.polyval(np.polyfit(dd.o, dd.e, 1), dd.o)
    cp = corr_moments(rm, re_)
    check(f"{nm} partial r | z_EMV_overall", q5.loc[nm, "partial_r_given_z_EMV_overall"], cp["r"], 1e-9, f"n={cp['n']}")
    check(f"{nm} partial HAC p", round(q5.loc[nm, "p_partial_hac"], 2), round(cp["p"], 2), 0.011)
hh = holm([pp["MCCC"], pp["CPU"]])
check("Holm CPU (text 0.074)", 0.074, round(hh[1], 3), 5e-4); check("Holm MCCC (text 0.996)", 0.996, round(hh[0], 3), 5e-4)
check("CPU direction-free p (text 0.040)", 0.040, round(q5.loc["CPU", "p_hac_direction_free"], 3), 5e-4)
check("CPU partial r (text 0.05, p 0.36)", "0.05/0.36", f"{q5.loc['CPU', 'partial_r_given_z_EMV_overall']:.2f}/{q5.loc['CPU', 'p_partial_hac']:.2f}", 0)
# Q5 table numbers quoted in the text (direction-free, own overlap)
Zm = {"MCCC": z_mccc, "CPU": z_cpu, "MCCC_transition": z_mtr}
L_ = {"MCCC": mccc, "CPU": cpu, "MCCC_transition": mccc_tr}
for nm, tr, ref, cl_r, cl_p in (("MCCC", "level", "EMV_env", -0.04, 0.67), ("MCCC", "shock", "EMV_env", -0.15, 0.006),
                                ("CPU", "level", "EMV_env", 0.15, 0.15), ("CPU", "shock", "EMV_env", 0.13, 0.042),
                                ("MCCC_transition", "level", "EMV_env", -0.00, None), ("MCCC_transition", "z", "EMV_env", 0.07, 0.29),
                                ("MCCC_transition", "shock", "EMV_env", -0.10, 0.030),
                                ("MCCC", "level", "VIX", -0.04, None), ("MCCC", "z", "VIX", -0.07, None), ("MCCC", "shock", "VIX", -0.10, None),
                                ("CPU", "level", "VIX", 0.07, None), ("CPU", "z", "VIX", 0.15, None), ("CPU", "shock", "VIX", 0.09, None)):
    x = {"level": L_[nm], "z": Zm[nm], "shock": sh[nm]}[tr]
    y = {"level": {"EMV_env": emv_env, "VIX": vix}, "z": {"EMV_env": z_env, "VIX": z_vix}, "shock": {"EMV_env": sh["EMV_env"], "VIX": sh["VIX"]}}[tr][ref]
    c = corr_moments(x, y)
    check(f"Q5 {nm} {tr} vs {ref} r", cl_r, round(c["r"], 2), 0.0051, f"n={c['n']}")
    if cl_p is not None:
        check(f"Q5 {nm} {tr} vs {ref} HAC p", cl_p, round(c["p"], 3 if cl_p < 0.1 else 2), 2e-3 if cl_p < 0.1 else 0.011)
for nm, cl_r, cl_p in (("MCCC", -0.01, 0.89), ("CPU", 0.01, 0.94), ("MCCC_transition", 0.03, 0.66)):
    c = corr_moments(z_share, Zm[nm], 6, "2006-02-28", "2025-06-30")
    check(f"share vs z_{nm} common r", cl_r, round(c["r"], 2), 0.0051, f"n={c['n']}")
    check(f"share vs z_{nm} common p", cl_p, round(c["p"], 2), 0.011)
for nm, cl_r, cl_n, cl_p in (("MCCC", -0.004, 235, 0.96), ("CPU", 0.03, 427, 0.62)):
    c = corr_moments(z_share, Zm[nm])
    check(f"share vs z_{nm} own overlap r", cl_r, round(c["r"], 3 if nm == "MCCC" else 2), 5e-4 if nm == "MCCC" else 0.0051, f"n={c['n']}")
    check(f"share vs z_{nm} own overlap p", cl_p, round(c["p"], 2), 0.011)
cz = pd.concat([z_mccc, z_cpu, z_mtr], axis=1).loc["2006-02-28":"2025-06-30"].corr()
check("common-sample corr z_MCCC, z_CPU", 0.16, round(cz.iloc[0, 1], 2), 0.005); check("common-sample corr z_MCCC, z_MCCC_tr", 0.88, round(cz.iloc[0, 2], 2), 0.005)
for nm, cl_r, cl_p, cl_t in (("MCCC", -0.12, 0.031, -2.16), ("MCCC_transition", -0.12, 0.063, None), ("CPU", 0.04, 0.38, None)):
    c = corr_moments(rate, sh[nm])
    check(f"shock {nm} vs RATE r", cl_r, round(c["r"], 2), 0.0051); check(f"shock {nm} vs RATE HAC p", cl_p, round(c["p"], 3 if cl_p < 0.1 else 2), 2e-3)
    if cl_t is not None:
        check(f"shock {nm} vs RATE t", cl_t, round(c["t"], 2), 0.02)
c = corr_moments(ff3["Mkt-RF"], sh["MCCC"])
check("shock MCCC vs Mkt-RF r / p (text 0.14, 0.010)", "0.14/0.010", f"{c['r']:.2f}/{c['p']:.3f}", 0)

# ============================================================================= R4 Q2 subsamples (fix 3)
print("\n== R4 Q2 VIX qualification")
d = pd.concat([z_env.rename("y"), z_vix.rename("v"), z_all.rename("o")], axis=1).dropna()
for per, (a, b), cl in (("full", (None, None), (-0.35, None, None, 0.169)), ("pre_2021-10", (None, "2021-09-30"), (0.16, None, None, 0.161)),
                        ("validation", V, (-2.51, -0.30, 0.126, 0.166)), ("post_2021-10", ("2021-10-31", None), (-1.92, -0.28, 0.245, 0.281)),
                        ("holdout", H, (-1.13, None, None, 0.267))):
    s = d.loc[a:b]; r = ols_nw(s.y, s[["v", "o"]]); r1 = ols_nw(s.y, s[["o"]])
    check(f"Q2 {per} t(z_VIX)", cl[0], round(r["t"]["v"], 2), 0.005, f"n={r['n']}, t(z_EMV_overall)={r['t']['o']:.2f}")
    if cl[1] is not None:
        check(f"Q2 {per} b(z_VIX)", cl[1], round(r["b"]["v"], 2), 0.005)
        check(f"Q2 {per} R2 EMV-only -> joint", f"{cl[2]}->{cl[3]}", f"{r1['r2']:.3f}->{r['r2']:.3f}", 0)
    check(f"Q2 {per} joint R2", cl[3], round(r["r2"], 3), 5e-4)
ts = [ols_nw(d.loc[a:b].y, d.loc[a:b][["v", "o"]])["t"]["o"] for a, b in ((None, None), (None, "2021-09-30"), V, ("2021-10-31", None), H)]
check("z_EMV_overall t across subsamples (text 3.2 to 5.4)", "3.2-5.4", f"{min(ts):.1f}-{max(ts):.1f}", 0)
dl = pd.concat([emv_env.rename("e"), emv_all.rename("o"), vix.rename("v")], axis=1).dropna()
r2s = [ols_nw(dl.e, dl[c])["r2"] for c in (["o"], ["v"], ["o", "v"])]
check("level R2 (text 0.110, 0.042, 0.113; n 440)", "0.110/0.042/0.113/440", "/".join(f"{x:.3f}" for x in r2s) + f"/{len(dl)}", 0)
dn = pd.concat([np.log(emv_env.where(emv_env > 0)).rename("e"), np.log(emv_all).rename("o"), np.log(vix).rename("v")], axis=1).dropna()
r2s = [ols_nw(dn.e, dn[c])["r2"] for c in (["o"], ["v"], ["o", "v"])]
check("log nonzero R2 (text 0.136, 0.066, 0.137; n 390)", "0.136/0.066/0.137/390", "/".join(f"{x:.3f}" for x in r2s) + f"/{len(dn)}", 0)
ds = pd.concat([z_share.rename("s"), z_vix.rename("v"), z_all.rename("o")], axis=1).dropna()
check("share z R2 on both (text 0.005)", 0.005, round(ols_nw(ds.s, ds[["v", "o"]])["r2"], 3), 5e-4)

# ============================================================================= R5 Q4 dependence-robust p-values (fix 8)
print("\n== R4 Q4")
cm = pd.DataFrame({"crossing": cross, "state": state, "thr": thr, "vix": vix, "vmed": vix.shift(1).expanding(36).median(),
                   "emv": emv_all, "emed": emv_all.shift(1).expanding(36).median()}).loc[thr.first_valid_index():"2026-08-31"]
CW = {"all_threshold_sample": (None, None), "since_2010": ("2010-01-31", "2026-07-31"), "pre2010": (None, "2009-12-31"),
      "validation": V, "holdout": H}
cvi = cv.set_index(["flag", "event", "window"])
worst = {"fisher": 0, "circ": 0, "lpm": 0}
for flag, (lv, md) in {"high_VIX": ("vix", "vmed"), "high_EMV_overall": ("emv", "emed")}.items():
    for ev in ("crossing", "state"):
        for win, (a, b) in CW.items():
            s = cm.loc[a:b]; s = s[s[md].notna()]; fl = (s[lv] > s[md]).to_numpy(); e = s[ev].to_numpy(bool)
            _, pf = stats.fisher_exact([[fl[e].sum(), (~fl[e]).sum()], [fl[~e].sum(), (~fl[~e]).sum()]])
            stat = fl[e].mean() - fl[~e].mean()
            sims = np.array([fl[np.roll(e, k)].mean() - fl[~np.roll(e, k)].mean() for k in range(12, len(e) - 11)])
            pc = (np.abs(sims) >= abs(stat) - 1e-12).mean()
            pl = ols_nw(pd.Series(fl.astype(float)), pd.Series(e.astype(float)).to_frame("e"), 12)["p"]["e"]
            row = cvi.loc[(flag, ev, win)]
            worst["fisher"] = max(worst["fisher"], abs(pf - row.fisher_p)); worst["circ"] = max(worst["circ"], abs(pc - row.p_circular_shift))
            worst["lpm"] = max(worst["lpm"], abs(pl - row.p_lpm_nw12))
check("Q4 20 rows: max |Fisher p diff|", 0.0, worst["fisher"], 1e-10)
check("Q4 20 rows: max |circular-shift p diff| (same rotation set 12..n-12)", 0.0, worst["circ"], 1e-10)
check("Q4 20 rows: max |LPM NW(12) p diff|", 0.0, worst["lpm"], 1e-8)
for key_, cl in ((("high_VIX", "crossing", "all_threshold_sample"), (0.097, 0.113, 0.049)),
                 (("high_EMV_overall", "crossing", "all_threshold_sample"), (0.0006, 0.0, 0.0003)),
                 (("high_VIX", "state", "all_threshold_sample"), (1.3e-5, 0.0026, 0.0001)),
                 (("high_EMV_overall", "crossing", "since_2010"), (0.0012, 0.0, 0.0001)),
                 (("high_VIX", "crossing", "since_2010"), (0.52, 0.53, 0.34)),
                 (("high_EMV_overall", "crossing", "holdout"), (0.57, 0.72, 0.023))):
    row = cvi.loc[key_]
    for lab, v, c_ in (("Fisher", row.fisher_p, cl[0]), ("circ", row.p_circular_shift, cl[1]), ("LPM", row.p_lpm_nw12, cl[2])):
        tol = max(abs(c_) * 0.05, 5e-5) if c_ > 0 else 1e-12
        check(f"Q4 {'/'.join(key_)} {lab} p (text)", c_, v, tol)
check("Q4 primary odds ratio (text 1.71)", 1.71, round(cvi.loc[("high_VIX", "crossing", "all_threshold_sample")].fisher_odds_ratio, 2), 0.005)

# ============================================================================= R6 standardized levels (fix 5)
print("\n== R6 standardized levels")
a0, a1 = "2003-01-31", "2025-06-30"
x = np.log1p(emv_env.loc[a0:a1]); xn = x.where(emv_env.loc[a0:a1] > 0); zn = (xn - xn.mean()) / xn.std(ddof=1)
m3, m6 = zn.rolling(12, min_periods=3).mean().loc["2022":"2024"], zn.rolling(12, min_periods=6).mean().loc["2022":"2024"]
check("zeros excluded, min 3: range", "-0.23/1.20", f"{m3.min():.2f}/{m3.max():.2f}", 0, f"{int(m3.notna().sum())} of 36 months")
check("zeros excluded, min 3: months with a value", 24, int(m3.notna().sum()), 0)
check("zeros excluded, min 6: range", "-0.05/0.35", f"{m6.min():.2f}/{m6.max():.2f}", 0)
check("zeros excluded, min 6: months with a value", 5, int(m6.notna().sum()), 0)
check("11 nonzero months of 2022-2024: mean std reading", 0.37, round(zn.loc["2022":"2024"].dropna().mean(), 2), 0.005, f"n={int(zn.loc['2022':'2024'].notna().sum())}")
for lab, (a, b), cl in (("2022-2024", ("2022-01-31", "2024-12-31"), 0.36), ("60m to 2021-09", ("2016-10-31", "2021-09-30"), 0.306),
                        ("1985-01 to 2021-09", ("1985-01-31", "2021-09-30"), 0.24)):
    s = emv_env.loc[a:b]; check(f"median nonzero EMV_env {lab}", cl, round(s[s > 0].median(), 3 if cl == 0.306 else 2), 5e-4 if cl == 0.306 else 0.005)
for nm, lv, cl in (("MCCC", mccc, "1.19/1.49"), ("CPU", cpu, "0.88/1.39")):
    xx = np.log1p(lv.loc[a0:a1]); zz = ((xx - xx.mean()) / xx.std(ddof=1)).rolling(12).mean().loc["2022":"2024"]
    check(f"{nm} 12m std 2022-2024 range", cl, f"{zz.min():.2f}/{zz.max():.2f}", 0)
ze = ((x - x.mean()) / x.std(ddof=1)).rolling(12).mean()
check("EMV_env 12m std 2022-2024 (with zeros)", "-1.16/-0.08", f"{ze.loc['2022':'2024'].min():.2f}/{ze.loc['2022':'2024'].max():.2f}", 0)
check("EMV_env 12m std peak and month", "0.96 2009-08", f"{ze.max():.2f} {ym(ze.idxmax())}", 0)
s12 = T("standardized_measures_12m").set_index("date")
s12.index = pd.to_datetime(s12.index)
check("figure table min3 series = mine", 0.0, float((s12.EMV_env_nonzero_min3 - zn.rolling(12, min_periods=3).mean().reindex(s12.index)).abs().max()), 1e-9)

# ============================================================================= R7 Q6a and Q6b robustness numbers quoted in the text
print("\n== R7 Q6a / Q6b")
fac_rate = ff3.join(rate.rename("RATE"), how="inner")
sh6 = {"MCCC": sh["MCCC"], "CPU": sh["CPU"], "MCCC_transition": sh["MCCC_transition"]}
b_, a_ = np.polyfit(mccc.shift(1).dropna().to_numpy(), mccc.iloc[1:].to_numpy(), 1); sh6["MCCC_fullAR1"] = mccc - (a_ + b_ * mccc.shift(1))
for nm, spec, per, cl_b, cl_t, cl_n in (("MCCC", "FF3", None, -0.049, -0.30, None), ("CPU", "FF3", None, -0.177, -1.40, None),
                                         ("MCCC", "FF3_RATE", None, -0.024, -0.14, None), ("CPU", "FF3_RATE", None, -0.182, -1.43, None),
                                         ("MCCC_fullAR1", None, None, -0.074, -0.47, 269), ("MCCC_transition", None, None, -0.082, -0.43, None),
                                         ("MCCC", None, ("2020-01-31", "2021-12-31"), 0.53, 0.96, None), ("CPU", None, ("2020-01-31", "2021-12-31"), 0.28, 0.84, None),
                                         ("CPU", None, None, -0.160, -1.23, 425)):
    s_ = sh6[nm].dropna(); xx = (s_ / s_.std(ddof=1)).rename("x").to_frame()
    if spec == "FF3":
        xx = xx.join(ff3, how="inner")
    elif spec == "FF3_RATE":
        xx = xx.join(fac_rate, how="inner")
    dd = pd.concat([gb.rename("y"), xx], axis=1).dropna()
    if per:
        dd = dd.loc[per[0]:per[1]]
    r = ols_nw(dd.y, dd.drop(columns="y"))
    check(f"Q6a {nm} {spec or 'none'} {per[0][:7] if per else 'full'} slope", cl_b, round(100 * r["b"]["x"], 3 if abs(cl_b) < 0.2 else 2), 5e-4 if abs(cl_b) < 0.2 else 0.005)
    check(f"Q6a {nm} {spec or 'none'} {per[0][:7] if per else 'full'} t", cl_t, round(r["t"]["x"], 2), 0.005)
    if cl_n:
        check(f"Q6a {nm} n", cl_n, r["n"], 0)
ct = T("contemporaneous")
rt = ct[(ct.spec == "FF3_RATE") & (ct.outcome == "green_minus_brown")].t_RATE.abs().max()
check("max |t_RATE| in GB regressions (text <= 1.69)", 1.69, round(rt, 2), 0.005)
res = rolling_resid(brown_x, ff3); res_r = rolling_resid(brown_x, fac_rate)
for sn, sig, cl in (("z_CPU", z_cpu, "-0.069/-1.46"), ("shock_CPU", sh["CPU"], "-0.070/-1.59"), ("z_MCCC", z_mccc, "0.079/1.40"),
                   ("shock_MCCC", sh["MCCC"], "0.034/0.50")):
    r = ic(sig, res_r); check(f"IC {sn} on Brown resid FF3+RATE", cl, f"{r['ic']:.3f}/{r['t']:.2f}", 0)
SIG = {"z_MCCC": z_mccc, "shock_MCCC": sh["MCCC"], "z_CPU": z_cpu, "shock_CPU": sh["CPU"], "z_EMV_env": z_env,
       "z_EMV_env_share": z_share, "shock_EMV_env": sh["EMV_env"]}
for sn, on, cl_v, cl_h in (("z_MCCC", "GB", 0.006, 0.114), ("z_MCCC", "BR", 0.058, 0.016), ("shock_MCCC", "GB", -0.015, 0.078),
                           ("shock_MCCC", "BR", 0.042, -0.115), ("z_CPU", "GB", 0.007, 0.050), ("z_CPU", "BR", -0.067, -0.078),
                           ("shock_CPU", "GB", 0.025, 0.163), ("shock_CPU", "BR", -0.063, -0.180),
                           ("z_EMV_env", "GB", 0.182, -0.127), ("z_EMV_env", "BR", -0.091, 0.123), ("z_EMV_env_share", "GB", 0.218, -0.118),
                           ("shock_EMV_env", "BR", -0.095, 0.160)):
    out = gb if on == "GB" else res
    rv, rh = ic(SIG[sn], out, *V), ic(SIG[sn], out, *H)
    check(f"IC {sn} -> {on} validation / holdout", f"{cl_v:+.3f}/{cl_h:+.3f}", f"{rv['ic']:+.3f}/{rh['ic']:+.3f}", 0,
          f"t {rv['t']:.2f}/{rh['t']:.2f}")
r = ic(z_mccc.shift(1), res); check("lag1 z_MCCC -> Brown IC / p (text 0.078, 0.12)", "0.078/0.12", f"{r['ic']:.3f}/{r['p']:.2f}", 0)
r = ic(z_vix, res, *("2025-08-31", "2026-07-31")); check("last12 z_VIX -> Brown resid IC (text -0.62, 11 months; outcome not named in text)", "-0.62/11", f"{r['ic']:.2f}/{r['n']}", 0)
for nm, s_, cl in (("MCCC", z_mccc, 5), ("CPU", z_cpu, 8)):
    check(f"{nm} last18 signal months with a next-month outcome", cl, len(pd.concat([s_.rename('x'), gb.shift(-1).rename('y')], axis=1).dropna().loc["2025-02-28":"2026-07-31"]), 0)
for leg, cl_b, cl_t in (("green", 0.75, 2.48), ("brown", 0.84, 2.22)):
    s_ = sh["MCCC"].dropna(); r = ols_nw(green_x if leg == "green" else brown_x, (s_ / s_.std(ddof=1)).rename("x").to_frame())
    check(f"MCCC shock -> {leg} excess (%, t)", f"{cl_b}/{cl_t}", f"{100 * r['b']['x']:.2f}/{r['t']['x']:.2f}", 0)
ls_ = T("tests_ledger_summary").set_index(["qid", "primary_or_exploratory"])
check("Q6a robustness tests with p < 0.05 (text: all 68 have p > 0.05)", "0/68", f"{int(ls_.loc[('Q6a', 'robustness')].n_p_below_05)}/{int(ls_.loc[('Q6a', 'robustness')].n_tests)}", 0)
check("Q6b robustness tests with p < 0.05 (text: all 110 have p > 0.05)", "0/110", f"{int(ls_.loc[('Q6b', 'robustness')].n_p_below_05)}/{int(ls_.loc[('Q6b', 'robustness')].n_tests)}", 0)
check("Q6b exploratory p < 0.05 (text 26 of 184)", "26/184", f"{int(ls_.loc[('Q6b', 'exploratory')].n_p_below_05)}/{int(ls_.loc[('Q6b', 'exploratory')].n_tests)}", 0)

out = pd.DataFrame(RES)
out.to_csv(HERE / "verify_results_round2.csv", index=False)
print(f"\n{(out.status == 'match').sum()} match, {(out.status == 'MISMATCH').sum()} mismatch, {(out.status == 'info').sum()} info rows")
print(out[out.status == "MISMATCH"].to_string())
