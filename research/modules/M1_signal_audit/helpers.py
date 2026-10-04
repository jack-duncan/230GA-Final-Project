"""Helpers for M1_signal_audit (module-local; the shared lib/common.py is not modified).

Conventions follow lib/common.py: month-end index, returns in decimals, Newey-West HAC via common.nw_ols.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from scipy import stats, optimize
from common import nw_ols, TABLES

MODULE = "M1_signal_audit"


# ----------------------------------------------------------------------------- tests ledger
class Ledger:
    """Collects one row per hypothesis test, including nulls and failures.

    `key` identifies the hypothesis (e.g. the unordered pair of series and the sample dates for a correlation).
    A second test of the same hypothesis is not recorded again: add() returns the test_id of the first row, notes the
    alias on it, and upgrades its label if the later use is more central (primary > robustness > exploratory)."""
    COLS = ["test_id", "module", "question", "statistic_name", "statistic", "p_value_two_sided",
            "n_obs", "primary_or_exploratory", "note"]
    RANK = {"primary": 0, "robustness": 1, "exploratory": 2}

    def __init__(self):
        self.rows = []
        self.keys = {}          # hypothesis key -> row index
        self.aliases = {}       # duplicate test_id -> recorded test_id

    def add(self, test_id, question, statistic_name, statistic, p, n, kind, note="", key=None):
        assert kind in self.RANK, kind
        if key is not None and key in self.keys:
            row = self.rows[self.keys[key]]
            if not (pd.isna(p) and pd.isna(row["p_value_two_sided"])):
                assert np.isclose(float(p), row["p_value_two_sided"], rtol=1e-9, atol=1e-12), (test_id, row["test_id"])
            if self.RANK[kind] < self.RANK[row["primary_or_exploratory"]]:
                row["primary_or_exploratory"] = kind
            row["note"] = f"{row['note']}; also reported as {test_id}"
            self.aliases[test_id] = row["test_id"]
            return row["test_id"]
        self.rows.append(dict(test_id=test_id, module=MODULE, question=question, statistic_name=statistic_name,
                              statistic=float(statistic) if statistic is not None else np.nan,
                              p_value_two_sided=float(p) if p is not None else np.nan,
                              n_obs=int(n) if n is not None and not pd.isna(n) else np.nan,
                              primary_or_exploratory=kind, note=note))
        if key is not None:
            self.keys[key] = len(self.rows) - 1
        return test_id

    def frame(self):
        df = pd.DataFrame(self.rows, columns=self.COLS)
        assert df["test_id"].is_unique, df["test_id"][df["test_id"].duplicated()].tolist()
        return df


def corr_key(a_name: str, b_name: str, start, end):
    """Direction-free hypothesis key for a correlation test: unordered pair of series names plus the sample dates."""
    return ("corr", frozenset((a_name, b_name)), ym(start), ym(end))


# ----------------------------------------------------------------------------- output helpers
def save_table(df: pd.DataFrame, name: str, tex: dict | None = None, index: bool = False):
    """Write outputs/tables/M1_signal_audit_<name>.csv and, if tex is given, a booktabs .tex.
    tex = {"caption": str, "label": str, "fmt": {col: format spec}, "columns": [..] or None, "rename": {..},
           "rows": optional callable df -> boolean mask selecting the rows shown in the .tex (the CSV keeps all rows)}"""
    path = TABLES / f"{MODULE}_{name}.csv"
    df.to_csv(path, index=index)
    if tex is not None:
        t = df.copy() if index is False else df.reset_index()
        if tex.get("rows") is not None:
            t = t[tex["rows"](t)]
        if tex.get("columns"):
            t = t[tex["columns"]]
        for c, f in tex.get("fmt", {}).items():
            if c in t.columns:
                t[c] = t[c].map(lambda v, f=f: "" if pd.isna(v) else (f.format(v) if isinstance(v, (int, float, np.floating, np.integer)) else str(v)))
        for c in t.columns:
            if pd.api.types.is_datetime64_any_dtype(t[c]):
                t[c] = t[c].dt.strftime("%Y-%m")
        for c in t.columns:
            nn = t[c].dropna()
            if len(nn) and (pd.api.types.is_bool_dtype(t[c]) or nn.map(lambda v: isinstance(v, (bool, np.bool_))).all()):
                t[c] = t[c].map(lambda v: "" if pd.isna(v) else ("yes" if bool(v) else "no"))
        src = df if index is False else df.reset_index()
        numeric = [c in src.columns and pd.api.types.is_numeric_dtype(src[c]) and not pd.api.types.is_bool_dtype(src[c]) for c in t.columns]
        t = t.rename(columns=tex.get("rename", {}))
        latex = t.to_latex(index=False, escape=True, caption=tex["caption"], label=tex["label"], na_rep="",
                           column_format="".join("r" if n else "l" for n in numeric))
        (TABLES / f"{MODULE}_{name}.tex").write_text(latex, encoding="utf-8")
    return path


def ym(ts) -> str:
    return "" if ts is None or pd.isna(ts) else pd.Timestamp(ts).strftime("%Y-%m")


# ----------------------------------------------------------------------------- signal construction
def ar1_shock_expanding(x: pd.Series, min_obs: int = 36) -> pd.Series:
    """Real-time AR(1) innovation. For month t: fit x_s = a + b x_{s-1} by OLS on all pairs with s <= t-1
    (at least min_obs pairs), then shock_t = x_t - (a + b x_{t-1}). Parameters never use month t."""
    x = x.dropna().astype(float)
    assert (x.index.to_series().diff().dropna().dt.days <= 31).all(), f"{x.name}: non-contiguous monthly index"
    v = x.to_numpy(); out = np.full(len(v), np.nan)
    for i in range(1, len(v)):
        y_est, x_est = v[1:i], v[:i - 1]          # pairs (x_{s-1}, x_s) for s = 1..i-1
        if len(y_est) < min_obs:
            continue
        b, a = np.polyfit(x_est, y_est, 1)
        out[i] = v[i] - (a + b * v[i - 1])
    return pd.Series(out, index=x.index, name=f"{x.name}_shock")


def ar1_shock_full(x: pd.Series) -> pd.Series:
    """Ex-post AR(1) residual using the full sample (look-ahead; robustness for contemporaneous tests only)."""
    x = x.dropna().astype(float)
    b, a = np.polyfit(x.shift(1).dropna().to_numpy(), x.iloc[1:].to_numpy(), 1)
    return (x - (a + b * x.shift(1))).rename(f"{x.name}_shock_full")


def rolling_factor_resid(y: pd.Series, X: pd.DataFrame, window: int = 60):
    """Replicates the team's rolling_factor_model: trailing-window OLS of y on [1, X]; intercept and betas shifted
    one month; residual_t = y_t - alpha_{t-1} - beta_{t-1}' X_t."""
    data = pd.concat([y.rename("y"), X], axis=1).dropna()
    cols = list(X.columns)
    Y = data["y"].to_numpy(); Xm = np.column_stack([np.ones(len(data)), data[cols].to_numpy()])
    coefs = np.full((len(data), len(cols) + 1), np.nan)
    for end in range(window - 1, len(data)):
        sl = slice(end - window + 1, end + 1)
        coefs[end], *_ = np.linalg.lstsq(Xm[sl], Y[sl], rcond=None)
    coefs = pd.DataFrame(coefs, index=data.index, columns=["alpha"] + cols).shift(1)
    hedged = data["y"] - (coefs[cols] * data[cols]).sum(axis=1, min_count=len(cols))
    return (hedged - coefs["alpha"]).rename(f"{y.name}_resid")


