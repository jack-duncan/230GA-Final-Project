# M2: Christhian's four overlooked tests

**Run:** `cd /home/hashim/projects/GA/project/research && uv run python modules/M2_christhian_tests/run.py`. It takes about 2 to 4 minutes: 46 pipeline runs, 8 of them in full bootstrap mode, and 8,050 strategy regressions. After the verification round the module was rerun twice. Every number in the round-1 verified outputs is unchanged. The fixes added two tables (`q2_hedge_cost_change.csv`, `q3_rolling_positive_runs.csv`), 30 exploratory `comeq|...` ledger rows, four spanning-regression columns in `q2_comeq_justification.csv` and 23 keys in `key_numbers.csv`. They also renamed two inherited columns in `q1_comparison.csv` and `q2_comparison.csv` and edited the captions and labels of `q2_comeq_justification.tex` and `summary_best_case.tex`. The second rerun reproduced the first byte for byte except `key_numbers.csv`, which gained 7 traceability keys (holdout census configurations and ledger counts).

## Question

Christhian (logs/whatsapp_halfway.md) asked whether four checks leave "any small, defensible alpha":
1. 8-and-8 industry legs.
2. Momentum and an explicit commodity exposure in the controls.
3. Where the Green-minus-Brown (GB) spread's HML exposure comes from.
4. Uniform cost sensitivity at 5, 10 and 25 bp.

**Answer: no.**
- No positive alpha survives Holm or BH, either in the pre-specified primary families or anywhere in the grid of 8,091 alpha tests.
- All six attention-timed rules have a negative holdout alpha in every configuration run (900 net-of-cost holdout regressions; the highest is -0.03%). The always-short benchmark with 8-and-8 legs has small positive holdout alphas in 24 rows (max 0.42%, t 0.22). At zero cost, run only for 5-and-5 legs with the FF3 and FF5+UMD+COMEQ hedges, all 28 holdout alphas are negative.
- The HML exposure is a Brown-leg value tilt (Steel, Ships), not Green-industry growth.
- The verdict stays **Do not implement**.

## Data

**Team inputs (read-only clone):**
- FF49 value-weighted industry returns.
- The team FF3 file.
- The macro file (attention = FRED EMVENRGYENVREG).
- The static emissions snapshot.

**Ken French library:**
- FF5 2x3 factors and UMD (`load_ff5_mom`, from 1963-07).
- Annual Sum BE / Sum ME for the 49 industries.

**FRED:**
- MCOILWTICO: WTI, monthly average, from 1986-01.
- PALLFNFINDEXM: IMF all-commodity index, monthly average, from 1992-01.

**COMEQ** is the new traded commodity-equity factor:
- COMEQ_t = mean(Oil, Coal, Mines, Gold)_t - RF_t, built from the team FF49 file.
- It is defined only when all four industries are present, so from 1963-07 (Gold starts then).
- COMEQx is the same factor without Gold.

**Why COMEQ** (`q2_comeq_justification.csv/.tex`; correlations over 1992-02 to 2026-06, n = 413, because the t+1 leads need one extra month; the FF5+UMD spanning regression over 1992-02 to 2026-07, n = 414):
- It is an investable month-end excess return, so it can serve as a hedge factor, and an intercept on it is a proper alpha. FRED commodity series are monthly-average spot prices, not returns.
- It tracks commodity prices. Correlation with WTI is 0.23 in the same month and 0.40 with next month's log change; for IMF it is 0.33 and 0.47. The higher lead correlation is the price-averaging effect.
- Most of its variance is not explained by FF5+UMD (R-squared 0.37), and its alpha on them is small and insignificant (-0.89% a year, t -0.24, p 0.81): it is a distinct exposure, not a source of alpha.
- It is what the Brown leg is exposed to: correlation 0.66 with the Brown leg (0.55 with the market).
- Gold is included because the brief asks for it. Its correlation with WTI is only 0.06, so COMEQx is a robustness hedge (R-squared 0.45 on FF5+UMD, alpha -1.42%, t -0.35).
- All of these correlations and both spanning alphas are in the ledger as `comeq|...` rows (exploratory; outside the strategy and spread alpha grid).

## Conventions and definitions

**Baselines:**
- **Team baseline** = `run_pipeline()` defaults. It reproduces write-up Table 1 exactly; the assertions are Pure 6m validation alpha 2.51% and Original 3m holdout t -2.19 (`q1_table1.csv`).
- **Corrected baseline** interpolates the Oct 2025 CPI value and lags attention and all five purification controls by one month. Every input used at the close of month t is published by then, and the position earns t+1.
- The inherited rolling hedge uses betas estimated on months t-59..t and applies them to t+1.

**Hedge sets** (traded factors, used as overlays):
- FF3 (team file).
- FF3+UMD.
- FF5+UMD. The FF5 file's HML is identical to FF3's; its SMB correlates 0.979 with the FF3 SMB.
- FF5+UMD+COMEQ (the Q2 primary).
- FF5+UMD+COMEQx.

**Evaluation sets:**
- The hedge set.
- The hedge set plus WTI and IMF.
- FF5+UMD+COMEQ, with and without WTI and IMF.
- FF5+UMD+COMEQ plus WTI, IMF and their t+1 values.

WTI and IMF enter as monthly log changes. They are non-traded attribution controls, never trading inputs, so no publication lag applies. They are demeaned inside each window, which sets their price of risk to zero.

