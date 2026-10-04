"""M8: the frozen EMV-share rule from exchange 1, scored once on the never-traded 1993-2009 window.

Pre-registration: modules/M8_frozen_pre2010/PREREGISTRATION.md (choices C1-C32 are referenced in comments).
Run (end to end):      cd /home/hashim/projects/GA/project/research && uv run python modules/M8_frozen_pre2010/run.py
Dry run on seen data:  ... run.py --dry-run   (2010-01 to 2022-07, code test only; writes to modules/M8_frozen_pre2010/dryrun/)

Only building blocks of lib/team_pipeline.py are used for the strategy (rolling_factor_model, state_position,
asset_strategy_returns, resolve_costs, newey_west_regression, expanding_threshold, rolling_z, cross_and_holds).
The calendar shuffle uses a numpy copy of the P&L engine that is checked against asset_strategy_returns at run time.
No shared lib file is modified.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import pathlib
import sys
import warnings

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, "/home/hashim/projects/GA/project/research/lib")
from common import FIGURES, RAW, TABLES, load_ff5_mom, load_fred, load_team  # noqa: E402
from team_pipeline import (TEAM_BROWN, TEAM_FACTOR_COLS, asset_strategy_returns, cross_and_holds,  # noqa: E402
                           expanding_threshold, newey_west_regression, resolve_costs, rolling_factor_model,
                           rolling_z, run_pipeline, state_position)

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message=".*Sorting by default.*")

HERE = pathlib.Path(__file__).resolve().parent
PREREG = HERE / "PREREGISTRATION.md"
MOD = "M8_frozen_pre2010"

# ----------------------------------------------------------------------------- frozen constants (PREREGISTRATION.md)
HOLD = 6                 # rule 4: 6-month hold
Z_WIN, Z_MIN_NZ = 60, 48  # C5
MAX_ZEROS = 6            # C6: more than 10% of 60 months zero -> off
TAIL_Q, TAIL_MIN = 0.80, 60  # C7
BETA_WIN, VOL_WIN, VOL_TGT, CAP, DIRECTION = 60, 36, 0.05, 1.0, -1  # C10
HEDGE_COLS = list(TEAM_FACTOR_COLS)
UNCOND = ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "UMD", "BOND", "WTI", "dVIX", "dlogEMV"]  # C20
COND = ["Mkt-RF", "HML", "BOND", "dVIX"]                                                  # C20
NW_MAIN, NW_CHECK = 6, 12  # C21
N_SHUFFLE, SEED = 5000, 230  # C24
PRIMARY_WINDOW = ("1993-01-31", "2009-12-31")
DRY_WINDOW = ("2010-01-31", "2022-07-31")


# ============================================================================ data
def load_inputs():
    T = load_team()
    ff5 = load_ff5_mom()
    env = load_fred("EMVENRGYENVREG")
    overall = load_fred("EMVOVERALLEMV")
    vix = load_fred("VIXCLS", how="mean")      # C17: monthly mean of daily VIX
    wti = load_fred("MCOILWTICO")               # C16
    gs10 = load_fred("GS10")                    # C15
    return T, ff5, env, overall, vix, wti, gs10


# ============================================================================ BOND (C15)
def par_bond_dc(y, maturity=10, m=2):
    """Price (per 100), modified duration (years) and convexity (years^2) of a par bond, m coupons a year, yield y."""
    y = np.atleast_1d(np.asarray(y, float))
    i = np.arange(1, maturity * m + 1)
    cf = np.repeat((100 * y / m)[:, None], len(i), axis=1)
    cf[:, -1] += 100
    disc = (1 + y[:, None] / m) ** (-i)
    P = (cf * disc).sum(1)
    D = (cf * (i / m) * disc).sum(1) / P / (1 + y / m)
    C = (cf * (i / m) * ((i + 1) / m) * disc).sum(1) / P / (1 + y / m) ** 2
    return P, D, C


def exact_par_return(y0, y1, maturity=10, m=2):
    """One-month total return of a par bond bought at y0 (coupon y0), repriced one month later at y1 (dirty price)."""
    y0, y1 = np.asarray(y0, float), np.asarray(y1, float)
    i = np.arange(1, maturity * m + 1)
    cf = np.repeat((100 * y0 / m)[:, None], len(i), axis=1)
    cf[:, -1] += 100
    return (cf * (1 + y1[:, None] / m) ** (-(i - m / 12))).sum(1) / 100 - 1


def build_bond(gs10, rf):
    y = (gs10 / 100).rename("y10")
    y0 = y.shift(1)
    dy = y - y0
    ok = y0.notna() & y.notna()
    D = pd.Series(np.nan, y.index)
    C = pd.Series(np.nan, y.index)
    _, d_, c_ = par_bond_dc(y0[ok].to_numpy())
    D[ok], C[ok] = d_, c_
    r = y0 / 12 - D * dy + 0.5 * C * dy ** 2
    ex = pd.Series(np.nan, y.index)
    ex[ok] = exact_par_return(y0[ok].to_numpy(), y[ok].to_numpy())
    out = pd.DataFrame({"y10": y, "dy": dy, "D_mod": D, "convexity": C, "ret_total": r, "ret_exact": ex})
    out["RF"] = rf.reindex(out.index)
    out["BOND"] = out["ret_total"] - out["RF"]
    return out


def bond_checks(bf):
    """Verification table for BOND: 2022 and other years, duration vs closed form, vs exact repricing, vs Damodaran."""
    rows = []
    ann = (1 + bf["ret_total"]).groupby(bf.index.year).prod() - 1
    ann_ex = (1 + bf["ret_exact"]).groupby(bf.index.year).prod() - 1
    dam = None
    p = HERE.parents[0] / "M3_alpha_beta" / "data" / "histretSP.xls"
    if p.exists():  # read-only use of M3's cached Damodaran file
        d = pd.read_excel(p, "T. Bond yield & return", header=None).iloc[7:, :3].dropna()
        d.columns = ["year", "yield", "ret"]
        d = d[pd.to_numeric(d["year"], errors="coerce").notna()]
        dam = pd.Series(d["ret"].astype(float).to_numpy(), index=d["year"].astype(int).to_numpy())
    for yr in (1994, 1999, 2008, 2009, 2022, 2023):
        rows.append({"check": f"calendar-year total return {yr}", "value": ann.get(yr, np.nan),
                     "reference": dam.get(yr, np.nan) if dam is not None else np.nan,
                     "note": "reference = Damodaran annual 10y T-bond return; exact-repricing BOND = %.4f" % ann_ex.get(yr, np.nan)})
    if dam is not None:
        yrs = [y_ for y_ in range(1993, 2026) if y_ in dam.index and y_ in ann.index]
        rows.append({"check": "corr(annual BOND, Damodaran) 1993-2025", "value": float(np.corrcoef(ann[yrs], dam[yrs])[0, 1]),
                     "reference": np.nan, "note": f"{len(yrs)} years"})
    d90 = bf.loc["1990":"1999"]
    d10 = bf.loc["2010":"2019"]
    closed = (1 / bf["y10"].shift(1)) * (1 - (1 + bf["y10"].shift(1) / 2) ** (-20))
    rows += [
        {"check": "mean GS10 1990-1999 (decimal)", "value": d90["y10"].mean(), "reference": np.nan, "note": ""},
        {"check": "modified duration 1990-1999 mean", "value": d90["D_mod"].mean(), "reference": np.nan,
         "note": "range %.2f to %.2f" % (d90["D_mod"].min(), d90["D_mod"].max())},
        {"check": "modified duration 1993-2009 mean", "value": bf.loc["1993":"2009", "D_mod"].mean(), "reference": np.nan,
         "note": "range %.2f to %.2f" % (bf.loc["1993":"2009", "D_mod"].min(), bf.loc["1993":"2009", "D_mod"].max())},
        {"check": "modified duration 2010-2019 mean", "value": d10["D_mod"].mean(), "reference": np.nan,
         "note": "range %.2f to %.2f" % (d10["D_mod"].min(), d10["D_mod"].max())},
        {"check": "max |D - closed form (1/y)(1-(1+y/2)^-20)|", "value": float((bf["D_mod"] - closed).abs().max()),
         "reference": 0.0, "note": "all months"},
        {"check": "max |monthly BOND total - exact repricing| 1993-2009", "value": float((bf["ret_total"] - bf["ret_exact"]).loc["1993":"2009"].abs().max()),
         "reference": np.nan, "note": "exact = dirty-price repricing at remaining maturity 10y - 1m"},
        {"check": "corr(monthly BOND total, exact) 1993-2009", "value": float(bf.loc["1993":"2009", ["ret_total", "ret_exact"]].corr().iloc[0, 1]),
         "reference": np.nan, "note": ""},
        {"check": "BOND excess mean 1993-2009, annualized", "value": 12 * bf.loc["1993":"2009", "BOND"].mean(), "reference": np.nan, "note": ""},
        {"check": "BOND excess vol 1993-2009, annualized", "value": np.sqrt(12) * bf.loc["1993":"2009", "BOND"].std(), "reference": np.nan, "note": ""},
    ]
    return pd.DataFrame(rows), ann


# ============================================================================ signals
def monthly_grid(*series):
    lo = min(s.dropna().index.min() for s in series)
    hi = max(s.dropna().index.max() for s in series)
    return pd.date_range(lo, hi, freq="ME")


def share_signal(env, overall):
    """Frozen rule, data-month time t (C3-C8). Returns a DataFrame; 'cross' is in data-month time."""
    idx = monthly_grid(env, overall)
    env, overall = env.reindex(idx), overall.reindex(idx)
    zero = env.eq(0)                                                        # C3
    missing = zero | env.isna() | overall.isna() | overall.le(0)
    s = (env / overall).where(~missing)
    ls = np.log(s)
    roll = ls.rolling(Z_WIN, min_periods=Z_MIN_NZ)                           # C5: >= 48 nonzero in trailing 60
    mu, sd = roll.mean(), roll.std(ddof=1)
    n_nz = ls.rolling(Z_WIN, min_periods=1).count()
    zeros60 = zero.astype(float).rolling(Z_WIN, min_periods=1).sum()
    off = zeros60 > MAX_ZEROS                                                # C6
    z = ((ls - mu) / sd.replace(0, np.nan)).where(~missing & ~off)
    thr = expanding_threshold(z, TAIL_Q, TAIL_MIN)                           # C7 (NaN months skipped)
    valid = z.notna() & thr.notna()
    extreme = (z > thr) & valid
    ev = extreme[valid]
    cr = ev & ~ev.shift(1, fill_value=False)                                 # C8: skip missing months
    cross = cr.reindex(idx, fill_value=False).astype(bool)
    return pd.DataFrame({"env": env, "overall": overall, "zero": zero, "share": s, "log_share": ls, "n_nonzero60": n_nz,
                         "zeros60": zeros60, "off": off, "z": z, "threshold": thr, "valid": valid, "extreme": extreme,
                         "cross": cross})


def team_signal(env):
    """Team original signal (C28): log1p level, rolling z 60/36, past-only p80 (min 60), team crossings; data time."""
    idx = monthly_grid(env)
    att = env.reindex(idx)
    z = rolling_z(np.log1p(att), 60, 36)
    thr = expanding_threshold(z, TAIL_Q, TAIL_MIN)
    state = z.gt(thr) & thr.notna()
    cross, _ = cross_and_holds(state, (HOLD,))
    return pd.DataFrame({"env": att, "z": z, "threshold": thr, "valid": z.notna() & thr.notna(), "extreme": state, "cross": cross})


def decision_hold(cross_data, grid):
    """C4 + C9: shift crossings one month (publication lag), then the team's hold = rolling max of crossings."""
    c = cross_data.reindex(grid, fill_value=False).astype(bool)
    cross_dec = c.shift(1, fill_value=False).astype(bool)
    hold = cross_dec.rolling(HOLD, min_periods=1).max().astype(bool)
    return cross_dec, hold


