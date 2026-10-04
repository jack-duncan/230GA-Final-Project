# Red team: Breaking the "Do not implement" verdict before a grader does

Tool: Claude
Date: 2026-09-26
Purpose: red-team review of the conclusion

## Prompt

### Message 1 (single prompt: red team of the draft executive summary and its claims)

Read my draft twice: first as a skeptical investment-committee member who must sign off on "Do not implement", then as a finance-journal referee. Break the conclusion before a grader does. No summary, no praise.

SETTING. My UC Berkeley MFE 230GA final project (thesis 40%, execution 40%, originality 20%). I extended our team's halfway project alone. "What did you learn" is at its page limit, so an edit there must replace text.

THE EXECUTIVE SUMMARY, AS DRAFTED.
Our team's halfway project proposed a state-dependent climate trade: short the factor-hedged Brown industry leg (Util, Ships, Aero, Steel, BldMt) for three or six months after "climate-transition attention" crosses its past-only 80th percentile, sized to 5% residual volatility. Its best-specified form, which I froze before testing it, triggers on the energy-and-environmental-regulation share of volatility news, lagged one month. I asked three questions of the strategy: what the signal measures, what the legs are, and whether any version survives a window it was not designed on. The study uses Fama-French industry and factor returns, FRED news and macro series, two climate-concern indices (MCCC and CPU) and EPA supply-chain emission factors; every inference uses real-time inputs and small-sample p-values, each module fixes a primary test, and an independent verifier rebuilt each module's headline numbers. The recommendation is Do not implement, for four reasons. First, the "attention" series is FRED's equity-volatility news tracker for energy and environmental regulation (identical in 500 of 500 months), its z-score is uncorrelated with media climate concern (r = -0.0004), and the same machinery fed genuine climate measures earns 0 of 12 validation alphas with t >= 1.96. Second, the rule frozen before its test window earns -0.18% a year over 1994-2009 (t = -0.27, shuffle p = 0.48). Third, the COVID gain belongs to the position: an untimed short of the same leg earns 71% of it, and the rule's edge over that short is +1.84% a year (t = 0.87). Fourth, every timed rule has a negative 2022-2026 holdout alpha in all 900 net-of-cost configurations, all 28 zero-cost runs are negative too, and rates do not explain the loss. Carbon-aware industry momentum and shrinkage-based timing on the same data fare no better. In short: read the label, benchmark timing against the always-on position, and spend the last clean window on one frozen rule.

THE CLAIMS BEHIND IT (Newey-West t, 6 lags; p from t(n-k)).
1. Signal. On VIX and overall-EMV z-scores, the team z-score has R^2 = 0.169, all through overall EMV; its CPU correlation is 0.123 (Holm p = 0.074). Its zeros (39 of 59 months since 2021-10) changed no holdout entry.
2. Placebo. Overall EMV, a pure volatility measure, earns a 1.07% mean validation alpha, against the team signal's 1.45%.
3. Exposures. Green-minus-Brown is short HML (-0.233, t = -4.63), mostly through Brown; the untimed short shares the rules' beta-timing drag.
4. Holdout. Pure 6m nets -1.84% = hedge leakage -0.24% + residual -1.14% - cost 0.46%; Treasury and UMD factors make every holdout alpha more negative.
5. Frozen test. Its pre-registration was hashed before its code existed, but the rule was chosen after 2010-2026 was seen; it meets 1 of 4 pass-bar components, and passing needed about +0.9% a year.
6. Legs. The team emissions file is undocumented; Ships and Aero rank 2nd and 3rd of 41 there, 20th and 31st of 49 on EPA factors, and with Util carry 86% of the COVID gross P&L. An EPA-ranked spread earns a post-2010 FF5+UMD alpha of 4.7% (t = 1.52).
7. Testing. No positive alpha survives its pre-specified family among 23,923 logged tests; only the frozen test's pre-specification is timestamped, and NW(6) over-rejects on synthetic nulls (13 of 100 at 5%).
Already disclosed: static emissions snapshots, final vintages, an assumed EMV lag, a 48-month holdout.