**Costs:**
- Team costs: 10 bp on the asset, 5 bp on Mkt-RF, 25 bp on every other overlay factor.
- Uniform: 5, 10 or 25 bp applied to the asset and every overlay.
- Zero cost (u0) is used only for break-evens and for the before-cost holdout alphas. It is run only for 5-and-5 legs with the FF3 and FF5+UMD+COMEQ hedges (both baselines).

**Inference:** Newey-West t with 6 lags. p-values come from t(n-k) in every window. Annualization is 12 x mean and sqrt(12) x std.

**Windows:**
- post2010: 2010-01 to 2026-07, 199 months.
- validation: 2010-01 to 2022-07, 151 months.
- holdout: 2022-08 to 2026-07, 48 months.
- covid: 2020-2021, 24 months.
- inflation_rates: 2022-2024.
- pre_covid.
- last18: 2025-02 to 2026-07.
- last12: 2025-08 to 2026-07.
- **full_live** runs from the month after the strategy's signal is first defined to 2026-07. Under the team baseline that is 1993-01 for the raw rules and always-short, 1992-12 for continuous raw, 1999-02 for the Pure rules and 1999-01 for continuous pure. The corrected baseline starts one month later.
- **full_1970** runs 1970-01 to 2026-07 for the raw spread and the industries. Rows that include WTI and IMF start in 1992-02.
- In last12 and last18 only the net mean and the FF3 alpha are estimated.

**Strategies:** the 7 hedged rules are Original 3m, Pure 3m, Original 6m, Pure 6m, Continuous raw, Continuous pure and Always-short Brown. The six attention-timed rules are the first six. The unhedged, cost-free buy-and-hold GB is treated as the raw spread.

## Pre-specified primary tests (stated in the run.py docstring)

**Timing record.** The builder transcript (workflow wf_bd8d2a66-0fa, agent a7dd3a997df54dc45) shows run.py, with this docstring, first written at 10:06 UTC on 2026-09-26. Two things came before it: data checks at 09:59 (COMEQ correlations) and a smoke test at 10:02 that printed the Q2 primary configuration's post2010 and holdout alphas. So the Q2 primary is not strictly blind. It follows the module brief's Q2 wording (FF5 + momentum + commodity control, corrected baseline), and its result is null. The Q1 and Q4 primary configurations were not computed before the docstring. The sign of the Q3 loading was already known from the team write-up.

**Template for Q1, Q2 and Q4:** 7 hedged strategies x {post2010, holdout} = 14 alpha t-tests, with Holm at 5% within the 14. "Alpha left" means a positive alpha with Holm p < 0.05.

- **Q1:** corrected baseline, 8-and-8 legs with the team tie-break (Hardw), FF3 hedge, team costs, FF3 alpha.
- **Q2:** corrected baseline, 5-and-5 legs, FF5+UMD+COMEQ hedge, team costs, FF5+UMD+COMEQ alpha.
- **Q4:** corrected baseline, 5-and-5, FF3 hedge, uniform 5 bp, FF3 alpha. The primary descriptive statistic is the uniform break-even cost of the validation alpha.
- **Q3:** the raw 5-and-5 GB HML loading under FF3 and FF5+UMD in full_1970 and post2010 (4 tests, Holm within 4), plus the exact industry decomposition. The "drivers" are the one or two industries with the largest absolute contribution post2010 under FF3.
- **Everything else** is robustness (the four main windows) or exploratory (sub-periods, last12/18, gross runs, characteristic links).
- **Whole-grid check:** Holm and BH over every alpha test in the grid: 7,938 net-of-cost strategy alphas plus 153 raw-spread alphas (unhedged and cost-free).

## Method

- **Spread:** GB_t = mean(Green)_t - mean(Brown)_t.
- **Strategy return:** a position w_t, set at the close of t, earns w_t*(B_{t+1} - RF_{t+1}) - w_t*beta_t'F_{t+1}.
- **Net return:** net = gross - c_asset*|dw| - sum_f c_f*|d(w beta_f)|, charged at t+1.
- **Evaluation regression:** r_t = a + b'F_t + d'(N_t - mean N) + e_t. The reported alpha is 12a.
- **HML decomposition** (exact, because it is the same OLS on the same regressors): b_HML(GB) = mean_i b_HML(G_i - RF) - mean_j b_HML(B_j - RF).
  - Green industry i contributes +b_i/nG; Brown industry j contributes -b_j/nB.
  - The asserted error is below 1e-10.
- **Break-even:** alpha(c) = alpha(0) - c*s exactly (checked to 1e-12 at 5 and 25 bp), so c* = alpha(0)/s.
- **Characteristic:** relative log BE/ME = industry log(Sum BE / Sum ME) minus the 49-industry median each June.
- **Rolling betas:** trailing 60-month OLS. They are descriptive only and never used for trading.

## Q1. 8-and-8 legs

Files: `q1_leg_composition.csv`, `q1_table1.csv`, `q1_table1_{corr,team}.tex/_wide.csv`, `q1_comparison.csv`, `q1_primary.csv`.

**Legs:**
- Green 8 = Fun, RlEst, Drugs, Telcm, Fin, Autos, Insur, plus Hardw or MedEq. These two tie at intensity 0.0126581; the team sort picks Hardw.
- Brown 8 = Util, Ships, Aero, Steel, BldMt, Chems, Trans, Mines.

**Structural fact:** the hedged strategies trade only the Brown-leg residual. The Green leg, and with it the tie-break, affects only the unhedged spread. So 8/8 H = 8/8 M for every strategy, and always-short is identical under both baselines.

**Corrected baseline, FF3 alpha % (t)** (`q1_table1_corr_wide.csv`):

