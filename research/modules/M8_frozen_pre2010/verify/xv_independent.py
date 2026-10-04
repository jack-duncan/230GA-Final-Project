"""Adversarial re-computation of M8 (frozen EMV-share rule, 1993-2009), written from PREREGISTRATION.md only.

Does NOT import run.py, verify_signal.py, verify_m8.py, lib/team_pipeline.py or lib/common.py.
Raw files are parsed here; signal, holds, hedge, vol target, costs, P&L, BOND, Newey-West, shuffle,
episodes and drop-one are re-implemented with explicit loops / numpy. M8's published tables are read
only at the end, for comparison.

Run: cd /home/hashim/projects/GA/project/research && uv run python modules/M8_frozen_pre2010/verify/xv_independent.py
Writes: verify/xv_results.json, verify/xv_comparison.csv, verify/xv_crossings.csv, verify/xv_monthly.csv
"""
from __future__ import annotations

import json
import math
import pathlib
import re

import numpy as np
import pandas as pd
from scipy import stats

RES = pathlib.Path("/home/hashim/projects/GA/project/research")
RAW = RES / "data" / "raw"
TEAMD = RES.parent / "230GA-Final-Project" / "data"      # read only
TAB = RES / "outputs" / "tables"
OUT = pathlib.Path(__file__).resolve().parent
BROWN = ["Util", "Ships", "Aero", "Steel", "BldMt"]
HOLD = 6
COST_ASSET, COST_MKT, COST_OTHER = 10e-4, 5e-4, 25e-4
UNCOND = ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "UMD", "BOND", "WTI", "dVIX", "dlogEMV"]
COND = ["Mkt-RF", "HML", "BOND", "dVIX"]
R = {}  # results


def me(x):
    return pd.DatetimeIndex(pd.to_datetime(x)) + pd.offsets.MonthEnd(0)


# ============================================================ raw loaders (own parsers)
def fred_monthly(sid):
    df = pd.read_csv(RAW / f"fred_{sid}.csv", dtype=str)
    v = pd.to_numeric(df.iloc[:, 1], errors="coerce").to_numpy()
    s = pd.Series(v, index=me(df.iloc[:, 0]))
    assert not s.index.duplicated().any()
    return s


def fred_daily_monthly_mean(sid):
    df = pd.read_csv(RAW / f"fred_{sid}.csv", dtype=str)
    d = pd.to_datetime(df.iloc[:, 0])
    v = pd.to_numeric(df.iloc[:, 1], errors="coerce")
    key = d.dt.year * 100 + d.dt.month
    m = pd.Series(v.to_numpy()).groupby(key.to_numpy()).mean()   # mean of available days
    idx = me(pd.to_datetime(m.index.astype(str), format="%Y%m"))
    return pd.Series(m.to_numpy(), index=idx)


def kf_first_monthly_block(path):
    rows, header = [], None
    for ln in pathlib.Path(path).read_text(errors="ignore").splitlines():
        if header is None:
            if ln.strip().startswith(","):
                header = [c.strip() for c in ln.split(",")[1:]]
            continue
        parts = [p.strip() for p in ln.split(",")]
        if re.fullmatch(r"\d{6}", parts[0] or ""):
            rows.append([parts[0]] + [float(x) for x in parts[1:len(header) + 1]])
        elif rows:
            break
    df = pd.DataFrame(rows, columns=["ym"] + header)
    df.index = me(pd.to_datetime(df["ym"], format="%Y%m"))
    df = df.drop(columns="ym").replace([-99.99, -999.0], np.nan) / 100.0
    return df


env = fred_monthly("EMVENRGYENVREG")
ovr = fred_monthly("EMVOVERALLEMV")
gs10 = fred_monthly("GS10")
wti = fred_monthly("MCOILWTICO")
vix = fred_daily_monthly_mean("VIXCLS")
ff5 = kf_first_monthly_block(RAW / "kf_F-F_Research_Data_5_Factors_2x3.csv")
mom = kf_first_monthly_block(RAW / "kf_F-F_Momentum_Factor.csv")
ind = pd.read_csv(TEAMD / "ff49_industry_monthly.csv")
ind.index = me(ind.pop("date"))
ff3 = pd.read_csv(TEAMD / "ff3_factors_monthly.csv")
ff3.index = me(ff3.pop("date"))

