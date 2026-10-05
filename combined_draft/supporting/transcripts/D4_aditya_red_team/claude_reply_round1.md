## 1. Weakest claims (ranked)

**1. "every timed rule has a negative 2022-2026 holdout alpha in all 900 net-of-cost configurations, all 28 zero-cost runs are negative too"**
*Why weak:* All 900 configurations run on the same 48-month path of the same Brown leg. That makes "900 of 900" one observation reported 900 times. You give no t-statistic, no interval and no count of entries. Since 39 of the last 59 months are zeros, the rule may have traded only a few episodes. Guess: at 5% residual volatility over 48 months, -1.84% a year has |t| < 1.
*Fix:* Lead with the frozen specification's holdout alpha, its NW t, a 95% interval and the number of entry months. Report how much of the variance in the 900 return series the first principal component explains. Call the rest "robustness of sign."

**2. "the rule frozen before its test window earns -0.18% a year over 1994-2009 (t = -0.27, shuffle p = 0.48)"**
*Why weak:* Failing to reject zero is not evidence of zero. The implied standard error is about 0.67% a year (0.18/0.27, derived), so the +0.9% pass bar needed t ≈ 1.35. Guess: a true 1%-a-year edge would fail about half the time. The window also comes before transition risk was plausibly priced, and the legs use today's emissions snapshot.
*Fix:* Test against the effect you are rejecting. If the frozen rule's own validation alpha is near the 1.45% mean (guess), -0.18% is about 2.4 standard errors below it. Report that, plus the minimum detectable effect at 80% power: about 2.8 × 0.67 ≈ 1.9% a year (derived).

**3. "the COVID gain belongs to the position ... +1.84% a year (t = 0.87)"**
*Why weak:* The implied standard error is about 2.1%, so the 95% interval runs from roughly -2.3% to +6.0% a year. The point estimate favours timing. "71%" is a ratio of two noisy P&Ls with no interval.
*Fix:* "Most of the COVID gain came from the position (71%). The timing edge of +1.84% a year cannot be told apart from zero or from 5% a year." Add a bootstrap interval on the 71%.

**4. "its z-score is uncorrelated with media climate concern (r = -0.0004)"**
*Why weak:* You quote MCCC and leave out CPU (r = 0.123, Holm p = 0.074). CPU is the index closest in concept to "environmental regulation." A Pearson r on a zero-inflated series is fragile. Also, R² = 0.169 means 83% of the signal's variance is not volatility. Counting newspaper articles that tie market volatility to environmental regulation is plausibly a transition-policy measure; the label alone does not rule that out.
*Fix:* Report both correlations, as Spearman and on innovations. Add the overlap between trigger months and top-quintile CPU and MCCC months. Reword to "weakly related to climate-policy uncertainty, unrelated to media climate concern."

**5. "every inference uses real-time inputs ... each module fixes a primary test"**
*Why weak:* Your own disclosures contradict both halves. Final vintages and static emissions snapshots are not real-time inputs, and only the frozen test's pre-specification is timestamped. A referee who catches this will discount everything after it.
*Fix:* "Every threshold, percentile and hedge uses only past data; macro series are final vintages and emissions a static snapshot. Each module names a primary test; only the frozen test's was timestamped before its data were seen."

## 2. Alternative explanations not ruled out

1. **Wrong horizon, not wrong signal.**
   - Pástor, Stambaugh and Taylor (2022) find green stocks outperformed in 2012-2020 mainly because climate concern rose more than expected. Ardia, Bluteau, Boudt and Inghelbrecht (2023) find brown stocks fall on days when climate concern rises unexpectedly.
   - If prices adjust in the same month, a short entered one month later and held 3-6 months arrives after the move.
   - *Prediction:* Green-minus-Brown loads positively on lag-0 CPU and MCCC innovations, and at zero or below at lags 1-6. Your explanation predicts no loading at any lag.

