"""Independent verification of M8 (frozen EMV-share rule, 1993-2009).

Written from the frozen rule text and PREREGISTRATION.md only. It does NOT import run.py, verify_signal.py,
lib/team_pipeline.py or lib/common.py. Every input is parsed from the raw files; every step (signal, holds,
rolling hedge, vol target, P&L with costs, BOND, Newey-West, shuffle) is re-implemented with plain loops,
numpy and statsmodels. M8's published CSVs are read only at the end, to compare numbers.

Run: cd /home/hashim/projects/GA/project/research && uv run python modules/M8_frozen_pre2010/verify/verify_m8.py
"""
from __future__ import annotations

import pathlib
import re

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

RES = pathlib.Path("/home/hashim/projects/GA/project/research")
RAW = RES / "data" / "raw"
TEAM = RES.parent / "230GA-Final-Project" / "data"          # read only
TAB = RES / "outputs" / "tables"
OUT = pathlib.Path(__file__).resolve().parent
BROWN = ["Util", "Ships", "Aero", "Steel", "BldMt"]


# ------------------------------------------------------------------ raw loaders (own parsers)
def fred(sid, daily_mean=False):
    df = pd.read_csv(RAW / f"fred_{sid}.csv")
    df.columns = ["date", "v"]
    df["date"] = pd.to_datetime(df["date"])
    s = pd.to_numeric(df["v"], errors="coerce")
    s.index = df["date"]
    if daily_mean:
        return s.groupby(s.index.to_period("M")).mean().to_timestamp("M").rename(sid)
    s.index = s.index + pd.offsets.MonthEnd(0)
    return s.rename(sid)


def kf_first_monthly(path):
    lines = pathlib.Path(path).read_text(errors="ignore").splitlines()
    hdr = None
    rows = []
    for ln in lines:
        if hdr is None:
            if ln.strip().startswith(",") and len(ln.split(",")) > 1:
                hdr = [c.strip() for c in ln.split(",")[1:]]
            continue
        m = re.match(r"^\s*(\d{6})\s*,", ln)
        if not m:
            if rows:
                break
            continue
        parts = [p.strip() for p in ln.split(",")]
        rows.append([parts[0]] + [float(x) for x in parts[1:]])
    df = pd.DataFrame(rows, columns=["ym"] + hdr)
    df.index = pd.to_datetime(df["ym"], format="%Y%m") + pd.offsets.MonthEnd(0)
    return df.drop(columns="ym").replace([-99.99, -999.0], np.nan) / 100


def team_csv(name):
    d = pd.read_csv(TEAM / name, parse_dates=["date"]).set_index("date")
    d.index = d.index + pd.offsets.MonthEnd(0)
    return d


env, ovr = fred("EMVENRGYENVREG"), fred("EMVOVERALLEMV")
vix = fred("VIXCLS", daily_mean=True)
wti, gs10 = fred("MCOILWTICO"), fred("GS10")
ff5 = kf_first_monthly(RAW / "kf_F-F_Research_Data_5_Factors_2x3.csv")
mom = kf_first_monthly(RAW / "kf_F-F_Momentum_Factor.csv")
ind, ff3 = team_csv("ff49_industry_monthly.csv"), team_csv("ff3_factors_monthly.csv")

# ------------------------------------------------------------------ 1. signal, brute force (data-month time)
grid = pd.date_range(min(env.index.min(), ovr.index.min()), max(env.index.max(), ovr.index.max()), freq="ME")
E, O = env.reindex(grid).to_numpy(), ovr.reindex(grid).to_numpy()
n = len(grid)
z = np.full(n, np.nan)
nz_count = np.zeros(n, int)
zero_count = np.zeros(n, int)
for t in range(n):
    lo = max(0, t - 59)
    we, wo = E[lo:t + 1], O[lo:t + 1]
    good = (we > 0) & (wo > 0) & ~np.isnan(we) & ~np.isnan(wo)
    nz_count[t], zero_count[t] = good.sum(), (we == 0).sum()
    if not good[-1]:
        continue                      # a zero month is missing: no z
    if good.sum() < 48:
        continue                      # needs >= 48 nonzero months in the trailing 60
    if (we == 0).sum() > 6:
        continue                      # > 10% of trailing 60 zero -> signal off
    x = np.log(we[good] / wo[good])
    z[t] = (np.log(E[t] / O[t]) - x.mean()) / x.std(ddof=1)
