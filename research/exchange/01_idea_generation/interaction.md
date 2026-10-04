# Idea generation: Refereeing the climate-attention timing design

Tool: Claude
Date: 2026-09-26
Purpose: idea generation

## Prompt

### Message 1 (initial prompt: design review of the halfway strategy)

You are a skeptical buy-side quant refereeing a student research project in climate-driven factor timing. Treat this as a design review: I want the weak points found before I spend time on them.

SETTING. This is the MFE 230GA (Active Asset Management) final project at Berkeley. The report needs a one-paragraph Executive Summary that says "Do not implement" if there is no alpha; "What did you try" (idea, data, risk model, turnover and costs, at least three substantial Claude interactions); "What did you learn" (factor exposures, performance over the full sample, post-2010 and the last 12 to 18 months, robustness and limits, a critical evaluation of Claude). Grading: thesis 40%, execution 40%, originality 20% (novel data use, prompt design). A well-documented "Do not implement" is an acceptable result. Our team of five wrote the first half; I am taking the second half forward.

HALFWAY DESIGN. Thesis: Green minus Brown has no permanent premium, but its factor-neutral part pays after spikes in climate-transition attention. Green is the five lowest emissions-intensity Fama-French 49 industries (Fun, RlEst, Drugs, Telcm, Fin), Brown the five highest (Util, Ships, Aero, Steel, BldMt), each leg equal-weighted across value-weighted industries. Emissions intensity is one static snapshot covering 41 of 49 industries (Oil, Chips, FabPr, Gold, Hshld, LabEq, Other, Toys missing). The traded position is not the spread: it shorts the Brown leg alone, with an FF3 overlay from rolling 60-month betas lagged one month. Signal: climate-transition attention (a monthly index starting in 1985) as a 60-month rolling z-score of log(1 + attention). A month is extreme when the signal exceeds its expanding, past-only 80th percentile, and each crossing opens a Short-Brown position held 3 or 6 months, sized to 5% residual volatility (cap 1x). Costs per unit of turnover are 10 bp on the leg, 5 bp on the market overlay and 25 bp on SMB/HML, all assumed. Variants: "purified" attention (the residual from a 120-month walk-forward ridge on rate, oil, inflation and activity shocks) and a continuous weight (floor 0.5, 3-month half-life). Validation ran 2010 to Jul 2022; Aug 2022 to Jul 2026 was a frozen holdout.

RESULTS.
- Validation: the 6-month rules earn about 2.5% a year net (FF3 alpha Newey-West t = 2.23 and 2.46); the 3-month rules have t of about 1.5.
- COVID carries it: the 3-month rule earns 5.94% net in 2020 to 2021 (alpha t = 3.21).
- Holdout: every version loses 2.1% to 3.8% a year (t = -1.7 to -2.2). The IC flips from about -0.08 (negative is the expected sign for a short-Brown rule) to +0.12 to +0.15.
- Over 2010 to 2026 the best timed version earns 1.3% a year net against 1.0% for always-short Brown.
- The raw spread loads on HML (-0.24 full sample, -0.35 since 2010). After hedging, residual HML is about -0.05 with t of about -2 in every version.
- The continuous variant cuts volatility 55 to 65% and drawdown 60 to 75%, but a calendar-shuffle placebo gives p of about 0.12.
- 2 of 32 strategy-period cells survive Holm, both in COVID.
- A follow-up notebook finds the attention slope turns positive in high-rate months (difference t = 1.83, Holm p of about 0.6); 47 of those 74 months are in the holdout.

TEAMMATE PROPOSALS. From Cristhian: (A) rebuild with 8 Green and 8 Brown industries; (B) add momentum and an explicit commodity exposure to the controls; (C) regress Fin, Telcm, Drugs, Fun and RlEst individually to find where the HML exposure comes from; (D) uniform costs at 5, 10 and 25 bp. From Charishma: (E) a Part B on whether this is alpha or beta at the portfolio level. From the group: (F) macro controls, since exposures look regime dependent (COVID, then inflation and rates); (G) a momentum control, in case the signal is only persistence in past returns.

DATA. In hand: the four team files (FF49 monthly returns, Jul 1926 to Jul 2026; FF3 and rf; the emissions snapshot; a macro file with attention, the 10-year yield, WTI, CPI, CFNAI, the NBER recession flag and GSCPI). Downloadable: Ken French FF5, UMD, short- and long-term reversal, FF49 value- and equal-weighted returns, industry BE/ME, firm counts and average size; FRED Treasury yields (3-month, 2-year, 10-year), BAA and AAA, VIX, commodity indices, activity series, breakevens and TIPS yields; the Gavriilidis Climate Policy Uncertainty index, the Ardia et al. Media Climate Change Concerns index, and EPA supply-chain GHG factors by NAICS. No firm-level data. Every result so far starts in 2010, and the holdout has now been seen, so it is no longer a clean test.