# ============================================================================ strategy engine (team building blocks)
def brown_model(brown, ind, ff3):
    """Exactly run_pipeline's Brown-leg model: EW leg - RF, rolling 60m OLS on team FF3."""
    leg = (ind[list(brown)].mean(axis=1) - ff3["RF"]).rename("Brown leg excess")
    aligned = pd.concat([leg, ff3[HEDGE_COLS]], axis=1, sort=True).dropna()
    b, h, e, a = rolling_factor_model(aligned.iloc[:, 0], aligned[HEDGE_COLS], BETA_WIN)
    return {"return": aligned.iloc[:, 0], "betas": b, "intercept": a, "hedged": h, "epsilon": e}


def run_strategy(hold, model, ff3, rates):
    pos = state_position(hold, model["epsilon"], DIRECTION, VOL_TGT, VOL_WIN, CAP)
    return asset_strategy_returns(pos, model, ff3, HEDGE_COLS, rates)


class FastEngine:
    """numpy copy of state_position + asset_strategy_returns for the shuffle (checked against the team engine)."""

    def __init__(self, model, ff3, rates, ref_index):
        eps = model["epsilon"]
        sigma = eps.rolling(VOL_WIN, min_periods=VOL_WIN).std(ddof=1)
        mag = (VOL_TGT / (np.sqrt(12) * sigma)).clip(upper=CAP)
        self.idx = ref_index
        self.mag = mag.reindex(ref_index).to_numpy()
        self.r = model["return"].reindex(ref_index).to_numpy()
        self.B = model["betas"].reindex(ref_index).to_numpy()
        self.F = ff3[HEDGE_COLS].reindex(ref_index).to_numpy()
        self.ra = rates["asset"]
        self.rf = np.array([rates[c] for c in HEDGE_COLS])

    def position(self, hold_bool):
        return np.where(hold_bool, DIRECTION * self.mag, 0.0)

    def net(self, h):
        O = -h[:, None] * self.B
        gross = np.full(len(h), np.nan)
        gross[1:] = h[:-1] * self.r[1:] + (O[:-1] * self.F[1:]).sum(1)
        at = np.abs(np.diff(h, prepend=0.0))
        ot = np.abs(np.diff(O, axis=0, prepend=np.zeros((1, O.shape[1]))))
        cost = self.ra * at + ot @ self.rf
        charged = np.r_[0.0, cost[:-1]]
        return gross - charged