# ============================================================ 1. frozen signal (data-month time), explicit loops
g = pd.date_range(min(env.index.min(), ovr.index.min()), max(env.index.max(), ovr.index.max()), freq="ME")
E = env.reindex(g).to_numpy()
O = ovr.reindex(g).to_numpy()
n = len(g)
is_zero = E == 0.0
missing = is_zero | np.isnan(E) | np.isnan(O) | (O <= 0)
logs = np.full(n, np.nan)
logs[~missing] = np.log(E[~missing] / O[~missing])
z = np.full(n, np.nan)
nzero60 = np.zeros(n, int)
off = np.zeros(n, bool)
for t in range(n):
    lo = max(0, t - 59)
    nzero60[t] = int(is_zero[lo:t + 1].sum())
    off[t] = nzero60[t] > 6                      # more than 10% of 60 months zero
    if missing[t] or off[t]:
        continue
    w = logs[lo:t + 1]
    w = w[~np.isnan(w)]                          # zeros dropped from the z window
    if len(w) < 48:
        continue
    mu = sum(w) / len(w)
    sd = math.sqrt(sum((x - mu) ** 2 for x in w) / (len(w) - 1))
    z[t] = (logs[t] - mu) / sd


def q_linear(x, q):
    x = sorted(x)
    h = (len(x) - 1) * q
    lo = int(math.floor(h))
    return x[lo] if lo + 1 >= len(x) else x[lo] + (h - lo) * (x[lo + 1] - x[lo])


thr = np.full(n, np.nan)
hist = []
for t in range(n):
    if len(hist) >= 60:
        thr[t] = q_linear(hist, 0.80)             # past-only: strictly before t
    if not np.isnan(z[t]):
        hist.append(z[t])                        # zero / off months never enter the history
valid = ~np.isnan(z) & ~np.isnan(thr)
ext = valid & (z > thr)
cross = np.zeros(n, bool)
prev = False
for t in range(n):
    if valid[t]:
        cross[t] = ext[t] and not prev
        prev = ext[t]
# alternative crossing rule without skipping (a missing month breaks a run) -> sensitivity only
cross_noskip = np.zeros(n, bool)
for t in range(n):
    cross_noskip[t] = ext[t] and not (t > 0 and ext[t - 1])

sig = pd.DataFrame({"env": E, "overall": O, "zero": is_zero, "zeros60": nzero60, "off": off, "z": z, "thr": thr,
                    "valid": valid, "extreme": ext, "cross": cross, "cross_noskip": cross_noskip}, index=g)
pre = sig.loc[:"2009-12"]
R["signal"] = {
    "zero_months_pre2010": int(pre["zero"].sum()),
    "zero_months_list_pre2010": [d.strftime("%Y-%m") for d in pre.index[pre["zero"]]],
    "off_months_pre2010": int(pre["off"].sum()),
    "max_zeros_in_60_pre2010": int(pre["zeros60"].max()),
    "first_z_data_month": pre["z"].first_valid_index().strftime("%Y-%m"),
    "first_threshold_data_month": sig["thr"].first_valid_index().strftime("%Y-%m"),
    "first_valid_data_month": sig.index[sig["valid"]].min().strftime("%Y-%m"),
    "first_cross_data_month": sig.index[sig["cross"]].min().strftime("%Y-%m"),
    "crossings_pre2010": int(pre["cross"].sum()),
    "noskip_rule_differs_months_pre2010": int((pre["cross"] != pre["cross_noskip"]).sum()),
    "noskip_rule_differs_months_all": int((sig["cross"] != sig["cross_noskip"]).sum()),
    "off_months_all": int(sig["off"].sum()),
}

# ============================================================ 2. team secondary signal (log1p level, zeros kept)
la = np.log1p(E)
tz = np.full(n, np.nan)
for t in range(n):
    w = la[max(0, t - 59):t + 1]
    w = w[~np.isnan(w)]
    if len(w) >= 36 and not np.isnan(la[t]):
        mu = w.mean()
        sd = w.std(ddof=1)
        tz[t] = (la[t] - mu) / sd if sd > 0 else np.nan
tthr = np.full(n, np.nan)
h2 = []
for t in range(n):
    if len(h2) >= 60:
        tthr[t] = q_linear(h2, 0.80)
    if not np.isnan(tz[t]):
        h2.append(tz[t])
tstate = (tz > tthr) & ~np.isnan(tthr)
tcross = tstate & ~np.r_[False, tstate[:-1]]
sig["team_z"], sig["team_thr"], sig["team_cross"] = tz, tthr, tcross

# ============================================================ 3. engine grid, Brown leg, hedge, vol target
grid = pd.date_range("1975-01-31", "2026-07-31", freq="ME")
F3 = ff3.reindex(grid)
assert not F3[["Mkt-RF", "SMB", "HML", "RF"]].isna().any().any()
for b in BROWN:
    assert not ind[b].reindex(grid).isna().any(), b


def decision_hold(cross_data_bool: pd.Series):
    """lag one month (value for t usable at end of t+1), then on for decision months d..d+5 per crossing (union)."""
    h = pd.Series(False, index=grid)
    for t in cross_data_bool.index[cross_data_bool.to_numpy()]:
        d = t + pd.offsets.MonthEnd(1)
        for k in range(HOLD):
            dd = d + pd.offsets.MonthEnd(k)
            if dd in h.index:
                h[dd] = True
    return h


