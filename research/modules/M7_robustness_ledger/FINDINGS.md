# M7 robustness ledger: project-wide test census, multiple testing, search-adjusted tests, deflated appraisal ratio and a frozen 1931-1969 run

BOTTOM LINE. Correcting for multiple testing across the whole project leaves none of the modules' labelled primary alphas standing. In family P (73 module primary alpha tests, one-sided), the smallest Holm p is 1.00 and the smallest BH p is 0.72. The attention thesis stays "Do not implement": the 2022-2026 holdout rejects a worthwhile alpha for all six team rules.

The optimizer book is the one candidate with something new. Its pre-registered, hash-verified 1931-1969 run PASSES: FF3+UMD alpha 1.95% a year, t 2.45, one-sided p 0.0074, positive in both halves. It still fails the other three conditions for implementation:

- Romano-Wolf adjusted p is 0.017 over 1970-2026 but 0.199 over 2010-2026.
- Its deflated appraisal ratio is 0.559 over 1970-2026 and 0.362 over 2010-2026, against a bar of 0.95.
- Its holdout alpha is -0.34%.

Under the verdict map fixed in advance (spec check 10), the book moves to "paper-trade at pilot size" and the report verdict stays "Do not implement". The EPA 5v5 spread has no confirmatory test, so it is "Do not implement".

Spec: `exchange/03_robustness_design/adopted_checks.md` (checks 0 to 10). Code: `modules/M7_robustness_ledger/run.py`, one script, end to end, 40 to 47 seconds. It writes only `outputs/tables/M7_*`, `outputs/figures/M7_*` and `modules/M7_robustness_ledger/first_run_record.json`. No shared lib file and no module output was changed.

## 0. Pre-registration and process (spec check 7, step 0)

- **Hashes.** When run.py first started, before any pre-1970 strategy return existed, it wrote `outputs/tables/M7_preregistration_hash.csv` at 2026-09-26 15:49:39 UTC (08:49:39 PDT). run.py asserts that the frozen-return file did not exist at that moment.
  - adopted_checks.md: 15fdce70e29e57a0fdf922ca20a8a6db16d0b2a0407eb58a09d390888af8e70b
  - optimizer.py: adbc414568aec1363c026252c677af9b4bcb8e196aa6fb8066b98a85abfd306b
  - m5lib.py: 952961a93c717a667d7b404219f1b343f487c02ec66630be3584f9517e1c5e2f
- **Where the spec hash came from.** At the first run, adopted_checks.md was not yet on disk, because the orchestrator saves returned files after the workflow. run.py therefore read its content from the workflow journal (wf_c1f5d333-469) and hashed the bytes exactly as `lib/save_returned_files.py` writes them (UTF-8, final newline).
  - The file has since been saved. The rerun at 18:09:03 UTC hashed the file itself and got the pre-registered value, and so did every run after it (the latest at 18:29:19 UTC).
  - In `M7_preregistration_hash.csv`, `source_this_run` now reads `file exchange/03_robustness_design/adopted_checks.md`. The `source` column keeps the first write's journal origin.
  - run.py stops with "PRE-REGISTRATION VIOLATION" if any of the three hashes differs. Every run since the first has verified all three.
- **Development runs.** Before the frozen run I made two development runs with `M7_SKIP_FROZEN=1`. They exercised the check 7 statistics code (`frozen_stats`) on post-1970 formation months only (1969-12 to 2008-05, already-seen data). Between the hash and the frozen run I changed only these things:
  - NaN handling in Holm and BH;
  - a ledger note;
  - the shock loading per standard deviation;
  - figure layout;
  - the verdict text.

  `book_path` and `frozen_stats` are unchanged since run.py was first written.
- **Dry run.** Formation months 1969-12 to 1970-11 with M5's own factor frame reproduce M5's `X_unc` net returns for 1970-01 to 1970-12 with a maximum absolute difference of 9.2e-17 (bar 1e-8). The same call with the FF3 Mkt-RF and RF inputs differs by at most 2.3e-5 a month. That difference is reported only.
- **Frozen run.** It executed once, first at 15:53:41 UTC (08:53:41 PDT), and its results are recorded in `first_run_record.json`.
  - Every later execution recomputes the run and checks it against that record: the SHA-256 of the net returns rounded to 1e-12, t, and the verdict. All match (`reproduces_first_run` True in `M7_frozen_pre1970.csv`).
  - After the frozen run I changed only output code:
    - figure label placement;
    - the LaTeX width wrapper and verdict-table column widths;
    - 25 extra context rows in the ledger;
    - the G7 label rule;
    - after the first verification, 22 more ledger rows for numbers these findings quote (see "Response to verification", R10);
    - after the second verification, the `p1_m7` cell of the check 7 (i) row in `M7_all_tests.csv`, plus an assertion that family F's `p1_m7` values equal those in `M7_family_F.csv` (R11).

    None of these touches a check 7 computation.
- **Deviations from the spec's choices:** none. The coding conventions where the spec left freedom are listed in section 11.

## 1. Test census and family map (check 1)

**Inputs.** The eight module ledgers hold 23,923 rows. There are no exact duplicates across the nine standard columns. `M7_all_tests.csv` holds 24,404 rows: the 23,923 module rows plus M7's own 481. Each row carries these columns:

- the nine standard columns, `p_value_one_sided` and `alternative`;
- `ledger_file`, `module_id`, `type`, `family`, `r_subfamily` and `is_primary_label`;
- `p1_m7`, the one-sided p that M7 used for families P, R and F. For P, R and M8's row in F it is derived from the two-sided p and the sign of the statistic. For the check 7 (i) row it is the t(457) one-sided p (0.0074), copied from that row's `p_value_one_sided`.

**Labels by module** (`M7_census_label_by_module.csv`):

| Module | Exploratory | Robustness | Primary | Placebo | Reference | Total |
|---|---|---|---|---|---|---|
| M1 | 435 | 217 | 15 | 0 | 0 | 667 |
| M1b | 588 | 1,102 | 40 | 88 | 82 | 1,900 |
| M2 | 7,874 | 5,562 | 46 | 0 | 0 | 13,482 |
| M3 | 5,590 | 737 | 33 | 0 | 0 | 6,360 |
| M4 | 426 | 375 | 1 | 0 | 0 | 802 |
| M5 | 412 | 0 | 4 | 0 | 0 | 416 |
| M6 | 146 | 120 | 8 | 0 | 0 | 274 |
| M8 | 14 | 0 | 8 | 0 | 0 | 22 |
| Total | 15,485 | 8,113 | 155 | 88 | 82 | 23,923 |

