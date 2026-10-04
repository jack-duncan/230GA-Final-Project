FAIL. The frozen EMV-share rule fails the pre-registered 1993-2009 test. It meets only one of the four pass-bar components (episodes), and its timing alpha is -0.18% a year (t = -0.27). "Do not implement" stands. An independent verifier rebuilt the whole test from the raw files and matched all 128 published numbers. The corrections made after verification (last section) change no number, no pass-bar component and no verdict.

# M8 frozen 1993-2009 test

PROCESS: PREREGISTRATION.md carries the stamp 2026-09-26 03:29:54 PDT, taken with `date` in the same second the module folder was created. The file itself was saved once at 03:30:46 PDT (its birth and modify times agree to 4 ms) and has never been edited. Both times come before run.py existed (first written 03:35:43; birth time recorded in corrections/pre_correction_0341/manifest.json) and before any 1993-2009 strategy return was computed. Its SHA-256 is e926c3aeef48555d3b895243cfeeb2007a356654207eb10ed8a630de2f270b51, recorded in outputs/tables/M8_preregistration_hash.csv, first_run_record.json and dryrun/first_run_record.json. It lists 32 implementation choices, C1-C32. A dry run on the already seen 2010-01 to 2022-07 window (03:36:35) was used only to catch bugs. The primary run was at 03:37:46 PDT (modules/M8_frozen_pre2010/first_run_record.json). Every later execution printed 'reproduces it: True', including the post-verification rerun at 06:05:14 PDT. Deviations from the pre-registered rule: none. One reporting deviation: C21's one-sided upper p was computed but not written to any table until the post-verification rerun (see Corrections). Between the primary run and 03:41 I changed only output formatting: figure y-axis limits to make room for the legends, LaTeX escaping, the crossings-table caption, and first-run-time columns in the meta table. The verifier confirmed this. It compared the run.py bytecode compiled at 03:37:28 from the 03:36:21 source, before the primary run, with the 03:41 source, function by function. Only fmt, main and make_figure differ, and every statistical function is identical. Another process later imported run.py and recompiled that bytecode (05:50:24), so the pre-primary bytecode survives only in the verifier's record, verify/xv_pyc_observation.json. After verification I changed output code once more (see Corrections).

WINDOW: 1994-03 to 2009-12 (190 months). The rule cannot fire earlier. The first z needs 48 nonzero months from 1985-01; with one zero month in 1985-04 that takes 49 months and gives data month 1989-01. The first threshold needs 60 prior z values, which gives data month 1994-01. With the publication lag, the first decision month is 1994-02. The first actual crossing is in data month 1995-08.

(i) TIMING ALPHA: -0.18%/yr, NW(6) t = -0.27. p-values come from t(175) with k = 15: two-sided 0.79, one-sided upper 0.605 (the C21 statistic). For reference, the bar t >= 2 corresponds to a one-sided p of 0.024. NW(12) t = -0.29, two-sided p 0.77, one-sided 0.613. FAIL.

(ii) CALENDAR SHUFFLE: one-sided p = 0.478 (two-sided 0.956) over 5,000 draws. The shuffled alphas have a median of -0.22%/yr and a 5th-95th percentile range of -1.30% to +0.91%, so the real alpha sits at the centre of the null. FAIL.

(iii) EPISODES: 10 merged runs of 6, 6, 16, 6, 11, 25, 14, 25, 23 and 10 months. PASS (bar 8).

(iv) DROP-ONE: Util -0.61% (t -0.87), Ships +0.03% (t 0.04), Aero +0.01% (t 0.01), Steel -0.19% (t -0.34), BldMt -0.11% (t -0.17). FAIL: the base alpha is not positive, and two of the five flip sign at about zero.

CONTEXT (not in the bar): pi = 0.729, and the rule is in position in 142 of 190 months (75%). Timed net return +0.51%/yr (t 0.42); always-on Short-Brown +0.65% (t 0.48); mean D +0.04%/yr (t 0.06).

DECOMPOSITION (%/yr; exact, residual mean 9e-18):

mean(D) +0.04 = alpha -0.18 + FF5+UMD +0.89 + BOND +0.28 + WTI -0.01 + volatility block +0.00 + conditional Mkt/HML -0.69 + conditional BOND -0.25