hold_P = decision_hold(sig["cross"])
hold_S = decision_hold(sig["team_cross"])


def brown_model(members):
    y = (ind[members].reindex(grid).mean(axis=1) - F3["RF"]).to_numpy()
    X = F3[["Mkt-RF", "SMB", "HML"]].to_numpy()
    N = len(grid)
    A = np.full(N, np.nan)
    B = np.full((N, 3), np.nan)
    for t in range(59, N):
        Xw = np.column_stack([np.ones(60), X[t - 59:t + 1]])
        coef = np.linalg.solve(Xw.T @ Xw, Xw.T @ y[t - 59:t + 1])   # normal equations (team uses lstsq)
        A[t], B[t] = coef[0], coef[1:]
    eps = np.full(N, np.nan)
    for t in range(60, N):
        eps[t] = y[t] - B[t - 1] @ X[t] - A[t - 1]      # betas and intercept through t-1 applied to t
    sig36 = np.full(N, np.nan)
    for t in range(N):
        w = eps[max(0, t - 35):t + 1]
        if t >= 35 and not np.isnan(w).any():
            sig36[t] = np.std(w, ddof=1)
    mag = np.minimum(0.05 / (math.sqrt(12) * sig36), 1.0)
    return {"y": y, "X": X, "B": B, "A": A, "eps": eps, "mag": mag}


def pnl(hold_bool: np.ndarray, M):
    """position h_t set at end of t earns t+1: h_t*y_{t+1} - h_t*beta_t'F_{t+1}; costs of trades at t charged at t+1."""
    N = len(grid)
    h = np.where(hold_bool, -M["mag"], 0.0)
    h = np.where(np.isnan(h), 0.0, h)                   # before the vol target exists: flat
    Ov = -h[:, None] * np.nan_to_num(M["B"])              # factor overlay
    net = np.full(N, np.nan)
    cost = np.zeros(N)
    for t in range(1, N):
        cost[t] = (COST_ASSET * abs(h[t] - h[t - 1]) + COST_MKT * abs(Ov[t, 0] - Ov[t - 1, 0])
                   + COST_OTHER * (abs(Ov[t, 1] - Ov[t - 1, 1]) + abs(Ov[t, 2] - Ov[t - 1, 2])))
    for t in range(1, N):
        gross = h[t - 1] * M["y"][t] + Ov[t - 1] @ M["X"][t]
        net[t] = gross - cost[t - 1]
    return h, net, cost


# ============================================================ 4. attribution factors
y10 = gs10 / 100
yl = y10.shift(1)
dy = y10 - yl


def par_price(c, y, T=10.0, m=2):
    """price per 1 of a bond with annual coupon c, yield y (semiannual), T years to maturity."""
    k = np.arange(1, int(round(T * m)) + 1)
    return (c / m * (1 + y / m) ** (-k)).sum() + (1 + y / m) ** (-len(k))


Dm = pd.Series(np.nan, index=y10.index)
Cv = pd.Series(np.nan, index=y10.index)
Dnum = pd.Series(np.nan, index=y10.index)
Cnum = pd.Series(np.nan, index=y10.index)
exact = pd.Series(np.nan, index=y10.index)
for t in y10.index:
    y0 = yl.get(t)
    if y0 is None or np.isnan(y0) or np.isnan(y10[t]):
        continue
    hstep = 1e-4
    p0, pu, pd_ = par_price(y0, y0), par_price(y0, y0 + hstep), par_price(y0, y0 - hstep)
    Dnum[t] = -(pu - pd_) / (2 * hstep) / p0                   # numerical modified duration (cross-check)
    Cnum[t] = (pu - 2 * p0 + pd_) / hstep ** 2 / p0             # numerical convexity (cross-check)
    kk = np.arange(1, 21)
    cf = np.full(20, y0 / 2)
    cf[-1] += 1.0
    v = 1 + y0 / 2
    P_ = (cf * v ** (-kk)).sum()                                # = 1 at par
    Dm[t] = (cf * (kk / 2) * v ** (-kk - 1)).sum() / P_         # analytic dP/dy / P
    Cv[t] = (cf * (kk / 2) * ((kk + 1) / 2) * v ** (-kk - 2)).sum() / P_   # analytic d2P/dy2 / P
    # exact: one month later, remaining 9y11m, dirty price at y_t
    k = np.arange(1, 21)
    tt = k / 2 - 1 / 12
    exact[t] = ((y0 / 2) * (1 + y10[t] / 2) ** (-2 * tt)).sum() + (1 + y10[t] / 2) ** (-2 * tt[-1]) - 1
bond_tot = yl / 12 - Dm * dy + 0.5 * Cv * dy ** 2
fac = pd.DataFrame(index=grid)
for c in ["Mkt-RF", "SMB", "HML", "RMW", "CMA"]:
    fac[c] = ff5[c].reindex(grid)
