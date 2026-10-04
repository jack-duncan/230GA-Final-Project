# M8 verification: frozen EMV-share rule, 1993-2009

**The FAIL verdict is confirmed, so "Do not implement" stands.** The preregistration was written before any 1993-2009 return existed and has not changed since. The code implements every one of the 32 preregistered choices. I rebuilt the whole test from the raw files with my own code, and all 128 published numbers I compared came out the same (largest gap 9e-13). The verdict also survives every reading of the rule that the text leaves open. Two text-only fixes are needed in FINDINGS.md: a free-month count that is off by one, and a one-sided p-value that C21 requires but no output reports. No number, table or verdict changes.

Verifier scripts (independent: none imports run.py, verify_signal.py, verify_m8.py, lib/team_pipeline.py or lib/common.py):
- `verify/xv_independent.py`: raw-file parsers, the signal as explicit loops, holds, rolling hedge, vol target, costs, P&L, BOND, own Newey-West, shuffle (replicated and independent sampler), episodes, drop-one, decomposition, then a comparison against every published M8 table (`xv_comparison.csv`, 128 rows).
- `verify/xv_timeline.py`: preregistration hash chain, file birth and modify times, and the run.py bytecode check (with `xv_pyc_observation.json`).
- `verify/xv_sensitivity.py`: exploratory variants for the readings the rule leaves open (`xv_sensitivity.csv`).
- `verify/xv_hml_reading.py`: checks the FINDINGS reading of the HML pair and computes the one-sided p.
- Outputs: `xv_results.json`, `xv_comparison.csv`, `xv_crossings.csv`, `xv_monthly.csv`, `xv_sensitivity.csv`.
- Run: `cd /home/hashim/projects/GA/project/research && uv run python modules/M8_frozen_pre2010/verify/xv_independent.py` (13 s). The sensitivity script takes 60 s.

The file `verify/verify_m8.py` (03:48, written by someone else) was not used.

## 1. Was the rule frozen before the results?

Yes. Birth times come from `stat` (statx). All times are PDT on 2026-09-26.

| Event | Time | Evidence |
|---|---|---|
| ChatGPT follow-up with the rule text | 03:15:14 | exchange/01 `chatgpt_followup_response.md` |
| M8 folder created | 03:29:54 | directory birth time |
| PREREGISTRATION.md written | 03:30:46 | birth 03:30:46.0, modify 03:30:46.4: written once, never edited |
| run.py first written | 03:35:43 | birth time |
| Dry run on seen 2010-2022 data | 03:36:35 | `dryrun/first_run_record.json`, same preregistration hash |
| run.py compiled to `__pycache__` | 03:37:28 | pyc header: source mtime 03:36:21, size 43,737 bytes |
| Primary 1993-2009 run | 03:37:46 | `first_run_record.json` (written 03:38:18), same hash |
| First M8 table exists | 03:38:13 | birth time of `outputs/tables/M8_passbar.csv` |
| Last run.py edit, last table write | 03:41:13, 03:41:24 | tables equal the first-run key exactly |

- **Hash:** the current SHA-256 of PREREGISTRATION.md is e926c3ae...0b51. It matches `first_run_record.json`, `dryrun/first_run_record.json` and `M8_preregistration_hash.csv`.
- **Code after the primary run:** the pyc compiled from the 03:36:21 source was written before the primary run. I compared it with the current run.py function by function, on normalized bytecode (opcode plus resolved argument). Only three functions differ:
  - `fmt`: LaTeX escaping;
  - `main`: the crossings-table caption and three added meta columns (first_run_time, this_run_time, prereg_written);
  - `make_figure`: added `set_ylim` calls.

  All other code objects are identical, including `share_signal`, `team_signal`, `decision_hold`, `brown_model`, `attribution`, `shuffle_test`, `count_episodes`, `evaluate` and the BOND functions. This matches the FINDINGS claim that only output formatting changed.
