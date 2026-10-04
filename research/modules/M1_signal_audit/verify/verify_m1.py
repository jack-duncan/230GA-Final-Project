"""Independent verification of M1_signal_audit (does NOT import run.py or helpers.py).

Recomputes the decision-relevant numbers from raw data with hand-written estimators:
  - Newey-West (Bartlett) HAC written in numpy, checked against statsmodels
  - real-time AR(1) shocks from cumulative sums
  - expanding past-only 80th percentile via numpy.percentile on the explicit past
  - rolling 60m FF3 hedge refitted by explicit loop, coefficients from months t-60..t-1
Run: cd /home/hashim/projects/GA/project/research && uv run python modules/M1_signal_audit/verify/verify_m1.py
Writes: modules/M1_signal_audit/verify/verify_results.csv (claim, builder value, verifier value, status)
Round 2: builder claims updated to the revised FINDINGS text (CPU t -1.23, bar 0.526, 667 ledger rows, MCCC sign wording,
ledger deduplication). The round-1 version is kept as verify_m1_round1.py. New checks are in verify_m1_round2.py.
"""
import sys, pathlib
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "lib"))

import warnings
import numpy as np
import pandas as pd
from scipy import stats
warnings.filterwarnings("ignore")
from common import load_team, load_mccc, load_cpu, TABLES, RAW  # loaders only

pd.set_option("display.width", 220); pd.set_option("display.max_columns", 30)
T = lambda name: pd.read_csv(TABLES / f"M1_signal_audit_{name}.csv")
RES = []


def check(claim, builder, mine, tol, note=""):
    """Record a comparison. tol is absolute tolerance on the numeric value."""
    try:
        ok = abs(float(builder) - float(mine)) <= tol
    except (TypeError, ValueError):
        ok = str(builder) == str(mine)
    RES.append(dict(claim=claim, builder=builder, verifier=mine, tol=tol, status="match" if ok else "MISMATCH", note=note))
    print(f"[{'ok ' if ok else 'BAD'}] {claim}: builder={builder} verifier={mine} {note}")


# ----------------------------------------------------------------------------- my own estimators
def ols_nw(y, X, lags=6, correction=False):
    """OLS with constant; Bartlett NW HAC. Returns dict of params, se, t, p (normal), r2, wald (chi2/q), n."""
    d = pd.concat([y.rename("__y"), X], axis=1).dropna()
    Y = d["__y"].to_numpy(float); Xm = np.column_stack([np.ones(len(d)), d.drop(columns="__y").to_numpy(float)])
    n, k = Xm.shape
    XtX_inv = np.linalg.inv(Xm.T @ Xm)
    b = XtX_inv @ Xm.T @ Y
    e = Y - Xm @ b
    u = Xm * e[:, None]
    S = u.T @ u
    for j in range(1, lags + 1):
        w = 1 - j / (lags + 1)
        G = u[j:].T @ u[:-j]
        S += w * (G + G.T)
    V = XtX_inv @ S @ XtX_inv
    if correction:
        V *= n / (n - k)
    se = np.sqrt(np.diag(V)); t = b / se
    p = 2 * stats.norm.sf(np.abs(t))
    r2 = 1 - (e @ e) / ((Y - Y.mean()) @ (Y - Y.mean()))
    R = np.eye(k)[1:]; rb = R @ b
    W = float(rb @ np.linalg.inv(R @ V @ R.T) @ rb)
    q = k - 1
    names = ["const"] + list(d.columns.drop("__y"))
    return dict(b=dict(zip(names, b)), se=dict(zip(names, se)), t=dict(zip(names, t)), p=dict(zip(names, p)),
                r2=r2, F=W / q, F_p=stats.f.sf(W / q, q, n - k), n=n, start=d.index[0], end=d.index[-1])


def zscore60(x, window=60, minp=36):
    """Trailing window including t, min 36 obs, ddof=1 (team convention) - written without common.rolling_z."""
    x = x.dropna(); v = x.to_numpy(float); out = np.full(len(v), np.nan)
    for i in range(len(v)):
        w = v[max(0, i - window + 1): i + 1]
        if len(w) >= minp:
            sd = w.std(ddof=1)
            out[i] = (v[i] - w.mean()) / sd if sd > 0 else np.nan
    return pd.Series(out, index=x.index)


def past_q80(z, q=80, min_hist=60):
    """Threshold at t = percentile of all non-NaN z_s with s < t (at least min_hist values)."""
    out = pd.Series(np.nan, index=z.index)
    vals = z.to_numpy(float)
    for i in range(len(vals)):
        past = vals[:i]; past = past[~np.isnan(past)]
        if len(past) >= min_hist:
            out.iloc[i] = np.percentile(past, q)
    return out