| Strategy | Val 5/5 | Val 8/8 | Hold 5/5 | Hold 8/8 |
|---|---|---|---|---|
| Original 3m | 1.62 (1.97) | 1.30 (1.85) | -2.16 (-1.90) | -2.51 (-1.81) |
| Pure 3m | 1.70 (2.01) | 1.36 (1.74) | -2.16 (-1.90) | -2.51 (-1.81) |
| Original 6m | 2.09 (2.18) | 1.80 (1.87) | -1.97 (-1.30) | -1.24 (-0.60) |
| Pure 6m | 2.33 (2.59) | 2.36 (2.47) | -1.97 (-1.30) | -1.24 (-0.60) |
| Continuous raw | 0.46 (1.40) | 0.36 (1.32) | -0.58 (-1.33) | -0.44 (-0.78) |
| Continuous pure | 0.51 (1.46) | 0.40 (1.39) | -0.59 (-1.33) | -0.41 (-0.70) |
| Always-short | 1.39 (1.12) | 2.05 (1.71) | -1.72 (-1.09) | -0.39 (-0.19) |

**Team baseline** (`q1_table1_team_wide.csv`):
- Validation: Original 3m goes from 1.33 (1.47) to 0.90 (1.02). Pure 6m goes from 2.51 (2.46) to 2.60 (2.31).
- Holdout: Original 3m goes from -4.03 (-2.19) to -4.02 (-2.01). Pure 6m goes from -2.71 (-1.94) to -2.16 (-1.09).

The wider Brown leg mainly improves the unconditional always-short benchmark. That points to the leg itself, not to the attention timing.

**Primary result:** there is no survivor (`q1_primary.csv`).
- Post2010: all 7 alphas are positive but small, 0.17% to 1.56%, with t between 0.56 and 1.67.
- Holdout: all 7 are negative, -0.39% to -2.51%, with t between -0.19 and -1.81.
- The smallest raw p is 0.077, for a negative alpha. Every Holm p is 1.00.

**2010-2026 comparison table with 5,000-rep bootstrap** (`q1_comparison.csv`):
- 8/8 corrected Pure 6m: net 1.79%, Sharpe 0.41, bootstrap p 0.050 (CI [0.000, 0.037]).
- 8/8 team Continuous pure: bootstrap p 0.037.
- 8/8 Always-short: bootstrap p 0.056.

These are nominal in-sample p-values, and none survives multiple testing.

**Inherited team columns renamed.** In `q1_comparison.csv` and `q2_comparison.csv` the team's `significant_after_multiple_testing` column is renamed `team_holm_flag_normal_p`, and `active_months_full` is renamed `team_active_months_full_nonzero_net`. The first is the team's Holm flag over 32 claims with normal p-values on NW(6) t-stats. It is True (for 5/5 team Original 3m and Continuous raw, and 5/5 corrected Original 3m and Pure 3m) only through 24-month COVID claims (replication audit item 3). It contradicts M2's t(n-k) inference and must not be cited. The second counts exit-cost-only months (audit item 6).

**Raw spread FF3 alpha % (t):**

| Window | 5/5 | 8/8 H | 8/8 M |
|---|---|---|---|
| post2010 | -1.12 (-0.49) | 1.09 (0.56) | 0.87 (0.41) |
| holdout | -4.59 (-0.99) | 1.21 (0.23) | -2.52 (-0.44) |

The tie-break flips the sign of the holdout spread, which shows how fragile it is.

## Q2. Momentum and commodity controls

Files: `q2_comeq_justification.csv/.tex`, `q2_spread_controls.csv/.tex`, `q2_primary.csv`, `q2_strategy_controls.tex/_wide.csv`, `q2_hedge_cost_post2010.csv`, `q2_hedge_cost_change.csv`, `q2_table1.csv`, `q2_comparison.csv`, `strategy_grid.csv`.

**Raw 5/5 spread, alpha % (t) and HML loading (t):**

| Controls | Full 1970 alpha | Full HML | Post2010 alpha | Post2010 HML | Holdout alpha | Holdout HML |
|---|---|---|---|---|---|---|
| FF3 | 0.54 (0.41) | -0.23 (-4.63) | -1.12 (-0.49) | -0.30 (-5.74) | -4.59 (-0.99) | -0.13 (-1.34) |
| FF3+UMD | 1.20 (0.89) | -0.26 (-5.20) | -0.67 (-0.30) | -0.32 (-6.16) | -3.96 (-0.85) | -0.11 (-1.45) |
| FF5+UMD | 2.20 (1.60) | -0.14 (-2.38) | -0.16 (-0.07) | -0.24 (-3.21) | -4.44 (-0.90) | 0.02 (0.14) |
| FF5+UMD+COMEQ | 1.91 (1.57) | -0.11 (-2.30) | -0.41 (-0.22) | -0.21 (-2.67) | -2.37 (-0.53) | 0.24 (2.01) |
| + WTI, IMF | 1.19 (0.79), from 1992-02, n = 414 | -0.09 (-1.56) | -0.40 (-0.22) | -0.19 (-2.55) | -1.90 (-0.42) | 0.20 (1.96) |

