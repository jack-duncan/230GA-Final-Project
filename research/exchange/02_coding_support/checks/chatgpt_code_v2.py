"""
brown_attention_prereg.py

Pre-registered, run-once backtest of the frozen Brown-attention rule (MFE 230GA).
pandas / numpy / statsmodels only. No plots, no parameter search, fixed seed.

Order of use
  1. MODE = "synthetic": debug end to end on random data (+ look-ahead test, planted effect).
  2. MODE = "seen":      2010-01..2022-12, compare with the team's existing numbers.
  3. MODE = "final":     1993-01..2009-12, exactly once, no code change after step 2.
"""
#
# chatgpt_code_v2.py (round 2 of exchange 2, assembled 2026-09-26 by the fact-checker)
#   = chatgpt_code_v1.py (verbatim extraction of ChatGPT's first answer)
#   + ChatGPT's follow-up reply applied: the six replaced functions and their tests, pasted verbatim as one
#     block at the end of the file (identical to checks/chatgpt_round2_block.py), with the old definitions of
#     attention_signal, leg_pipeline, pass_fail_table, make_synthetic_inputs, check_no_lookahead and __main__ removed;
#   + ChatGPT's four listed driver changes (run_backtest signature, hedge_fac to every leg_pipeline call,
#     z_burn_in to attention_signal, overlay on the leg's own f/b, pass_fail_table on plain numbers), marked
#     "ROUND 2 driver change";
#   + three small adapters the reply did not supply but its replacements need, marked "ROUND-2 INTEGRATION
#     (not in ChatGPT's reply)": _driver_signal, _leg_books, _panel.
# Everything else is v1 unchanged, including now-unused v1 functions (brown_leg, rolling_hedge,
# hedge_residual_and_size, plant_timing_effect).
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


# -----------------------------------------------------------------------------
# ROUND-2 INTEGRATION (not in ChatGPT's reply). ChatGPT replaced attention_signal and leg_pipeline with
# functions whose outputs have a new layout, but said everything else is unchanged. These adapters feed the
# unchanged v1 driver (crossings, test_window, crossing_table, diagnostics_summary, run_trade, timing_difference,
# calendar_shuffle) without changing any value.
# -----------------------------------------------------------------------------
def _driver_signal(sig: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    """New attention_signal output -> v1 layout. v1 readers need: extreme as 1/0 where z and thr are defined and
    NaN elsewhere (crossings() bridges NaN flags; test_window() takes the first non-NaN flag), s with zero months
    kept as 0 (diagnostics count s == 0), and `off` (diagnostics). The new function returns a boolean extreme that
    is False where undefined, NaN s on zero months, and no `off` column."""
    defined = sig["z"].notna() & sig["thr"].notna()
    max_missing = int(np.floor(cfg.max_zero_share * cfg.z_window + 1e-9))
    s = sig["s"].where(~sig["zero"].astype(bool), 0.0)
    missing = ~(s > 0)
    return pd.DataFrame({"s": s, "missing": missing, "n_missing60": sig["n_zero"],
                         "off": ~missing & (sig["n_zero"] > max_missing),
                         "z": sig["z"], "thr": sig["thr"],
                         "extreme": sig["extreme"].astype(float).where(defined)}, index=sig.index)


def _leg_books(ff49: pd.DataFrame, hedge_fac: pd.DataFrame, industries, hold: pd.Series,
               index: pd.DatetimeIndex, cfg: Config) -> dict:
    """New leg_pipeline (a DataFrame) -> the dict the v1 driver consumes (rb, f, a, b, e, sd, m, tr_T, tr_AO).
    ROUND 2 driver change 2: both books are built by the unchanged run_trade on the leg's own f_* and b_*
    (hedge_fac), so the overlay return and the overlay costs never see `fac`."""
    L = leg_pipeline(ff49, hedge_fac, brown=list(industries)).reindex(index)
    hf = list(cfg.hedge_factors)
    f = L[[f"f_{k}" for k in hf]].set_axis(hf, axis=1)
    b = L[[f"b_{k}" for k in hf]].set_axis(hf, axis=1)
    rb, m = L["RB"].rename("RB"), L["m"].rename("m")
    tr_T = run_trade(rb, f, b, m, hold, cfg)
    tr_AO = run_trade(rb, f, b, m, pd.Series(True, index=index), cfg)
    return dict(rb=rb, f=f, a=L["a"], b=b, e=L["e"], sd=L["sd"], m=m, tr_T=tr_T, tr_AO=tr_AO, leg=L)


def _panel(leg: dict, hold: pd.Series) -> pd.DataFrame:
    """The panel run_panel's docstring promises: w, w_ao (set at end of t), RT, RAO (net, earned in t), m, hold,
    b_<k> (end-of-t states), I (1 if a timed position was held entering t)."""
    T, A = leg["tr_T"], leg["tr_AO"]
    P = pd.DataFrame({"w": T["w"], "w_ao": A["w"], "RT": T["net"], "RAO": A["net"], "m": leg["m"],
                      "hold": hold.reindex(T.index, fill_value=False).astype(bool)}, index=T.index)
    for k in leg["b"].columns:
        P[f"b_{k}"] = leg["b"][k]
    P["I"] = P["hold"].shift(1, fill_value=False).astype(float)
    return P


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
                  cfg: Config, *, hedge_fac: pd.DataFrame) -> pd.DataFrame:
    """
    Step 15. Drop each Brown industry in turn; rebuild leg, hedge, sizing, timed and always-on
    books, pi and D; refit the attribution. Hold timing is unchanged (the signal does not use
    returns). Output: one row per dropped industry with alpha, NW(6) t, p, pi, same_sign.
    ROUND 2 driver change 1: every rebuild hedges on hedge_fac (team FF3), not fac.
    """
    rows = []
    for drop in cfg.brown:
        keep = tuple(c for c in cfg.brown if c != drop)
        leg = _leg_books(ff49, hedge_fac, keep, hold, index, cfg)
        D, pi, I = timing_difference(leg["tr_T"], leg["tr_AO"], window, cfg)
        _, f6, _ = attribution_regression(D, design_matrix(F, I, cfg), cfg)
        a = float(f6.params["const"])
        rows.append({"dropped": drop, "alpha": a, f"t NW({cfg.nw_lags})": float(f6.tvalues["const"]),
                     "p": float(f6.pvalues["const"]), "pi": pi,
                     "same_sign": bool(np.sign(a) == np.sign(alpha_full))})
    return pd.DataFrame(rows)


