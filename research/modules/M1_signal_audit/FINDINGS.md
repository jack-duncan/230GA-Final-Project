<!-- Saved by the orchestrator from the builder's returned text (subagent report writes are blocked by the harness). Source agent a06cb6634f2111caa. -->
# M1 signal audit: what the team's "climate-transition attention" signal measures

Table names are in brackets after each number, without the M1_signal_audit_ prefix. All tables are in outputs/tables.

Run: cd /home/hashim/projects/GA/project/research && uv run python modules/M1_signal_audit/run.py (about 20 to 60 seconds, depending on machine load).

This version applies the fixes from the independent verification (VERIFY.md). The last section says what changed and why.

## Question
What does the team's "climate-transition attention" signal actually measure, and do genuine climate-concern measures behave differently?

## Data
- Team inputs come from common.load_team(): macro.attention, FF49 value-weighted industry returns, and the team's FF3 factors and RF.
- Legs: Green = Fun, RlEst, Drugs, Telcm, Fin. Brown = Util, Ships, Aero, Steel, BldMt. Both are equal-weighted.
  - Membership comes from the team's single, undated emissions-intensity cross-section, applied to every month back to 1985 (see Caveats).
- EMV_env = FRED EMVENRGYENVREG, 1985-01 to 2026-08.
- EMV_overall = FRED EMVOVERALLEMV, 1985-01 to 2026-08.
- VIX = monthly mean of daily VIXCLS, 1990-01 to 2026-08. The partial month 2026-09 is dropped.
- EMV_env_share = EMV_env / EMV_overall; mean 0.0136 [share_summary; series in data/derived/attention_measures.csv].
  - My reading of the BBDK construction is that this is the fraction of volatility-related articles that mention energy or environmental regulation terms. I did not check this against article counts.
- MCCC = Ardia et al. Media Climate Change Concerns index, aggregate, 2025 update, 2003-01 to 2025-06.
- MCCC_transition = equal-weighted mean of five MCCC topic columns: Climate Legislation/Regulations, Carbon Tax, Carbon Credits Market, Renewable Energy, Agreements/Actions.
- CPU = Gavriilidis climate policy uncertainty index, 1987-04 to 2025-09.
- RATE = -diff(GS10), in percentage points.

## Lag convention
- Each measure for month t is built from month-t news (or month-t daily VIX) and is treated as known at the end of month t.
- A signal dated t is always paired with the month t+1 return.
- rolling_z uses the trailing 60 months including t, following the team convention.
- The extreme threshold at t is the 80th percentile of z over months up to t-1, with at least 60 past values.
- The real-time AR(1) shock at t uses coefficients estimated only on pairs ending at t-1, with at least 36 pairs.
- The Brown-leg hedge replicates the team: a rolling 60-month FF3 regression with alpha and betas lagged one month.
- The high-VIX and high-EMV flags compare month t with the expanding median of months up to t-1.
- The contemporaneous tests (Q6a) are pricing regressions with same-month factors, not trading rules.
- The indices are not point-in-time vintages. The "lag1" robustness check adds one more month of publication lag.
- No macro releases and no Ken French BE/ME data are used in this module.

## Pre-specified primary tests (fixed before looking at results)
- Q2: HAC Wald test and R2 of z_EMV_env on z_VIX + z_EMV_overall, full sample.
- Q3: Fisher exact test of the zero rate, 2021-10 to 2026-08 versus 1985-01 to 2021-09.
- Q4: Fisher exact test of the high-VIX share in crossing months versus other months, full threshold sample. "High VIX" means above its expanding past-only median.
- Q5: corr(z_MCCC, z_EMV_env) and corr(z_CPU, z_EMV_env), each tested by the NW(6) t of the slope of the standardized measure on the standardized team z. Holm over the 2 tests was added after verification.
- Q6a: slope of GB on a 1-sd real-time MCCC shock and on a 1-sd CPU shock, no controls, each shock's full sample, Holm-adjusted over the 2 tests.
- Q6b: IC of {z_MCCC, shock_MCCC, z_CPU, shock_CPU} for next-month GB and for the next-month Brown FF3 residual, full overlapping sample, Holm-adjusted over the 8 tests.
- Everything else is labelled robustness or exploratory in tests_ledger.csv. The Q3 counterfactuals and the Q4 dependence-robust p-values were added after verification and are labelled robustness or exploratory.