- **COMEQ loading:** -0.18 (t -8.70) full sample, -0.12 (t -2.70) post2010, -0.28 (t -3.57) holdout. The Brown leg is a bet on commodity producers.
- **UMD:** loads negatively, strongest in the holdout at -0.38 (t -6.76) with COMEQ; post2010 it is -0.14 (t -2.10).
- **WTI and IMF:** add nothing once COMEQ is in; post2010 t = -0.66 (WTI) and 0.65 (IMF).
- **HML:** the richer controls roughly halve the 1970-2026 loading (-0.23 under FF3 to -0.11 under FF5+UMD+COMEQ). Post2010 the loading falls only about 30% (-0.30 to -0.21, and -0.19 with WTI and IMF). In the holdout the sign flips to +0.24 (t 2.01) with COMEQ in the model. There, the Brown leg's value exposure is better described as commodity exposure.
- **8/8 H spread:** 1970-2026 alpha is 2.52% (t 2.57, p 0.010) on FF5+UMD+COMEQ and 2.91% (t 2.35) on FF5+UMD. This is a pre-2010 effect: post2010 1.64% (t 1.11), holdout 0.88% (t 0.20).

**Strategies, corrected 5/5, team costs, hedge set = evaluation set.** Post2010 alpha t falls when moving from the FF3 hedge to FF5+UMD+COMEQ:

| Strategy | FF3 | FF5+UMD+COMEQ |
|---|---|---|
| Original 3m | 1.04 | 0.39 |
| Pure 3m | 1.10 | 0.08 |
| Original 6m | 1.36 | 0.83 |
| Pure 6m | 1.65 | 0.75 |
| Continuous raw | 0.83 | 0.34 |
| Continuous pure | 0.93 | 0.29 |
| Always-short | 0.67 | -0.00 |

- Holdout alphas stay between -0.58% and -3.44% (t between -1.01 and -2.27) across the four hedge sets.
- **Why the richer hedge hurts** (`q2_hedge_cost_change.csv`, corrected baseline, post2010):
  - Total turnover (asset plus overlay) rises 24% to 37% for the six signal rules and 127% for always-short. Overlay turnover alone rises 35% to 54% for the signal rules and 163% for always-short. Original 3m total turnover goes from 4.80 to 5.99 a year and its cost drag from 0.53% to 0.85%.
  - The hedge also removes gross return that was factor exposure. Always-short gross return drops from 1.15% to 0.44%.
- **Changing only the evaluation, not the hedge,** barely moves the result: FF3-hedged Pure 6m post2010 is 1.42% (1.65) on FF3, 1.35% (1.74) on FF5+UMD+COMEQ and 1.34% (1.75) with WTI and IMF added.
- **Residual HML loading of the hedged strategies** (`q2_hedge_cost_post2010.csv`):
  - Team FF3 hedge, corrected baseline, post2010: -0.015 to -0.053 (t -1.19 to -1.95). Under the team baseline: -0.018 to -0.061 (t -1.35 to -2.36).
  - FF5+UMD+COMEQ hedge, corrected baseline, post2010: -0.024 to -0.079 (t -0.78 to -1.69).
  - FF5+UMD+COMEQ hedge, holdout: +0.039 to +0.148 (t up to 2.24), because the rolling hedge lags the rise in the Brown leg's HML beta.

**Primary result:** no commodity-controlled alpha is significantly positive (`q2_primary.csv`).
- Post2010: 6 of the 7 point estimates are positive, from -0.005% (Always-short) to 0.59% (Original 6m), with t at most 0.83.
- Holdout: all negative, -0.61% to -3.28%, t between -1.28 and -2.27.
- The smallest p is 0.028, for Original/Pure 3m holdout at -2.50%; its Holm p is 0.397. There are 0 positive survivors.

**Robustness, all with the same verdict:**
- Team baseline: post2010 -0.56% to 1.00% (t at most 1.40); holdout -0.66% to -3.61%.
- 8/8 legs: post2010 -0.12% to 0.61%; holdout -0.34% to -2.70%.
- COMEQ ex-Gold: post2010 -0.58% to 0.34%; holdout -0.80% to -3.55%.
- WTI and IMF added to the evaluation: post2010 t at most 0.80.
- Full-mode 2010-2026 bootstrap p (`q2_comparison.csv`): at least 0.29 for every strategy.

## Q3. Where the HML exposure comes from

Files: `q3_primary.csv`, `q3_industry_loadings.csv`, `q3_hml_decomposition.csv`, `q3_industry_hml.tex`, `q3_hml_contributions.tex/_wide.csv`, `q3_rolling_hml.csv`, `q3_rolling_summary.csv`, `q3_rolling_positive_runs.csv`, `q3_log_bm.csv`, `q3_bm_link.csv`, `q3_bm_cross_section.csv`.

**Primary result:** all four long-window loadings are significant after Holm within 4 (largest Holm p 0.017).

| Model | Full 1970 (n = 679) | Post2010 (n = 199) |
|---|---|---|
| FF3 | -0.233 (t -4.63) | -0.298 (t -5.74) |
| FF5+UMD | -0.140 (t -2.38) | -0.240 (t -3.21) |

In the holdout the loading is not significant: -0.126 (t -1.34) under FF3 and +0.018 (t 0.14) under FF5+UMD.

**FF3 HML loadings by industry, post2010 (t):**
- Green: Fun -0.34 (-3.1), RlEst 0.45 (4.8), Drugs -0.09 (-1.0), Telcm 0.27 (4.0), Fin 0.40 (4.9).
- Brown: Util 0.19 (2.7), Ships 0.52 (6.8), Aero 0.44 (3.6), Steel 0.67 (4.6), BldMt 0.36 (6.0).
- Full 1970: every Brown industry loads between 0.32 and 0.48 (t > 3.8). Among Green, RlEst 0.70 and Fin 0.29 load positively and Drugs -0.26 negatively.

**Exact decomposition:**