- **Process note:** another process imported run.py at 05:50:24 and recompiled the pyc, so the pre-primary bytecode is no longer on disk. I made the comparison before that happened and recorded it in `verify/xv_pyc_observation.json`. The M8 tables and figure were not touched; they still date from 03:41.
- **First-run key and published tables agree exactly:** alpha, t, shuffle p, episodes, the five drop-one alphas and the verdict.
- **Contamination:** the two items disclosed in PREREGISTRATION.md section 0 are the ones that matter.
  - One exchange-1 check (c04) regressed raw, unhedged and untimed Brown industry returns on the market, the change in the 10y yield and commodity returns over 1992-2026. That is consistent with the claim that no strategy return, hedged residual, P&L or alpha was seen, and it is negligible.
  - M3 and M6 later computed pre-2010 Short-Brown and residual statistics. Their earliest surviving outputs date from 03:39:59, after the primary run, so they could not have shaped the frozen choices.

## 2. Does run.py implement the rule exactly?

Yes. For each item below I wrote an independent implementation, and its result matches M8's.

| Rule element | Preregistered choice | run.py | Independent result |
|---|---|---|---|
| One-month publication lag | C4: data month t becomes the decision at t+1 and first earns t+2 | `decision_hold` shifts crossings by 1 | Hold series identical in all 190 window months |
| Zeros dropped from the z window | C3, C5 | zero months set to NaN before a rolling 60, min 48 | z identical to 8e-15, NaN pattern identical over 1985-2010 |
| Zeros dropped from the percentile history | C6, C7 | expanding quantile of the lagged z skips NaN | Threshold identical to 4e-15 |
| 48 nonzero of 60 | C5 | `min_periods=48` on the masked log share | First z in data month 1989-01 (49 months, one zero in 1985-04) |
| More than 10% zero means off | C6: more than 6 zeros in 60 | `zeros60 > 6` masks z | 0 off months before 2010 (at most 3 zeros in any 60-month window); 53 off months, all after 2010 |
| Past-only p80 with 60 prior z values | C7: strict >, linear interpolation | team `expanding_threshold` | First threshold in data month 1994-01 |
| Crossing that skips missing months | C8 | run on the valid months only | 0 differences from a no-skip rule over the whole sample, so this choice is inert |
| Extend, do not stack | C9: union of 6-month windows | rolling max of the lagged crossings | Same holds; 23 of 33 crossings extend a running hold |
| Hedge lag | C10: 60m FF3 betas through t hedge t+1 | team `rolling_factor_model` | Rebuilt with a normal-equation solve; net returns identical to 1e-15 |
| Vol target and cap | C10: 5%/(sqrt 12 x 36m residual sd), capped at 1 | team `state_position` | Positions identical to 2e-14 |
| Costs | C10: 10bp asset, 5bp Mkt-RF, 25bp SMB/HML, charged the next month | team `asset_strategy_returns` | Explicit cost loop; timed and always-on net returns identical |
| Window | C12: W0 = max(1993-01, tau0 + 1) | tau0 = 1994-02 | W0 = 1994-03 to 2009-12, 190 months |
| pi and D | C13 | mean abs lagged position ratio | pi 0.72943 in both; D identical to 8e-16 |
| Regressors | C14-C18: FF5 2x3 + UMD, BOND, WTI log return, dVIX from the daily mean, dlog EMV overall | as specified | Own Ken French and FRED parsers; all 15 coefficients identical to 1e-9 |
| Conditional terms | C19, C20: I_{t-1} x {Mkt-RF, HML, BOND, dVIX} | I = position entering t is nonzero | 142 of 190 months in position |
| k and t(n-k) | C20, C21: k = 15, NW(6) Bartlett, no scaling | as specified | n 190, df 175; all 15 t-stats identical to 1e-12 |
| Shuffle | C24: same blocks in random order, non-touching, uniform, 5,000 draws, seed 230 | stars-and-bars placement | See below |
| Episodes | C25: runs of the decision-time hold that touch decision months 1994-02 to 2009-11 | `count_episodes` | 10 (lengths 6, 6, 16, 6, 11, 25, 14, 25, 23, 10; sum 142) |
| Leave one industry out | C26: leg, hedge, residual, vol target, always-on, pi, D and regression all rebuilt | `evaluate` | All five alphas and t-stats identical |
| Decomposition | C22 | contributions = coef x mean | Identity gap 2e-19 |
| BOND | C15: par 10y semiannual, D and C at y_{t-1} | exact cash-flow sums | Analytic D and C, cross-checked by numerical derivatives (D to 2e-6); closed form to 3e-13; exact repricing within 5.4 bp |