# =============================================================================
# 17. Run
# =============================================================================
def run_backtest(paths: dict, fac: pd.DataFrame, start, end, *, hedge_fac: pd.DataFrame,
                 z_burn_in: str = "nonzero", n_shuffle: int = 5000, run_loo: bool = True,
                 verbose: bool = True) -> dict:
    """
    Step 17. Runs steps 1-16 once; returns and prints the five outputs.
    ROUND 2 driver changes (ChatGPT's list): signature run_backtest(paths, fac, start, end, *, hedge_fac,
    z_burn_in, n_shuffle, run_loo, verbose); hedge_fac to every leg_pipeline call (main run and the five
    leave-one-out rebuilds); z_burn_in to attention_signal; overlay on the leg's own f/b; pass_fail_table on
    plain numbers. n_shuffle = 0 skips the shuffle and run_loo = False the leave-one-out (the unit tests call
    run_panel that way). Extra outputs for run_panel: panel, alpha, alpha_t.
    paths: 'ff49' and the FRED ids, in the layout write_raw_csvs produces. fac: FF5 + UMD (attribution, BOND RF).
    start/end: test window in return months; the start still moves later if the rule cannot fire yet.
    """
    cfg = replace(Config(), test_start=f"{pd.Timestamp(start):%Y-%m}", test_end=f"{pd.Timestamp(end):%Y-%m}",
                  shuffle_draws=int(n_shuffle))
    ff49 = load_ff49(paths["ff49"])
    fac = load_factors(fac)
    emv_cat = load_fred_monthly(paths["EMVENRGYENVREG"], "EMVENRGYENVREG")
    emv_all = load_fred_monthly(paths["EMVOVERALLEMV"], "EMVOVERALLEMV")
    gs10 = load_fred_monthly(paths["GS10"], "GS10")
    wti = load_fred_monthly(paths["MCOILWTICO"], "MCOILWTICO")
    vix = load_vix_monthly(paths["VIXCLS"], "VIXCLS")
    index = _month_range(fac.index.min(), min(fac.index.max(), ff49.index.max()))

    # signal and hold: independent of the Brown leg
    sig = _driver_signal(attention_signal(emv_cat, emv_all, z_burn_in=z_burn_in), cfg)   # ROUND 2: z_burn_in
    cross = crossings(sig["extreme"], cfg)
    hold = hold_positions(cross, index, cfg)
    first_sig, first_pos, first_ret, window = test_window(sig, index, cfg)
    pos_months = _position_months(window)
    eps = hold_episodes(hold, pos_months)
    xtab = crossing_table(sig, cross, pos_months, cfg)

    # books, D, regressors
    leg = _leg_books(ff49, hedge_fac, cfg.brown, hold, index, cfg)                       # ROUND 2: hedge_fac
    D, pi, I_prev = timing_difference(leg["tr_T"], leg["tr_AO"], window, cfg)
    bond = bond_excess_return(gs10, fac["RF"])
    F = attribution_factors(fac, bond, wti, vix, emv_all, index).loc[window]
    summary = diagnostics_summary(sig, hold, leg, ff49, window, first_sig, first_pos, first_ret,
                                  eps, xtab, pi, cfg)
    panel = _panel(leg, hold)

    if eps.empty:
        pf = pd.DataFrame([["(iii) independent episodes", "merged hold runs in window",
                            f">= {cfg.min_episodes}", "0", "FAIL"],
                           ["OVERALL", "all four required", "4/4", "-", "FAIL (no position in window)"]],
                          columns=["component", "statistic", "bar", "value", "pass"])
        if verbose:
            _show("1. PASS / FAIL", pf)
            _show("4a. DIAGNOSTICS", summary)
        return {"pass_fail": pf, "verdict": "FAIL", "diagnostics": summary,
                "crossings": xtab, "episodes": eps, "panel": panel, "D": D, "hold": hold, "signal": sig}

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

    if cfg.shuffle_draws > 0:
        shuf, null = calendar_shuffle(alpha, leg, hold, F, window, pi, I_prev, cfg)
        shuffle_p = float(shuf.at["p (one-sided)", "value"])
    else:
        shuf, null, shuffle_p = None, np.array([]), np.nan
    if run_loo:
        loo = leave_one_out(ff49, fac, hold, F, window, index, alpha, cfg, hedge_fac=hedge_fac)
        loo_alpha = loo.set_index("dropped")["alpha"]
    else:
        loo, loo_alpha = pd.DataFrame(), pd.Series(dtype=float)
    pf = pass_fail_table(alpha, float(f6.tvalues["const"]), float(f6.pvalues["const"]),   # ROUND 2: plain numbers
                         shuffle_p, len(eps), loo_alpha)
    verdict = str(pf.at["overall", "result"])

    if verbose:
        _show("1. PASS / FAIL", pf)
        _show("2a. ATTRIBUTION (D_t on FF5+UMD, BOND, WTI, dVIX, dlogEMV, I_{t-1} x F)", coef)
        _show("2b. REGRESSION FACTS", meta)
        _show("3. DECOMPOSITION OF mean(D)", decomp)
        _show("4a. DIAGNOSTICS", summary)
        _show("4b. CROSSINGS AFFECTING THE WINDOW", xtab)
        _show("4c. EPISODES", eps)
        if len(loo):
            _show("4d. LEAVE ONE INDUSTRY OUT", loo)
        if shuf is not None:
            _show("5. CALENDAR SHUFFLE", shuf)

    return {"pass_fail": pf, "verdict": verdict, "attribution": coef, "attribution_meta": meta,
            "decomposition": decomp, "diagnostics": summary, "crossings": xtab, "episodes": eps,
            "leave_one_out": loo, "shuffle": shuf, "null_alphas": null,
            "D": D, "X": X, "hold": hold, "signal": sig, "fit_nw6": f6, "fit_nw12": f12,
            "panel": panel, "alpha": alpha, "alpha_t": float(f6.tvalues["const"]), "leg": leg}


# =============================================================================
# 18. Pre-run checks: synthetic data, look-ahead test, planted effect
# =============================================================================
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


# =============================================================================
# Replacements. Everything not defined here is unchanged from the earlier script.
# =============================================================================
import os
import sys
import tempfile

import numpy as np
import pandas as pd

# Constants (already in the script; repeated so this block stands alone)
BROWN = ["Util", "Ships", "Aero", "Steel", "BldMt"]
HEDGE_COLS = ["Mkt-RF", "SMB", "HML"]
FRED_IDS = ["EMVENRGYENVREG", "EMVOVERALLEMV", "GS10", "MCOILWTICO", "VIXCLS"]
FF49_NAMES = [
    "Agric", "Food", "Soda", "Beer", "Smoke", "Toys", "Fun", "Books", "Hshld", "Clths",
    "Hlth", "MedEq", "Drugs", "Chems", "Rubbr", "Txtls", "BldMt", "Cnstr", "Steel", "FabPr",
    "Mach", "ElcEq", "Autos", "Aero", "Ships", "Guns", "Gold", "Mines", "Coal", "Oil",
    "Util", "Telcm", "PerSv", "BusSv", "Hardw", "Softw", "Chips", "LabEq", "Paper", "Boxes",
    "Trans", "Whlsl", "Rtail", "Meals", "Banks", "Insur", "RlEst", "Fin", "Other",
]
LATE_START = {"Soda": "1963-07-31", "Hlth": "1969-07-31", "Rubbr": "1963-07-31", "FabPr": "1963-07-31",
              "Guns": "1963-07-31", "Gold": "1963-07-31", "Softw": "1965-07-31"}
