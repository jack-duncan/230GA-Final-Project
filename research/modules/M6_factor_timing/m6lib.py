"""Helpers for M6_factor_timing: predictor construction, walk-forward ridge with time-series CV,
Campbell-Thompson / Clark-West statistics, timing portfolios with industry-level turnover, an
LMN (2024) portfolio-shrinkage variant, and an exploratory pooled-ridge industry-rotation panel.

Timing convention used everywhere in this module:
  a row indexed by month-end t holds predictors known at the END of month t; its target is the
  return earned in month t+1. Output series are re-indexed by the target month (the month the
  return is earned), so they line up with the Green-minus-Brown return series itself.
"""
from __future__ import annotations
import sys, pathlib
HERE = pathlib.Path(__file__).resolve().parent
LIB = HERE.parents[1] / "lib"
for p in (str(LIB), str(HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)
import numpy as np
import pandas as pd
from scipy import stats
from common import (load_team, legs_by_emissions, leg_returns, load_ff5_mom, load_kf_ff3, load_kf_industries,
                    load_fred, load_mccc, load_emv_env, nw_ols, perf, alpha_row, PERIODS, LAST_MONTH, rolling_z, holm, bh,
                    TABLES)

MOD = "M6_factor_timing"
ME1 = pd.offsets.MonthEnd(1)
LAMBDA_GRID = np.r_[np.logspace(-4, 3, 36), 1e6]      # ridge penalty grid (per-observation scaling), 1e6 ~ historical mean
CV_FIRST, CV_BLOCK = 60, 12                            # expanding CV folds: first fold trains on 60 months, 12-month blocks
COST = 10e-4                                           # 10 bp per unit of traded notional
TARGET_VOL = 0.05
FF6 = ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "UMD"]

LABELS = {"VS": "Value spread (G-B log BE/ME)", "VS_m": "Value spread, monthly price-updated",
          "MOM12": "G-B trailing 12m return", "TERM": "Term spread GS10-TB3MS", "CREDIT": "Credit spread BAA-AAA",
          "DGS10": "12m change in GS10", "INFL": "CPI inflation YoY (lag 1)", "CFNAI": "CFNAI (lag 1)",
          "WTI": "WTI 12m log return", "LVIX": "log VIX", "ATTN": "Attention z (team signal)",
          "ATTN_l1": "Attention z, lagged 1m", "MCCC": "log MCCC (lag 0)"}


# =============================================================================================== data
def gb_legs():
    t = load_team()
    g, b = legs_by_emissions(5, t["emissions"])
    G, B, GB = leg_returns(t["industries"], g, b)
    return t, g, b, GB.loc[:LAST_MONTH]


def monthly_from_june(annual: pd.DataFrame | pd.Series, end="2026-12-31"):
    """Ken French annual BE/ME rows indexed at June 30 of formation year Y -> monthly, first usable at END of July Y
    (so first used for the August Y return), carried forward for at most 12 months."""
    a = annual.copy()
    a.index = a.index + ME1                                   # June 30 Y -> July 31 Y
    idx = pd.date_range(a.index.min(), end, freq="ME")
    return a.reindex(idx).ffill(limit=11)


