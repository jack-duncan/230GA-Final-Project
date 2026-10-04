# M7 robustness ledger: adversarial verification, round 2

Verifier run on 2026-09-26, 18:13 to 18:30 UTC. This round covers the FINDINGS version that adds the section 0 note on the spec hash, the survivor list at the end of section 4 and the section "Rerun after the spec was saved". It also rechecks everything else.

Scope:

- rerun `run.py`;
- recompute on my own the ledger aggregation counts, the Holm, BH and BY survivors in every family, the Romano-Wolf survivors and the deflated appraisal ratio of each candidate from the Bailey and Lopez de Prado (2014) formula;
- check the family definitions against `exchange/03_robustness_design/adopted_checks.md`, which is now on disk;
- flag any conclusion that overreaches.

**Verdict.** Every number in FINDINGS reproduces. My independent code agrees with M7 to between 1e-16 and 5e-14. The family map matches the adopted spec rule for rule. The three final verdicts are confirmed:

- the optimizer book: paper-trade at pilot size, and the report verdict stays "Do not implement";
- the EPA 5v5 spread: "Do not implement";
- the attention thesis: "Do not implement".

For the first time, the pre-registration record is verified against the builder's own transcript (section 7 below). All ten round-1 fixes (R1 to R10) are in the text and the ledger.

Two sentences are still slightly wrong (R11, R12). Both are one-sentence text fixes. Neither touches a number, a pass bar or a verdict. `all_confirmed` = false until they are applied.

## 1. What I ran

- **Rerun.** `uv run python modules/M7_robustness_ledger/run.py`, 41.3 s wall time, exit 0.
  - All three pre-registration hashes verified. `source_this_run` = `file exchange/03_robustness_design/adopted_checks.md`.
  - Dry-run differences: 9.22e-17 with M5's inputs and 2.31e-5 with the FF3 inputs.
  - The frozen run gives alpha 0.0195, t 2.448, one-sided p 0.0074, halves 0.0171 and 0.0090, PASS. `reproduces_first_run` is True, and `first_run_record.json` is byte-identical (first_run_utc 15:53:41 UTC).
  - Against a snapshot of the 18:09 UTC outputs:
    - 38 of the 39 M7 tables are byte-identical;
    - `M7_preregistration_hash.csv` differs only in `this_run_utc`;
    - the three PNG figures are byte-identical;
    - the three PDF figures differ only in `/CreationDate`.
  - Ledger 481 rows; `M7_all_tests.csv` 24,404 rows; verdicts unchanged.
- **Hashes.** An independent `sha256sum` of adopted_checks.md, optimizer.py and m5lib.py gives the three pre-registered values.
  - The saved adopted_checks.md is byte-identical to the journal copy with a final newline, which is what `lib/save_returned_files.py` writes.
  - optimizer.py and m5lib.py were last modified at 09:55 and 10:31 UTC, before the 15:49:39 UTC pre-registration.
- **New verification scripts** (in `modules/M7_robustness_ledger/verify/`; logs in `verify/out_r2/`; 49 checks, 0 failures):
  - `r2_census_mt.py` reads the eight module ledgers with Python's `csv` module and classifies each row in a plain loop with `re`, per spec check 1. Holm, BH and BY are hand-written loops, cross-checked against `statsmodels.multipletests`. The script also audits the M7 ledger against rule G7 and `M7_all_tests.csv`.
  - `r2_search_dsr.py` handles checks 4 to 8 and 10.
    - Search members are rebuilt from the saved module tables and the modules' library calls, with the arguments taken from M5's and M1b's own `run.py`, not from M7.
    - Everything statistical is my own numpy code, including my own Ken French parser, checked against `lib/common`.
    - That code covers OLS by QR, Newey-West, bias-corrected skew and kurtosis, and the stationary bootstrap in two draw orders.
    - It also covers Romano-Wolf as an explicit stepdown loop, the consistent SPA, Nyholt and Li-Ji, the cluster V and the DSR.
  - `r2_holdout_ss.py` is a small-sample sensitivity of the check 6 readings (not in the spec).
- **Process audit.** I read the M7 builder's transcript (`subagents/workflows/wf_c1f5d333-469/agent-aa2b4cbf1c426bd97.jsonl`) and diffed today's `run.py` against the file as first written at 15:49:05 UTC (section 7).
- **LaTeX.** All 10 `M7_*.tex` tables compile with tectonic and `report/preamble.tex`. The only messages are cosmetic: a 1 pt overfull box in the census table and underfull boxes in the verdict table's p-columns.
- **Figures.** I checked all three visually. The critical values, RW labels, window shares and the frozen-run title match the tables.

