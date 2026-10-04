"""M6_factor_timing: can the Green-minus-Brown (GB) spread be timed out of sample with a disciplined shrinkage model
(in the spirit of Lehnherr, Mehta and Nagel 2024), and does climate attention add anything beyond value spreads and
macro variables?

Run: cd /home/hashim/projects/GA/project/research && uv run python modules/M6_factor_timing/run.py
Outputs: outputs/tables/M6_factor_timing_*.csv|.tex, outputs/figures/M6_factor_timing_*.pdf|.png

Checks added after the independent verification (VERIFY.md), all labelled robustness in the ledger:
  cv_design            CV-design sensitivity (validate on the last 120/60 months, first fold 120, grid without 1e6)
  team_target_check    ATTN vs the team's own target (next-month FF3 residual of the Brown leg)
  scaling_sensitivity  timing minus static with the static leg at the timing rule's mean |w| instead of equal vol
  risk_concentration   share of squared gross returns by sub-window
  lmn_attn_increment   LMN variant, B minus B0 monthly return difference
  timing_vs_prevmean   how close the ridge-CV timing portfolio is to the prevailing-mean portfolio
Ledger: CW rows carry p_value_one_sided (the pre-specified p) and an 'alternative' column; t < 0 means model worse.
"""
from __future__ import annotations
import sys, pathlib, warnings
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from m6lib import *                     # noqa: F401,F403  (also puts lib/ on sys.path)
from plotstyle import *                 # noqa: F401,F403
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

warnings.filterwarnings("ignore", category=FutureWarning)
pd.set_option("display.width", 220)

T = lambda name: TABLES / f"{MOD}_{name}.csv"
GAMMA = 5.0            # nominal risk aversion in w = forecast / (gamma * trailing variance); irrelevant after vol scaling
VAR_WIN = 60           # trailing window (months) for the GB variance in the timing weight

# ---------------------------------------------------------------------------------------------- specifications
A_COLS = ["VS", "MOM12", "TERM", "CREDIT", "DGS10", "INFL", "CFNAI"]      # macro + value spread + GB momentum
B0_COLS = A_COLS + ["WTI", "LVIX"]                                          # + oil and VIX (1990 on)
B_COLS = B0_COLS + ["ATTN"]                                                 # + team attention signal
SPECS = {
    # name: (columns, first origin row, first OOS target month, last origin row)
    "A_noVIX_1970": (A_COLS, "1970-01-31", "1990-01-31", "2026-06-30"),
    "B_full_1990": (B_COLS, "1990-01-31", "2000-01-31", "2026-06-30"),
    "B0_noATTN_1990": (B0_COLS, "1990-01-31", "2000-01-31", "2026-06-30"),
    "C0_macro_2003": (B0_COLS, "2003-01-31", "2013-01-31", "2025-06-30"),
    "C_mccc_2003": (B0_COLS + ["MCCC"], "2003-01-31", "2013-01-31", "2025-06-30"),
    "C_attn_2003": (B0_COLS + ["ATTN"], "2003-01-31", "2013-01-31", "2025-06-30"),
    # robustness
    "A_wti_1987": (A_COLS + ["WTI"], "1987-01-31", "1997-01-31", "2026-06-30"),
    "A_vsm_1970": ([c if c != "VS" else "VS_m" for c in A_COLS], "1970-01-31", "1990-01-31", "2026-06-30"),
    "B_vsm_1990": ([c if c != "VS" else "VS_m" for c in B_COLS], "1990-01-31", "2000-01-31", "2026-06-30"),
    "B_attnlag_1990": (B0_COLS + ["ATTN_l1"], "1990-01-31", "2000-01-31", "2026-06-30"),
}
FIXED_LAMBDAS = [0.0, 0.01, 0.1, 1.0, 10.0]