fac["UMD"] = mom.iloc[:, 0].reindex(grid)
fac["BOND"] = (bond_tot - ff5["RF"]).reindex(grid)
fac["WTI"] = np.log(wti).diff().reindex(grid)
fac["dVIX"] = vix.diff().reindex(grid)
fac["dlogEMV"] = np.log(ovr).diff().reindex(grid)

closed_D = (1 / yl) * (1 - (1 + yl / 2) ** (-20))
ann = (1 + bond_tot).groupby(bond_tot.index.year).prod() - 1
ann_ex = (1 + exact).groupby(exact.index.year).prod() - 1
R["bond"] = {
    "ann_total_2022": float(ann[2022]), "ann_exact_2022": float(ann_ex[2022]),
    "ann_total_1994": float(ann[1994]), "ann_total_2008": float(ann[2008]),
    "max_abs_D_analytic_minus_closed_form": float((Dm - closed_D).abs().max()),
    "max_abs_D_numeric_minus_analytic": float((Dnum - Dm).abs().max()),
    "max_rel_C_numeric_minus_analytic": float(((Cnum - Cv) / Cv).abs().max()),
    "max_abs_monthly_total_minus_exact_1993_2009": float((bond_tot - exact).loc["1993":"2009"].abs().max()),
    "mean_D_1990s": float(Dm.loc["1990":"1999"].mean()), "min_D_1990s": float(Dm.loc["1990":"1999"].min()),
    "max_D_1990s": float(Dm.loc["1990":"1999"].max()), "mean_y_1990s": float(y10.loc["1990":"1999"].mean()),
    "min_D_1993_2009": float(Dm.loc["1993":"2009"].min()), "max_D_1993_2009": float(Dm.loc["1993":"2009"].max()),
}


# ============================================================ 5. window, pi, D, regression with own NW
def nw(yv, Xv, L):
    Xc = np.column_stack([np.ones(len(yv)), Xv])
    XtXi = np.linalg.inv(Xc.T @ Xc)
    b = XtXi @ Xc.T @ yv
    u = yv - Xc @ b
    S = np.zeros((Xc.shape[1], Xc.shape[1]))
    T = len(yv)
    for t in range(T):
        S += np.outer(Xc[t] * u[t], Xc[t] * u[t])
    for lag in range(1, L + 1):
        wgt = 1 - lag / (L + 1)
        G = np.zeros_like(S)
        for t in range(lag, T):
            G += np.outer(Xc[t] * u[t], Xc[t - lag] * u[t - lag])
        S += wgt * (G + G.T)
    V = XtXi @ S @ XtXi
    return b, np.sqrt(np.diag(V)), u


# window per C12: tau0 = first decision month whose flag is defined (data month valid, +1)
first_valid = sig.index[sig["valid"]].min()
tau0 = first_valid + pd.offsets.MonthEnd(1)
W0 = max(pd.Timestamp("1993-01-31"), tau0 + pd.offsets.MonthEnd(1))
WEND = pd.Timestamp("2009-12-31")
win = pd.date_range(W0, WEND, freq="ME")
wpos = np.array([grid.get_loc(t) for t in win])
R["window"] = {"tau0": tau0.strftime("%Y-%m"), "W0": W0.strftime("%Y-%m"), "n_months": len(win)}


def attribution(hold_bool, M, lags=6, return_all=False):
    hT, netT, costT = pnl(hold_bool, M)
    hA, netA, _ = pnl(np.ones(len(grid), bool), M)
    hTl, hAl = hT[wpos - 1], hA[wpos - 1]
    pi = np.abs(hTl).mean() / np.abs(hAl).mean()
    D = netT[wpos] - pi * netA[wpos]
    I = (hTl != 0).astype(float)
    Xu = fac.loc[win, UNCOND].to_numpy()
    Xc = fac.loc[win, COND].to_numpy() * I[:, None]
    X = np.column_stack([Xu, Xc])
    ok = ~np.isnan(D) & ~np.isnan(X).any(1)
    b, se, u = nw(D[ok], X[ok], lags)
    nobs, k = int(ok.sum()), X.shape[1] + 1
    t_a = b[0] / se[0]
    out = {"alpha_m": b[0], "alpha_ann": 12 * b[0], "t": t_a, "n": nobs, "k": k, "df": nobs - k,
           "p_two": 2 * stats.t.sf(abs(t_a), nobs - k), "pi": pi, "months_in_pos": int(I.sum())}
    if return_all:
        means = np.r_[1.0, X[ok].mean(0)]
        out.update({"coef": b, "se": se, "contrib": b * means, "mean_D": D[ok].mean(), "resid_mean": u.mean(),
                    "D": D, "netT": netT[wpos], "netA": netA[wpos], "hTl": hTl, "costT": costT, "I": I,
                    "names": ["const"] + UNCOND + [f"I x {c}" for c in COND]})
    return out


