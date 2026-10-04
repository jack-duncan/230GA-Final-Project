"""Re-implementation (not execution) of the team's halfway baseline, used only to link it to industry momentum.

Mirrors notebooks/climate_alpha_analysis.py in the read-only team repo: equal-weighted Green (5 lowest intensity)
and Brown (5 highest) legs from the team FF49 file; rolling 60-month FF3 betas and intercept lagged one month give
the Brown-leg residual epsilon; attention = rolling 60m z-score of log1p(attention); extreme state = z above the
expanding past-only 80th percentile (60-month minimum history); a crossing opens a 3- or 6-month Short-Brown
window; position = -min(1, 5% / (sqrt(12) * trailing 36m std of epsilon)); FF3 overlay hedge with the team's costs
(10 bp asset, 5 bp market, 25 bp SMB/HML per unit of turnover).
"""
from __future__ import annotations
import numpy as np
import pandas as pd

FACT = ["Mkt-RF", "SMB", "HML"]


def rolling_z(s, window=60, min_periods=36):
    return (s - s.rolling(window, min_periods=min_periods).mean()) / s.rolling(window, min_periods=min_periods).std(ddof=1).replace(0, np.nan)


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
    return betas, data["y"], hedged - alpha_used


def expanding_tail(series, q=.80, min_history=60):
    threshold = series.shift(1).expanding(min_periods=min_history).quantile(q)
    return series.gt(threshold) & threshold.notna()


def cross_and_holds(state):
    state = state.astype(bool)
    cross = state & ~state.shift(1, fill_value=False).astype(bool)
    return cross.rolling(3, min_periods=1).max().astype(bool), cross.rolling(6, min_periods=1).max().astype(bool)


def state_position(state, residual, direction, target=.05, vol_window=36):
    sigma = residual.rolling(vol_window, min_periods=vol_window).std(ddof=1)
    magnitude = (target / (np.sqrt(12) * sigma)).clip(upper=1.0)
    position = pd.Series(np.nan, index=residual.index)
    live = position.index >= sigma.first_valid_index()
    position.loc[live] = (direction * magnitude).loc[live].where(state.reindex(position.index).fillna(False).astype(bool), 0)
    return position


def strategy_returns(position, ret, betas, factors):
    idx = position.index.intersection(ret.index).intersection(factors.index).intersection(betas.index)
    h = position.reindex(idx); idx = idx[idx >= h.first_valid_index()]; h = h.reindex(idx).fillna(0)
    beta = betas.reindex(idx); f = factors[FACT].reindex(idx)
    overlay = pd.DataFrame(-h.to_numpy()[:, None] * beta.to_numpy(), index=idx, columns=beta.columns)
    gross = h.shift(1) * ret.reindex(idx) + (overlay.shift(1) * f).sum(axis=1, min_count=len(FACT))
    asset_to = h.diff().abs().fillna(h.abs()); ov_to = overlay.diff().abs().fillna(overlay.abs())
    cost = 10e-4 * asset_to + 5e-4 * ov_to["Mkt-RF"] + 25e-4 * ov_to[["SMB", "HML"]].sum(axis=1)
    return pd.DataFrame({"position": h, "gross": gross, "net": gross - cost.shift(1).fillna(0)})


def build(team: dict, green: list, brown: list, att_lag: int = 0) -> dict:
    """att_lag = 0 is the team's convention (EMV for month t used at the end of month t). att_lag = 1 uses the
    month t-1 value at the end of month t, in case the monthly EMV figure is not available until after month-end."""
    ind, ff3, macro = team["industries"], team["ff3"], team["macro"]
    g, b = ind[green].mean(axis=1), ind[brown].mean(axis=1)
    gb = (g - b).rename("GB")
    brown_x = (b - ff3["RF"]).rename("brown_x")
    aligned = pd.concat([brown_x, ff3[FACT]], axis=1).dropna()
    betas, ret, eps = rolling_factor_model(aligned["brown_x"], aligned[FACT])
    att = rolling_z(np.log1p(macro["attention"].shift(att_lag)))
    h3, h6 = cross_and_holds(expanding_tail(att))
    s3 = strategy_returns(state_position(h3, eps, -1), ret, betas, ff3)
    s6 = strategy_returns(state_position(h6, eps, -1), ret, betas, ff3)
    return {"GB": gb, "brown_eps": eps.rename("brown_eps"), "short_brown_h3": s3["net"].rename("short_brown_h3"),
            "short_brown_h6": s6["net"].rename("short_brown_h6")}
