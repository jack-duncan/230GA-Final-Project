# M7 robustness ledger: adversarial verification

Verifier run on 2026-09-26. Scope: rerun `run.py`; recompute on my own the census counts, the Holm, BH and BY survivors in every family, and the deflated appraisal ratio of each candidate from the Bailey and Lopez de Prado (2014) formula; check the family definitions and every other check against the adopted spec; flag any conclusion that overreaches.

**Verdict.** Every number in FINDINGS reproduces except one rounding (R5). My independent recomputations agree with M7 to machine precision. The family map matches the adopted spec exactly. The three final verdicts are confirmed:

- the book: paper-trade, and the report verdict stays "Do not implement";
- the EPA 5v5 spread: "Do not implement";
- the attention thesis: "Do not implement".

The write-up still needs fixes before it goes into the report:

- four sentences are factually wrong or overreach (R1 to R4);
- five are small corrections (R5 to R9);
- a few quoted numbers have no ledger row, which spec G7 requires (R10).

`all_confirmed` = false until R1 to R10 are applied.

## 1. What I ran

- **Rerun.** `uv run python modules/M7_robustness_ledger/run.py`, 46.5 s wall time, exit 0.
  - All three pre-registration hashes verified.
  - The frozen run reproduced `first_run_record.json`: the net-return SHA-256 matched and the file was unchanged byte for byte.
  - Every `outputs/tables/M7_*` file is bit-identical to the pre-rerun snapshot, except the `this_run_utc` timestamp in `M7_preregistration_hash.csv`.
- **Verification scripts** (in `modules/M7_robustness_ledger/verify/`, logs in `verify/out/`):
  - `v1_census_mt.py` reads the eight module ledgers directly, not `M7_all_tests.csv`. It classifies rows with plain `re` per spec check 1 and runs Holm, BH and BY with `statsmodels.multipletests`, not M7's own adjusters.
  - `v2_search_dsr.py` regenerates all 58 and 89 search members with the modules' library calls. Everything else is my own code:
    - numpy OLS with a hand-written Newey-West estimator (Bartlett kernel, 6 lags, no scaling);
    - my own stationary bootstrap, with three draw orders and seeds;
    - Romano-Wolf and SPA written from the spec formulas;
    - Nyholt and Li-Ji;
    - the cluster V;
    - my own `expected_max` and `deflated_sr` from the Bailey and Lopez de Prado formula;
    - the holdout reading, cost stress, and the frozen-run statistics from the saved returns.
  - `v3_claim_checks.py` spot-checks quoted claims: factor source, windows, eval_end, duplicates, fallbacks, ledger coverage, provenance.
- **Spec.** `adopted_checks.md` is not on disk yet. I pulled it from the workflow journal, where it is the only version.
  - Its SHA-256 with a final newline is 15fdce70...f8e70b, equal to the pre-registered hash.
  - I also simulated `lib/save_returned_files.py`'s `write_text` (locale UTF-8) and got the same hash, so the first run after the orchestrator saves the file should verify.
  - optimizer.py and m5lib.py hash to the recorded values (`sha256sum`). Their last change was at 02:55 and 03:31 PDT, before the 08:49:39 PDT pre-registration.
- **LaTeX.** All 10 `M7_*.tex` tables compile with tectonic and the report preamble. The only messages were a 1 pt overfull box in the census table and underfull boxes in the p-column verdict table, both cosmetic.
- **Figures.** I checked all three figures visually. Labels and critical values match the tables.

## 2. Census and family map (check 1): confirmed

| Item | FINDINGS | Independent | Match |
|---|---|---|---|
| Ledger rows, exact duplicates | 23,923, 0 | 23,923, 0 | yes |
| F / P / D / X / L / R / E | 1 / 81 / 73 / 170 / 4,850 / 9,337 / 9,411 | same | yes (0 cell differences in the family-by-module table) |
| P by module | M1b 24, M2 42, M3 12, M4 1, M5 2 | same | yes |
| D by module | M1 15, M1b 16, M2 4, M3 21, M5 2, M6 8, M8 7 | same | yes |
| R-M2 / R-other | 8,161 / 1,176 (M1b 736, M3 156, M4 282, M6 2) | same | yes |
| Label by module | all rows and totals | same (0 cell differences) | yes |
| Nominal p2 < 0.05 | 4,184: alpha 1,624 (783+, 841-), loading 1,325, mean 561, other 536, beta-timing 138 | same; loading share 31.7% | yes |
| Nominal in D / X / L / E | 15 / 33 / 1,452 / 1,636 | same | yes |

The family rules in `run.py` follow the spec's first-match order F, P, D, X, L, R, E exactly, and the type rules follow its regex order.

## 3. Multiple testing (checks 2 and 3): confirmed