## 2. Family definitions against the adopted spec: confirmed

- **Type rules.** The regex order in `run.py` is beta-timing, then `loading|t_b_|t_NW6_b_` or the `[loading]` note tag, then alpha, mean and other. This is the spec's order.
- **Family rules.** First match wins, in the order F, P, D, X, L, R, E. The rules are exactly the spec's:
  - F: `M8_share_i_alpha_nw6`;
  - P: primary, alpha type, not M8;
  - D: other primaries;
  - X: placebo or reference;
  - L: loading or beta-timing;
  - R: M2 `|alpha` rows plus other modules' robustness alpha rows;
  - E: everything else.
- **Other checks.** Family F, the P dedup key, R's split into subfamilies, the search-family membership and exclusions, G2, G5, G6, the RW and SPA formulas, check 5 steps 1 to 7, the check 6 reading order, the check 7 frozen specification and the check 10 map all match the spec text.
- **One wording point, not an error.** The spec gives BY's divisor as 9.58 at m = 8,091 (M2's own grid). M7 runs R-M2 at the family rule's m = 8,161, with divisor 9.584. The spec itself says the difference changes no survivor count.

## 3. Census and M7 ledger aggregation (check 1, G7): confirmed

| Item | FINDINGS | Independent | Match |
|---|---|---|---|
| Ledger rows, exact duplicates | 23,923, 0 | 23,923, 0 | yes |
| F / P / D / X / L / R / E | 1 / 81 / 73 / 170 / 4,850 / 9,337 / 9,411 | same; family-by-module table 0 cell differences | yes |
| P by module | M1b 24, M2 42, M3 12, M4 1, M5 2 | same | yes |
| D by module | M1 15, M1b 16, M2 4, M3 21, M5 2, M6 8, M8 7 | same | yes |
| R-M2 / R-other | 8,161 / 1,176 (M1b 736, M4 282, M3 156, M6 2) | same | yes |
| Label by module, all 40 cells and totals | as in the section 1 table | same | yes |
| Nominal p2 < 0.05 | 4,184: alpha 1,624 (783+, 841-), loading 1,325, mean 561, other 536, beta-timing 138 | same; loading share 31.7%, alpha 38.8% | yes |
| Nominal D / X / L / E | 15 / 33 / 1,452 / 1,636 | same | yes |
| M7 ledger | 481 rows: 1 primary, 387 robustness, 86 descriptive, 7 exploratory; 33 "[context: descriptive]", 1 "[context: exploratory]" | same; the exploratory tag is `M7_C2_allprimaries_holm_survivors` | yes |
| G7 labels | only check 7 (i) primary; checks 2 to 8 otherwise robustness; checks 1 and 9 descriptive or exploratory | same | yes |
| `M7_all_tests.csv` | 24,404 = 23,923 + 481 | same. The module rows keep order, test_id, label, family and type; statistic and p are equal to parser precision (5.7e-14) | yes |

In `M7_all_tests.csv`, `p1_m7` is filled for all 81 P rows, all 9,337 R rows and M8's F row. It is empty for the check 7 (i) row (see R11).

## 4. Multiple testing (checks 2 and 3): confirmed

- **Family P.**
  - 81 rows collapse to 73: 6 M2 and 2 M3 Original/Pure holdout pairs, as listed in the log.
  - Smallest adjusted p: Holm 1.0000, BH 0.7181, BY 1.0000. No survivors.
  - Best one-sided p 0.02991 (`strat|L5|corr|FF3|u5|Pure 6m|post2010|E:FF3|alpha`, t 1.893); Sidak count 1.689.
  - The largest difference from `M7_family_P.csv` is 2.2e-16. The statsmodels cross-check agrees to 1.1e-16.
- **Family F.** One-sided p 0.6048 (M8, t -0.266) and 0.00737 (check 7 (i), t 2.448). Holm gives 0.6048 and 0.01475, so only check 7 (i) survives.
- **All 155 primaries** (not adopted, two-sided). 154 have a p-value; `M8_share_iii_episodes` has none.
  - Holm has 4 survivors and BY has the same 4: M1 `Q3_fisher_zero_pre_post`, M1 `Q2_joint_team_signal_z_full`, and M2's FF3 `b_HML` spread loadings in post2010 and full_1970.
  - BH adds M2 `spread|L5|post2010|E:FF5U|b_HML` (loading) and M3 `Q3b.ln_timing.Pure 3m|...|post2010` (beta-timing).
  - None is alpha-type. This matches the section 2 text and the section 4 survivor table exactly.
