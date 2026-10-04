<!-- Saved by the orchestrator from the builder's returned text (subagent report writes are blocked by the harness). Source agent aa4d57e92717c48a9. -->
# M6_factor_timing: can a disciplined shrinkage model time Green-minus-Brown?

Run: `cd /home/hashim/projects/GA/project/research && uv run python modules/M6_factor_timing/run.py` (about 60 s; exit 0).
Every number below is copied from a CSV in `outputs/tables/`, named in brackets after each block. This version includes the fixes from the independent verification (`modules/M6_factor_timing/VERIFY.md`). Checks added in response to it are marked "added after verification". They are robustness checks, not pre-registered tests.

## Headlines

1. **The pre-registered ridge model cannot time GB.** Its MSE-based time-series CV picks the maximum penalty in 100% of monthly refits: 439 of 439 for Spec A from 1990-01, and 319 of 319 for Spec B from 2000-01. Every forecast is the expanding historical mean (largest gap 3.0e-8), and R2_OOS is numerically 0.000% for both specs, full OOS and post-2010 (Holm p = 1). CV that validates only on the last 120 or 60 training months picks a smaller penalty in 14% to 48% of months, with no gain: R2_OOS is at most +0.13% and CW t at most 0.50.
2. **Less shrinkage is worse.** At fixed penalties from OLS to 10, full-OOS R2_OOS runs from -2.58% to -0.12% (A) and from -7.77% to -0.02% (B). The pseudo-OOS CV error is above the historical mean at every penalty (1.17x at OLS in Spec A). The LMN Sharpe-validated variant does time: it picks the static limit in at most 12% of years. It loses (net Sharpe -0.33 to 0.11, none significant).
3. **Attention adds nothing.**
   - The primary nested comparison (B vs B0) is numerically 0 (max forecast gap 5e-9).
   - At every fixed penalty, adding ATTN lowers R2_OOS: -1.07% to -0.08% over 2000-2026 and -1.55% to -0.01% post-2010, with every CW t negative.
   - In the LMN variant, adding ATTN lowers the net return by 1.04%/yr (sign, t -2.38) and 0.57%/yr (raw, t -2.00).
   - On the team's own target (next-month Brown-leg FF3 residual), ATTN's in-sample slope is -0.03%/sd (t -0.24). Its OOS R2 is -0.74% from 2000 and -0.78% in the holdout.
   - MCCC (exploratory) is roughly neutral: best +0.32%, p = 0.24.
4. **The recent gains are not timing skill.**
   - The timing portfolio is the prevailing-mean portfolio (identical to within 4.5e-7 per month).
   - It has been short GB in every month since 2022-05 (A) and 2021-12 (B). The historical mean was last positive for the 2022-04 (A) and 2021-11 (B) target months.
   - Last-12-month net Sharpe is 0.64 (A) and 0.99 (B), against -1.37 for static long.
   - Over the full OOS window, timing minus static is +0.84%/yr (t = 1.17) and +0.66%/yr (t = 0.45). With the static leg scaled to the timing rule's mean |w| instead of equal volatility, the t-stats are 0.98 and 0.11.
5. **Style exposure.**
   - The static GB spread at 5% vol is short RMW (-0.12; t -2.90 from 1990 and -2.62 from 2000) and HML (-0.07, t -1.99; -0.08, t -2.22) in both windows.
   - From 2000 it is also short Mkt (-0.05, t -2.68) and UMD (-0.06, t -2.47).
   - From 1990 it is also short CMA (-0.10, t -2.05) and SMB (-0.055, t -1.98). CMA is not significant from 2000 (-0.08, t -1.48).
   - The exploratory rotation ridge (net Sharpe 0.32) does not beat plain 12-1 industry momentum (0.40). The difference is -1.98%/yr, t -1.07; the ridge's UMD beta is 0.73 (t 11.0).
   - The module supports "Do not implement".

## 1. Question

Can the team's Green-minus-Brown spread (GB) be timed out of sample by a shrinkage-disciplined forecasting model, in the spirit of Lehnherr, Mehta and Nagel (2024, "Optimal Factor Timing in a High-Dimensional Setting")? And does climate attention (the team's EMV Energy and Environmental Regulation signal) or MCCC add anything beyond value spreads and macro variables?

Short answer: no to both.
- Under the pre-registered MSE-based CV, the model is the expanding historical mean in 100% of months.
- CV designs that allow some timing, fixed smaller penalties, forecast combinations and the LMN Sharpe-validated variant all fail to beat it.
- Adding attention makes forecasts worse at every fixed penalty. It also makes forecasts worse on the team's own Brown-residual target.

## 2. Data and timing (lag) convention

**Real-time convention.** Row t holds only information known at the end of month t. Its target is the return earned in month t+1. Output series are indexed by the month the return is earned.

**Target.** Next-month GB, where:
- GB = equal-weighted mean of the 5 lowest-intensity industries (Fun, RlEst, Drugs, Telcm, Fin) minus the 5 highest (Util, Ships, Aero, Steel, BldMt).
- Returns come from the team file `data/ff49_industry_monthly.csv` (value-weighted, decimals, 1926-07 to 2026-07).

