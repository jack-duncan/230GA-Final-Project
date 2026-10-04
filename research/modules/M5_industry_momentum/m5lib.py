"""M5 industry momentum: data, signal, portfolio construction, backtest, statistics, bootstrap, table writers.

Timing convention used everywhere in this module: a weight vector indexed at month-end t (the formation date)
uses only information available at the end of month t and earns the month t+1 return. Backtest outputs are
re-indexed to the holding month t+1 so they line up with factor returns.
"""
from __future__ import annotations
import sys, pathlib
import numpy as np
import pandas as pd
import statsmodels.api as sm

HERE = pathlib.Path(__file__).resolve().parent
RESEARCH = HERE.parents[1]
if str(RESEARCH / "lib") not in sys.path:
    sys.path.insert(0, str(RESEARCH / "lib"))
import common as C  # noqa: E402
from common import TABLES, PERIODS, nw_ols  # noqa: E402

MOD = "M5_industry_momentum"
RET_START, RET_END = pd.Timestamp("1970-01-31"), pd.Timestamp("2026-07-31")
FORM_START, FORM_END = pd.Timestamp("1969-12-31"), pd.Timestamp("2026-06-30")
BASE_COST = 0.0010           # 10 bp per unit of traded notional (one-way)
PERIOD_ORDER = ["full_1970", "post2010", "validation", "holdout", "pre_covid", "covid", "inflation_rates", "last18", "last12"]
DECADES = {"1970s": ("1970-01-31", "1979-12-31"), "1980s": ("1980-01-31", "1989-12-31"),
           "1990s": ("1990-01-31", "1999-12-31"), "2000s": ("2000-01-31", "2009-12-31"),
           "2010s": ("2010-01-31", "2019-12-31"), "2020s_to_2026_07": ("2020-01-31", "2026-07-31")}
F3 = ["Mkt-RF", "SMB", "HML"]
F5 = ["Mkt-RF", "SMB", "HML", "RMW", "CMA"]
MODELS = {"CAPM": ["Mkt-RF"], "FF3": F3, "FF5": F5, "FF5+UMD": F5 + ["UMD"]}


# ----------------------------------------------------------------------------- data
def load_inputs() -> dict:
    team = C.load_team()
    R = team["industries"].loc[:RET_END].copy()
    ff5 = C.load_ff5_mom().loc[:RET_END]
    ff3 = C.load_kf_ff3().loc[:RET_END]
    nf, sz = C.load_kf_industries("nfirms"), C.load_kf_industries("size")
    cap = (nf * sz).reindex(columns=R.columns)          # industry market cap proxy, known at end of month
    R_kf = C.load_kf_industries("vw").reindex(columns=R.columns).loc[:RET_END]
    return {"R": R, "R_kf": R_kf, "ff5": ff5, "ff3": ff3, "cap": cap, "emis": team["emissions"], "team": team}


def factor_frame(model: str, ff5: pd.DataFrame, ff3: pd.DataFrame) -> pd.DataFrame:
    """CAPM and FF3 from the Ken French 3-factor file; FF5 and FF5+UMD from the 5-factor file plus UMD."""
    cols = MODELS[model]
    return ff3[cols] if model in ("CAPM", "FF3") else ff5[cols]


# ----------------------------------------------------------------------------- signal and weights
def mom_signal(R: pd.DataFrame, L: int, S: int) -> pd.DataFrame:
    """Cumulative return over months t-S-L+1 .. t-S at formation month t. Requires all L returns (else NaN).
    Primary: L=11, S=1, i.e. months t-11..t-1 at formation t, which is t-12..t-2 relative to the holding month t+1."""
    lr = np.log1p(R)
    return np.expm1(lr.rolling(L, min_periods=L).sum().shift(S))


def formation_dates(R: pd.DataFrame, start=FORM_START, end=FORM_END) -> pd.DatetimeIndex:
    return R.index[(R.index >= start) & (R.index <= end)]