STATE_COLS = ["w", "w_ao", "m", "hold"] + [f"b_{k}" for k in HEDGE_COLS]
POS_OF = {"RT": "w", "RAO": "w_ao"}          # return column -> the position that earns it
TEST_WINDOW = ("1993-01-31", "2009-12-31")
SEEN_WINDOW = ("2010-01-31", "2022-07-31")   # the holdout starts 2022-08
MONTH_END = pd.offsets.MonthEnd()


# -----------------------------------------------------------------------------
# Raw-input helpers. Checks and tests work on `raw` (the files as read from disk),
# so synthetic, perturbed and truncated data all pass through your unchanged loader.
# -----------------------------------------------------------------------------
def read_raw(paths, fac, hedge_fac):
    """Inputs: dict of CSV paths (keys 'ff49' and the FRED ids), fac (FF5+UMD), hedge_fac (team FF3).
    Output: dict of raw frames exactly as on disk plus the two factor frames. Timing: none."""
    raw = {"ff49": pd.read_csv(paths["ff49"], parse_dates=["date"], float_precision="round_trip"),
           "fac": fac, "hedge_fac": hedge_fac}
    for sid in FRED_IDS:
        df = pd.read_csv(paths[sid], parse_dates=["observation_date"], float_precision="round_trip")
        df[sid] = pd.to_numeric(df[sid], errors="coerce")        # FRED blanks -> NaN
        raw[sid] = df
    return raw


def write_raw_csvs(raw, folder):
    """Inputs: raw dict, folder. Output: dict of paths in the same layout as the real files. Timing: none."""
    paths = {"ff49": os.path.join(folder, "ff49_industry_monthly.csv")}
    raw["ff49"].to_csv(paths["ff49"], index=False, date_format="%Y-%m-%d")
    for sid in FRED_IDS:
        paths[sid] = os.path.join(folder, f"{sid}.csv")
        raw[sid].to_csv(paths[sid], index=False, date_format="%Y-%m-%d")
    return paths


def truncate_raw(raw, cut_to):
    """Inputs: raw dict, month-end cut_to. Output: copy with every row dated after cut_to removed
    (FRED monthly rows are dated the 1st, so month cut_to itself is kept). Timing: nothing after cut_to survives."""
    cut = pd.Timestamp(cut_to)
    out = {}
    for k, v in raw.items():
        if not isinstance(v, pd.DataFrame):
            out[k] = v
        elif "date" in v.columns:
            out[k] = v[v["date"] <= cut].copy()
        elif "observation_date" in v.columns:
            out[k] = v[v["observation_date"] <= cut].copy()
        else:
            out[k] = v.loc[v.index <= cut].copy()
    return out


def _last_date(raw):
    dates = []
    for v in raw.values():
        if isinstance(v, pd.DataFrame) and len(v):
            col = "date" if "date" in v.columns else ("observation_date" if "observation_date" in v.columns else None)
            dates.append(v[col].max() if col else v.index.max())
    return max(dates)


def _bump(raw, key, T, cols, fn):
    """Copy of raw with fn applied to `cols` of frame `key` in the calendar month of T."""
    r = dict(raw)
    df = raw[key].copy()
    p = pd.Timestamp(T).to_period("M")
    if "date" in df.columns:
        rows = (df["date"].dt.to_period("M") == p).to_numpy()
    elif "observation_date" in df.columns:
        rows = (df["observation_date"].dt.to_period("M") == p).to_numpy()
    else:
        rows = df.index.to_period("M") == p
    df.loc[rows, cols] = fn(df.loc[rows, cols])
    r[key] = df
    return r


def _maxdiff(a, b, cols):
    """Max |a - b| over cols on a's rows; NaN vs NaN counts as equal, NaN vs number as inf."""
    av = a[cols].astype(float).to_numpy()
    bv = b.reindex(a.index)[cols].astype(float).to_numpy()
    if (np.isnan(av) ^ np.isnan(bv)).any():
        return np.inf
    d = np.abs(av - bv)[~(np.isnan(av) & np.isnan(bv))]
    return float(d.max()) if d.size else 0.0


def _ret_err(base, pert, T, expected):
    errs = []
    for col, e in expected.items():
        d = pert.at[T, col] - base.at[T, col] - e if T in pert.index else np.nan
        errs.append(abs(d) if np.isfinite(d) else np.inf)
    return max(errs)


def run_panel(raw, start, end, z_burn_in="nonzero", n_shuffle=0, loo=False, verbose=False):
    """
    ADAPTER to the unchanged driver: the only place the tests touch it. Edit names here if yours differ.
    Inputs : raw dict; window; burn-in reading; shuffle draws (0 = skip); leave-one-out on/off.
    Output : (panel, out).
             panel, indexed by month-end t: w, w_ao (positions set at end of t), RT, RAO (net returns earned
             in t), m, hold, b_Mkt-RF, b_SMB, b_HML (end-of-t states), I (1 if a timed position was held
             entering t).
             out: D (Series), X (design DataFrame incl. constant), alpha, alpha_t (NW(6)), plus the
             driver's printed tables.
    Timing : the window end is clipped to the last month in raw, so truncated inputs run cleanly.
    """
    end = min(pd.Timestamp(end), pd.Timestamp(raw["ff49"]["date"].max()))
    with tempfile.TemporaryDirectory() as d:
        paths = write_raw_csvs(raw, d)
        out = run_backtest(paths, raw["fac"], start, end, hedge_fac=raw["hedge_fac"],   # noqa: F821
                           z_burn_in=z_burn_in, n_shuffle=n_shuffle, run_loo=loo, verbose=verbose)
    return out["panel"], out


