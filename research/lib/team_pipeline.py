"""Parameterized, importable port of the team's climate-alpha pipeline.

Source of truth: 230GA-Final-Project/notebooks/climate_alpha_analysis.py and
notebooks/macro_state_dependence.py (commit 08e7d31). With default arguments,
`run_pipeline()` reproduces the committed outputs/tables/comparison_table.csv
and macro_state_slopes.csv to floating-point noise (see test_team_pipeline.py).

Every numerical step keeps the team's exact operations (same lstsq/solve calls on
identically built arrays, same pandas shifts and rolling windows, same RNG stream).
Only the slow pandas loops were rewritten with numpy indexing; results are unchanged.

Usage
-----
    import sys; sys.path.insert(0, '/home/hashim/projects/GA/project/research/lib')
    from team_pipeline import run_pipeline
    res = run_pipeline()                                   # team defaults, full bootstrap
    res = run_pipeline(bootstrap_reps=0)                   # cheap: skip every bootstrap
    res["comparison_table"]; res["strategies"]["Pure | Short Brown hold 6m"]

Timing conventions (inherited from the team):
  * betas/intercept estimated on the 60 months ending at t are applied to month t+1;
  * a position (and its factor overlay) set at the end of month t earns month t+1;
  * the trading cost of the trade at the end of month t is deducted from month t+1's return.
"""
from __future__ import annotations

import sys
import time
import warnings
from dataclasses import dataclass, field, replace, asdict
from typing import Callable, Iterable

import numpy as np
import pandas as pd
from scipy import stats as _stats

sys.path.insert(0, "/home/hashim/projects/GA/project/research/lib")
from common import load_team, me  # noqa: E402

TEAM_FACTOR_COLS = ("Mkt-RF", "SMB", "HML")
TEAM_GREEN = ["Fun", "RlEst", "Drugs", "Telcm", "Fin"]
TEAM_BROWN = ["Util", "Ships", "Aero", "Steel", "BldMt"]
TEAM_COSTS = {"asset": 10e-4, "Mkt-RF": 5e-4, "other_factor": 25e-4}

TEAM_PERIODS = {
    "Full 2010-Jul2026": ("2010-01-31", "2026-07-31"),
    "Validation 2010-Jul2022": ("2010-01-31", "2022-07-31"),
    "Holdout Aug2022-Jul2026": ("2022-08-31", "2026-07-31"),
    "Pre-COVID 2010-2019": ("2010-01-31", "2019-12-31"),
    "COVID 2020-2021": ("2020-01-31", "2021-12-31"),
    "Inflation/rates 2022-2024": ("2022-01-31", "2024-12-31"),
    "Recent 12m (Aug2025-Jul2026)": ("2025-08-31", "2026-07-31"),
    "Recent 18m (Feb2025-Jul2026)": ("2025-02-28", "2026-07-31"),
}
TEAM_IC_WINDOWS = {
    "Full 2010-Jul2026": ("2010-01-31", "2026-07-31"),
    "Validation 2010-Jul2022": ("2010-01-31", "2022-07-31"),
    "Holdout Aug2022-Jul2026": ("2022-08-31", "2026-07-31"),
}
TEAM_CLAIM_PERIODS = {
    "COVID 2020-2021": ("2020-01-31", "2021-12-31"),
    "Validation 2010-Jul2022": ("2010-01-31", "2022-07-31"),
    "Holdout Aug2022-Jul2026": ("2022-08-31", "2026-07-31"),
    "Inflation/rates 2022-2024": ("2022-01-31", "2024-12-31"),
}


@dataclass(frozen=True)
class Config:
    """All tunable constants. Defaults are the team's values. Override via run_pipeline(**cfg)."""
    # factor model and sizing
    beta_window: int = 60
    residual_vol_window: int = 36
    annual_vol_target: float = 0.05
    position_cap: float = 1.0
    # attention transform and signal
    z_window: int = 60
    z_min_periods: int = 36
    tail_q: float = 0.80
    tail_min_history: int = 60
    holds: tuple = (3, 6)
    # purification
    macro_window: int = 120
    min_macro_obs: int = 60
    ridge: float = 0.10
    # continuous conditioning
    cont_floor: float = 0.5
    cont_halflife: float = 3.0
    cont_min_history: int = 60
    # traded asset: "Brown leg", "Green leg" or "Green-Brown"; direction -1 = short
    traded: str = "Brown leg"
    direction: int = -1
    # inference
    nw_lags: int = 6
    bootstrap_block: int = 12
    full_start: str = "2010-01-31"
    full_end: str = "2026-07-31"
    holdout_start: str = "2022-08-31"
    covid_start: str = "2020-01-31"
    covid_end: str = "2021-12-31"
    placebo_seed: int = 11
    # macro-state notebook
    state_min_months: int = 12


# ============================================================================ statistics
def newey_west_regression(y, x, lags=6):
    """Team OLS with Bartlett-kernel HAC standard errors. Returns DataFrame(coef, t_hac6) indexed const + x cols."""
    data = pd.concat([y.rename("y"), x], axis=1, sort=True).dropna()
    names = ["const"] + list(x.columns)
    X = np.column_stack([np.ones(len(data)), data[x.columns].to_numpy()])
    response = data["y"].to_numpy()
    inv = np.linalg.pinv(X.T @ X)
    coef = inv @ X.T @ response
    resid = response - X @ coef
    xu = X * resid[:, None]
    meat = xu.T @ xu
    for lag in range(1, min(lags, len(data) - 1) + 1):
        weight = 1.0 - lag / (lags + 1.0)
        gamma = xu[lag:].T @ xu[:-lag]
        meat += weight * (gamma + gamma.T)
    se = np.sqrt(np.clip(np.diag(inv @ meat @ inv), 0, None))
    with np.errstate(divide="ignore", invalid="ignore"):  # all-zero return windows give 0/0 -> NaN, as in the team code
        t = coef / se
    return pd.DataFrame({"coef": coef, "t_hac6": t}, index=names)