**Families** (`M7_census_family_by_module.csv/.tex`). All counts match the spec exactly:

- F: 1 row.
- P: 81 rows (M1b 24, M2 42, M3 12, M4 1, M5 2).
- D: 73 rows (M1 15, M1b 16, M2 4, M3 21, M5 2, M6 8, M8 7).
- X: 170 rows.
- L: 4,850 rows.
- R: 9,337 rows, split into R-M2 (8,161) and R-other (1,176: M1b 736, M4 282, M3 156, M6 2).
- E: 9,411 rows.

**Nominal census** (`M7_census_nominal.csv`). 4,184 rows have two-sided p below 0.05, which matches the spec:

- alpha 1,624 (38.8%): 783 with a positive statistic, 841 with a negative one;
- loading 1,325 (31.7%);
- mean 561;
- other 536;
- beta-timing 138.

Loadings are 32% of the nominal hits.

## 2. Family P, family F and the not-adopted all-primaries family (check 2)

**Family P.** Collapsing exact duplicates removes 8 of the 81 rows: 6 in M2 and 2 in M3, the Original and Pure holdout variants that coincide once the CPI gap is corrected. That leaves m = 73.

- The best one-sided p is 0.0299: M2, u5 Pure 6m, post-2010, t 1.89. It would stay significant at 5% only if the effective number of tests were below 1.69 (Sidak).
- Smallest Holm-adjusted p: 1.00. Smallest BH p: 0.718. Smallest BY p: 1.00.
- No survivors under any method. This matches the spec's expected values and confirms the verdict.
- Table: `M7_family_P.csv`.

**Family F** (Holm, one-sided; `M7_family_F.csv`):

| Test | t | One-sided p | Holm-adjusted p | Survives at 5% |
|---|---|---|---|---|
| M8_share_i_alpha_nw6 | -0.27 | 0.605 | 0.605 | no |
| M7 check 7 (i) | 2.45 | 0.0074 | 0.0147 | yes |

Among the confirmatory families P and F, the check 7 test is the only survivor. The search families answer a different question: 15 S-full members, the book among them, survive Romano-Wolf over 1970-2026, and none survives over 2010-2026 (section 4).

**All 155 labelled primaries as one family** (not adopted; for reference only, two-sided). 154 of them have a p-value; M8_share_iii_episodes has none. This family has 4 Holm survivors, 6 BH survivors and 4 BY survivors, and none of them is an alpha test:

- M1's Fisher test on zero months (p 1.3e-32);
- M1's joint Wald test (8.8e-12);
- two M2 FF3 HML loadings of the spread;
- BH also passes an M3 beta-timing term and an M2 FF5U HML loading.

This is the spec's reason for splitting the primaries into P and D (`M7_all_primaries_not_adopted_survivors.csv`).

**Uncorrected families**, reported as nominal counts only:

- D: 15 of 73 rows have p below 0.05.
- X: 33 of 170.
- L: 1,452 of 4,850.
- E: 1,636 of 9,411.

## 3. Family R: the robustness grids as distributions (check 3)

One-sided BH and BY at 5%, positive side only (`M7_family_R_summary.csv`):

| Family | m | Share with t > 0 | Smallest one-sided p | Smallest BH p | Smallest BY p | BH / BY survivors |
|---|---|---|---|---|---|---|
| R-M2 | 8,161 | 54.0% | 0.00018 | 0.475 | 1.000 | 0 / 0 |
| R-other M1b | 736 | 40.8% | 0.000066 | 0.049 | 0.349 | 1 / 0 |
| R-other M3 | 156 | 25.0% | 0.0116 | 0.804 | 1.000 | 0 / 0 |
| R-other M4 | 282 | 59.2% | 0.00062 | 0.125 | 0.777 | 0 / 0 |
| R-other M6 | 2 | 0% | 0.641 | 0.929 | 1.000 | 0 / 0 |
| R-other pooled | 1,176 | 43.0% | 0.000066 | 0.078 | 0.594 | 0 / 0 |
| R pooled | 9,337 | 52.7% | 0.000066 | 0.466 | 1.000 | 0 / 0 |

BY divisors: 9.584 at m = 8,161 and 9.719 at m = 9,337.

The single survivor in the whole R family is a BH survivor within M1b's 736 rows: `CPU_realtime_none_O3_covid_alpha`.

- It is the level-transform robustness variant of the CPU Original 3m rule.
- Its FF3 alpha is 6.83% a year with t 4.72, over the 24 COVID months (2020-01 to 2021-12).
- It fails BY and disappears when R-other is pooled.
- It is the level-transform twin of the CPU Original 3m COVID result that M1b already analyses (the log1p version earns 6.44%, t 4.46, over the same 24 months). M1b finds that CPU Original 3m's paired edge over the signal-free always-short position is +1.90% (t 1.02), so this window does not separate a climate trigger from being short the Brown residual in 2020-21.

**R-M2 by window** (`M7_grid_windows.csv/.tex`, figure `M7_grid_windows`). The window is the third-from-last field of the test id.

| Window | All 8,161 rows: n | Positive | Median t | Strategy rows only (8,008): positive | Median t |
|---|---|---|---|---|---|
| all | 8,161 | 54.0% | 0.13 | 53.8% | 0.12 |
| validation | 1,099 | 88.9% | 1.14 | 88.9% | 1.15 |
| post2010 | 1,078 | 76.4% | 0.60 | 76.6% | 0.61 |
| full_live | 1,078 | 75.0% | 0.52 | 75.0% | 0.52 |
| pre_covid | 1,071 | 73.2% | 0.50 | 72.9% | 0.49 |
| covid | 1,071 | 70.7% | 0.44 | 70.5% | 0.44 |
| holdout | 1,078 | 2.7% | -1.32 | 2.3% | -1.34 |
| inflation_rates | 1,071 | 13.9% | -0.73 | 13.3% | -0.74 |
| last18 | 297 | 0.0% | -2.35 | 0.0% | -2.35 |
| last12 | 297 | 20.2% | -1.11 | 20.4% | -1.11 |

