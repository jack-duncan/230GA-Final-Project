# M3 alpha vs beta: adversarial verification

VERDICT. Every decision-relevant number was recomputed independently and reproduces. This covers BOND, the GB BOND loading, the holdout alphas with and without BOND, the Lewellen-Nagel timing term and its bootstrap, the Ferson-Schadt statistics, the BOND-hedge rerun, the attribution and the macro-state result. The three primary tests stand as reported, and "Do not implement" is unaffected.

Five statements in the text overreach or are not robust, and the ledger misses some quoted tests. So `all_confirmed = false`. The required fixes are wording and ledger changes; none changes a primary result.

## 1. What was run

- `cd /home/hashim/projects/GA/project/research && uv run python modules/M3_alpha_beta/run.py` completed in 146 s, exit 0. It printed a ledger of 4,781 tests (33 primary) and 1,117 key numbers.
- Verify scripts are in `/home/hashim/projects/GA/project/research/modules/M3_alpha_beta/verify/`, with outputs in `verify/out/`. None imports `m3lib.py` or `run.py`. They use only `lib/common.py` loaders, `lib/team_pipeline.py` and M8's `build_bond`, which is used only for comparison.
  - `vlib.py` holds all of my own statistics code: Bartlett HAC, t(n-k) p, Wald, Holm, backward rolling OLS, the Lewellen-Nagel identity and a circular block bootstrap with a different RNG seed. It also builds BOND from scratch, with finite-difference duration and convexity and my own dirty-price repricing.
  - `v1_bond.py`: BOND construction and validation.
  - `v2_gb_bond.py`: primary (i), the leg split, rolling 60-month betas and BOND_eom.
  - `v3_holdout_alpha.py`: primary (ii), both baselines rebuilt through `run_pipeline`, the hedged Brown leg and the exchange-1 fact-check. `v3b_bond_hedge.py` reruns the pipeline with BOND and UMD in the hedge.
  - `v4_lewellen_nagel.py`: primary (iii), with a look-ahead fuzz test, the COVID terms and the D = strategy - pi x benchmark decomposition. `v4b_block_sensitivity.py` tries bootstrap blocks of 6, 12, 24 and 36 months.
  - `v5_ferson_schadt.py`: instruments rebuilt from raw FRED files, standardization checked for look-ahead, and three versions of the joint test: fixed-design bootstrap, wild block bootstrap and classical F. `v5b_fs_seeds.py` checks Monte Carlo stability.
  - `v6_attribution.py`: COVID and holdout attribution, and position overlap with the benchmark.
  - `v7_macro_state.py`: the High-rates slope difference.
  - `v8_ledger.py`: ledger audit.
  - `v9_alpha_sweep.py`: every model and period for GB and the strategies, plus the BOND_eom timing term.

## 2. Recomputed numbers