WHAT I NEED, in this order and under these headings.
1. Design critique. At most six problems, ranked by how much each could change the verdict: the problem, why it matters here, the fix.
2. Proposal ranking. One table for A to G: rank, proposal, the result that would change our conclusion, what it cannot tell us, overlap with other proposals, effort in hours. One line of reasoning per row.
3. New ideas. Exactly five, at least two extending the current strategy and at least two alternatives on the same data, each aimed at a small defensible alpha or a more rigorous "Do not implement". For each: (a) a falsifiable hypothesis and the result that rejects it; (b) the exact test: sample, return series, specification, benchmark, pass bar; (c) the data, and whether it is listed above; (d) main pitfalls (look-ahead, multiple testing, small N, overlapping holds); (e) effort in hours; (f) what it adds to the report if it fails.
4. Plan. The three items from sections 2 and 3 you would run first, in order, and why.
5. The three assumptions in your answer you are least confident about.

RULES. Work from our numbers, not generic ESG results. Cite a paper only with authors, year and the specific claim. Do not invent backtest results; label any number you have not computed as a guess. Stay under 1,800 words.

### Message 2 (follow-up, sent after fact-checking Reply 1)

I ran most of your proposed tests on the seen data. Five of your claims are wrong, and you missed a data fact that changes the review.

The attention series is not what we called it. I traced the team's column to its source: it is FRED EMVENRGYENVREG, the Baker, Bloom, Davis and Kost Equity Market Volatility tracker for Energy and Environmental Regulation. It counts newspaper articles on stock-market volatility that mention the category, scaled to the VIX. Since 2010 its z-score correlates +0.39 with overall EMV, +0.11 with CPU and -0.06 with MCCC, and 38% of crossing months are high-EMV months, against 12% of other months (odds ratio 4.5, p = 0.002). Your coverage worry also points the wrong way. The series is exactly zero in 12 of 441 months from 1985-01 to 2021-09, but in 39 of 59 months from 2021-10 (31 of 48 holdout months). The holdout tested a near-binary signal, not the one we validated.

Corrections:
1. Duration. The hedged Brown leg has no holdout rate exposure (Δ10y t = 0.05), and the strategies gain when yields rise. After FF5+UMD+Δ10y+commodity controls, holdout alphas are still -2.3% to -4.8% (t about -2).
2. Newey-West lags. More lags do not shrink the validation t (2.23 at 6 lags, 2.30 at 12); they push the 24-month COVID t to 5.3. The binding problem is small-sample p-values: with t(n-4), 0 of 32 cells survive Holm.
3. IC flip. It is 1.3 to 1.6 SE for raw and purified, but 2.8 to 2.9 NW SE for the continuous signals.
4. Idea 1 dates. The frozen rule first crosses in 1993-01 (raw) and 1999-01 (purified).

Your tests rescue nothing: timed minus always-on FF5+UMD alpha peaks at t = 1.09, and the Idea 2 post-event CAR is -1.29% (t = -1.08).

Two questions.
(a) Do I salvage this series (as a share of total EMV, or zero-robust) or replace it with CPU or MCCC, given both end in 2025 and burn about eight years under our rule? Give the one rule you would freeze for the unseen 1993 to 2009 test, its pass bar, and how it treats zeros.
(b) Give an exact attribution spec that separates timing alpha from duration, value and volatility exposure: dependent variable, regressors, an exposure-matched benchmark, lags, and what counts as alpha.

Under 600 words. Label anything you have not computed as a guess.

## Output summary

### Reply 1: design review (about 1,700 words)

Claude opened with a bottom line: the timed rule beats always-on Short-Brown by about 0.3% a year (1.3% vs. 1.0%), so the job is to "Make "Do not implement" airtight, and test pre-specified ideas on the one period nobody has looked at, **1990–2009**."