def rolling_factor_model(y, x, window=60):
    """Trailing-window OLS of y on [1, x]. Returns (betas, hedged, epsilon, intercept).

    betas/intercept at t use months t-window+1..t. hedged_t = y_t - beta_{t-1}'x_t and
    epsilon_t = hedged_t - alpha_{t-1}. Same lstsq calls as the team (loop is numpy, not iloc)."""
    data = pd.concat([y.rename("y"), x], axis=1, sort=True).dropna()
    cols = list(x.columns)
    Y = data["y"].to_numpy()
    F = data[cols].to_numpy()
    n, k = len(data), len(cols)
    B = np.full((n, k), np.nan)
    A = np.full(n, np.nan)
    ones = np.ones(window)
    for end in range(window - 1, n):
        X = np.column_stack([ones, F[end - window + 1:end + 1]])
        coef, *_ = np.linalg.lstsq(X, Y[end - window + 1:end + 1], rcond=None)
        A[end], B[end] = coef[0], coef[1:]
    betas = pd.DataFrame(B, index=data.index, columns=cols, dtype=float)
    intercept = pd.Series(A, index=data.index, dtype=float)
    beta_used, alpha_used = betas.shift(1), intercept.shift(1)
    hedged = data["y"] - (beta_used * data[cols]).sum(axis=1, min_count=len(cols))
    epsilon = hedged - alpha_used
    return betas, hedged, epsilon, intercept


def rolling_z(s, window=60, min_periods=36):
    return (s - s.rolling(window, min_periods=min_periods).mean()) / s.rolling(window, min_periods=min_periods).std(ddof=1).replace(0, np.nan)


def expanding_threshold(series, q=.80, min_history=60):
    """Past-only expanding quantile (threshold for month t uses values up to t-1)."""
    return series.shift(1).expanding(min_periods=min_history).quantile(q)


def expanding_tail(series, q=.80, min_history=60):
    threshold = expanding_threshold(series, q, min_history)
    return series.gt(threshold) & threshold.notna()


def ridge_predict(train_y, train_x, test_x, ridge=.10):
    X = np.column_stack([np.ones(len(train_x)), np.asarray(train_x, dtype=float)])
    penalty = np.eye(X.shape[1]) * ridge
    penalty[0, 0] = 0
    coef = np.linalg.solve(X.T @ X + penalty, X.T @ np.asarray(train_y, dtype=float))
    return float(np.r_[1, np.asarray(test_x, dtype=float)] @ coef)


def rolling_oos_prediction(y, x, window=120, min_obs=60, ridge=.10):
    """Walk-forward ridge prediction of y_t from x_t, trained on the last `window` complete rows strictly before t."""
    panel = x.join(y.rename("target"), how="outer").sort_index()
    cols = list(x.columns)
    XA = panel[cols].to_numpy(float)
    TA = panel["target"].to_numpy(float)
    ctrl_ok = ~np.isnan(XA).any(axis=1)
    ok_idx = np.flatnonzero(ctrl_ok & ~np.isnan(TA))
    pred = np.full(len(panel), np.nan)
    for i in range(len(panel)):
        if not ctrl_ok[i]:
            continue
        j = np.searchsorted(ok_idx, i)            # complete rows strictly before row i
        if j < min_obs:
            continue
        rows = ok_idx[max(0, j - window):j]
        pred[i] = ridge_predict(TA[rows], XA[rows], XA[i], ridge=ridge)
    return pd.Series(pred, index=panel.index)


def macro_r_squared(signal, controls):
    data = pd.concat([signal.rename("y"), controls], axis=1, sort=True).dropna()
    X = np.column_stack([np.ones(len(data)), data[controls.columns].to_numpy(float)])
    y = data["y"].to_numpy(float)
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ coef
    ss_res, ss_tot = (resid ** 2).sum(), ((y - y.mean()) ** 2).sum()
    return (1 - ss_res / ss_tot if ss_tot > 0 else np.nan), len(data)


def information_coefficient(signal, forward_series, start=None, end=None, lags=6):
    """Slope of z(forward_{t+1}) on z(signal_t) with NW t. Window filter is on the signal date t."""
    fwd = forward_series.shift(-1)
    data = pd.concat([signal.rename("x"), fwd.rename("y")], axis=1, sort=True).dropna()
    if start:
        data = data.loc[start:]
    if end:
        data = data.loc[:end]
    if len(data) < 10:
        return np.nan, np.nan, len(data)
    zx = (data["x"] - data["x"].mean()) / data["x"].std(ddof=1)
    zy = (data["y"] - data["y"].mean()) / data["y"].std(ddof=1)
    fit = newey_west_regression(zy, zx.to_frame("signal_z"), lags=lags)
    return fit.loc["signal_z", "coef"], fit.loc["signal_z", "t_hac6"], len(data)


def circular_block_bootstrap(series, block=12, reps=5000, seed=230):
    """Team circular block bootstrap of the annualized mean. Same RNG stream as the team loop.
    p_two_sided = 2*min(P(draw>0), P(draw<0)) (percentile-interval inversion). reps=0 -> NaN CI/p."""
    values = series.dropna().to_numpy()
    n = len(values)
    if reps <= 0 or n == 0:
        return pd.Series({"mean_ann": 12 * values.mean() if n else np.nan, "ci_low": np.nan, "ci_high": np.nan, "p_two_sided": np.nan})
    rng = np.random.default_rng(seed)
    nb = int(np.ceil(n / block))
    offs = np.arange(block)
    draws = np.empty(reps)
    for i in range(reps):
        starts = rng.integers(0, n, size=nb)
        idx = ((starts[:, None] + offs) % n).ravel()[:n]
        draws[i] = 12 * values[idx].mean()
    return pd.Series({"mean_ann": 12 * values.mean(), "ci_low": np.quantile(draws, .025), "ci_high": np.quantile(draws, .975),
                      "p_two_sided": 2 * min((draws > 0).mean(), (draws < 0).mean())})


bootstrap = circular_block_bootstrap  # alias requested by the task