2. **Industry-specific holdout shocks.**
   - Guess: utilities repricing on data-centre power demand in 2024-25, and Ships and Steel in 2021-22, drive the -1.14% residual.
   - *Prediction:* splitting the residual by industry and year puts most of it in one or two legs and periods. Your explanation predicts losses spread across legs and years.

3. **Unhedged inflation or commodity exposure.**
   - You tested rates, not inflation. Steel, BldMt and Ships are commodity-sensitive.
   - *Prediction:* adding FRED WTI returns or 10-year breakeven changes to the hedge pulls the holdout residual toward zero. Your explanation predicts no change.

4. **Wrong leg.**
   - Ships and Aero rank 20th and 31st of 49 on EPA factors.
   - *Prediction:* the frozen rule applied to the EPA-ranked leg shows a validation timing edge over the untimed EPA short. Your explanation predicts about zero edge there as well.

## 3. The case against "Do not implement"

**The strongest argument:**
- The evidence rejects one timing rule on one poorly classified leg, but the verdict reads as a rejection of the climate trade.
- The untimed short captured 71% of the COVID gain, and the timing edge's point estimate is positive.
- The EPA-ranked spread earns 4.7% a year after 2010. Its implied standard error is about 3.1%, so the interval runs from roughly -1.4% to +10.8%.
- On that evidence the trade is unproven, not refuted.

**Why it mostly fails:**
- A t of 1.52 does not survive a family of 23,923 tests.
- The EPA spread was probably specified after the post-2010 results were known (my assumption).
- Bolton and Kacperczyk (2021) find that higher-emission stocks earn higher returns, so an always-on Brown short expects to pay a carbon premium.
- Pástor, Stambaugh and Taylor (2022) argue that green stocks' realized outperformance does not mean higher expected returns.

**Verdict:**
- "Do not implement the timed rule" survives. Nothing in the current data can reverse it, because both clean windows are spent.
- The broad version should be narrowed, not defended.
- The one result that would reverse the broad version is a positive 2022-2026 alpha for the untimed EPA-ranked short, which you do not report. If it is negative, say so and the broad verdict stands.

## 4. Three edits for the grade

**1. Executive summary, verdict sentence.** Replace "The recommendation is Do not implement, for four reasons." with:
> "The recommendation is Do not implement the timed rule. The untimed Brown short is unproven rather than refuted; an EPA-ranked Brown leg (post-2010 alpha 4.7% a year, t = 1.52) is the only open lead and does not survive the test family. Four reasons:"

**2. Executive summary, reasons two to four.** Replace with:
> "Second, the frozen rule earns -0.18% a year over 1994-2009 (t = -0.27), about [2.4] standard errors below its validation alpha, though the window cannot exclude an edge near 1.9% a year. Third, the untimed short earns 71% of the COVID gain; the timing edge, +1.84% a year (95% interval about -2.3% to +6.0%), is not distinguishable from zero. Fourth, the frozen specification's 2022-2026 alpha is [x]% (t = [y], [n] entries); all 900 configurations share that 48-month path and its sign, and rates do not explain it."

Drop "Carbon-aware industry momentum and shrinkage-based timing ... fare no better", or give each one's best alpha and adjusted p.

**3. "What did you learn".** Replace whichever lesson restates a count of tests or configurations:
> "Test the claim, not zero. Counting negative configurations felt decisive, but 900 configurations share one 48-month path. What separates results is how far the out-of-sample alpha sits from the in-sample one in standard errors, and the smallest effect the window could detect. By that standard the 1994-2009 test is informative and the holdout only weakly so."

## 5. The two assumptions I am least sure of

1. **The 2.4-standard-error figure.** It assumes the frozen rule's own validation alpha is near the 1.45% mean and that alpha divided by t gives a usable standard error. Your finding that NW(6) rejects 13 of 100 synthetic nulls at 5% suggests the standard errors are understated. If so, every interval above widens and the 2.4 shrinks.
2. **What drove the holdout.** I assumed there are few holdout entries, and that Util, Ships and Steel drove the loss. I inferred both from the zero count and from market history, not from your files.
