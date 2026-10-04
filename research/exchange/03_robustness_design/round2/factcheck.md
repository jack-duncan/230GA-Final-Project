# Fact-check: exchange 03 (robustness design), Claude as the committee skeptic

Independent re-check, 2026-09-26 (10:45 PDT). Inputs: `prompt.md` and `claude_response.md` in this folder, identical to the chat transcript. Script: `checks/fc03b_verify.py`, run with `cd /home/hashim/projects/GA/project/research && uv run python exchange/03_robustness_design/checks/fc03b_verify.py` (about 1 minute). Outputs go to `checks/out_b/`: `moments.csv`, `dsr_table.csv`, `regressions.csv`, `ar_dsr.csv`, `t_needed.csv`, `team_holdout.csv`, `six_variants_corr.csv`, `power_pre1970.csv`, `epa_mccc.csv`, `industry_first_month.csv` and `fc03b_results.json`. Other sources: the module FINDINGS files and tables in `outputs/tables/`, the M7 outputs, `logs/lit_digest.md` and `logs/replication.md`.

**Chronology.** Claude answered before M7 existed. M7, which implements `adopted_checks.md`, has since run several of the checks the reply proposes, including the one-shot pre-1970 run of the optimizer book (first run 2026-09-26 15:53 UTC, hash-verified). The coverage tables therefore have two status columns: what the modules had done when the prompt was sent (M1 to M6 and M8), and what M7 has done since. My own script computes no pre-1970 strategy return. Its only pre-1970 quantities are data-availability counts. Every pre-1970 result quoted below is read from M7's saved outputs.

**Notation.** "Book" is the M5 Grinold-Kahn optimizer book (convention X, unconstrained, 10 bp; series `X_unc`). "EW book" is M5's pre-registered equal-weight 8-long, 8-short momentum book. "EPA spread" is M4's EPA 5v5 Green-minus-Brown. "Hold rules" are the team's four Short-Brown hold variants, and "six rules" adds the two continuous variants. t-statistics are Newey-West with 6 lags unless stated. "Val" is validation (2010-01 to 2022-07) and "HO" is the holdout (2022-08 to 2026-07). Verdicts: C = correct, P = partly correct, W = wrong, U = unverifiable.

**Literature.** `lit_digest.md` covers Pástor, Stambaugh and Taylor (2022) but none of the statistics papers the reply cites. I checked Holm (1979), Benjamini and Hochberg (1995), Benjamini and Yekutieli (2001), Romano and Wolf (2005), White (2000), Hansen (2005), Nyholt (2004), Li and Ji (2005), Bailey and López de Prado (2014), López de Prado and Lewis (2019), Lo (2002) and Daniel and Moskowitz (2016) from general knowledge of the published papers, and I say so where it matters. Every citation in the reply names a real paper in the stated journal and year, and each attributed claim matches what that paper does.

## Summary

I extracted 93 checkable claims and recommendations: **67 correct, 15 partly correct, 11 wrong, 0 unverifiable.** The statistics are sound and the arithmetic is right. The errors concern our own strategies, and several of them trace back to the prompt.