def ar1_realtime(x, min_pairs=36):
    x = x.dropna(); v = x.to_numpy(float); out = np.full(len(v), np.nan)
    for i in range(1, len(v)):
        xp, xc = v[0:i - 1], v[1:i]      # pairs (v[s-1], v[s]) for s = 1..i-1
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
        c = np.linalg.lstsq(X[i - window:i], Y[i - window:i], rcond=None)[0]
        out[i] = Y[i] - X[i] @ c
    return pd.Series(out, index=d.index)


def ic(signal, outcome, start=None, end=None, lags=6):
    d = pd.concat([signal.rename("x"), outcome.shift(-1).rename("y")], axis=1).dropna()
    d = d.loc[start:end] if (start or end) else d
    zx = (d.x - d.x.mean()) / d.x.std(ddof=1); zy = (d.y - d.y.mean()) / d.y.std(ddof=1)
    r = ols_nw(zy, zx.to_frame("s"), lags)
    return dict(ic=r["b"]["s"], t=r["t"]["s"], p=r["p"]["s"], n=r["n"], start=d.index[0], end=d.index[-1])


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


# ----------------------------------------------------------------------------- data (raw where possible)
team = load_team()
att = team["macro"]["attention"].dropna()
f = fred_raw("EMVENRGYENVREG"); emv_env = pd.Series(f.v.values, index=f.date + pd.offsets.MonthEnd(0))
f = fred_raw("EMVOVERALLEMV"); emv_all = pd.Series(f.v.values, index=f.date + pd.offsets.MonthEnd(0))
f = fred_raw("VIXCLS").dropna()
vix = f.groupby(f.date + pd.offsets.MonthEnd(0)).v.mean()
vix_days_last = int((f.date.dt.to_period("M") == f.date.max().to_period("M")).sum())
vix = vix.loc[:"2026-08-31"]      # 2026-09 has only a partial month of dailies
mccc = load_mccc("Aggregate"); cpu = load_cpu()
ind = team["industries"]; ff3 = team["ff3"][["Mkt-RF", "SMB", "HML"]]; rf = team["ff3"]["RF"]
G = ["Fun", "RlEst", "Drugs", "Telcm", "Fin"]; B = ["Util", "Ships", "Aero", "Steel", "BldMt"]
em = team["emissions"].sort_values()
check("Green leg = 5 lowest-intensity", ",".join(G), ",".join(em.index[:5]), 0)
check("Brown leg = 5 highest-intensity", ",".join(B), ",".join(em.index[::-1][:5]), 0)
green, brown = ind[G].mean(axis=1), ind[B].mean(axis=1)
gb = green - brown
brown_x = brown - rf

# ----------------------------------------------------------------------------- V1 identity
both = pd.concat([att.rename("a"), emv_env.rename("e")], axis=1)
check("Q1 overlap months", 500, int(both.dropna().shape[0]), 0)
check("Q1 months differing", 0, int((both.a - both.e).abs().gt(0).sum()), 0)
check("Q1 first/last month", "1985-01/2026-08", f"{ym(both.dropna().index[0])}/{ym(both.dropna().index[-1])}", 0)
check("Q1 months only in one series", 0, int(both.isna().any(axis=1).sum()), 0)
print("VIX last daily month has", vix_days_last, "days (dropped)")

# ----------------------------------------------------------------------------- V2 zeros
zero = emv_env.eq(0)
pre, post = zero.loc[:"2021-09-30"], zero.loc["2021-10-31":"2026-08-31"]
check("Q3 zeros pre-2021-10", "12/441", f"{int(pre.sum())}/{len(pre)}", 0)
check("Q3 zeros post-2021-10", "39/59", f"{int(post.sum())}/{len(post)}", 0)
orr, pz = stats.fisher_exact([[post.sum(), (~post).sum()], [pre.sum(), (~pre).sum()]])
check("Q3 Fisher p", 1.3e-32, float(f"{pz:.2g}"), 0.05e-32)
check("Q3 Fisher odds ratio", 69.7, round(orr, 1), 0.05)
for per, (a, b), claim in [("validation", ("2010-01-31", "2022-07-31"), "12/151"), ("holdout", ("2022-08-31", "2026-07-31"), "31/48"),
                           ("inflation_rates", ("2022-01-31", "2024-12-31"), "25/36"), ("last18", ("2025-02-28", "2026-07-31"), "9/18"),
                           ("last12", ("2025-08-31", "2026-07-31"), "8/12")]:
    s = zero.loc[a:b]; check(f"Q3 zeros {per}", claim, f"{int(s.sum())}/{len(s)}", 0)
z24 = zero.astype(float).rolling(24).mean()
check("Q3 24m zero share max pre-2021", 0.125, round(z24.loc[:"2020-12-31"].max(), 4), 1e-4)
check("Q3 24m zero share max", 0.792, round(z24.max(), 3), 5e-4, f"at {ym(z24.idxmax())} (claim 2024-02)")
share = emv_env / emv_all
check("EMV_env_share mean", 0.0136, round(share.mean(), 4), 5e-5)
sp = share.loc["2021-10-31":][share.loc["2021-10-31":] > 0]
check("nonzero share post-2021-10 min", 0.006, round(sp.min(), 3), 5e-4)
check("nonzero share post-2021-10 max", 0.054, round(sp.max(), 3), 5e-4)

