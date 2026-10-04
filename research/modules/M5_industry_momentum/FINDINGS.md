<!-- Saved by the orchestrator from the builder's returned text (subagent report writes are blocked by the harness). Source agent a665426fc68563025. -->
# M5 Industry momentum, made carbon-aware

All tables are in outputs/tables/M5_industry_momentum_<name>.csv, cited below by <name> only. Percentages are annualized unless stated. t-statistics are Newey-West with 6 lags (NW6) unless stated. This version incorporates the independent verification (modules/M5_industry_momentum/verify/); the changes are listed in section 12.

## 1. Question
Is there a defensible active strategy in the team's data, and what does a carbon constraint cost it? The candidate is FF49 industry momentum (Moskowitz and Grinblatt 1999; the brief cites Zarattini and Antonacci 2024), made carbon-aware with the team's emissions-intensity file.

## 2. Pre-registered specification and primary tests (fixed before any result was computed)

Primary strategy (Q1):
- Signal: cumulative return over months t-11 to t-1, measured at the formation month-end t. This skips month t. In holding-month notation (holding month t+1) it is the usual "t-12 to t-2" window of 11 monthly returns.
- Portfolio: each month, rank all value-weighted FF49 industries in the team file (data/ff49_industry_monthly.csv, through 2026-07) that have a complete window. Go long the top 8 and short the bottom 8, equal weights inside each leg (+1 long, -1 short), rebalanced monthly.
- Sample: returns 1970-01 to 2026-07 (679 months).
- Costs: 10 bp per unit of one-way traded notional.
- Primary tests: FF5+UMD alpha (NW6) of the net returns over the full sample (P1) and post-2010 (P2).

Q3 primary test (pre-specified before the frontier was run): the Grinold-Kahn optimizer on the 41 covered industries (convention X). The statistic is the realized net information ratio (IR) of the book with the carbon-neutral bound b = 0 minus that of the unconstrained book, full sample. It is tested with a paired circular block bootstrap (block 12, 5,000 draws, p-value from the re-centred distribution). The FF5+UMD alpha difference is reported alongside. (Section 7 explains why this bound turned out to be a weak test.)

Q4 primary test: NW6 t-statistic on the industry-momentum return (INDMOM; primary book, gross) in a regression of the team's green-minus-brown spread (GB) on FF3 + INDMOM, 1970-01 to 2026-07.

Everything else is labelled exploratory or robustness. The tests ledger (tests_ledger) has 416 rows: 4 primary and 412 exploratory, of which 30 are descriptive factor loadings (tagged "[loading]" in the note); 10 of these are logged for completeness but not cited here (GB's holdout HML loadings, the brown_eps HML loadings, and the attention-lag strategies' HML loadings with INDMOM or UMD added). multiple_testing gives Holm-adjusted p-values within the 4 primaries and Benjamini-Hochberg (BH) p-values within the exploratory tests, with and without the loading rows; multiple_testing_summary has the counts.

## 3. Data
- Industry returns: team file, FF49 value-weighted returns in decimals, 1926-07 to 2026-07.
- Ken French Aug-2026 vintage (robustness row only). It differs from the team file materially only in 2026-07 (kf_vintage_diff, kf_vintage_diff_last_month). In all, 113 cells in 54 months differ, all from 2020-07 on. Outside 2026-07 the revisions are at most 0.22 percentage points (pp). In 2026-07, 26 industries differ by up to 7.02 pp (PerSv); PerSv, Clths and BusSv, the three that move by more than 1 pp, are all in that month's short leg. The ranking, and therefore every monthly weight, is identical under both files. 2026-07 net is -13.95% under KF against -14.18%, still the 6th-worst month.
- Industry size: Ken French number of firms times average firm size, same vintage. Used for the cap-weighted legs and the market carbon benchmark.
- Factors: Ken French FF3 (used for CAPM and FF3) and FF5 + UMD (used for FF5 and FF5+UMD), Aug-2026 vintage.
- Emissions: team emissions_ff_industry.csv, one static cross-section covering 41 of 49 industries. Uncovered: Chips, FabPr, Gold, Hshld, LabEq, Oil, Other, Toys. Median intensity 0.0610 in team units.
- Team baseline (Q4 only): re-implemented from notebooks/climate_alpha_analysis.py, not executed. It matches the team's comparison_table.csv (team_replica_check): Short-Brown hold 3m, 2010-01 to 2026-07, net return 0.000696 a year, volatility 0.03255 (hold 6m: 0.013436 and 0.04243).
- Eligibility: Hlth starts in 1969-07, so the ranking universe is 48 industries for the first 6 formation months and 49 after that (returns_monthly, column n_eligible).