| Window and model | Brown side | Green side | Total |
|---|---|---|---|
| Post2010, FF3 | -0.437 | +0.139 | -0.298 |
| Full 1970, FF3 | -0.419 | +0.186 | -0.233 |
| Post2010, FF5+UMD | -0.316 | +0.076 | -0.240 |
| Holdout, FF3 | -0.518 | +0.392 | -0.126 |

Contributions by industry, post2010 FF3:
- Brown: Steel -0.135, Ships -0.105, Aero -0.089, BldMt -0.071, Util -0.038.
- Green: RlEst +0.090, Fin +0.080, Telcm +0.054, Drugs -0.018, Fun -0.067.

**Drivers (pre-specified): Steel and Ships**, which together contribute -0.239 of the -0.298.

What this means:
- The negative loading is a Brown-leg value tilt. The Green leg is itself mildly value because of Fin, RlEst and Telcm; only Drugs, and Fun since about 2010, are growth-like.
- Christhian's five Green industries therefore partly offset the exposure; they do not create it.
- In the holdout the Green industries' HML loadings rose (Telcm 0.65, RlEst 0.54, Drugs 0.52, Fin 0.46).
- With 8-and-8 legs the post2010 loading is -0.35. Autos, now a growth industry, contributes -0.060 post2010 and -0.219 in the holdout.

**Rolling 60-month FF3 betas** (`q3_rolling_summary.csv`, `q3_rolling_positive_runs.csv`):
- The GB HML beta is negative in 78% of windows ending 1975-2026 (mean -0.19), 76% in 2010-2026 and 100% of holdout windows (mean -0.31).
- There are two sustained positive runs. One covers windows ending 1983-12 to 1987-03 (40 windows, peak +0.25 in the window ending 1985-03). The other covers windows ending 2008-02 to 2013-10 (69 windows, peak +0.53 in the window ending 2008-12). At both peaks the Brown leg's own HML beta was slightly negative (-0.04 and -0.12) while the Green leg's was well above its 0.10 average (0.21 and 0.41). Both sustained flips therefore combine a temporary loss of the Brown leg's value tilt with an unusually value-tilted Green leg; in the 2008 episode the Green leg supplies most of the +0.53. The other positive runs are short (at most 9 windows, peak at most +0.10).
- The Brown leg's own beta averages 0.29 and is negative in only 9% of windows; the Green leg's averages 0.10.
- Under FF5+UMD the GB beta is negative in 63% of windows (75% since 2010).

**Characteristics** (`q3_bm_link.csv`):
- GB relative log BE/ME is negative in 88.5% of years 1975-2026 (mean -0.255).
- Util and Steel are at or above the 49-industry median in 100% of years and Ships in 94%.
- Drugs is below the median in 98% of years and Fun in 69%; Fin, RlEst and Telcm are at or above it in 96%, 87% and 85%.
- Across the 49 industries, the yearly Spearman correlation between the June rolling HML beta and relative log BE/ME averages 0.468 (t 10.5, NW(4), 52 years).
- The time variation of the GB beta is not explained by the GB BE/ME spread (correlation -0.08, t -0.34).

**Conclusion:** the sign is a persistent value tilt of the Brown leg, while its size varies and is partly absorbed by RMW, CMA and (in the holdout) COMEQ.

## Q4. Uniform cost sensitivity

Files: `q4_costs.csv`, `q4_costs_{corr,team}.tex/_wide.csv`, `q4_breakeven.csv`, `q4_primary.csv`.

**Corrected baseline, 5/5 legs, FF3 hedge. Validation alpha % (t), holdout alpha %, and break-even cost:**

| Strategy | Validation 5 / 10 / 25 bp | Holdout 5 / 10 / 25 bp | Break-even |
|---|---|---|---|
| Original 3m | 1.92 (2.31) / 1.66 (2.02) / 0.89 (1.09) | -1.87 / -2.08 / -2.69 | 42 bp |
| Pure 3m | 2.05 (2.37) / 1.76 (2.06) / 0.89 (1.07) | same as Original 3m | 40 bp |
| Original 6m | 2.25 (2.36) / 2.12 (2.22) / 1.74 (1.80) | -1.70 / -1.89 / -2.47 | 93 bp |
| Pure 6m | 2.51 (2.80) / 2.37 (2.63) / 1.98 (2.13) | same as Original 6m | 100 bp |
| Continuous raw | 0.54 / 0.47 / 0.27 | -0.51 / -0.56 / -0.70 | 46 bp |
| Continuous pure | 0.60 / 0.53 / 0.31 | -0.52 / -0.57 / -0.72 | 47 bp |
| Always-short | 1.47 (1.18) / 1.43 / 1.33 | -1.67 / -1.70 / -1.78 | 211 bp |

- Validation turnover per year: 5.1, 5.8, 2.4, 2.5, 1.3, 1.5 and 0.7, in table order.
- Team baseline break-evens: 37, 37, 111, 108, 53, 53 and 211 bp.
- With the seven-factor FF5+UMD+COMEQ hedge, break-evens fall to 19-50 bp (corrected) and 16-68 bp (team).
- **Holdout alpha before costs is negative in every zero-cost run.** Zero-cost runs exist only for 5-and-5 legs with the FF3 and FF5+UMD+COMEQ hedges. All 28 of their holdout alphas (7 strategies x 2 baselines x 2 hedges) are negative; the highest is -0.39% (Continuous pure, team baseline, FF3 hedge, t -1.35). For example, it is -1.67% for Original 3m and -1.65% for Always-short (corrected, FF3). In these designs no cost level rescues the holdout.
- Other break-evens (corrected, FF3): 27-60 bp for the six signal rules post2010 (always-short 124 bp) and 10-61 bp over the full live sample (always-short 131 bp).