**Shuffle, in detail.** There are 190 decision months, 142 of them in position, split into 10 blocks. That leaves 48 flat months, and 9 of them are needed as separators between blocks, so 39 months are free to place. I ran two checks:
- **Same draws as run.py.** Replicating run.py's generator calls, every one of the 5,000 draws matches the published M8_shuffle_draws.csv to 1e-13, and p = 0.4779.
- **Independent sampler.** I shuffled 10 labelled blocks among 39 unit gaps with a different seed. It gives the same distribution: p = 0.4789, median -0.21%/yr, 5th to 95th percentile -1.36% to +0.92%.

Every draw kept the number of blocks and their lengths, and blocks never touched. For the secondary signal the two checks give p = 0.1282 and 0.1320.

**Team secondary signal (C28).** The z of log1p (60 months, min 36, zeros kept), the threshold and the crossings match the panel exactly.

## 3. Key numbers: M8 against my recomputation

| Statistic | M8 | Independent |
|---|---|---|
| (i) timing alpha, %/yr | -0.18 | -0.18 (-0.1818) |
| NW(6) t; two-sided p from t(175) | -0.27; 0.790 | -0.266; 0.790 |
| NW(12) t | -0.29 | -0.287 |
| (ii) shuffle p, one-sided | 0.478 | 0.4779 same draws; 0.4789 independent sampler |
| Shuffle median; 5th to 95th percentile, %/yr | -0.22; -1.30 to +0.91 | -0.22; -1.30 to +0.91 |
| (iii) episodes | 10 | 10 |
| (iv) drop Util / Ships / Aero / Steel / BldMt, %/yr | -0.61 / +0.03 / +0.01 / -0.19 / -0.11 | identical (to 1e-9) |
| pi; months in position | 0.729; 142 of 190 | 0.7294; 142 |
| Timed net; always-on; mean D, %/yr (t) | +0.51 (0.42); +0.65 (0.48); +0.04 (0.06) | identical |
| Secondary alpha (t); shuffle p; drop-one | +0.69 (1.00); 0.128; all five > 0 | identical; 0.128 and 0.132; identical |

Pass bar: (i) FAIL, (ii) FAIL, (iii) PASS, (iv) FAIL, so the verdict is FAIL. That is confirmed.

## 4. Sensitivity to readings the rule left open (exploratory, not part of the verdict)

All variants below use the same 1994-03 to 2009-12 window.

