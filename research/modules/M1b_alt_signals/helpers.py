"""Helpers for M1b_alt_signals: build alternative attention measures, run the team machinery on each,
and compute window statistics, ICs, crossings and paired tests.

Conventions (see FINDINGS.md):
  * measure value for month m is the month-m observation (FRED monthly value, monthly mean of daily VIX, etc.);
  * timing 'same_month' = team timing: value for month t is used at the close of month t, earns t+1;
  * timing 'realtime'   = corrected baseline: value for month t-1 (and controls lagged one month) used at the
    close of month t, earns t+1 (the value for month t-1 is published during month t);
  * both timings use the macro file with the Oct-2025 CPI gap linearly interpolated (limit_area='inside');
  * FF3 alpha: team NW(6) regression on the team FF3 file; p-values from t(n-k) when n < 60, else normal.
"""
from __future__ import annotations

import sys
import warnings

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, "/home/hashim/projects/GA/project/research/lib")
from common import load_team, load_fred, load_cpu, load_mccc, load_emv_env  # noqa: E402
from team_pipeline import (run_pipeline, team_controls, period_stats, information_coefficient,  # noqa: E402
                           circular_block_bootstrap, newey_west_regression, turnover_stats)

MODULE = "M1b_alt_signals"
FF3 = ("Mkt-RF", "SMB", "HML")
TRANSITION_TOPICS = ["Climate Legislation/Regulations", "Carbon Tax", "Carbon Credits Market",
                     "Renewable Energy", "Agreements/Actions"]
SAMPLE_END = pd.Timestamp("2026-07-31")

# role: team (reference), primary (climate concern), placebo (volatility), robustness (variant)
MEASURES = {
    "EMV_env": {"label": "EMV env. regulation (team)", "role": "team", "transform": "log1p"},
    "MCCC": {"label": "MCCC aggregate", "role": "primary", "transform": "log1p"},
    "CPU": {"label": "Climate Policy Uncertainty", "role": "primary", "transform": "log1p"},
    "VIX": {"label": "VIX (monthly mean)", "role": "placebo", "transform": "log1p"},
    "EMV_overall": {"label": "EMV overall", "role": "placebo", "transform": "log1p"},
    "EMV_env_share": {"label": "EMV env. / EMV overall", "role": "robustness", "transform": "log1p"},
    "MCCC_transition": {"label": "MCCC transition topics", "role": "robustness", "transform": "log1p"},
}

STRATS = {
    "O3": "Original | Short Brown hold 3m",
    "P3": "Pure | Short Brown hold 3m",
    "O6": "Original | Short Brown hold 6m",
    "P6": "Pure | Short Brown hold 6m",
    "CR": "Continuous | raw attention",
    "CP": "Continuous | pure attention",
}
STRAT_LABEL = {"O3": "Original 3m", "P3": "Pure 3m", "O6": "Original 6m", "P6": "Pure 6m",
               "CR": "Continuous raw", "CP": "Continuous pure"}
# signal whose IC goes with each strategy, and the signal key that defines when the strategy is live
STRAT_SIGNAL = {"O3": "raw", "O6": "raw", "P3": "pure", "P6": "pure", "CR": "w_raw", "CP": "w_pure"}
STRAT_LIVE_KEY = {"O3": "threshold_raw", "O6": "threshold_raw", "P3": "threshold_pure", "P6": "threshold_pure",
                  "CR": "w_raw", "CP": "w_pure"}
SIGNAL_LABEL = {"raw": "Raw attention z", "pure": "Purified attention", "w_raw": "Continuous weight (raw)",
                "w_pure": "Continuous weight (pure)"}

CHEAP = dict(bootstrap_reps=0, extras=False, paired=False, macro_states=False)
FULL = dict(bootstrap_reps=5000, extras=True, paired=True, macro_states=False)


# ----------------------------------------------------------------------------- data
def macro_fixed():
    """Team macro file with the Oct-2025 CPI gap linearly interpolated (corrected baseline)."""
    mac = load_team()["macro"].copy()
    mac["cpi"] = mac["cpi"].interpolate(limit_area="inside")
    return mac


def build_measures() -> pd.DataFrame:
    """Monthly (month-end) measures, each on its own native range, truncated at 2026-08 (macro file end)."""
    emv = load_emv_env()
    emv_all = load_fred("EMVOVERALLEMV").rename("EMV_overall")
    share = (emv / emv_all).rename("EMV_env_share")
    vix = load_fred("VIXCLS", "mean").rename("VIX")
    mccc = load_mccc("Aggregate").rename("MCCC")
    trans = pd.concat([load_mccc(c) for c in TRANSITION_TOPICS], axis=1)
    trans = trans.mean(axis=1, skipna=False).rename("MCCC_transition")
    cpu = load_cpu().rename("CPU")
    df = pd.concat([emv.rename("EMV_env"), mccc, cpu, vix, emv_all, share, trans], axis=1).sort_index()
    df = df.loc[:"2026-08-31"]
    return df[list(MEASURES)]


def native_range(s: pd.Series):
    s = s.dropna()
    return s.index.min(), s.index.max()