def paired_bootstrap_improvement(new_series, benchmark_series, block=12, reps=5000, seed=230):
    both = pd.concat([new_series.rename("new"), benchmark_series.rename("bench")], axis=1, sort=True).dropna()
    return circular_block_bootstrap(both["new"] - both["bench"], block=block, reps=reps, seed=seed)


def holm_bonferroni(pvalues, alpha=0.05):
    pvalues = np.asarray(pvalues, dtype=float)
    m = len(pvalues)
    order = np.argsort(pvalues)
    adjusted = np.empty(m)
    running_max = 0.0
    for rank, idx in enumerate(order):
        val = (m - rank) * pvalues[idx]
        running_max = max(running_max, val)
        adjusted[idx] = min(running_max, 1.0)
    return adjusted, adjusted < alpha


def holm(pvalues):
    """Holm-adjusted p-values only (macro notebook helper)."""
    return holm_bonferroni(pvalues)[0]


# ============================================================================ legs
def team_legs(n=5, emissions=None, exclude_from_high=None):
    """Team ranking: n lowest-intensity industries (ascending) and n highest (descending).
    Uses the team's sort (pandas default). Warns when a tie straddles the leg boundary."""
    e = load_team()["emissions"] if emissions is None else emissions
    df = pd.DataFrame({"ff": e.index, "emissions_intensity": e.values}) if isinstance(e, pd.Series) else e
    ranked = df.sort_values("emissions_intensity")
    if exclude_from_high is not None:
        ranked = ranked[~ranked.ff.isin(exclude_from_high)]
    low = ranked.head(n)["ff"].tolist()
    high = ranked.tail(n).sort_values("emissions_intensity", ascending=False)["ff"].tolist()
    v = ranked["emissions_intensity"].to_numpy()
    if n < len(v) and v[n - 1] == v[n]:
        warnings.warn(f"Green leg boundary tie at n={n}: {ranked.iloc[n-1].ff} and {ranked.iloc[n].ff} share intensity {v[n]}")
    if n < len(v) and v[-n] == v[-n - 1]:
        warnings.warn(f"Brown leg boundary tie at n={n}")
    return low, high


# ============================================================================ signal machinery
def team_controls(macro, extended=False):
    """The team's real-time ('safe') purification controls, built from the macro file."""
    rate_shock = rolling_z(macro["rate10y"].diff())
    oil_return = rolling_z(np.log(macro["wti"]).diff())
    inflation_yoy = 100 * np.log(macro["cpi"]).diff(12)
    ctrl = pd.DataFrame({
        "rate_shock": rate_shock,
        "oil_return": oil_return,
        "inflation_level_l1": rolling_z(inflation_yoy.shift(1)),
        "inflation_accel_l1": rolling_z(inflation_yoy.diff().shift(1)),
        "activity_l1": rolling_z(macro["activity"].shift(1)),
    })
    if extended:
        ctrl["recession"] = macro["recession"].astype(float)
        ctrl["supply_chain_l1"] = rolling_z(macro["supply_chain"].shift(1))
    return ctrl


def _transform(s, how):
    if callable(how):
        return how(s)
    if how in (None, "none", "identity"):
        return s.astype(float)
    if how == "log1p":
        if (s.dropna() < -1).any():
            warnings.warn("attention has values < -1; log1p gives NaN there")
        return np.log1p(s)
    if how == "log":
        return np.log(s)
    raise ValueError(f"unknown attention_transform {how!r}")


def _monthly(s, like_index=None):
    """Coerce to month-end, contiguous monthly index (so rolling windows count months, not rows)."""
    s = s.copy()
    s.index = me(s.index)
    s = s[~s.index.duplicated(keep="last")].sort_index()
    idx = s.index if like_index is None else s.index.union(like_index)
    full = pd.date_range(idx.min(), idx.max(), freq="ME")
    return s.reindex(full)


def expanding_percentile_rank(series, min_history=60):
    values = series.to_numpy(float)
    n = len(values)
    ranks = np.full(n, np.nan)
    seen = []
    for i in range(n):
        if np.isnan(values[i]):
            continue
        seen.append(values[i])
        if len(seen) >= min_history:
            ranks[i] = (np.asarray(seen) <= values[i]).mean()
    return pd.Series(ranks, index=series.index)


def continuous_conditioning_weight(series, floor=0.5, halflife=3.0, min_history=60):
    rank = expanding_percentile_rank(series, min_history=min_history)
    raw = ((rank - floor) / (1 - floor)).clip(lower=0.0, upper=1.0)
    smoothed = raw.ewm(halflife=halflife, min_periods=1).mean()
    smoothed[rank.isna()] = np.nan
    return smoothed


def cross_and_holds(state, holds=(3, 6)):
    """Returns (cross, {h: hold_state}). hold_state_t is True for the crossing month and the next h-1 months."""
    state = state.astype(bool)
    cross = state & ~state.shift(1).fillna(False).astype(bool)
    return cross, {h: cross.rolling(h, min_periods=1).max().astype(bool) for h in holds}


def build_signals(attention_raw, macro, cfg: Config, controls=None, attention_transform="log1p"):
    """z-score, p80 thresholds, walk-forward purification, crossings/holds and continuous weights."""
    att_in = _monthly(attention_raw, macro.index)
    attention = rolling_z(_transform(att_in, attention_transform), cfg.z_window, cfg.z_min_periods)
    ctrl = team_controls(macro) if controls is None else controls
    if not ctrl.index.equals(attention.index):
        ctrl = ctrl.reindex(attention.index.union(ctrl.index))
    prediction = rolling_oos_prediction(attention, ctrl, window=cfg.macro_window, min_obs=cfg.min_macro_obs, ridge=cfg.ridge)
    pure = attention - prediction
    out = {"attention_input": att_in, "raw": attention, "controls": ctrl, "prediction": prediction, "pure": pure}
    for key, sig in (("raw", attention), ("pure", pure)):
        thr = expanding_threshold(sig, cfg.tail_q, cfg.tail_min_history)
        state = sig.gt(thr) & thr.notna()
        cross, holds = cross_and_holds(state, cfg.holds)
        out[f"threshold_{key}"] = thr
        out[f"state_{key}"] = state
        out[f"cross_{key}"] = cross
        out[f"hold_{key}"] = holds
        out[f"w_{key}"] = continuous_conditioning_weight(sig, cfg.cont_floor, cfg.cont_halflife, cfg.cont_min_history)
    return out