- **Family P.**
  - 81 rows collapse to 73: 6 M2 and 2 M3 duplicates, all Original/Pure holdout pairs, as stated.
  - Smallest adjusted p: Holm 1.0000, BH 0.7181, BY 1.0000. No survivors.
  - Best one-sided p 0.02991 (`strat|L5|corr|FF3|u5|Pure 6m|post2010`, t 1.893); Sidak count 1.689.
  - Largest absolute difference from `M7_family_P.csv`: 1.1e-16.
- **Family F.** Raw one-sided p 0.6048 (M8, t -0.266) and 0.00737 (check 7 (i)). Holm gives 0.6048 and 0.01475, so only check 7 (i) survives.
- **All 155 primaries** (not adopted). 154 have a p-value; `M8_share_iii_episodes` has none. Survivors: Holm 4, BH 6, BY 4, none of them alpha-type. The module attributions are correct: Q2 joint Wald and Q3 Fisher are M1; the HML loadings are M2; the beta-timing term is M3.
- **Family R** (one-sided BH and BY, positive side). Every cell of the FINDINGS table reproduces:
  - m, share positive, smallest p1, smallest BH and BY p, survivors;
  - largest difference in adjusted p 1.1e-16;
  - BY divisors 9.584 and 9.719.
  - The single BH survivor is `CPU_realtime_none_O3_covid_alpha` (t 4.717, alpha 6.83%, n 24).
- **R-M2 by window.** Both the all-rows and strategy-only columns reproduce to the printed precision:
  - 153 spread rows and 8,008 strategy rows;
  - validation 88.9% (median t 1.14, or 1.15 on strategy rows);
  - holdout 2.7% / -1.32 on all rows, 2.3% / -1.34 on strategy rows;
  - last 18 months 0% / -2.35;
  - full_1970 21 rows, all spread rows, 100% positive.

## 4. Search families (check 4): confirmed

- **Members.**
  - S-full has 679 x 58 and S-post 199 x 89, with no missing month.
  - My NW t-statistics match `M7_search_members.csv` to 4.7e-14 and the alphas to 1.3e-15.
  - Membership follows the spec's lists and exclusions.
  - M1b eval_end dates are MCCC 2025-07 and CPU 2025-10. The zeroed-month counts match the ledger note.
  - Reproduction diffs: 9.7e-17 (M5) and 8.3e-17 (M1b).
- **Romano-Wolf and SPA, same draw order and seed.** My own implementation gives:
  - adjusted p identical to M7's (largest difference 1.1e-16);
  - SPA p 0.0086 and 0.1496;
  - max-t 95th percentiles 2.677 and 2.781;
  - the same 15 S-full survivors: 11 X paths from X_unc to X_b-1.50, plus epa8, epa_nomargin5, epa_anylink5 and epa_median8.
  - Nyholt 42.38 / 74.82, Li-Ji 14 / 27, Sidak 116.0 / 4.8.
- **Monte Carlo sensitivity** (my addition; the spec leaves the draw order free):

| Bootstrap | S-full RW p, book | S-full RW p, EPA 5v5 | S-full survivors | S-post RW p, book | S-post RW p, EPA 5v5 |
|---|---|---|---|---|---|
| M7 order, seed 20260926 | 0.0166 | 0.0580 | 15 | 0.1994 | 0.5577 |
| draw-by-draw order, same seed | 0.0104 | 0.0506 | 15 | 0.2094 | 0.5649 |
| M7 order, seed 12345 | 0.0170 | 0.0524 | 15 | 0.2036 | 0.5503 |

  - The book's pass over 1970-2026 and its fail over 2010-2026 are robust.
  - The EPA 5v5 S-full fail is narrow, 0.051 to 0.058 across the three bootstraps, and epa_anylink5 survives at 0.048.
  - Neither changes a verdict, because the EPA spread fails (a) and (c) anyway. An optional one-line note is suggested in section 8.

## 5. Deflated appraisal ratio (check 5): confirmed with my own implementation

My implementation:

- E[max_N] = (1 - gamma) Phi^-1(1 - 1/N) + gamma Phi^-1(1 - 1/(N e));
- SR0 = sqrt(V) E[max_N];
- z = (AR - SR0) sqrt(T - 1) / sqrt(1 - g3 AR + (g4 - 1)/4 AR^2);
- governing DSR = min(Phi(z), Phi(z t_NW / t_OLS)).

Nyholt, Li-Ji and the average-linkage clustering (K = round(N_eff), with 42 and 75 clusters formed) were computed from my own FF5+UMD residuals:

- S-full: V_cl 0.00246, floor 0.00147, E_N 2.212, annualized SR0 0.380.
- S-post: V_cl 0.00583, floor 0.00505, E_N 2.427, annualized SR0 0.642.