## Method (plain text)
- Signal: z_t = (x_t - mean(x_{t-59..t})) / sd(x_{t-59..t}), with x = log(1 + level).
- State: state_t = 1{z_t > q80(z_s, s <= t-1)}.
- Crossing: crossing_t = state_t AND NOT state_{t-1}. A crossing opens a 3- or 6-month Short-Brown hold.
- Shock: shock_t = m_t - a_hat - b_hat * m_{t-1}, where m_s = a + b * m_{s-1} is fitted on s <= t-1.
- Brown residual: e_t = (R_brown_t - RF_t) - alpha_{t-1} - beta_{t-1}' F_t, with F = FF3 (the variant adds RATE).
- IC: z(y_{t+1}) = c + IC * z(s_t) + u.
  - Both variables are standardized within the window.
  - The window is chosen on the signal date.
  - NW(6) standard errors.
  - The "ctrl" variants add FF3 or FF3 + RATE dated t+1.
- Contemporaneous: GB_t = c + g * shock_t / sd(shock) + [FF3_t, RATE_t] + u, NW(6); g is in % per month per 1 sd.
- Correlation tests other than the two Q5 primaries: direction-free delta-method HAC test. With standardized a, b and r = corr(a, b), psi_t = a_t b_t - (r/2)(a_t^2 + b_t^2) and se(r) = sqrt(NW(6) long-run variance of psi / n). The test gives the same p whichever series is listed first.
- Counterfactuals for the rule after 2021-10 (Q3):
  - Frozen scaling: for t >= 2021-10, z_t = (x_t - m*) / s*, where m* = 0.281 and s* = 0.171 are the mean and sd of x over the 60 months to 2021-09. The threshold is rebuilt past-only on this z path. A variant keeps the team's own threshold path.
  - Zeros as missing: zero months are dropped before the rolling z-score, over either the last 60 calendar months or the last 60 nonzero months, with at least 12 nonzero values. A zero month then has no z and cannot enter. The threshold is rebuilt past-only.
- Minimum EMV_env needed to cross at t: the root of z_t(v) = threshold_t given the previous 59 months. z_t is strictly increasing in v above the past mean, so the root is exact.
- Q4 dependence-robust p-values:
  - Circular shift: rotate the crossing (or state) indicator by 12 to n-12 months, recompute the difference in flag shares, and report the two-sided share of rotations at least as extreme.
  - LPM: regress the 0/1 flag on the 0/1 event indicator with NW(12) errors.
- Ledger rule: a hypothesis reported in two tables (same series pair, or same signal and outcome, on the same sample) is recorded once. Every table row carries its ledger_test_id.
- Replication check [ic_replication]:
  - Team-signal IC on the Brown residual is -0.0915 in validation (n = 151) and 0.1234 in the holdout (n = 47). The team notebook prints the same values.
  - The team's 34 p80 months over 2010-01 to 2026-07 are reproduced exactly.

## Primary results

### Q1: identity
- 500 overlapping months, 1985-01 to 2026-08.
- 0 months differ; maximum absolute difference 0.0.
- Neither series has months the other lacks [identity].

### Q2: what the signal is made of
- Joint regression, 1992-12 to 2026-08, n = 405: R2 = 0.169 (HAC Wald F = 27.1, p = 8.8e-12).
  - z_VIX slope = -0.03 (t -0.35).
  - z_EMV_overall slope = 0.43 (t 5.07).
  - [decomposition_team_signal]
- In the full sample, VIX adds nothing once overall EMV is included (R2 0.168 with z_EMV_overall alone, 0.169 with both). The same holds before 2021-10 (t 0.16), but not in every subsample [decomposition]:
  - Validation (2010-01 to 2022-07, n = 151): z_VIX enters with a negative sign, slope -0.30 (t -2.51), and R2 rises from 0.126 to 0.166.
  - After 2021-10 (n = 59): z_VIX slope -0.28 (t -1.92); R2 0.245 to 0.281.
  - Holdout: t -1.13.
  - In every subsample the positive link between the signal and VIX runs through overall EMV (z_EMV_overall t between 3.2 and 5.4). Holding overall EMV fixed, extra VIX is associated with a lower team signal in validation.