- **Family R.** Every cell of the section 3 table reproduces: m, share positive, smallest one-sided p, smallest BH and BY p, survivors and best test. The largest difference is below 1e-12, and the BY divisors are 9.584 and 9.719.
  - The single BH survivor is `CPU_realtime_none_O3_covid_alpha`: t 4.717, alpha 6.83%, n 24, window 2020-01 to 2021-12.
  - The M1b figures that R2 introduced are in the M1b ledger: `CPU_realtime_log1p_O3_covid_alpha` t 4.463 (alpha 6.44%), and `COVIDB_realtime_CPU_O3_minus_always_short_covid` t 1.017 (difference 1.90%).
- **R-M2 by window.** Every row of both column groups reproduces: 153 spread rows and 8,008 strategy rows.
  - Validation: 88.9%, median 1.142 on all rows; 88.9%, median 1.148 on strategy rows.
  - Holdout: 2.7%, median -1.316 on all rows; 2.3%, median -1.339 on strategy rows.
  - last18: 0%, median -2.35.
  - full_1970: 21 spread rows, 100% positive, median 1.453.
  - The window dates in `lib/common.py` match the section 3 text: covid 2020-01 to 2021-12, inflation_rates 2022-01 to 2024-12, last18 2025-02 on, last12 2025-08 on.

## 5. Search families (check 4): confirmed

- **Members.**
  - S-full is 679 x 58 and S-post 199 x 89, with no missing month.
  - My EW-variant and screen lists equal the non-primary rows of M5's tables. The 18 regenerations reproduce Sharpe and alpha to 1.8e-16, and the 12 M1b rules reproduce their t to 8.3e-17.
  - M1b eval_end is MCCC 2025-07 and CPU 2025-10. The months zeroed are 2 each for MCCC O6, P6, CR and CP and for CPU P3, CR and CP, and 5 for CPU P6, as stated.
