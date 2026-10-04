# Red team: The revised verdict against its own best counter-evidence

Tool: ChatGPT
Date: 2026-09-26
Purpose: red-team review of the conclusion

## Prompt

### Message 1 (single prompt, round 2: the revised executive summary, its claims and the best evidence against it)

Read my draft conclusion as the skeptical investment-committee member who must sign "Do not implement", then as a finance-journal referee. No summary, no praise.

SETTING. My solo extension of our team's MFE 230GA final project (40% thesis, 40% execution, 20% originality).

EXECUTIVE SUMMARY (DRAFT).
Our team's halfway project proposed a state-dependent climate trade, and this report is my solo extension of it. The strategy shorts a factor-hedged Brown leg of five high-emission industries (utilities, shipbuilding and railroad equipment, aircraft, steel, construction materials) for three or six months after "climate-transition attention" crosses its past-only 80th percentile, sized to 5% residual volatility. I tested it on Fama-French industry and factor returns, FRED news and macro series, two climate-concern indices, media climate change concern (MCCC) and climate policy uncertainty (CPU), and EPA supply-chain emission factors. Every threshold, percentile and hedge uses only past data, p-values come from small-sample t distributions, and independent code rebuilt each module's headline numbers. The recommendation is Do not implement, for four reasons. First, the "attention" series is FRED's equity-volatility news tracker for energy and environmental regulation (identical in 500 of 500 months). Its z-score is uncorrelated with MCCC (r=-0.0004), its weak link to CPU (r=0.123, Holm p=0.074) runs through overall volatility news, and the same rules fed either climate index earn 0 of 12 validation alphas with t>=1.96. In plain terms, the rule shorts value-tilted utility and industrial stocks after stock-market volatility makes the news. Second, a cleaner version frozen before its test (the regulation share of volatility news, lagged one month) has a timing alpha of -0.18% a year over 1994-2009 (t=-0.27; p=0.48 against random re-datings of its holding periods); that window detects an edge of about 1.9% a year with 80% power, so the fail excludes a large edge, not a small one. Third, most of the COVID gain came from the position: the rule's alpha over an untimed short of the same leg is +1.84% a year (t=0.87; 95% interval -2.6% to +6.2%). Fourth, every one of our team's timed rules lost over the 2022-2026 holdout, before costs as well as after (6-month rule: FF3 alpha -1.97% a year, t=-1.30), the untimed short lost too (-1.72%, t=-1.09), and rates do not explain the loss; the 900 net-of-cost variants share that one 48-month window, so their common sign is one result. Of the alternatives, shrinkage timing collapses to the historical mean, and an optimized industry-momentum book that passed a pre-registered 1931-1969 test (alpha 1.95% a year, t=2.45) fails the deflated appraisal ratio and lost in the holdout (-0.34%), which earns it a paper-trading pilot, not capital. In short: read the label, benchmark timing against the always-short position, and spend the last unused window on one frozen rule.

CLAIMS BEHIND IT (annualized; Newey-West t, 6 lags).
1. Signal: R^2=0.169 on VIX and overall-EMV z-scores, all through overall EMV; its non-volatility topic share correlates 0.03 with CPU; same-month Green-minus-Brown slopes on MCCC and CPU shocks are wrong-signed (t=-0.49, -1.23).
2. Exposures: Green-minus-Brown loads -0.233 on HML (t=-4.63), mostly through Brown; the hedged rules keep -0.015 to -0.053 since 2010.
3. Holdout: the 6-month rule's -1.84% net is leakage -0.24%, residual -1.14% and cost 0.46%, from six entries; Steel carries -1.37 of -1.38 gross points. BOND, UMD or a commodity factor leave every alpha negative.
4. Frozen rule: chosen after 2010-2026 was seen; in position 142 of 190 months; off from 2022-04, so flat through the holdout.
5. Legs: Ships and Aero rank 2nd and 3rd of 41 in the undocumented team file, 20th and 31st of 49 on EPA factors. The EPA-ranked spread's post-2010 FF5+UMD alpha is 4.7% (t=1.52).
6. Testing: 73 primary alphas, best one-sided p=0.030, smallest Holm p=1.00; that t rejects 13 of 100 synthetic nulls at 5%.

