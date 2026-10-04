"""Helpers for M3_alpha_beta (alpha vs static / time-varying beta; rates-duration channel).

Everything here is module-local; lib/common.py, lib/plotstyle.py and lib/team_pipeline.py are imported, never edited.
Conventions: month-end index, decimal returns, annualize mean x12 and vol x sqrt(12).
"""
from __future__ import annotations

import pathlib
import sys
import warnings

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, "/home/hashim/projects/GA/project/research/lib")
from common import (TABLES, FIGURES, PERIODS, load_team, load_ff5_mom, load_fred, me)  # noqa: E402,F401
from team_pipeline import run_pipeline, team_controls  # noqa: E402,F401

MOD = "M3_alpha_beta"
HERE = pathlib.Path(__file__).resolve().parent
DATA = HERE / "data"
END = "2026-07-31"
STRAT_START = "1999-03-31"          # first month every timing strategy (both baselines) can hold a position
NW_LAGS = 6

STRATS = ["Original | Short Brown hold 3m", "Pure | Short Brown hold 3m", "Original | Short Brown hold 6m",
          "Pure | Short Brown hold 6m", "Continuous | raw attention", "Continuous | pure attention"]
BENCH = "Benchmark | Always-short Brown"
SHORT = {"Original | Short Brown hold 3m": "Orig 3m", "Pure | Short Brown hold 3m": "Pure 3m",
         "Original | Short Brown hold 6m": "Orig 6m", "Pure | Short Brown hold 6m": "Pure 6m",
         "Continuous | raw attention": "Cont raw", "Continuous | pure attention": "Cont pure",
         "Benchmark | Always-short Brown": "Always-short Brown"}

# analysis periods: common.PERIODS plus the strategy live window
M3_PERIODS = {"full": ("1970-01-31", END), "full_live": (STRAT_START, END)}
for _k in ("post2010", "validation", "holdout", "pre_covid", "covid", "inflation_rates", "last18", "last12"):
    M3_PERIODS[_k] = PERIODS[_k]


# ============================================================================ regression engine
def nw_fit(y: pd.Series, X: pd.DataFrame | None, lags: int = NW_LAGS, const: bool = True) -> dict:
    """OLS with Bartlett-kernel HAC covariance (identical estimator to team_pipeline.newey_west_regression:
    pinv, no df correction). Returns coefficients, se, t, HAC covariance, n, k, R2 and two-sided p-values
    from t(n-k) ('p') and N(0,1) ('p_norm')."""
    X = pd.DataFrame(index=y.index) if X is None else X
    d = pd.concat([y.rename("__y"), X], axis=1, sort=True).dropna()
    names = (["const"] if const else []) + list(X.columns)
    Xm = d[list(X.columns)].to_numpy(float)
    if const:
        Xm = np.column_stack([np.ones(len(d)), Xm])
    yv = d["__y"].to_numpy(float)
    n, k = Xm.shape
    inv = np.linalg.pinv(Xm.T @ Xm)
    b = inv @ Xm.T @ yv
    u = yv - Xm @ b
    xu = Xm * u[:, None]
    meat = xu.T @ xu
    for lag in range(1, min(lags, n - 1) + 1):
        g = xu[lag:].T @ xu[:-lag]
        meat += (1.0 - lag / (lags + 1.0)) * (g + g.T)
    V = inv @ meat @ inv
    se = np.sqrt(np.clip(np.diag(V), 0, None))
    with np.errstate(divide="ignore", invalid="ignore"):
        t = b / se
    df = max(n - k, 1)
    sst = ((yv - yv.mean()) ** 2).sum()
    r2 = 1 - (u ** 2).sum() / sst if sst > 0 else np.nan
    return {"b": pd.Series(b, names), "se": pd.Series(se, names), "t": pd.Series(t, names),
            "p": pd.Series(2 * stats.t.sf(np.abs(t), df), names), "p_norm": pd.Series(2 * stats.norm.sf(np.abs(t)), names),
            "V": pd.DataFrame(V, names, names), "n": n, "k": k, "df": df, "r2": r2,
            "resid": pd.Series(u, d.index), "index": d.index}