MB = brown_model(BROWN)
hP = hold_P.to_numpy()
hS = hold_S.to_numpy()
aP = attribution(hP, MB, 6, True)
aP12 = attribution(hP, MB, 12)
aS = attribution(hS, MB, 6, True)
aS12 = attribution(hS, MB, 12)


def tmean(x, L=6):
    x = x[~np.isnan(x)]
    b, se, _ = nw(x, np.empty((len(x), 0)), L)
    return b[0] / se[0]


for lab, a, a12 in (("primary", aP, aP12), ("secondary", aS, aS12)):
    R[lab] = {k: (float(v) if isinstance(v, (float, np.floating, int, np.integer)) else v)
              for k, v in a.items() if k in ("alpha_m", "alpha_ann", "t", "n", "k", "df", "p_two", "pi", "months_in_pos")}
    R[lab]["t_nw12"] = float(a12["t"])
    R[lab]["p_nw12"] = float(a12["p_two"])
    R[lab]["timed_ann_net"] = float(12 * np.nanmean(a["netT"]))
    R[lab]["timed_t"] = float(tmean(a["netT"]))
    R[lab]["always_ann_net"] = float(12 * np.nanmean(a["netA"]))
    R[lab]["always_t"] = float(tmean(a["netA"]))
    R[lab]["D_ann_mean"] = float(12 * a["mean_D"])
    R[lab]["D_t"] = float(tmean(a["D"]))
    R[lab]["decomp_identity_gap"] = float(a["mean_D"] - a["contrib"].sum())
    R[lab]["resid_mean"] = float(a["resid_mean"])
    R[lab]["contrib_ann"] = {nm: float(12 * c) for nm, c in zip(a["names"], a["contrib"])}
    R[lab]["coef_t"] = {nm: [float(c), float(c / s)] for nm, c, s in zip(a["names"], a["coef"], a["se"])}


# ============================================================ 6. episodes
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


d_lo, d_hi = wpos[0] - 1, wpos[-1] - 1        # decision months W0-1 .. 2009-11


def episodes(hold_arr):
    eps = []
    for s, e in runs(hold_arr):
        if e >= d_lo and s <= d_hi:
            eps.append((grid[s].strftime("%Y-%m"), grid[e].strftime("%Y-%m"), e - s + 1))
    return eps


R["primary"]["episodes"] = episodes(hP)
R["secondary"]["episodes"] = episodes(hS)


# ============================================================ 7. drop-one
def drop_one(hold_arr):
    out = {}
    for j in BROWN:
        Mj = brown_model([b for b in BROWN if b != j])
        a = attribution(hold_arr, Mj, 6)
        out[j] = {"alpha_ann": float(a["alpha_ann"]), "t": float(a["t"]), "pi": float(a["pi"])}
    return out


R["primary"]["drop_one"] = drop_one(hP)
R["secondary"]["drop_one"] = drop_one(hS)