def build_predictors(green, brown, industries, GB):
    """All candidate predictors, each known at the end of month t (row t). See LABELS."""
    bm = load_kf_industries("be_me_sum")
    logbm = np.log(bm.where(bm > 0))
    vs_annual = logbm[green].mean(axis=1) - logbm[brown].mean(axis=1)
    VS = monthly_from_june(vs_annual)

    # monthly price-updated value spread (robustness): log BM_{i,t} = log BM_{i,Y} - sum_{s=Jan Y..t} log(1+r_{i,s})
    lb = monthly_from_june(logbm[green + brown])
    C = np.log1p(industries[green + brown]).cumsum()
    anchor_year = np.where(lb.index.month >= 7, lb.index.year - 1, lb.index.year - 2)   # Dec of Y-1, Y = formation year
    anchor = pd.to_datetime([f"{y}-12-31" for y in anchor_year])
    Ca = C.reindex(anchor).values
    lbm_m = lb - (C.reindex(lb.index).values - Ca)
    VS_m = lbm_m[green].mean(axis=1) - lbm_m[brown].mean(axis=1)

    MOM12 = np.expm1(np.log1p(GB).rolling(12).sum())
    gs10, tb3, baa, aaa = load_fred("GS10"), load_fred("TB3MS"), load_fred("BAA"), load_fred("AAA")
    cpi, cfnai = load_fred("CPIAUCSL"), load_fred("CFNAI")
    wti = load_team()["macro"]["wti"]                      # identical to FRED MCOILWTICO, 1986-01 onward
    vix = load_fred("VIXCLS", "last")
    emv = load_emv_env()
    X = pd.DataFrame({
        "VS": VS, "VS_m": VS_m, "MOM12": MOM12,
        "TERM": gs10 - tb3, "CREDIT": baa - aaa, "DGS10": gs10.diff(12),
        # CPI for t-1 is released during month t; Oct-2025 CPI was never published, so carry the last print forward
        "INFL": np.log(cpi).diff(12).shift(1).ffill(limit=1),
        "CFNAI": cfnai.shift(1),                           # CFNAI for t-1 is released near the end of month t
        "WTI": np.log(wti).diff(12), "LVIX": np.log(vix),
        "ATTN": rolling_z(np.log1p(emv)), "MCCC": np.log(load_mccc()),
    })
    X["ATTN_l1"] = X["ATTN"].shift(1)
    return X.loc[:"2026-08-31"]


# =============================================================================================== ridge
def _ridge_all(Xtr, ytr, grid):
    """Standardize with training moments, return (mu, sd, intercept, B[p x L]) for every penalty in grid.
    Objective: (1/n)||y - a - Zb||^2 + lam ||b||^2, intercept unpenalized."""
    mu = Xtr.mean(0); sd = Xtr.std(0); sd = np.where(sd > 0, sd, 1.0)
    Z = (Xtr - mu) / sd
    ybar = ytr.mean(); yc = ytr - ybar; n = len(ytr)
    U, s, Vt = np.linalg.svd(Z, full_matrices=False)
    fac = s[:, None] / (s[:, None] ** 2 + n * np.asarray(grid)[None, :])
    B = Vt.T @ (fac * (U.T @ yc)[:, None])
    return mu, sd, ybar, B


def walk_forward_ridge(X: pd.DataFrame, y: pd.Series, oos_start: str, grid=LAMBDA_GRID, fixed_lambda=None,
                       first=CV_FIRST, block=CV_BLOCK, last_target=LAST_MONTH, recent=None):
    """Monthly-refit expanding-window ridge. X rows = origins t (predictors known at t), y[t] = return in t+1.
    At origin t: training rows are origins s < t (targets realized by t). Penalty chosen by expanding-fold
    time-series CV inside the training rows (12-month validation blocks after the first 60 rows; each block is
    predicted by a model fit, and standardized, on rows strictly before the block; pooled validation MSE; ties
    go to the larger penalty). recent=m (CV-design sensitivity only): keep only the validation blocks that end
    inside the last m training rows, i.e. validate on the most recent m months instead of all blocks.
    Returns DataFrame indexed by TARGET month."""
    d = pd.concat([X, y.rename("__y")], axis=1)
    d = d.loc[d[X.columns].notna().all(axis=1)]
    Xv, yv, rows = d[X.columns].to_numpy(float), d["__y"].to_numpy(float), d.index
    grid = np.asarray(grid if fixed_lambda is None else [fixed_lambda], float)
    cache, out = {}, []
    oos_start = pd.Timestamp(oos_start)
    for k, t in enumerate(rows):
        tgt = t + ME1
        if tgt < oos_start or tgt > pd.Timestamp(last_target):
            continue
        Xtr, ytr = Xv[:k], yv[:k]
        if np.isnan(ytr).any():
            raise ValueError(f"missing target inside training window at origin {t}")
        if fixed_lambda is None and len(grid) > 1:
            sse = np.zeros(len(grid))
            for v in range(first, k, block):
                e = min(v + block, k)
                if recent is not None and e <= k - recent:
                    continue
                key = (v, e)
                if key not in cache:
                    mu, sd, a, B = _ridge_all(Xtr[:v], ytr[:v], grid)
                    pred = a + ((Xtr[v:e] - mu) / sd) @ B
                    cache[key] = ((ytr[v:e, None] - pred) ** 2).sum(0)
                sse += cache[key]
            j = np.flatnonzero(sse <= sse.min() * (1 + 1e-12)).max()
            lam = grid[j]
        else:
            lam = grid[0]
        mu, sd, a, B = _ridge_all(Xtr, ytr, np.array([lam]))
        b = B[:, 0]
        f = a + ((Xv[k] - mu) / sd) @ b
        rec = {"date": tgt, "origin": t, "y": yv[k], "forecast": f, "hist_mean": ytr.mean(), "lambda": lam,
               "lambda_at_max": bool(lam >= grid.max()) and len(grid) > 1, "n_train": k}
        rec.update({f"b_{c}": bb for c, bb in zip(X.columns, b)})
        out.append(rec)
    return pd.DataFrame(out).set_index("date")