def wald(fit: dict, names: list[str], R: np.ndarray | None = None, r: np.ndarray | None = None) -> dict:
    """HAC Wald test of R b = r for the coefficients `names` (default: all equal zero).
    Returns chi2 statistic, its p (chi2(q)), the F version stat/q with p from F(q, n-k)."""
    b = fit["b"][names].to_numpy()
    V = fit["V"].loc[names, names].to_numpy()
    q = len(names) if R is None else R.shape[0]
    R = np.eye(len(names)) if R is None else R
    r = np.zeros(q) if r is None else r
    d = R @ b - r
    try:
        W = float(d @ np.linalg.pinv(R @ V @ R.T) @ d)
    except np.linalg.LinAlgError:
        W = np.nan
    return {"chi2": W, "q": q, "p_chi2": float(stats.chi2.sf(W, q)), "F": W / q, "p_F": float(stats.f.sf(W / q, q, fit["df"]))}


def lincom(fit: dict, weights: dict) -> tuple[float, float, float]:
    """Linear combination sum_j w_j b_j: (estimate, HAC se, p from t(n-k))."""
    names = list(weights)
    w = np.array([weights[n] for n in names])
    est = float(w @ fit["b"][names].to_numpy())
    se = float(np.sqrt(w @ fit["V"].loc[names, names].to_numpy() @ w))
    p = float(2 * stats.t.sf(abs(est / se), fit["df"])) if se > 0 else np.nan
    return est, se, p


