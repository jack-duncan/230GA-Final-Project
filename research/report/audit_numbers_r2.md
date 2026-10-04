# Number audit of report.tex (draft of 2026-09-26, 10:58)

Scope: every number in the main body (Executive Summary to Section 2.9), the appendix prose and captions, and the generated tables the report inputs (`report/tables/tab_*.tex`, `body_M7_*.tex`, and the captions of `app_*.tex`). Hashim's own boxes and evaluations in Appendix A are in scope. The verbatim prompts, replies and fact-check excerpts in `appendix_transcripts.tex` are not.

Sources:
- module CSVs in `outputs/tables/`;
- the latest round of each `modules/<id>/FINDINGS.md` and `VERIFY.md`;
- `logs/replication.md` and the team `writeup.pdf`;
- `exchange/01` to `exchange/04` (fact-checks, evaluations, `04_red_team/revisions.md`, `checks/out/fc04_results.json`);
- `logs/lit_digest.md`;
- the course brief.

Severity scale:
- **High**: a wrong claim, or a headline that contradicts the report's own method or a cited source.
- **Medium**: a wrong count or range, overreach, or an internal inconsistency.
- **Low**: rounding, labelling, a missing qualifier, or provenance.

None of the findings changes the verdict.

## Summary

- About 320 numeric claims checked. 23 findings: 1 High, 3 Medium, 19 Low.
- The core numbers are sound. Every cell of tab_time, tab_signals, tab_frozen, tab_ledgers, tab_m1_cross and the M7 body tables matches its source CSV. The replication, M1 to M8 and exchange numbers match their verified sources.
- The previous audit (08:47 draft) raised 32 findings. 29 are fixed in this draft. Three survive in weaker form: the provenance list (M2 here), the executive summary's p-value claim (L1) and the citations (L17).
- The High item: the executive summary says the optimizer book "lost in the holdout (-0.34%)". The -0.34% is its FF5+UMD alpha (t -0.15). Its holdout net return was +2.29% a year.
- `report.log` has no undefined references and no overfull boxes.

## Findings

Line numbers refer to `report/report.tex` unless stated. "App A" lines refer to `report/appendix_transcripts.tex`.

