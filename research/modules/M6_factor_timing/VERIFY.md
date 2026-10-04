# M6_factor_timing: adversarial verification

Verifier script: `modules/M6_factor_timing/verify/verify_m6.py`. It does not import `run.py` or `m6lib.py`. It uses only the `lib/common.py` raw-data loaders and rebuilds GB, the predictors, the walk-forward ridge with time-series CV, the Clark-West tests, the timing portfolios (industry turnover and costs), the FF5+UMD regressions, 12-1 industry momentum, and the LMN variant from scratch. Results are in `verify/verify_results.json`.
Run: `cd /home/hashim/projects/GA/project/research && uv run python modules/M6_factor_timing/verify/verify_m6.py` (about 30 s). The module itself (`run.py`) runs cleanly: exit 0 in 29 s, 174 ledger rows.

**Status of FINDINGS.md: it is not on disk.** The builder's text exists only in its return message. I verified that text against the CSVs and against my own recomputation.

## Summary
All numbers I recomputed match to rounding: 40+ quantities, most to 4 or more decimals, with no numeric discrepancies beyond rounding. There is no look-ahead in any predictor. I checked the BE/ME timing directly against the data. The problems are in wording and interpretation:
- three overreaching statements (section 9.1, section 9.2, headline 5 "and CMA");
- one off-by-one date phrasing (headline 4);
- two caveats that are incomplete (risk concentration, and ex-post scaling in the difference test);
- ledger gaps.

## Look-ahead, timing, and conventions (all checked)
| Item | Finding |
|---|---|
| BE/ME timing | Confirmed safe. The change in log BE/ME from KF row Y-1 to row Y correlates -0.67 with industry returns in calendar year Y-1 and +0.02 with calendar year Y. So row Y uses December Y-1 market equity. Using it from end-July Y (first applied to the August Y return) is look-ahead free and one month more conservative than FF. The legs have no BE/ME that is ≤ 0 or missing since 1969. |
| Other predictors | MOM12 covers t-11..t. INFL and CFNAI are lagged one month; October 2025 CPI is missing and I handled it identically. TERM, CREDIT and DGS10 are monthly averages of month t. VIX is the month-end value. ATTN is contemporaneous (team convention), and the lagged robustness check is also degenerate. My independent rebuild reproduces all 10 predictor means and the 1990-sample in-sample slopes and t-stats to 4 decimals. For example, INFL is -0.315 with t -1.94. |
| WTI | The team `macro.wti` equals FRED MCOILWTICO exactly (max abs diff 0). |
| Training and target alignment | At origin t, training uses origins s < t, so the latest training target is the return of month t. Each CV fold is fit and standardized only on rows before its validation block. The historical mean is taken over the same rows and matches the module to 1e-16. GB matches to 1e-16. |
| Annualization, NW, sign | Returns are annualized as 12x the mean and volatility as sqrt(12)x the sd. Newey-West uses 6 lags with a Bartlett kernel. My own HAC code reproduces the statsmodels t-stats to 4 decimals. GB = Green - Brown, and w > 0 means long Green. |
| Costs | 10 bp per unit of industry-level turnover, measured against drifted weights. My own implementation reproduces the module's turnover: 0.930, 1.180, 0.604 and 0.614 per year. The first month's initial build is not charged, which is negligible. |
| Windows | n = 439 (1990-01 to 2026-07), 319 (2000-01 on), 199 (post-2010), and 151 (MCCC, 2013-01 to 2025-07), with no gaps. The first Spec B training window has 119 pairs and Spec A has 239. |