**Primary result:** there is no survivor (`q4_primary.csv`).
- At 5 bp, post2010 alphas are 0.32% to 1.61% (t 0.73 to 1.89) and holdout alphas are -0.51% to -1.87%.
- The best Holm p is 0.838 (Pure 6m post2010, raw p 0.060).

**Last 18 and last 12 months** (corrected, FF3 hedge, FF3 alpha):
- Last 18: all FF3 alphas are negative, for example Always-short -6.19% (t -1.86) at 5 bp.
- Last 12 at 5 bp: Original/Pure 3m +1.15% (t 0.28) and Original/Pure 6m +1.51% (t 0.28); the continuous rules and always-short are negative. Pure equals Original here because the two coincide in the corrected holdout.

## What is left (summary_best_case.csv/.tex, key_numbers.csv, grid_top40.csv)

**Whole grid:**
- 8,091 alpha tests (7,938 net-of-cost strategy alphas and 153 raw-spread alphas, which are unhedged and cost-free). 368 have a positive alpha with p < 0.05; 531 have a negative alpha with p < 0.05.
- **Holm: 0 survivors.** The smallest adjusted p is 0.082, for a negative last-18-month alpha.
- **BH: 0 positive survivors** and 27 negative ones (23 in last18, 4 in the holdout with lead commodity controls).
- The best positive test is Pure 3m in COVID (corrected, 5 bp): p 0.00035, Holm 1.00, BH 0.062.
- The best positive test in post2010 or the holdout is Original 6m post2010 (team baseline, FF5+UMD+COMEQ hedge, 5 bp): 1.36%, t 1.98, p 0.049, Holm 1.00.

**Holdout sign census** (`key_numbers.csv`, `holdout_*` keys; 1,050 net-of-cost holdout regressions, 150 per strategy):
- Six attention-timed rules: 0 of 900 positive. The highest is -0.03% (t -0.08; Continuous pure, 8/8 H, team baseline, FF3 hedge, evaluated on FF5+UMD+COMEQ plus WTI and IMF).
- Always-short: 24 of 150 positive, all with 8-and-8 legs (24 of its 92 8-and-8 rows), team costs, all five hedges and both baselines, evaluated on FF5+UMD+COMEQ (4 rows) or FF5+UMD+COMEQ plus WTI and IMF (20 rows). The largest is +0.42% (t 0.22; 8/8 H, team baseline, FF5+UMD hedge, evaluated with WTI and IMF). With 5-and-5 legs its highest holdout alpha is -0.91%.
- Zero-cost runs: 0 of 28 positive (see Q4).

**Best case per strategy: alpha % (t)**

| Strategy | Best anywhere | Best post2010 | Best holdout | Q2 primary Holm p (post2010 / holdout) |
|---|---|---|---|---|
| Original 3m | 6.15 (4.36), COVID | 1.08 (1.41) | none positive | 1.00 / 0.40 |
| Pure 3m | 6.48 (4.33), COVID | 1.20 (1.50) | none positive | 1.00 / 0.40 |
| Original 6m | 4.41 (3.05), COVID | 1.36 (1.98) | none positive | 1.00 / 0.75 |
| Pure 6m | 4.27 (2.93), COVID | 1.41 (1.98) | none positive | 1.00 / 0.75 |
| Continuous raw | 1.99 (3.48), COVID | 0.32 (1.09) | none positive | 1.00 / 1.00 |
| Continuous pure | 1.99 (3.46), COVID | 0.40 (1.56) | none positive | 1.00 / 1.00 |
| Always-short | 3.87 (2.76), COVID | 1.29 (1.36) | 0.42 (0.22) | 1.00 / 1.00 |
| Raw GB spread | 2.52 (2.57), 1970-2026, 8/8 H, FF5+UMD+COMEQ | 1.71 (1.17) | 1.55 (0.33) | n/a |

- The grid Holm p of every row's best test is 1.00, and no row survives Holm.
- Every strategy's best case sits in the 24-month COVID window, where NW(6) is unreliable.
- The paired holdout bootstraps of continuous vs discrete rules (p about 0.000, `paired|` rows in the ledger) compare strategies at different leverage (see replication audit item 4). They are exploratory.

## Implications for the verdict

- **No defensible alpha is left.** Validation FF3 alphas of 1.8% to 2.6% for the 6-month rules (FF3 hedge, team costs, both baselines, 5-and-5 and 8-and-8 legs; `q1_table1.csv`) come from the design sample. They shrink under richer hedges and fail Holm. In the holdout all six attention-timed rules have a negative alpha in every configuration run. Only the always-short benchmark with 8-and-8 legs has small positive holdout alphas (24 rows, max 0.42%, t 0.22).
- **Richer controls make the strategies look worse.** They add overlay costs and remove return that was commodity exposure.
- **The HML exposure is Brown-leg value** (Steel, Ships), with commodity exposure behind it in the holdout. It is not Green growth. The team hedge already removes most of it: residual loadings post2010 are -0.015 to -0.053 under the team FF3 hedge (corrected baseline).
- **Suggested wording for the report:** the GB spread is "long financials and real estate plus a few growth industries, short value-priced commodity and industrial producers".
- **Costs are not the binding constraint.** In every zero-cost run (5-and-5 legs, FF3 and FF5+UMD+COMEQ hedges, both baselines) the holdout alpha is already negative.
- **Do not implement** remains the verdict, and these tests strengthen it.

## Caveats

