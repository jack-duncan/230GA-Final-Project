# Follow-up: Signal Choice and Attribution

Your corrections are right, including the ones on duration and the IC. The EMV finding matters more than any of them. The signal we validated partly tracks news about market volatility, and the holdout ran on a different, near-binary signal. That explains the holdout but does not rescue the strategy. On the data you have already seen, timed minus always-on peaks at t = 1.09, so **"Do not implement" stands**.

---

## (a) Salvage the series; don't replace it

- **MCCC can't test 1993–2009** because it starts in 2003.
- **CPU would only cover about 1995–2009** once the burn-in is used up (a guess). Its correlation with your series is +0.11, so switching to it tests a new hypothesis rather than a cleaner version of yours.
- Run CPU and MCCC only after the primary test, and label them exploratory.
- **Use the series as a share of total EMV.** As I understand the construction, the category tracker equals overall EMV times the fraction of EMV articles that mention the category. Dividing by overall EMV removes the part scaled to the VIX and leaves the attention part. This goes straight at your odds ratio of 4.5.

**The rule to freeze.** Write it down before you load any pre-2010 data.
1. **Signal:** s_t = EMVENRGYENVREG_t / EMVOVERALLEMV_t.
2. **Zeros:** treat a zero month as missing, not as low attention.
   - A zero month cannot trigger a position.
   - Drop zero months from both the z-score window and the percentile history.
   - The z-score needs at least 48 nonzero months out of the trailing 60.
   - If more than 10% of the trailing 60 months are zero, the signal is off.
3. **Extreme month:** z_t is the 60-month rolling z-score of log(s_t). A month is extreme when z_t exceeds its expanding, past-only 80th percentile.
4. **Trade:** the validated 6-month Short-Brown rule, unchanged: lagged 60-month FF3 hedge, 5% vol target, cap 1x, same costs. A new crossing during a hold extends the hold; positions never stack.
5. **Sample:** Jan 1993 to Dec 2009, run once.
6. **Pass bar:** all four of the following. Anything less confirms "Do not implement."
   - The timing alpha from (b) is above zero with t ≥ 2, using t(n−k) p-values.
   - The calendar-shuffle p is 0.05 or lower.
   - There are at least 8 independent episodes (a guessed threshold).
   - The alpha keeps its sign when each Brown industry is dropped in turn.

**Caveat:** the zero rule (rule 2) would probably have kept you flat for most of the holdout (a guess). It was written after seeing the holdout, though, so take no credit for that period.

---

## (b) Attribution spec

**Dependent variable.** D_t = R^T_t − π·R^AO_t, net of costs.
- R^T is the timed strategy.
- R^AO is always-on Short-Brown with the same hedge and vol target.
- π = mean timed weight / mean always-on weight. The benchmark then has the same average exposure as the timed strategy but no timing.

**Regressors.** These are for ex-post attribution only; keep the ex-ante hedge unchanged.
- FF5 + UMD.
- **Duration:** TERM_t ≈ −8·Δy10_t, an approximate 10-year Treasury return. The duration of 8 is a guess.
- **Commodity:** the WTI log return.
- **Volatility:** ΔVIX_t (VIX data start in 1990) and Δlog EMV_t.
- **Conditional terms:** I_{t−1} × {Mkt, HML, TERM, ΔVIX}, where I_{t−1} = 1 if the strategy is in position. This follows Ferson and Schadt (1996), who let betas vary with lagged public information so that changing exposure is not counted as skill. Here it means any return from loading on value, duration or volatility only while in position counts as beta.

**Model.** D_t = α + β′F_t + γ′(I_{t−1}·F_t) + ε_t.

**Inference.**
- Newey-West standard errors with 6 lags, and 12 as a check.
- p-values from t(n−k), with k = 14 parameters.
- The null with matched exposure is a calendar shuffle: move the same hold windows to random dates 5,000 times and recompute α each time.

**What counts as alpha.** Only α.
- Report the decomposition mean(D) = α + Σβ·mean(F) + Σγ·mean(I·F). That gives duration, value and volatility a number each.
- Timing alpha exists only if α passes the bar in (a) and survives the volatility block.
- If α drops when ΔVIX and ΔEMV enter, the signal was a volatility bet, not a climate one.