# ============================================================================ attribution (C12-C22)
def nw_numpy(y, X, lags):
    """Same formula as team newey_west_regression (Bartlett, pinv, no df scaling). X excludes the constant."""
    Xc = np.column_stack([np.ones(len(y)), X])
    inv = np.linalg.pinv(Xc.T @ Xc)
    coef = inv @ Xc.T @ y
    xu = Xc * (y - Xc @ coef)[:, None]
    meat = xu.T @ xu
    for lag in range(1, min(lags, len(y) - 1) + 1):
        g = xu[lag:].T @ xu[:-lag]
        meat += (1 - lag / (lags + 1)) * (g + g.T)
    se = np.sqrt(np.clip(np.diag(inv @ meat @ inv), 0, None))
    return coef, se


def attribution(net_T, net_AO, pos_T, pos_AO, fac, window):
    """D_t = R^T - pi R^AO; regression on UNCOND + I_{t-1} x COND; NW(6) and NW(12); t(n-k) p-values; decomposition."""
    w = pd.date_range(window[0], window[1], freq="ME")
    hT = pos_T.shift(1).reindex(w)
    hA = pos_AO.shift(1).reindex(w)
    pi = hT.abs().mean() / hA.abs().mean()                                   # C13
    D = (net_T.reindex(w) - pi * net_AO.reindex(w)).rename("D")
    I = hT.ne(0).astype(float)                                               # C19
    X = fac.reindex(w)[UNCOND].copy()
    for c in COND:
        X[f"I x {c}"] = I * X[c]
    data = pd.concat([D, X], axis=1).dropna()
    n, k = len(data), X.shape[1] + 1
    fit6 = newey_west_regression(data["D"], data[X.columns], lags=NW_MAIN)
    fit12 = newey_west_regression(data["D"], data[X.columns], lags=NW_CHECK)
    df_ = n - k
    tab = pd.DataFrame({"coef": fit6["coef"], "t_nw6": fit6["t_hac6"], "t_nw12": fit12["t_hac6"]})
    tab["p_nw6_t(n-k)"] = 2 * stats.t.sf(tab["t_nw6"].abs(), df_)
    tab["p_nw12_t(n-k)"] = 2 * stats.t.sf(tab["t_nw12"].abs(), df_)
    means = data[X.columns].mean()
    contrib = pd.Series({"alpha": fit6.loc["const", "coef"], **{c: fit6.loc[c, "coef"] * means[c] for c in X.columns}})
    resid_mean = data["D"].mean() - contrib.sum()
    a, t6 = fit6.loc["const", "coef"], fit6.loc["const", "t_hac6"]
    return {"pi": pi, "D": D, "I": I, "X": X, "data": data, "n": n, "k": k, "df": df_, "table": tab,
            "alpha_m": a, "alpha_ann": 12 * a, "t6": t6, "t12": fit12.loc["const", "t_hac6"],
            "p6": 2 * stats.t.sf(abs(t6), df_), "p6_upper": stats.t.sf(t6, df_),
            "p12": 2 * stats.t.sf(abs(fit12.loc["const", "t_hac6"]), df_),
            "mean_D": data["D"].mean(), "contrib": contrib, "resid_mean": resid_mean, "fac_means": means}


def runs(mask: np.ndarray):
    """Maximal runs of True: list of (start, end_inclusive)."""
    out, i, n = [], 0, len(mask)
    while i < n:
        if mask[i]:
            j = i
            while j + 1 < n and mask[j + 1]:
                j += 1
            out.append((i, j))
            i = j + 1
        else:
            i += 1
    return out


def shuffle_test(hold, eng: FastEngine, net_AO, pos_AO, fac, window, reps=N_SHUFFLE, seed=SEED):
    """C24: move the same blocks (runs of hold inside decision months W0-1..E-1) to random non-touching dates."""
    idx = eng.idx
    w = pd.date_range(window[0], window[1], freq="ME")
    d_lo = idx.get_loc(w[0]) - 1
    d_hi = idx.get_loc(w[-1]) - 1
    hold_arr = hold.reindex(idx, fill_value=False).to_numpy().astype(bool)
    seg = hold_arr[d_lo:d_hi + 1]
    blocks = runs(seg)
    L = np.array([e - s + 1 for s, e in blocks])
    N, m = len(seg), len(L)
    free = N - L.sum() - (m - 1)
    # fixed pieces of the regression on the window
    wpos = np.array([idx.get_loc(t) for t in w])
    hA = np.abs(pos_AO.reindex(idx).to_numpy()[wpos - 1])
    nA = net_AO.reindex(idx).to_numpy()[wpos]
    Xu = fac.reindex(w)[UNCOND].to_numpy()
    Xc = fac.reindex(w)[COND].to_numpy()

    def alpha_of(hold_bool):
        h = eng.position(hold_bool)
        nT = eng.net(h)[wpos]
        hT = h[wpos - 1]
        pi = np.abs(hT).mean() / hA.mean()
        D = nT - pi * nA
        I = (hT != 0).astype(float)
        X = np.column_stack([Xu, I[:, None] * Xc])
        ok = ~np.isnan(D) & ~np.isnan(X).any(1)
        coef, se = nw_numpy(D[ok], X[ok], NW_MAIN)
        return coef[0], coef[0] / se[0]

    real_alpha, real_t = alpha_of(hold_arr)
    if m == 0 or free < 0:
        return {"blocks": L, "real_alpha": real_alpha, "draws": np.array([]), "p_upper": np.nan, "p_two": np.nan}
    rng = np.random.default_rng(seed)
    draws, tdraws = np.empty(reps), np.empty(reps)
    for b in range(reps):
        order = rng.permutation(m)
        pos = np.sort(rng.choice(free + m, size=m, replace=False))
        Ls = L[order]
        starts = pos + np.r_[0, np.cumsum(Ls)[:-1]]
        hb = hold_arr.copy()
        hb[d_lo:d_hi + 1] = False
        for s_, l_ in zip(starts, Ls):
            hb[d_lo + s_: d_lo + s_ + l_] = True
        draws[b], tdraws[b] = alpha_of(hb)
    p_up = (1 + (draws >= real_alpha).sum()) / (reps + 1)
    p_lo = (1 + (draws <= real_alpha).sum()) / (reps + 1)
    return {"blocks": L, "N": N, "m": m, "free": free, "real_alpha": real_alpha, "real_t": real_t, "draws": draws,
            "tdraws": tdraws, "p_upper": p_up, "p_lower": p_lo, "p_two": min(1.0, 2 * min(p_up, p_lo))}