def rank_weights(sig: pd.DataFrame, R: pd.DataFrame, n_long: int = 8, n_short: int | None = None,
                 long_universe=None, short_universe=None, cap: pd.DataFrame | None = None,
                 dates=None) -> pd.DataFrame:
    """Long the n_long highest-signal eligible industries, short the n_short lowest. Equal weights (or cap weights
    within each leg if cap is given, cap measured at the formation month). Legs sum to +1 and -1.
    Eligible at t: signal non-missing at t and return non-missing in t+1 (an industry that exists at t)."""
    n_short = n_short or n_long
    dates = formation_dates(R) if dates is None else dates
    W = pd.DataFrame(0.0, index=dates, columns=R.columns)
    nxt = R.shift(-1)
    for t in dates:
        s = sig.loc[t]
        s = s[s.notna() & nxt.loc[t].notna()]
        sl = s if long_universe is None else s[s.index.isin(long_universe)]
        ss = s if short_universe is None else s[s.index.isin(short_universe)]
        top = sl.sort_values(ascending=False, kind="mergesort").index[:n_long]
        bot = ss.drop(top, errors="ignore").sort_values(ascending=True, kind="mergesort").index[:n_short]
        if cap is None:
            wl = pd.Series(1.0 / len(top), index=top); ws = pd.Series(1.0 / len(bot), index=bot)
        else:
            cl, cs = cap.loc[t, top], cap.loc[t, bot]
            wl, ws = cl / cl.sum(), cs / cs.sum()
        W.loc[t, top] = wl.values
        W.loc[t, bot] = -ws.values
    return W


# ----------------------------------------------------------------------------- backtest
def drift(h_prev: np.ndarray, r: np.ndarray) -> np.ndarray:
    """Holdings after one month of returns, per unit of capital (zero-investment book on 1 unit of collateral)."""
    r = np.where(h_prev != 0, np.nan_to_num(r), 0.0)
    rp = float(h_prev @ r)
    return h_prev * (1 + r) / (1 + rp)


def backtest(W: pd.DataFrame, R: pd.DataFrame, cost: float = BASE_COST) -> pd.DataFrame:
    """W indexed at formation month t. Returns a frame indexed by the holding month t+1 with gross, long-leg,
    short-leg, turnover (sum |w_t - drifted w_{t-1}|, traded at the end of t) and net = gross - cost * turnover."""
    idx = R.index; pos = {d: i for i, d in enumerate(idx)}
    Rv = R.values; rows = []; prev = np.zeros(R.shape[1]); prev_t = None
    for t, w in zip(W.index, W.values):
        i = pos[t]
        if prev_t is not None:
            assert pos[prev_t] == i - 1, "formation dates must be consecutive"
            d = drift(prev, Rv[i])
        else:
            d = np.zeros_like(prev)
        to = float(np.abs(w - d).sum())
        rn = Rv[i + 1]
        if np.any((w != 0) & np.isnan(rn)):
            raise ValueError(f"missing next-month return for a held industry at {t}")
        rn0 = np.nan_to_num(rn)
        lw, sw = np.clip(w, 0, None), np.clip(-w, 0, None)
        rows.append((idx[i + 1], float(w @ rn0), float(lw @ rn0) / max(lw.sum(), 1e-12),
                     float(sw @ rn0) / max(sw.sum(), 1e-12), to))
        prev, prev_t = w, t
    out = pd.DataFrame(rows, columns=["date", "gross", "long", "short", "turnover"]).set_index("date")
    out["cost"] = cost * out["turnover"]
    out["net"] = out["gross"] - out["cost"]
    return out


def to_holding_index(W: pd.DataFrame) -> pd.DataFrame:
    """Re-index weights formed at t to the holding month t+1."""
    W = W.copy(); W.index = W.index + pd.offsets.MonthEnd(1)
    return W


# ----------------------------------------------------------------------------- statistics
def sl(s, period):
    if isinstance(period, tuple):
        return s.loc[period[0]:period[1]]
    return C.sub(s, period)


def max_dd(r: pd.Series) -> float:
    w = (1 + r.dropna()).cumprod()
    return float((w / w.cummax() - 1).min())


