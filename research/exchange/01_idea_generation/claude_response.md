# Design Review: Climate-Attention Timing of Short-Brown

**Bottom line:** The holdout failed, validation rests on one episode, and timing beats always-on Short-Brown by roughly 0.3% a year (1.3% vs 1.0%, arithmetic on your figures). Make "Do not implement" airtight, and test pre-specified ideas on the one period nobody has looked at, **1990–2009**.

---

## 1. Design critique

**1. The benchmark is wrong for a timing claim.**
- *Problem:* Timed returns are tested against zero. For a timing thesis the null is "always short Brown, same hedge, same vol target."
- *Why it matters:* The signal adds about 0.3%/yr over 2010–2026. Also, the traded position has no Green leg, so "Green minus Brown" isn't what you're testing.
- *Fix:* Make the primary statistic the alpha of (timed − always-on), or regress hedged Brown returns on an in-position dummy. Restate the thesis as "Brown underperforms after attention spikes."

**2. Validation is one episode.**
- *Problem:* Both Holm survivors are COVID; the 3-month rule's 2020–21 alpha (t = 3.21) carries the result.
- *Why it matters:* Aero (Boeing-heavy: 737 MAX grounding plus the travel collapse), Ships and Util took COVID-specific hits unrelated to transition risk. With five equal-weighted industries, each is 20% of the leg.
- *Fix:* Leave-one-industry-out, and rerun excluding Mar 2020–Dec 2021. If the 6-month t-stats drop below ~1.5, the Executive Summary should say so.

**3. The holdout is spent; everything after it is post-hoc.**
- *Problem:* The high-rate interaction was found with 47 of its 74 months in the holdout.
- *Why it matters:* It can't be confirmed on the data that suggested it. The holdout also doesn't prove a *reversal*: with ~48 months the IC's standard error is roughly 1/√48 ≈ 0.14 (a rough approximation that ignores overlap), so −0.08 → +0.13 is about one standard error of the difference. The honest reading is "failed to confirm," not "flipped."
- *Fix:* Declare 1990–2009 the new frozen holdout and write down one rule before running it.

**4. The Brown leg may not measure what the thesis claims.**
- *Problem:* One static snapshot, eight industries missing, including Oil, the most obvious transition-risk industry. Aircraft and Shipbuilding in the top five by emissions intensity is surprising; check the mapping and where Coal ranks.
- *Why it matters:* If the ranking is off, a "climate" result is an "industrials and utilities" result.
- *Fix:* Rebuild intensity from EPA supply-chain GHG factors (NAICS → SIC → FF49) covering all 49, and rerun with Oil and Coal in.

**5. Hedge residuals line up with the regime story.**
- *Problem:* Residual HML ≈ −0.05 (t ≈ −2) in *every* version, and no control for momentum, profitability/investment, rates or commodities.
- *Why it matters:* Util, BldMt and Steel are rate- and commodity-sensitive. A 2022–2026 holdout dominated by rates can lose money through unhedged duration, not climate.
- *Fix:* Attribute ex post against FF5 + UMD + a rate factor (e.g., Δ10-year yield) + a commodity return. Keep the ex-ante hedge unchanged so you aren't re-optimizing.

**6. Inference is weaker than the t-stats suggest.**
- *Problem:* Overlapping 3–6-month holds, few independent crossings, 4+ variants, and a purified signal built from CPI, CFNAI and GSCPI, which are published with a lag and revised.
- *Why it matters:* Too few Newey-West lags overstate t; final-vintage macro data is look-ahead. The continuous variant's lower vol and drawdown is partly mechanical (lower average exposure), which is consistent with placebo p ≈ 0.12.
- *Fix:* NW lags ≥ hold length; report the count of independent events; block-bootstrap by event; lag macro inputs 1–2 months; compare the continuous variant with always-on scaled to the same average exposure.

---

## 2. Proposal ranking

| Rank | Proposal | Result that would change our conclusion | What it cannot tell us | Overlap | Hours | Reasoning |
|---|---|---|---|---|---|---|
| 1 | **E** Alpha vs beta | Timed − always-on alpha significant after FF5+UMD | Whether the mechanism is climate | B, F, G | 4–6 | The question graders ask, and the one your numbers are closest to answering |
| 2 | **A** 8+8 industries (add leave-one-out) | Timing alpha survives broader legs and dropping Aero | Whether emissions matter vs any 5 industries | C | 3–4 | Cheap; directly tests the COVID concentration |
| 3 | **G** Momentum control | Signal loses a horse race to Brown's own trailing 3–12m return | Whether attention causes the persistence | B | 2–3 | Cheap; kills the simplest alternative story |
| 4 | **B** Momentum + commodity controls | Alpha t falls below ~1.5 with a commodity factor | Climate vs commodity channel (Oil is missing) | G, F | 3–5 | Useful but mostly subsumed by E |
| 5 | **F** Macro controls | Alpha vanishes when conditioning on rate/inflation state | Anything confirmatory; regimes were picked after seeing the holdout | B, purified variant | 6–10 | Most expensive, most overfit-prone |
| 6 | **C** Green industries one by one | Little: Green isn't in the traded position | Source of the *traded* HML residual (that sits in Brown) | A | 2 | Redirect it to the five Brown industries |
| 7 | **D** Uniform 5/10/25 bp | Only a break-even cost below ~10 bp, unlikely with 3–6-month holds (guess) | Anything about the signal | none | 1 | Costs can't rescue a −2% to −4% holdout; report break-even instead |

---

## 3. New ideas

