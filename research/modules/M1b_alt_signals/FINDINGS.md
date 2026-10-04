# M1b_alt_signals: the team machinery fed alternative attention measures

Run: `cd /home/hashim/projects/GA/project/research && uv run python modules/M1b_alt_signals/run.py` (about one minute; measured 45 s and 68 s; exits 0; all tables and figures regenerate).
All tables are in `outputs/tables/` with the prefix `M1b_alt_signals_`, and figures are in `outputs/figures/`. Each number below names its CSV. This version incorporates the independent verification (VERIFY.md); see section 12.

## Headline

- **Q1 (primary): no change. "Do not implement" stands.** Feeding the identical machinery a genuine climate-concern measure (MCCC or CPU) gives no positive holdout alpha with Holm p < 0.05 (smallest Holm p 1.00 over 40 primary tests). All six MCCC holdout alphas are negative. The team's validation alpha is specific to the EMV tracker family: EMV env. has 4 of 6 validation alphas with t >= 1.96, MCCC and CPU have 0 of 6 each, while EMV overall gets close to EMV env.
- **Q2 (placebo): by the pre-specified rule, the climate reading of the COVID gain fails**, but the outcome is carried by the 6-month and continuous rules and depends on timing. EMV overall reproduces the gain in 4 of 6 rules under real-time timing (Original 6m, Pure 6m, both continuous) and 6 of 6 under team timing. For Original 3m, the team's headline COVID number, the volatility placebos fall short under real-time timing, EMV overall reaches 77% under team timing, and the climate-policy index CPU matches it under both.
- **The COVID gain is mostly a good period to be short the Brown residual.** A signal-free always-short position earns 4.54% (t 1.96), 71% of the EMV env. Original 3m alpha, and the rule's paired edge over it is +1.84% (t 0.87). The Original 3m result is one 24-month window with about 13 held months, half of the real-time gain comes from March and April 2020, inference is exploratory (n = 22 to 24, NW(6)) and there is no holdout support. It is not a basis for implementation, but it cannot be attributed to the pandemic alone.

## 1. Question

1. **Q1.** Our team's strategy trades a Short-Brown position when "attention" crosses its expanding 80th percentile. That attention series is FRED EMVENRGYENVREG, the Baker-Bloom-Davis-Kost equity-market-volatility tracker for Energy and Environmental Regulation. If the identical machinery is fed a genuine climate-concern measure instead, does the result change? The two measures are the Ardia et al. Media Climate Change Concerns index (MCCC) and Gavriilidis' Climate Policy Uncertainty index (CPU).
2. **Q2.** Our team reports a COVID-window gain (Original 3m: FF3 alpha 6.03%, t = 3.21). Does a pure volatility placebo (VIX, or the overall EMV tracker) reproduce it? If it does, the climate reading of that gain fails.

## 2. Pre-specification (in the run.py docstring)

The docstring states it was written before any alternative measure was run, when only the EMV env. team and corrected baselines were known from logs/replication.md. `research/` has no version control, so this ordering cannot be verified independently (see caveats). The revision after verification left the docstring unchanged; the changes are listed in a comment below it.

- **Machinery.** `lib/team_pipeline.run_pipeline` is used unchanged: the same legs, rolling 60-month FF3 hedge, Brown-leg residual, rolling z, past-only p80 crossing, 3- and 6-month holds, walk-forward ridge purification and continuous weight. Only the attention series and its timing change.
- **Transform.** log1p for every measure, since all are nonnegative. Robustness: levels (`attention_transform="none"`) for MCCC and CPU.
- **Timing.**
  - Primary: the corrected baseline ("realtime"). Attention and the purification controls are lagged one month, and the Oct-2025 CPI gap is linearly interpolated.
  - Comparison: the team timing ("same_month") with the CPI gap interpolated.
  - Reference: the team baseline, `run_pipeline()` defaults.
- **Windows.**
  - Validation is 2010-01 to 2022-07.
  - The holdout runs from 2022-08 to end_m. end_m is the last month whose return is driven by the measure under both timings (last data month + 1): 2025-07 for MCCC (36 months), 2025-10 for CPU (39 months), and 2026-07 (48 months) for EMV env., VIX and EMV overall.
- **Q1 primary family: 40 tests, Holm and BH within the family.** For MCCC and CPU under realtime timing:
  - the FF3 alpha t of the six team strategies (Original 3m, Pure 3m, Original 6m, Pure 6m, Continuous raw, Continuous pure) in validation and holdout (24 tests);
  - the IC of the four signals (raw z, purified, continuous weight raw, continuous weight pure) in validation and holdout (16 tests).
  - Decision rule: the result "changes" only if some MCCC or CPU strategy has a positive holdout alpha with Holm p < 0.05.
- **Q2 placebo, a separate pre-specified family.**
  - For VIX and EMV overall under realtime timing, the same statistics plus the COVID-window FF3 alpha of the six strategies. The COVID window is 2020-01 to 2021-12 (n = 24, t(20) p-values).
  - A paired test: the FF3 alpha of r(EMV env.) minus r(placebo).
  - A placebo "reproduces" the COVID gain for a strategy when its COVID alpha is positive and at least 50% of the EMV env. alpha for that strategy.
  - The climate interpretation fails if either placebo reproduces it in at least 4 of the 6 strategies.