- Joint R2 by subsample: pre-2021-10 0.161; validation 0.166; holdout 0.267; post-2021-10 0.281.
- Signal correlations [decomposition_correlations]:
  - With z_EMV_overall: 0.39 (n = 465, HAC p = 1e-12).
  - With z_VIX: 0.29 (n = 405, HAC p = 7e-5), falling to -0.001 after 2021-10 (n = 59).
- Level regressions, 1990-01 to 2026-08, n = 440 (R2 on overall EMV, on VIX, on both):
  - EMV_env level: 0.110, 0.042, 0.113.
  - log EMV_env on nonzero months (n = 390): 0.136, 0.066, 0.137 [decomposition].
- The share component:
  - Correlates 0.865 with the team signal (n = 465) [measure_correlations].
  - Correlates -0.05 with z_VIX (HAC p 0.36) and -0.03 with z_EMV_overall (p 0.56) [decomposition_correlations].
  - R2 on both = 0.005 [decomposition].
  - It is a cleaner measure of topic share, but it is not climate concern (see Q5).

### Q3: zero inflation
- Zeros: 12 of 441 months (2.7%) before 2021-10, against 39 of 59 (66.1%) after. Fisher odds ratio 69.7, p = 1.3e-32 [zero_counts].
- By period [zero_counts]:
  - Validation: 12/151.
  - Holdout: 31/48.
  - inflation_rates: 25/36.
  - last18: 9/18.
  - last12: 8/12.
- Trailing 24-month zero share: at or below 12.5% before 2021, peaking at 79.2% in 2024-02 [zero_share_24m].
- Zero months can never trigger the rule.
  - A zero is the smallest possible reading, so its z is negative, while the threshold never fell below 0.61 (range 0.61 to 0.99 over 1992-12 to 2026-08).
  - 0 of the 50 zero months in the threshold sample (1992-12 to 2026-08) were above the threshold [zero_mechanics].
- Window arithmetic, 2021-09 to 2026-07 [zero_window_arithmetic]:
  - The zero share inside the 60-month window rose from 0.033 to 0.633.
  - The window mean of log1p(EMV_env) fell from 0.281 to 0.142; the window sd rose from 0.171 to 0.241.
  - The z of a zero month moved from -1.58 to -0.59.
  - The expanding 80th-percentile threshold stayed put (0.809 to 0.800).
  - The minimum EMV_env needed to cross fell from 0.526 to 0.406.
- The holdout [zero_mechanics]:
  - Zero months: mean z -0.95, never above the threshold.
  - Nonzero months: mean z +0.95. 7 of 17 (41%) are above the threshold, against a mean z of 0.08 and 19% above in validation.
  - Fisher test of state against nonzero months in the holdout: p = 0.00026 (exploratory). This follows from zero months never triggering.
  - All 5 holdout crossings followed a zero month; in validation, 2 of 21 did.
  - Share of months inside a 6-month hold: 0.646 in the holdout against 0.642 in validation.
- Did the zeros change which months the rule traded? No [zero_counterfactual_summary, zero_counterfactual_holdout_nonzero]:
  - Team rule, holdout entries: 2023-04, 2024-06, 2025-02, 2025-09, 2025-11; 7 state months.
  - Window frozen at 2021-09: the same 5 entries and the same 7 state months. With the team's own threshold path: also identical. Across 2021-10 to 2026-08, 0 state or entry months differ.
  - Zeros as missing, last 60 nonzero months: the same 5 entries and 7 state months.
  - Zeros as missing, 60 calendar months: the same 5 entries. 6 state months; 2022-08 (inside the hold opened in 2022-07) drops out.
  - The entries were readings of 0.64 to 0.94. Each clears both the team's bar at that month (0.37 to 0.53 across holdout nonzero months) and the frozen pre-regime bar (0.518 to 0.521). No holdout reading lies between the two bars.
  - Of the 11 holdout nonzero months that followed a zero month, 6 did not trigger; their readings were 0.16 to 0.36.
  - "All 5 entries followed a zero month" is close to the base rate: 11 of 17 holdout nonzero months follow a zero. At that rate, P(5 of 5) = 0.113 one-sided (binomial two-sided p = 0.169).
  - Among holdout nonzero months, the state rate after a zero is 5/11 against 2/6 after a nonzero month (Fisher p = 1.0) [zero_entry_base_rate].