# ============================================================================ BOND factor
# BOND is the factor built and validated in M8 (modules/M8_frozen_pre2010/run.py, build_bond / par_bond_dc /
# exact_par_return; checks in outputs/tables/M8_bond_check.csv). It is imported here, not re-implemented.
# M8's run.py only defines functions at import time (main() runs under __main__), so importing it is side-effect free.
def _load_m8():
    import importlib.util
    p = HERE.parent / "M8_frozen_pre2010" / "run.py"
    spec = importlib.util.spec_from_file_location("m8_frozen_run", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


M8 = _load_m8()


def par_bond_duration_convexity(y: np.ndarray, maturity: float = 10.0, m: int = 2):
    """Independent M3 implementation, kept only to cross-check M8.par_bond_dc (the series used is M8's).
    Modified duration and convexity (years, years^2) of a par bond with m coupons a year at yield y (decimal, BEY).
    Closed form check: D_mod = (1/y) * (1 - (1 + y/m)^(-m*T))."""
    y = np.asarray(y, float)
    i = np.arange(1, int(maturity * m) + 1)
    cf = np.repeat((100 * y / m)[:, None], len(i), axis=1)
    cf[:, -1] += 100
    disc = (1 + y[:, None] / m) ** (-i)
    P = (cf * disc).sum(1)
    D = (cf * (i / m) * disc / (1 + y[:, None] / m)).sum(1) / P
    C = (cf * (i / m) * ((i + 1) / m) * disc / (1 + y[:, None] / m) ** 2).sum(1) / P
    return P, D, C


def bond_frame(rf: pd.Series) -> pd.DataFrame:
    """BOND = y_{t-1}/12 - D_{t-1}(y_t - y_{t-1}) + 0.5 C_{t-1}(y_t - y_{t-1})^2 - RF_t, from GS10 (monthly average of
    daily constant-maturity yields), computed by M8.build_bond (imported from modules/M8_frozen_pre2010/run.py).
    RF = team FF3 RF (the RF of the Green and Brown leg excess returns; identical to the Ken French RF M8 uses, 1970-2026).
    Adds: carry, duration-only return, exact-repricing excess return, a cross-check against the independent M3
    implementation, and (if the cached end-of-month Treasury par yield file exists) the same construction from
    end-of-month yields (BOND_eom, robustness only)."""
    g = load_fred("GS10")
    out = M8.build_bond(g, rf)                    # y10, dy, D_mod, convexity, ret_total, ret_exact, RF, BOND
    y0, dy = out["y10"].shift(1), out["dy"]
    out["carry"] = y0 / 12
    out["ret_dur_only"] = y0 / 12 - out["D_mod"] * dy
    out["BOND_exact"] = out["ret_exact"] - out["RF"]
    ok = y0.notna() & out["y10"].notna()
    _, d_i, c_i = par_bond_duration_convexity(y0[ok].to_numpy())
    alt = pd.Series(np.nan, out.index)
    alt[ok] = y0[ok] / 12 - d_i * dy[ok] + 0.5 * c_i * dy[ok] ** 2
    out["check_absdiff_independent_impl"] = (alt - out["ret_total"]).abs()
    eom = eom_yield()
    if eom is not None:
        ye = eom.reindex(out.index)
        y0e = ye.shift(1); dye = ye - y0e
        oke = y0e.notna() & ye.notna()
        _, de, ce = M8.par_bond_dc(y0e[oke].to_numpy())
        be = pd.Series(np.nan, out.index)
        be[oke] = y0e[oke] / 12 - de * dye[oke] + 0.5 * ce * dye[oke] ** 2
        out["y10_eom"] = ye
        out["BOND_eom"] = be - out["RF"]
    return out.loc["1953-05-31":]


def eom_yield() -> pd.Series | None:
    """End-of-month 10y par yield (decimal), 1990 onward, from the cached US Treasury daily par yield curve
    (fetch_treasury.py). Falls back to a cached FRED DGS10 file. None if nothing is cached (robustness is skipped)."""
    p = DATA / "tsy_10y_eom.csv"
    if p.exists():
        s = pd.read_csv(p, parse_dates=["date"]).set_index("date")["y10_eom"].astype(float)
        s.index = me(s.index)
        return (s / 100).rename("y10_eom")
    for f in ("fred_DGS10_eom.csv", "fred_DGS10.csv"):
        p = DATA / f
        if p.exists() and p.stat().st_size > 1000:
            df = pd.read_csv(p)
            df.columns = ["date", "v"]
            s = pd.to_numeric(df.set_index(pd.to_datetime(df["date"]))["v"], errors="coerce").dropna()
            return (s.resample("ME").last() / 100).rename("y10_eom")
    return None


def damodaran_tbond() -> pd.Series | None:
    """Damodaran (NYU Stern, histretSP.xls, updated Jan 2026) annual 10-year T-bond total return, if cached."""
    p = DATA / "histretSP.xls"
    if not p.exists():
        return None
    d = pd.read_excel(p, "T. Bond yield & return", header=None)
    d = d.iloc[7:, :3].dropna()
    d.columns = ["year", "yield", "ret"]
    d = d[pd.to_numeric(d["year"], errors="coerce").notna()]
    return pd.Series(d["ret"].astype(float).to_numpy(), index=d["year"].astype(int).to_numpy(), name="damodaran")


# ============================================================================ factors and instruments
def load_factor_panel() -> pd.DataFrame:
    """One panel with every factor used in M3.
    Mkt-RF, SMB, HML, RF: team FF3 file (identical to the write-up's inputs).
    Mkt-RF5, SMB5, HML5, RMW, CMA: Ken French 5-factor 2x3 file (Aug 2026 vintage). UMD: Ken French momentum.
    BOND: 10y par Treasury excess return (bond_frame)."""
    T = load_team()
    ff3 = T["ff3"][["Mkt-RF", "SMB", "HML", "RF"]]
    k5 = load_ff5_mom()
    k5 = k5.rename(columns={"Mkt-RF": "Mkt-RF5", "SMB": "SMB5", "HML": "HML5"})[["Mkt-RF5", "SMB5", "HML5", "RMW", "CMA", "UMD"]]
    bf = bond_frame(ff3["RF"])
    cols = ["BOND"] + [c for c in ("BOND_exact", "BOND_eom") if c in bf]
    return ff3.join(k5, how="left").join(bf[cols], how="left").loc[:END]


MODELS = {
    "CAPM": ["Mkt-RF"],
    "FF3": ["Mkt-RF", "SMB", "HML"],
    "FF3+BOND": ["Mkt-RF", "SMB", "HML", "BOND"],
    "FF3+UMD+BOND": ["Mkt-RF", "SMB", "HML", "UMD", "BOND"],
    "FF5": ["Mkt-RF5", "SMB5", "HML5", "RMW", "CMA"],
    "FF5+UMD": ["Mkt-RF5", "SMB5", "HML5", "RMW", "CMA", "UMD"],
    "FF5+UMD+BOND": ["Mkt-RF5", "SMB5", "HML5", "RMW", "CMA", "UMD", "BOND"],
}


def fname(c: str) -> str:
    """Display name: drop the '5' suffix of the 5-factor-file columns."""
    return c[:-1] if c in ("Mkt-RF5", "SMB5", "HML5") else c


def instruments() -> pd.DataFrame:
    """Information-date instruments z_t, all known at the end of month t:
    TERM_t = GS10_t - TB3MS_t, CREDIT_t = BAA_t - AAA_t, Y10_t = GS10_t (monthly averages over month t, known at t);
    INFL_t = 100 * log(CPI_{t-1}/CPI_{t-13}) and CFNAI_t = CFNAI_{t-1} (one-month publication lag).
    CPI Oct-2025 gap linearly interpolated. Used as z_{t-1} for returns of month t."""
    gs10, tb3 = load_fred("GS10"), load_fred("TB3MS")
    baa, aaa = load_fred("BAA"), load_fred("AAA")
    cpi = load_fred("CPIAUCSL").interpolate(limit_area="inside")
    cfnai = load_fred("CFNAI")
    infl = 100 * np.log(cpi).diff(12)
    return pd.DataFrame({"TERM": gs10 - tb3, "CREDIT": baa - aaa, "Y10": gs10,
                         "INFL": infl.shift(1), "CFNAI": cfnai.shift(1)})


# ============================================================================ pipeline runs
def corrected_macro():
    mac = load_team()["macro"].copy()
    mac["cpi"] = mac["cpi"].interpolate(limit_area="inside")
    return mac


def run_baseline(which: str, factors=None, factor_cols=("Mkt-RF", "SMB", "HML"), costs=None, full=False, **kw):
    """which='team' -> run_pipeline defaults; which='corrected' -> CPI gap interpolated and attention plus purification
    controls lagged one month. factors/factor_cols/costs pass through (for BOND-hedged reruns)."""
    mode = dict(bootstrap_reps=5000) if full else dict(bootstrap_reps=0, extras=False, paired=False)
    mode.setdefault("macro_states", kw.pop("macro_states", False))
    if which == "team":
        return run_pipeline(factors=factors, factor_cols=factor_cols, costs=costs, **mode, **kw)
    m3 = corrected_macro()
    return run_pipeline(macro=m3, attention=m3["attention"].shift(1), controls=team_controls(m3).shift(1),
                        factors=factors, factor_cols=factor_cols, costs=costs, **mode, **kw)


# ============================================================================ rolling betas, decomposition
def rolling_betas(y: pd.Series, F: pd.DataFrame, window: int, mode: str = "backward") -> pd.DataFrame:
    """Rolling OLS betas of y on [1, F] aligned to month t.
    backward: estimated on months t-window..t-1 (known at the end of t-1; predetermined for month t).
    centered: estimated on months t-window/2+1..t+window/2 (uses future data; ex-post attribution only), clamped to
    the span of complete rows so the first/last window/2 months use the nearest full window (same sample as backward).
    Windows with any missing value are skipped."""
    d = pd.concat([y.rename("__y"), F], axis=1, sort=True)
    Y = d["__y"].to_numpy(float); X = d[F.columns].to_numpy(float)
    n, k = X.shape
    B = np.full((n, k + 1), np.nan)
    ok = np.flatnonzero(~(np.isnan(Y) | np.isnan(X).any(axis=1)))
    first, last = (ok[0], ok[-1]) if len(ok) else (0, -1)
    for t in range(n):
        if mode == "backward":
            lo, hi = t - window, t
        else:
            if t < first or t > last:
                continue
            lo = min(max(t - window // 2 + 1, first), last + 1 - window)
            hi = lo + window
        if lo < 0 or hi > n:
            continue
        yy, xx = Y[lo:hi], X[lo:hi]
        if np.isnan(yy).any() or np.isnan(xx).any():
            continue
        coef, *_ = np.linalg.lstsq(np.column_stack([np.ones(hi - lo), xx]), yy, rcond=None)
        B[t] = coef
    return pd.DataFrame(B, index=d.index, columns=["alpha"] + list(F.columns))


def ln_decomposition(r: pd.Series, betas: pd.DataFrame, F: pd.DataFrame, start, end) -> dict:
    """Exact identity over [start, end] with 1/n moments:
    mean(r) = mean(alpha_c) + sum_k mean(beta_k) mean(f_k) + sum_k cov(beta_k, f_k), alpha_c,t = r_t - beta_t'f_t.
    Returns annualized (x12) components and per-factor timing covariances."""
    cols = list(F.columns)
    d = pd.concat([r.rename("r"), betas[cols].add_prefix("b_"), F], axis=1, sort=True).loc[start:end].dropna()
    if len(d) < 3:
        return {"n": len(d)}
    B = d[[f"b_{c}" for c in cols]].to_numpy(); Fm = d[cols].to_numpy()
    alpha_c = d["r"].to_numpy() - (B * Fm).sum(1)
    mb, mf = B.mean(0), Fm.mean(0)
    cov = ((B - mb) * (Fm - mf)).mean(0)
    out = {"n": len(d), "mean_r": 12 * d["r"].mean(), "cond_alpha": 12 * alpha_c.mean(),
           "static_beta": 12 * float(mb @ mf), "timing_cov": 12 * float(cov.sum())}
    for j, c in enumerate(cols):
        out[f"cov_{fname(c)}"] = 12 * cov[j]
        out[f"meanbeta_{fname(c)}"] = mb[j]
        out[f"static_{fname(c)}"] = 12 * mb[j] * mf[j]
    out["identity_gap"] = out["mean_r"] - out["cond_alpha"] - out["static_beta"] - out["timing_cov"]
    return out


def block_indices(n: int, block: int, rng) -> np.ndarray:
    nb = int(np.ceil(n / block))
    starts = rng.integers(0, n, size=nb)
    return ((starts[:, None] + np.arange(block)) % n).ravel()[:n]


def adaptive_block(n: int, block: int | None = None) -> int:
    """Team block length 12, shortened for short windows so every draw has at least 8 blocks: min(12, max(2, n // 8)).
    n >= 96 keeps 12 (all primary tests); holdout n = 48 -> 6; COVID n = 24 -> 3."""
    return block if block is not None else int(min(12, max(2, n // 8)))


def timing_cov_bootstrap(r: pd.Series, betas: pd.DataFrame, F: pd.DataFrame, start, end, reps=5000, block=None, seed=230):
    """Circular block bootstrap of the annualized beta-timing component sum_k cov(beta_k,t, f_k,t) and of the
    conditional alpha. Rows (r_t, beta_t, f_t) resampled jointly in blocks (adaptive_block). p = 2 min(P(draw>0), P(draw<0)).
    Also NW(6) t and t(n-1) p for both, from the mean of the per-month product and conditional-alpha series."""
    cols = list(F.columns)
    d = pd.concat([r.rename("r"), betas[cols].add_prefix("b_"), F], axis=1, sort=True).loc[start:end].dropna()
    B = d[[f"b_{c}" for c in cols]].to_numpy(); Fm = d[cols].to_numpy(); R = d["r"].to_numpy()
    n = len(d)
    block = adaptive_block(n, block)
    rng = np.random.default_rng(seed)
    cov_d = np.empty(reps); alp_d = np.empty(reps)
    for i in range(reps):
        idx = block_indices(n, block, rng)
        b, f = B[idx], Fm[idx]
        cov_d[i] = 12 * ((b - b.mean(0)) * (f - f.mean(0))).mean(0).sum()
        alp_d[i] = 12 * (R[idx] - (b * f).sum(1)).mean()
    cov_hat = 12 * ((B - B.mean(0)) * (Fm - Fm.mean(0))).mean(0).sum()
    alp_hat = 12 * (R - (B * Fm).sum(1)).mean()
    p = lambda x: 2 * min((x > 0).mean(), (x < 0).mean())  # noqa: E731
    # NW t on the mean of the demeaned product series (asymptotic alternative)
    prod = pd.Series(((B - B.mean(0)) * (Fm - Fm.mean(0))).sum(1), index=d.index)
    fit = nw_fit(prod, None)
    fa = nw_fit(pd.Series(R - (B * Fm).sum(1), index=d.index), None)
    return {"n": n, "block": block, "timing_cov": cov_hat, "timing_ci_low": np.quantile(cov_d, .025), "timing_ci_high": np.quantile(cov_d, .975),
            "timing_p_boot": p(cov_d), "timing_t_nw": float(fit["t"]["const"]), "timing_p_nw": float(fit["p"]["const"]),
            "cond_alpha": alp_hat, "alpha_ci_low": np.quantile(alp_d, .025), "alpha_ci_high": np.quantile(alp_d, .975),
            "alpha_p_boot": p(alp_d), "alpha_t_nw": float(fa["t"]["const"]), "alpha_p_nw": float(fa["p"]["const"])}


def mean_block_bootstrap(x: pd.Series, reps=5000, block=None, seed=230) -> dict:
    v = x.dropna().to_numpy(); n = len(v)
    block = adaptive_block(n, block)
    rng = np.random.default_rng(seed)
    dr = np.array([12 * v[block_indices(n, block, rng)].mean() for _ in range(reps)])
    return {"mean_ann": 12 * v.mean(), "ci_low": np.quantile(dr, .025), "ci_high": np.quantile(dr, .975),
            "p_boot": 2 * min((dr > 0).mean(), (dr < 0).mean()), "block": block}


# ============================================================================ Ferson-Schadt
def expanding_standardize(Z: pd.DataFrame, min_periods: int = 24) -> pd.DataFrame:
    """Column by column (z_t - mean(z_..t)) / sd(z_..t) over each instrument's own history from its first observation
    (expanding, ddof=1). Z is already the information-date-lagged instrument (z_{t-1} on row t), so row t only uses
    data known at the end of t-1: the standardization is real time, like the instruments themselves."""
    m = Z.expanding(min_periods=min_periods).mean()
    s = Z.expanding(min_periods=min_periods).std(ddof=1)
    return (Z - m) / s


def _hac_wald_fixed(X: np.ndarray, inv: np.ndarray, y: np.ndarray, idx: np.ndarray, lags: int) -> float:
    """HAC (Bartlett, no df correction) Wald statistic for b[idx] = 0 with a fixed design X and inv = pinv(X'X)."""
    b = inv @ (X.T @ y)
    u = y - X @ b
    xu = X * u[:, None]
    meat = xu.T @ xu
    for lag in range(1, min(lags, len(y) - 1) + 1):
        g = xu[lag:].T @ xu[:-lag]
        meat += (1.0 - lag / (lags + 1.0)) * (g + g.T)
    V = inv @ meat @ inv
    bc = b[idx]
    return float(bc @ np.linalg.pinv(V[np.ix_(idx, idx)]) @ bc)


def ferson_schadt(y: pd.Series, F: pd.DataFrame, Z: pd.DataFrame, cond: list[str], start, end,
                  dummies: pd.DataFrame | None = None, tv_alpha: bool = False, standardize: str = "expanding",
                  boot_reps: int = 0, block: int = 12, seed: int = 230) -> dict:
    """r_t = a + sum_k (b_k + c_k' z_{t-1}) f_k,t [+ a' z_{t-1}] [+ dummies] + e_t.
    Z = lagged instruments aligned to t (z_{t-1} on row t).
    standardize='expanding': Z is used as passed (the caller standardizes with expanding_standardize, real time), so
        `a` is the conditional alpha when every instrument sits at its real-time historical mean.
    standardize='window': Z is standardized with the estimation-window mean and sd (ex post; robustness).
    Factors in F not listed in `cond` enter unconditionally.
    Joint test of all c = 0: (1) HAC Wald, (2) classical nested F, (3) if boot_reps > 0, a fixed-design circular
    block bootstrap of the HAC Wald statistic under the null (restricted-model residuals resampled in blocks of
    `block`, y* = X_r b_r + u*): p = (1 + #{W* >= W}) / (1 + reps), and (4) a wild block bootstrap under the null
    (y* = X_r b_r + u_r x eta, eta a Rademacher sign per block of `block` months). The HAC Wald with q = 20
    restrictions and n = 150-680 over-rejects badly (asymptotic chi2 critical values). (3) breaks the link between
    residual size and the regressors; (4) keeps it and is the preferred bootstrap p."""
    d = pd.concat([y.rename("__y"), F, Z.add_prefix("z_")], axis=1, sort=True).loc[start:end].dropna()
    zc = [f"z_{c}" for c in Z.columns]
    zs = (d[zc] - d[zc].mean()) / d[zc].std(ddof=1) if standardize == "window" else d[zc]
    X = d[list(F.columns)].copy()
    inter = []
    for k in cond:
        for zcol in zc:
            nm = f"{k}x{zcol[2:]}"
            X[nm] = d[k] * zs[zcol]
            inter.append(nm)
    tva = []
    if tv_alpha:
        for zcol in zc:
            X[f"a_{zcol[2:]}"] = zs[zcol]; tva.append(f"a_{zcol[2:]}")
    if dummies is not None:
        X = X.join(dummies.reindex(X.index))
    fit = nw_fit(d["__y"], X)
    out = {"fit": fit, "interactions": inter, "tv_alpha_cols": tva, "start": d.index[0], "end": d.index[-1]}
    out["wald_c"] = wald(fit, inter)
    restr = nw_fit(d["__y"], X.drop(columns=inter))
    ssr_u, ssr_r = float((fit["resid"] ** 2).sum()), float((restr["resid"] ** 2).sum())
    q = len(inter)
    Fc = ((ssr_r - ssr_u) / q) / (ssr_u / fit["df"])
    out["ols_F_c"] = {"F": Fc, "p": float(stats.f.sf(Fc, q, fit["df"]))}
    adj = lambda r2, n, k: 1 - (1 - r2) * (n - 1) / (n - k)  # noqa: E731
    out["adj_r2"] = adj(fit["r2"], fit["n"], fit["k"])
    out["adj_r2_restricted"] = adj(restr["r2"], restr["n"], restr["k"])
    if tva:
        out["wald_a"] = wald(fit, tva)
    if boot_reps > 0:
        names = list(fit["b"].index)
        Xu = np.column_stack([np.ones(len(X)), X.to_numpy(float)])
        Xr = np.column_stack([np.ones(len(X)), X.drop(columns=inter).to_numpy(float)])
        inv_u = np.linalg.pinv(Xu.T @ Xu)
        idx = np.array([names.index(c) for c in inter])
        W0 = _hac_wald_fixed(Xu, inv_u, d["__y"].to_numpy(float), idx, NW_LAGS)
        fitted_r = Xr @ restr["b"].to_numpy()
        u_r = restr["resid"].to_numpy()
        rng = np.random.default_rng(seed)
        n = len(u_r)
        draws = np.empty(boot_reps)
        for i in range(boot_reps):
            ys = fitted_r + u_r[block_indices(n, block, rng)]
            draws[i] = _hac_wald_fixed(Xu, inv_u, ys, idx, NW_LAGS)
        out["boot_wald_c"] = {"W": W0, "p": (1 + (draws >= W0).sum()) / (1 + boot_reps), "reps": boot_reps,
                              "null_q95": float(np.quantile(draws, 0.95)), "null_median": float(np.median(draws))}
        # Wild block bootstrap under the null (added after verification): every month keeps its own restricted
        # residual, multiplied by a Rademacher sign drawn once per consecutive block of `block` months. This keeps
        # heteroskedasticity tied to the regressors (e.g. residual size tied to position size, zero-position months)
        # and within-block serial dependence, which the fixed-design resampling breaks. Separate RNG stream, so the
        # fixed-design draws above are unchanged.
        rng_w = np.random.default_rng(seed + 1)
        nb = int(np.ceil(n / block))
        draws_w = np.empty(boot_reps)
        for i in range(boot_reps):
            eta = np.repeat(rng_w.choice([-1.0, 1.0], size=nb), block)[:n]
            draws_w[i] = _hac_wald_fixed(Xu, inv_u, fitted_r + u_r * eta, idx, NW_LAGS)
        out["boot_wald_c_wild"] = {"W": W0, "p": (1 + (draws_w >= W0).sum()) / (1 + boot_reps), "reps": boot_reps,
                                   "null_q95": float(np.quantile(draws_w, 0.95)), "null_median": float(np.median(draws_w))}
    return out


# ============================================================================ timing tests
def timing_test(y: pd.Series, F: pd.DataFrame, factor: str, kind: str, controls: list[str] | None = None) -> dict:
    """Treynor-Mazuy (kind='TM'): r = a + b f + g f^2 [+ controls]; Henriksson-Merton ('HM'): r = a + b f + g max(f,0).
    Returns gamma, t, p (t(n-k)), alpha and n."""
    X = F[[factor] + [c for c in (controls or []) if c != factor]].copy()
    X["timing"] = F[factor] ** 2 if kind == "TM" else F[factor].clip(lower=0)
    fit = nw_fit(y, X)
    return {"gamma": fit["b"]["timing"], "t_gamma": fit["t"]["timing"], "p_gamma": fit["p"]["timing"],
            "beta": fit["b"][factor], "alpha_ann": 12 * fit["b"]["const"], "t_alpha": fit["t"]["const"],
            "p_alpha": fit["p"]["const"], "n": fit["n"], "k": fit["k"]}


# ============================================================================ output helpers
def fmt_num(v, nd=2):
    if v is None or (isinstance(v, float) and not np.isfinite(v)):
        return "--"
    if isinstance(v, (int, np.integer)):
        return f"{v:d}"
    if isinstance(v, (float, np.floating)):
        return f"{v:.{nd}f}".replace("-", "$-$")
    return str(v).replace("&", r"\&").replace("%", r"\%").replace("_", r"\_")


def to_tex(df: pd.DataFrame, path, digits: dict | None = None, default=2, col_format=None, header=None):
    """Minimal booktabs tabular writer. digits maps column -> decimals."""
    digits = digits or {}
    cols = list(df.columns)
    col_format = col_format or ("l" * 1 + "r" * (len(cols) - 1))
    head = header or [str(c).replace("_", r"\_").replace("&", r"\&").replace("%", r"\%") for c in cols]
    lines = [rf"\begin{{tabular}}{{{col_format}}}", r"\toprule", " & ".join(head) + r" \\", r"\midrule"]
    for i in range(len(df)):                  # column-wise access keeps integer dtypes (iterrows upcasts to float)
        cells = [fmt_num(df[c].iloc[i], digits.get(c, default)) for c in cols]
        lines.append(" & ".join(cells) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    pathlib.Path(path).write_text("\n".join(lines) + "\n")


class Ledger:
    """Tests ledger with the project schema."""

    def __init__(self):
        self.rows = []

    def add(self, test_id, question, statistic_name, statistic, p, n, kind, note=""):
        self.rows.append({"test_id": test_id, "module": MOD, "question": question, "statistic_name": statistic_name,
                          "statistic": float(statistic) if statistic is not None and np.isfinite(statistic) else np.nan,
                          "p_value_two_sided": float(p) if p is not None and np.isfinite(p) else np.nan,
                          "n_obs": int(n) if n is not None else np.nan, "primary_or_exploratory": kind, "note": note})

    def frame(self):
        return pd.DataFrame(self.rows)