BEST EVIDENCE AGAINST ME.
a. Our team's signal, lagged: timing alpha +0.69% over 1994-2009 (t=1.00; all five drop-one-industry alphas positive), +0.36% (t=0.70) pooled over both unseen windows.
b. COVID, against an exposure-matched benchmark: 5.4% (t=2.35), 3.0% (t=1.67) with in-window factors.
c. Momentum book, 2010-2026: alpha 3.12% (t=2.18).

WHAT I NEED, under these headings.
1. Weakest claims: five summary sentences, ranked by effect on the verdict (overreach toward "Do not implement" counts), each with the gap between evidence and wording, and the test or rewording that closes it.
2. Alternatives I have not ruled out: at most three, each with a separating prediction on this data.
3. The case against "Do not implement": the strongest argument that it is wrong or too broad, and the one result that would reverse it (or "none").
4. Three edits that would most improve the report, with replacement text no longer than the original.
5. Your two least certain assumptions.

RULES. Label any number you have not computed as a guess. Cite papers by authors, year and claim. Under 1,000 words.

## Output summary

### Reply: a five-part referee report (1,091 words against a cap of 1,000)

ChatGPT kept to the five headings and skipped summary and praise. It labelled two numbers as its own ("Guess: in 2022–2025 the coverage was mostly IRA subsidies, tariffs and rollbacks that favoured Steel"; "The 1.4% is my arithmetic from your t=0.70, not a computed result") and cited six papers by authors, year and claim. The full reply is in `chatgpt_response.md`.

- **Five weakest claims, ranked.**
  1. Reason 2, the frozen rule: "This rejects a rule you are not proposing", because in position 142 of 190 months "it is mostly the untimed short". Our team's lagged rule earns +0.69% in the same window, and "the 1.9% power caveat applies to that result too". Also: "A p of 0.48 for a negative alpha means either the re-dating null is centred below zero or the test is two-sided. Say which." And "name which window is "the last unused" one."
  2. Reason 4, the holdout: "The evidence is one industry (Steel, −1.37 of −1.38 gross points), six entries and t=−1.30"; "the holdout indicts the position, not the timing the thesis sells"; the −1.97%, −1.84% and −1.38% figures "are never reconciled". It asked for the holdout timing alpha, the ex-Steel alpha and the model behind each number.
  3. Reason 1, "In plain terms": R² = 0.169 "leaves 83% of the signal unexplained", the hedged rules keep "at most −0.053 HML", and "A mislabelled signal can still pay. This reason supports "don't call it climate", not "don't implement"." Its fix: rerun the rule on the signal's residual after VIX and EMV.
  4. Reason 3, COVID: the claim "rests on a point estimate", and the exposure-matched benchmark gives 5.4% (t = 2.35). It asked me to write "the data cannot split the COVID gain between position and timing" and to "say why you prefer one".
  5. The opening's "five high-emission industries", given EPA ranks of 20th and 31st: "The verdict therefore covers this construction, not the thesis."
- **Three alternatives, each with a separating prediction.**
  - Wrong legs, citing Ardia, Bluteau, Boudt and Inghelbrecht (2023) and Pástor, Stambaugh and Taylor (2022): "on EPA-ranked legs the slopes turn positive and the MCCC- and CPU-timed validation alphas improve. If they do not, the thesis fails at industry level whatever the signal."
  - Regulation news without a direction, citing Baker, Bloom, Davis and Kost (2019): split the entries by administration or by hand-coded articles. "The short should earn after tightening news and lose after loosening news, and the Steel loss should cluster in tariff and IRA months."
  - A crisis hedge: "timing alpha concentrates in months with VIX above 30 or in NBER recessions, and is near zero elsewhere."
- **The case against "Do not implement".**
  - "The verdict is right for this rule, but it is written as if the climate thesis was tested."
  - For the rule, the evidence reads "not proven", not "disproven", on four grounds: "positive in both unseen windows"; "robust to dropping any one industry"; 5.4% (t = 2.35) against an exposure-matched COVID benchmark; and "a holdout loss that comes from one industry".
  - On momentum, the deflated Sharpe ratio (Bailey and López de Prado 2014) applied to a pre-registered pass "double-counts trials". If 2010–2026 was not used for optimisation, the book "has two out-of-sample passes (t=2.45 and 2.18)", which with Moskowitz and Grinblatt (1999) "argues for small capital".
  - The committee's stronger case: "Your best unseen estimate (+0.36%) is below the holdout cost (0.46%)", and Bolton and Kacperczyk (2021) give the always-short leg "a negative expected return".
  - Reversing result: "none on existing data ... Only a frozen rule's forward record can reverse the verdict."