# ----------------------------------------------------------------------------- signals
lz = np.log1p(emv_env)
z_env = zscore60(lz)
z_vix = zscore60(np.log1p(vix)); z_all = zscore60(np.log1p(emv_all)); z_share = zscore60(np.log1p(share))
z_mccc = zscore60(np.log1p(mccc)); z_cpu = zscore60(np.log1p(cpu))

# ----------------------------------------------------------------------------- V3 decomposition (Q2 primary)
d = pd.concat([z_env.rename("y"), z_vix.rename("z_VIX"), z_all.rename("z_EMV_overall")], axis=1).dropna()
r = ols_nw(d.y, d[["z_VIX", "z_EMV_overall"]], 6)
check("Q2 n", 405, r["n"], 0, f"{ym(r['start'])}..{ym(r['end'])}")
check("Q2 joint R2", 0.169, round(r["r2"], 3), 5e-4)
check("Q2 HAC Wald F", 27.1, round(r["F"], 1), 0.05)
check("Q2 Wald p", 8.8e-12, float(f"{r['F_p']:.2g}"), 0.05e-12)
check("Q2 t(z_VIX)", -0.35, round(r["t"]["z_VIX"], 2), 0.005)
check("Q2 t(z_EMV_overall)", 5.07, round(r["t"]["z_EMV_overall"], 2), 0.005)
r1 = ols_nw(d.y, d[["z_EMV_overall"]], 6)
print(f"  R2 on z_EMV_overall alone = {r1['r2']:.4f}; VIX increment = {r['r2'] - r1['r2']:.4f}")
for L_ in (12, 24, 60):
    rr = ols_nw(d.y, d[["z_VIX", "z_EMV_overall"]], L_)
    print(f"  NW({L_}) Wald F = {rr['F']:.2f}, p = {rr['F_p']:.2e}, t(z_EMV_overall) = {rr['t']['z_EMV_overall']:.2f}")
RES.append(dict(claim="Q2 Wald p with NW(24) (sensitivity)", builder="8.8e-12 (NW6)",
                verifier=f"{ols_nw(d.y, d[['z_VIX', 'z_EMV_overall']], 24)['F_p']:.2e}", tol=np.nan, status="info"))
dv = d.loc["2010-01-31":"2022-07-31"]; rv = ols_nw(dv.y, dv[["z_VIX", "z_EMV_overall"]], 6)
rv1 = ols_nw(dv.y, dv[["z_EMV_overall"]], 6)
RES.append(dict(claim="Q2 validation: t(z_VIX) and R2 increment from VIX", builder="headline: 'VIX adds nothing'",
                verifier=f"t={rv['t']['z_VIX']:.2f}, dR2={rv['r2'] - rv1['r2']:.3f}", tol=np.nan, status="info"))
print(f"  validation: t(z_VIX)={rv['t']['z_VIX']:.2f}, R2 joint={rv['r2']:.3f} vs EMV-only {rv1['r2']:.3f}")
check("Q2 corr(z_share, team z) n=465", 0.865, round(pd.concat([z_share, z_env], axis=1).dropna().corr().iloc[0, 1], 3), 5e-4)
# statsmodels cross-check of my NW
import statsmodels.api as sm
Xs = sm.add_constant(d[["z_VIX", "z_EMV_overall"]])
smr = sm.OLS(d.y, Xs).fit(cov_type="HAC", cov_kwds={"maxlags": 6})
check("NW(6) implementation vs statsmodels t(z_EMV_overall)", round(smr.tvalues["z_EMV_overall"], 4), round(r["t"]["z_EMV_overall"], 4), 1e-3,
      "(statsmodels default: no small-sample correction)")

# ----------------------------------------------------------------------------- V4 team rule mechanics (Q3)
thr = past_q80(z_env)
state = (z_env > thr) & thr.notna()
cross = state & ~state.shift(1, fill_value=False)
check("team p80 months 2010-01..2026-07", 34, int(state.loc["2010-01-31":"2026-07-31"].sum()), 0)
prevz = zero.shift(1, fill_value=False).reindex(state.index)
for per, (a, b), nc, npz in [("validation", ("2010-01-31", "2022-07-31"), 21, 2), ("holdout", ("2022-08-31", "2026-07-31"), 5, 5)]:
    c = cross.loc[a:b]
    check(f"Q3 crossings {per}", nc, int(c.sum()), 0)
    check(f"Q3 crossings after zero month {per}", npz, int((c & prevz.loc[a:b]).sum()), 0)