# =============================================================================
# 1. make_synthetic_inputs
# =============================================================================
def make_synthetic_inputs(seed=0, out_dir=None, plant=0.0, plant_months=None, end="2026-06-30"):
    """
    Synthetic stand-ins for every input, shaped exactly like the real files.

    Inputs
      seed         : fixed RNG seed (nothing is tuned on it).
      out_dir      : if given, also write the six CSVs there; their paths are returned under 'paths'.
      plant        : positive-control effect (decimal). Every Brown industry return is lowered by `plant`
                     in each month of `plant_months`, so the short Brown leg gains there.
      plant_months : month-ends t whose return is earned by a timed position (I_{t-1} = 1) in an unplanted
                     run with the same seed. The signal files do not depend on returns and the plant draws
                     no random numbers, so the hold schedule and all other data are identical with and without it.
    Outputs
      dict: 'ff49' (date column + 49 industries, NaN before an industry starts), 'fac' (Mkt-RF, SMB, HML,
      RMW, CMA, RF, UMD from 1963-07), 'hedge_fac' (FF3: Mkt-RF, SMB, HML, RF from 1926-07; its SMB differs
      from fac's, as in the real files), one frame per FRED id (observation_date + id).
    Timing
      Returns at month-ends. FRED monthly rows dated the 1st. GS10 from 1953-04, EMV from 1985-01,
      WTI from 1986-01, VIXCLS daily business days from 1990-01-02 with ~3% blanks.
    Fix
      GS10 used to be a random walk clipped at 0.5, so it could sit on the clip and make BOND constant.
      log(GS10) is now a stationary AR(1): always positive, never clipped, and it moves every month.
    """
    rng = np.random.default_rng(seed)
    idx = pd.date_range("1926-07-31", end, freq=MONTH_END)
    n = len(idx)

    def ar1(nobs, mu, phi, sig, x0):
        eps = rng.standard_normal(nobs)
        x = np.empty(nobs)
        x[0] = x0
        for i in range(1, nobs):
            x[i] = mu + phi * (x[i - 1] - mu) + sig * eps[i]
        return x

    y10 = np.exp(ar1(n, np.log(5.0), 0.985, 0.045, np.log(3.5)))            # percent, roughly 2-11
    rf = y10 * 0.6 * np.exp(ar1(n, 0.0, 0.9, 0.05, 0.0)) / 1200.0              # monthly decimal

    zf = rng.standard_normal((n, 7))
    mkt, smb3, hml = 0.006 + 0.045 * zf[:, 0], 0.002 + 0.030 * zf[:, 1], 0.003 + 0.030 * zf[:, 2]
    rmw, cma, umd = 0.003 + 0.020 * zf[:, 3], 0.003 + 0.020 * zf[:, 4], 0.006 + 0.040 * zf[:, 5]
    smb5 = smb3 + 0.004 * zf[:, 6]
    hedge_fac = pd.DataFrame({"Mkt-RF": mkt, "SMB": smb3, "HML": hml, "RF": rf}, index=idx)
    fac = pd.DataFrame({"Mkt-RF": mkt, "SMB": smb5, "HML": hml, "RMW": rmw, "CMA": cma,
                        "RF": rf, "UMD": umd}, index=idx).loc["1963-07-31":]

    brown_common = 0.015 * rng.standard_normal(n)
    rets = {}
    for name in FF49_NAMES:
        bm, bs, bh = rng.normal(1.0, 0.2), rng.normal(0.2, 0.3), rng.normal(0.2, 0.3)
        r = rf + bm * mkt + bs * smb3 + bh * hml + 0.05 * rng.standard_normal(n)
        if name in BROWN:
            r = r + brown_common
        if name in LATE_START:
            r = np.where(idx < pd.Timestamp(LATE_START[name]), np.nan, r)
        rets[name] = r
    if plant != 0.0:
        if plant_months is None:
            raise ValueError("plant != 0 needs plant_months")
        hit = idx.to_period("M").isin(pd.DatetimeIndex(plant_months).to_period("M"))
        for name in BROWN:
            rets[name] = np.where(hit, rets[name] - plant, rets[name])
    ff49 = pd.DataFrame(rets, index=idx)[FF49_NAMES]
    ff49.insert(0, "date", idx)
    ff49 = ff49.reset_index(drop=True)

    def fred(mask, values, sid):
        return pd.DataFrame({"observation_date": idx[mask].to_period("M").to_timestamp(), sid: values})

    g = idx >= pd.Timestamp("1953-04-30")
    e = idx >= pd.Timestamp("1985-01-31")
    o = idx >= pd.Timestamp("1986-01-31")
    ne = int(e.sum())
    overall = np.exp(ar1(ne, np.log(25.0), 0.8, 0.15, np.log(25.0)))            # never zero
    env = overall * np.exp(ar1(ne, np.log(0.02), 0.6, 0.35, np.log(0.02)))
    p_zero = np.where(idx[e] < pd.Timestamp("1995-01-01"), 0.05, 0.01)          # zeros cluster early
    env = np.where(rng.random(ne) < p_zero, 0.0, env)
    wti = np.exp(ar1(int(o.sum()), np.log(40.0), 0.98, 0.09, np.log(22.0)))
    days = pd.bdate_range("1990-01-02", end)
    vix = np.round(np.exp(ar1(len(days), np.log(19.0), 0.98, 0.06, np.log(19.0))), 2)
    vix[rng.random(len(days)) < 0.03] = np.nan

    raw = {"ff49": ff49, "fac": fac, "hedge_fac": hedge_fac,
           "GS10": fred(g, y10[g], "GS10"),
           "EMVOVERALLEMV": fred(e, overall, "EMVOVERALLEMV"),
           "EMVENRGYENVREG": fred(e, env, "EMVENRGYENVREG"),
           "MCOILWTICO": fred(o, wti, "MCOILWTICO"),
           "VIXCLS": pd.DataFrame({"observation_date": days, "VIXCLS": vix})}
    if out_dir is not None:
        os.makedirs(out_dir, exist_ok=True)
        raw["paths"] = write_raw_csvs(raw, out_dir)
    return raw


def positive_control(seed=0, plant=0.03, window=TEST_WINDOW):
    """
    Check (b)10. Inputs: seed, plant (Brown leg lower by `plant` in every held month), window.
    Output: dict with the planted shift = mean(D_planted) - mean(D_unplanted), the share of it in alpha,
    and the planted run's alpha and NW(6) t. Timing: the plant sits in month t when I_{t-1} = 1.
    """
    raw0 = make_synthetic_inputs(seed)
    p0, o0 = run_panel(raw0, *window)
    w0 = p0.loc[window[0]:window[1]]
    held = w0.index[(w0["I"] == 1).to_numpy()]
    raw1 = make_synthetic_inputs(seed, plant=plant, plant_months=held)
    p1, o1 = run_panel(raw1, *window)
    shift = o1["D"].mean() - o0["D"].mean()
    return dict(seed=seed, same_I=bool(p1["I"].equals(p0["I"])), n_held=len(held), shift=shift,
                share=(o1["alpha"] - o0["alpha"]) / shift, alpha=o1["alpha"], t=o1["alpha_t"])