# ============================================================ 8. calendar shuffle
def shuffle(hold_arr, M, reps, seed, method):
    seg = hold_arr[d_lo:d_hi + 1]
    bl = runs(seg)
    L = np.array([e - s + 1 for s, e in bl])
    Nn, m = len(seg), len(L)
    free = Nn - L.sum() - (m - 1)
    # precompute the always-on pieces once
    hA, netA, _ = pnl(np.ones(len(grid), bool), M)
    hAl = np.abs(hA[wpos - 1]).mean()
    nA = netA[wpos]
    Xu = fac.loc[win, UNCOND].to_numpy()
    Xcnd = fac.loc[win, COND].to_numpy()
    mag = np.where(np.isnan(M["mag"]), 0.0, M["mag"])
    Bz = np.nan_to_num(M["B"])
    Xf = M["X"]
    y = M["y"]

    def alpha_fast(hb):
        h = np.where(hb, -mag, 0.0)
        Ov = -h[:, None] * Bz
        cost = np.r_[0.0, COST_ASSET * np.abs(np.diff(h)) + COST_MKT * np.abs(np.diff(Ov[:, 0]))
                     + COST_OTHER * (np.abs(np.diff(Ov[:, 1])) + np.abs(np.diff(Ov[:, 2])))]
        netT = h[wpos - 1] * y[wpos] + (Ov[wpos - 1] * Xf[wpos]).sum(1) - cost[wpos - 1]
        hTl = h[wpos - 1]
        pi = np.abs(hTl).mean() / hAl
        D = netT - pi * nA
        I = (hTl != 0).astype(float)
        X = np.column_stack([np.ones(len(D)), Xu, Xcnd * I[:, None]])
        b = np.linalg.lstsq(X, D, rcond=None)[0]
        return b[0]

    real = alpha_fast(hold_arr)
    rng = np.random.default_rng(seed)
    draws = np.empty(reps)
    arrangements = set()
    for r in range(reps):
        if method == "replicate":           # same generator calls as run.py (checks numbers draw by draw)
            order = rng.permutation(m)
            pos = np.sort(rng.choice(free + m, size=m, replace=False))
            Ls = L[order]
            starts = pos + np.r_[0, np.cumsum(Ls)[:-1]]
        else:                               # independent sampler: shuffle m labelled blocks among `free` unit gaps
            tokens = np.r_[np.arange(m), np.full(free, -1)]
            rng.shuffle(tokens)
            starts, Ls, cur, first = [], [], 0, True
            for tok in tokens:
                if tok < 0:
                    cur += 1
                else:
                    if not first:
                        cur += 1                # mandatory flat month between blocks
                    starts.append(cur)
                    Ls.append(L[tok])
                    cur += L[tok]
                    first = False
            starts, Ls = np.array(starts), np.array(Ls)
        hb = hold_arr.copy()
        hb[d_lo:d_hi + 1] = False
        for s_, l_ in zip(starts, Ls):
            assert not hb[d_lo + s_: d_lo + s_ + l_].any()
            hb[d_lo + s_: d_lo + s_ + l_] = True
        seg2 = hb[d_lo:d_hi + 1]
        rr = runs(seg2)
        assert len(rr) == m and sorted(e - s + 1 for s, e in rr) == sorted(L.tolist()) and rr[-1][1] < Nn
        arrangements.add(tuple(np.flatnonzero(seg2)[:3]))
        draws[r] = alpha_fast(hb)
    p_up = (1 + (draws >= real).sum()) / (reps + 1)
    return {"blocks": L.tolist(), "N": int(Nn), "m": int(m), "free": int(free), "real_alpha": float(real),
            "p_upper": float(p_up), "median_ann": float(12 * np.median(draws)),
            "p5_ann": float(12 * np.percentile(draws, 5)), "p95_ann": float(12 * np.percentile(draws, 95)),
            "draws": draws}


shP_rep = shuffle(hP, MB, 5000, 230, "replicate")
shP_ind = shuffle(hP, MB, 5000, 20260926, "independent")
shS_rep = shuffle(hS, MB, 5000, 230, "replicate")
shS_ind = shuffle(hS, MB, 5000, 20260926, "independent")
for lab, a, b in (("primary", shP_rep, shP_ind), ("secondary", shS_rep, shS_ind)):
    R[lab]["shuffle_replicate"] = {k: v for k, v in a.items() if k != "draws"}
    R[lab]["shuffle_independent"] = {k: v for k, v in b.items() if k != "draws"}
    assert abs(a["real_alpha"] - R[lab]["alpha_m"]) < 1e-12

# ============================================================ 9. crossing list (C29) and context counts
rw = slice(pd.Timestamp("1993-01-31"), pd.Timestamp("2009-12-31"))
vx, eo = vix.loc[rw], ovr.loc[rw]
last_dec, first_dec = WEND - pd.offsets.MonthEnd(1), W0 - pd.offsets.MonthEnd(1)
tc = sig.index[sig["team_cross"]]
rows = []
for t in sig.index[sig["cross"]]:
    d = t + pd.offsets.MonthEnd(1)
    # holds inside the window: decision d .. d+5 overlaps first_dec .. last_dec
    if d > last_dec or d + pd.offsets.MonthEnd(HOLD - 1) < first_dec:
        continue
    prev_on = bool(hold_P.get(d - pd.offsets.MonthEnd(1), False))
    near_team = any(abs((t.year - c.year) * 12 + t.month - c.month) <= 1 for c in tc)
    rows.append({"data_month": t.strftime("%Y-%m"), "decision_month": d.strftime("%Y-%m"), "z": z[g.get_loc(t)],
                 "thr": thr[g.get_loc(t)], "share_pct": 100 * E[g.get_loc(t)] / O[g.get_loc(t)],
                 "emv_pct": 100 * (eo <= ovr[t]).mean(), "vix_pct": 100 * (vx <= vix[t]).mean(),
                 "extends_hold": prev_on, "team_within_1m": near_team})
cr = pd.DataFrame(rows)
cr.to_csv(OUT / "xv_crossings.csv", index=False)
R["crossings"] = {"n": len(cr), "extends": int(cr["extends_hold"].sum()), "team_within_1m": int(cr["team_within_1m"].sum()),
                  "emv_top_quintile_gt80": int((cr["emv_pct"] > 80).sum()), "vix_top_quintile_gt80": int((cr["vix_pct"] > 80).sum()),
                  "emv_median_pct": float(cr["emv_pct"].median()), "vix_median_pct": float(cr["vix_pct"].median())}