thr = np.full(n, np.nan)
for t in range(n):
    past = z[:t][~np.isnan(z[:t])]    # past-only, zero/off months never enter
    if len(past) >= 60:
        thr[t] = np.percentile(past, 80)
valid = ~np.isnan(z) & ~np.isnan(thr)
ext = valid & (z > thr)
cross = np.zeros(n, bool)
prev = False
for t in range(n):
    if valid[t]:
        cross[t] = ext[t] and not prev
        prev = ext[t]
# alternative (team-style, zero month breaks a run) for sensitivity
cross_alt = ext & ~np.r_[False, ext[:-1]]
sig = pd.DataFrame({"z": z, "thr": thr, "valid": valid, "ext": ext, "cross": cross, "cross_alt": cross_alt,
                    "zero": E == 0, "zeros60": zero_count, "nz60": nz_count}, index=grid)

first_z = sig.index[~np.isnan(z)][0]
first_thr = sig.index[valid][0]
print(f"[signal] first z {first_z:%Y-%m}; first valid threshold (data month) {first_thr:%Y-%m}")
pre = sig.loc[:"2009-12"]
print(f"[signal] zero months <= 2009: {int(pre.zero.sum())} ({', '.join(f'{d:%Y-%m}' for d in pre.index[pre.zero])}); "
      f"off months (valid-z blocked by >6 zeros) <= 2009: {int(((pre.zeros60 > 6) & ~pre.zero).sum())}")
print(f"[signal] crossings with skip-missing vs zero-breaks-run differ before 2010 in {int((pre.cross != pre.cross_alt).sum())} months")

# ------------------------------------------------------------------ 2. decision-time holds (lag 1, hold 6, extend not stack)
dgrid = pd.date_range("1926-07-31", "2026-09-30", freq="ME")
cross_dec = pd.Series(False, index=dgrid)
for t in sig.index[sig.cross]:
    cross_dec[t + pd.offsets.MonthEnd(1)] = True          # usable at the end of t+1
hold = pd.Series(False, index=dgrid)
cd = cross_dec.to_numpy()
hv = np.zeros(len(dgrid), bool)
for i in range(len(dgrid)):
    hv[i] = cd[max(0, i - 5):i + 1].any()                  # on at the crossing's decision month and next 5
hold[:] = hv

tau0 = first_thr + pd.offsets.MonthEnd(1)                  # first decision month with a defined flag
W0 = max(pd.Timestamp("1993-01-31"), tau0 + pd.offsets.MonthEnd(1))
WEND = pd.Timestamp("2009-12-31")
win = pd.date_range(W0, WEND, freq="ME")
dec_lo, dec_hi = W0 - pd.offsets.MonthEnd(1), WEND - pd.offsets.MonthEnd(1)
print(f"[window] tau0 (first decision month) {tau0:%Y-%m}; return window {W0:%Y-%m} to {WEND:%Y-%m} ({len(win)} months)")
fc = sig.index[sig.cross & (sig.index >= first_thr)][0]
print(f"[window] first crossing (data month) {fc:%Y-%m} -> decision {fc + pd.offsets.MonthEnd(1):%Y-%m}")


def runs(mask):
    out, i = [], 0
    while i < len(mask):
        if mask[i]:
            j = i
            while j + 1 < len(mask) and mask[j + 1]:
                j += 1
            out.append((i, j))
            i = j + 1
        else:
            i += 1
    return out


seg = hold.loc[dec_lo:dec_hi].to_numpy()
blocks = runs(seg)
episodes = [(hold.loc[dec_lo:dec_hi].index[a], hold.loc[dec_lo:dec_hi].index[b], b - a + 1) for a, b in blocks]
print(f"[episodes] {len(episodes)} merged runs in decision months {dec_lo:%Y-%m}..{dec_hi:%Y-%m}: "
      + ", ".join(f"{a:%Y-%m}..{b:%Y-%m} ({L})" for a, b, L in episodes))