def test_make_synthetic_inputs(seeds=range(21), pc_seeds=(0, 1, 2)):
    for seed in seeds:
        raw = make_synthetic_inputs(seed)
        g = raw["GS10"]["GS10"]
        assert g.notna().all() and g.min() > 0.5, (seed, g.min())               # no floor
        assert (g.diff().iloc[1:] != 0).all(), seed                              # moves every month
        assert g.diff().rolling(24).std().dropna().min() > 0.02, seed            # and in every window
        for start, end in (TEST_WINDOW, SEEN_WINDOW):
            panel, out = run_panel(raw, start, end)
            X = out["X"]
            I = panel["I"].reindex(X.index).astype(float)
            assert np.linalg.matrix_rank(X.to_numpy()) == X.shape[1], (seed, start)   # seed 16 crashed here
            assert (X.std() < 1e-12).sum() == 1, (seed, start)                         # only the constant
            coef = np.linalg.lstsq(X.to_numpy(), I.to_numpy(), rcond=None)[0]
            r2 = 1 - ((I - X @ coef) ** 2).sum() / ((I - I.mean()) ** 2).sum()
            assert r2 < 0.5, (seed, start, r2)          # no regressor combination can stand in for I itself
    for seed in pc_seeds:
        r = positive_control(seed)
        assert r["same_I"] and r["n_held"] > 0 and r["shift"] > 0, r
        assert r["share"] >= 0.8 and r["t"] > 2, r


# =============================================================================
# 2. attention_signal
# =============================================================================
def attention_signal(env, overall, z_burn_in="nonzero", window=60, min_nonzero=48,
                     max_zero_frac=0.10, pct=0.80, min_prior_z=60):
    """
    Rule steps 1-3: ratio, zero handling, rolling z, past-only percentile threshold, extreme flag.

    Inputs
      env, overall : Series of EMVENRGYENVREG and EMVOVERALLEMV indexed by data month (month-end).
                     Months before the first observation do not exist: unavailable, not zero.
      z_burn_in    : "nonzero"  (default, your reading): z_t exists once the trailing 60 months hold
                                 >= 48 nonzero months, counting only months inside the sample.
                     "calendar" (my previous hard-coded reading): also require 60 calendar months since
                                 the first observation.
      Rules shared by both readings: a zero month has no z and cannot be extreme; the month is "off"
      (no z) when the trailing 60 calendar months contain more than 6 zeros (10% of 60) or fewer than
      48 nonzero months; the z window and the percentile history use only months with a z.
    Outputs
      DataFrame by data month t: s, zero, n_nonzero, n_zero, on, z, n_prior_z, thr, extreme.
      z_t = (log s_t - mean) / std(ddof=1) over nonzero months t-59..t.
      thr_t = 80th percentile (linear) of all z before t, needing >= 60 of them. extreme_t = on_t and z_t > thr_t.
    Timing
      Row t uses EMV data for months <= t only. Publication lag: row t is usable at the end of t+1.
      The lag is applied in the hold step (unchanged), which reads extreme[t-1] at the end of t.
    """
    if z_burn_in not in ("nonzero", "calendar"):
        raise ValueError("z_burn_in must be 'nonzero' or 'calendar'")
    env, overall = env.copy(), overall.copy()
    env.index = pd.DatetimeIndex(env.index) + pd.offsets.MonthEnd(0)
    overall.index = pd.DatetimeIndex(overall.index) + pd.offsets.MonthEnd(0)
    df = pd.concat({"env": env, "overall": overall}, axis=1).sort_index()
    idx = pd.date_range(df.dropna().index.min(), df.index.max(), freq=MONTH_END)
    df = df.reindex(idx)

    avail = df["env"].notna() & df["overall"].notna() & (df["overall"] > 0)
    zero = avail & (df["env"] == 0)
    good = avail & (df["env"] > 0)
    s = (df["env"] / df["overall"]).where(good)
    x = np.log(s)

    n_nonzero = good.astype(int).rolling(window, min_periods=1).sum()
    n_zero = zero.astype(int).rolling(window, min_periods=1).sum()
    max_zero = int(np.floor(max_zero_frac * window + 1e-9))
    on = good & (n_nonzero >= min_nonzero) & (n_zero <= max_zero)
    if z_burn_in == "calendar":
        on &= pd.Series(np.arange(len(idx)) >= window - 1, index=idx)

    roll = x.rolling(window, min_periods=min_nonzero)
    z = ((x - roll.mean()) / roll.std(ddof=1)).where(on)

    zv = z.to_numpy()
    thr = np.full(len(zv), np.nan)
    n_prior = np.zeros(len(zv), dtype=int)
    hist = []
    for i, zi in enumerate(zv):
        n_prior[i] = len(hist)
        if len(hist) >= min_prior_z:
            thr[i] = np.quantile(hist, pct)
        if np.isfinite(zi):
            hist.append(zi)
    thr = pd.Series(thr, index=idx)
    extreme = on & (z > thr)
    return pd.DataFrame({"s": s, "zero": zero, "n_nonzero": n_nonzero, "n_zero": n_zero, "on": on,
                         "z": z, "n_prior_z": n_prior, "thr": thr, "extreme": extreme})


def test_attention_signal():
    idx = pd.date_range("1985-01-31", "2005-12-31", freq=MONTH_END)
    rng = np.random.default_rng(1)
    overall = pd.Series(100 * np.exp(rng.normal(0, 0.2, len(idx))), idx)
    env = overall * np.exp(rng.normal(np.log(0.01), 0.3, len(idx)))
    a = attention_signal(env, overall, z_burn_in="nonzero")
    b = attention_signal(env, overall, z_burn_in="calendar")
    assert a["z"].first_valid_index() == idx[47]           # month 48
    assert b["z"].first_valid_index() == idx[59]           # month 60
    assert a["thr"].first_valid_index() == idx[107] and b["thr"].first_valid_index() == idx[119]
    assert np.allclose(a["z"].iloc[59:], b["z"].iloc[59:], rtol=0, atol=0)   # same z once the window is full
    t = 100                                                                    # hand-checked z
    x = np.log(env / overall).iloc[t - 59:t + 1]
    assert abs(a["z"].iloc[t] - (x.iloc[-1] - x.mean()) / x.std(ddof=1)) < 1e-10
    h = a["z"].iloc[:150].dropna().to_numpy()                                  # past-only threshold
    assert a["thr"].iloc[150] == np.quantile(h, 0.8) and a["n_prior_z"].iloc[150] == len(h)
    env4 = env.copy(); env4.iloc[150] *= 10
    a4 = attention_signal(env4, overall)
    pd.testing.assert_series_equal(a["thr"].iloc[:151], a4["thr"].iloc[:151])
    env2 = env.copy(); env2.iloc[[100, 101]] = 0.0                              # zeros dropped, not low
    c = attention_signal(env2, overall)
    assert c["z"].iloc[100:102].isna().all() and not c["extreme"].iloc[100:102].any()
    x2 = np.log((env2 / overall).where(env2 > 0)).iloc[102 - 59:103]
    assert abs(c["z"].iloc[102] - (x2.iloc[-1] - x2.mean()) / x2.std(ddof=1)) < 1e-10
    env3 = env.copy(); env3.iloc[150:157] = 0.0                                 # 7 zeros in 60 -> off
    d = attention_signal(env3, overall)
    assert not d["on"].iloc[150:210].any() and d["on"].iloc[210]
    assert (a["extreme"] == (a["z"] > a["thr"])).all()