# ============================================================================ strategy builders
def _magnitude(residual, annual_vol_target=.05, vol_window=36, cap=1.0):
    sigma = residual.rolling(vol_window, min_periods=vol_window).std(ddof=1)
    return sigma, (annual_vol_target / (np.sqrt(12) * sigma)).clip(upper=cap)


def state_position(state, residual, direction, annual_vol_target=.05, vol_window=36, cap=1.0):
    sigma, magnitude = _magnitude(residual, annual_vol_target, vol_window, cap)
    position = pd.Series(np.nan, index=residual.index)
    live = position.index >= sigma.first_valid_index()
    position.loc[live] = (direction * magnitude).loc[live].where(state.reindex(position.index).fillna(False), 0)
    return position


def continuous_position(weight, residual, direction, annual_vol_target=.05, vol_window=36, cap=1.0):
    sigma, magnitude = _magnitude(residual, annual_vol_target, vol_window, cap)
    position = pd.Series(np.nan, index=residual.index)
    live = position.index >= sigma.first_valid_index()
    w = weight.reindex(position.index).fillna(0).clip(lower=0.0, upper=1.0)
    position.loc[live] = (direction * magnitude * w).loc[live]
    return position


def resolve_costs(factor_cols, costs=None, cost_bps_uniform=None):
    """Per-unit-turnover cost rates {'asset': r, factor: r, ...}. Team default: 10bp asset, 5bp Mkt-RF, 25bp others."""
    if cost_bps_uniform is not None:
        r = float(cost_bps_uniform) * 1e-4
        return {"asset": r, **{c: r for c in factor_cols}}
    c = dict(TEAM_COSTS if costs is None else costs)
    other = c.get("other_factor", TEAM_COSTS["other_factor"])
    return {"asset": c.get("asset", TEAM_COSTS["asset"]), **{f: c.get(f, other) for f in factor_cols}}


def asset_strategy_returns(position, model, factors, factor_cols=TEAM_FACTOR_COLS, cost_rates=None, leg_multiplier=1.0):
    """Team P&L engine. position_t (set at end of t) earns model return and -position_t*beta_t overlay in t+1.
    Cost of the trade at t is charged at t+1. Returns DataFrame with position, gross_return, cost (charged that month),
    cost_incurred (trade at t), net_return, turnover (asset + overlay), asset_turnover, overlay_turnover."""
    factor_cols = list(factor_cols)
    rates = cost_rates if cost_rates is not None else resolve_costs(factor_cols)
    idx = position.index.intersection(model["return"].index).intersection(factors.index).intersection(model["betas"].index)
    h = position.reindex(idx)
    idx = idx[idx >= h.first_valid_index()]
    h = h.reindex(idx).fillna(0)
    beta = model["betas"].reindex(idx)
    f = factors[factor_cols].reindex(idx)
    overlay = pd.DataFrame(-h.to_numpy()[:, None] * beta.to_numpy(), index=idx, columns=beta.columns)
    gross = h.shift(1) * model["return"].reindex(idx) + (overlay.shift(1) * f).sum(axis=1, min_count=len(factor_cols))
    asset_turnover = leg_multiplier * h.diff().abs().fillna(h.abs())
    overlay_turnover = overlay.diff().abs().fillna(overlay.abs())
    # group factors by rate in order of first appearance; team grouping = [Mkt-RF], [SMB, HML]
    groups: dict = {}
    for c in factor_cols:
        groups.setdefault(rates[c], []).append(c)
    cost = rates["asset"] * asset_turnover
    for rate, cols in groups.items():
        cost = cost + (rate * overlay_turnover[cols[0]] if len(cols) == 1 else rate * overlay_turnover[cols].sum(axis=1))
    charged = cost.shift(1).fillna(0)
    return pd.DataFrame({"position": h, "gross_return": gross, "cost": charged, "net_return": gross - charged,
                         "turnover": asset_turnover + overlay_turnover.sum(axis=1), "cost_incurred": cost,
                         "asset_turnover": asset_turnover, "overlay_turnover": overlay_turnover.sum(axis=1)})


# ============================================================================ evaluation
def period_stats(net_return_series, start, end, label=None, factors=None, factor_cols=TEAM_FACTOR_COLS, lags=6):
    """Team period statistics. Alpha/loadings from NW(lags) regression on `factor_cols` of `factors`."""
    if factors is None:
        factors = load_team()["ff3"]
    s = net_return_series.loc[start:end].dropna()
    if len(s) == 0:
        return None
    active = s[s != 0]
    ann_net = 12 * s.mean()
    ann_vol = np.sqrt(12) * s.std(ddof=1) if len(s) > 1 else np.nan
    sharpe = ann_net / ann_vol if ann_vol else np.nan
    wealth = (1 + s).cumprod()
    dd = (wealth / wealth.cummax() - 1).min()
    cols = list(factor_cols)
    fit = newey_west_regression(s, factors[cols].reindex(s.index), lags=lags)
    row = {"period": label, "n_months": len(s), "active_months": len(active), "ann_net": ann_net, "ann_vol": ann_vol,
           "sharpe_net": sharpe, "max_drawdown": dd, "alpha_ann": 12 * fit.loc["const", "coef"], "alpha_t_hac6": fit.loc["const", "t_hac6"]}
    for c in cols:
        nm = "MKT" if c == "Mkt-RF" else c
        row[f"{nm}_beta"] = fit.loc[c, "coef"]
    for c in cols:
        nm = "MKT" if c == "Mkt-RF" else c
        row[f"{nm}_t"] = fit.loc[c, "t_hac6"]
    return row


