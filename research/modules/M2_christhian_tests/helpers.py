"""Helpers for M2_christhian_tests (module-local; lib/common.py, lib/plotstyle.py and lib/team_pipeline.py are not modified).

Conventions (same as lib/common.py and lib/team_pipeline.py):
  * monthly data on month-end timestamps, returns in decimals, annualized mean = 12 x monthly mean;
  * inference: Newey-West (Bartlett, 6 lags) standard errors via team_pipeline.newey_west_regression;
    two-sided p-values from the t distribution with n - k degrees of freedom (k = regressors + intercept) in EVERY window;
  * non-traded evaluation controls (WTI and IMF commodity log changes) are demeaned inside each evaluation window,
    so the intercept keeps the meaning "mean return not explained by the traded factors' premia", and the commodity
    controls only absorb covariance (their price of risk is set to zero).
"""
from __future__ import annotations

import sys
import warnings

sys.path.insert(0, "/home/hashim/projects/GA/project/research/lib")
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy import stats  # noqa: E402

from common import TABLES, PERIODS, load_team, load_ff5_mom, load_fred  # noqa: E402
from team_pipeline import (run_pipeline, team_controls, team_legs, newey_west_regression,  # noqa: E402
                           TEAM_GREEN, TEAM_BROWN)

MODULE = "M2_christhian_tests"

# ----------------------------------------------------------------------------- names
STRATS = ["Original | Short Brown hold 3m", "Pure | Short Brown hold 3m", "Original | Short Brown hold 6m",
          "Pure | Short Brown hold 6m", "Continuous | raw attention", "Continuous | pure attention",
          "Benchmark | Always-short Brown"]
BH_GB = "Benchmark | Buy-and-hold Green-Brown"
SHORT = {"Original | Short Brown hold 3m": "Original 3m", "Pure | Short Brown hold 3m": "Pure 3m",
         "Original | Short Brown hold 6m": "Original 6m", "Pure | Short Brown hold 6m": "Pure 6m",
         "Continuous | raw attention": "Continuous raw", "Continuous | pure attention": "Continuous pure",
         "Benchmark | Always-short Brown": "Always-short Brown", BH_GB: "Buy-and-hold GB (unhedged)"}
# signal whose first valid month starts each strategy's live sample (always-short uses the raw-signal start)
SIGNAL_KEY = {"Original | Short Brown hold 3m": "threshold_raw", "Original | Short Brown hold 6m": "threshold_raw",
              "Pure | Short Brown hold 3m": "threshold_pure", "Pure | Short Brown hold 6m": "threshold_pure",
              "Continuous | raw attention": "w_raw", "Continuous | pure attention": "w_pure",
              "Benchmark | Always-short Brown": "threshold_raw", BH_GB: "threshold_raw"}

LONG_PERIODS = ["full_live", "post2010", "validation", "holdout", "pre_covid", "covid", "inflation_rates"]
SHORT_PERIODS = ["last18", "last12"]
END = PERIODS["post2010"][1]

HEDGE_LABEL = {"FF3": "FF3 (team)", "FF3U": "FF3+UMD", "FF5U": "FF5+UMD", "FF5UC": "FF5+UMD+COMEQ",
               "FF5UCx": "FF5+UMD+COMEQ ex-Gold"}
HEDGE_COLS = {"FF3": ["Mkt-RF", "SMB", "HML"], "FF3U": ["Mkt-RF", "SMB", "HML", "UMD"],
              "FF5U": ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "UMD"],
              "FF5UC": ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "UMD", "COMEQ"],
              "FF5UCx": ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "UMD", "COMEQx"]}
NONTRADED = {"cmdty": ["WTI", "IMF"], "cmdty+lead": ["WTI", "IMF", "WTI_lead", "IMF_lead"]}
LEGS_LABEL = {"L5": "5 and 5 (team)", "L8H": "8 and 8, Hardw", "L8M": "8 and 8, MedEq"}
BASE_LABEL = {"team": "team baseline", "corr": "corrected baseline"}
COST_LABEL = {"team": "team costs (10/5/25 bp)", "u0": "zero cost (gross)", "u5": "uniform 5 bp", "u10": "uniform 10 bp",
              "u25": "uniform 25 bp"}