- **Short windows:** NW(6) on 12, 18 or 24 observations is unreliable. The grid's most extreme t-stats (negative, last18) and every strategy's best case (COVID) come from such windows. t(n-k) p-values mitigate this but do not fix the variance estimate.
- **Commodity controls:**
  - WTI and IMF are monthly-average prices, so they are time-averaged and partly lead month-end returns; the "+lead" evaluation set addresses this.
  - As non-traded controls they make the intercept a conditional alpha, not a tradable one.
- **COMEQ overlap:** COMEQ contains Mines, which is also in the 8/8 Brown leg. FF5+UMD results without COMEQ are reported and agree.
- **Dependent grid:** Original = Pure in the corrected holdout, 8/8 H = 8/8 M for the strategies, and always-short is identical under both baselines. Holm is valid but conservative here. Cite the 14-test primary families.
- **Zero-cost coverage:** gross runs exist only for 5-and-5 legs with the FF3 and FF5+UMD+COMEQ hedges. Statements about gross holdout alphas do not extend to 8-and-8 legs or the other hedges.
- **Q2 primary not strictly blind:** its configuration's alphas were printed in a smoke test four minutes before the docstring was written (see the timing record above).
- **Inherited from the team design:**
  - The static emissions snapshot introduces mild look-ahead into leg formation.
  - Costs are linear, with no market impact or shorting costs.
  - The FF5 file's SMB differs from the team SMB.
- **FF3+UMD start date:** the set starts in 1963-07 because UMD is loaded through the FF5 file. Strategies start in 1993, so this has no effect.
- **Descriptive only:** the rolling industry betas and BE/ME links are not trading inputs. RlEst's 1990 BE/ME value is an outlier in the Ken French file.

## Ledger codes

The ledger (`tests_ledger.csv`) has 13,482 tests: 46 primary, 5,562 robustness and 7,874 exploratory (`n_ledger_*` keys in `key_numbers.csv`).

Test ID patterns:
- `strat|legs|baseline|hedge|costs|strategy|window|eval|alpha` (the last field can also be `mean` or `b_HML`).
- `spread|legs|window|eval|alpha` (or `b_HML`).
- `industry|name|model|window|coef`.
- `boot|...` and `paired|...` for the full-mode bootstraps.
- `comeq|series|corr_X` (X = WTI, IMF, WTI_lead, IMF_lead, Mkt-RF, brown) and `comeq|series|ff5u_alpha` (spanning regression on FF5+UMD), for COMEQ, COMEQx and the four industries.
- `bmlink|...`.

Field values:
- **legs:** L5 = 5 and 5; L8H and L8M = 8 and 8 with Hardw or MedEq.
- **baseline:** `team` or `corr`.
- **hedge:** FF3, FF3U, FF5U, FF5UC, FF5UCx.
- **costs:** team, u0, u5, u10, u25.

The whole-grid family is the `strat|...|alpha` and `spread|...|alpha` rows, excluding gross (u0) runs; the `comeq` spanning alphas are outside it.

## Output files

**Code:** `/home/hashim/projects/GA/project/research/modules/M2_christhian_tests/run.py` (entry point) and `helpers.py`. The verifier's independent scripts are in `modules/M2_christhian_tests/verify/`.

**Tables** (`/home/hashim/projects/GA/project/research/outputs/tables/M2_christhian_tests_*`):
- Grid and summary: `strategy_grid.csv`, `tests_ledger.csv`, `key_numbers.csv`, `grid_top40.csv`, `primary_all.csv`, `summary_best_case.csv/.tex`.
- Q1: `q1_leg_composition.csv`, `q1_table1.csv`, `q1_table1_corr.tex`, `q1_table1_corr_wide.csv`, `q1_table1_team.tex`, `q1_table1_team_wide.csv`, `q1_comparison.csv`, `q1_primary.csv`.
- Q2: `q2_comeq_justification.csv/.tex`, `q2_spread_controls.csv/.tex`, `q2_primary.csv`, `q2_strategy_controls.tex`, `q2_strategy_controls_wide.csv`, `q2_hedge_cost_post2010.csv`, `q2_hedge_cost_change.csv`, `q2_table1.csv`, `q2_comparison.csv`.
- Q3: `q3_primary.csv`, `q3_industry_loadings.csv`, `q3_hml_decomposition.csv`, `q3_industry_hml.tex`, `q3_hml_contributions.tex`, `q3_hml_contributions_wide.csv`, `q3_rolling_hml.csv`, `q3_rolling_summary.csv`, `q3_rolling_positive_runs.csv`, `q3_log_bm.csv`, `q3_bm_link.csv`, `q3_bm_cross_section.csv`.
- Q4: `q4_costs.csv`, `q4_costs_corr.tex`, `q4_costs_corr_wide.csv`, `q4_costs_team.tex`, `q4_costs_team_wide.csv`, `q4_breakeven.csv`, `q4_primary.csv`.

**Figures** (`/home/hashim/projects/GA/project/research/outputs/figures/M2_christhian_tests_*.pdf/.png`): `rolling_hml_industries`, `hml_spread_and_bm`, `log_bm_industries`, `hml_decomposition`, `alpha_t_by_controls`, `cost_sensitivity`.

## Response to verification

Every point below was re-derived from the current CSVs after rerunning run.py. Code changes were made before this round's rerun (run.py edits for items 3, 8, 12, 13, 14, 16 and the holdout census). In this round `key_numbers.csv` gained the census configurations and ledger counts. All other tables are byte-identical to the first post-verification rerun. Against the round-1 verified run, every previously reported number is unchanged (the file-level changes are listed under Run).