# are there runs separated by exactly one flat month (a stricter 'touch' reading would merge them)?
gaps = [blocks[i + 1][0] - blocks[i][1] - 1 for i in range(len(blocks) - 1)]
print(f"[episodes] flat gaps between runs (months): {gaps}")
n_cross_in = int(cross_dec.loc[dec_lo - pd.offsets.MonthEnd(5):dec_hi].sum())
print(f"[episodes] lagged crossings whose hold touches the window: {n_cross_in}")


# ------------------------------------------------------------------ 3. strategy engine (own implementation)
def engine(members, hold_bool):
    leg = ind[members].mean(axis=1) - ff3["RF"]
    df = pd.concat([leg.rename("y"), ff3[["Mkt-RF", "SMB", "HML"]]], axis=1).dropna()
    Y, F = df["y"].to_numpy(), df[["Mkt-RF", "SMB", "HML"]].to_numpy()
    T = len(df)
    a = np.full(T, np.nan)
    B = np.full((T, 3), np.nan)
    for t in range(59, T):
        Xw = np.column_stack([np.ones(60), F[t - 59:t + 1]])
        c = np.linalg.lstsq(Xw, Y[t - 59:t + 1], rcond=None)[0]
        a[t], B[t] = c[0], c[1:]
    eps = np.full(T, np.nan)
    eps[1:] = Y[1:] - (B[:-1] * F[1:]).sum(1) - a[:-1]
    sig36 = pd.Series(eps).rolling(36, min_periods=36).std(ddof=1).to_numpy()
    mag = np.minimum(0.05 / (np.sqrt(12) * sig36), 1.0)
    idx = df.index
    hb = hold_bool.reindex(idx, fill_value=False).to_numpy()
    h = np.where(np.isnan(mag), 0.0, np.where(hb, -mag, 0.0))
    ov = -h[:, None] * np.nan_to_num(B)
    gross = np.full(T, np.nan)
    gross[1:] = h[:-1] * (Y[1:] - (np.nan_to_num(B[:-1]) * F[1:]).sum(1))
    dh = np.abs(np.diff(h, prepend=0.0))
    dov = np.abs(np.diff(ov, axis=0, prepend=np.zeros((1, 3))))
    cost = 10e-4 * dh + 5e-4 * dov[:, 0] + 25e-4 * (dov[:, 1] + dov[:, 2])
    net = gross - np.r_[0.0, cost[:-1]]                     # trade at t charged at t+1
    return pd.DataFrame({"h": h, "net": net, "mag": mag}, index=idx)


# ------------------------------------------------------------------ 4. attribution factors (own BOND)
def par_price(y, cpn, periods_left):
    k = np.arange(1, 21)
    cf = np.full(20, 100 * cpn / 2)
    cf[-1] += 100
    return (cf / (1 + y / 2) ** (k - periods_left)).sum()


yv = (gs10 / 100)
Dm, Cx = pd.Series(np.nan, yv.index), pd.Series(np.nan, yv.index)
for t, y in yv.items():                                     # numerical derivatives of the par-bond price
    h_ = 1e-5
    P0, Pu, Pd = par_price(y, y, 0), par_price(y + h_, y, 0), par_price(y - h_, y, 0)
    Dm[t] = -(Pu - Pd) / (2 * h_) / P0
    Cx[t] = (Pu - 2 * P0 + Pd) / h_ ** 2 / P0
dy = yv.diff()
bond_tot = yv.shift(1) / 12 - Dm.shift(1) * dy + 0.5 * Cx.shift(1) * dy ** 2
BOND = (bond_tot - ff5["RF"]).rename("BOND")
fac = ff5[["Mkt-RF", "SMB", "HML", "RMW", "CMA"]].join(mom.iloc[:, 0].rename("UMD"))
fac["BOND"] = BOND
fac["WTI"] = np.log(wti).diff()
fac["dVIX"] = vix.diff()
fac["dlogEMV"] = np.log(ovr).diff()
UNC = ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "UMD", "BOND", "WTI", "dVIX", "dlogEMV"]
CON = ["Mkt-RF", "HML", "BOND", "dVIX"]
b22 = (1 + bond_tot.loc["2022"]).prod() - 1
print(f"[BOND] 2022 total return {b22:+.4f}; 1994 {(1 + bond_tot.loc['1994']).prod() - 1:+.4f}; "
      f"mean modified duration 1993-2009 {Dm.loc['1993':'2009'].mean():.2f}")