- Conclusion for Q3: the input is two-thirds exact zeros from 2021-10, and zero months can never trigger. The lower bar that the zeros created never mattered. The rule entered in the same holdout months it would have entered with pre-regime scaling, so the holdout losses cannot be attributed to the zero-driven window arithmetic.
- For the team's continuous IC test (not the rule), the holdout z is largely a zero/nonzero split: corr(z, 1{nonzero}) = 0.79 in the holdout against 0.42 in validation [zero_mechanics]. The holdout IC therefore largely compares months with and without any matching article. I did not test whether this explains the IC sign flip.

### Q4: crossings and volatility [crossings_vix_summary]
- Primary: 31 of 50 crossings (62%) are high-VIX months, against 48.9% of other months, 1993-01 to 2026-08. Odds ratio 1.71, Fisher p = 0.097.
  - Fisher treats persistent monthly flags as independent. The dependence-robust p-values are 0.113 (circular shift, 381 rotations) and 0.049 (LPM, NW(12)).
  - I read this as borderline: not significant under the pre-specified test, and just under 0.05 in one of the two dependence-robust versions.
- Robustness:
  - All 82 state months: 72.0% high-VIX against 45.0% (Fisher p = 1.3e-5; circular shift 0.0026; LPM 0.0001).
  - Crossings in high overall-EMV months: 88% against 64.5% (Fisher p = 0.0006). This link survives the dependence corrections: 0 of 382 rotations are as extreme (p < 0.003), and LPM p = 0.0003.
  - Since 2010: 23 of 26 crossings in high overall-EMV months (88.5% against 56.1%; Fisher p = 0.0012, circular shift 0 of 176, LPM 0.0001), but only 13 of 26 high-VIX (50% against 41.6%; Fisher 0.52, circular shift 0.53, LPM 0.34).
  - Holdout: 2 of 5 crossings high-VIX; 5 of 5 high overall-EMV (Fisher 0.57, circular shift 0.72; LPM 0.023, unreliable here because all 5 events are flagged).
- The full tables are in [crossings] and [crossings_post2010].

### Q5: genuine climate-concern measures [measure_correlations, q5_primary_robustness]
- Primary:
  - corr(z_MCCC, z_EMV_env) = -0.0004 (n = 235, 2005-12 to 2025-06, p = 0.996; Holm 0.996).
  - corr(z_CPU, z_EMV_env) = 0.123 (n = 427, 1990-03 to 2025-09, p = 0.037; Holm over the 2 primary tests 0.074).
- The CPU correlation is nominally significant but fragile:
  - Reverse regression direction: p 0.048. NW(24): p 0.050. Direction-free HAC(6): p 0.040.
  - It runs through overall volatility news. The partial correlation given z_EMV_overall is 0.05 (HAC p 0.36).
  - So CPU and the team signal share overall volatility news, not climate content.
- Correlations with EMV_env, own overlap, direction-free HAC p in brackets [measure_correlations_wide, measure_correlations]:
  - MCCC: level -0.04 (0.67), shock -0.15 (0.006).
  - CPU: level 0.15 (0.15), shock 0.13 (0.042).
  - MCCC_transition: level -0.00, z 0.07 (0.29), shock -0.10 (0.030).
- Correlations with VIX:
  - MCCC: level -0.04, z -0.07, shock -0.10.
  - CPU: level 0.07, z 0.15, shock 0.09.
- The share component against climate concern (robustness, direction-free HAC):
  - On the common sample 2006-02 to 2025-06 (n = 233): -0.01 with z_MCCC (p 0.89); 0.01 with z_CPU (p 0.94); 0.03 with z_MCCC_transition (p 0.66).
  - On own overlaps: -0.004 with z_MCCC (n = 235, p 0.96); 0.03 with z_CPU (n = 427, p 0.62).