## 4. Method

Real-time convention (lag convention): a position formed at the end of month t uses only data known at the end of month t and earns the month t+1 return.
- Momentum windows end at t (or t-1 with the skip). Industry caps are from month t.
- Optimizer covariance and residual volatility use months t-59 to t.
- The Daniel-Moskowitz bear flag (past 24-month market return < 0) is lagged one month.
- Factor returns enter only the ex-post performance regressions.
- This module uses no macro releases and no Ken French BE/ME, so no release lag is needed.
- Exceptions: emissions are one static cross-section applied to every month, and the Q4 team strategies keep the team's same-month attention timing (see Caveats; section 8 reports a one-month-lag check).

Returns and costs:
- gross(t+1) = sum_i w_i(t) r_i(t+1)
- TO(t) = sum_i |w_i(t) - w~_i(t)|, where w~_i(t) = w_i(t-1)(1 + r_i(t)) / (1 + r_p(t)) is the previous book after drift
- net(t+1) = gross(t+1) - c * TO(t), with c = 10 bp
- TO counts every dollar bought or sold once, per unit of capital; fully replacing both legs gives TO = 4. Annual turnover = 12 * mean(TO); cost drag = 12 * mean(c * TO).

Performance statistics:
- Annualized mean = 12 * mean; annualized volatility = sqrt(12) * sd; Sharpe (or IR for a zero-investment book) = sqrt(12) * mean / sd.
- Maximum drawdown is taken on compounded net wealth.
- Alpha = 12 * intercept from OLS on the factor set, with NW6 standard errors and normal p-values. Multi-factor alphas need n >= 24 and CAPM needs n >= 12, so the last-12 and last-18 month windows show CAPM only.
- Small-sample check (alphas, robustness): the same intercept with a classic OLS standard error and a Student-t p-value on n - k degrees of freedom (columns t_alpha_ols, p_alpha_ols_t).
- Alpha break-even cost = the one-way cost at which the FF5+UMD alpha of gross - c * TO reaches zero. It is undefined (NaN) when the gross alpha is negative.

Carbon:
- WACI (weighted average carbon intensity) of a leg = sum_i w_i c_i / sum_i w_i, over holdings that have an intensity.
- Convention X: the 8 uncovered industries are excluded from carbon-constrained books, and WACI is taken over covered holdings; the coverage share is reported.
- Convention M: uncovered industries get the median intensity, 0.0610.
- Market benchmark: cap-weighted WACI of the 41 covered industries.
- Top-5 emitters: Util, Ships, Aero, Steel, BldMt. Top-8 adds Chems, Trans, Mines.
- Screens: (a) exclude top-5 or top-8 from the long leg only; (b) exclude them from both legs. Under X the uncovered 8 are also excluded from each constrained leg; the "0" variants (A0X, B0X) isolate that effect alone.

Grinold-Kahn optimizer, at each month-end t:
- z_i = cross-sectional z-score of the 11-1 signal
- sigma_i = sd of residuals from an OLS of industry excess return on Mkt-RF over months t-59 to t
- alpha_i = IC * sigma_i * z_i, with IC = 0.05 fixed a priori (monthly units)
- V = Ledoit-Wolf shrunk covariance of trailing 60-month industry excess returns
- c_i = cross-sectional z-score of log intensity
- Problem: maximize alpha'h - kappa * sum|h - h~| subject to h'Vh <= 0.05^2/12, sum h = 0, |h_i| <= 0.10, c'h <= b, with kappa = 10 bp. Realized costs are also 10 bp per unit traded.

Why the risk limit is a constraint: it is the Lagrangian dual of a lambda h'Vh penalty, with lambda set so ex-ante tracking volatility is exactly 5% a year. Rescaling h after solving would break the box and carbon limits; the constraint form keeps them exact. Solver: Clarabel via cvxpy.