The 21 full_1970 rows are spread rows only: 100% positive, median t 1.45.

The pattern the spec asked for is clear. Gains appear in validation and its sub-windows. Losses appear in every window that starts in 2022 or later: the rates window (2022-01 to 2024-12, which overlaps the last seven validation months), the holdout (2022-08 to 2026-07), the last 18 months and the last 12 months.

The spec's expected window figures (validation median 1.15, holdout 2.3% and -1.34) are reproduced exactly on the 8,008 strategy rows. On all 8,161 rows, which include the 153 green-minus-brown spread rows, the holdout reads 2.7% and -1.32. The two differ only in whether the spread rows are counted, and neither changes the reading.

## 4. Search families: Romano-Wolf max-t and Hansen's SPA (check 4)

**Members** (`M7_search_members.csv`).

S-full covers 1970-01 to 2026-07 (679 months) with M = 58 series:

- 24 optimizer paths;
- the EW primary book;
- 8 EW robustness variants;
- 10 carbon screens;
- 15 M4 green-minus-brown variants.

S-post covers 2010-01 to 2026-07 (199 months) with M = 89 series: S-full plus 6 team rules (`run_pipeline(bootstrap_reps=0)`), 12 M1b real-time MCCC and CPU rules, and 13 M6 series.

**Reproduction checks** (`M7_search_reproduction.csv`). Every regenerated member reproduces its saved number.

- The 8 EW variants and 10 screens match M5's full-sample Sharpe and FF5+UMD alpha to at most 9.7e-17.
- The 12 M1b rules match M1b's validation alpha t to at most 8.3e-17.
- M1b rules are flat after M1b's own eval_end (MCCC 2025-07, CPU 2025-10). This zeroed a few trailing nonzero months of stale holds and closing costs: 2 months each for MCCC O6, P6, CR and CP and for CPU P3, CR and CP, and 5 months for CPU P6.

**Method.** FF5+UMD alpha, NW(6) standard errors and t-statistics as in G2. The null bootstrap is stationary with mean block 12, B = 5,000 and seed 20260926. Returns are demeaned by each series' alpha, and months are resampled jointly with the factors. OLS is refitted in each draw, with tau* = alpha* / s_i. The spec's Romano-Wolf stepdown and consistent SPA follow.

**Results** (`M7_search_summary.csv/.tex`, `M7_search_top.tex`, figure `M7_search_family_t`):

| | S-full (1970-2026) | S-post (2010-2026) |
|---|---|---|
| Best member | optimizer X_b-1.00, alpha 2.52%, t 3.34 | optimizer X_b-0.25, t 2.32 |
| RW adjusted p of best | 0.0088 | 0.150 |
| SPA p | 0.0086 | 0.150 |
| 95th percentile of bootstrap max-t | 2.68 | 2.78 |
| RW survivors at 5% | 15 | 0 |
| Book (X_unc): alpha, t, RW p | 2.17%, 3.07, 0.017 (pass) | 3.12%, 2.18, 0.199 (fail) |
| EPA 5v5 (epa5): alpha, t, RW p | 4.54%, 2.58, 0.058 (fail) | 4.72%, 1.52, 0.558 (fail) |
| Nyholt / Li-Ji M_eff (residuals) | 42.4 / 14 | 74.8 / 27 |
| Sidak count at which the best t stops being significant | 116 | 4.8 |

The 15 S-full survivors are:

- 11 convention-X optimizer paths, from X_unc through X_b-1.50 (X_b-2.00 and all 12 convention-M paths fail);
- four EPA variants: epa_nomargin5 (t 3.23), epa8 (3.13), epa_median8 (2.76) and epa_anylink5 (2.66).

**Reading.** Over 1970-2026 the book survives the search as nonzero. Over 2010-2026 it does not survive the search, and nothing does.

The EPA 5v5 spread fails in both windows, although several sister variants with different intensity inputs clear the full-sample bar. That spread of results across sister variants is itself a warning about specification choice.

M2's grid is not in either family because its series are not saved. This makes both tests slightly lenient.

**Every test that survives a correction, by family.** The list below gathers sections 2 to 4 in one place. Each adjusted p is in the M7 ledger: the `M7_C2_*` rows for F and P, `M7_C3_*` for R, and `M7_C4_<family>_<member>` for the search families.

| Family | Correction | Survivors at 5% |
|---|---|---|
| F (frozen, hash-verified; m = 2) | Holm, one-sided | M7 check 7 (i), the frozen 1931-1969 book (Holm p 0.0147). M8's frozen test does not survive (0.605). |
| P (73 module primary alphas) | Holm and BH (BY reported), one-sided | none |
| D, X, L, E | none, by design | not applicable; nominal counts in section 2 |
| R-M2, R-other by module, R-other pooled, R pooled | BH and BY, one-sided | one BH survivor in R-other M1b, `CPU_realtime_none_O3_covid_alpha` (smallest BH p 0.049); none under BY and none in any pooled family |
| S-full (58 series, 1970-2026) | Romano-Wolf stepdown | 15. Adjusted p: X_b-1.00 and X_b-0.75 0.0088; X_b-0.50 0.0090; X_b-0.25 0.0092; X_b-1.25 and epa_nomargin5 0.0106; X_b+0.00 0.0120; X_b+0.25 and epa8 0.0142; X_b+0.50 0.0150; X_unc 0.0166; X_b+1.00 0.0168; X_b-1.50 0.0202; epa_median8 0.0350; epa_anylink5 0.0478 |
| S-post (89 series, 2010-2026) | Romano-Wolf stepdown | none (best adjusted p 0.150) |
| All 155 labelled primaries (not adopted; two-sided) | Holm, BH, BY | Holm and BY, 4: M1 `Q3_fisher_zero_pre_post`, M1 `Q2_joint_team_signal_z_full`, M2 `spread\|L5\|post2010\|E:FF3\|b_HML`, M2 `spread\|L5\|full_1970\|E:FF3\|b_HML`. BH adds 2: M3 `Q3b.ln_timing.Pure 3m\|corrected\|36m-backward\|post2010` and M2 `spread\|L5\|post2010\|E:FF5U\|b_HML`. None is an alpha test. |

## 5. Deflated appraisal ratio and PSR (check 5)