**Predictors** (row t) and their lags:
- **VS:** Green minus Brown mean industry log BE/ME (Ken French "Sum of BE / Sum of ME").
  - The row indexed June 30 of year Y first enters at the end of July Y. So it is first used for the August Y return, and it is carried forward at most 12 months.
  - This is one month more conservative than the Fama-French convention. The verifier confirmed the KF row Y uses December Y-1 market equity.
- **MOM12:** GB compounded over months t-11..t.
- **TERM = GS10 - TB3MS, CREDIT = BAA - AAA, DGS10 = GS10(t) - GS10(t-12):** FRED monthly averages, fully observed at the end of t.
- **INFL:** CPI YoY for month t-1 (one-month release lag). October 2025 CPI was never published, so the September print is carried forward for 2025-11.
- **CFNAI:** value for month t-1 (one-month release lag).
- **WTI:** 12-month log change of the monthly-average price (team macro file, which equals FRED MCOILWTICO), 1986 onward.
- **LVIX:** log month-end VIX (1990 onward).
- **ATTN:** the team signal rolling_z(log1p(EMV_env)), a 60-month window including t (team convention), 1987-12 onward. Robustness uses ATTN lagged one month.
- **MCCC:** log Ardia et al. aggregate for month t, 2003-01 to 2025-06.

**Other inputs.**
- Alpha factors: FF5 + UMD (Ken French).
- Team target (section 7, added after verification): the team's FF3 file.
- Trailing variance for the timing weight: 60-month GB variance through t.

**Data vintages.** FRED data are final revised vintages, not real-time vintages.

**In-sample univariate slopes** [M6_factor_timing_predictors.csv; descriptive, look-ahead in the standardization]. No predictor has |t| > 2.
- Largest (1990 sample): INFL -0.32% per month per s.d. (t = -1.94), WTI (t = -1.71) and DGS10 (t = -1.67).
- ATTN: +0.09% per s.d. (t = 0.52).
- MCCC: +0.09% (t = 0.46). Its in-sample regression starts 2003-01 (ledger id `IS_univariate_MCCC_2003`; the column `is_start_1990` records the true start).

## 3. Method

**Specifications**, all refit every month on an expanding window:
- **Spec A "no VIX, from 1970":** VS, MOM12, TERM, CREDIT, DGS10, INFL, CFNAI. Rows start 1970-01; OOS targets start 1990-01.
- **Spec B "full, from 1990":** Spec A + WTI + LVIX + ATTN. Rows start 1990-01; OOS targets start 2000-01. The first training window has 119 predictor-target pairs.
- **Spec B0:** Spec B without ATTN, the nested model for the attention test.
- **C0 / C_mccc / C_attn (exploratory):** B0, B0 + MCCC and B0 + ATTN, estimated from 2003-01. OOS targets run 2013-01 to 2025-07.

