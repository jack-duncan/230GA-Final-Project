# Fact-check: exchange 03 (robustness design), Claude as the committee skeptic

Independent fact-check, 2026-09-26. Inputs: the prompt and Claude's reply as copied from the chat (this folder had no saved copies when I ran the checks). Scripts: `checks/fc03_checks.py` and `checks/fc03_extra.py`. Run each with `cd /home/hashim/projects/GA/project/research && uv run python exchange/03_robustness_design/checks/<script>`. Outputs go to `checks/out/`: `moments.csv`, `dsr_grid.csv`, `book_regressions.csv`, `power_pre1970.csv`, `holdout_tost.csv`, `meff.csv`, `fc03_results.json`, plus three ALFRED vintage files. Corroborating material: the eight ledgers and module tables in `outputs/tables/`, the module FINDINGS files, `logs/replication.md` and `logs/lit_digest.md`.

Guard for the pre-1970 window. I computed no strategy return, return moment or factor moment before 1970. From pre-1970 data I took only availability counts: which FF49 industries have a return in which month, and each file's first month. The frozen pre-1970 test that Claude proposes is still unspent.

Notation. "The book" is the M5 Grinold-Kahn optimizer book (convention X, unconstrained, 10 bp). "EW book" is M5's pre-registered equal-weight 8-long/8-short momentum book. "EPA spread" is M4's EPA 5v5 Green-minus-Brown. Unless stated otherwise, t-statistics are Newey-West with 6 lags. Verdicts: C = correct, P = partly correct, W = wrong, U = unverifiable.

## Summary

I extracted 72 checkable claims and recommendations from the reply: 47 correct, 17 partly correct, 8 wrong, 0 unverifiable. The statistics are sound and the arithmetic is right. The main errors are about our own strategy, and they matter because they sit in the reply's lead candidate.

1. **The formulas and hand arithmetic check out.**
   - The PSR and DSR formulas and their inputs match Bailey and López de Prado (2014), including monthly SR, raw kurtosis and the expected-maximum term.
   - The BY constant is right (9.576 at m = 8,091), and so is the Nyholt formula.
   - All ten cells of its DSR table reproduce to within 0.005.
   - Its appraisal ratio (0.41) and its break-even count of about 7 trials both reproduce: 0.400 to 0.408, and N at most 6 to 7.
2. **Two facts about the lead candidate are wrong.**
   - The UMD beta of 0.99 belongs to the EW book (recomputed: 0.987). The optimizer book's UMD beta is 0.27 (t 15.2, R2 0.39).
   - The book's carbon constraint does not use "2022 intensities". It uses the team's undated `emissions_ff_industry.csv` (M5 section 3; `m5lib.load_inputs`), the file M4 found has no source and ranks Aero and Ships implausibly.
   - The 2022 EPA factors are used only by the EPA spread.
3. **One statistical claim is wrong.** Romano-Wolf is not stricter than BH.
   - BH, like Holm, needs p at most q/m (6e-6 here) before it rejects anything. A max-t stepdown uses the dependence between tests and can reject when BH rejects nothing.
   - The grid's best positive cell has one-sided p 0.00019. A max-t test would flag it if the grid's effective number of tests were below about 270.
   - That cell is a 24-month COVID alpha, the known small-sample artefact, so the conclusion "nothing implementable is rescued" probably survives. The stated reason does not.