def main():
    t, green, brown, GB = gb_legs()
    IND = t["industries"].loc[:LAST_MONTH]
    X = build_predictors(green, brown, IND, GB)
    y = GB.shift(-1)                                     # y[t] = GB return in month t+1
    fac = load_ff5_mom()
    var60 = GB.rolling(VAR_WIN).var()
    ledger, oos_rows = [], []

    def add_test(test_id, question, stat_name, stat, p2, n, kind, note, p1=np.nan, alternative="two-sided"):
        """Ledger row. Clark-West rows are one-sided tests (H1: model has lower MSPE than the benchmark); for them
        p_value_one_sided = 1 - Phi(t) is the pre-specified p, and p_value_two_sided is kept only for completeness.
        A CW row with t < 0 is evidence that the model is WORSE than the benchmark, never a discovery."""
        ledger.append({"test_id": test_id, "module": MOD, "question": question, "statistic_name": stat_name,
                       "statistic": stat, "p_value_two_sided": p2, "n_obs": n, "primary_or_exploratory": kind,
                       "note": note, "p_value_one_sided": p1, "alternative": alternative})

    def p2n(t):
        return 2 * (1 - stats.norm.cdf(abs(t)))

    CW_ALT = "greater (one-sided CW: model MSPE below benchmark; t<0 means model worse)"

    def evaluate(model, bench_name, f_m, f_b, y_, oos_start, kind, question, extra=None, windows=None,
                 id_prefix=None, lam_share=np.nan):
        windows = windows or period_windows(oos_start)
        for pname, (a, b) in windows.items():
            if len(y_.loc[a:b].dropna()) < 6:
                continue
            s = oos_stats(y_.loc[a:b], f_m.loc[a:b], f_b.loc[a:b])
            diff = float((f_m.loc[a:b] - f_b.loc[a:b]).abs().max())
            degenerate = diff < 1e-7
            if degenerate:          # forecast identical to benchmark: adjusted-MSPE differential is identically zero
                s["cw_t"], s["cw_p_one_sided"], s["cw_p_two_sided"] = 0.0, 0.5, 1.0
            row_kind = kind if pname in ("full_oos", "post2010") else ("exploratory" if kind == "primary" else kind)
            row = {"model": model, "benchmark": bench_name, "period": pname, **s, "r2_oos_pct": 100 * s["r2_oos"],
                   "max_abs_forecast_diff": diff, "degenerate": degenerate, "share_lambda_at_max": lam_share,
                   "label": row_kind, "question": question}
            if extra:
                row.update(extra)
            oos_rows.append(row)
            tid = f"{id_prefix or model}_vs_{bench_name}_{pname}"
            add_test(tid, question, "Clark-West adjusted-MSPE t (NW6)", s["cw_t"], s["cw_p_two_sided"], s["n"],
                     row_kind, f"R2_OOS={100 * s['r2_oos']:.3f}%; one-sided p={s['cw_p_one_sided']:.3f}; "
                               f"{s['start']:%Y-%m} to {s['end']:%Y-%m}"
                               + ("; DEGENERATE: forecast equals benchmark (max diff "
                                  f"{diff:.1e}), statistic set to 0" if degenerate else "")
                               + ("; direction: model WORSE than benchmark" if s["cw_t"] < 0 else ""),
                     p1=s["cw_p_one_sided"], alternative=CW_ALT)

    # ================================================================== 1. predictor summary (descriptive, in-sample)
    rows = []
    for c in ["VS", "VS_m", "MOM12", "TERM", "CREDIT", "DGS10", "INFL", "CFNAI", "WTI", "LVIX", "ATTN", "ATTN_l1", "MCCC"]:
        s = X[c].loc[:"2026-06-30"].dropna()
        row = {"predictor": c, "label": LABELS[c], "first": s.index.min().strftime("%Y-%m"),
               "last": s.index.max().strftime("%Y-%m"), "mean": s.mean(), "sd": s.std(), "ar1": s.autocorr(1)}
        for samp, st in (("1970", "1970-01-31"), ("1990", "1990-01-31")):
            ss = s.loc[st:]
            if len(ss) < 60 or ss.index.min() > pd.Timestamp(st) + pd.DateOffset(years=15):
                continue
            z = (ss - ss.mean()) / ss.std()
            r = nw_ols(y.reindex(z.index), z.rename("z"))
            row[f"slope_pct_per_sd_{samp}"] = 100 * r.params["z"]; row[f"t_nw_{samp}"] = r.tvalues["z"]
            row[f"n_{samp}"] = int(r.nobs); row[f"is_start_{samp}"] = z.index.min().strftime("%Y-%m")
            add_test(f"IS_univariate_{c}_{z.index.min().year}", "Q0 descriptive: in-sample univariate predictive slope",
                     "NW6 t on slope of next-month GB on standardized predictor", r.tvalues["z"], r.pvalues["z"],
                     int(r.nobs), "exploratory", f"full-sample in-sample regression from {z.index.min():%Y-%m}; "
                                                 "look-ahead in the standardization, descriptive only")
        rows.append(row)
    pred_tab = pd.DataFrame(rows)
    pred_tab.to_csv(T("predictors"), index=False)
    to_tex(pred_tab[["predictor", "first", "last", "ar1", "slope_pct_per_sd_1970", "t_nw_1970", "slope_pct_per_sd_1990",
                     "t_nw_1990"]], f"{MOD}_predictors",
           "Predictors of next-month Green-minus-Brown return. In-sample univariate slopes (percent per month per "
           "standard deviation) with NW(6) t-statistics; descriptive only.", "tab:m6_predictors",
           digits={"slope_pct_per_sd_1970": 3, "slope_pct_per_sd_1990": 3})

    # ================================================================== 2. walk-forward ridge for every spec
    fc = {}
    for name, (cols, st, oos, last) in SPECS.items():
        Xs = X.loc[st:last, cols]
        fc[name] = walk_forward_ridge(Xs, y, oos)
    fixed = {}
    for name in ("A_noVIX_1970", "B_full_1990", "B0_noATTN_1990", "C0_macro_2003", "C_mccc_2003", "C_attn_2003"):
        cols, st, oos, last = SPECS[name]
        for lam in FIXED_LAMBDAS:
            fixed[(name, lam)] = walk_forward_ridge(X.loc[st:last, cols], y, oos, fixed_lambda=lam)
    uni, comb = {}, {}
    for name in ("A_noVIX_1970", "B_full_1990"):
        cols, st, oos, last = SPECS[name]
        for c in cols:
            uni[(name, c)] = walk_forward_ridge(X.loc[st:last, [c]], y, oos, fixed_lambda=0.0)
        comb[name] = pd.concat([uni[(name, c)]["forecast"] for c in cols], axis=1).mean(axis=1)

    # save forecasts
    fcast = pd.DataFrame({"gb_realized": fc["A_noVIX_1970"]["y"]})
    for name, f in fc.items():
        fcast[f"{name}_ridgecv"] = f["forecast"]; fcast[f"{name}_histmean"] = f["hist_mean"]
        fcast[f"{name}_lambda"] = f["lambda"]
    for (name, lam), f in fixed.items():
        if name in ("A_noVIX_1970", "B_full_1990"):
            fcast[f"{name}_fixed{lam:g}"] = f["forecast"]
    for name, f in comb.items():
        fcast[f"{name}_combination"] = f
    fcast.index.name = "target_month"
    fcast.to_csv(T("forecasts"))
    hm_rows = []
    for name in ("A_noVIX_1970", "B_full_1990"):
        f = fc[name]
        pos = f["hist_mean"] > 0
        hm_rows.append({"spec": name, "oos_start": f.index.min().strftime("%Y-%m"),
                        "share_months_histmean_positive": pos.mean(),
                        "last_month_histmean_positive": f.index[pos].max().strftime("%Y-%m") if pos.any() else "never",
                        # the forecast for target month m is formed at the end of m-1: the portfolio is short GB in
                        # every target month after the last positive one
                        "first_month_short_thereafter": (f.index[pos].max() + ME1).strftime("%Y-%m") if pos.any() else "",
                        "short_every_month_thereafter": bool((f.loc[f.index[pos].max() + ME1:, "hist_mean"] < 0).all()),
                        "histmean_at_end_ann_pct": 1200 * f["hist_mean"].iloc[-1],
                        "share_months_lambda_at_max": f["lambda_at_max"].mean(),
                        "max_abs_ridge_minus_histmean": (f["forecast"] - f["hist_mean"]).abs().max()})
    pd.DataFrame(hm_rows).to_csv(T("histmean_sign"), index=False)

    # ================================================================== 3. primary OOS tests + nested + robustness
    Q1 = "Q1 OOS predictability of next-month GB (ridge-CV vs expanding historical mean)"
    Q2 = "Q2 incremental value of climate attention / MCCC over macro + value spread"
    for name in ("A_noVIX_1970", "B_full_1990"):
        f = fc[name]; oos = SPECS[name][2]
        evaluate(f"{name}_ridgecv", "histmean", f["forecast"], f["hist_mean"], f["y"], oos, "primary", Q1,
                 lam_share=f["lambda_at_max"].mean(), extra={"median_lambda": f["lambda"].median()})
    evaluate("B_full_1990_ridgecv", "B0_noATTN_1990_ridgecv", fc["B_full_1990"]["forecast"],
             fc["B0_noATTN_1990"]["forecast"], fc["B_full_1990"]["y"], "2000-01-31", "primary", Q2,
             id_prefix="ATTN_increment_ridgecv")
    # Holm across the pre-registered primary family (6 tests: A/B vs HM and B vs B0, each full OOS and post2010)
    oos_df = pd.DataFrame(oos_rows)
    prim = oos_df["label"].eq("primary")
    oos_df.loc[prim, "p_holm_primary_family"] = holm(oos_df.loc[prim, "cw_p_one_sided"]).values

    # exploratory / robustness rows appended after the primary family
    n_before = len(oos_rows)
    evaluate("B0_noATTN_1990_ridgecv", "histmean", fc["B0_noATTN_1990"]["forecast"], fc["B0_noATTN_1990"]["hist_mean"],
             fc["B0_noATTN_1990"]["y"], "2000-01-31", "robustness", Q1,
             lam_share=fc["B0_noATTN_1990"]["lambda_at_max"].mean())
    for name, bench in (("C_mccc_2003", "C0_macro_2003"), ("C_attn_2003", "C0_macro_2003")):
        w = period_windows("2013-01-31", extra=("holdout", "inflation_rates", "last18", "last12"))
        evaluate(f"{name}_ridgecv", f"{bench}_ridgecv", fc[name]["forecast"], fc[bench]["forecast"], fc[name]["y"],
                 "2013-01-31", "exploratory", Q2, windows=w)
        evaluate(f"{name}_ridgecv", "histmean", fc[name]["forecast"], fc[name]["hist_mean"], fc[name]["y"],
                 "2013-01-31", "exploratory", Q1, windows=w, lam_share=fc[name]["lambda_at_max"].mean())
    for name in ("A_wti_1987", "A_vsm_1970", "B_vsm_1990", "B_attnlag_1990"):
        f = fc[name]; w = {k: v for k, v in period_windows(SPECS[name][2]).items() if k in ("full_oos", "post2010")}
        evaluate(f"{name}_ridgecv", "histmean", f["forecast"], f["hist_mean"], f["y"], SPECS[name][2], "robustness",
                 Q1, windows=w, lam_share=f["lambda_at_max"].mean())
    for name in ("A_noVIX_1970", "B_full_1990"):
        oos = SPECS[name][2]; w = {k: v for k, v in period_windows(oos).items() if k in ("full_oos", "post2010")}
        for lam in FIXED_LAMBDAS:
            f = fixed[(name, lam)]
            evaluate(f"{name}_fixed_lambda_{lam:g}", "histmean", f["forecast"], f["hist_mean"], f["y"], oos,
                     "robustness", Q1 + " [fixed penalty sensitivity, NOT a selectable spec]", windows=w)
        base = fc[name]
        evaluate(f"{name}_combination", "histmean", comb[name], base["hist_mean"], base["y"], oos, "robustness", Q1,
                 windows=w)
        for c in SPECS[name][0]:
            f = uni[(name, c)]
            evaluate(f"{name}_univariate_{c}", "histmean", f["forecast"], f["hist_mean"], f["y"], oos, "exploratory",
                     Q1 + " [univariate OLS, Goyal-Welch style]", windows=w)
    for lam in FIXED_LAMBDAS:                                   # nested attention / MCCC increments at fixed penalties
        w = {k: v for k, v in period_windows("2000-01-31").items() if k in ("full_oos", "post2010")}
        evaluate(f"B_full_1990_fixed_lambda_{lam:g}", f"B0_noATTN_1990_fixed_lambda_{lam:g}",
                 fixed[("B_full_1990", lam)]["forecast"], fixed[("B0_noATTN_1990", lam)]["forecast"],
                 fixed[("B_full_1990", lam)]["y"], "2000-01-31", "robustness", Q2 + " [fixed penalty]", windows=w,
                 id_prefix=f"ATTN_increment_fixed{lam:g}")
        w = {"full_oos": (pd.Timestamp("2013-01-31"), pd.Timestamp("2025-07-31"))}
        for name in ("C_mccc_2003", "C_attn_2003"):
            evaluate(f"{name}_fixed_lambda_{lam:g}", f"C0_macro_2003_fixed_lambda_{lam:g}",
                     fixed[(name, lam)]["forecast"], fixed[("C0_macro_2003", lam)]["forecast"],
                     fixed[(name, lam)]["y"], "2013-01-31", "exploratory", Q2 + " [fixed penalty]", windows=w)
    # ---- 3b. CV-design sensitivity (robustness, added after verification): does the 100% max-penalty result depend
    # on validating over ALL expanding blocks? Alternatives: validate only on the last 120 or 60 training months,
    # start CV folds after 120 rows, or drop the 1e6 grid point (max penalty 1e3).
    CV_DESIGNS = {"recent120": dict(recent=120), "recent60": dict(recent=60), "first120": dict(first=120),
                  "grid_max1e3": dict(grid=LAMBDA_GRID[:-1])}
    cvd = {}
    for name in ("A_noVIX_1970", "B_full_1990", "B0_noATTN_1990"):
        cols, st, oos, last = SPECS[name]
        for dname, kw in CV_DESIGNS.items():
            cvd[(name, dname)] = walk_forward_ridge(X.loc[st:last, cols], y, oos, **kw)
    QCV = Q1 + " [CV-design sensitivity]"
    for name in ("A_noVIX_1970", "B_full_1990", "B0_noATTN_1990"):
        oos = SPECS[name][2]; w = {k: v for k, v in period_windows(oos).items() if k in ("full_oos", "post2010")}
        for dname in CV_DESIGNS:
            f = cvd[(name, dname)]
            evaluate(f"{name}_ridgecv_{dname}", "histmean", f["forecast"], f["hist_mean"], f["y"], oos, "robustness",
                     QCV, windows=w, lam_share=f["lambda_at_max"].mean(),
                     extra={"cv_design": dname, "median_lambda": f["lambda"].median(),
                            "share_lambda_le_1": float((f["lambda"] <= 1).mean())})
    w = {k: v for k, v in period_windows("2000-01-31").items() if k in ("full_oos", "post2010")}
    for dname in CV_DESIGNS:
        b, b0 = cvd[("B_full_1990", dname)], cvd[("B0_noATTN_1990", dname)]
        evaluate(f"B_full_1990_ridgecv_{dname}", f"B0_noATTN_1990_ridgecv_{dname}", b["forecast"], b0["forecast"],
                 b["y"], "2000-01-31", "robustness", Q2 + " [CV-design sensitivity]", windows=w,
                 id_prefix=f"ATTN_increment_ridgecv_{dname}", extra={"cv_design": dname})

    # ---- 3c. the team's own target (robustness, added after verification): next-month FF3 residual of the Brown leg
    # (team rolling_factor_model: 60m window, alpha and betas lagged one month). Team hypothesis: high ATTN_t ->
    # negative eps_{t+1} (they go Short-Brown), i.e. a negative slope.
    eps = team_brown_residual(brown)
    y_eps = eps.shift(-1)                                 # y_eps[t] = Brown residual realized in month t+1
    QT = "Q2b attention vs the team's target: next-month Brown-leg FF3 residual (team hedge, lagged betas)"
    team_rows = []
    for st in ("1990-01-31", "2010-01-31"):
        z = X["ATTN"].loc[st:"2026-06-30"].dropna()
        z = (z - z.mean()) / z.std()
        r = nw_ols(y_eps.reindex(z.index), z.rename("z"))
        team_rows.append({"test": "in_sample_slope", "model": "ATTN univariate", "benchmark": "", "period": f"from_{st[:4]}",
                          "start": (z.index.min() + ME1).strftime("%Y-%m"), "end": (z.index.max() + ME1).strftime("%Y-%m"),
                          "n": int(r.nobs), "slope_pct_per_sd": 100 * r.params["z"], "t_nw": r.tvalues["z"],
                          "p_two_sided": r.pvalues["z"]})
        add_test(f"TEAMTGT_IS_ATTN_slope_from{st[:4]}", QT, "NW6 t on slope of next-month Brown residual on standardized ATTN",
                 r.tvalues["z"], r.pvalues["z"], int(r.nobs), "robustness",
                 f"slope={100 * r.params['z']:.3f}% per month per sd (team hypothesis: negative); in-sample, descriptive")
    eps_fc = {"ATTN_ols": walk_forward_ridge(X.loc["1990-01-31":"2026-06-30", ["ATTN"]], y_eps, "2000-01-31",
                                             fixed_lambda=0.0)}
    for nm, cols in (("B", B_COLS), ("B0", B0_COLS)):
        eps_fc[f"{nm}_ridgecv"] = walk_forward_ridge(X.loc["1990-01-31":"2026-06-30", cols], y_eps, "2000-01-31")
        for lam in (0.0, 1.0):
            eps_fc[f"{nm}_fixed{lam:g}"] = walk_forward_ridge(X.loc["1990-01-31":"2026-06-30", cols], y_eps,
                                                              "2000-01-31", fixed_lambda=lam)
    tw = {k: v for k, v in period_windows("2000-01-31").items() if k in ("full_oos", "post2010", "validation", "holdout")}
    n_team0 = len(oos_rows)
    f = eps_fc["ATTN_ols"]
    evaluate("TEAMTGT_ATTN_ols", "histmean", f["forecast"], f["hist_mean"], f["y"], "2000-01-31",
             "robustness", QT, windows=tw)
    f = eps_fc["B_ridgecv"]
    evaluate("TEAMTGT_B_full_1990_ridgecv", "histmean", f["forecast"], f["hist_mean"], f["y"], "2000-01-31",
             "robustness", QT, windows=tw, lam_share=f["lambda_at_max"].mean())
    for key in ("ridgecv", "fixed0", "fixed1"):
        evaluate(f"TEAMTGT_B_full_1990_{key}", f"TEAMTGT_B0_noATTN_1990_{key}", eps_fc[f"B_{key}"]["forecast"],
                 eps_fc[f"B0_{key}"]["forecast"], eps_fc[f"B_{key}"]["y"], "2000-01-31", "robustness",
                 QT + " [nested ATTN increment]", windows=tw,
                 lam_share=eps_fc["B_ridgecv"]["lambda_at_max"].mean() if key == "ridgecv" else np.nan)
    for r_ in oos_rows[n_team0:]:
        team_rows.append({"test": "oos_clark_west", "model": r_["model"], "benchmark": r_["benchmark"],
                          "period": r_["period"], "start": r_["start"].strftime("%Y-%m"),
                          "end": r_["end"].strftime("%Y-%m"), "n": r_["n"], "r2_oos_pct": r_["r2_oos_pct"],
                          "cw_t": r_["cw_t"], "cw_p_one_sided": r_["cw_p_one_sided"],
                          "share_lambda_at_max": r_["share_lambda_at_max"], "degenerate": r_["degenerate"]})
    team_tab = pd.DataFrame(team_rows)
    team_tab.to_csv(T("team_target_check"), index=False)
    to_tex(team_tab[team_tab["test"].eq("oos_clark_west") & team_tab["period"].isin(["full_oos", "post2010", "holdout"])]
           [["model", "benchmark", "period", "start", "end", "n", "r2_oos_pct", "cw_t", "cw_p_one_sided"]],
           f"{MOD}_team_target_check", "Attention and the team's own target: next-month FF3 residual of the Brown leg "
           "(60-month rolling hedge, alpha and betas lagged one month). Out-of-sample $R^2$ (percent) and Clark-West t "
           "(NW6, one-sided p).", "tab:m6_team_target", digits={"r2_oos_pct": 3, "cw_p_one_sided": 3})
    eps.to_frame().to_csv(T("team_brown_residual"))

    oos_df = pd.concat([oos_df, pd.DataFrame(oos_rows[n_before:])], ignore_index=True)
    oos_df["start"] = pd.to_datetime(oos_df["start"]).dt.strftime("%Y-%m")
    oos_df["end"] = pd.to_datetime(oos_df["end"]).dt.strftime("%Y-%m")
    oos_df.to_csv(T("oos_tests"), index=False)
    main_tab = oos_df[oos_df["model"].isin(["A_noVIX_1970_ridgecv", "B_full_1990_ridgecv"])
                      & oos_df["benchmark"].isin(["histmean", "B0_noATTN_1990_ridgecv"])]
    main_tab = main_tab[["model", "benchmark", "period", "start", "end", "n", "r2_oos_pct", "cw_t", "cw_p_one_sided",
                         "share_lambda_at_max", "max_abs_forecast_diff", "label"]]
    main_tab.to_csv(T("oos_primary"), index=False)
    to_tex(main_tab.drop(columns=["max_abs_forecast_diff"]), f"{MOD}_oos_primary",
           "Out-of-sample predictability of next-month Green-minus-Brown. Campbell-Thompson $R^2_{OOS}$ (percent) vs the "
           "expanding historical mean (or vs the nested no-attention model) and Clark-West t (NW6). Ridge penalty "
           "chosen each month by expanding-fold time-series CV. When CV picks the maximum penalty in every month the "
           "forecast equals the benchmark and the CW statistic is set to 0.", "tab:m6_oos_primary",
           digits={"r2_oos_pct": 3, "cw_p_one_sided": 3, "share_lambda_at_max": 2})
    rob = oos_df[oos_df["label"].isin(["robustness", "exploratory"]) & oos_df["period"].isin(["full_oos", "post2010"])
                 & ~oos_df["model"].str.contains("univariate")]
    rob = rob[["model", "benchmark", "period", "start", "end", "n", "r2_oos_pct", "cw_t", "cw_p_one_sided", "label"]]
    rob.to_csv(T("oos_robustness"), index=False)
    rob_tex = rob[~rob["model"].str.startswith("TEAMTGT") & oos_df.loc[rob.index, "cv_design"].isna()]
    to_tex(rob_tex, f"{MOD}_oos_robustness", "Robustness and exploratory out-of-sample comparisons. Fixed-penalty rows "
           "are a sensitivity path, not selectable specifications. CV-design and team-target rows are in separate "
           "tables.", "tab:m6_oos_robustness", digits={"r2_oos_pct": 3, "cw_p_one_sided": 3})
    cvd_tab = oos_df[oos_df["cv_design"].notna()][["model", "benchmark", "cv_design", "period", "start", "end", "n",
                                                    "share_lambda_at_max", "share_lambda_le_1", "median_lambda",
                                                    "r2_oos_pct", "cw_t", "cw_p_one_sided", "max_abs_forecast_diff",
                                                    "degenerate"]].copy()
    base = oos_df[oos_df["model"].isin(["A_noVIX_1970_ridgecv", "B_full_1990_ridgecv"])
                  & oos_df["period"].isin(["full_oos", "post2010"])].copy()
    base["cv_design"] = "expanding_all_blocks (primary)"
    base["share_lambda_le_1"] = np.nan
    cvd_tab = pd.concat([base[cvd_tab.columns], cvd_tab], ignore_index=True)
    cvd_tab.to_csv(T("cv_design"), index=False)
    to_tex(cvd_tab.drop(columns=["start", "end", "max_abs_forecast_diff", "degenerate", "share_lambda_le_1"]),
           f"{MOD}_cv_design", "Cross-validation design sensitivity. Primary: validate on all expanding 12-month blocks "
           "after the first 60 training rows. recent120/recent60: only blocks ending in the last 120/60 training months. "
           "first120: first fold trains on 120 rows. grid\_max1e3: grid without the 1e6 point. Share of monthly refits "
           "at the largest grid penalty, median penalty, $R^2_{OOS}$ (percent) and Clark-West t.", "tab:m6_cv_design",
           digits={"r2_oos_pct": 3, "cw_p_one_sided": 3, "share_lambda_at_max": 2, "median_lambda": 0})
    uni_tab = oos_df[oos_df["model"].str.contains("univariate")][["model", "period", "n", "r2_oos_pct", "cw_t",
                                                                  "cw_p_one_sided"]].copy()
    uni_tab["bh_q_univariate_family"] = bh(uni_tab["cw_p_one_sided"]).values
    uni_tab.to_csv(T("oos_univariate"), index=False)
    to_tex(uni_tab, f"{MOD}_oos_univariate", "Exploratory univariate OLS forecasts (Goyal-Welch style), each vs the "
           "expanding historical mean. BH q-values across all univariate tests in this table.", "tab:m6_oos_univariate",
           digits={"r2_oos_pct": 3, "cw_p_one_sided": 3, "bh_q_univariate_family": 3})

    # ================================================================== 4. timing portfolios
    port_rows, port_series, load_rows = [], {}, []
    scale_rows, risk_rows, degen_rows = [], [], []
    RISK_WINDOWS = {"1990-1994": ("1990-01-31", "1994-12-31"), "1995-1999": ("1995-01-31", "1999-12-31"),
                    "2000-2001": ("2000-01-31", "2001-12-31"), "2002-2009": ("2002-01-31", "2009-12-31"),
                    "2010-2019": ("2010-01-31", "2019-12-31"), "2020-2026": ("2020-01-31", "2026-07-31")}
    for name in ("A_noVIX_1970", "B_full_1990"):
        f = fc[name]; oos = SPECS[name][2]
        windows = period_windows(oos)
        scale_win = windows["full_oos"]
        v = var60.reindex(f["origin"]).to_numpy()
        cands = {
            "timing_ridgecv": f["forecast"] / (GAMMA * v),
            "prevailing_mean": f["hist_mean"] / (GAMMA * v),
            "static_long": pd.Series(1.0, index=f.index),
            "timing_ols_lambda0": fixed[(name, 0.0)]["forecast"] / (GAMMA * v),
            "timing_combination": comb[name] / (GAMMA * v),
        }
        for label, w_raw in cands.items():
            S = scaled_strategy(w_raw, GB, IND, green, brown, scale_win)
            port_series[(name, label)] = S
            kind = "primary" if label in ("timing_ridgecv", "static_long") else "robustness"
            for r in perf_block(S, fac, windows, f"{name}:{label}"):
                r["label"] = kind; port_rows.append(r)
            load_rows.append(ff6_loadings(S["net"], fac, f"{name}:{label}"))
            if label in ("timing_ridgecv", "static_long", "timing_ols_lambda0"):
                a = alpha_row(S["net"].loc[scale_win[0]:scale_win[1]], fac.reindex(S.index)[FF6])
                add_test(f"PORT_{name}_{label}_alpha_ff6_net_full", "Q1b timing portfolio: FF5+UMD alpha (net, 10bp)",
                         "NW6 t on annualized alpha", a["t_alpha"], 2 * (1 - stats.norm.cdf(abs(a["t_alpha"]))), a["n"],
                         "exploratory" if kind == "primary" else "robustness",
                         f"alpha={100 * a['alpha_ann']:.2f}%/yr at 5% vol; full OOS from {oos[:7]}")
        d = (port_series[(name, "timing_ridgecv")]["net"] - port_series[(name, "static_long")]["net"]).loc[
            scale_win[0]:scale_win[1]]
        r = nw_ols(d)
        add_test(f"PORT_{name}_timing_minus_static_net_full", "Q1b timing minus static always-long (both at 5% vol, net)",
                 "NW6 t on mean difference", r.tvalues.iloc[0], r.pvalues.iloc[0], int(r.nobs), "primary",
                 f"mean diff={1200 * d.mean():.2f}%/yr")
        # ---- scaling sensitivity (robustness, added after verification). Each strategy's own Sharpe and t are
        # invariant to its constant scale, but the DIFFERENCE is not: compare with the static leg scaled to the timing
        # rule's mean |w| (equal average gross exposure) instead of equal ex-post volatility.
        Tm = port_series[(name, "timing_ridgecv")]
        mean_abs_w = float(Tm["w"].loc[scale_win[0]:scale_win[1]].abs().mean())
        S_eq = scaled_strategy(pd.Series(1.0, index=f.index), GB, IND, green, brown, scale_win, scale=mean_abs_w)
        port_series[(name, "static_long_meanabsw")] = S_eq
        for kind in ("net", "gross"):
            for sname, Sref in (("equal_vol_5pct", port_series[(name, "static_long")]), ("equal_mean_abs_w", S_eq)):
                dd_ = (Tm[kind] - Sref[kind]).loc[scale_win[0]:scale_win[1]]
                rr_ = nw_ols(dd_)
                scale_rows.append({"spec": name, "static_scaling": sname, "returns": kind, "n": int(rr_.nobs),
                                   "static_w": float(Sref["w"].iloc[0]), "timing_mean_abs_w": mean_abs_w,
                                   "static_ann_vol": np.sqrt(12) * Sref["gross"].loc[scale_win[0]:scale_win[1]].std(),
                                   "mean_diff_ann": 12 * dd_.mean(), "t_nw": rr_.tvalues.iloc[0],
                                   "p_two_sided": rr_.pvalues.iloc[0]})
                if sname == "equal_mean_abs_w":
                    add_test(f"PORT_{name}_timing_minus_static_meanabsw_{kind}_full",
                             "Q1b robustness: timing minus static, static scaled to the timing rule's mean |w|",
                             "NW6 t on mean difference", rr_.tvalues.iloc[0], rr_.pvalues.iloc[0], int(rr_.nobs),
                             "robustness", f"mean diff={1200 * dd_.mean():.2f}%/yr ({kind}); static w={mean_abs_w:.3f}")
        # ---- where the timing risk sits: share of the sum of squared gross returns by sub-window
        for lab in ("timing_ridgecv", "static_long"):
            g = port_series[(name, lab)]["gross"].loc[scale_win[0]:scale_win[1]]
            tot = (g ** 2).sum()
            for wname, (a_, b_) in RISK_WINDOWS.items():
                gw = g.loc[a_:b_]
                if len(gw) == 0:
                    continue
                risk_rows.append({"spec": name, "strategy": lab, "window": wname, "start": gw.index.min().strftime("%Y-%m"),
                                  "end": gw.index.max().strftime("%Y-%m"), "n_months": len(gw),
                                  "share_months": len(gw) / len(g), "share_sum_sq_gross": (gw ** 2).sum() / tot,
                                  "ann_vol_gross": np.sqrt(12) * gw.std(), "max_abs_month": gw.abs().max(),
                                  "max_abs_month_date": gw.abs().idxmax().strftime("%Y-%m"),
                                  "max_abs_month_signed": gw.loc[gw.abs().idxmax()]})
        # ---- how close the timing portfolio is to the prevailing-mean portfolio
        Pm = port_series[(name, "prevailing_mean")]
        sw = slice(scale_win[0], scale_win[1])
        degen_rows.append({"spec": name, "n": len(Tm.loc[sw]),
                           "max_abs_forecast_gap": float((f["forecast"] - f["hist_mean"]).abs().max()),
                           "max_abs_diff_w": float((Tm["w"] - Pm["w"]).loc[sw].abs().max()),
                           "max_abs_diff_gross": float((Tm["gross"] - Pm["gross"]).loc[sw].abs().max()),
                           "max_abs_diff_net": float((Tm["net"] - Pm["net"]).loc[sw].abs().max()),
                           "cost_drag_bp_ann_timing": 1e4 * 12 * COST * Tm["turnover"].loc[sw].mean(),
                           "cost_drag_bp_ann_prevmean": 1e4 * 12 * COST * Pm["turnover"].loc[sw].mean(),
                           "scale_timing": float(Tm["scale"].iloc[0]), "scale_prevmean": float(Pm["scale"].iloc[0]),
                           "frac_long_timing": float((Tm["w"].loc[sw] > 0).mean())})
    # LMN (2024) portfolio-shrinkage variant (robustness)
    lmn_grid = np.r_[0.0, np.logspace(-1, 5, 25), 1e9]
    lmn_rows = []
    for name in ("A_noVIX_1970", "B_full_1990", "B0_noATTN_1990"):
        cols, st, oos, last = SPECS[name]
        for norm in (True, False):
            L = lmn_timing(X.loc[st:last, cols], y, lmn_grid, normalize=norm)
            lab = "lmn_sign" if norm else "lmn_raw"
            start = max(pd.Timestamp(oos), L.index.min())
            windows = period_windows(start)
            S = scaled_strategy(L["h"], GB, IND, green, brown, windows["full_oos"])
            port_series[(name, lab)] = S
            for r in perf_block(S, fac, windows, f"{name}:{lab}"):
                r["label"] = "robustness"; port_rows.append(r)
            lam_share = float((L.loc[start:, "lambda"] >= 1e9).mean())
            lmn_rows.append({"spec": name, "variant": lab, "oos_start": start.strftime("%Y-%m"),
                             "share_years_static_lambda": lam_share, "median_lambda": L.loc[start:, "lambda"].median(),
                             "sharpe_gross": perf(S.loc[start:, "gross"])["sharpe"],
                             "sharpe_net": perf(S.loc[start:, "net"])["sharpe"]})
            r = nw_ols(S.loc[start:, "net"])
            add_test(f"LMN_{name}_{lab}_mean_net", "Q1b robustness: LMN portfolio-shrinkage timing, mean net return",
                     "NW6 t on mean", r.tvalues.iloc[0], r.pvalues.iloc[0], int(r.nobs), "robustness",
                     f"Sharpe net={perf(S.loc[start:, 'net'])['sharpe']:.2f}; OOS from {start:%Y-%m}")
    lmn_df = pd.DataFrame(lmn_rows); lmn_df.to_csv(T("lmn_variant"), index=False)
    # ---- LMN attention increment (robustness, added after verification): B minus B0 monthly return, same months
    lmn_inc = []
    for lab in ("lmn_sign", "lmn_raw"):
        for kind in ("net", "gross"):
            dd_ = (port_series[("B_full_1990", lab)][kind] - port_series[("B0_noATTN_1990", lab)][kind]).dropna()
            rr_ = nw_ols(dd_)
            lmn_inc.append({"variant": lab, "returns": kind, "start": dd_.index.min().strftime("%Y-%m"),
                            "end": dd_.index.max().strftime("%Y-%m"), "n": int(rr_.nobs),
                            "mean_diff_ann": 12 * dd_.mean(), "t_nw": rr_.tvalues.iloc[0], "p_two_sided": rr_.pvalues.iloc[0]})
            add_test(f"LMN_B_minus_B0_{lab}_{kind}", "Q2 robustness: LMN timing with vs without ATTN, monthly return difference",
                     "NW6 t on mean difference", rr_.tvalues.iloc[0], rr_.pvalues.iloc[0], int(rr_.nobs), "robustness",
                     f"mean diff={1200 * dd_.mean():.2f}%/yr ({kind}; each leg at 5% vol); negative = ATTN hurts")
    pd.DataFrame(lmn_inc).to_csv(T("lmn_attn_increment"), index=False)
    sc_df = pd.DataFrame(scale_rows); sc_df.to_csv(T("scaling_sensitivity"), index=False)
    risk_df = pd.DataFrame(risk_rows); risk_df.to_csv(T("risk_concentration"), index=False)
    pd.DataFrame(degen_rows).to_csv(T("timing_vs_prevmean"), index=False)
    port_df = pd.DataFrame(port_rows); port_df.to_csv(T("portfolio_perf"), index=False)
    pd.DataFrame(load_rows).to_csv(T("portfolio_ff6_loadings"), index=False)
    pt = port_df[port_df["label"].eq("primary") | port_df["strategy"].str.contains("lmn_sign")]
    pt = pt[pt["period"].isin(["full_oos", "post2010", "holdout", "last18", "last12"])]
    pt = pt[["strategy", "period", "start", "n", "ann_ret_net", "ann_vol", "sharpe_net", "t_mean_net",
             "alpha_ff6_net", "t_alpha_ff6_net", "turnover_ann", "cost_drag_bp_ann"]].copy()
    for c in ("ann_ret_net", "ann_vol", "alpha_ff6_net"):
        pt[c] = 100 * pt[c]
    to_tex(pt, f"{MOD}_portfolio", "Timing portfolio $w_t=\\hat{\\mu}_t/(\\gamma\\hat{\\sigma}^2_t)$ vs static always-long "
           "Green-minus-Brown, both scaled to 5\\% annual volatility over the full OOS window; net of 10 bp per unit "
           "traded (industry-level turnover incl. leg rebalancing). Returns, vol and FF5+UMD alpha in percent per year.",
           "tab:m6_portfolio", digits={"turnover_ann": 2, "cost_drag_bp_ann": 1})
    save_series = pd.DataFrame({f"{k[0]}:{k[1]}:{c}": v[c] for k, v in port_series.items() for c in ("w", "gross", "net")})
    save_series.index.name = "month"; save_series.to_csv(T("portfolio_returns"))

    # ================================================================== 5. shrinkage path (full sample, interpretation)
    path_grid = np.logspace(-4, 3, 57)
    paths = {}
    for name in ("A_noVIX_1970", "B_full_1990"):
        cols, st, oos, last = SPECS[name]
        P_, idx = ridge_path(X.loc[st:last, cols], y.loc[st:last], path_grid)
        cv = cv_curve_full(X.loc[st:last, cols], y.loc[st:last], np.r_[path_grid, 1e6])
        paths[name] = (P_, cv / cv.iloc[-1])
        out = P_.copy(); out.columns = [f"b_{c}" for c in out.columns]
        out["cv_mse_rel_histmean"] = (cv / cv.iloc[-1]).iloc[:-1].values
        out["spec"] = name; out["sample"] = f"{idx.min():%Y-%m} to {idx.max():%Y-%m}"
        out.to_csv(T(f"shrinkage_path_{name}"))

    # ================================================================== 6. industry-rotation panel (exploratory)
    P, feats = industry_panel()
    F = panel_walk_forward(P, feats, "1990-01-31")
    F.to_csv(T("rotation_forecasts"), index=False)
    Wr, Wm = long_short(F, "forecast"), long_short(F, "mom_raw")
    rot = {"rotation_ridge": ls_returns(Wr, IND), "industry_mom_12_1": ls_returns(Wm, IND)}
    windows = period_windows("1990-01-31")
    rot_rows = []
    for k, S in rot.items():
        for r in perf_block(S, fac, windows, k):
            r["label"] = "exploratory"; rot_rows.append(r)
        load_rows.append(ff6_loadings(S["net"], fac, k))
    ok = F.dropna(subset=["y_dm"])
    r2p = 1 - ((ok["y_dm"] - ok["forecast"]) ** 2).sum() / (ok["y_dm"] ** 2).sum()
    ic = ok.groupby("target_date").apply(lambda g: stats.spearmanr(g["forecast"], g["y_dm"])[0])
    icm = ok.groupby("target_date").apply(lambda g: stats.spearmanr(g["mom_raw"], g["y_dm"])[0])
    rot_stats = []
    for nm, s in (("ridge_forecast", ic), ("mom_12_1", icm)):
        r = nw_ols(s)
        rot_stats.append({"signal": nm, "mean_rank_ic": s.mean(), "t_nw": r.tvalues.iloc[0], "n_months": len(s)})
        add_test(f"ROT_rank_ic_{nm}", "Q3 exploratory industry rotation: mean monthly rank IC vs beta-adjusted residual",
                 "NW6 t on mean IC", r.tvalues.iloc[0], r.pvalues.iloc[0], len(s), "exploratory", f"mean IC={s.mean():.4f}")
    rs = pd.DataFrame(rot_stats); rs["pooled_r2_oos_vs_zero_pct"] = [100 * r2p, np.nan]
    rs["median_lambda"] = [F.groupby("target_date")["lambda"].first().median(), np.nan]
    rs.to_csv(T("rotation_stats"), index=False)
    for k, S in rot.items():
        s = S["net"].loc["1990-01-31":]
        a = alpha_row(s, fac.reindex(s.index)[FF6])
        add_test(f"ROT_{k}_alpha_ff6_net", "Q3 exploratory industry rotation: FF5+UMD alpha (net)", "NW6 t on alpha",
                 a["t_alpha"], 2 * (1 - stats.norm.cdf(abs(a["t_alpha"]))), a["n"], "exploratory",
                 f"alpha={100 * a['alpha_ann']:.2f}%/yr; raw vol")
    dd = (rot["rotation_ridge"]["net"] - rot["industry_mom_12_1"]["net"]).loc["1990-01-31":]
    r = nw_ols(dd)
    add_test("ROT_ridge_minus_mom_net", "Q3 exploratory: ridge rotation minus plain 12-1 industry momentum (net)",
             "NW6 t on mean difference", r.tvalues.iloc[0], r.pvalues.iloc[0], int(r.nobs), "exploratory",
             f"mean diff={1200 * dd.mean():.2f}%/yr")
    rot_df = pd.DataFrame(rot_rows); rot_df.to_csv(T("rotation_perf"), index=False)
    rt = rot_df[rot_df["period"].isin(["full_oos", "post2010", "holdout", "last18", "last12"])][
        ["strategy", "period", "n", "ann_ret_net", "ann_vol", "sharpe_net", "t_mean_net", "alpha_ff6_net",
         "t_alpha_ff6_net", "turnover_ann"]].copy()
    for c in ("ann_ret_net", "ann_vol", "alpha_ff6_net"):
        rt[c] = 100 * rt[c]
    to_tex(rt, f"{MOD}_rotation", "Exploratory industry rotation: pooled ridge on own characteristics and macro "
           "interactions, long top 8 / short bottom 8 of 49 industries, vs plain 12-1 industry momentum. Net of 10 bp. "
           "Percent per year.", "tab:m6_rotation", digits={"turnover_ann": 2})
    ld = pd.DataFrame(load_rows); ld.to_csv(T("portfolio_ff6_loadings"), index=False)
    keep = ["A_noVIX_1970:timing_ridgecv", "A_noVIX_1970:static_long", "B_full_1990:timing_ridgecv",
            "B_full_1990:static_long", "rotation_ridge", "industry_mom_12_1"]
    li = ld.set_index("strategy").loc[keep]
    lt = pd.DataFrame({"strategy": keep, "n": li["n"].astype(int).values,
                       "alpha (t)": [f"{100 * a:.2f} ({t:.2f})" for a, t in zip(li["alpha_ann"], li["t_alpha"])]})
    for c in FF6:
        lt[f"{c} (t)"] = [f"{b:.3f} ({t:.2f})" for b, t in zip(li[f"b_{c}"], li[f"t_{c}"])]
    lt["r2"] = li["r2"].values
    to_tex(lt, f"{MOD}_ff6_loadings", "Style exposures (net returns, full OOS window of each strategy: 1990-01 on for "
           "Spec A and the rotation strategies, 2000-01 on for Spec B) on FF5 + UMD. Timing and static strategies at 5\% "
           "volatility; rotation strategies at raw scale. Alpha in percent per year; NW(6) t in parentheses.",
           "tab:m6_ff6_loadings")
    # ledger rows for every loading quoted in FINDINGS (descriptive exposures, exploratory)
    for strat in keep:
        rowl = li.loc[strat]
        for c in FF6:
            add_test(f"FF6_{strat.replace(':', '_')}_{c}", "Style exposure: FF5+UMD loading of the net return (full OOS)",
                     "NW6 t on loading", rowl[f"t_{c}"], p2n(rowl[f"t_{c}"]), int(rowl["n"]), "exploratory",
                     f"loading={rowl[f'b_{c}']:.3f}")
    for k in rot:
        rr_ = rot_df[(rot_df["strategy"] == k) & (rot_df["period"] == "full_oos")].iloc[0]
        add_test(f"ROT_{k}_mean_net", "Q3 exploratory industry rotation: mean net return", "NW6 t on mean",
                 rr_["t_mean_net"], p2n(rr_["t_mean_net"]), int(rr_["n"]), "exploratory",
                 f"net ret={100 * rr_['ann_ret_net']:.2f}%/yr; Sharpe={rr_['sharpe_net']:.2f}; {rr_['start']} to {rr_['end']}")
    (pd.DataFrame({k: S["net"] for k, S in rot.items()})).to_csv(T("rotation_returns"))

    # ================================================================== 7. ledger
    led = pd.DataFrame(ledger)
    led.to_csv(T("tests_ledger"), index=False)

    # ================================================================== 8. figures
    fig_gw(fc, fixed, comb)
    fig_shrinkage(paths)
    fig_timing(port_series)
    fig_rotation(rot)
    print_summary(oos_df, port_df, lmn_df, rot_df, rs, led)