def expanding_tail(series: pd.Series, q: float = 0.80, min_history: int = 60):
    """Team rule: state_t = z_t > (80th percentile of z_s for s <= t-1), threshold needs min_history past values."""
    threshold = series.shift(1).expanding(min_periods=min_history).quantile(q)
    return (series.gt(threshold) & threshold.notna()), threshold


def cross_and_holds(state: pd.Series):
    """Team rule: crossing = state switches on; hold windows of 3 and 6 months starting at the crossing month."""
    state = state.astype(bool)
    cross = state & ~state.shift(1, fill_value=False).astype(bool)
    return cross, cross.rolling(3, min_periods=1).max().astype(bool), cross.rolling(6, min_periods=1).max().astype(bool)


# ----------------------------------------------------------------------------- statistics
def zstd(s: pd.Series) -> pd.Series:
    return (s - s.mean()) / s.std(ddof=1)


def hac_corr(x: pd.Series, y: pd.Series, lags: int = 6):
    """Direction-free HAC test of a Pearson correlation (delta method). With standardized a, b and r = corr(a, b), the
    influence function of r is psi_t = a_t b_t - (r / 2)(a_t^2 + b_t^2); se(r) = sqrt(NW long-run variance of psi / n).
    Symmetric in x and y. Returns (r, t, p) with normal p-values."""
    d = pd.concat([x.rename("x"), y.rename("y")], axis=1).dropna()
    a, b = zstd(d["x"]), zstd(d["y"])
    r = float(d["x"].corr(d["y"]))
    psi = a * b - 0.5 * r * (a ** 2 + b ** 2)
    se = float(nw_ols(psi.rename("psi"), lags=lags).bse.iloc[0])
    t = r / se
    return r, t, float(2 * stats.norm.sf(abs(t)))


