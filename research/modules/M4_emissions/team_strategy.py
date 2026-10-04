"""Faithful re-implementation of the team's 'Original | Short Brown hold 3m/6m' strategies
(notebooks/climate_alpha_analysis.py, Sections 2-4) so the Brown leg can be swapped for the EPA-ranked Brown leg.

Conventions copied from the team code (not changed here):
- Brown leg excess = EW Brown industries minus RF (team ff3 file). Rolling 60m OLS on team FF3 (Mkt-RF, SMB, HML);
  betas and intercept shifted one month before use; epsilon_t = y_t - beta_{t-1}'f_t - alpha_{t-1}.
- Attention z_t = rolling 60m z-score (min 36) of log1p(attention_t) (team macro file; = FRED EMVENRGYENVREG).
  Extreme state_t = z_t > expanding past-only 80th percentile of z (threshold uses z up to t-1, min 60 obs).
- Cross = first month of an extreme state; hold window = cross in the last 3 (or 6) months including t.
- Position h_t = -min(1, 0.05 / (sqrt(12) sd_36(epsilon))) while in a hold window, else 0; h_t formed at end of t
  earns month t+1; FF3 overlay -h_t * beta_t earns t+1. Costs: 10 bp asset, 5 bp Mkt, 25 bp SMB/HML per unit traded,
  charged one month after the trade (team convention).
"""
from __future__ import annotations
import numpy as np
import pandas as pd

FACTOR_COLS = ["Mkt-RF", "SMB", "HML"]
COST_ASSET, COST_MKT, COST_OTHER = 10e-4, 5e-4, 25e-4


def newey_west_regression(y, x, lags=6):
    data = pd.concat([y.rename("y"), x], axis=1).dropna()
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
    return pd.DataFrame({"coef": coef, "t_hac6": coef / se}, index=names)


def rolling_factor_model(y, x, window=60):
    data = pd.concat([y.rename("y"), x], axis=1).dropna()
    betas = pd.DataFrame(index=data.index, columns=x.columns, dtype=float)
    intercept = pd.Series(index=data.index, dtype=float)
    for end in range(window - 1, len(data)):
        sample = data.iloc[end - window + 1:end + 1]
        X = np.column_stack([np.ones(window), sample[x.columns].to_numpy()])
        coef, *_ = np.linalg.lstsq(X, sample["y"].to_numpy(), rcond=None)
        intercept.iloc[end], betas.iloc[end] = coef[0], coef[1:]
    beta_used, alpha_used = betas.shift(1), intercept.shift(1)
    hedged = data["y"] - (beta_used * data[x.columns]).sum(axis=1, min_count=len(x.columns))
    return betas, hedged, hedged - alpha_used


def rolling_z(s, window=60, min_periods=36):
    return (s - s.rolling(window, min_periods=min_periods).mean()) / s.rolling(window, min_periods=min_periods).std(ddof=1).replace(0, np.nan)


def expanding_tail(series, q=.80, min_history=60):
    threshold = series.shift(1).expanding(min_periods=min_history).quantile(q)
    return series.gt(threshold) & threshold.notna()


def cross_and_holds(state):
    state = state.astype(bool)
    cross = state & ~state.shift(1, fill_value=False).astype(bool)
    return cross, cross.rolling(3, min_periods=1).max().astype(bool), cross.rolling(6, min_periods=1).max().astype(bool)


def state_position(state, residual, direction, annual_vol_target=.05, vol_window=36):
    sigma = residual.rolling(vol_window, min_periods=vol_window).std(ddof=1)
    magnitude = (annual_vol_target / (np.sqrt(12) * sigma)).clip(upper=1.0)
    position = pd.Series(np.nan, index=residual.index)
    live = position.index >= sigma.first_valid_index()
    st = state.reindex(position.index).fillna(False).astype(bool)
    position.loc[live] = (direction * magnitude).loc[live].where(st.loc[live], 0)
    return position


def asset_strategy_returns(position, model, factors):
    idx = position.index.intersection(model["return"].index).intersection(factors.index).intersection(model["betas"].index)
    h = position.reindex(idx); idx = idx[idx >= h.first_valid_index()]; h = h.reindex(idx).fillna(0)
    beta = model["betas"].reindex(idx); f = factors[FACTOR_COLS].reindex(idx)
    overlay = pd.DataFrame(-h.to_numpy()[:, None] * beta.to_numpy(), index=idx, columns=beta.columns)
    gross = h.shift(1) * model["return"].reindex(idx) + (overlay.shift(1) * f).sum(axis=1, min_count=len(FACTOR_COLS))
    asset_turnover = h.diff().abs().fillna(h.abs())
    overlay_turnover = overlay.diff().abs().fillna(overlay.abs())
    cost = COST_ASSET * asset_turnover + COST_MKT * overlay_turnover["Mkt-RF"] + COST_OTHER * overlay_turnover[["SMB", "HML"]].sum(axis=1)
    return pd.DataFrame({"position": h, "gross_return": gross, "net_return": gross - cost.shift(1).fillna(0),
                         "turnover": asset_turnover + overlay_turnover.sum(axis=1)})


def short_brown_strategies(brown_ret: pd.Series, factors: pd.DataFrame, attention: pd.Series) -> dict:
    """Return {'hold3': df, 'hold6': df} for a given EW Brown-leg raw return series."""
    y = (brown_ret - factors["RF"]).dropna()
    aligned = pd.concat([y.rename("y"), factors[FACTOR_COLS]], axis=1).dropna()
    b, h, e = rolling_factor_model(aligned["y"], aligned[FACTOR_COLS], 60)
    model = {"return": aligned["y"], "betas": b, "hedged": h, "epsilon": e}
    z = rolling_z(np.log1p(attention))
    p80 = expanding_tail(z)
    _, h3, h6 = cross_and_holds(p80)
    return {"hold3": asset_strategy_returns(state_position(h3, e, -1), model, factors),
            "hold6": asset_strategy_returns(state_position(h6, e, -1), model, factors),
            "epsilon": e}


def period_stats(net, factors, start, end):
    s = net.loc[start:end].dropna()
    if len(s) < 3:
        return None
    fit = newey_west_regression(s, factors[FACTOR_COLS].loc[s.index])
    wealth = (1 + s).cumprod()
    return {"n_months": len(s), "active_months": int((s != 0).sum()), "ann_net": 12 * s.mean(),
            "ann_vol": np.sqrt(12) * s.std(ddof=1), "sharpe_net": (12 * s.mean()) / (np.sqrt(12) * s.std(ddof=1)) if s.std() > 0 else np.nan,
            "max_drawdown": (wealth / wealth.cummax() - 1).min(),
            "alpha_ff3_ann": 12 * fit.loc["const", "coef"], "alpha_ff3_t_hac6": fit.loc["const", "t_hac6"],
            "b_HML": fit.loc["HML", "coef"], "t_HML": fit.loc["HML", "t_hac6"]}