def perf_block(bt: pd.DataFrame, period) -> dict:
    d = sl(bt, period)
    if len(d) < 3:
        return {"n": len(d)}
    g, n = d["gross"], d["net"]
    t_net = nw_ols(n, lags=6).tvalues.iloc[0]
    return {"start": d.index[0].strftime("%Y-%m"), "end": d.index[-1].strftime("%Y-%m"), "n": len(d),
            "gross_ret": 12 * g.mean(), "net_ret": 12 * n.mean(), "vol": np.sqrt(12) * n.std(ddof=1),
            "sharpe_gross": np.sqrt(12) * g.mean() / g.std(ddof=1), "sharpe_net": np.sqrt(12) * n.mean() / n.std(ddof=1),
            "t_net_mean_nw6": t_net, "max_dd_net": max_dd(n), "hit_rate": float((n > 0).mean()),
            "turnover_ann": 12 * d["turnover"].mean(), "cost_drag_ann": 12 * d["cost"].mean()}


def alpha_fit(y: pd.Series, X: pd.DataFrame, lags: int = 6) -> dict:
    """NW-HAC alpha and loadings, plus a small-sample check on the intercept: classic (iid) OLS t with a Student-t
    p-value on n - k degrees of freedom (t_alpha_ols, p_alpha_ols_t). With few observations and many regressors
    the NW standard error is biased down and its normal p-value is optimistic; the OLS column shows by how much."""
    res = nw_ols(y, X, lags=lags)
    ols = sm.OLS(res.model.endog, res.model.exog).fit()
    row = {"n": int(res.nobs), "alpha_ann": 12 * res.params["const"], "t_alpha": res.tvalues["const"],
           "p_alpha": res.pvalues["const"], "r2": res.rsquared,
           "t_alpha_ols": float(ols.tvalues[0]), "p_alpha_ols_t": float(ols.pvalues[0]), "df_resid": int(ols.df_resid)}
    for c in X.columns:
        row[f"b_{c}"] = res.params[c]; row[f"t_{c}"] = res.tvalues[c]; row[f"p_{c}"] = res.pvalues[c]
    return row


def min_obs(model: str) -> int:
    return 12 if model == "CAPM" else 24


def ir(x: np.ndarray, axis=None):
    return np.sqrt(12) * np.mean(x, axis=axis) / np.std(x, axis=axis, ddof=1)


# ----------------------------------------------------------------------------- bootstrap
def cbb_indices(n: int, block: int, B: int, rng) -> np.ndarray:
    """Circular block bootstrap index matrix (B x n)."""
    nb = int(np.ceil(n / block))
    starts = rng.integers(0, n, size=(B, nb))
    idx = (starts[:, :, None] + np.arange(block)[None, None, :]) % n
    return idx.reshape(B, nb * block)[:, :n]


def paired_boot(a: pd.Series, b: pd.Series, X: pd.DataFrame | None = None, block: int = 12, B: int = 5000,
                seed: int = 20260926) -> dict:
    """Paired circular block bootstrap of IR(a) - IR(b) and (if X given) the factor alpha of (a - b).
    Two-sided p-value from the bootstrap distribution re-centred at the point estimate."""
    d = pd.concat([a.rename("a"), b.rename("b")] + ([X] if X is not None else []), axis=1).dropna()
    av, bv = d["a"].values, d["b"].values; n = len(d)
    rng = np.random.default_rng(seed)
    idx = cbb_indices(n, block, B, rng)
    dir_hat = ir(av) - ir(bv)
    dirs = ir(av[idx], axis=1) - ir(bv[idx], axis=1)
    out = {"n": n, "block": block, "B": B, "d_ir": dir_hat,
           "d_ir_lo": np.percentile(dirs, 2.5), "d_ir_hi": np.percentile(dirs, 97.5),
           "p_d_ir": float(np.mean(np.abs(dirs - dir_hat) >= abs(dir_hat)))}
    if X is not None:
        Xm = np.column_stack([np.ones(n), d[X.columns].values]); y = av - bv
        coef_hat = np.linalg.lstsq(Xm, y, rcond=None)[0][0] * 12
        al = np.empty(B)
        for k in range(B):
            ii = idx[k]
            al[k] = np.linalg.lstsq(Xm[ii], y[ii], rcond=None)[0][0] * 12
        out.update({"d_alpha": coef_hat, "d_alpha_lo": np.percentile(al, 2.5), "d_alpha_hi": np.percentile(al, 97.5),
                    "p_d_alpha_boot": float(np.mean(np.abs(al - coef_hat) >= abs(coef_hat)))})
    return out