| # | Location | Claim as written | Correct value | Source | Severity |
|---|---|---|---|---|---|
| H1 | l.46 (Executive Summary) | "an optimized industry-momentum book ... fails the deflated appraisal ratio and lost in the holdout (-0.34%)" | -0.34% is the book's holdout FF5+UMD alpha (t -0.15). Its holdout net return is +2.29% a year (validation +5.07%). The book made money in the holdout; its alpha vanished. l.235 states this correctly ("its holdout alpha is -0.34%"). | `M5_industry_momentum_optimizer_periods.csv` (X_unc, holdout: net_ret 0.0229, alpha_ff5umd -0.0034, t -0.15); `M7_cost_stress.csv` (holdout gross alpha -0.04%) | High |
| M1 | l.105 | "hashed a pre-registration of 32 implementation choices five minutes before its code existed" | The file was saved and date-stamped at 03:30:46 PDT, five minutes before run.py (03:35:43). Its SHA-256 was first recorded by run.py itself, in the dry run at 03:36:35, after the code existed. The evidence that the pre-registration came first is the file's birth and modify times, not a prior hash. The hash shows the file never changed: its SHA-256 on disk today is e926c3ae...0b51, equal to the recorded value (recomputed for this audit). | M8 FINDINGS, PROCESS; `M8_preregistration_hash.csv`; `modules/M8_frozen_pre2010/dryrun/first_run_record.json` (run_time 03:36:35, prereg_sha256); `stat PREREGISTRATION.md` | Medium |
| M2 | l.107 | "computed only once: the 86% P&L share, the null-seed counts, and the holdout entry, path and interval figures from exchange 04" | The list is incomplete. Three more single-computation numbers from `fc04_checks.py` appear in the body: Steel -1.37 of -1.38 gross points (l.201); the untimed EPA short's +1.07%, t 0.79 (l.251); and our team's lagged signal, +0.36%, t 0.70, on the two unseen windows (l.258, the verdict paragraph). `revisions.md` lists all of them under "[fc04] numbers to verify before submission", and no verifier has re-run them. The intervals (-5.0% to +1.1%, -2.6% to +6.2%) and the 1.9% power figure are arithmetic on verified numbers and need no rerun. | `exchange/04_red_team/revisions.md`, last table; `checks/out/fc04_results.json` | Medium |
| M3 | l.680 (tab:m7dsr caption) | "the book would pass only if the project had tried three or fewer independent strategies" | The pass bar needs both windows. The largest passing N is 3 over 1970-2026 but 2 over 2010-2026, so the book passes both only with 2 or fewer. The M7 verifier (R7) required exactly this qualification in FINDINGS; the caption repeats the pre-fix wording. | `M7_dsr.csv` (max_N_pass 3 and 2); M7 VERIFY R7; M7 FINDINGS s5 | Medium |
| L1 | l.46 | "p-values come from small-sample t distributions" | True for the strategy tests (M2, M3, M8, M1b with n < 60, M7's holdout reading). Not true for M1 (normal HAC p), M4 and M5 (normal p; Appendix E itself quotes M5's BH 0.022 from a normal p of 0.0015) or M6 (normal one-sided Clark-West). Section 1.3 (l.103) states the scope correctly. | M1 FINDINGS, caveats; M4 VERIFY; M5 FINDINGS s4; M6 FINDINGS s3 | Low |
| L2 | l.46 | "shrinkage timing collapses to the historical mean" | Holds under the pre-registered MSE cross-validation: 758 of 758 refits choose the maximum penalty. Recent-window CV designs pick a smaller penalty in 14% to 48% of months, and the LMN Sharpe-validated variant times in 88% to 100% of years. None beats the mean (R2_OOS at most +0.13%; net Sharpe -0.33 to 0.11). Section 2.6 and Appendix C keep the qualifier; the summary drops it. | M6 FINDINGS, headlines 1 and 2, s9; M6 VERIFY | Low |
| L3 | l.46 | "the untimed short lost too (-1.72%, t=-1.09)" | -1.72% is the FF3 alpha. The holdout net return is -1.04%. Label the statistic. | M2 strategy grid (Always-short Brown, corrected, holdout); tab_time | Low |
| L4 | l.201 | "Steel alone carries the gross loss (-1.37 of -1.38 points)" | By industry: Util +1.07, Ships -0.51, Aero -0.20, Steel -1.37, BldMt -0.37 (sum -1.38). Steel equals the total only because Util offsets the other three losers. The exchange 04 evaluation mentions the offset; the body drops it. | `fc04_results.json`, holdout6_split.by_industry_ann | Low |
| L5 | l.87 against l.201 | "the rule enters in the same five holdout months" against "from six entries" | Both are right, for different counts. M1 counts five crossings in holdout data months (2023-04, 2024-06, 2025-02, 2025-09, 2025-11). The corrected rule's six entry decision months add the 2022-07 crossing, which the one-month lag turns into a 2022-08 entry. The report does not say so, so the two counts look inconsistent. | M1 FINDINGS Q3; `fc04_results.json`, holdout_lead_rules.corrected_6m.entry_decision_months | Low |
| L6 | l.233 | "A carbon limit costs no detectable IR ... b=0 cut long-book carbon intensity only 11.6% ... b=-1 cuts it 60%" | The numbers are correct, but they belong to the Grinold-Kahn optimizer book (convention X), not the equal-weight book the paragraph describes. | M5 FINDINGS s2 (Q3 primary) and s7 | Low |
| L7 | l.639 | "The best one-sided p is 0.030 (M2, Pure 6m post-2010, t=1.89)" | This is the uniform 5 bp variant (M2's Q4 primary: 1.61%, t 1.89). At team costs the same rule's post-2010 FF3 alpha is 1.42% (t 1.65). | M7 FINDINGS s2 ("u5 Pure 6m"); `M2_christhian_tests_q4_primary.csv` | Low |
| L8 | l.700 | "At 25 bp the full-sample alpha stays positive (1.73%, t=2.43)" | This is the 1970-2026 FF5+UMD alpha (check 8). In a paragraph about the frozen run it reads as the 1931-1969 figure, which is 1.55% (t 1.94) at 25 bp. | `M7_cost_stress.csv`; `M7_frozen_pre1970.csv` (S4) | Low |
| L9 | l.698 | "Two development runs before the frozen run used only post-1970 formation months" | The formation months ran from 1969-12 to 2008-05; the return months start in 1970-01. | M7 FINDINGS s0 | Low |
| L10 | l.126 (Table 2, M6 row) | "timing minus static +0.84% (t=1.17)" with adjusted p "1.00" | 1.00 is the Holm p of the six Clark-West tests. The timing-minus-static test is outside that Holm family; its p is 0.24 (0.65 for Spec B), as Table E.2 says. | M6 FINDINGS s4 and s5 | Low |
| L11 | l.386 (App C, M1b) and l.389 (tab:signals caption) | "no validation alpha near t=2"; "Only the EMV tracker produces validation alphas near t=2" | CPU Original 6m has a validation alpha of 1.81% (t 1.73), arguably near 2. The accurate statement, used in Section 2.1, is "none with t >= 1.96". | `M1b_alt_signals_primary.csv`; tab_signals | Low |
| L12 | l.504 (M5 carbon-cost table caption) | "Only b=-2, partly infeasible, costs significantly." | Only under convention X over the full sample (IR change -0.284, p 0.038). Post-2010 p is 0.185 and convention M p is 0.17. | M5 FINDINGS s7 | Low |
| L13 | l.156 (Table 3); App A l.14 | "A 1,772-word review" | 1,772 is the wc count. Appendix A's stated convention compares the count without Markdown symbols with the cap, which is 1,609 here. Table 3 uses that convention for exchanges 03 (1,716) and 04 (1,340), so the table mixes conventions. | `appendix_transcripts.tex` word-count lines; `build_transcripts.py` l.227 | Low |
| L14 | App A l.38 (exchange 01 evaluation, last bullet) | "M7: the exposure-matched benchmark, calendar-shuffle null ... The 1993--2009 rule is frozen ... and is scored once." | Stale module label. In this report the frozen rule is M8; M7 is the robustness ledger. | report Table 2; `modules/` | Low |
| L15 | App A l.28 (exchange 01 evaluation) | "since 2010, crossings are 4.5 times as likely, in odds, in high overall-EMV months; p = 0.002" | Right under the fact-check's definition (overall-EMV z above its past 80th percentile). Section 2.1 and Table C use M1's verified definition (above the past median). Under M1's definition the since-2010 odds ratio is 6.0 (88.5% against 56.1%, Fisher p 0.0012). Name the definition. | `exchange/01_idea_generation/checks/c10_attention_meaning.py` l.35; `M1_signal_audit_crossings_vix_summary.csv` | Low |
| L16 | App A l.2354 (exchange 03 evaluation) | "the appraisal ratio (0.40) passes only up to 6 or 7 trials" | This holds on the fact-check's inputs. M7's implementation, with the cross-trial variance from clusters, allows at most 3 trials over 1970-2026 and 2 over 2010-2026, the basis of the tab:m7dsr caption. The report gives two numbers for one quantity. | exchange 03 fact-check; `M7_dsr.csv` | Low |
| L17 | l.264 to l.288 (Bibliography) | ardia2023, bbdk2019, bldp2014, bh1995, by2001, ct2008, cw2007, fs1996, gavriilidis2021, gk2000, hansen2005, holm1979, nw1987, rw2005 | None of these has an entry in `logs/lit_digest.md`, whose section 12 covers only MG1999, ZA2024, TM1966, HM1981 and LN2006. Journal, volume, issue and pages agree with my general knowledge, but check each against the original before submission. | `logs/lit_digest.md` s0 and s12 | Low |
| L18 | l.87 | "a count of newspaper articles on stock-market volatility that mention the category, scaled to the VIX" | Consistent with the share construction (category tracker = overall EMV x category share). However, M1 records it as the builder's reading, "not checked against article counts", and bbdk2019 is not in the digest. | M1 FINDINGS, Data | Low |
| L19 | l.242 | "In the robustness grids (9,337 alphas) BY keep none and BH keep one" | Correct only under the spec's per-module correction. One-sided BH over the pooled 9,337 keeps none (smallest BH p 0.466). The single survivor appears within M1b's 736-row grid (BH p 0.049) and disappears when the grids are pooled, as Appendix E says. The parenthetical makes the pooled reading the natural one. | `M7_multiple_testing_summary.csv`; M7 FINDINGS s3; `adopted_checks.md` check 3 | Low |

## Recomputed from CSVs for this audit

- **tab_time, every cell.**
  - Rules and always-short: `M2_christhian_tests_strategy_grid.csv` (L5, corrected, FF3 hedge, team costs, E:FF3).
  - GB column: `M3_alpha_beta_exposures.csv` (GB, FF3).
  - n: 402 from 1993-02; Continuous raw 403 from 1993-01; GB 679.
  - Note b: classical OLS |t| of 1.41 and 1.37 (`M3_alpha_beta_gb_short_window_alpha.csv`).
- **Smallest post-2010 p (l.186).** 0.053 over 84 regressions (7 models x 2 baselines x 6 rules): corrected Pure 6m, FF5, 1.58%, t 1.95. No positive alpha has t > 2 outside the COVID and validation windows for the six rules, always-short or GB.
- **GB loadings (l.179).**
  - FF3 HML: -0.233 (t -4.63) full sample; -0.298 (t -5.74) post-2010.
  - FF5: HML -0.112 (t -1.90), RMW -0.148 (t -1.90), CMA -0.249 (t -2.80).
  - Write-up windows: 1970 to 2022-07 and 2010-01 to 2022-07 (team notebook l.114 and l.115; validation HML -0.351).
- **Risk statistics (l.136).**
  - Original 6m post-2010: vol 4.26%, IR 0.279, max DD -14.4%; validation IR 0.509; holdout IR -0.432.
  - Always-short: vol 5.19%, IR 0.202, max DD -17.0%.
- **"Before costs as well as after" (l.46).** Every rule loses before costs in the holdout, under both baselines. Corrected gross returns run from -2.12% to -0.36%; team baseline from -3.36% to -0.34%. All 28 zero-cost alphas are negative (maximum -0.39%).
- **Holdout intervals and power.**
  - Pure 6m: -1.97% +/- 2.015 x 1.51 gives -5.0% to +1.1% (fc04 lo/hi -5.02%/+1.08%).
  - COVID edge: 1.84% +/- 2.086 x 2.11 gives -2.6% to +6.2%.
  - Frozen test: SE 0.683%, t bar 1.37%, MDE80 1.94%, power at 1% 0.30.
- **pi-scaled COVID edge (l.213).** Corrected Original 3m, `M3_alpha_beta_ln_vs_benchmark.csv`: pi 0.390, mean D 5.37% (t 2.35); in-window alpha 2.98% (t 1.67, p 0.113).
- **tab_m1_cross.** Every row matches `M1_signal_audit_crossings_vix_summary.csv`. Shift bounds: 1/382 < 0.003, 1/176 < 0.006, 1/128 < 0.008.
- **Figure 1 caption.** The MCCC 12-month mean runs 1.22 (2021-12) to 1.31 to 1.47 (2022 to 2024) to 1.82 (2025-06); CPU 0.92 to 1.92. The EMV_env 12-month mean was between -0.94 and -0.51 over 2022-2024.
- **Optimizer book (H1).** Holdout net +2.29%, alpha -0.34% (t -0.15); gross holdout alpha -0.04%.
- **Pre-registration hashes, recomputed on disk.**
  - PREREGISTRATION.md: e926c3ae...0b51 (saved 03:30:46 PDT).
  - adopted_checks.md: 15fdce70...8e70b. The file was saved at 10:43 PDT, after M7's last run at 09:15 PDT, so no M7 run has yet hashed the saved file; the recorded and on-disk values agree.
  - optimizer.py and m5lib.py also match.
- **Code listings.** Every `lstinputlisting` range in Appendix D starts and ends on the named function: team_pipeline, M8 run.py (re-created at 06:05), m3lib, m6lib, optimizer and test_team_pipeline.
- **Exchange provenance.**
  - All four quoted prompt lines occur verbatim in the prompt files.
  - Prompt word counts: 993, 997, 997, 795.
  - Reply word counts: 1,772 (1,609), 1,716 and 1,340 without Markdown.
  - ChatGPT's script has 985 lines.
- **Arithmetic checks.**
  - 71% = 4.54 / 6.38.
  - 86% = (2.74 + 1.71 + 1.30) / 6.70.
  - -1.84 = -0.24 - 1.14 - 0.46.
  - 758 = 439 + 319.
  - 36.5 s = 28.6 + 7.9.
  - Ledgers: 23,923 + 481 = 24,404; primaries 155 + 1 = 156.
  - Census L + E = 14,261 of 23,923 (59.6%).

## Verified without issue (selection)

- **Section 1.1 and the team write-up.**
  - 2.45% and 2.59% (t 2.23 and 2.46).
  - COVID 5.94% net; alpha 6.03% (t 3.21).
  - Holdout losses of 2.1% to 3.8%.
  - 0.07% to 0.73%; 2 of 32 becomes 0 of 32 (smallest Holm p 0.119).
- **M1.**
  - 500 of 500 months; 12 of 441 and 39 of 59 zeros (Fisher p 1.3e-32); 31 of 48 holdout months.
  - R2 0.169 (p 8.8e-12), slope 0.43 (t 5.07); VIX t -0.35 (full) and -2.51 (validation).
  - Correlations -0.0004 (p 0.996) and 0.123 (Holm 0.074); share against CPU 0.03.
  - Crossings in high overall-EMV months: 88% against 64.5% (p 0.0006).
  - Q6a t -0.49 and -1.23; Holm 0.62 and 0.43.
- **M1b.**
  - 4 of 6 against 0 of 12 validation alphas with t >= 1.96; means 1.45%, 1.07%, 0.88% and 0.34%.
  - Largest CPU holdout alpha +0.36% (t 0.37); holdout windows of 48, 36 and 39 months.
  - COVID: 6.38 (3.62), 4.54 (1.96), +1.84 (0.87), +0.42 ex-crash; 4 of 6 placebo reproductions.
  - App E: paired t up to 3.22, Holm 0.051, +1.39% (0.87), +4.08% (2.34, p 0.030); CPU +1.90% (1.02).
- **M2.**
  - COMEQ correlation 0.66; COMEQ alpha -0.89% (t -0.24); COMEQ loading -0.18 (t -8.70).
  - Brown side -0.437; Steel and Ships -0.239; residual HML -0.015 to -0.053.
  - Turnover 2.4 to 5.8 times; drag at most 0.63%.
  - Break-evens 40 to 100 bp, 211 bp, 19 to 50 bp; 28 zero-cost runs, highest -0.39%.
  - 8,091 tests; 368 positive and 531 negative with p < 0.05; Holm 0.397 and 0.017.
  - Smoke test four minutes before the docstring.
- **M3.**
  - BOND 0.132 (Holm 0.019) and 0.088 (Holm 0.549); smallest Holm p 0.155 for the 12 alphas.
  - Timing term -0.57% to -1.07%, 4 of 6 survive Holm; always-short -1.35%.
  - Attribution: -0.24, -1.14 and 0.46; COVID leakage 4.76 of 6.87, residual 2.21 (t 1.27).
  - BOND correlations 0.991 and 0.987; 2022 return -15.0% against -17.8%.
  - 45 of 48 BH survivors are HML; TM t 3.24.
- **M4.**
  - 6,051x and 33x; Spearman 0.700; ranks 2nd and 3rd of 41, 20th and 31st of 49.
  - 14 to 47x and 1.9 to 6.0x.
  - 4.7% (t 1.52, p 0.129); smallest Holm p 0.471; 4.5% (t 2.58); 7 of 9 and 5 of 9.
  - EPA minus team: 8.2% (t 2.84), Holm 0.071 and 0.178.
- **M5.**
  - 8.52% net; alphas 1.74% (t 1.09) and 1.86% (t 0.71); UMD beta 0.99.
  - 11.6% WACI cut, IR change +0.010, Holm 0.823; 60% WACI cut, -0.005 [-0.110, +0.096].
  - Optimizer 2.17% (t 3.07); COVID 15.80% (t 3.18, OLS t 1.58, p 0.132).
- **M6.** 758 refits; R2 0.000%; +0.84% (t 1.17), p 0.24 and 0.65; DGS10 p 0.018 and 0.020, q 0.34.
- **M7.**
  - 23,923 module rows; 4,184 hits; 1,624 alphas (783 positive, 841 negative).
  - 73 tests after 8 duplicates; best one-sided p 0.030; Sidak 1.69; Holm 1.00; BH 0.72.
  - D 15 of 73; X 33 of 170; L 1,452 of 4,850; E 1,636 of 9,411; 4 Holm survivors among the 155 primaries.
  - Search families: 58 and 89 members; 15 survivors; best t 3.34 against a max-t bar of 2.68; Nyholt 42.4 and 74.8.
  - DSR 0.559 and 0.362 (0.897 most lenient); RW 0.017 and 0.199; EPA RW 0.058.
  - Holdout readings; frozen run 1.95% (t 2.45, p 0.007, Holm 0.015); halves 1.71% (1.44) and 0.90% (0.83).
  - 1.99% (2.31) and 3.12% (2.18); S2 -0.006 [-0.194, +0.228]; timestamps 08:49:39 and 08:53:41.
- **M8.**
  - Alpha -0.18% (t -0.27); shuffle median -0.22%, p 0.478; 10 episodes; 2 of 5 drop-one alphas positive.
  - Team signal: +0.69% (t 1.00), one-sided p 0.159 and 0.128, 5 of 5 positive.
  - Dry run -0.12% (t -0.19); 142 of 190 months in position; 128 of 128 numbers matched.
  - Timeline: 03:29:54, 03:30:46, 03:35:43, 03:36:35, 03:37:46, 03:41, 06:05:07; 32 choices; 192 pre-2010 months.
- **Exchanges.**
  - 6 of 52 (rows 13, 22, 26, 32, 33 and 36) and 8 of 72; rate beta t 0.05.
  - 3.3e-13; ChatGPT's -0.19% (t -0.25); 4 of 6 and 7 of 8 bugs caught; 13 of 100 null seeds.
  - +1.07% (t 0.79) and +0.36% (t 0.70) match `fc04_results.json`.
- **Literature.** PST 2022 (-4 bp, HML -0.26), PST 2021 (unexpected concern shocks; a known spike carries no positive expected GMB), EIJP (no BH survivor) and BK against Zhang on the sign: all supported by `lit_digest.md`.

## Previous audit (08:47 draft): status

Fixed in this draft: H1, H2, H3, M1, M3, M4, M5, M6, M7, M8, M9, M10, M11, M12 and L1 to L16 (L15 excepted). In particular:
- the "no positive holdout alpha" wording;
- both COVID benchmarks, now reported;
- the PST 2021 reading;
- turnover of 2.4 to 5.8;
- "no post-2010 alpha";
- the shift-p bounds;
- the 86% source;
- the 5.94% net and 6.03% alpha;
- the t-11 to t-1 signal;
- the loadings' significance;
- the ex post attribution label;
- the write-up HML windows;
- the VIX paired test.

Still open, in weaker form:
- prior M13 (provenance) is now M2;
- prior M2 (t(n-k) everywhere) is now L1, the summary only;
- prior L15 (citations) is now L17.

## Actions without a text change

1. **Verifier rerun.** Have an independent verifier re-run the [fc04] numbers the body uses before submission: six entries and 32 months; PC1 90%; Steel -1.37 of -1.38; +1.07% (t 0.79); +0.36% (t 0.70). If no rerun is possible, the M2 text fix discloses them.
2. **Citations.** Check the 14 bibliography entries in L17 against the originals, or add them to `lit_digest.md` section 12.
3. **M7 hash check.** Rerun `modules/M7_robustness_ledger/run.py` once, so that a run hashes the saved `adopted_checks.md`. Appendix E says every run re-hashes it, but no run has happened since the file was saved; this audit's SHA-256 matches the recorded value.
4. **Rebuild caveat.** Fixes L13 to L16 touch text that `report/build_transcripts.py` generates from `exchange/*/evaluation.md` and its `BOXES`. Edit those sources as well, or a rebuild will undo the fixes.
5. **Teammate's name.** `\CR` prints "Cristhian" (HW1 author list); the WhatsApp log and module names use "Christhian". Confirm the spelling (hw_context.md item 3).