- **Design critique, six problems ranked.**
  1. The benchmark is wrong for a timing claim: "For a timing thesis the null is "always short Brown, same hedge, same vol target."" It also noted that the traded position has no Green leg, so the thesis should be restated as Brown underperforming after attention spikes.
  2. Validation is one episode. Aero, Ships and Util "took COVID-specific hits unrelated to transition risk", and each is 20% of an equal-weighted leg. Fix: leave one industry out, and rerun without Mar 2020 to Dec 2021.
  3. The holdout is spent. The high-rate interaction cannot be confirmed on the data that suggested it, and the IC change is "about one standard error of the difference", so the reading is "failed to confirm" rather than "flipped". Fix: declare 1990–2009 the new frozen holdout.
  4. The Brown leg may not measure transition risk. Oil is missing, and Aero and Ships in the top five is "surprising". Fix: rebuild intensities from EPA supply-chain factors for all 49 industries and "rerun with Oil and Coal in."
  5. Hedge residuals line up with the regime story: "A 2022–2026 holdout dominated by rates can lose money through unhedged duration, not climate." Fix: attribute ex post against FF5 + UMD + Δ10-year yield + a commodity return, with the ex-ante hedge unchanged.
  6. Inference is weaker than the t-stats suggest (overlapping holds, few events, revised macro data). Fix: "NW lags ≥ hold length", count independent events, block-bootstrap by event, lag macro inputs, and compare the continuous variant with always-on at the same average exposure, since its lower volatility is "partly mechanical".
- **Proposal ranking.** E (alpha vs. beta) first, then A with leave-one-out, G, B, F, C and D. It redirected C to the Brown industries ("Green isn't in the traded position") and ranked D last: "Costs can't rescue a −2% to −4% holdout; report break-even instead".
- **Five new ideas.** Three extensions: (1) a backward out-of-sample test over 1990–2009 with the high-rate interaction pre-registered as a second hypothesis and Holm across both; (2) an event-time profile of hedged Brown residuals after crossings, passing only if the post-event dummy has t > 2 outside 2020–21, with Ardia, Bluteau, Boudt and Inghelbrecht (2023) and Pástor, Stambaugh and Taylor (2022) cited for contemporaneous repricing; (3) the frozen rule rerun on the CPU and MCCC indices. Two alternatives: (4) an all-49 carbon-intensity spread from EPA factors, framed as the industry analogue of Bolton and Kacperczyk (2021); (5) an FF49 climate-news hedge portfolio after Engle, Giglio, Kelly, Lee and Stroebel (2020).
- **Plan.** Idea 2 with leave-one-out, then Idea 1, then E with B and G folded in.
- **Least-confident assumptions.** Usable index coverage over 1985–2009 and a stable emissions ranking; that the COVID gains come from Aero, Util and Ships ("a hypothesis, not something I computed"); the index start dates and every hour estimate.

### Reply 2: follow-up on signal choice and attribution (under 600 words)

It accepted the corrections ("Your corrections are right, including the ones on duration and the IC. The EMV finding matters more than any of them."), read the EMV fact as explaining the holdout without rescuing the strategy, and restated the verdict: "Do not implement" stands.

- **(a) Signal choice: "Salvage the series; don't replace it".** MCCC "can't test 1993–2009", CPU would cover only about 1995–2009, and at a correlation of +0.11 switching to CPU "tests a new hypothesis rather than a cleaner version of yours". CPU and MCCC should run afterwards, labelled exploratory. The proposed signal is s_t = EMVENRGYENVREG_t / EMVOVERALLEMV_t, on the reasoning that a category tracker equals overall EMV times the share of EMV articles mentioning the category. The rule to freeze: zero months are missing, never trigger, and are dropped from the z-score and percentile windows; the z-score needs 48 nonzero months of the trailing 60; the signal is off if more than 10% of the trailing 60 are zero; a month is extreme when the 60-month z of log(s_t) exceeds its expanding past-only 80th percentile; the trade is the validated 6-month Short-Brown rule, run once on Jan 1993 to Dec 2009. The pass bar has four parts: timing alpha t ≥ 2 with t(n−k) p-values, calendar-shuffle p ≤ 0.05, at least 8 independent episodes (a guessed threshold), and the same sign with each Brown industry dropped. It added that the zero rule "would probably have kept you flat for most of the holdout (a guess)", then: "It was written after seeing the holdout, though, so take no credit for that period."
- **(b) Attribution.** The dependent variable is D_t = R^T_t − π·R^AO_t, with π the ratio of mean timed weight to mean always-on weight, so the benchmark has matched exposure and no timing. Regressors: FF5 + UMD; TERM_t ≈ −8·Δy10_t ("The duration of 8 is a guess."); the WTI log return; ΔVIX and Δlog EMV; and in-position interactions I_{t−1} × {Mkt, HML, TERM, ΔVIX}, citing Ferson and Schadt (1996) so that exposure taken only while in position counts as beta. Inference: Newey–West with 6 lags (12 as a check), t(n−k) p-values with k = 14, and a 5,000-draw calendar-shuffle null. On what counts as alpha: "Only α." Its closing test: "If α drops when ΔVIX and ΔEMV enter, the signal was a volatility bet, not a climate one."