## Per-claim verdicts
| # | Claim (FINDINGS) | Module / CSV | Independent recomputation | Verdict |
|---|---|---|---|---|
| H1 | CV picks the max penalty in 439/439 (A) and 319/319 (B) refits; max gap 3e-8; R2_OOS 0.000% full and post-2010; Holm p = 1 | histmean_sign, oos_primary | 439/439 and 319/319 (B0 also 100%). Max gap 1.97e-8 (A) and 2.98e-8 (B). R2_OOS -1.2e-6% and 4.5e-7% | **Confirmed.** Nuance: the 100% depends on the CV design. If validation uses only the last 120 months, the max-penalty share is 86% (A) and 81% (B). With the last 60 months it is 80% and 52%. R2_OOS still ranges from -0.54% to +0.13%, with CW t ≤ 0.50, so the conclusion holds. |
| H2 | Fixed-penalty full-OOS R2 from -2.58 to -0.12% (A) and -7.77 to -0.02% (B); CV MSE 1.17x at OLS | oos_robustness, shrinkage_path | A: -2.581, -2.527, -2.150, -0.911, -0.123. B: -7.766, -7.364, -5.024, -0.990, -0.017. CV ratio at λ = 1e-4: 1.1701 (A) and 1.1494 (B); at λ = 10: 1.0039 and 1.0023 | **Confirmed** |
| H2 | LMN net Sharpe between -0.33 and 0.11 | lmn_variant | Own LMN code: A sign -0.332, A raw -0.178, B sign -0.098, B raw -0.079, B0 sign 0.110, B0 raw 0.034 | **Confirmed** |
| H3 | B vs B0 at fixed penalties: full -1.07 to -0.08%, post-2010 -1.55 to -0.01%, all CW t negative | oos_robustness | Full: -1.069, -1.040, -0.879, -0.474, -0.085. Post-2010: -1.554, -1.490, -1.082, -0.258, -0.015. CW t from -1.89 to -0.37 | **Confirmed.** "Exactly 0" for the ridge-CV increment should read "numerically 0" (the max forecast gap is 5e-9). |
| H3 | LMN: adding ATTN takes net Sharpe from 0.11 to -0.10 | lmn_variant | Reproduced. **Untested in the module.** My NW(6) test of the B minus B0 LMN net return: -1.04%/yr, t -2.38 (sign) and -0.57%/yr, t -2.00 (raw) | **Confirmed, and stronger than stated.** It should be added to the ledger as a robustness test. |
| H3 | MCCC best +0.32%, p 0.24 | oos_robustness | +0.322%, CW t 0.719, p 0.236 | **Confirmed** |
| H4 | Timing equals the prevailing-mean portfolio; last-12 net Sharpe 0.64 (A) and 0.99 (B) vs -1.37 static; timing minus static +0.84%/yr (t 1.17) and +0.66%/yr (t 0.45) | portfolio_perf, ledger | 0.643 / 0.992 / -1.373. Differences +0.837%/yr (t 1.170) and +0.660%/yr (t 0.450). Long share 83.4% and 29.2% | **Confirmed numbers. Discrepancy in wording:** "short GB since the historical mean turned negative (2022-04 / 2021-11)". Those are the **last target months with a positive mean**, so the portfolio is short from 2022-05 (A) and 2021-12 (B). Section 5 states this correctly. |
| H4 | "Sharpe, t-stats ... do not depend on this constant" | | True for each strategy on its own, but **not** for the timing-minus-static difference. If the static leg is scaled to the timing rule's mean \|w\| instead of equal ex-post volatility, the t-stats become 1.06 (A) and 0.17 (B). The conclusion is unchanged. | **Caveat missing** |
| H5 | Static GB at 5% vol is short RMW (-0.12, t -2.6 to -2.9), HML (-0.07 to -0.08, t -2.0 to -2.2) "and CMA" | portfolio_ff6_loadings | A window: RMW -0.124 (t -2.90), CMA -0.102 (t -2.05), HML -0.066 (t -1.99), SMB -0.055 (t -1.98), Mkt -0.031 (t -1.94). B window: RMW -0.122 (t -2.62), HML -0.081 (t -2.22), Mkt -0.050 (t -2.68), UMD -0.056 (t -2.47), **CMA -0.078 (t -1.48)** | **Numbers confirmed. Overreach:** CMA is significant only in the 1990 window. The headline also leaves out Mkt and UMD in the 2000 window, which are as strong as HML, and section 5 leaves out SMB in the A window. |
| H5 | Rotation ridge net Sharpe 0.32 vs 12-1 momentum 0.40; difference -1.98%/yr (t -1.07); ridge UMD beta 0.73 | rotation_perf, ledger | Momentum rebuilt independently: 7.46%/yr, vol 18.45%, Sharpe 0.404, t 2.37, post-2010 Sharpe 0.437, turnover 12.48x, alpha 1.65% (t 0.94), UMD beta 0.955 (t 27.3). It matches the module's series to 1e-16. Ridge minus momentum: -1.985%/yr, t -1.069. Ridge Sharpe from the module's returns: 0.324 | **Confirmed.** I did not re-estimate the ridge panel itself, only its saved returns. |
| S2 | No in-sample \|t\| > 2; INFL -0.32 (t -1.94), WTI t -1.71, DGS10 t -1.67, ATTN +0.09 (t 0.52) | predictors | Identical | **Confirmed** |
| S5 | Period table (10 timing/static pairs), FF6 alphas, turnover, post-2010 volatility 1.42% / 2.82% | portfolio_perf | Recomputed values match: full, post-2010, last 12 and last 18 Sharpe; alphas 0.24 (t 0.33), -0.74 (t -0.89), 0.58 (t 0.71), -0.05 (t -0.05); volatility 1.418 and 2.824 | **Confirmed.** "Identical rows in the CSV" is only approximately true: returns differ by up to 4e-7 per month and cost drag differs in the 4th digit. |
| S6 | Univariate DGS10 post-2010: +0.45% (p 0.018) and +1.11% (p 0.020); BH q 0.34 | oos_univariate | +0.448% (p 0.0176) and +1.109% (p 0.0202) | **Confirmed** |
| S6 | A+WTI: 96.9% at max, R2 -0.059% | oos_tests | CSV only, not recomputed | CSV-consistent |
| S9.1 | "LMN-style skepticism, applied honestly, gives zero weight to every value-spread, macro and attention predictor" | lmn_variant | The actual LMN variant picks the static limit (λ = 1e9) in only 0-12% of years, with median λ from 0 to 5623. So it **does** time, and it loses money. Recent-window CV also gives non-maximal penalties in 14-48% of months. | **Overreach.** Only the pre-registered MSE-based ridge-CV gives zero weight. |
| S9.2 | Attention's failure "is not an artifact of the 80th-percentile rule" | | M6 tests the raw GB spread, not the team's target, which is the FF3-hedged Brown-leg residual. My check on that target (60-month rolling FF3 with betas lagged one month, as in the team code): in-sample slope of the next-month residual on ATTN is -0.03%/sd (t -0.24) from 1990 and -0.07 (t -0.39) from 2010. Expanding OOS R2 is -0.74% (2000 on, CW t -1.98), -0.25% (2010 on) and -0.78% (holdout). | **Overreach in M6's own evidence.** The conclusion is supported by my extra check, so add that check or reword the claim. |
| S10 | "the timing portfolio's risk is concentrated in the late 1990s" | portfolio_returns | A: 68% of squared gross returns fall in 1995-99 (max month +9.6% in April 1999). **B: 58% fall in 2000-01** (24 of 319 months; +7.4% in January 2000). | **Partly wrong:** this is true for A only. |
| Ledger | 174 rows = 8 primary + 58 robustness + 108 exploratory; p-values match | tests_ledger | Counts confirmed; no duplicate IDs. Recorded two-sided p equals the normal p of the statistic (max diff 3e-16). Holm = 1 is trivially correct. | **Incomplete.** See the fixes below. |

