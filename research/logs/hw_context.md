# Homework context digest for the MFE 230GA final project

Written 2026-09-26 from the HW1 and HW2 materials and the halfway WhatsApp log. Every number carries a source tag. "derived here" means I recomputed it while writing this digest (plain pandas on the files named); nothing in the team repo was modified or run.

Source tags

| Tag | File |
|---|---|
| HW1tex | /home/hashim/projects/GA/HW1_merged.tex (submitted HW1, line numbers given as L###) |
| NB1 | /home/hashim/projects/GA/230GA__PS1.ipynb (HW1 Problem 4 code, re-executed after Q4 corrections) |
| Q4corr | /home/hashim/projects/GA/Q4_corrections.md |
| Q5ans | /home/hashim/projects/GA/Q5_answer.md |
| Q5gpt | /home/hashim/projects/GA/Q5_chatgpt_response.md (ChatGPT round-2 reply) |
| Q5crit | /home/hashim/projects/GA/Q5_round1_critique.md (critique of the round-1 reply) |
| HW2pdf | /home/hashim/projects/GA/homework 2 2025.pdf |
| HW2body | /home/hashim/projects/GA/HW2/hw2_body.tex |
| HW2notes | /home/hashim/projects/GA/HW2/REVIEW_NOTES.md |
| Q4prompt | /home/hashim/projects/GA/HW2/q4_prompt.txt |
| Q4reply | /home/hashim/projects/GA/HW2/q4_chatgpt_reply.md |
| Q4crit | /home/hashim/projects/GA/HW2/q4_critique.md |
| Q4sec | /home/hashim/projects/GA/HW2/q4_sections.py (holds the written HW2 Q4 summary, feasibility table and HW01 comparison that are spliced into hw2.tex) |
| Q4chk | /home/hashim/projects/GA/HW2/hw2_q4_checks.py |
| WA | /home/hashim/projects/GA/project/research/logs/whatsapp_halfway.md |
| TeamNB | /home/hashim/projects/GA/project/230GA-Final-Project/notebooks/climate_alpha_analysis.py (read only) |

---

## 1. HW1: what it asked and what we found

Team (HW1tex L111-120): Hashim Almodamagha, Aditya Aryan, Jack Duncan, Charishma Takkallapalli, Cristhian Ruiz Cardozo (spelled "Christhian" in WA). Group number is inconsistent: Q4corr L35 says the header said Group 4 and the footer Group 5; HW1tex now sets both to Group 4 through one macro. Confirm before the final report.

### 1.1 Problems 1 to 3 (portfolio math, useful as formulas)

- P1 two assets, sigma 30% and 40%, rho 0.5. h_P = (0.55, 0.45) gives sigma_P = 29.89%; against a 50/50 benchmark psi = sqrt((h_P - h_B)' V (h_P - h_B)) = 1.80%; minimum-variance h_C = (10/13, 3/13), sigma_C = 28.82% (HW1tex L123-287).
- P2 minimum active risk holding N = 20 equal-weighted names against an M = 500 equal-weighted benchmark, sigma = 25%: psi_min = sigma sqrt(1/N - 1/M) = 5.48%; a cap-weighted benchmark lowers it (HW1tex L290-317).
- P3 fundamental law IR = IC sqrt(BR) TC with TC = 1: Fischer IC 0.05 on 500 bets equals Myron IC 0.08 on N = 195.3, so 196 asset classes per quarter (HW1tex L319-347).

### 1.2 Problem 4: emissions tilts, high vs low emitters, factor exposures

Data (NB1 cells 0-12; derived here):
- FF_49_Returns.csv: 49 value-weighted FF industry returns in percent, Jan 1970 to Jul 2022 (631 months), plus mktrf, smb, hml, rf. No momentum (UMD) column.
- Emissions_FF_Industry.csv: 41 industries, one static snapshot. It is byte-for-byte the same data as the team's data/emissions_ff_industry.csv (max abs difference 0.0, derived here). Missing: Oil, Chips, FabPr, Gold, Hshld, LabEq, Other, Toys.
- Ranking. Dirtiest: Util 3.264, Ships 1.019, Aero 0.531, Steel 0.403, BldMt 0.365. Cleanest: Fun 0.00054, RlEst 0.00465, Drugs 0.00470, Telcm 0.00565, Fin 0.00914. Next dirty: Chems 0.269, Trans 0.219, Mines 0.196, Coal 0.163. Next clean: Autos 0.00922, Insur 0.01024, Hardw 0.01266, MedEq 0.01266, Banks 0.01633 (Emissions_FF_Industry.csv). Util is 3.2x Ships.
- Data-quality flag (derived here): several intensities are exact ties (Hardw = MedEq; Clths = Txtls; Beer = Food = Smoke = Soda), which suggests the values were assigned at a coarser sector level and mapped onto FF49. The Hardw/MedEq tie decides the eighth Green industry in any 8/8 build.

Construction (NB1 cells 13-14): Low5 and High5 are equal-weighted averages of the five VW industry returns; Green = Low5 minus High5, zero cost, rebalanced monthly.

(a) Individual industries, 1970 to Jul 2022 (HW1tex L356-380). No gap between groups. Util, the dirtiest, has the best Sharpe (0.78) and the smallest drawdown (-42.4%); RlEst, second cleanest, has the worst Sharpe (0.29) and drawdown (-85.6%). These are raw Sharpe ratios (mean/vol, no rf); excess-return Sharpe ranges from 0.13 (RlEst) to 0.49 (Drugs) with the same ordering (Q4corr L36).

(b) Composites (HW1tex L386-415):

| Portfolio | Ann. mean % | Ann. vol % | Raw Sharpe | Max DD % |
|---|---|---|---|---|
| Low5 (Green) | 11.98 | 18.17 | 0.66 | -65.9 |
| High5 (Brown) | 12.13 | 18.78 | 0.65 | -58.4 |
| Green L/S | -0.15 | 9.58 | -0.02 | -58.7 |

Excess Sharpe High5 0.41, Low5 0.42 (Q4corr L36; verified derived here). Green L/S by regime (HW1tex L468, verified derived here): +1.94%/yr 1970-99, -5.69%/yr 2000-09, +2.34%/yr 2010-20, and -25.70% annualized mean over Jul 2021 to Jul 2022. That last figure is an annualized arithmetic mean over 13 months; the cumulative 13-month loss was -25.2% (derived here). The HW1 prompt calls it "-25.7% over the last 13 months", which reads as cumulative. Do not repeat that wording.

(c) FF3 regressions on excess returns (Green is not rf-adjusted because rf cancels), Newey-West 6 lags, OLS for the 13-month window (HW1tex L417-453; Q4corr table):

| Window | Port. | alpha ann % (t) | MKT b (t) | SMB b (t) | HML b (t) | R2 |
|---|---|---|---|---|---|---|
| Full 1970-2022, N=631 | High5 | -1.59 (-1.60) | 1.09 (53.8) | 0.16 (2.71) | 0.40 (7.95) | 0.85 |
| | Low5 | -0.76 (-0.89) | 1.07 (49.4) | 0.17 (4.43) | 0.17 (5.27) | 0.90 |
| | Green | 0.82 (0.60) | -0.02 (-0.70) | 0.02 (0.35) | -0.23 (-4.40) | 0.07 |
| 2010 to Jul 2022, N=151 | High5 | -0.39 (-0.22) | 1.11 (25.1) | 0.25 (2.54) | 0.40 (7.44) | 0.87 |
| | Low5 | -1.07 (-0.78) | 1.07 (32.3) | 0.20 (4.63) | 0.05 (1.45) | 0.92 |
| | Green | -0.69 (-0.27) | -0.04 (-0.82) | -0.05 (-0.43) | -0.35 (-6.58) | 0.18 |
| Jul 2021 to Jul 2022, N=13 | High5 | 16.58 (1.41) | 1.06 (5.83) | 0.67 (1.50) | 0.32 (1.38) | 0.81 |
| | Low5 | -9.06 (-1.08) | 1.09 (8.37) | 0.43 (1.33) | 0.20 (1.18) | 0.90 |
| | Green | -25.65 (-1.63) | 0.03 (0.13) | -0.24 (-0.41) | -0.12 (-0.40) | 0.03 |

Findings (HW1tex L446-453):
- Both legs are market beta about 1.06 to 1.11; Green is market neutral and size neutral. No portfolio has a significant alpha in any window.
- The story is HML. High5 loads 0.40 in both windows (dirty industries are structural value). Low5 falls from 0.17 to 0.05 (insignificant) after 2010, so Green goes from -0.23 to -0.35: a long-growth, short-value bet that got bigger over time. Hypothesis written in HW1: the clean leg (Fin, RlEst, growthier names) re-rated toward growth in the low-rate 2010s; emissions are not the driver.
- The 2021-22 loss (High5 +16.6%, Low5 -9.1%, Green -25.6% annualized alpha) came through alpha, not through HML (loading -0.12, t -0.40). An HML hedge alone would not have caught it.

Correction lesson (Q4corr): the first version regressed raw leg returns, so rf leaked into the intercept and produced fake significant alphas (High5 2.76%, t 2.75; Low5 3.59%, t 3.77). HAC lags were 4 in code and 6 in text. Both fixed; betas moved by at most 0.01.

### 1.3 Problem 5: the two ChatGPT strategy ideas and how they were critiqued

Process: round 1 prompt and reply (text not saved in these files), a written critique (Q5crit), a tightened round-2 prompt (Q5ans; HW1tex L480-499), the round-2 reply (Q5gpt), then a summary, a plausibility check against the four questions in the assignment, and a forward link (HW1tex L462-527).

Round-1 critique (Q5crit): it changed the universe from 5/5 to 8/8 without naming members, and its own 40% cluster cap would have bound once Insur entered; it said roughly one flip a year for the regime strategy, contradicting the four-regimes-in-52-years story; no backtest start date; it ran a pass/fail regression on the 13-month window (N = 13); the emissions link in Strategy B was thin; it sprawled (industry double-sort, MOM variant, commodity variant, 6m/12m lookbacks); cost guesses were not flagged up front. Each point became an explicit instruction in the round-2 prompt.

Round-2 reply (Q5gpt), shared construction: 8/8 equal-weight baskets, monthly rebalance, built by walking down the ranking with at most 3 rate-sensitive names per leg. Brown = the 5 plus Chems, Trans, Mines. Green = the 5 plus Autos, Hardw, MedEq (Insur and Banks skipped). Rate-sensitive share 37.5% of Green, 12.5% of Brown; single-name cap 20%, cluster cap 40%, neither binds on day one. Backtest starts Jan 1975 (60-month beta warm-up), 571 months to Jul 2022.

- Strategy A, factor-neutral emissions spread. Each month regress the last 60 months of G on Mkt-RF, SMB, HML and CMD = (Oil + Coal + Gold)/3 minus Mkt (built from FF49 industries), hold G minus beta times factors. Expected overlay: long 0.23 to 0.35 units of HML. 10% vol target, leverage clipped to [0.5, 2], retrade only when leverage moves more than 10%, and a 15% drawdown breaker that halves leverage until a new high-water mark. Verification regression on the hedged series: pass if realized |b_H| < 0.10 with |t| < 1 under NW(6) in full and 2010+ windows. Falsifier: emissions adds nothing if hedged alpha has |t| < 2 in both windows. Turnover guess about 1.8 units/yr; cost guesses 10 bps per unit for industry baskets, 25 bps for HML/SMB, 5 bps for Mkt, about 20 to 25 bps/yr drag.
- Strategy B, regime-switched Brown/Green. Signal m_t = trailing 12-month sum of HML; long Green if m_t < -2%, long Brown if m_t > +2%, else hold. Only market beta hedged; HML is left on because it is the trade. Required benchmark: the same rule applied to HML itself at 10% vol. Overfitting check: 12-month block bootstrap of the signal, 1,000 draws, Sharpe must beat the 95th percentile. 4 units traded per flip; 0.5 to 1.5 flips a year expected (60 to 120 bps/yr) against only 3 true regime turns in 52 years, so most flips are whipsaw. Falsifier: B adds nothing if alpha is zero against timed HML and B does not beat benchmark (iii).
- HML explanation: partly agreed with the hypothesis. The dirty leg's stable 0.40 is because emissions per unit of output proxies tangible-capital intensity. The clean leg is mixed (Drugs, Fun, RlEst fit the duration story; Fin benefits from rising rates); HML's own growth leg became mega-cap tech after 2010. Proposed test: FF3 regressions of each clean-leg industry on 1975-2009 and 2010-2022 separately. HML drop concentrated in Fin/Telcm means composition; in Drugs/Fun/RlEst means re-rating.
- 2021-22: agreed an HML hedge would not have helped (loss was alpha); CMD added for that reason, while admitting a 2016-21 CMD beta may be near zero and the rates half of the shock cannot be hedged without a rates series. 13-month window: SE of the mean 2.77%/sqrt(13) = 0.77%/month, so -25.7% is about 2.6 SE, but the window was chosen for being extreme; stress test only.
- Least-confident assumptions (Q5gpt L63-69): HML tradable at 25 bps; CMD catches a 2021-22 shock; 12-month HML momentum has timing power; static 2020-era ranking applied back to 1975 is mild look-ahead (Telcm, Fin changed character); 3%/month drift turnover is a guess; vol targeting will not fix a regime drawdown.

Plausibility check written in HW1 (HW1tex L513-519):
- HML constraint: A's rolling hedge is the right overlay for a slow -0.23 to -0.35 drift, and the pass criterion is checkable. But the hedge does not address what hurt in 2021-22. CMD is a fifth regressor on 60 observations with a beta ChatGPT expects near zero, so treat it as an experiment, not a control.
- Concentration: widening to 8/8 cuts Util from 20% to 12.5% of Brown and the cluster rule works at selection. But 8/8 changes the baseline, so the -0.23/-0.35 loadings must be re-established on 8/8; the added names are higher-beta cyclicals. The 20% cap only binds under the inverse-vol variant.
- Turnover: fine for A (the signal is static, so all trading is drift plus hedge). B's flip rate is the weak point: 3 real turns in 52 years against 0.5 to 1.5 expected flips a year makes B's turnover 3 to 6 times A's. It also flagged the look-ahead in calling Telcm and Fin clean in 1975.
- Robustness: uses the three windows with NW(6), adds a rolling 36-month b_H plot. Rates side of 2021-22 cannot be hedged with the HW1 data. Nit on B: estimate the beta of G and multiply by p_t, rather than estimating beta on p_t times G_t.

Forward link (HW1tex L523-527): chose Strategy A. Next tests: rerun 8/8; build the rolling 60-month hedge and check realized |b_H| < 0.10 in full and 2010+; split-sample FF3 regressions on each clean-leg industry; cost-aware version with measured drift turnover, 5/10/25 bps sensitivity, and a with/without CMD comparison over Jul 2021 to Jul 2022. Key risk: if hedged alpha is zero, the Green spread is "a growth-minus-value bet with a commodity short attached, not a climate factor", to be reported as a legitimate finding.

### 1.4 Momentum in HW1

Momentum was named but never tested:
- The HW1 data file has no UMD column (derived here), and no HW1 regression includes momentum (NB1 cell 17 uses mktrf, smb, hml only).
- The prompt nevertheless told ChatGPT the data included "the three Fama-French factors plus momentum" (HW1tex L496; Q5ans L35), and the forward link says Strategy A is backtestable "with the FF49 returns and the FF3 plus momentum factors" (HW1tex L523).
- The round-1 reply offered a MOM variant, cut as sprawl (Q5crit L16).
- Strategy B's signal is itself time-series momentum on HML, and "12m HML momentum has timing power" is ChatGPT's third least-confident assumption (Q5gpt L66).
This gap is why Christhian now asks for momentum controls (WA message 2 item 2; message 3).

---

## 2. HW2: what it asked and what we found

Assignment (HW2pdf): five problems, due 2025-08-31. Problems 3 and 4 use 20 US large caps with a Barra active-risk forecast omega (11.38% PG to 21.51% DOW), a broker BUY/SELL rating (11 BUY, 9 SELL), and an independent research-service alpha (-4.92% JNJ to +2.50% BA). Optimizer: maximize h'alpha - lambda h'Vh; with uncorrelated active returns h_i = alpha_i / (2 lambda omega_i^2); lambda = 0.125 (or 12.5 in decimal units) so that IR 0.5 gives 2% active risk. HW2 was reworked on 2026-09-13 as a learning exercise after submission (HW2notes).

### 2.1 Problem 1 (valuation, convention)
Gordon P/E = p/(r - g) = 0.5/0.04 = 12.5x forward = 13.75x trailing. Trading at 8x trailing and re-rating in a year: 95.94% (78.1% on a forward reading); staying at 8x: 16.875% (16.25% forward), which beats 14% because the same dividend is bought at a lower price (HW2body L2-65). Of the 95.9%, the re-rating contributes 79.1 points.

### 2.2 Problem 2 (IC, signal combination)
- alpha = c1 theta + c2 Z with IC 0.05, omega 25%: c1 = IC^2 = 0.0025, c2 = IC omega sqrt(1 - IC^2) = 0.01248. Conditions: Corr(alpha, theta) = IC and calibration E[theta | alpha] = alpha. The signal component has sd 0.0625% against 1.248% of noise (HW2body L70-111).
- Three sources, IC (0.10, 0.10, 0.09), corr 0.6 between 1 and 2, 0.1 with 3. Score weights c = C^-1 IC = (0.0576, 0.0576, 0.0785); alpha weights w = c/IC = (0.576, 0.576, 0.872); IC_combined = sqrt(c'IC) = 0.136. The least skilled source gets the most weight because it is nearly uncorrelated (HW2body L113-212).
- Equal-weighted alphas: IC_Eq = IC'IC / sqrt(IC'C IC) = 0.0281/sqrt(0.0437) = 0.134 (HW2body L214-257). The submission averaged scores instead (0.135), wrong in principle (HW2notes). Lesson: the gain is from combining at all (0.10 to 0.134), not from optimizing weights.

### 2.3 Problem 3 (plus-minus 1% alphas, lambda, holdings, the units lesson)
- Correct answer in percent units (alpha = plus or minus 1, omega in percent, lambda 0.125): h_i = 4 z_i/omega_i^2, bet B_i = |h_i| omega_i = 4/omega_i. PG has the largest holding, 3.089%, and the largest bet, 0.351%; DOW the smallest, -0.865% and 0.186%. Gross 46.41%, net +11.41%, psi 1.363%, portfolio alpha 0.464%, implied IR 0.341 (HW2body table p3_holdings, L287-321).
- The units lesson (HW2notes): the submission used lambda = 0.125 with decimal alpha and omega, so every holding was 100x too large: PG 308.87%, psi 136%, gross 4641%. The sanity check that settles it: psi = sqrt(sum h_i^2 omega_i^2) should land near the 2% target that lambda was calibrated for; 1.36% does, 136% does not. General rule: lambda = IR/(2 psi) in whatever units alpha and omega are in; 0.125 in percent is 12.5 in decimals.
- Implicit skill in plus-minus 1%: IC_i = alpha_i/omega_i runs from 0.088 (PG) to 0.046 (DOW); the rule claims the broker is twice as good on quiet stocks (HW2body; HW2notes).
- ChatGPT's two alternative mappings (HW2body L323-546): standardized scores (alpha BUY +0.9045%, SELL -1.1055%, an artefact of the 11/9 count; WMT becomes the largest at -3.19%; psi 1.342%, IR 0.336) and Grinold-Kahn alpha = IC omega z with IC 0.05 (every bet 0.20%, PG 1.76%, gross 30.09%, psi 0.894%, IR 0.224). The GK rule was judged more realistic because it moves the assumption from a common alpha to a common skill that can be estimated; the standardized score was not. Research-service alphas disagree in sign with the broker on 12 of 20 names.

### 2.4 Problem 4 (GK alpha with IC 0.04, breadth, robustness checks)
- alpha_i = 0.04 omega_i z_i gives h_i = 0.16 z_i/omega_i and a constant bet IC/(2 lambda) = 0.16% for all 20 names. PG 1.406%, DOW -0.744%, max/min |h| 1.89x (vs 3.57x). Gross 24.07%, net +4.39%, psi 0.716%, portfolio alpha 0.128%, IR 0.179 = IC sqrt(20), the fundamental law exactly (HW2body table p4_holdings, L548-620). Ranking of positions unchanged (rank correlation 1.0); IC is a pure scale parameter.
- ChatGPT robustness design (Q4prompt, Q4reply): four stability definitions (elasticity of |h| to omega: -2 vs -1; relative perturbation turnover; concentration/effective N; worst single-name move), twelve ranked checks with a data requirement and a feasibility flag each, closed forms, pseudocode, and in the follow-up "stability tells you how much the answer moves; it says nothing about whether the answer was right".
- Checks I ran (Q4sec feasibility table; Q4chk): 10% lognormal omega shock, one-way turnover 8.1% vs 4.0% of gross; one random rating flip trades 5.0% of gross under both (a tie by construction, 2k/N two-way), sd/mean 0.28 vs 0.16; worst-case PG flip 3.09% vs 1.41% (13.3% vs 11.7% of gross); effective N of risk 18.5 vs 20.0; Staples 18.8% vs 15.0% of active variance; broker and research service agree on 8 of 20 signs, h'alpha_RS = -0.20% vs -0.09%, and the z*omega regression t = 1.0, so the snapshot cannot say which alpha rule is right.
- Fact-check of the reply (Q4crit): every closed form was right; every plugged-in aggregate was wrong by 15 to 35% because it used a "representative omega of 16%" (gross 30% vs true 46.4%, psi 1.1% vs 1.36%, IR 0.28 vs 0.34); wrong prose on the dollar-neutral Lagrange multiplier while its code was right; listed Spearman correlation as discriminating when the two rules rank identically; kept a primary metric that is degenerate on its own flip test; did not state one-way vs two-way turnover.

### 2.5 Problem 5 (impact)
Square-root impact: B (twice the vol, twice the volume) costs 2 sqrt(1/2) = sqrt(2) = 1.41x A; generally 2^(1 - gamma) (HW2body L646-665).

### 2.6 HW2 Q4(c): what we learned about ChatGPT (Q4sec, "hw01" block)
- It helped most with idea generation, then model realism, least with robustness. It enumerates and structures well, is unreliable on arithmetic it did not run, and sprawls unless the prompt fixes the count.
- In HW1 the first attempt without our numbers produced generic ESG material; useful answers came only after the numbers and data constraints went at the top.
- Workflow adopted for the final project: numbers and data constraints first, then the ask, a fixed number of alternatives, a feasibility flag and data requirement on every item, and a closing request for the assumptions it is least confident in. Evaluation order: does it use our numbers; is it internally consistent (re-derive closed forms); can it be run with the data this week; does it say what result would falsify it. Recompute every number before it goes in a table. "I will use it as an idea generator and a checklist writer. The calculator is mine."

---

## 3. Methods from HW1 and HW2 the final project should reuse, and how

| # | Method | Source | How to reuse in the final project |
|---|---|---|---|
| 1 | FF regressions on excess returns (legs minus rf; spread not adjusted), NW(6), alpha annualized x12 | HW1tex L419; Q4corr | Same spec for every strategy and leg, now with FF5 + UMD (+ ST/LT reversal) from data/raw. Always subtract rf from long-only legs; the rf-in-intercept bug produced fake t = 3.8 alphas once. |
| 2 | Three-window reporting with a small-N caveat | HW1tex L419; Q5gpt (13-obs SE arithmetic) | Brief windows: full, post-2010, last 12-18 months (common.PERIODS). For last12/last18, OLS or very short HAC and descriptive language only. Arithmetic (derived here): t = IR sqrt(years), so t = 2 needs IR 0.27 over 1970-2026, 0.49 post-2010, 0.56 on the team validation, 1.0 on the 4-year holdout, 1.63 over the last 18 months. The holdout cannot confirm any plausible IR; say so. |
| 3 | Rolling 60-month factor hedge with a verification regression (realized abs(b_H) < 0.10, abs(t) < 1) | Q5gpt Strategy A | The team hedges FF3 with a lagged 60m beta but reports no ex-post check that the hedge worked. Run the verification regression on the hedged series per window and plot rolling 36m b_H. |
| 4 | Split-sample per-industry regressions to locate the HML drift | Q5gpt; HW1tex L525 | FF3 (and FF5) regressions of each Green and Brown industry on 1975-2009 vs 2010-2022, extended to 2010-2026. Cross-check with the characteristic: Ken French annual BE/ME per industry (load_kf_industries("be_me_vw")). |
| 5 | 8/8 baskets with a rate-sensitive cluster cap | Q5gpt | Naive 8/8 (common.legs_by_emissions(8)) gives Green + Autos, Insur, Hardw and Brown + Chems, Trans, Mines. The HW1 ChatGPT rule swaps Insur for MedEq. Hardw and MedEq tie exactly, so the rule must be fixed ex ante. Keep 5/5 as primary. |
| 6 | Commodity control CMD = (Oil + Coal + Gold)/3 minus Mkt from FF49 | Q5gpt L13-14 | Traded, so usable in a hedge. Coal is ranked (9th dirtiest), so the ChatGPT fallback (Oil + Gold)/2 avoids overlap. FRED WTI (MCOILWTICO), PALLFNFINDEXM, PPIACO for attribution only (not traded). |
| 7 | Timed-factor benchmark | Q5gpt Strategy B | The cleanest alpha-vs-beta test for the attention strategy: apply the identical attention rule to HML (and to CMD, UMD) and ask whether timing Green-Brown beats timing the factor. |
| 8 | Block bootstrap of the signal (12-month blocks) as an overfitting check | Q5gpt Strategy B | Team already uses a 12-month circular block bootstrap on returns (TeamNB L449). Add a signal-placebo version: shuffle the signal in blocks, require the real Sharpe above the 95th percentile. |
| 9 | Cost model 10/25/5 bps and turnover arithmetic | Q5gpt L29 | The team's cost parameters are exactly these ChatGPT guesses (TeamNB L32-34: cost_asset 10e-4, cost_mkt 5e-4, cost_other_factor 25e-4). Label them as assumptions, run 5/10/25 bps uniformly, and report the break-even cost. State one-way vs two-way turnover (HW2 lesson, Q4crit item 7). |
| 10 | GK alpha = IC omega z; h = alpha/(2 lambda omega^2); bet = IC/(2 lambda) | HW2body P3-P4 | Turn the attention z-score into a position: h_t = IC z_t/(2 lambda omega_t), omega_t = trailing residual vol. This is a principled version of the team's continuous-weight variant, with an explicit, estimable IC. |
| 11 | Units and calibration check | HW2notes | Team files are decimals (ff49 file 0.0236 = 2.36%); HW1 and raw Ken French files are percent (common.py divides by 100); FRED rates are percent levels. After any sizing step, recompute realized psi or vol and compare with the target (the team targets 5% residual vol, TeamNB L262). |
| 12 | Fundamental law and breadth | HW1tex L319-347; HW2body P4 | Arithmetic (derived here): for IR 0.5, a single spread timed with 2 independent bets a year needs IC 0.35, 4 bets 0.25, 12 bets 0.14; a cross-sectional signal over 41 industries monthly (492 bets, before correlation) needs 0.023. This is the thesis-level reason a one-spread attention timer is hard, and a reason to consider a cross-sectional industry signal. |
| 13 | Signal combination c = C^-1 IC, IC_combined = sqrt(c'IC); average alphas, not scores | HW2body P2 | Combine attention proxies (team attention = FRED EMVENRGYENVREG per research/STATUS.md; Gavriilidis CPU; Ardia MCCC; EMV overall) with IC and C estimated on the design sample only. Coverage (derived here): CPU ends 2025-09 and MCCC ends 2025-06, so a combined signal does not cover the last months of the holdout. Given that the team's IC flips sign, equal-weighted z-scores are the robust default and GK weights a secondary. |
| 14 | Noise share of a forecast (c1, c2) | HW2body P2 | At IC 0.05 the signal part of alpha is 0.0625% sd against 1.248% noise; use it to set expectations in "What did you learn". |
| 15 | Robustness design: define stability, flag feasibility per check, perturb inputs | Q4prompt; Q4sec | For the attention rule: perturb the 80th percentile threshold, the 60m z-score window, the hold period; "flip" the signal in random months (analogue of rating flips); report dispersion, not just the mean. |
| 16 | Square-root impact | HW2body P5 | Only a sentence: industry baskets and factor ETFs are liquid; impact matters little at the notional sizes implied. |

Other HW lessons to carry forward: state that the emissions ranking is one snapshot applied backward (look-ahead flagged in Q5gpt L67); keep the 2021-22 "loss shows up as alpha, not HML" point, since the team's residual HML loading of t about -2 is the same fingerprint; keep a "what result would falsify it" line for every strategy (Q5gpt).

---

## 4. The ChatGPT-exchange format used before

HW1 Problem 5 (HW1tex L462-527; Q5ans; Q5crit; Q5gpt):
1. (a) Context: three bullets with our own numbers (ranking, performance, factor loadings) placed at the top of the prompt.
2. (b) Research step: one message; the assignment's four requirements mapped to numbered items 1-4; a data-constraints paragraph so answers cannot depend on data we lack; "be concrete enough that I can write this in Python this week"; closing request for the least-confident assumptions.
3. Round 1 critique (Q5crit), headed "What worked" and "What's missing or off"; each gap became an explicit instruction in the round-2 prompt (name the industries, give the start month, cap variants to one line, 13 obs is a stress test, flip frequency consistent with regimes, cost guesses flagged up front).
4. (c)(i) Exact prompt verbatim in a listing; (c)(ii) summary in 5 to 8 bullets; (c)(iii) plausibility check, one paragraph per assignment question, each tied to our numbers; (d) forward link: selected strategy, what to test next, key risk.

HW2 Problems 3 and 4 (HW2body; Q4prompt; Q4reply; Q4crit; Q4sec):
1. Prompt: a SETUP block with exact universe, coding, lambda, formulas and data limitation; "Propose exactly TWO"; numbered requirements (operational definitions with at least three candidates, statistical and economic checks, data requirement and feasibility flag per item, ranked list with named fields, reproducible pseudocode, closed forms where they exist); a follow-up prompt asking it to work two checks in closed form and give the single strongest counter-argument.
2. Reply saved verbatim (Q4reply).
3. Independent fact-check file (Q4crit) with fixed headings: FACT CHECK (wrong or materially off, with true values; correct and non-obvious, safe to cite), SUMMARY, FEASIBILITY, GAPS, VERDICT.
4. Every feasible check rerun by us (Q4chk), with numbers in the write-up taken from our code, not ChatGPT's.
5. Write-up: prompt listing, summary bullets, feasibility table (check, needs, feasible, result), "what the checks say / cannot say", a fact-check paragraph, and a comparison with HW1.
6. Three-agent production (HW2notes): one agent wrote the prompt, a second answered it cold "as ChatGPT", a third fact-checked. research/STATUS.md plans the same pattern for the final project.

Integrity flags for the final report:
- The HW2 rework reply is labelled "Simulated ChatGPT replies ... generated by an independent agent given only q4_prompt.txt" (Q4reply line 1), while the HW2 prose says "I sent the main prompt". The final brief asks for ChatGPT prompts and ChatGPT transcripts in the appendix. Any reply produced by another model must be labelled as such, or the prompts should be run in ChatGPT and the verbatim replies saved, before submission.
- In HW1 the "Exact prompt used" in the submitted tex (HW1tex L480-499) is a cleaned-up rewrite of the casual prompt in Q5ans L20-37 ("hey so I'm doing an equity markets class..."). For the final project, paste the prompt exactly as sent.

Suggested template per exchange (combining both): context with our numbers; data constraints; numbered asks with a fixed count; feasibility flag and data requirement per item; falsifier per idea; least-confident assumptions; save reply verbatim; fact-check file with the Q4crit headings; our own reruns; write-up with summary, feasibility/results table, critique, and a forward link. The brief needs at least 3 such prompts.

---

## 5. Every concrete idea teammates proposed at the halfway point, with an assessment

Christhian, message 1 (WA L3-14)

1. Hypothesis: no permanent Green-minus-Brown premium, but the factor-neutral spread pays after extreme jumps in climate-transition attention, conditional on rates, oil, inflation and macro. Assessment: already tested and rejected by his own numbers (COVID-only gains, holdout loss, IC sign flip); keep it as the documented null and the benchmark every new variant must beat.
2. Green and Brown FF industry legs with market, size and value controls. Assessment: correct baseline, but FF3 leaves the HML drift, commodity and momentum channels; add the HW1 verification regression (abs(b_H) < 0.10) so the hedge is shown to work.
3. Raw and macro-adjusted (purified) attention signals. Assessment: sound design (120-month walk-forward ridge, TeamNB L135), but each extra version is another test; count them in one Holm/BH family.
4. Transaction costs, out-of-sample tests, bootstrap inference, multiple-testing corrections, separate COVID and post-2022 evaluations. Assessment: keep all of it; this is the execution-grade part and matches the brief's time-pattern requirement.
5. Continuous version of the signal (lower vol and drawdown, no reliable alpha). Assessment: report it as risk management (vol -55 to -65%, drawdown -60 to -75%, fails Holm, TeamNB L715), not as alpha.
6. Literature framing: contrast with Bolton and Kacperczyk (2021); consistent with Zhang (2025), Eskildsen et al. (2026) and Pastor, Stambaugh and Taylor. Assessment: good framing; the Ardia MCCC series in data/raw allows a direct PST test (does the spread move with unexpected climate-concern changes in the same month while the lagged signal has no predictive power?).
7. Open to improving this idea or pursuing a different one. Assessment: the brief rewards a well-evidenced "Do not implement"; any new idea should be pre-specified and tested on a sample the team has not looked at.

Christhian, message 2: the four HW1 tests (WA L16-22)

8. Rebuild the baseline with 8 Green and 8 Brown. Assessment: cheap and it was the first HW1 next step; fix the membership rule first (naive 8/8 includes Insur and the Hardw/MedEq tie; the HW1 ChatGPT rule used Autos, Hardw, MedEq), and report 8/8 as a robustness check, not a new primary.
9. Add momentum and an explicit commodity exposure to the controls. Assessment: yes for attribution regressions; UMD is in data/raw, CMD should use FF49 Oil and Gold (Coal is ranked). Adding them to a rolling 60-month hedge makes the betas noisy (the HW1 critique called CMD "a fifth regressor on 60 observations"), so prefer them in the ex-post regressions or use a longer estimation window.
10. Individual regressions for Fin, Telcm, Drugs, Fun, RlEst to locate the HML exposure. Assessment: highest value per hour; run the HW1 split-sample version (1975-2009 vs 2010-2022/2026), include the Brown industries, and cross-check with industry BE/ME so the answer (composition vs re-rating) is not only regression-based.
11. Transaction-cost sensitivity at 5, 10, 25 bps. Assessment: cheap but cannot change a "no alpha" verdict; report the break-even cost as well. Also note the team charges the spread position once (leg_multiplier fixed at 1.0, TeamNB L280-289), while a unit change in the spread trades one unit in each leg, and within-leg equal-weight drift is not charged; state the convention.
12. Use his notebook as the starting point and have Opus 5.5 implement the tests. Assessment: fine as a workflow, but the team repo stays read-only; reimplement in research/ using lib/common.py so his notebook's outputs remain the frozen baseline.

Charishma (WA L24-28)

13. Part A, signal building. Assessment: needs to be more than threshold tuning, which the team's own notebook warns against (TeamNB L723); options with a real rationale are combining attention proxies (HW2 P2 weights) or a cross-sectional industry signal with more breadth (HW1 P3, HW2 P4).
14. Part B, alpha vs beta at the portfolio level; she offers to set up the code. Assessment: this is the core of the brief's "What did you learn" section. It should include FF5 + UMD (+ reversal, CMD, and a rates or duration factor) per window. It also needs conditional-beta and timing tests (signal times factor interactions, Treynor-Mazuy or Henriksson-Merton), because a timing strategy can look like alpha against static factors while it is only factor timing. Add the timed-HML benchmark from HW1 Strategy B.

Christhian, message 3 (WA L30-41)

15. Give the model context about the exercise and his findings before prompting. Assessment: agrees with the HW lesson (our numbers first, generic answers otherwise); give it the numbers, not the ZIP.
16. Add macro controls, since alpha and exposures are regime dependent (COVID, then rising inflation and rates), using the macro data he shared. Assessment: use macro variables for attribution with interactions, not as a new trading filter found after seeing the holdout. The "high rates flip the signal" idea has one clean test left: the attention series starts in 1985-01 (derived here), so 1990-2009 is a pre-design sample the team never used, and it includes higher-rate years.
17. Use the shared papers as prompt context (Bolton and Kacperczyk carbon premium; Pastor et al. on climate concerns). Assessment: useful; quote the specific claims and sample periods in the prompt so ChatGPT cannot substitute generic ESG results.
18. Frame the question as genuine alpha vs exposure to traditional factors, notably HML, that change across regimes. Assessment: right framing, and HW1 quantifies it: FF3 R2 of the spread rose from 0.07 to 0.18 and HML from -0.23 to -0.35 after 2010 (HW1tex L433, L437); report the time-varying loading, not one full-sample number.
19. Include HW1 context in the prompt. Assessment: yes; use the corrected Table 3 (excess returns), not the pre-correction alphas.
20. Control for momentum in the alpha-vs-beta analysis because the signal might capture persistence in past returns. Assessment: correct, and HW1 never ran it. For industry baskets the relevant control is industry momentum (build a 12-1 month industry momentum factor from FF49) in addition to stock-level UMD. Also check directly whether attention spikes follow strong trailing spread returns.
21. Others may add context to the prompt. Assessment: process only; nothing to test.

---

## 6. Discrepancies and pitfalls found while reading

1. "-25.7% over the last 13 months" (HW1 prompt) is an annualized mean; cumulative was -25.2% (derived here).
2. HW1 Tables 1 and 2 report raw Sharpe; the prompt uses excess Sharpe (0.41/0.42). Say which one.
3. Group number 4 vs 5 (Q4corr L35). Author spelling Cristhian (HW1tex) vs Christhian (WA).
4. HW1 said momentum was in the data; it was not (section 1.4).
5. The team's ff49 file is a later vintage than the HW1 file. From 1970 to Jul 2022, 85% of industry-month cells differ by more than 1 bp (correlation 0.997), and Green L/S 5/5 is -0.13%/yr with 9.60% vol vs -0.15% and 9.58% in HW1 (derived here). HW1 numbers will not replicate to the second decimal on team data.
6. The team's cost parameters come from ChatGPT's self-described guesses in HW1 (section 3, row 9), and asset turnover counts a spread change once (section 5, item 11).
7. Emissions ties (Hardw = MedEq, and others) mean leg membership beyond rank 7 depends on sort order.
8. Coal is both a ranked industry (9th dirtiest) and a component of the HW1 CMD basket; Oil and Gold, the other two components, are among the 8 industries without emissions data.
9. HW2 replies were simulated by an agent and labelled as such in the file; the HW2 prose reads as if ChatGPT was used (section 4). Resolve this for the final project's transcripts.
10. Units: the team data are decimals, HW1 and raw Ken French files are percent, and lambda is 0.125 in percent vs 12.5 in decimals. Check realized risk against the target after every sizing step.
