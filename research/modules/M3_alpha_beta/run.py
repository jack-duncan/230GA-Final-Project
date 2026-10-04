"""M3_alpha_beta: is any return of Green-minus-Brown (GB) or of the team's timing strategies alpha, or is it static or
time-varying beta (value, momentum, duration, market)? Does a rates/duration channel explain the holdout?

Run: cd /home/hashim/projects/GA/project/research && uv run python modules/M3_alpha_beta/run.py
Outputs: outputs/tables/M3_alpha_beta_*.csv|.tex, outputs/figures/M3_alpha_beta_*.pdf|.png, tests ledger.

PRE-SPECIFICATION (fixed before any M3 result was computed; everything not listed here is robustness/exploratory)
------------------------------------------------------------------------------------------------------------------
Conventions. GB = team legs (5 lowest / 5 highest emissions intensity, equal-weighted team FF49 file), full sample
1970-01..2026-07. Strategies = six team timing strategies + Always-short Brown, net returns from run_pipeline for the
team baseline (defaults) and the corrected baseline (CPI gap interpolated; attention and purification controls lagged
one month). Strategy "full_live" sample = 1999-03..2026-07 (every timing strategy in both baselines can hold a
position). NW(6) Bartlett HAC, the team's estimator; all p-values from t(n-k), k = coefficients incl. constant.
BOND = 10y par Treasury excess return from GS10 with modified duration and convexity.

(i)  Q1 PRIMARY: BOND coefficient of GB in FF5+UMD+BOND, full 1970-2026 and post-2010 (2 tests, Holm).
     Positive = Green leg longer duration than Brown.
(ii) Q2 PRIMARY: for each of the six timing strategies, holdout (2022-08..2026-07) alpha under FF3+UMD+BOND vs FF3,
     and the joint Wald F test that the UMD and BOND loadings are zero. Both baselines (team = the write-up's claim;
     corrected = real-time version). Holm within each family of 6.
(iii) Q3 PRIMARY: Lewellen-Nagel decomposition with backward rolling 36-month betas (months t-36..t-1) on Mkt-RF, SMB,
     HML, UMD, BOND; statistic = annualized beta-timing component sum_k cov(beta_k,t, f_k,t), post-2010; circular block
     bootstrap (block 12, 5000 reps, joint rows), p = 2 min(P>0, P<0). Family of 7: GB + six corrected-baseline
     strategies (Holm).
Q4 (Treynor-Mazuy, Henriksson-Merton) and Q5 (return attribution) are descriptive: no primary test.

CHANGES AFTER THE FIRST (INTERRUPTED) RUN, none of which touches the three primary tests above:
- BOND is now computed by M8's build_bond (imported; identical to the earlier M3 series to 3e-17).
- Ferson-Schadt (exploratory): instruments standardized with expanding past-only moments (the specification asked
  for); the in-window standardization is kept as robustness. The joint test of c now reports a fixed-design block
  bootstrap p for the HAC Wald statistic, because the asymptotic HAC Wald with q = 20 over-rejects badly.
- Added (exploratory): the FF3-hedged Brown leg as an asset; an exchange-1 fact-check replication (d10y vs BOND);
  a Lewellen-Nagel decomposition of D = strategy - pi x Always-short Brown (attention-specific beta timing);
  a count summary of the timing tests.
- Block bootstraps use block = min(12, max(2, n // 8)) so short windows get at least 8 blocks per draw (n >= 96,
  including every primary test, keeps the team's 12; holdout n = 48 uses 6; COVID n = 24 uses 3). With block 12 a
  24-month window had only 2 blocks per draw and degenerate p-values.

CHANGES AFTER ADVERSARIAL VERIFICATION (exploratory/robustness only; the three primary tests are untouched):
- Ferson-Schadt joint test of c = 0: adds a wild block bootstrap p (restricted residual kept in its own month,
  Rademacher sign per 12-month block) next to the fixed-design p, and a seed-sensitivity table for both
  (fs_boot_seeds). The fixed-design draws use the same RNG stream as before, so their p-values are unchanged.
- Ledger: adds the factor loadings of GB and the legs (all models and periods) and the strategies' UMD loadings,
  the GS10-BOND counterpart of the BOND_eom leg regressions, the baseline-hedge mean and post-hedge BOND loadings
  of the hedge reruns, the mean and in-period alpha tests of D = strategy - pi x Always-short Brown, and the
  24-month structural and in-period regression attribution tests.
- holdout_alpha: adds the return contributions b x mean(f) of BOND and UMD under FF3+UMD+BOND.
- gb_short_window_alpha: GB's last-18 and last-12-month alphas with NW(6), NW(2) and classical OLS standard errors.
- factor_means: annualized factor means by period.
- key_numbers: adds factor means by period, GB short-window alphas, attribution rows and the new bootstrap p.
"""
from __future__ import annotations

import sys
import time
import pathlib
import warnings

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from m3lib import *                     # noqa: F401,F403
from m3lib import (MOD, END, STRAT_START, STRATS, BENCH, SHORT, M3_PERIODS, MODELS, TABLES, nw_fit, wald, lincom,
                   bond_frame, load_factor_panel, instruments, run_baseline, rolling_betas, ln_decomposition,
                   timing_cov_bootstrap, mean_block_bootstrap, ferson_schadt, timing_test, fname, to_tex, Ledger,
                   damodaran_tbond, corrected_macro, load_team, PERIODS, expanding_standardize, block_indices)
from team_pipeline import team_states, state_slopes, macro_state_tables, TEAM_GREEN, TEAM_BROWN  # noqa: E402
from common import holm  # noqa: E402
import numpy as np
import pandas as pd
from scipy import stats
from plotstyle import *                 # noqa: F401,F403
import plotstyle as ps
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, PercentFormatter

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)

T0 = time.perf_counter()
TP = lambda name: TABLES / f"{MOD}_{name}.csv"      # noqa: E731
TX = lambda name: TABLES / f"{MOD}_{name}.tex"      # noqa: E731
L = Ledger()
Q1_PERIODS = ["full", "post2010", "validation", "holdout", "covid", "inflation_rates", "last18", "last12"]
LN_PERIODS = ["full", "post2010", "validation", "pre_covid", "covid", "inflation_rates", "holdout", "last18", "last12"]
LNF = ["Mkt-RF", "SMB", "HML", "UMD", "BOND"]        # factor set for decomposition, attribution, Ferson-Schadt
COND = ["Mkt-RF", "HML", "UMD", "BOND"]              # factors with conditional betas in Ferson-Schadt
BOND_COSTS = {"asset": 10e-4, "Mkt-RF": 5e-4, "BOND": 5e-4, "other_factor": 25e-4}


def log(msg):
    print(f"[{time.perf_counter() - T0:6.1f}s] {msg}", flush=True)


def period_bounds(asset_kind, period):
    if period == "full":
        return M3_PERIODS["full"] if asset_kind == "leg" else M3_PERIODS["full_live"]
    return M3_PERIODS[period]


def period_label(asset_kind, period):
    if period == "full":
        return "full_1970" if asset_kind == "leg" else "full_live_1999"
    return period


# =============================================================================================== data
F = load_factor_panel()
log("factor panel loaded: " + ", ".join(F.columns))
runs = {"team": run_baseline("team", macro_states=True), "corrected": run_baseline("corrected", macro_states=True)}
legs = runs["team"]["legs"]
HEDGED = "Brown leg FF3-hedged"   # R^B_t - b_{t-1}'f_t (team 60m FF3 hedge, unscaled): what the strategies trade
ASSETS = {("GB", "legs"): legs["green_minus_brown"], ("Green leg", "legs"): legs["green_excess"],
          ("Brown leg", "legs"): legs["brown_excess"], (HEDGED, "legs"): runs["team"]["models"]["Brown leg"]["hedged"]}
assert np.allclose(runs["team"]["models"]["Brown leg"]["hedged"].dropna(),
                   runs["corrected"]["models"]["Brown leg"]["hedged"].dropna())   # hedge does not depend on the signal
for b, res in runs.items():
    for s in STRATS + [BENCH]:
        ASSETS[(s, b)] = res["strategies"][s]["net_return"]
kind_of = lambda key: "leg" if key[1] == "legs" else "strategy"   # noqa: E731
log(f"pipelines done; {len(ASSETS)} assets")

# =============================================================================================== Q0 BOND construction + validation
bf = bond_frame(F["RF"])
bf.to_csv(TP("bond_monthly"))
yr = bf.loc["1954-01-31":"2025-12-31"]
ann = pd.DataFrame({
    "bond_total": (1 + yr["ret_total"]).groupby(yr.index.year).prod() - 1,
    "bond_exact": (1 + yr["ret_exact"]).groupby(yr.index.year).prod() - 1,
    "bond_duration_only": (1 + yr["ret_dur_only"]).groupby(yr.index.year).prod() - 1,
    "rf": (1 + yr["RF"]).groupby(yr.index.year).prod() - 1,
    "gs10_dec_avg": yr["y10"].groupby(yr.index.year).last(),
})
ann["bond_excess"] = ann["bond_total"] - ann["rf"]
dam = damodaran_tbond()
if dam is not None:
    ann["damodaran_tbond"] = dam.reindex(ann.index)
if "BOND_eom" in bf:
    ye = bf.loc["1990-01-31":"2025-12-31"].dropna(subset=["BOND_eom"])
    g_ = (1 + ye["BOND_eom"] + ye["RF"]).groupby(ye.index.year)
    ann["bond_eom_total"] = (g_.prod() - 1).where(g_.count() == 12).reindex(ann.index)
ann["rank_worst"] = ann["bond_total"].rank()
ann.index.name = "year"
ann.to_csv(TP("bond_annual"))
b70 = bf.loc["1970-01-31":END]
x = b70["BOND"]
summ = {
    "sample": "1970-01..2026-07", "n_months": len(x), "mean_excess_ann": 12 * x.mean(), "vol_ann": np.sqrt(12) * x.std(),
    "sharpe": np.sqrt(12) * x.mean() / x.std(), "ar1": x.autocorr(), "corr_exact_repricing": b70["BOND"].corr(b70["BOND_exact"]),
    "max_abs_diff_vs_exact_bp": 1e4 * (b70["BOND"] - b70["BOND_exact"]).abs().max(),
    "mean_convexity_term_bp": 1e4 * (0.5 * b70["convexity"] * b70["dy"] ** 2).mean(),
    "mean_mod_duration": b70["D_mod"].mean(), "min_mod_duration": b70["D_mod"].min(), "max_mod_duration": b70["D_mod"].max(),
    "worst_year": int(ann["bond_total"].idxmin()), "worst_year_total_return": ann["bond_total"].min(),
    "second_worst_year": int(ann["bond_total"].nsmallest(2).index[-1]), "second_worst_total_return": ann["bond_total"].nsmallest(2).iloc[-1],
    "best_year": int(ann["bond_total"].idxmax()), "best_year_total_return": ann["bond_total"].max(),
}
if dam is not None:
    c = ann[["bond_total", "damodaran_tbond"]].dropna()
    summ.update({"corr_annual_vs_damodaran": c.corr().iloc[0, 1], "n_years_damodaran": len(c),
                 "mean_abs_diff_vs_damodaran_pp": 100 * (c.iloc[:, 0] - c.iloc[:, 1]).abs().mean(),
                 "damodaran_worst_year": int(c["damodaran_tbond"].idxmin()), "damodaran_2022": c.loc[2022, "damodaran_tbond"]})
    r_ = summ["corr_annual_vs_damodaran"]; nn = len(c)
    tstat = r_ * np.sqrt((nn - 2) / (1 - r_ ** 2))
    L.add("Q0.bond.corr_damodaran", "Q0 BOND validation", "corr(annual BOND total return, Damodaran 10y T-bond)", r_,
          2 * stats.t.sf(abs(tstat), nn - 2), nn, "robustness", "1954-2025 calendar years; validation of the constructed factor")
    yrs93 = [y_ for y_ in range(1993, 2026) if y_ in c.index]
    summ["corr_annual_vs_damodaran_1993_2025"] = c.loc[yrs93].corr().iloc[0, 1]
# provenance: the series is M8's build_bond (imported); cross-check against M8's own verification table
summ["bond_source"] = "modules/M8_frozen_pre2010/run.py build_bond (imported by m3lib.bond_frame)"
summ["max_abs_diff_vs_independent_M3_impl"] = float(bf["check_absdiff_independent_impl"].max())
m8chk = TABLES / "M8_bond_check.csv"
if m8chk.exists():
    m8t = pd.read_csv(m8chk).set_index("check")["value"]
    for yy in (1994, 2008, 2022):
        kk = f"calendar-year total return {yy}"
        if kk in m8t.index:
            summ[f"absdiff_vs_M8_table_{yy}_total_return"] = abs(float(m8t[kk]) - ann.loc[yy, "bond_total"])
