# M3 alpha vs beta: is any Green-minus-Brown or timing return alpha, and do rates explain the holdout?

BOTTOM LINE. No return in this project shows alpha that holds up.

- Green-minus-Brown (GB) is static factor beta: mostly short value, plus short profitability and investment in FF5. Its alpha is insignificant under every model in every window with enough data: full, post-2010, validation, COVID, 2022-2024 and holdout.
- Over the last 12 to 18 months GB lost 15% to 20% a year. Some factor models give it large negative alphas with NW(6) p below 0.05. Those fits have only 4 to 14 degrees of freedom, and none is significant with classical OLS standard errors.
- The timing strategies have no significant post-2010 alpha under any model.
- A traded 10-year Treasury factor (BOND) does not explain the holdout:
  - adding BOND and UMD leaves every holdout alpha negative;
  - rates moved holdout returns by at most about half a point a year, and the sign depends on the attribution method;
  - the rolling hedge still loses when it also hedges BOND.
- The strategies' beta-timing component is negative, not positive. The Always-short Brown benchmark, which does no timing, shows the same term.
- The COVID gain came from being short the hedged Brown leg while the lagged FF3 hedge left exposure open, mainly to market and size. It is not residual alpha and not attention timing.

All of this supports "Do not implement".

Table references in [brackets] are files `outputs/tables/M3_alpha_beta_<name>.csv`. Percentages are annualized (mean x 12). t-stats are Newey-West(6) with the team's estimator (Bartlett kernel, pinv, no df correction). Unless stated otherwise, p-values are two-sided from t(n-k).

## 1. Question

Charishma's Part B:
- Is any return from the Green-minus-Brown trade or the team's timing strategies alpha? Or is it static or time-varying beta (value, momentum, duration, market)?
- Does a rates/duration channel explain the 2022-08 to 2026-07 holdout?

## 2. Data

- **GB** = equal-weighted Green (Fun, RlEst, Drugs, Telcm, Fin) minus equal-weighted Brown (Util, Ships, Aero, Steel, BldMt), built from the team FF49 value-weighted file.
  - Leg excess returns use the team FF3 RF.
  - I also use the FF3-hedged Brown leg `R^B_t - b_{t-1}'f_t` (team 60-month hedge, unscaled). This is what the strategies trade.
- **Strategies**: the six team timing strategies (Original/Pure x 3m/6m holds; Continuous raw/pure) and Always-short Brown.
  - Net returns come from `run_pipeline()` for two baselines. The team baseline uses the defaults. The corrected baseline interpolates the Oct-2025 CPI gap and lags attention and the purification controls by one month.
  - Every strategy can hold a position from 1999-03 on (the first Pure positions are set in 1999-02). The strategies' "full" sample is therefore 1999-03 to 2026-07 (329 months). For GB and the legs it is 1970-01 to 2026-07 (679 months).
- **Factors**: Mkt-RF, SMB, HML and RF from the team FF3 file, used for CAPM, FF3 and the hedge. The FF5 models use Ken French FF5 (2x3) and UMD, Aug 2026 vintage.
- **BOND** = `y_{t-1}/12 - D_{t-1}(y_t - y_{t-1}) + 0.5 C_{t-1}(y_t - y_{t-1})^2 - RF_t`, built from GS10. D and C are the modified duration and convexity of a 10-year semiannual par bond at `y_{t-1}`.
  - It is computed by M8's `build_bond`, imported from `modules/M8_frozen_pre2010/run.py`, not re-implemented.
  - It matches an independent M3 implementation to 2.8e-17 and M8's own check table to 6e-17 [bond_validation_summary].
- **Ferson-Schadt instruments** z_{t-1} [instruments_lagged]:
  - term spread GS10 - TB3MS, credit spread BAA - AAA and the GS10 level, each a monthly average known at the end of the month;
  - CPI inflation, 12-month log change, lagged one month, with the Oct-2025 gap interpolated;
  - CFNAI, lagged one month.
- **Robustness data**:
  - BOND_eom: the same construction from end-of-month US Treasury 10-year par yields (1990-02 on, cached by `fetch_treasury.py`);
  - Damodaran annual 10-year T-bond returns (histretSP.xls);
  - d10y = change in GS10;
  - COM = IMF all-commodity index return (PALLFNFINDEXM).