- **Member fits.** My NW t and alpha equal `M7_search_members.csv` for all 147 member-family pairs, to 4.7e-14 in t and 1.3e-15 in alpha.
- **Romano-Wolf and SPA** (my code, M7's documented draw order, seed 20260926).
  - Adjusted p equals M7's for every member (largest difference 1.1e-16).
  - SPA p is 0.0086 and 0.1496. The 95th percentiles of max-t are 2.677 and 2.781.
  - Nyholt 42.38 / 74.82; Li-Ji 14 / 27; Sidak counts 116.0 / 4.8.
- **Survivor list** (new in section 4). All 15 S-full adjusted p-values reproduce to four decimals:
  - X_b-1.00 and X_b-0.75 0.0088; X_b-0.50 0.0090; X_b-0.25 0.0092;
  - X_b-1.25 and epa_nomargin5 0.0106; X_b+0.00 0.0120;
  - X_b+0.25 and epa8 0.0142; X_b+0.50 0.0150;
  - X_unc 0.0166; X_b+1.00 0.0168; X_b-1.50 0.0202;
  - epa_median8 0.0350; epa_anylink5 0.0478.
- **Details of the survivor list.**
  - X_b-2.00 (0.197) and all 12 M paths (smallest 0.131) fail.
  - The EPA survivors' t are 3.228, 3.126, 2.761 and 2.665. The last prints as 2.66 because it is 2.6646.
  - Each adjusted p sits in its `M7_C4_<family>_<member>` ledger note.
  - S-post has no survivor; its best adjusted p is 0.1496.
- **Book and EPA 5v5.**

| | 1970-2026 | 2010-2026 |
|---|---|---|
| Book | 2.17%, t 3.07, RW 0.0166 | 3.12%, t 2.18, RW 0.1994 |
| EPA 5v5 | 4.54%, t 2.58, RW 0.0580 | 4.72%, t 1.52, RW 0.5577 |

- **Monte Carlo sensitivity** (not in FINDINGS; the spec leaves the draw order free).

| Bootstrap | S-full book | S-full EPA 5v5 | S-full survivors | S-post book | S-post EPA 5v5 |
|---|---|---|---|---|---|
| M7 order, seed 20260926 | 0.0166 | 0.0580 | 15 | 0.1994 | 0.5577 |
| Draw-by-draw order, same seed | 0.0104 | 0.0506 | 15 | 0.2094 | 0.5649 |
| M7 order, seed 777 | 0.0146 | 0.0546 | 15 | 0.2048 | 0.5561 |

Every reading holds. The EPA 5v5 full-sample fail is narrow (0.051 to 0.058), but the spread fails (a) and (c) anyway.

## 6. Deflated appraisal ratio (check 5): confirmed with my own implementation

My implementation, written from the Bailey and Lopez de Prado formula:

- E[max_N] = (1 - g) Phi^-1(1 - 1/N) + g Phi^-1(1 - 1/(N e)), with g = 0.5772156649;
- SR0 = sqrt(V) E[max_N];
- z = (AR - SR0) sqrt(T - 1) / sqrt(1 - g3 AR + (g4 - 1)/4 AR^2);
- governing DSR = min(Phi(z), Phi(z t_NW / t_OLS)).

The inputs come from my own residuals: Nyholt with ddof 1, Li-Ji, average linkage on sqrt(0.5(1 - rho)) with K = round(N), and the cluster ARs from my own OLS.

| Family | Nyholt | Li-Ji | K (clusters formed) | V_cl | Floor | E_N | SR0 annual |
|---|---|---|---|---|---|---|---|
| S-full | 42.383 | 14.000 | 42 (42) | 0.00246 | 0.00147 | 2.2122 | 0.380 |
| S-post | 74.816 | 27.000 | 75 (75) | 0.00583 | 0.00505 | 2.4268 | 0.642 |

| Candidate, window | AR | DSR iid / NW | Governing | Li-Ji | Raw M | V floor | Li-Ji + floor | Raw M + floor | PSR(0) | Max N | Raw SR / Lo SR / raw DSR |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Book 1970-2026 | 0.400 | 0.559 / 0.563 | 0.559 | 0.776 | 0.497 | 0.786 | 0.897 | 0.749 | 0.999 | 3 | 0.555 / 0.553 / 0.859 |
| EPA 5v5 1970-2026 | 0.376 | 0.488 / 0.488 | 0.488 | 0.709 | 0.427 | 0.720 | 0.849 | 0.680 | 0.996 | 2 | 0.199 / 0.181 / 0.062 |
| Book 2010-2026 | 0.557 | 0.363 / 0.362 | 0.362 | 0.533 | 0.336 | 0.433 | 0.593 | 0.408 | 0.989 | 2 | 0.696 / 0.632 / 0.505 |
| EPA 5v5 2010-2026 | 0.410 | 0.171 / 0.182 | 0.171 | 0.302 | 0.155 | 0.222 | 0.357 | 0.203 | 0.945 | 0 | 0.520 / 0.418 / 0.238 |

- Every value matches `M7_dsr.csv` to 8.0e-15, including t_NW / t_OLS, residual skew and kurtosis, and all five sensitivities.
- Both candidates fail 0.95 in both windows under every sensitivity. The most lenient value is 0.897. The largest passing N (3, 2, 2, 0) is confirmed.
- **Formula check (my addition).** The closed-form E[max_N] slightly overstates the simulated mean maximum of N iid normals: 2.212 against 2.183 at N = 42.38, and 2.427 against 2.401 at N = 74.82. With the simulated values, the governing DSR would be 0.574, 0.503, 0.372 and 0.178, so the spec's formula is mildly conservative and no verdict moves.

## 7. Pre-registration process (check 7, step 0): now verified from the transcript

Round 1 could not verify the development-run history. The builder's transcript settles it (times in UTC):

| Time | Event |
|---|---|
| 15:36 to 15:44 | Exploration. The only optimizer call (`explore4.py`, 15:42:30) used formation months 1969-12 to 1970-11, the dry-run window, with returns in 1970. No pre-1970 strategy return. |
| 15:49:05 | `run.py` first written. |
| 15:49:31, 15:49:34 | Edits before the hash: verdict-table text and the `M7_SKIP_FROZEN` branch, which runs `frozen_stats` on formation months 1969-12 to 2008-05. |
| 15:49:38 | Development run 1 with `M7_SKIP_FROZEN=1`; hashes written 15:49:39. |
| 15:51:18 | Edit: NaN-safe Holm, BH and BY; shock loading per s.d. |
| 15:51:27 | Edit: ledger note; development run 2 with `M7_SKIP_FROZEN=1`. |
| 15:52:47 | Edit: figure layout and verdict-table text (placement of the pre-1970 result). |
| 15:53:01 | Frozen run; `first_run_record.json` written 15:53:41. |

- This matches section 0: two development runs, on post-1970 formation months only. The changes between the hash and the frozen run are exactly NaN handling, a ledger note, the shock loading per s.d., figure layout and verdict text.
- `book_path`, `realized_ic`, `frozen_stats`, `fit`, `preregister`/`spec_bytes` and the FF3+UMD factor frame in today's `run.py` are byte-identical to the 15:49:05 first write. The only difference in the dry-run and frozen-call block is the development branch added at 15:49:34, before the hash.
- So "`book_path` and `frozen_stats` are unchanged since run.py was first written" is confirmed, and no post-frozen edit touched a check 7 computation.
- The exchange-3 fact-check that preceded the spec (`checks/fc03_checks.py`, outputs at 15:04 UTC) computed only pre-1970 availability counts and a power table from post-1970 moments. The window was therefore unseen for this book when the spec was hashed.

## 8. Checks 6 to 10: confirmed

- **Holdout (check 6).** All 16 rows reproduce with my NW: 10 on FF5+UMD and 6 on FF3. That covers alpha, the 90% interval, delta and MDE80 (largest difference 8.1e-16), and every reading.
  - The six team rules and Always-short Brown read "rejects"; the book, EW book and EPA spread read "inconclusive".
  - Under FF3, Original 6m's upper bound is +0.03% against a delta of 1.12%.
- **Cost stress (check 8).** All 12 alphas and t-statistics reproduce (2.0e-14). Break-even is 84 bp and 117 bp; the holdout gross alpha is -0.04%; turnover is 2.92. The pass at 25 bp (1.73%, t 2.43) is confirmed.
- **Frozen run (check 7)**, from the saved returns with my own NW and factor parse:
  - main regression: 462 months, alpha 1.953%, SE 0.798%, t 2.4478, one-sided p 0.00737 on 457 df;
  - halves: 1.71% (t 1.44) and 0.90% (t 0.83), 231 months each;
  - 90% interval 0.64% to 3.27%; delta 1.28% (residual vol 5.14%);
  - UMD beta 0.229 (t 12.12), market beta 0.030, R2 0.415, AR 0.380;
  - net return 3.42%, volatility 6.69%, turnover 2.68;
  - 34 to 39 eligible industries; ex-ante TE 5.000% every month; 0 fallbacks and 0 inaccurate months;
  - S1 3.26% (SE 1.85%, t 1.76); S2 -0.006 [-0.194, 0.228], p 0.957; alpha difference -0.04% [-1.38%, 1.36%]; binding 77.9%; 38 fallback months;
  - S3 -11.2% (1932-07), -21.6% (ending 1932-09), -30.2% (trough 1939-09); S4 1.55% (t 1.94); S5 IC 0.080, t 6.78 and 2.57;
  - M5's post-1970 X_b-1.00 path has 0 fallbacks;
  - caveat numbers: halves-difference t 0.501; post-1970 FF3+UMD 2.024% (t 2.859) with the KF3 files and 2.010% (t 2.840) with the FF5-file factors; FF5+UMD 1970-2009 1.987% (t 2.308, 480 months).
  - Family F Holm 0.0147. The PASS follows the pre-registered rule.
- **Check 9.**
  - Post-1970 crash rows: -12.8% (2009-04), -17.5% for March to May 2009 (also the worst three months), maximum drawdown -24.1% (trough 2010-01).
  - All seven EPA shock-control rows match (for example 4.87% / 1.52, and 6.66% / 2.13 with a loading of -0.52% per s.d., t -2.21). The Pastor-Stambaugh-Taylor direction statement is correct: green minus brown lost when concern rose.
  - Provenance rows are correct, including the extra 2022-07 vintage difference.
  - M4 describes the EPA factors as 2022-vintage, which supports "2022 intensities applied back to 1970" in the verdict table.
- **Check 10.** My own inputs give the same map:
  - the book: (a) yes, (b) no (0.0166 / 0.1994), (c) no (0.559 / 0.362), (d) no (-0.34%, inconclusive), so paper-trade;
  - EPA 5v5: (a) no, so "Do not implement";
  - the attention thesis: M8 FAIL, family P Holm 1.00 (BH 0.72), 6 of 6 rules reject, so "Do not implement".

## 9. Rerun section and new section 0 text

- **Confirmed:**
  - the spec was saved at 17:43:33 UTC;
  - the 18:09:03 UTC run hashed the file itself, and `source_this_run` reads `file exchange/03_robustness_design/adopted_checks.md`, while `source` keeps the journal origin;
  - between 16:15 and 18:09 UTC, no module ledger, saved return series, lib file, `data/` file or `exchange/03_robustness_design/checks/out/` file changed;
  - the check 7 figures, and the table, figure and ledger counts, are as stated;
  - every number in the section 4 survivor list is in the M7 ledger.
- **Not reproducible by me:** the 41.8 s wall time of that run (mine: 41.3 s), and the comparison against that run's own pre-run snapshot. My rerun shows the same pattern against the 18:09 outputs.
- **Wrong:** one sentence about `modules/` (R12).

## 10. Overreach review

- **No conclusion overreaches the evidence.**
  - The bottom line is scoped to the modules' labelled primaries.
  - "Survives the search as nonzero, not bankable after selection" follows the spec's fixed rule.
  - The PASS is read only as "the edge was there before 1970", with the four caveats.
  - Every verdict follows the pre-registered map.
- **Two readings are softer than they sound** (optional notes N1 and N2 below):
  - "including both continuous rules" rests on the spec's NW(6) standard errors;
  - the frozen PASS rests on a 10 bp cost that is low for 1931-1969.

## 11. Required fixes

**R11. Column description (section 1, `M7_all_tests.csv` bullet list).**

- Replace: "`p1_m7`, the one-sided p that M7 used for families P, R and F."
- With: "`p1_m7`, the one-sided p that M7 used for families P and R and for M8's row in family F. The check 7 (i) row leaves `p1_m7` empty and carries its one-sided p (0.0074) in `p_value_one_sided`."
- Why: in `M7_all_tests.csv`, `p1_m7` is NaN for `M7_C7_i_alpha_ff3umd`. The mask in `run.py` covers only families P and R and `M8_share_i_alpha_nw6`.
- Alternative: fill that cell in code. This changes only `M7_all_tests.csv`, and the rerun must still show `reproduces_first_run` True.

**R12. Incomplete statement (section "Rerun after the spec was saved", bullet "Inputs unchanged").**

- Replace: "The only newer files under `modules/` are other modules' FINDINGS.md text."
- With: "The only newer files under `modules/` are Markdown text the orchestrator saved at 17:43 UTC: the FINDINGS.md of M1, M1b, M2, M5 and M8, and M7's own FINDINGS.md and VERIFY.md."
- Why: `modules/M7_robustness_ledger/FINDINGS.md` and `VERIFY.md` also carry the 17:43:33 UTC timestamp. Neither is an input, so the conclusion stands.

## 12. Optional notes (not blocking)

- **N1 (section 6, reading).** Under the spec's NW(6), all six team rules reject. The alternatives:
  - With classic OLS standard errors, Continuous pure reads inconclusive: upper bound +0.35% against a delta of 0.27%.
  - Also with OLS standard errors, the four hold rules and Continuous raw still reject.
  - With NW(6) scaled by n/(n-k), or with NW(3), all six reject.
  - Always-short Brown turns inconclusive under OLS and NW(3).
  - Suggested addition to "all six rules reject, including both continuous rules": "; the four hold rules also reject with OLS or small-sample-scaled standard errors, while Continuous pure becomes inconclusive with OLS standard errors."
  - If quoted, these numbers need ledger rows (G7). They are in `verify/out_r2/r2_holdout_small_sample.csv`.
- **N2 (section 7, caveats).** The PASS is at 10 bp. At 25 bp (S4, already in the ledger) the alpha is 1.55% with t 1.94, below the pass bar's 2.00.
  - Verification also finds that t falls below 2.00 from about 23.5 bp, and that the frozen book's break-even cost is 83 bp.
  - A fifth caveat could say that 10 bp is a modern cost level. Any new number needs a ledger row.
- **N3 (section 4).** The EPA 5v5 full-sample Romano-Wolf fail is narrow: 0.051 to 0.058 across three bootstrap draws (section 5 above).
- **N4 (section 5).** The closed-form E[max_N] is mildly conservative against simulation, and the governing DSR would rise by at most 0.015 (section 6 above). No text change is needed.