- On the common sample, z_MCCC and z_CPU correlate 0.16, and z_MCCC and z_MCCC_transition correlate 0.88 [zsignal_corr_matrix_common].
- 12-month average standardized levels, 2003-01 to 2025-06 [standardized_measures_12m]:
  - With its exact zeros, EMV_env peaks at +0.96 sd in 2009-08 and sits between -1.16 and -0.08 sd over 2022-2024.
  - Over 2022-2024, MCCC runs 1.19 to 1.49 sd and CPU 0.88 to 1.39 sd.
  - The low 2022-2024 EMV_env level comes from the exact zeros, not from low readings.
    - With zeros excluded, the 12-month average of standardized nonzero readings runs -0.23 to +1.20 sd when at least 3 of the 12 months are nonzero (24 of 36 months have a value). It runs -0.05 to +0.35 sd when at least 6 are required (5 months have a value).
    - The 11 nonzero months of 2022-2024 average +0.37 sd [emv_nonzero_levels].
    - The median nonzero reading was 0.36 in 2022-2024, against 0.31 in the 60 months to 2021-09 and 0.24 over 1985-01 to 2021-09 [emv_nonzero_levels].
  - So the published series was at its lowest when climate concern was at its highest, but only because most months had no matching article. When there was one, the reading was typical or above typical.

### Q6a: contemporaneous Pastor-Stambaugh-Taylor test [contemporaneous]
| Shock | Sample | n | Slope (% per month per sd) | t | p | Holm p |
|---|---|---|---|---|---|---|
| MCCC (real-time AR1) | 2006-02 to 2025-06 | 233 | -0.093 | -0.49 | 0.62 | 0.62 |
| CPU (real-time AR1) | 1990-05 to 2025-09 | 425 | -0.160 | -1.23 | 0.22 | 0.43 |

Both slopes have the wrong sign relative to the predicted positive slope, and neither is significant.

### Q6b: predictive IC [predictive_ic]
Team hypothesis: IC > 0 for GB and IC < 0 for the Brown residual. All 8 primary tests are null.

| Signal | Outcome | Start | IC | t | p | Holm p |
|---|---|---|---|---|---|---|
| z_MCCC | GB | 2005-12 | -0.022 | -0.36 | 0.72 | 1.00 |
| z_MCCC | Brown residual | 2005-12 | 0.074 | 1.27 | 0.21 | 1.00 |
| shock_MCCC | GB | 2006-02 | 0.001 | 0.02 | 0.99 | 1.00 |
| shock_MCCC | Brown residual | 2006-02 | 0.020 | 0.29 | 0.77 | 1.00 |
| z_CPU | GB | 1990-03 | 0.027 | 0.58 | 0.56 | 1.00 |
| z_CPU | Brown residual | 1990-03 | -0.073 | -1.55 | 0.12 | 0.84 |
| shock_CPU | GB | 1990-05 | 0.038 | 1.02 | 0.31 | 1.00 |
| shock_CPU | Brown residual | 1990-05 | -0.079 | -1.77 | 0.077 | 0.62 |

## Robustness
- Q6a with controls:
  - FF3: MCCC -0.049 (t -0.30); CPU -0.177 (t -1.40).
  - FF3 + RATE: MCCC -0.024 (t -0.14); CPU -0.182 (t -1.43).
  - Full-sample AR(1) MCCC shock from 2003-02: -0.074 (t -0.47, n = 269).
  - MCCC_transition: -0.082 (t -0.43).
  - COVID window: MCCC 0.53 (t 0.96); CPU 0.28 (t 0.84).
  - All 68 Q6a robustness regressions have p > 0.05 [tests_ledger_summary].
- Is climate concern just rates? (direction-free HAC tests, exploratory):
  - Shock correlations with RATE: MCCC -0.12 (t -2.16, p 0.031); MCCC_transition -0.12 (p 0.063); CPU 0.04 (p 0.38) [measure_correlations].
    - MCCC concern shocks lean toward months when the 10-year yield rose, but the link is weak and is one of many exploratory tests.
  - RATE loadings in the GB regressions: |t| <= 1.69.
  - Brown residual hedged on FF3 + RATE: z_CPU -0.069 (t -1.46); shock_CPU -0.070 (t -1.59); z_MCCC 0.079 (t 1.40); shock_MCCC 0.034 (t 0.50).