h = pd.Series(slice(None))
zh, zzh, sth = z_env.loc["2022-08-31":"2026-07-31"], zero.loc["2022-08-31":"2026-07-31"], state.loc["2022-08-31":"2026-07-31"]
check("Q3 holdout mean z | zero", -0.95, round(zh[zzh].mean(), 2), 0.005)
check("Q3 holdout mean z | nonzero", 0.95, round(zh[~zzh].mean(), 2), 0.005)
check("Q3 holdout nonzero months above threshold", "7/17", f"{int(sth[~zzh].sum())}/{int((~zzh).sum())}", 0)
zv, zzv, stv = z_env.loc["2010-01-31":"2022-07-31"], zero.loc["2010-01-31":"2022-07-31"], state.loc["2010-01-31":"2022-07-31"]
check("Q3 validation mean z | nonzero", 0.08, round(zv[~zzv].mean(), 2), 0.005)
check("Q3 validation P(state | nonzero)", 0.19, round(stv[~zzv].mean(), 2), 0.005)
h6 = cross.rolling(6, min_periods=1).max().astype(bool)
check("Q3 hold6 share holdout", 0.646, round(h6.loc["2022-08-31":"2026-07-31"].mean(), 3), 5e-4)
check("Q3 hold6 share validation", 0.642, round(h6.loc["2010-01-31":"2022-07-31"].mean(), 3), 5e-4)
o2, p2 = stats.fisher_exact([[int((sth & ~zzh).sum()), int((~sth & ~zzh).sum())], [int((sth & zzh).sum()), int((~sth & zzh).sum())]])
check("Q3 Fisher state vs nonzero, holdout", 0.00026, float(f"{p2:.2g}"), 5e-6)
# does the rule 'collapse to a nonzero reading right after a zero month'?
hold = pd.DataFrame({"x": emv_env, "zero": zero, "prevz": zero.shift(1), "cross": cross, "state": state}).loc["2022-08-31":"2026-07-31"]
cand = hold[(~hold.zero) & (hold.prevz == True)]
print(f"  holdout nonzero-after-zero months: {len(cand)}, of which crossings: {int(cand.cross.sum())}; EMV_env at crossings: "
      f"{hold[hold.cross].x.round(3).tolist()}; non-crossing candidates: {cand[~cand.cross].x.round(3).tolist()}")
RES.append(dict(claim="Holdout nonzero-after-zero months that crossed", builder="'rule collapses to a nonzero reading right after a zero month'",
                verifier=f"{int(cand.cross.sum())}/{len(cand)}", tol=np.nan, status="info"))
# window arithmetic: min EMV_env to cross at 2021-09 and 2026-07
for t, claim in (("2021-09-30", 0.526), ("2026-07-31", 0.406)):
    t = pd.Timestamp(t); past = lz.loc[:t].iloc[-60:-1].to_numpy()
    lo, hi = 0.0, 3.0
    for _ in range(60):   # bisection on log1p level; z is monotone in the month-t value
        mid = (lo + hi) / 2; w = np.r_[past, mid]; zt = (mid - w.mean()) / w.std(ddof=1)
        lo, hi = (lo, mid) if zt > thr.loc[t] else (mid, hi)
    check(f"Q3 min EMV_env to cross {ym(t)}", claim, round(float(np.expm1(hi)), 3), 1.5e-3)

# ----------------------------------------------------------------------------- V5 crossings vs volatility (Q4)
def past_median(x, minp=36):
    return x.shift(1).expanding(min_periods=minp).median()

cm = pd.DataFrame({"cross": cross, "state": state, "thr": thr, "vix": vix, "vmed": past_median(vix), "emv": emv_all,
                   "emed": past_median(emv_all)}).loc[thr.first_valid_index():"2026-08-31"]
out = {}
for flag, (lv, md) in {"high_VIX": ("vix", "vmed"), "high_EMV_overall": ("emv", "emed")}.items():
    s = cm[cm[md].notna()].copy(); s["f"] = s[lv] > s[md]
    ev, non = s[s.cross], s[~s.cross]
    o, p = stats.fisher_exact([[ev.f.sum(), (~ev.f).sum()], [non.f.sum(), (~non.f).sum()]])
    out[flag] = (len(ev), ev.f.mean(), non.f.mean(), p, s)
    # dependence-robust check: circular-shift permutation of the crossing indicator (keeps both autocorrelations)
    cr, fl = s.cross.to_numpy(), s.f.to_numpy()
    stat = fl[cr].mean() - fl[~cr].mean()
    sims = np.array([fl[np.roll(cr, k)].mean() - fl[~np.roll(cr, k)].mean() for k in range(12, len(cr) - 12)])
    p_perm = (np.abs(sims) >= abs(stat) - 1e-12).mean()
    # linear probability model with NW(12): flag_t on crossing_t
    lpm = ols_nw(s.f.astype(float), s.cross.astype(float).to_frame("cross"), 12)
    out[flag] += (p_perm, lpm["p"]["cross"])
    print(f"  {flag}: {len(ev)} crossings, {ev.f.mean():.3f} vs {non.f.mean():.3f}, Fisher p={p:.4f}, circular-shift p={p_perm:.4f}, "
          f"LPM NW(12) p={lpm['p']['cross']:.4f}, sample {ym(s.index[0])}..{ym(s.index[-1])}")