**Estimator.**
- At origin t, the training rows are the origins s < t, all of whose targets are realized by t.
- Predictors are standardized with training-row means and standard deviations. The same moments are applied to x_t.

    min over (a, b):  (1/n) * sum_s (y_{s+1} - a - z_s'b)^2 + lambda * ||b||^2     (intercept a unpenalized)
    forecast_t = a_hat + z_t' b_hat(lambda*)

**Penalty choice (primary, pre-registered).**
- Grid: 36 log-spaced lambdas from 1e-4 to 1e3, plus 1e6. The 1e6 point reproduces the historical mean to about 1e-8.
- Folds are expanding. The first fold trains on 60 training rows. Each subsequent 12-month block is predicted by a model fit, and standardized, only on rows before it.
- lambda* minimizes the pooled validation MSE; ties go to the larger penalty.
- Benchmark: the expanding historical mean of GB over the same training rows. This is the model's limit as lambda goes to infinity.

**Tests.**

    R2_OOS = 1 - sum (y - f_model)^2 / sum (y - f_bench)^2                               (Campbell-Thompson)
    CW_t   = e_b^2 - [ e_m^2 - (f_b - f_m)^2 ];  t-stat of mean(CW_t), NW(6)             (Clark-West 2007)
    H1 (one-sided): model has lower MSPE than the benchmark;  p1 = 1 - Phi(t).

- A CW t < 0 is never evidence for the model.
- When the forecast equals the benchmark in every month (max |gap| < 1e-7), the statistic is set to 0 (p1 = 0.5). The gap is reported in `max_abs_forecast_diff`.

**Timing portfolio.**

    w_t = f_t / (gamma * sigma2_t),   gamma = 5,   sigma2_t = 60-month GB variance through t;   return = w_t * GB_{t+1}

- One ex-post constant scales gross volatility to 5% a year over each spec's full OOS window.
- The static benchmark is w = 1, scaled the same way.
- Each strategy's own Sharpe ratio and t-stat are invariant to its constant. A difference between two strategies is not; see section 10.

**Positions and costs.**
- Industry positions are +w/5 in each Green and -w/5 in each Brown industry. Turnover is measured against drifted weights:

      turnover_t = sum_i | h_{i,t} - h_{i,t-1} (1 + r_{i,t-1}) / (1 + R_{p,t-1}) |

- Cost: 10 bp per unit traded.

**LMN (2024) portfolio-shrinkage variant (robustness).** K = 1.
- Timing portfolios: G_j = z_{j,t} GB_{t+1}, plus GB itself.
- At each December:
  - mu = mean of the G_j.
  - Sigma = their Ledoit-Wolf covariance; D = diag(Sigma).
  - w0 = (mu_GB, 0, ..., 0).
  - w(lambda) = (Sigma + lambda/T D)^{-1} (mu + lambda/T w0).
- The implied GB weight is h_t = w_0 + sum_j w_j z_{j,t}. "lmn_sign" uses sign(h_t), which is LMN's |h| = 1 normalization when K = 1. "lmn_raw" uses h_t itself.
- lambda maximizes the Sharpe ratio over all earlier 12-month blocks; the grid is 0, 25 values from 0.1 to 1e5, and 1e9 (the static limit).
- The first block is used only for validation, so Spec B's LMN OOS starts 2001-01.

**Industry rotation panel (exploratory).**
- Target: the next-month industry excess return minus beta_t * MKT_{t+1} (60-month beta), demeaned across industries.
- Features: cross-sectional z-scores (winsorized at +/-3) of log BE/ME (from the end of July), 12-1 momentum and log firm size, plus their interactions with point-in-time expanding z-scores of TERM, CREDIT and INFL.
- Estimation: pooled ridge with the same walk-forward CV.
- Portfolio: long the top 8 and short the bottom 8 of 49 industries. The comparison is plain 12-1 momentum, top 8 minus bottom 8.

## 4. Pre-registered primary tests (fixed before any result was inspected)

- **Q1 (predictability):** one-sided CW test and R2_OOS of ridge-CV vs the expanding historical mean. Spec A over 1990-01 to 2026-07 and post-2010; Spec B over 2000-01 to 2026-07 and post-2010 (4 tests).
- **Q2 (attention increment):** CW test of Spec B vs the nested Spec B0, full OOS and post-2010 (2 tests). Holm is applied across the 6 Q1 + Q2 tests.
- **Q1b (economic value):** NW(6) t of the monthly net-return difference, timing minus static always-long GB, both at 5% vol, over each spec's full OOS window (2 tests).

Everything else is robustness or exploratory, as labelled in the CSVs and the ledger.

## 5. Primary results

**Q1. The disciplined model never times.**
- CV chose lambda = 1e6 in 100% of monthly refits: 439 of 439 for A and 319 of 319 for B.
- The largest gap between the ridge forecast and the historical mean is 2.0e-8 (A) and 3.0e-8 (B) in monthly return units [M6_factor_timing_histmean_sign.csv].

| Spec | Window | n | R2_OOS (%) | CW t | one-sided p | Holm p |
|---|---|---|---|---|---|---|
| A | 1990-01 to 2026-07 | 439 | 0.000 | 0 (degenerate) | 0.50 | 1.00 |
| A | 2010-01 to 2026-07 | 199 | 0.000 | 0 (degenerate) | 0.50 | 1.00 |
| B | 2000-01 to 2026-07 | 319 | 0.000 | 0 (degenerate) | 0.50 | 1.00 |
| B | 2010-01 to 2026-07 | 199 | 0.000 | 0 (degenerate) | 0.50 | 1.00 |

[M6_factor_timing_oos_primary.csv; Holm in M6_factor_timing_oos_tests.csv]

- The same holds in the validation, holdout, covid, inflation_rates, last18 and last12 windows (exploratory).
- The full-sample CV curve, CV MSE relative to the historical mean [M6_factor_timing_shrinkage_path_*.csv, cv_mse_rel_histmean]. It never goes below 1:

| Penalty | 1e-4 | 0.1 | 1 | 10 | 100 |
|---|---|---|---|---|---|
| Spec A | 1.170 | 1.108 | 1.034 | 1.004 | 1.0004 |
| Spec B | 1.149 | 1.077 | 1.018 | 1.002 | 1.0002 |

**Q2. Attention adds nothing (primary).** Both B and B0 collapse to the historical mean, so the nested comparison is numerically 0:
- R2_OOS = 0.000% and CW t = 0 over 2000-01 to 2026-07 (n = 319) and post-2010 (n = 199); Holm p = 1.00.
- The largest forecast gap between B and B0 is 5.4e-9 (full OOS) [M6_factor_timing_oos_tests.csv, max_abs_forecast_diff].

**Q1b. Timing portfolio vs static always-long** (both at 5% vol, net of 10 bp) [M6_factor_timing_portfolio_perf.csv]:

| Window | A timing ret %/yr | A timing Sharpe | A static ret %/yr | A static Sharpe | B timing ret %/yr | B timing Sharpe | B static ret %/yr | B static Sharpe |
|---|---|---|---|---|---|---|---|---|
| full OOS (A 1990-01, B 2000-01, to 2026-07) | 0.09 | 0.02 | -0.75 | -0.15 | -0.97 | -0.19 | -1.63 | -0.33 |
| post2010 | -0.31 | -0.22 | -0.94 | -0.19 | -0.40 | -0.14 | -0.90 | -0.19 |
| validation 2010-01 to 2022-07 | -0.45 | -0.29 | -0.38 | -0.08 | -0.87 | -0.32 | -0.37 | -0.08 |
| holdout 2022-08 to 2026-07 | 0.12 | 0.13 | -2.71 | -0.49 | 1.07 | 0.33 | -2.60 | -0.49 |
| covid 2020-21 | -0.49 | -0.15 | 0.79 | 0.12 | -1.67 | -1.19 | 0.76 | 0.12 |
| inflation_rates 2022-24 | -0.68 | -0.90 | -3.78 | -0.64 | 0.69 | 0.26 | -3.63 | -0.64 |
| last18 2025-02 to 2026-07 | 0.72 | 0.52 | -7.27 | -1.14 | 3.42 | 0.84 | -6.98 | -1.14 |
| last12 2025-08 to 2026-07 | 1.10 | 0.64 | -9.84 | -1.37 | 4.83 | 0.99 | -9.45 | -1.37 |

Pre-registered test of timing minus static [M6_factor_timing_tests_ledger.csv, PORT_*_timing_minus_static_net_full]:
- A: +0.84%/yr, t = 1.17, p = 0.24, n = 439.
- B: +0.66%/yr, t = 0.45, p = 0.65, n = 319.

Net FF5+UMD alpha at 5% vol over the full OOS window [M6_factor_timing_portfolio_perf.csv]:
- Timing: A 0.24%/yr (t = 0.33); B -0.74%/yr (t = -0.89).
- Static: A 0.58%/yr (t = 0.71); B -0.05%/yr (t = -0.05).

Turnover and costs:
- Timing: 0.93x/yr (9.3 bp/yr) for A and 1.18x/yr (11.8 bp/yr) for B.
- Static: 0.60x/yr (6.0 bp) and 0.61x/yr (6.1 bp), all from rebalancing within the legs.

**The timing portfolio is the prevailing-mean portfolio.**
- Its monthly returns equal those of the `prevailing_mean` strategy to within 4.5e-7 per month: max abs difference in net return 4.2e-7 (A) and 4.4e-7 (B).
- Its annual cost drag differs by less than 0.0001 bp: 9.2985 vs 9.2985 bp (A) and 11.8001 vs 11.8000 bp (B) [M6_factor_timing_timing_vs_prevmean.csv].
- Its only signal is the sign of GB's own expanding mean. Spec A is long GB in 83.4% of OOS months and Spec B in 29.2%.
- The historical mean was last positive for the 2022-04 (A) and 2021-11 (B) target months. So the portfolio is short GB in every target month from 2022-05 (A) and from 2021-12 (B) onward.
- At the end of the sample the historical mean stands at -0.62%/yr (A) and -1.57%/yr (B) [M6_factor_timing_histmean_sign.csv].

The good holdout and last-12/18-month numbers therefore come from being short a spread that kept falling, not from any predictor. None of the differences is significant.

**Style exposures** (net returns, 5% vol, full OOS window) [M6_factor_timing_portfolio_ff6_loadings.csv; also in the ledger as FF6_* rows]:

Static GB spread, Spec A window (1990-01 to 2026-07, n = 439), R2 0.14:

| Factor | RMW | CMA | HML | SMB | Mkt | UMD |
|---|---|---|---|---|---|---|
| Loading (t) | -0.124 (-2.90) | -0.102 (-2.05) | -0.066 (-1.99) | -0.055 (-1.98) | -0.031 (-1.94) | -0.032 (-1.41) |

Static GB spread, Spec B window (2000-01 to 2026-07, n = 319), R2 0.18:

| Factor | RMW | HML | Mkt | UMD | CMA | SMB |
|---|---|---|---|---|---|---|
| Loading (t) | -0.122 (-2.62) | -0.081 (-2.22) | -0.050 (-2.68) | -0.056 (-2.47) | -0.078 (-1.48) | -0.041 (-1.16) |

Reading:
- RMW and HML are negative in both windows.
- CMA is significant only in the 1990 window.
- Mkt and UMD are significant only in the 2000 window.

Timing portfolios:
- A: RMW -0.092 (t = -4.29) and UMD +0.048 (t = 2.05); all other |t| at most 1.55.
- B: RMW -0.110 (t = -2.62), UMD +0.058 (t = 2.15) and SMB +0.068 (t = 2.03); all other |t| at most 1.60.

GB is a short-profitability, short-value tilt; the team found the HML part.

## 6. Robustness (labelled robustness in the CSVs)

**CV-design sensitivity (added after verification)** [M6_factor_timing_cv_design.csv / .tex]. The 100% maximum-penalty share belongs to the pre-registered design, which validates on all expanding blocks. Other designs let the model time some of the time, but none gains.

| Design | Spec | Share of refits at max penalty | R2_OOS full % (CW t) | R2_OOS post-2010 % (CW t) |
|---|---|---|---|---|
| recent120: validate only on the last 120 training months | A | 85.6% | -0.21 (-1.30) | -0.41 (-1.11) |
| recent120 | B | 80.6% | +0.07 (0.50) | +0.13 (0.50) |
| recent60: last 60 months only | A | 80.2% | -0.54 (-0.63) | -0.32 (-0.18) |
| recent60 | B | 52.4% | -0.34 (0.34) | -0.33 (0.10) |
| first120: first fold trains on 120 rows | A | 100% | numerically 0 | numerically 0 |
| first120 | B | 99.4% | -0.60 (-1.04) | numerically 0 |
| grid_max1e3: no 1e6 point (max 1e3) | A | 100% | -0.001 (-1.06) | +0.001 (0.47) |
| grid_max1e3 | B | 100% | +0.000 (0.15) | +0.003 (0.69) |

- For Specs A and B, a penalty of 1 or less is chosen in at most 23% of months (B, recent60); for B0, recent60 reaches 24.5%.
- For Specs A and B, no design has a one-sided p below 0.24 against the historical mean (for B0, grid_max1e3 post-2010 has p 0.226).
- B0 under the same designs ranges from -0.50% (first120, full) to +0.01% (recent120).

**Fixed penalties.** These are a sensitivity path, not a selectable specification: choosing among them after the fact would be look-ahead. R2_OOS vs the historical mean at lambda = 0 (OLS), 0.01, 0.1, 1 and 10 [M6_factor_timing_oos_robustness.csv]:
- A, full: -2.58%, -2.53%, -2.15%, -0.91%, -0.12% (CW t from -1.40 to -1.08).
- A, post2010: -0.20%, -0.19%, -0.12%, +0.07%, +0.05% (one-sided p at least 0.33).
- B, full: -7.77%, -7.36%, -5.02%, -0.99%, -0.02%.
- B, post2010: -8.28%, -7.86%, -5.19%, -0.39%, +0.18% (at lambda = 10: CW t = 0.66, p = 0.25).

Figure `M6_factor_timing_gw_cumsse` shows where the OLS losses build up: 1990-91 and 2000-02 (A), and 2000-01 and after 2010 (B).

**Combination of univariate OLS forecasts:**
- A: -0.21% full (CW t = -1.06) and +0.08% post-2010 (p = 0.32).
- B: -0.03% full (t = 0.15) and +0.22% post-2010 (t = 0.69, p = 0.24).

**Other specification changes:**
- Monthly price-updated value spread (A_vsm, B_vsm): degenerate, 100% at the maximum.
- ATTN lagged one month (B_attnlag): degenerate.
- B0 alone vs the historical mean: degenerate.
- A + WTI from 1987 (OOS from 1997-01): CV at the maximum in 96.9% of months; R2_OOS = -0.059% (CW t = -0.87); degenerate post-2010.

**LMN portfolio-shrinkage variant** [M6_factor_timing_lmn_variant.csv, M6_factor_timing_portfolio_perf.csv]:

| Spec, variant | OOS window | Share of months at static limit | Median lambda | Net Sharpe |
|---|---|---|---|---|
| A, sign | 1990-01 to 2026-07 | 10.9% | 5623 | -0.33 (mean t = -1.79) |
| A, raw | 1990-01 to 2026-07 | 0% | 0 | -0.18 |
| B, sign | 2001-01 to 2026-07 | 11.7% | 1000 | -0.10 |
| B, raw | 2001-01 to 2026-07 | 11.7% | 1.78 | -0.08 |
| B0, sign | 2001-01 to 2026-07 | 0% | 31.6 | +0.11 |
| B0, raw | 2001-01 to 2026-07 | 7.8% | 5.62 | +0.03 |

- None is significant.
- Turnover is 2.0x to 5.2x a year, costing 20 to 52 bp/yr.
- Last 12 months (12 observations, descriptive): net Sharpe 1.65 for A sign and -0.71 for B sign.

**OLS kitchen-sink timing portfolio:** net Sharpe -0.13 (A) and 0.01 (B), with turnover of 3.32x/yr (33 bp) and 6.07x/yr (61 bp).

**Univariate forecasts** (exploratory, Goyal-Welch style, 34 tests) [M6_factor_timing_oos_univariate.csv]:
- The only one-sided p values below 0.05 are for DGS10 post-2010: +0.45% (A, p = 0.018) and +1.11% (B, p = 0.020). Neither survives BH across the family (q = 0.34).
- ATTN alone: -1.01% full (CW t = -1.47) and -0.15% post-2010.

## 7. Incremental value of attention and MCCC (Q2 beyond the primary test)

**Nested B vs B0 at fixed penalties** [M6_factor_timing_oos_robustness.csv]. R2_OOS of B relative to B0 at lambda = 0, 0.01, 0.1, 1 and 10:
- Full 2000-01 to 2026-07: -1.07%, -1.04%, -0.88%, -0.47%, -0.08%.
- Post-2010: -1.55%, -1.49%, -1.08%, -0.26%, -0.01%.
- Every CW t is negative, from -1.89 to -0.37. Negative means B is worse. The two-sided p of some of these rows is below 0.10, but that is evidence against attention, not a discovery.

**Nested B vs B0 under the alternative CV designs** (added after verification) [M6_factor_timing_cv_design.csv]:
- recent120 and recent60: +0.05% to +0.15% (CW t from 0.38 to 0.73, one-sided p at least 0.23).
- grid_max1e3: -0.001% and -0.0001%.
- first120: -0.10% full, and +0.14% post-2010 (CW t = 1.99, one-sided p = 0.024). The post-2010 number is not attention information. In that window B collapses to the historical mean, while B0 picks a smaller penalty in some months and loses to the historical mean (B0 vs historical mean post-2010: R2 -0.14%, CW t -1.97). One robustness row out of eight in this family, not pre-registered.

**LMN attention increment** (added after verification) [M6_factor_timing_lmn_attn_increment.csv]. B minus B0 monthly return, both at 5% vol, 2001-01 to 2026-07, n = 307:
- Sign variant: -1.04%/yr net (NW t = -2.38, two-sided p = 0.018) and -1.08%/yr gross (t = -2.42).
- Raw variant: -0.57%/yr net (t = -2.00, p = 0.045) and -0.54%/yr gross (t = -1.87).
- Adding ATTN turns a small positive net Sharpe (B0: 0.11 sign, 0.03 raw) into a negative one (B: -0.10 sign, -0.08 raw).
- These are robustness tests without a multiple-testing adjustment; the direction is "attention hurts".

**Attention vs the team's own target** (added after verification) [M6_factor_timing_team_target_check.csv / .tex, M6_factor_timing_team_brown_residual.csv].

Target: the next-month FF3 residual of the Brown leg, rebuilt exactly as the team's `rolling_factor_model`:

    eps_t = (r_brown,t - RF_t) - alpha_{t-1} - beta_{t-1}' [Mkt-RF, SMB, HML]_t,   60-month rolling OLS, estimates lagged one month.

The team goes Short-Brown after attention spikes, so its hypothesis is a negative slope of eps_{t+1} on ATTN_t.

- In-sample slope (descriptive): -0.028% per month per s.d. from 1990 (t = -0.24, n = 438) and -0.067% from 2010 (t = -0.39, n = 198). The sign is the team's; the size is tiny and not significant.
- Expanding univariate OLS forecast vs the expanding mean of eps (OOS from 2000-01):

| Window | R2_OOS | CW t |
|---|---|---|
| Full | -0.74% | -1.98 (one-sided p = 0.98) |
| Post-2010 | -0.25% | -0.61 |
| Validation 2010-01 to 2022-07 | +0.005% | 0.13 |
| Holdout | -0.78% | -0.82 |

- Spec B ridge-CV on this target: CV at the maximum in 83.7% of months. R2_OOS -0.02% full (CW t = -1.10) and -0.05% post-2010 (t = -2.00).
- Nested B vs B0 on this target:
  - Ridge-CV: +0.07% full (CW t = 1.25, one-sided p = 0.105), +0.07% post-2010 (p = 0.13), numerically 0 in the holdout.
  - OLS: -0.56% (full) and -0.66% (post-2010).
  - lambda = 1: -0.26% and -0.18%.
- No significant increment in any variant.

**MCCC (exploratory; estimation from 2003-01, OOS 2013-01 to 2025-07, n = 151):**
- Ridge-CV collapses to the historical mean, so the MCCC increment is numerically 0 (max forecast gap 7e-9).
- At fixed penalties (lambda = 0 to 10), C_mccc vs C0: -0.42%, -0.27%, +0.32%, +0.17%, -0.01%. The best is +0.32% at lambda = 0.1 (CW t = 0.72, one-sided p = 0.24).
- ATTN on the same sample: -1.70%, -1.68%, -1.52%, -0.62%, -0.06%.

**Full-sample shrinkage path** (interpretation only, look-ahead) [M6_factor_timing_shrinkage_path_B_full_1990.csv]:
- At lambda = 1e-4, the largest coefficients are INFL -0.52, MOM12 -0.35 and VS -0.25 (% per month per s.d.). ATTN is +0.02.
- In the 1970 sample, VS and MOM12 flip sign (Spec A path: +0.01 and +0.11). This instability is why CV refuses them.

## 8. Exploratory: industry-rotation panel (not a GB-timing result)

OOS 1990-01 to 2026-07, n = 439, net of 10 bp, raw volatility [M6_factor_timing_rotation_perf.csv, M6_factor_timing_rotation_stats.csv, M6_factor_timing_portfolio_ff6_loadings.csv]:

| Strategy | Net ret %/yr | Vol %/yr | Sharpe (net) | t (mean) | FF6 alpha %/yr (t) | UMD beta (t) | Turnover x/yr |
|---|---|---|---|---|---|---|---|
| Pooled ridge rotation, top 8 minus bottom 8 | 5.47 | 16.92 | 0.32 | 2.06 | 1.39 (0.57) | 0.73 (11.00) | 10.95 |
| Plain 12-1 industry momentum, top 8 minus bottom 8 | 7.46 | 18.45 | 0.40 | 2.37 | 1.65 (0.94) | 0.96 (27.29) | 12.48 |

- The ridge's CV picks finite penalties here (median lambda 3.98).
- Mean rank IC: 0.0348 (t = 2.97) for the ridge vs 0.0346 (t = 2.79) for raw momentum. Pooled R2_OOS 0.07%.
- Ridge minus momentum: -1.98%/yr (t = -1.07). The ridge also loads on SMB: -0.20 (t = -2.41).
- Net Sharpe in other windows, ridge vs momentum: post-2010 0.19 vs 0.44; holdout 0.01 vs 0.14; last12 0.47 vs 0.51.
- The characteristics-plus-macro model is a noisier industry momentum. Neither has a significant FF5+UMD alpha.

## 9. Implications for the project verdict

1. **Disciplined timing supports "Do not implement".**
   - Under the pre-registered MSE-based ridge-CV, the model puts zero weight on every value-spread, macro and attention predictor in every month since 1990 (A) and 2000 (B). The best forecast of next-month GB is its own historical mean.
   - That "zero weight" is a property of this CV design. CV that validates only on recent months does time in 14% to 48% of months, and the LMN Sharpe-validated variant times in 88% to 100% of years.
   - Neither helps: R2_OOS is at most +0.13%, CW t at most 0.50 for the recent-window designs, and LMN net Sharpe runs from -0.33 to 0.11. Every route to "some timing" ends at no reliable predictability.
2. **Attention fails as a continuous forecaster too, on GB and on the team's own target.**
   - On GB, the ATTN increment is numerically 0 under CV, negative at every fixed penalty, and in the LMN variant ATTN costs 1.04%/yr (t = -2.38).
   - On the FF3-hedged Brown-leg residual the team trades, ATTN's slope has the team's sign but is about 0.03% per s.d. (t = -0.24). Its OOS R2 is -0.74% from 2000 and -0.78% in the holdout.
   - So the attention failure is not specific to the 80th-percentile threshold rule. M6 does not re-test the event rule itself; see M1 and M2.
3. **The recent gains are not timing skill.** Timing net Sharpe of 0.64 to 0.99 over the last 12 months comes from the historical mean turning negative in 2021-22, which left the portfolio short GB while GB kept falling.
4. **Style exposure.**
   - The static GB spread is short RMW and HML in both windows. It is also short CMA and SMB from 1990, and short Mkt and UMD from 2000.
   - Part of any raw GB performance is a style bet.
   - The timing portfolios keep the short-RMW tilt (t = -4.29 for A).

## 10. Caveats

- **Revised data.** FRED vintages are final revised data, which matters for CFNAI and seasonally adjusted CPI. EMV and MCCC are published with a delay in practice. ATTN at month t follows the team convention; the lagged-ATTN robustness gives the same answer.
- **EMV zeros.** EMV has exact zeros in 39 of 59 months from 2021-10, which compresses the rolling z-score in the holdout.
- **Ex-post vol scaling.** Scaling is one ex-post constant per strategy. Each strategy's own Sharpe and t are invariant to it, but the Q1b difference test is not. Timing minus static [M6_factor_timing_scaling_sensitivity.csv]:

| Static leg scaled to | Spec A net t | Spec A gross t | Spec B net t | Spec B gross t |
|---|---|---|---|---|
| Equal ex-post vol, 5% (pre-registered) | 1.17 | 1.21 | 0.45 | 0.49 |
| Timing rule's mean \|w\| | 0.98 | 1.06 | 0.11 | 0.17 |

  The static weights are 0.338 (A) and 0.320 (B) under the mean-|w| scaling, against 0.490 and 0.471 at equal vol. The conclusion is unchanged under either scaling.
- **Risk concentration differs by spec** [M6_factor_timing_risk_concentration.csv]. This is the share of the timing portfolio's sum of squared gross returns:

| Spec | Window | Months | Share of squared gross returns | Window vol | Largest month |
|---|---|---|---|---|---|
| A | 1995-99 | 60 of 439 | 68% | 11.1% | -9.6% in 1999-04 |
| B | 2000-01 | 24 of 319 | 58% | 14.1% | -10.7% in 2000-04 |

  - After 2010 the timing portfolios are small: vol is 1.42% (A) and 2.82% (B) against the 5% full-window target.
  - The static portfolios' risk is spread much more evenly (no window above 34% of squared returns).
- **Turnover** ignores netting across legs and the rebalancing inside each Ken French industry portfolio.
- **Short windows.** last12 and last18 have 12 and 18 observations, and alphas need at least 24. CW statistics in short windows are descriptive.
- **Degenerate primary tests.** The primary CW statistics are degenerate by construction. The informative evidence is the 100% maximum-penalty share and the CV curve, backed by the CV-design, fixed-penalty, combination, univariate, LMN and team-target checks.

## 11. Deviations from the requested specification

- **WTI in Spec A:** no pre-1986 WTI is available locally (the team file and FRED MCOILWTICO start 1986-01), so Spec A omits WTI. A_wti_1987 adds it as robustness.
- **First Spec B training window:** 119 pairs.
- **CW convention:** when the forecast equals the benchmark, CW t = 0.
- **Panel choices:** month fixed effects, with TERM, CREDIT and INFL as the macro interactions, chosen before any result.
- **LMN covariance:** scikit-learn's Ledoit-Wolf intensity is used rather than Schafer-Strimmer.

## 12. Tests ledger

[M6_factor_timing_tests_ledger.csv] 274 rows: 8 primary, 120 robustness, 146 exploratory.
- **Added after verification (100 rows):**
  - 32 CV-design rows.
  - 22 team-target rows.
  - 4 scaling-sensitivity rows.
  - 4 LMN B-minus-B0 rows.
  - 36 FF5+UMD loading rows (6 factors for each of 6 strategies).
  - 2 rotation mean-return rows.
- **Columns.** After the shared nine columns, two are appended:
  - `p_value_one_sided`: the pre-specified p for Clark-West rows, 1 - Phi(t).
  - `alternative`.
- **Two-sided p on CW rows.** `p_value_two_sided` on CW rows is the two-sided normal p of the same statistic, kept for schema compatibility. Report-level multiple testing should use `p_value_one_sided` for CW rows.
- **Negative CW t.** Twelve CW rows have t < 0 with a two-sided p below 0.10, for example B univariate TERM post-2010 (t = -2.62). Each note says "model WORSE than benchmark"; none is a discovery.
- **One-sided p below 0.05.** Only three CW rows have one: the two exploratory DGS10 post-2010 rows and the robustness first120 ATTN row explained in section 7.
- **Rename.** `IS_univariate_MCCC_1990` is now `IS_univariate_MCCC_2003`, its true start.

## 13. Output files

Tables (outputs/tables/):
- **Out-of-sample tests:**
  - M6_factor_timing_oos_primary.csv / .tex
  - M6_factor_timing_oos_tests.csv (all OOS comparisons, with Holm for the primary family)
  - M6_factor_timing_oos_robustness.csv / .tex
  - M6_factor_timing_oos_univariate.csv / .tex
- **Forecasts:**
  - M6_factor_timing_forecasts.csv
  - M6_factor_timing_histmean_sign.csv (adds first_month_short_thereafter)
  - M6_factor_timing_timing_vs_prevmean.csv
- **Portfolios:**
  - M6_factor_timing_portfolio_perf.csv; M6_factor_timing_portfolio.tex; M6_factor_timing_portfolio_returns.csv
  - M6_factor_timing_portfolio_ff6_loadings.csv; M6_factor_timing_ff6_loadings.tex (now with t-stats)
  - M6_factor_timing_scaling_sensitivity.csv; M6_factor_timing_risk_concentration.csv
- **LMN:**
  - M6_factor_timing_lmn_variant.csv; M6_factor_timing_lmn_attn_increment.csv
- **Added after verification:**
  - M6_factor_timing_cv_design.csv / .tex
  - M6_factor_timing_team_target_check.csv / .tex; M6_factor_timing_team_brown_residual.csv
- **Predictors and shrinkage path:**
  - M6_factor_timing_shrinkage_path_A_noVIX_1970.csv; M6_factor_timing_shrinkage_path_B_full_1990.csv
  - M6_factor_timing_predictors.csv / .tex
- **Rotation:**
  - M6_factor_timing_rotation_perf.csv; M6_factor_timing_rotation.tex; M6_factor_timing_rotation_stats.csv
  - M6_factor_timing_rotation_returns.csv; M6_factor_timing_rotation_forecasts.csv
- **Ledger:** M6_factor_timing_tests_ledger.csv

Figures (outputs/figures/, .pdf and .png):
- M6_factor_timing_gw_cumsse
- M6_factor_timing_shrinkage_path
- M6_factor_timing_timing_vs_static
- M6_factor_timing_rotation_cum

Code: modules/M6_factor_timing/run.py (entry point) and modules/M6_factor_timing/m6lib.py. m6lib.py now has CV `recent=`, `scaled_strategy(scale=)` and `team_brown_residual`.

## 14. Response to verification

I re-derived every point in the module code. The verdict is unchanged.

1. **FINDINGS.md not on disk.** Agreed that it is missing. I cannot fix this myself: the harness refuses subagent writes of FINDINGS/report .md files, and my instructions forbid them. This text is returned for the orchestrator to save verbatim.
2. **Headline 4 dates.** Agreed and fixed. histmean_sign.csv now records first_month_short_thereafter = 2022-05 (A) and 2021-12 (B), and short_every_month_thereafter = True.
3. **Headline 5 "and CMA".** Agreed and fixed. CMA is significant only in the 1990 window. Mkt and UMD (2000 window) and SMB (1990 window) are now reported. The timing-portfolio loadings are added as well.
4. **Section 9.1 overreach.** Agreed and reworded. The CV-design sensitivity is now in section 6 and matches the verifier (86% / 80% at the maximum for A, 81% / 52% for B).
   - Refinement: "CW t at most 0.50" holds for the recent-window designs. Across all four alternative designs the maximum is 0.69 (grid_max1e3, B, post-2010, R2 +0.003%).
   - The first120 design also produces the one nominally significant nested ATTN row (p = 0.024). As explained in section 7, it is B0 losing to the historical mean, not attention information.
5. **Section 9.2 overreach.** Agreed. I added the team-target check and it reproduces the verifier: -0.03%/sd (t -0.24), OOS R2 -0.74% (CW t -1.98), -0.25% post-2010, -0.78% holdout.
   - I also ran the multivariate nested test on that target, which the verifier did not. The ridge-CV increment is slightly positive (+0.07%, one-sided p = 0.105), and it is negative at lambda = 0 and 1.
   - This is reported plainly and does not change the conclusion.
6. **Section 10 caveats.** Agreed on both points and fixed.
   - Risk concentration: 68% (A, 1995-99) and 58% (B, 2000-01) confirmed. One correction to VERIFY.md: the largest A month is -9.6% in 1999-04, a loss, not +9.6%. For B, the largest absolute month is -10.7% in 2000-04, not +7.4% in 2000-01 [risk_concentration.csv].
   - Scaling: the verifier's 1.06 / 0.17 are gross returns; net of costs the t-stats are 0.98 / 0.11. Both are reported.
7. **Ledger direction.** Agreed. I added p_value_one_sided and alternative columns, plus a "model WORSE" note on negative-t CW rows. I kept p_value_two_sided as the true two-sided p so the shared schema is unchanged.
8. **Ledger completeness.** Agreed and fixed. The loading, rotation-mean, UMD-beta and LMN B-minus-B0 rows are added; the LMN difference is in section 7 and headline 3. The MCCC row is renamed.
9. **Minor wording.** Agreed and fixed. "Numerically 0 (max forecast gap 5e-9)" replaces "exactly 0", and "identical to within 4.5e-7 per month" replaces "identical rows".
=== END FINDINGS.md ===