## Ledger problems
1. **Two-sided p for one-sided CW tests.** Seven CW rows have negative t (the model is *worse* than the benchmark) and a two-sided p below 0.10. Examples: `B_full_1990_univariate_TERM_vs_histmean_post2010` has t -2.62 and p2 0.009; the ATTN-increment fixed-λ post-2010 rows have p2 from 0.06 to 0.10. A report-wide BH that reads `p_value_two_sided` would count these as discoveries in the wrong direction.
2. **Headline statistics missing from the ledger:** the static FF6 loading t-stats (RMW, HML, CMA, Mkt, UMD), the rotation mean-return t-stats (2.06 and 2.37), the UMD betas, and the LMN B minus B0 difference (t -2.38 and -2.00).
3. `IS_univariate_MCCC_1990` is mislabeled. Its sample starts in 2003-01.

## Required fixes
1. Save FINDINGS.md to `modules/M6_factor_timing/FINDINGS.md`. It is currently missing.
2. Headline 4: change to "short GB since 2022-05 (A) and 2021-12 (B); the historical mean was last positive for the 2022-04 and 2021-11 returns."
3. Headline 5 and section 5: say CMA is significant only in the 1990-2026 window (t -2.05; t -1.48 from 2000). Add Mkt (-0.05, t -2.68) and UMD (-0.06, t -2.47) for the 2000 window and SMB (-0.055, t -1.98) for the 1990 window.
4. Section 9.1: reword. The MSE-based ridge-CV gives zero weight. The LMN Sharpe-based variant does time, choosing the static limit in at most 12% of years, and loses. Recent-window CV designs pick smaller penalties in 14-48% of months with no gain (R2_OOS ≤ +0.13%, t ≤ 0.50). Add that CV-design sensitivity to section 6.
5. Section 9.2: either add the Brown-leg-residual check (ATTN in-sample t -0.24 from 1990; OOS R2 -0.74% from 2000, -0.78% in the holdout) or drop "not an artifact of the 80th-percentile rule". As written, M6 tests only the GB spread.
6. Section 10 caveats:
   - Risk is concentrated in 1995-99 for A (68% of variance) and in 2000-01 for B (58% in 24 months).
   - The Q1b timing-minus-static t depends on the relative ex-post scaling: with the static leg matched to the timing rule's mean |w|, t is 1.06 (A) and 0.17 (B).