def all_period_stats(net_return_series, periods=None, **kw):
    periods = TEAM_PERIODS if periods is None else periods
    return pd.DataFrame([r for label, (s, e) in periods.items() if (r := period_stats(net_return_series, s, e, label, **kw)) is not None])


def turnover_and_cost_drag(df, start="2010-01-31", end="2026-07-31"):
    sl = df.loc[start:end]
    return {"annual_turnover_x": 12 * sl["turnover"].mean(), "ann_gross_return": 12 * sl["gross_return"].mean(),
            "ann_cost_drag": 12 * (sl["gross_return"] - sl["net_return"]).mean(), "ann_net_return": 12 * sl["net_return"].mean()}


def turnover_stats(df, start, end):
    if "turnover" not in df.columns:
        return np.nan
    s = df["turnover"].loc[start:end].dropna()
    return 12 * s.mean() if len(s) else np.nan


def implied_lambda(alpha_ann_series, sigma_tgt, omega_ann_series):
    return (alpha_ann_series / 12) / (2 * (sigma_tgt / np.sqrt(12)) * (omega_ann_series / np.sqrt(12)))


# ============================================================================ macro-state notebook
def above_past_median(s, window=120, min_periods=60):
    median = s.shift(1).rolling(window, min_periods=min_periods).median()
    return (s > median).where(median.notna())


def team_states(macro):
    inflation_yoy = 100 * np.log(macro["cpi"]).diff(12)
    activity_3m = macro["activity"].rolling(3).mean().shift(1)
    return pd.DataFrame({
        "High rates": above_past_median(macro["rate10y"]),
        "Rising rates (12m)": (macro["rate10y"].diff(12) > 0).where(macro["rate10y"].diff(12).notna()),
        "Oil up (12m)": (np.log(macro["wti"]).diff(12) > 0).where(macro["wti"].diff(12).notna()),
        "High inflation": above_past_median(inflation_yoy.shift(1)),
        "Weak activity (CFNAI<0)": (activity_3m < 0).where(activity_3m.notna()),
        "Supply-chain stress (GSCPI>0)": (macro["supply_chain"].shift(1) > 0).where(macro["supply_chain"].shift(1).notna()),
    }).astype(float)


def _nw_matrix(y, X, lags=6):
    X = np.column_stack([np.ones(len(X)), X])
    inv = np.linalg.pinv(X.T @ X)
    coef = inv @ X.T @ y
    xu = X * (y - X @ coef)[:, None]
    meat = xu.T @ xu
    for lag in range(1, min(lags, len(y) - 1) + 1):
        gamma = xu[lag:].T @ xu[:-lag]
        meat += (1 - lag / (lags + 1)) * (gamma + gamma.T)
    return coef, inv @ meat @ inv


def state_slopes(signal, state, forward_eps, start, end, min_months=12, lags=6):
    """eps_{t+1} = a + c S_t + b_off A_t (1-S_t) + b_on A_t S_t, A and eps z-scored in-window."""
    zs = lambda s: (s - s.mean()) / s.std(ddof=1)  # noqa: E731
    data = pd.concat([signal.rename("A"), state.rename("S"), forward_eps.rename("y")], axis=1, sort=True).loc[start:end].dropna()
    a, y, s = zs(data["A"]).to_numpy(), zs(data["y"]).to_numpy(), data["S"].to_numpy()
    n_on, n_off = int(s.sum()), int((1 - s).sum())
    if min(n_on, n_off) < min_months:
        return {"n": len(data), "n_on": n_on, "slope_off": np.nan, "t_off": np.nan, "slope_on": np.nan, "t_on": np.nan, "diff": np.nan, "t_diff": np.nan}
    coef, cov = _nw_matrix(y, np.column_stack([s, a * (1 - s), a * s]), lags)
    b_off, b_on = coef[2], coef[3]
    se_off, se_on = np.sqrt(cov[2, 2]), np.sqrt(cov[3, 3])
    se_diff = np.sqrt(cov[2, 2] + cov[3, 3] - 2 * cov[2, 3])
    return {"n": len(data), "n_on": n_on, "slope_off": b_off, "t_off": b_off / se_off, "slope_on": b_on, "t_on": b_on / se_on,
            "diff": b_on - b_off, "t_diff": (b_on - b_off) / se_diff}


def macro_state_tables(signals: dict, epsilon, macro, end="2026-07-31", holdout_start="2022-08-31", min_months=12, lags=6, states=None):
    """Port of macro_state_dependence.py. Returns (full_table, split_table, start_date)."""
    states = team_states(macro) if states is None else states
    forward_eps = epsilon.shift(-1)
    # team: first month where the purified signal and the forward residual both exist
    start = pd.concat([*signals.values(), forward_eps], axis=1, sort=True).dropna().index.min()
    rows = [{"signal": sn, "state": st, **state_slopes(sig, states[st], forward_eps, start, end, min_months, lags)}
            for sn, sig in signals.items() for st in states]
    full = pd.DataFrame(rows)
    full["p_diff"] = 2 * (1 - _stats.norm.cdf(full["t_diff"].abs()))
    full["holm_p"] = holm(full["p_diff"])
    rows = []
    for sn, sig in signals.items():
        for st in states:
            for period, (s, e) in {"Pre-holdout": (start, pd.Timestamp(holdout_start) - pd.offsets.MonthEnd(1)), "Holdout": (holdout_start, end)}.items():
                r = state_slopes(sig, states[st], forward_eps, s, e, min_months, lags)
                rows.append({"signal": sn, "state": st, "period": period, "n_on": r["n_on"], "slope_off": r["slope_off"],
                             "slope_on": r["slope_on"], "t_diff": r["t_diff"]})
    split = pd.DataFrame(rows).pivot_table(index=["signal", "state"], columns="period", values=["n_on", "slope_off", "slope_on"], sort=False)
    return full, split, start