- **Everything else is robustness or exploratory.** This covers team timing, EMV env. share, the MCCC transition composite, the level transform, matched holdout windows, live-window validation, other periods (including last 12 and 18 months), crossing overlap, the COVID decomposition and the comparisons with the always-short benchmark.

## 3. Data (measures_monthly.csv, month-end, each on its native range)

| Measure | Construction | Range | Role |
|---|---|---|---|
| EMV_env | FRED EMVENRGYENVREG (identical to the team `attention`) | 1985-01 to 2026-08 | team reference |
| MCCC | Ardia et al. MCCC aggregate, 2025 update (`load_mccc()`), as used by Pastor-Stambaugh-Taylor (2022) | 2003-01 to 2025-06 | primary |
| CPU | Gavriilidis Climate Policy Uncertainty (`load_cpu()`) | 1987-04 to 2025-09 | primary |
| VIX | monthly mean of daily FRED VIXCLS | 1990-01 to 2026-08 | placebo |
| EMV_overall | FRED EMVOVERALLEMV | 1985-01 to 2026-08 | placebo |
| EMV_env_share | EMV_env / EMVOVERALLEMV | 1985-01 to 2026-08 | robustness |
| MCCC_transition | mean of MCCC topics Climate Legislation/Regulations, Carbon Tax, Carbon Credits Market, Renewable Energy, Agreements/Actions | 2003-01 to 2025-06 | robustness |

The legs, FF3 factors and macro controls come from the team files (`load_team()`), with the October 2025 CPI value interpolated.

**Warm-up (signal_availability.csv).** The machinery needs 36 months for the z-score, 60 more for the p80 threshold, and 60 complete rows before purification. Under realtime timing, the MCCC Original rules therefore first earn a return in 2011-02 (138 validation months) and the MCCC Pure rules in 2016-02 (78 validation months). Every other measure is live before 2010.

**Zeros.** EMV env. and its share are exactly 0 in 65% of holdout months (31 of 48). No other measure has zeros.

**Correlation of the realtime rolling z with the EMV env. z, 2010 onward.** MCCC -0.07, CPU 0.10, VIX 0.14, EMV overall 0.39, EMV env. share 0.88.

## 4. Method

With A_t = measure value for month t and T = log1p:

- z_t = (T(A)_t - mean_60(T(A))_t) / sd_60(T(A))_t, with at least 36 observations.
- state_t = 1[z_t > q80(z_1..z_{t-1})], where q80 is expanding with at least 60 observations.
- cross_t = state_t and not state_{t-1}.
- hold_h(t) = 1 if a crossing happened in t-h+1..t.
- pure_t = z_t - ridge_prediction_t(controls), walk-forward: 120-month window, at least 60 rows, ridge 0.10.
- w_t = EWM_halflife3( clip((pct_rank_t(signal) - 0.5)/0.5, 0, 1) ).
- position_t = -hold_h(t) * min(1, 0.05 / (sqrt(12) * sd_36(eps)_t)). The continuous rule uses w_t in place of hold_h(t). eps is the Brown-leg FF3 residual, with betas from 60 months ending at t applied to t+1.
- r_{t+1} = position_t * (Brown excess_{t+1} - beta_t' f_{t+1}), less the team costs: 10 bp on the asset, 5 bp on Mkt-RF and 25 bp on SMB and HML per unit of turnover, charged the next month.
- **Timing.**
  - Realtime: A_{t-1} and controls_{t-1} are used at the close of t.
  - Same month: A_t is used at the close of t.
  - Either way, the position earns t+1.
- **Performance and inference.**
  - r_t = alpha + b' FF3_t + e_t, fitted by OLS with Newey-West 6-lag t (the team function).
  - Two-sided p comes from t(n-4) when n < 60, and from the normal otherwise.
  - Annualized: mean x12, vol x sqrt(12).
- **IC.** The NW(6) slope of z(eps_{t+1}) on z(signal_t), with the window defined on the month of eps_{t+1}.
  - The team filters on the signal date instead; both are in ic.csv.
  - For a Short-Brown rule, a NEGATIVE IC is favorable.
- **Bootstrap.** Circular block bootstrap of the mean net return: block 12, 5000 reps, seed 230 (bootstrap.csv).

Checks: `run_pipeline(attention=EMV_env)` equals the team default (max diff 0.0). The helper's realtime run equals the audit's corrected baseline (0.0). The full-mode strategies equal the cheap-mode ones (asserted in run.py). The team-baseline rows in results_long.csv reproduce the write-up, for example Original 3m COVID net 5.94%, alpha 6.03%, t 3.21. The verifier's independent statistics reproduce every primary estimate exactly, and its from-scratch engine reproduces the Original 3m and 6m net returns exactly (VERIFY.md).

## 5. Primary results (Q1): the result does not change

From primary.csv / primary.tex, realtime timing. Entries are FF3 alpha in % per year with t in parentheses.

| Strategy | EMV env. Val. | EMV env. Hold. | MCCC Val. | MCCC Hold. (to 2025-07) | CPU Val. | CPU Hold. (to 2025-10) |
|---|---|---|---|---|---|---|
| Original 3m | 1.62 (1.97) | -2.16 (-1.90) | 0.44 (0.53) | -2.91 (-1.88) | 1.50 (1.44) | 0.36 (0.37) |
| Pure 3m | 1.70 (2.01) | -2.16 (-1.90) | 0.37 (0.40) | -2.19 (-1.95) | -0.11 (-0.11) | -0.61 (-0.52) |
| Original 6m | 2.09 (2.18) | -1.97 (-1.30) | 1.05 (0.93) | -2.70 (-1.70) | 1.81 (1.73) | -1.62 (-0.98) |
| Pure 6m | 2.33 (2.59) | -1.97 (-1.30) | 0.04 (0.05) | -1.66 (-1.31) | 1.37 (1.28) | 0.20 (0.20) |
| Continuous raw | 0.46 (1.40) | -0.58 (-1.33) | 0.25 (0.53) | -0.95 (-1.55) | 0.41 (0.87) | -0.56 (-0.91) |
| Continuous pure | 0.51 (1.46) | -0.59 (-1.33) | -0.12 (-0.22) | -0.56 (-1.39) | 0.28 (0.88) | -0.30 (-0.56) |

- **Holdout.** No MCCC or CPU strategy has a significant positive holdout alpha.
  - All six MCCC holdout alphas are negative, from -0.56% to -2.91%, with t between -1.31 and -1.95.
  - Four of the six CPU holdout alphas are negative. The two positive ones are Original 3m (+0.36%, t 0.37) and Pure 6m (+0.20%, t 0.20).
  - Decision: UNCHANGED (key_numbers.csv: q1_decision).
- **Holm.** The smallest Holm-adjusted p among the 40 primary tests is 1.00. The smallest raw p is 0.033, for the MCCC purified-signal holdout IC. That IC is +0.163 (t 2.22), which is the wrong sign for Short-Brown. Holm = 1.00 is close to mechanical here (40 x 0.033 > 1): with 36 to 39 holdout months the rule needed p < 0.00125, so the decision could hardly have flipped. The substantive evidence is the sign pattern (MCCC negative in 6 of 6).
- **Validation.** The validation evidence does not carry over to climate-concern measures.
  - EMV env. has 4 of 6 validation alphas with t >= 1.96. MCCC has 0 and CPU has 0.
  - The largest climate-measure validation t is CPU Original 6m, 1.81% (t 1.73).
  - Mean validation alpha across the six strategies: EMV env. 1.45%, CPU 0.88%, MCCC 0.34% (key_numbers.csv).
  - The validation pattern belongs to the EMV tracker family rather than to the environmental-regulation category: EMV overall has a mean validation alpha of 1.07% with Original 6m at 1.88% (t 2.05) (alpha_grid_realtime.csv; key_numbers.csv).
- **ICs** (primary.csv, realtime).
  - EMV env.: the validation IC is negative only for the continuous weights (-0.147, t -2.16 raw; -0.162, t -2.19 pure). The raw z (-0.024, t -0.23) and purified signal (-0.045, t -0.41) are near zero.
  - MCCC validation ICs are 0.030 to 0.092 (all t < 1.1), and CPU's are -0.005 to 0.019 (all |t| < 0.32). Neither shows the favorable negative sign.
  - In the holdout, MCCC ICs are positive (0.103 to 0.214; t 0.90 to 2.22). Higher media climate concern was followed by a HIGHER Brown residual, against the thesis. CPU holdout ICs are near zero (-0.029 to 0.065).
- **Matched windows** (robustness, results_long.csv periods holdout_to_2025-07 and holdout_to_2025-10).
  - Over MCCC's window, EMV env. Original 3m earns -1.17% (t -2.08), against -2.91% (t -1.88) for MCCC.
  - Over CPU's window, EMV env. Original 3m earns -1.04% (t -1.97), against +0.36% (t 0.37) for CPU.
  - So the negative holdout is not an artifact of the longer EMV env. window.
- **Post-2010 and full sample** (results_long.csv periods post2010 and full_live).
  - Post-2010 alphas are small for every measure. EMV env. ranges 0.24% to 1.42% (max t 1.65), MCCC -0.27% to 0.35% (max |t| 0.51) and CPU -0.21% to 1.23% (max t 1.43).
  - Full live samples: EMV env. Original 3m from 1993-02 earns 0.44% (t 0.75), and CPU Original 3m from 1995-05 earns 0.33% (t 0.52).
- **Recent 12 and 18 months** (exploratory; recent.csv / recent.tex, realtime, Original 3m). MCCC and CPU data end before these windows, so only EMV env., the placebos, the share variant and the benchmark are available. FF3 alpha in % (t), then annualized net return in %:

  | Measure | Last 18 (2025-02 to 2026-07) alpha (t) | net | Last 12 (2025-08 to 2026-07) alpha (t) | net |
  |---|---|---|---|---|
  | EMV env. | -4.05 (-1.55), p 0.14, n 18 | -4.51 | +1.20 (0.30), p 0.77, n 12 | -5.21 |
  | VIX | +0.79 (0.86) | +2.49 | +0.82 (0.90) | +4.43 |
  | EMV overall | -1.56 (-0.45) | +1.97 | +1.30 (0.18) | +4.51 |
  | Always-short Brown (no signal) | -6.25 (-1.87) | -1.07 | -3.39 (-0.52) | +1.35 |

  - None is significant (p < 0.05 needs |t| > 2.14 with 18 observations and > 2.31 with 12 under t(n-4)). The EMV env. share variant is identical to EMV env. for Original 3m in both windows.
  - Under real-time timing, five recent-window cells have |t| above 2, all of them losses (recent.csv, exploratory): EMV env. Continuous raw and Continuous pure over the last 18 months (-1.74%, t -2.19, p 0.046; -1.99%, t -2.59, p 0.021), the same two rules for the EMV env. share variant (-1.64%, t -2.33; -2.07%, t -2.64), and EMV overall Pure 6m over the last 12 months (-8.73%, t -2.21, p 0.058).
  - The EMV env. last-12 alpha is positive while its net return is -5.21%; with 12 observations and four parameters, the split between alpha and factor loadings is not informative.
  - Under the team's same-month timing (identical to the team baseline for Original 3m), EMV env. Original 3m earns -10.82% alpha (t -4.75, p 0.0003; net -8.10%) over the last 18 months and -11.31% (t -2.68, p 0.028; net -8.84%) over the last 12 (results_long.csv, timing same_month, periods last18 and last12; exploratory).

## 6. Placebo results (Q2): by the pre-specified rule the climate reading fails, but the outcome depends on rule family and timing

From placebo_covid.csv / placebo_covid.tex. COVID window (2020-01 to 2021-12, n = 24), FF3 alpha in % with t in parentheses. With t(20), |t| > 2.09 is needed for p < 0.05.

**Real-time timing (primary):**

| Strategy | EMV env. | VIX | EMV overall | CPU | MCCC | EMV env. - VIX | EMV env. - EMV overall |
|---|---|---|---|---|---|---|---|
| Original 3m | 6.38 (3.62) | 2.41 (2.03) | 1.65 (1.29) | 6.44 (4.46) | 1.63 (0.91) | 3.97 (2.67) | 4.73 (3.22) |
| Pure 3m | 6.65 (3.95) | 0.54 (0.49) | 2.69 (1.64) | 4.81 (2.59) | 4.84 (2.54) | 6.11 (2.70) | 3.96 (2.75) |
| Original 6m | 3.99 (1.79) | 0.40 (0.25) | 4.83 (1.98) | 4.29 (2.00) | 3.23 (2.18) | 3.59 (3.18) | -0.84 (-1.16) |
| Pure 6m | 4.54 (1.96) | 5.79 (3.06) | 3.06 (2.07) | 2.45 (1.66) | 2.89 (2.02) | -1.25 (-0.39) | 1.48 (1.01) |
| Continuous raw | 1.95 (2.68) | 1.22 (1.03) | 1.61 (1.68) | 2.08 (2.52) | 1.48 (2.58) | 0.74 (0.78) | 0.34 (0.53) |
| Continuous pure | 1.85 (2.42) | 0.97 (0.53) | 1.19 (0.94) | 1.04 (1.12) | 1.20 (2.27) | 0.88 (0.55) | 0.66 (0.62) |

**Team timing (same month, CPI interpolated; robustness):**

| Strategy | EMV env. | VIX | EMV overall | CPU |
|---|---|---|---|---|
| Original 3m | 6.03 (3.21) | 1.95 (1.75) | 4.64 (2.18) | 6.33 (3.57) |
| Pure 3m | 6.27 (3.09) | 0.74 (0.55) | 3.30 (2.18) | 4.10 (1.93) |
| Original 6m | 5.23 (2.07) | 2.57 (1.58) | 4.91 (2.41) | 4.43 (1.95) |
| Pure 6m | 5.30 (2.09) | 3.71 (2.30) | 2.83 (1.87) | 2.91 (1.87) |
| Continuous raw | 2.14 (3.28) | 1.45 (1.37) | 1.65 (1.86) | 2.11 (2.55) |
| Continuous pure | 2.09 (3.14) | 1.31 (0.77) | 1.18 (1.00) | 1.01 (1.12) |

- **Pre-specified rule outcome: fails** (key_numbers.csv q2_decision).
  - Real-time timing: EMV overall reproduces the gain in 4 of 6 strategies (Original 6m, Pure 6m, Continuous raw, Continuous pure) and VIX in 3 of 6 (Pure 6m, Continuous raw, Continuous pure). The threshold of 4 is met exactly, by EMV overall.
  - Team timing: EMV overall reproduces it in 6 of 6 and VIX in 3 of 6 (key_numbers.csv q2_*_reproduced_strategies_*).
  - Under real-time timing the "fails" outcome comes entirely from the 6-month and continuous rules. For the 6-month rules the EMV env. COVID alpha is itself weak: Original 6m 3.99% (t 1.79, p 0.089) and Pure 6m 4.54% (t 1.96, p 0.064). EMV env. Pure 6m is short in all 24 COVID months, so in this window it is the always-short position (4.54%, t 1.96).
- **Original 3m, the team's headline COVID number, and Pure 3m.**
  - Real-time timing: neither volatility placebo reproduces the gain. On Original 3m, VIX reaches 38% of the EMV env. alpha and EMV overall 26%; on Pure 3m, 8% and 40%.
  - Team timing: EMV overall reproduces both 3-month rules, Original 3m at 4.64% (t 2.18), 77% of the EMV env. 6.03%, and Pure 3m at 3.30%, 53%. VIX does not (32% and 12%).
  - Real-time timing: the paired differences EMV env. minus placebo are nominally significant for both 3-month rules (Original 3m t 2.67 vs VIX and 3.22 vs EMV overall; Pure 3m t 2.70 and 2.75), but after Holm within the 12 real-time paired tests none survives (smallest Holm p 0.051; placebo_covid.csv holm_p_paired_placebo_family). Team timing: against EMV overall the differences are not significant (Original 3m +1.39%, t 0.87; Pure 3m t 1.29), while against VIX they remain nominally significant (Original 3m +4.08%, t 2.34, p 0.030; Pure 3m +5.53%, t 2.15, p 0.044; placebo_covid.csv emv_minus_measure_*).
  - CPU, a climate-policy measure, matches EMV env. on Original 3m under both timings: 6.44% vs 6.38% real-time (paired t -0.06) and 6.33% vs 6.03% under team timing (ratio 1.05).
  - Summary: by the pre-specified rule, the climate reading fails (EMV overall 4 of 6, driven by the 6-month and continuous rules). For Original 3m, the volatility placebos fall short under real-time timing (EMV overall reaches 77% under team timing), and the climate-policy index CPU matches it.
- **A signal-free position earns most of the COVID gain.** The always-short-Brown benchmark earns 6.87% net with FF3 alpha 4.54% (t 1.96) over the same 24 months (results_long.csv, measure "none"). That is 71% of the EMV env. Original 3m real-time alpha (75% of the team-timing 6.03%). The paired FF3 alpha of EMV env. Original 3m minus always-short is +1.84% (t 0.87, p 0.39) under real-time timing and +1.49% (t 0.45) under team timing; for CPU Original 3m it is +1.90% (t 1.02) (covid_decomposition.csv, ledger COVIDB_*). The rule's timing adds nothing statistically detectable over a permanent short of the Brown residual in this window.
- **What drives the 3-month COVID alpha** (exploratory; covid_attribution.tex, covid_decomposition.csv, crossings.csv, key_numbers.csv).
  - The Brown-leg FF3 residual fell -3.33% in 2020-03 and -5.91% in 2020-04 (key_numbers.csv).
  - Real-time timing: EMV env. Original 3m is short in return months 2019-11 through 2020-04. The crossing in data month 2019-09 (signal at the close of 2019-10) earns November 2019 to January 2020; the crossing in data month 2019-12 (signal at the close of 2020-01) extends the hold to earn February to April 2020. March and April give 49% of the summed COVID net return (7.93% of 16.08%). The rule is short in about 13 of the 24 COVID months.
  - Team timing: the 2019-12 crossing earns January to March 2020, so only March is held, and March-April give only 23% of the COVID net return (2.71% of 11.87%).
  - EMV env. and CPU both cross in data month 2019-12, before the pandemic reached US markets. The volatility measures cross only in 2020-02, after the crash had started; under real-time timing they catch April but miss March, while under team timing they hold both months.
  - Holding the crash months is not sufficient on its own: MCCC is short in both March and April 2020 under real-time timing yet earns only 1.63% (t 0.91) over the window.
  - Excluding March and April 2020 (22 observations), FF3 alpha in % (t):

    | Measure | Real-time | Team timing |
    |---|---|---|
    | EMV env. | 3.48 (2.68) | 4.25 (2.41) |
    | CPU | 3.81 (2.44) | 4.22 (1.92) |
    | VIX | 2.20 (1.25) | -0.23 (-0.29) |
    | EMV overall | 1.18 (0.67) | 2.64 (0.99) |
    | MCCC | 0.03 (0.01) | 0.64 (0.22) |
    | Always-short Brown (no signal) | 3.06 (1.05) | 3.06 (1.05) |

    Paired against the always-short position with the crash months excluded, EMV env. Original 3m earns +0.42% (t 0.18) and CPU +0.75% (t 0.44) under real-time timing.
  - **Interpretation.** The Original 3m COVID alpha is a single 24-month window with about 13 held months, half of the real-time gain comes from two crash months, the placebo comparison is timing-dependent, inference is exploratory (n = 22 to 24 with NW(6)), and there is no holdout support. It is not a basis for implementation. It cannot be attributed to the pandemic alone either: outside March and April the climate-linked measures keep alphas of 3.5% to 4.3% (t 1.9 to 2.7), and the December 2019 crossing is shared with CPU, a genuine climate-policy index. That shared crossing is the one result in this module consistent with a climate trigger. But those ex-crash alphas are close to the signal-free always-short alpha (3.06%), and the paired differences against it are small (t 0.18 and 0.44), so the COVID window does not separate a climate trigger from simply being short the Brown residual in 2020-21.
- **The team's other COVID "Holm survivor," Continuous raw, is reproduced by every measure.** Ratios to the EMV env. alpha are 0.62 for VIX, 0.83 for EMV overall, 0.76 for MCCC and 1.06 for CPU.

## 7. Crossings

From crossings.csv, crossings_events.csv, crossings.tex and figure M1b_alt_signals_crossings. Raw-signal crossings are dated by data month, from 2010-01 to each measure's data end. The ±1m column counts crossings within one month of a team EMV env. crossing. Chance is the expected count if the measure's crossings fell on random months, using the exact share of window months that lie within one month of a team crossing (0.376 to 0.381, which accounts for non-adjacent team crossings and window edges). Two one-sided tests of "more overlap than chance" are reported: the binomial with that exact share, and a circular-shift permutation that rotates the measure's crossings around the window while keeping the team's fixed.

| Measure | Crossings | Validation | Holdout | COVID | Same month as team | Within ±1m | Chance ±1m | p binomial (one-sided) | p circular shift (one-sided) |
|---|---|---|---|---|---|---|---|---|---|
| EMV env. (team) | 26 | 21 | 5 | 3 | 26 | 26 | | | |
| MCCC | 25 | 19 | 6 | 4 | 2 | 11 | 9.4 | 0.32 | 0.32 |
| CPU | 23 | 20 | 3 | 4 | 4 | 12 | 8.8 | 0.12 | 0.059 |
| VIX | 10 | 7 | 3 | 2 | 3 | 4 | 3.8 | 0.56 | 0.56 |
| EMV overall | 14 | 10 | 4 | 3 | 7 | 9 | 5.3 | 0.040 | 0.035 |
| EMV env. share | 29 | 24 | 5 | 2 | 17 | 19 | 10.9 | 0.002 | 0.010 |
| MCCC transition | 17 | 15 | 2 | 3 | 2 | 8 | 6.4 | 0.29 | 0.32 |

- The climate-concern measures cross about as often as the team signal. MCCC matches the team crossing month exactly only 2 times and CPU 4 times.
- Their ±1-month overlap (11 and 12) is not distinguishable from chance (9.4 and 8.8).
- The only measure beyond the share variant whose overlap exceeds chance at 5% one-sided is EMV overall: 9 vs 5.3 (p 0.040 binomial, 0.035 circular shift). The two-sided p-values stored in the ledger are 0.052 (binomial) and 0.071 (circular shift).
- The Jaccard overlap of 3-month hold months with the team is 0.24 for MCCC, 0.34 for CPU and 0.34 for EMV overall.
- Crossings 2019-11 to 2021-12:
  - EMV env.: 2019-12, 2020-05, 2020-10, 2021-05
  - CPU: 2019-12, 2020-03, 2020-10, 2021-07, 2021-09
  - MCCC: 2019-11, 2020-01, 2020-09, 2021-01, 2021-08
  - VIX: 2020-02, 2020-09
  - EMV overall: 2020-02, 2020-10, 2021-03

## 8. Robustness

- **Team timing (same month, CPI interpolated; alpha_grid_same_month.csv).**
  - MCCC validation alphas stay below t 1.6 (best Original 6m, 1.57%, t 1.59). Its holdout alphas are all negative, and Pure 3m reaches -3.11% (t -2.39).
  - CPU validation is best at Original 6m, 1.86% (t 1.82), and its holdout ranges from -1.20% to +0.50% (all |t| < 0.82).
- **Level transform** (transform "none").
  - MCCC validation t is at most 0.62. Its holdout alphas run from -0.65% to -2.48%, and its holdout ICs are positive (0.121 to 0.216).
  - CPU validation t is at most 1.66. Its holdout alphas run from -1.62% to +0.36%.
  - Nothing changes. The level transform is exactly scale-invariant, so MCCC index vintage and normalization cannot drive the MCCC result.
- **MCCC live-window validation** (period validation_live). Original 3m earns 0.54% (t 0.59) over 138 months and Pure 6m 0.16% (t 0.10) over 78 months. The weak MCCC validation is not caused by its warm-up months.
- **MCCC transition composite.**
  - Validation alphas: all |t| <= 0.99.
  - Holdout alphas: -1.35% to +0.56%.
  - Holdout ICs: all positive, with purified 0.267 (t 2.92) and continuous-weight 0.244 to 0.248 (t 2.53 to 2.80). Transition-topic concern was followed by higher Brown residuals in 2022-2025, the opposite of the thesis.
- **EMV env. share.**
  - Validation: Pure 6m 1.93% (t 2.19), but Original 3m falls to 0.26% (t 0.32).
  - Holdout: Original 3m -2.16% (t -1.90), the same as EMV env., because both series share the same zero months.
- **Placebos outside COVID.**
  - EMV overall validation alphas are close to EMV env.'s: mean 1.07% vs 1.45%, with Original 6m at 1.88% (t 2.05).
  - VIX and EMV overall holdout alphas are near zero, with no |t| above 1.01.
  - Much of the EMV env. rule's validation behavior is shared with the overall EMV tracker.
- **Bootstrap** (bootstrap.csv).
  - MCCC holdout mean net: Original 3m -2.69% (CI -5.41% to -0.29%) and Original 6m -2.87% (CI -5.65% to -0.47%). With 36 months (3 blocks) these intervals are coarse.
  - CPU holdout Original 3m: -0.37% (CI -1.81% to +1.22%).
  - EMV env. holdout Original 3m: -2.57% (CI -4.72% to -0.78%).
- **Turnover and costs** (compact.csv, validation, realtime). They do not separate the measures.
  - Discrete rules turn over 1.7 to 5.8 times a year (1.8 to 5.8 for EMV env., the primary and the placebo measures), with cost drag at most 0.63% a year (EMV env. Pure 3m, 5.8x). Original 3m: EMV env. 5.1x and 0.56%, MCCC 3.8x and 0.43%, CPU 4.9x and 0.52%.
  - Continuous rules turn over 0.7 to 1.5 times a year, with cost drag 0.07% to 0.16%.
- **Full mode** (full_mode_comparison.csv, full_mode_paired.csv; full window 2010-01 to end_m, holdout 2022-08 to end_m).
  - These are the pipeline's own per-strategy bootstrap and paired tables. The pipeline's `significant_after_multiple_testing` column (a normal-p Holm over 24-month COVID NW(6) t-stats, attached to full-sample rows; audit items 3 and 8) and `active_months_full` (which counts exit-cost months; audit item 6) are dropped. `months_held_full` counts months with a position actually held, for example EMV env. Original 3m 75 of 199.
  - None of the 30 attention-strategy full-window bootstrap p-values is below 0.05 (smallest: EMV overall Original 6m, 0.064).
  - For MCCC, continuous beats discrete in the holdout (Continuous raw minus Original 3m +1.82%, bootstrap p 0.018, pipeline Holm p 0.048 within MCCC's four pairs; ledger FULLPAIR_MCCC_realtime_CR_minus_O3_holdout). That is the de-leveraging effect of audit item 4 applied to losing discrete rules, not evidence for the signal.

## 9. Implications for the verdict

- **Do not implement stands and gets stronger.**
  1. The team's validation alpha (t around 2 under corrected timing) is specific to the EMV tracker family. The same machinery fed MCCC or CPU gives 0 of 12 validation alphas with t >= 1.96, while EMV overall gets close to EMV env. (mean 1.07% vs 1.45%).
  2. No measure, climate or placebo, delivers a positive holdout alpha with t near significance. MCCC is negative in all six rules, and its holdout ICs have the wrong sign. The last 12 and 18 months add no support: under real-time timing no Original 3m |t| exceeds 1.6, and under the team's own timing EMV env. Original 3m had an alpha of -10.82% (t -4.75) over the last 18 months and -11.31% (t -2.68) over the last 12.
  3. The COVID gain is not usable evidence for a climate channel. A signal-free always-short-Brown position earns 4.54% alpha (71% of EMV env. Original 3m), and the rule's paired edge over it is +1.84% (t 0.87). By the pre-specified rule the climate reading fails (EMV overall 4 of 6 under real-time timing, 6 of 6 under team timing), an outcome driven by the 6-month and continuous rules. For Original 3m the volatility placebos fall short under real-time timing, EMV overall reaches 77% under team timing, and CPU matches it. The shared December 2019 EMV env./CPU crossing is consistent with a climate trigger, but it is one event in one window, and its contribution cannot be separated from being short the Brown residual during 2020-21.
- **For the report.** The write-up's thesis is framed as climate attention, but the signal that produced its in-sample numbers is a volatility-news series that is 65% zeros in the holdout. A genuine climate-concern series, run through the identical machinery, does not produce the in-sample result.

## 10. Caveats

- MCCC and CPU have short holdouts (36 and 39 months), with no last-12 or last-18 coverage.
- MCCC is a research dataset released ex post, so even a one-month lag flatters it. The CPU normalization window runs to 2022-08, which log1p makes almost irrelevant, and the level-transform robustness is exactly scale-invariant.
- The MCCC Pure rules are live only from 2016.
- The same-month VIX timing is already real time.
- The 50%-of-alpha rule is not exposure-matched, and the 4-of-6 threshold is met exactly (EMV overall, real-time), so the Q2 rule outcome sits on its boundary.
- COVID inference rests on 22 to 24 observations with a 6-lag HAC.
- Linking the December 2019 spike to climate-policy news is an inference from CPU crossing in the same month; the module does not test event content.
- The pre-specification cannot be verified: `research/` has no version control, so the claim that the docstring predates the alternative-measure runs rests on the builder's account.
- The ledger has 1900 tests; only the 40 primary ones form a confirmatory family.

## 11. Output files

- Tables are in `outputs/tables/`, all with the prefix `M1b_alt_signals_`:
  - measures_monthly
  - signal_availability (.csv/.tex)
  - results_long
  - ic
  - primary (.csv/.tex)
  - placebo_covid (.csv/.tex)
  - covid_decomposition (.csv) and covid_attribution (.tex, new)
  - alpha_grid_realtime and alpha_grid_same_month (.csv/.tex)
  - compact (.csv/.tex)
  - recent (.csv/.tex, new: last 18 and last 12 months)
  - crossings (.csv/.tex) and crossings_events
  - bootstrap
  - full_mode_comparison and full_mode_paired
  - key_numbers
  - tests_ledger (1900 rows: primary 40, placebo 88, reference 82, robustness 1102, exploratory 588)
- Figures, as .pdf and .png, in `outputs/figures/`:
  - M1b_alt_signals_crossings
  - M1b_alt_signals_alpha_t_heatmap
  - M1b_alt_signals_covid_paths (corrected: cumulative net return compounded over 2020-01 to 2021-12 from 0 at 2019-12-31; EMV env. Original 3m ends at 17.09%, VIX at 7.50%, the always-short benchmark at 14.21%)
- Code is in modules/M1b_alt_signals/: run.py (the entry point, with the pre-specification docstring and a revision comment) and helpers.py.

## 12. Response to verification

Each required fix in VERIFY.md, re-derived and addressed. After the fixes, a copy of the verifier's script (patched only for the renamed crossing columns and the dropped flag column, run from the scratchpad so the verifier's own results were not overwritten) passes all 211 value checks. The only remaining mismatches are the text claims corrected below and the intended growth of the ledger.

1. **FINDINGS.md not on disk.** This file is the complete FINDINGS.md, returned for the orchestrator to write (the harness blocks subagent Markdown writes).
2. **Issue A (Q2 headline and the "exception" are timing-dependent).** Confirmed. Under team timing EMV overall reproduces both 3-month rules (Original 3m 4.64%, t 2.18, 77%; Pure 3m 3.30%, 53%; placebo_covid.csv), and under real-time timing the "fails" outcome comes only from Original 6m, Pure 6m and the continuous rules, where the EMV env. 6-month alphas are themselves weak (t 1.79 and 1.96). The headline and section 6 now say this, using the verifier's suggested wording, and add a team-timing table. I also found that EMV env. Pure 6m is short in all 24 COVID months, so it equals the always-short position there; section 6 states it.
3. **Issue B ("one pandemic event, not climate evidence" overreaches).** Confirmed. The phrase is removed. Section 6 now reports the team-timing Mar-Apr share (23%), the timing of the two EMV env. holds (the 2019-09 crossing earned 2019-11 to 2020-01; the 2019-12 crossing earned 2020-02 to 2020-04, correcting the imprecision the verifier noted), the ex-crash alphas under both timings, and the ex-crash benchmark (3.06%, t 1.05). It also names the shared December 2019 CPU crossing as the one climate-consistent result. I added one piece of evidence the verifier did not compute: paired tests against the always-short position (EMV env. Original 3m +1.84%, t 0.87 over COVID; +0.42%, t 0.18 ex-crash; CPU +1.90%, t 1.02 and +0.75%, t 0.44). These show that the ex-crash alphas do not beat a permanent short, so the softened conclusion says the window "cannot be attributed to the pandemic alone" and also "does not separate a climate trigger from being short the Brown residual". These paired tests are now in the ledger (COVIDB_*) and key_numbers.csv. A new table, covid_attribution.tex, collects the Original 3m attribution for the report.
4. **Issue C (covid_paths figure compounding bug).** Confirmed and fixed. The paths now compound only 2020-01 to 2021-12 and prepend 0 at 2019-12-31, for the benchmark too (`covid_path` in run.py section 11c). EMV env. Original 3m ends at 17.09% (was 20.55%), VIX at 7.50%, and the always-short benchmark at 14.21%. The end values are in key_numbers.csv (`*_covid_cum_net_realtime`).
5. **Issue D (crossing chance approximation).** Confirmed and fixed. Chance now uses the exact share of window months within ±1 of a team crossing (0.376 to 0.381). Chance counts become MCCC 9.4, CPU 8.8 and EMV overall 5.3, with one-sided binomial p 0.32, 0.12 and 0.040, matching the verifier. I added a circular-shift permutation test (one-sided p 0.32, 0.059 and 0.035). The conclusions are unchanged: MCCC and CPU are indistinguishable from chance, and EMV overall stays below 0.05 one-sided.
6. **Issue E (misleading full-mode flag columns).** Confirmed and fixed. `significant_after_multiple_testing` and `active_months_full` are dropped from full_mode_comparison.csv, and `months_held_full` (months with a position actually held) is added. Section 8 explains why.
7. **Issue F (ledger incomplete; one-sided p in a two-sided column).** Confirmed and fixed.
   - Added the 20 full-mode paired bootstrap tests (FULLPAIR_*, robustness) and the 40 per-strategy full-window bootstrap tests (FULLBOOT_*: 30 robustness; 10 signal-free benchmark rows labelled reference).
   - The CROSS_* rows now store the exact two-sided binomial p, with the one-sided p in the note, and new CROSSPERM_* rows hold the two-sided circular-shift p.
   - Bootstrap p-values reported as 0 by the pipeline (3 rows: no draw crossed zero) are stored as the 2/5000 resolution bound, with a note.
   - Also added: the 168 exploratory paired COVID tests against the always-short position (two of them degenerate, stored as t 0 and p 1 with a note), and 2 reference rows for the benchmark's last-12 and last-18 windows.
   - The ledger now has 1900 rows and no missing p-values or statistics; all 40 primary test ids are unchanged.
8. **Issue G (recent 12- and 18-month windows missing).** Fixed. Section 5 now has the Original 3m real-time table for EMV env., VIX, EMV overall and the always-short benchmark, and a new recent.csv/recent.tex covers Original 3m, Original 6m and Continuous raw (all six strategies in the CSV). The EMV env. figures match the verifier: last 18 -4.05% (t -1.55, p 0.14, n 18), net -4.51%; last 12 +1.20% (t 0.30), net -5.21%.
9. **Issue H (turnover and runtime text).** Confirmed and fixed. Discrete turnover is 1.7 to 5.8x (1.8 to 5.8x for the team, primary and placebo measures), with maximum drag 0.63% (EMV env. Pure 3m). The runtime is about one minute (measured 45 s and 68 s).
10. **Issue I (pre-specification unverifiable).** Agreed; no fix is possible. It is now stated in sections 2 and 10, together with the point that the 4-of-6 threshold is met exactly.
11. **Wording note on claim 2 ("EMV volatility tracker" vs "EMV tracker family").** Adopted in the headline and in sections 5 and 9.