7. Ledger:
   - add a one-sided p (or a direction flag) for the CW rows;
   - add rows for the static FF6 loadings, the rotation mean-return t-stats and UMD betas, and the LMN B minus B0 net-return difference (-1.04%/yr, t -2.38 sign; -0.57%/yr, t -2.00 raw);
   - report that difference in section 7 and headline 3;
   - rename `IS_univariate_MCCC_1990`.
8. Minor wording: "exactly 0" should read "numerically 0 (max forecast gap 5e-9)". "Identical rows" should read "identical to within 4e-7 per month".

None of these changes the verdict. The module's evidence supports "Do not implement".

## Round 2 (re-verification after fixes)

Scripts: `verify/verify_m6.py` (round 1, unchanged, rerun) and `verify/verify_m6_r2.py` (new; imports only my round-1 verifier, never `run.py` or `m6lib.py`). Results are in `verify/verify_results.json` and `verify/verify_results_r2.json`.
Run: `cd /home/hashim/projects/GA/project/research && uv run python modules/M6_factor_timing/verify/verify_m6_r2.py` (about 25 s; it also reruns the round-1 script).

**Status of FINDINGS.md: still not on disk.** The fixer could not write it because the harness refuses subagent writes of findings files. The full revised text is in the fixer's return, between `=== BEGIN FINDINGS.md ===` and `=== END FINDINGS.md ===`. I checked that text; the orchestrator must save it verbatim.

### Reruns
- `run.py`: exit 0 in 62 s, with 274 ledger rows (8 primary, 120 robustness, 146 exploratory).
  - All 34 M6 tables are byte-identical to the fixer's run, so the pipeline is deterministic.
  - Two harmless `SyntaxWarning`s come from `"\_"` and `"\%"` in non-raw strings (run.py lines 344 and 562). The .tex output is correct.