b sweep: {none, +1, +0.5, +0.25, 0, -0.25, -0.5, -0.75, -1, -1.25, -1.5, -2}. When c'h <= b is infeasible, the month falls back to the minimum-carbon book. That happened only at b = -2: 64 months under X and 38 under M (optimizer_frontier). A month counts as "binding" when c'h >= b - 1e-5; that share depends slightly on solver tolerance (26.5% here at b = 0, 26.7% in the verifier's own solve), so it is quoted to one decimal at most.

Bootstrap: paired circular block, block 12, 5,000 draws, seed 20260926. Two-sided p = share of |stat* - stat_hat| >= |stat_hat|.

## 5. Primary results (Q1)

The pre-registered tests fail.
- P1 (full sample): net FF5+UMD alpha 1.74% (t = 1.09, p = 0.274, n = 679).
- P2 (post-2010): 1.86% (t = 0.71, p = 0.481, n = 199).
- Holm-adjusted p = 0.823 for both (alphas, multiple_testing).

The raw premium is real, but it is the UMD premium in industry form.
- Net return 8.52% a year, volatility 18.00%, net Sharpe 0.47 (t = 3.47).
- CAPM alpha 9.45% (t = 3.92); FF3 10.92% (t = 4.60); FF5 10.25% (t = 3.96).
- Adding UMD brings alpha to 1.74%: UMD beta 0.99 (t = 30.5), R-squared 0.67, correlation with UMD 0.81 (gb_correlations). The book's net return is spanned by the gross paper UMD factor.
- Without UMD the book loads on HML: -0.32 (t = -2.44) in FF3 and -0.46 (t = -3.16) in FF5.

Performance by period, net of 10 bp (perf_periods):

| Period | Net return | Vol | Sharpe | Max DD | Turnover x/yr |
|---|---|---|---|---|---|
| Full 1970-01 to 2026-07 | 8.52% | 18.00% | 0.47 | -60.3% | 12.47 |
| Post-2010 | 6.79% | 15.82% | 0.43 | -29.5% | 12.69 |
| Validation 2010-01 to 2022-07 | 8.35% | 15.60% | 0.54 | -29.5% | 12.39 |
| Holdout 2022-08 to 2026-07 | 1.86% | 16.58% | 0.11 | -25.4% | 13.64 |
| COVID 2020-21 | 14.44% | 19.92% | 0.72 | -22.6% | 10.78 |
| Last 18 months | 3.90% | 19.49% | 0.20 | -14.2% | 12.72 |
| Last 12 months | 8.58% | 23.00% | 0.37 | -14.2% | 12.11 |

- Holdout FF5+UMD alpha: -4.48% (t = -0.84).
- COVID 2020-21 FF5+UMD alpha: 15.80% (t = 3.18, n = 24; BH p = 0.022). No other reported window comes close (the next largest is 5.89% in the 1990s, t = 1.80), so the pattern mirrors the team's own COVID-only result. It is fragile: 24 months with 7 parameters leaves 17 degrees of freedom, and the classic OLS t is 1.58 (Student-t p = 0.132), so the NW normal p-value of 0.0015 is optimistic (alphas, columns t_alpha_ols and p_alpha_ols_t).
- Last 18 and 12 months, CAPM alpha: -2.60% (t = -0.19) and -5.19% (t = -0.26), with market betas of 0.55 and 0.95.
- Net Sharpe by decade (perf_decades): 1970s 0.86, 1980s 0.34, 1990s 1.12, 2000s 0.02, 2010s 0.46, 2020-2026 0.39. No decade has an FF5+UMD alpha with |t| above 1.80.

Turnover and costs (cost_sensitivity, cost_breakeven):
- Turnover is 12.5 a year (1.04 a month), a cost drag of 1.25% a year.
- Full-sample FF5+UMD alpha: 2.99% gross (t = 1.89); 2.36% at 5 bp (t = 1.49); 1.74% at 10 bp (t = 1.09); -0.14% at 25 bp (t = -0.09).
- Net Sharpe: 0.54 gross, 0.51 at 5 bp, 0.47 at 10 bp, 0.37 at 25 bp.
- Break-even cost for the alpha: 23.9 bp (full sample) and 24.5 bp (post-2010). In the holdout the gross alpha is already negative (-3.14%), so no positive break-even exists. For the raw mean: 78 bp and 63 bp (holdout 24 bp).
- The alpha break-even compares a book that pays trading costs with factors that pay none. It says where the book's alpha against paper factors vanishes, not how it compares with an investable UMD replication, whose costs this module does not measure.

Crash behaviour (worst_months, crash_2009, drawdowns, crash_dm_regression, crash_conditional_means):
- Worst month is 2009-04 at -38.75%. The short leg (Fun, Txtls, Steel, FabPr, Autos, Coal, Banks, RlEst) rose +39.40%; the long leg (Food, Beer, Smoke, Drugs, Gold, PerSv, Rtail, Meals) rose +0.80%. UMD was -34.36% and Mkt-RF +10.17%.
- March-May 2009 compounded to -42.88% (UMD -49.37%). Calendar 2009 was -46.25% (UMD -52.83%).
- Maximum drawdown -60.3%: peak 2008-06, trough 2012-01, recovered 2020-04.
- Daniel-Moskowitz regression: market beta falls by 0.53 in bear states (t = -2.94, p = 0.003; BH p = 0.037); the extra up-market bear beta is -0.02 (t = -0.05).
- Bear-state months with a rising market average -2.85% a month (n = 55).
- 2026-07, the last month of the sample, is the 6th-worst month: -14.18% (UMD -12.20%).

## 6. Robustness (exploratory; robustness)

Net FF5+UMD alpha, full sample (t) [net Sharpe]:
- Window 1-0: 3.29% (1.65) [0.25], turnover 38.4 a year
- Window 6-1: -2.70% (-1.59) [0.18]
- Window 12-1: 1.87% (1.30) [0.48]
- No skip (12-0): 2.88% (1.87) [0.51]
- 5 per leg: 2.22% (1.04) [0.44]
- 10 per leg: 0.35% (0.27) [0.40]
- Cap-weighted legs: -4.50% (-2.44) [0.22]
- KF Aug-2026 vintage: 1.74% (1.10) [0.47]. Weights are identical to the primary in every month, so this row differs only through the revised returns (section 3).

No variant has a positive alpha significant at 5%; the only |t| > 2 is negative (cap-weighted legs). Every variant has a negative holdout alpha. The most negative is the cap-weighted legs at -13.33% (t = -2.16). Window 6-1 has the most negative t: -10.79% (t = -3.02, BH p = 0.029; classic OLS t = -1.61, Student-t p = 0.116). Skipping the latest month does not help: 12-0 has Sharpe 0.51 against 0.47 for the primary.

## 7. Carbon (Q3)

Carbon profile of the primary book (carbon_waci, membership, waci_monthly):
- Full sample, convention X: long-leg WACI 0.179 against 0.277 for the cap-weighted market of the 41 covered industries (ratio 0.65). The long leg is above the market in only 24.7% of months.
- That gap is a 1970s-1990s effect of Util's large market weight. Post-2010 the long leg is 0.193 against a market of 0.192 (ratio 1.01). The ratio is 1.08 in the holdout, 0.88 in the last 18 months and 0.78 in the last 12.
- Short-leg WACI is 0.195, so the net long-minus-short WACI is about zero: -0.016 full sample, -0.018 post-2010.
- 84% of long-leg weight is in covered industries. Under convention M the long and short WACIs are 0.160 and 0.165.
- Momentum rotates through the high emitters. Steel is in the short leg 30.5% of months and the long leg 21.2%; Util is long 13.8% and short 15.0%. At least one of the team's Brown-5 industries is in the long leg in 60.5% of months (gb_exposure_summary).

Exclusion screens (carbon_screens; equal weight, 10 bp):
- A8X (drop the top-8 emitters and the 8 uncovered industries from the long leg) cuts long WACI from 0.179 to 0.046 (-74%). Full-sample net Sharpe goes from 0.473 to 0.456: difference -0.017, 95% CI [-0.094, 0.061], bootstrap p = 0.68. Alpha difference -0.15% (t = -0.20).
- B8X (the same exclusion on both legs): Sharpe 0.481, difference +0.007 (p = 0.91), alpha 2.10% (t = 1.68).
- Full sample, across all screens and both conventions, no Sharpe difference exceeds 0.03 in absolute value and no bootstrap p is below 0.29.
- Post-2010 the screens do worse: every screen has a lower Sharpe than the primary's 0.43, by 0.02 to 0.12 (carbon_screens, post-2010 columns). Under convention X none of the differences is significant: B5X -0.120 (95% CI [-0.333, +0.081], p = 0.26), B8X -0.110 (CI [-0.335, +0.105], p = 0.33), A8X -0.036 (p = 0.56), and no X screen has a bootstrap p below 0.258. The intervals are wide enough to include losses of a third of a Sharpe unit. Under convention M the two top-5 screens are nominally significant: A5M -0.067 (CI [-0.130, -0.010], p = 0.027) and B5M -0.117 (CI [-0.214, -0.026], p = 0.017; alpha difference -1.99%, t = -2.10). Neither survives the BH adjustment (BH p = 0.195 and 0.153). The M intervals are narrower because those books keep the uncovered industries and so track the primary more closely.

Optimizer frontier (optimizer_frontier, carbon_cost_test):
- Unconstrained book (X), full sample: realized net IR 0.555; FF5+UMD alpha 2.17% (t = 3.07); realized volatility 6.95% against the 5% ex-ante target; turnover 2.92 a year; long WACI 0.159.
- Q3 PRIMARY: IR change at b = 0 is +0.010, 95% CI [-0.010, +0.031], bootstrap p = 0.328 (Holm p = 0.823). Alpha change +0.08% (t = 1.00). No cost is detected, but b = 0 is a weak test. It binds in about 26.5% of months and cuts long WACI by only 11.6% (to 0.141), and it was chosen knowing that the unconstrained book's c'h averages about -0.09, so a mild bound was expected.
- The informative points are the tighter bounds:

| Bound b | IR | IR change vs unconstrained (95% CI) | Bootstrap p | Long WACI change |
|---|---|---|---|---|
| -0.5 | 0.564 | +0.009 [-0.054, +0.068] | 0.77 | -40% |
| -1.0 | 0.550 | -0.005 [-0.110, +0.096] | 0.93 | -60% |
| -1.5 | 0.481 | -0.074 [-0.244, +0.087] | 0.38 | -72% |
| -2.0 | 0.271 | -0.284 [-0.555, -0.015] | 0.038 | -82% |

- At b = -1 the long book's WACI falls by 60% with a point IR change of -0.005, but the CI reaches -0.110, about 20% of the unconstrained IR of 0.555. The test cannot rule out an IR loss of about 0.1.
- At b = -2, 64 of the months are fallbacks to the minimum-carbon book.
- Alpha differences up to b = -1.5 lie between about 0 and +0.34% a year; none is significant (smallest NW p = 0.109).
- Post-2010 (carbon_cost_test): IR change +0.028 at b = 0 (p = 0.132), -0.008 at b = -1 (CI [-0.188, +0.182], p = 0.93) and -0.318 at b = -2 (p = 0.185). The CIs are wider still.
- Convention M has the same shape. Unconstrained IR is 0.489. IR change is +0.002 at b = 0 (p = 0.84), -0.017 at b = -1 (p = 0.73) and -0.152 at b = -2 (p = 0.17).
- In short: no IR or alpha loss is detected until the extreme, partly infeasible bound b = -2, but the tests have low power. An IR loss of about 0.1 (a fifth of the IR) at b = -1 is inside the confidence interval.

Is the optimizer's own alpha defensible? (exploratory; optimizer_periods, optimizer_vs_primary, realized_ic)
- Full sample: alpha 2.17% (t = 3.07, BH p = 0.027).
- Post-2010: alpha 3.12% (t = 2.18, p = 0.029, BH p = 0.195), IR 0.696 against 0.43 for the equal-weight primary. The post-2010 IR difference against equal weight is +0.267, 95% CI [-0.111, +0.657], bootstrap p = 0.155 (BH p = 0.417), so it is not significant (optimizer_vs_primary).
- By subperiod: validation 2010-01 to 2022-07 alpha 2.99% (t = 1.78); holdout -0.34% (t = -0.15). By decade, the alpha is significant at the nominal 5% level only in 2020-2026 (5.45%, t = 1.97, p = 0.049) and not after the BH adjustment (BH p = 0.220).
- Its full-sample IR is not significantly higher than the equal-weight primary: difference +0.082, CI [-0.120, 0.282], p = 0.436.
- Realized rank IC of the signal is 0.054 (t = 4.85) over the full sample, but 0.033 post-2010, 0.030 (t = 1.14) in the holdout and -0.005 in the last 18 months. The a priori IC of 0.05 is optimistic for the recent period.

## 8. Link to green-minus-brown (Q4)

- Q4 PRIMARY: in GB = FF3 + INDMOM, 1970-2026, the INDMOM loading is -0.062 (t = -1.94, p = 0.053; Holm-adjusted 0.211). Not significant.
- Correlations (gb_correlations): corr(GB, INDMOM) = -0.068 and corr(GB, UMD) = -0.039 over the full sample; 0.042 and 0.033 post-2010; about -0.29 in the 48-month holdout (t about -1.87).
- GB has no time-series momentum of its own: slope 0.0069 (t = 0.60) (gb_tsmom).

Industry momentum does not explain the raw spread's HML loading (gb_hml_attribution):
- Full sample: GB's HML loading is -0.233 (t = -4.63) in FF3, -0.253 (t = -5.27) once INDMOM is added and -0.256 (t = -5.20) with UMD instead.
- Post-2010: -0.298 (t = -5.74) in FF3, -0.306 (t = -5.76) with INDMOM and -0.323 (t = -6.16) with UMD instead.

The team's traded Short-Brown strategies (post-2010) carry a weak, generic momentum tilt:
- Hold 3m: HML goes from -0.051 (t = -2.34) to -0.040 (t = -2.00) when INDMOM is added. INDMOM loads +0.038 (t = 2.12, BH p = 0.205).
- Hold 6m: HML goes from -0.061 (t = -2.36) to -0.046 (t = -2.12). INDMOM loads +0.054 (t = 2.59, BH p = 0.090).
- The tilt is not specific to industry momentum. INDMOM absorbs 22% (hold 3m) and 25% (hold 6m) of the HML loading, but UMD alone absorbs 26% in both, and with UMD in the regression INDMOM's t falls to 1.10 and 1.22.
- Their correlation with INDMOM is 0.21-0.22 post-2010 (t = 2.34 and 2.79; BH p = 0.160 and 0.056) and about zero in the holdout (-0.004 and 0.073).
- Timing check: the team code uses the EMV value for month t at the end of month t. With attention lagged one month (rows *_attlag1 in gb_regressions and gb_hml_attribution), the INDMOM loadings are about the same, 0.037 (t = 1.99) for hold 3m and 0.057 (t = 2.70) for hold 6m. They again fall to t = 1.27 and 1.50 once UMD is added. The HML loadings shrink to -0.030 (t = -1.19) and -0.049 (t = -1.92). The Q4 conclusion does not depend on the timing. (The lagged strategies earn 0.73% and 1.19% a year post-2010, against 0.07% and 1.34%; team_replica_check.)

Interpretation: the team's Short-Brown windows may have leaned slightly toward shorting Brown industries when they were already losers, but this is a generic momentum exposure, it does not survive multiple-testing correction, and it cannot be attributed to industry momentum as opposed to UMD. The raw spread's -0.23 to -0.32 HML loading is value versus growth, not momentum.

## 9. Implications for the project verdict

Do not implement industry momentum as a stand-alone alpha source on these data.
- The pre-registered net FF5+UMD alphas are 1.74% (t = 1.09) and 1.86% (t = 0.71).
- The book's net return is spanned by the gross paper UMD factor (beta 0.99, R-squared 0.67). Its alpha against these costless factors vanishes at about 24 bp one-way.
- It lost 38.75% in one month in 2009 and had a drawdown lasting 12 years.
- Every variant's holdout alpha is negative.
- The optimizer version looks better post-2010 (IR 0.696), but its edge over equal weight there is not significant (p = 0.155), it loses its alpha in the holdout (-0.34%, t = -0.15), and none of its subperiod alphas survives the BH adjustment.

The carbon answer for the report: on an industry-momentum book, no cost of a carbon constraint is detectable, but the tests have low power. Full sample, exclusion screens cut long-leg WACI by 67-74% (A5X, A8X) with Sharpe changes of 0.03 or less, and the optimizer at b = -1 cuts it by about 60% with an IR change of -0.005. The confidence intervals still allow an IR loss of about 0.1, and post-2010 the screened books' Sharpes are 0.02 to 0.12 lower. This is largely because there is little alpha to lose.

For the team's thesis: industry momentum is not the hidden driver of green-minus-brown. The traded strategies' small momentum tilt is generic (UMD does as well), not significant after multiple-testing correction, and does not touch the raw spread's HML loading.

## 10. Caveats
- Static emissions: one cross-section of unknown (probably recent) vintage is applied back to 1970, so early WACIs and screens are anachronistic. The market benchmark's decline over time reflects changing cap weights, not changing intensities.
- Missing coverage: 8 industries lack intensities, including Oil, which convention M assigns the median (0.061), surely an understatement. Convention X drops them. The uncovered-only variants show that dropping them costs little over the full sample: A0X Sharpe change -0.010 (p = 0.73), B0X +0.001 (p = 0.98). Post-2010 the uncovered-only effect is larger (B0X -0.071, p = 0.43), about half of the both-legs X screens' post-2010 gap.
- Costs: 10 bp per unit traded is a stylized industry-ETF or futures cost with no market impact. The alpha break-even of about 24 bp leaves little room, and it is measured against factors that pay no costs.
- Optimizer choices: IC, the 60-month window, the 5% tracking target and the 0.10 box were fixed a priori, not tuned. The b grid was fixed before results. The b = 0 primary was chosen knowing that c'h averages about -0.09 when unconstrained, which makes it a mild bound. Realized volatility (6.95%) exceeds the 5% ex-ante target. The binding share is sensitive to solver tolerance at the first decimal.
- Multiple testing: 416 tests are logged. All four primaries have Holm-adjusted p of 0.211 or more. 37 exploratory tests have BH p below 0.05 (multiple_testing_summary). Eleven are descriptive factor loadings (the book's UMD and FF5 HML betas and nine HML loadings of GB). If the 30 loading rows are left out of the BH family, 26 tests survive, and they are the same hypothesis tests. They are: the INDMOM-UMD correlations (4); the primary book's raw mean and CAPM, FF3 and FF5 alphas, all removed by UMD (4); the full-sample rank IC (1); the optimizer's full-sample alphas for the unconstrained book and at every bound from +1 to -1.5 (11); the Daniel-Moskowitz bear-state beta change for the book and for UMD (2); the COVID 2020-21 FF3, FF5 and FF5+UMD alphas of the primary book (3); and the window 6-1 holdout alpha, which is negative (1). The COVID and 6-1 results rest on NW t-statistics that fall by roughly half or more with classic OLS standard errors (the COVID FF5 alpha's t goes from 6.44 to 1.99), and all four have classic Student-t p-values between 0.06 and 0.19 (sections 5 and 6; column p_alpha_ols_t in alphas and p_alpha_ols_t_holdout in robustness), so they are not robust discoveries.
- Short windows: last-12 and last-18 month statistics carry almost no information, and multi-factor alphas are not reported for them. The 24-month COVID window is also too short for reliable NW inference (section 5).
- Q4 team strategies are my re-implementation of the team's code (exact match on their published 2010-2026 figures; team_replica_check), not their output files. They inherit the team's same-month attention timing: the EMV value for month t is used at the end of month t, which logs/replication.md flags as possibly unavailable in real time. Section 8 reports the one-month-lag version.
- The KF Aug-2026 robustness row differs from the primary only through revised returns in 2026-07 and small revisions from 2020-07 on (section 3).
- Runtime: run.py takes 4 to 10.5 minutes depending on machine load: 4m11s in the final run here, 7m13s in an earlier run under load, and 10m26s for the verifier. Most of it is the 24 optimizer paths and the bootstraps.

## 11. Output files
- Code: modules/M5_industry_momentum/run.py (entry point), m5lib.py, optimizer.py, team_replica.py.
- Tables (outputs/tables/M5_industry_momentum_*.csv; .tex where marked): returns_monthly, weights_primary, perf_periods(.tex), perf_decades(.tex), alphas(.tex), cost_sensitivity(.tex), cost_breakeven, worst_months(.tex), crash_2009(.tex), drawdowns, crash_dm_regression, crash_conditional_means, robustness(.tex), kf_vintage_diff, kf_vintage_diff_last_month, carbon_waci(.tex), waci_monthly, membership, gb_weight_exposure, carbon_screens(.tex), optimizer_frontier(.tex), optimizer_returns_monthly, optimizer_paths_monthly, optimizer_periods(.tex), optimizer_vs_primary, carbon_cost_test(.tex), realized_ic, team_replica_check, gb_correlations, gb_regressions(.tex), gb_hml_attribution, gb_tsmom, gb_exposure_summary, rolling_alpha, tests_ledger, multiple_testing, multiple_testing_summary.
- Figures (outputs/figures/M5_industry_momentum_*.pdf/.png): cumulative, carbon_frontier, rolling_alpha, waci.

## 12. Response to verification
I re-derived every point from the tables and the data before changing anything. I agree with all 11 points and disagree with none. Two of the checks turned out worse for the original text than the verifier said (items 5 and 8c). No previously reported estimate changed. All 335 original ledger rows (statistics and raw p-values) and every existing table cell are identical after the rerun, with one intended exception: the holdout alpha break-even is now NaN instead of 0 (item 11a). The BH-adjusted p-values move because the ledger grew. The fixes add columns, rows and four new tables.

1. Sec 8, -0.256 (agree). -0.256 (t = -5.20) is the full-sample FF3+UMD HML loading. The post-2010 value is -0.323 (t = -6.16) (gb_hml_attribution). Both are now stated in the right sentences.
2. Sec 6, most negative holdout alpha (agree). Cap-weighted legs have the lowest holdout alpha (-13.33%, t = -2.16); window 6-1 has the most negative t (-10.79%, t = -3.02). Reworded. New check: the 6-1 t is fragile (classic OLS t = -1.61, p = 0.116).
3. Optimizer decade t = 1.97 (agree). p = 0.049 is below 0.05. The text now says the alpha is significant at the nominal 5% level only in 2020-2026 and not after BH (BH p = 0.220 in the enlarged ledger; 0.234 in the old one).
4. Optimizer post-2010 omission (agree). Added: alpha 3.12% (t = 2.18, p = 0.029, BH p = 0.195), IR 0.696 against 0.43. I also bootstrapped the post-2010 IR difference against equal weight, which the verifier had not: +0.267, CI [-0.111, +0.657], p = 0.155. The verdict stands.
5. BH survivors omission (agree). The COVID FF5+UMD alpha (15.80%, t = 3.18, BH p = 0.022) and the 6-1 holdout alpha (BH p = 0.029) are now in sections 5, 6 and 10. The verifier's small-sample concern is borne out: alpha_fit now also reports classic OLS t-statistics with Student-t p-values, and the COVID alpha's t falls from 3.18 to 1.58 (p = 0.132, 17 degrees of freedom).
6. KF vintage (agree). The two files differ in 113 cells over 54 months from 2020-07, by at most 0.22 pp outside 2026-07 and by up to 7.02 pp in 2026-07 (26 industries; PerSv, Clths and BusSv are in the short leg). The monthly weights are identical. 2026-07 net is -13.95% under KF against -14.18%, still the 6th-worst month. New tables kf_vintage_diff and kf_vintage_diff_last_month.
7. "A client who can hold UMD" (agree). Replaced with the spanning statement (UMD beta 0.99, R-squared 0.67). The break-even caveat now notes the benchmark factors pay no trading costs.
8. "Costs nothing measurable" / "close to free" (agree). (a) The b = 0 primary is now described as a weak test: it binds in about 26.5% of months, cuts long WACI by 11.6%, and was chosen knowing that c'h averages -0.09. (b) The b = -1 interval [-0.110, +0.096] is quoted, with the statement that an IR loss of about 0.1 cannot be ruled out. (c) I bootstrapped the post-2010 screen differences instead of only adding a qualifier. Under convention X none is significant (p >= 0.258). Under convention M, A5M (p = 0.027) and B5M (p = 0.017) show nominally significant post-2010 Sharpe losses, which do not survive BH (0.195 and 0.153). The headline now says "no detectable cost, low power", with the post-2010 qualifier.
9. Q4 22-25% absorbed (agree). Reworded as a generic momentum tilt: with UMD in the regression INDMOM's t is 1.10 and 1.22, UMD alone absorbs 26%, and the INDMOM loadings' BH p are 0.205 and 0.090.
10. Ledger completeness (agree, and extended). Added the Daniel-Moskowitz B x M rows (book: -0.53, t = -2.94, p = 0.003, BH p = 0.037; UMD also logged) and the gross (0 bp) FF5+UMD alphas. I also logged every other inferential statistic this file cites: the factor loadings (tagged [loading]), the screen alphas, the post-2010 screen and optimizer-vs-EW bootstraps, and the attention-lag Q4 rows. The ledger has 416 rows. BH survivors are 37 with the loadings and 26 without; the surviving hypothesis tests are the same either way (multiple_testing, p_bh_exploratory_excl_loadings).
11. Minor (agree with all four). (a) The holdout alpha break-even is now NaN with a note (gross alpha -3.14%). (b) Runtime caveat updated with measured times. (c) The Q4 caveat now states the same-month attention timing, and I ran the one-month-lag version: INDMOM loadings 0.037 (t = 1.99) and 0.057 (t = 2.70), falling to t = 1.27 and 1.50 with UMD. Conclusion unchanged. (d) The binding share is quoted as about 26.5%, and the tolerance dependence is noted in the method.