| Candidate, window | AR | Governing DSR (mine) | Li-Ji | Raw M | V floor | Li-Ji + V floor | PSR(0) | Largest passing N | Raw-Sharpe DSR |
|---|---|---|---|---|---|---|---|---|---|
| Book 1970-2026 | 0.400 | 0.559 | 0.776 | 0.497 | 0.786 | 0.897 | 0.999 | 3 | 0.859 |
| EPA 5v5 1970-2026 | 0.376 | 0.488 | 0.709 | 0.427 | 0.720 | 0.849 | 0.996 | 2 | 0.062 |
| Book 2010-2026 | 0.557 | 0.362 | 0.533 | 0.336 | 0.433 | 0.593 | 0.989 | 2 | 0.505 |
| EPA 5v5 2010-2026 | 0.410 | 0.171 | 0.302 | 0.155 | 0.222 | 0.357 | 0.945 | 0 | 0.238 |

- Every DSR, sensitivity and context value (Lo-adjusted Sharpe 0.553, 0.632, 0.181, 0.418) matches `M7_dsr.csv` within 3.1e-13.
- Both candidates fail the 0.95 bar in both windows under every sensitivity. The most lenient value is 0.897.
- The claim that Nyholt counts block structure generously, while Li-Ji leaves the verdict unchanged, is supported: all Li-Ji values are 0.776 or lower.

## 6. Checks 6 to 9: confirmed

- **Holdout (check 6).**
  - All 16 rows (10 FF5+UMD and 6 FF3) reproduce: alpha, interval, delta, MDE80 and reading.
  - All six team rules and Always-short Brown read "rejects". The book, EW book and EPA spread read "inconclusive".
  - The FF3 team alphas equal the fact-check's `holdout_tost.csv` within 0.001 percentage points (Original 3m -4.034% in both).
  - One rounding error: see R5.
- **Cost stress (check 8).** All 12 alphas and t-statistics reproduce. Break-even is 84 bp and 117 bp, the holdout gross alpha is negative, and turnover is 2.92. The pass at 25 bp (1.73%, t 2.43) is confirmed.
- **Frozen run (check 7), from the saved returns with my own NW.**
  - Main regression: 462 months (1931-07 to 1969-12), alpha 1.953%, SE 0.798%, t 2.4478, one-sided p 0.00737 on 457 df.
  - Halves: 231 months each, 1.71% (t 1.44) and 0.90% (t 0.83).
  - 90% interval 0.64% to 3.27%; delta 1.28% (residual vol 5.14%).
  - UMD beta 0.229 (t 12.12), market beta 0.030, R2 0.415, AR 0.380.
  - S1 3.26% (SE 1.85%, t 1.76); S3 -11.2% (1932-07), -21.6% (ending 1932-09), -30.2% (trough 1939-09); S4 1.55% (t 1.94).
  - 34 to 39 eligible industries, ex-ante TE 5.000% in every month, 0 fallbacks, 0 inaccurate months.
  - M5's post-1970 X_b-1.00 path has 0 fallback months. `optimizer.py` documents the minimum-carbon fallback.
  - The PASS follows the pre-registered rule.
  - Process: the dry-run diffs are 9.2e-17 and 2.3e-5; `first_run_record.json` has mtime 08:53:41 PDT, after the 08:49:39 pre-registration; and `preregister()` asserts that no pre-1970 return file exists at first write.
- **Check 9.**
  - Post-1970 crash profile: -12.8% (2009-04), -17.5% for March to May 2009, maximum drawdown -24.1% (trough 2010-01).
  - The EPA shock-control rows match the spec and fact-check: 4.87% / 1.52, 6.66% / 2.13, loading -0.52% per s.d. (t -2.21), and so on.
  - Provenance rows are correct, including the extra 2022-07 vintage difference.

## 7. What I could not verify

- The development-run history, and the statement that `book_path` and `frozen_stats` are unchanged since run.py was first written. There is no version control. The reproduced SHA-256 of the frozen net returns shows only that the current code gives the first-run numbers.
- The on-disk spec hash. Once the orchestrator saves `adopted_checks.md`, `run.py` should be run once more so that the hash is verified against the file itself. The simulation in section 1 says it will pass.

## 8. Required fixes

**R1. Overreach (section 2).**

- Replace: "The check 7 test is the only test in the project that survives a project-level correction."
- With: "Among the confirmatory families P and F, the check 7 test is the only survivor. The search families answer a different question: 15 S-full members, the book among them, survive Romano-Wolf over 1970-2026, and none survives over 2010-2026 (section 4)."
- Why: section 4's own table has 15 Romano-Wolf survivors over 1970-2026, including the book at 0.017.

**R2. Overreach against M1b's verified reading (section 3).**