**Inputs.** For each candidate and window, the appraisal ratio comes from its FF5+UMD regression (G5): monthly alpha over residual standard deviation with ddof = 7, plus the residual skew and raw kurtosis. N_eff is Nyholt's, from the family's FF5+UMD residual correlations. The cross-trial variance V comes from K = round(N_eff) average-linkage clusters: V_cl is the variance of the clusters' monthly ARs, and V = max(1/(T-1), V_cl). Cluster membership is in `M7_dsr_clusters_s_full.csv` and `_s_post.csv`.

| Family | N Nyholt | N Li-Ji | K | V_cl | Floor 1/(T-1) | V used | E_N | SR0 (annualized) |
|---|---|---|---|---|---|---|---|---|
| S-full | 42.4 | 14 | 42 | 0.00246 | 0.00147 | 0.00246 | 2.21 | 0.38 |
| S-post | 74.8 | 27 | 75 | 0.00583 | 0.00505 | 0.00583 | 2.43 | 0.64 |

**Results** (`M7_dsr.csv/.tex`, `M7_dsr_sensitivity.csv`). The governing DSR is the smaller of the iid DSR and the DSR with z scaled by t_NW / t_OLS.

| Candidate, window | AR (annual) | t NW / t OLS | DSR iid | DSR NW | Governing DSR | N = Li-Ji | N = raw M | V = 1/(T-1) | Li-Ji and V floor | PSR(0) | Largest passing N |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Book, 1970-2026 | 0.400 | 3.07 / 2.85 | 0.559 | 0.563 | **0.559** | 0.776 | 0.497 | 0.786 | 0.897 | 0.999 | 3 |
| EPA 5v5, 1970-2026 | 0.376 | 2.58 / 2.68 | 0.488 | 0.488 | **0.488** | 0.709 | 0.427 | 0.720 | 0.849 | 0.996 | 2 |
| Book, 2010-2026 | 0.557 | 2.18 / 2.15 | 0.363 | 0.362 | **0.362** | 0.533 | 0.336 | 0.433 | 0.593 | 0.989 | 2 |
| EPA 5v5, 2010-2026 | 0.410 | 1.52 / 1.58 | 0.171 | 0.182 | **0.171** | 0.302 | 0.155 | 0.222 | 0.357 | 0.945 | 0 |

Pass bar: governing DSR of at least 0.95 in both windows. **Both candidates fail** in both windows, and under every sensitivity. The most lenient case, the book over 1970-2026 with N = Li-Ji and V at its floor, gives 0.897.

The EPA spread's post-2010 PSR(0) is 0.945, so it fails even as a single trial. The book passes at the step-3 V only for N of 3 or fewer over 1970-2026, and 2 or fewer over 2010-2026.

**Context** (raw returns, not a pass test):

| Series | Raw annual Sharpe | Lo-adjusted Sharpe | Raw-Sharpe DSR |
|---|---|---|---|
| Book, 1970-2026 | 0.555 | 0.553 | 0.859 |
| Book, 2010-2026 | 0.696 | 0.632 | 0.505 |
| EPA 5v5, 1970-2026 | 0.199 | 0.181 | 0.062 |
| EPA 5v5, 2010-2026 | 0.520 | 0.418 | 0.238 |

**Rule between checks 4 and 5.** For the book over 1970-2026, a max-t pass with a DSR fail reads "survives the search as nonzero, not bankable after selection". Over 2010-2026 it fails both. Only the DSR can move a verdict, and it moves nothing.

Nyholt's N_eff here (42 and 75) is far above the fact-check's 6.4 to 8.1, which covered the 24 optimizer paths alone. These families mix three or more near-duplicate blocks (optimizer paths, EW variants and screens, GB variants), and Nyholt's variance-of-eigenvalues formula counts block structure generously. The spec makes Nyholt govern, and the Li-Ji rows show the verdict does not depend on that choice.

## 6. Holdout reading in appraisal-ratio units (check 6)

FF5+UMD on the 48 holdout months (2022-08 to 2026-07; k = 7, 41 degrees of freedom, t critical 1.683). The margin delta is 0.25 times the annualized residual volatility. Source: `M7_holdout_reading.csv/.tex`.

| Series | Alpha | 90% interval | Delta | MDE80 | Reading |
|---|---|---|---|---|---|
| Optimizer book | -0.34% | -4.16% to +3.48% | 1.35% | 5.75% | inconclusive |
| EW momentum book | -4.48% | -13.51% to +4.54% | 2.35% | 13.58% | inconclusive |
| EPA 5v5 spread | +3.90% | -5.49% to +13.29% | 3.18% | 14.14% | inconclusive |
| Team Original 3m | -4.41% | -8.00% to -0.81% | 0.86% | 5.41% | rejects a worthwhile alpha |
| Team Pure 3m | -2.09% | -3.84% to -0.35% | 0.62% | 2.63% | rejects |
| Team Original 6m | -3.18% | -5.85% to -0.51% | 1.10% | 4.01% | rejects |
| Team Pure 6m | -3.38% | -6.19% to -0.58% | 1.07% | 4.22% | rejects |
| Team Continuous raw | -0.92% | -1.69% to -0.14% | 0.28% | 1.16% | rejects |
| Team Continuous pure | -0.65% | -1.17% to -0.13% | 0.27% | 0.78% | rejects |
| Reference: Always-short Brown | -2.37% | -5.44% to +0.70% | 1.29% | 4.62% | rejects |

**FF3 sensitivity for the team rules** (FF3 from `load_kf_ff3`, per G3). All six still read "rejects". Original 6m's FF3 interval just crosses zero (upper bound +0.03%) but stays below its delta of 1.12%. The FF3 alphas agree with the fact-check's team-file FF3 figures to within 0.01 percentage points: Original 3m is -4.03% here and -4.03% there.

**Reading.**

- For the attention thesis, the holdout is evidence against a worthwhile alpha, not merely a lack of evidence: all six rules reject, including both continuous rules.
- The book is inconclusive. Its interval is -4.2% to +3.5% against a margin of 1.35%, and 48 months cannot tell 0% from 3%.

## 7. Frozen 1931-1969 run of the optimizer book (check 7, pre-registered)

**Specification.** The book is the unconstrained Grinold-Kahn book called exactly as M5 calls it:

- `optimizer.precompute` and then `run_path` with b = 1e3 and kappa = cost = 10 bp;
- the 41 covered industries (convention X);
- the signal `m5lib.mom_signal(R, 11, 1)`;
- Mkt-RF and RF from `load_kf_ff3()`.

Formation months run from 1931-06 to 1969-11, so return months run from 1931-07 to 1969-12 (462 months). Between 34 and 39 industries are eligible each month. There are 0 solver fallbacks and 0 inaccurate months, and the ex-ante tracking volatility is 5.00% in every month. Pre-1963 UMD comes from the raw Ken French file, which equals `load_ff5_mom` UMD exactly from 1963-07.

**Results** (`M7_frozen_pre1970.csv/.tex`, returns in `M7_frozen_pre1970_returns_monthly.csv`, holdings in `M7_frozen_pre1970_holdings.csv`, figure `M7_frozen_pre1970`):

| Statistic | Value |
|---|---|
| (i) FF3+UMD alpha, net of 10 bp | **1.95% a year, SE 0.80%, t 2.45, one-sided p 0.0074 (t(457))** |
| (ii) first half, 1931-07 to 1950-09 (231 months) | 1.71%, t 1.44 |
| (ii) second half, 1950-10 to 1969-12 (231 months) | 0.90%, t 0.83 |
| 90% interval | 0.64% to 3.27% |
| Delta (0.25 x residual volatility of 5.14%) | 1.28% |
| Loadings | UMD beta 0.23 (t 12.1); market beta 0.03; R2 0.42 |
| Appraisal ratio | 0.38 |
| Net return, volatility, turnover | 3.42% a year; 6.69% a year; 2.68 times a year |
| **Verdict** | **PASS**: alpha > 0 with t >= 2.00, and both halves' alphas > 0 |

The pre-registered reading of a PASS: the book's edge over UMD existed in 38.5 unseen years. The book moves to "paper-trade at pilot size". The report verdict stays "Do not implement" because the 2022-2026 holdout alpha is -0.34%.

Family F's Holm correction (section 2) keeps the test significant, with an adjusted p of 0.0147. By the spec's operating characteristics, a PASS happens with probability 0.02 under a true zero alpha. It happens with probability 0.62 under a true 2% alpha at post-1970 residual volatility.

**Secondary rows** (reported, never part of the verdict):

- **S1.** FF5+UMD alpha on 1963-07 to 1969-12 (78 months): 3.26%, SE 1.85%, t 1.76. It is uninformative by design.
- **S2.** The b = -1 book minus the unconstrained book has a net IR difference of -0.006, with a 95% paired circular block bootstrap interval of -0.194 to +0.228 (p 0.957).
  - The lower bound is below -0.10, so "no carbon cost" is not stated.
  - The FF3+UMD alpha difference is -0.04%, with an interval of -1.38% to +1.36%.
  - Before 1970, the b = -1 constraint binds in 77.9% of months and is infeasible in 38 months. Those months fall back to the minimum-carbon book; M5's post-1970 X_b-1.00 path had 0 such months.
  - The ranking is the undated team file applied to 1930s industries, so this row tests a portfolio restriction, not a climate claim.
- **S3.** Crash profile:
  - worst month 1932-07 at -11.2%;
  - worst three months, ending 1932-09, at -21.6%;
  - maximum drawdown of compounded net wealth -30.2% (trough 1939-09).
- **S4.** At 25 bp realized costs, the FF3+UMD alpha is 1.55% (t 1.94).
- **S5.** The realized rank IC of the 11-1 signal averages 0.080 over 462 months. Its NW(6) t is 6.78 against zero and 2.57 against the assumed 0.05.

**Caveats on the PASS.**

1. The window is unseen for this book, not for the field. UMD from 1927 is public, and industry trend rules have been studied over about a century (Zarattini and Antonacci 2024).
2. The pre-1970 benchmark lacks RMW and CMA, which do not exist before 1963-07. For comparison, the post-1970 FF3+UMD alpha with the same factor files as the frozen test (load_kf_ff3 plus UMD) is 2.02% (t 2.86); the fact-check's 2.01% (t 2.84) used the Mkt-RF, SMB and HML columns of the FF5 file.
3. The second-half alpha is about half the first-half alpha (0.90% against 1.71%), although the difference is far from significant (t about 0.5, treating the halves as independent). After 1970 the alpha did not decay after 2010 (FF5+UMD alpha 1.99%, t 2.31, over 1970-2009; 3.12%, t 2.18, over 2010-2026); it disappeared in the 2022-2026 holdout (-0.34%).
4. A pre-1970 pass answers "was the edge there before 1970", not "is it there now".

## 8. Cost stress on the book (check 8)

net_c = gross - c x turnover, with holdings fixed at the 10 bp solution. Source: `M7_cost_stress.csv/.tex`.

| Cost | Full 1970-2026 | Post-2010 | Holdout |
|---|---|---|---|
| 0 bp | 2.47% (t 3.50) | 3.42% (t 2.40) | -0.04% (t -0.02) |
| 10 bp | 2.17% (t 3.07) | 3.12% (t 2.18) | -0.34% (t -0.15) |
| 25 bp | 1.73% (t 2.43) | 2.68% (t 1.86) | -0.79% (t -0.35) |
| 50 bp | 1.00% (t 1.39) | 1.95% (t 1.33) | -1.54% (t -0.67) |

The break-even cost c* = alpha(gross) / alpha(turnover) is 84 bp over the full sample and 117 bp after 2010. The holdout gross alpha is negative, so no break-even exists there. Turnover is 2.92 times a year over the full sample.

Pass bar: full-sample alpha above zero at 25 bp. **PASS** (1.73%, t 2.43). The alpha does not exist only at stylized costs.

## 9. Descriptive and exploratory rows (check 9)

**Crash profile of the book after 1970:**

- worst month 2009-04 at -12.8%;
- March to May 2009 at -17.5%, which is also the worst three-month window;
- maximum drawdown -24.1%, with its trough in 2010-01.

No drawdown budget is set.

**EPA 5v5 with climate-concern shock controls** (exploratory; `M7_epa_shock_controls.csv`). All regressions are post-2010 and FF5+UMD unless stated.