def corr_test(x: pd.Series, y: pd.Series, lags: int = 6, start=None, end=None) -> dict:
    """Pearson correlation with two NW tests and Spearman rho.
    t_slope/p_slope: NW t of the slope of standardized y on standardized x (depends on which series is y).
    t_hac/p_hac: direction-free delta-method HAC test (hac_corr); used for every ledger row except the two pre-specified
    Q5 primary tests, which keep their pre-specified slope test."""
    d = pd.concat([x.rename("x"), y.rename("y")], axis=1).dropna()
    if start is not None:
        d = d.loc[start:]
    if end is not None:
        d = d.loc[:end]
    if len(d) < 10 or d["x"].std() == 0 or d["y"].std() == 0:
        return dict(n=len(d), pearson=np.nan, t_slope=np.nan, p_slope=np.nan, t_hac=np.nan, p_hac=np.nan,
                    spearman=np.nan, start=None, end=None)
    res = nw_ols(zstd(d["y"]), zstd(d["x"]).to_frame("x"), lags=lags)
    _, t_h, p_h = hac_corr(d["x"], d["y"], lags=lags)
    return dict(n=int(res.nobs), pearson=d["x"].corr(d["y"]), t_slope=res.tvalues["x"], p_slope=res.pvalues["x"],
                t_hac=t_h, p_hac=p_h, spearman=d["x"].corr(d["y"], method="spearman"), start=d.index[0], end=d.index[-1])


def partial_corr_test(x: pd.Series, y: pd.Series, control: pd.Series, lags: int = 6) -> dict:
    """Partial correlation of x and y given one control (OLS residuals on [1, control]), with the direction-free HAC test."""
    d = pd.concat([x.rename("x"), y.rename("y"), control.rename("c")], axis=1).dropna()
    C = np.column_stack([np.ones(len(d)), d["c"].to_numpy()])
    rx = d["x"] - C @ np.linalg.lstsq(C, d["x"].to_numpy(), rcond=None)[0]
    ry = d["y"] - C @ np.linalg.lstsq(C, d["y"].to_numpy(), rcond=None)[0]
    r, t, p = hac_corr(rx, ry, lags=lags)
    return dict(n=len(d), partial_r=r, t_hac=t, p_hac=p, start=d.index[0], end=d.index[-1])