- Replace: "It is the known small-sample COVID artefact that M1b's placebo work already covers. It is not evidence for a climate signal."
- With: "It is the level-transform twin of the CPU Original 3m COVID result that M1b already analyses (the log1p version earns 6.44%, t 4.46, over the same 24 months). M1b finds that CPU Original 3m's paired edge over the signal-free always-short position is +1.90% (t 1.02), so this window does not separate a climate trigger from being short the Brown residual in 2020-21."
- Why: M1b's verifier removed exactly this kind of "not climate evidence" phrasing (M1b FINDINGS, issue B). M1b calls the shared December 2019 CPU crossing "the one result in this module consistent with a climate trigger".

**R3. Wrong window dates (section 3).**

- Replace: "Losses appear in every window after 2022-07: holdout, the 2022-2024 rates window, the last 18 months and the last 12 months."
- With: "Losses appear in every window that starts in 2022 or later: the rates window (2022-01 to 2024-12, which overlaps the last seven validation months), the holdout (2022-08 to 2026-07), the last 18 months and the last 12 months."
- Why: `lib/common.py` defines inflation_rates as 2022-01-31 to 2024-12-31.

**R4. Wrong claim about the book's history (section 7, caveat 3).**

- Replace: "The second-half alpha is about half the first-half alpha (0.90% against 1.71%). The decay visible after 2010 has an earlier echo."
- With: "The second-half alpha is about half the first-half alpha (0.90% against 1.71%), although the difference is far from significant (t about 0.5, treating the halves as independent). After 1970 the alpha did not decay after 2010 (FF5+UMD alpha 1.99%, t 2.31, over 1970-2009; 3.12%, t 2.18, over 2010-2026); it disappeared in the 2022-2026 holdout (-0.34%)."
- Why: the post-2010 alpha is larger than the full-sample 2.17%. The decay is the validation-to-holdout drop, which the verdict table already names correctly.

**R5. Rounding (section 6 table, Team Original 6m row).**

- Replace "-5.85% to -0.52%" with "-5.85% to -0.51%".
- Why: `ci90_hi` = -0.00515 (-0.514968%), and `M7_holdout_reading.tex` prints -0.51.

**R6. Factor-source mismatch (section 7, caveat 2).**

- Replace: "For comparison, the post-1970 FF3+UMD alpha is 2.01% (t 2.84)."
- With: "For comparison, the post-1970 FF3+UMD alpha with the same factor files as the frozen test (`load_kf_ff3` plus UMD) is 2.02% (t 2.86); the fact-check's 2.01% (t 2.84) used the Mkt-RF, SMB and HML columns of the FF5 file."
- Also add a ledger row (see R10).
- Why: I reproduced 2.010% (t 2.840) only with the FF5-file factors. The KF3 file gives 2.024% (t 2.859).

**R7. Incomplete statement (section 5).**

- Replace: "The book passes at the step-3 V only for N of 3 or fewer."
- With: "The book passes at the step-3 V only for N of 3 or fewer over 1970-2026, and 2 or fewer over 2010-2026."

**R8. Ledger description (section 11, item 7).**

- Replace: "Context-only rows among them carry "[context: descriptive]" in the note."
- With: "Context-only rows among them carry "[context: descriptive]" (29 rows) or "[context: exploratory]" (1 row, the not-adopted all-primaries family) in the note."

**R9. Internal tension (bottom line).**

- Replace: "Correcting for multiple testing across the whole project leaves no labelled primary alpha standing."
- With: "Correcting for multiple testing across the whole project leaves none of the modules' labelled primary alphas standing."
- Why: M7's own labelled primary, check 7 (i), survives Holm in family F two paragraphs later.

**R10. Spec G7 ("Every number M7 quotes has a row"): code fix, output-only.** These quoted numbers have no row in `M7_robustness_tests_ledger.csv`:

- the share of positive t-statistics for the R subfamilies other than R-M2: 40.8%, 25.0%, 59.2%, 0%, 43.0% and 52.7%;
- the governing DSR at "N = Li-Ji, V = 1/(T-1)" (0.897, 0.849, 0.593, 0.357) and at "N = raw M, V = 1/(T-1)";
- the largest passing N (3, 2, 2, 0);
- the post-1970 FF3+UMD comparison alpha (R6).

Add `led()` rows in checks 3, 5 and 7. They are in `M7_family_R_summary.csv` and `M7_dsr.csv` but not in the ledger. After the change, the rerun must still show `reproduces_first_run` True.

**Optional, not blocking.**

- Section 4 could add: "The EPA 5v5 full-sample fail is narrow: its adjusted p is 0.051 to 0.058 across three bootstrap draw orders in verification."
- The run time is about 45 to 47 seconds, not 41.
