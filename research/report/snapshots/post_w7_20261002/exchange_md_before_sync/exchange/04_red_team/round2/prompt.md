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