| Specification | Months | Alpha | t | Shock loading per s.d. a month |
|---|---|---|---|---|
| Base, same sample | 186 | 4.87% | 1.52 | |
| + same-month MCCC shock | 186 | 6.66% | 2.13 | -0.52% (t -2.21) |
| + lagged shock only | 187 | 3.39% | 1.06 | |
| + shock and lag | 186 | 6.02% | 1.95 | |
| + MCCC transition shock | 186 | 6.38% | 1.95 | |
| + CPU shock | 189 | 6.48% | 1.97 | |
| FF3 + MCCC shock | 186 | 5.95% | 1.76 | |

These reproduce the fact-check. The spread lost when concern rose, which is the opposite of the Pastor, Stambaugh and Taylor channel. This is not a pass test.

**Data provenance** (`M7_data_provenance.csv`):

- The 2024-06-15 ALFRED vintage of EMVENRGYENVREG equals the current file in all 473 months.
- The 2022-09-15 vintage (452 months compared) differs in 2022-08 (0.56327 against 0.54389). It also differs trivially in 2022-07 (0.63738 against 0.63729), which the spec's "only in 2022-08" omitted.
- The 2025-12-20 CPIAUCSL vintage lacks 2025-10, as does the current file, so the CPI gap was real-time.
- The team emissions file has 41 rows and two columns (`ff`, `emissions_intensity`), with no source, units, scope or date.

## 10. Verdict map (check 10, fixed in advance)

Source: `M7_verdict_map.csv`, `M7_verdict_table.csv/.tex`.

| Candidate | (a) Confirmatory test | (b) RW adj. p <= 0.05 in both families | (c) DSR >= 0.95 in both windows | (d) Positive holdout alpha, not "rejects" | Verdict |
|---|---|---|---|---|---|
| Optimizer book (X_unc) | yes: check 7 PASS, Holm-adjusted 0.015 in F | no: 0.017 / 0.199 | no: 0.559 / 0.362 | no: -0.34%, inconclusive | **Paper-trade at pilot size; report verdict stays "Do not implement"** |
| EPA 5v5 spread | no: none exists | no: 0.058 / 0.558 | no: 0.488 / 0.171 | yes: +3.90%, inconclusive | **Do not implement** |
| Attention thesis (Short-Brown rules) | M8 FAIL | family P smallest Holm p 1.00 (BH 0.72) | not a candidate | holdout rejects a worthwhile alpha for 6 of 6 rules | **Do not implement** |

No candidate can reach "implement" within this project, as the spec anticipated. The frozen run decided only between retiring the book and paper-trading it. It passed, so the book is paper-traded, not retired. That is the only verdict M7 moves.

## 11. Conventions where the spec left freedom, and other notes

1. **Stationary bootstrap.** Each search family uses a fresh `default_rng(20260926)`. The draws are a B x T block of uniform start indices, then a B x T block of restart uniforms. The spec fixes the seed, B and the law, but not the order of draws.
2. **M1b flat convention.** M1b rules are set to zero after M1b's eval_end, the last return month that M1b treats as driven by the measure (see section 4).
3. **DSR sensitivities.** When N changes (Li-Ji, raw M), V stays at its step-3 value. Rows combining the V floor with each N are added.
4. **Critical values.** t critical values come from scipy (1.6829 at 41 degrees of freedom, 1.6482 at 457). They round to the spec's 1.683 and 1.648.
5. **FF3 source for check 6.** The FF3 sensitivity uses `load_kf_ff3` (G3); the fact-check used the team FF3 file (see section 6).
6. **R-M2 window statistics.** See section 3: the spec's expected values correspond to the 8,008 strategy rows.
7. **Ledger** (G7). `M7_robustness_tests_ledger.csv` has 481 rows: 1 primary (check 7 (i), family F), 387 robustness, 86 descriptive and 7 exploratory. It has the nine standard columns plus `p_value_one_sided`, `alternative` and `family`.
   - Rows of checks 2 to 8 are all labelled `robustness`. Context-only rows among them carry "[context: descriptive]" (33 rows) or "[context: exploratory]" (1 row, the not-adopted all-primaries family) in the note.
   - Checks 1 and 9 are descriptive or exploratory.
   - The M7 ledger is excluded from the census glob, so the census always reads the eight module ledgers.
8. **LaTeX tables.** All tables compile with tectonic. The DSR, holdout and search-summary tables use `\resizebox{\textwidth}{!}` (graphicx, already in the report preamble).

## 12. Output files

- **Code:** /home/hashim/projects/GA/project/research/modules/M7_robustness_ledger/run.py
- **First-run record:** /home/hashim/projects/GA/project/research/modules/M7_robustness_ledger/first_run_record.json
- **Tables** (/home/hashim/projects/GA/project/research/outputs/tables/):
  - Pre-registration and ledgers: M7_preregistration_hash.csv, M7_robustness_tests_ledger.csv, M7_all_tests.csv.
  - Census: M7_census_family_by_module.csv/.tex, M7_census_label_by_module.csv, M7_census_nominal.csv.
  - Families P, F and D: M7_family_P.csv, M7_family_F.csv, M7_family_D.csv, M7_all_primaries_not_adopted_survivors.csv.
  - Family R: M7_family_R_summary.csv, M7_grid_windows.csv/.tex.
  - Summary: M7_multiple_testing_summary.csv/.tex.
  - Search families: M7_search_members.csv, M7_search_summary.csv/.tex, M7_search_top.tex, M7_search_reproduction.csv.
  - Deflated appraisal ratio: M7_dsr.csv/.tex, M7_dsr_sensitivity.csv, M7_dsr_clusters_s_full.csv, M7_dsr_clusters_s_post.csv.
  - Holdout: M7_holdout_reading.csv/.tex.
  - Frozen run: M7_frozen_pre1970.csv/.tex, M7_frozen_pre1970_returns_monthly.csv, M7_frozen_pre1970_holdings.csv.
  - Cost stress: M7_cost_stress.csv/.tex.
  - Check 9: M7_epa_shock_controls.csv, M7_data_provenance.csv.
  - Verdicts: M7_verdict_map.csv, M7_verdict_table.csv/.tex.
- **Figures** (/home/hashim/projects/GA/project/research/outputs/figures/), each as PDF and PNG:
  - M7_search_family_t: member t-statistics by source, with the max-t critical value;
  - M7_grid_windows: R-M2 alpha t by window;
  - M7_frozen_pre1970: cumulative book return and the book less its FF3+UMD exposures, 1931 to 1969.