# ============================================================ 10. compare with M8's published tables
cmp = []


def c(name, mine, theirs, tol):
    d = abs(float(mine) - float(theirs))
    cmp.append({"item": name, "independent": float(mine), "M8": float(theirs), "abs_diff": d, "tol": tol, "ok": d <= tol})


dro = pd.read_csv(TAB / "M8_drop_one.csv")
summ = pd.read_csv(TAB / "M8_strategy_summary.csv")
att = pd.read_csv(TAB / "M8_attribution.csv")
pb = pd.read_csv(TAB / "M8_passbar.csv")
epi = pd.read_csv(TAB / "M8_episodes.csv")
shd = pd.read_csv(TAB / "M8_shuffle_draws.csv")
pan = pd.read_csv(TAB / "M8_monthly_panel.csv", parse_dates=["month"]).set_index("month")
led = pd.read_csv(TAB / "M8_tests_ledger.csv")
m8cr = pd.read_csv(TAB / "M8_crossings.csv")
for lab, key, a, sh in (("primary", "Frozen EMV-share rule (primary)", aP, shP_rep),
                        ("secondary", "Team EMV_env level, lagged 1m (secondary)", aS, shS_rep)):
    at = att[att.signal == key].set_index("term")
    c(f"{lab} alpha (monthly)", a["alpha_m"], at.loc["const", "coef"], 1e-10)
    c(f"{lab} t NW6", a["t"], at.loc["const", "t_nw6"], 1e-6)
    c(f"{lab} t NW12", R[lab]["t_nw12"], at.loc["const", "t_nw12"], 1e-6)
    c(f"{lab} p t(n-k)", a["p_two"], at.loc["const", "p_nw6_t(n-k)"], 1e-6)
    for nm, cf, se in zip(a["names"], a["coef"], a["se"]):
        c(f"{lab} coef {nm}", cf, at.loc[nm, "coef"], 1e-9)
        c(f"{lab} t {nm}", cf / se, at.loc[nm, "t_nw6"], 1e-5)
    s = summ[summ.signal == key].iloc[0]
    c(f"{lab} pi", a["pi"], s["pi"], 1e-12)
    c(f"{lab} months in position", a["months_in_pos"], s["months_in_position"], 0)
    c(f"{lab} timed ann net", R[lab]["timed_ann_net"], s["timed_ann_net"], 1e-10)
    c(f"{lab} always ann net", R[lab]["always_ann_net"], s["always_ann_net"], 1e-10)
    c(f"{lab} D ann mean", R[lab]["D_ann_mean"], s["D_ann_mean"], 1e-10)
    c(f"{lab} D t", R[lab]["D_t"], s["D_t_mean_nw6"], 1e-6)
    c(f"{lab} timed t", R[lab]["timed_t"], s["timed_t_mean_nw6"], 1e-6)
    for j, v in R[lab]["drop_one"].items():
        rr = dro[(dro.signal == key) & (dro.dropped == j)].iloc[0]
        c(f"{lab} drop {j} alpha_ann", v["alpha_ann"], rr["alpha_ann"], 1e-9)
        c(f"{lab} drop {j} t", v["t"], rr["t_nw6"], 1e-5)
    c(f"{lab} episodes", len(R[lab]["episodes"]), len(epi[epi.signal == key]), 0)
    c(f"{lab} shuffle p (replicated draws)", sh["p_upper"], pb[(pb.signal == key) & pb.component.str.startswith("(ii)")]["p_value"].iloc[0], 1e-12)
    col = "primary_alpha_ann" if lab == "primary" else "secondary_alpha_ann"
    c(f"{lab} shuffle draws max|diff| (ann)", float(np.max(np.abs(12 * sh["draws"] - shd[col].to_numpy()))), 0.0, 1e-9)
