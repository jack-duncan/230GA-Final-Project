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
