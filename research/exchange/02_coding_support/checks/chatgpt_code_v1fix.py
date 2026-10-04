"""
brown_attention_prereg.py

Pre-registered, run-once backtest of the frozen Brown-attention rule (MFE 230GA).
pandas / numpy / statsmodels only. No plots, no parameter search, fixed seed.

Order of use
  1. MODE = "synthetic": debug end to end on random data (+ look-ahead test, planted effect).
  2. MODE = "seen":      2010-01..2022-12, compare with the team's existing numbers.
  3. MODE = "final":     1993-01..2009-12, exactly once, no code change after step 2.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace

import numpy as np
import pandas as pd
import statsmodels.api as sm

pd.set_option("display.width", 220)
pd.set_option("display.max_columns", 40)
pd.set_option("display.max_rows", 500)
pd.set_option("display.float_format", "{:.6g}".format)

BROWN = ("Util", "Ships", "Aero", "Steel", "BldMt")


# =============================================================================
# 0. Frozen configuration
# =============================================================================
@dataclass(frozen=True)
class Config:
    """Every number the test uses. Nothing here is estimated or tuned."""
    # test window in RETURN months (inclusive); start moves later if the rule cannot fire yet
    test_start: str = "1993-01"
    test_end: str = "2009-12"
    brown: tuple = BROWN
    hedge_factors: tuple = ("Mkt-RF", "SMB", "HML")
    # team trade (validated, unchanged)
    hedge_window: int = 60
    vol_window: int = 36
    vol_target: float = 0.05
    cost_w: float = 0.0010
    cost_mkt: float = 0.0005
    cost_smb: float = 0.0025
    cost_hml: float = 0.0025
    hold_months: int = 6
    pub_lag: int = 1
    # frozen signal
    z_window: int = 60
    z_min_nonzero: int = 48
    max_zero_share: float = 0.10
    pct: float = 80.0
    min_pct_history: int = 60
    # attribution
    attr_factors: tuple = ("Mkt-RF", "SMB", "HML", "RMW", "CMA", "UMD",
                           "BOND", "WTI", "dVIX", "dlogEMV")
    interact: tuple = ("Mkt-RF", "HML", "BOND", "dVIX")
    nw_lags: int = 6
    nw_lags_check: int = 12
    # pass bars
    t_bar: float = 2.0
    p_bar: float = 0.05
    min_episodes: int = 8
    # readings of the points the spec leaves open -- see notes (a)1-(a)3
    bridge_missing: bool = True       # extreme, zero, extreme = one run (no new crossing)
    bridge_limit: int = 6             # ... unless more than 6 consecutive missing months
    end_policy: str = "truncate"      # "truncate" or "liquidate" a hold still open at test_end
    shuffle_draws: int = 5000
    shuffle_min_gap: int = 1          # shuffled episodes never touch, so K is preserved
    shuffle_recompute_pi_I: bool = True
    seed: int = 230


# =============================================================================
# Calendar / IO helpers
# =============================================================================
def _me(x) -> pd.Timestamp:
    """Month-end timestamp (midnight) of any date-like."""
    return (pd.Timestamp(x) + pd.offsets.MonthEnd(0)).normalize()


def _to_month_end(values) -> pd.DatetimeIndex:
    """Vectorised month-end mapping; FRED first-of-month dates map to the same month's end."""
    return (pd.DatetimeIndex(pd.to_datetime(values)) + pd.offsets.MonthEnd(0)).normalize()


def _month_range(a, b) -> pd.DatetimeIndex:
    return pd.date_range(_me(a), _me(b), freq=pd.offsets.MonthEnd())


def _shift_months(ts, k: int) -> pd.Timestamp:
    return (_me(ts) + pd.offsets.MonthEnd(k)).normalize()