WHAT I NEED, under these headings.
1. Weakest claims. Exactly five, ranked by effect on the verdict or the grade: the sentence, why the evidence is weaker than the wording, and the test or rewording that fixes it. Overreach toward "Do not implement" counts (t = 0.87 does not prove timing adds nothing).
2. Alternative explanations I have not ruled out. At most four, each with a prediction that separates it from mine on this data.
3. The case against "Do not implement": the strongest argument that the verdict is wrong or too broad, and the one result that would reverse it; if none survives these numbers, say so.
4. The three edits that would most improve the grade, each with its section and replacement text.
5. The two assumptions in your answer you are least sure of.

RULES. Work from these numbers; label any number you have not computed as a guess. Cite a paper only with authors, year and the specific claim. Stay under 1,200 words.

## Output summary

### Reply: a five-part referee report (1,340 words against a cap of 1,200)

Claude kept to the five headings, skipped summary and praise, and labelled most numbers it had not computed ("Guess:", "derived", "my assumption"). The full reply is in `claude_response.md`.

- **Five weakest claims, ranked.**
  1. The holdout count: "That makes "900 of 900" one observation reported 900 times." It guessed that −1.84% a year "has |t| < 1" and asked me to "Lead with the frozen specification's holdout alpha, its NW t, a 95% interval and the number of entry months", plus the first principal component's share of the 900 return series.
  2. The frozen test: "Failing to reject zero is not evidence of zero." From t = −0.27 it derived a standard error of about 0.67% a year and a minimum detectable effect of "about 2.8 × 0.67 ≈ 1.9% a year", guessed that a true 1% edge "would fail about half the time", and proposed measuring −0.18% against the rule's validation alpha, "about 2.4 standard errors below it" if that alpha is near the 1.45% mean (a guess). It added that the window "comes before transition risk was plausibly priced".
  3. COVID: the edge's interval "runs from roughly -2.3% to +6.0% a year", "The point estimate favours timing", and the 71% needs a bootstrap interval.
  4. The signal: the summary quotes MCCC and leaves out CPU, "the index closest in concept to "environmental regulation."", and "R² = 0.169 means 83% of the signal's variance is not volatility", which it read as possibly a transition-policy measure. It asked for Spearman and innovation correlations and the overlap of trigger months with top-quintile CPU and MCCC months.
  5. "every inference uses real-time inputs ... each module fixes a primary test" is contradicted by my own disclosures; it supplied replacement wording.
- **Four alternative explanations, each with a separating prediction.** Wrong horizon, citing Pástor, Stambaugh and Taylor (2022) and Ardia, Bluteau, Boudt and Inghelbrecht (2023): Green-minus-Brown should load on lag-0 CPU and MCCC innovations. Industry-specific holdout shocks, with a guess of utilities on data-centre demand plus Ships and Steel: the residual should sit in one or two legs and periods. Unhedged inflation or commodity exposure: WTI or breakevens in the hedge should pull the holdout residual toward zero. The wrong leg: the frozen rule on the EPA-ranked leg should show a validation timing edge over the untimed EPA short.
- **The case against "Do not implement".** The evidence "rejects one timing rule on one poorly classified leg, but the verdict reads as a rejection of the climate trade"; with the EPA-ranked spread at 4.7% (t = 1.52), "the trade is unproven, not refuted." It then argued this mostly fails (the size of the test family, a probably post hoc EPA specification, Bolton and Kacperczyk (2021) on the carbon premium, and Pástor, Stambaugh and Taylor (2022) on realized versus expected green returns) and concluded: ""Do not implement the timed rule" survives", "The broad version should be narrowed, not defended", and the one reversing result is "a positive 2022-2026 alpha for the untimed EPA-ranked short".
- **Three edits.** A narrowed verdict sentence naming "an EPA-ranked Brown leg (post-2010 alpha 4.7% a year, t = 1.52)" as "the only open lead"; a replacement for reasons two to four with placeholders ("about [2.4] standard errors below its validation alpha"; "the frozen specification's 2022-2026 alpha is [x]%"); and a "What did you learn" lesson, "Test the claim, not zero", ending "By that standard the 1994-2009 test is informative and the holdout only weakly so."
- **Least certain assumptions.** The 2.4-standard-error figure, which assumes the frozen rule's validation alpha is near 1.45%, and what drove the holdout ("few holdout entries", Util, Ships and Steel): "I inferred both from the zero count and from market history, not from your files."