# ---------------------------------------------------------------------------------------------- figures
def _cum_sse(y, fm, fb):
    d = pd.concat([y, fm, fb], axis=1).dropna()
    return ((d.iloc[:, 0] - d.iloc[:, 2]) ** 2 - (d.iloc[:, 0] - d.iloc[:, 1]) ** 2).cumsum() * 1e4


def fig_gw(fc, fixed, comb):
    fig, axes = plt.subplots(3, 1, figsize=(7.2, 8.4), sharex=True)
    for ax, name, title in ((axes[0], "A_noVIX_1970", "(a) Spec A (no VIX, estimation from 1970): model vs historical mean"),
                            (axes[1], "B_full_1990", "(b) Spec B (full, estimation from 1990): model vs historical mean")):
        f = fc[name]
        ax.plot(_cum_sse(f["y"], f["forecast"], f["hist_mean"]), color=ENTITY["strategy"], label="Ridge, CV penalty (primary)")
        ax.plot(_cum_sse(f["y"], fixed[(name, 1.0)]["forecast"], f["hist_mean"]), color=AQUA, ls="--",
                label="Ridge, fixed penalty 1 (sensitivity)")
        ax.plot(_cum_sse(f["y"], fixed[(name, 0.0)]["forecast"], f["hist_mean"]), color=ORANGE, ls="--",
                label="OLS kitchen sink (no shrinkage)")
        ax.plot(_cum_sse(f["y"], comb[name], f["hist_mean"]), color=VIOLET, ls=":", label="Combination of univariate OLS")
        ax.axhline(0, color=INK2, lw=0.8); ax.set_title(title, loc="left")
        ax.set_ylabel("Cum. SSE(hist. mean) - SSE(model)\n(x 1e-4)")
        ax.axvline(pd.Timestamp("2010-01-31"), color=MUTED, lw=0.8, ls=":")
    ax = axes[2]
    b, b0 = fc["B_full_1990"], fc["B0_noATTN_1990"]
    ax.plot(_cum_sse(b["y"], b["forecast"], b0["forecast"]), color=ENTITY["strategy"], label="Ridge, CV penalty (primary)")
    ax.plot(_cum_sse(b["y"], fixed[("B_full_1990", 1.0)]["forecast"], fixed[("B0_noATTN_1990", 1.0)]["forecast"]),
            color=AQUA, ls="--", label="Ridge, fixed penalty 1 (sensitivity)")
    ax.plot(_cum_sse(b["y"], fixed[("B_full_1990", 0.0)]["forecast"], fixed[("B0_noATTN_1990", 0.0)]["forecast"]),
            color=ORANGE, ls="--", label="OLS kitchen sink (no shrinkage)")
    ax.axhline(0, color=INK2, lw=0.8); ax.axvline(pd.Timestamp("2010-01-31"), color=MUTED, lw=0.8, ls=":")
    ax.set_title("(c) Adding the attention signal: Spec B vs Spec B without attention", loc="left")
    ax.set_ylabel("Cum. SSE(no attention) - SSE(with)\n(x 1e-4)")
    axes[0].legend(loc="lower left", ncol=2)
    axes[1].legend(loc="lower left", ncol=2)
    axes[2].legend(loc="lower left", ncol=1)
    fig.text(0.01, -0.01, "Rising line = model beats the benchmark over that stretch (Goyal-Welch plot). Dotted vertical line: 2010-01.",
             fontsize=7, color=INK2)
    savefig(fig, f"{MOD}_gw_cumsse")