def count_episodes(hold, window):
    """C25: runs of the decision-time hold that include at least one decision month in W0-1..E-1."""
    w = pd.date_range(window[0], window[1], freq="ME")
    d_lo, d_hi = w[0] - pd.offsets.MonthEnd(1), w[-1] - pd.offsets.MonthEnd(1)
    arr = hold.to_numpy().astype(bool)
    ep = []
    for s, e in runs(arr):
        a, b = hold.index[s], hold.index[e]
        if b >= d_lo and a <= d_hi:
            ep.append({"first_decision_month": a, "last_decision_month": b, "months": e - s + 1,
                       "in_window_months": int(((hold.index[s:e + 1] >= d_lo) & (hold.index[s:e + 1] <= d_hi)).sum())})
    return pd.DataFrame(ep)


# ============================================================================ one full evaluation of a signal
def evaluate(label, hold, T, ff3, fac, window, rates, check_engine=False):
    ind = T["industries"]
    model = brown_model(TEAM_BROWN, ind, ff3)
    always = pd.Series(True, index=model["epsilon"].index)
    sT = run_strategy(hold, model, ff3, rates)
    sA = run_strategy(always, model, ff3, rates)
    att = attribution(sT["net_return"], sA["net_return"], sT["position"], sA["position"], fac, window)
    eng = FastEngine(model, ff3, rates, sT.index)
    hold_idx = hold.reindex(sT.index, fill_value=False).to_numpy().astype(bool)
    fast_net = eng.net(eng.position(hold_idx))
    eng_diff = float(np.nanmax(np.abs(fast_net - sT["net_return"].to_numpy())))
    assert eng_diff < 1e-12, f"fast engine mismatch {eng_diff}"
    sh = shuffle_test(hold, eng, sA["net_return"], sA["position"], fac, window)
    assert abs(sh["real_alpha"] - att["alpha_m"]) < 1e-12, "shuffle real alpha != attribution alpha"
    ep = count_episodes(hold, window)
    drops = []
    for j in TEAM_BROWN:
        mj = brown_model([b for b in TEAM_BROWN if b != j], ind, ff3)
        tj = run_strategy(hold, mj, ff3, rates)
        aj = run_strategy(pd.Series(True, index=mj["epsilon"].index), mj, ff3, rates)
        r = attribution(tj["net_return"], aj["net_return"], tj["position"], aj["position"], fac, window)
        drops.append({"signal": label, "dropped": j, "alpha_ann": r["alpha_ann"], "t_nw6": r["t6"], "p_tnk": r["p6"],
                      "pi": r["pi"], "n": r["n"]})
    drops = pd.DataFrame(drops)
    w = pd.date_range(*window, freq="ME")
    nT, nA = sT["net_return"].reindex(w), sA["net_return"].reindex(w)
    summ = {"signal": label, "window": f"{w[0]:%Y-%m} to {w[-1]:%Y-%m}", "n_months": len(w),
            "months_in_position": int(att["I"].sum()), "pi": att["pi"],
            "mean_abs_pos_timed": sT["position"].shift(1).reindex(w).abs().mean(),
            "mean_abs_pos_always": sA["position"].shift(1).reindex(w).abs().mean(),
            "timed_ann_net": 12 * nT.mean(), "timed_t_mean_nw6": _t_mean(nT),
            "always_ann_net": 12 * nA.mean(), "always_t_mean_nw6": _t_mean(nA),
            "D_ann_mean": 12 * att["D"].mean(), "D_t_mean_nw6": _t_mean(att["D"]),
            "timed_ann_cost": 12 * sT["cost"].reindex(w).mean(), "engine_check_maxdiff": eng_diff}
    passes = {
        "i": bool(att["alpha_m"] > 0 and att["t6"] >= 2.0),
        "ii": bool(sh["p_upper"] <= 0.05) if np.isfinite(sh["p_upper"]) else False,
        "iii": bool(len(ep) >= 8),
        "iv": bool(att["alpha_m"] > 0 and (np.sign(drops["alpha_ann"]) == np.sign(att["alpha_m"])).all()),
    }
    return {"label": label, "model": model, "timed": sT, "always": sA, "att": att, "shuffle": sh, "episodes": ep,
            "drops": drops, "summary": summ, "passes": passes, "passed": all(passes.values()), "hold": hold}


def _t_mean(s):
    s = s.dropna()
    return float(newey_west_regression(s, pd.DataFrame(index=s.index), lags=NW_MAIN).loc["const", "t_hac6"])


# ============================================================================ output helpers
def fmt(v, nd=2):
    if v is None or (isinstance(v, (float, np.floating)) and not np.isfinite(v)):
        return ""
    if isinstance(v, (bool, np.bool_)):
        return "yes" if v else "no"
    if isinstance(v, (int, np.integer)):
        return f"{v:d}"
    if isinstance(v, (float, np.floating)):
        return f"{v:.{nd}f}"
    out = str(v).replace("&", "\\&").replace("%", "\\%").replace("_", "\\_")
    out = out.replace("^", "\\^{}").replace("|", "$|$")
    out = out.replace(">=", "$\\geq$").replace("<=", "$\\leq$")
    return out.replace(">", "$>$").replace("<", "$<$")