- FF5+UMD splits into HML +0.62, Mkt +0.27, RMW -0.16, CMA +0.10, SMB +0.08 and UMD -0.02.
- The volatility block is dVIX, dlogEMV and I x dVIX.
- Conditional Mkt/HML splits into I x HML -0.46 and I x Mkt -0.23.

Only two coefficients have |t| > 2: HML +0.145 (t 2.28) and I x HML -0.143 (t -2.36). They roughly cancel in in-position months.

In the pooled Ferson-Schadt model, the pair describes the always-on benchmark's value exposure in out-of-position months, when D is essentially -pi x R^AO. In those 48 months, the always-on leg's HML-only beta is -0.195 (t -1.93), and -pi x -0.195 = +0.142, close to the pooled +0.145. In the 142 in-position months that beta is +0.008. This reading describes the pooled model and is not robust on its own terms: with the full factor set fitted to the 48 out-of-position months alone, D's HML beta is -0.04 (t -0.47). Either way, the terms are booked as beta, not alpha. The volatility block explains nothing because there is no alpha to explain.

SECONDARY (exploratory): the team EMV_env level signal, lagged one month, run through the same engine on the same window. (i) +0.69%/yr, t 1.00, two-sided p 0.32, one-sided upper p 0.159 (NW12 t 1.16, one-sided 0.124): FAIL. (ii) Shuffle p 0.128: FAIL. (iii) 10 episodes: PASS. (iv) All five drop-one alphas are positive, from Util +0.04% (t 0.06) up to Aero +1.35% (t 2.02): PASS. Verdict: FAIL. pi is 0.556, with 104 of 190 months in position. For comparison, the dry run on the seen 2010-2022 window gave the lagged team signal +1.11% (t 2.03) and the share rule -0.12% (t -0.19). The team signal's pre-2010 alpha is about 60% of that size, with half the t.

CROSSINGS: 33 crossings of the frozen rule have holds inside the window (M8_crossings.csv, with share, z, threshold, overall EMV and VIX). 23 of the 33 extend a hold already running, and 19 fall within one month of a team crossing. They are not volatility events. Against a base rate of 20%, 7 of 33 are in the top quintile of overall EMV and 5 of 33 in the top quintile of VIX, ranking within 1993-2009. Their median ranks are the 45th and 53rd percentiles.

BOND CHECK: the 2022 total return is -15.0%. Exact repricing gives -14.9%, and the Damodaran 10y T-bond return is -17.8%; Damodaran uses year-end yields, while GS10 is a monthly average. 1994: -7.5% (Damodaran -8.0%). 2008: +19.4% (+20.1%). The annual correlation with Damodaran over 1993-2025 is 0.987. Duration matches the closed form to 3e-13, and the monthly return is within 5.4 bp of exact repricing. Duration is NOT 8 to 9 at 1990s yields, as the task expected. It averages 7.2 (range 6.5 to 8.0 at a 6.7% mean yield) and runs 6.8 to 8.8 over 1993-2009. The 8 to 9 range holds at 2 to 4% yields (2010s mean 8.8). This is par-bond arithmetic, not a construction error.

IMPLEMENTATION CHECKS:

- My engine reproduces run_pipeline's 'Original | Short Brown hold 6m' and 'Benchmark | Always-short Brown' net returns bitwise (max diff 0.0), and the team z exactly.
- verify_signal.py, an independent brute-force loop, reproduces the frozen z (2e-14), the threshold (3e-15) and every crossing.
- The team cross_and_holds already implements extend-not-stack (a rolling max of crossings is a union of windows), so no change was needed.
- The numpy shuffle engine matches asset_strategy_returns to a max diff of 4.3e-19 (engine_check_maxdiff in M8_strategy_summary.csv).
- The shuffle's real alpha equals the attribution alpha (asserted).
- Before 2010 there are 7 zero months and 0 'off' months, and the skip-missing crossing rule changes nothing.

CAVEATS:

1. Pre-2010 data informed the team's macro-state notebook (192 pre-2010 months of forward Brown residuals), though no pre-2010 strategy return had been computed.
2. The rule was chosen after seeing 2010-2026, including the holdout. The share transform was motivated by the post-2010 VIX link, and the zero rule by the holdout zeros. The window is out of sample for returns, not for design. A pass would have been weaker evidence; a fail is not weakened.
3. Power is limited. The rule is in position in 75% of months, and the shuffle had only 39 free months to move 10 blocks: 190 decision months, 142 in position, 48 flat, 9 of them needed as separators between the 10 blocks. On the shuffle null, a pass needed alpha above about +0.9%/yr.
4. Brown membership uses a static modern emissions snapshot, which is look-ahead in leg formation.
5. The EMV series are the current FRED vintage, not real-time.
6. The episode threshold of 8 and the sign-only drop-one test are Claude's guesses, and the verdict does not depend on them.
7. The attribution uses current Ken French FF5+UMD, while the hedge keeps the team FF3 file.

FILES:

- Module: /home/hashim/projects/GA/project/research/modules/M8_frozen_pre2010/, containing:
  - PREREGISTRATION.md;
  - run.py (end to end; --dry-run for the seen window);
  - verify_signal.py;
  - first_run_record.json;
  - dryrun/;
  - corrections/ (see below).
- Tables in /home/hashim/projects/GA/project/research/outputs/tables/:
  - .csv and .tex, all compiling with tectonic: M8_passbar, M8_attribution, M8_decomposition, M8_drop_one, M8_strategy_summary, M8_crossings and M8_bond_check;
  - .csv only: M8_decomposition_terms, M8_episodes, M8_shuffle_draws, M8_monthly_panel, M8_preregistration_hash, and M8_tests_ledger (22 rows: 8 primary, 14 exploratory).
- Layout: M8_crossings.tex fits a portrait page with 1 in margins. M8_passbar.tex and M8_strategy_summary.tex fit a landscape letter page only with 0.5 in margins (35 pt too wide at 1 in), and are 216 pt too wide for portrait at 1 in margins (10pt; 263 to 266 pt at 11pt), so they need \resizebox or a landscape page with 0.5 in margins in the report.
- Figure: /home/hashim/projects/GA/project/research/outputs/figures/M8_share_signal.{pdf,png}. Its three stacked panels show the share level with zero months; the frozen-rule z, threshold, crossings and months in position; and the team signal, lagged.

## Corrections after verification

The verifier (VERIFY.md; scripts in modules/M8_frozen_pre2010/verify/) confirmed the FAIL verdict. It also confirmed that run.py implements all 32 preregistered choices, and it reproduced all 128 compared numbers from raw files (largest gap 9e-13). I re-derived each of its points and accept all of them, so there are no rebuttals. None of the corrections is a re-specification: the rule, the window, the regressors and the pass bar are untouched.

