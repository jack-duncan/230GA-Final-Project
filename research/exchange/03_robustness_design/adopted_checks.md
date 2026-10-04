# Adopted checks for M7: the project-wide robustness ledger

Written 2026-09-26, after exchange 3 (robustness design) and its fact-check. This file turns the parts of Claude's design I kept, with the fact-check's corrections, into checks another person can code without asking me. M7 reads the eight module ledgers and the saved monthly return series, writes only `outputs/tables/M7_*` and `outputs/figures/M7_*`, and changes no module output. Paths are relative to `/home/hashim/projects/GA/project/research`.

Check 7 is a pre-registration. When M7's `run.py` starts, before any pre-1970 strategy return exists, it writes the SHA-256 of this file, the SHA-256 of `modules/M5_industry_momentum/optimizer.py` and of `m5lib.py`, and a UTC timestamp to `outputs/tables/M7_preregistration_hash.csv`. After that no choice in this file changes. A clear coding error against this text is fixed only as a listed deviation with before-and-after numbers, the rule M8 used (its C31).

## 0. Conventions for every check

- **G1. Returns.** Monthly decimals, net of costs as stored by the module that made them. Alphas are annualized by 12, volatilities by √12.
- **G2. Alpha inference.** Alpha is the OLS intercept. Standard errors are Newey–West with 6 lags, Bartlett kernel and no small-sample scaling: `sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": 6}, use_t=True)`. p-values come from t(n − k), with k the number of regressors plus 1. "One-sided" always means H1: α > 0.
- **G3. Factors.** FF5+UMD is Mkt-RF, SMB, HML, RMW, CMA (2x3) and UMD from `lib/common.load_ff5_mom()` (Ken French, Aug-2026 vintage, from 1963-07). FF3 comes from `lib/common.load_kf_ff3()` (from 1926-07). Before 1963-07, UMD comes from the raw file `data/raw/kf_F-F_Momentum_Factor.csv` (from 1927-01), parsed with `common._kf_sections` and `common._kf_monthly` as in `exchange/03_robustness_design/checks/fc03_extra.py`.
- **G4. Windows.** Full 1970-01 to 2026-07 (679 months); post-2010 2010-01 to 2026-07 (199); validation 2010-01 to 2022-07 (151); holdout 2022-08 to 2026-07 (48).
- **G5. Appraisal ratio (AR).** Monthly AR = monthly α̂ / σ̂_e, where σ̂_e is the standard deviation of the OLS residuals with ddof = k. Annual AR = √12 × monthly AR. Residual skewness γ3 = `scipy.stats.skew(e, bias=False)`; raw kurtosis γ4 = `scipy.stats.kurtosis(e, fisher=False, bias=False)`.
- **G6. Bootstrap.** Seed 20260926 (`numpy.random.default_rng`), B = 5,000 draws. Stationary bootstrap (Politis and Romano 1994) with mean block length 12: the first index is uniform on 0..T−1, and each later index is a fresh uniform draw with probability 1/12 and otherwise the previous index plus one, modulo T. All series and factors in a family are resampled with the same index vector.
- **G7. Ledger.** `outputs/tables/M7_robustness_tests_ledger.csv` has the nine standard ledger columns plus `p_value_one_sided`, `alternative` and `family`. Every number M7 quotes has a row. Only check 7's statistic (i) is labelled `primary`; the other rows of checks 2 to 8 are `robustness`, and the rows of checks 1 and 9 are `descriptive` or `exploratory`.

## 1. Test census and family map

Input: the eight ledgers `outputs/tables/*_tests_ledger.csv`, 23,923 rows.

**Type.** The first rule that matches, as a case-insensitive regex on `statistic_name`:
1. beta-timing: `beta-timing`
2. loading: `loading|t_b_|t_NW6_b_`, or the tag `[loading]` in `note`
3. alpha: `alpha`
4. mean: `mean`
5. other: everything else

**Family.** The first rule that matches:

| Family | Rule | Rows | Treatment |
|---|---|---|---|
| F, frozen and hash-verified | `test_id` is `M8_share_i_alpha_nw6`; check 7 (i) joins once run | 1 | Holm, one-sided (check 2) |
| P, module primaries (alpha) | label `primary`, type alpha, module not M8 | 81 | Holm and BH, one-sided (check 2) |
| D, other primaries | the remaining `primary` rows: 66 non-alpha rows in M1 to M6 and M8's 7 pass-bar components | 73 | raw p, no correction |
| X, placebo and reference | label `placebo` or `reference` | 170 | calibration only |
| L, loadings and beta-timing | type loading or beta-timing | 4,850 | confidence intervals only, never evidence |
| R, robustness alpha grids | M2 rows whose `test_id` ends in `\|alpha`, plus other modules' `robustness` rows of type alpha | 9,337 | BH and BY, one-sided, as distributions (check 3) |
| E, exploratory | everything else | 9,411 | no correction, never evidence |

R splits into R-M2 (8,161 rows; M2's own grid family has 8,091, and the difference changes no survivor count) and R-other (1,176: M1b 736, M4 282, M3 156, M6 2).

**Output.** A family-by-module count table, and a nominal census: rows with two-sided p < 0.05 by type, with alphas split by sign. Expected: 4,184 rows, of which 1,624 alpha (783 positive, 841 negative), 1,325 loading, 561 mean, 536 other and 138 beta-timing. No pass bar. In the report the census replaces the prompt's "about 4,200 nominal hits"; loadings are 32% of them.

## 2. Family P: the module primaries, one-sided Holm and BH

1. Collapse exact duplicates among the 81 P rows: same module, `n_obs`, statistic (to 1e-8) and two-sided p (to 1e-10). These are Original and Pure variants that coincide once the CPI gap is corrected (6 pairs in M2, 2 in M3), which leaves m = 73.
2. One-sided p: p1 = p2/2 if the statistic is positive, else 1 − p2/2. M3's rows store the alpha estimate rather than t, with the same sign. p-values are used as each module recorded them.
3. Holm at 5% (valid under any dependence) and BH at 5%.
4. Romano–Wolf is not run on P. The best one-sided p is 0.030 (M2, u5 Pure 6m, post-2010, t = 1.89), which survives a 5% family-wise correction only if the effective number of tests is below 1.7 (Šidák), so no dependence adjustment can change the answer.
5. Expected: smallest Holm p 1.00, smallest BH p 0.72, no survivors. Reading: no labelled primary alpha survives a project-wide correction. This confirms the verdict and cannot change it.

**Family F.** Holm over its two one-sided p-values (M8: 0.605). Check 7 (i) requires t ≥ 2.00 at 457 degrees of freedom, a one-sided p of at most 0.023, which already clears Holm's 0.025 bar, so F adds no hurdle of its own. It is reported so that the frozen tests are corrected as a family.

## 3. Family R: the robustness grids as distributions

1. One-sided BH and BY at 5%, positive side only, for R-M2, for R-other by module, and for R pooled. BY is BH run at q / Σ_{i≤m} 1/i (the divisor is 9.58 at m = 8,091; Benjamini and Yekutieli 2001).
2. R-M2 by window, where the window is the third-from-last `|` field of `test_id` (full_live, full_1970, post2010, validation, holdout, pre_covid, covid, inflation_rates, last18, last12): count, share with a positive statistic, and median t.
3. Expected on the 8,161 rows: 54% positive with median t 0.13 overall; validation 89% (median 1.15); holdout 2.3% (median −1.34); last 18 months 0% (median −2.35). BH and BY: no positive survivors.
4. No pass bar. The grid is a sensitivity analysis, and its message is the pattern across windows: gains in validation, losses in every later window.

## 4. Search families: Romano–Wolf max-t and Hansen's SPA

Purpose: decide whether the best alpha in the project is distinguishable from zero once every series I could have presented as "the strategy" is counted.

**Membership.** A series enters a family if it is a strategy (not a benchmark, placebo or reference) and has a return in every month of the family window. A timing strategy whose signal ends early is flat, with zero return, after its last signal month.

- **S-full**, 1970-01 to 2026-07 (679 months), M = 58:
  - the 24 optimizer paths: every column of `M5_industry_momentum_optimizer_returns_monthly.csv`;
  - the equal-weight (EW) primary book: column `net` of `M5_industry_momentum_returns_monthly.csv`;
  - the 8 EW robustness variants (the non-primary rows of `M5_industry_momentum_robustness.csv`) and the 10 carbon screens (the non-primary rows of `M5_industry_momentum_carbon_screens.csv`), regenerated by calling `m5lib` with the arguments M5's `run.py` uses. Each must reproduce its table row (full-sample Sharpe and FF5+UMD alpha, to 1e-6) before use;
  - the 15 green-minus-brown variants of M4: every column of `M4_emissions_gb_monthly_returns.csv` except `date` and `epa5_minus_team5`, which is a difference of two members.
- **S-post**, 2010-01 to 2026-07 (199 months), M = 89: S-full restricted to the window, plus
  - the six team rules: `run_pipeline(bootstrap_reps=0)` from `lib/team_pipeline.py`, keys not starting with `Benchmark`;
  - the 12 real-time MCCC and CPU rules of M1b (six rules per measure), regenerated as `modules/M1b_alt_signals/run.py` builds its primary grid. Each must reproduce its validation alpha t in the M1b ledger to 1e-6;
  - 13 M6 series: the `:net` columns of `M6_factor_timing_portfolio_returns.csv` for `timing_ridgecv`, `timing_ols_lambda0`, `timing_combination`, `lmn_sign` and `lmn_raw` (12), and `rotation_ridge` from `M6_factor_timing_rotation_returns.csv`.
- **Left out, with reasons.** Benchmarks (Always-short Brown, `prevailing_mean`, `static_long`, `static_long_meanabsw`, `industry_mom_12_1`); M8, whose window is 1994–2009; placebos; and M2's grid, whose series are not saved and which varies legs, hedges and costs around the same six rules (those six have a Nyholt M_eff of 3.0). Leaving M2 out makes both tests slightly lenient, and the report says so.

**Statistic.** For each member i: the FF5+UMD alpha α̂_i, its NW(6) standard error s_i, and t̂_i = α̂_i / s_i.

**Null bootstrap.** Subtract each series' monthly α̂_i from its returns, resample months of the demeaned returns and the factors jointly (G6), refit OLS in each draw, and form τ*_ib = α*_ib / s_i with the original s_i.

**Romano–Wolf stepdown** (Romano and Wolf 2005). Order t̂_(1) ≥ … ≥ t̂_(M). For j = 1, …, M, p̃_(j) = (1 + #{b : max_{k≥j} τ*_(k)b ≥ t̂_(j)}) / (B + 1), and the adjusted p_(j) = max_{l≤j} p̃_(l). Report the adjusted p of every member. A member passes if its adjusted p ≤ 0.05.

**SPA, consistent version** (Hansen 2005). T_SPA = max(0, max_i t̂_i). In each draw, T*_b = max(0, max_i [τ*_ib + t̂_i · 1{t̂_i < −√(2 ln ln n)}]), with n the number of months (the threshold is 1.94 at n = 679 and 1.83 at n = 199). p = (1 + #{b : T*_b ≥ T_SPA}) / (B + 1).

**Also report** each family's Nyholt and Li–Ji M_eff (check 5, step 2) and the Šidák count at which the best t̂ stops being significant at 5%.

**Reading.** The book's full-sample t of 3.07 (one-sided p 0.0011) survives a 5% max-t test only if the effective number of series is below about 46, so a pass is plausible. A pass means "distinguishable from zero after the search", nothing more. Check 5 decides whether the alpha is large enough to bank.

## 5. Deflated appraisal ratio

**Candidates.** The optimizer book (`X_unc`) and the EPA 5v5 spread (`epa5`), each in S-full (full window) and in S-post (post-2010 window). A candidate must pass in both windows, which removes the freedom to quote the better one.

1. **AR inputs** (G5): monthly AR, T, γ3 and γ4 from the candidate's FF5+UMD regression on the window; t_NW, the NW(6) alpha t; and t_OLS, the classic OLS alpha t.
2. **Effective trials**, from the family's FF5+UMD OLS residuals: their correlation matrix R and its eigenvalues λ. Nyholt (2004): N_eff = 1 + (M − 1)(1 − Var(λ)/M), with Var using ddof = 1. Li and Ji (2005): the sum, over λ clipped at 0, of 1{λ ≥ 1} + (λ − ⌊λ⌋). Nyholt governs; Li–Ji and the raw M are sensitivities.
3. **Cross-trial variance.** Cluster the family's residual series with distance d_ij = √(0.5(1 − ρ_ij)), `scipy.cluster.hierarchy.linkage(method="average")` and `fcluster(criterion="maxclust", t=K)`, K = round(N_eff). Each cluster's series is the equal-weight mean of its members' returns. V_cl is the variance (ddof 1) of the K clusters' monthly ARs, and V = max(1/(T − 1), V_cl).
4. **Expected maximum** (Bailey and López de Prado 2014): SR0 = √V × E_N, with E_N = (1 − γ)Φ⁻¹(1 − 1/N) + γΦ⁻¹(1 − 1/(N·e)), γ = 0.5772156649 and N = N_eff (non-integer allowed; SR0 = 0 if N ≤ 1).
5. **DSR.** With the monthly AR, z = (AR − SR0)√(T − 1) / √(1 − γ3·AR + ((γ4 − 1)/4)·AR²) and DSR_iid = Φ(z). For serial correlation, DSR_NW = Φ(z · t_NW / t_OLS). The governing DSR is min(DSR_iid, DSR_NW).
6. **Report** the governing DSR at N_eff (Nyholt) with V from step 3; the same at the Li–Ji N, at the raw M, and with V = 1/(T − 1); and, as context only, the raw-Sharpe DSR and Lo's (2002) annualized Sharpe η(12)·SR_monthly, with η(q) = q / √(q + 2 Σ_{k=1}^{q−1} (q − k) ρ_k).
7. **Pass bar:** governing DSR ≥ 0.95 in both windows. Expected, from the fact-check's partial inputs: both candidates fail. The book's AR of 0.40 passes only for N ≤ 6 or 7, and the 24 optimizer paths alone give N_eff of 6.4 to 8.1 (DSR 0.939 at N = 8). The EPA spread's raw-Sharpe DSR is 0.906 at N = 2 once scaled for serial correlation.

**Rule between checks 4 and 5, fixed now.** A max-t pass with a DSR fail reads "survives the search as nonzero, not bankable after selection". Only the DSR can move a verdict.

## 6. Holdout reading in appraisal-ratio units

**Series.** The optimizer book, the EW book, the EPA spread, the six team rules, and Always-short Brown as a reference. The model is FF5+UMD on the 48 holdout months (k = 7, 41 degrees of freedom), with FF3 as a sensitivity for the team rules, which were evaluated on FF3.

1. α̂ and its NW(6) standard error SE; the 90% interval L = α̂ − 1.683·SE, U = α̂ + 1.683·SE (1.683 = t_{0.95, 41}).
2. **Margin.** δ = 0.25 × the annualized residual volatility of the same regression, a quarter of an appraisal ratio. Grinold and Kahn (2000) put a top-quartile information ratio at about 0.5, and a book below half of that does not pay for its risk budget. The margin scales with each strategy's risk, which a fixed ±2% cannot do when volatilities here run from 1.4% (continuous team rules) to 18% (EW book).
3. **Reading,** first match: L > 0 and U < δ, "positive but below the worthwhile margin"; L > 0, "confirms a positive alpha"; U < δ, "rejects a worthwhile alpha" (evidence against); otherwise "inconclusive" (insufficient evidence).
4. Also report the minimum detectable alpha at 80% power, (t_{0.95, 41} + t_{0.80, 41}) × SE.
5. Expected, from the fact-check's FF3 figures: the four team hold rules reject (their 90% intervals lie wholly below zero), and the book is inconclusive (about −4.1% to +3.4% against δ of about 1.4%).

## 7. Frozen 1931–1969 run of the optimizer book (pre-registration)

**Question.** Did the optimizer book's edge over UMD exist before 1970, in months on which no strategy of this kind has been computed in this project?

**What I had seen before writing this.**
- No momentum or optimizer return, residual or alpha before 1970 has been computed. From pre-1970 data I have seen only availability counts (40 FF49 industries in 1926-07, 43 from 1931-07 through 1962 and 49 from 1969-07; Soda, FabPr, Guns and Gold start in 1963-07, Softw in 1965-07 and Hlth in 1969-07, so 37 of the 41 covered industries exist before 1963), each file's first month, and the fact that from 1963-07 on the FF3 and FF5 files carry identical RF series and Mkt-RF series that differ by at most 0.0008 a month.
- Other pre-1970 series exist on disk, and none is a momentum book: the team pipeline's Always-short Brown (from 1934-07) and buy-and-hold GB (from 1926-07), and M6's hedged Brown residual (from 1931-07).
- The window is unseen for this book, not for the field. UMD from 1927 is public, and industry trend rules have been tested over roughly a century (Zarattini and Antonacci 2024). The FF3+UMD benchmark removes the generic momentum premium, so the test asks the narrower question of whether the book beats UMD.
- The book's post-1970 numbers were known: FF5+UMD alpha 2.17% (t = 3.07), FF3+UMD 2.01% (t = 2.84), residual volatility 5.44%, UMD beta 0.27, holdout alpha −0.34% (t = −0.15).

**Frozen specification.**
1. Code: `modules/M5_industry_momentum/optimizer.py` and `m5lib.py`, unchanged and hashed at M7 start.
2. Book: the unconstrained Grinold–Kahn book, called as M5 calls it (`optimizer.precompute`, then `optimizer.run_path` with b = 1e3 and κ = cost = 10 bp). That fixes IC = 0.05 (monthly units), the 60-month window, Ledoit–Wolf covariance with sklearn defaults, ex-ante tracking volatility of 5% a year as a constraint, the box |h_i| ≤ 0.10, Σh = 0, the Clarabel solver via cvxpy with M5's settings, and a zero starting book, so the first month pays full entry costs.
3. Universe: the 41 industries covered by the team emissions file (convention X: M5's `covered` list, with `cm["X"]` as the carbon input), used only as a fixed list of names. M5's eligibility rule is unchanged: 60 complete months of returns, a momentum signal, and a return in t+1. The file's intensity values play no role in the unconstrained book.
4. Inputs: industry returns `R` from `m5lib.load_inputs()` (the team FF49 file, from 1926-07); the signal `m5lib.mom_signal(R, 11, 1)`; and, in place of M5's `ff5`, a frame with `Mkt-RF` and `RF` from `load_kf_ff3()`, because FF5 starts in 1963-07.
5. Dates: formation month-ends 1931-06 to 1969-11, so return months 1931-07 to 1969-12 (462 months). No return from 1970-01 on is recomputed here.
6. Statistic (i): the FF3+UMD alpha of net returns, NW(6), one-sided p from t(457).
7. Halves (ii): the same regression on 1931-07 to 1950-09 and on 1950-10 to 1969-12, 231 months each.
8. δ = 0.25 × the annualized residual volatility of the full-window regression, and U = α̂ + 1.648·SE (1.648 = t_{0.95, 457}).

**Dry run.** Before the frozen run, the same call with M5's own `ff5` over formation months 1969-12 to 1970-11 must reproduce M5's `X_unc` net returns for 1970-01 to 1970-12 to 1e-8. The call is then repeated on the same months with the FF3 inputs, and the largest absolute difference is reported. Neither step can change a choice above. The frozen run then executes once.

**Pass bar and readings, fixed now.**
- **PASS:** α̂ > 0 with t ≥ 2.00 (one-sided p ≤ 0.023), and both halves' alphas above zero. Reading: the book's edge over UMD existed in 38.5 unseen years. The book moves to "paper-trade at pilot size", and the report's verdict stays "Do not implement" because the 2022–2026 holdout alpha is −0.34% (check 10).
- **REJECT:** not PASS, and U < δ. Reading: the 90% interval excludes a worthwhile alpha, so the post-1970 alpha is a product of that sample or of the search. Retire the book.
- **INCONCLUSIVE:** anything else. Reading: the unseen sample cannot settle the question. The book stays exploratory, and "Do not implement" rests on checks 5 and 6.

**Operating characteristics** (my calculation from post-1970 moments, with the halves treated as independent; not a pre-1970 number). Under a true zero alpha: PASS 0.02, REJECT 0.47, INCONCLUSIVE 0.50. Under a true 2% alpha: PASS 0.62, 0.32 or 0.20 at 1, 1.5 or 2 times the post-1970 residual volatility, and REJECT 0.01, 0.05 or 0.11. A fail is likely even if the alpha is real, which is why a fail has two readings.

**Dropped from Claude's pass bar.** The DSR clause, because a single frozen trial has N = 1 and the clause then duplicates (i). "No significant carbon cost", because it rewards low power, and a ranking of unknown date says nothing about carbon in the 1930s.

**Secondary rows** (reported, never part of the verdict):
- S1. The FF5+UMD alpha on 1963-07 to 1969-12 (78 months; a standard error of about 2.1% a year, so uninformative).
- S2. The b = −1 book (carbon input `cm["X"]`, as in M5) minus the unconstrained book: the net IR difference, with a paired circular block bootstrap (block 12, B = 5,000, seed 20260926) and its 95% interval. "No carbon cost" is stated only if the lower bound is above −0.10. This tests a portfolio restriction, not a climate claim.
- S3. Crash profile: worst month, worst three-month compounded return and maximum drawdown of compounded net wealth, 1932 included.
- S4. The FF3+UMD alpha at 25 bp realized costs, net = gross − 0.0025 × turnover.
- S5. The realized rank IC of the 11-1 signal: the monthly Spearman correlation between eligible industries' signal z-scores and next-month returns, its mean and NW(6) t, against the assumed 0.05.

## 8. Cost stress on the book

From `M5_industry_momentum_optimizer_paths_monthly.csv`, path `X_unc`, fields `gross` and `turnover`: net_c = gross − c × turnover for c in {0, 10, 25, 50} bp, with holdings unchanged (the optimizer is not re-solved). Report the FF5+UMD alpha and t for the full, post-2010 and holdout windows. The break-even cost is c* = α(gross) / α(turnover), where α(turnover) is the intercept of the turnover series regressed on the same factors; OLS is linear in the dependent variable, so α(gross − c·turnover) = α(gross) − c·α(turnover). **Pass bar:** full-sample alpha above zero at 25 bp. A fail means the alpha exists only at stylized costs. ETF proxies are not run: `data/raw` holds no ETF prices, and many FF49 industries have no ETF.

## 9. Descriptive and exploratory rows

- **Crash profile of the book after 1970**, from the fact-check: worst month 2009-04 at −12.8%, March to May 2009 −17.5%, maximum drawdown −24.1% (trough 2010-01). No drawdown budget is set, because one chosen now, after seeing 2009, would be post hoc.
- **EPA spread with climate-concern shock controls.** Log the regressions of `exchange/03_robustness_design/checks/fc03_extra.py` as exploratory. On the 186 post-2010 months with MCCC data, the FF5+UMD alpha is 4.9% (t = 1.52); adding a same-month MCCC shock raises it to 6.7% (t = 2.13), with a shock loading of −0.52% a month per standard deviation (t = −2.21). The lagged shock gives t = 1.06, the transition shock 1.95 and the CPU shock 1.97. It is not a pass test: I have already seen it, Claude's reading of a fail is backwards on our data, and the pass depends on the specification.
- **Data provenance**, from `exchange/03_robustness_design/checks/out/`: the 2024-06-15 ALFRED vintage of EMVENRGYENVREG equals the current file in all 473 months, and the 2022-09-15 vintage differs only in 2022-08; the 2025-12-20 CPIAUCSL vintage also lacks October 2025, so the CPI gap was real-time; the emissions file has no source, units or date. Labelled descriptive.

## 10. Verdict map, fixed now

For each candidate, the optimizer book and the EPA spread:
- **Implement** requires all four: (a) a hash-verified confirmatory alpha test passes (family F; for the book, check 7 PASS; the EPA spread has none); (b) Romano–Wolf adjusted p ≤ 0.05 in S-full and in S-post; (c) governing DSR ≥ 0.95 in both windows; (d) a positive holdout α̂ and a check 6 reading other than "rejects".
- **Paper-trade**, with the report's verdict still "Do not implement": (a) holds and any of (b) to (d) fails.
- **Do not implement:** (a) fails.

The attention thesis is "Do not implement" whatever M7 finds: M8 failed, family P's smallest Holm p is 1.00, and the holdout rejects a worthwhile alpha for every hold rule. On current numbers, (d) already fails for the book (holdout α̂ −0.34%) and the EPA spread cannot meet (a). No candidate can reach "implement" within this project; the frozen run decides only whether the book is retired or paper-traded.

## Not adopted from the reply

- One family of all 155 "primaries": 67 of them are not alpha tests, and M1's Fisher test (p 1e-32) would "survive". Replaced by P and D.
- Romano–Wolf on the primaries: the answer is foregone (check 2, step 4).
- A composite of the six team variants: it can only be pre-specified for unseen data, and the attention rules have none left after M8 spent 1994–2009. The holdout composite is −2.1%.
- The ±2% equivalence margin: replaced by δ = 0.25 AR (check 6).
- ETF proxies and a crash budget: checks 8 and 9 give the reasons.
- The pre-1970 carbon frontier as a pass test: moved to secondary row S2.