def ridge_path(X: pd.DataFrame, y: pd.Series, grid):
    """Full-sample coefficient path (standardized predictors), for interpretation only."""
    d = pd.concat([X, y.rename("__y")], axis=1).dropna()
    mu, sd, a, B = _ridge_all(d[X.columns].to_numpy(float), d["__y"].to_numpy(float), grid)
    return pd.DataFrame(B.T, index=pd.Index(grid, name="lambda"), columns=X.columns), d.index


def cv_curve_full(X, y, grid, first=CV_FIRST, block=CV_BLOCK):
    d = pd.concat([X, y.rename("__y")], axis=1).dropna()
    Xv, yv = d[X.columns].to_numpy(float), d["__y"].to_numpy(float)
    sse = np.zeros(len(grid))
    for v in range(first, len(yv), block):
        e = min(v + block, len(yv))
        mu, sd, a, B = _ridge_all(Xv[:v], yv[:v], grid)
        sse += ((yv[v:e, None] - (a + ((Xv[v:e] - mu) / sd) @ B)) ** 2).sum(0)
    return pd.Series(sse / (len(yv) - first), index=grid, name="cv_mse")


# =============================================================================================== OOS statistics
def oos_stats(y, f_model, f_bench, lags=6):
    """Campbell-Thompson OOS R2 of f_model vs f_bench and the Clark-West (2007) adjusted-MSPE test
    (H0: equal MSPE of nested models; one-sided H1: model better). NW(lags) t-stat on the CW series."""
    d = pd.concat([y.rename("y"), f_model.rename("m"), f_bench.rename("b")], axis=1).dropna()
    em, eb = d["y"] - d["m"], d["y"] - d["b"]
    r2 = 1 - (em ** 2).sum() / (eb ** 2).sum()
    fcw = eb ** 2 - (em ** 2 - (d["b"] - d["m"]) ** 2)
    if fcw.std() > 0 and len(fcw) > 3:
        t = float(nw_ols(fcw, lags=min(lags, max(len(fcw) // 4, 1))).tvalues.iloc[0])
    else:
        t = np.nan
    p1 = 1 - stats.norm.cdf(t) if np.isfinite(t) else np.nan
    p2 = 2 * (1 - stats.norm.cdf(abs(t))) if np.isfinite(t) else np.nan
    return {"n": len(d), "start": d.index.min(), "end": d.index.max(), "r2_oos": r2, "cw_t": t,
            "cw_p_one_sided": p1, "cw_p_two_sided": p2,
            "mse_model_x1e4": 1e4 * (em ** 2).mean(), "mse_bench_x1e4": 1e4 * (eb ** 2).mean(),
            "corr_forecast_realized": d["m"].corr(d["y"]),
            "dir_accuracy": float((np.sign(d["m"] - d["b"]) == np.sign(d["y"] - d["b"])).mean())}


def period_windows(oos_start, extra=("post2010", "validation", "holdout", "covid", "inflation_rates", "last18", "last12")):
    w = {"full_oos": (pd.Timestamp(oos_start), LAST_MONTH)}
    for p in extra:
        a, b = PERIODS[p]
        w[p] = (max(pd.Timestamp(a), pd.Timestamp(oos_start)), pd.Timestamp(b))
    return w


# =============================================================================================== portfolios
def leg_positions(w: pd.Series, green, brown):
    """Industry positions implied by weight w on the GB spread (equal-weighted legs)."""
    H = pd.DataFrame(index=w.index)
    for i in green:
        H[i] = w / len(green)
    for i in brown:
        H[i] = -w / len(brown)
    return H


def industry_turnover(H: pd.DataFrame, R: pd.DataFrame):
    """Monthly turnover (sum |trade| per unit NAV) of positions H[m] held during month m, set at the end of m-1.
    Pre-trade weights drift with the month m-1 returns. The first month's initial build is excluded (NaN)."""
    R = R.reindex(H.index)[H.columns]
    Hp = H.shift(1)
    port = (Hp * R.shift(1)).sum(axis=1, min_count=1)
    drifted = Hp.mul(1 + R.shift(1)).div(1 + port, axis=0)
    to = (H - drifted).abs().sum(axis=1, min_count=1)
    to.iloc[0] = np.nan
    return to


def scaled_strategy(w_raw: pd.Series, GB: pd.Series, industries, green, brown, scale_window, cost=COST,
                    target_vol=TARGET_VOL, scale=None):
    """w_raw indexed by target month. Constant ex-post scale so that gross returns have target_vol over scale_window
    (Sharpe ratios and each strategy's own t-stats are invariant to this constant; a DIFFERENCE between two
    strategies is not). scale=k overrides the vol-targeting constant (used for the scaling-sensitivity check)."""
    w_raw = w_raw.dropna()
    g = (w_raw * GB.reindex(w_raw.index))
    a, b = scale_window
    k = target_vol / (np.sqrt(12) * g.loc[a:b].std(ddof=1)) if scale is None else float(scale)
    w = k * w_raw
    H = leg_positions(w, green, brown)
    to = industry_turnover(H, industries)
    gross = w * GB.reindex(w.index)
    net = gross - cost * to.fillna(0)
    return pd.DataFrame({"w": w, "gross": gross, "net": net, "turnover": to,
                         "timing_turnover": 2 * w.diff().abs(), "scale": k})


def perf_block(df: pd.DataFrame, factors: pd.DataFrame, windows: dict, label: str, lags=6):
    rows = []
    for pname, (a, b) in windows.items():
        s = df.loc[a:b]
        if len(s) < 3:
            continue
        pg, pn = perf(s["gross"], lags), perf(s["net"], lags)
        row = {"strategy": label, "period": pname, "start": s.index.min().strftime("%Y-%m"),
               "end": s.index.max().strftime("%Y-%m"), "n": pg["n"],
               "ann_ret_gross": pg["ann_ret"], "ann_ret_net": pn["ann_ret"], "ann_vol": pg["ann_vol"],
               "sharpe_gross": pg["sharpe"], "sharpe_net": pn["sharpe"], "t_mean_gross": pg["t_mean_nw"],
               "t_mean_net": pn["t_mean_nw"], "max_dd_net": pn["max_dd"], "hit_rate_net": pn["hit_rate"],
               "turnover_ann": 12 * s["turnover"].mean(), "timing_turnover_ann": 12 * s["timing_turnover"].mean(),
               "cost_drag_bp_ann": 1e4 * 12 * COST * s["turnover"].mean(), "mean_w": s["w"].mean(),
               "frac_long": float((s["w"] > 0).mean())}
        if len(s) >= 24:
            for kind in ("gross", "net"):
                ar = alpha_row(s[kind], factors.reindex(s.index)[FF6], lags)
                row[f"alpha_ff6_{kind}"] = ar["alpha_ann"]; row[f"t_alpha_ff6_{kind}"] = ar["t_alpha"]
            row["r2_ff6"] = ar["r2"]
        rows.append(row)
    return rows


def ff6_loadings(r: pd.Series, factors: pd.DataFrame, label: str, lags=6):
    ar = alpha_row(r.dropna(), factors.reindex(r.dropna().index)[FF6], lags)
    ar["strategy"] = label
    return ar


# =============================================================================================== team target
def team_brown_residual(brown, window=60):
    """The team's trading target, rebuilt exactly as in notebooks/climate_alpha_analysis.py (rolling_factor_model):
    Brown-leg excess return (equal-weighted Brown industries minus RF, team FF3 file) regressed on Mkt-RF, SMB, HML
    over a trailing 60-month window ending at t; intercept and betas shifted one month before use, so
      eps_t = r_brown,t - alpha_{t-1} - beta_{t-1}' F_t
    uses no information from month t in the hedge. Returns eps indexed by the month it is realized."""
    t = load_team()
    ff3, R = t["ff3"], t["industries"]
    cols = ["Mkt-RF", "SMB", "HML"]
    yb = (R[brown].mean(axis=1) - ff3["RF"]).rename("y")
    data = pd.concat([yb, ff3[cols]], axis=1).dropna()
    coef = pd.DataFrame(np.nan, index=data.index, columns=["const"] + cols)
    Xall, yall = data[cols].to_numpy(float), data["y"].to_numpy(float)
    for end in range(window - 1, len(data)):
        Xw = np.column_stack([np.ones(window), Xall[end - window + 1:end + 1]])
        coef.iloc[end] = np.linalg.lstsq(Xw, yall[end - window + 1:end + 1], rcond=None)[0]
    used = coef.shift(1)
    hedged = data["y"] - (used[cols] * data[cols]).sum(axis=1, min_count=len(cols))
    return (hedged - used["const"]).rename("eps_brown").loc[:LAST_MONTH]


# =============================================================================================== LMN (2024) variant
def lmn_timing(X: pd.DataFrame, y: pd.Series, lam_grid, first_train=119, normalize=True):
    """Lehnherr-Mehta-Nagel (2024) portfolio-shrinkage timing for ONE factor (K=1).
    Timing portfolios G_j = z_{j,t} * F_{t+1} plus the factor itself (j=0). At each December origin with at least
    first_train training rows: standardize predictors with training moments, mu = mean(G), Sigma = Ledoit-Wolf
    (shrink to scaled identity), D = diag(Sigma), w0 = (mu_0, 0, ..., 0),
      w(lam) = (Sigma + lam/T * D)^{-1} (mu + lam/T * w0).
    Implied factor weight h_t = w_0 + sum_j w_j z_{j,t}; with K=1 LMN's rotation normalization |h|=1 gives sign(h).
    lam chosen to maximize the Sharpe ratio over all earlier 12-month validation blocks (expanding, as in their
    Figure 1). The first block is validation only. Weights refit annually and held for the next 12 origins."""
    from sklearn.covariance import LedoitWolf
    d = pd.concat([X, y.rename("__y")], axis=1)
    d = d.loc[d[X.columns].notna().all(axis=1)]
    Xv, yv, rows = d[X.columns].to_numpy(float), d["__y"].to_numpy(float), d.index
    lam_grid = np.asarray(lam_grid, float)
    refits = [k for k, t in enumerate(rows) if t.month == 12 and k >= first_train]
    blocks = []   # (refit k, application rows, H[L x rows])
    for k in refits:
        Xtr, ytr = Xv[:k], yv[:k]
        mu_x = Xtr.mean(0); sd_x = Xtr.std(0); sd_x = np.where(sd_x > 0, sd_x, 1)
        Z = (Xtr - mu_x) / sd_x
        G = np.column_stack([ytr, Z * ytr[:, None]])
        T = len(ytr)
        mu = G.mean(0)
        S = LedoitWolf().fit(G).covariance_
        D = np.diag(np.diag(S))
        w0 = np.zeros_like(mu); w0[0] = mu[0]
        app = np.arange(k, min(k + 12, len(rows)))
        Za = (Xv[app] - mu_x) / sd_x
        Hs = []
        for lam in lam_grid:
            w = np.linalg.solve(S + lam / T * D, mu + lam / T * w0)
            h = w[0] + Za @ w[1:]
            Hs.append(np.sign(h) if normalize else h)
        blocks.append((k, app, np.array(Hs)))
    out = []
    for m, (k, app, Hs) in enumerate(blocks):
        if m == 0:
            continue
        past_r = np.concatenate([Hs_p * yv[app_p][None, :] for (_, app_p, Hs_p) in blocks[:m]], axis=1)
        past_r = past_r[:, ~np.isnan(past_r).any(axis=0)]
        sr = past_r.mean(1) / np.where(past_r.std(1) > 0, past_r.std(1), np.nan)
        sr = np.where(np.isfinite(sr), sr, -np.inf)
        j = int(np.flatnonzero(sr >= sr.max() - 1e-12).max())
        for jj, r in enumerate(app):
            tgt = rows[r] + ME1
            if tgt > LAST_MONTH:
                continue
            out.append({"date": tgt, "h": Hs[j, jj], "lambda": lam_grid[j], "y": yv[r]})
    return pd.DataFrame(out).set_index("date")


# =============================================================================================== industry panel
def industry_panel(start="1970-01-31", macro_cols=("TERM", "CREDIT", "INFL")):
    """Exploratory pooled panel. Rows (t, industry): target = industry excess return in t+1 minus beta_t * MKT_{t+1}
    (beta from 60m rolling regression through t), demeaned across industries within month (month fixed effects).
    Features: cross-sectional z-scores (winsorized at +/-3) of log BE/ME (Ken French, usable from end of July),
    12-1 momentum (months t-11..t-1), log average firm size; plus their interactions with point-in-time expanding
    z-scores of the macro variables (moments through t, >= 60 months of history)."""
    t = load_team(); R = t["industries"].loc[:LAST_MONTH]
    ff = load_kf_ff3()
    ex = R.sub(ff["RF"].reindex(R.index), axis=0)
    mkt = ff["Mkt-RF"].reindex(R.index)
    mx = mkt.rolling(60, min_periods=36)
    cov = (ex.mul(mkt, axis=0)).rolling(60, min_periods=36).mean() - ex.rolling(60, min_periods=36).mean().mul(mx.mean(), axis=0)
    beta = cov.div(mx.var(ddof=0), axis=0)
    resid_next = ex.shift(-1) - beta.mul(mkt.shift(-1), axis=0)
    bm = load_kf_industries("be_me_sum")
    logbm = monthly_from_june(np.log(bm.where(bm > 0)))
    mom = np.expm1(np.log1p(R).shift(1).rolling(11, min_periods=11).sum())
    size = np.log(load_kf_industries("size").where(lambda s: s > 0))
    gs10, tb3, baa, aaa, cpi = (load_fred(s) for s in ("GS10", "TB3MS", "BAA", "AAA", "CPIAUCSL"))
    macro = pd.DataFrame({"TERM": gs10 - tb3, "CREDIT": baa - aaa, "INFL": np.log(cpi).diff(12).shift(1).ffill(limit=1),
                          "CFNAI": load_fred("CFNAI").shift(1)})[list(macro_cols)]
    macro_z = (macro - macro.expanding(60).mean()) / macro.expanding(60).std()
    dates = R.loc[start:].index
    logbm, size = logbm.reindex(dates)[R.columns], size.reindex(dates)[R.columns]
    Rnext = R.shift(-1)
    recs = []
    for d in dates:
        f = pd.DataFrame({"logbm": logbm.loc[d], "mom": mom.loc[d], "size": size.loc[d],
                          "y": resid_next.loc[d], "ret_next": Rnext.loc[d]})
        f = f.dropna(subset=["logbm", "mom", "size"])
        if len(f) < 20:
            continue
        for c in ("logbm", "mom", "size"):
            z = (f[c] - f[c].mean()) / f[c].std()
            f[c + "_z"] = z.clip(-3, 3)
        f["mom_raw"] = f["mom"]
        f["date"] = d; f["industry"] = f.index
        for m in macro_cols:
            mz = macro_z.loc[d, m]
            for c in ("logbm", "mom", "size"):
                f[f"{c}_x_{m}"] = f[c + "_z"] * mz
        recs.append(f)
    P = pd.concat(recs, ignore_index=True)
    feats = ["logbm_z", "mom_z", "size_z"] + [f"{c}_x_{m}" for m in macro_cols for c in ("logbm", "mom", "size")]
    P = P.dropna(subset=feats)
    # cross-sectionally demean target within the estimation universe (industries with features and a target)
    ok = P["y"].notna()
    P.loc[ok, "y_dm"] = P.loc[ok, "y"] - P.loc[ok].groupby("date")["y"].transform("mean")
    return P, feats


def panel_walk_forward(P: pd.DataFrame, feats, oos_start, grid=LAMBDA_GRID, first=CV_FIRST, block=CV_BLOCK):
    """Pooled ridge (no intercept: target and features are cross-sectionally centered) with monthly expanding refits
    and expanding-fold time-series CV over months, computed from per-month sufficient statistics."""
    dates = np.array(sorted(P["date"].unique()))
    p = len(feats)
    S = np.zeros((len(dates), p, p)); s = np.zeros((len(dates), p)); yy = np.zeros(len(dates)); nn = np.zeros(len(dates))
    groups = {d: g for d, g in P.groupby("date")}
    for i, d in enumerate(dates):
        g = groups[d]; g = g[g["y_dm"].notna()]
        if len(g) == 0:
            continue
        Xg = g[feats].to_numpy(float); yg = g["y_dm"].to_numpy(float)
        S[i] = Xg.T @ Xg; s[i] = Xg.T @ yg; yy[i] = yg @ yg; nn[i] = len(g)
    cS, cs, cn = np.cumsum(S, 0), np.cumsum(s, 0), np.cumsum(nn)

    def fit(k, lam):          # coefficients using months 0..k-1
        A, bvec, N = cS[k - 1] / cn[k - 1], cs[k - 1] / cn[k - 1], cn[k - 1]
        ev, Q = np.linalg.eigh(A)
        qb = Q.T @ bvec
        return Q @ (qb[:, None] / (ev[:, None] + np.asarray(lam)[None, :]))   # p x L

    cache, out = {}, []
    oos_start = pd.Timestamp(oos_start)
    for k, d in enumerate(dates):
        d = pd.Timestamp(d); tgt = d + ME1
        if tgt < oos_start or tgt > LAST_MONTH:
            continue
        sse = np.zeros(len(grid))
        for v in range(first, k, block):
            e = min(v + block, k)
            if (v, e) not in cache:
                B = fit(v, grid)
                Sb, sb, yb = S[v:e].sum(0), s[v:e].sum(0), yy[v:e].sum()
                cache[(v, e)] = yb - 2 * sb @ B + np.einsum("pl,pq,ql->l", B, Sb, B)
            sse += cache[(v, e)]
        j = np.flatnonzero(sse <= sse.min() * (1 + 1e-12)).max()
        b = fit(k, [grid[j]])[:, 0]
        g = groups[d].copy()
        g["forecast"] = g[feats].to_numpy(float) @ b
        g["lambda"] = grid[j]; g["target_date"] = tgt
        out.append(g)
    return pd.concat(out, ignore_index=True)


def long_short(F: pd.DataFrame, score: str, n=8):
    """Equal-weighted long top-n / short bottom-n by score within each origin month. Returns weights (target-month
    index x industry) and the portfolio return series."""
    W = {}
    for tgt, g in F.groupby("target_date"):
        g = g.dropna(subset=[score, "ret_next"]).sort_values(score)
        w = pd.Series(0.0, index=g["industry"].values)
        w.iloc[-n:] = 1.0 / n; w.iloc[:n] = -1.0 / n
        W[tgt] = w
    W = pd.DataFrame(W).T.fillna(0.0).sort_index()
    W.index = pd.DatetimeIndex(W.index)
    return W


def ls_returns(W: pd.DataFrame, R: pd.DataFrame, cost=COST):
    Rn = R.reindex(W.index)[W.columns]
    gross = (W * Rn).sum(axis=1)
    to = industry_turnover(W, R)
    return pd.DataFrame({"w": 1.0, "gross": gross, "net": gross - cost * to.fillna(0), "turnover": to,
                         "timing_turnover": np.nan})


# =============================================================================================== output helpers
def to_tex(df: pd.DataFrame, name: str, caption: str, label: str, digits=None, index=False):
    """Write a booktabs LaTeX table next to the CSV. digits: {column: n decimals} (default 2)."""
    d = df.copy()
    digits = digits or {}
    for c in d.columns:
        if pd.api.types.is_float_dtype(d[c]):
            nd = digits.get(c, 2)
            d[c] = d[c].map(lambda v, nd=nd: "" if pd.isna(v) else f"{v:.{nd}f}".replace("-0." + "0" * nd, "0." + "0" * nd)
                            if nd > 0 else f"{v:.0f}")
    tex = d.to_latex(index=index, escape=True, caption=caption, label=label, column_format=None)
    (TABLES / f"{name}.tex").write_text(tex)