- Validation versus holdout [ic_sign_stability]:
  - z_MCCC keeps its sign in both halves.
    - GB +0.006 / +0.114 (the sign the team hypothesis predicts).
    - Brown residual +0.058 / +0.016 (the wrong sign both times).
    - None is significant.
  - shock_MCCC flips sign: GB -0.015 / +0.078; Brown residual +0.042 / -0.115.
  - CPU is the only measure whose sign matches the team hypothesis in both halves for both outcomes:
    - z_CPU: GB 0.007 / 0.050; Brown -0.067 / -0.078.
    - shock_CPU: GB 0.025 / 0.163 (t 1.85); Brown -0.063 / -0.180 (t -1.93).
  - None of these is significant, and the holdout covers only 35 months for MCCC and 38 for CPU.
- One more month of publication lag: every primary IC stays insignificant.
  - shock_CPU on Brown: -0.034 (p 0.54).
  - z_MCCC on Brown: 0.078 (p 0.12).
  - All 110 Q6b robustness tests have p > 0.05.
- The common-sample (2006-02 to 2025-06) results in [predictive_ic] give the same conclusions.

## Exploratory
- The EMV family flips sign between validation and holdout:
  - z_EMV_env on GB: 0.182 (t 1.81) to -0.127.
  - z_EMV_env on Brown: -0.091 to 0.123 (this matches the team's result).
  - z_EMV_env_share on GB: 0.218 (t 2.62) to -0.118.
  - shock_EMV_env on Brown: -0.095 to 0.160 (t 2.38).
  - The share component carries the validation-period predictability, and it reverses in the holdout.
- 26 of 184 exploratory Q6b tests have p < 0.05 (14%) [tests_ledger_summary]. They overlap heavily and include tiny last12/last18 windows, e.g. last12 z_VIX IC -0.62 on 11 months. I read them as noise.
- An MCCC shock lifts both legs: Green excess +0.75% per sd (t 2.48), Brown excess +0.84% (t 2.22). This looks like a market effect; the MCCC shock correlates 0.14 with Mkt-RF (HAC p 0.010).

## Implications for the verdict
1. The report should not call the team signal "climate-transition attention".
   - About 17% of its variance is overall volatility news.
   - VIX adds nothing beyond overall EMV in the full sample and before 2021-10. In validation it enters with a negative sign (t -2.51).
   - The rest is a topic share unrelated to climate concern: -0.01 with z_MCCC (p 0.89) and 0.01 with z_CPU (p 0.94) on the 2006-02 to 2025-06 common sample.
2. The zero regime is a data problem, but it is not the explanation of the holdout losses.
   - Supported: from 2021-10 the input is two-thirds exact zeros, and zero months can never trigger.
   - Not supported: that the rule "traded a different signal" in the holdout. With pre-regime scaling, or with zeros treated as missing, it enters in the same 5 holdout months, on readings (0.64 to 0.94) that clear the pre-regime bar (0.526).
   - The holdout losses cannot be attributed to the zero-driven window arithmetic.
   - A replacement signal built on EMV_env would still inherit the zeros, and the report should flag them as a data-quality problem.
3. Genuine concern measures give null contemporaneous and predictive results for these legs (smallest Q6b Holm p = 0.62).
   - The one nominal link to the team signal (CPU, p 0.037) fails Holm (0.074) and comes through overall volatility news (partial r 0.05).
   - CPU's stable IC sign is weak and does not survive an extra month of lag.
4. Taken together, this supports "Do not implement". Any proposed replacement signal should be presented as untested or null, not as a fix.

## Caveats
- Leg membership (inherited from the team) uses one emissions-intensity cross-section with no documented date, source or units (see M4). It is applied to every month back to 1985.
  - The CPU tests from 1990 and the MCCC tests from 2005 therefore use a leg composition chosen with later information.
  - This is a look-ahead in the portfolio definition, not in the signal. It would bias toward finding a relation that holds for today's high emitters, and I still find none.
- Coverage:
  - MCCC ends 2025-06 and CPU ends 2025-09.
  - Their holdouts are 35 and 38 months.
  - Neither covers last12. Their last18 windows have only 5 (MCCC) and 8 (CPU) signal months, below the 10-observation minimum.
- Vintages:
  - The MCCC 2025 update and CPU are not point-in-time series; CPU is renormalized.
  - z-scores and standardized slopes are unchanged by a constant rescaling.
  - Real-time availability is assumed; the lag1 check addresses publication delay.
- The cause of the zero regime is not identified.
  - The 20 nonzero EMV_env_share values after 2021-10 range from 0.006 to 0.054 [share_summary], which is consistent with a handful of matching articles per month.
  - That reading is an inference, not something I checked.
- Limits of the Q3 counterfactuals:
  - They show that the entry months did not change. Because the entries and the lagged hedge are identical, the counterfactual holdout returns are identical too.
  - They do not show whether a differently designed signal would have avoided the losses.
- The zeros-excluded 12-month averages depend on how many nonzero months the window must contain. Both minimums are reported above.
- PST sort green and brown firms on MSCI environmental scores. The team's Green leg is low-emission but not green in that sense, so the Q6a null applies to these industry legs and does not refute PST.
- RATE comes from a monthly-average yield, so it is a smoothed proxy.
- NW standard errors come from statsmodels HAC, normal-based. The team IC and t-statistic replicate to four decimals.
- Ledger [tests_ledger]:
  - It holds 667 tests: 15 primary, 217 robustness and 435 exploratory.
  - 21 duplicate reports of the same hypothesis on the same sample are merged: 17 correlations and 4 identical ICs.
  - Holm correction is applied only within the primary families of Q5, Q6a and Q6b.

## Output files
- Code: modules/M1_signal_audit/run.py, modules/M1_signal_audit/helpers.py.
- Tables (outputs/tables, prefix M1_signal_audit_):
  - identity
  - ic_replication
  - decomposition
  - decomposition_team_signal (+ .tex)
  - decomposition_correlations (+ .tex)
  - zero_counts (+ .tex)
  - zero_mechanics (+ .tex)
  - zero_window_arithmetic (+ .tex)
  - zero_share_24m
  - share_summary
  - zero_counterfactual_summary (+ .tex)
  - zero_counterfactual_months
  - zero_counterfactual_holdout_nonzero (+ .tex)
  - zero_entry_base_rate
  - crossings
  - crossings_post2010 (+ .tex)
  - crossings_vix_summary (+ .tex)
  - measure_correlations
  - measure_correlations_wide (+ .tex)
  - q5_primary_robustness (+ .tex)
  - zsignal_corr_matrix_common
  - shock_corr_matrix_common
  - standardized_measures_12m
  - emv_nonzero_levels
  - contemporaneous
  - contemporaneous_summary (+ .tex)
  - predictive_ic
  - predictive_ic_summary (+ .tex)
  - ic_sign_stability
  - tests_ledger
  - tests_ledger_summary
  - key_numbers
- Figures (outputs/figures, pdf and png):
  - M1_signal_audit_emv_vs_vix
  - M1_signal_audit_zero_share
  - M1_signal_audit_standardized_measures: now also shows EMV_env with exact zeros excluded.
  - M1_signal_audit_rule_mechanics: now has a third panel with the frozen-scaling counterfactual.
  - M1_signal_audit_ic_by_period
- Derived data: data/derived/attention_measures.csv, 1985-01 to 2026-08.
  - Levels: EMV_env, EMV_overall, VIX, EMV_env_share, MCCC, MCCC_transition, CPU.
  - Real-time AR(1) shocks: *_shock.
  - Rolling z-scores: z_*.

## Response to verification
I re-derived each point with my own code before changing anything. I agree with all ten required fixes, and they are applied above. Where my numbers differ slightly from the verifier's, the reason is given here.

1. "Different signal / mechanical failure" claims: agreed and removed.
   - Reproduced: 5 identical holdout entries under frozen 2021-09 scaling, under frozen scaling with the team threshold, and under zeros-as-missing.
   - Reproduced: entry readings 0.64 to 0.94; 6 of 11 nonzero-after-zero months not triggering (0.16 to 0.36); base rate 11/17 and P(5/5) = 0.113.
   - The counterfactuals are now in run.py [zero_counterfactual_summary, zero_counterfactual_months, zero_counterfactual_holdout_nonzero, zero_entry_base_rate], and figure rule_mechanics has a counterfactual panel.
   - One nuance: with zeros as missing over 60 calendar months (rather than the last 60 nonzero months, the verifier's version), there are 6 state months, not 7. 2022-08 drops out, but it sits inside the hold opened in 2022-07, so no entry changes.
   - Both zeros-missing variants also drop one marginal pre-regime validation crossing (2015-07, z 0.801 against a threshold of 0.798).
2. Q6a CPU t: corrected to -1.23 (CSV -1.2347).
3. "VIX adds nothing": now qualified. Validation t = -2.51 (R2 0.126 to 0.166); after 2021-10, t = -1.92.
   - One nuance: it is not only a full-sample result. It also holds before 2021-10 (t 0.16), and the holdout is not significant (t -1.13). The text now says so.
4. MCCC sign stability: corrected. z_MCCC keeps its sign in both halves; only shock_MCCC flips.
5. "Lowest when concern was highest": qualified, and the zeros-excluded line is added to the standardized_measures figure.
   - The verifier's -0.23 to +1.20 sd range reproduces when at least 3 nonzero months are required in the 12-month window. The upper end is sensitive: with at least 6 it is -0.05 to +0.35 sd. Both are reported.
   - The verifier's "0.30 before 2021-10" matches the median over the 60 months to 2021-09 (0.306, which I round to 0.31). Over all of 1985-01 to 2021-09 the median is 0.24.
   - Either way the 2022-2024 median nonzero reading (0.36) is higher, so the point stands.
6. Ledger: agreed, and the duplication was wider than the 4 pairs flagged.
   - Deduplicating by hypothesis key (unordered series pair or signal/outcome, plus sample dates) found 17 duplicated correlations and 4 identical IC duplicates. The ICs are shock_MCCC and shock_MCCC_transition, whose full_overlap and common samples coincide.
   - Each is now recorded once. All non-primary correlations use a direction-free delta-method HAC test. For example, EMV_env vs VIX level (r = 0.205) now has one row with p = 0.0035, where the two directional versions gave 5.1e-5 and 0.038.
   - The two Q5 primaries keep their pre-specified slope test, so I am not switching tests after seeing results. The direction-free, reverse-direction and NW(24) versions and the partial correlation are robustness rows.
   - Added: ledger rows for the share-vs-MCCC and share-vs-CPU correlations, and Holm over the 2 Q5 primaries (CPU 0.074).
   - Ledger: 632 rows before, 667 now. 56 rows were added: 6 share correlations, 8 Q5 primary robustness rows, 40 Q4 dependence-robust rows and 2 Q3 base-rate rows. 21 duplicates were merged, a net change of 35 rows (632 + 56 - 21 = 667).
   - One consequence of the direction-free test: the exploratory MCCC shock vs RATE correlation (r = -0.12) moves from t -1.91 (slope direction) to t -2.16 (p 0.031). It is reported as such.
7. Q5 text: added. CPU p 0.037, Holm 0.074, reverse 0.048, NW(24) 0.050, direction-free 0.040; partial r given z_EMV_overall 0.05 (p 0.36).
8. Q4: dependence-robust p-values added for all 20 Fisher tests.
   - Primary: circular shift 0.113, LPM NW(12) 0.049, so it is now called borderline.
   - EMV_overall: 0 of 382 rotations (p < 0.003), LPM 0.0003.
   - My rotation count is 381 rather than the verifier's 380 because I include the upper bound n-12; that is why I get 0.1129 against 0.1132.
9. Leg-membership caveat: added.
10. FINDINGS.md: the harness blocks subagents from writing report files. This text is the full FINDINGS.md content for the orchestrator to save.
- Also fixed:
  - The minimum EMV_env needed to cross is now solved exactly. It is 0.526 in 2021-09 (the verifier's bisection value), not 0.527 from the old grid.
  - A rounding slip the verifier did not flag: the Q6a FF3 + RATE CPU t is -1.43 (CSV -1.4349), not -1.44.