4. **The frozen pre-1970 test is feasible, but it is mis-specified and low-powered.**
   - The optimizer needs 60 months of returns, so the window is 1931-07 to 1969-12 (462 months), not 1927-07.
   - Only 37 of its 41 covered industries exist before 1963.
   - With a true 2% alpha, the chance of reaching t 2.0 is 0.63 at post-1970 residual volatility, 0.33 at 1.5 times that level and 0.20 at twice it. So a fail is the likely outcome even if the alpha is real.
   - The pass bar contradicts itself. Its "project-wide DSR on the appraisal ratio" clause either cannot be met (Claude's own arithmetic fails it for more than 7 trials) or should use N = 1 for a single frozen trial.
5. **Two checklist items can give opposite answers.** DSR at least 0.95 requires t at least E[max_N] + 1.645 (3.10 at N = 8). A 5% max-t or SPA-type test requires only the 95th percentile of the maximum (2.49 at N = 8).
   - The book's alpha has t 3.07 and one-sided p 0.0011.
   - It passes a max-t test for up to about 46 effective series, but it fails DSR from N = 7.
   - The reply does not say which yardstick governs.
6. **The "low power" objection overreaches for the attention thesis.** Every one of the four hold variants rejects a +2% holdout alpha at p at most 0.001, and their 90% intervals lie wholly below zero. The low-power point is right only for the book.
7. **Its EPA test and its stated reading of a fail are backwards on our data.**
   - I ran it as an exploratory check. With a same-month real-time MCCC shock added, the post-2010 FF5+UMD alpha rises from 4.9% (t 1.52) to 6.7% (t 2.13) over the same 186 months (MCCC ends 2025-06).
   - The shock loading is negative: -0.52% a month per 1-sd shock, t -2.21. So the spread lost when concern rose, the opposite of the Pástor, Stambaugh and Taylor (2022) channel.
   - The pass is knife-edge. Lagged shock: t 1.06. MCCC-transition shock: t 1.95. CPU shock: t 1.97. FF3 base: t 1.76.
8. **Checklist status.**
   - Three items have outcomes that the existing numbers already settle:
     - 3, Romano-Wolf on the primaries, cannot pass: the largest positive primary alpha t is 1.89.
     - 5, the TOST, I computed here.
     - 7, the EMV vintages, pass on ALFRED.
   - Two items are partly done already (8 and 9).
   - One cannot be run on our data (ETF proxies).
   - The reply is also over its word limit: 1,716 words, or 1,469 without the two tables and formula lines, against "under 1,500".

## Claims table

Numbers are recomputed by `fc03_checks.py` unless another source is named. "Val" = validation, 2010-01 to 2022-07. "HO" = holdout, 2022-08 to 2026-07.

### Bottom line

| # | Claim (quoted or condensed) | Verdict | Evidence | Source |
|---|---|---|---|---|
| 1 | "no candidate reaches 'implement' on the current evidence" | C | Every pre-specified alpha fails (M4 t 1.52; M5 P1 t 1.09, P2 t 0.71; M8 t -0.27). The book's alpha is exploratory, and its holdout alpha is -0.34%. | M4, M5, M8 FINDINGS |
| 2 | "The attention thesis is finished (items 1-3, 7 and 8)" | C | Signal is volatility news (M1). MCCC and CPU are null (M1b: smallest Holm p 1.00). Frozen 1994-2009 rule FAIL (M8). Ridge collapses to the mean (M6). | M1, M1b, M6, M8 |
| 3 | "only one still has an unseen sample" | P | The book has no computed pre-1970 return, so its window is unseen by this project. The window is not unseen by the field, though (see 42). The EPA spread has no unseen sample. | M5 returns start 1970-01 |

### 1. Families

| # | Claim | Verdict | Evidence | Source |
|---|---|---|---|---|
| 4 | Confirmatory family = each candidate's pre-specified alpha test, one-sided because only a positive alpha leads to implementation | C | Sound. It matches the brief's decision rule. | brief p.1 |
| 5 | Romano and Wolf (2005, *Econometrica*): the bootstrap stepdown controls FWER using the dependence between tests, "so it has more power than Holm" | C | Correct attribution (Econometrica 73(4)). Resampling stepdown is asymptotically at least as powerful as Holm under dependence. | general knowledge |
| 6 | Stationary block bootstrap on the same months for every series; "Holm is valid under any dependence" | C | Both are standard and correct. | general knowledge |
| 7 | "Treat all 155 as one project-level family" | P | The idea of one family, not eight, is right. But 67 of the 155 primaries are not alpha tests: M1 has 15 (Fisher, Wald, IC, correlations), M1b 16 ICs, M2 4 HML loadings, M3 21 (12 Wald F, 7 beta-timing terms, 2 BOND loadings), M5 2, M6 8 (CW t), M8 1. Its own rule excludes loadings. The item-3 checklist test would "pass" on M1's zero-month Fisher test (p 1e-32), which has nothing to do with alpha. | ledgers |
| 8 | "Cristhian's 8,091 alphas are a sensitivity analysis" | C | M2 labels 46 tests primary; the rest are robustness (5,562) or exploratory (7,874). | M2 ledger |
| 9 | BH holds under positive dependence; Benjamini and Yekutieli (2001) prove it for PRDS statistics | C | Correct (Ann. Statist. 29(4)). | general knowledge |
| 10 | "near-duplicate one-sided alphas are plausibly PRDS" | P | Plausible for one-sided normal statistics with nonnegative correlations. M2's grid uses two-sided p-values, which the PRDS result does not cover. The grid also mixes windows, hedges and benchmark strategies. | M2 ledger |
| 11 | BY factor ln m + 0.58, "about 9.6 for m = 8,091" | C | The sum of 1/i for i up to 8,091 is 9.5758. | fc03 |
| 12 | "BH already finds zero positive survivors" | C | grid_bh_survivors_positive = 0. | M2 key_numbers |
| 13 | "BY and Romano-Wolf are stricter, so they will not rescue anything" | W | BY is stricter than BH; RW is not nested within BH. The best positive grid cell (24-month COVID FF3 alpha, t 4.36, two-sided p 0.00038) would survive a max-t test at 5% if the grid's effective number of tests were below about 270 (Šidák arithmetic). It is still not implementable: its classic OLS t roughly halves (M2, M5 section 5). | M2 ledger; fc03 |
| 14 | Report the grid as a distribution: share of positive alphas and median t | C | Partly done already: M2 reports 368 positive and 531 negative alphas with p < 0.05. Recomputed over 8,203 alpha rows (112 outside the family): 54% positive, median t 0.13. Holdout: 2.2% positive, median -1.34. Val: 89%, median 1.15. Last 18 months: 0% positive, median -2.35. | M2 key_numbers; fc03 |
| 15 | Exploratory tests get no family; "the optimizer book's full-sample alpha sits in this group" | C | The book's alpha row is labelled exploratory. M5 nonetheless applied BH inside its exploratory set (BH p 0.027). | M5 ledger, FINDINGS section 7 |
| 16 | Loadings, descriptive statistics and placebos are excluded | C | Sound principle, though see 7: M2 and M3 registered loadings and beta-timing terms as primaries. | ledgers |
| 17 | "Most of the roughly 4,200 nominal hits are loadings" | W | 4,184 rows have p < 0.05. Of these, 1,325 (32%) are factor loadings and 138 are beta-timing components. Alpha tests are 1,624 (39%: 783 positive, 841 negative), mean tests 561 and other tests 536. The prompt said "many"; Claude made it "most". | ledgers; fc03 |
| 18 | One composite statistic per family, "one test, with more power" | P | It is one test. More power follows only if the variants share one effect and are imperfectly correlated; the six team variants have a Nyholt M_eff of 3.0. Equal-weighting raw alphas mixes scales: holdout alpha SEs run from 0.30% (continuous) to 1.84% (hold). Use t-stats or volatility-scaled alphas. It can only be pre-specified for data not yet seen. The holdout composite is -2.1%. | fc03 holdout_tost |
| 19 | A max-t bootstrap handles the correlation automatically | C | Correct. | general knowledge |
| 20 | Nyholt (2004): M_eff = 1 + (M-1)(1 - Var(λ)/M) | C | Formula as published (Am. J. Hum. Genet. 74). For alpha tests, use residual correlations: on the 24 optimizer paths M_eff is 6.4 on raw returns and 8.1 on FF5+UMD residuals. The Li-Ji estimator gives 4 and 6, so the estimate depends on the method. | fc03 meff |
| 21 | White (2000) Reality Check and Hansen (2005, *JBES*) SPA test the best strategy after the search; "SPA is less distorted by poor, irrelevant alternatives" | C | Correct attributions and characterization (studentization and recentring). | general knowledge |

### 2. Deflated Sharpe

| # | Claim | Verdict | Evidence | Source |
|---|---|---|---|---|
| 22 | PSR(SR0) = Φ[(SR - SR0)√(T-1) / √(1 - γ3 SR + ((γ4-1)/4) SR²)] | C | Matches Bailey and López de Prado (2014, *JPM* 40(5)). With raw kurtosis 3, the denominator is 1 + SR²/2, as it should be. | general knowledge |
| 23 | SR0 = √V · [(1-γ)Φ⁻¹(1-1/N) + γΦ⁻¹(1-1/(Ne))] | C | Correct. It is an approximation: E[max] for N = 2 is 0.520 against 0.564 exact, and for N = 100 it is 2.531 against 2.508. | fc03 emax |
| 24 | Inputs: monthly SR, T, skew, raw kurtosis, N, V in monthly units, γ = 0.5772, bar 0.95 | C | Complete and correctly specified. | |
| 25 | Deflate the book's SR, the book's appraisal ratio and the EPA post-2010 SR | C | Right choice. The raw-SR DSR alone would mislead: the book's raw SR passes DSR 0.95 for up to 83 trials, but its FF5 alpha without UMD is 4.53% (t 5.21), so the raw SR is largely factor premia. | fc03 dsr_grid, book_regressions |
| 26 | "with a UMD beta of 0.99 the raw Sharpe is mostly momentum" | W | 0.99 is the EW book (0.987, R2 0.67). The optimizer book loads 0.273 on UMD (t 15.2; R2 0.39; correlation with UMD 0.60). The effect is similar, since adding UMD halves its alpha, but the number is wrong. | fc03; M5 section 5 |
| 27 | A trial is every return series that could have been presented as the strategy, including sample windows; placebos and loadings are not trials | C | Consistent with Bailey and López de Prado. Claude's own EPA N = 2 contradicts it (see 34). | |
| 28 | López de Prado and Lewis (2019, *Quantitative Finance*) cluster strategy returns to estimate the effective number of trials | C | Correct attribution (QF 19(9)). | general knowledge |
| 29 | Setting V = 1/(T-1) "gives a lower bound on SR0" | P | True for independent trials whose true SRs differ: the cross-trial variance equals sampling variance plus true dispersion. For near-duplicate trials, the observed cross-trial variance falls below 1/(T-1), so the bound holds only after collapsing to clusters. Trials with different T (full sample against post-2010) also have different null variances. | |
| 30 | "PSR assumes independent returns" | C | The Mertens-type SR variance assumes iid returns. | |
| 31 | "Newey-West t-statistics are below their iid equivalents (EPA: 1.72 against about 2.1)" | C | EPA: 1.72 against 2.12 (ρ1 to ρ3 are 0.13, 0.11, 0.10). Book post-2010: 2.54 against 2.83 (ρ1 0.11). Book full sample: 4.14 against 4.18, negligible. | fc03 moments |
| 32 | Lo (2002, *FAJ*) gives the serial-correlation adjustment | C | Correct attribution (FAJ 58(4)). Adjusted annual SRs: EPA 0.52 to 0.42; book post-2010 0.70 to 0.63; book full 0.555 to 0.553. | fc03 moments |
| 33 | DSR table (book full 1.00/0.99/0.94/0.81; post-2010 0.998/0.90/0.62/0.34; EPA 0.98/0.71) | C | Recomputed: 1.000/0.994/0.943/0.812; 0.998/0.901/0.625/0.338; 0.984/0.708. Summary inputs match the data: 0.555, -0.28, 5.77; 0.696, 0.29, 3.66; 0.520, 0.35, 4.77 (population-moment estimators). | fc03 dsr_grid, moments |
| 34 | EPA: "DSR is only about 0.94 to 0.95 at N = 2 ... It fails" | C | 0.947 with the approximation, 0.942 with the exact E[max]. With the Newey-West scaling it is 0.906, and PSR(0) itself falls to 0.96. N = 2 is lenient: M4's 15 GB variants have M_eff 7.8, where the DSR is about 0.75. | fc03; fc03_extra |
| 35 | Book appraisal ratio "roughly t/√years ≈ 0.41" | C | 0.408 (t/√years). The OLS residual version is 0.400 (alpha 2.17%, residual volatility 5.44%). | fc03 book_regressions |
| 36 | Clears DSR 0.95 "only if the effective number of trials is at most about 7" | C | Largest N is 6 with residual moments (skew 0.04, kurtosis 3.41) and 7 via the NW t. | fc03 |
| 37 | "Your project almost certainly has more, so the full-sample alpha does not survive deflation" | C | Right, but by a smaller margin than "almost certainly" suggests. The 24 optimizer paths alone give M_eff 6.4 to 8.1 (Nyholt) or 4 to 6 (Li-Ji). DSR on the AR is 0.939 at N = 8 and 0.847 at N = 24. Adding the EW variants and screens pushes N past 7. | fc03 meff; fc03_extra |

### 3. Candidates

| # | Claim | Verdict | Evidence | Source |
|---|---|---|---|---|
| 38 | Book "has the strongest statistics, but its alpha was exploratory" | C | Full-sample FF5+UMD alpha 2.17%, t 3.07; exploratory label. | M5 section 7 |
| 39 | Holdout -0.34% with SE about 2.3%; "too short either to confirm the alpha or to kill it" | C | SE 2.27%. The 90% CI runs from -4.1% to +3.4%. It cannot reject alpha of at least +2% (p 0.15). The minimum detectable alpha at 80% power is 5.6%. | fc03 holdout_tost |
| 40 | Holdout rank IC 0.030 is about 1 SE below 0.054 (SE guessed at 0.02) | C | Actual holdout SE 0.026 (t 1.14), so the gap is 0.9 SE. The last 18 months show -0.005. | M5 section 7 |
| 41 | Sample 1927-07 to 1969-12, because "the momentum signal needs 12 months of history" | P | Right for the EW book (510 months). The optimizer also needs 60 months for its residual volatility and Ledoit-Wolf covariance, so its window is 1931-07 to 1969-12 (462 months, 38.5 years). FF49 has 40 industries in 1926-07, 43 from 1931-07 to 1962, and 49 only from 1969-07. Soda, FabPr, Guns and Gold start 1963-07, Softw 1965-07, Hlth 1969-07. Of the 41 covered industries, Softw, Hlth, Soda and Guns are missing, leaving 37. | fc03 (counts only) |
| 42 | "Nothing has touched this period" | P | No momentum or optimizer return exists before 1970 (M5 formation used 1965-69 inputs only). But the team pipeline computes Always-short Brown from 1934-07 (426 nonzero pre-1970 months) and buy-and-hold GB from 1926-07 (522), and M6 saved the hedged Brown residual from 1931-07. UMD itself (from 1927-01), and momentum over 1927-1969 in general, are widely published; Claude itself cites the 1932 crash. The window is unseen for this book, not unseen. | team_pipeline; M6 team_brown_residual |
| 43 | Freeze the code, IC 0.05, 5% TE, b = -1, 10 bp and the missing-industry rule; hash and timestamp | P | Right procedure (M8 template). Incomplete: it must also freeze the emissions file (team or EPA), the 60-month window and warm-up rule, the 0.10 box, the solver and tolerance, the fallback when b = -1 is infeasible, and the reading of a fail. | M5 section 4 |
| 44 | Benchmark FF3 + UMD "because FF5 starts in 1963-07" | C | FF3 from 1926-07, UMD from 1927-01, FF5 from 1963-07. Post-1970, the book's FF3+UMD alpha is 2.01% (t 2.84), below the headline 3.07. | fc03 |
| 45 | Secondary FF5+UMD test on 1963-07 to 1969-12 | P | Feasible but uninformative: 78 months give a SE of about 2.1% a year at post-1970 residual volatility. | fc03 arithmetic |
| 46 | "The carbon ranks use 2022 intensities" | W | The optimizer's c_i comes from the team's undated file (`m5lib.load_inputs`: `team["emissions"]`; M5 section 3). 2022-vintage EPA factors are used only in M4. | M5 code and FINDINGS |
| 47 | Static ranks are "acceptable here because carbon acts as a constraint, not as the source of return" | P | Acceptable for the return question only. The bound changes holdings (b = -1 cuts long WACI by 60%), and convention X drops 8 uncovered industries from the universe, so the ranking does shape returns. Pre-1970 carbon statements would be anachronistic. | M5 section 7 |
| 48 | Pass bar: t at least 2.0; positive before and after 1948; no significant carbon cost; project-wide DSR on the AR at least 0.95 | P | The first three are sensible. The DSR clause contradicts itself. If it means the post-1970 AR, Claude's own item 36 fails it for N > 7, so no pre-1970 result could pass. If it means the pre-1970 AR, a single frozen trial has N = 1. "No significant carbon cost" rewards low power (see checklist 10). | |
| 49 | Power: residual volatility about 5%; SE about 0.8% over 43 years; a true 2% clears t 2.0 about two-thirds of the time; pre-war volatility lowers it | C | Residual volatility 5.44% (FF3+UMD). SE 0.82%; power 0.67. For the optimizer's 462 months: SE 0.86%, power 0.63. At 1.5 times the volatility, 0.33; at 2 times, 0.20. I computed no pre-1970 moment. | fc03 power_pre1970 |
| 50 | EPA pre-specified alpha t 1.52 | C | 4.7%, t 1.52, p 0.129. | M4 primary_test |
| 51 | EPA full-sample alpha comes from CMA and UMD loadings and a 2022 sort back to 1970 | C | CMA -0.345 (t -3.04), UMD -0.096 (t -2.02); raw mean t 1.40. | M4 Robustness |
| 52 | Pástor, Stambaugh and Taylor (2022, *JFE*) attribute 2012-2020 green outperformance to unexpected rises in climate concern, not higher expected returns | C | Nov 2012 to Dec 2020; shock-purged mean about -4 bps a month (Table 4, p.415). | lit_digest section 3 |
| 53 | Test: post-2010 FF5+UMD alpha with MCCC innovations as a control | P | Feasible only from 2010-01 to 2025-06 (MCCC ends 2025-06), 186 months with 13 holdout months lost. My exploratory run gives the result in Summary item 7: alpha t 2.13, with the shock loading of the opposite sign. | fc03; fc03_extra |
| 54 | No clean unseen sample; point-in-time intensities "do not exist before 2010"; pre-1970 says nothing about climate | C | Matches the literature: Zhang drops backfilled pre-2008 Trucost, and EIJP's US data start 2009-09. Our data hold no point-in-time intensities at all: EPA v1.3 (2022 USD) and v1.0 (2016). | lit_digest sections 6-7; data/raw |
| 55 | EPA spread cannot reach implement here; its only route is paper trading | C | Consistent with 50 to 54. | |

### 4. The one check

| # | Claim | Verdict | Evidence | Source |
|---|---|---|---|---|
| 56 | The frozen pre-1970 run is the check most likely to overturn the verdict | P | Right by elimination: it is the only unseen sample for any candidate. With power of 0.20 to 0.63 at a true 2% alpha, though, overturning is unlikely, and a pass would leave the 2022-2026 holdout at -0.34%. | fc03 power |
| 57 | Overturn if the FF3+UMD alpha is at least about 1.5% with one-sided t at least 2.0 | P | The t bar binds: t 2.0 needs an alpha of at least 1.72% at post-1970 residual volatility, 2.57% at 1.5 times and 3.43% at 2 times. The 1.5% figure never decides anything. | fc03 power |
| 58 | A pass justifies only a paper-traded pilot; it would not rescue the attention thesis; EMV starts 1985; the frozen test failed | C | EMV from 1985-01; M8 FAIL (alpha -0.18%, t -0.27). | M8 |

### 5. Committee objections

| # | Claim | Verdict | Evidence | Source |
|---|---|---|---|---|
| 59 | "The book is industry momentum with a carbon screen (UMD beta 0.99)" | W | UMD beta 0.27 (see 26), and the 2.17% book is unconstrained, not screened. The objection still holds: alpha falls from 4.53% (FF5) to 2.17% (FF5+UMD), and the FF3+UMD t is 2.84. | fc03 book_regressions |
| 60 | Daniel and Moskowitz (2016, *JFE*): momentum crashes are rare and persistent, occur in panic states after market declines, and coincide with rebounds | C | Matches their abstract ("infrequent and persistent strings of negative returns"). | general knowledge |
| 61 | "The full-sample skew is -0.28" | C | Book -0.28. The book's own crashes: worst month 2009-04 at -12.8%; Mar-May 2009 -17.5%; max drawdown -24.1% (trough 2010-01). The EW book is worse: skew -0.66, -38.75% in 2009-04. | fc03; M5 section 5 |
| 62 | "Forty-eight holdout months cannot tell 0% from a 2-4% alpha" | P | True for the book (CI -4.1% to +3.4%). False for the four team hold variants: their 90% CIs are wholly negative (O3 -7.1% to -1.0%; P3 -4.1% to -0.3%; O6 -4.6% to -0.02%; P6 -5.0% to -0.4%). | fc03 holdout_tost |
| 63 | "'Do not implement' rests on insufficient evidence, not on evidence of no alpha" | W | For the attention thesis, the holdout rejects a +2% alpha for all four hold variants (p at most 0.001), the frozen 1994-2009 test fails, and genuine climate measures are null. That is evidence against the thesis. The statement holds only for the book. | fc03; M1b; M8 |
| 64 | Only item 7 is provably pre-registered; 23,923 tests | C | Ledger total 23,923; M8 has `first_run_record.json`. | ledgers |
| 65 | One missing CPI print created an entire result | C | The October 2025 CPI gap explains the whole Pure-versus-Original holdout gap. | replication.md item 2 |
| 66 | The emissions file has no source | C | No source, units, scope or year anywhere. | M4 Results section 1 |
| 67 | "The 2022 carbon ranks are applied back to 1970" | P | True for the EPA spread. The book's ranks come from the undated team file. | M4; M5 |
| 68 | FF49 portfolios are not tradable; ETF proxies and borrow costs are untested | C | Neither appears in any module. | |
| 69 | "costs above 10 bp are untested" | W | M5 ran 0, 5, 10 and 25 bp on the EW book: alpha -0.14% at 25 bp, break-even about 24 bp. M2 ran 5, 10 and 25 bp on the team strategies. Only the optimizer book lacks a cost sweep. | M5 section 5; M2 |
| 70 | The IC flip and holdout losses coincide with the 2022 rate and energy shock; "The BOND control helps" | P | The timing is right. But BOND + UMD makes every holdout alpha slightly more negative, and rates moved holdout returns by at most 0.5 pp a year. The control does not explain the losses. | M3 |

### Rules of the prompt

| # | Claim | Verdict | Evidence |
|---|---|---|---|
| 71 | "Under 1,500 words" | W | 1,716 words (tokens with a letter or digit), or 1,469 without the two tables and the two formula lines. |
| 72 | Guesses labelled, papers cited with authors, year and claim, no new signals | C | Every citation has authors, year and a specific claim. MCCC is proposed as a control, not a signal. Computed quantities (SE 2.3%, AR 0.41) are derived from given numbers, and the guessed ones are labelled. |

## Checklist coverage

Each of Claude's ten items is shown with what the project already has, whether our data can run it, and what it would likely show.

| # | Claude's test | Already done? | Feasible with our data? | Likely result, and whether the pass bar and fail reading hold up |
|---|---|---|---|---|
| 1 | Frozen pre-1970 run of the book | No. M5 returns start 1970-01. | Yes, with limits. EW book: 1927-07 to 1969-12, 510 months. Optimizer: 1931-07 to 1969-12, 462 months, on 37 of the 41 covered industries (Softw, Hlth, Soda, Guns absent). Benchmark FF3 + UMD (UMD from 1927-01). Needs a hashed pre-registration like M8's. | Unknown by design. Power at a true 2% alpha is 0.63, 0.33 or 0.20 at 1, 1.5 or 2 times the post-1970 residual volatility. A fail is therefore likely even if the alpha is real, and "a post-1970 artifact; close it" overstates what a fail shows. Pre-register a fail reading such as a one-sided test that rejects alpha of at least 2%. |
| 2 | DSR on the book's appraisal ratio, trials by clustering | No (planned for M7). M5 reports BH within its exploratory set only. | Yes for M5 (24 optimizer paths and the primary are saved; robustness variants must be regenerated from `run.py`). Project-wide clustering needs the M1b and M2 series regenerated. | **Fail.** AR 0.400; DSR at least 0.95 only for N up to 6 or 7. The optimizer paths alone give N_eff 6.4 to 8.1, where the DSR is 0.939 at N = 8. |
| 3 | Project-wide one-sided Romano-Wolf on the 155 primaries | Holm within each module only (M1b smallest Holm p 1.00; M2 0 survivors; M5 Holm at least 0.211). | Partly. 67 primaries are not alpha tests, and the windows range from 1994-2009 to 2022-2026, so a joint bootstrap needs every series regenerated. | **Fail, and foreseeable without running it.** The largest positive primary alpha t is 1.89 (M2, u5 Pure 6m, post-2010), one-sided p 0.029, and no FWER method with more than one effective test can make it significant. Restrict the family to alpha tests; otherwise M1's Fisher test "survives". |
| 4 | Hansen SPA over all strategy series against zero alpha | No. | Partly. Monthly series are saved for M4 (16), M5 (25), M6, M8 and the team pipeline (8). M1b and M2 must be regenerated. The factor model defining "alpha" must be fixed in advance. | **Uncertain; it may pass where item 2 fails.** Against FF5+UMD, the best series is the book (one-sided p 0.0011). A max-t test rejects at 5% if the effective number of series is below about 46. Against CAPM, the EW book (t 3.92) dominates. Pre-commit whether DSR (item 2) or SPA governs. |
| 5 | Holdout power and TOST, ±2% margin | Not as a TOST. Holdout alphas and SEs exist in M3, M4 and M5 and in the team pipeline. | Yes (computed here). | Book: **fails** (CI -4.1% to +3.4%), so "insufficient evidence" is correct. Team hold variants: CIs wholly below zero, rejecting alpha of at least +2% at p at most 0.001; this is evidence against, not insufficiency. Continuous variants fall inside ±2% only because they run at 1.4% volatility. EPA: -5.3% to +13.1%. A fixed ±2% margin is not scale-free; set it in IR units. |
| 6 | EPA spread with an MCCC-innovation control | Not for the EPA spread. M1 regressed the team GB on real-time MCCC shocks (-0.09, t -0.49). | Yes, but only 2010-01 to 2025-06 (186 months). | Exploratory run: alpha 6.7% (t 2.13) against 4.9% (t 1.52) on the same months, with a negative shock loading (t -2.21). The pass is knife-edge (other specifications give t 1.06 to 1.97), and DSR still fails. The fail reading ("its returns came from a shock in climate concern") is backwards on our data. |
| 7 | Data audit: ALFRED vintages for CPI and EMV, emissions source | Partly. CPI gap (replication.md item 2) and the corrected baseline; emissions provenance (M4); modules note that FRED data are final vintages. | Yes. ALFRED is reachable; I downloaded three vintages. | EMV **passes**. The 2024-06-15 vintage equals the current file in all 473 months. The 2022-09-15 vintage differs only in its last month, 2022-08 (0.563 against 0.544). The zero regime is in real-time data (37 zeros through 2024-05 in both). The 2025-12-20 CPI vintage also lacks October 2025, so the gap was real-time. That gap already fails the "< 0.1 pp" bar and is documented. The emissions source cannot be audited because none exists. |
| 8 | Pre-registered crash stress, 1932 and 2009 | 2009 for the EW book (M5: -38.75% in 2009-04; Daniel-Moskowitz bear beta -0.53, t -2.94). The book's own 2009 numbers were not tabulated; computed here as -12.8% (worst month), -17.5% (Mar-May) and -24.1% (max drawdown). | 2009: yes. 1932: only inside the frozen run; run on its own, it spends the unseen window. | The pass bar is untestable as written: no drawdown budget is stated. |
| 9 | ETF proxies with 25 bp costs | 25 bp on FF49 portfolios: EW book (alpha -0.14%) and team strategies (M2). ETF proxies: no. | 25 bp on the book: yes, by rerunning M5. ETF proxies: no. No ETF prices are in `data/raw`, and many FF49 industries have no ETF. | At 2.92 turnover a year, 25 bp costs about 0.44% more than 10 bp, leaving a full-sample alpha of about 1.7% (my arithmetic, not run). The holdout alpha is already negative before extra costs. |
| 10 | Carbon frontier re-run on pre-1970 data | Post-1970 only (b = -1: IR change -0.005, CI -0.110 to +0.096). | Yes, inside the frozen run. | Almost certainly "not significant", because power is low and the ranking is the undated team file applied to 1930s industries. Non-significance does not show the constraint is free. Use an equivalence bound, for example a CI lower limit above -0.1 IR. |

Other checks recommended in the body of the reply:

| Recommendation | Done? | Feasible? | Result or likely result |
|---|---|---|---|
| Grid as a distribution (share positive, median t) | Partly (M2 counts) | Yes | Computed: 54% positive, median t 0.13. Holdout: 2.2% positive, median -1.34 (see 14). |
| BY on the 8,091 grid | No | Yes | 0 positive survivors: BY rejects a subset of BH, and BH rejects none. |
| Romano-Wolf on the grid | No | Needs the M2 series regenerated | Could flag a 24-month COVID cell (see 13). It would not flag anything implementable. |
| Composite of the six variants | No | Yes | Holdout composite -2.1% a year. Scale the variants first (see 18). |
| Lo (2002) autocorrelation correction | No | Yes | Computed: EPA SR 0.52 to 0.42; book post-2010 0.70 to 0.63; full sample unchanged. |
| Nyholt M_eff | No | Yes | Computed: optimizer paths 6.4 (raw) and 8.1 (residual); M4 GB variants 7.8 and 8.1; team six 3.0. |
| Book minus unconstrained alpha at b = -1 | Yes, post-1970 (M5) | Yes | Post-1970: differences 0 to +0.34%, none significant. |

## Coverage of the prompt's requests

| Request | Covered? | Note |
|---|---|---|
| 1. Families | Yes | Sound structure. Errors in 7, 13 and 17. |
| 2. Deflated Sharpe | Yes | Formulas and arithmetic correct. The UMD attribution is wrong (26), and N = 2 is lenient for the EPA spread (34). |
| 3. At most two candidates, with exact tests | Yes | Window, emissions file and pass bar need fixing (41, 46, 48). |
| 4. The one check | Yes | Power is low (56, 57). |
| 5. Committee objections | Yes | 59, 63 and 69 are wrong. |
| 6. At most ten checklist items | Yes | See the coverage table above. |
| Rules: word limit, guess labels, citations, no new signals | Mostly | Over the word limit (71). |

## What Claude missed

1. **Its two yardsticks for "best of many" disagree, and it gives no rule for choosing between them.**
   - DSR at least 0.95 with V = 1/(T-1) is equivalent to t at least E[max_N] + 1.645: 2.84 at N = 5, 3.10 at N = 8, 3.62 at N = 24.
   - A 5% max-t, Romano-Wolf or SPA test needs only the 95th percentile of the maximum: 2.32, 2.49 and 2.86 at the same N.
   - The book's t of 3.07 falls between the two, so checklist items 2 and 4 can return opposite verdicts on the same alpha.
2. **The binding fact for the book is decay, and no in-sample correction addresses it.**
   - The alpha went from 2.99% in validation (t 1.78) to -0.34% in the holdout.
   - No decade's alpha is significant after BH (M5 section 7).
   - A pre-1970 pass would answer "was it there before 1970", not "is it there now".
3. **The candidate's carbon side rests on the discredited team file.**
   - Freezing b = -1 on that file freezes a ranking that M4 found has no source and puts Aero and Ships near the top.
   - Switching to the EPA ranking covers all 49 industries, which changes convention X's universe. That choice has to be made before the frozen run.
4. **Margins and composites need a common scale.** Strategy volatilities in this project run from 1.4% (continuous team variants) to 18% (EW book). A ±2% margin or an equal-weight alpha average means different things for each.
5. **The fail reading of the frozen run.** With power of 0.2 to 0.6, the run needs a pre-registered reading of a fail, or a fail will be over-read.

## Notes on our own prompt

- **"No module computed a strategy return before 1970" is not accurate.**
  - The inherited team pipeline (`lib/team_pipeline.py`) produces Always-short Brown returns from 1934-07 and buy-and-hold Green-minus-Brown returns from 1926-07.
  - M6 saved the hedged Brown-leg residual from 1931-07 (`M6_factor_timing_team_brown_residual.csv`).
  - No momentum or optimizer return exists before 1970, so the book's window is still unspent. The prompt should say that instead.
- **The prompt placed "UMD beta 0.99" next to the EW book's alphas in item 9 without naming that book.** That probably caused Claude's misattribution in 26 and 59. The optimizer book's UMD beta is 0.27.
- **The prompt did not say which emissions file the optimizer uses.** Claude filled the gap with the 2022 EPA vintage from item 6.
- **Of the "155 primary" tests, 67 are not alpha tests.** Any project-wide family has to be defined by hypothesis type, not by the label.