## Response to verification

There have been two verification rounds. Round 1 raised R1 to R10; round 2 raised R11 and R12. All twelve are accepted. Between the rounds, a rerun checked the pre-registered spec hash against the saved file. No verdict, pass bar or check 7 number has changed at any point.

### Round 1: R1 to R10

I re-derived all ten required fixes, and all ten are accepted. Nine are wording or rounding corrections to this document. R10 is a code change that only adds output. No verdict, pass bar or check 7 number changes.

**R1 (section 2, "only test that survives").** Accepted.

- `M7_search_members.csv` has 15 S-full members with RW adjusted p of 0.05 or less, including opt:X_unc (0.0166). S-post has none.
- The old sentence was true only for the confirmatory families. It now says so and points to section 4.

**R2 (section 3, the COVID R survivor).** Accepted, with both new numbers checked against the M1b ledger.

- `CPU_realtime_log1p_O3_covid_alpha`: alpha_ann 0.06438, t 4.463, n 24.
- `COVIDB_realtime_CPU_O3_minus_always_short_covid`: diff alpha_ann 0.01898, t 1.017.
- M1b's FINDINGS (section 6) uses the same numbers and the same conclusion. The old wording ("covered by M1b's placebo work") pointed at the wrong M1b result: the VIX and EMV-overall placebos do not reproduce the CPU O3 gain. What M1b does show is that CPU O3 does not beat a permanent short of the Brown residual.

**R3 (section 3, windows "after 2022-07").** Accepted. `lib/common.py` defines the windows as follows:

- inflation_rates: 2022-01-31 to 2024-12-31;
- last18: 2025-02 to 2026-07;
- last12: 2025-08 to 2026-07.

So the rates window starts in 2022-01 and shares 2022-01 to 2022-07 (seven months) with validation. The old phrase "after 2022-07" was wrong for that window.

**R4 (section 7, caveat 3, "decay after 2010 has an earlier echo").** Accepted. The old sentence implied a post-2010 decay that the data do not show.

- The halves-difference t is (1.710 - 0.903) / sqrt(1.190^2 + 1.087^2) = 0.50. Each SE is alpha / t from the two half regressions.
- The book's FF5+UMD alpha is 1.99% (t 2.31) over 1970-01 to 2009-12 (480 months) and 3.12% (t 2.18) over 2010-2026.

**R5 (section 6, Team Original 6m upper bound).** Accepted.

- ci90_hi in `M7_holdout_reading.csv` is -0.00514968, which rounds to -0.51%. The .tex already printed -0.51.
- The findings table had a hand-rounding error; it now reads -5.85% to -0.51%.

**R6 (section 7, caveat 2, comparison alpha).** Accepted, both numbers recomputed on opt X_unc, 1970-01 to 2026-07.

- With `load_kf_ff3` Mkt-RF, SMB and HML plus UMD, the same factor files as the frozen test: 2.02%, t 2.86.
- With Mkt-RF, SMB and HML from the FF5 file plus UMD: 2.01%, t 2.84, the fact-check's figure.
- The matched-files number is now quoted, and the fact-check's source is named.

**R7 (section 5, largest passing N).** Accepted. `max_N_pass` in `M7_dsr.csv` for the book is 3 over 1970-2026 and 2 over 2010-2026, and the sentence now gives both.

**R8 (section 11, item 7, context tags).** Accepted, with the count updated for R10.

- The verifier's counts (29 descriptive, 1 exploratory) were right for the 459-row ledger.
- R10 adds four check 7 context rows, which the G7 rule relabels robustness with a "[context: descriptive]" tag. The rerun ledger therefore has 33 descriptive tags and 1 exploratory tag.
- The item now reports 33 and the new totals: 481 rows, of which 387 robustness.

**R9 (bottom line, "no labelled primary alpha standing").** Accepted. M7's own primary, check 7 (i), survives Holm in family F at 0.0147, so the sentence now covers only the modules' labelled primaries.

**R10 (code, G7: every quoted number has a ledger row).** Accepted and fixed in run.py. The change only adds output: `led()` calls placed after the computations they report. It adds 22 rows:

1. `C3_<family>_share_pos` for R-other M1b, M3, M4, M6, R-other pooled and R pooled: 0.408, 0.250, 0.592, 0.000, 0.430, 0.527. R-M2's 54.0% was already in `C3_RM2_all_all_share_pos`.
2. The governing DSR at "N = Li-Ji, V = 1/(T-1)" and "N = raw M, V = 1/(T-1)" for both candidates and windows.
   - Li-Ji with the V floor: book 0.897 / 0.593, EPA 0.849 / 0.357.
   - Raw M with the V floor: book 0.749 / 0.408, EPA 0.680 / 0.203.
   - The loop that already wrote the other three sensitivities now also writes these two.
3. `C5_<family>_<member>_max_N_pass` for both candidates and windows: 3, 2, 2, 0.
4. `C7_context_post1970_kf3umd` (2.02%, t 2.86) and `C7_context_post1970_ff5file_ff3umd` (2.01%, t 2.84).
5. Two rows for the new numbers R4 brings into section 7: `C7_context_halves_diff_t` (t 0.50) and `C7_context_ff5umd_1970_2009` (1.99%, t 2.31). The 2010-2026 figure was already in `C4_S-post_opt:X_unc`.

The 1970-2026 rows use the saved X_unc returns. The halves row uses only fields of the frozen-run result. No check 7 input or computation changed.

**Rerun** (`uv run python modules/M7_robustness_ledger/run.py`, 41 seconds, 2026-09-26 16:15 UTC):

- All three pre-registration hashes verified; only `this_run_utc` changed in `M7_preregistration_hash.csv`.
- The dry-run difference is 9.22e-17.
- The frozen run gives alpha 0.0195, t 2.448, PASS.
- `reproduces_first_run` is True in `M7_frozen_pre1970.csv`, and `first_run_record.json` is byte-identical to the record written at 15:53:41 UTC.
- Of the 39 M7 tables, 36 are byte-identical to a snapshot taken before the rerun. The other three are the pre-registration file (timestamp only), the M7 ledger and `M7_all_tests.csv`.
- In the M7 ledger, the 459 earlier rows are identical and 22 rows are new.
- In `M7_all_tests.csv`, the 23,923 module rows are identical, for 24,404 rows in total.
- Verdicts are unchanged: book "Paper-trade (report verdict stays Do not implement)", EPA 5v5 "Do not implement".