# ----------------------------------------------------------------------------- data
class Data:
    """All inputs, built once. Factor frames carry RF so they can be passed to run_pipeline(factors=...)."""

    def __init__(self):
        T = load_team()
        self.ind, self.ff3, self.mac, self.emissions = T["industries"], T["ff3"], T["macro"], T["emissions"]
        f5 = load_ff5_mom()
        rf = self.ff3["RF"]
        ind = self.ind
        # COMEQ: equal-weighted excess return of the FF49 commodity-producer industries (all four must be present)
        self.comeq = (ind[["Oil", "Coal", "Mines", "Gold"]].mean(axis=1, skipna=False) - rf).rename("COMEQ")
        self.comeq_x = (ind[["Oil", "Coal", "Mines"]].mean(axis=1, skipna=False) - rf).rename("COMEQx")
        # non-traded commodity controls: monthly log change of monthly-average prices
        wti = np.log(load_fred("MCOILWTICO")).diff().rename("WTI")
        imf = np.log(load_fred("PALLFNFINDEXM")).diff().rename("IMF")
        self.nontraded = pd.concat([wti, imf, wti.shift(-1).rename("WTI_lead"), imf.shift(-1).rename("IMF_lead")], axis=1)
        # factor frames
        umd = f5["UMD"]
        self.frames = {
            "FF3": self.ff3[["Mkt-RF", "SMB", "HML", "RF"]].copy(),
            "FF3U": self.ff3[["Mkt-RF", "SMB", "HML", "RF"]].join(umd, how="inner"),
            "FF5U": f5[["Mkt-RF", "SMB", "HML", "RMW", "CMA", "UMD", "RF"]].loc[:END].copy(),
        }
        self.frames["FF5UC"] = self.frames["FF5U"].join(self.comeq, how="inner")
        self.frames["FF5UCx"] = self.frames["FF5U"].join(self.comeq_x, how="inner")
        for k in self.frames:
            self.frames[k] = self.frames[k].dropna()
        # legs
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            g8, b8 = team_legs(8)
        self.tie_warning = "; ".join(str(x.message) for x in w)
        g8m = [x if x != "Hardw" else "MedEq" for x in g8]
        self.legs = {"L5": (list(TEAM_GREEN), list(TEAM_BROWN)), "L8H": (g8, b8), "L8M": (g8m, b8)}
        # corrected-baseline macro: CPI gap interpolated; attention and purification controls lagged one month
        m = self.mac.copy()
        m["cpi"] = m["cpi"].interpolate(limit_area="inside")
        self.mac_corr = m

    def baseline_kwargs(self, baseline: str) -> dict:
        if baseline == "team":
            return {}
        m = self.mac_corr
        return dict(macro=m, attention=m["attention"].shift(1), controls=team_controls(m).shift(1))

    def eval_X(self, hedge: str) -> pd.DataFrame:
        return self.frames[hedge][HEDGE_COLS[hedge]]


# ----------------------------------------------------------------------------- pipeline runs
CHEAP = dict(bootstrap_reps=0, extras=False, paired=False, macro_states=False)
FULL = dict(bootstrap_reps=5000, extras=True, paired=True, macro_states=False)


def run_config(D: Data, legs: str, baseline: str, hedge: str, costs: str, full: bool = False) -> dict:
    g, b = D.legs[legs]
    kw = dict(industries=D.ind, green=g, brown=b, factors=D.frames[hedge], factor_cols=tuple(HEDGE_COLS[hedge]))
    kw.update(D.baseline_kwargs(baseline))
    if costs != "team":
        kw["cost_bps_uniform"] = int(costs[1:])
    kw.update(FULL if full else CHEAP)
    return run_pipeline(**kw)