# ============================================================================ placebo
def placebo_test(attention_z, epsilon, model, factors, factor_cols, cost_rates, cfg: Config, reps=300, seed=11,
                 start="2010", end="2026-07"):
    """Team placebo: block-bootstrap the calendar order of attention z, rebuild the continuous strategy."""
    attn_vals = attention_z.dropna()
    rng = np.random.default_rng(seed)
    draws = np.empty(reps)
    n, block = len(attn_vals), cfg.bootstrap_block
    for i in range(reps):
        starts = rng.integers(0, n, size=int(np.ceil(n / block)))
        idx = ((starts[:, None] + np.arange(block)) % n).ravel()[:n]
        shuffled = pd.Series(attn_vals.to_numpy()[idx], index=attn_vals.index)
        w = continuous_conditioning_weight(shuffled, cfg.cont_floor, cfg.cont_halflife, cfg.cont_min_history)
        pos = continuous_position(w, epsilon, cfg.direction, cfg.annual_vol_target, cfg.residual_vol_window, cfg.position_cap)
        ret = asset_strategy_returns(pos, model, factors, factor_cols, cost_rates)
        draws[i] = 12 * ret["net_return"].loc[start:end].mean()
    return draws


# ============================================================================ orchestrator
_SHORT = {"Brown leg": "Brown", "Green leg": "Green", "Green-Brown": "Green-Brown"}