1. **The formulas and hand arithmetic check out.**
   - The PSR, DSR and SR0 formulas match Bailey and López de Prado (2014): monthly Sharpe ratio, raw kurtosis in (γ4 - 1)/4, and the expected-maximum term with the Euler-Mascheroni constant.
   - The BY constant is right: the harmonic sum is 9.576 at m = 8,091, against ln m + 0.58 = 9.576. The Nyholt formula is printed correctly.
   - All ten cells of its DSR table reproduce to within 0.005 (largest gap 0.0047, `dsr_table.csv`).
   - Its appraisal ratio (0.41) and its break-even count of "about 7" trials reproduce. The exact FF5+UMD appraisal ratio is 0.400, and it clears DSR 0.95 for N of 6 or fewer (7 with Claude's 0.408).
2. **Two facts about the lead candidate are wrong, and both came from the prompt.**
   - The UMD beta of 0.99 belongs to the EW book (recomputed 0.987, t 30.5). The book's UMD beta is 0.273 (t 15.2, R2 0.39). The prompt printed 0.99 beside the optimizer's numbers without naming the EW book.
   - The book's carbon constraint does not use "2022 intensities". It uses the team's undated `emissions_ff_industry.csv` (M5 section 3). The 2022 EPA factors are used only by M4's EPA spread, and the prompt's "2022 sort applied back to 1970" referred to that spread.
3. **One statistical claim is wrong.** Romano-Wolf is not in general stricter than BH.
   - When one p-value stands alone, BH needs it to be at most q/m, which is 6.2e-6 on the 8,091 grid. A max-t stepdown uses the correlation between tests and can reject when BH rejects nothing.
   - The grid's best positive cell has one-sided p 0.000176 (a 24-month COVID alpha, t 4.30). A max-t test would flag it if the grid's effective number of independent tests were below about 285.
   - That cell is a known small-sample COVID artefact (M1b, M3), so the conclusion "nothing implementable is rescued" very likely survives. The stated reason does not. The test cannot be run as things stand, because M2 did not save its grid's return series (M7 section 4).
4. **The frozen pre-1970 test was mis-specified, and its pass bar could not be met as written.**
   - The optimizer needs 60 months of returns for its covariance and residual volatility, so the window is 1931-07 to 1969-12 (462 months), not 1927-07. Only 34 to 37 of the book's 41 industries exist before 1963-07.
   - Power at a true 2% alpha is 0.61 on the feasible window at post-1970 residual volatility (normal approximation; M7 reports 0.62). Claude's two-thirds is right for its own, infeasible window (0.65).
   - The pass bar's "project-wide DSR on the appraisal ratio of at least 0.95" clause is decided by post-1970 data, and Claude's own arithmetic already fails it for more than about 7 trials.
   - M7 has since run the test: FF3+UMD alpha 1.95%, t 2.45, halves 1.71% and 0.90%. It passes the first two clauses and fails the DSR clause (0.559). By Claude's own bar, the "one check" did not overturn "Do not implement".
5. **The "low power" objection overreaches for the attention thesis.** With p-values from t(44), as the prompt specified, all six rules reject a +2% holdout alpha at one-sided p of 0.0016 or less. Three of the four hold rules have 90% intervals wholly below zero; Original 6m's upper bound is +0.03%. The low-power point is right only for the book (holdout SE 2.27%, 90% interval -4.16% to +3.48%).
6. **Its equivalence test would misread the strongest evidence.** A TOST with a ±2% margin fails all four hold rules because their intervals are too negative (Original 3m: -7.13% to -0.94%). Under Claude's reading, that fail means "insufficient evidence". The question for implementation is one-sided (non-inferiority against a worthwhile alpha), which is what M7 check 6 adopted.
7. **Its EPA test and its reading of a fail are backwards on our data, and the result is knife-edge.** Adding a same-month MCCC shock raises the post-2010 alpha, because the shock loading is negative: the spread lost when concern rose, the opposite of the Pástor, Stambaugh and Taylor (2022) channel.
   - With M1's expanding-window AR(1) shock, the alpha is 6.66% (t 2.13; M7 check 9).
   - With PST's own trailing-36-month AR(1), which I computed, the alpha is 5.88% (t 1.85) and the loading is -0.42% per s.d. (t -1.89).
   - So whether the spread "passes" depends on how the shock is built.
8. **Four smaller factual errors.**
   - Loadings are 32% of the 4,184 nominal hits, not "most". Alphas are the largest group at 39% (783 positive, 841 negative).
   - Costs above 10 bp were tested: M2 at 25 bp; M5 at 25 bp for the EW book (FF5+UMD alpha -0.14%) and for the book (IR 0.49).
   - "The BOND control helps" contradicts M3: adding BOND and UMD leaves every holdout alpha negative.
   - "Residual volatility before the war is probably higher" ignores the book's 5% ex-ante tracking target. The realized pre-1970 residual volatility was 5.14%, against 5.44% after 1970 (M7).
9. **It broke the word limit.** The reply has 1,716 words with its two tables and 1,481 without them, against "under 1,500".

## Claims table

Numbers are recomputed by `fc03b_verify.py` unless another source is named.

### Bottom line

| # | Claim (quoted or condensed) | Verdict | Evidence | Source |
|---|---|---|---|---|
| B1 | No candidate reaches "implement" on the current evidence | C | Every pre-specified alpha fails: M4 t 1.52; M5 P1 t 1.09, P2 t 0.71; M8 t -0.27. The book's alpha is exploratory, and its HO alpha is -0.34%. M7's verdict map, fixed in advance, agrees. | M4, M5, M8, M7 section 10 |
| B2 | The attention thesis is finished (items 1-3, 7, 8) | C | The signal is volatility news (M1). MCCC and CPU are null (M1b: smallest Holm p 1.00). The frozen 1994-2009 rule FAILs (M8). Ridge timing collapses to the historical mean (M6). All six rules lose in HO. | M1, M1b, M6, M8 |
| B3 | Two strategies from outside the thesis deserve scrutiny, and both fail today | C | Book: exploratory alpha 2.17% (t 3.07), HO -0.34%. EPA: pre-specified alpha 4.7% (t 1.52). | M5, M4 |
| B4 | Only one of them still has an unseen sample | P | True for the book when the prompt was written: M5 starts in 1970-01. The EPA spread cannot even be formed before 1965-07, because its Green leg holds Softw (first return 1965-07). The window was unseen by this project, not by the field. M7 has now spent it. | `industry_first_month.csv`, M7 section 7 |

### 1. Families

| # | Claim | Verdict | Evidence | Source |
|---|---|---|---|---|
| F1 | Group tests by the decision they could change, not by module | C | Sound. It is the organising rule M7 adopted (families F, P, D, R, S, X, L, E). | M7 section 1 |
| F2 | The confirmatory family holds each candidate's pre-specified alpha test, one-sided, because only a positive alpha leads to implementation | C | Sound. Only a positive alpha can move the verdict. M7 used one-sided p in families P, R and F. | M7 sections 1-2 |
| F3 | Romano and Wolf (2005, Econometrica): a bootstrap stepdown controls the FWER using the dependence between tests, so it has more power than Holm | C | The paper's StepM controls the FWER asymptotically. It gains power over Bonferroni-type stepdowns because it uses the joint distribution of the tests. (General knowledge.) | Romano and Wolf (2005) |
| F4 | Use a stationary block bootstrap that resamples the same months for every series. Report Holm alongside, since Holm is valid under any dependence | C | Joint resampling preserves the cross-correlation that max-t needs. Holm (1979) needs no dependence assumption. M7 used a stationary bootstrap (mean block 12, B = 5,000) with months resampled jointly. | M7 section 4 |
| F5 | Only item 7 can be shown to have been pre-registered | C | True when the prompt was written. M5's primaries are "fixed before any result was computed" by its own account, but there is no hash. M7 check 7 is now a second hash-verified test. | M8, M5 section 2, M7 section 0 |
| F6 | Treat all 155 "primary" labels as one project-level family | P | The reason is valid: a committee cannot audit self-given labels. But the 155 mix alpha tests with Fisher, Wald, correlation and loading tests, which contradicts F1. M7 ran this family as a reference: 4 Holm survivors, none an alpha test (Fisher test on zero months, p 1.3e-32; a joint Wald test; two HML loadings). | M7 section 2 |
| F7 | Cristhian's 8,091 alphas are a sensitivity analysis and belong in an FDR family | C | Sound. They are near-duplicate variants of one rule, not separate hypotheses that could each be implemented. | M2 |
| F8 | BH controls the FDR under positive dependence; Benjamini and Yekutieli (2001) prove it for PRDS statistics, and near-duplicate one-sided alphas are plausibly PRDS | C | BY (2001) prove that BH controls the FDR under PRDS on the true nulls. One-sided tests on jointly normal statistics with non-negative correlations are PRDS. "Plausibly" is the right hedge, because the grid's series were never saved. BH (1995) itself assumed independence. (General knowledge.) | BY (2001) |
| F9 | BY holds under any dependence at a cost of about ln m + 0.58, about 9.6 for m = 8,091 | C | Harmonic sum 9.5758; ln m + 0.5772 = 9.5757. M7 uses 9.584 at m = 8,161. | `fc03b_results.json` |
| F10 | BH already finds zero positive survivors in the grid | C | M2: 0 positive survivors under Holm or BH. M7 R-M2: smallest one-sided BH p 0.475. | M2, M7 section 3 |
| F11 | BY is stricter than BH | C | The BY thresholds are BH's divided by c(m), so BY rejects a subset of what BH rejects. | BY (2001) |
| F12 | Romano-Wolf is stricter than BH, so it will not rescue anything | W | Not true in general (summary point 3). BH's lone-rejection threshold is 6.2e-6. The grid's best positive one-sided p is 0.000176 (`strat\|L5\|corr\|FF3\|u5\|Pure 3m\|covid\|E:FF3\|alpha`, t 4.30, n 24), and a max-t test would reject it if the effective number of tests were below about 285 (Šidák). It has not been run: the M2 series are not saved. | `fc03b_results.json` (RM2_best), M7 section 4 |
| F13 | Report the grid as a distribution: share of positive alphas and median t | C | Sound, and done in M7 check 3: 54.0% positive with median t 0.13 overall; 88.9% positive with median t 1.14 in validation; 2.7% positive with median t -1.32 in HO. | M7 section 3 |
| F14 | Exploratory tests (15,485) belong in no family; nothing can be confirmed on the data that produced it | C | Sound. The count matches the census (15,485 exploratory labels). | M7 section 1 |
| F15 | The book's full-sample alpha sits in the exploratory group | C | M5 labels it exploratory. Its BH p of 0.027 is within M5's exploratory family. | M5 section 7 |
| F16 | Exclude loadings, descriptive statistics and placebos; report loadings with confidence intervals; placebos calibrate the null | C | Sound. The example "UMD beta 0.99" is the EW book's loading (see D8). | M5 section 5 |
| F17 | "Most of the roughly 4,200 nominal hits are loadings" | W | 4,184 hits: loadings 1,325 (31.7%); alphas 1,624 (38.8%; 783 positive, 841 negative); means 561; other 536; beta-timing 138. A crude regex classifier I wrote independently gives 30.5% loading-like. | M7_all_tests.csv (type column), `fc03b_results.json` |
| F18 | Pre-specify one composite statistic, for example the equal-weight average of the six variants' alphas: one test, with more power | P | It is one test. "More power" holds against a multiplicity-adjusted family only when the effects are similar. The composite's Val FF3 alpha is 1.44% (t 2.06), below the two 6-month rules (t 2.23 and 2.46); its HO alpha is -2.09% (t -2.46). Defining it now, after both windows have been seen, is post hoc. | `team_holdout.csv` |
| F19 | A max-t bootstrap handles the correlation automatically | C | Correct by construction. | Romano and Wolf (2005) |
| F20 | Nyholt (2004): M_eff = 1 + (M - 1)(1 - Var(λ)/M), with λ the eigenvalues of the correlation matrix | C | The formula is as published. It is an approximation; Li and Ji (2005) give another. On our data: six team variants 2.98 (Li-Ji 3; pairwise correlations 0.61 to 0.98); 24 optimizer paths 6.38 (Li-Ji 4); M7's search families 42.4 and 74.8 (Li-Ji 14 and 27). | `six_variants_corr.csv`, `fc03b_results.json`, M7 section 4 |
| F21 | White's Reality Check (2000, Econometrica) and Hansen's SPA (2005, JBES) test whether the best strategy beats the benchmark after allowing for the search | C | Both test the null that no strategy in the set beats the benchmark. (General knowledge.) | White (2000), Hansen (2005) |
| F22 | SPA is less distorted by poor, irrelevant alternatives | C | This is Hansen's main point: studentization and a data-dependent recentring stop poor models from making the test conservative. (General knowledge.) | Hansen (2005) |

### 2. Deflated Sharpe

| # | Claim | Verdict | Evidence | Source |
|---|---|---|---|---|
| D1 | DSR = PSR(SR0), with PSR(SR0) = Φ[(SR - SR0)√(T - 1)/√(1 - γ3 SR + ((γ4 - 1)/4) SR²)] (Bailey and López de Prado 2014, JPM) | C | Matches the paper. (General knowledge.) | BLdP (2014) |
| D2 | SR0 = √V · [(1 - γ)Φ⁻¹(1 - 1/N) + γΦ⁻¹(1 - 1/(Ne))] | C | Matches the paper. The approximation is close to the exact E[max] for N of 7 or more (1.387 against 1.352 at N = 7) and rough at N = 2 (0.520 against 0.564). | `fc03b_results.json` (emax) |
| D3 | SR is monthly, not annualized, and T is in months | C | Mixing units is the classic error: an annualized SR with monthly T gives PSR 1.000 for all three series. | `dsr_table.csv` |
| D4 | Inputs include skewness and raw (not excess) kurtosis | C | The (γ4 - 1)/4 term needs raw kurtosis; a normal distribution gives 0.5. | BLdP (2014) |
| D5 | N is the effective number of independent trials; V is the variance of the trials' Sharpe ratios in monthly units; γ ≈ 0.5772 | C | Correct. | BLdP (2014) |
| D6 | Pass bar DSR ≥ 0.95 | C | The conventional threshold, used in the paper's example. It is a choice, not a rule. | BLdP (2014) |
| D7 | Deflate three ratios: the book's Sharpe, the book's appraisal ratio and the EPA spread's post-2010 Sharpe | C | A sound choice. The appraisal ratio is the right object for an alpha claim. | |
| D8 | Reason for the appraisal ratio: "with a UMD beta of 0.99 the raw Sharpe is mostly momentum" | W | Wrong premise: the book's UMD beta is 0.273 (t 15.2, R2 0.39); 0.99 is the EW book (0.987). The conclusion still holds for another reason: the book's FF5 alpha without UMD is 4.53% (t 5.21) and falls to 2.17% with UMD, so about half of it is UMD exposure. | `regressions.csv` |
| D9 | A trial is every return series that could have been presented as "the strategy", including variants, grids, lookbacks, bounds, optimizer settings and sample windows; placebos and loadings are not trials | C | Sound. It follows BLdP's definition. | |
| D10 | Estimate the effective number of trials by clustering the return series (López de Prado and Lewis 2019, Quantitative Finance) | C | That paper clusters strategy trials to estimate the number of effectively independent trials and the cross-cluster Sharpe variance. (General knowledge.) M7 used Nyholt N with round(N) average-linkage clusters. | M7 section 5 |
| D11 | V is the variance of the Sharpe ratios across clusters; setting it to the null value 1/(T - 1) gives a lower bound on SR0 | C | 1/(T - 1) is the sampling variance of a monthly SR under a zero true SR, so it is a sensible floor for independent clusters. Correlated trials can show less cross-trial variance, which is why N must be effective. M7 used V = max(1/(T - 1), V_cl). | M7 section 5 |
| D12 | PSR assumes independent returns | C | The SR standard error behind PSR assumes iid, possibly non-normal, returns. | BLdP (2014) |
| D13 | "Your Newey-West t-statistics are below their iid equivalents (EPA: 1.72 against about 2.1)" | P | Right for the EPA spread (iid t 2.12, NW 1.72) and for the book after 2010 (2.83 against 2.54). Not general: the book's full-sample mean is 4.18 iid against 4.14 NW, and its alpha t is higher with NW (3.07) than with OLS (2.85). | `moments.csv`, `regressions.csv` |
| D14 | Correct with Lo (2002, FAJ), which adjusts annualized Sharpe ratios and their standard errors for serial correlation | C | Correct. (General knowledge.) Lo-adjusted annual Sharpe: EPA post-2010 0.418 (against 0.520); book full 0.553 (0.555); book post-2010 0.632 (0.696). | `moments.csv` |
| D15 | Table, book full (0.555, T = 679): PSR(0) ≈ 1.00; DSR 0.99, 0.94, 0.81 at N = 10, 100, 1,000 | C | 1.0000; 0.9939, 0.9432, 0.8116. | `dsr_table.csv` |
| D16 | Table, book post-2010 (0.70, T = 199): PSR(0) ≈ 0.998; DSR 0.90, 0.62, 0.34 | C | 0.9981; 0.9013, 0.6247, 0.3378. | `dsr_table.csv` |
| D17 | Table, EPA post-2010 (0.52, T = 199): PSR(0) ≈ 0.98; DSR at N = 10 ≈ 0.71 | C | 0.9841; 0.7076. The raw Sharpe passes 0.95 only at N = 1. | `dsr_table.csv` |
| D18 | EPA: DSR about 0.94 to 0.95 at N = 2, before the autocorrelation correction, so it fails | C | 0.947 with BLdP's approximation, 0.942 with the exact E[max]. Lo's adjustment lowers it further. | `dsr_table.csv` |
| D19 | Book appraisal ratio ≈ t/√years ≈ 0.41 | C | 3.07/√56.6 = 0.408. The exact FF5+UMD appraisal ratio (ddof 7) is 0.400. | `regressions.csv` |
| D20 | It clears DSR 0.95 only if the effective number of trials is at most about 7 (guess) | C | N of 7 or fewer at 0.408; N of 6 or fewer at 0.400 with the residual moments (skew 0.04, kurtosis 3.41); post-2010, N of 2 or fewer. | `ar_dsr.csv` |
| D21 | The project almost certainly has more trials, so the full-sample alpha does not survive deflation | C | M7: Nyholt N 42 gives DSR 0.559. The most lenient case (Li-Ji N 14, V at its floor) gives 0.897. | M7 section 5 |

Moment inputs. The prompt's moments reproduce: Sharpe 0.5553, 0.6961 and 0.5204. It quoted population kurtosis (5.77, 3.66, 4.77), where the unbiased values are 5.80, 3.71 and 4.84. The difference moves no DSR cell by more than 0.007.

### 3. Candidates

| # | Claim | Verdict | Evidence | Source |
|---|---|---|---|---|
| K1 | The book has the strongest statistics, but its alpha was exploratory | C | FF5+UMD alpha 2.17% (t 3.07), IR 0.555; labelled exploratory. | M5 section 7 |
| K2 | HO alpha -0.34% with SE about 2.3% (backed out from the t) | C | SE 2.27%; 90% interval -4.16% to +3.48% (t(41)). | `fc03b_results.json` (book_holdout) |
| K3 | Too short to confirm the alpha or to kill it | C | The minimum alpha detectable with 80% power is 5.75%. | same; M7 section 6 |
| K4 | HO rank IC 0.030 is about one SE below 0.054; SE guessed at about 0.02 | P | HO rank IC 0.0303 with NW t 1.14, so SE = 0.027. The gap to 0.054 is 0.9 SE. The guess is low by about a quarter; the conclusion stands. The comparison ignores that the full-sample IC contains the holdout. | M5 `realized_ic` |
| K5 | "The signal has not clearly died" | P | Nor is it clearly alive: the HO IC is not different from zero (p 0.25), and the last 18 months give -0.005. | M5 `realized_ic` |
| K6 | Sample 1927-07 to 1969-12, because FF49 starts in 1926-07 and the signal needs 12 months | W | The book needs 60 months for its Ledoit-Wolf covariance and residual volatility (M5 method), so the first return month is 1931-07 (462 months). 34 of the 41 covered industries exist in 1926-07 and 37 from 1930-07 to 1963-06. Soda and Guns start in 1963-07, Softw in 1965-07 and Hlth in 1969-07. M7 ran 1931-07 to 1969-12 with 34 to 39 eligible industries. | `industry_first_month.csv`, M7 section 7 |
| K7 | "Nothing has touched this period" | P | True for the book when written: M5 starts in 1970-01. But M6 saved an unused hedged Brown residual from 1931-07 (`M6_factor_timing_team_brown_residual.csv`), industry momentum and UMD have been studied since the 1920s, and M7 has now spent the window. | M6 run.py section 3c; M7 section 7 |
| K8 | Freeze the code, IC 0.05, 5% tracking error, b = -1, 10 bp and the missing-data rule; hash and timestamp; run once | C | Sound. M7 did this for the unconstrained book, with b = -1 as a secondary row. | M7 section 0 |
| K9 | Benchmark FF3+UMD, because FF5 starts in 1963-07 | C | FF3 starts in 1926-07, UMD in 1927-01 (raw Ken French file) and FF5 in 1963-07. | data/raw files |
| K10 | Secondary: FF5+UMD on 1963-07 to 1969-12 | C | Feasible: 78 months. M7 S1: 3.26%, t 1.76. Uninformative by design. | M7 section 7 |
| K11 | "The carbon ranks use 2022 intensities" | W | The book uses the team's undated file (M5 section 3). The 2022 EPA factors are used only by the EPA spread (M4). | M5, M4 |
| K12 | That is acceptable because carbon is a constraint, not the source of return | P | Partly. Under convention X the same file also defines the 41-industry universe, so even the unconstrained book depends on it. Before 1970 the b = -1 bound binds in 77.9% of months and is infeasible in 38 (M7 S2), so the constraint shapes the constrained book's holdings. | M5 section 4, M7 S2 |
| K13 | Statistics: one-sided NW(6) t on alpha, and the alpha of the constrained book minus the unconstrained book | C | Sound. | |
| K14 | Pass bar: alpha t ≥ 2.0; positive before and after 1948; no significant carbon cost; project-wide DSR on the appraisal ratio ≥ 0.95 | P | The first two clauses are sound. "No significant carbon cost" is passed by low power (M7 S2 interval -0.194 to +0.228). The DSR clause is decided by post-1970 data and already failed (Claude's own ≤ 7 trials; M7 0.559), so the bar could not be met whatever the pre-1970 result. | M7 sections 5, 7 |
| K15 | Power (guess): residual volatility about 5%, SE about 0.8% over 43 years; a true 2% alpha clears t = 2.0 about two-thirds of the time | C | Post-1970 FF3+UMD residual volatility 5.44%. Over Claude's 510 months: SE 0.83%, power 0.65. Over the feasible 462 months: SE 0.88%, power 0.61 (M7: 0.62). | `power_pre1970.csv` |
| K16 | Residual volatility before the war is probably higher, which lowers power | W | The book targets 5% ex-ante tracking volatility, so realized residual volatility is held down by construction. Realized: 5.14% for 1931-1969 against 5.44% after 1970. | M5 section 4, M7 section 7 |
| K17 | EPA pre-specified alpha t 1.52 | C | 4.72% (t 1.52), n 199. | M4 primary test |
| K18 | EPA full-sample alpha comes from CMA and UMD loadings and a 2022 sort applied back to 1970 | C | CMA -0.345 (t -3.04), UMD -0.096 (t -2.02); raw mean 2.5% (t 1.40); static 2022 EPA ranking. | M4 section 4 |
| K19 | Pástor, Stambaugh and Taylor (2022, JFE) attribute green outperformance in 2012-2020 to unexpected rises in climate concern, not higher expected returns | C | Nov 2012 to Dec 2020; the shock-purged mean is about -4 bp a month (Table 4, p.415). They add earnings shocks as a second driver. | lit_digest section 3 |
| K20 | Test: post-2010 FF5+UMD alpha with MCCC innovations as a control; MCCC is an existing series, not a new signal | C | Feasible and compliant with the prompt's rules. Run in M7 check 9 and here (K21). | M7 section 9 |
| K21 | EPA pass bar: one-sided alpha t ≥ 2.0 and DSR ≥ 0.95 | P | The DSR clause cannot be met: raw-Sharpe DSR passes only at N = 1 (D17), and the appraisal-ratio PSR(0) is 0.945 even as a single trial (M7). The alpha clause is knife-edge and depends on the shock construction: 2.13 (expanding AR(1), M7) against 1.85 (PST trailing 36-month AR(1), here). Either way the shock loads negatively (-0.52%, t -2.21; -0.42%, t -1.89), so a pass would come from the spread losing when concern rose. MCCC ends 2025-06, so the sample is 186 months. | `epa_mccc.csv`, M7 section 9 |
| K22 | The EPA spread has no clean unseen sample; intensities as they stood do not exist before 2010, and a pre-1970 test says nothing about climate | P | The conclusion is right. The date is loose: EPA's GHGRP facility data start in reporting year 2010 (general knowledge), but Trucost firm data start in fiscal 2005 (BK 2021, lit_digest section 4). A pre-1970 EPA 5v5 cannot be formed before 1965-07, because Softw is missing. | lit_digest, `industry_first_month.csv` |
| K23 | The EPA spread cannot reach "implement" within this project; its only route is live paper trading | C | M7 verdict: "Do not implement". | M7 section 10 |

### 4. The one check

| # | Claim | Verdict | Evidence | Source |
|---|---|---|---|---|
| O1 | The frozen pre-1970 run of the book is the check most likely to overturn "Do not implement" | C | It was the only unseen sample left for any candidate. | M5, M7 |
| O2 | It overturns with an FF3+UMD alpha of about 1.5% or more (guess), one-sided t ≥ 2.0, the same sign in both halves, and DSR ≥ 0.95 at a documented N | P | M7's result meets the first three conditions (1.95%, t 2.45; halves 1.71% and 0.90%) and fails the fourth (DSR 0.559). By Claude's own bar the verdict does not move, which shows that the DSR clause settled the matter before the run. | M7 sections 5, 7 |
| O3 | Even a pass justifies only pilot size with paper trading, because the post-1970 evidence is exploratory and the holdout is flat | C | This is M7's verdict: "paper-trade at pilot size; the report verdict stays Do not implement". | M7 section 10 |
| O4 | It would change the verdict for a different strategy, not for the attention thesis | C | Correct and important for the report. | |
| O5 | EMV data start in 1985 | C | FRED EMVENRGYENVREG starts in 1985-01. | data/raw |
| O6 | The frozen 1994-2009 test has already failed | C | M8: 1994-03 to 2009-12, alpha -0.18% (t -0.27). | M8 |

### 5. Committee objections

| # | Claim | Verdict | Evidence | Source |
|---|---|---|---|---|
| J1 | "It is just momentum": industry momentum with a carbon screen, UMD beta 0.99 | W | For the book, UMD beta is 0.27 and R2 0.39, and the unconstrained book has no carbon screen. The objection fits the EW book (0.99, R2 0.67). | `regressions.csv` |
| J2 | The incremental alpha is small and was found by searching | C | 2.17% net against costless paper factors, exploratory, one of 24 optimizer paths and 58 S-full series. | M5, M7 section 4 |
| J3 | Daniel and Moskowitz (2016, JFE): momentum suffers rare, persistent crashes in panic states after market declines, when the market rebounds | C | Matches the paper's abstract (general knowledge). M5 reproduces the pattern for the EW book: its market beta falls 0.53 in bear states (t -2.94). | M5 section 5 |
| J4 | Crash risk applies to the book (full-sample skew -0.28) | P | The skew is right (-0.283). The exposure is much smaller than the UMD-beta-0.99 framing implies: the book's worst month is -12.8% (2009-04), against -38.75% for the EW book, and its residual skew is +0.04. | `moments.csv`, M7 section 9, M5 section 5 |
| J5 | 48 holdout months cannot tell 0% from a 2-4% alpha | P | Right for the book (SE 2.27%, minimum detectable alpha 5.75%). Wrong for the attention rules, whose SEs are 0.30% to 1.84% (FF3). | `team_holdout.csv` |
| J6 | "Do not implement" rests on insufficient evidence, not on evidence of no alpha | W | Wrong for the attention thesis. With t(44) p-values, each of the six rules rejects a +2% HO alpha at one-sided p of 0.0016 or less. The equal-weight composite of the six earns -2.09% (t -2.46). M8's frozen test failed. Right only for the book. | `team_holdout.csv`, M8 |
| J7 | Only item 7's pre-registration is provable; with 23,923 tests, every other "primary" label is taken on trust | C | True when written. | M7 section 1 |
| J8 | Data provenance: one missing CPI print created a result; the emissions file has no source; 2022 ranks are applied back to 1970 | C | replication.md (the CPI 2025-10 gap); M4 section 1 (no source, units, scope or year). The 2022 ranks apply to the EPA spread only. | replication.md, M4 |
| J9 | FF49 portfolios cannot be traded directly; ETF proxies and borrow costs for shorting Aero and Ships are untested | C | No module tests ETF proxies or borrow costs. | module FINDINGS |
| J10 | Costs above 10 bp are untested | W | M2 ran 5, 10 and 25 bp. M5 ran 25 bp for the EW book (FF5+UMD alpha -0.14%, t -0.09) and for the book (IR 0.49 in `optimizer_periods`, column `ir_25bp_fixed_path`). | M2, M5 section 5 |
| J11 | The IC flip and the holdout losses coincide with the 2022 rate and energy shock | P | The timing coincides: the rates window is 2022-01 to 2024-12, and M4's energy rally runs 2021-01 to 2022-12. As an explanation it is weak: M3 finds rates moved HO returns by at most 0.5 pp a year. | M3, M4 |
| J12 | "The BOND control helps" | W | The prompt said, and M3 shows, that adding BOND and UMD leaves every HO alpha negative and slightly more negative. | M3 FINDINGS lines 8-11 |
| J13 | 48 months cover a single regime | C | A judgement, and a fair one. | |

### Rules of the prompt

| # | Rule | Verdict | Evidence |
|---|---|---|---|
| R1 | Under 1,500 words | W | 1,716 words with the two tables; 1,481 without them (1,469 without the formula lines as well). |
| R2 | Label any number not computed as a guess | C | It labels its DSR table, the BY constant, the power estimate, the ±2% margin, the 1.5% threshold and the IC SE as guesses. Its unlabelled figures are derived (the HO SE, the iid t) and correct. |
| R3 | Cite a paper only with authors, year and the specific claim | C | All eleven citations comply, and each claim matches the paper. |
| R4 | Do not propose new signals | C | MCCC appears only as a control, and the reply says so. |

## Checklist coverage

Status when the prompt was sent (M1 to M6, M8), status since (M7), feasibility, result, and whether the pass bar and the stated meaning of a fail are sound.

| # | Claude's test and pass bar | Before the exchange | Since (M7) | Feasible with our data? | Result, or likely result | Is the pass bar sound? |
|---|---|---|---|---|---|---|
| 1 | Frozen pre-1970 run of the book; alpha t ≥ 2.0, positive in both halves | Not done: M5 starts in 1970-01 | M7 check 7: 1931-07 to 1969-12, FF3+UMD alpha 1.95%, t 2.45, one-sided p 0.0074; halves 1.71% (t 1.44) and 0.90% (t 0.83). **PASS** | Yes, from 1931-07 only (60-month history), with 34 to 39 of the 41 industries | Before the run: power 0.61 at a true 2% alpha, 0.02 chance of a pass at zero alpha | Mostly. "Close it" on a fail ignored the 39% chance of failing with a real 2% alpha. A pass shows the edge existed before 1970, not that it exists now (HO -0.34%; Val 2.99% to HO -0.34% is a decay Claude does not mention). |
| 2 | DSR on the book's appraisal ratio, N from clustering; ≥ 0.95 | Not done | M7 check 5: 0.559 (1970-2026), 0.362 (2010-2026); most lenient sensitivity 0.897. **FAIL** | Yes | My arithmetic: passes only for N ≤ 6 (1970-2026) or N ≤ 2 (2010-2026) | Yes. It is the clause that decides the verdict. |
| 3 | Project-wide one-sided Romano-Wolf on the 155 primaries; any positive survivor at 5% | Within-module Holm and BH only (for example, M1b smallest Holm p 1.00 over 40; M5 Holm 0.823) | M7 check 2 ran Holm, BH and BY, not RW. Family P (73 one-sided alpha tests): smallest Holm p 1.00, BH 0.718. All 155 (reference): 4 Holm survivors, none an alpha | No, not as specified. A joint bootstrap would have to recompute Fisher, Wald, correlation and IC statistics from eight modules on each resample. | It cannot pass. The best positive primary alpha has t 1.89 (one-sided p 0.030) and would survive only if N_eff were below 1.7 | No. A survivor among non-alpha primaries says nothing about implementation. Restrict the family to alpha tests, as M7 did. |
| 4 | Hansen SPA over all strategy series against zero alpha; p < 0.05 | Not done | M7 check 4: S-full (58 series, 1970-2026) SPA p 0.0086, book RW p 0.017. S-post (89 series, 2010-2026) SPA p 0.150, book RW p 0.199 | Yes, except for M2's grid, whose series were not saved (so both families are slightly lenient) | Passes over 1970-2026, fails over 2010-2026 | Yes. It answers "survives the search as nonzero", which is weaker than the DSR (see "What Claude missed", item 1). |
| 5 | Holdout power and TOST with a ±2% margin (a guess); 90% interval inside the margin | Partly: M5 and M4 report HO alphas; the team HO t-statistics are known | M7 check 6 replaced it with a one-sided reading against δ = 0.25 × residual volatility: all six rules "reject a worthwhile alpha"; the book is inconclusive | Yes | Here (team FF3, t(44)): the four hold rules fail the TOST because their intervals are too negative (Original 3m -7.13% to -0.94%; Pure 3m -4.13% to -0.29%; Original 6m -4.59% to +0.03%; Pure 6m -5.06% to -0.37%). The two continuous rules pass. The book fails (-4.16% to +3.48%), which correctly reads as "insufficient evidence" | No. A two-sided equivalence test calls a significantly negative holdout "insufficient evidence". Use non-inferiority against a worthwhile alpha. |
| 6 | EPA spread with an MCCC-innovation control; alpha t ≥ 2.0 | Not done in M4. M1 built the MCCC shocks | M7 check 9 (exploratory): 6.66% (t 2.13), shock loading -0.52% per s.d. (t -2.21), 186 months | Yes, to 2025-06 | Here, with PST's trailing 36-month AR(1): 5.88% (t 1.85), loading -0.42% (t -1.89). A knife-edge pass or fail depending on the construction | No. The negative loading means the control raises the alpha. The stated meaning of a fail ("its returns came from a concern shock") has the sign backwards. |
| 7 | Data audit: ALFRED vintages for CPI and EMV, and the emissions source; headline figures move < 0.1 pp | CPI gap found (replication.md); emissions provenance searched (M4 section 1) | M7 check 9: the 2024-06-15 EMV vintage equals the current file in all 473 months. The 2022-09-15 vintage differs in 2022-08 (0.563 against 0.544) and trivially in 2022-07. The 2025-12-20 CPI vintage also lacks 2025-10, so the gap was there in real time | Vintages yes; the emissions source no | Vintage part passes. Headline figures were not rerun on the 2022-09 vintage (one month differs by 3.6%) | Yes for the vintages. The emissions clause cannot be met, because no source exists. |
| 8 | Pre-registered crash stress (1932, 2009); drawdown within the stated budget | EW book: 2009-04 -38.75%, maximum drawdown -60.3%, bear-state beta change -0.53 (M5) | Book after 1970: 2009-04 -12.8%, maximum drawdown -24.1% (M7 check 9). Before 1970: 1932-07 -11.2%, maximum drawdown -30.2% (M7 S3) | Yes | Descriptive only | No. No budget was ever stated, so there is nothing to pass. Setting one now would be post hoc (M7 declined to). |
| 9 | ETF proxies at 25 bp; net alpha > 0 | 25 bp done: M2 grid; M5 EW book (alpha -0.14%); M5 book (IR 0.49) | M7 check 8, book at 25 bp: 1.73% (t 2.43) full sample, 2.68% (t 1.86) post-2010, -0.79% HO; break-even 84 bp | The 25 bp part yes. ETF proxies no: the project has no ETF data, and FF49 industries have no one-to-one ETFs (general knowledge) | The 25 bp part passes over the full sample | The cost part is sound. The ETF part cannot be run here. |
| 10 | Carbon frontier on pre-1970 data; IR change at b = -1 not significant | M5 post-1970: -0.005 (95% CI -0.110 to +0.096) | M7 S2: -0.006 (CI -0.194 to +0.228); binds in 77.9% of months; infeasible in 38 | Yes, but with the undated team ranking applied to the 1930s | "Not significant", as expected | No. A low-power test passes by failing to reject. Use a non-inferiority bound (for example, CI lower bound above -0.10). M7 applied that reading and did not claim "no carbon cost". |

### Other recommendations in the reply

| Recommendation | Before the exchange | Since (M7) or here | Result |
|---|---|---|---|
| Confirmatory family, one-sided, RW with Holm alongside (F2-F4) | Not done | M7 family F (Holm over 2 tests): check 7 adjusted p 0.0147; RW used on the search families | Check 7 is the only confirmatory survivor |
| BH and BY on the grids, reported as distributions (F7-F13) | M2: 0 positive BH or Holm survivors | M7 check 3: R-M2 BH and BY 0 survivors; one BH survivor in R-other (a CPU COVID cell), which fails BY | Confirms the verdict |
| Composite of the six variants (F18) | Not done | Here: Val 1.44% (t 2.06), HO -2.09% (t -2.46) | Post hoc, and it tells the same story |
| Nyholt M_eff (F20) | Not done | Here: six variants 2.98, 24 paths 6.38. M7: 42.4 and 74.8 (Li-Ji 14 and 27) | Nyholt counts block structure generously; the verdict does not depend on the choice (M7) |
| White's Reality Check (F21) | Not done | Superseded by SPA in M7 check 4 | See checklist item 4 |
| DSR of the raw Sharpe ratios (D7) | Not done | Here: book passes up to N = 83 (1970-2026) and N = 5 (2010-2026); EPA post-2010 only N = 1. M7 context: 0.859, 0.505, 0.238 | The raw Sharpe flatters the book; the appraisal ratio governs |
| Lo (2002) adjustment (D14) | Not done | Here and in M7: EPA post-2010 Sharpe 0.52 to 0.42; book 0.555 to 0.553 and 0.696 to 0.632 | Hurts the EPA spread most |
| Secondary FF5+UMD, 1963-07 to 1969-12 (K10) | Not done | M7 S1: 3.26%, t 1.76 | Uninformative, as expected |
| Book minus unconstrained book (K13) | M5 post-1970 frontier | M7 S2 (checklist item 10) | No detectable cost, low power |

## What Claude missed

1. **Its two best-of-many yardsticks disagree, and it never says which governs.** A DSR of 0.95 needs roughly t ≥ E[max_N] + 1.645. A 5% max-t (or SPA) test needs only the 95th percentile of the maximum. At N = 8 these are 3.10 and 2.49; at N = 42, 3.85 and 3.03 (`t_needed.csv`). The book's alpha t of 3.07 (one-sided p 0.0011) passes a max-t test for up to about 46 independent series and fails the DSR from N = 7. M7's rule resolves this: max-t decides whether the alpha survives the search, and only the DSR can move a verdict.
2. **Decay.** The book's alpha went from 2.99% (t 1.78) in validation to -0.34% in the holdout. A pre-1970 pass shows the edge existed, not that it persists.
3. **A pre-registered reading of a fail.** At 0.61 power for a true 2% alpha, "close it" on a fail throws away a real 2% edge 39% of the time.
4. **Even the unconstrained book depends on the team's undocumented emissions file**, through the 41-industry universe (convention X). The 8 uncovered industries include Oil, Gold and Chips.
5. **The pre-1970 universe is smaller.** 37 of the 41 industries exist from 1930-07 until 1963-06, which changes the book's breadth.
6. **The M2 grid cannot enter a max-t or SPA family without rerunning M2**, because its return series were not saved. This limits recommendations F12 and checklist item 4.
7. **The EPA shock control is sensitive to how the shock is built**: t 2.13 with an expanding AR(1), 1.85 with PST's trailing 36-month AR(1).

## Notes on our own prompt

1. It printed "UMD beta 0.99" in the sentence about the optimizer book without saying it belongs to the EW book. That produced Claude's errors D8 and J1.
2. It gave "a 2022 sort applied back to 1970" for the EPA spread and never named the book's carbon source. That produced K11.
3. "No module computed a strategy return before 1970" is slightly too strong. M6 saved a hedged Brown-leg residual from 1931-07 (never used before 1990), and M3 saved a BOND series from 1953-05. No momentum-book or EPA-spread return existed before 1970, so the claim that matters, that the book's window was unseen, was true.
4. The DSR moment inputs are population estimates (kurtosis 5.77, 3.66, 4.77 against unbiased 5.80, 3.71, 4.84). This is immaterial: every DSR cell moves by less than 0.007.
5. The prompt specified "p from t(n - k)". Under that convention Original 6m's HO 90% interval reaches +0.03% and its p against +2% is 0.0016. With normal p-values the interval ends at -0.02% and p is 0.0009. Any statement that all four hold rules have intervals "wholly below zero" or reject at "p ≤ 0.001" holds only with normal p-values.