- Nothing pre-existing changed. Every table from the original build (snapshot 03:12) matches the fixed build on all common rows, with a max numeric difference of exactly 0. This covers:
  - oos_primary, oos_robustness, oos_univariate and oos_tests;
  - portfolio_perf and portfolio_returns;
  - lmn_variant, ff6 loadings, predictors, rotation_perf and rotation_returns;
  - ledger statistics and p-values.
  The only removed ledger id is the renamed `IS_univariate_MCCC_1990`.
- `verify_m6.py` rerun: every value equals round 1. The only change is the ledger counts, which is expected.

### New outputs recomputed independently (all match to machine precision)
| Output | My recomputation vs module | Max abs diff |
|---|---|---|
| cv_design (3 specs x 4 designs x 2 windows, plus 8 nested B vs B0 rows) | Shares at max and at λ ≤ 1, median λ, R2_OOS, CW t, one-sided p | 2.9e-13 |
| team_brown_residual (team `rolling_factor_model`, α and β lagged 1m) | My own rebuild from team ff49 and ff3 | 1.0e-16 |
| team_target_check (IS slopes; ATTN OLS; B ridge-CV; nested B vs B0 at ridge-CV, λ = 0 and λ = 1; 4 windows) | All 22 rows, including n. B ridge-CV at max in 83.70% of months | 2.4e-13 |
| scaling_sensitivity | Net and gross, equal-vol vs mean-\|w\| (A 0.338, B 0.320) | < 1e-14 |
| risk_concentration | Shares, window vol, and signed largest month with its date, for timing and static | < 1e-14 |
| timing_vs_prevmean | Max net gap 4.18e-7 (A) and 4.44e-7 (B); cost drag 9.2985 vs 9.2985 bp and 11.8001 vs 11.8000 bp | exact |
| histmean_sign | First short month 2022-05 (A) and 2021-12 (B). The hist mean is < 0 and w < 0 in every later month | exact |
| portfolio_ff6_loadings (timing rows, new claims) | A: RMW -0.092 (t -4.29), UMD +0.048 (t 2.05), other \|t\| ≤ 1.55. B: RMW -0.110 (t -2.62), UMD +0.058 (t 2.15), SMB +0.068 (t 2.03), other \|t\| ≤ 1.60. Static R2 0.14 and 0.18 | < 1e-14 |
| lmn_attn_increment | Own LMN: sign net -1.04%/yr (t -2.375), sign gross -1.08 (t -2.42), raw net -0.57 (t -2.00), raw gross -0.54 (t -1.87); n 307 from 2001-01 | 1e-14 |

### Earlier required fixes
| # | Round-1 fix | Status |
|---|---|---|
| 1 | Save FINDINGS.md | **Not resolved on disk (harness limitation).** The text exists and is verified; the orchestrator must save it. |
| 2 | Headline 4 dates | **Resolved.** The text now says short from 2022-05 (A) and 2021-12 (B); the mean was last positive for the 2022-04 and 2021-11 targets. histmean_sign.csv records this, and I confirmed it. |
| 3 | Headline 5 and section 5 exposures | **Resolved.** CMA is significant only from 1990 (t -2.05 vs -1.48). Mkt and UMD are added for 2000, and SMB for 1990. Full tables for both windows are included, and all values are verified. |
| 4 | Section 9.1 overreach; CV-design sensitivity | **Resolved.** "Zero weight" is now attributed to the pre-registered MSE CV. The LMN variant times in 88-100% of years. Recent-window CV picks smaller penalties in 14-48% of months with R2 ≤ +0.13% and CW t ≤ 0.50. Section 6 has the table, and every cell reproduces. |
| 5 | Section 9.2: add the team-target check or drop the claim | **Resolved.** The check is added, and the claim is now scoped ("M6 does not re-test the event rule itself"). The fixer also ran the multivariate nested test on the team target (ridge-CV +0.07%, one-sided p 0.105; negative at λ = 0 and 1), and I reproduced it exactly. |
| 6 | Section 10 caveats (risk concentration, scaling) | **Resolved.** The fixer corrects two of my round-1 statements, and **both corrections are right.** (a) The largest Spec A month in 1995-99 is **-9.6% (1999-04)**, a loss, not +9.6%. (b) For Spec B the largest absolute month is **-10.7% (2000-04)**, not +7.4% in 2000-01; the largest gain is +7.6% in 2000-06. My 1.06 / 0.17 scaling t-stats were on gross returns. Net they are 0.98 / 0.11, and FINDINGS reports both. |
| 7 | Ledger fixes | **Resolved.** Details below. |
| 8 | "Exactly 0" and "identical rows" wording | **Resolved.** The text now says "numerically 0 (max forecast gap 5e-9)" and "identical to within 4.5e-7 per month" (actual max 4.52e-7 gross, 4.44e-7 net). |