| Variant | Alpha, %/yr | t | Note |
|---|---|---|---|
| Frozen rule (C5-C8) | -0.18 | -0.27 | |
| z needs a full 60-month history (no burn-in from 48 months) | -0.28 | -0.37 | first valid data month 1994-12; 4 crossings differ |
| z >= threshold instead of > | -0.18 | -0.27 | no change |
| Lower or higher order statistic for the p80 | -0.18 | -0.27 | 2 crossings differ under "lower", same holds |
| Crossing-level shuffle (each 6-month window moved on its own, 2,000 draws) | | | one-sided p 0.446 |
| 3-month hold (the team's other hold; not the frozen rule) | -0.96 | -1.30 | |

No reading gets close to t = 2. The verdict does not depend on any of these choices.

## 5. FINDINGS.md claims checked

Confirmed:
- **WINDOW:** first z 1989-01, first threshold 1994-01, first decision 1994-02, first crossing 1995-08.
- **Pass-bar numbers:** (i) to (iv) as in section 3.
- **CONTEXT:** confirmed.
- **DECOMPOSITION:** every term and group matches to 0.01 pp. The HML pair is HML +0.145 (t 2.28) and I x HML -0.143 (t -2.36).
- **HML interpretation:** it holds for the pooled Ferson-Schadt model. In an HML-only split, the always-on leg's HML beta in out-of-position months is -0.195, and -pi x -0.195 = +0.142, against the pooled +0.145. In in-position months it is +0.008. With the full factor set fitted to the 48 out-of-position months alone, the HML beta of D is -0.04 (t -0.47). So the reading is descriptive of the pooled model and fragile on its own, but the wording is acceptable.
- **SECONDARY:** confirmed, including the dry-run comparison. On the seen 2010-2022 window the lagged team signal had +1.11% (t 2.03) and the share rule -0.12% (t -0.19).
- **CROSSINGS:** 33 crossings; 23 extend a hold; 19 fall within one month of a team crossing; 7 and 5 are in the top quintile of overall EMV and of VIX; median ranks 45 and 53.
- **BOND CHECK:**
  - 2022: -15.0% (exact repricing -14.9%, Damodaran -17.8%).
  - 1994: -7.5% (-8.0%); 2008: +19.4% (+20.1%). I spot-checked the Damodaran values against the M3 xls.
  - Duration in the 1990s averages 7.2 (range 6.5 to 8.0); over 1993-2009 it runs 6.8 to 8.8.
  - I did not recompute the 0.987 correlation independently.
- **Zero months before 2010:** there are 7 (1985-04, 1995-11, 2000-01, 2000-02, 2004-09, 2005-02, 2006-06). EMVOVERALLEMV has 500 contiguous months with no zero and no missing value.
- **Ledger:** 22 rows, 8 of them primary.
- **LaTeX:** all 12 M8 .tex tables compile with tectonic.
- **Process claims:** "Deviations: none" and "only output formatting changed" are both confirmed by the bytecode check.

Not exactly right:
- **Caveat (3)** says the shuffle "had only 38 free months". The correct figure is 39: 48 flat months minus 9 separators.
- **IMPLEMENTATION CHECKS** says the numpy shuffle engine equals `asset_strategy_returns` "(0.0)". The recorded maximum difference is 4.3e-19 (`engine_check_maxdiff` in M8_strategy_summary.csv). This is immaterial.
- **C21 reporting gap:** C21 says "one-sided upper p also reported". run.py computes it (`p6_upper`) but writes it to no table, and FINDINGS does not quote it. From t(175) it is 0.605 for the primary and 0.159 for the secondary.

## 6. Required fixes (text only; no code change, rerun or number change)

1. FINDINGS.md caveat (3): replace "only 38 free months" with "only 39 free months (190 decision months, 142 in position, 48 flat, 9 of them needed as separators between the 10 blocks)".
2. FINDINGS.md (i): add the one-sided upper p that C21 preregistered: primary p = 0.605 from t(175), secondary 0.159. List this under Deviations as "reporting only: computed by run.py but not written to a table".

Optional:
- Change "(0.0)" to "(max diff 4e-19)" for the shuffle-engine check.
- M8_crossings.tex is 5.7 pt overfull even on a landscape page with 0.5 in margins. It needs `\small` or `\resizebox` before it goes into the report.
- Add one line to the PROCESS paragraph: the pre-primary bytecode check was made by the verifier, and the pyc was later recompiled by another process (see `verify/xv_pyc_observation.json`).

# Round 2: the post-verification corrections (06:05 rerun)

**All seven corrections are confirmed, and the verdict is unchanged: FAIL, so "Do not implement" stands.**
- I reran run.py at 06:09:57 PDT. It reproduces the 03:37:46 first-run key.
- My independent rebuild still matches all 128 published numbers (largest gap 9.3e-13).
- No published number has moved since 03:41: every shared numeric column has a max abs diff of 0.0.
- The code change is output-only. Its one reporting change, writing out C21's one-sided p, is the kind of fix C31 allows.

FINDINGS.md still has two small text problems, both new:
- The correction edit re-created run.py, so its on-disk birth time now reads 06:05:07. The timeline section does not say so, and a reader who runs `stat` would see a file apparently born after the primary run.
- The claim that two tables "fit a landscape page" holds only with 0.5 in margins.

Neither changes a number or the verdict.

New script: `verify/xv_round2.py` (about 2 minutes, mostly TeX compiles). It writes `verify/xv_round2.json` and `verify/xv_round2_tex.csv` and imports none of run.py, lib/team_pipeline.py or lib/common.py. Sections A and C use this session's scratch folders (a sandbox run of run_0341.py and a copy of the 06:05 outputs). The script skips them when those folders are gone; their results are recorded here.

## R2.1 What I reran

| Run | Result |
|---|---|
| `run.py` (primary), 06:09:57 | "this run reproduces it: True" against 03:37:46. The console now prints one-sided upper p 0.605 (primary) and 0.159 (secondary) |
| `verify/xv_independent.py` | 128 of 128 comparisons pass against the corrected tables; largest gap 9.3e-13 |
| `verify/xv_hml_reading.py` | Same as round 1. The t-stats it prints are used in R2.3, item 6 |
| `verify/xv_sensitivity.py` | Identical to round 1 |
| `verify/xv_timeline.py` | Hash chain and first-run key unchanged; see R2.5 for its bytecode section |
| `verify_signal.py` (builder's) | z 2.3e-14, threshold 3.2e-15, crossings identical, as FINDINGS says |
| `corrections/pre_correction_0341/run_0341.py`, sandboxed | Reproduces the 03:41 snapshot (R2.2) |

Before my rerun I copied the 06:05 outputs to my scratch folder. My rerun reproduces them:
- all 20 tables are byte-identical except the `this_run_time` cell of M8_preregistration_hash.csv;
- the PNG is byte-identical;
- the PDF differs only in its /CreationDate stamp.

## R2.2 Is the 03:41 snapshot faithful?

Yes.
- **Manifest.** All 25 SHA-256 values in `corrections/pre_correction_0341/manifest.json` match: the copied tables, figures and run_0341.py, and the live PREREGISTRATION.md and first_run_record.json. Every copy keeps its 03:41 modify time.
- **run_0341.py.** It is 44,443 bytes with modify time 03:41:13. That is the size and time I recorded for run.py in round 1 (`xv_pyc_observation.json`), before any correction.
- **Sandbox run.** I ran run_0341.py with tables and figures redirected to my scratch folder. M3's Damodaran file is linked in, because bond_checks finds it relative to run.py; without the link, the bond table loses its reference column.
  - It reproduces the first-run key.
  - 19 of 20 tables are byte-identical to the snapshot. The 20th, M8_preregistration_hash.csv, differs only in `this_run_time` and in the `prereg_file` path, which is the sandbox path.
  - The PNG is byte-identical; the PDF differs only in /CreationDate.

So the snapshot is exactly what the 03:41 code produces.

## R2.3 Is the code change output-only?

Yes.
- `corrections/run_py_changes.diff` is exactly `diff -u run_0341.py run.py`.
- **Bytecode.** I compared normalized bytecode function by function. There are 33 code objects before and after, and only `main` and `to_tex` differ.
  - At module level the only change is to_tex's new default arguments (`'\\small', None`).
  - These are identical: share_signal, team_signal, decision_hold, brown_model, run_strategy, FastEngine, nw_numpy, attribution, runs, shuffle_test (with alpha_of), count_episodes, evaluate, the BOND functions, load_inputs, monthly_grid, fmt and make_figure.
- **The five hunks in `main`:** two appended attribution columns, the crossings.tex headers and size, the four ledger notes, `prereg_file_mtime` in the meta table, and the console line. None feeds a statistic.
- **C31.** C31 allows a post-primary fix only for "a clear coding error against this document", listed under Deviations with before and after numbers.
  - Not writing out C21's one-sided p is an error against C21 ("one-sided upper p also reported") and C32 (every statistic goes to the ledger). FINDINGS lists it with before and after values.
  - The crossings.tex layout and the extra meta column are output format only and touch no preregistered choice.

| # | Correction | Verdict | My evidence |
|---|---|---|---|
| 1 | 39 free shuffle months | Confirmed | From my own block lengths: N 190, in position 142, flat 48, 9 separators, free 39. Secondary: 104, 86, 9, 77. run.py computes `free = N - L.sum() - (m - 1)`, and shuffle_test's bytecode has not changed since 03:36, so the shuffle always used 39. |
| 2 | C21 one-sided upper p | Confirmed | The two new attribution columns equal t.sf(t, 175) of my own t-stats, to 3e-13, in all 30 rows. Constants: primary 0.6048 (NW6) and 0.6128 (NW12); secondary 0.1588 and 0.1237. The old columns keep their positions and values, and the two-sided p equals 2 min(p_upper, 1 - p_upper) to 3e-16. Ledger: 22 rows, 8 primary; the four i_alpha notes quote 0.6048, 0.6128, 0.1588 and 0.1237. |
| 3 | Engine check 4.3e-19 | Confirmed | engine_check_maxdiff = 4.336808689942019e-19 for both signals |
| 4 | Preregistration stamp against file save | Confirmed | The file says "Written: 2026-09-26 03:29:54 PDT". Folder birth 03:29:54.463, the same second. File birth 03:30:46.443 and modify 03:30:46.447 (4 ms apart). The new prereg_file_mtime column reads 03:30:46 PDT. Hash still e926c3ae...0b51. |
| 5 | PROCESS wording on post-primary edits | Confirmed | Matches `xv_pyc_observation.json` (set_ylim constants in make_figure; fmt and main the only other changes) |
| 6 | HML reading qualified | Confirmed | Always-on HML-only beta: -0.195 (t -1.93) out of position, +0.008 (t 0.15) in position. 0.7294 x 0.195 = 0.142. D with the full factor set on the 48 out-of-position months: -0.044 (t -0.47). D's own HML-only beta out of position is +0.144 (t 1.95), matching the pooled +0.145. |
| 7 | M8_crossings.tex layout | Confirmed | See the TeX table below |

TeX check: each M8 .tex, from now and from the 03:41 snapshot (14 files), compiled with tectonic inside a 10pt or 11pt article with booktabs. Numbers are the widest overfull hbox, in pt; 0 means it fits. All 14 compile.

| File | Portrait 1 in, 10pt | Portrait 1 in, 11pt | Landscape 1 in, 10pt | Landscape 0.5 in, 10pt |
|---|---|---|---|---|
| M8_crossings.tex at 03:41 | 258.6 | 306.9 | 77.9 | 5.7 |
| M8_crossings.tex now | 0 | 0 | 0 | 0 |
| M8_passbar.tex (unchanged) | 216.2 | 265.8 | 35.5 | 0 |
| M8_strategy_summary.tex (unchanged) | 216.2 | 263.0 | 35.5 | 0 |
| attribution, decomposition, drop_one, bond_check | 0 | 0 | 0 | 0 |

## R2.4 Other claims in the corrected FINDINGS

Confirmed:
- **(i) p-values:**
  - Primary: two-sided 0.790, one-sided 0.605. NW(12): two-sided 0.774, one-sided 0.613.
  - t = 2 on t(175) gives a one-sided 0.0235, which FINDINGS rounds to 0.024.
  - Secondary: two-sided 0.318, one-sided 0.159. NW(12): t 1.161, one-sided 0.124.
  - Shuffle: two-sided 0.956.
- **BOND against Damodaran, 1993-2025: correlation 0.987 over 33 years.** This uses my own BOND construction and my own reading of `histretSP.xls` (sheet "Returns by year", column "US T. Bond (10-year)"). Round 1 left this number unchecked; it is now confirmed.
- **Rerun evidence:**
  - The 06:05 copy's this_run_time is 06:05:14.
  - `rerun_comparison.csv` agrees with my own comparison on all 20 files. 16 are byte-identical. The only changes are M8_attribution.csv (2 appended columns), M8_tests_ledger.csv (4 note cells), M8_preregistration_hash.csv (this_run_time and the new prereg_file_mtime) and M8_crossings.tex.
  - Every shared numeric column has a max abs diff of 0.0, and the PNG is byte-identical.
- **My verify/ outputs** still carried their 05:59 times until my own rerun, so the builder's rerun did not overwrite them, as FINDINGS says.
- **Untouched files:** first_run_record.json (03:38:18), dryrun/ and PREREGISTRATION.md have the same birth times, modify times and hashes as in round 1.
- **Table birth times** are unchanged; for example, M8_passbar.csv was born at 03:38:13.195.
- **Deviations:** "the rule has none" and the single reporting-only deviation are both accurate.

Not right:
- **run.py birth time.**
  - The 06:05 edit re-created run.py as a new file (new inode), so `stat run.py` now shows birth 06:05:07.823.
  - The original birth, 03:35:43.583, survives only in `corrections/pre_correction_0341/manifest.json` and in round 1 of this file.
  - FINDINGS PROCESS still cites "run.py existed (first written 03:35:43)" as if it could be read from disk. "Preserving the timeline" covers the tables' birth times but not this.
  - The timeline matters for a preregistration audit, so this should be disclosed.
- **Table modify times.** FINDINGS says the tables' modify times "are now 06:05". My round-2 rerun moved them to 06:10:07. This is a consequence of verification, not an error, but the sentence should not name a single time.
- **Layout claim.** "M8_passbar.tex and M8_strategy_summary.tex fit a landscape page" is true only with 0.5 in margins; at 1 in margins they are 35.5 pt too wide. The "about 216 pt too wide for portrait at 1 in margins" figure is right at 10pt; at 11pt it is 263 to 266 pt.

## R2.5 Corrections to my own round 1

- Section 5 says "all 12 M8 .tex tables compile". There are 7 M8 .tex tables in outputs/tables, plus 7 M8dry_ tables in dryrun/. All 7 compile, as do the 7 in the 03:41 snapshot.
- Section 1's "run.py first written 03:35:43, birth time" was true when I checked it. It can no longer be read from run.py itself; the evidence is now the manifest.
- **xv_timeline.py bytecode section.** It is now vacuous, because the pyc on disk has been recompiled from the current run.py, and its "unchanged: 33" line is not evidence.
  - I added printed notes saying so, pointing to `xv_round2.py` section E for the 03:41 to 06:05 comparison and to the manifest for run.py's original birth time.
  - The pre-primary comparison stands, as recorded in `xv_pyc_observation.json`.
  - The script's hash-chain and first-run-key checks are still valid.

## R2.6 Required fixes (text only; no code change, rerun or number change)

1. **FINDINGS.md, timeline.**
   - In "Preserving the timeline", add: "The 06:05 edit re-created run.py as a new file, so `stat run.py` now shows birth 06:05:07. Its original birth, 03:35:43.583, is recorded in corrections/pre_correction_0341/manifest.json and in VERIFY.md round 1."
   - Replace "their modify times are now 06:05" with "their modify times show the latest rerun (06:05 for the correction run; the verifier's round-2 rerun moved them to 06:10)".
   - In PROCESS, after "(first written 03:35:43)", add "(birth time recorded in corrections/pre_correction_0341/manifest.json)".
2. **FINDINGS.md, FILES, Layout.** Replace "fit a landscape page, but are about 216 pt too wide for portrait at 1 in margins" with "fit a landscape letter page only with 0.5 in margins (35 pt too wide at 1 in), and are 216 pt too wide for portrait at 1 in margins (10pt; 263 to 266 pt at 11pt)".

Optional:
- In the rerun evidence, say that the figure PDF differs from the 03:41 copy only in its /CreationDate stamp.
- Add the verifier's round-2 rerun (06:09:57, reproduces: True) to "Every later execution printed 'reproduces it: True'".