# =============================================================================
# 3. leg_pipeline
# =============================================================================
def leg_pipeline(ff49, hedge_fac, brown=BROWN, beta_window=60, sd_window=36, vol_target=0.05):
    """
    Brown leg, rolling hedge, out-of-sample residual, sizing.

    Inputs
      ff49      : industry returns (decimal), month-end DatetimeIndex or a 'date' column.
      hedge_fac : the team's FF3 frame (Mkt-RF, SMB, HML, RF; decimal; month-end). It supplies R^B's RF,
                  the hedge regressors and the overlay factor returns. The attribution's `fac` (FF5+UMD)
                  never enters this function. An FF5 frame is refused.
      brown     : industries in the leg (pass four names for a leave-one-out rebuild).
    Outputs (DataFrame by month-end t)
      RB = mean(brown_t) - RF_t; f_<k> = hedge factor returns in t; a, b_<k> = OLS of RB on [1, f] over
      t-59..t; e = RB_t - a_{t-1} - b_{t-1}'f_t; sd = std(e_{t-35..t}, ddof=1);
      m = min(1, vol_target / (sqrt(12) sd_t)).
    Timing
      Row t uses data through t only; nothing is shifted forward. A position set at the end of t
      (size m_t, hedge b_t) earns in t+1: w_t RB_{t+1} - w_t b_t' f_{t+1}, with f_{t+1} from THIS frame.
    """
    if "date" in ff49.columns:
        ff49 = ff49.set_index("date")
    ff49 = ff49.copy()
    ff49.index = pd.DatetimeIndex(ff49.index)
    missing = [c for c in HEDGE_COLS + ["RF"] if c not in hedge_fac.columns]
    if missing:
        raise ValueError(f"hedge_fac lacks {missing}")
    if {"RMW", "CMA"} & set(hedge_fac.columns):
        raise ValueError("hedge_fac has RMW/CMA: that is the FF5 file; the team hedge uses its FF3 file")
    idx = ff49.index.intersection(hedge_fac.index).sort_values()
    per = idx.to_period("M").asi8
    if len(per) > 1 and (np.diff(per) != 1).any():
        raise ValueError("gaps in the monthly overlap of ff49 and hedge_fac")

    F = hedge_fac.loc[idx, HEDGE_COLS].astype(float)
    rb = ff49.loc[idx, list(brown)].mean(axis=1, skipna=False) - hedge_fac.loc[idx, "RF"]
    y = rb.to_numpy(float)
    X = np.column_stack([np.ones(len(idx)), F.to_numpy()])
    usable = np.isfinite(y) & np.isfinite(X).all(axis=1)
    coef = np.full((len(idx), 1 + len(HEDGE_COLS)), np.nan)
    for i in range(beta_window - 1, len(idx)):
        lo = i - beta_window + 1
        if usable[lo:i + 1].all():
            coef[i] = np.linalg.lstsq(X[lo:i + 1], y[lo:i + 1], rcond=None)[0]

    out = pd.DataFrame(index=idx)
    out["RB"] = rb
    for k in HEDGE_COLS:
        out[f"f_{k}"] = F[k]
    out["a"] = coef[:, 0]
    for j, k in enumerate(HEDGE_COLS):
        out[f"b_{k}"] = coef[:, j + 1]
    fit_prev = out["a"].shift(1) + sum(out[f"b_{k}"].shift(1) * out[f"f_{k}"] for k in HEDGE_COLS)
    out["e"] = out["RB"] - fit_prev
    out["sd"] = out["e"].rolling(sd_window, min_periods=sd_window).std(ddof=1)
    out["m"] = np.minimum(1.0, vol_target / (np.sqrt(12.0) * out["sd"]))
    return out


def test_leg_pipeline():
    raw = make_synthetic_inputs(seed=3)
    ff49, hf = raw["ff49"].set_index("date"), raw["hedge_fac"]
    leg = leg_pipeline(ff49, hf)
    T = pd.Timestamp("2000-06-30"); i = leg.index.get_loc(T); Tm1 = leg.index[i - 1]
    win = leg.index[i - 59:i + 1]
    Xw = np.column_stack([np.ones(60), hf.loc[win, HEDGE_COLS].to_numpy()])
    yw = (ff49.loc[win, BROWN].mean(axis=1) - hf.loc[win, "RF"]).to_numpy()
    bh = np.linalg.lstsq(Xw, yw, rcond=None)[0]
    assert np.allclose(leg.loc[T, ["a"] + [f"b_{k}" for k in HEDGE_COLS]].to_numpy(float), bh, rtol=0, atol=1e-12)
    e_hand = leg.at[T, "RB"] - leg.at[Tm1, "a"] - sum(leg.at[Tm1, f"b_{k}"] * hf.at[T, k] for k in HEDGE_COLS)
    assert abs(leg.at[T, "e"] - e_hand) < 1e-12                                 # residual uses t-1 coefficients
    ff49b, hfb = ff49.copy(), hf.copy()                                          # month T+1 cannot reach row T
    ff49b.loc[leg.index[i + 1], BROWN] += 0.2
    hfb.loc[leg.index[i + 1], HEDGE_COLS] += 0.2
    pd.testing.assert_frame_equal(leg.iloc[:i + 1], leg_pipeline(ff49b, hfb).iloc[:i + 1])
    hf2 = hf.copy()                                                              # hedge SMB moves b, not X
    hf2["SMB"] = hf2["SMB"] + 0.01 * np.random.default_rng(0).standard_normal(len(hf2))
    assert (leg_pipeline(ff49, hf2)["b_SMB"] - leg["b_SMB"]).abs().max() > 1e-3
    _, o1 = run_panel(raw, *TEST_WINDOW)
    _, o2 = run_panel(dict(raw, hedge_fac=hf2), *TEST_WINDOW)
    pd.testing.assert_frame_equal(o1["X"], o2["X"])
    try:
        leg_pipeline(ff49, raw["fac"])
    except ValueError:
        pass
    else:
        raise AssertionError("FF5 frame accepted as hedge_fac")


# =============================================================================
# 4. pass_fail_table
# =============================================================================
def _fin(v):
    try:
        return v is not None and bool(np.isfinite(float(v)))
    except (TypeError, ValueError):
        return False


def _fmt(v, spec=".6f"):
    return format(float(v), spec) if _fin(v) else "nan"