n, a_, b_, p, s, pp, pl = out["high_VIX"]
check("Q4 crossings (VIX sample)", 50, n, 0); check("Q4 share crossings high VIX", 0.62, round(a_, 3), 5e-4)
check("Q4 share other months high VIX", 0.489, round(b_, 3), 5e-4); check("Q4 Fisher p (primary)", 0.097, round(p, 3), 5e-4)
check("Q4 sample start", "1993-01", ym(s.index[0]), 0)
n, a_, b_, p, s, pp, pl = out["high_EMV_overall"]
check("Q4 share crossings high EMV_overall", 0.88, round(a_, 3), 5e-4); check("Q4 share other high EMV_overall", 0.645, round(b_, 3), 5e-4)
check("Q4 Fisher p EMV_overall", 0.0006, round(p, 4), 5e-5)
RES.append(dict(claim="Q4 EMV_overall link, dependence-robust p (circular shift / LPM NW12)", builder="p = 0.0006 (Fisher, iid months)",
                verifier=f"{pp:.4f} / {pl:.4f}", tol=np.nan, status="info"))
pv = out["high_VIX"]
RES.append(dict(claim="Q4 VIX link, dependence-robust p (circular shift / LPM NW12)", builder="p = 0.097 (Fisher)",
                verifier=f"{pv[5]:.4f} / {pv[6]:.4f}", tol=np.nan, status="info"))
# state months robustness claim
s = out["high_VIX"][4]; ev, non = s[s.state], s[~s.state]
check("Q4 state months high-VIX share", 0.720, round(ev.f.mean(), 3), 5e-4, f"n={len(ev)} vs other {non.f.mean():.3f}")

# ----------------------------------------------------------------------------- V6 climate measures (Q5)
for nm, zc, claim_r, claim_n, claim_p in (("MCCC", z_mccc, -0.0004, 235, 0.996), ("CPU", z_cpu, 0.123, 427, 0.037)):
    dd = pd.concat([zc.rename("m"), z_env.rename("e")], axis=1).dropna()
    rr = dd.corr().iloc[0, 1]
    zs = lambda v: (v - v.mean()) / v.std(ddof=1)
    p_me = ols_nw(zs(dd.m), zs(dd.e).to_frame("x"), 6)["p"]["x"]         # builder direction: y = measure, x = EMV_env
    p_rev = ols_nw(zs(dd.e), zs(dd.m).to_frame("x"), 6)["p"]["x"]
    p_24 = ols_nw(zs(dd.m), zs(dd.e).to_frame("x"), 24)["p"]["x"]
    check(f"Q5 corr(z_{nm}, z_EMV_env)", claim_r, round(rr, 4 if nm == "MCCC" else 3), 5e-4 if nm == "CPU" else 5e-5)
    check(f"Q5 n {nm}", claim_n, len(dd), 0)
    check(f"Q5 NW p {nm}", claim_p, round(p_me, 3), 5e-4, f"reverse-direction p={p_rev:.3f}; NW(24) p={p_24:.3f}")
    RES.append(dict(claim=f"Q5 {nm} corr p sensitivity", builder=f"{claim_p} (NW6, y=measure)",
                    verifier=f"reverse direction {p_rev:.3f}; NW(24) {p_24:.3f}", tol=np.nan, status="info"))
cmn = pd.concat([z_share.rename("share"), z_mccc.rename("mccc"), z_cpu.rename("cpu"), z_env.rename("env")], axis=1).loc["2006-02-28":"2025-06-30"]
check("Q5 common-sample corr(z_share, z_MCCC)", -0.01, round(cmn.corr().loc["share", "mccc"], 2), 0.005)
check("Q5 common-sample corr(z_share, z_CPU)", 0.01, round(cmn.corr().loc["share", "cpu"], 2), 0.005)
dfull = pd.concat([z_share, z_cpu], axis=1).dropna()
print(f"  corr(z_share, z_CPU) on full CPU overlap ({len(dfull)} months) = {dfull.corr().iloc[0, 1]:.3f}")