def run_pipeline(industries=None, factors=None, macro=None, green=None, brown=None,
                 factor_cols=TEAM_FACTOR_COLS, attention=None, costs=None, cost_bps_uniform=None,
                 bootstrap_reps=5000, seed=230, eval_factor_cols=None, controls=None,
                 attention_transform="log1p", placebo_reps=0, macro_states=True, paired=True,
                 extras=True, **cfg) -> dict:
    """Run the team's full pipeline with optional substitutions.

    industries : DataFrame of industry returns (decimal, month-end index). Default team FF49 file (VW).
    factors    : DataFrame with factor columns and 'RF'. Default team FF3 file.
    macro      : DataFrame with attention, rate10y, wti, cpi, activity, recession, supply_chain. Default team file.
    green/brown: industry name lists. Default team legs (5 lowest / 5 highest emissions intensity).
    factor_cols: hedge factors (any columns of `factors`, e.g. FF5 + UMD + a commodity return).
    eval_factor_cols: factors for period alpha regressions (default = factor_cols).
    attention  : replacement attention pd.Series (month-end index); goes through transform -> rolling z ->
                 p80 threshold -> purification -> continuous weight exactly like the team series.
    attention_transform: 'log1p' (team), 'log', 'none', or a callable.
    controls   : replacement purification controls DataFrame (default team 'safe' controls from macro).
    costs      : dict {'asset': r, 'Mkt-RF': r, <factor>: r, 'other_factor': r} (decimal per unit turnover).
    cost_bps_uniform: one cost level in bp applied to the asset and every overlay factor (overrides costs).
    bootstrap_reps: 5000 reproduces the team; small values (or 0) for sweeps.
    placebo_reps: team used 300 (seed 11); default 0 skips it.
    **cfg      : any Config field (beta_window, tail_q, holds, annual_vol_target, traded, direction, ...).
    """
    t0 = time.perf_counter()
    C = replace(Config(), **cfg)
    factor_cols = list(factor_cols)
    eval_cols = list(factor_cols if eval_factor_cols is None else eval_factor_cols)
    T = None
    if industries is None or factors is None or macro is None or attention is None:
        T = load_team()
    industries = T["industries"] if industries is None else industries
    factors = T["ff3"] if factors is None else factors
    macro = T["macro"] if macro is None else macro
    green = TEAM_GREEN if green is None else list(green)
    brown = TEAM_BROWN if brown is None else list(brown)
    rates = resolve_costs(factor_cols, costs, cost_bps_uniform)
    fs, fe, hs = C.full_start, C.full_end, C.holdout_start
    val_end = (pd.Timestamp(hs) - pd.offsets.MonthEnd(1)).strftime("%Y-%m-%d")
    timings = {}

    # ---- legs
    low_ret = industries[green].mean(axis=1)
    high_ret = industries[brown].mean(axis=1)
    green_brown = (low_ret - high_ret).rename("Green-Brown")
    green_leg = (low_ret - factors["RF"]).rename("Green leg excess")
    brown_leg = (high_ret - factors["RF"]).rename("Brown leg excess")
    legs = {"green": green, "brown": brown, "green_ret": low_ret, "brown_ret": high_ret, "green_minus_brown": green_brown,
            "green_excess": green_leg, "brown_excess": brown_leg}

    # ---- rolling factor models
    models = {}
    for name, series in {"Green-Brown": green_brown, "Green leg": green_leg, "Brown leg": brown_leg}.items():
        aligned = pd.concat([series, factors[factor_cols]], axis=1, sort=True).dropna()
        b, h, e, a = rolling_factor_model(aligned.iloc[:, 0], aligned[factor_cols], C.beta_window)
        models[name] = {"return": aligned.iloc[:, 0], "betas": b, "intercept": a, "hedged": h, "epsilon": e}
    timings["models"] = time.perf_counter() - t0

    # ---- signals
    att_raw = macro["attention"] if attention is None else attention
    sig = build_signals(att_raw, macro, C, controls=controls, attention_transform=attention_transform)
    timings["signals"] = time.perf_counter() - t0

    # ---- strategies
    tm = models[C.traded]
    eps = tm["epsilon"]
    tag = f"{'Short' if C.direction < 0 else 'Long'} {_SHORT[C.traded]}"
    pos_kw = dict(annual_vol_target=C.annual_vol_target, vol_window=C.residual_vol_window, cap=C.position_cap)
    run = lambda pos: asset_strategy_returns(pos, tm, factors, factor_cols, rates)  # noqa: E731
    baseline = {}
    for hold in C.holds:
        for label, key in (("Original", "raw"), ("Pure", "pure")):
            baseline[f"{label} | {tag} hold {hold}m"] = run(state_position(sig[f"hold_{key}"][hold], eps, C.direction, **pos_kw))
    improved = {
        "Continuous | raw attention": run(continuous_position(sig["w_raw"], eps, C.direction, **pos_kw)),
        "Continuous | pure attention": run(continuous_position(sig["w_pure"], eps, C.direction, **pos_kw)),
    }
    always_on = pd.Series(True, index=eps.index)
    benchmarks = {
        f"Benchmark | Always-{tag[0].lower()}{tag[1:]}": run(state_position(always_on, eps, C.direction, **pos_kw)),  # team: "Always-short Brown"
        "Benchmark | Buy-and-hold Green-Brown": pd.DataFrame({"net_return": green_brown, "turnover": 0.0}),
    }
    strategies = {**baseline, **improved, **benchmarks}
    timings["strategies"] = time.perf_counter() - t0

    ps_kw = dict(factors=factors, factor_cols=eval_cols, lags=C.nw_lags)
    periods = dict(TEAM_PERIODS)

    # ---- per-period table (every strategy x every period)
    rows = []
    for name, df in strategies.items():
        st = all_period_stats(df["net_return"], periods, **ps_kw)
        st.insert(0, "strategy", name)
        rows.append(st)
    period_table = pd.concat(rows, ignore_index=True)

    # ---- IC table
    # labels are the team's; dates follow cfg (full_start, full_end, holdout_start)
    ic_windows = {"Full 2010-Jul2026": (fs, fe), "Validation 2010-Jul2022": (fs, val_end), "Holdout Aug2022-Jul2026": (hs, fe)}
    ic_rows = []
    for sn, s in [("Raw attention", sig["raw"]), ("Purified attention", sig["pure"]),
                  ("Continuous weight (raw)", sig["w_raw"]), ("Continuous weight (pure)", sig["w_pure"])]:
        for label, (a, b) in ic_windows.items():
            ic, t, n = information_coefficient(s, eps, a, b, lags=C.nw_lags)
            ic_rows.append({"signal": sn, "period": label, "IC": ic, "t_hac6": t, "n": n})
    ic_table = pd.DataFrame(ic_rows)

    # ---- multiple-testing claims (team: 8 strategies x 4 periods)
    claim_periods = dict(TEAM_CLAIM_PERIODS)
    claims = []
    for name, df in strategies.items():
        for label, (a, b) in claim_periods.items():
            r = period_stats(df["net_return"], a, b, label, **ps_kw)
            if r is not None and not np.isnan(r["alpha_t_hac6"]):
                claims.append({"strategy": name, "period": label, "alpha_t_hac6": r["alpha_t_hac6"]})
    claims_table = pd.DataFrame(claims)
    claims_table["p_two_sided"] = 2 * (1 - _stats.norm.cdf(np.abs(claims_table["alpha_t_hac6"])))
    adj, rej = holm_bonferroni(claims_table["p_two_sided"].to_numpy())
    claims_table["holm_p"] = adj
    claims_table["reject_at_5pct"] = rej
    claims_table = claims_table.sort_values("p_two_sided")

    # ---- comparison table (team row_for)
    boot_rows = {}

    def row_for(name, df):
        full = period_stats(df["net_return"], fs, fe, "full", **ps_kw)
        oos = period_stats(df["net_return"], hs, fe, "oos", **ps_kw)
        cx = df["net_return"].loc[fs[:4]:fe[:7]]
        cx = cx[~((cx.index >= C.covid_start) & (cx.index <= C.covid_end))]
        covid_excl = period_stats(cx, cx.index.min(), cx.index.max(), "ex_covid", **ps_kw)
        boot = circular_block_bootstrap(df["net_return"].loc[fs[:4]:fe[:7]], block=C.bootstrap_block, reps=bootstrap_reps, seed=seed)
        boot_rows[name] = boot
        mt = claims_table[claims_table.strategy == name]
        mt_sig = bool(mt["reject_at_5pct"].any()) if len(mt) else np.nan
        g = lambda d, k: d[k] if d else np.nan  # noqa: E731
        return {"strategy": name, "active_months_full": g(full, "active_months"), "ann_return_full": g(full, "ann_net"),
                "ann_vol_full": g(full, "ann_vol"), "sharpe_full": g(full, "sharpe_net"), "max_drawdown_full": g(full, "max_drawdown"),
                "annual_turnover_full": turnover_stats(df, fs, fe), "factor_alpha_ann_full": g(full, "alpha_ann"),
                "newey_west_t_full": g(full, "alpha_t_hac6"), "bootstrap_ci_low": boot["ci_low"], "bootstrap_ci_high": boot["ci_high"],
                "bootstrap_p": boot["p_two_sided"], "oos_ann_return": g(oos, "ann_net"), "oos_alpha_t": g(oos, "alpha_t_hac6"),
                "covid_excluded_ann_return": g(covid_excl, "ann_net"), "significant_after_multiple_testing": mt_sig}

    comparison_table = pd.DataFrame([row_for(n, d) for n, d in strategies.items()])
    bootstrap_table = pd.DataFrame(boot_rows).T
    timings["tables"] = time.perf_counter() - t0

    out = {"config": C, "cost_rates": rates, "factor_cols": factor_cols, "eval_factor_cols": eval_cols,
           "legs": legs, "models": models, "signals": sig, "strategies": strategies,
           "baseline_names": list(baseline), "improved_names": list(improved), "benchmark_names": list(benchmarks),
           "comparison_table": comparison_table, "period_table": period_table, "ic_table": ic_table,
           "claims_table": claims_table, "bootstrap_table": bootstrap_table}

    if extras:
        # unconditional raw-spread regression and robustness of leg width (team Section 2 and 6)
        unc = {}
        for label, (a, b) in {"Full 1970-Jul2022": ("1970-01-31", val_end), "Post-2010": (fs, val_end)}.items():
            fit = newey_west_regression(green_brown.loc[a:b], factors[eval_cols].loc[a:b], lags=C.nw_lags)
            unc[label] = {"alpha_ann": 12 * fit.loc["const", "coef"], "alpha_t": fit.loc["const", "t_hac6"],
                          **{("MKT" if c == "Mkt-RF" else c): fit.loc[c, "coef"] for c in eval_cols}}
        out["unconditional"] = pd.DataFrame(unc).T
        rob = []
        for label, kw in [("Baseline N=5", dict(n=5)), ("Widened N=10", dict(n=10)), ("N=5, ex-Utilities", dict(n=5, exclude_from_high=["Util"]))]:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                lo, hi = team_legs(**kw)
            gb = (industries[lo].mean(axis=1) - industries[hi].mean(axis=1)).rename("gb")
            fit = newey_west_regression(gb.loc[fs:val_end], factors[eval_cols].loc[fs:val_end], lags=C.nw_lags)
            rob.append({"specification": label, "alpha_ann_2010_2022": 12 * fit.loc["const", "coef"], "alpha_t_hac6": fit.loc["const", "t_hac6"]})
        out["robustness"] = pd.DataFrame(rob)
        common = sig["pure"].dropna().index
        r2_raw, n_raw = macro_r_squared(sig["raw"].reindex(common), sig["controls"])
        r2_pure, n_pure = macro_r_squared(sig["pure"], sig["controls"])
        diag = [{"signal": "Raw attention", "n": n_raw, "macro_r_squared": r2_raw},
                {"signal": "Purified attention (investable)", "n": n_pure, "macro_r_squared": r2_pure}]
        if controls is None and {"recession", "supply_chain"} <= set(macro.columns):
            r2_ext, n_ext = macro_r_squared(sig["raw"], team_controls(macro, extended=True))
            diag.append({"signal": "Raw attention vs. extended (ex-post) controls", "n": n_ext, "macro_r_squared": r2_ext})
        out["diagnostics"] = pd.DataFrame(diag).set_index("signal")
        out["turnover_table"] = pd.DataFrame({n: turnover_and_cost_drag(strategies[n], fs, fe) for n in baseline}).T
        lam = []
        omega = eps.rolling(C.residual_vol_window, min_periods=C.residual_vol_window).std(ddof=1) * np.sqrt(12)
        for n in baseline:
            r = period_stats(strategies[n]["net_return"], fs, fe, n, **ps_kw)
            imp = implied_lambda(pd.Series(r["alpha_ann"], index=omega.dropna().index), C.annual_vol_target, omega.dropna())
            lam.append({"strategy": n, "implied_lambda_mean": imp.mean(), "implied_lambda_median": imp.median()})
        out["lambda_table"] = pd.DataFrame(lam)
        sens = []
        for floor, hl in [(0.5, 3.0), (0.6, 6.0), (0.4, 1.5)]:
            w = continuous_conditioning_weight(sig["pure"], floor=floor, halflife=hl, min_history=C.cont_min_history)
            ret = run(continuous_position(w, eps, C.direction, **pos_kw))
            v = period_stats(ret["net_return"], fs, val_end, "val", **ps_kw)
            h_ = period_stats(ret["net_return"], hs, fe, "hold", **ps_kw)
            sens.append({"floor": floor, "halflife": hl, "val_ann_net": v["ann_net"], "val_t": v["alpha_t_hac6"],
                         "hold_ann_net": h_["ann_net"], "hold_t": h_["alpha_t_hac6"]})
        out["sensitivity"] = pd.DataFrame(sens)

    if paired and len(C.holds) >= 1:
        pr, pv = [], []
        for cname, key in (("Continuous | raw attention", "Original"), ("Continuous | pure attention", "Pure")):
            for hold in C.holds:
                bench = f"{key} | {tag} hold {hold}m"
                a = strategies[cname]["net_return"].loc[hs[:7]:fe[:7]]
                b = strategies[bench]["net_return"].loc[hs[:7]:fe[:7]]
                boot = paired_bootstrap_improvement(a, b, block=C.bootstrap_block, reps=bootstrap_reps, seed=seed)
                pr.append({"new": cname, "benchmark": bench, **boot.to_dict()})
                pv.append(boot.p_two_sided)
        paired_table = pd.DataFrame(pr)
        if bootstrap_reps > 0:
            adj, rej = holm_bonferroni(pv)
            paired_table["holm_p"] = adj
            paired_table["reject_at_5pct"] = rej
        out["paired_table"] = paired_table

    if macro_states:
        try:
            full, split, start = macro_state_tables({"Raw attention": sig["raw"], "Purified attention": sig["pure"]}, eps, macro,
                                                    end=fe, holdout_start=hs, min_months=C.state_min_months, lags=C.nw_lags)
            out["macro_state_table"], out["macro_state_by_period"], out["macro_state_start"] = full, split, start
        except KeyError as exc:  # custom macro without the needed columns
            out["macro_state_error"] = str(exc)

    if placebo_reps:
        draws = placebo_test(sig["raw"], eps, tm, factors, factor_cols, rates, C, reps=placebo_reps, seed=C.placebo_seed,
                             start=fs[:4], end=fe[:7])
        real = 12 * strategies["Continuous | raw attention"]["net_return"].loc[fs[:4]:fe[:7]].mean()
        out["placebo"] = {"draws": draws, "real_mean": real, "p_ge_real": float((draws >= real).mean())}

    timings["total"] = time.perf_counter() - t0
    out["timings"] = timings
    return out


__all__ = [
    "Config", "run_pipeline", "rolling_factor_model", "newey_west_regression", "rolling_z", "expanding_threshold",
    "expanding_tail", "rolling_oos_prediction", "ridge_predict", "build_signals", "team_controls", "cross_and_holds",
    "expanding_percentile_rank", "continuous_conditioning_weight", "state_position", "continuous_position",
    "asset_strategy_returns", "resolve_costs", "period_stats", "all_period_stats", "information_coefficient",
    "circular_block_bootstrap", "bootstrap", "paired_bootstrap_improvement", "holm_bonferroni", "holm", "team_legs",
    "macro_state_tables", "state_slopes", "team_states", "placebo_test", "turnover_and_cost_drag", "macro_r_squared",
    "TEAM_GREEN", "TEAM_BROWN", "TEAM_FACTOR_COLS", "TEAM_COSTS", "TEAM_PERIODS",
]