| # | Item | Before | After | How I re-derived it |
|---|---|---|---|---|
| 1 | Caveat (3), free shuffle months | "only 38 free months" | 39 free months (190 decision months, 142 in position, 48 flat, 9 separators between 10 blocks) | Runs of the lagged position in M8_monthly_panel.csv: N 190, in position 142, blocks [6, 6, 16, 6, 11, 25, 14, 25, 23, 10]. run.py's `free = N - sum(L) - (m - 1)` = 39, so the shuffle always used 39; only the text was wrong. The secondary signal has 77. |
| 2 | C21 one-sided upper p (reporting gap) | Computed in run.py (`p6_upper`) but written to no table and not quoted | Primary: 0.6048 (NW6), 0.6128 (NW12). Secondary: 0.1588 (NW6), 0.1237 (NW12) | stats.t.sf(t, 175) on the published t-stats gives 0.6048 and 0.1588, matching the verifier's 0.605 and 0.159. |
| 3 | Shuffle-engine check in IMPLEMENTATION CHECKS | "(0.0)" | max diff 4.3e-19 | engine_check_maxdiff = 4.336808689942018e-19 for both signals in M8_strategy_summary.csv. Immaterial. |
| 4 | Pre-registration time in PROCESS | "written at 03:29:54 PDT" | Stamped 03:29:54 (`date`, same second as the folder's birth); file saved once at 03:30:46 | statx birth 03:30:46.443, modify 03:30:46.447; folder birth 03:29:54.463. Both times precede run.py (03:35:43) and the primary run (03:37:46). |
| 5 | Post-primary edits in PROCESS | "figure legend placement"; no bytecode evidence cited | "figure y-axis limits to make room for the legends"; the verifier's bytecode comparison and the 05:50:24 recompilation are cited | verify/xv_pyc_observation.json lists set_ylim constants added in make_figure, plus fmt and main as the only changed functions. |
| 6 | HML reading in DECOMPOSITION | "Together they are the always-on benchmark's residual value exposure in out-of-position months" | Qualified as descriptive of the pooled model, with the split-sample numbers | My own NW(6) split regressions: always-on HML-only beta -0.195 (t -1.93) out of position and +0.008 in position; -pi x -0.195 = +0.142 against the pooled +0.145. The full factor set on the 48 out-of-position months gives D's HML beta -0.044 (t -0.47), which matches the verifier. |
| 7 | M8_crossings.tex layout | 5.66 pt overfull on a landscape page with 0.5 in margins (10pt article; reproduced with tectonic) | Short headers, \footnotesize and \tabcolsep 4pt; no overfull box on a portrait letter page with 1 in margins at 10pt or 11pt | Compiled all seven M8 .tex files with tectonic in both geometries. The CSV keeps its full column names. |

The code change for items 2, 4 and 7 is output-only; the full diff is in modules/M8_frozen_pre2010/corrections/run_py_changes.diff.

- M8_attribution.csv gains two columns, `p_upper_nw6_t(n-k)` and `p_upper_nw12_t(n-k)`, for every term. They are appended after the existing columns, so every earlier column keeps its position and values.
- The four `i_alpha` rows of M8_tests_ledger.csv now quote the one-sided p in their notes, as C32 (every statistic in the ledger) requires.
- M8_preregistration_hash.csv gains `prereg_file_mtime` (03:30:46 PDT) next to the existing `prereg_written` stamp.
- M8_crossings.tex gets the new layout.
- The console line prints the one-sided p.

No statistical function changed. I went beyond the verifier's text-only suggestion here because C21 says the one-sided p is "reported" and C32 puts every statistic in the ledger. Writing out a number the frozen code already computed is a correction toward the preregistration, not a change to it.

Rerun evidence (06:05:14 PDT):

- run.py printed 'this run reproduces it: True' against the 03:37:46 first-run key (alpha, t, shuffle p, episodes, five drop-one alphas, verdict).
- modules/M8_frozen_pre2010/corrections/rerun_comparison.csv (script compare_rerun.py) compares every table with the 03:41 copy:
  - 16 of 20 table files are byte-identical;
  - the 4 that changed are M8_attribution.csv, M8_tests_ledger.csv (4 note cells), M8_preregistration_hash.csv (this_run_time and the new column) and M8_crossings.tex;
  - every shared numeric column has a max abs diff of 0.0;
  - the figure PNG is byte-identical.
- The verifier's own verify/xv_independent.py, run from a scratch copy so that its outputs in verify/ were not overwritten, still passes all 128 of 128 comparisons against the corrected tables.

Preserving the timeline:

- The rerun rewrote outputs/tables/M8_* in place. Their birth times (first table 03:38:13) are unchanged, but their modify times show the latest rerun (06:05 for the correction run; the verifier's round-2 rerun moved them to 06:10).
- The 06:05 edit re-created run.py as a new file, so `stat run.py` now shows birth 06:05:07. Its original birth, 03:35:43.583, is recorded in corrections/pre_correction_0341/manifest.json and in VERIFY.md round 1.
- The 03:41 state is preserved in modules/M8_frozen_pre2010/corrections/pre_correction_0341/: cp -p copies of every M8 table and figure, run_0341.py (the 03:41:13 source that produced them), and manifest.json with each file's SHA-256, birth and modify time as they were before the rerun.
- first_run_record.json (03:38:18), dryrun/ and PREREGISTRATION.md were not touched. Its SHA-256 is still e926c3ae...0b51.

Deviations, updated: the rule has none. There is one reporting-only deviation: the C21 one-sided upper p was computed by run.py but not written to a table until the post-verification rerun. The before and after values are in item 2.