# ----------------------------------------------------------------------------- carbon helpers
def carbon_maps(emis: pd.Series, columns) -> dict:
    """Convention X: only the 41 covered industries have intensities. Convention M: the 8 uncovered industries
    get the cross-sectional median intensity of the 41 covered industries."""
    covered = [c for c in columns if c in emis.index]
    missing = [c for c in columns if c not in emis.index]
    med = float(emis.median())
    return {"covered": covered, "missing": missing, "median": med,
            "X": emis.reindex(covered), "M": emis.reindex(columns).fillna(med)}


def leg_waci(W: pd.DataFrame, ci: pd.Series):
    """Weighted average carbon intensity of the long and short legs (weights renormalised over industries that have
    an intensity in ci) plus the share of each leg's weight that is covered."""
    out = {}
    for leg, w in (("long", W.clip(lower=0)), ("short", (-W).clip(lower=0))):
        wc = w.reindex(columns=ci.index).fillna(0.0)
        tot = wc.sum(axis=1)
        out[f"{leg}_waci"] = (wc * ci).sum(axis=1) / tot.replace(0, np.nan)
        out[f"{leg}_cov"] = tot / w.sum(axis=1).replace(0, np.nan)
    df = pd.DataFrame(out)
    df["net_waci"] = df["long_waci"] - df["short_waci"]
    return df


def market_waci(cap: pd.DataFrame, ci: pd.Series, dates) -> pd.Series:
    c = cap.reindex(index=dates, columns=ci.index)
    return (c * ci).sum(axis=1) / c.sum(axis=1)


# ----------------------------------------------------------------------------- output helpers
LEDGER: list[dict] = []


def ledger_add(test_id, question, statistic_name, statistic, p, n_obs, kind, note=""):
    LEDGER.append({"test_id": test_id, "module": MOD, "question": question, "statistic_name": statistic_name,
                   "statistic": float(statistic) if statistic is not None else np.nan,
                   "p_value_two_sided": float(p) if p is not None else np.nan, "n_obs": int(n_obs),
                   "primary_or_exploratory": kind, "note": note})


def save(df: pd.DataFrame, name: str, index: bool = True):
    df.to_csv(TABLES / f"{MOD}_{name}.csv", index=index)
    return df


def save_tex(df: pd.DataFrame, name: str, fmt: dict | None = None, index: bool = True, pct: tuple = (),
             digits: int = 2, caption: str | None = None):
    """Write a booktabs LaTeX table. Columns in pct are multiplied by 100. fmt maps column -> format string."""
    d = df.copy()
    fmt = fmt or {}
    for c in d.columns:
        num = pd.to_numeric(d[c], errors="coerce")
        is_num = num.notna().sum() == d[c].notna().sum() and num.notna().any() and d[c].map(lambda v: not isinstance(v, (bool, np.bool_))).all()
        if c in pct:
            d[c] = num.map(lambda v: "" if pd.isna(v) else f"{100 * v:.{digits}f}")
        elif c in fmt:
            f = fmt[c]
            d[c] = num.map(lambda v, f=f: "" if pd.isna(v) else (format(int(round(v)), "d") if f == "d" else format(v, f)))
        elif is_num and not (num.dropna() % 1 == 0).all():
            d[c] = num.map(lambda v: "" if pd.isna(v) else f"{v:.{digits}f}")
        elif is_num:
            d[c] = num.map(lambda v: "" if pd.isna(v) else f"{int(v)}")
    tex = d.to_latex(index=index, escape=True, caption=caption, column_format=None)
    (TABLES / f"{MOD}_{name}.tex").write_text(tex)