# ----------------------------------------------------------------------------- V7 contemporaneous PST (Q6a)
sh_m, sh_c = ar1_realtime(mccc), ar1_realtime(cpu)
pa = []
for nm, sh, cl_b, cl_t, cl_n in (("MCCC", sh_m, -0.093, -0.49, 233), ("CPU", sh_c, -0.160, -1.23, 425)):
    x = (sh / sh.std(ddof=1)).rename("x")
    rr = ols_nw(gb, x.to_frame(), 6)
    check(f"Q6a slope GB on 1sd {nm} shock (%/mo)", cl_b, round(100 * rr["b"]["x"], 3), 5e-4, f"{ym(rr['start'])}..{ym(rr['end'])}")
    check(f"Q6a t {nm}", cl_t, round(rr["t"]["x"], 2), 0.005); check(f"Q6a n {nm}", cl_n, rr["n"], 0)
    pa.append(rr["p"]["x"])
    rc = ols_nw(gb, x.to_frame().join(ff3, how="inner"), 6)
    print(f"  {nm} with FF3: slope {100 * rc['b']['x']:.3f} t {rc['t']['x']:.2f}")
ha = holm(pa)
check("Q6a Holm p MCCC", 0.62, round(ha[0], 2), 0.005); check("Q6a Holm p CPU", 0.43, round(ha[1], 2), 0.005)

# ----------------------------------------------------------------------------- V8 predictive IC (Q6b) and team replication
res = rolling_resid(brown_x, ff3, 60)
rv_ = ic(z_env, res, "2010-01-31", "2022-07-31"); rh_ = ic(z_env, res, "2022-08-31", "2026-07-31")
check("Team IC validation (Brown resid)", -0.0915, round(rv_["ic"], 4), 5e-5, f"n={rv_['n']}")
check("Team IC holdout (Brown resid)", 0.1234, round(rh_["ic"], 4), 5e-5, f"n={rh_['n']}")
sigs = {"z_MCCC": z_mccc, "shock_MCCC": sh_m, "z_CPU": z_cpu, "shock_CPU": sh_c}
claims = {("z_MCCC", "GB"): -0.022, ("z_MCCC", "BR"): 0.074, ("shock_MCCC", "GB"): 0.001, ("shock_MCCC", "BR"): 0.020,
          ("z_CPU", "GB"): 0.027, ("z_CPU", "BR"): -0.073, ("shock_CPU", "GB"): 0.038, ("shock_CPU", "BR"): -0.079}
rows = []
for (sn, on), cl in claims.items():
    rr = ic(sigs[sn], gb if on == "GB" else res)
    rows.append(dict(sig=sn, out=on, ic=rr["ic"], t=rr["t"], p=rr["p"], n=rr["n"]))
    check(f"Q6b IC {sn} -> {on}", cl, round(rr["ic"], 3), 5e-4, f"t={rr['t']:.2f} n={rr['n']} start {ym(rr['start'])}")
icd = pd.DataFrame(rows); icd["holm"] = holm(icd.p)
check("Q6b smallest Holm p", 0.62, round(icd.holm.min(), 2), 0.005)
check("Q6b smallest raw p (shock_CPU -> Brown)", 0.077, round(icd.p.min(), 3), 5e-4)
# validation/holdout for shock_CPU (claims t 1.85 and -1.93 in holdout)
for on, cl in (("GB", 1.85), ("BR", -1.93)):
    rr = ic(sh_c, gb if on == "GB" else res, "2022-08-31", "2026-07-31")
    check(f"Q6b shock_CPU holdout t -> {on}", cl, round(rr["t"], 2), 0.005, f"IC={rr['ic']:.3f} n={rr['n']}")
# lag1 robustness
rr = ic(sh_c.shift(1), res); check("Q6b lag1 shock_CPU -> Brown IC", -0.034, round(rr["ic"], 3), 5e-4, f"p={rr['p']:.2f}")