def fig_shrinkage(paths):
    PB, cvB = paths["B_full_1990"]; PA, cvA = paths["A_noVIX_1970"]
    fig, axes = plt.subplots(1, 3, figsize=(11.5, 3.8))
    groups = [("(a) Spec B: VS, MOM12, ATTN, VIX", ["VS", "MOM12", "ATTN", "LVIX"],
               {"VS": BLUE, "MOM12": GREEN, "ATTN": ENTITY["emv"], "LVIX": ENTITY["vix"]}),
              ("(b) Spec B: macro predictors", ["TERM", "CREDIT", "DGS10", "INFL", "CFNAI", "WTI"],
               {"TERM": AQUA, "CREDIT": VIOLET, "DGS10": RED, "INFL": YELLOW, "CFNAI": MAGENTA, "WTI": INK2})]
    for ax, (title, cols, colors) in zip(axes[:2], groups):
        for c in cols:
            ax.plot(PB.index, 100 * PB[c], color=colors[c], label=c)
        ax.set_xscale("log"); ax.axhline(0, color=INK2, lw=0.8)
        ax.set_title(title, loc="left", fontsize=9); ax.set_xlabel("Ridge penalty (per observation)")
        ax.set_ylabel("Coefficient (% per month per s.d.)"); ax.legend(ncol=2, fontsize=7)
    ax = axes[2]
    ax.plot(cvA.index[:-1], cvA.values[:-1], color=BLUE, label="Spec A (1970-2026)")
    ax.plot(cvB.index[:-1], cvB.values[:-1], color=ORANGE, label="Spec B (1990-2026)")
    ax.axhline(1, color=INK2, lw=0.8); ax.set_xscale("log")
    ax.set_title("(c) CV error relative to historical mean", loc="left", fontsize=9)
    ax.set_xlabel("Ridge penalty (per observation)"); ax.set_ylabel("CV MSE / CV MSE(historical mean)"); ax.legend()
    savefig(fig, f"{MOD}_shrinkage_path")