def pass_fail_table(alpha, t_alpha, p_alpha, shuffle_p, n_episodes, loo_alpha,
                    t_bar=2.0, p_bar=0.05, min_episodes=8, n_brown=5):
    """
    Inputs : alpha, t_alpha, p_alpha (NW(6) fit; p from t(n-k)), shuffle_p, n_episodes (merged holds),
             loo_alpha (Series of drop-one alphas indexed by the dropped industry).
    Output : DataFrame indexed (i), (ii), (iii), (iv), overall; columns name, statistic, bar, value,
             passed, result, detail.
    Timing : ex post summary of the single run.
    (iv)   : "keeps its sign" is read as "stays positive": the full alpha and all five drop-one alphas
             must be > 0. A negative alpha whose drop-one alphas are also negative fails. So does a
             missing or NaN drop-one alpha.
    """
    loo = pd.Series(loo_alpha, dtype=float)
    all_a = pd.concat([pd.Series({"full": alpha}, dtype=float), loo])
    ok1 = _fin(alpha) and _fin(t_alpha) and alpha > 0 and t_alpha >= t_bar
    ok2 = _fin(shuffle_p) and shuffle_p <= p_bar
    ok3 = _fin(n_episodes) and n_episodes >= min_episodes
    ok4 = len(loo) == n_brown and bool(all_a.notna().all()) and bool((all_a > 0).all())
    rows = [
        ("(i)", "timing alpha", "NW(6) t of alpha", f"alpha > 0 and t >= {t_bar:g}", t_alpha, ok1,
         f"alpha = {_fmt(alpha)}/month, p = {_fmt(p_alpha, '.4f')} (t, n-k df)"),
        ("(ii)", "calendar shuffle", "shuffle p", f"<= {p_bar:g}", shuffle_p, ok2, ""),
        ("(iii)", "independent episodes", "merged hold episodes", f">= {min_episodes}", n_episodes, ok3, ""),
        ("(iv)", "drop each Brown industry", "min(full, drop-one alphas)", f"> 0, all {n_brown + 1}",
         all_a.min() if len(all_a) else np.nan, ok4, ", ".join(f"{k}: {_fmt(v)}" for k, v in all_a.items())),
    ]
    n_pass = int(sum(r[5] for r in rows))
    rows.append(("overall", "verdict", "components passed", "4 of 4", n_pass, n_pass == 4, f"{n_pass} of 4"))
    t = pd.DataFrame(rows, columns=["component", "name", "statistic", "bar", "value", "passed", "detail"])
    t = t.set_index("component")
    t["result"] = np.where(t["passed"], "PASS", "FAIL")
    return t[["name", "statistic", "bar", "value", "passed", "result", "detail"]]


def test_pass_fail_table():
    pos, neg = pd.Series(0.002, index=BROWN), pd.Series(-0.001, index=BROWN)
    t = pass_fail_table(-0.002, -1.0, 0.3, 0.5, 5, neg)
    assert t.at["(iv)", "result"] == "FAIL" and t.at["overall", "result"] == "FAIL"   # the reported bug
    t = pass_fail_table(0.004, 2.0, 0.05, 0.05, 8, pos)                                # boundaries pass
    assert (t["result"] == "PASS").all()
    t = pass_fail_table(0.004, 2.5, 0.01, 0.01, 9, pd.Series([0.002] * 4 + [-1e-5], index=BROWN))
    assert t.at["(iv)", "result"] == "FAIL" and t.at["overall", "value"] == 3
    t = pass_fail_table(0.004, 2.5, 0.01, np.nan, 9, pos.iloc[:4])
    assert t.at["(ii)", "result"] == "FAIL" and t.at["(iv)", "result"] == "FAIL"
    t = pass_fail_table(0.004, 1.99, 0.05, 0.01, 7, pos)
    assert t.at["(i)", "result"] == "FAIL" and t.at["(iii)", "result"] == "FAIL"


# =============================================================================
# 5. check_no_lookahead
# =============================================================================
def check_no_lookahead(raw, run_fn, start, end, cut_to=None, delta=0.05, n_months=8, min_obs=48,
                       seed=0, tol=1e-10, state_cols=STATE_COLS, pos_of=POS_OF, brown=BROWN):
    """
    Look-ahead audit on both the state side and the return side.

    Inputs
      raw      : raw dict (read_raw / make_synthetic_inputs).
      run_fn   : raw -> panel by month-end t with w, w_ao (positions set at end of t), RT, RAO (net returns
                 earned in t), m, hold, b_<k> (end-of-t states).
      start,end: window audited.
      cut_to   : if given, every input is cut at this month BEFORE anything runs, so later data are never
                 loaded (seen mode: 2022-07-31).
    Tests (one report row per test and month T)
      post_window    inputs cut at `end`: all states and returns in the window identical.
      truncate       inputs cut at T: states through T-1 identical (the old check; T >= start + min_obs).
      rb_perturb     every Brown industry +delta in T: states and returns before T identical, and
                     RT_T moves by exactly w_{T-1}*delta (RAO_T by w_ao_{T-1}*delta).
      f_perturb      hedge-file Mkt-RF, SMB, HML +delta in T: same, with move -w_{T-1}*delta*sum_k b_{T-1,k}.
      signal_perturb EMVENRGYENVREG for T spiked: states through T and returns through T+1 identical,
                     because the value for T is usable only at the end of T+1.
      A month-t return hedged with b_t, or a position earning its own month, leaves every end-of-month
      state unchanged. Both do change how RT_T and RAO_T respond to month-T data, and the two perturb
      tests measure that response. D and alpha are not compared: pi is an ex post window constant by design.
    Months T : fixed-seed draw of up to n_months each from hold entries/exits, held months (w_{T-1} != 0)
               and flat months (w_{T-1} = w_T = 0) inside the window.
    Output   : (report DataFrame, ok). Stop if ok is False.
    """
    start, end = pd.Timestamp(start), pd.Timestamp(end)
    if cut_to is not None:
        raw = truncate_raw(raw, cut_to)
        end = min(end, pd.Timestamp(cut_to))
    rows = []

    def add(test, T, pre, err):
        rows.append(dict(test=test, month=T, pre_diff=pre, ret_err=err, passed=bool(pre <= tol and err <= tol)))

    ret_cols = list(pos_of)
    all_cols = state_cols + ret_cols
    base = run_fn(raw)
    if _last_date(raw) > end:
        add("post_window", end, _maxdiff(base.loc[start:end], run_fn(truncate_raw(raw, end)), all_cols), 0.0)

    w, wprev = base["w"], base["w"].shift(1)
    inwin = base.index.to_series().between(start, end)
    groups = {
        "change": inwin & (w != wprev) & ((w == 0) | (wprev == 0)) & wprev.notna(),
        "held": inwin & (wprev != 0) & wprev.notna(),
        "flat": inwin & (wprev == 0) & (w == 0),
    }
    rng = np.random.default_rng(seed)
    months = pd.DatetimeIndex([])
    for mask in groups.values():
        ix = base.index[mask.to_numpy()]
        if len(ix) > n_months:
            ix = ix[np.sort(rng.choice(len(ix), n_months, replace=False))]
        months = months.union(ix)
    if len(months) == 0:
        add("coverage", pd.NaT, np.inf, 0.0)

    for T in months:
        pos = base.index.get_loc(T)
        Tm1, Tp1 = base.index[pos - 1], base.index[min(pos + 1, len(base) - 1)]
        before = base.loc[start:Tm1]
        if T >= start + pd.DateOffset(months=min_obs):
            add("truncate", T, _maxdiff(before, run_fn(truncate_raw(raw, T)), state_cols), 0.0)

        p = run_fn(_bump(raw, "ff49", T, list(brown), lambda v: v + delta))
        exp = {r: base.at[Tm1, c] * delta for r, c in pos_of.items()}
        add("rb_perturb", T, _maxdiff(before, p, all_cols), _ret_err(base, p, T, exp))

        p = run_fn(_bump(raw, "hedge_fac", T, HEDGE_COLS, lambda v: v + delta))
        bsum = sum(base.at[Tm1, f"b_{k}"] for k in HEDGE_COLS)
        exp = {r: -base.at[Tm1, c] * delta * bsum for r, c in pos_of.items()}
        add("f_perturb", T, _maxdiff(before, p, all_cols), _ret_err(base, p, T, exp))

        p = run_fn(_bump(raw, "EMVENRGYENVREG", T, ["EMVENRGYENVREG"], lambda v: 5.0 * v + 0.5))
        pre = max(_maxdiff(base.loc[start:T], p, state_cols), _maxdiff(base.loc[start:Tp1], p, ret_cols))
        add("signal_perturb", T, pre, 0.0)

    rep = pd.DataFrame(rows)
    return rep, bool(len(rep)) and bool(rep["passed"].all())