### Rerun after the spec was saved (2026-09-26 18:09 UTC)

The verification left one item open: checking the pre-registered spec hash against the saved `adopted_checks.md` rather than against the journal copy. The orchestrator saved the file at 17:43 UTC (10:43 PDT), so I reran the delivered script once, unchanged.

- **Inputs unchanged.** No module ledger, saved return series or lib file is newer than M7's previous outputs (16:15 to 16:16 UTC). The only newer files under `modules/` are Markdown text the orchestrator saved at 17:43 UTC: the FINDINGS.md of M1, M1b, M2, M5 and M8, and M7's own FINDINGS.md and VERIFY.md. `optimizer.py` and `m5lib.py` were last modified at 09:55 and 10:31 UTC, before the pre-registration.
- **Run.** `uv run python modules/M7_robustness_ledger/run.py`, 41.8 seconds wall time, exit 0.
- **Hashes.** All three verified. adopted_checks.md was hashed from the file itself (`source_this_run` = `file exchange/03_robustness_design/adopted_checks.md`) and equals the pre-registered 15fdce70e29e57a0fdf922ca20a8a6db16d0b2a0407eb58a09d390888af8e70b. An independent `sha256sum` of the three files gives the same values.
- **Check 7.** The dry-run difference is 9.22e-17 with M5's inputs and 2.31e-5 with the FF3 inputs. The frozen run again gives alpha 0.0195, t 2.448, one-sided p 0.0074, halves 0.0171 and 0.0090, and PASS. `reproduces_first_run` is True, and `first_run_record.json` is byte-identical to the 15:53:41 UTC record.
- **Outputs.** 38 of the 39 M7 tables are byte-identical to a snapshot taken before the rerun. `M7_preregistration_hash.csv` differs only in `this_run_utc` and `source_this_run`. The three PNG figures are byte-identical, and the three PDF figures differ only in their embedded CreationDate. The ledger still has 481 rows, `M7_all_tests.csv` still has 24,404, and the verdicts are unchanged.
- **Code.** Not changed in this pass. Nothing the report reads has changed.

The pre-registration is now verified end to end against files on disk. The only new text in this pass is this subsection, the note in section 0 and the survivor list at the end of section 4. Every number in them was already in the M7 ledger or the tables above.

### Round 2: R11 and R12

I re-derived both fixes, and both are accepted. R11 is fixed in run.py (the verifier's alternative), so the section 1 description is now true as a statement about the file. R12 is a wording correction. No verdict, pass bar or check 7 number changes.

**R11 (section 1, `p1_m7` for family F).** Accepted and fixed in code.

- Re-derived from the file: before the fix, `M7_all_tests.csv` had `p1_m7` = 0.604759 for `M8_share_i_alpha_nw6` and an empty cell for `M7_C7_i_alpha_ff3umd`. That row's one-sided p (0.007374) was only in `p_value_one_sided`. The mask that fills `p1_m7` took families P and R plus M8's row by name, and missed the M7 row.
- Fix: run.py now copies that row's `p_value_one_sided` into `p1_m7`. It copies the exact value family F's Holm used (the t(457) p, `FROZEN["p1"]`) instead of deriving a new one. A new assertion checks that both F rows' `p1_m7` equal the `p1` column of `M7_family_F.csv` to 1e-15, so the column and the table cannot drift apart.
- Section 1 now says how the check 7 row's value is sourced, and section 0 lists this as an output-only change made after the frozen run.

**R12 ("Rerun after the spec was saved", bullet "Inputs unchanged").** Accepted with the verifier's wording.

- Re-derived: `find modules lib -newermt 2026-09-26T16:16:30Z` lists seven files at 17:43:33 UTC. They are the FINDINGS.md of M1, M1b, M2, M5 and M8, and M7's FINDINGS.md and VERIFY.md. Nothing under `lib/` is newer.
- The only later files under `modules/` are the round-2 verifier's scripts and logs in `modules/M7_robustness_ledger/verify/` (18:17 to 18:22 UTC). They were written after the 18:09 rerun.
- None of these files is a run.py input, so the conclusion stands.

**Rerun for R11** (`uv run python modules/M7_robustness_ledger/run.py`, started 2026-09-26 18:29:18 UTC, 43.0 seconds wall time, exit 0):

- **Inputs.** Since the previous execution (18:14:08 UTC), the workspace's only newer files are:
  - run.py itself;
  - the round-2 verifier's files under `modules/M7_robustness_ledger/verify/`;
  - red-team check scripts and output under `exchange/04_red_team/checks/`.

  run.py reads none of the last two. `sha256sum` of the three pre-registered files still gives the pre-registered values.
- **Hashes.** All three verified. adopted_checks.md was again hashed from the file itself.
- **Check 7.** The dry-run differences are 9.22e-17 (M5 inputs) and 2.31e-5 (FF3 inputs). The frozen run gives alpha 0.0195, t 2.448, one-sided p 0.0074, halves 0.0171 and 0.0090, and PASS. `reproduces_first_run` is True, and `first_run_record.json` is byte-identical to the 15:53:41 UTC record.
- **Outputs**, compared with a snapshot taken just before the rerun:
  - 37 of the 39 M7 tables are byte-identical, including the M7 ledger (481 rows), `M7_family_F.csv` and the verdict map.
  - `M7_all_tests.csv` differs in one cell only: `p1_m7` of `M7_C7_i_alpha_ff3umd`, which went from empty to 0.007374. The other 24,403 rows and the other 17 columns are identical.
  - `M7_preregistration_hash.csv` differs only in `this_run_utc`, which went from 18:14:08 to 18:29:19 UTC.
  - The 18:14:08 value came from an execution after my 18:09 rerun that I did not make. This rerun reproduces all of its tables byte for byte, apart from the R11 cell, so it does not matter which process ran it.
  - The three PNG figures are byte-identical. The three PDF figures differ only in their embedded CreationDate.
- **Verdicts.** Unchanged: book "Paper-trade (report verdict stays Do not implement)", EPA 5v5 "Do not implement".