# ----------------------------------------------------------------------------- V9 ledger audit
led = T("tests_ledger")
check("ledger rows", 667, len(led), 0); check("ledger unique ids", True, bool(led.test_id.is_unique), 0)
check("ledger primary count", 15, int((led.primary_or_exploratory == "primary").sum()), 0)
print("  primary tests:", led[led.primary_or_exploratory == "primary"].test_id.tolist())
# p-values in ledger vs source tables
ics = T("predictive_ic").dropna(subset=["ic"])
ics = ics[~ics.signal.str.endswith("_lag1")]
m = ics.merge(led, left_on="ledger_test_id", right_on="test_id", how="left")   # round 2: merged duplicates carry ledger_test_id
check("ledger Q6b p = predictive_ic p (max abs diff)", 0.0, float((m.p_nw - m.p_value_two_sided).abs().max()), 1e-12, f"{len(m)} rows, missing {int(m.p_value_two_sided.isna().sum())}")
ct = T("contemporaneous"); ct = ct[ct.outcome == "green_minus_brown"]
m = ct.assign(test_id="Q6a_" + ct.shock + "_" + ct.spec + "_" + ct.period).merge(led, on="test_id", how="left")
check("ledger Q6a p = contemporaneous p (max abs diff)", 0.0, float((m.p_nw - m.p_value_two_sided).abs().max()), 1e-12, f"{len(m)} rows, missing {int(m.p_value_two_sided.isna().sum())}")
cv = T("crossings_vix_summary")
m = cv.assign(test_id="Q4_" + cv.flag + "_" + cv.event + "_" + cv.window).merge(led, on="test_id", how="left")
check("ledger Q4 p = crossings_vix_summary p (max abs diff)", 0.0, float((m.fisher_p - m.p_value_two_sided).abs().max()), 1e-12, f"{len(m)} rows")
# ledger summary recomputed
lsum = T("tests_ledger_summary")
led["qid"] = led.test_id.str.split("_").str[0]
mine = led.groupby(["qid", "primary_or_exploratory"]).agg(n=("test_id", "size"), k=("p_value_two_sided", lambda p: int((p < 0.05).sum()))).reset_index()
mm = lsum.merge(mine, on=["qid", "primary_or_exploratory"])
check("ledger summary recount (rows with mismatch)", 0, int(((mm.n_tests != mm.n) | (mm.n_p_below_05 != mm.k)).sum()), 0)
# same pair tested twice with different p-values (direction-dependent NW correlation t)
dup = {"Q2_corr_EMV_env_VIX_full": "Q5_corr_VIX_level_EMV_env_overlap", "Q2_corr_z_EMV_env_z_VIX_full": "Q5_corr_VIX_z_EMV_env_overlap",
       "Q2_corr_z_EMV_env_z_EMV_overall_full": "Q5_corr_EMV_overall_z_EMV_env_overlap", "Q2_corr_EMV_env_EMV_overall_full": "Q5_corr_EMV_overall_level_EMV_env_overlap"}
lp = led.set_index("test_id")
RES.append(dict(claim="round-1 duplicate pairs still present in ledger", builder="4 pairs (round 1)",
                verifier=str(sum(a in lp.index and b in lp.index for a, b in dup.items())), tol=np.nan, status="info",
                note="round 2 dedups by hypothesis key; see verify_m1_round2.py"))
for a, b in dup.items():
    if a in lp.index and b in lp.index:
        RES.append(dict(claim=f"duplicate test in ledger: {a} vs {b}", builder=f"r={lp.loc[a, 'statistic']:.3f} p={lp.loc[a, 'p_value_two_sided']:.2e}",
                        verifier=f"r={lp.loc[b, 'statistic']:.3f} p={lp.loc[b, 'p_value_two_sided']:.2e}", tol=np.nan,
                        status="MISMATCH" if abs(np.log10(lp.loc[a, 'p_value_two_sided']) - np.log10(lp.loc[b, 'p_value_two_sided'])) > 0.5 else "info",
                        note="same correlation, same sample, different NW p because the regression direction differs"))
        print(f"  dup {a}: p={lp.loc[a, 'p_value_two_sided']:.2e} vs {b}: p={lp.loc[b, 'p_value_two_sided']:.2e}")
# headline numbers that have no ledger entry
for tid in ["Q5_corr_EMV_env_share_z_MCCC", "Q5_corr_MCCC_z_EMV_env_share_common"]:
    print(f"  ledger has {tid}? {tid in lp.index}")
has_share_mccc = any(("EMV_env_share" in t and "MCCC" in t) for t in lp.index)
check("ledger contains share-vs-MCCC / share-vs-CPU correlation tests (headline numbers)", True, has_share_mccc, 0)

# ----------------------------------------------------------------------------- V10 FINDINGS text vs CSV spot checks
std12 = T("standardized_measures_12m").set_index("date")
check("text: EMV_env 12m std peak", 0.96, round(std12.EMV_env.max(), 2), 0.005)
dec = T("decomposition"); dts = dec[(dec.block == "team_signal_z") & (dec.regressors == "z_VIX + z_EMV_overall")].set_index("sample")
for s, cl in (("pre_2021-10", 0.161), ("validation", 0.166), ("holdout", 0.267), ("post_2021-10", 0.281)):
    check(f"text: joint R2 {s}", cl, round(dts.loc[s, "r2"], 3), 5e-4)
ct = T("contemporaneous").set_index(["shock", "outcome", "spec", "period"])
check("text: MCCC leg green excess slope", 0.75, round(ct.loc[("MCCC", "green_excess", "none", "full"), "slope_pct_per_sd"], 2), 0.005)
check("text: MCCC leg brown excess slope", 0.84, round(ct.loc[("MCCC", "brown_excess", "none", "full"), "slope_pct_per_sd"], 2), 0.005)
icsg = T("ic_sign_stability").set_index(["outcome", "signal"])
for o_ in ("GB", "brown_resid_FF3"):
    for s_ in ("z_MCCC", "shock_MCCC"):
        v_, h_ = icsg.loc[(o_, s_), "validation"], icsg.loc[(o_, s_), "holdout"]
        claim_same = s_ == "z_MCCC"      # round-2 text: z_MCCC keeps its sign, shock_MCCC flips
        check(f"sign stability {s_} -> {o_} (text: {'keeps sign' if claim_same else 'flips'})", "same" if claim_same else "flips",
              "same" if np.sign(v_) == np.sign(h_) else "flips", 0, f"validation {v_:+.3f}, holdout {h_:+.3f}")