def min_level_to_cross(past_log1p: np.ndarray, threshold: float) -> float:
    """Smallest month-t EMV level v such that z_t > threshold, where z_t is the rolling z-score of log1p over the window
    [past_log1p, log1p(v)]. z_t is strictly increasing in log1p(v) above the past mean, so a root-finder is exact."""
    past = np.asarray(past_log1p, dtype=float)
    if not np.isfinite(threshold) or threshold <= 0:
        return np.nan

    def f(v):
        w = np.r_[past, v]
        return (v - w.mean()) / w.std(ddof=1) - threshold
    lo, hi = past.mean(), past.mean() + 50 * past.std(ddof=1) + 10
    return float(np.expm1(optimize.brentq(f, lo, hi, xtol=1e-12)))


def circular_shift_p(flag: pd.Series, event: pd.Series, min_shift: int = 12) -> tuple:
    """Dependence-robust permutation test of 'flag share differs between event months and other months'.
    The event indicator is rotated by k = min_shift..n-min_shift months (keeps the autocorrelation of both series).
    Returns (difference in flag share, two-sided p, number of shifts)."""
    f = flag.astype(bool).to_numpy(); e = event.astype(bool).to_numpy()
    stat = f[e].mean() - f[~e].mean()
    sims = np.array([f[np.roll(e, k)].mean() - f[~np.roll(e, k)].mean() for k in range(min_shift, len(e) - min_shift + 1)])
    return float(stat), float((np.abs(sims) >= abs(stat) - 1e-12).mean()), len(sims)


def ic_test(signal: pd.Series, outcome: pd.Series, start=None, end=None, controls: pd.DataFrame | None = None,
            lags: int = 6, min_n: int = 10) -> dict:
    """Team IC convention: pair signal_t with outcome_{t+1}; window selected on the signal date; standardize both
    within the window; slope of z(outcome_{t+1}) on z(signal_t) with NW t. Optional controls are dated t+1
    (contemporaneous with the outcome) and enter unstandardized, making the slope a partial coefficient."""
    outcome = outcome.asfreq("ME")
    parts = [signal.rename("x"), outcome.shift(-1).rename("y")]
    if controls is not None:
        parts.append(controls.asfreq("ME").shift(-1))
    d = pd.concat(parts, axis=1).dropna()
    if start is not None:
        d = d.loc[start:]
    if end is not None:
        d = d.loc[:end]
    if len(d) < min_n or d["x"].std() == 0:
        return dict(ic=np.nan, t_nw=np.nan, p_nw=np.nan, n=len(d), start=None, end=None)
    X = zstd(d["x"]).to_frame("signal_z")
    if controls is not None:
        X = X.join(d[list(controls.columns)])
    res = nw_ols(zstd(d["y"]), X, lags=lags)
    return dict(ic=res.params["signal_z"], t_nw=res.tvalues["signal_z"], p_nw=res.pvalues["signal_z"],
                n=int(res.nobs), start=d.index[0], end=d.index[-1])


def reg_row(y: pd.Series, X: pd.DataFrame, lags: int = 6, start=None, end=None) -> dict:
    """OLS with NW t-stats; returns R-squared, HAC Wald F p-value for all slopes, coefficients and t-stats."""
    d = pd.concat([y.rename("__y"), X], axis=1).dropna()
    if start is not None:
        d = d.loc[start:]
    if end is not None:
        d = d.loc[:end]
    if len(d) < 12:
        return dict(n=len(d))
    res = nw_ols(d["__y"], d.drop(columns="__y"), lags=lags)
    row = dict(n=int(res.nobs), start=d.index[0], end=d.index[-1], r2=res.rsquared,
               wald_F=float(np.squeeze(res.fvalue)), wald_p=float(np.squeeze(res.f_pvalue)))
    for c in X.columns:
        row[f"b_{c}"] = res.params[c]; row[f"t_{c}"] = res.tvalues[c]; row[f"p_{c}"] = res.pvalues[c]
    return row


def fisher_2x2(a_yes, a_no, b_yes, b_no):
    """Two-sided Fisher exact test on [[a_yes, a_no], [b_yes, b_no]]; returns odds ratio and p."""
    res = stats.fisher_exact([[a_yes, a_no], [b_yes, b_no]], alternative="two-sided")
    return float(res.statistic), float(res.pvalue)