def _fred_month_end(df, sid):
    s = df.set_index("observation_date")[sid].astype(float)
    s.index = pd.DatetimeIndex(s.index) + pd.offsets.MonthEnd(0)
    return s


def _toy_run(raw, bug=None):
    """Minimal pipeline used only to test the auditor. bug: None, 'hedge_bt' (month-t return hedged with b_t),
    'own_month' (position set at end of t earns month t), 'signal_lag' (extreme flag of t used at end of t)."""
    leg = leg_pipeline(raw["ff49"], raw["hedge_fac"])
    sig = attention_signal(_fred_month_end(raw["EMVENRGYENVREG"], "EMVENRGYENVREG"),
                           _fred_month_end(raw["EMVOVERALLEMV"], "EMVOVERALLEMV"))
    ext = sig["extreme"].reindex(leg.index, fill_value=False).astype(bool)
    cross = ext & ~ext.shift(1, fill_value=False)
    usable = cross if bug == "signal_lag" else cross.shift(1, fill_value=False)
    hold = usable.astype(float).rolling(6, min_periods=1).max().astype(bool)
    m = leg["m"].fillna(0.0)
    B = leg[[f"b_{k}" for k in HEDGE_COLS]].fillna(0.0)
    F = leg[[f"f_{k}" for k in HEDGE_COLS]].to_numpy()
    panel = pd.DataFrame({"m": leg["m"], "hold": hold}, index=leg.index)
    for k in HEDGE_COLS:
        panel[f"b_{k}"] = leg[f"b_{k}"]
    for wcol, rcol, wpos in (("w", "RT", -m.where(hold, 0.0)), ("w_ao", "RAO", -m)):
        panel[wcol] = wpos
        if bug == "own_month":
            p, bb = wpos, B.shift(1)
        elif bug == "hedge_bt":
            p, bb = wpos.shift(1), B
        else:
            p, bb = wpos.shift(1), B.shift(1)
        gross = p * (leg["RB"] - (bb.to_numpy() * F).sum(axis=1))
        ov = B.mul(wpos, axis=0)
        trade = (0.0010 * wpos.diff().abs() + 0.0005 * ov["b_Mkt-RF"].diff().abs()
                 + 0.0025 * (ov["b_SMB"].diff().abs() + ov["b_HML"].diff().abs()))
        panel[rcol] = gross - trade.shift(1)                  # trade at end of t pays in t+1
    return panel


def test_check_no_lookahead():
    raw = make_synthetic_inputs(seed=0)
    kw = dict(start="1995-01-31", end="2009-12-31", n_months=4)
    rep, ok = check_no_lookahead(raw, _toy_run, **kw)
    assert ok, rep.loc[~rep["passed"]]
    for bug, must_fail in (("hedge_bt", {"rb_perturb", "f_perturb"}),
                           ("own_month", {"rb_perturb", "f_perturb"}),
                           ("signal_lag", {"signal_perturb"})):
        rep, ok = check_no_lookahead(raw, lambda r, b=bug: _toy_run(r, bug=b), **kw)
        failed = set(rep.loc[~rep["passed"], "test"])
        assert not ok and must_fail <= failed, (bug, failed)
        assert rep.loc[rep["test"] == "truncate", "passed"].all(), bug   # the old state-only check misses all three


def test_seen_cut():
    raw = make_synthetic_inputs(seed=0)
    assert _last_date(raw) > pd.Timestamp("2022-12-31")
    assert _last_date(truncate_raw(raw, SEEN_WINDOW[1])) <= pd.Timestamp("2022-07-31")


def run_unit_tests():
    for f in (test_attention_signal, test_pass_fail_table, test_seen_cut, test_leg_pipeline,
              test_check_no_lookahead, test_make_synthetic_inputs):
        f()
        print(f"{f.__name__}: ok")


# =============================================================================
# 6. __main__
# =============================================================================
if __name__ == "__main__":
    MODE = "synthetic"                 # "synthetic" -> "seen" -> "test"
    Z_BURN_IN = "nonzero"              # your reading; "calendar" reproduces my previous version
    WINDOWS = {"synthetic": TEST_WINDOW, "seen": SEEN_WINDOW, "test": TEST_WINDOW}
    PATHS = {"ff49": "ff49_industry_monthly.csv", **{sid: f"{sid}.csv" for sid in FRED_IDS}}
    fac = None                         # <- your FF5+UMD frame, as before
    hedge_fac = None                   # <- NEW: the team's FF3 frame (Mkt-RF, SMB, HML, RF), decimals

    start, end = WINDOWS[MODE]
    if MODE == "synthetic":
        run_unit_tests()
        raw = make_synthetic_inputs(seed=0)
    else:
        if fac is None or hedge_fac is None:
            sys.exit("Set `fac` (FF5+UMD) and `hedge_fac` (team FF3) first.")
        raw = read_raw(PATHS, fac, hedge_fac)

    cut_to = end if MODE == "seen" else None
    if cut_to is not None:
        raw = truncate_raw(raw, cut_to)            # nothing after 2022-07 reaches the audit or the run

    rep, ok = check_no_lookahead(raw, lambda r: run_panel(r, start, end, z_burn_in=Z_BURN_IN)[0],
                                 start, end, cut_to=cut_to)
    print(rep.groupby("test")["passed"].agg(["size", "sum"]).to_string())
    if not ok:
        print(rep.loc[~rep["passed"]].to_string())
        sys.exit("STOP: look-ahead audit failed.")

    run_panel(raw, start, end, z_burn_in=Z_BURN_IN, n_shuffle=5000, loo=True, verbose=True)  # prints the five tables
