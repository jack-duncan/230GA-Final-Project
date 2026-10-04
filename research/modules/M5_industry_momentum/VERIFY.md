<!-- Reconstructed by the orchestrator from the verifier's structured return (the harness blocked the verifier's own report write). -->
# Verification

## Round 1

all_confirmed: False

### Confirmed claims
- Execution: run.py runs end to end (exit 0, 10m26s) and writes 33 CSV and 13 .tex tables plus 4 figures (PDF and PNG). A rerun reproduces every one of the 33 earlier CSV tables to within 1e-9 (deterministic).
- Independent re-implementation: I did not import any module code. I wrote my own ranking, drift, turnover, Newey-West (Bartlett kernel, 6 lags, no small-sample correction), bootstrap with a different seed, and a separate cvxpy formulation of the optimizer (quad_form). My primary net returns match returns_monthly to 1e-16 and turnover to 4e-16. My optimizer paths match the builder's to 3e-5 per month (correlation 1.00000) for b = none, 0, -1 and -2.
- Look-ahead and timing: the signal at formation t uses months t-11..t-1 and earns t+1 (a 12-2 window relative to the holding month). The optimizer's covariance and residual vol use t-59..t, cap weights use month t, and the DM bear flag is lagged one month. The 'next return exists' eligibility filter has no effect: my book without it is identical. No BE/ME or macro data is used. The only look-ahead is the static emissions snapshot, which the builder discloses.
- Sample, annualization, costs: 679 months (1970-01 to 2026-07), 48 industries eligible for the first 6 formation months, 12x mean and sqrt(12)x sd. Costs are 10 bp times full-count one-way turnover (fully replacing both legs = 4), charged on the trade at t against the t+1 return. Newey-West uses 6 lags with normal p-values; my NW t-stats equal statsmodels' to 6 decimals.
- Headline 1 CONFIRMED: net 8.52%/yr, vol 18.00%, Sharpe 0.47 (t=3.47). FF5+UMD alpha is 1.74% (t=1.09, p=0.274) full sample and 1.86% (t=0.71, p=0.481) post-2010. UMD beta 0.99 (t=30.5), R2 0.67, correlation with UMD 0.81. CAPM, FF3 and FF5 alphas are 9.45/10.92/10.25% (t 3.92/4.60/3.96), and the HML loading is -0.32 (FF3) and -0.46 (FF5).
- Headline 2 CONFIRMED: alpha break-even is 23.9 bp (full) and 24.5 bp (post-2010); mean break-even is 78 and 63 bp. Worst month 2009-04 at -38.75%: short leg +39.40%, UMD -34.36%, March-May 2009 -42.88%. Max drawdown -60.3% (peak 2008-06, trough 2012-01, recovered 2020-04). Holdout FF5+UMD alpha is negative in all 9 variants (primary -4.48%, t=-0.84).
- Cost and robustness CONFIRMED: FF5+UMD alpha is 2.99/2.36/1.74/-0.14% at 0/5/10/25 bp; turnover 12.47x a year, cost drag 1.25%. All 8 robustness rows (alpha, t, Sharpe; 1-0 turnover 38.4) are confirmed. Performance-table rows are confirmed for full, post-2010, holdout, last 18 and last 12 months. CAPM alpha last 18/12 months is -2.60%/-5.19% with betas 0.55/0.95. DM: B x M -0.53 (t=-2.94), B x U x M -0.02, bear-and-up months average -2.85% (n=55).
- Headline 3 numbers CONFIRMED by my own optimizer: unconstrained IR 0.555, alpha 2.17% (t=3.07), realized vol 6.95% against a 5.00% ex-ante target, turnover 2.92x, long WACI 0.159, mean c'h -0.094. b=0: dIR +0.010, CI [-0.010, +0.032], my bootstrap p 0.339 (builder 0.328), WACI -11.6%, alpha change +0.08% (t=1.01). b=-1: dIR -0.005, p 0.925, CI [-0.111, +0.097], WACI -60%. b=-2: dIR -0.284, p 0.040, 64 fallback months, WACI -82%. Optimizer minus equal-weight IR +0.082 (p 0.431). Holdout alpha -0.34% (t=-0.15).
- Carbon screens CONFIRMED: long WACI 0.179, short 0.195, market (41 covered) 0.277; long above market in 24.7% of months; 84% of long weight covered; post-2010 long 0.193 against market 0.192; holdout ratio 1.08. A8X: WACI 0.046 (-74%), Sharpe 0.456, dSharpe -0.017 (my p 0.674), alpha difference -0.15% (t=-0.20). A5X: -67%. B8X: Sharpe 0.481, alpha 2.10% (t=1.68). Across screens, max |dSharpe| is 0.026 and min p is 0.291. At least one Brown-5 industry is in the long leg in 60.5% of months.
- Headline 4 numbers CONFIRMED: Q4 primary INDMOM loading -0.062 (t=-1.94, p=0.053). GB's HML loading goes from -0.233 (t=-4.63) to -0.253 with INDMOM, and post-2010 from -0.298 to -0.306. GB time-series momentum slope 0.0069 (t=0.60). Short-Brown hold 3m/6m: HML -0.051 to -0.040 and -0.061 to -0.046 (22% and 25% absorbed); INDMOM loadings 0.038 (t=2.12) and 0.054 (t=2.59); correlations 0.21/0.22 post-2010 and -0.004/0.073 in the holdout. I rebuilt the team strategy with the orchestrator's separately tested lib/team_pipeline.py; it reproduces the team's 0.000696 return and 0.03255 volatility.
- Signal IC CONFIRMED: rank IC 0.054 (t=4.85) full sample, 0.030 in the holdout, -0.005 in the last 18 months.
- Ledger and multiple testing CONFIRMED: 335 rows, 4 primary and 331 exploratory, no duplicate IDs, no missing p-values. P1, P2 and Q4 ledger p-values equal my own recomputations. My own Holm and BH code matches the CSV (max difference 2e-15). Holm p is 0.823 for P1, P2 and Q3 and 0.211 for Q4. 24 exploratory tests have BH p<0.05. BH p for the unconstrained optimizer's alpha is 0.034.
- The overall 'Do not implement' verdict is supported: none of the discrepancies or overreaches changes it.