Ledger details (fix 7):
- **One-sided p on CW rows.** `p_value_one_sided` equals 1 - Φ(t) on all 186 CW rows (max diff 2e-16), and no non-CW row has one. `alternative` is set on every CW row.
- **Direction notes.** All 67 negative-t CW rows carry "model WORSE". Twelve of them have a two-sided p below 0.10, matching the text.
- **Low one-sided p.** Exactly 3 CW rows have a one-sided p below 0.05: the DGS10 post-2010 rows for A and B (exploratory) and the first120 nested ATTN row (robustness, p 0.024).
- **First120 row explained.** I confirmed the explanation for the first120 row. Post-2010, B sits at the max penalty in 100% of months (gap 2.5e-8), and B0 loses to the historical mean (R2 -0.138%, CW t -1.97).
- **Added rows.**
  - 36 FF6 loading rows, which include the rotation UMD betas (0.730, t 11.00; 0.955, t 27.29).
  - 2 rotation mean-return rows (t 2.06 and 2.37).
  - 4 LMN B minus B0 rows and 4 mean-|w| rows.
- **Counts and ids.** There are 32 CV-design rows and 22 team-target rows, for 100 new rows. No ids are duplicated. `IS_univariate_MCCC_2003` is renamed correctly, and the other IS ids carry their true start years.

### Other text claims checked
All other numbers in the revised FINDINGS text match the CSVs and my recomputations. This covers:
- headlines 1-5;
- sections 2, 5, 6 (the CV table, fixed-penalty post-2010 values with one-sided p ≥ 0.33 (A) and λ = 10 for B at t 0.66, p 0.25; and B0 ranging from -0.50% to +0.01%);
- section 7 (nested CV-design rows from +0.05% to +0.15% with p ≥ 0.23, and the team-target table);
- sections 9, 10 and 12, and the "about 60 s" run time.

### Optional polish (does not affect any conclusion)
- **Section 6, CV-design table.** Two statements are true for Specs A and B only, so qualify them:
  - "No design has a one-sided p below 0.24": B0 grid_max1e3 post-2010 has p 0.226, with R2 +0.003%.
  - "λ ≤ 1 in at most 23% of months": B0 recent60 is at 24.5%.
- **Section 10, "the static portfolios' risk is spread evenly".** Change it to "much more evenly (no window above 34% of squared returns)". The static 2000-01 window still carries 14% (A) and 18% (B) of squared returns in 5.5% and 7.5% of months.
- **run.py SyntaxWarnings.** Use raw strings at lines 344 and 562.

### Round 2 verdict
- All eight round-1 fixes are resolved in content. Fix 1 is blocked by the harness, and the orchestrator has to save the file.
- My two factual errors in round 1 (the sign and date of the largest risk months) are corrected.
- Nothing new broke: the pre-existing outputs are unchanged, and every new output reproduces independently.
- The module supports "Do not implement".