def live_start(res: dict, strat: str) -> pd.Timestamp:
    """First return month of the strategy's live sample: first month its signal is defined, plus one month."""
    first = res["signals"][SIGNAL_KEY[strat]].first_valid_index()
    return first + pd.offsets.MonthEnd(1)


def window(period: str, live: pd.Timestamp | None = None):
    if period == "full_live":
        return live, pd.Timestamp(END)
    a, b = PERIODS[period]
    return pd.Timestamp(a), pd.Timestamp(b)


# ----------------------------------------------------------------------------- regressions
def _nw_np(yv: np.ndarray, Xm: np.ndarray, lags: int):
    """Numpy copy of team_pipeline.newey_west_regression (pinv normal equations, Bartlett kernel, same loop)."""
    n = len(yv)
    inv = np.linalg.pinv(Xm.T @ Xm)
    coef = inv @ Xm.T @ yv
    resid = yv - Xm @ coef
    xu = Xm * resid[:, None]
    meat = xu.T @ xu
    for lag in range(1, min(lags, n - 1) + 1):
        gamma = xu[lag:].T @ xu[:-lag]
        meat += (1.0 - lag / (lags + 1.0)) * (gamma + gamma.T)
    se = np.sqrt(np.clip(np.diag(inv @ meat @ inv), 0, None))
    with np.errstate(divide="ignore", invalid="ignore"):
        t = coef / se
    return coef, t, resid


def nw_fit(y: pd.Series, X: pd.DataFrame | None, nontraded: pd.DataFrame | None = None, lags: int = 6) -> dict:
    """NW(lags) OLS of y on [1, X, demeaned nontraded]. Rows with any missing value are dropped first; the
    non-traded columns are then demeaned in-sample. p-values from t(n - k). Returns a flat dict."""
    idx = y.index
    blocks, cols = [y.to_numpy(float)[:, None]], []
    if X is not None and X.shape[1]:
        blocks.append(X.reindex(idx).to_numpy(float)); cols += list(X.columns)
    n_tr = len(cols)
    if nontraded is not None and nontraded.shape[1]:
        blocks.append(nontraded.reindex(idx).to_numpy(float)); cols += list(nontraded.columns)
    M = np.hstack(blocks)
    ok = ~np.isnan(M).any(axis=1)
    M, used = M[ok], idx[ok]
    if len(cols) > n_tr:
        M[:, 1 + n_tr:] -= M[:, 1 + n_tr:].mean(axis=0)
    n, k = len(M), len(cols) + 1
    out = {"n": n, "k": k, "start": used.min() if n else pd.NaT, "end": used.max() if n else pd.NaT}
    if n - k < 2:
        return out
    yv = M[:, 0]
    Xm = np.column_stack([np.ones(n), M[:, 1:]])
    coef, t, resid = _nw_np(yv, Xm, lags)
    df_resid = n - k
    p = np.where(np.isfinite(t), 2 * stats.t.sf(np.abs(t), df_resid), np.nan)
    sst = ((yv - yv.mean()) ** 2).sum()
    out.update({"alpha_ann": 12 * coef[0], "t_alpha": t[0], "p_alpha": p[0],
                "r2": 1 - (resid ** 2).sum() / sst if sst > 0 else np.nan})
    for i, c in enumerate(cols, start=1):
        out[f"b_{c}"] = coef[i]
        out[f"t_{c}"] = t[i]
        out[f"p_{c}"] = p[i]
    return out