### Required fixes
1. NOTE ON FILES: FINDINGS.md does not exist on disk, so I verified the text relayed in primary_results. I did not write VERIFY.md: my instructions forbid report .md files, the same limit that stopped the builder. The per-claim verdicts are in this output and in modules/M5_industry_momentum/verify/verify_core_results.csv and verify_optimizer_results.csv. The orchestrator should save FINDINGS.md with the fixes below.
2. DISCREPANCY, Sec 8: 'Post-2010: -0.298, then -0.306 with INDMOM. With UMD instead of INDMOM: -0.256.' The -0.256 is the full-sample FF3+UMD HML loading. The post-2010 FF3+UMD HML loading is -0.323 (t=-6.16) (gb_hml_attribution, and my own regression gives -0.3229). Correct the number or move -0.256 into the full-sample sentence.
3. DISCREPANCY, Sec 6: 'Every variant has a negative holdout alpha, down to -10.79% (t=-3.02) for 6-1.' The most negative holdout alpha is the cap-weighted legs at -13.33% (t=-2.16). Window 6-1 has the most negative t, not the lowest alpha. Reword.
4. DISCREPANCY, headline 5 and Sec 7: the optimizer's full-sample alpha 'is not significant in any decade (largest t = 1.97, 2020-2026)'. That t is 1.965 with nominal NW p = 0.0494, which is below 0.05. Say it is significant at the nominal 5% level only in 2020-2026 (p=0.049) and not after the Benjamini-Hochberg (BH) adjustment (BH p=0.234).
5. OMISSION, Sec 7: report the optimizer's post-2010 numbers, a window the brief requires. X_unc FF5+UMD alpha is 3.12%/yr (t=2.18, p=0.029, BH p=0.224) and post-2010 IR is 0.696, against 0.43 for the equal-weight book. The verdict survives: validation t=1.78, holdout -0.34% (t=-0.15), and the IR difference versus equal weight is not significant (p=0.436).
6. OMISSION, Sec 10 BH-survivor sentence: 2 of the 24 BH<0.05 exploratory tests are not mentioned. (1) The primary book's COVID 2020-21 FF5+UMD alpha is 15.80%/yr (t=3.18, n=24, BH p=0.029). This COVID-only pattern mirrors the team's own result and deserves a sentence; note that 24 observations with 7 regressors makes the NW/normal p optimistic. (2) The 6-1 holdout alpha is -10.79% (t=-3.02, BH p=0.036).
7. MINOR DISCREPANCY, Sec 3 and last caveat: 'KF Aug-2026 vintage differs from the team file only in the final month' is wrong as stated. The two files differ in 54 months from 2020-07 on: revisions of at most 22 bp outside 2026-07, and up to 7.0 pp in 2026-07 across 26 industries (PerSv, Clths and BusSv are in that month's short leg). Reword to 'differs materially only in 2026-07'. The effect is small: 2026-07 net is -13.95% under KF against -14.18%, and it is still the 6th-worst month.
8. OVERREACH, Sec 9: 'A client who can hold UMD gets the same premium more cheaply.' Nothing in the module supports this. UMD here is a cost-free paper factor, and stock-level UMD usually costs more to trade than industry ETFs. Replace with: the book's net return is spanned by the gross paper UMD factor (beta 0.99, R2 0.67). Also note that the 24 bp break-even compares a net-of-cost book with a costless benchmark.
9. OVERREACH, headline 3 ('costs nothing measurable') and Sec 9 ('close to free'): (a) The Q3 primary bound b=0 is weak: it binds in 26.5% of months, cuts long WACI by only 11.6%, and was chosen after seeing that the unconstrained c'h averages -0.09, which biases the test toward 'no cost'. (b) At b=-1 the 95% CI for the IR change is [-0.110, +0.096], so the test cannot rule out losing about 20% of the 0.555 IR. (c) Post-2010, the equal-weight screens' Sharpes are 0.02-0.12 lower (B5X -0.120, B8X -0.110, B0X -0.071), and this was not bootstrapped. Reword to 'no detectable cost, with low power to detect an IR loss of about 0.1', and add the post-2010 qualifier to the screens headline or bootstrap the post-2010 differences.
10. OVERREACH, headline 4 and Sec 8 interpretation: the 22-25% of Short-Brown HML absorbed by INDMOM rests on exploratory loadings (t=2.12 and 2.59, BH p=0.228 and 0.106). With UMD also in the regression, INDMOM's t falls to 1.10 (hold 3m) and 1.22 (hold 6m), and UMD alone absorbs 26%. Call it a generic momentum tilt that does not survive multiple-testing correction, not an industry-momentum effect.
11. LEDGER COMPLETENESS: FINDINGS cites two inferential statistics that tests_ledger does not log: the Daniel-Moskowitz bear-state beta B x M (-0.53, t=-2.94, p=0.003; only the B x U x M term is logged) and the gross FF5+UMD alpha (2.99%, t=1.89; only 5 bp and 25 bp are logged). Add both, then recompute the BH adjustments and the '24 BH survivors' count.
12. MINOR: (a) The cost_breakeven holdout row shows breakeven_bp_alpha_ff5umd = 0.0 when the gross alpha is negative (-3.14%); report NaN or 'negative', not 0 bp. (b) run.py took 10m26s here, not 4-7 minutes; update the caveat. (c) The Q4 Short-Brown series inherit the team's same-month attention timing flagged in logs/replication.md; say so in the Q4 caveat. (d) The optimizer's 'binding share' depends on solver tolerance: 26.5% (builder) against 26.7% (my solve). Keep one decimal at most.

## Round 2

all_confirmed: False (text-only). Every number checked in round 2 is confirmed, all eleven substantive round-1 fixes (items 2 to 12) are resolved, and the rerun is deterministic. The fix text added three small wording inaccuracies (R2-1 to R2-3 below). They are text-only, change no number or conclusion, and need no rerun or re-verification once applied.

### What was run
- run.py: exit 0 in 4m17s wall time, inside the "4 to 10.5 minutes" now stated in the runtime caveat. It writes 37 CSV and 13 .tex tables and 4 figures (PDF and PNG). All 37 CSVs match the files on disk before the rerun to 1e-9, and all 13 .tex files are byte-identical, so the run is deterministic.
- Round-1 scripts, rerun unchanged:
  - verify/verify_m5_optimizer.py: 31 of 31 confirmed. My four optimizer paths (b = none, 0, -1, -2) are identical to round 1 (max difference 0) and match the builder's to 3.3e-5 a month (correlation 1.00000).
  - verify/verify_m5.py: every value it computes independently is identical to round 1 (max difference 0 outside the ledger rows); 164 rows confirmed. Its 7 DISCREPANCY rows all test old-text values that are hardcoded in the script and that the fixes deliberately changed: "most negative holdout alpha is 6-1", "KF differs only in the final month", post-2010 FF3+UMD HML -0.256, ledger rows 335, BH survivors 24, BH p of the X_unc alpha 0.034 (now 0.027 because the ledger grew), and "not significant in any decade". Each is resolved below. The ledger-completeness row changed from DISCREPANCY to confirmed. verify_core_results.csv now holds this rerun.
  - The 34 builder-table cells that the round-1 script reads back are unchanged from round 1 (max difference 0). This supports the builder's statement that no previously reported estimate changed. The pre-fix tables were overwritten before round 2, so a full cell-by-cell comparison was not possible.
- New independent script: verify/verify_m5_round2.py. It imports no module code and uses my own book, Newey-West, classic OLS with Student-t p-values, Holm and BH, bootstrap seeds, my round-1 optimizer paths, and lib/team_pipeline.py for the Short-Brown series. All 163 of its checks are confirmed. Results: verify/verify_round2_results.csv.

### Status of the round-1 required fixes
1. Files note: RESOLVED. FINDINGS.md and VERIFY.md are now on disk (saved by the orchestrator).
2. Sec 8, -0.256: RESOLVED. From my own regressions, the HML loadings are:
   - full sample: FF3 -0.233 (t -4.63); FF3+INDMOM -0.253 (t -5.27); FF3+UMD -0.256 (t -5.20)
   - post-2010: FF3 -0.298 (t -5.74); FF3+INDMOM -0.306 (t -5.76); FF3+UMD -0.323 (t -6.16)
   Each value is now in the correct sentence.
3. Sec 6, holdout alphas: RESOLVED. All 9 holdout alphas are negative. The lowest alpha is the cap-weighted legs at -13.33% (t -2.16), and window 6-1 has the most negative t (-10.79%, t -3.02). The new claim also checks out: the 6-1 classic OLS t is -1.61, Student-t p 0.116 (41 df).
4. Optimizer decade: RESOLVED. On my own optimizer path, the 2020-2026 alpha is 5.45% (t 1.965, p 0.049). This is the only decade with a nominal p below 0.05; the next lowest is the 1970s at 0.062. My own BH over the 416-row ledger gives 0.220, the value quoted.
5. Optimizer post-2010: RESOLVED. On my own path, the post-2010 alpha is 3.12% (t 2.18, p 0.029, BH p 0.195) and the IR is 0.696, against 0.429 for the equal-weight book. Validation alpha is 2.99% (t 1.78). One correction to my own round-1 item: the p = 0.436 I cited there was the full-sample IR comparison. The builder's new post-2010 bootstrap is the right test. It gives dIR +0.267, CI [-0.111, +0.657], p 0.155; my seed gives CI [-0.102, +0.632], p 0.159 (Monte Carlo difference). Its BH p is 0.417. The verdict text in Secs 7 and 9 matches.
6. BH survivors: RESOLVED.
   - COVID FF5+UMD alpha: 15.80%, NW t 3.18, classic OLS t 1.58 on 17 df (Student-t p 0.132), BH p 0.022 in the larger ledger.
   - 6-1 holdout: BH p 0.029.
   - "Next largest reported window is the 1990s, 5.89% (t 1.80)" and "no decade has |t| above 1.80": confirmed.
   - I also computed the other two COVID survivors: FF3 alpha NW t 3.03, OLS t 1.36 (p 0.189); FF5 alpha NW t 6.44, OLS t 1.99 (p 0.061). See R2-2.
7. KF vintage: RESOLVED. My own comparison of the two files:
   - 113 cells differ, in 54 months, starting in 2020-07.
   - Outside 2026-07 the largest difference is 0.22 pp.
   - In 2026-07, 26 industries differ, by up to 7.02 pp (PerSv).
   - The industries that move by more than 1 pp are exactly PerSv, Clths and BusSv, and all three are in that month's short leg.
   - Portfolio weights under the KF vintage equal the primary's in every month (max |dw| 0).
   - 2026-07 net return is -13.95% under KF against -14.18%, the 6th-worst month under both files.
8. "A client who can hold UMD": RESOLVED. The phrase is gone. Secs 5 and 9 give the spanning statement (UMD beta 0.99, R-squared 0.67), and Secs 5 and 10 say the break-even is measured against paper factors that pay no costs.
9. Carbon overreach: RESOLVED.
   - (a) b = 0 is now described as a weak test. On my own path it binds in 26.7% of months, long WACI is 0.141 (-11.6%), and the unconstrained mean c'h is -0.094.
   - (b) The b = -1 CI is quoted, with the statement that an IR loss of about 0.1 cannot be ruled out.
   - (c) The builder bootstrapped the post-2010 screen differences. I rebuilt all 10 screens with my own book and bootstrapped them with my own seed (table below).
   - Section 9 now reads "no detectable cost, low power" with the post-2010 qualifier.
   - I also checked the post-2010 frontier points in Sec 7 with my own optimizer paths: dIR +0.028 (p 0.133) at b = 0; -0.008 (CI [-0.187, +0.177], p 0.925) at b = -1; -0.318 at b = -2 (on its p-value, see Other checks).

   | Screen | Post-2010 dSharpe | Builder CI; p | My CI; p (own seed) |
   |---|---|---|---|
   | A0X | -0.021 | [-0.122, +0.094]; 0.708 | [-0.119, +0.090]; 0.696 |
   | A5X | -0.068 | [-0.188, +0.055]; 0.274 | [-0.190, +0.052]; 0.267 |
   | A8X | -0.036 | [-0.154, +0.093]; 0.562 | [-0.156, +0.091]; 0.562 |
   | B0X | -0.071 | [-0.240, +0.106]; 0.430 | [-0.244, +0.101]; 0.421 |
   | B5X | -0.120 | [-0.333, +0.081]; 0.258 | [-0.330, +0.081]; 0.253 |
   | B8X | -0.110 | [-0.335, +0.105]; 0.334 | [-0.332, +0.102]; 0.324 |
   | A5M | -0.067 | [-0.130, -0.010]; 0.027 | [-0.132, -0.009]; 0.030 |
   | A8M | -0.028 | [-0.095, +0.044]; 0.425 | [-0.093, +0.046]; 0.429 |
   | B5M | -0.117 | [-0.214, -0.026]; 0.017 | [-0.212, -0.022]; 0.018 |
   | B8M | -0.107 | [-0.239, +0.023]; 0.108 | [-0.228, +0.022]; 0.098 |

   The table supports the text:
   - Every screen's post-2010 Sharpe is below the primary's, by 0.021 to 0.120.
   - The smallest p among the X screens is 0.258 (0.253 with my seed).
   - The two M top-5 screens are nominally significant but not after BH: my BH p-values are 0.195 and 0.153.
   - B5M's post-2010 alpha difference is -1.99% (t -2.10).
   - Full sample: max |dSharpe| is 0.026; the smallest p is 0.291 (0.287 with my seed); A0X -0.010 (p 0.74), B0X +0.001 (p 0.98).
   - B0X post-2010: -0.071 (p 0.42).
10. Q4 overreach: RESOLVED. From my own regressions:
   - INDMOM loadings: 0.038 (t 2.12, hold 3m) and 0.054 (t 2.59, hold 6m); with UMD also in the regression, t falls to 1.10 and 1.22.
   - UMD alone absorbs 25.7% and 26.3% of the HML loading.
   - BH p of the loadings: 0.205 and 0.090.
   - Correlation NW t: 2.34 and 2.79, with BH p 0.160 and 0.056.
   Sec 8's interpretation and Sec 9 now call this a generic momentum tilt.
11. Ledger: RESOLVED.
   - 416 rows: 4 primary, 412 exploratory, 30 tagged [loading]; no duplicate IDs or missing p-values.
   - The DM B x M rows (book and UMD) and the gross (0 bp) alphas are now logged.
   - My own Holm and BH (with and without the loading rows) equal the CSV to machine precision. Holm p is 0.823 for P1, P2 and Q3 and 0.211 for Q4.
   - 37 tests have BH p below 0.05 with the loadings and 26 without. The 26 are exactly the 37 minus the 11 loadings, and the Sec 10 category counts (4, 4, 1, 11, 2, 3, 1) are correct; R2-1 concerns only how the "11" is described.
   - Every BH p quoted in FINDINGS matches my BH to 3 decimals.
12. Minor items: all RESOLVED.
   - (a) The holdout alpha break-even is now NaN with a note. Gross holdout alpha is -3.14%; mean break-even is 23.7 bp (quoted as 24).
   - (b) The runtime caveat is updated; my rerun took 4m17s.
   - (c) The caveat and Sec 4 now state the same-month attention timing. I rebuilt the lagged strategies with lib/team_pipeline.py (attention shifted one month). They return 0.73% and 1.19% a year post-2010, against 0.07% and 1.34%. INDMOM loadings are 0.037 (t 1.99) and 0.057 (t 2.70), with t falling to 1.27 and 1.50 when UMD is added. FF3 HML loadings are -0.030 (t -1.19) and -0.049 (t -1.92). For these Original strategies the lagged series are identical to the project's corrected baseline (CPI interpolation and control lags affect only the Pure strategies; max difference 0).
   - (d) Sec 4 now says "about 26.5%" and notes the tolerance dependence; my solve gives 26.7%.

### Other checks (nothing new broke)
- The table list in Section 11 matches the disk exactly: 37 CSVs, with the 13 .tex files marked correctly. All 4 figures are present.
- Holdout correlations of GB with INDMOM and with UMD are -0.291 and -0.294 (NW t -1.87 and -1.89).
- Rank IC: 0.033 post-2010; holdout t 1.14.
- FINDINGS.md contains no em dashes.
- Information only, no fix needed: the post-2010 bootstrap p at b = -2 is 0.185 with the builder's fixed seed, which I reproduced exactly. Over 200 other seeds it averages 0.168 (sd 0.005, max 0.181), so the builder's seed falls at the high end of Monte Carlo noise. This does not matter, since the value is far from 0.05. Note that every paired bootstrap in run.py uses the same seed, so all post-2010 comparisons share one resample index matrix and their Monte Carlo errors are correlated. That is legitimate.

### Required fixes (round 2; text-only, no rerun needed)
R2-1. Sec 10 (Multiple testing caveat), miscount. The bounds from +1 to -1.5 are 10; the 11th surviving optimizer alpha is the unconstrained book (M5-Q3-optalpha-X_unc-full_1970).
- Replace: "the optimizer's full-sample alphas at every bound from +1 to -1.5 (11);"
- With: "the optimizer's full-sample alphas for the unconstrained book and at every bound from +1 to -1.5 (11);"

R2-2. Sec 10 (Multiple testing caveat), imprecise. The COVID FF5 alpha's t falls by a factor of 3.2 (6.44 to 1.99), not by half. The four ratios are 2.2, 3.2, 2.0 and 1.9, and all four Student-t p-values lie between 0.06 and 0.19.
- Replace: "The COVID and 6-1 results rest on NW t-statistics that roughly halve with classic OLS standard errors (sections 5 and 6), so they are not robust discoveries."
- With: "The COVID and 6-1 results rest on NW t-statistics that fall by half or more with classic OLS standard errors (the COVID FF5 alpha's t goes from 6.44 to 1.99), and all four have classic Student-t p-values between 0.06 and 0.19 (sections 5 and 6; column p_alpha_ols_t in alphas and robustness), so they are not robust discoveries."

R2-3. Sec 2, overstatement. Ten of the 30 [loading] rows are neither cited nor summarized in FINDINGS: GB's three holdout HML loadings, the three brown_eps HML loadings, and the four HML loadings of the attention-lag strategies with INDMOM or UMD added.
- Replace: "The tests ledger (tests_ledger) has 416 rows: 4 primary and 412 exploratory, of which 30 are factor loadings cited in this file (tagged "[loading]" in the note)."
- With: "The tests ledger (tests_ledger) has 416 rows: 4 primary and 412 exploratory, of which 30 are descriptive factor loadings (tagged "[loading]" in the note); 10 of these are logged for completeness but not cited here (GB's holdout HML loadings, the brown_eps HML loadings, and the attention-lag strategies' HML loadings with INDMOM or UMD added)."

Optional, not required: in Sec 8's timing check, after "The Q4 conclusion does not depend on the timing.", add: "For these Original strategies the one-month-lag version is identical to the project's corrected baseline, since the CPI interpolation and control lags affect only the purified strategies."