# month-by-month panel
wp = pan.loc[win]
c("panel hold_primary_decision mismatches", int((wp["hold_primary_decision"].astype(bool).to_numpy() != hP[wpos]).sum()), 0, 0)
c("panel pos_primary_lag max|diff|", float(np.nanmax(np.abs(wp["pos_primary_lag"].to_numpy() - aP["hTl"]))), 0.0, 1e-12)
c("panel net_primary max|diff|", float(np.nanmax(np.abs(wp["net_primary"].to_numpy() - aP["netT"]))), 0.0, 1e-12)
c("panel net_always max|diff|", float(np.nanmax(np.abs(wp["net_always"].to_numpy() - aP["netA"]))), 0.0, 1e-12)
c("panel D_primary max|diff|", float(np.nanmax(np.abs(wp["D_primary"].to_numpy() - aP["D"]))), 0.0, 1e-12)
c("panel D_team max|diff|", float(np.nanmax(np.abs(wp["D_team"].to_numpy() - aS["D"]))), 0.0, 1e-12)
ps = pan.loc["1985-01-31":"2010-12-31"]
sg = sig.loc["1985-01-31":"2010-12-31"]
c("panel share_z max|diff|", float(np.nanmax(np.abs(ps["share_z"].to_numpy() - sg["z"].to_numpy()))), 0.0, 1e-10)
c("panel share_z NaN pattern mismatches", int((ps["share_z"].isna().to_numpy() != np.isnan(sg["z"].to_numpy())).sum()), 0, 0)
c("panel share_threshold max|diff|", float(np.nanmax(np.abs(ps["share_threshold"].to_numpy() - sg["thr"].to_numpy()))), 0.0, 1e-10)
c("panel share_cross mismatches", int((ps["share_cross"].astype(bool).to_numpy() != sg["cross"].to_numpy()).sum()), 0, 0)
c("panel team_z max|diff|", float(np.nanmax(np.abs(ps["team_z"].to_numpy() - sg["team_z"].to_numpy()))), 0.0, 1e-10)
c("panel team_cross mismatches", int((ps["team_cross"].astype(bool).to_numpy() != sg["team_cross"].to_numpy()).sum()), 0, 0)
c("crossing list length", len(cr), len(m8cr), 0)
c("crossing list data months mismatches", int(sum(a_ != b_ for a_, b_ in zip(cr["data_month"], m8cr["data_month"]))), 0, 0)
c("crossings extending a hold", int(cr["extends_hold"].sum()), int(m8cr["extends_hold"].sum()), 0)
c("crossings within 1m of team", int(cr["team_within_1m"].sum()), int(m8cr["team_cross_within_1m"].sum()), 0)
c("crossings EMV pctile max|diff|", float(np.max(np.abs(cr["emv_pct"].to_numpy() - m8cr["EMV_overall_pctile"].to_numpy()))), 0.0, 1e-9)
c("crossings VIX pctile max|diff|", float(np.max(np.abs(cr["vix_pct"].to_numpy() - m8cr["VIX_pctile"].to_numpy()))), 0.0, 1e-9)
c("ledger rows", len(led), 22, 0)
c("ledger primary rows", int((led.primary_or_exploratory == "primary").sum()), 8, 0)

cmp = pd.DataFrame(cmp)
cmp.to_csv(OUT / "xv_comparison.csv", index=False)
R["comparison_all_ok"] = bool(cmp["ok"].all())
R["comparison_failures"] = cmp.loc[~cmp["ok"], ["item", "independent", "M8", "abs_diff"]].to_dict("records")
pd.DataFrame({"month": win, "hold_dec_prev": hP[wpos - 1], "pos_lag": aP["hTl"], "netT": aP["netT"], "netA": aP["netA"],
              "D": aP["D"], "I": aP["I"]}).to_csv(OUT / "xv_monthly.csv", index=False)


def jsonable(o):
    if isinstance(o, dict):
        return {k: jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [jsonable(v) for v in o]
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, np.bool_):
        return bool(o)
    return o


(OUT / "xv_results.json").write_text(json.dumps(jsonable(R), indent=1))
print(json.dumps(jsonable({k: v for k, v in R.items() if k not in ("primary", "secondary")}), indent=1))
for lab in ("primary", "secondary"):
    r = R[lab]
    print(f"\n== {lab}: alpha {r['alpha_ann']:+.5f}/yr t {r['t']:.3f} p {r['p_two']:.3f} (df {r['df']}, k {r['k']}) "
          f"NW12 t {r['t_nw12']:.3f}; pi {r['pi']:.4f}; in position {r['months_in_pos']}")
    print(f"   shuffle replicate p {r['shuffle_replicate']['p_upper']:.4f}; independent sampler p {r['shuffle_independent']['p_upper']:.4f}; "
          f"blocks {r['shuffle_replicate']['blocks']} N {r['shuffle_replicate']['N']} free {r['shuffle_replicate']['free']}; "
          f"median {r['shuffle_replicate']['median_ann']:+.4f} 5-95 [{r['shuffle_replicate']['p5_ann']:+.4f}, {r['shuffle_replicate']['p95_ann']:+.4f}]")
    print(f"   episodes {len(r['episodes'])}: {[e[2] for e in r['episodes']]}")
    print("   drop-one: " + ", ".join(f"{j} {v['alpha_ann']:+.5f} (t {v['t']:.2f})" for j, v in r["drop_one"].items()))
    print(f"   timed {r['timed_ann_net']:+.5f} (t {r['timed_t']:.2f}); always {r['always_ann_net']:+.5f} (t {r['always_t']:.2f}); "
          f"D {r['D_ann_mean']:+.5f} (t {r['D_t']:.2f}); decomposition gap {r['decomp_identity_gap']:.1e}")
print("\ncomparison: all ok =", R["comparison_all_ok"], "; failures:", R["comparison_failures"])