if "BOND_eom" in bf:
    e = b70[["BOND", "BOND_eom"]].dropna()
    summ.update({"eom_sample": f"{e.index[0]:%Y-%m}..{e.index[-1]:%Y-%m}", "corr_monthly_vs_eom_construction": e.corr().iloc[0, 1],
                 "ar1_eom": e["BOND_eom"].autocorr(), "ar1_avg_same_sample": e["BOND"].autocorr(),
                 "vol_ann_eom": np.sqrt(12) * e["BOND_eom"].std(), "vol_ann_avg_same_sample": np.sqrt(12) * e["BOND"].std(),
                 "corr_BOND_t_with_BONDeom_t_minus_1": e["BOND"].corr(e["BOND_eom"].shift(1)),
                 "eom_2022_total_return": ann.loc[2022, "bond_eom_total"], "eom_worst_year_1991_2025": int(ann["bond_eom_total"].idxmin())})
fitb = nw_fit(x, None)
L.add("Q0.bond.mean_excess", "Q0 BOND validation", "mean BOND excess return (annualized)", 12 * x.mean(), fitb["p"]["const"], len(x),
      "robustness", "1970-01..2026-07, NW(6)")
# stock-bond correlation by decade (known regime change: positive before 2000, negative 2000-2020, positive after 2021)
sb = pd.concat([F["Mkt-RF"], bf["BOND"]], axis=1).loc["1970":END].dropna()
dec_corr = sb.groupby((sb.index.year // 10) * 10).apply(lambda d: d.corr().iloc[0, 1])
dec_corr.loc["2022-2026"] = sb.loc["2022":].corr().iloc[0, 1]
for k_, v_ in dec_corr.items():
    summ[f"corr_mkt_bond_{k_}"] = v_
pd.Series(summ, name="value").to_frame().to_csv(TP("bond_validation_summary"))
worst = ann.nsmallest(8, "bond_total").reset_index()
cols_w = ["year", "gs10_dec_avg", "bond_total", "bond_exact", "bond_excess"] + (["damodaran_tbond"] if dam is not None else [])
wt = worst[cols_w].copy()
for c in cols_w[1:]:
    wt[c] = 100 * wt[c]
to_tex(wt, TX("bond_validation"), digits={c: 1 for c in cols_w[1:]} | {"gs10_dec_avg": 2},
       header=["Year", "GS10 Dec (\\%)", "BOND total (\\%)", "Exact reprice (\\%)", "Excess of RF (\\%)"] +
       (["Damodaran (\\%)"] if dam is not None else []))
log(f"Q0 BOND: worst year {summ['worst_year']} {summ['worst_year_total_return']:.3f}; corr Damodaran {summ.get('corr_annual_vs_damodaran', np.nan):.3f}")

# =============================================================================================== Q1 unconditional exposures
rows = []
for key, r in ASSETS.items():
    kind = kind_of(key)
    for period in Q1_PERIODS:
        a, b = period_bounds(kind, period)
        y = r.loc[a:b]
        for mname, cols in MODELS.items():
            fit = nw_fit(y, F[cols])
            row = {"asset": key[0], "baseline": key[1], "period": period_label(kind, period), "model": mname, "n": fit["n"],
                   "k": fit["k"], "df": fit["df"], "mean_ann": 12 * y.dropna().mean(), "alpha_ann": 12 * fit["b"]["const"],
                   "t_alpha": fit["t"]["const"], "p_alpha": fit["p"]["const"], "p_alpha_normal": fit["p_norm"]["const"], "r2": fit["r2"]}
            for c in cols:
                row[f"b_{fname(c)}"] = fit["b"][c]; row[f"t_{fname(c)}"] = fit["t"][c]; row[f"p_{fname(c)}"] = fit["p"][c]
            rows.append(row)
            is_primary = key == ("GB", "legs") and mname == "FF5+UMD+BOND" and period in ("full", "post2010")
            tag = f"{SHORT.get(key[0], key[0])}|{key[1]}|{mname}|{period_label(kind, period)}"
            L.add(f"Q1.alpha.{tag}", "Q1 unconditional exposures", "alpha (annualized)", 12 * fit["b"]["const"],
                  fit["p"]["const"], fit["n"], "exploratory", f"NW(6), t(n-k) p; df={fit['df']}")
            if "BOND" in cols:
                L.add(f"Q1.bond.{tag}", "Q1 unconditional exposures", "BOND loading", fit["b"]["BOND"], fit["p"]["BOND"], fit["n"],
                      "primary" if is_primary else "exploratory",
                      "PRIMARY (i): GB duration exposure" if is_primary else f"NW(6), t(n-k) p; df={fit['df']}")
            # other factor loadings: every loading for GB and the legs (static-beta question); UMD for the strategies
            for c in cols:
                if c == "BOND" or (kind == "strategy" and c != "UMD"):
                    continue
                L.add(f"Q1.loading.{fname(c)}.{tag}", "Q1 unconditional exposures", f"{fname(c)} loading", fit["b"][c], fit["p"][c],
                      fit["n"], "exploratory", f"NW(6), t(n-k) p; df={fit['df']}")
Q1 = pd.DataFrame(rows)
Q1.to_csv(TP("exposures"), index=False)
prim1 = Q1[(Q1.asset == "GB") & (Q1.model == "FF5+UMD+BOND") & Q1.period.isin(["full_1970", "post2010"])].copy()
prim1["holm_p_BOND"] = holm(prim1.set_index("period")["p_BOND"]).to_numpy()
prim1.to_csv(TP("primary_i"), index=False)
# compact exposure table for the legs (FF5+UMD+BOND, full and post-2010) + BOND loading across models
fcols = ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "UMD", "BOND"]
leg_rows = []
for asset in ["Green leg", "Brown leg", "GB", HEDGED]:
    for period in ["full_1970", "post2010", "holdout"]:
        rr = Q1[(Q1.asset == asset) & (Q1.model == "FF5+UMD+BOND") & (Q1.period == period)].iloc[0]
        d = {"Asset": asset, "Period": period.replace("_", " "), "alpha (%/yr)": 100 * rr.alpha_ann, "t(alpha)": rr.t_alpha}
        for c in fcols:
            d[c] = rr[f"b_{c}"]
        d["t(BOND)"] = rr["t_BOND"]; d["R2"] = rr.r2
        leg_rows.append(d)
legtab = pd.DataFrame(leg_rows)
legtab.to_csv(TP("leg_exposures"), index=False)
to_tex(legtab, TX("leg_exposures"), col_format="ll" + "r" * (len(legtab.columns) - 2))
bond_models = Q1[Q1.model.isin(["FF3+BOND", "FF3+UMD+BOND", "FF5+UMD+BOND"])][["asset", "baseline", "period", "model", "n", "b_BOND", "t_BOND", "p_BOND"]]
bond_models.to_csv(TP("bond_loadings"), index=False)
# ---- GB in the short windows the brief asks about: the same alphas with other standard errors (NW(6) on 12-18
# observations is unreliable). OLS = classical homoskedastic se; NW(2) = Bartlett with 2 lags. Exploratory.
sw_rows = []
for period in ("last18", "last12"):
    a, e = PERIODS[period]
    y = ASSETS[("GB", "legs")].loc[a:e]
    m0, m2 = nw_fit(y, None), nw_fit(y, None, lags=2)
    t0 = y.mean() / (y.std(ddof=1) / np.sqrt(len(y)))
    sw_rows.append({"period": period, "model": "mean (no factors)", "n": m0["n"], "df": m0["df"], "alpha_ann": 12 * y.mean(),
                    "t_nw6": m0["t"]["const"], "p_nw6": m0["p"]["const"], "t_nw2": m2["t"]["const"], "p_nw2": m2["p"]["const"],
                    "t_ols": t0, "p_ols": 2 * stats.t.sf(abs(t0), len(y) - 1)})
    for mname, cols in MODELS.items():
        f6, f2, f0 = nw_fit(y, F[cols]), nw_fit(y, F[cols], lags=2), nw_fit(y, F[cols], lags=0)
        # classical OLS se (df-corrected residual variance) for the constant
        d_ = pd.concat([y.rename("__y"), F[cols]], axis=1, sort=True).dropna()
        Xo = np.column_stack([np.ones(len(d_)), d_[cols].to_numpy(float)])
        s2 = float((f0["resid"] ** 2).sum()) / f0["df"]
        se_ols = np.sqrt(s2 * np.linalg.pinv(Xo.T @ Xo)[0, 0])
        t_ols = f0["b"]["const"] / se_ols
        sw_rows.append({"period": period, "model": mname, "n": f6["n"], "df": f6["df"], "alpha_ann": 12 * f6["b"]["const"],
                        "t_nw6": f6["t"]["const"], "p_nw6": f6["p"]["const"], "t_nw2": f2["t"]["const"], "p_nw2": f2["p"]["const"],
                        "t_ols": t_ols, "p_ols": 2 * stats.t.sf(abs(t_ols), f6["df"])})
        L.add(f"Q1.alpha_ols.GB|legs|{mname}|{period}", "Q1 unconditional exposures", "alpha (annualized), classical OLS se",
              12 * f6["b"]["const"], 2 * stats.t.sf(abs(t_ols), f6["df"]), f6["n"], "robustness",
              f"same estimate as Q1.alpha.GB|legs|{mname}|{period}; homoskedastic se; t(n-k) p; df={f6['df']}")
SW = pd.DataFrame(sw_rows)
SW.to_csv(TP("gb_short_window_alpha"), index=False)
print(SW.round(4).to_string())
log("Q1 done: GB BOND loading " + ", ".join(f"{r.period}: {r.b_BOND:.3f} (t {r.t_BOND:.2f})" for r in prim1.itertuples()))

# =============================================================================================== Q2a holdout alpha before/after BOND
H0, H1 = PERIODS["holdout"]
rows = []
for b in ("team", "corrected"):
    for s in STRATS + [BENCH]:
        y = ASSETS[(s, b)].loc[H0:H1]
        rec = {"baseline": b, "strategy": s, "short": SHORT[s], "n": len(y), "ann_net": 12 * y.mean()}
        for mname in ("FF3", "FF3+BOND", "FF3+UMD+BOND", "FF5+UMD+BOND"):
            fit = nw_fit(y, F[MODELS[mname]])
            rec[f"alpha_{mname}"] = 12 * fit["b"]["const"]; rec[f"t_{mname}"] = fit["t"]["const"]; rec[f"p_{mname}"] = fit["p"]["const"]
            rec[f"se_{mname}"] = 12 * fit["se"]["const"]; rec[f"df_{mname}"] = fit["df"]
            if "BOND" in MODELS[mname]:
                rec[f"bBOND_{mname}"] = fit["b"]["BOND"]; rec[f"tBOND_{mname}"] = fit["t"]["BOND"]
            if mname == "FF3+UMD+BOND":
                w = wald(fit, ["UMD", "BOND"])
                rec["wald_UMD_BOND_F"] = w["F"]; rec["wald_UMD_BOND_p"] = w["p_F"]
                rec["bUMD"] = fit["b"]["UMD"]; rec["tUMD"] = fit["t"]["UMD"]
                # regression-based return contribution of each added factor: 12 x b_k x mean(f_k) over the holdout
                # (positive = the exposure added to the strategy's return)
                fbar = F[["BOND", "UMD"]].loc[H0:H1].mean()
                rec["contrib_BOND_FF3+UMD+BOND"] = 12 * fit["b"]["BOND"] * fbar["BOND"]
                rec["contrib_UMD_FF3+UMD+BOND"] = 12 * fit["b"]["UMD"] * fbar["UMD"]
        rows.append(rec)
Q2 = pd.DataFrame(rows)
for b in ("team", "corrected"):
    m = (Q2.baseline == b) & Q2.strategy.isin(STRATS)
    Q2.loc[m, "holm_p_alpha_FF3+UMD+BOND"] = holm(Q2.loc[m, "p_FF3+UMD+BOND"]).to_numpy()
    Q2.loc[m, "holm_p_wald"] = holm(Q2.loc[m, "wald_UMD_BOND_p"]).to_numpy()
    Q2.loc[m, "holm_p_alpha_FF3"] = holm(Q2.loc[m, "p_FF3"]).to_numpy()
for r in Q2.itertuples():
    prim = r.strategy in STRATS
    kind = "primary" if prim else "exploratory"
    L.add(f"Q2.holdout_alpha_FF3UMDBOND.{r.short}|{r.baseline}", "Q2 holdout explanation", "holdout alpha FF3+UMD+BOND (annualized)",
          Q2.loc[r.Index, "alpha_FF3+UMD+BOND"], Q2.loc[r.Index, "p_FF3+UMD+BOND"], r.n, kind,
          f"PRIMARY (ii); FF3 alpha {Q2.loc[r.Index, 'alpha_FF3']:.4f} (p {Q2.loc[r.Index, 'p_FF3']:.3f}); df={Q2.loc[r.Index, 'df_FF3+UMD+BOND']}" if prim else "benchmark")
    L.add(f"Q2.holdout_wald_UMD_BOND.{r.short}|{r.baseline}", "Q2 holdout explanation", "Wald F: b_UMD = b_BOND = 0 (holdout)",
          r.wald_UMD_BOND_F, r.wald_UMD_BOND_p, r.n, kind, "PRIMARY (ii); F(2, n-6)" if prim else "benchmark")
    L.add(f"Q2.holdout_alpha_FF3BOND.{r.short}|{r.baseline}", "Q2 holdout explanation", "holdout alpha FF3+BOND (annualized)",
          Q2.loc[r.Index, "alpha_FF3+BOND"], Q2.loc[r.Index, "p_FF3+BOND"], r.n, "robustness", "NW(6) HAC, t(n-k) p")
    L.add(f"Q2.holdout_alpha_FF5UMDBOND.{r.short}|{r.baseline}", "Q2 holdout explanation", "holdout alpha FF5+UMD+BOND (annualized)",
          Q2.loc[r.Index, "alpha_FF5+UMD+BOND"], Q2.loc[r.Index, "p_FF5+UMD+BOND"], r.n, "robustness", "NW(6) HAC, t(n-k) p")
Q2.to_csv(TP("holdout_alpha"), index=False)
tex = Q2[Q2.strategy.isin(STRATS)].copy()
tex = pd.DataFrame({"Baseline": tex.baseline, "Strategy": tex.short, "Net (%/yr)": 100 * tex.ann_net,
                    "a FF3": 100 * tex["alpha_FF3"], "t FF3": tex["t_FF3"],
                    "a +BOND": 100 * tex["alpha_FF3+BOND"], "t +BOND": tex["t_FF3+BOND"],
                    "a +UMD+BOND": 100 * tex["alpha_FF3+UMD+BOND"], "t +UMD+BOND": tex["t_FF3+UMD+BOND"],
                    "p (t48-6)": tex["p_FF3+UMD+BOND"], "b BOND": tex["bBOND_FF3+UMD+BOND"], "b UMD": tex["bUMD"],
                    "Wald p": tex["wald_UMD_BOND_p"]})
to_tex(tex, TX("holdout_alpha"), digits={"p (t48-6)": 3, "Wald p": 3}, col_format="ll" + "r" * 11,
       header=["Baseline", "Strategy", "Net", r"$\alpha$ FF3", "$t$", r"$\alpha$ +BOND", "$t$", r"$\alpha$ +UMD+BOND", "$t$",
               "$p$", r"$\beta_{BOND}$", r"$\beta_{UMD}$", "Wald $p$"])
log("Q2a done")

# ---- robustness: BOND built from end-of-month Treasury par yields (1990-02 onward) instead of GS10 monthly averages
eom_rows = []
if "BOND_eom" in F:
    swap = lambda cols: [("BOND_eom" if c == "BOND" else c) for c in cols]  # noqa: E731
    e0 = F["BOND_eom"].first_valid_index().strftime("%Y-%m-%d")
    for asset in ("GB", "Green leg", "Brown leg"):
        for per, (a, e) in {"1990_2026": (e0, END), "post2010": PERIODS["post2010"], "holdout": PERIODS["holdout"],
                            "inflation_rates": PERIODS["inflation_rates"]}.items():
            y = ASSETS[(asset, "legs")].loc[a:e]
            for bname, cols in (("BOND (GS10 avg)", MODELS["FF5+UMD+BOND"]), ("BOND_eom", swap(MODELS["FF5+UMD+BOND"]))):
                fit = nw_fit(y, F[cols])
                bc = "BOND_eom" if "BOND_eom" in cols else "BOND"
                eom_rows.append({"test": "Q1 leg duration", "asset": asset, "baseline": "legs", "period": per, "bond_series": bname,
                                 "model": "FF5+UMD+BOND", "n": fit["n"], "b_bond": fit["b"][bc], "t_bond": fit["t"][bc], "p_bond": fit["p"][bc],
                                 "alpha_ann": 12 * fit["b"]["const"], "t_alpha": fit["t"]["const"], "p_alpha": fit["p"]["const"]})
                if bname == "BOND_eom":
                    L.add(f"Q1.bond_eom.{asset}|{per}", "Q1 unconditional exposures", "BOND_eom loading (FF5+UMD+BOND_eom)", fit["b"][bc],
                          fit["p"][bc], fit["n"], "robustness", "BOND from end-of-month Treasury par yields")
                elif per == "1990_2026":   # GS10 counterpart on the same months (other windows duplicate Q1 rows)
                    L.add(f"Q1.bond_gs10_same_months.{asset}|{per}", "Q1 unconditional exposures", "BOND loading (FF5+UMD+BOND), BOND_eom months",
                          fit["b"][bc], fit["p"][bc], fit["n"], "robustness", "GS10 BOND on the months where BOND_eom exists (comparison row)")
    for b in ("team", "corrected"):
        for s in STRATS + [BENCH]:
            y = ASSETS[(s, b)].loc[H0:H1]
            fit = nw_fit(y, F[swap(MODELS["FF3+UMD+BOND"])])
            w = wald(fit, ["UMD", "BOND_eom"])
            eom_rows.append({"test": "Q2 holdout alpha", "asset": s, "baseline": b, "period": "holdout", "bond_series": "BOND_eom",
                             "model": "FF3+UMD+BOND", "n": fit["n"], "b_bond": fit["b"]["BOND_eom"], "t_bond": fit["t"]["BOND_eom"],
                             "p_bond": fit["p"]["BOND_eom"], "alpha_ann": 12 * fit["b"]["const"], "t_alpha": fit["t"]["const"],
                             "p_alpha": fit["p"]["const"], "wald_UMD_BOND_p": w["p_F"]})
            L.add(f"Q2.holdout_alpha_FF3UMDBONDeom.{SHORT[s]}|{b}", "Q2 holdout explanation", "holdout alpha FF3+UMD+BOND_eom (annualized)",
                  12 * fit["b"]["const"], fit["p"]["const"], fit["n"], "robustness", "BOND from end-of-month Treasury par yields")
    EOM = pd.DataFrame(eom_rows)
    EOM.to_csv(TP("bond_eom_robustness"), index=False)
    log("BOND end-of-month robustness done")
    print(EOM.round(3).to_string())
print(Q2[["baseline", "short", "ann_net", "alpha_FF3", "t_FF3", "alpha_FF3+BOND", "t_FF3+BOND", "alpha_FF3+UMD+BOND",
          "t_FF3+UMD+BOND", "p_FF3+UMD+BOND", "bBOND_FF3+UMD+BOND", "tBOND_FF3+UMD+BOND", "bUMD", "tUMD", "wald_UMD_BOND_p"]].round(3).to_string())

# ---- exchange-1 fact-check revisited: d10y (change in GS10, pp) vs the traded BOND factor
F["d10y"] = load_fred("GS10").diff().reindex(F.index)
F["COM"] = load_fred("PALLFNFINDEXM").pct_change().reindex(F.index)
fc_rows = []
fc_periods = {"validation": PERIODS["validation"], "holdout": PERIODS["holdout"], "post2010": PERIODS["post2010"]}
fc_specs_leg = {"d10y+COM (exchange-1 spec)": ["d10y", "COM"], "BOND+COM": ["BOND", "COM"], "BOND": ["BOND"],
                "FF3+UMD+BOND": MODELS["FF3+UMD+BOND"], "FF5+UMD+BOND": MODELS["FF5+UMD+BOND"]}
for per, (a, e) in fc_periods.items():
    y = ASSETS[(HEDGED, "legs")].loc[a:e]
    for sname, cols in fc_specs_leg.items():
        fit = nw_fit(y, F[cols])
        rc = "d10y" if "d10y" in cols else "BOND"
        fc_rows.append({"asset": HEDGED, "baseline": "legs", "period": per, "spec": sname, "n": fit["n"], "rate_factor": rc,
                        "b_rate": fit["b"][rc], "t_rate": fit["t"][rc], "p_rate": fit["p"][rc],
                        "b_COM": fit["b"].get("COM", np.nan), "t_COM": fit["t"].get("COM", np.nan),
                        "alpha_ann": 12 * fit["b"]["const"], "t_alpha": fit["t"]["const"], "p_alpha": fit["p"]["const"],
                        "sum_d10y_pp": F["d10y"].loc[a:e].sum(), "BOND_mean_ann": 12 * F["BOND"].loc[a:e].mean()})
        L.add(f"Q2.factcheck.{HEDGED}|{per}|{sname}", "Q2 holdout explanation", f"{rc} loading of the FF3-hedged Brown leg",
              fit["b"][rc], fit["p"][rc], fit["n"], "robustness", "exchange-1 fact-check replication; NW(6) t(n-k) p")
fc_specs_str = {"FF5+UMD+d10y+COM (exchange-1 spec)": ["Mkt-RF5", "SMB5", "HML5", "RMW", "CMA", "UMD", "d10y", "COM"],
                "FF5+UMD+BOND+COM": MODELS["FF5+UMD+BOND"] + ["COM"], "FF5+UMD+BOND": MODELS["FF5+UMD+BOND"]}
for b in ("team", "corrected"):
    for s in STRATS + [BENCH]:
        y = ASSETS[(s, b)].loc[H0:H1]
        for sname, cols in fc_specs_str.items():
            fit = nw_fit(y, F[cols])
            rc = "d10y" if "d10y" in cols else "BOND"
            fc_rows.append({"asset": s, "baseline": b, "period": "holdout", "spec": sname, "n": fit["n"], "rate_factor": rc,
                            "b_rate": fit["b"][rc], "t_rate": fit["t"][rc], "p_rate": fit["p"][rc],
                            "b_COM": fit["b"].get("COM", np.nan), "t_COM": fit["t"].get("COM", np.nan),
                            "alpha_ann": 12 * fit["b"]["const"], "t_alpha": fit["t"]["const"], "p_alpha": fit["p"]["const"]})
            L.add(f"Q2.factcheck.{SHORT[s]}|{b}|holdout|{sname}", "Q2 holdout explanation", "holdout alpha (annualized)",
                  12 * fit["b"]["const"], fit["p"]["const"], fit["n"], "robustness", f"exchange-1 fact-check replication; df={fit['df']}")
FC = pd.DataFrame(fc_rows)
FC.to_csv(TP("factcheck_rates"), index=False)
print(FC.round(3).to_string())
# the hedged Brown leg itself: holdout alpha before/after BOND (not in the Holm family; reference row)
hb_rows = []
for mname in ("FF3", "FF3+BOND", "FF3+UMD+BOND", "FF5+UMD+BOND"):
    fit = nw_fit(ASSETS[(HEDGED, "legs")].loc[H0:H1], F[MODELS[mname]])
    hb_rows.append({"model": mname, "n": fit["n"], "alpha_ann": 12 * fit["b"]["const"], "t_alpha": fit["t"]["const"],
                    "p_alpha": fit["p"]["const"], "b_BOND": fit["b"].get("BOND", np.nan), "t_BOND": fit["t"].get("BOND", np.nan)})
HB = pd.DataFrame(hb_rows)
HB.insert(0, "asset", HEDGED)
HB.to_csv(TP("hedged_brown_holdout"), index=False)
log("fact-check replication done")

# =============================================================================================== Q2b BOND-hedged reruns
HEDGES = {"FF3 (team)": (["Mkt-RF", "SMB", "HML"], None),
          "FF3+BOND": (["Mkt-RF", "SMB", "HML", "BOND"], BOND_COSTS),
          "FF3+UMD+BOND": (["Mkt-RF", "SMB", "HML", "UMD", "BOND"], BOND_COSTS),
          "FF3+BOND (BOND 25bp)": (["Mkt-RF", "SMB", "HML", "BOND"], None),
          "FF3+UMD+BOND (BOND 25bp)": (["Mkt-RF", "SMB", "HML", "UMD", "BOND"], None)}
if "BOND_eom" in F:   # hedge with the month-end-yield BOND (a futures hedge earns month-end returns); betas from 1995 on
    HEDGES["FF3+BOND_eom"] = (["Mkt-RF", "SMB", "HML", "BOND_eom"], {**BOND_COSTS, "BOND_eom": 5e-4})
    HEDGES["FF3+UMD+BOND_eom"] = (["Mkt-RF", "SMB", "HML", "UMD", "BOND_eom"], {**BOND_COSTS, "BOND_eom": 5e-4})
fac_h = F[["Mkt-RF", "SMB", "HML", "UMD", "BOND"] + (["BOND_eom"] if "BOND_eom" in F else []) + ["RF"]]
hedge_runs = {}
rows = []
for b in ("team", "corrected"):
    for hname, (cols, costs) in HEDGES.items():
        full = hname in ("FF3+BOND", "FF3+UMD+BOND")
        if hname == "FF3 (team)":
            res = runs[b]
        else:
            res = run_baseline(b, factors=fac_h, factor_cols=tuple(cols), costs=costs, full=full, macro_states=True)
        hedge_runs[(b, hname)] = res
        for s in STRATS + [BENCH]:
            net = res["strategies"][s]["net_return"]
            for per in ("post2010", "validation", "holdout", "last18", "last12"):
                a, e = PERIODS[per]
                y = net.loc[a:e]
                f0 = nw_fit(y, None)
                f3 = nw_fit(y, F[MODELS["FF3"]])
                f5 = nw_fit(y, F[MODELS["FF3+UMD+BOND"]])
                rec = {"baseline": b, "hedge": hname, "strategy": s, "short": SHORT[s], "period": per, "n": len(y),
                       "ann_net": 12 * y.mean(), "t_mean": f0["t"]["const"], "p_mean": f0["p"]["const"],
                       "sharpe": np.sqrt(12) * y.mean() / y.std() if y.std() > 0 else np.nan,
                       "alpha_FF3": 12 * f3["b"]["const"], "t_alpha_FF3": f3["t"]["const"], "p_alpha_FF3": f3["p"]["const"],
                       "alpha_FF3UMDBOND": 12 * f5["b"]["const"], "t_alpha_FF3UMDBOND": f5["t"]["const"],
                       "p_alpha_FF3UMDBOND": f5["p"]["const"], "bBOND_after": f5["b"]["BOND"], "tBOND_after": f5["t"]["BOND"],
                       "pBOND_after": f5["p"]["BOND"],
                       "annual_turnover": 12 * res["strategies"][s]["turnover"].loc[a:e].mean(),
                       "ann_cost": 12 * res["strategies"][s]["cost"].loc[a:e].mean()}
                if per == "holdout":
                    bb = mean_block_bootstrap(y, reps=5000 if full else 1000)
                    rec.update({"boot_ci_low": bb["ci_low"], "boot_ci_high": bb["ci_high"], "boot_p": bb["p_boot"], "boot_block": bb["block"]})
                rows.append(rec)
                if per in ("holdout", "post2010"):
                    L.add(f"Q2b.hedged_mean.{SHORT[s]}|{b}|{hname}|{per}", "Q2 BOND-hedged rerun", f"mean net return ({per}, annualized)",
                          12 * y.mean(), f0["p"]["const"], len(y), "robustness",
                          f"hedge {hname}" + (" (baseline hedge, reference row)" if hname == "FF3 (team)" else "") + "; NW(6) t(n-1) p")
                if per == "holdout" and hname != "FF3 (team)":
                    L.add(f"Q2b.residual_bond_loading.{SHORT[s]}|{b}|{hname}|{per}", "Q2 BOND-hedged rerun",
                          "BOND loading of the rerun net return (FF3+UMD+BOND)", f5["b"]["BOND"], f5["p"]["BOND"], len(y), "robustness",
                          f"hedge {hname}; exposure left after the rolling hedge; NW(6) t(n-k) p")
Q2b = pd.DataFrame(rows)
Q2b.to_csv(TP("bond_hedge_rerun"), index=False)
# comparison tables of the full-mode runs (bootstrap 5000) for the record
for (b, hname), res in hedge_runs.items():
    if hname in ("FF3+BOND", "FF3+UMD+BOND"):
        ct = res["comparison_table"].copy(); ct.insert(0, "hedge", hname); ct.insert(0, "baseline", b)
        ct.to_csv(TP(f"bond_hedge_comparison_{b}_{hname.replace('+', '_')}"), index=False)
ht = Q2b[(Q2b.period == "holdout") & Q2b.strategy.isin(STRATS) & Q2b.hedge.isin(["FF3 (team)", "FF3+BOND", "FF3+UMD+BOND"])]
ht = ht.pivot_table(index=["baseline", "short"], columns="hedge", values=["ann_net", "t_mean"], sort=False)
ht.columns = [f"{v}|{h}" for v, h in ht.columns]
ht = ht.reset_index()
order = ["ann_net|FF3 (team)", "t_mean|FF3 (team)", "ann_net|FF3+BOND", "t_mean|FF3+BOND", "ann_net|FF3+UMD+BOND", "t_mean|FF3+UMD+BOND"]
ht = ht[["baseline", "short"] + order]
for c in order:
    if c.startswith("ann_net"):
        ht[c] = 100 * ht[c]
to_tex(ht, TX("bond_hedge_rerun"), col_format="ll" + "r" * 6,
       header=["Baseline", "Strategy", "Net FF3 hedge", "$t$", "Net FF3+BOND hedge", "$t$", "Net FF3+UMD+BOND hedge", "$t$"])
log("Q2b done")
print(Q2b[(Q2b.period == "holdout") & Q2b.strategy.isin(STRATS)][["baseline", "hedge", "short", "ann_net", "t_mean", "p_mean", "alpha_FF3", "t_alpha_FF3", "ann_cost"]].round(3).to_string())

# =============================================================================================== Q2c macro-state finding with BOND controlled
def state_slopes_ctrl(signal, state, fwd, ctrl, start, end, min_months=12):
    """Team state-slope regression plus a z-scored control realized in the same month as the forward residual."""
    zs = lambda s: (s - s.mean()) / s.std(ddof=1)  # noqa: E731
    d = pd.concat([signal.rename("A"), state.rename("S"), fwd.rename("y"), ctrl.rename("c")], axis=1, sort=True).loc[start:end].dropna()
    a, s = zs(d["A"]), d["S"]
    n_on, n_off = int(s.sum()), int((1 - s).sum())
    if min(n_on, n_off) < min_months:
        return {"n": len(d), "n_on": n_on}
    X = pd.DataFrame({"S": s, "Aoff": a * (1 - s), "Aon": a * s, "ctrl": zs(d["c"])})
    fit = nw_fit(zs(d["y"]), X)
    diff, se, p = lincom(fit, {"Aon": 1.0, "Aoff": -1.0})
    return {"n": len(d), "n_on": n_on, "slope_off": fit["b"]["Aoff"], "t_off": fit["t"]["Aoff"], "slope_on": fit["b"]["Aon"],
            "t_on": fit["t"]["Aon"], "diff": diff, "t_diff": diff / se, "p_diff": p, "b_ctrl": fit["b"]["ctrl"], "t_ctrl": fit["t"]["ctrl"]}


ms_rows = []
mac_team = load_team()["macro"]
start_ms = runs["team"]["macro_state_start"]
bond_fwd = F["BOND"].shift(-1)
variants = {
    "team signals, FF3 residual (team result)": ("team", runs["team"]["models"]["Brown leg"]["epsilon"], None, mac_team),
    "team signals, FF3 residual + BOND(t+1) control": ("team", runs["team"]["models"]["Brown leg"]["epsilon"], bond_fwd, mac_team),
    "team signals, FF3+BOND-hedged residual": ("team", hedge_runs[("team", "FF3+BOND")]["models"]["Brown leg"]["epsilon"], None, mac_team),
    "team signals, FF3+UMD+BOND-hedged residual": ("team", hedge_runs[("team", "FF3+UMD+BOND")]["models"]["Brown leg"]["epsilon"], None, mac_team),
    "corrected signals, FF3 residual": ("corrected", runs["corrected"]["models"]["Brown leg"]["epsilon"], None, corrected_macro()),
    "corrected signals, FF3+BOND-hedged residual": ("corrected", hedge_runs[("corrected", "FF3+BOND")]["models"]["Brown leg"]["epsilon"], None, corrected_macro()),
    "team signals, target = BOND(t+1)": ("team", F["BOND"], None, mac_team),
}
if "BOND_eom" in F:
    variants["team signals, FF3 residual + BOND_eom(t+1) control"] = ("team", runs["team"]["models"]["Brown leg"]["epsilon"], F["BOND_eom"].shift(-1), mac_team)
    variants["corrected signals, FF3 residual + BOND_eom(t+1) control"] = ("corrected", runs["corrected"]["models"]["Brown leg"]["epsilon"], F["BOND_eom"].shift(-1), corrected_macro())
    variants["team signals, target = BOND_eom(t+1)"] = ("team", F["BOND_eom"], None, mac_team)
for vname, (b, eps, ctrl, mac) in variants.items():
    sig = runs[b]["signals"]
    states = team_states(mac)
    for sn, sgl in (("Raw attention", sig["raw"]), ("Purified attention", sig["pure"])):
        for st in states:
            for per, (a, e) in {"Full": (start_ms, END), "Pre-holdout": (start_ms, "2022-07-31"), "Holdout": (H0, END)}.items():
                if ctrl is None:
                    r = state_slopes(sgl, states[st], eps.shift(-1), a, e, 12, 6)
                    if np.isfinite(r.get("t_diff", np.nan)):
                        r["p_diff"] = 2 * stats.t.sf(abs(r["t_diff"]), r["n"] - 4)
                else:
                    r = state_slopes_ctrl(sgl, states[st], eps.shift(-1), ctrl, a, e)
                ms_rows.append({"variant": vname, "signal": sn, "state": st, "period": per, **r})
MS = pd.DataFrame(ms_rows)
MS.to_csv(TP("macro_state"), index=False)
for r in MS[(MS.period == "Full")].itertuples():
    if np.isfinite(getattr(r, "t_diff", np.nan)):
        L.add(f"Q2c.state_diff.{r.variant}|{r.signal}|{r.state}", "Q2 macro-state with BOND", "slope_on - slope_off (IC scale)",
              r.diff, r.p_diff, r.n, "exploratory", "team state-slope regression; t(n-4) p (t(n-5) with control)")
mst = MS[(MS.state == "High rates") & (MS.period == "Full")][["variant", "signal", "n", "n_on", "slope_off", "t_off", "slope_on", "t_on", "diff", "t_diff", "p_diff"]]
to_tex(mst, TX("macro_state_high_rates"), digits={"p_diff": 3, "slope_off": 3, "slope_on": 3, "diff": 3}, col_format="llrrrrrrrrr",
       header=["Variant", "Signal", "$n$", "$n_{on}$", "slope off", "$t$", "slope on", "$t$", "diff", "$t$", "$p$"])
log("Q2c done")
print(mst.round(3).to_string())

# =============================================================================================== Q3a Ferson-Schadt conditional alpha
Zraw = instruments().shift(1)          # z_{t-1} aligned to return month t (information-date lag already inside)
Z = expanding_standardize(Zraw, min_periods=24)   # real-time standardization (expanding moments, past-only)
pd.concat([Zraw.add_suffix("_lag1"), Z.add_suffix("_lag1_expstd")], axis=1).loc["1965":END].to_csv(TP("instruments_lagged"))
FSF = F[LNF]
dum = pd.DataFrame(index=F.index)
dum["D_covid"] = ((F.index >= PERIODS["covid"][0]) & (F.index <= PERIODS["covid"][1])).astype(float)
dum["D_holdout"] = (F.index >= H0).astype(float)
FS_BOOT = 999
fs_rows = []
for key, r in ASSETS.items():
    kind = kind_of(key)
    for period in ("full", "post2010", "validation"):
        a, e = period_bounds(kind, period)
        out = ferson_schadt(r, FSF, Z, COND, a, e, standardize="expanding", boot_reps=FS_BOOT)
        fit = out["fit"]
        unc = nw_fit(r.loc[out["start"]:out["end"]], FSF)
        tv = ferson_schadt(r, FSF, Z, COND, a, e, tv_alpha=True)
        win = ferson_schadt(r, FSF, Zraw, COND, a, e, standardize="window")
        rec = {"asset": key[0], "baseline": key[1], "period": period_label(kind, period), "start": out["start"].strftime("%Y-%m"),
               "n": fit["n"], "k": fit["k"],
               "alpha_uncond": 12 * unc["b"]["const"], "t_alpha_uncond": unc["t"]["const"], "p_alpha_uncond": unc["p"]["const"],
               "alpha_cond": 12 * fit["b"]["const"], "t_alpha_cond": fit["t"]["const"], "p_alpha_cond": fit["p"]["const"],
               "wald_c_chi2": out["wald_c"]["chi2"], "wald_c_q": out["wald_c"]["q"], "wald_c_p_F": out["wald_c"]["p_F"],
               "wald_c_p_chi2": out["wald_c"]["p_chi2"], "boot_wald_c_p": out["boot_wald_c"]["p"],
               "boot_wald_null_q95": out["boot_wald_c"]["null_q95"], "boot_reps": out["boot_wald_c"]["reps"],
               "boot_wald_c_wild_p": out["boot_wald_c_wild"]["p"], "boot_wald_wild_null_q95": out["boot_wald_c_wild"]["null_q95"],
               "ols_F_c": out["ols_F_c"]["F"], "ols_F_c_p": out["ols_F_c"]["p"],
               "r2_uncond": unc["r2"], "r2_cond": fit["r2"], "adj_r2_cond": out["adj_r2"], "adj_r2_restricted": out["adj_r2_restricted"],
               "tv_alpha_wald_p_F": tv["wald_a"]["p_F"], "tv_alpha_const": 12 * tv["fit"]["b"]["const"],
               "win_alpha_cond": 12 * win["fit"]["b"]["const"], "win_t_alpha_cond": win["fit"]["t"]["const"],
               "win_p_alpha_cond": win["fit"]["p"]["const"], "win_ols_F_c_p": win["ols_F_c"]["p"]}
        assert abs(out["boot_wald_c"]["W"] - out["wald_c"]["chi2"]) < 1e-6 * max(1.0, out["wald_c"]["chi2"])
        # which instrument-factor pairs drive beta variation (largest |t|)
        ti = fit["t"][out["interactions"]].abs().sort_values(ascending=False)
        rec["top_interactions"] = "; ".join(f"{i} ({fit['t'][i]:.2f})" for i in ti.index[:3])
        for fk in COND:
            names = [n for n in out["interactions"] if n.startswith(fk + "x")]
            rec[f"wald_c_{fk}_p_F"] = wald(fit, names)["p_F"]
        tag = f"{SHORT.get(key[0], key[0])}|{key[1]}|{period_label(kind, period)}"
        if period == "post2010":
            d2 = ferson_schadt(r, FSF, Z, COND, a, e, dummies=dum)
            f2 = d2["fit"]
            est, se, p = lincom(f2, {"const": 1.0, "D_holdout": 1.0})
            rec.update({"dummy_alpha_base": 12 * f2["b"]["const"], "dummy_alpha_holdout_total": 12 * est, "t_alpha_holdout_total": est / se,
                        "p_alpha_holdout_total": p, "dummy_holdout_shift": 12 * f2["b"]["D_holdout"], "p_holdout_shift": f2["p"]["D_holdout"],
                        "dummy_covid_shift": 12 * f2["b"]["D_covid"], "p_covid_shift": f2["p"]["D_covid"]})
            estc, sec, pc = lincom(f2, {"const": 1.0, "D_covid": 1.0})
            rec.update({"dummy_alpha_covid_total": 12 * estc, "t_alpha_covid_total": estc / sec, "p_alpha_covid_total": pc})
            if kind == "strategy" or key[0] == "GB":
                L.add(f"Q3a.fs_holdout_alpha.{SHORT.get(key[0], key[0])}|{key[1]}", "Q3 conditional alpha (Ferson-Schadt)",
                      "conditional alpha in holdout (a + a_holdout, annualized)", 12 * est, p, f2["n"], "exploratory",
                      "post-2010 FS model (expanding-standardized z) with covid and holdout intercept dummies")
                L.add(f"Q3a.fs_covid_alpha.{SHORT.get(key[0], key[0])}|{key[1]}", "Q3 conditional alpha (Ferson-Schadt)",
                      "conditional alpha in COVID (a + a_covid, annualized)", 12 * estc, pc, f2["n"], "exploratory",
                      "post-2010 FS model (expanding-standardized z) with covid and holdout intercept dummies")
        fs_rows.append(rec)
        L.add(f"Q3a.fs_alpha.{tag}", "Q3 conditional alpha (Ferson-Schadt)", "conditional alpha (annualized)", 12 * fit["b"]["const"],
              fit["p"]["const"], fit["n"], "exploratory", f"FS: {len(COND)} factors x 5 expanding-standardized instruments + SMB; k={fit['k']}")
        L.add(f"Q3a.fs_boot_wald_c.{tag}", "Q3 conditional alpha (Ferson-Schadt)", "HAC Wald chi2: all beta-instrument interactions = 0",
              out["wald_c"]["chi2"], out["boot_wald_c"]["p"], fit["n"], "exploratory",
              f"q={out['wald_c']['q']}; p from fixed-design block bootstrap under H0 ({FS_BOOT} reps, block 12)")
        L.add(f"Q3a.fs_boot_wald_c_wild.{tag}", "Q3 conditional alpha (Ferson-Schadt)", "HAC Wald chi2: all beta-instrument interactions = 0",
              out["wald_c"]["chi2"], out["boot_wald_c_wild"]["p"], fit["n"], "exploratory",
              f"q={out['wald_c']['q']}; p from wild block bootstrap under H0 (Rademacher sign per 12-month block, {FS_BOOT} reps)")
        L.add(f"Q3a.fs_wald_c_asymptotic.{tag}", "Q3 conditional alpha (Ferson-Schadt)", "HAC Wald F: all beta-instrument interactions = 0",
              out["wald_c"]["F"], out["wald_c"]["p_F"], fit["n"], "robustness", "asymptotic F(q, n-k) p; over-rejects with q=20 (see boot p)")
        L.add(f"Q3a.fs_olsF_c.{tag}", "Q3 conditional alpha (Ferson-Schadt)", "classical nested F: all beta-instrument interactions = 0",
              out["ols_F_c"]["F"], out["ols_F_c"]["p"], fit["n"], "robustness", "homoskedastic nested F")
        L.add(f"Q3a.fs_alpha_windowstd.{tag}", "Q3 conditional alpha (Ferson-Schadt)", "conditional alpha, window-standardized z (annualized)",
              12 * win["fit"]["b"]["const"], win["fit"]["p"]["const"], win["fit"]["n"], "robustness", "instruments standardized in-window (ex post)")
FS = pd.DataFrame(fs_rows)
FS.to_csv(TP("ferson_schadt"), index=False)
fst = FS[(FS.baseline.isin(["legs", "corrected"])) & FS.asset.isin(["GB", "Green leg", "Brown leg"] + STRATS) & FS.period.isin(["full_1970", "full_live_1999", "post2010"])]
fst = pd.DataFrame({"Asset": fst.asset.map(lambda a: SHORT.get(a, a)), "Period": fst.period.str.replace("_", " "), "n": fst.n,
                    "a uncond": 100 * fst.alpha_uncond, "t": fst.t_alpha_uncond, "a cond": 100 * fst.alpha_cond, "t ": fst.t_alpha_cond,
                    "Boot Wald p": fst.boot_wald_c_p, "Wild boot p": fst.boot_wald_c_wild_p, "F p (c=0)": fst.ols_F_c_p,
                    "a holdout": 100 * fst.dummy_alpha_holdout_total,
                    "p holdout": fst.p_alpha_holdout_total, "a covid": 100 * fst.dummy_alpha_covid_total, "p covid": fst.p_alpha_covid_total})
to_tex(fst, TX("ferson_schadt"), digits={"Boot Wald p": 3, "Wild boot p": 3, "F p (c=0)": 3, "p holdout": 3, "p covid": 3},
       col_format="llr" + "r" * 11,
       header=["Asset", "Period", "$n$", r"$\alpha$ uncond.", "$t$", r"$\alpha$ cond.", "$t$", "Fixed-design boot $p$", "Wild boot $p$",
               "OLS $F$ $p$", r"$\alpha$ holdout", "$p$", r"$\alpha$ COVID", "$p$"])
# Monte Carlo stability of both bootstrap p-values for the quoted cases (5 seeds x FS_BOOT reps)
seed_rows = []
for key in [("GB", "legs")] + [(s, "corrected") for s in STRATS]:
    for period in (("full", "post2010") if key[0] == "GB" else ("post2010",)):
        a, e = period_bounds(kind_of(key), period)
        for sd in (230, 1230, 2230, 3230, 4230):      # 230 = the main-run seed (wild stream uses seed + 1)
            o = ferson_schadt(ASSETS[key], FSF, Z, COND, a, e, standardize="expanding", boot_reps=FS_BOOT, seed=sd)
            seed_rows.append({"asset": key[0], "baseline": key[1], "period": period_label(kind_of(key), period), "seed": sd,
                              "n": o["fit"]["n"], "W": o["wald_c"]["chi2"], "p_fixed": o["boot_wald_c"]["p"], "p_wild": o["boot_wald_c_wild"]["p"],
                              "q95_fixed": o["boot_wald_c"]["null_q95"], "q95_wild": o["boot_wald_c_wild"]["null_q95"]})
FSS = pd.DataFrame(seed_rows)
FSS.to_csv(TP("fs_boot_seeds"), index=False)
FSS_sum = FSS.groupby(["asset", "baseline", "period"], sort=False).agg(p_fixed_min=("p_fixed", "min"), p_fixed_max=("p_fixed", "max"),
                                                                        p_wild_min=("p_wild", "min"), p_wild_max=("p_wild", "max")).reset_index()
print(FSS_sum.round(3).to_string())
log("Q3a Ferson-Schadt done")
print(FS[["asset", "baseline", "period", "n", "alpha_uncond", "t_alpha_uncond", "alpha_cond", "t_alpha_cond", "wald_c_p_F", "dummy_alpha_holdout_total", "p_alpha_holdout_total", "dummy_alpha_covid_total", "p_alpha_covid_total"]].round(3).to_string())

# =============================================================================================== Q3b Lewellen-Nagel decomposition
fLN = F[LNF]
fLN_eom = F[["Mkt-RF", "SMB", "HML", "UMD", "BOND_eom"]] if "BOND_eom" in F else None
beta_cache = {}


def asset_betas(key, window, mode):
    ck = (key, window, mode)
    if ck not in beta_cache:
        beta_cache[ck] = rolling_betas(ASSETS[key], fLN, window, mode)
    return beta_cache[ck]


# structural betas for strategies: position-scaled (Brown leg rolling beta - hedge beta used)
brown_b36 = rolling_betas(ASSETS[("Brown leg", "legs")], fLN, 36, "backward")


def structural_betas(b, s):
    res = runs[b]
    pos = res["strategies"][s]["position"].shift(1)          # h_{t-1}
    hedge = res["models"]["Brown leg"]["betas"].shift(1)     # beta used for month t
    hb = pd.DataFrame(0.0, index=brown_b36.index, columns=LNF)
    for c in ("Mkt-RF", "SMB", "HML"):
        hb[c] = hedge[c].reindex(brown_b36.index)
    bs = (brown_b36[LNF] - hb).mul(pos.reindex(brown_b36.index), axis=0)
    return bs


ln_rows = []
boot_rows = []
PRIMARY_LN = [("GB", "legs")] + [(s, "corrected") for s in STRATS]
for key in ASSETS:
    kind = kind_of(key)
    specs = [(36, "backward"), (24, "backward"), (36, "centered"), (24, "centered")]
    if kind == "strategy":
        specs.append((36, "structural"))
    if "BOND_eom" in F:
        specs.append((36, "backward_eom"))
    for window, mode in specs:
        fF = fLN_eom if mode == "backward_eom" else fLN
        if mode == "structural":
            betas = structural_betas(key[1], key[0])
        elif mode == "backward_eom":
            betas = rolling_betas(ASSETS[key], fLN_eom, 36, "backward")
        else:
            betas = asset_betas(key, window, mode)
        for period in LN_PERIODS:
            a, e = period_bounds(kind, period)
            if mode == "backward_eom" and period == "full":
                continue
            dcmp = ln_decomposition(ASSETS[key], betas, fF, a, e)
            if dcmp.get("n", 0) < 3:
                continue
            rec = {"asset": key[0], "baseline": key[1], "window": window, "mode": mode, "period": period_label(kind, period), **dcmp}
            if dcmp["n"] >= 24:
                primary = (key in PRIMARY_LN and window == 36 and mode == "backward" and period == "post2010")
                reps = 5000 if (window == 36 and mode in ("backward", "structural", "backward_eom") and period == "post2010") else 1000
                bt = timing_cov_bootstrap(ASSETS[key], betas, fF, a, e, reps=reps)
                rec.update({k: v for k, v in bt.items() if k not in ("n", "timing_cov", "cond_alpha")})
                rec["boot_reps"] = reps
                tag = f"{SHORT.get(key[0], key[0])}|{key[1]}|{window}m-{mode}|{period_label(kind, period)}"
                L.add(f"Q3b.ln_timing.{tag}", "Q3 beta timing (Lewellen-Nagel)", "beta-timing component sum_k cov(beta_k,t, f_k,t) (annualized)",
                      bt["timing_cov"], bt["timing_p_boot"], bt["n"], "primary" if primary else ("robustness" if period == "post2010" else "exploratory"),
                      ("PRIMARY (iii); " if primary else "") + f"circular block bootstrap, block {bt['block']}, {reps} reps; NW t {bt['timing_t_nw']:.2f}")
                L.add(f"Q3b.ln_condalpha.{tag}", "Q3 beta timing (Lewellen-Nagel)", "mean conditional alpha (annualized)", bt["cond_alpha"],
                      bt["alpha_p_boot"], bt["n"], "exploratory", f"circular block bootstrap, {reps} reps")
            ln_rows.append(rec)
LN = pd.DataFrame(ln_rows)
LN.to_csv(TP("ln_decomposition"), index=False)
prim3 = LN[(LN.window == 36) & (LN["mode"] == "backward") & (LN.period == "post2010") &
           LN.apply(lambda r: (r.asset, r.baseline) in PRIMARY_LN, axis=1)].copy()
prim3["holm_p_timing"] = holm(prim3.set_index("asset")["timing_p_boot"]).to_numpy()
prim3.to_csv(TP("primary_iii"), index=False)
# ---- exploratory: attention-specific beta timing. D_t = r_strategy,t - pi * r_AlwaysShortBrown,t with
# pi = mean|position| of the strategy / mean|position| of the benchmark over 2010-01..2026-07 (exposure-matched,
# no-timing benchmark, as in exchange 1 / M8). The LN timing term of D is the part of beta timing due to the signal.
bm_rows = []
A10, E10 = PERIODS["post2010"]
for b in ("team", "corrected"):
    pos_ao = runs[b]["strategies"][BENCH]["position"].shift(1).loc[A10:E10]
    r_ao = ASSETS[(BENCH, b)]
    for s_ in STRATS:
        pos_s = runs[b]["strategies"][s_]["position"].shift(1).loc[A10:E10]
        pi = float(pos_s.abs().mean() / pos_ao.abs().mean())
        D = (ASSETS[(s_, b)] - pi * r_ao).rename("D")
        bD = rolling_betas(D, fLN, 36, "backward")
        for period in ("post2010", "validation", "covid", "holdout"):
            a, e = PERIODS[period]
            dcmp = ln_decomposition(D, bD, fLN, a, e)
            reps = 5000 if period == "post2010" else 1000
            bt = timing_cov_bootstrap(D, bD, fLN, a, e, reps=reps)
            mfit = nw_fit(D.loc[a:e], None)
            rfit = nw_fit(D.loc[a:e], F[LNF])        # in-period FF3+UMD+BOND alpha of D (constant betas within the window)
            bm_rows.append({"baseline": b, "strategy": s_, "short": SHORT[s_], "period": period, "pi": pi,
                            "mean_D_t": mfit["t"]["const"], "mean_D_p": mfit["p"]["const"],
                            "alpha_D_inperiod": 12 * rfit["b"]["const"], "t_alpha_D_inperiod": rfit["t"]["const"],
                            "p_alpha_D_inperiod": rfit["p"]["const"], **dcmp,
                            **{k: v for k, v in bt.items() if k not in ("n", "timing_cov", "cond_alpha")}, "boot_reps": reps})
            L.add(f"Q3b.ln_timing_vs_benchmark.{SHORT[s_]}|{b}|36m-backward|{period}", "Q3 beta timing (Lewellen-Nagel)",
                  "beta-timing component of D = strategy - pi x Always-short Brown (annualized)", bt["timing_cov"], bt["timing_p_boot"],
                  bt["n"], "exploratory", f"pi={pi:.3f}; circular block bootstrap, block {bt['block']}, {reps} reps")
            L.add(f"Q3b.D_mean.{SHORT[s_]}|{b}|{period}", "Q3 beta timing (Lewellen-Nagel)",
                  "mean of D = strategy - pi x Always-short Brown (annualized)", 12 * D.loc[a:e].mean(), mfit["p"]["const"], mfit["n"],
                  "exploratory", f"pi={pi:.3f}; NW(6) t(n-1) p")
            L.add(f"Q3b.D_alpha_inperiod.{SHORT[s_]}|{b}|{period}", "Q3 beta timing (Lewellen-Nagel)",
                  "in-period FF3+UMD+BOND alpha of D (annualized)", 12 * rfit["b"]["const"], rfit["p"]["const"], rfit["n"],
                  "exploratory", f"pi={pi:.3f}; constant betas within the window; NW(6) t(n-k) p; df={rfit['df']}")
BM = pd.DataFrame(bm_rows)
BM.to_csv(TP("ln_vs_benchmark"), index=False)
print(BM[BM.period == "post2010"][["baseline", "short", "pi", "n", "mean_r", "cond_alpha", "static_beta", "timing_cov",
                                   "timing_ci_low", "timing_ci_high", "timing_p_boot"]].round(4).to_string())
lnt = LN[(LN.window == 36) & (LN["mode"] == "backward") & (LN.period == "post2010") & LN.baseline.isin(["legs", "corrected", "team"])]
lnt = pd.DataFrame({"Asset": lnt.asset.map(lambda a: SHORT.get(a, a)), "Baseline": lnt.baseline, "n": lnt.n, "Mean": 100 * lnt.mean_r,
                    "Cond. alpha": 100 * lnt.cond_alpha, "Static beta": 100 * lnt.static_beta, "Timing cov": 100 * lnt.timing_cov,
                    "CI low": 100 * lnt.timing_ci_low, "CI high": 100 * lnt.timing_ci_high, "p boot": lnt.timing_p_boot})
to_tex(lnt, TX("ln_post2010"), digits={"p boot": 3}, col_format="llr" + "r" * 7,
       header=["Asset", "Baseline", "$n$", "Mean", r"Cond.\ $\alpha$", r"Static $\bar\beta'\bar f$", "Timing cov", "95\\% low", "95\\% high", "$p$"])
log("Q3b Lewellen-Nagel done")
print(prim3[["asset", "baseline", "n", "mean_r", "cond_alpha", "static_beta", "timing_cov", "timing_ci_low", "timing_ci_high", "timing_p_boot", "timing_t_nw", "holm_p_timing"]].round(4).to_string())

# =============================================================================================== Q4 timing tests
tm_rows = []
ctrl = ["Mkt-RF", "SMB", "HML", "UMD", "BOND"]
for key, r in ASSETS.items():
    kind = kind_of(key)
    if key[0] in ("Green leg", "Brown leg", HEDGED):
        continue
    for period in ("full", "post2010", "validation", "holdout", "pre_covid", "post2010_ex_covid"):
        if period == "post2010_ex_covid":
            a, e = PERIODS["post2010"]
            y = r.loc[a:e]
            y = y[(y.index < PERIODS["covid"][0]) | (y.index > PERIODS["covid"][1])]
        else:
            a, e = period_bounds(kind, period)
            y = r.loc[a:e]
        for fac in ("Mkt-RF", "HML", "BOND"):
            for kindt in ("TM", "HM"):
                for spec, cc in (("multifactor", ctrl), ("single", [])):
                    out = timing_test(y, F, fac, kindt, cc)
                    tm_rows.append({"asset": key[0], "baseline": key[1], "period": period_label(kind, period), "factor": fac, "test": kindt,
                                    "spec": spec, **out})
                    L.add(f"Q4.{kindt}.{fac}.{spec}.{SHORT.get(key[0], key[0])}|{key[1]}|{period_label(kind, period)}", "Q4 timing tests",
                          f"{kindt} timing coefficient on {fac}", out["gamma"], out["p_gamma"], out["n"], "exploratory",
                          f"{spec}; NW(6) t(n-k) p")
TM = pd.DataFrame(tm_rows)
TM.to_csv(TP("timing_tests"), index=False)
from common import bh  # noqa: E402
tsum = []
for (spec, fac, kindt), g in TM.groupby(["spec", "factor", "test"]):
    tsum.append({"spec": spec, "factor": fac, "test": kindt, "n_tests": len(g), "n_p_below_05": int((g.p_gamma < 0.05).sum()),
                 "n_positive_sig": int(((g.p_gamma < 0.05) & (g.gamma > 0)).sum()),
                 "n_negative_sig": int(((g.p_gamma < 0.05) & (g.gamma < 0)).sum()),
                 "n_bh_q05": int((bh(g.p_gamma) < 0.05).sum())})
tsum.append({"spec": "all", "factor": "all", "test": "all", "n_tests": len(TM), "n_p_below_05": int((TM.p_gamma < 0.05).sum()),
             "n_positive_sig": int(((TM.p_gamma < 0.05) & (TM.gamma > 0)).sum()),
             "n_negative_sig": int(((TM.p_gamma < 0.05) & (TM.gamma < 0)).sum()), "n_bh_q05": int((bh(TM.p_gamma) < 0.05).sum())})
TSUM = pd.DataFrame(tsum)
TSUM.to_csv(TP("timing_tests_summary"), index=False)
print(TSUM.to_string())
tmt = TM[(TM.spec == "multifactor") & TM.baseline.isin(["legs", "corrected"]) & TM.period.isin(["post2010"])]
tmt = tmt.pivot_table(index=["asset"], columns=["factor", "test"], values="t_gamma", sort=False)
tmt.columns = [f"{f} {t}" for f, t in tmt.columns]
tmt = tmt.reset_index(); tmt["asset"] = tmt["asset"].map(lambda a: SHORT.get(a, a))
to_tex(tmt, TX("timing_tests"), col_format="l" + "r" * (len(tmt.columns) - 1))
log(f"Q4 timing done: {len(TM)} tests; share |t|>1.96 = {(TM.t_gamma.abs() > 1.96).mean():.3f}")

# =============================================================================================== Q5 attribution
KEY_STRATS = ["Pure | Short Brown hold 6m", "Continuous | pure attention"]
brown = ASSETS[("Brown leg", "legs")]


def clamped_centered_betas(y, Fm, window):
    """Centered window (t-w/2+1..t+w/2) clamped to the sample so the edges use the nearest full window."""
    d = pd.concat([y.rename("__y"), Fm], axis=1, sort=True).dropna()
    Y, X = d["__y"].to_numpy(), d[Fm.columns].to_numpy()
    n = len(d)
    B = np.full((n, X.shape[1]), np.nan)
    for t in range(n):
        lo = min(max(t - window // 2 + 1, 0), n - window)
        coef, *_ = np.linalg.lstsq(np.column_stack([np.ones(window), X[lo:lo + window]]), Y[lo:lo + window], rcond=None)
        B[t] = coef[1:]
    return pd.DataFrame(B, index=d.index, columns=Fm.columns)


att_rows, att_monthly = [], {}
brown_c = {w: clamped_centered_betas(brown, fLN, w) for w in (36, 24)}
for b in ("team", "corrected"):
    for s in KEY_STRATS:
        st = runs[b]["strategies"][s]
        h = st["position"].shift(1)
        hedge = runs[b]["models"]["Brown leg"]["betas"].shift(1)
        for w in (36, 24):
            bc = brown_c[w]
            idx = st.index.intersection(bc.index)
            comp = pd.DataFrame(index=idx)
            for c in LNF:
                hb = hedge[c].reindex(idx) if c in ("Mkt-RF", "SMB", "HML") else 0.0
                comp[f"leak_{c}"] = h.reindex(idx) * (bc[c].reindex(idx) - hb) * F[c].reindex(idx)
            comp["leak_total"] = comp[[f"leak_{c}" for c in LNF]].sum(axis=1)
            comp["gross"] = st["gross_return"].reindex(idx)
            comp["residual"] = comp["gross"] - comp["leak_total"]
            comp["cost"] = -st["cost"].reindex(idx)
            comp["net"] = st["net_return"].reindex(idx)
            att_monthly[(b, s, w)] = comp
            for period in ["post2010", "validation", "pre_covid", "covid", "inflation_rates", "holdout", "last18", "last12"]:
                a, e = PERIODS[period]
                cc = comp.loc[a:e]
                rec = {"baseline": b, "strategy": s, "short": SHORT[s], "method": f"structural centered {w}m", "period": period, "n": len(cc)}
                for col in comp.columns:
                    rec[col] = 12 * cc[col].mean()
                # significance of the residual and the leakage (NW mean tests)
                for col in ("residual", "leak_total"):
                    ft = nw_fit(cc[col], None)
                    rec[f"t_{col}"] = ft["t"]["const"]; rec[f"p_{col}"] = ft["p"]["const"]
                att_rows.append(rec)
                if w == 36:
                    L.add(f"Q5.attr_residual.{SHORT[s]}|{b}|{period}", "Q5 attribution", "residual (non-factor) return, annualized",
                          rec["residual"], rec["p_residual"], len(cc), "exploratory", "structural centered 36m Brown betas; NW(6) mean test")
                    L.add(f"Q5.attr_leak.{SHORT[s]}|{b}|{period}", "Q5 attribution", "factor leakage (hedging error), annualized",
                          rec["leak_total"], rec["p_leak_total"], len(cc), "exploratory", "structural centered 36m Brown betas; NW(6) mean test")
                else:
                    L.add(f"Q5.attr_residual_{w}m.{SHORT[s]}|{b}|{period}", "Q5 attribution", "residual (non-factor) return, annualized",
                          rec["residual"], rec["p_residual"], len(cc), "robustness", f"structural centered {w}m Brown betas; NW(6) mean test")
                    L.add(f"Q5.attr_leak_{w}m.{SHORT[s]}|{b}|{period}", "Q5 attribution", "factor leakage (hedging error), annualized",
                          rec["leak_total"], rec["p_leak_total"], len(cc), "robustness", f"structural centered {w}m Brown betas; NW(6) mean test")
        # regression-based attribution within each period (in-period FF3+UMD+BOND loadings)
        for period in ["post2010", "validation", "pre_covid", "covid", "inflation_rates", "holdout", "last18", "last12"]:
            a, e = PERIODS[period]
            y = st["net_return"].loc[a:e]
            fit = nw_fit(y, F[LNF])
            fm = F[LNF].loc[a:e].mean()
            rec = {"baseline": b, "strategy": s, "short": SHORT[s], "method": "in-period regression FF3+UMD+BOND", "period": period,
                   "n": fit["n"], "net": 12 * y.mean(), "residual": 12 * fit["b"]["const"], "p_residual": fit["p"]["const"],
                   "t_residual": fit["t"]["const"]}
            for c in LNF:
                rec[f"leak_{c}"] = 12 * fit["b"][c] * fm[c]
            rec["leak_total"] = sum(rec[f"leak_{c}"] for c in LNF)
            att_rows.append(rec)
            # same regression as the Q1 row Q1.alpha.<strategy>|<baseline>|FF3+UMD+BOND|<period>; log only where Q1 has no window
            if period not in Q1_PERIODS:
                L.add(f"Q5.attr_residual_regression.{SHORT[s]}|{b}|{period}", "Q5 attribution",
                      "residual = in-period FF3+UMD+BOND alpha of the net return, annualized", rec["residual"], rec["p_residual"], fit["n"],
                      "robustness", f"in-period regression attribution; NW(6) t(n-k) p; df={fit['df']}")
            else:
                assert np.isclose(rec["residual"], Q1[(Q1.asset == s) & (Q1.baseline == b) & (Q1.model == "FF3+UMD+BOND") &
                                                      (Q1.period == period)]["alpha_ann"].iloc[0])
# position overlap with Always-short Brown (position earning month t = position set at t-1)
ov_rows = []
for b in ("team", "corrected"):
    ao = runs[b]["strategies"][BENCH]["position"].shift(1)
    for s_ in STRATS:
        hh = runs[b]["strategies"][s_]["position"].shift(1)
        for per in ("post2010", "validation", "covid", "inflation_rates", "holdout", "last18", "last12"):
            a, e = PERIODS[per]
            h_, ao_ = hh.loc[a:e], ao.loc[a:e]
            ov_rows.append({"baseline": b, "strategy": s_, "short": SHORT[s_], "period": per, "n": len(h_),
                            "months_in_position": int((h_ != 0).sum()), "months_equal_to_always_short": int(np.isclose(h_, ao_).sum()),
                            "mean_abs_pos": h_.abs().mean(), "mean_abs_pos_always_short": ao_.abs().mean(),
                            "ratio_mean_abs_pos": h_.abs().mean() / ao_.abs().mean(),
                            "net_ann": 12 * ASSETS[(s_, b)].loc[a:e].mean(), "always_short_net_ann": 12 * ASSETS[(BENCH, b)].loc[a:e].mean()})
OV = pd.DataFrame(ov_rows)
OV.to_csv(TP("position_overlap"), index=False)
ATT = pd.DataFrame(att_rows)
ATT.to_csv(TP("attribution"), index=False)
pd.concat({f"{b}|{SHORT[s]}|{w}m": v for (b, s, w), v in att_monthly.items()}, names=["series", "date"]).to_csv(TP("attribution_monthly"))
at = ATT[(ATT.method == "structural centered 36m")]
at = pd.DataFrame({"Baseline": at.baseline, "Strategy": at.short, "Period": at.period, "Net": 100 * at.net,
                   "Leak Mkt": 100 * at["leak_Mkt-RF"], "Leak SMB": 100 * at.leak_SMB, "Leak HML": 100 * at.leak_HML,
                   "Leak UMD": 100 * at.leak_UMD, "Leak BOND": 100 * at.leak_BOND, "Residual": 100 * at.residual,
                   "t resid": at.t_residual, "Cost": 100 * at.cost})
to_tex(at, TX("attribution"), col_format="lll" + "r" * 9)
log("Q5 attribution done")
print(ATT[ATT.method == "structural centered 36m"][["baseline", "short", "period", "n", "net", "leak_Mkt-RF", "leak_SMB", "leak_HML", "leak_UMD", "leak_BOND", "residual", "t_residual", "cost"]].round(4).to_string())

# =============================================================================================== figures
# F1 rolling 60m BOND and HML betas of GB (FF3+UMD+BOND)
def rolling_with_se(y, Fm, window=60):
    d = pd.concat([y.rename("__y"), Fm], axis=1, sort=True).dropna()
    Y, X = d["__y"].to_numpy(), np.column_stack([np.ones(len(d)), d[Fm.columns].to_numpy()])
    n, k = X.shape
    B = np.full((n, k), np.nan); S = np.full((n, k), np.nan)
    for t in range(window - 1, n):
        xx, yy = X[t - window + 1:t + 1], Y[t - window + 1:t + 1]
        inv = np.linalg.pinv(xx.T @ xx); b = inv @ xx.T @ yy; u = yy - xx @ b
        xu = xx * u[:, None]; meat = xu.T @ xu
        for lag in range(1, 7):
            g = xu[lag:].T @ xu[:-lag]; meat += (1 - lag / 7) * (g + g.T)
        B[t] = b; S[t] = np.sqrt(np.clip(np.diag(inv @ meat @ inv), 0, None))
    cols = ["const"] + list(Fm.columns)
    return pd.DataFrame(B, d.index, cols), pd.DataFrame(S, d.index, cols)


gbB, gbS = rolling_with_se(ASSETS[("GB", "legs")].loc["1965":END], F[LNF].loc["1965":END], 60)
roll = pd.concat([gbB.add_prefix("b_"), gbS.add_prefix("se_")], axis=1).dropna(how="all")
roll.to_csv(TP("gb_rolling60_betas"))
fig, axes = plt.subplots(2, 1, figsize=(7.0, 5.2), sharex=True)
for ax, fct, title in ((axes[0], "BOND", "Rolling 60-month BOND beta of Green-minus-Brown"),
                       (axes[1], "HML", "Rolling 60-month HML beta of Green-minus-Brown")):
    b_, s_ = roll[f"b_{fct}"], roll[f"se_{fct}"]
    ax.fill_between(b_.index, b_ - 1.96 * s_, b_ + 1.96 * s_, color=ps.ENTITY["green_minus_brown"], alpha=0.15, lw=0, label="95% band (NW 6)")
    ax.plot(b_.index, b_, color=ps.ENTITY["green_minus_brown"], label="GB beta (FF3+UMD+BOND model)")
    ax.axhline(0, color=ps.INK2, lw=0.8)
    ax.axvspan(pd.Timestamp(H0), pd.Timestamp(END), color=ps.MUTED, alpha=0.15, lw=0, label="Holdout (window end)")
    ax.set_title(title, loc="left"); ax.set_ylabel("Beta")
h_, l_ = axes[0].get_legend_handles_labels()
fig.legend(h_, l_, loc="outside lower center", ncol=3)
axes[1].set_xlabel("End of 60-month window")
ps.savefig(fig, f"{MOD}_rolling_betas")

# F2 holdout alpha before and after BOND
fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.9), sharey=True)
mcol = {"FF3": ps.MUTED, "FF3+BOND": ps.BLUE, "FF3+UMD+BOND": ps.VIOLET}
for ax, b in zip(axes, ("team", "corrected")):
    q = Q2[(Q2.baseline == b) & Q2.strategy.isin(STRATS)].reset_index(drop=True)
    ypos = np.arange(len(q))
    for j, mname in enumerate(mcol):
        off = (j - 1) * 0.22
        crit = stats.t.ppf(0.975, q[f"df_{mname}"])
        ax.errorbar(100 * q[f"alpha_{mname}"], ypos + off, xerr=100 * crit * q[f"se_{mname}"], fmt="o", ms=4,
                    color=mcol[mname], ecolor=mcol[mname], elinewidth=1.2, capsize=2, label=mname)
    ax.axvline(0, color=ps.INK2, lw=0.8)
    ax.set_yticks(ypos, q["short"])
    ax.set_title(f"{b.capitalize()} baseline", loc="left"); ax.set_xlabel("Holdout alpha, % per year (95% CI, t(n-k))")
    ax.grid(axis="y", visible=False)
axes[0].invert_yaxis()                      # shared y: invert once
h_, l_ = axes[0].get_legend_handles_labels()
fig.legend(h_, l_, loc="outside lower center", ncol=3, title="Factor model", title_fontsize=8)
ps.savefig(fig, f"{MOD}_holdout_alpha_bond")

# F3 Lewellen-Nagel decomposition by period (backward 36m)
comp_cols = [("cond_alpha", "Conditional alpha", ps.BLUE), ("static_beta", "Average beta x average factor", ps.MUTED),
             ("timing_cov", "Beta-timing covariance", ps.VIOLET)]
panels = [("GB", "legs", "Green-minus-Brown"), ("Pure | Short Brown hold 6m", "corrected", "Pure Short Brown 6m (corrected)"),
          ("Continuous | pure attention", "corrected", "Continuous pure (corrected)"),
          (BENCH, "corrected", "Always-short Brown (no timing; identical in both baselines)")]
per_show = ["post2010", "validation", "pre_covid", "covid", "inflation_rates", "holdout", "last18"]
fig, axes = plt.subplots(4, 1, figsize=(7.0, 9.2), sharex=True)
for ax, (asset, b, title) in zip(axes, panels):
    q = LN[(LN.asset == asset) & (LN.baseline == b) & (LN.window == 36) & (LN["mode"] == "backward")].set_index("period").reindex(per_show)
    xpos = np.arange(len(per_show))
    for j, (c, lab, colr) in enumerate(comp_cols):
        ax.bar(xpos + (j - 1) * 0.26, 100 * q[c], width=0.24, color=colr, label=lab, edgecolor=ps.SURFACE, linewidth=0.8)
    ax.plot(xpos, 100 * q["mean_r"], "D", color=ps.INK, ms=4, label="Mean return")
    ax.axhline(0, color=ps.INK2, lw=0.8)
    ax.set_title(title, loc="left"); ax.set_ylabel("% per year")
h_, l_ = axes[0].get_legend_handles_labels()
fig.legend(h_, l_, loc="outside lower center", ncol=4)
axes[-1].set_xticks(np.arange(len(per_show)), [p.replace("_", " ") for p in per_show])
ps.savefig(fig, f"{MOD}_decomposition")

# F4 attribution of Pure 6m and Continuous pure (corrected), structural centered 36m
leak_parts = [("leak_Mkt-RF", "Market leakage", ps.MUTED), ("leak_SMB", "SMB leakage", ps.YELLOW), ("leak_HML", "HML leakage", ps.AQUA),
              ("leak_UMD", "UMD leakage", ps.MAGENTA), ("leak_BOND", "BOND leakage", ps.VIOLET), ("residual", "Residual (non-factor)", ps.BLUE),
              ("cost", "Trading cost", ps.RED)]
fig, axes = plt.subplots(2, 1, figsize=(7.0, 6.3), sharex=True)
for ax, s in zip(axes, KEY_STRATS):
    q = ATT[(ATT.baseline == "corrected") & (ATT.strategy == s) & (ATT.method == "structural centered 36m")].set_index("period").reindex(per_show + ["last12"])
    xpos = np.arange(len(q))
    pos_b = np.zeros(len(q)); neg_b = np.zeros(len(q))
    for c, lab, colr in leak_parts:
        v = 100 * q[c].to_numpy()
        base = np.where(v >= 0, pos_b, neg_b)
        ax.bar(xpos, v, bottom=base, width=0.6, color=colr, label=lab, edgecolor=ps.SURFACE, linewidth=0.8)
        pos_b += np.where(v >= 0, v, 0); neg_b += np.where(v < 0, v, 0)
    ax.plot(xpos, 100 * q["net"], "D", color=ps.INK, ms=4, label="Net return")
    ax.axhline(0, color=ps.INK2, lw=0.8)
    ax.set_title(f"{SHORT[s]} (corrected baseline)", loc="left"); ax.set_ylabel("% per year")
h_, l_ = axes[0].get_legend_handles_labels()
fig.legend(h_, l_, loc="outside lower center", ncol=4)
axes[-1].set_xticks(np.arange(len(per_show) + 1), [p.replace("_", " ") for p in per_show + ["last12"]])
ps.savefig(fig, f"{MOD}_attribution")

# F5 BOND validation: annual total return, ours vs Damodaran
fig, ax = plt.subplots(figsize=(7.0, 3.4))
ax.bar(ann.index, 100 * ann["bond_total"], color=ps.BLUE, width=0.8, label="BOND total return (GS10, duration + convexity)")
if dam is not None:
    ax.plot(ann.index, 100 * ann["damodaran_tbond"], "o", ms=3, color=ps.INK2, label="Damodaran 10y T-bond (year-end yields)")
if "bond_eom_total" in ann:
    ax.plot(ann.index, 100 * ann["bond_eom_total"], "s", ms=3, color=ps.MAGENTA, label="Same construction, month-end Treasury yields (1991+)")
ax.axhline(0, color=ps.INK2, lw=0.8)
ax.annotate(f"2022: {100 * ann.loc[2022, 'bond_total']:.1f}%", xy=(2022, 100 * ann.loc[2022, "bond_total"]), xytext=(1995, -16),
            fontsize=8, color=ps.INK, arrowprops=dict(arrowstyle="-", color=ps.INK2, lw=0.8))
ax.set_ylabel("Calendar-year return, %"); ax.set_title("Constructed 10-year Treasury return vs an external series", loc="left")
fig.legend(loc="outside lower center", ncol=2)
ps.savefig(fig, f"{MOD}_bond_validation")
log("figures done")

# =============================================================================================== ledger
led = L.frame()
holm_map = {}
for r in prim1.itertuples():
    holm_map[f"Q1.bond.GB|legs|FF5+UMD+BOND|{r.period}"] = r.holm_p_BOND
for r in Q2[Q2.strategy.isin(STRATS)].itertuples():
    holm_map[f"Q2.holdout_alpha_FF3UMDBOND.{r.short}|{r.baseline}"] = Q2.loc[r.Index, "holm_p_alpha_FF3+UMD+BOND"]
    holm_map[f"Q2.holdout_wald_UMD_BOND.{r.short}|{r.baseline}"] = Q2.loc[r.Index, "holm_p_wald"]
for r in prim3.itertuples():
    holm_map[f"Q3b.ln_timing.{SHORT.get(r.asset, r.asset)}|{r.baseline}|36m-backward|post2010"] = r.holm_p_timing
for tid, hp in holm_map.items():
    m = led.test_id == tid
    assert m.sum() == 1, tid
    led.loc[m, "note"] = led.loc[m, "note"] + f"; Holm-adjusted p within family = {hp:.4f}"
led.to_csv(TP("tests_ledger"), index=False)

# ---- key numbers (every number quoted in the findings, with its source table)
K = []
def kn(key, value, source, locator):
    K.append({"key": key, "value": value, "source_table": f"{MOD}_{source}.csv", "locator": locator})
for k_, v_ in summ.items():
    kn(f"bond.{k_}", v_, "bond_validation_summary", k_)
for per_, (a_, e_) in {"holdout": PERIODS["holdout"], "inflation_rates": PERIODS["inflation_rates"], "post2010": PERIODS["post2010"]}.items():
    kn(f"bond.mean_excess_ann.{per_}", 12 * F["BOND"].loc[a_:e_].mean(), "bond_monthly", f"12 x mean(BOND) {a_}..{e_}")
    if "BOND_eom" in F:
        kn(f"bond_eom.mean_excess_ann.{per_}", 12 * F["BOND_eom"].loc[a_:e_].mean(), "bond_monthly", f"12 x mean(BOND_eom) {a_}..{e_}")
for r in prim1.itertuples():
    kn(f"primary_i.GB.bond.{r.period}", r.b_BOND, "primary_i", f"period={r.period}, b_BOND")
    kn(f"primary_i.GB.t_bond.{r.period}", r.t_BOND, "primary_i", f"period={r.period}, t_BOND")
    kn(f"primary_i.GB.p_bond.{r.period}", r.p_BOND, "primary_i", f"period={r.period}, p_BOND")
    kn(f"primary_i.GB.holm_p.{r.period}", r.holm_p_BOND, "primary_i", f"period={r.period}, holm_p_BOND")
for _, r in legtab.iterrows():
    for c_ in ("alpha (%/yr)", "t(alpha)", "HML", "BOND", "t(BOND)"):
        kn(f"legs.{r['Asset']}.{r['Period']}.{c_}", r[c_], "leg_exposures", f"Asset={r['Asset']}, Period={r['Period']}, {c_}")
for r in Q2.itertuples():
    for c_ in ("ann_net", "alpha_FF3", "t_FF3", "p_FF3", "alpha_FF3+UMD+BOND", "t_FF3+UMD+BOND", "p_FF3+UMD+BOND", "bBOND_FF3+UMD+BOND",
               "tBOND_FF3+UMD+BOND", "wald_UMD_BOND_p", "holm_p_alpha_FF3+UMD+BOND"):
        kn(f"primary_ii.{r.baseline}.{r.short}.{c_}", Q2.loc[r.Index, c_], "holdout_alpha", f"baseline={r.baseline}, short={r.short}, {c_}")
for r in prim3.itertuples():
    for c_ in ("mean_r", "cond_alpha", "static_beta", "timing_cov", "timing_ci_low", "timing_ci_high", "timing_p_boot", "timing_t_nw",
               "holm_p_timing", "alpha_p_boot"):
        kn(f"primary_iii.{SHORT.get(r.asset, r.asset)}.{c_}", getattr(r, c_), "primary_iii", f"asset={r.asset}, {c_}")
for fct in ("BOND", "HML"):
    rb = roll[f"b_{fct}"].dropna()
    for lab, sl in (("1970_2009", slice("1970", "2009")), ("2010_2021", slice("2010", "2021")), ("2022_2026", slice("2022", END))):
        x_ = rb.loc[sl]
        kn(f"gb_rolling60.{fct}.{lab}.mean", x_.mean(), "gb_rolling60_betas", f"mean of b_{fct} for window ends {lab}")
        kn(f"gb_rolling60.{fct}.{lab}.min", x_.min(), "gb_rolling60_betas", f"min b_{fct} ({x_.idxmin():%Y-%m})")
        kn(f"gb_rolling60.{fct}.{lab}.max", x_.max(), "gb_rolling60_betas", f"max b_{fct} ({x_.idxmax():%Y-%m})")
for r in FC.itertuples():
    kn(f"factcheck.{SHORT.get(r.asset, r.asset)}.{r.baseline}.{r.period}.{r.spec}.b_rate", r.b_rate, "factcheck_rates",
       f"asset={r.asset}, baseline={r.baseline}, period={r.period}, spec={r.spec}, b_rate")
    kn(f"factcheck.{SHORT.get(r.asset, r.asset)}.{r.baseline}.{r.period}.{r.spec}.t_rate", r.t_rate, "factcheck_rates", "t_rate")
    kn(f"factcheck.{SHORT.get(r.asset, r.asset)}.{r.baseline}.{r.period}.{r.spec}.alpha_ann", r.alpha_ann, "factcheck_rates", "alpha_ann")
    kn(f"factcheck.{SHORT.get(r.asset, r.asset)}.{r.baseline}.{r.period}.{r.spec}.t_alpha", r.t_alpha, "factcheck_rates", "t_alpha")
for r in BM[BM.period == "post2010"].itertuples():
    for c_ in ("pi", "mean_r", "cond_alpha", "static_beta", "timing_cov", "timing_ci_low", "timing_ci_high", "timing_p_boot"):
        kn(f"ln_vs_benchmark.{r.baseline}.{r.short}.{c_}", getattr(r, c_), "ln_vs_benchmark", f"baseline={r.baseline}, short={r.short}, period=post2010, {c_}")
for r in FS.itertuples():
    for c_ in ("alpha_uncond", "t_alpha_uncond", "alpha_cond", "t_alpha_cond", "p_alpha_cond", "boot_wald_c_p", "boot_wald_c_wild_p",
               "ols_F_c_p", "wald_c_p_F"):
        kn(f"fs.{SHORT.get(r.asset, r.asset)}.{r.baseline}.{r.period}.{c_}", getattr(r, c_), "ferson_schadt", f"asset={r.asset}, baseline={r.baseline}, period={r.period}, {c_}")
for r in FSS_sum.itertuples():
    for c_ in ("p_fixed_min", "p_fixed_max", "p_wild_min", "p_wild_max"):
        kn(f"fs_seeds.{SHORT.get(r.asset, r.asset)}.{r.baseline}.{r.period}.{c_}", getattr(r, c_), "fs_boot_seeds",
           f"asset={r.asset}, baseline={r.baseline}, period={r.period}; {c_} over 5 seeds")
# factor means by period (annualized), for the contribution arithmetic quoted in the findings
fm_rows = []
for per_ in ("post2010", "validation", "pre_covid", "covid", "inflation_rates", "holdout", "last18", "last12"):
    a_, e_ = PERIODS[per_]
    for c_ in LNF:
        fm_ = nw_fit(F[c_].loc[a_:e_], None)
        fm_rows.append({"factor": c_, "period": per_, "n": fm_["n"], "mean_ann": 12 * F[c_].loc[a_:e_].mean(), "t_mean": fm_["t"]["const"]})
        kn(f"factor_mean_ann.{c_}.{per_}", 12 * F[c_].loc[a_:e_].mean(), "factor_means", f"factor={c_}, period={per_}, mean_ann")
pd.DataFrame(fm_rows).to_csv(TP("factor_means"), index=False)
# GB short-window alphas (Section 5 / fix 1)
for r in Q1[(Q1.asset == "GB") & Q1.period.isin(["last18", "last12", "holdout", "post2010", "full_1970"])].itertuples():
    for c_ in ("mean_ann", "alpha_ann", "t_alpha", "p_alpha", "df"):
        kn(f"exposures.GB.{r.period}.{r.model}.{c_}", getattr(r, c_), "exposures", f"asset=GB, period={r.period}, model={r.model}, {c_}")
for r in SW.itertuples():
    for c_ in ("alpha_ann", "t_nw6", "p_nw6", "t_nw2", "p_nw2", "t_ols", "p_ols"):
        kn(f"gb_short_window.{r.period}.{r.model}.{c_}", getattr(r, c_), "gb_short_window_alpha", f"period={r.period}, model={r.model}, {c_}")
for r in Q2.itertuples():
    for c_ in ("contrib_BOND_FF3+UMD+BOND", "contrib_UMD_FF3+UMD+BOND"):
        kn(f"primary_ii.{r.baseline}.{r.short}.{c_}", Q2.loc[r.Index, c_], "holdout_alpha", f"baseline={r.baseline}, short={r.short}, {c_}")
for r in ATT[ATT.period.isin(["covid", "holdout"])].itertuples():
    for c_ in ("net", "leak_Mkt-RF", "leak_SMB", "leak_HML", "leak_UMD", "leak_BOND", "leak_total", "residual", "t_residual", "p_residual",
               "p_leak_total", "cost"):
        if c_ in ATT.columns:
            kn(f"attribution.{r.baseline}.{r.short}.{r.method}.{r.period}.{c_}", ATT.loc[r.Index, c_], "attribution",
               f"baseline={r.baseline}, short={r.short}, method={r.method}, period={r.period}, {c_}")
for r in BM[BM.period.isin(["covid", "holdout"])].itertuples():
    for c_ in ("mean_r", "mean_D_t", "mean_D_p", "alpha_D_inperiod", "t_alpha_D_inperiod", "p_alpha_D_inperiod"):
        kn(f"ln_vs_benchmark.{r.baseline}.{r.short}.{r.period}.{c_}", getattr(r, c_), "ln_vs_benchmark",
           f"baseline={r.baseline}, short={r.short}, period={r.period}, {c_}")
pd.DataFrame(K).to_csv(TP("key_numbers"), index=False)
log(f"key numbers: {len(K)}")
log(f"ledger: {len(led)} tests ({(led.primary_or_exploratory == 'primary').sum()} primary)")
print(led[led.primary_or_exploratory == "primary"][["test_id", "statistic", "p_value_two_sided", "n_obs"]].to_string())