def _position_months(window: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """Position months whose positions earn inside the window (return month t <- position t-1)."""
    return _month_range(_shift_months(window[0], -1), _shift_months(window[-1], -1))


def _assert_monthly(idx: pd.DatetimeIndex, name: str) -> None:
    if idx.has_duplicates:
        raise ValueError(f"{name}: duplicate months")
    if len(idx) != len(_month_range(idx.min(), idx.max())):
        raise ValueError(f"{name}: gaps in the monthly index")


def _assert_decimal(frame: pd.DataFrame, name: str) -> None:
    q = np.nanpercentile(np.abs(frame.to_numpy(float)), 99)
    if q > 1.0:
        raise ValueError(f"{name}: 99th pct |return| = {q:.2f}; looks like percent, not decimals")


def _read(src) -> pd.DataFrame:
    return src.copy() if isinstance(src, pd.DataFrame) else pd.read_csv(src)


def _show(title: str, obj) -> None:
    print("\n" + "=" * 100 + f"\n{title}\n" + "=" * 100)
    print(obj.to_string() if hasattr(obj, "to_string") else obj)


# =============================================================================
# 1. Loaders
# =============================================================================
def load_ff49(src) -> pd.DataFrame:
    """
    Step 1a. Fama-French 49 industries.
    Input : path or DataFrame with `date` (month-end) + 49 industry columns, monthly decimals.
    Output: DataFrame on a sorted, gap-free month-end index; NaN where an industry does not
            exist; values <= -0.99 (French's -99.99 code) set to NaN.
    Timing: row t = value-weighted return over calendar month t.
    """
    df = _read(src)
    df.columns = [str(c).strip() for c in df.columns]
    idx = _to_month_end(df.pop("date"))
    df = df.apply(pd.to_numeric, errors="coerce")
    df.index = idx
    df = df.sort_index().mask(lambda x: x <= -0.99)
    _assert_monthly(df.index, "ff49")
    _assert_decimal(df, "ff49")
    return df


def load_factors(fac: pd.DataFrame) -> pd.DataFrame:
    """
    Step 1b. French FF5 + momentum.
    Input : DataFrame with Mkt-RF, SMB, HML, RMW, CMA, RF, UMD (decimals), month-end index.
    Output: those columns on a sorted, gap-free month-end index.
    Timing: row t = return over month t.
    """
    cols = ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF", "UMD"]
    out = fac[cols].astype(float).copy()
    out.index = _to_month_end(out.index)
    out = out.sort_index()
    _assert_monthly(out.index, "fac")
    _assert_decimal(out, "fac")
    return out


def load_fred_monthly(src, series_id: str) -> pd.Series:
    """
    Step 1c. Monthly FRED series (EMV trackers, GS10, MCOILWTICO).
    Input : path or DataFrame with `observation_date` (first of month) and `series_id`.
    Output: Series on a complete month-end index; '.'/blank -> NaN; exact zeros kept.
    Timing: the value dated month t describes month t (publication lag handled downstream).
    """
    df = _read(src)
    s = pd.Series(pd.to_numeric(df[series_id], errors="coerce").to_numpy(float),
                  index=_to_month_end(df["observation_date"]), name=series_id).sort_index()
    if s.index.has_duplicates:
        raise ValueError(f"{series_id}: more than one observation per month")
    return s.reindex(_month_range(s.index.min(), s.index.max()))


def load_vix_monthly(src, series_id: str = "VIXCLS") -> pd.Series:
    """
    Step 1d. Monthly mean of daily VIX closes.
    Input : path or DataFrame with daily `observation_date` and VIXCLS (blank on holidays).
    Output: Series on a complete month-end index = mean of the non-missing closes in month t.
    Timing: known at the end of month t.
    """
    df = _read(src)
    d = pd.Series(pd.to_numeric(df[series_id], errors="coerce").to_numpy(float),
                  index=pd.DatetimeIndex(pd.to_datetime(df["observation_date"]))).dropna()
    m = d.groupby(_to_month_end(d.index)).mean()
    m.index = pd.DatetimeIndex(m.index)
    return m.reindex(_month_range(m.index.min(), m.index.max())).rename("VIX")


# =============================================================================
# 2-4. Brown leg, hedge, sizing
# =============================================================================
def brown_leg(ff49: pd.DataFrame, rf: pd.Series, industries) -> pd.Series:
    """
    Step 2. Brown leg.
    Inputs : industry returns, RF, list of Brown industries.
    Output : R^B_t = equal-weighted mean of the listed industries available in t, minus RF_t.
    Timing : month-t return.
    """
    missing = [c for c in industries if c not in ff49.columns]
    if missing:
        raise KeyError(f"industries not found in FF49 file: {missing}")
    leg = ff49[list(industries)].mean(axis=1, skipna=True)
    return (leg - rf.reindex(leg.index)).rename("RB")


def rolling_hedge(rb: pd.Series, f: pd.DataFrame, window: int = 60):
    """
    Step 3. Rolling factor hedge.
    Inputs : R^B_t and hedge factors f_t = (Mkt-RF, SMB, HML) on the same complete index.
    Output : a (Series) and b (DataFrame, columns = f.columns).
    Timing : (a_t, b_t) = OLS of R^B on [1, f] over months t-window+1..t, i.e. data through t,
             known at the end of t. NaN unless all `window` months are complete.
    """
    idx = rb.index
    X = np.column_stack([np.ones(len(idx)), f.reindex(idx).to_numpy(float)])
    y = rb.to_numpy(float)
    coef = np.full((len(idx), X.shape[1]), np.nan)
    for i in range(window - 1, len(idx)):
        Xi, yi = X[i - window + 1:i + 1], y[i - window + 1:i + 1]
        if np.isfinite(Xi).all() and np.isfinite(yi).all():
            coef[i] = np.linalg.lstsq(Xi, yi, rcond=None)[0]
    a = pd.Series(coef[:, 0], index=idx, name="a")
    b = pd.DataFrame(coef[:, 1:], index=idx, columns=list(f.columns))
    return a, b


def hedge_residual_and_size(rb: pd.Series, f: pd.DataFrame, a: pd.Series, b: pd.DataFrame,
                            cfg: Config):
    """
    Step 4. Out-of-sample residual and position size.
    Inputs : R^B, f, (a, b) from step 3.
    Output : e_t = R^B_t - a_{t-1} - b_{t-1}'f_t;
             sd_t = std(e_{t-35..t}, ddof=1), all 36 required;
             m_t = min(1, vol_target / (sqrt(12) sd_t)).
    Timing : e_t, sd_t, m_t use data through t, known at the end of t.
    """
    fitted = a.shift(1) + (b.shift(1) * f[b.columns]).sum(axis=1, min_count=b.shape[1])
    e = (rb - fitted).rename("e")
    sd = e.rolling(cfg.vol_window, min_periods=cfg.vol_window).std(ddof=1).rename("sd")
    m = np.minimum(1.0, cfg.vol_target / (np.sqrt(12.0) * sd)).rename("m")
    return e, sd, m


# =============================================================================
# 5-7. Signal, crossings, hold
# =============================================================================
def attention_signal(emv_cat: pd.Series, emv_all: pd.Series, cfg: Config) -> pd.DataFrame:
    """
    Step 5. Frozen signal, indexed by SIGNAL month tau.
    Inputs : EMVENRGYENVREG and EMVOVERALLEMV (monthly, month-end index).
    Output : DataFrame with
        s            EMVENRGYENVREG / EMVOVERALLEMV
        missing      s is zero (or NaN): missing, never "low attention"
        n_missing60  missing months in tau-59..tau (NaN until 60 calendar months exist)
        off          month is nonzero but > 10% of the trailing 60 months are missing
        z            (log s_tau - mean) / sd over the NONZERO months of tau-59..tau
                     (needs >= 48 nonzero and <= 6 missing; NaN otherwise)
        thr          80th percentile of all valid z strictly before tau (needs >= 60)
        extreme      1 if z > thr, 0 if not, NaN if z or thr undefined
    Timing : row tau uses data dated <= tau only, but tau's data are published at the end of
             tau+1, so row tau may drive a position no earlier than the end of tau+pub_lag.
             Missing months are dropped from the z window and the percentile history.
    """
    start = max(emv_cat.first_valid_index(), emv_all.first_valid_index())
    end = min(emv_cat.last_valid_index(), emv_all.last_valid_index())
    idx = _month_range(start, end)
    s = emv_cat.reindex(idx) / emv_all.reindex(idx)
    missing = ~(s > 0)                                   # exact zero or NaN
    W = cfg.z_window
    max_missing = int(np.floor(cfg.max_zero_share * W + 1e-9))   # = 6
    logs = np.log(s.where(~missing))
    n_miss = missing.astype(float).rolling(W, min_periods=W).sum()
    n_nz = W - n_miss
    mu = logs.rolling(W, min_periods=cfg.z_min_nonzero).mean()
    sd = logs.rolling(W, min_periods=cfg.z_min_nonzero).std(ddof=1)
    ok = (~missing) & (n_nz >= cfg.z_min_nonzero) & (n_miss <= max_missing) & (sd > 0)
    z = ((logs - mu) / sd).where(ok)

    zv = z.to_numpy(float)
    thr = np.full(len(zv), np.nan)
    hist: list = []
    for i, zi in enumerate(zv):
        if len(hist) >= cfg.min_pct_history:
            thr[i] = np.percentile(hist, cfg.pct)        # past-only: z_tau not yet appended
        if np.isfinite(zi):
            hist.append(zi)
    defined = np.isfinite(zv) & np.isfinite(thr)
    extreme = np.where(defined, (np.nan_to_num(zv) > np.nan_to_num(thr)).astype(float), np.nan)

    return pd.DataFrame({
        "s": s, "missing": missing, "n_missing60": n_miss,
        "off": (~missing) & (n_miss > max_missing),
        "z": z, "thr": thr, "extreme": extreme}, index=idx)


def crossings(extreme: pd.Series, cfg: Config) -> pd.Series:
    """
    Step 6. Crossings.
    Input  : extreme flag (1/0/NaN) by signal month.
    Output : bool Series, True in signal month tau if extreme_tau == 1 and the previous month
             was not extreme. With bridge_missing, a missing flag (zero or off month) carries
             the last defined flag forward for up to bridge_limit months, so
             extreme -> zero -> extreme is ONE run. Undefined previous state = not extreme.
    Timing : uses flags dated <= tau; usable at the end of tau+pub_lag.
    """
    prev = extreme.ffill(limit=cfg.bridge_limit) if cfg.bridge_missing else extreme
    prev = prev.shift(1)
    return ((extreme == 1) & (prev != 1)).rename("crossing")


def hold_positions(cross: pd.Series, index: pd.DatetimeIndex, cfg: Config) -> pd.Series:
    """
    Step 7. Hold state in position time.
    Inputs : crossings (signal time) and the master monthly index.
    Output : bool Series on `index`; True = a short position is SET at the end of month t.
    Timing : hold in signal time covers tau..tau+5 after each crossing (a new crossing extends,
             positions never stack); with the publication lag the hold at the end of t uses
             signal month t-1: hold_pos_t = hold_sig_{t-pub_lag}. So a crossing in tau gives
             positions set at the end of tau+1..tau+6, earning tau+2..tau+7.
    """
    c = cross.reindex(index, fill_value=False).astype(float)
    hold_sig = c.rolling(cfg.hold_months, min_periods=1).max() > 0
    return hold_sig.shift(cfg.pub_lag, fill_value=False).astype(bool).rename("hold")


# =============================================================================
# 8. Trade engine (timed and always-on)
# =============================================================================
def run_trade(rb: pd.Series, f: pd.DataFrame, b: pd.DataFrame, m: pd.Series,
              hold: pd.Series, cfg: Config) -> pd.DataFrame:
    """
    Step 8. Team trade.
    Inputs : R^B_t, hedge factors, b_t, m_t, hold (bool, set at end of t).
    Output : DataFrame on rb.index:
             hold, m, w (w_t = -m_t if hold else 0, set at end of t),
             h_<factor> (overlay = -w_t b_t, set at end of t), trade_cost (trade at end of t),
             w_prev = w_{t-1}, hedged_t = R^B_t - b_{t-1}'f_t, gross_t = w_{t-1} hedged_t,
             cost_t = trade_cost_{t-1} (paid in t), net_t = gross_t - cost_t.
    Timing : row t's net return is earned in month t by the position set at the end of t-1.
    """
    idx = rb.index
    hf = list(cfg.hedge_factors)
    f = f.reindex(idx)[hf]
    b = b.reindex(idx)[hf]
    hold = hold.reindex(idx, fill_value=False).astype(bool)
    mv = m.reindex(idx).to_numpy(float)
    w = np.where(hold.to_numpy(), -mv, 0.0)
    bv = b.to_numpy(float)
    h = np.where(w[:, None] == 0.0, 0.0, -w[:, None] * bv)
    dw = np.abs(np.diff(w, prepend=0.0))
    dh = np.abs(np.diff(h, axis=0, prepend=np.zeros((1, h.shape[1]))))
    unit = np.array([cfg.cost_mkt, cfg.cost_smb, cfg.cost_hml])
    trade_cost = cfg.cost_w * dw + dh @ unit

    out = pd.DataFrame({"hold": hold, "m": mv, "w": w}, index=idx)
    for j, c in enumerate(hf):
        out[f"h_{c}"] = h[:, j]
    out["trade_cost"] = trade_cost
    out["w_prev"] = out["w"].shift(1)
    out["hedged"] = rb - (b.shift(1) * f).sum(axis=1, min_count=len(hf))
    out["gross"] = out["w_prev"] * out["hedged"]
    out["cost"] = out["trade_cost"].shift(1)
    out["net"] = out["gross"] - out["cost"]
    return out


def leg_pipeline(ff49: pd.DataFrame, fac: pd.DataFrame, industries, hold: pd.Series,
                 index: pd.DatetimeIndex, cfg: Config) -> dict:
    """
    Steps 2-4 + 8 for one set of Brown industries (used for the main run and for each
    leave-one-out rebuild).
    Output : dict with rb, f, a, b, e, sd, m, tr_T (timed book), tr_AO (always-on book).
    Timing : as in steps 2-4 and 8; the hold series is taken as given.
    """
    f = fac.reindex(index)[list(cfg.hedge_factors)]
    rb = brown_leg(ff49.reindex(index), fac["RF"].reindex(index), industries)
    a, b = rolling_hedge(rb, f, cfg.hedge_window)
    e, sd, m = hedge_residual_and_size(rb, f, a, b, cfg)
    tr_T = run_trade(rb, f, b, m, hold, cfg)
    tr_AO = run_trade(rb, f, b, m, pd.Series(True, index=index), cfg)
    return dict(rb=rb, f=f, a=a, b=b, e=e, sd=sd, m=m, tr_T=tr_T, tr_AO=tr_AO)


# =============================================================================
# 9-10. Attribution regressors
# =============================================================================
def par_bond_duration_convexity(y, maturity: float = 10.0, freq: int = 2):
    """
    Step 9a. Modified duration (years) and convexity (years^2) of a par bond.
    Input : annual yield(s) y in decimals, semiannual compounding and coupons.
    Output: (D, C) arrays, from exact cash flows.
    """
    y = np.asarray(y, dtype=float).reshape(-1, 1)
    n = int(round(maturity * freq))
    i = np.arange(1, n + 1, dtype=float)[None, :]
    g = 1.0 + y / freq
    cf = np.repeat(y / freq, n, axis=1)
    cf[:, -1] += 1.0
    disc = g ** (-i)
    price = (cf * disc).sum(axis=1)
    dur = (cf * (i / freq) * disc).sum(axis=1) / g[:, 0] / price
    conv = (cf * (i / freq) * ((i + 1) / freq) * disc).sum(axis=1) / g[:, 0] ** 2 / price
    return dur, conv


def bond_excess_return(gs10: pd.Series, rf: pd.Series) -> pd.Series:
    """
    Step 9b. BOND_t = y_{t-1}/12 - D_{t-1} dy_t + 0.5 C_{t-1} dy_t^2 - RF_t,
    y = GS10/100, dy_t = y_t - y_{t-1}, D and C of a 10y semiannual par bond at y_{t-1}.
    Timing: month-t excess return (contemporaneous regressor).
    """
    y = (gs10 / 100.0).astype(float)
    y_prev = y.shift(1)
    dy = y - y_prev
    dur, conv = par_bond_duration_convexity(y_prev.to_numpy())
    r = y_prev / 12.0 - dur * dy + 0.5 * conv * dy ** 2
    return (r - rf.reindex(r.index)).rename("BOND")


def attribution_factors(fac: pd.DataFrame, bond: pd.Series, wti: pd.Series, vix_m: pd.Series,
                        emv_all: pd.Series, index: pd.DatetimeIndex) -> pd.DataFrame:
    """
    Step 10. Month-t regressors, contemporaneous by design (NOT lagged):
    FF5 + UMD, BOND_t, WTI_t = log(P_t / P_{t-1}), dVIX_t = VIXbar_t - VIXbar_{t-1},
    dlogEMV_t = log EMVOVERALLEMV_t - log EMVOVERALLEMV_{t-1}.
    All differences are taken on complete monthly calendars before reindexing.
    """
    F = fac.reindex(index)[["Mkt-RF", "SMB", "HML", "RMW", "CMA", "UMD"]].copy()
    F["BOND"] = bond.reindex(index)
    F["WTI"] = np.log(wti).diff().reindex(index)
    F["dVIX"] = vix_m.diff().reindex(index)
    F["dlogEMV"] = np.log(emv_all).diff().reindex(index)
    return F


# =============================================================================
# 11. Window, timing difference D
# =============================================================================
def test_window(sig: pd.DataFrame, index: pd.DatetimeIndex, cfg: Config):
    """
    Step 11a. Test window.
    Output : (first_signal, first_position, first_return, window).
             first_signal   = first signal month with a defined flag (valid z, >= 60 prior z)
             first_position = first month-end a position can be set = first_signal + pub_lag
             first_return   = first return month that position affects = first_position + 1
             window         = RETURN months [max(test_start, first_return), test_end]
    """
    elig = sig["extreme"].dropna()
    if elig.empty:
        raise ValueError("the signal never produces a defined flag")
    first_sig = elig.index[0]
    first_pos = _shift_months(first_sig, cfg.pub_lag)
    first_ret = _shift_months(first_pos, 1)
    start, end = max(_me(cfg.test_start), first_ret), _me(cfg.test_end)
    if end > index[-1] or start > end:
        raise ValueError(f"window {start:%Y-%m}..{end:%Y-%m} not covered by the data")
    return first_sig, first_pos, first_ret, _month_range(start, end)


def _liquidation_cost(tr: pd.DataFrame, t_end: pd.Timestamp, cfg: Config) -> float:
    """Cost of closing, at the end of t_end, the book set at the end of t_end - 1."""
    prev = _shift_months(t_end, -1)
    h = np.abs(tr.loc[prev, [f"h_{c}" for c in cfg.hedge_factors]].to_numpy(float))
    unit = np.array([cfg.cost_mkt, cfg.cost_smb, cfg.cost_hml])
    return float(cfg.cost_w * abs(tr.loc[prev, "w"]) + h @ unit)


def timing_difference(tr_T: pd.DataFrame, tr_AO: pd.DataFrame, window: pd.DatetimeIndex,
                      cfg: Config, pi: float | None = None):
    """
    Step 11b. D_t = R^T_t - pi R^AO_t over the window's return months, net of costs.
    pi = mean|w^T_{t-1}| / mean|w^AO_{t-1}| over the same months (positions that earn there),
    unless pi is passed in. end_policy="liquidate" charges both books' closing cost in the last
    window month; "truncate" does not (that trade would be paid after the window).
    Output : D (Series), pi (float), I_prev (0/1: position held entering month t).
    """
    T, A = tr_T.loc[window], tr_AO.loc[window]
    cols = ["w_prev", "gross", "cost", "net"]
    if not (np.isfinite(T[cols].to_numpy(float)).all() and np.isfinite(A[cols].to_numpy(float)).all()):
        raise ValueError("non-finite strategy values inside the test window")
    if pi is None:
        pi = T["w_prev"].abs().mean() / A["w_prev"].abs().mean()
    RT, RA = T["net"].copy(), A["net"].copy()
    if cfg.end_policy == "liquidate":
        RT.iloc[-1] -= _liquidation_cost(tr_T, window[-1], cfg)
        RA.iloc[-1] -= _liquidation_cost(tr_AO, window[-1], cfg)
    elif cfg.end_policy != "truncate":
        raise ValueError(f"unknown end_policy {cfg.end_policy}")
    D = (RT - pi * RA).rename("D")
    I_prev = tr_T["hold"].shift(1, fill_value=False).loc[window].astype(float).rename("I_prev")
    return D, float(pi), I_prev


# =============================================================================
# 12. Attribution regression and decomposition
# =============================================================================
def design_matrix(F: pd.DataFrame, I_prev: pd.Series, cfg: Config) -> pd.DataFrame:
    """
    Step 12a. X_t = [const, FF5+UMD, BOND, WTI, dVIX, dlogEMV, I_{t-1} x {Mkt-RF, HML, BOND, dVIX}].
    No I_{t-1} main effect (the spec lists only the interactions). k = X.shape[1] = 15.
    """
    F = F.loc[I_prev.index, list(cfg.attr_factors)]
    X = F.copy()
    for c in cfg.interact:
        X[f"I*{c}"] = I_prev.to_numpy() * F[c].to_numpy()
    return sm.add_constant(X, has_constant="add")


def attribution_regression(D: pd.Series, X: pd.DataFrame, cfg: Config):
    """
    Step 12b. OLS of D on X; Newey-West (Bartlett) HAC with nw_lags and nw_lags_check.
    use_t=True -> t statistics and p-values from t(n-k), k counted from X.
    Output : coefficient table, NW(6) fit, NW(12) fit. Raises on missing data or rank deficiency.
    """
    bad = X.isna().any(axis=1) | D.isna()
    if bad.any():
        raise ValueError(f"missing regressors/returns in {list(X.index[bad.to_numpy()].strftime('%Y-%m'))}")
    if np.linalg.matrix_rank(X.to_numpy(float)) < X.shape[1]:
        raise ValueError("design matrix is rank deficient (e.g. I_{t-1} never or always 1)")
    f6 = sm.OLS(D, X).fit(cov_type="HAC", cov_kwds={"maxlags": cfg.nw_lags}, use_t=True)
    f12 = sm.OLS(D, X).fit(cov_type="HAC", cov_kwds={"maxlags": cfg.nw_lags_check}, use_t=True)
    n, k = X.shape
    if int(round(f6.df_resid)) != n - k:
        raise RuntimeError("df_resid != n - k")
    tab = pd.DataFrame({
        "coef": f6.params,
        f"t NW({cfg.nw_lags})": f6.tvalues,
        f"p NW({cfg.nw_lags})": f6.pvalues,
        f"t NW({cfg.nw_lags_check})": f12.tvalues,
        f"p NW({cfg.nw_lags_check})": f12.pvalues,
    }).rename(index={"const": "alpha"})
    return tab, f6, f12


def decompose_mean(D: pd.Series, X: pd.DataFrame, fit) -> pd.DataFrame:
    """
    Step 12c. mean(D) = alpha + sum beta_j mean(F_j) + sum gamma_j mean(I F_j).
    Exact for OLS with a constant (residuals sum to zero); the gap is reported.
    """
    contrib = fit.params * X.mean()
    rows = {"mean(D)": D.mean(), "alpha": contrib["const"]}
    for c in X.columns.drop("const"):
        rows[f"gamma*mean({c})" if c.startswith("I*") else f"beta*mean({c})"] = contrib[c]
    rows["sum of terms"] = contrib.sum()
    rows["identity gap"] = D.mean() - contrib.sum()
    return pd.Series(rows, name="value").to_frame()


# =============================================================================
# 13. Episodes and crossings
# =============================================================================
def hold_episodes(hold: pd.Series, pos_months: pd.DatetimeIndex) -> pd.DataFrame:
    """
    Step 13a. Independent episodes.
    Inputs : hold (bool, position time) and the position months that earn inside the window.
    Output : one row per maximal run of consecutive hold months (holds that touch or overlap
             merge), with position/return dates and whether the run was already open before,
             or is still open after, the window.
    """
    cols = ["position_from", "position_to", "months", "return_from", "return_to",
            "open_before_window", "open_after_window"]
    h = hold.reindex(pos_months, fill_value=False).to_numpy(bool)
    before = bool(hold.get(_shift_months(pos_months[0], -1), False))
    after = bool(hold.get(_shift_months(pos_months[-1], 1), False))
    rows, i = [], 0
    while i < len(h):
        if not h[i]:
            i += 1
            continue
        j = i
        while j + 1 < len(h) and h[j + 1]:
            j += 1
        rows.append({"position_from": pos_months[i], "position_to": pos_months[j],
                     "months": j - i + 1,
                     "return_from": _shift_months(pos_months[i], 1),
                     "return_to": _shift_months(pos_months[j], 1),
                     "open_before_window": i == 0 and before,
                     "open_after_window": j == len(h) - 1 and after})
        i = j + 1
    return pd.DataFrame(rows, columns=cols)


def crossing_table(sig: pd.DataFrame, cross: pd.Series, pos_months: pd.DatetimeIndex,
                   cfg: Config) -> pd.DataFrame:
    """
    Step 13b. Crossings whose hold overlaps the window's position months.
    Signal month tau -> positions set at the end of tau+pub_lag .. tau+pub_lag+hold_months-1.
    """
    cols = ["signal_month", "z", "threshold", "position_from", "position_to"]
    rows = []
    for tau in cross.index[cross.to_numpy(bool)]:
        p0 = _shift_months(tau, cfg.pub_lag)
        p1 = _shift_months(p0, cfg.hold_months - 1)
        if p1 < pos_months[0] or p0 > pos_months[-1]:
            continue
        rows.append({"signal_month": tau, "z": sig.at[tau, "z"], "threshold": sig.at[tau, "thr"],
                     "position_from": p0, "position_to": p1})
    return pd.DataFrame(rows, columns=cols)


def diagnostics_summary(sig, hold, leg, ff49, window, first_sig, first_pos, first_ret,
                        eps, xtab, pi, cfg: Config) -> pd.DataFrame:
    """
    Step 13c. Key facts about the run: fire dates, zero counts, hold months, pi, settings.
    Signal months "feeding" the window = the latest flags available at each position month.
    """
    pos_months = _position_months(window)
    sig_months = _month_range(_shift_months(pos_months[0], -cfg.pub_lag),
                              _shift_months(pos_months[-1], -cfg.pub_lag))
    sw = sig.reindex(sig_months)
    trw = leg["tr_T"].loc[pos_months]
    hist = _month_range(_shift_months(window[0], -(cfg.hedge_window + cfg.vol_window + 1)), window[-1])
    n_brown = int(ff49.reindex(hist)[list(cfg.brown)].notna().sum(axis=1).min())
    info = {
        "first signal month with a defined flag": f"{first_sig:%Y-%m}",
        "first month a position can be set (end of)": f"{first_pos:%Y-%m}",
        "first return month the rule can affect": f"{first_ret:%Y-%m}",
        "test window (return months)": f"{window[0]:%Y-%m} to {window[-1]:%Y-%m}",
        "n return months": len(window),
        "EMVENRGYENVREG zero months, whole file": int((sig["s"] == 0).sum()),
        "signal months feeding the window": f"{sig_months[0]:%Y-%m} to {sig_months[-1]:%Y-%m}",
        "  zero months among them": int((sw["s"] == 0).sum()),
        "  signal-off months (>10% zeros in trailing 60)": int(sw["off"].eq(True).sum()),
        "  months with a defined flag": int(sw["extreme"].notna().sum()),
        "  extreme months": int((sw["extreme"] == 1).sum()),
        "crossings affecting the window": len(xtab),
        "hold months (position months in window)": int(trw["hold"].sum()),
        "independent episodes": len(eps),
        "pi": pi,
        "mean m_t in hold months": float(trw.loc[trw["hold"], "m"].mean()) if trw["hold"].any() else np.nan,
        "min # Brown industries available (hedge history + window)": n_brown,
    }
    info.update({f"cfg.{k}": v for k, v in asdict(cfg).items()})
    return pd.Series(info, name="value").to_frame()


# =============================================================================
# 14. Calendar shuffle
# =============================================================================
def place_blocks(lengths, n: int, min_gap: int, rng: np.random.Generator) -> np.ndarray:
    """
    Step 14a. Uniform random placement of blocks with the given lengths in n slots, in random
    order, with >= min_gap empty slots between consecutive blocks (stars and bars).
    Output: bool array of length n.
    """
    lengths = np.asarray(lengths, dtype=int)
    K = len(lengths)
    free = n - int(lengths.sum()) - min_gap * (K - 1)
    if free < 0:
        raise ValueError("episodes do not fit in the window with the required gaps")
    lens = lengths[rng.permutation(K)]
    slots = np.sort(rng.choice(free + K, size=K, replace=False))
    starts = (slots - np.arange(K)
              + np.concatenate(([0], np.cumsum(lens)[:-1]))
              + min_gap * np.arange(K))
    out = np.zeros(n, dtype=bool)
    for s, L in zip(starts, lens):
        out[s:s + L] = True
    return out


def calendar_shuffle(alpha_actual: float, leg: dict, hold: pd.Series, F: pd.DataFrame,
                     window: pd.DatetimeIndex, pi_actual: float, I_actual: pd.Series,
                     cfg: Config):
    """
    Step 14b. Calendar-shuffle null.
    Inputs : actual alpha, the Brown pipeline `leg`, actual hold (position time), regressors,
             window, actual pi and I (used only if shuffle_recompute_pi_I is False).
    Method : the K actual episodes (maximal hold runs among the position months that earn in
             the window) are placed at random (place_blocks) inside those position months;
             months before the window keep their actual state. Each draw rebuilds the timed
             book (w, overlay, costs); pi and I_{t-1} are recomputed if shuffle_recompute_pi_I;
             alpha is re-estimated by OLS (point estimate only).
    Output : (summary table, array of null alphas);
             p = (1 + #{alpha_null >= alpha_actual}) / (1 + draws), one-sided.
    """
    pos_months = _position_months(window)
    lengths = hold_episodes(hold, pos_months)["months"].to_numpy(int)
    if len(lengths) == 0:
        raise ValueError("no episodes to shuffle")
    loc = hold.index.get_indexer(pos_months)
    if (loc < 0).any():
        raise ValueError("position months outside the hold index")
    rng = np.random.default_rng(cfg.seed)
    base = hold.to_numpy(bool)
    Fw = F.loc[window]
    null = np.empty(cfg.shuffle_draws)
    for d in range(cfg.shuffle_draws):
        hv = base.copy()
        hv[loc] = place_blocks(lengths, len(pos_months), cfg.shuffle_min_gap, rng)
        tr = run_trade(leg["rb"], leg["f"], leg["b"], leg["m"], pd.Series(hv, index=hold.index), cfg)
        if cfg.shuffle_recompute_pi_I:
            D, _, I = timing_difference(tr, leg["tr_AO"], window, cfg)
        else:
            D, _, _ = timing_difference(tr, leg["tr_AO"], window, cfg, pi=pi_actual)
            I = I_actual
        X = design_matrix(Fw, I, cfg).to_numpy(float)
        null[d] = np.linalg.lstsq(X, D.to_numpy(float), rcond=None)[0][0]
    p = (1 + np.sum(null >= alpha_actual)) / (1 + cfg.shuffle_draws)
    q = [0.01, 0.05, 0.10, 0.50, 0.90, 0.95, 0.99]
    vals = ([alpha_actual, null.mean(), null.std(ddof=1)] + list(np.quantile(null, q))
            + [p, cfg.shuffle_draws, len(lengths), int(lengths.sum()), cfg.seed])
    names = (["actual alpha", "null mean", "null sd"] + [f"null q{int(round(x * 100)):02d}" for x in q]
             + ["p (one-sided)", "draws", "episodes K", "hold months", "seed"])
    return pd.DataFrame({"value": vals}, index=names), null


# =============================================================================
# 15. Leave one industry out
# =============================================================================
def leave_one_out(ff49: pd.DataFrame, fac: pd.DataFrame, hold: pd.Series, F: pd.DataFrame,
                  window: pd.DatetimeIndex, index: pd.DatetimeIndex, alpha_full: float,
                  cfg: Config) -> pd.DataFrame:
    """
    Step 15. Drop each Brown industry in turn; rebuild leg, hedge, sizing, timed and always-on
    books, pi and D; refit the attribution. Hold timing is unchanged (the signal does not use
    returns). Output: one row per dropped industry with alpha, NW(6) t, p, pi, same_sign.
    """
    rows = []
    for drop in cfg.brown:
        keep = tuple(c for c in cfg.brown if c != drop)
        leg = leg_pipeline(ff49, fac, keep, hold, index, cfg)
        D, pi, I = timing_difference(leg["tr_T"], leg["tr_AO"], window, cfg)
        _, f6, _ = attribution_regression(D, design_matrix(F, I, cfg), cfg)
        a = float(f6.params["const"])
        rows.append({"dropped": drop, "alpha": a, f"t NW({cfg.nw_lags})": float(f6.tvalues["const"]),
                     "p": float(f6.pvalues["const"]), "pi": pi,
                     "same_sign": bool(np.sign(a) == np.sign(alpha_full))})
    return pd.DataFrame(rows)


# =============================================================================
# 16. Pass / fail
# =============================================================================
def pass_fail_table(f6, shuffle_p: float, n_episodes: int, loo: pd.DataFrame, cfg: Config):
    """
    Step 16. All four components required.
    Output : (table with one row per component + OVERALL, verdict "PASS"/"FAIL").
    """
    a, t, p = float(f6.params["const"]), float(f6.tvalues["const"]), float(f6.pvalues["const"])
    p1 = p / 2 if t > 0 else 1 - p / 2
    same, nl = int(loo["same_sign"].sum()), len(loo)
    rows = [
        ["(i) timing alpha", f"alpha/month, NW({cfg.nw_lags}) t, p from t(n-k)",
         f"alpha > 0 and t >= {cfg.t_bar:g}",
         f"alpha={a:.6f}, t={t:.3f}, p2={p:.4f}, p1={p1:.4f}", bool(a > 0 and t >= cfg.t_bar)],
        ["(ii) calendar shuffle", f"one-sided p, {cfg.shuffle_draws} draws", f"p <= {cfg.p_bar:g}",
         f"{shuffle_p:.4f}", bool(shuffle_p <= cfg.p_bar)],
        ["(iii) independent episodes", "merged hold runs in window", f">= {cfg.min_episodes}",
         str(n_episodes), bool(n_episodes >= cfg.min_episodes)],
        ["(iv) leave one industry out", "LOO alphas with the full alpha's sign", f"{nl}/{nl}",
         f"{same}/{nl}", bool(same == nl)],
    ]
    n_pass = sum(r[4] for r in rows)
    tab = pd.DataFrame(rows, columns=["component", "statistic", "bar", "value", "pass"])
    tab["pass"] = np.where(tab["pass"].astype(bool), "PASS", "FAIL")
    verdict = "PASS" if n_pass == 4 else "FAIL"
    tab.loc[len(tab)] = ["OVERALL", "all four required", "4/4", f"{n_pass}/4", verdict]
    return tab, verdict


# =============================================================================
# 17. Run
# =============================================================================
def run_backtest(inputs: dict, cfg: Config = Config(), verbose: bool = True) -> dict:
    """
    Step 17. Runs steps 1-16 once; returns and prints the five outputs.
    inputs: ff49 (path/DataFrame), fac (DataFrame), emv_cat, emv_all, gs10, wti, vix
            (FRED CSV paths, or DataFrames in the FRED CSV layout).
    """
    ff49 = load_ff49(inputs["ff49"])
    fac = load_factors(inputs["fac"])
    emv_cat = load_fred_monthly(inputs["emv_cat"], "EMVENRGYENVREG")
    emv_all = load_fred_monthly(inputs["emv_all"], "EMVOVERALLEMV")
    gs10 = load_fred_monthly(inputs["gs10"], "GS10")
    wti = load_fred_monthly(inputs["wti"], "MCOILWTICO")
    vix = load_vix_monthly(inputs["vix"], "VIXCLS")
    index = _month_range(fac.index.min(), min(fac.index.max(), ff49.index.max()))

    # signal and hold: independent of the Brown leg
    sig = attention_signal(emv_cat, emv_all, cfg)
    cross = crossings(sig["extreme"], cfg)
    hold = hold_positions(cross, index, cfg)
    first_sig, first_pos, first_ret, window = test_window(sig, index, cfg)
    pos_months = _position_months(window)
    eps = hold_episodes(hold, pos_months)
    xtab = crossing_table(sig, cross, pos_months, cfg)

    # books, D, regressors
    leg = leg_pipeline(ff49, fac, cfg.brown, hold, index, cfg)
    D, pi, I_prev = timing_difference(leg["tr_T"], leg["tr_AO"], window, cfg)
    bond = bond_excess_return(gs10, fac["RF"])
    F = attribution_factors(fac, bond, wti, vix, emv_all, index).loc[window]
    summary = diagnostics_summary(sig, hold, leg, ff49, window, first_sig, first_pos, first_ret,
                                  eps, xtab, pi, cfg)

    if eps.empty:
        pf = pd.DataFrame([["(iii) independent episodes", "merged hold runs in window",
                            f">= {cfg.min_episodes}", "0", "FAIL"],
                           ["OVERALL", "all four required", "4/4", "-", "FAIL (no position in window)"]],
                          columns=["component", "statistic", "bar", "value", "pass"])
        if verbose:
            _show("1. PASS / FAIL", pf)
            _show("4a. DIAGNOSTICS", summary)
        return {"pass_fail": pf, "verdict": "FAIL", "diagnostics": summary,
                "crossings": xtab, "episodes": eps}

    X = design_matrix(F, I_prev, cfg)
    coef, f6, f12 = attribution_regression(D, X, cfg)
    alpha = float(f6.params["const"])
    alpha_ls = np.linalg.lstsq(X.to_numpy(float), D.to_numpy(float), rcond=None)[0][0]
    if abs(alpha_ls - alpha) > 1e-10:
        raise RuntimeError("shuffle alpha path disagrees with statsmodels")
    n, k = X.shape
    meta = pd.Series({"n": n, "k": k, "n - k": n - k, "R-squared": f6.rsquared,
                      "adj. R-squared": f6.rsquared_adj, "pi": pi,
                      "window start": f"{window[0]:%Y-%m}", "window end": f"{window[-1]:%Y-%m}",
                      "HAC": f"Bartlett, maxlags {cfg.nw_lags} ({cfg.nw_lags_check} check), no small-sample corr."},
                     name="value").to_frame()
    decomp = decompose_mean(D, X, f6)

    shuf, null = calendar_shuffle(alpha, leg, hold, F, window, pi, I_prev, cfg)
    loo = leave_one_out(ff49, fac, hold, F, window, index, alpha, cfg)
    pf, verdict = pass_fail_table(f6, float(shuf.at["p (one-sided)", "value"]), len(eps), loo, cfg)

    if verbose:
        _show("1. PASS / FAIL", pf)
        _show("2a. ATTRIBUTION (D_t on FF5+UMD, BOND, WTI, dVIX, dlogEMV, I_{t-1} x F)", coef)
        _show("2b. REGRESSION FACTS", meta)
        _show("3. DECOMPOSITION OF mean(D)", decomp)
        _show("4a. DIAGNOSTICS", summary)
        _show("4b. CROSSINGS AFFECTING THE WINDOW", xtab)
        _show("4c. EPISODES", eps)
        _show("4d. LEAVE ONE INDUSTRY OUT", loo)
        _show("5. CALENDAR SHUFFLE", shuf)

    return {"pass_fail": pf, "verdict": verdict, "attribution": coef, "attribution_meta": meta,
            "decomposition": decomp, "diagnostics": summary, "crossings": xtab, "episodes": eps,
            "leave_one_out": loo, "shuffle": shuf, "null_alphas": null,
            "D": D, "X": X, "hold": hold, "signal": sig, "fit_nw6": f6, "fit_nw12": f12}


# =============================================================================
# 18. Pre-run checks: synthetic data, look-ahead test, planted effect
# =============================================================================
def make_synthetic_inputs(seed: int = 0, end: str = "2025-12") -> dict:
    """
    Debug data only: random inputs in exactly the raw layouts run_backtest expects.
    No effect is planted (use plant_timing_effect for a positive control).
    """
    rng = np.random.default_rng(seed)
    idx = _month_range("1926-07", end)
    n = len(idx)
    mkt, smb, hml = rng.normal(0.006, 0.045, n), rng.normal(0.002, 0.03, n), rng.normal(0.003, 0.03, n)
    rmw, cma, umd = rng.normal(0.003, 0.02, n), rng.normal(0.003, 0.02, n), rng.normal(0.006, 0.04, n)
    rf = np.full(n, 0.003)
    names = list(BROWN) + [f"Ind{i:02d}" for i in range(1, 45)]
    beta_m, beta_h = rng.uniform(0.6, 1.4, 49), rng.normal(0.0, 0.5, 49)
    ind = rf[:, None] + mkt[:, None] * beta_m + hml[:, None] * beta_h + rng.normal(0.0, 0.04, (n, 49))
    ff49 = pd.DataFrame(ind, columns=names)
    ff49.loc[idx < _me("1970-01"), "Ind44"] = np.nan              # an industry that starts late
    ff49.insert(0, "date", idx.strftime("%Y-%m-%d"))
    fac = pd.DataFrame({"Mkt-RF": mkt, "SMB": smb, "HML": hml, "RMW": rmw, "CMA": cma,
                        "RF": rf, "UMD": umd}, index=idx).loc[idx >= _me("1963-07")]

    def fred(dates, values, sid):
        return pd.DataFrame({"observation_date": dates.to_period("M").to_timestamp().strftime("%Y-%m-%d"),
                             sid: values})

    e_idx = _month_range("1985-01", end)
    ne = len(e_idx)
    x = np.zeros(ne)
    for i in range(1, ne):
        x[i] = 0.85 * x[i - 1] + rng.normal(0.0, 0.35)
    emv_all = 20.0 * np.exp(rng.normal(0.0, 0.3, ne))
    emv_cat = emv_all * np.exp(-3.5 + x)
    emv_cat[rng.random(ne) < np.where(e_idx < _me("1996-01"), 0.05, 0.01)] = 0.0
    g_idx = _month_range("1953-04", end)
    # FIX (BUG-1): v1 used a driftless random walk clipped at [0.5, 15]; with this seed it sits on the 0.5 floor in
    # 76% of 1995-2009 months, so BOND is a constant there and I*BOND acts as an I main effect that absorbs the
    # planted timing effect. Same shocks (same RNG consumption, so every later synthetic series is unchanged),
    # filtered as a mean-reverting AR(1) around 5% whose clip never binds.
    shocks = rng.normal(0.0, 0.2, len(g_idx))
    gs10 = np.empty(len(g_idx))
    gs10[0] = 5.0 + shocks[0]
    for i in range(1, len(g_idx)):
        gs10[i] = 5.0 + 0.97 * (gs10[i - 1] - 5.0) + shocks[i]
    gs10 = np.clip(gs10, 0.5, 15.0)
    w_idx = _month_range("1986-01", end)
    wti = 20.0 * np.exp(np.cumsum(rng.normal(0.0, 0.08, len(w_idx))))
    days = pd.bdate_range("1990-01-02", _me(end))
    vix = 20.0 * np.exp(rng.normal(0.0, 0.25, len(days)))
    vix[rng.random(len(days)) < 0.03] = np.nan
    return {"ff49": ff49, "fac": fac,
            "emv_cat": fred(e_idx, emv_cat, "EMVENRGYENVREG"),
            "emv_all": fred(e_idx, emv_all, "EMVOVERALLEMV"),
            "gs10": fred(g_idx, gs10, "GS10"),
            "wti": fred(w_idx, wti, "MCOILWTICO"),
            "vix": pd.DataFrame({"observation_date": days.strftime("%Y-%m-%d"), "VIXCLS": vix})}


def check_no_lookahead(inputs: dict, cfg: Config = Config(), n_random: int = 20,
                       cut_from: str | None = None, cut_to: str | None = None,
                       seed: int = 7) -> pd.DataFrame:
    """
    Look-ahead (truncation) test. For each cut month T keep French data dated <= T and EMV
    data dated <= T - pub_lag (what is published by the end of T), rerun signal, hold, hedge,
    sizing and trade, and compare everything set at the end of T (hold, w, m, overlay, b) with
    the full-sample run. Cuts = every crossing month tau and tau+pub_lag (where a lag bug shows)
    plus random months, restricted to [cut_from, cut_to]. Any row with ok == False = look-ahead.
    """
    ff49 = load_ff49(inputs["ff49"])
    fac = load_factors(inputs["fac"])
    emv_cat = load_fred_monthly(inputs["emv_cat"], "EMVENRGYENVREG")
    emv_all = load_fred_monthly(inputs["emv_all"], "EMVOVERALLEMV")
    index = _month_range(fac.index.min(), min(fac.index.max(), ff49.index.max()))

    def state(ff, fc, ec, ea, idx):
        s = attention_signal(ec, ea, cfg)
        hd = hold_positions(crossings(s["extreme"], cfg), idx, cfg)
        lg = leg_pipeline(ff, fc, cfg.brown, hd, idx, cfg)
        cols = ["hold", "w", "m"] + [f"h_{c}" for c in cfg.hedge_factors]
        return lg["tr_T"][cols].astype(float).join(lg["b"].add_prefix("b_"))

    full = state(ff49, fac, emv_cat, emv_all, index)
    sig = attention_signal(emv_cat, emv_all, cfg)
    cr = crossings(sig["extreme"], cfg)
    taus = cr.index[cr.to_numpy(bool)]
    first = _shift_months(sig["extreme"].first_valid_index(), cfg.pub_lag)
    lo = max(first, _me(cut_from)) if cut_from else first
    hi = min(index[-1], _me(cut_to)) if cut_to else index[-1]
    pool = index[(index >= lo) & (index <= hi)]
    rng = np.random.default_rng(seed)
    cuts = set(taus) | {_shift_months(t, cfg.pub_lag) for t in taus}
    cuts |= set(pd.DatetimeIndex(rng.choice(pool.to_numpy(), size=min(n_random, len(pool)), replace=False)))
    cuts = sorted(t for t in cuts if lo <= t <= hi)

    rows = []
    for T in cuts:
        L = _shift_months(T, -cfg.pub_lag)
        part = state(ff49.loc[:T], fac.loc[:T], emv_cat.loc[:L], emv_all.loc[:L], index[index <= T])
        a, b = part.loc[T], full.loc[T]
        diff = (a - b).abs().max()
        rows.append({"cut": T, "max_abs_diff": float(diff) if pd.notna(diff) else 0.0,
                     "nan_mismatch": bool((a.isna() != b.isna()).any())})
    out = pd.DataFrame(rows, columns=["cut", "max_abs_diff", "nan_mismatch"])
    out["ok"] = (out["max_abs_diff"] <= 1e-12) & ~out["nan_mismatch"]
    return out


def plant_timing_effect(inputs: dict, cfg: Config = Config(), delta: float = 0.03) -> dict:
    """
    Positive control (synthetic only). Lowers each Brown industry's return by `delta` in every
    month t entered with a position (hold set at the end of t-1). The signal is untouched, so
    the hold series is unchanged. Expected: alpha > 0, roughly
    delta * (1 - pi) * mean_t(I_{t-1} m_{t-1}), with a small shuffle p.
    """
    emv_cat = load_fred_monthly(inputs["emv_cat"], "EMVENRGYENVREG")
    emv_all = load_fred_monthly(inputs["emv_all"], "EMVOVERALLEMV")
    raw = _read(inputs["ff49"])
    months = _to_month_end(raw["date"])
    sig = attention_signal(emv_cat, emv_all, cfg)
    hold = hold_positions(crossings(sig["extreme"], cfg), _month_range(months.min(), months.max()), cfg)
    on = hold.shift(1, fill_value=False).reindex(months, fill_value=False).to_numpy(bool)
    raw.loc[on, list(cfg.brown)] = raw.loc[on, list(cfg.brown)] - delta
    out = dict(inputs)
    out["ff49"] = raw
    return out


if __name__ == "__main__":
    MODE = "synthetic"      # "synthetic" -> "seen" -> "final" (final: once, no edits after "seen")

    if MODE == "synthetic":
        cfg = replace(Config(), shuffle_draws=500)
        syn = make_synthetic_inputs(seed=0)
        _show("LOOK-AHEAD TEST (synthetic)", check_no_lookahead(syn, cfg))
        out = run_backtest(syn, cfg)
        out_planted = run_backtest(plant_timing_effect(syn, cfg, delta=0.03), cfg)
    else:
        fac = pd.read_pickle("fac.pkl")     # your parsed French FF5 + UMD DataFrame (decimals)
        inputs = dict(ff49="ff49_industry_monthly.csv", fac=fac,
                      emv_cat="EMVENRGYENVREG.csv", emv_all="EMVOVERALLEMV.csv",
                      gs10="GS10.csv", wti="MCOILWTICO.csv", vix="VIXCLS.csv")
        if MODE == "seen":
            cfg = replace(Config(), test_start="2010-01", test_end="2022-12")
            _show("LOOK-AHEAD TEST (seen data only)", check_no_lookahead(inputs, cfg, cut_from="2010-01"))
        elif MODE == "final":
            cfg = Config()
        else:
            raise ValueError(MODE)
        out = run_backtest(inputs, cfg)