def eval_end(s: pd.Series) -> pd.Timestamp:
    """Last return month driven by the measure under BOTH timings: last data month + 1, capped at sample end."""
    last = native_range(s)[1]
    return min(last + pd.offsets.MonthEnd(1), SAMPLE_END)


def timed_inputs(series: pd.Series, mac: pd.DataFrame, timing: str):
    ctrl = team_controls(mac)
    s = series.dropna()
    if timing == "same_month":
        return s, ctrl
    if timing == "realtime":
        return s.shift(1, freq="ME"), ctrl.shift(1)
    raise ValueError(timing)


def run_measure(series, mac, timing, transform="log1p", mode="cheap", full_end="2026-07-31"):
    att, ctrl = timed_inputs(series, mac, timing)
    kw = CHEAP if mode == "cheap" else FULL
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return run_pipeline(macro=mac, attention=att, controls=ctrl, attention_transform=transform,
                            full_end=pd.Timestamp(full_end).strftime("%Y-%m-%d"), **kw)


# ----------------------------------------------------------------------------- statistics
def p_from_t(t, n, k):
    """Two-sided p: t(n-k) when n < 60, else standard normal."""
    if t is None or not np.isfinite(t) or n is None or n <= k:
        return np.nan
    return float(2 * stats.t.sf(abs(t), n - k)) if n < 60 else float(2 * stats.norm.sf(abs(t)))


def window_stats(strat_df: pd.DataFrame, start, end, factors, min_n=12):
    """Team period statistics on [start, end] plus turnover, cost drag, months held and a small-sample p-value."""
    start, end = pd.Timestamp(start), pd.Timestamp(end)
    if end < start:
        return None
    net = strat_df["net_return"].loc[start:end].dropna()
    if len(net) < min_n:
        return {"n_months": len(net)}
    r = period_stats(strat_df["net_return"], start, end, factors=factors, factor_cols=FF3, lags=6)
    sl = strat_df.loc[start:end]
    held = strat_df["position"].shift(1).loc[start:end].fillna(0)
    out = {k: r[k] for k in ("n_months", "ann_net", "ann_vol", "sharpe_net", "max_drawdown", "alpha_ann", "alpha_t_hac6",
                             "MKT_beta", "SMB_beta", "HML_beta")}
    out["p_alpha"] = p_from_t(r["alpha_t_hac6"], r["n_months"], 4)
    out["months_held"] = int((held != 0).sum())
    out["mean_abs_position"] = float(held.abs().mean())
    out["annual_turnover"] = turnover_stats(strat_df, start, end)
    out["ann_cost_drag"] = 12 * float((sl["gross_return"] - sl["net_return"]).mean())
    return out


def ic_return_aligned(signal, eps, start, end):
    """IC with the window defined on the forward-return month: pairs (signal_t, eps_{t+1}) with t+1 in [start, end]."""
    s0 = pd.Timestamp(start) - pd.offsets.MonthEnd(1)
    e0 = pd.Timestamp(end) - pd.offsets.MonthEnd(1)
    ic, t, n = information_coefficient(signal, eps, s0, e0, lags=6)
    return ic, t, n, p_from_t(t, n, 2)


def ic_team_convention(signal, eps, start, end):
    """Team convention: window on the signal date t; the forward return may fall one month after `end`."""
    ic, t, n = information_coefficient(signal, eps, start, end, lags=6)
    return ic, t, n


def paired_alpha(ret_a: pd.Series, ret_b: pd.Series, start, end, factors):
    """FF3 alpha of (a - b) on [start, end], NW(6)."""
    d = (ret_a - ret_b).loc[start:end].dropna()
    fit = newey_west_regression(d, factors[list(FF3)].reindex(d.index), lags=6)
    n = len(d)
    t = fit.loc["const", "t_hac6"]
    return {"n": n, "diff_ann_net": 12 * d.mean(), "diff_alpha_ann": 12 * fit.loc["const", "coef"], "diff_t": t,
            "diff_p": p_from_t(t, n, 4)}


def live_start(sig: dict, key: str) -> pd.Timestamp:
    """First return month for which the strategy's signal is defined (signal date + 1 month)."""
    s = sig[key]
    fv = s.first_valid_index()
    return fv + pd.offsets.MonthEnd(1) if fv is not None else pd.NaT


def crossings(sig: dict, key="cross_raw", start="2010-01-31", end=None) -> pd.DatetimeIndex:
    c = sig[key].loc[start:end] if end is not None else sig[key].loc[start:]
    return c[c.astype(bool)].index


def within(dates, ref, months=1) -> np.ndarray:
    """For each date in `dates`, is there a date in `ref` within +/- `months` months?"""
    to_m = lambda ix: np.asarray(pd.DatetimeIndex(ix).year * 12 + pd.DatetimeIndex(ix).month, dtype=int)  # noqa: E731
    r = to_m(ref)
    if len(r) == 0:
        return np.zeros(len(dates), dtype=bool)
    return np.array([bool(np.any(np.abs(r - d) <= months)) for d in to_m(dates)], dtype=bool)