- **Three edits.**
  - Edit 1 rewrites Reason 2 around our team's pooled +0.36%, "below its 0.46% annual holdout cost", and detectable edges of "about 1.4–1.9% a year".
  - Edit 2 rewrites Reason 4: the timed rules lost "about as much as the untimed short ..., so timing added little; Steel accounts for nearly all of the gross loss".
  - Edit 3: "In plain terms, the signal counts regulation mentions in volatility news; no test links it to climate concern." It is stated as 17 words and has 18.
- **Least certain assumptions.**
  - That "13 of 100 synthetic nulls" means a 13% rejection rate, so "every t in the report is overstated, including 2.35, 2.45 and 2.18".
  - That the two timing alphas are measured the same way, and that "the 0.46% holdout cost reflects the lagged rule's turnover in other windows. The cost comparison in Edit 1 depends on both."

## Evaluation

This round did what round 1's evaluation asked for: the prompt sent the best evidence against my verdict as well as the evidence for it. ChatGPT used that evidence as an advocate would, selectively, and that is where it went wrong. I checked every point against the modules and ran the tests it proposed (`checks/fc04b_checks.py`, exploratory).

**All five weak claims found real gaps in the wording, and the summary now closes them.** "Five high-emission industries" hid that EPA factors rank Ships and Aero 20th and 31st of 49. "Most of the COVID gain came from the position" rested on a point estimate: the rule's edge is +1.84% over the untimed short (t = 0.87) and 3.0% over an exposure-matched one (t = 1.67), so the window cannot split the gain. "p = 0.48" needed its null, whose median is −0.22%. "Value-tilted" described the raw leg rather than the hedged rule, and a wrong label explains why the thesis is untested, not why the returns fail, so the verdict sentence now says both. "The last unused window" is the live record.

**Four of its supporting claims were wrong.** The holdout does not indict "the position, not the timing": against an exposure-matched short the timing lost a further 1.0% to 1.7% a year (t = −0.99 to −1.72). The loss does not come from one industry either: rebuilt without any one industry, the rule still loses in 10 of 10 cases (FF3 alpha −1.26% to −2.61%). Both results now stand in the summary. The figures it called unreconciled add up in my own claims list. And the residual test it asked for is the frozen rule, which trades the signal with overall volatility news divided out, the same rule it had just dismissed as one I am not proposing.

**Each alternative failed its own prediction.** On EPA-ranked legs the same-month slopes on MCCC and CPU shocks became more wrong-signed (t = −2.95 and −2.17), and CPU timing added no detectable edge over the untimed EPA short (holdout +0.05% to +1.22%, largest t = 1.43; negative in 5 of 6 rules over 1994–2009); Section 2.1 and Appendix C now say so. With the administration as a crude proxy for policy direction, the short lost more after entries under Biden (−4.5 gross points) than under Trump (−1.0). And 80% of the 6-month rule's 1994–2026 timing gain came in months with VIX at or below 30, 95% outside NBER recessions.

**Its case against the verdict misread what I sent.** "Positive in both unseen windows" reads a pooled +0.36% as two positives; the windows give +0.69% (t = 1.00) and −1.11% (t = −1.13). Its committee argument set that timing alpha against the 0.46% holdout cost, but the alpha is computed on net returns, so the cost is already inside it. The deflated appraisal ratio is applied to the windows the momentum book was chosen on, and 2010–2026 is one of them, so it is no second out-of-sample pass. None of its three edits went in as written: two carry these errors, and the third runs 18 words against a 17-word original while claiming 17.

**ChatGPT referees sentences well and reads numbers carelessly.** Sending the counter-evidence bought sharper, testable alternatives, but an advocate quotes the favourable half: 5.4% without the 3.0%, and the 1994–2009 drop-one result without the holdout. As in round 1, the error that reached its replacement text sat in the assumption it flagged as least certain, and it again ran over its cap (1,091 words of 1,000). Read its flags, test its predictions, and never paste its edits.