BOND validation [bond_validation_summary, bond_annual]:
- 2022 total return was -15.0%, the worst calendar year since 1954. Damodaran has -17.8%, also its worst. The gap arises because GS10 is a monthly average, while Damodaran uses year-end yields.
- Annual correlation with Damodaran is 0.991 over 1954-2025 (72 years) and 0.987 over 1993-2025 (M8's figure). Mean absolute difference is 0.85 pp.
- The monthly return is within 5.4 bp of exact dirty-price repricing (correlation 0.99999). Mean modified duration is 7.56 (range 5.04 to 9.68).
- 1970-2026: excess return 2.16%/yr, volatility 6.95%, Sharpe 0.31.
- AR(1) is 0.31 because GS10 averages daily yields. BOND_eom has AR(1) 0.08.
- Mean BOND excess return: -3.68%/yr in the holdout and -8.37%/yr over 2022-2024 [key_numbers].

## 3. Method

Primary tests. These were pre-specified in the `run.py` docstring by the interrupted first run and are unchanged. Everything else is exploratory or robustness.
- (i) GB's BOND loading in FF5+UMD+BOND, full 1970-2026 and post-2010. Two tests, Holm.
- (ii) For each of the six timing strategies:
  - the holdout alpha under FF3+UMD+BOND versus FF3;
  - the joint Wald F test that the UMD and BOND loadings are zero.
  - Both baselines; Holm within each family of six.
- (iii) Lewellen-Nagel decomposition with backward rolling 36-month betas (months t-36..t-1) on Mkt-RF, SMB, HML, UMD and BOND.
  - The statistic is the annualized beta-timing term `sum_k cov(beta_k,t, f_k,t)` over post-2010.
  - Inference uses a circular block bootstrap (block 12, 5,000 reps, rows resampled jointly), with p = 2 min(P>0, P<0).
  - Family of seven: GB plus the six corrected-baseline strategies, Holm.

Other steps:
- **Q1**: CAPM, FF3, FF3+BOND, FF3+UMD+BOND, FF5, FF5+UMD and FF5+UMD+BOND, fitted to GB, each leg, the hedged Brown leg and every strategy in both baselines.
  - Periods: full, post2010, validation, holdout, covid, inflation_rates, last18, last12 [exposures, bond_loadings, leg_exposures].
  - GB's last18 and last12 alphas are also reported with NW(2) and classical OLS standard errors [gb_short_window_alpha].
- **Q2**:
  - holdout alphas before and after BOND, with the return contributions b x mean(f) of BOND and UMD [holdout_alpha];
  - replication of the exchange-1 fact-check with d10y, then with BOND in its place [factcheck_rates, hedged_brown_holdout];
  - the full team pipeline rerun with BOND (and UMD) in the rolling 60-month hedge [bond_hedge_rerun]. The BOND overlay costs 5 bp, like Mkt-RF; a 25 bp variant is also run;
  - the team macro-state regression with BOND controlled [macro_state].
- **Q3**:
  - Ferson-Schadt: `r_t = a + sum_k (b_k + c_k'z_{t-1}) f_k,t + e_t`.
    - Betas on Mkt-RF, HML, UMD and BOND are conditional; SMB is unconditional.
    - The instruments are standardized with expanding, past-only moments.
    - The joint test of c = 0 (q = 20) uses the HAC Wald statistic with two bootstrap nulls: a fixed-design block bootstrap, and a wild block bootstrap (restricted residual kept in its own month, Rademacher sign per 12-month block).
    - The asymptotic HAC Wald over-rejects badly: the bootstrap null 95th percentile is 71 to 241, against 31.4 for chi2(20) [ferson_schadt, fs_boot_seeds].
  - Lewellen-Nagel with 36- and 24-month backward windows. Robustness versions use centered windows (ex post), "structural" betas (position x (Brown beta - hedge beta)) and BOND_eom [ln_decomposition, primary_iii].
  - Exploratory: the same decomposition for `D = strategy - pi x Always-short Brown`, with pi = the ratio of mean |position| over 2010-2026. This isolates the attention-specific part. Mean and in-period factor-alpha tests of D are also run [ln_vs_benchmark].
- **Q4**: Treynor-Mazuy (f, f^2) and Henriksson-Merton (f, max(f,0)) for Mkt-RF, HML and BOND, single-factor and with FF3+UMD+BOND controls [timing_tests, timing_tests_summary].
- **Q5**: attribution of Pure 6m and Continuous pure.
  - Realized gross return = leakage + residual. Leakage is `sum_k h_{t-1}(beta_k,t - hedge beta_k,t-1) f_k,t`, the hedging error of the lagged hedge.
  - beta_t comes from centered 36-month (or 24-month) windows of the Brown leg.
  - An in-period regression version is also reported [attribution, attribution_monthly, position_overlap]. Factor means by period are in [factor_means].

Block bootstraps use block = min(12, max(2, n // 8)).
- Every window with n >= 96, including all primary tests, keeps the team's 12.
- The holdout (n = 48) uses 6 and COVID (n = 24) uses 3. With 12, COVID draws had only two blocks and degenerate p-values.
- The Ferson-Schadt bootstraps use 12 throughout (n >= 151).

## 4. Primary results

### (i) Is Green long duration relative to Brown? Over 1970-2026 yes, modestly; since 2010, no [primary_i, leg_exposures, gb_rolling60_betas]

| GB, FF5+UMD+BOND | n | BOND loading | t | p | Holm p |
|---|---|---|---|---|---|
| 1970-01 to 2026-07 | 679 | 0.132 | 2.60 | 0.0095 | 0.019 |
| 2010-01 to 2026-07 | 199 | 0.088 | 0.60 | 0.549 | 0.549 |

- The full-sample loading splits into Green +0.068 (t 2.10) and Brown -0.064 (t -1.67). Post-2010 it is Green +0.097 (t 1.10) and Brown +0.008 (t 0.09).
- A 0.13 loading on a bond with duration 7.6 is roughly one year of duration per unit of GB. That is small next to GB's value tilt: FF3 HML -0.233 (t -4.63) full and -0.298 (t -5.74) post-2010 [exposures].
- The rolling 60-month BOND beta (FF3+UMD+BOND) changes sign [key_numbers]:
  - it averages 0.134 for windows ending 1970-2009;
  - it averages -0.203 for windows ending 2010-2021 (minimum -0.60 at 2020-01);
  - it averages +0.380 for windows ending 2022-2026 (maximum 0.65 at 2022-05).
- During COVID, GB's BOND loading was 1.24 (t 5.87, 24 months). Over the last 18 months, the Brown leg's was +1.59 (t 2.28, 10 df) [exposures]. These short-window loadings are unstable.
- With BOND_eom over 1990-2026, GB's loading is 0.082 (t 1.19), against 0.129 (t 1.65) for the GS10 BOND over the same months [bond_eom_robustness]. The significant full-sample loading therefore rests partly on 1970-1989 and on GS10 averaging.

### (ii) Do the holdout FF3 alphas lose significance once BOND and UMD are added? No: they get slightly more negative [holdout_alpha]

| Strategy (n = 48) | Team: FF3 alpha (t) | Team: FF3+UMD+BOND alpha (t, p, Holm p) | Wald UMD=BOND=0 p | Corrected: FF3 alpha (t) | Corrected: FF3+UMD+BOND alpha (t, p) | Wald p |
|---|---|---|---|---|---|---|
| Orig 3m | -4.03% (-2.19) | -4.43% (-2.31, 0.026, 0.155) | 0.342 | -2.16% (-1.90) | -2.40% (-1.97, 0.056) | 0.507 |
| Pure 3m | -2.21% (-1.93) | -2.45% (-1.97, 0.056, 0.164) | 0.410 | -2.16% (-1.90) | -2.40% (-1.97, 0.056) | 0.507 |
| Orig 6m | -2.28% (-1.66) | -2.94% (-2.14, 0.038, 0.164) | 0.248 | -1.97% (-1.30) | -2.27% (-1.40, 0.169) | 0.728 |
| Pure 6m | -2.71% (-1.94) | -3.22% (-2.16, 0.037, 0.164) | 0.262 | -1.97% (-1.30) | -2.27% (-1.40, 0.169) | 0.728 |
| Cont raw | -0.76% (-1.98) | -0.86% (-2.21, 0.033, 0.164) | 0.394 | -0.58% (-1.33) | -0.64% (-1.36, 0.181) | 0.342 |
| Cont pure | -0.54% (-1.79) | -0.62% (-2.00, 0.052, 0.164) | 0.680 | -0.59% (-1.33) | -0.64% (-1.33, 0.192) | 0.377 |

In the corrected baseline, the Original and Pure rules had identical holdout returns (same positions in all 48 months), so their rows coincide [position_overlap].

- In the team baseline, raw p < 0.05 goes from 1 of 6 under FF3 to 4 of 6 under FF3+UMD+BOND. After Holm, none is significant (smallest 0.155).
- No Wald test rejects UMD = BOND = 0 (p 0.25 to 0.73; Holm 1.0). In the corrected baseline, no alpha is significant before or after.
- Adding UMD and BOND lowers the alphas by 0.05 to 0.66 pp.
  - The strategies' holdout BOND loadings are negative but insignificant (team -0.02 to -0.14, t -0.87 to -1.69), and BOND earned -3.68%/yr.
  - By regression, BOND exposure therefore added +0.06 to +0.51 pp/yr in the team baseline and +0.06 to +0.23 pp/yr in the corrected baseline [holdout_alpha, contrib_BOND_FF3+UMD+BOND].
  - The structural attribution in Section 7 gives the opposite sign, with BOND leakage of -0.02 to -0.20 pp.
  - Either way, rates moved holdout returns by half a point a year at most. The net losses were 0.5% to 3.8% a year.
- FF5+UMD+BOND gives -0.70% to -4.74% (team) and -0.85% to -3.18% (corrected) [holdout_alpha].
- With BOND_eom, team alphas are -0.9% to -5.1% (t -1.77 to -2.75) and corrected alphas -1.0% to -3.4% [bond_eom_robustness].

The exchange-1 hypothesis is confirmed with the traded factor [factcheck_rates, hedged_brown_holdout]:
- The exchange-1 check reproduces exactly. The hedged Brown leg's holdout d10y loading is 0.0010 (t 0.05). Team alphas after FF5+UMD+d10y+COM run from -0.67% to -4.78%: -2.30% to -4.78% for the four discrete rules (t -2.01 to -2.31).
- Swapping BOND for d10y like for like (BOND+COM), the hedged Brown leg's holdout BOND loading is -0.009 (t -0.04). With BOND alone it is -0.015 (t -0.07), and with FF5+UMD+BOND +0.013 (t 0.07).
- Team alphas after FF5+UMD+BOND+COM are -0.68% to -4.81% (discrete rules -2.32% to -4.81%, t -2.04 to -2.32).
- The FF3-hedged Brown leg's holdout alpha is +2.82% (t 0.95) under FF3 and +2.86% (t 0.90) under FF3+UMD+BOND. The short side therefore lost on residual Brown performance, not on rates.

Rates in the hedge do not rescue the strategies [bond_hedge_rerun]. Holdout net return (t), with the rolling hedge re-estimated on each factor set:

| Hedge | Corrected 3m | Corrected 6m | Cont raw | Cont pure | Team Orig 3m | Team Pure 6m |
|---|---|---|---|---|---|---|
| FF3 (team) | -2.57% (-2.27) | -1.84% (-1.30) | -0.48% (-1.09) | -0.50% (-1.13) | -3.82% (-2.29) | -3.04% (-2.25) |
| FF3+BOND | -2.30% (-1.93) | -1.44% (-1.00) | -0.43% (-0.97) | -0.45% (-1.02) | -3.79% (-2.16) | -2.77% (-1.96) |
| FF3+UMD+BOND | -2.66% (-2.22) | -1.86% (-1.35) | -0.54% (-1.19) | -0.57% (-1.23) | -4.01% (-2.30) | -2.91% (-2.01) |

- The 60-month BOND hedge beta, estimated before the holdout, adds a BOND exposure the Brown leg did not have. Under the FF3+BOND hedge, the residual holdout BOND loadings are -0.03 to -0.20 (team Orig 6m -0.20, t -2.22).
- A 25 bp BOND cost and a hedge on month-end-yield BOND give the same picture (corrected 3m -2.35% and -2.49%).

The macro-state finding with BOND controlled [macro_state, macro_state_high_rates.tex]:
- M3 reproduces the team's result exactly (raw attention, High rates): slope off -0.063, slope on +0.166 (t 1.65), difference 0.229 (t 1.83, p 0.068). In the team's own table, normal p = 0.067 and Holm p = 0.585.
- BOND variants:
  - with BOND(t+1) as a control, the difference is 0.231 (t 1.86);
  - on the FF3+BOND-hedged residual it is 0.224 (t 1.74);
  - with FF3+UMD+BOND it is 0.192 (t 1.51).
- BOND therefore does not drive the result. It was never significant after multiple testing.
- It vanishes with real-time (corrected, lagged) signals: difference 0.035 (t 0.32, p 0.75), purified 0.041 (p 0.72).
- All 47 holdout months are high-rate months, so the holdout cannot test it.

### (iii) Is beta timing significant? The term is negative, and the no-timing benchmark shows it too [primary_iii, ln_vs_benchmark, ln_decomposition]

Post-2010, backward 36-month betas, % per year:

| Asset | Mean | Conditional alpha | Average beta x average factor | Beta-timing term (95% CI) | p boot | Holm p |
|---|---|---|---|---|---|---|
| GB | -1.79 | 0.72 | -0.78 | -1.72 (-3.75, 0.57) | 0.146 | 0.146 |
| Orig 3m (corr.) | 0.73 | 1.55 | 0.17 | -0.99 (-1.55, -0.34) | 0.002 | 0.014 |
| Pure 3m (corr.) | 0.75 | 1.69 | 0.12 | -1.06 (-1.64, -0.42) | 0.001 | 0.006 |
| Orig 6m (corr.) | 1.19 | 2.05 | 0.18 | -1.04 (-1.87, -0.09) | 0.030 | 0.089 |
| Pure 6m (corr.) | 1.37 | 2.40 | 0.04 | -1.07 (-1.97, -0.07) | 0.032 | 0.089 |
| Cont raw (corr.) | 0.32 | 0.78 | 0.11 | -0.57 (-0.99, -0.16) | 0.003 | 0.014 |
| Cont pure (corr.) | 0.38 | 0.85 | 0.13 | -0.60 (-1.04, -0.17) | 0.003 | 0.014 |
| Always-short Brown (reference) | 1.05 | 1.96 | 0.43 | -1.35 (-2.48, -0.09) | 0.035 | not in family |

- Four of six strategy terms are significant after Holm, and all six are negative. The strategies' betas were high when factor returns were low, which subtracted about 0.6% to 1.1% a year. GB's term is not significant.
- This is not attention timing:
  - Always-short Brown holds a position every month and shows the same term (-1.35%, p 0.035).
  - The FF3-hedged Brown leg has +1.94% (p 0.020) and the Brown leg itself +2.31% (p 0.014). Shorting the leg flips the sign.
  - Against the exposure-matched benchmark, D = strategy - pi x Always-short Brown, the corrected strategies' timing terms are -0.47% (p 0.018), -0.48% (0.009), -0.16% (0.41), -0.11% (0.54), -0.27% (0.010) and -0.28% (0.008). That is at most half a percent a year, and also negative. D's post-2010 mean is insignificant (t 0.46 to 1.41).
- BOND contributes about half the total term (-0.36% to -0.60% for the corrected strategies).
- The sign is robust; the significance is not:
  - 24-month windows: -0.60% to -1.54%, p 0.008 to 0.042.
  - Structural betas: -0.20% to -0.91%, 2 of 6 at p < 0.05.
  - BOND_eom: -0.32% to -0.54%. The 3-month holds and the continuous rules have p 0.037 to 0.070, and the 6-month holds 0.24 to 0.35. Pure 3m sits at 0.053, so how many fall below 0.05 depends on the bootstrap seed.
  - Centered (ex post) windows: all near zero (-0.13% to +0.22%).

## 5. Other results

Is any return alpha? [exposures, gb_short_window_alpha]
- GB has no significant alpha under any of the seven models in the full, post-2010, validation, COVID, 2022-2024 or holdout windows:
  - full 1970-2026: -0.6% (CAPM, t -0.40) to +2.2% (FF5+UMD, t 1.60, p 0.11);
  - post-2010: -1.2% to -0.2%;
  - validation: -0.6% to +1.7%;
  - holdout: -3.8% to -4.8% (|t| < 1).
- Factor adjustment raises GB's measured alpha above its raw mean (-0.5%/yr full, -1.8% post-2010), because GB is short value, profitability and investment. In FF5 over the full sample the loadings are HML -0.11 (t -1.90), RMW -0.15 (t -1.90) and CMA -0.25 (t -2.80). With UMD added they are -0.14, -0.15 and -0.23.
- The last 12 to 18 months, the window the brief asks about:
  - GB's raw mean is -14.7%/yr over the last 18 months and -19.9%/yr over the last 12 (NW(6) t -1.83 and -2.19).
  - With NW(6) standard errors, 7 of 14 factor-model alphas have p < 0.05:
    - last 18 months: FF3 -19.2% (t -2.79, p 0.014), FF3+BOND -19.2% (p 0.021), FF3+UMD+BOND -16.1% (p 0.033);
    - last 12 months: FF3 -32.8% (t -5.65, p 0.0005), FF3+BOND -32.8% (t -10.0, p 2e-5), FF3+UMD+BOND -25.3% (p 0.011), FF5+UMD+BOND -39.3% (p 0.046).
  - These fits have 4 to 14 df, and NW(6) on 12 to 18 observations is unreliable. With NW(2), 5 of 14 have p < 0.05. With classical OLS standard errors none does (|t| 0.82 to 1.67, p 0.155 to 0.44).
  - They are exploratory and not adjusted for multiple testing.
  - Read them as: Brown beat Green by a wide margin over the last year, and the factor models do not explain it. The sample is too short to call that alpha. It is also the wrong sign for a Green-minus-Brown trade.
- Timing strategies, post-2010: alphas range from -0.04% to 1.44% under FF3, FF3+UMD+BOND and FF5+UMD+BOND, and every t is below 1.8.
  - The only t above 2 come from the design sample (validation 2010-2022). For example, corrected Pure 6m has 2.34% (t 2.54) under FF5+UMD+BOND.
  - That is the in-sample result the holdout failed to confirm.

Ferson-Schadt conditional alpha [ferson_schadt, fs_boot_seeds]:
- Conditional alphas are close to the unconditional ones:
  - GB: full 0.77% (t 0.57) against 0.99% (t 0.74); post-2010 0.35% (t 0.17).
  - Corrected strategies, post-2010: 0.29% to 1.67% (t 0.76 to 1.91; Pure 6m p 0.058). None is significant at 5%.
- Joint test that all instrument interactions are zero (c = 0), fixed-design bootstrap p:
  - GB: 0.073 (full) and 0.159 (post-2010).
  - Corrected strategies, post-2010: 0.066, 0.038, 0.170, 0.121, 0.034 and 0.039.
- Three reasons not to trust the fixed-design p-values:
  - That scheme resamples residuals across months with the regressors held fixed. This breaks the link between residual size and position size: the 3-month holds have no position in 116 to 124 of the 199 post-2010 months, and the continuous rules' positions vary strongly in size [position_overlap].
  - The fixed-design p also moves with the seed. Across five seeds it ranges 0.038 to 0.051 for Pure 3m, 0.034 to 0.041 for Cont raw and 0.039 to 0.046 for Cont pure.
  - The classical nested F (0.038 and 0.024 for the continuous rules) assumes homoskedasticity.
- The wild block bootstrap keeps each month's residual in its own month and flips signs by 12-month block:
  - corrected strategies: 0.603, 0.397, 0.524, 0.485, 0.558 and 0.554 (0.40 to 0.62 across seeds);
  - GB: 0.086 (full) and 0.274 (post-2010).
- There is therefore no robust evidence that any strategy's betas vary with the macro instruments. GB's full-sample test is borderline under both schemes (0.07 to 0.09 across seeds).
- Standardizing the instruments in-window instead gives conditional alphas within 0.4 pp in the full and post-2010 windows (0.5 pp at most in any window).
- With intercept dummies, the holdout conditional alpha is -4.4% (p 0.013) for team Orig 3m and -2.8% (p 0.039) for team Pure 3m. For the corrected baseline it is -1.4% to +0.1% (p >= 0.27). Conditioning betas on macro state does not explain the holdout.

Timing tests [timing_tests_summary, timing_tests]. There are 1,080 exploratory tests, with 129 at p < 0.05.
- Mkt-RF: 2 (HM) and 3 (TM) of 90 multifactor tests at p < 0.05, about the chance rate.
- BOND: 7 of 90 each for TM and HM. None survives BH within its group of 90.
- HML: 21 (HM) and 28 (TM) of 90, all positive (convexity). 16 and 21 survive BH within their groups.
- Pooled BH over all 1,080 tests leaves 48 survivors: 45 HML tests and 3 BOND tests. The 3 BOND survivors are team-baseline 3-month holds in the 48-month holdout, all positive, with q = 0.041.
- The HML convexity is shared by the Always-short Brown benchmark (TM t 3.24 over 1999-2026), so it is a property of the hedged Brown leg, not of attention.
- GB has no timing ability. Its only tests at p < 0.05 are:
  - HM Mkt-RF over the full sample (t -2.11, a negative coefficient);
  - BOND in two windows of 48 and 151 months, with opposite signs.

## 6. The COVID gain: beta leakage, not alpha, and not attention timing

- Position overlap [position_overlap]. In 2020-2021 the corrected Pure 6m strategy held the Always-short Brown position in all 24 months, and team Pure 6m in 23 of 24. Their COVID return (corrected 6.87%/yr) is the benchmark's return (6.87%/yr).
- Attribution, corrected Pure 6m, COVID [attribution, factor_means]:
  - structural centered 36-month betas: net 6.87% = leakage 4.76% (Mkt 1.97, SMB 2.14, HML 1.49, UMD -0.50, BOND -0.35; p 0.037) + residual 2.21% (t 1.27, p 0.22) - cost 0.11%;
  - 24-month betas: leakage 6.26% (Mkt 2.59, SMB 3.53, HML 0.72, UMD -0.81, BOND +0.23; p 0.006) and residual 0.71% (p 0.72);
  - in-period FF3+UMD+BOND regression: factor part 6.38% (Mkt 3.34, SMB 1.79, HML -0.76, UMD -0.17, BOND +2.19) and residual 0.49% (t 0.24);
  - Continuous pure: net 3.10%, leakage 2.18% (p 0.069), residual 1.12% (t 1.23).
- Which exposures earned the gain:
  - Market and size are the contributors on which all three methods agree.
  - The short-Brown position did carry momentum and duration exposure that the FF3 hedge did not cover. Within COVID, FF5+UMD+BOND gives UMD 0.31 (t 4.49) and BOND 0.76 (t 2.29), with alpha 1.4% (t 0.59) [exposures].
  - Momentum added nothing: UMD earned -0.58%/yr in 2020-2021, and its contribution is negative under every method.
  - Duration's contribution depends on the method (-0.35, +0.23 or +2.19 pp).
- Relative to predetermined betas the COVID gain looks like alpha, and that is because of the lag:
  - backward 36-month Lewellen-Nagel gives a conditional alpha of 8.3% (p boot 0.034), and 8.9% (p 0.024) for the Always-short Brown benchmark [ln_decomposition];
  - Ferson-Schadt with a COVID dummy says the same: Pure 6m 7.2% (p 0.002), benchmark 6.1% (p 0.026).
  - Real-time betas did not see the COVID shift in Brown's exposures. The ex-post, within-window exposures explain most of the gain.
- The 3-month holds beat the exposure-matched benchmark in COVID [ln_vs_benchmark]:
  - D = 5.4% and 5.8%/yr (t 2.35, 3.15);
  - 3.0% and 3.4% after in-window factors (t 1.67, 1.79; p 0.11, 0.09).
  - These come from 24 months, with 13 to 15 of them in position, among thousands of exploratory tests.

## 7. Holdout attribution

[attribution], structural centered 36-month betas:
- Corrected Pure 6m: net -1.84% = leakage -0.24% (p 0.74) + residual -1.14% (t -0.86) - cost 0.46%.
- Team Pure 6m: residual -2.19% (t -1.75), leakage -0.39%.
- Continuous pure (corrected): residual -0.51% (t -1.32), leakage +0.13%.

The holdout loss is therefore residual (non-factor) Brown performance plus costs, not factor leakage. Duration was immaterial: BOND leakage was -0.02% to -0.20% in this attribution, and the regression contribution was +0.06% to +0.51% (Section 4(ii)).

Relative to the exposure-matched always-short benchmark, the corrected timing rules lost more in the holdout [ln_vs_benchmark]:
- D = -2.1% for the 3-month holds (t -2.23 to -2.28);
- D = -1.1% for the 6-month holds (t -1.44 to -1.51).

## 8. Robustness summary

| Check | Effect on conclusions |
|---|---|
| BOND from month-end par yields (1990+) [bond_eom_robustness] | (i) weaker (GB 1990-2026 0.08, t 1.19); (ii) unchanged, holdout alphas more negative; (iii) timing term smaller, p 0.037 to 0.070 for four strategies and 0.24 to 0.35 for the 6-month holds |
| 24-month windows, structural betas, centered windows [ln_decomposition] | timing term negative or about zero in every version; never positive and significant |
| BOND cost 25 bp; UMD in hedge [bond_hedge_rerun] | holdout losses unchanged in sign and size |
| Expanding vs in-window instrument standardization [ferson_schadt] | conditional alphas within 0.4 pp (full, post-2010); 0.5 pp at most in any window |
| Fixed-design vs wild block bootstrap for the Ferson-Schadt joint test; five seeds [ferson_schadt, fs_boot_seeds] | fixed-design p 0.03 to 0.23 for the corrected strategies, wild p 0.40 to 0.62: no robust beta variation |
| GB short-window alphas with NW(2) and classical OLS standard errors [gb_short_window_alpha] | the nominally significant last12/last18 alphas are not significant with OLS standard errors |
| Independent re-computation (statsmodels HAC, hand-coded rolling OLS) | GB BOND 0.1319 (t 2.603), team Orig 3m holdout alpha -4.43% (t -2.31), Pure 3m and benchmark decompositions all reproduce exactly |
| Adversarial verification (independent code, `verify/`) | every decision-relevant number reproduces; see Section 12 |

## 9. Implications for the verdict

"Do not implement" is strengthened.
1. The inherited GB spread is a value tilt with a small, unstable duration tilt. It has no alpha to harvest in any window with enough data. The only nominally significant GB alphas are negative, come from the last 12 to 18 months, and are not significant with classical standard errors.
2. The holdout loss is not a rates accident. Rates moved the strategies' holdout returns by half a point a year at most, with a sign that depends on the attribution method. The losses survive BOND and UMD in both the regressions and the hedge.
3. The strategies earn no beta-timing premium. The measurable timing term is a drag that the always-short benchmark also bears. The macro instruments do not robustly move the strategies' betas either.
4. The team's COVID gain was earned by simply being short the hedged Brown leg: the 6-month rules matched the benchmark month by month. It came mostly through market and size exposure that the lagged FF3 hedge failed to neutralize.
5. The team's "slope turns positive in high-rate months" result is not about duration and does not survive real-time signal timing.

## 10. Caveats

1. GS10 is a monthly average of daily yields, so BOND is smoothed (AR(1) 0.31) and partly realized a month early: BOND_t correlates 0.58 with BOND_eom_{t-1}. The month-end version exists only from 1990, and it weakens (i) and (iii).
2. Short windows have few degrees of freedom: holdout 48, COVID 24, last18 18, last12 12 observations. NW(6) on 12 to 24 observations is unreliable (Section 5 shows how much the last12/last18 t-stats move with the standard error). The FF5+UMD+BOND fits on last12 have 4 df and should be ignored.
3. Rolling-window betas estimated from monthly returns are noisy. The Lewellen-Nagel split depends on the beta estimator; the identity itself is exact for each estimator (gap < 1e-15).
4. Centered-window attribution uses future data, and in-window fitting can move some residual into leakage. The in-period regression and 24-month versions bracket it.
5. The ledger has 6,360 tests: 33 primary, 737 robustness and 5,590 exploratory. It now includes the factor loadings of GB and the legs and the strategies' UMD loadings. Only the primary tests have pre-set families and Holm adjustments.
6. The primary list was written in the docstring by the interrupted first run, which says it predates every M3 result. I could not verify that from file timestamps, and I did not change it.
   - After the first run I changed only exploratory parts: the Ferson-Schadt standardization and bootstrap, the added benchmark and fact-check tables, the adaptive bootstrap block (which does not affect any test with n >= 96) and the BOND import from M8 (identical to 3e-17).
   - After verification I added only exploratory or robustness outputs. Every previously published number is unchanged (Section 12).
7. Data and timing assumptions:
   - Brown and Green membership uses a static emissions snapshot.
   - FF5 and UMD are the Aug 2026 Ken French vintage, while the hedge uses the team FF3 file.
   - The corrected baseline's one-month publication lag for EMV is an assumption, not a verified release calendar.
   - The interpolated Oct-2025 CPI uses the Nov-2025 print (released mid-December 2025). It enters the inflation instrument for the Dec-2025 return, so one value is about three weeks early.

## 11. Output files

- Code:
  - `/home/hashim/projects/GA/project/research/modules/M3_alpha_beta/run.py` (entry: `cd /home/hashim/projects/GA/project/research && uv run python modules/M3_alpha_beta/run.py`, about 250 s);
  - `m3lib.py` (helpers; imports M8's `build_bond`; `ferson_schadt` has the fixed-design and wild bootstraps);
  - `fetch_treasury.py` (caches month-end par yields);
  - `data/` (Treasury par yields 1990-2026, Damodaran histretSP.xls);
  - `verify/` (the verifier's independent scripts).
- Tables in `/home/hashim/projects/GA/project/research/outputs/tables/`, prefix `M3_alpha_beta_`:
  - primary tests: primary_i, holdout_alpha (.tex), primary_iii, ln_post2010.tex;
  - exposures: exposures, bond_loadings, leg_exposures (.tex), gb_short_window_alpha, factor_means;
  - rates and the holdout: factcheck_rates, hedged_brown_holdout, bond_hedge_rerun (.tex), bond_hedge_comparison_{team,corrected}_{FF3_BOND,FF3_UMD_BOND}, macro_state, macro_state_high_rates.tex;
  - conditional alpha and timing: ferson_schadt (.tex), fs_boot_seeds, instruments_lagged, ln_decomposition, ln_vs_benchmark, timing_tests (.tex), timing_tests_summary;
  - attribution: attribution (.tex), attribution_monthly, position_overlap;
  - BOND: bond_monthly, bond_annual, bond_validation_summary, bond_validation.tex, bond_eom_robustness, gb_rolling60_betas;
  - bookkeeping: key_numbers (1,990 quoted numbers with source table and locator) and tests_ledger (6,360 rows).
  - All .tex tables compile with tectonic.
- Figures in `/home/hashim/projects/GA/project/research/outputs/figures/` (.pdf and .png):
  - `M3_alpha_beta_rolling_betas`: GB's rolling 60-month BOND and HML betas, stacked, with NW 95% bands;
  - `M3_alpha_beta_decomposition`: Lewellen-Nagel components by period for GB, Pure 6m, Continuous pure and Always-short Brown;
  - `M3_alpha_beta_holdout_alpha_bond`: holdout alpha under FF3, FF3+BOND and FF3+UMD+BOND with t(n-k) 95% intervals, both baselines;
  - `M3_alpha_beta_attribution`: leakage by factor, residual and cost by period;
  - `M3_alpha_beta_bond_validation`: annual BOND against Damodaran and the month-end construction.

## 12. Response to verification

I accept all six required fixes. None changes a primary result.

How the changes were checked:
- After the code changes, `run.py` was rerun (exit 0, about 250 s).
- Every previously published CSV was compared with a pre-change copy, cell by cell. The 28 tables and the 4,781 original ledger rows are identical (maximum difference 0), apart from added columns.
- The changes add columns, tables and ledger rows only.

**Fix 1 (GB is not insignificant in every window).** Accepted.
- The re-derived [exposures] numbers match the verifier: 7 of 14 last12/last18 fits have NW(6) p < 0.05, with 4 to 14 df.
- I added [gb_short_window_alpha], which reports the same estimates with other standard errors:
  - with NW(2), 5 of 14 have p < 0.05;
  - with classical OLS standard errors none does (|t| 0.82 to 1.67).
- The bottom line, Section 5 and Section 9.1 now say:
  - there is no significant GB alpha in any window with enough data;
  - the last 12 to 18 months show a large negative, fragile, exploratory alpha.
- The opening now reads "No return in this project shows alpha that holds up", which covers the negative short-window GB alpha.
- While re-deriving I also corrected two small errors: GB's post-2010 range is -1.2% to -0.2% (FF3+BOND -1.20%), not -1.1% to -0.2%, and GB's full-sample CAPM t is -0.40, not -0.41.

**Fix 2 (COVID gain not earned through momentum; duration method-dependent).** Accepted. Re-derived from [attribution] and the new [factor_means]:
- UMD earned -0.58%/yr in 2020-2021.
- UMD contributed -0.50 (structural 36m), -0.81 (24m) and -0.17 pp (in-period regression).
- BOND contributed -0.35, +0.23 and +2.19 pp.
- Market contributed +1.97, +2.59 and +3.34 pp, and size +2.14, +3.53 and +1.79 pp.
- The bottom line, Section 6 and Section 9.4 now name market and size as the channels and state that momentum added nothing and duration depends on the method.

**Fix 3 ("rates helped" is method-dependent).** Accepted.
- `holdout_alpha.csv` now carries `contrib_BOND_FF3+UMD+BOND` = 12 x b_BOND x mean(BOND).
- That contribution is +0.06 to +0.51 pp (team) and +0.06 to +0.23 pp (corrected). The structural BOND leakage is -0.02 to -0.20 pp.
- Sections 4(ii), 7 and 9.2 now say rates were immaterial either way (at most about half a point a year, against net losses of 0.5% to 3.8%).

**Fix 4 (Ferson-Schadt joint test not robust).** Accepted and implemented.
- `m3lib.ferson_schadt` now also runs a wild block bootstrap under the null: the restricted residual stays in its own month and is multiplied by a Rademacher sign per 12-month block. It uses a separate RNG stream, so the fixed-design p-values are unchanged.
- [ferson_schadt] gains `boot_wald_c_wild_p`, and the .tex table has a wild-p column.
- [fs_boot_seeds] repeats both bootstraps for GB and the corrected strategies over five seeds.
- My wild p-values are 0.40 to 0.60 for the corrected strategies post-2010 (0.40 to 0.62 across seeds), and 0.086 and 0.274 for GB. The verifier had 0.38 to 0.62, 0.085 and 0.28; the differences are seed noise.
- Section 5 now reads "no robust evidence that any strategy's betas vary with the macro instruments". It reports both p-values and the seed ranges, and notes that the classical F assumes homoskedasticity.
- One detail differs: I count 116 to 124 zero-position months (position h_{t-1} earning month t) for the 3-month holds post-2010, against the verifier's 115 to 123. This is most likely a one-month alignment difference and does not matter.

**Fix 5 (ledger completeness).** Accepted, with one qualification. Added rows:
- 32 + 32 for the 24-month structural attribution (residual and leakage, robustness);
- 48 + 48 for the mean and in-period alpha of D (all periods, both baselines);
- 1,232 factor loadings (every loading of GB and the three leg series, including the quoted HML, RMW and CMA loadings, and the strategies' UMD loadings);
- 3 GS10-BOND comparison rows for the BOND_eom months;
- 28 baseline-hedge mean rows and 84 post-hedge BOND loadings for the hedge reruns;
- 54 wild-bootstrap rows;
- 14 classical-OLS short-window GB alphas.

The qualification: the in-period regression residual (for example COVID t 0.24) was already in the ledger. It is the same regression as `Q1.alpha.<strategy>|<baseline>|FF3+UMD+BOND|<period>`, and `run.py` now asserts the equality. A new `Q5.attr_residual_regression` row is added only for pre_covid, the one window Q1 lacks (4 rows).

The ledger now has 6,360 rows (33 primary, 737 robustness, 5,590 exploratory), and caveat 5 is updated.

**Fix 6 (labels).** All three accepted:
- (a) The like-for-like BOND+COM swap gives -0.009 (t -0.04). The BOND-only -0.015 (t -0.07) is now labelled as such.
- (b) BOND_eom timing p-values are 0.037 to 0.070 for the 3-month holds and continuous rules and 0.24 to 0.35 for the 6-month holds. Pure 3m is at 0.053, so the count below 0.05 is flagged as seed-dependent.
- (c) FF5-alone loadings are HML -0.11, RMW -0.15, CMA -0.25. The -0.14, -0.15, -0.23 set is labelled FF5+UMD.

Further corrections found while re-deriving:
- The old text said every BH survivor among the timing tests is an HML test. Pooled BH over all 1,080 tests leaves 45 HML and 3 BOND survivors (team 3-month holds, holdout, q 0.041). Within each group of 90, no BOND test survives. Section 5 now reports both.
- "In-window standardization within 0.4 pp" holds for the full and post-2010 windows (maximum 0.36 pp). In a validation window it reaches 0.52 pp, and the text now says so.
- Caveats 1 and 7 now include two timing points from the verifier's Section 3: GS10 BOND is partly realized a month early (correlation 0.58 with BOND_eom_{t-1}), and the interpolated Oct-2025 CPI is about three weeks early for one instrument value.