### Idea 1 (extension): Backward out-of-sample test, 1990–2009
- **(a) Hypothesis:** The frozen 6-month rule earns positive alpha over always-on before 2010. *Rejected* if timed − always-on alpha ≤ 0 or t < 1.
- **(b) Test:** Signal from Jan 1990 (60-month z-score uses 1985–89); purified variant from ~1995 (120-month ridge). Hedged Short-Brown, 5% vol target, validation parameters unchanged. FF3 and FF5+UMD alpha, NW 6 lags. Benchmark: always-short Brown. Pass: t > 2. Pre-register the high-rate interaction as a second hypothesis, Holm across both.
- **(c) Data:** In hand.
- **(d) Pitfalls:** Static snapshot applied backward (classification look-ahead); transition risk was arguably unpriced before ~2005, so failure doesn't fully kill the mechanism; early index coverage may be thin.
- **(e) Effort:** 3–5 h.
- **(f) If it fails:** Twenty more years behind "Do not implement," from the cleanest test left.

### Idea 2 (extension): Timing increment and event-time profile
- **(a) Hypothesis:** Hedged Brown residuals are more negative in t+1…t+6 after crossings than unconditionally. *Rejected* if the post-event cumulative residual is within one SE of zero, or the move sits in spike month t itself.
- **(b) Test:** 2010–2026 only until Idea 1 is run (don't contaminate the new holdout). Event-time averages t−3…t+6; regression of residual on a post-event dummy, NW 6 lags. Benchmark: always-on. Pass: dummy t > 2 excluding 2020–21.
- **(c) Data:** In hand.
- **(d) Pitfalls:** Overlapping events (merge crossings within 6 months), small N (report event count), COVID dominance.
- **(e) Effort:** 3–4 h.
- **(f) If it fails:** Evidence attention is priced on impact. Ardia, Bluteau, Boudt & Inghelbrecht (2023) find green stocks rise and brown stocks fall on days of unexpected increases in climate-change concerns; Pástor, Stambaugh & Taylor (2022) attribute green outperformance over 2012–2020 to unanticipated strengthening of climate concerns. If the repricing is contemporaneous, a post-spike rule has nothing left to harvest.

### Idea 3 (extension): Replicate the signal across attention indices
- **(a) Hypothesis:** If the effect is about climate attention, the frozen rule works with the Climate Policy Uncertainty (CPU) and Media Climate Change Concerns (MCCC) indices. *Rejected* if neither gives timed − always-on t > 1 with the same sign.
- **(b) Test:** Identical rule and parameters, swap the signal; samples set by index start dates (CPU late 1980s, MCCC ~2003; verify). Pass: same sign in all three, pooled t > 2.
- **(c) Data:** Downloadable, listed.
- **(d) Pitfalls:** Different samples per index; three tests (Holm); the 60-month z-score burns five years of a short index.
- **(e) Effort:** 4–6 h.
- **(f) If it fails:** Shows the result is index-specific noise; earns originality credit either way.

### Idea 4 (alternative): Rebuilt carbon-intensity spread across all 49 industries
- **(a) Hypothesis:** No unconditional premium: an intensity-sorted industry spread has FF5+UMD alpha of zero. Bolton & Kacperczyk (2021) find a positive carbon premium at the firm level; this tests the industry analogue. *Rejected* if alpha t > 2 in either direction.
- **(b) Test:** 1990–2026, monthly; long top-third/short bottom-third intensity, VW industries. FF5+UMD alpha, NW 12 lags; report pre/post-2010 and the last 18 months.
- **(c) Data:** EPA factors (listed); a NAICS→SIC crosswalk (not listed; public concordances exist).
- **(d) Pitfalls:** Single-vintage intensity applied backward; crosswalk error; supply-chain factors include upstream emissions, a different concept from your snapshot.
- **(e) Effort:** 6–10 h.
- **(f) If it fails:** A rigorous version of the "no permanent premium" half of your thesis, with Oil and Coal included.

### Idea 5 (alternative): Climate-news hedge portfolio on FF49
- **(a) Hypothesis:** Following Engle, Giglio, Kelly, Lee & Stroebel (2020), who build mimicking portfolios that hedge innovations in a climate news index, an FF49 portfolio mimicking attention innovations hedges out of sample. *Rejected* if its out-of-sample correlation with next-month innovations is ≤ 0.
- **(b) Test:** 1995–2026. Monthly rolling 60-month regressions of each industry's excess return on attention innovations (past-only AR(1) residual) plus FF3; long top-10/short bottom-10 by beta, one-month hold. Pass: OOS correlation t > 2; report alpha as the price of the hedge.
- **(c) Data:** In hand.
- **(d) Pitfalls:** Noisy betas, only 49 assets, innovation definition choice, full-sample AR fits (look-ahead).
- **(e) Effort:** 6–8 h.
- **(f) If it fails:** Reframes attention as a risk to hedge, not a signal to trade.

---

## 4. Plan
1. **Idea 2 + leave-one-out (Critique #2).** Cheapest, and decides whether timing adds anything over always-on, on data already seen.
2. **Idea 1.** The only clean out-of-sample test left. Freeze the rule in writing first, and don't touch pre-2010 attention data before then.
3. **E with B and G folded in.** FF5 + UMD + rates + commodities attribution for full sample, post-2010 and last 18 months; the report needs it whatever the outcome.

---

## 5. Assumptions I'm least confident about
1. That the attention index has usable coverage in 1985–2009 and the emissions ranking is stable enough to apply backward; if not, Idea 1 is weak.
2. That the COVID gains come from Aero, Util and Ships shocks; this is a hypothesis, not something I computed.
3. The index start dates (CPU, MCCC), the NAICS→FF49 mapping effort, and every hour estimate.