def to_tex(df, path, digits=None, default=2, caption=None, label=None):
    digits = digits or {}
    cols = list(df.columns)
    lines = ["\\begin{table}[htbp]\\centering\\small"]
    if caption:
        lines.append(f"\\caption{{{caption}}}")
    if label:
        lines.append(f"\\label{{{label}}}")
    lines += ["\\begin{tabular}{l" + "r" * (len(cols) - 1) + "}", "\\toprule",
              " & ".join(fmt(c) for c in cols) + " \\\\", "\\midrule"]
    for _, r in df.iterrows():
        lines.append(" & ".join(fmt(r[c], digits.get(c, default)) for c in cols) + " \\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
    pathlib.Path(path).write_text("\n".join(lines) + "\n")


# ============================================================================ main
def main(dry_run=False):
    t_start = dt.datetime.now().astimezone()
    window = DRY_WINDOW if dry_run else PRIMARY_WINDOW
    out_t = (HERE / "dryrun") if dry_run else TABLES
    out_t.mkdir(parents=True, exist_ok=True)
    pre = "M8dry_" if dry_run else "M8_"
    prereg_hash = hashlib.sha256(PREREG.read_bytes()).hexdigest()
    print(f"[{t_start:%Y-%m-%d %H:%M:%S %Z}] M8 {'DRY RUN (seen data)' if dry_run else 'PRIMARY RUN'}; prereg sha256 {prereg_hash[:16]}")

    T, ff5, env, overall, vix, wti, gs10 = load_inputs()
    ff3 = T["ff3"]
    rates = resolve_costs(HEDGE_COLS)                       # team costs: 10bp asset, 5bp Mkt-RF, 25bp SMB/HML

    # ---- BOND (C15) and attribution factor panel (C14-C18)
    bf = build_bond(gs10, ff5["RF"])
    bchk, bond_annual = bond_checks(bf)
    fac = ff5[["Mkt-RF", "SMB", "HML", "RMW", "CMA", "UMD"]].copy()
    fac["BOND"] = bf["BOND"]
    fac["WTI"] = np.log(wti).diff()
    fac["dVIX"] = vix.diff()
    fac["dlogEMV"] = np.log(overall).diff()

    # ---- signals (data time) and decision-time holds
    sig = share_signal(env, overall)
    tsig = team_signal(env)
    model_ref = brown_model(TEAM_BROWN, T["industries"], ff3)
    grid = pd.date_range(model_ref["epsilon"].index.min(), max(model_ref["epsilon"].index.max(), sig.index.max() + pd.offsets.MonthEnd(1)), freq="ME")
    cross_dec, hold = decision_hold(sig["cross"], grid)
    tcross_dec, thold = decision_hold(tsig["cross"], grid)
    defined_dec = sig["valid"].reindex(grid, fill_value=False).shift(1, fill_value=False)
    tau0 = defined_dec[defined_dec].index.min()
    W0 = max(pd.Timestamp(window[0]), tau0 + pd.offsets.MonthEnd(1))
    win = (W0.strftime("%Y-%m-%d"), window[1])
    print(f"first decision month with a defined flag tau0 = {tau0:%Y-%m}; test window {W0:%Y-%m} to {pd.Timestamp(window[1]):%Y-%m}")

    # ---- engine check against the team pipeline (same-month team signal, full history; max abs diff only)
    team = run_pipeline(bootstrap_reps=0, extras=False, paired=False, macro_states=False)
    _, thold_same = decision_hold(tsig["cross"].shift(-1, fill_value=False), grid)  # undo the lag: same-month holds
    mine = run_strategy(thold_same, model_ref, ff3, rates)
    ref = team["strategies"]["Original | Short Brown hold 6m"]
    d_team = float((mine["net_return"] - ref["net_return"]).abs().max())
    ao_ref = team["strategies"]["Benchmark | Always-short Brown"]
    ao_mine = run_strategy(pd.Series(True, index=model_ref["epsilon"].index), model_ref, ff3, rates)
    d_ao = float((ao_mine["net_return"] - ao_ref["net_return"]).abs().max())
    d_z = float((tsig["z"] - team["signals"]["raw"].reindex(tsig.index)).abs().max())
    print(f"engine check vs run_pipeline: Original 6m net max|diff| = {d_team:.2e}; Always-short max|diff| = {d_ao:.2e}; team z max|diff| = {d_z:.2e}")
    assert d_team < 1e-14 and d_ao < 1e-14 and d_z < 1e-12

    # ---- the one evaluation of each signal
    P = evaluate("Frozen EMV-share rule (primary)", hold, T, ff3, fac, win, rates)
    S = evaluate("Team EMV_env level, lagged 1m (secondary)", thold, T, ff3, fac, win, rates)

    # ---------------------------------------------------------------- tables
    wtag = f"{W0:%Y-%m} to {pd.Timestamp(window[1]):%Y-%m}"
    bar = []
    for R, kind in ((P, "primary"), (S, "secondary")):
        a, sh = R["att"], R["shuffle"]
        bar += [
            {"signal": R["label"], "role": kind, "component": "(i) timing alpha, NW(6)", "statistic": f"alpha {a['alpha_ann']:.4f}/yr, t {a['t6']:.2f}",
             "p_value": a["p6"], "bar": "alpha > 0 and t >= 2", "pass": R["passes"]["i"]},
            {"signal": R["label"], "role": kind, "component": "(ii) calendar shuffle", "statistic": f"{len(sh['draws'])} draws, {sh.get('m', 0)} blocks",
             "p_value": sh["p_upper"], "bar": "one-sided p <= 0.05", "pass": R["passes"]["ii"]},
            {"signal": R["label"], "role": kind, "component": "(iii) independent episodes", "statistic": f"{len(R['episodes'])}",
             "p_value": np.nan, "bar": ">= 8", "pass": R["passes"]["iii"]},
            {"signal": R["label"], "role": kind, "component": "(iv) drop-one Brown industry",
             "statistic": "alphas " + ", ".join(f"{r.dropped} {r.alpha_ann:+.4f}" for r in R["drops"].itertuples()),
             "p_value": np.nan, "bar": "all five alphas > 0", "pass": R["passes"]["iv"]},
            {"signal": R["label"], "role": kind, "component": "VERDICT", "statistic": "", "p_value": np.nan,
             "bar": "all four", "pass": R["passed"]},
        ]
    passbar = pd.DataFrame(bar)
    passbar.to_csv(out_t / f"{pre}passbar.csv", index=False)
    pb_tex = passbar.copy()
    pb_tex["signal"] = pb_tex["role"]
    to_tex(pb_tex.drop(columns=["role"]).rename(columns={"p_value": "p"}), out_t / f"{pre}passbar.tex", default=3,
           caption=f"Frozen rule scored once, {wtag}. Primary: EMV-share rule; secondary: team signal lagged one month.",
           label="tab:m8_passbar")

    coef_rows = []
    for R in (P, S):
        tb = R["att"]["table"].copy()
        tb.insert(0, "term", tb.index)
        tb.insert(0, "signal", R["label"])
        tb["n"], tb["k"] = R["att"]["n"], R["att"]["k"]
        coef_rows.append(tb)
    coefs = pd.concat(coef_rows, ignore_index=True)
    coefs.to_csv(out_t / f"{pre}attribution.csv", index=False)
    ct = coefs[coefs.signal == P["label"]][["term", "coef", "t_nw6", "p_nw6_t(n-k)", "t_nw12"]].copy()
    ct2 = coefs[coefs.signal == S["label"]][["term", "coef", "t_nw6"]].rename(columns={"coef": "coef (team)", "t_nw6": "t (team)"})
    ct = ct.reset_index(drop=True).join(ct2.drop(columns="term").reset_index(drop=True))
    ct.loc[ct.term == "const", ["coef", "coef (team)"]] *= 12
    ct["term"] = ct["term"].replace({"const": "alpha (annualized)"})
    to_tex(ct, out_t / f"{pre}attribution.tex", digits={"coef": 4, "coef (team)": 4, "p_nw6_t(n-k)": 3}, default=2,
           caption=f"Attribution of $D_t = R^T_t - \\pi R^{{AO}}_t$, {wtag}; NW(6) t, p from t(n-k), k = {P['att']['k']}.",
           label="tab:m8_attribution")

    dec_rows = []
    for R in (P, S):
        c = R["att"]["contrib"] * 12
        groups = {
            "alpha": ["alpha"], "FF5+UMD": ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "UMD"], "BOND (unconditional)": ["BOND"],
            "WTI": ["WTI"], "Volatility (dVIX, dlogEMV, I x dVIX)": ["dVIX", "dlogEMV", "I x dVIX"],
            "Conditional Mkt-RF and HML": ["I x Mkt-RF", "I x HML"], "Conditional BOND": ["I x BOND"],
        }
        for g, terms in groups.items():
            dec_rows.append({"signal": R["label"], "component": g, "ann_contribution": float(c[terms].sum())})
        dec_rows.append({"signal": R["label"], "component": "sum = mean(D)", "ann_contribution": float(c.sum())})
        dec_rows.append({"signal": R["label"], "component": "check: 12 x mean(D)", "ann_contribution": 12 * R["att"]["mean_D"]})
    dec = pd.DataFrame(dec_rows)
    dec.to_csv(out_t / f"{pre}decomposition.csv", index=False)
    detail = pd.concat([pd.DataFrame({"signal": R["label"], "term": R["att"]["contrib"].index,
                                      "ann_contribution": 12 * R["att"]["contrib"].to_numpy(),
                                      "factor_mean_ann": [np.nan] + list(12 * R["att"]["fac_means"].to_numpy())}) for R in (P, S)])
    detail.to_csv(out_t / f"{pre}decomposition_terms.csv", index=False)
    dw = dec.pivot(index="component", columns="signal", values="ann_contribution").reindex(dec.component.unique())
    dw = dw[[P["label"], S["label"]]].reset_index()
    dw.columns = ["component", "primary (share rule)", "secondary (team signal)"]
    to_tex(dw, out_t / f"{pre}decomposition.tex", default=4,
           caption=f"Decomposition of annualized mean(D), {wtag}.", label="tab:m8_decomposition")

    drops = pd.concat([P["drops"], S["drops"]], ignore_index=True)
    drops.to_csv(out_t / f"{pre}drop_one.csv", index=False)
    dd = P["drops"][["dropped", "alpha_ann", "t_nw6", "p_tnk"]].merge(
        S["drops"][["dropped", "alpha_ann", "t_nw6"]].rename(columns={"alpha_ann": "alpha (team)", "t_nw6": "t (team)"}), on="dropped")
    to_tex(dd, out_t / f"{pre}drop_one.tex", digits={"alpha_ann": 4, "alpha (team)": 4, "p_tnk": 3},
           caption=f"Timing alpha with each Brown industry dropped, {wtag}.", label="tab:m8_drop_one")

    summ = pd.DataFrame([P["summary"], S["summary"]])
    summ.to_csv(out_t / f"{pre}strategy_summary.csv", index=False)
    to_tex(summ[["signal", "months_in_position", "pi", "timed_ann_net", "timed_t_mean_nw6", "always_ann_net", "always_t_mean_nw6",
                 "D_ann_mean", "D_t_mean_nw6"]].assign(signal=["primary", "secondary"]),
           out_t / f"{pre}strategy_summary.tex", digits={"timed_ann_net": 4, "always_ann_net": 4, "D_ann_mean": 4, "pi": 3},
           caption=f"Timed and always-on Short-Brown, net of costs, {wtag}.", label="tab:m8_summary")

    eps_rows = []
    for R in (P, S):
        e = R["episodes"].copy()
        e.insert(0, "signal", R["label"])
        eps_rows.append(e)
    pd.concat(eps_rows, ignore_index=True).to_csv(out_t / f"{pre}episodes.csv", index=False)

    shuf = pd.DataFrame({"primary_alpha_ann": 12 * P["shuffle"]["draws"], "primary_t": P["shuffle"]["tdraws"]})
    if len(S["shuffle"]["draws"]) == len(shuf):
        shuf["secondary_alpha_ann"] = 12 * S["shuffle"]["draws"]
        shuf["secondary_t"] = S["shuffle"]["tdraws"]
    shuf.to_csv(out_t / f"{pre}shuffle_draws.csv", index=False)

    # crossing list (C29): primary crossings whose decision month is at or before the last window decision month
    last_dec = pd.Timestamp(window[1]) - pd.offsets.MonthEnd(1)
    first_dec = W0 - pd.offsets.MonthEnd(1)
    rank_win = slice(pd.Timestamp(window[0]), pd.Timestamp(window[1]))  # C29: ranks within the nominal window
    vx, eo = vix.loc[rank_win], overall.loc[rank_win]
    tc = set(tsig.index[tsig["cross"]])
    crows = []
    hold_arr = P["hold"]
    for t in sig.index[sig["cross"]]:
        dmo = t + pd.offsets.MonthEnd(1)
        if dmo > last_dec or dmo < first_dec - pd.offsets.MonthEnd(HOLD - 1):
            continue
        prev_on = bool(hold_arr.get(dmo - pd.offsets.MonthEnd(1), False))
        crows.append({"data_month": t.strftime("%Y-%m"), "decision_month": dmo.strftime("%Y-%m"),
                      "first_return_month": (dmo + pd.offsets.MonthEnd(1)).strftime("%Y-%m"),
                      "share_pct": 100 * sig.at[t, "share"], "z": sig.at[t, "z"], "threshold": sig.at[t, "threshold"],
                      "EMV_overall": overall.get(t, np.nan), "EMV_overall_pctile": 100 * (eo <= overall.get(t, np.nan)).mean(),
                      "VIX_mean": vix.get(t, np.nan), "VIX_pctile": 100 * (vx <= vix.get(t, np.nan)).mean(),
                      "EMV_env": env.get(t, np.nan), "extends_hold": prev_on,
                      "team_cross_within_1m": any(abs((t - c).days) <= 31 for c in tc)})
    cr = pd.DataFrame(crows)
    cr.to_csv(out_t / f"{pre}crossings.csv", index=False)
    to_tex(cr.drop(columns=["first_return_month", "EMV_env"]), out_t / f"{pre}crossings.tex",
           digits={"share_pct": 2, "z": 2, "threshold": 2, "EMV_overall": 1, "EMV_overall_pctile": 0, "VIX_mean": 1, "VIX_pctile": 0},
           caption=f"Crossings of the frozen EMV-share rule; EMV overall and VIX percentile ranks within the {pd.Timestamp(window[0]):%Y}-{pd.Timestamp(window[1]):%Y} data months.", label="tab:m8_crossings")

    bchk.to_csv(out_t / f"{pre}bond_check.csv", index=False)
    to_tex(bchk[["check", "value", "reference"]], out_t / f"{pre}bond_check.tex", default=4,
           caption="BOND factor checks (GS10 par bond, duration and convexity).", label="tab:m8_bond")

    # monthly panel: signals (data time) and window returns
    panel = sig[["env", "overall", "share", "zero", "zeros60", "off", "z", "threshold", "valid", "extreme", "cross"]].add_prefix("share_")
    panel = panel.join(tsig[["z", "threshold", "extreme", "cross"]].add_prefix("team_"), how="outer")
    wr = pd.date_range(*win, freq="ME")
    rets = pd.DataFrame({"hold_primary_decision": P["hold"].reindex(wr), "pos_primary_lag": P["timed"]["position"].shift(1).reindex(wr),
                         "net_primary": P["timed"]["net_return"].reindex(wr), "D_primary": P["att"]["D"],
                         "hold_team_decision": S["hold"].reindex(wr), "pos_team_lag": S["timed"]["position"].shift(1).reindex(wr),
                         "net_team": S["timed"]["net_return"].reindex(wr), "D_team": S["att"]["D"],
                         "pos_always_lag": P["always"]["position"].shift(1).reindex(wr), "net_always": P["always"]["net_return"].reindex(wr)})
    panel.loc["1985-01-31":"2010-12-31"].join(rets, how="left").to_csv(out_t / f"{pre}monthly_panel.csv", index_label="month")

    # ---- ledger
    L = []

    def add(test_id, question, stat_name, stat, p, n, kind, note):
        L.append({"test_id": test_id, "module": MOD, "question": question, "statistic_name": stat_name, "statistic": stat,
                  "p_value_two_sided": p, "n_obs": n, "primary_or_exploratory": kind, "note": note})

    for R, tag, kind in ((P, "share", "primary"), (S, "team", "exploratory")):
        a, sh = R["att"], R["shuffle"]
        q = "Does the frozen EMV-share rule time Short-Brown on 1993-2009?" if tag == "share" else \
            "Secondary context: does the team signal (lagged 1m) time Short-Brown on the same window?"
        add(f"M8_{tag}_i_alpha_nw6", q, "timing alpha NW(6) t", a["t6"], a["p6"], a["n"], kind,
            f"alpha_ann={a['alpha_ann']:.5f}; k={a['k']}; p from t({a['df']}); window {wtag}; pass(i)={R['passes']['i']}")
        add(f"M8_{tag}_i_alpha_nw12", q, "timing alpha NW(12) t (check)", a["t12"], a["p12"], a["n"], "exploratory",
            f"alpha_ann={a['alpha_ann']:.5f}; lag check only")
        add(f"M8_{tag}_ii_shuffle", q, "calendar-shuffle rank of alpha", a["alpha_ann"], sh["p_two"], a["n"], kind,
            f"one-sided upper p={sh['p_upper']:.4f} (pass bar); {len(sh['draws'])} draws seed {SEED}; blocks={list(map(int, sh['blocks']))}; "
            f"median shuffled alpha_ann={12 * np.median(sh['draws']) if len(sh['draws']) else np.nan:.5f}; pass(ii)={R['passes']['ii']}")
        add(f"M8_{tag}_iii_episodes", q, "independent episodes (merged holds)", len(R["episodes"]), np.nan, a["n"], kind,
            f"bar >= 8; pass(iii)={R['passes']['iii']}")
        for r in R["drops"].itertuples():
            add(f"M8_{tag}_iv_drop_{r.dropped}", q, f"timing alpha NW(6) t, {r.dropped} dropped", r.t_nw6, r.p_tnk, r.n, kind,
                f"alpha_ann={r.alpha_ann:.5f}; sign kept={np.sign(r.alpha_ann) == np.sign(a['alpha_m'])}")
        add(f"M8_{tag}_ctx_D_mean", q, "mean D NW(6) t (no factors)", R["summary"]["D_t_mean_nw6"],
            2 * stats.t.sf(abs(R["summary"]["D_t_mean_nw6"]), a["n"] - 1), a["n"], "exploratory",
            f"D_ann={R['summary']['D_ann_mean']:.5f}; context")
        add(f"M8_{tag}_ctx_timed_mean", q, "timed net return NW(6) t", R["summary"]["timed_t_mean_nw6"],
            2 * stats.t.sf(abs(R["summary"]["timed_t_mean_nw6"]), a["n"] - 1), a["n"], "exploratory",
            f"ann_net={R['summary']['timed_ann_net']:.5f}; context, not the timing test")
    ledger = pd.DataFrame(L)
    ledger.to_csv(out_t / f"{pre}tests_ledger.csv", index=False)

    rec = HERE / ("dryrun/first_run_record.json" if dry_run else "first_run_record.json")
    first_time = json.loads(rec.read_text())["run_time"] if rec.exists() else t_start.strftime("%Y-%m-%d %H:%M:%S %Z")
    meta = pd.DataFrame([{"first_run_time": first_time, "this_run_time": t_start.strftime("%Y-%m-%d %H:%M:%S %Z"),
                          "prereg_written": "2026-09-26 03:29:54 PDT", "mode": "dry_run" if dry_run else "primary",
                          "prereg_file": str(PREREG), "prereg_sha256": prereg_hash, "window": wtag, "tau0": tau0.strftime("%Y-%m"),
                          "shuffle_reps": N_SHUFFLE, "seed": SEED, "engine_check_team_orig6m": d_team, "engine_check_always": d_ao}])
    meta.to_csv(out_t / f"{pre}preregistration_hash.csv", index=False)

    # ---- figure (primary only)
    if not dry_run:
        make_figure(sig, tsig, P, S, W0, pd.Timestamp(window[1]))

    # ---- first-run record (C31)
    key = {"alpha_ann": round(float(P["att"]["alpha_ann"]), 10), "t6": round(float(P["att"]["t6"]), 8),
           "shuffle_p": round(float(P["shuffle"]["p_upper"]), 8), "episodes": int(len(P["episodes"])),
           "drop_alphas": [round(float(x), 10) for x in P["drops"]["alpha_ann"]], "passed": bool(P["passed"])}
    rec = HERE / ("dryrun/first_run_record.json" if dry_run else "first_run_record.json")
    if rec.exists():
        old = json.loads(rec.read_text())
        same = old["key"] == key
        print(f"first-run record exists ({old['run_time']}); this run reproduces it: {same}")
    else:
        rec.write_text(json.dumps({"run_time": t_start.strftime("%Y-%m-%d %H:%M:%S %Z"), "prereg_sha256": prereg_hash, "key": key}, indent=1))
        print(f"first-run record written: {rec}")

    # ---- console summary
    for R in (P, S):
        a, sh = R["att"], R["shuffle"]
        print(f"\n== {R['label']} | {wtag}")
        print(f"  pi={a['pi']:.3f}  n={a['n']}  k={a['k']}  months in position={int(a['I'].sum())}")
        print(f"  (i)   alpha={a['alpha_ann']:+.4f}/yr  t6={a['t6']:.2f}  p6={a['p6']:.3f}  t12={a['t12']:.2f}  -> {R['passes']['i']}")
        print(f"  (ii)  shuffle p_upper={sh['p_upper']:.4f} (two-sided {sh['p_two']:.4f}), blocks={list(map(int, sh['blocks']))} -> {R['passes']['ii']}")
        print(f"  (iii) episodes={len(R['episodes'])} -> {R['passes']['iii']}")
        print(f"  (iv)  drop-one alphas: " + ", ".join(f"{r.dropped} {r.alpha_ann:+.4f} (t {r.t_nw6:.2f})" for r in R["drops"].itertuples()) + f" -> {R['passes']['iv']}")
        print(f"  VERDICT: {'PASS' if R['passed'] else 'FAIL'}")
        print("  decomposition (ann): " + ", ".join(f"{k} {v:+.4f}" for k, v in (12 * a["contrib"]).items()) + f"; mean D {12 * a['mean_D']:+.4f}; resid mean {a['resid_mean']:.1e}")
    print("\nBOND checks:\n" + bchk.to_string(index=False))
    return P, S