| # | Claim in FINDINGS | Independent result | Status |
|---|---|---|---|
| 1 | BOND = y_{t-1}/12 - D_{t-1} dy + 0.5 C_{t-1} dy^2 - RF_t | Mine matches M8 `build_bond` to 2.9e-9 (finite-difference duration) and M3's published BOND to 2.9e-9. Exact repricing is identical. BOND_t uses y_{t-1} (May-2022 2.90%) and y_t (Jun-2022 3.14%). | Confirmed |
| 1a | 2022 -15.0%, worst since 1954; Damodaran -17.8%; corr 0.991 (72 yrs), 0.987 (1993-2025); MAD 0.85 pp | -15.04%, worst year (2013 second, -7.96%); -17.83%; 0.9907, 0.9870; 0.854 pp | Confirmed |
| 1b | Excess 2.16%/yr, vol 6.95%, Sharpe 0.31, AR(1) 0.31, D 7.56 (5.04 to 9.68), within 5.4 bp of exact, corr 0.99999 | 2.163%, 6.948%, 0.311, 0.311, 7.563 (5.036 to 9.682), 5.37 bp, 0.999994 | Confirmed |
| 1c | Holdout BOND -3.68%/yr, 2022-2024 -8.37%/yr, BOND_eom AR(1) 0.08 | -3.681%, -8.371%, 0.082 | Confirmed |
| 2 | Primary (i): GB FF5+UMD+BOND BOND loading, full 0.132 (t 2.60, p 0.0095, Holm 0.019); post-2010 0.088 (t 0.60, p 0.549) | 0.1319 (2.603, 0.0095, 0.0189); 0.0884 (0.600, 0.549) | Confirmed |
| 2a | Legs, full: Green +0.068 (t 2.10), Brown -0.064 (t -1.67). Post-2010: +0.097, +0.008. FF3 HML -0.233 (t -4.63), -0.298 (t -5.74) | 0.0683 (2.10), -0.0635 (-1.67); 0.0966, 0.0082; -0.233 (-4.63), -0.298 (-5.74) | Confirmed |
| 2b | Rolling 60-month BOND beta means 0.134 / -0.203 / +0.380, min -0.60 (2020-01), max 0.65 (2022-05); BOND_eom 1990-2026 0.082 (t 1.19) vs 0.129 (t 1.65) | Identical | Confirmed. The full-sample loading comes from 1970-1989 (0.214, t 3.04). Over 1970-2009 it is 0.112 (t 1.92). The t is stable in the lag choice (2.55 to 2.72 for NW 3 to 18). |
| 3 | Primary (ii): all 12 FF3 and FF3+UMD+BOND holdout alphas, t, p, Holm and Wald p in the Section 4(ii) table | All 24 cells match. Max abs difference vs `holdout_alpha.csv`: 4.6e-12 (alpha), 5.5e-10 (Wald p). Holm minimum 0.155 (team); none significant (corrected). | Confirmed |
| 3a | FF5+UMD+BOND holdout: team -0.70% to -4.74%; corrected -0.85% to -3.18% | Same | Confirmed |
| 3b | Hedged Brown holdout alpha +2.82% (t 0.95) under FF3; +2.86% (t 0.90) under FF3+UMD+BOND. d10y 0.0010 (t 0.05). Exchange-1 alphas -0.67% to -4.78%; with BOND+COM -0.68% to -4.81% | Same | Confirmed |
| 3c | BOND in the rolling hedge: every cell of the Section 4(ii) hedge table; residual BOND loadings -0.03 to -0.20 (team Orig 6m -0.20, t -2.22) | Every cell identical | Confirmed |
| 4 | Primary (iii): timing term GB -1.72, Orig 3m -0.99, Pure 3m -1.06, Orig 6m -1.04, Pure 6m -1.07, Cont raw -0.57, Cont pure -0.60 (%/yr); 4 of 6 strategy terms significant after Holm | Point estimates match to 1e-4, and the identity gap is 0. Bootstrap p with my own seed: 0.130, 0.0016, 0.0004, 0.034, 0.034, 0.0024, 0.0028. Holm gives the same 4 of 6. | Confirmed |
| 4a | Robustness of (iii) | Blocks of 6, 12, 24 and 36 months all give 4 of 6 significant after Holm (Orig 6m and Pure 6m Holm 0.07 to 0.18). A look-ahead fuzz test shows the betas for month t use only t-36..t-1 (the first changed beta is the month after the perturbation). | Confirmed |
| 4b | Always-short Brown -1.35% (p 0.035); hedged Brown +1.94% (p 0.020); Brown leg +2.31% (p 0.014); BOND share -0.36 to -0.60; 24-month windows -0.60 to -1.54 | -1.35 (0.036); +1.94 (0.024); +2.31 (0.013); -0.36 to -0.60; -0.60 to -1.54 (p 0.006 to 0.044) | Confirmed |
| 4c | D timing -0.47, -0.48, -0.16, -0.11, -0.27, -0.28. COVID D 5.4% and 5.8% (t 2.35, 3.15); in-window 3.0% and 3.4% (p 0.11, 0.09). Holdout D t -2.23 to -2.28 and -1.44 to -1.51. COVID backward conditional alpha 8.3% (benchmark 8.9%) | Same values; bootstrap p within Monte Carlo noise | Confirmed |
| 5 | Ferson-Schadt conditional alphas: GB full 0.77% (t 0.57), post-2010 0.35% (t 0.17); strategies 0.29% to 1.67% (Pure 6m p 0.058) | Same. Instruments match M3's to 8.9e-16, and the expanding standardization is past-only (fuzz test). | Confirmed |
| 5a | Joint test of c = 0, fixed-design bootstrap p: GB 0.073 / 0.159; strategies 0.066, 0.038, 0.170, 0.121, 0.034, 0.039; null q95 71 to 241 | W is identical. Fixed-design p across 5 seeds x 999 reps: Pure 3m 0.031 to 0.045, Pure 6m 0.141 to 0.177, Cont raw 0.029 to 0.043, Cont pure 0.034 to 0.052. A wild block bootstrap gives 0.38 to 0.62 for all six strategies. | Numbers reproduce, but the inference is not robust (Fix 4) |
| 5b | Dummy alphas: holdout team Orig 3m -4.4% (p 0.013), Pure 3m -2.8% (p 0.039), corrected -1.4% to +0.1% (p >= 0.27); COVID Pure 6m 7.2% (p 0.002), benchmark 6.1% (p 0.026) | Same | Confirmed |
| 6 | COVID attribution, corrected Pure 6m: net 6.87 = leakage 4.76 (Mkt 1.97, SMB 2.14, HML 1.49, UMD -0.50, BOND -0.35; p 0.037) + residual 2.21 (t 1.27) - cost 0.11. 24-month: 6.26 / 0.71. In-period: 6.38 / 0.49 (t 0.24). Positions equal Always-short in 24/24 months (team 23/24) | Every number identical; net = leakage + residual + cost to 1e-12 | Numbers confirmed; interpretation overreaches (Fix 2) |
| 6a | Holdout attribution: corrected Pure 6m leakage -0.24 (p 0.74), residual -1.14 (t -0.86), cost -0.46; team residual -2.19 (t -1.75); BOND leakage -0.02 to -0.20 | Same | Confirmed |
| 7 | Macro state, High rates: diff 0.229 (t 1.83, p 0.068), normal p 0.067, Holm 0.585; BOND(t+1) control 0.231 (t 1.86); corrected 0.035 (p 0.75), purified 0.041 (p 0.72); 47 of 47 holdout months high-rate | Same | Confirmed |
| 8 | GB alpha: full -0.6% (CAPM) to +2.2% (FF5+UMD, t 1.60); post-2010 -1.1% to -0.2%; holdout -3.8% to -4.8%. Strategies post-2010 -0.04% to 1.44%, t < 1.8; corrected Pure 6m validation 2.34% (t 2.54) | Same | Confirmed, but GB is significant in last12 and last18 (Fix 1) |

