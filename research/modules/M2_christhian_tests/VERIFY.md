<!-- Reconstructed by the orchestrator from the verifier's structured return (the harness blocked the verifier's own report write). -->
# Verification

## Round 1

all_confirmed: False

### Confirmed claims
- METHOD: I ran the module once (exit 0, 239 s). Outputs are identical to the pre-rerun snapshot: max numeric diff 0.0 in q1/q2/q4/q3 primary, q4_breakeven and key_numbers. My own script does not import run.py or helpers.py. It rebuilds COMEQ, the corrected baseline, the raw p80 signal, the 60-month rolling hedge, positions, P&L, costs, the NW(6) regression and the t(n-k) p-values from scratch; it takes only the pure and continuous signals from team_pipeline.build_signals. Result: 785 checks, 783 match (verify/verify_results.csv). A separate text-vs-CSV sweep has 311 checks, 301 match (verify/verify_text_claims.csv).
- Q2 PRIMARY CONFIRMED (corrected baseline, 5/5 legs, FF5+UMD+COMEQ hedge and alpha, team costs). All 14 alphas, t-stats, t(n-8) p-values and Holm p-values reproduce to within 5e-8. Post-2010 alphas run from -0.005% (Always-short) to 0.59% (Original 6m), with max t 0.83. Holdout alphas run from -0.61% to -3.28%. The smallest p is 0.028 (Original/Pure 3m holdout, -2.50%) and its Holm p is 0.397. There are 0 positive survivors.
- Q1 PRIMARY CONFIRMED (corrected baseline, 8/8 legs with Hardw, FF3). All 14 tests reproduce. Post-2010 alphas are 0.17% to 1.56% (t 0.56 to 1.67). Holdout alphas are -0.39% to -2.51%. The smallest p is 0.077 and every Holm p is 1.00. 8/8 H and 8/8 M strategies are identical across the whole grid (max alpha diff 0), because only the Brown leg is traded. Hardw and MedEq tie at 0.0126581. The raw-spread tie-break sign flip is confirmed: holdout +1.21% for 8/8 H vs -2.52% for 8/8 M.
- Q3 CONFIRMED. Raw 5/5 GB HML loading: FF3 -0.233 (t -4.63) in 1970-2026 and -0.298 (t -5.74) post-2010; FF5+UMD -0.140 and -0.240; largest Holm p 0.017 within 4. The exact decomposition holds to 1e-10. Post-2010 FF3: Brown side -0.437, Green side +0.139. The drivers are Steel (-0.135) and Ships (-0.105). Fin (+0.080) and RlEst (+0.090) offset part of the loading. Also reproduced: full-sample -0.419/+0.186, holdout -0.518/+0.392, the 78% share of negative rolling windows, and the 88.5% share of years with negative GB relative BE/ME. The Brown-leg value reading is supported both by the loadings (relative to the market as the zero point) and by BE/ME characteristics.
- Q4 CONFIRMED. All 28 validation break-evens reproduce (both baselines, FF3 and FF5UC hedges). Corrected FF3: 42, 40, 93, 100, 46, 47 and 211 bp, so the range is 40-211 bp. Team FF3: 37, 37, 111, 108, 53, 53 and 211 bp. FF5UC: 19-50 bp (corrected) and 16-68 bp (team). Validation turnover is 5.1, 5.8, 2.4, 2.5, 1.3, 1.5 and 0.7 a year. Costs enter linearly, so break-even = alpha(0)/slope exactly. All 28 zero-cost holdout alphas (5/5, both baselines, FF3 and FF5UC) are negative, e.g. -1.67% for Original 3m and -1.65% for Always-short. The Q4 primary family reproduces: best Holm p 0.838, 0 survivors.
- WHOLE GRID CONFIRMED from the ledger. The family has 8,091 tests, equal to the 7,938 non-gross strategy regressions plus the 153 spread regressions, so it is complete. Holm: 0 positive survivors; the minimum Holm p is 0.0818, for a negative last-18-month alpha. BH: 0 positive and 27 negative survivors. 368 positive and 531 negative tests have p < 0.05. The ledger has 13,452 unique IDs: 46 primary, 5,562 robustness, 7,844 exploratory. A random sample of 90 strategy-grid rows (all 5 hedges, all cost levels, windows including covid/last12/last18/full_live, and the +cmdty and +lead evaluations) and 25 spread rows was recomputed independently. Every row matches, with max alpha diff 3e-9 and max t diff 5e-8.
- CORRECTED BASELINE CONFIRMED. CPI is linearly interpolated at 2025-10 and attention plus all five purification controls are lagged one month, which matches the project definition. The corrected raw p80 state equals the team state shifted +1 month exactly. The purified signal is NaN in Nov and Dec 2025 under the team baseline and defined under the corrected one. Under the corrected baseline Pure equals Original in the holdout for both hold lengths. I found no look-ahead: betas estimated through t are applied at t+1, the threshold uses only past values, and the leading WTI/IMF values enter only the evaluation regressions, not trading. Full-live start dates are as stated (team 1993-01 for the raw rules and always-short, 1992-12 continuous raw, 1999-02 pure rules, 1999-01 continuous pure; corrected one month later).
- COMEQ CONFIRMED. It is mean(Oil, Coal, Mines, Gold) - RF from the team FF49 file, starting 1963-07 with no later gaps. Over 1992-02 to 2026-06: correlation with WTI 0.23 (0.40 with next month's WTI), with IMF 0.33 (0.47 next month), with the Brown leg 0.66 and with the market 0.55. On FF5+UMD it has R2 0.37 and alpha -0.89% (t -0.24). The FF5-file HML equals the team FF3 HML (diff 1e-16); SMB correlation is 0.979 from 1970 on.
- TEAM ANCHORS AND CONVENTIONS CONFIRMED. My engine reproduces the write-up's team Pure 6m validation FF3 alpha of 2.51% and Original 3m holdout t of -2.19. Annualization is 12 x mean. Costs match (10/5/25 bp or uniform, charged at t+1). The sign convention is short the Brown-leg residual. NW is Bartlett with 6 lags and no small-sample correction; my NW matches statsmodels HAC(6, use_correction=False) to 1e-8. p-values come from t(n-k) in every window.
- OTHER TEXT NUMBERS CONFIRMED against the CSVs: the Q2 spread control table (alphas, HML, COMEQ and UMD loadings), the 8/8 H 1970-2026 FF5UC alpha of 2.52% (t 2.57, p 0.010), the post-2010 t-stats for the FF3 vs FF5UC hedges, the holdout ranges across hedges, and Original 3m turnover 4.80 -> 5.99 with cost drag 0.53% -> 0.85%. Also the residual HML ranges, the robustness ranges (team baseline, 8/8, COMEQx, WTI/IMF), bootstrap p >= 0.29, the Q1 team-baseline table, the Q1 bootstrap p-values (0.050, 0.037, 0.056), the best-case table (all strategy bests in COVID), and the best post-2010 test (Original 6m, team, FF5UC, 5 bp: 1.36%, t 1.98, p 0.049).
- VERDICT: the substantive conclusions hold. No positive alpha survives Holm or BH in any primary family or across the grid. The HML exposure is a Brown-leg value tilt. The holdout fails before costs. The 'Do not implement' verdict holds. The required fixes are wording and scope corrections; they do not change the verdict.

### Required fixes
1. [Substantive overreach, Answer section and Implications] The text says 'Every hedged strategy has a negative holdout alpha under every leg design, control set and cost level, including zero cost' and that validation alphas 'reverse in the holdout under every leg design, control set and cost level, including zero cost'. This is false. In strategy_grid.csv, 24 of the 1,078 holdout regressions have a positive alpha. All 24 are Always-short Brown with 8-and-8 legs (L8H/L8M x team/corr x FF3, FF3U, FF5U, FF5UC or FF5UCx hedges, evaluated on E:FF5UC or E:FF5UC+cmdty). The largest is +0.42% (t 0.22). The best-case table already reports it ('Always-short best holdout 0.42 (0.22)'), so the FINDINGS text contradicts itself. Zero-cost (u0) runs exist only for 5-and-5 legs with the FF3 and FF5UC hedges. Replace with: 'All six attention-timed rules have a negative holdout alpha in every configuration run. The always-short benchmark with 8-and-8 legs has small positive holdout alphas in 24 rows (max 0.42%, t 0.22). At zero cost, run only for 5-and-5 legs with the FF3 and FF5+UMD+COMEQ hedges, all 28 holdout alphas are negative.'
2. [Q4 qualifier] 'Holdout alpha before costs is negative for every strategy, baseline and hedge' holds only for 5-and-5 legs and the FF3 and FF5UC hedges. Those are the only zero-cost runs (max gross holdout alpha -0.39%, Continuous pure, team, FF5UC). Add that qualifier here and in headline 5.
3. [Q2 mislabel] 'Overlay turnover rises 24% to 37% for the signal rules and 127% for always-short' uses TOTAL turnover (asset + overlay): 4.80 -> 5.99 is +24.9%. Overlay turnover itself rises 35% to 54% for the signal rules and 163% for always-short (q2_hedge_cost_post2010.csv, corrected baseline). Either write 'total turnover rises 24-37% (always-short 127%)' or 'overlay turnover rises 35-54% (always-short 163%)'.
4. [Q4 last-12 wrong] The text says 'Last 12: Original 3m +1.15% (t 0.28) and Original 6m +1.51% (t 0.28); the others are negative.' Pure 3m and Pure 6m have the same positive alphas, because Pure = Original in the corrected holdout. Replace with: 'Original/Pure 3m +1.15% (t 0.28) and Original/Pure 6m +1.51% (t 0.28); the continuous rules and always-short are negative.'
5. [Q4 incomplete range] 'Other break-evens (corrected, FF3): 27-60 bp post2010 and 10-61 bp over the full live sample' leaves out always-short, which is 124 bp post2010 and 131 bp full live. Write: '27-60 bp for the six signal rules post2010 (always-short 124 bp) and 10-61 bp over the full live sample (always-short 131 bp).'
6. [Headline 1 and grid wording] The '8,091 net-of-cost alpha tests' include 153 raw Green-minus-Brown spread alphas, which are unhedged and cost-free (7,938 strategy alphas + 153 spread alphas). Write '8,091 alpha tests (7,938 net-of-cost strategy alphas and 153 raw-spread alphas)'.
7. [Headline 2 overreach] 'No positive commodity-controlled alpha exists' is wrong as written: 6 of the 7 post-2010 Q2 primary point estimates are positive (up to 0.59%, t 0.83). Write 'No commodity-controlled alpha is significantly positive.'
8. [Q3 rolling, minor] 'The exception is windows ending around 2009-2013, which peak at +0.53' is slightly off. The positive run covers windows ending 2008-02 to 2013-10 and peaks at +0.53 in the window ending 2008-12. There is also an earlier positive run in windows ending 1983-12 to 1987-03 (max +0.25). Fix the dates.
9. [Implications, minor] 'The team hedge already removes most of it: residual loadings are -0.02 to -0.08 post-2010' mixes two hedges. The team FF3 hedge gives -0.015 to -0.053 (t -1.19 to -1.95); -0.079 comes from the FF5UC hedge. Write '-0.015 to -0.053 under the team FF3 hedge'.
10. [Q2 wording, minor] 'The richer controls roughly halve the long-window loading' is true for 1970-2026 (-0.23 -> -0.11). Post-2010 the loading only falls from -0.30 to -0.21 (-0.19 with WTI and IMF), about 30%. State both.
11. [Rounding, trivial] The IMF t post2010 is 0.65, not 0.66 (WTI -0.66 is correct). Steel + Ships contribute -0.239, not -0.240 (-0.1345 - 0.1047).
12. [Output hygiene] q1_comparison.csv carries the inherited team column significant_after_multiple_testing = True for L5/team Original 3m and Continuous raw, and for L5/corr Original 3m and Pure 3m. That flag comes from normal p-values on 24-month COVID NW(6) t-stats (replication audit item 3), and it contradicts M2's own t(n-k) conclusion. Drop the column or rename it (for example team_holm_flag_normal_p) before anyone cites the CSV.
13. [Ledger completeness, minor] FINDINGS cites the COMEQ spanning regression (alpha -0.9%, t -0.24, R2 0.37 on FF5+UMD; COMEQx R2 0.45) and the lead and Brown-leg correlations, but the ledger has only the 12 same-month corr_WTI/corr_IMF tests. Add the COMEQ and COMEQx FF5+UMD alpha tests to the ledger.
14. [Tex caption, minor] The q2_comeq_justification.tex caption says '1992-02 to 2026-07'. The correlations use 1992-02 to 2026-06 (n = 413, because the t+1 leads need one extra month); only the FF5+UMD regression runs through 2026-07 (n = 414). Fix the caption.
15. [Process] FINDINGS.md does not exist on disk because the builder's write was blocked. The orchestrator must save the builder's text with the corrections above to /home/hashim/projects/GA/project/research/modules/M2_christhian_tests/FINDINGS.md. VERIFY.md was not written either, because subagents may not write report .md files; this structured output is its content.
16. [Unverifiable wording, low priority] 'fixed in the run.py docstring before any M2 result existed' cannot be checked: there is no version history. Keep it only if there is a timestamped record; otherwise write 'stated in the run.py docstring'.

## Round 2

all_confirmed: False. All 16 round-1 fixes are resolved, and every headline number in the corrected FINDINGS reproduces independently. Six text fixes remain. Two are new provenance and interpretation sentences, and four are small errors that were already in the text and that round 1 missed. None of them changes a number, a test result or the verdict.

### Method
- **Rerun of run.py.** I saved an md5 snapshot of the 45 current tables and reran `run.py`. It exited 0 in 1 min 41 s, with 46 pipeline runs (8 in full mode), 8,050 strategy regressions, 13,482 ledger tests and a grid family of 8,091. All 45 tables came out byte-identical to the pre-rerun files, so the corrected outputs are reproducible. The 12 figures were regenerated.
- **Comparison with the round-1 verified outputs** (scratchpad snapshot `m2fix/before`, identical to `m2_before`):
  - Every number in the round-1 tables is unchanged.
  - `q1_comparison.csv` and `q2_comparison.csv`: two columns renamed, values identical.
  - `q2_comeq_justification.csv`: four columns added (`ff5u_start`, `ff5u_end`, `ff5u_n`, `ff5u_p_alpha`).
  - `q2_comeq_justification.tex` and `summary_best_case.tex`: captions and period labels edited.
  - `tests_ledger.csv`: 30 new exploratory `comeq|` rows and 12 notes reworded; all other rows identical.
  - `key_numbers.csv`: 23 new keys, and `n_ledger_tests` went from 13,452 to 13,482.
  - Two new files: `q2_hedge_cost_change.csv` and `q3_rolling_positive_runs.csv`.
  - The only difference between the fixer's two reruns is 7 extra keys in `key_numbers.csv`.
- **`verify/verify_m2.py`, rerun.** I patched only V10, which now compares just the keys present in the round-1 `key_numbers.csv`. Result: 785 checks, 783 match, and every recomputed value and every module value equals round 1 exactly (max diff 0). The two mismatches are the round-1 claim tests behind fixes 1 and 2: 24 positive holdout rows, and no zero-cost 8-and-8 runs. The corrected text now states both facts.
- **`verify/verify_text_claims.py`, rerun with the round-1 wording.** 311 claims, 299 match. The 12 mismatches are the 10 round-1 wording errors, all now corrected, plus the two ledger counts that grew by 30 under fix 13.
- **New `verify/verify_round2.py`.** This is an independent engine that imports no module code. It has 344 checks, and 339 match. It recomputes:
  - all 1,078 holdout strategy regressions (max alpha diff 5e-10, max t diff 5e-8);
  - the FF3 to FF5+UMD+COMEQ hedge-cost change;
  - the rolling-beta positive runs;
  - the COMEQ, COMEQx and industry spanning regressions and the new ledger rows;
  - the full corrected Q1 and Q4 tables and the residual-HML ranges;
  - the BE/ME shares, the ledger counts and the BH counts.
  The 5 mismatches are new fixes 4 and 6 below.
- **New `verify/verify_text_claims_r2.py`.** It checks the corrected wording against the CSVs: 545 claims, 544 match. The one mismatch is the rounding in new fix 6.
- **Builder transcript.** For fix 16 I read the builder transcript (workflow wf_bd8d2a66-0fa, agent a7dd3a997df54dc45).

### Status of the round-1 required fixes
1. **Resolved.** Independently recomputed:
   - There are 1,050 net-of-cost holdout regressions, 150 per strategy.
   - Six signal rules: 0 of 900 are positive. The highest is -0.03% (t -0.08): Continuous pure, 8/8 H (8/8 M is identical), team baseline, FF3 hedge, E:FF5UC+cmdty.
   - Always-short: 24 of 150 are positive, all with 8-and-8 legs. That is 12 L8H and 12 L8M rows out of its 92 8-and-8 rows, all at team costs, spanning all five hedges and both baselines; 4 are evaluated on E:FF5UC and 20 on E:FF5UC+cmdty.
   - The largest is +0.42% (t 0.22): 8/8, team baseline, FF5U hedge, E:FF5UC+cmdty. The 5-and-5 maximum is -0.91%.
   - The Answer, the census block and Implications now match these numbers.
2. **Resolved, and the fixer's correction of my round-1 detail is right.** The highest zero-cost holdout alpha is -0.39%, for Continuous pure, team baseline, **FF3** hedge (t -1.35), not FF5UC as I wrote. The team FF5UC Continuous pure value is -0.47%. All 28 zero-cost holdout alphas are negative (recomputed). The qualifier now appears in Answer, Conventions, Q4, Implications and Caveats.
3. **Resolved.** Corrected baseline, post2010, recomputed with my engine for all 14 rows of `q2_hedge_cost_change.csv`:
   - Total turnover rises 23.6% to 37.0% for the signal rules and 126.6% for always-short.
   - Overlay turnover rises 35.1% to 53.9% and 163.2%.
   - Original 3m total turnover goes from 4.80 to 5.99, and its cost drag from 0.53% to 0.85%.
   - Always-short gross return goes from 1.15% to 0.44%.
4. **Resolved.** In last12, Pure equals Original to 1e-12, and the continuous rules and always-short are negative.
5. **Resolved.** Post2010: 27-60 bp for the signal rules and 124 bp for always-short. Full live: 10-61 bp and 131 bp.
6. **Resolved.** The family is 7,938 strategy alphas plus 153 spread alphas. The count is in `key_numbers.csv` and in the `summary_best_case.tex` caption.
7. **Resolved.** 6 of 7 post2010 point estimates are positive (-0.005% to 0.59%, t at most 0.83).
8. **Resolved.** I recomputed the runs and peaks: 2008-02 to 2013-10 (69 windows, +0.53 at 2008-12) and 1983-12 to 1987-03 (40 windows, +0.25 at 1985-03). Every other run has at most 9 windows and a peak of at most +0.10. The Brown-leg betas at the two peaks are -0.04 and -0.12. The interpretive sentence added with this fix overreaches (new fix 3).
9. **Resolved for the corrected baseline** (-0.015 to -0.053, t -1.19 to -1.95). The newly added team-baseline range has a rounding slip (new fix 6). The FF5UC range (-0.024 to -0.079, t -0.78 to -1.69) is correct.
10. **Resolved.**
11. **Resolved** (0.65 and -0.239).
12. **Resolved.**
    - The column is renamed in both files, with values unchanged.
    - The True rows in `q1_comparison.csv` are exactly the four named in the text, and `q2_comparison.csv` has none.
    - `team_active_months_full_nonzero_net` is present in both files.
13. **Resolved.**
    - There are 42 `comeq|` rows (6 series x 7 tests), all exploratory and outside the grid family.
    - COMEQ: alpha -0.89%, t -0.24, p 0.810, R2 0.373, n 414. COMEQx: -1.42%, t -0.35, R2 0.451.
    - The ledger t and p values, and the lead and Brown-leg correlation t-stats, equal my recomputation.
14. **Resolved.** The caption is built from the data: 1992-02 to 2026-06, n = 413 for the correlations, and 1992-02 to 2026-07, n = 414 for the spanning regression.
15. **Resolved** (process).
16. **Resolved.**
    - The transcript timestamps match the text: COMEQ-correlation check at 09:59:44 UTC; smoke test at 10:02:26 that printed the Q2-primary configuration's post2010 and holdout alphas (for example Original 3m holdout -2.50, t -2.27); first Write of `run.py` at 10:06:36.
    - The primary-spec block of the docstring and the `PRIMARY` dict in the current `run.py` are character-identical to that first write.
    - The Q1 (corrected, 8/8) and Q4 (corrected, u5) configurations were not computed before 10:06:36.
    - The withdrawn claim is gone.

**Additional correction confirmed:** the 6-month rules' validation FF3 alphas (FF3 hedge, team costs, both baselines, all leg designs) run from 1.80% (corrected 8/8 Original 6m) to 2.60% (team 8/8 Pure 6m).

### Other headline numbers reproduced this round
All of these reproduce with my engine or against the CSVs:
- **Corrected Q1 table:** all 56 cells (alpha and t, 5/5 and 8/8, validation and holdout).
- **Q4 cost table:** all 55 cells at 5, 10 and 25 bp.
- **Q4 primary:** post2010 alphas 0.32% to 1.61% (t 0.73 to 1.89), holdout -0.51% to -1.87%. The best Holm p is 0.838 (Pure 6m post2010, raw p 0.060).
- **Q2 across the four hedge sets:** holdout alphas -0.58% to -3.44% (t -1.01 to -2.27).
- **Q2 table:** the FF3 vs FF5UC post2010 t-stats.
- **Best-case table:** every cell, including the Q2 Holm column and the raw-spread row.
- **BH negatives:** 23 in last18 and 4 in the holdout, all 4 on E:FF5UC+cmdty+lead. The best positive test is Pure 3m, COVID, corrected baseline, u5 (p 0.00035, BH 0.062, Holm 1.00).
- **Ledger:** 13,482 tests (46 primary, 5,562 robustness, 7,874 exploratory).
- **Verdict:** Do not implement still holds.

### Required fixes (round 2)
1. **[Run paragraph, provenance statement is false]**
   - Quote: "After the verification round the module was rerun twice. All 45 tables are byte-identical to the verified run except `key_numbers.csv`, which gained 7 traceability keys (holdout census configurations and ledger counts)."
   - Problem: against the round-1 verified outputs, 7 existing files changed and 2 are new. The byte-identity holds only between the fixer's two reruns.
   - Replacement: "After the verification round the module was rerun twice. Every number in the round-1 verified outputs is unchanged. The fixes added two tables (`q2_hedge_cost_change.csv`, `q3_rolling_positive_runs.csv`), 30 exploratory `comeq|...` ledger rows, four spanning-regression columns in `q2_comeq_justification.csv` and 23 keys in `key_numbers.csv`. They also renamed two inherited columns in `q1_comparison.csv` and `q2_comparison.csv` and edited the captions and labels of `q2_comeq_justification.tex` and `summary_best_case.tex`. The second rerun reproduced the first byte for byte except `key_numbers.csv`, which gained 7 traceability keys (holdout census configurations and ledger counts)."
2. **[Response to verification, preamble, same error]**
   - Quote: "All other tables are byte-identical to the verified run."
   - Replacement: "All other tables are byte-identical to the first post-verification rerun. Against the round-1 verified run, every previously reported number is unchanged (the file-level changes are listed under Run)."
3. **[Q3 rolling, the new sentence overreaches]**
   - Quote: "At both peaks the Brown leg's own HML beta was slightly negative (-0.04 and -0.12), so the spread's sign flips only when the Brown leg temporarily loses its value tilt."
   - Problem: at the two peaks the Green leg's rolling HML beta was 0.21 (1985-03) and 0.41 (2008-12), against a 1975-2026 average of 0.10. In the 2008 episode the Green leg supplies 0.41 of the +0.53. Short positive spells also occur while the Brown leg keeps a normal value tilt, for example the window ending 2014-02 (Brown 0.28, Green 0.29) and 1992-02 (Brown 0.16).
   - Replacement: "At both peaks the Brown leg's own HML beta was slightly negative (-0.04 and -0.12) while the Green leg's was well above its 0.10 average (0.21 and 0.41). Both sustained flips therefore combine a temporary loss of the Brown leg's value tilt with an unusually value-tilted Green leg; in the 2008 episode the Green leg supplies most of the +0.53."
4. **[Q3 characteristics, older error missed in round 1]**
   - Problem: the stated shares equal 1 minus the share of years below the median, so they count years at the median as "above". Strictly above the median: Steel 98% (1 year at the median), Ships 92% (1 year), RlEst 77% (5 years), Telcm 81% (2 years). Util (100%) and Fin (96%) are unaffected.
   - Quote: "Util and Steel are above the 49-industry median in 100% of years and Ships in 94%." Replacement: "Util and Steel are at or above the 49-industry median in 100% of years and Ships in 94%."
   - Quote: "Fin, RlEst and Telcm are above it in 96%, 87% and 85%." Replacement: "Fin, RlEst and Telcm are at or above it in 96%, 87% and 85%."
5. **[Q4, older error, trivial]**
   - Quote: "With the 8-factor FF5+UMD+COMEQ hedge, break-evens fall to 19-50 bp (corrected) and 16-68 bp (team)."
   - Problem: FF5+UMD+COMEQ has seven factors; k = 8 counts the intercept.
   - Replacement: "With the seven-factor FF5+UMD+COMEQ hedge, break-evens fall to 19-50 bp (corrected) and 16-68 bp (team)."
6. **[Rounding, trivial]**
   - Problem: the least-negative team-baseline residual HML loading is -0.018499 (Continuous raw), which rounds to -0.018.
   - Quote (Q2): "Under the team baseline: -0.019 to -0.061 (t -1.35 to -2.36)." Replacement: "Under the team baseline: -0.018 to -0.061 (t -1.35 to -2.36)."
   - Quote (Response item 9): "The team-baseline range (-0.019 to -0.061, t down to -2.36)". Replacement: "The team-baseline range (-0.018 to -0.061, t down to -2.36)".

### Recommended wording changes (not blocking)
- **Data, "not spanned".**
  - Quote: "It is not spanned by FF5+UMD: R-squared 0.37, alpha -0.89% a year (t -0.24, p 0.81)."
  - Problem: in spanning-test language, an insignificant alpha means FF5+UMD does span COMEQ's mean return. The R-squared shows only that most of its variance is unexplained.
  - Suggested: "Most of its variance is not explained by FF5+UMD (R-squared 0.37), and its alpha on them is small and insignificant (-0.89% a year, t -0.24, p 0.81): it is a distinct exposure, not a source of alpha."
- **Conventions, zero-cost runs.**
  - Quote: "Zero cost (u0) is used only to compute break-evens."
  - Problem: the zero-cost holdout alphas are now also cited, in the Answer, Q4 and the census.
  - Suggested: "Zero cost (u0) is used only for break-evens and for the before-cost holdout alphas."
- **Timing record, completeness.** A check at 09:57:23 UTC, before the 09:59 data check, ran the team pipeline at its defaults. It printed the team's unconditional GB HML loadings: -0.24 for 1970 to 2022-07 and -0.35 post-2010. This is consistent with "The sign of the Q3 loading was already known from the team write-up". For completeness, "Two things came before it" could list this run as well.

### Scripts and outputs (round 2)
- `modules/M2_christhian_tests/verify/verify_m2.py`: round-1 engine, rerun; V10 is patched for the new `key_numbers.csv` keys. Output: `verify_results.csv`.
- `modules/M2_christhian_tests/verify/verify_text_claims.py`: round-1 wording, rerun. Output: `verify_text_claims.csv`.
- `modules/M2_christhian_tests/verify/verify_round2.py`: new independent checks. Output: `verify_round2_results.csv`.
- `modules/M2_christhian_tests/verify/verify_text_claims_r2.py`: corrected wording against the CSVs. Output: `verify_text_claims_r2.csv`.