ctt = T("contemporaneous").set_index(["shock", "outcome", "spec", "period"]).loc[("CPU", "green_minus_brown", "none", "full"), "t_nw"]
check("text Q6a CPU t printed as -1.23", -1.23, round(ctt, 2), 0.005, f"CSV t = {ctt:.4f}")

# ----------------------------------------------------------------------------- V11 counterfactuals for the 'different signal' claim
H = slice("2022-08-31", "2026-07-31")
base_cross = [ym(t) for t in cross.loc[H][cross.loc[H]].index]
# (B) window moments frozen at the pre-regime 2021-09 window, same past-only threshold
w = lz.loc[:"2021-09-30"].iloc[-60:]
zB = (lz - w.mean()) / w.std(ddof=1)
stB = (zB > thr) & thr.notna()
crB = stB & ~stB.shift(1, fill_value=False)
# (A) zeros treated as missing, rolling moments over nonzero months (min 12), threshold rebuilt on this z
lzn = lz.where(emv_env > 0)
zA = zscore60(lzn.dropna(), minp=12).reindex(lz.index)
thrA = past_q80(zA); stA = (zA > thrA) & thrA.notna(); crA = stA & ~stA.shift(1, fill_value=False)
for lab, c_ in (("frozen 2021-09 scaling", crB), ("zeros as missing", crA)):
    alt = [ym(t) for t in c_.loc[H][c_.loc[H]].index]
    RES.append(dict(claim=f"holdout crossings under counterfactual: {lab}", builder=f"baseline {base_cross}", verifier=str(alt), tol=np.nan,
                    status="info", note="identical" if alt == base_cross else "differs"))
    print(f"  counterfactual {lab}: {alt} vs baseline {base_cross}")
print("  EMV_env at holdout crossings:", emv_env.reindex(cross.loc[H][cross.loc[H]].index).round(3).tolist())
nzh = emv_env.loc[H][emv_env.loc[H] > 0]; pzr = emv_env.shift(1).reindex(nzh.index).eq(0).mean()
RES.append(dict(claim="base rate: holdout nonzero months that follow a zero month", builder="'all 5 entries followed a zero month'",
                verifier=f"{pzr:.3f} of 17 -> P(5 of 5) = {pzr ** 5:.3f}", tol=np.nan, status="info"))
print(f"  base rate of nonzero-after-zero among holdout nonzero months: {pzr:.3f}; P(5/5) = {pzr ** 5:.3f}")

# ----------------------------------------------------------------------------- V12 channel of the CPU correlation, and the 'lowest when concern highest' claim
dd = pd.concat([z_env.rename("z"), z_all.rename("zo"), z_cpu.rename("zc")], axis=1).dropna()
rz_ = dd.z - np.polyval(np.polyfit(dd.zo, dd.z, 1), dd.zo); rc_ = dd.zc - np.polyval(np.polyfit(dd.zo, dd.zc, 1), dd.zo)
RES.append(dict(claim="partial corr(z_CPU, z_EMV_env | z_EMV_overall)", builder="raw corr 0.123 (p 0.037)", verifier=f"{rz_.corr(rc_):.3f} (n={len(dd)})",
                tol=np.nan, status="info"))
print(f"  partial corr(z_CPU, z_EMV_env | z_EMV_overall) = {rz_.corr(rc_):.3f}")
x_ = np.log1p(emv_env.loc["2003-01-31":"2025-06-30"]); zx_ = (x_ - x_.mean()) / x_.std(ddof=1)
xn_ = x_.where(emv_env.loc["2003-01-31":"2025-06-30"] > 0); zxn_ = (xn_ - xn_.mean()) / xn_.std(ddof=1)
a_, b_ = zx_.rolling(12).mean().loc["2022":"2024"], zxn_.rolling(12, min_periods=3).mean().loc["2022":"2024"]
check("std12 EMV_env 2022-2024 min (with zeros)", -1.16, round(a_.min(), 2), 0.005)
RES.append(dict(claim="std12 EMV_env 2022-2024 range with zeros excluded", builder="-1.16 to -0.08 sd ('lowest when concern highest')",
                verifier=f"{b_.min():.2f} to {b_.max():.2f} sd", tol=np.nan, status="info"))
print(f"  2022-2024 12m standardized EMV_env, zeros excluded: {b_.min():.2f} to {b_.max():.2f}")

out = pd.DataFrame(RES)
out.to_csv(HERE / "verify_results.csv", index=False)
print(f"\n{(out.status == 'match').sum()} match, {(out.status == 'MISMATCH').sum()} mismatch, {(out.status == 'info').sum()} info rows")
print(out[out.status == "MISMATCH"].to_string())