def attribution(tim, ao, window, lags=6):
    hT, hA = tim["h"].shift(1).reindex(window), ao["h"].shift(1).reindex(window)
    pi = hT.abs().mean() / hA.abs().mean()
    D = tim["net"].reindex(window) - pi * ao["net"].reindex(window)
    I = (hT != 0).astype(float)
    X = fac.reindex(window)[UNC].copy()
    for c in CON:
        X["Ix" + c] = I * X[c]
    d = pd.concat([D.rename("D"), X], axis=1).dropna()
    mod = sm.OLS(d["D"], sm.add_constant(d[X.columns]))
    r = mod.fit(cov_type="HAC", cov_kwds={"maxlags": lags, "use_correction": False})
    k = len(r.params)
    t_a = r.params["const"] / r.bse["const"]
    return {"alpha_ann": 12 * r.params["const"], "t": t_a, "p": 2 * stats.t.sf(abs(t_a), len(d) - k), "n": len(d), "k": k,
            "pi": pi, "inpos": int(I.sum()), "D": D, "res": r, "X": d[X.columns], "meanD": d["D"].mean()}


ao_full = engine(BROWN, pd.Series(True, index=dgrid))
tim = engine(BROWN, hold)
A6 = attribution(tim, ao_full, win, 6)
A12 = attribution(tim, ao_full, win, 12)
print(f"[alpha] n={A6['n']} k={A6['k']} pi={A6['pi']:.4f} in-position months={A6['inpos']}")
print(f"[alpha] timing alpha {A6['alpha_ann']:+.5f}/yr  NW6 t {A6['t']:+.3f}  p t(n-k) {A6['p']:.3f}  |  NW12 t {A12['t']:+.3f}")
# decomposition identity
r = A6["res"]
dec = r.params["const"] + (r.params.drop("const") * A6["X"].mean()).sum()
print(f"[alpha] decomposition identity: mean(D) {12 * A6['meanD']:+.6f} vs alpha + sum b*mean(F) {12 * dec:+.6f}")
with_corr = sm.OLS(A6["D"].dropna(), sm.add_constant(A6["X"])).fit(cov_type="HAC", cov_kwds={"maxlags": 6, "use_correction": True})
print(f"[alpha] NW6 with n/(n-k) small-sample correction: t {with_corr.params['const'] / with_corr.bse['const']:+.3f}")

# ------------------------------------------------------------------ 5. leave-one-industry-out
loo = []
for j in BROWN:
    mem = [b for b in BROWN if b != j]
    a_j = attribution(engine(mem, hold), engine(mem, pd.Series(True, index=dgrid)), win, 6)
    loo.append((j, a_j["alpha_ann"], a_j["t"]))
print("[LOO] " + ", ".join(f"{j} {a:+.5f} (t {t:+.2f})" for j, a, t in loo))
print(f"[LOO] same sign as base alpha: {sum(np.sign(a) == np.sign(A6['alpha_ann']) for _, a, _ in loo)} of 5; positive: {sum(a > 0 for _, a, _ in loo)} of 5")

# ------------------------------------------------------------------ 6. calendar shuffle (own draw scheme, own seed)
seg_idx = hold.loc[dec_lo:dec_hi].index
L = np.array([b - a + 1 for a, b in blocks])
N, m = len(seg), len(L)
free = N - L.sum() - (m - 1)
print(f"[shuffle] N={N} decision months, {m} blocks, {L.sum()} on-months, free slack for placement = {free}")

# precompute a fast version of engine pieces for the Brown leg
leg = ind[BROWN].mean(axis=1) - ff3["RF"]
base = engine(BROWN, pd.Series(True, index=dgrid))            # magnitudes when always on
mag_s = (-base["h"]).reindex(dgrid)                            # |position| if on
dfm = pd.concat([leg.rename("y"), ff3[["Mkt-RF", "SMB", "HML"]]], axis=1).dropna()