1. **Holdout overreach (Answer, Implications). Fixed.** Re-derived from `strategy_grid.csv`: 24 of 1,078 holdout regressions are positive, all Always-short with 8-and-8 legs (12 L8H, 12 L8M), team costs, all five hedges, both baselines, evaluated on E:FF5UC (4) or E:FF5UC+cmdty (20); max +0.42% (t 0.22). The six signal rules are negative in all 900 of their net-of-cost holdout rows (highest -0.03%). The Answer, Implications and a new "Holdout sign census" block now use the verifier's wording plus these counts. run.py writes the census to `key_numbers.csv` (`holdout_net_*`, `holdout_gross_*`).
2. **Q4 zero-cost qualifier. Fixed** in Q4, Conventions, Implications and Caveats. One correction to the verifier's detail: the highest gross holdout alpha, -0.39%, is Continuous pure, team baseline, **FF3** hedge (t -1.35), not FF5UC (`holdout_gross_max_alpha_config` = Continuous pure|L5|team|FF3|E:FF3). The FF5UC team Continuous pure gross holdout alpha is -0.47%.
3. **Turnover mislabel. Fixed.** The text now gives both: total turnover +24% to +37% (always-short +127%) and overlay turnover +35% to +54% (always-short +163%), from the new `q2_hedge_cost_change.csv` (corrected baseline, post2010). Original 3m total 4.80 to 5.99, cost drag 0.53% to 0.85%.
4. **Last-12 wording. Fixed:** Original/Pure 3m +1.15% (t 0.28) and Original/Pure 6m +1.51% (t 0.28); the continuous rules and always-short are negative (`q4_costs.csv`, u5, corrected, FF3).
5. **Break-even range. Fixed:** 27-60 bp for the six signal rules post2010 (always-short 124 bp) and 10-61 bp full live (always-short 131 bp), from `q4_breakeven.csv`.
6. **Grid description. Fixed** everywhere as "8,091 alpha tests (7,938 net-of-cost strategy alphas and 153 raw-spread alphas)". The summary .tex caption says the same, and `key_numbers.csv` carries both counts.
7. **"No positive commodity-controlled alpha". Fixed.** The Q2 primary result now reads "no commodity-controlled alpha is significantly positive" and reports that 6 of 7 post2010 point estimates are positive (-0.005% to 0.59%, t at most 0.83).
8. **Rolling-beta dates. Fixed** using the new `q3_rolling_positive_runs.csv`. FF3 positive runs: windows ending 2008-02 to 2013-10 (69 windows, peak +0.53 at 2008-12) and 1983-12 to 1987-03 (40 windows, peak +0.25 at 1985-03). The file also records that the Brown leg's HML beta was negative at both peaks (-0.12, -0.04), which is now stated in the text.
9. **Residual HML mixing hedges. Fixed:** "-0.015 to -0.053 under the team FF3 hedge (corrected baseline)". The team-baseline range (-0.018 to -0.061, t down to -2.36) and the FF5UC range (-0.024 to -0.079) are reported separately in Q2.
10. **"Halve the loading". Fixed:** 1970-2026 -0.23 to -0.11 (about half); post2010 -0.30 to -0.21 (about 30%), -0.19 with WTI and IMF.
11. **Rounding. Fixed:** IMF t post2010 = 0.65 (0.6549); Steel + Ships = -0.239.
12. **Inherited team flag in q1_comparison.csv. Fixed in code:** `significant_after_multiple_testing` is renamed `team_holm_flag_normal_p` in both `q1_comparison.csv` and `q2_comparison.csv`. `active_months_full` is renamed `team_active_months_full_nonzero_net` (audit item 6). A code comment and the Q1 section explain why neither may be cited.
13. **Ledger completeness. Fixed:** the ledger now has `comeq|<series>|ff5u_alpha` spanning-alpha tests for COMEQ (alpha -0.89%, t -0.24, p 0.81, R2 0.373) and COMEQx (-1.42%, t -0.35, R2 0.451), and for the four industries. It also has the lead, market and Brown-leg correlation tests (`corr_WTI_lead`, `corr_IMF_lead`, `corr_Mkt-RF`, `corr_brown`). The comeq rows go from 12 to 42 and the ledger from 13,452 to 13,482 (the 30 new rows are all exploratory). They are outside the grid family, which stays at 8,091.
14. **Tex caption. Fixed:** `q2_comeq_justification.tex` now says correlations over 1992-02 to 2026-06, n = 413, and the FF5+UMD regression over 1992-02 to 2026-07, n = 414. Both come from the data, not hard-coded.
15. **Process.** This file is returned to the orchestrator in full for saving; no .md file was written by the subagent.
16. **Pre-specification wording. Resolved with a timestamped record, and the claim is weakened.** The builder transcript (wf_bd8d2a66-0fa, agent a7dd3a997df54dc45) shows run.py first written at 10:06:36 UTC. Before that came the data checks (09:59:44) and a smoke test (10:02:26) that printed the Q2-primary configuration's post2010 and holdout alphas. The docstring and this file now say "stated in the run.py docstring" and disclose that the Q2 primary is not strictly blind. The claim "fixed before any M2 result existed" is withdrawn.

**Additional correction found while re-deriving:** Implications said the 6-month rules' validation alphas were "1.5% to 2.5%". Across the FF3-hedge, team-cost configurations (both baselines, 5/5 and 8/8) they are 1.80% to 2.60% (`q1_table1.csv`), and the text now says 1.8% to 2.6%.
