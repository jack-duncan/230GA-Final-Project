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