## 3. Look-ahead, windows, signs and small samples

- Look-ahead:
  - Rolling betas for Lewellen-Nagel and the structural betas are strictly backward. Fuzz-tested.
  - Team hedge betas are lagged one month (`betas.shift(1)`; P&L is h_{t-1}(R^B_t - b_{t-1}'f_t)). M3's attribution uses the same timing.
  - Ferson-Schadt instruments enter as z_{t-1}; INFL and CFNAI carry an extra publication lag. The expanding standardization uses only rows up to z_{t-1}.
  - Centered-window attribution uses future data and is labeled ex post.
  - One negligible exception: the interpolated Oct-2025 CPI uses the Nov-2025 print (released mid-Dec 2025), and it enters the instrument for the Dec-2025 return, about three weeks early for one value.
  - GS10-based BOND is a monthly-average return: BOND_t correlates 0.58 with BOND_eom_{t-1}, so part of it is already realized at t-1. This does not bias the regressions toward the claims, and the month-end hedge robustness covers the tradability concern.
- Windows: full 1970-01 to 2026-07 (n = 679), strategies 1999-03 on, post-2010 n = 199, holdout n = 48, COVID n = 24, macro-state holdout n = 47 (the forward residual is lost). All as stated.
- Signs: GB = Green - Brown; a positive BOND loading means Green has longer duration; the strategies hold negative (short) Brown positions; a negative timing term means beta was high when the factor return was low. All consistent.
- Small samples: every regression p uses t(n-k), and the Holm families match the pre-specification (2, 6+6 and 6+6, 7). NW(6) on 12 to 24 observations is still unreliable; see Fix 1.
- Pre-specification: I found no file that dates the docstring's primary list. The scratchpad snapshots are M8's. This remains an honest, unverifiable caveat, as FINDINGS already says.

## 4. Required fixes

1. **GB is not insignificant "in every model and period"** (bottom line, Section 5, Section 9.1).
   - In [exposures], GB's alpha is large, negative and nominally significant in 7 of 14 short-window fits:
     - last18: FF3 -19.2% (t -2.79, p 0.014), FF3+BOND -19.2% (p 0.021), FF3+UMD+BOND -16.1% (p 0.033);
     - last12: FF3 -32.8% (t -5.65, p 0.0005), FF3+BOND -32.8% (t -10.0, p 2e-5), FF3+UMD+BOND -25.3% (p 0.011), FF5+UMD+BOND -39.3% (p 0.046).
   - The brief asks about exactly this window. Restate as: no significant alpha in the full, post-2010, validation or holdout windows. Over the last 12 to 18 months GB (Green minus Brown) shows a large negative alpha, but those fits have 4 to 14 df with NW(6), are exploratory and are not multiplicity-adjusted.
   - Replace "No return in this project is alpha" with "No return shows alpha that survives out of sample".
2. **The COVID gain was not earned through momentum, and duration is method-dependent** (bottom line, Section 6 bullet 3, Section 9.4).
   - UMD averaged -0.58%/yr in 2020-2021. Despite the loading of 0.30 (t 9.0), UMD contributed -0.50% (structural 36-month) and -0.17% (in-period regression).
   - BOND contributed -0.35% (structural) but +2.19% (regression).
   - Market (+1.97 / +3.34) and size (+2.14 / +1.79) are the contributors both methods agree on.
   - Say: the gain came mainly from market and size exposure the lagged FF3 hedge left open. The UMD and BOND exposures were open too, but momentum added nothing, and duration's contribution depends on the method.
3. **"Rates helped the short-Brown strategies in the holdout"** (Section 4(ii) "Why alphas fall", Section 9.2) is method-dependent.
   - By regression, the insignificant negative BOND loadings times -3.68%/yr give about +0.1 to +0.5 pp.
   - By the structural attribution in the same FINDINGS (Section 7), BOND leakage is -0.02 to -0.20 pp.
   - Say rates were immaterial either way. The conclusion that BOND does not explain the holdout is unaffected.
4. **Ferson-Schadt joint test: "only the continuous strategies' betas move measurably with the macro instruments" is not robust** (Section 5).
   - The fixed-design bootstrap resamples residuals across months while keeping X fixed. That breaks the link between residual size and position size: the 3-month holds have zero position in 115 to 123 of 199 post-2010 months, and the continuous rules' positions vary strongly in size.
   - A wild block bootstrap keeps each month's residual in its own month and flips signs by 12-month block. It gives p = 0.56 to 0.60 for the continuous rules and 0.38 to 0.62 for the others (GB full 0.085, post-2010 0.28).
   - The fixed-design p itself moves 0.029 to 0.052 across seeds. The classical nested F assumes homoskedasticity.
   - Replace with: "no robust evidence that strategy betas vary with the instruments". Report the wild bootstrap p alongside the fixed-design p.
5. **Ledger completeness.** These quoted inferential results have no ledger row:
   - the 24-month structural attribution (COVID leakage p 0.006, residual p 0.72);
   - the in-period regression attribution residuals (COVID t 0.24);
   - the D = strategy - pi x benchmark mean, COVID mean, COVID in-window alpha (p 0.11, 0.09) and holdout mean tests (t -2.23 to -2.28, -1.44 to -1.51). Only D's timing term is logged.

   Add them and update "4,781 tests" in caveat 5. Optionally also log the quoted HML loadings (t -4.63, -5.74).
6. **Small label corrections.**
   - (a) Section 4(ii): "With BOND in place of d10y, the hedged Brown leg's holdout BOND loading is -0.015 (t -0.07)" is the BOND-only spec. The like-for-like BOND+COM swap gives -0.009 (t -0.04).
   - (b) Section 4(iii) BOND_eom: Pure 3m's p is 0.053 in M3's run and 0.049 with my seed, so "only the two continuous strategies at p < 0.05" depends on the seed. Say: the 3-month holds and the continuous rules have p 0.04 to 0.07; the 6-month holds 0.22 to 0.35.
   - (c) Section 5 "FF5 full: HML -0.14, RMW -0.15, CMA -0.23" are the FF5+UMD (or FF5+UMD+BOND) loadings. FF5 alone gives -0.11, -0.15, -0.25.

## 5. What is solid

- BOND is correctly built, correctly timed and externally validated.
- Primary (i): the full-sample GB duration tilt is modest and rests on 1970-1989; since 2010 there is none.
- Primary (ii): adding UMD and BOND makes every holdout alpha slightly more negative, and no Holm-adjusted p is below 0.15.
- Primary (iii): the beta-timing term is negative and significant for 4 of 6 strategies after Holm, robust to the block length. The no-timing benchmark shows the same term, so it is not attention timing.
- Putting BOND in the hedge does not rescue the holdout.
- The High-rates macro-state result does not survive real-time signals.
- The 6-month rules' COVID return is the Always-short Brown return month by month.

## Round 2

VERDICT (round 2). All six round-1 fixes are resolved. M3's one qualification (Fix 5, the in-period regression residual) is a valid rebuttal. I rechecked every number the fixes added or changed with my own code, and each one reproduces. No published number moved: the rerun is bit-identical to the tables M3 wrote, and every table, ledger row and key number that existed before the fixes is unchanged. The primary results and "Do not implement" stand. `all_confirmed = true`. Three optional wording points are listed in R2.5. None is required.

### R2.1 What was run

- `cd /home/hashim/projects/GA/project/research && uv run python modules/M3_alpha_beta/run.py`: exit 0, 199 s. It reports 6,360 ledger tests (33 primary) and 1,990 key numbers.
- Determinism (`verify/v11_round2_tables.py`, output `verify/out/v11_determinism.csv`): all 33 M3 CSV tables from this rerun are identical to the copy taken just before it. Maximum numeric difference is 0 and the text columns are equal.
- All ten round-1 scripts were rerun (v1 to v4b, v6 to v9), each with exit 0, along with v5 and v5b. Every round-1 output CSV is reproduced with maximum difference 0; only `v8_ledger.csv` changes, because the ledger gained rows. Comparisons with the published tables are unchanged: BOND 2.9e-9, holdout alphas 4.6e-12, Wald p 5.5e-10, and the standardized instruments 8.9e-16.
- New round-2 scripts, which again import nothing from `m3lib.py` or `run.py`:
  - `v10_round2.py`: GB short-window alphas under NW(6), NW(2) and classical OLS standard errors; GB alphas in every long window; FF5 loadings; COVID factor means and contributions; holdout BOND and UMD contributions; zero-position months; mean tests on D. Outputs are `v10_gb_short_window.csv`, `v10_holdout_contrib.csv` and `v10_D_means.csv`.
  - `v11_round2_tables.py`: the ledger audit after Fix 5; my own Benjamini-Hochberg (BH) adjustment of the 1,080 timing tests, with spot-check regressions; the Ferson-Schadt table claims; determinism.
  - `v12_prefix_compare.py`: compares the pre-fix snapshot M3 took at 06:29 (after round-1 verification, before any code change; session scratchpad `m3_before/`) with the current tables. Output is `v12_prefix_compare.csv`.
  - The paths to the scratchpad snapshots in v11 and v12 are specific to this session.

### R2.2 Were only additions made?

M3 says the fixes only add columns, tables and ledger rows. `v12_prefix_compare.py` confirms it:
- All 28 pre-existing result tables have the same rows, no removed columns, and maximum numeric difference 0 with equal text. Only three tables gained columns: `holdout_alpha` (+2: the BOND and UMD contributions), `ferson_schadt` (+2: wild p and the wild null q95) and `bond_hedge_rerun` (+1).
- All 4,781 original ledger rows and all 1,117 original key numbers are present and identical.
- Three tables are new: `factor_means`, `fs_boot_seeds` and `gb_short_window_alpha`.
- The three changed .tex tables (`ferson_schadt`, `holdout_alpha`, `attribution`) compile with tectonic. All five figures exist as .pdf and .png.

### R2.3 Fix-by-fix

| Fix | M3 response | Independent re-derivation | Status |
|---|---|---|---|
| 1. GB not insignificant everywhere | New [gb_short_window_alpha]; bottom line, Section 5 and Section 9.1 reworded; opening sentence changed | Short-window fits with p < 0.05: 7 of 14 with NW(6), 5 of 14 with NW(2), 0 of 14 with classical OLS (\|t\| 0.82 to 1.67, p 0.155 to 0.443). The seven NW(6) hits have 4 to 14 df. Matches M3's table to 1.1e-10 (alpha) and 4.7e-9 (t). Raw GB mean is -14.7% (last 18 months) and -19.9% (last 12), with NW(6) t -1.83 and -2.19. Smallest p across the 7 models in each long window: full 0.110, post-2010 0.606, validation 0.427, COVID 0.126, 2022-2024 0.274, holdout 0.328. Also confirmed: full CAPM t -0.40; post-2010 range -1.20% (FF3+BOND) to -0.16%. | Resolved |
| 2. COVID gain not through momentum | Section 6, bottom line and Section 9.4 now name market and size; new [factor_means] | UMD earned -0.58%/yr and BOND +2.84%/yr in COVID. Contributions, corrected Pure 6m, in the order Mkt / SMB / HML / UMD / BOND: structural 36-month 1.97 / 2.14 / 1.49 / -0.50 / -0.35 (leakage p 0.036); structural 24-month 2.59 / 3.53 / 0.72 / -0.81 / +0.23 (leakage p 0.006, residual 0.71 with p 0.72); in-period 3.34 / 1.79 / -0.76 / -0.17 / +2.19 (residual 0.49, t 0.24). Market and size are positive under all three methods; UMD is negative under all three. The FF5+UMD+BOND fit over COVID gives UMD 0.31 (t 4.49), BOND 0.76 (t 2.29) and alpha 1.4% (t 0.59). | Resolved |
| 3. "Rates helped" depends on the method | New `contrib_BOND_FF3+UMD+BOND` column; Sections 4(ii), 7 and 9.2 reworded | 12 x b_BOND x mean(BOND): team +0.06 to +0.51 pp, corrected +0.06 to +0.23 pp (matches the table to 4e-10 pp). Structural 36-month BOND leakage in the holdout is -0.02 to -0.20 pp; the 24-month version gives -0.06 to +0.02. Adding UMD and BOND lowers alphas by 0.05 to 0.66 pp. Holdout net losses are 0.48% to 3.82%. Team BOND loadings are -0.02 to -0.14 (t -0.87 to -1.69). | Resolved |
| 4. Ferson-Schadt joint test not robust | Wild block bootstrap added in `m3lib.ferson_schadt` (restricted residual kept in its own month, one Rademacher sign per 12-month block, separate RNG stream); [fs_boot_seeds] added; Section 5 reworded | I reviewed the code and it is a correct implementation. My own wild bootstrap (seed 7) gives, for the corrected strategies post-2010: 0.620, 0.426, 0.539, 0.498, 0.563, 0.569. For GB: 0.085 (full) and 0.277 (post-2010). Across my 5 seeds plus a 4,999-rep run the wild p ranges are Pure 3m 0.38 to 0.43, Pure 6m 0.50 to 0.52, Cont raw 0.56 to 0.60 and Cont pure 0.57 to 0.58. M3 reports 0.603, 0.397, 0.524, 0.485, 0.558, 0.554 (0.397 to 0.623 across its seeds), and GB 0.086 / 0.274. The fixed-design p ranges across my seeds (Pure 3m 0.031 to 0.045, Cont raw 0.029 to 0.043, Cont pure 0.034 to 0.052) are slightly wider than M3's, and both straddle 0.05. That supports "not robust". Classical F for the continuous rules: 0.038 and 0.024. "No robust evidence" is the right conclusion. | Resolved |
| 5. Ledger completeness | Added 1,579 rows; one qualification | 6,360 = 4,781 + 1,579. M3's breakdown adds up exactly: 64 + 96 + 1,232 + 3 + 28 + 84 + 54 + 14 + 4. No duplicate ids, no missing p-values, and all 33 primary rows carry Holm notes. Every quoted test I flagged now has a row, for example: 24-month COVID leakage 0.0626 (p 0.0063) and residual 0.0071 (p 0.718); D COVID means p 0.028 and 0.0045; D in-window alphas p 0.113 and 0.091; D holdout means p 0.027 and 0.031; GB FF3 HML loadings for full and post-2010. **The qualification is valid.** `Q1.alpha.Pure 6m\|corrected\|FF3+UMD+BOND\|covid` is 0.004863 with p 0.8106, exactly the in-period residual (0.49%, t 0.24), and `run.py` now asserts the equality. The new pre_covid rows fill the only window Q1 lacks. | Resolved (rebuttal accepted) |
| 6a. BOND+COM label | Relabelled | Hedged Brown holdout BOND loading: BOND+COM -0.009 (t -0.04); BOND only -0.015 (t -0.07); FF5+UMD+BOND +0.013 (t 0.07) | Resolved |
| 6b. BOND_eom timing p | Reworded; seed dependence flagged | M3's p-values: 0.070, 0.053, 0.244, 0.352, 0.049, 0.037. Mine (different seed): 0.056, 0.049, 0.225, 0.333, 0.047, 0.036. Point estimates are -0.32% to -0.54% in both. The text (0.037 to 0.070 for the 3-month holds and continuous rules; 0.24 to 0.35 for the 6-month holds) matches M3's run. | Resolved |
| 6c. FF5 loadings | Relabelled | FF5 alone: HML -0.112 (t -1.90), RMW -0.148 (t -1.90), CMA -0.249 (t -2.80). FF5+UMD: -0.140, -0.145, -0.227. | Resolved |

### R2.4 Other changed or new statements, re-derived

- **Zero-position months (my round-1 error).** Over 2010-01 to 2026-07 the 3-month holds have no position in 124 months (Orig 3m, both baselines), 118 (team Pure 3m) and 116 (corrected Pure 3m). The count is the same whether it uses h_{t-1} or h_t. M3's "116 to 124" is correct. My round-1 "115 to 123" was my own miscount, not a timing difference. It does not affect Fix 4.
- **Timing-test BH counts.** I applied my own BH adjustment to all 1,080 p-values:
  - 48 survivors pooled: 45 HML and 3 BOND. The BOND survivors are team Orig 3m TM and HM (multifactor) and team Pure 3m TM (single), all in the holdout, all positive, all with q 0.041.
  - Within each group of 90, no BOND test survives. Multifactor HML survivors: 16 (HM) and 21 (TM). Counts at p < 0.05: Mkt-RF 2 and 3; BOND 7 and 7; HML 21 and 28, all positive.
  - GB's tests at p < 0.05 are HM Mkt-RF over the full sample (t -2.11, which my own regression reproduces) and the BOND TM and HM tests in the validation window (negative) and the holdout (positive).
  - Always-short Brown HML TM, 1999-2026: t 3.24.
- **In-window versus expanding standardization.** The largest difference in conditional alpha is 0.36 pp (full), 0.24 (post-2010), 0.13 (1999-2026) and 0.52 (validation, Green leg). As stated.
- **Section 4(i) short-window loadings.** GB COVID BOND loading 1.244 (t 5.87, FF5+UMD+BOND). Brown leg last18: 1.585 (t 2.28, 10 df).
- **D = strategy - pi x benchmark.** Post-2010 mean t 0.46 to 1.41. COVID: 5.37% and 5.78% (t 2.35, 3.15). Holdout: -2.17% and -2.13% (t -2.28, -2.23), -1.17% and -1.11% (t -1.51, -1.44).
- **COVID position counts.** The corrected 3-month holds were in position for 13 and 15 of the 24 months, and the team Pure 6m position equals the benchmark's in 23 of 24.
- **Holdout attribution (Section 7).** Team Pure 6m: residual -2.19% (t -1.75), leakage -0.39%. Corrected Continuous pure: residual -0.51% (t -1.32), leakage +0.13%.
- **Bottom line "no significant post-2010 alpha under any model".** Over all 7 models, both baselines and all 6 strategies, the smallest p is 0.053 (corrected Pure 6m, FF5: 1.58%, t 1.95). The Section 5 range (-0.04% to 1.44%, t < 1.8) is for the three models it names, as labelled.
- **Exchange-1 team alphas.** With d10y+COM: -0.67% to -4.78% (discrete rules t -2.01 to -2.31). With BOND+COM: -0.68% to -4.81% (t -2.04 to -2.32).

### R2.5 Optional wording points (not required)

1. **Section 2, the strategies' "full" window.** "The first Pure positions are set in 1999-02" holds only for the corrected Pure 3m and 6m rules, which set the binding start. Team Pure rules first take a position in 1999-01, and Continuous pure in 1998-12 (team) and 1999-01 (corrected). More useful to a reader: the Original and Continuous raw rules hold positions from 1993-02 (team) or 1993-03 (corrected). The common 1999-03 window therefore leaves out 28 to 73 of their earliest in-position months. The window choice itself is correct, as `STRAT_START` says ("first month every timing strategy, in both baselines, can hold a position"). Suggested wording: "The strategies' full sample is the common window 1999-03 to 2026-07 (329 months), the first month every strategy in both baselines can hold a position. The raw-attention rules trade from 1993, so this window omits their earliest months."
2. **Section 5, "Factor adjustment raises GB's measured alpha above its raw mean".** This fails for CAPM over the full sample: the alpha is -0.59% against a raw mean of -0.50%. It holds for the six models that include value. Say "Models with value, profitability and investment raise...".
3. **Section 3, "the bootstrap null 95th percentile is 71 to 241".** This is the fixed-design range. The wild bootstrap's null 95th percentile runs from 72 to 403. Either label the range as fixed-design or quote both.

### R2.6 Round-2 status

- Round-1 required fixes: 6 of 6 resolved. Fix 5's qualification is accepted.
- Headline numbers recomputed; none changed:
  - (i) GB BOND loading: 0.132 (t 2.60, Holm 0.019) over the full sample, 0.088 (t 0.60) post-2010.
  - (ii) Holdout alphas: every one is more negative with UMD and BOND added. The smallest Holm p is 0.155.
  - (iii) Timing term: -0.57% to -1.07% for the strategies, 4 of 6 significant after Holm.
- New required fixes: none. `all_confirmed = true`.