def perf_block(df: pd.DataFrame, a, b, lags: int = 6) -> dict:
    """Net-return performance of a pipeline strategy frame in [a, b]."""
    s = df["net_return"].loc[a:b].dropna()
    n = len(s)
    if n < 3:
        return {"n": n}
    vol = np.sqrt(12) * s.std(ddof=1)
    wealth = (1 + s).cumprod()
    m = nw_fit(s, None, lags=lags)
    held = df["position"].shift(1).reindex(s.index).fillna(0) if "position" in df else pd.Series(0.0, index=s.index)
    out = {"n": n, "ann_net": 12 * s.mean(), "ann_vol": vol, "sharpe": 12 * s.mean() / vol if vol > 0 else np.nan,
           "t_mean": m.get("t_alpha", np.nan), "p_mean": m.get("p_alpha", np.nan),
           "max_dd": (wealth / wealth.cummax() - 1).min(), "months_held": int((held != 0).sum()),
           "mean_abs_pos": held.abs().mean()}
    if "turnover" in df:
        sl = df.loc[a:b]
        out["ann_turnover"] = 12 * sl["turnover"].mean()
        if "asset_turnover" in sl:
            out["ann_asset_turnover"] = 12 * sl["asset_turnover"].mean()
            out["ann_overlay_turnover"] = 12 * sl["overlay_turnover"].mean()
        if "gross_return" in sl:
            out["ann_gross"] = 12 * sl["gross_return"].loc[s.index].mean()
            out["ann_cost_drag"] = out["ann_gross"] - out["ann_net"]
    return out


# ----------------------------------------------------------------------------- ledger
class Ledger:
    """One row per hypothesis test (including nulls and failures)."""
    COLS = ["test_id", "module", "question", "statistic_name", "statistic", "p_value_two_sided", "n_obs",
            "primary_or_exploratory", "note"]

    def __init__(self):
        self.rows = []

    def add(self, test_id, question, statistic_name, statistic, p, n, kind, note=""):
        assert kind in ("primary", "robustness", "exploratory"), kind
        self.rows.append(dict(test_id=test_id, module=MODULE, question=question, statistic_name=statistic_name,
                              statistic=float(statistic) if statistic is not None and not pd.isna(statistic) else np.nan,
                              p_value_two_sided=float(p) if p is not None and not pd.isna(p) else np.nan,
                              n_obs=int(n) if n is not None and not pd.isna(n) else np.nan,
                              primary_or_exploratory=kind, note=note))

    def frame(self) -> pd.DataFrame:
        df = pd.DataFrame(self.rows, columns=self.COLS)
        dup = df["test_id"][df["test_id"].duplicated()].tolist()
        assert not dup, dup[:5]
        return df


# ----------------------------------------------------------------------------- output
def save_csv(df: pd.DataFrame, name: str, index: bool = False):
    path = TABLES / f"{MODULE}_{name}.csv"
    df.to_csv(path, index=index, float_format="%.8g")
    return path


def save_tex(df: pd.DataFrame, name: str, caption: str, label: str, fmt: dict | None = None, default: str = "{:.2f}",
             index: bool = False, column_format: str | None = None):
    """Booktabs table. fmt maps column -> python format string (e.g. '{:.2f}', '{:.0f}'); other floats use `default`.
    Strings are escaped; NaN prints as '--'."""
    fmt = fmt or {}
    d = df.reset_index() if index else df.copy()
    for c in d.columns:
        f = fmt.get(c)
        if f is None and pd.api.types.is_float_dtype(d[c]):
            f = default
        if f is not None:
            d[c] = d[c].map(lambda v, f=f: "--" if v is None or (isinstance(v, float) and np.isnan(v)) else
                            (f.format(v) if isinstance(v, (int, float, np.floating, np.integer)) else str(v)))
            d[c] = d[c].str.replace(r"^-(0\.0*)$", r"\1", regex=True)  # no negative zero
    if column_format is None:
        column_format = "".join("l" if (i == 0 or d[c].map(lambda v: not _numlike(v)).any()) else "r"
                                for i, c in enumerate(d.columns))
    tex = d.to_latex(index=False, escape=True, caption=caption, label=label, column_format=column_format, na_rep="--")
    (TABLES / f"{MODULE}_{name}.tex").write_text(tex, encoding="utf-8")


def _numlike(v) -> bool:
    try:
        float(str(v).replace("--", "nan"))
        return True
    except ValueError:
        return False


def fmt_p(p: float) -> str:
    if p is None or pd.isna(p):
        return "--"
    return f"{p:.3f}" if p >= 0.001 else f"{p:.1e}"