def fast_setup():
    idx = dfm.index
    Y, F = dfm["y"].to_numpy(), dfm[["Mkt-RF", "SMB", "HML"]].to_numpy()
    T = len(idx)
    B = np.full((T, 3), np.nan)
    for t in range(59, T):
        Xw = np.column_stack([np.ones(60), F[t - 59:t + 1]])
        B[t] = np.linalg.lstsq(Xw, Y[t - 59:t + 1], rcond=None)[0][1:]
    return idx, Y, F, np.nan_to_num(B)


fidx, fY, fF, fB = fast_setup()
fmag = mag_s.reindex(fidx).fillna(0).to_numpy()
wpos = np.array([fidx.get_loc(t) for t in win])
d0 = fidx.get_loc(dec_lo)
hA_abs = fmag[wpos - 1]
nA = ao_full["net"].reindex(fidx).to_numpy()[wpos]
Xu = fac.reindex(win)[UNC].to_numpy()
Xc = fac.reindex(win)[CON].to_numpy()
real_hold = hold.reindex(fidx, fill_value=False).to_numpy()


def nw_alpha(y, X, lags=6):
    Xc_ = np.column_stack([np.ones(len(y)), X])
    XtX = np.linalg.inv(Xc_.T @ Xc_)
    b = XtX @ Xc_.T @ y
    u = Xc_ * (y - Xc_ @ b)[:, None]
    S = u.T @ u
    for l in range(1, lags + 1):
        G = u[l:].T @ u[:-l]
        S += (1 - l / (lags + 1)) * (G + G.T)
    V = XtX @ S @ XtX
    return b[0], b[0] / np.sqrt(V[0, 0])


def alpha_for(hb):
    h = np.where(hb, -fmag, 0.0)
    ov = -h[:, None] * fB
    gross = np.r_[np.nan, h[:-1] * (fY[1:] - (fB[:-1] * fF[1:]).sum(1))]
    cost = 10e-4 * np.abs(np.diff(h, prepend=0.0)) + (np.abs(np.diff(ov, axis=0, prepend=np.zeros((1, 3)))) * [5e-4, 25e-4, 25e-4]).sum(1)
    net = gross - np.r_[0.0, cost[:-1]]
    hT = h[wpos - 1]
    pi = np.abs(hT).mean() / hA_abs.mean()
    D = net[wpos] - pi * nA
    I = (hT != 0).astype(float)
    return nw_alpha(D, np.column_stack([Xu, I[:, None] * Xc]))


a_real, t_real = alpha_for(real_hold)
print(f"[shuffle] fast-path real alpha {12 * a_real:+.5f} t {t_real:+.3f} (must equal the statsmodels result above)")
rng = np.random.Generator(np.random.PCG64(20260926))
R = 5000
draws = np.empty(R)
for b in range(R):
    # uniform over gap vectors (g0>=0, g1..g_{m-1}>=1, gm>=0): draw a random composition by sorting uniforms
    cuts = np.sort(rng.integers(0, free + 1, size=m))            # m cut points in 0..free (with repetition)
    g = np.diff(np.r_[0, cuts, free])                             # m+1 nonnegative parts summing to free
    g[1:m] += 1
    order = rng.permutation(L)
    hb = real_hold.copy()
    hb[d0:d0 + N] = False
    pos = g[0]
    for i in range(m):
        hb[d0 + pos:d0 + pos + order[i]] = True
        pos += order[i] + (g[i + 1] if i + 1 < m else 0)
    draws[b] = alpha_for(hb)[0]
p_up = (1 + (draws >= a_real).sum()) / (R + 1)
print(f"[shuffle] own scheme (random multiset composition, PCG64 seed 20260926, {R} draws): one-sided p {p_up:.3f}; "
      f"median {12 * np.median(draws):+.5f}; 5-95% {12 * np.quantile(draws, .05):+.5f} to {12 * np.quantile(draws, .95):+.5f}")
print("[shuffle] note: sorted integers with repetition give a NON-uniform composition law; used only as a robustness null")