## Evaluation

The first reply was a competent design review built on a variable it never examined. The fact-check scored 52 checkable claims: 26 correct, 15 partly correct, 6 wrong and 5 unverifiable. Its arithmetic, citations and labeling of guesses were sound.

**Three contributions changed the plan.** First, critique 1: timed returns had been tested against zero, when a timing claim's null is the always-short position with the same hedge. On seen data it settles the question (timed minus always-short FF5+UMD alpha peaks at t = 1.09). Second, Idea 1, a backward test on the one window with no computed strategy returns (pre-2010), was not in my plan. Third, it flagged Aero and Ships as odd Brown members and guessed that Aero, Util and Ships drove the COVID gains. Both held: EPA factors rank Aero 31st and Ships 20th of 49, and those three industries deliver 86% of the Original 3-month rule's COVID gross P&L. Its redirect of test C to the Brown leg was also right (HML +0.44 for Brown vs. +0.14 for Green since 2010).

**Six claims were wrong** (five corrections in my follow-up). The holdout was not lost to duration: the hedged Brown leg has no holdout rate exposure (Δ10y t = 0.05), and holdout alphas stay at −2.3% to −4.8% annually after FF5+UMD, rate and commodity controls. Its inference fix fails: more Newey–West lags raise the 24-month COVID t from 3.21 to 5.32, and the binding problem is small-sample p-values (with t(n−4), 0 of 32 cells survive Holm). The IC flip is 1.3 to 1.6 standard errors for the raw and purified signals and 2.8 to 2.9 Newey–West standard errors for the continuous ones, not "about one". Idea 1's dates were wrong (two claims; first crossings 1993-01 and 1999-01), and the team's macro-state notebook had already used 192 pre-2010 months. The sixth, on coverage, is below. Two weaker points were not scored wrong: it asked where Coal ranks (9th of 41, in the file) but missed that EPA v1.3 lacks electricity codes, and ideas 4 and 5 were generic climate-premium portfolios with no stated alpha source.

**It never asked what "attention" measures.** My prompt passed on the team's label without a source, and neither reply asked who builds the index. The series is the EMV tracker for Energy and Environmental Regulation (since 2010, 88.5% of crossings fall in months when overall EMV is above its past-only median, against 56.1% of other months; Fisher p = 0.0012), and 31 of 48 holdout months are exactly zero. It put the coverage risk in the wrong period ("early index coverage may be thin"; the pre-2010 zero share is 0.8% to 4.2%). This is a failure of my prompt as much as of the replies.

**The follow-up turned the corrections into specifications.** It accepted every correction, kept "Do not implement", and gave a frozen 1993–2009 rule (share of overall EMV, zeros as missing, the 6-month rule, a four-part pass bar) plus an attribution against an exposure-matched always-short benchmark, with a calendar-shuffle null. It rightly declined credit for the holdout: its zero rule silences the signal in all 48 holdout months but was written after seeing them. Three flaws remain. The two zero thresholds are redundant (at most 6 zeros in 60 makes the 48-nonzero minimum inert). The share signal keeps most of the original timing (15 of its 25 post-2010 crossings sit within a month of the team's, against about 10 by chance). Its k = 14 undercounts the model's 15 coefficients.

**Where each piece went.**
- M1b: MCCC and CPU stay the primary alternatives on 2010–2026, with VIX and overall EMV as COVID placebos. The share series was already a robustness measure; the follow-up's point that MCCC starts in 2003 and CPU cannot signal before 1995 is why it carries the pre-2010 test.
- M2 and M4: test C covers both legs, costs are reported as break-evens, and the EPA rebuild patches Util from USEEIO.
- M3: its Ferson–Schadt terms match my planned conditional-beta step, and a GS10 bond return with duration and convexity supersedes its −8·Δy10 guess.
- M8: the exposure-matched benchmark, calendar-shuffle null, merged event counts and t(n−k) p-values apply to every timing claim. The 1993–2009 rule is frozen with corrected dates and a one-month publication lag, and is scored once.
- M5 and M6 owe nothing here: neither reply proposed industry momentum or shrinkage timing.