def fig_timing(port_series):
    fig, axes = plt.subplots(2, 1, figsize=(7.2, 6.2))
    for ax, name, title, st in ((axes[0], "A_noVIX_1970", "(a) Spec A, OOS from 1990-01", "1990-01-31"),
                                (axes[1], "B_full_1990", "(b) Spec B, OOS from 2000-01 (LMN from 2001-01)", "2000-01-31")):
        for lab, color, ls, text in (("timing_ridgecv", ENTITY["strategy"], "-", "Timing: ridge-CV forecast (primary)"),
                                     ("static_long", ENTITY["benchmark"], "-", "Static always-long Green-minus-Brown"),
                                     ("timing_ols_lambda0", ORANGE, "--", "Timing: OLS kitchen sink (robustness)"),
                                     ("lmn_sign", VIOLET, ":", "LMN portfolio shrinkage, sign (robustness)")):
            S = port_series.get((name, lab))
            if S is None:
                continue
            ax.plot(100 * S["net"].loc[st:].cumsum(), color=color, ls=ls, label=text)
        ax.axhline(0, color=INK2, lw=0.8); ax.set_title(title, loc="left")
        ax.set_ylabel("Cumulative net return (%, 5% vol)")
    axes[0].legend(loc="lower left", fontsize=7)
    axes[1].legend(loc="lower left", fontsize=7)
    savefig(fig, f"{MOD}_timing_vs_static")