## Evaluation

The reply refereed my wording well and my evidence badly. Every criticism aimed at a sentence landed, but almost every number it needed from our files was guessed, and four of the six guesses I could check were wrong. I checked each point against the modules and ran the missing tests (`checks/fc04_checks.py`, exploratory).

**All five criticisms of my wording were right, and the executive summary now follows them.** "900 of 900" is one result: corrected Original and Pure coincide in all 48 holdout months, so the six rules have four return paths, and the first principal component carries 90% of their variance. The summary and Section 2.3 now lead with Pure 6m (FF3 alpha −1.97% a year, t = −1.30, six entries; 95% interval −5.0% to +1.1%). Its power arithmetic for the frozen test is right (standard error 0.68%, so only an edge of about 1.9% a year passes with 80% probability) and exposed an error of mine: "+0.9%" was the shuffle's bar, while the t bar needed +1.4%. The COVID edge's interval runs from −2.6% to +6.2%, and a block bootstrap puts the 71% between −36% and 233% (90%), so the ratio left the summary. The omitted CPU correlation and the "real-time inputs" overclaim are fixed in its words.

**Three corrections were wrong.** Its first fix, lead with the frozen rule's holdout alpha, is impossible: the frozen rule's zero clause switches it off from 2022-04 onward, so it never trades there. Its guess that the holdout |t| is below 1 fails for every rule (t = −1.30 to −1.90 corrected, −1.66 to −2.19 as our team ran them); only the residual term qualifies (t = −0.86). And its second edit would have put a false claim in the summary: "2.4 standard errors below its validation alpha" compares a timing alpha with a mean strategy alpha (1.45%); the frozen rule's own seen-window timing alpha was −0.12% (t = −0.19), so its proposed lesson, that the 1994–2009 test is informative, has no footing either. It flagged this as its least certain assumption. A true 1% edge fails 70% of the time, not half as it guessed.

**Three of its four alternatives were already answered by modules my prompt left out.** Same-month slopes on MCCC and CPU shocks have the wrong sign (t = −0.49 and −1.23). M2's commodity hedge left every holdout alpha negative; oil in the evaluation trims Pure 6m's to −1.50% (t = −0.88), and breakevens add nothing once oil is in. The split is not what it guessed: Util, which it blamed, contributed a gain (+1.07 points), and Steel's −1.37 points match the −1.38-point gross loss only because that gain offsets Ships, Aero and BldMt (−1.08). On the EPA leg the frozen rule earns −0.01% over 1994–2009.

**Its case against the verdict was aimed at the wrong result.** Its reversal test, a positive holdout alpha for the untimed EPA-ranked short, is met (+1.07%, t = 0.79) by a position whose 1994–2009 alpha is −1.57% (t = −0.74): a sign on 48 months, the counting its own first point warned against. The strongest case against sits in my own results: our team's signal, lagged, has a timing alpha of +0.69% over 1994–2009 (t = 1.00) and +0.36% (t = 0.70) pooled over both windows it was not designed on. My prompt left it out.

Claude is a good referee of prose and arithmetic and a weak one of data it cannot see. Its derived numbers were right to rounding and its citations accurate; it ran 12% over its word cap (1,340 of 1,200). A red team is only as hard as its evidence: the next prompt sends the best result against my verdict, not only the results for it.