# exact uniform scheme, different generator, for the pass-bar comparison
rng2 = np.random.Generator(np.random.PCG64(7))
draws2 = np.empty(R)
for b in range(R):
    sel = np.sort(rng2.choice(free + m, size=m, replace=False))
    g0 = sel[0]
    order = rng2.permutation(L)
    hb = real_hold.copy()
    hb[d0:d0 + N] = False
    starts = sel + np.r_[0, np.cumsum(order)[:-1]]
    for s_, l_ in zip(starts, order):
        hb[d0 + s_:d0 + s_ + l_] = True
    draws2[b] = alpha_for(hb)[0]
p_up2 = (1 + (draws2 >= a_real).sum()) / (R + 1)
print(f"[shuffle] uniform scheme, PCG64 seed 7: one-sided p {p_up2:.3f}; median {12 * np.median(draws2):+.5f}; "
      f"95th pct {12 * np.quantile(draws2, .95):+.5f}")

# ------------------------------------------------------------------ 7. sensitivity: nominal 1993-01 start, and zero-breaks-run crossings
win93 = pd.date_range("1993-01-31", WEND, freq="ME")
A93 = attribution(tim, ao_full, win93, 6)
print(f"[sens] window 1993-01..2009-12 (n={A93['n']}): alpha {A93['alpha_ann']:+.5f} t {A93['t']:+.3f}")

# ------------------------------------------------------------------ 8. compare with M8 published outputs
m8x = pd.read_csv(TAB / "M8_crossings.csv")
mine_x = [f"{t:%Y-%m}" for t in sig.index[sig.cross] if dec_lo - pd.offsets.MonthEnd(5) <= t + pd.offsets.MonthEnd(1) <= dec_hi]
print(f"[compare] crossings: mine {len(mine_x)}, M8 {len(m8x)}, identical list: {mine_x == list(m8x.data_month)}")
m8p = pd.read_csv(TAB / "M8_monthly_panel.csv", index_col=0, parse_dates=True)
zc = m8p["share_z"].reindex(grid)
print(f"[compare] z max|diff| vs M8 panel (1985-2010): {np.nanmax(np.abs(zc.loc[:'2010'].to_numpy() - sig.z.loc[:'2010'].to_numpy())):.2e}; "
      f"threshold max|diff|: {np.nanmax(np.abs(m8p['share_threshold'].reindex(grid).loc[:'2010'].to_numpy() - sig.thr.loc[:'2010'].to_numpy())):.2e}")
dm = m8p["D_primary"].reindex(win)
print(f"[compare] D_t max|diff| vs M8 panel: {np.nanmax(np.abs(dm.to_numpy() - A6['D'].to_numpy())):.2e}; "
      f"net timed max|diff|: {np.nanmax(np.abs(m8p['net_primary'].reindex(win).to_numpy() - tim['net'].reindex(win).to_numpy())):.2e}")
m8a = pd.read_csv(TAB / "M8_attribution.csv")
r0 = m8a[(m8a.signal.str.startswith("Frozen")) & (m8a.term == "const")].iloc[0]
print(f"[compare] M8 alpha {12 * r0.coef:+.5f} t {r0.t_nw6:+.3f}; mine {A6['alpha_ann']:+.5f} t {A6['t']:+.3f}; "
      f"diff alpha {abs(12 * r0.coef - A6['alpha_ann']):.1e}, diff t {abs(r0.t_nw6 - A6['t']):.1e}")
m8d = pd.read_csv(TAB / "M8_drop_one.csv")
m8d = m8d[m8d.signal.str.startswith("Frozen")].set_index("dropped")
print("[compare] LOO alpha diffs: " + ", ".join(f"{j} {abs(m8d.loc[j, 'alpha_ann'] - a):.1e}" for j, a, _ in loo))
m8b = pd.read_csv(TAB / "M8_monthly_panel.csv", index_col=0, parse_dates=True)["BOND" if False else "net_always"]
pd.DataFrame({"z": sig.z, "thr": sig.thr, "cross": sig.cross}).to_csv(OUT / "verify_signal_out.csv")
pd.DataFrame({"hold": hold.loc[dec_lo:dec_hi]}).to_csv(OUT / "verify_hold_out.csv")
print("done")