# ============================================================================ figure
def make_figure(sig, tsig, P, S, W0, E):
    sys.path.insert(0, "/home/hashim/projects/GA/project/research/lib")
    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt
    import plotstyle as ps

    lo, hi = pd.Timestamp("1988-01-31"), E
    fig, axes = plt.subplots(3, 1, figsize=(7.2, 7.4), sharex=True)

    def shade(ax, R, color):
        on = R["timed"]["position"].shift(1).reindex(pd.date_range(lo, hi, freq="ME")).fillna(0).ne(0).to_numpy()
        months = pd.date_range(lo, hi, freq="ME")
        for s, e in runs(on):
            ax.axvspan(months[s] - pd.offsets.MonthBegin(1), months[e], color=color, alpha=0.13, lw=0)

    # panel A: share level
    ax = axes[0]
    s = sig["share"].loc[lo:hi]
    ax.plot(s.index, 100 * s, color=ps.BLUE, lw=1.2)
    zm = sig.loc[lo:hi].index[sig.loc[lo:hi, "zero"]]
    ax.plot(zm, np.full(len(zm), 0.0), ls="none", marker="x", color=ps.INK2, ms=5, label="zero month (missing)")
    ax.set_ylabel("EMV env. / EMV overall (%)")
    ax.set_title("A. Signal: share of EMV articles on energy and environmental regulation", loc="left")
    ax.legend(loc="upper left")

    # panel B: primary z, threshold, crossings, holds
    ax = axes[1]
    shade(ax, P, ps.BLUE)
    z, thr = sig["z"].loc[lo:hi], sig["threshold"].loc[lo:hi]
    ax.plot(z.index, z, color=ps.BLUE, lw=1.1, label="z of log share (60m, nonzero months)")
    ax.plot(thr.index, thr, color=ps.INK, lw=1.1, ls="--", label="past-only 80th percentile")
    c = sig.loc[lo:hi].index[sig.loc[lo:hi, "cross"]]
    ax.plot(c, sig.loc[c, "z"], ls="none", marker="o", ms=6, color=ps.BLUE, mec="white", mew=1.2, label="crossing (data month)")
    ax.axvline(W0, color=ps.MUTED, lw=1)
    ax.text(W0, ax.get_ylim()[1], " test window starts", va="top", ha="left", fontsize=7.5, color=ps.INK2)
    ax.set_ylabel("z")
    ax.set_ylim(-5.0, 3.6)  # empty band at the bottom holds the legend
    ax.set_title("B. Frozen rule: crossings and months earning the short-Brown return (shaded)", loc="left")
    ax.legend(loc="lower left", ncol=3, fontsize=7)

    # panel C: team signal (secondary)
    ax = axes[2]
    shade(ax, S, ps.ORANGE)
    z, thr = tsig["z"].loc[lo:hi], tsig["threshold"].loc[lo:hi]
    ax.plot(z.index, z, color=ps.ORANGE, lw=1.1, label="team z of log(1 + EMV env.)")
    ax.plot(thr.index, thr, color=ps.INK, lw=1.1, ls="--", label="past-only 80th percentile")
    c = tsig.loc[lo:hi].index[tsig.loc[lo:hi, "cross"]]
    ax.plot(c, tsig.loc[c, "z"], ls="none", marker="o", ms=6, color=ps.ORANGE, mec="white", mew=1.2, label="crossing (data month)")
    ax.axvline(W0, color=ps.MUTED, lw=1)
    ax.set_ylabel("z")
    ax.set_ylim(-3.9, 6.0)  # empty band at the bottom holds the legend
    ax.set_title("C. Secondary: team signal, lagged one month, same engine", loc="left")
    ax.legend(loc="lower left", ncol=3, fontsize=7)
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.set_xlim(lo - pd.offsets.MonthBegin(1), hi)
    ps.savefig(fig, "M8_share_signal")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="run on the seen 2010-01..2022-07 window (code test only)")
    args = ap.parse_args()
    main(dry_run=args.dry_run)