def fig_rotation(rot):
    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    ax.plot(100 * rot["rotation_ridge"]["net"].cumsum(), color=ENTITY["strategy"], label="Pooled ridge rotation, top 8 - bottom 8")
    ax.plot(100 * rot["industry_mom_12_1"]["net"].cumsum(), color=ENTITY["benchmark"], label="Plain 12-1 industry momentum, top 8 - bottom 8")
    ax.axhline(0, color=INK2, lw=0.8); ax.set_ylabel("Cumulative net return (%, raw scale)")
    ax.set_title("Exploratory industry rotation, OOS from 1990-01 (net of 10 bp)", loc="left"); ax.legend(loc="upper left")
    savefig(fig, f"{MOD}_rotation_cum")


def print_summary(oos_df, port_df, lmn_df, rot_df, rs, led):
    cols = ["model", "benchmark", "period", "n", "r2_oos_pct", "cw_t", "cw_p_one_sided", "share_lambda_at_max", "label"]
    print(oos_df[oos_df["label"].eq("primary")][cols + ["p_holm_primary_family"]].to_string())
    print(oos_df[oos_df["label"].isin(["robustness", "exploratory"]) & oos_df["period"].isin(["full_oos", "post2010"])
                 & ~oos_df["model"].str.contains("univariate")][cols].to_string())
    print(port_df[port_df["period"].isin(["full_oos", "post2010", "holdout", "last18", "last12"])][
        ["strategy", "period", "n", "ann_ret_net", "sharpe_gross", "sharpe_net", "alpha_ff6_net", "t_alpha_ff6_net",
         "turnover_ann", "cost_drag_bp_ann", "frac_long"]].to_string())
    print(lmn_df.to_string()); print(rot_df[rot_df["period"].isin(["full_oos", "post2010"])].to_string()); print(rs)
    for nm in ("cv_design", "team_target_check", "scaling_sensitivity", "lmn_attn_increment", "timing_vs_prevmean"):
        print(f"--- {nm}"); print(pd.read_csv(T(nm)).to_string())
    print(f"ledger rows: {len(led)}; " + ", ".join(f"{k}={v}" for k, v in led["primary_or_exploratory"].value_counts().items()))


if __name__ == "__main__":
    main()
