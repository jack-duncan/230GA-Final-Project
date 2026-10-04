# M8 pre-registration: frozen EMV-share rule, scored once on 1993-2009

Written: 2026-09-26 03:29:54 PDT (2026-09-26T10:29:54Z, from `date`), before any strategy return for 1993-2009 was computed.
Author: research exercise for Hashim (MFE 230GA final project). Module folder: `research/modules/M8_frozen_pre2010/`.
The SHA-256 of this file is recorded by `run.py` in `outputs/tables/M8_preregistration_hash.csv` and quoted in FINDINGS.md, so any later edit is detectable.

## 0. What I had seen before writing this

- Signal-side facts only. EMVENRGYENVREG (the team "attention") is exactly zero in 1 month of 1985-1989, 1 of 1990-1999 and 5 of 2000-2009 (exchange 1, check c06). EMVOVERALLEMV has no zero and no missing month in 1985-01 to 2026-08 (checked while writing this file). The team's same-month raw signal first crosses in 1993-01 and its purified signal in 1999-01.
- No strategy return, hedged residual, P&L or alpha of any rule over 1993-2009 has been computed or looked at by me. Exchange 1 checks were signal-only for pre-2010 by design.
- Known contamination, not removable: (a) the team's macro-state notebook regressed forward Brown-leg residuals on the attention signal from the first available month (192 pre-2010 months), so the team saw pre-2010 residual behaviour in aggregate; (b) the rule below was proposed by ChatGPT and adopted by the student after the 2010-2026 results, including the holdout, were known. Its zero treatment in particular was written after the holdout zeros were seen.

## 1. The rule, verbatim (as adopted in exchange 1 with the student's two amendments)

1. Signal: s_t = EMVENRGYENVREG_t / EMVOVERALLEMV_t, observed one month late (the value for month t is usable at the end of month t+1).
2. Zeros: a zero month is missing, not low attention. It cannot trigger a position, and it is dropped from both the z-score window and the percentile history. The z-score needs at least 48 nonzero months in the trailing 60; if more than 10% of the trailing 60 months are zero, the signal is off.
3. Extreme month: z_t = 60-month rolling z-score of log(s_t) over nonzero months; extreme when z_t exceeds its expanding, past-only 80th percentile (team convention: at least 60 prior z observations).
4. Trade: the team's validated 6-month Short-Brown rule unchanged (lagged 60-month FF3 hedge, 5% vol target, cap 1x, team costs). A new crossing during a hold extends the hold; positions never stack.
5. Sample: 1993-01 to 2009-12 (or from the first month the rule can fire, if later), run once.
6. Pass bar, all four required: (i) the timing alpha from the attribution below is positive with t >= 2 and p from t(n-k); (ii) calendar-shuffle p <= 0.05 (move the same hold windows to random dates, 5,000 times, recompute alpha); (iii) at least 8 independent episodes (merge holds that touch or overlap); (iv) alpha keeps its sign when each Brown industry is dropped in turn.

Attribution: D_t = R^T_t - pi * R^AO_t, net of costs, where R^T is the timed strategy, R^AO the always-on Short-Brown with the same hedge and vol target, and pi = mean |timed position| / mean |always-on position| over the test window. Regress D_t on FF5 + UMD, BOND, WTI log return, dVIX_t (VIX monthly mean, from 1990), dlog EMVOVERALLEMV_t, and conditional terms I_{t-1} x {Mkt-RF, HML, BOND, dVIX} where I_{t-1} = 1 if the strategy held a position entering month t. Alpha = intercept. Newey-West 6 lags (12 as a check); p-values from t(n-k) with k = the actual number of estimated parameters. Report the decomposition mean(D) = alpha + sum beta*mean(F) + sum gamma*mean(I*F).

BOND: monthly excess return of a constant-maturity 10-year Treasury built from GS10 (percent to decimal yields): r_t = y_{t-1}/12 - D_{t-1}*(y_t - y_{t-1}) + 0.5*C_{t-1}*(y_t - y_{t-1})^2, with D and C the modified duration and convexity of a 10-year semiannual par bond at yield y_{t-1}; excess over FF RF.

## 2. Implementation choices the rule leaves open

Each choice is fixed here, before any 1993-2009 return exists. The reason is given for each; none was chosen by looking at returns.

**Data**
- C1. Sources: FRED EMVENRGYENVREG and EMVOVERALLEMV (current vintage in `data/raw`); team FF49 value-weighted industry file and team FF3 file for the legs and the hedge (the team rule "unchanged"); Ken French FF5 (2x3) and momentum files for the attribution factors and for RF in BOND; FRED GS10, VIXCLS (daily) and MCOILWTICO. Why: these are the files the team rule and the attribution name; the team hedge must stay as validated.
- C2. The EMV vintage is today's FRED file, not a real-time vintage. Why: no archived vintages exist offline. The share s_t cancels any common rescaling of the two trackers, which reduces but does not remove the concern.

**Signal**
- C3. A zero month is a month in which EMVENRGYENVREG equals exactly 0.0. A month with EMVOVERALLEMV missing or zero would also be missing (none exists). Why: literal rule.
- C4. All signal steps run in data-month time t. The extreme flag of data month t becomes the decision flag at the end of month t+1. A position set at the end of month tau earns month tau+1 (team convention), so a crossing in data month t first earns month t+2. Why: amendment 1 plus the team P&L timing.
- C5. z_t = (log s_t - mean) / std over the trailing 60 calendar months t-59..t, including month t (team convention), using nonzero months only; std with ddof = 1. z_t is computed only if s_t is nonzero and the window holds at least 48 nonzero months. Months before 1985-01 count as unavailable, not as zeros, so near the series start the 48 minimum acts as the burn-in (the analogue of the team's min_periods = 36). Why: literal reading of "at least 48 nonzero months in the trailing 60" as a calendar window with a minimum count.
- C6. The signal is off in data month t if more than 6 of months t-59..t are zero (more than 10% of 60). When off, z_t is set to missing: it cannot trigger and does not enter the percentile history. Why: "the signal is off" read symmetrically with the zero rule. Once the window is full, at most 6 zeros implies at least 54 nonzero months, so the 48 minimum only binds during the burn-in.
- C7. Threshold_t = 80th percentile (pandas linear interpolation, the team's `expanding_threshold`) of all non-missing z values of data months strictly before t, defined only when at least 60 such values exist. Extreme: z_t > threshold_t (strict, team `gt`). Why: team convention named in the rule.
- C8. Crossing: a month with non-missing z and threshold that is extreme while the previous month with non-missing z and threshold was not extreme (the team's `state & ~state.shift(1)` applied to the sequence of valid months). A zero or off month is skipped: it neither starts nor breaks a run of extreme months. The first valid extreme month counts as a crossing. Why: "a zero month is missing, not low attention" means it carries no state, so it cannot end a run.
- C9. Hold: the position is on at the decision month of the crossing and the next 5 decision months (earning 6 monthly returns), which is the team's `cross_and_holds` rolling maximum. A new crossing inside a hold restarts the 6-month clock from the new crossing, which the union of windows implements; a continuing extreme state without a new crossing does not extend (team rule). Positions never stack because the hold is a boolean. I checked the team code before writing this: `cross_and_holds` already implements extend-not-stack, so no change is needed.

**Strategy**
- C10. Brown leg = equal-weighted mean of the team FF49 VW returns of Util, Ships, Aero, Steel, BldMt minus team RF. Rolling 60-month OLS on team FF3 (`rolling_factor_model`): betas estimated through month t hedge month t+1; residual epsilon = hedged return minus lagged intercept. Magnitude = min(0.05 / (sqrt(12) * sigma_t), 1), sigma_t the 36-month std of epsilon (`state_position`). Position = -magnitude while in hold, else 0. P&L, turnover and costs from `asset_strategy_returns` with the team costs (10bp asset, 5bp Mkt-RF overlay, 25bp SMB and HML overlays, charged the month after the trade). Why: "the team's validated rule unchanged"; team building blocks from `lib/team_pipeline.py`.
- C11. Always-on R^AO: the same engine with the state always on (the team's "Benchmark | Always-short Brown"), net of costs.
- C12. Test window: return months W0 to 2009-12, W0 = max(1993-01, tau0 + 1), where tau0 is the first decision month whose flag is defined (non-missing z and threshold of data month tau0 - 1). The decision months that matter are W0-1 to 2009-11. Positions after 2009-11 earn only post-2009 returns and are ignored. Why: literal rule; months before the rule can fire would be pure dilution.
- C13. pi = mean over return months t in the window of |h^T_{t-1}| divided by the same mean of |h^AO_{t-1}|, where h_{t-1} is the position that earns month t. D_t = net R^T_t - pi * net R^AO_t.

**Attribution regressors (all monthly, month t, decimal unless noted)**
- C14. FF5 + UMD: Mkt-RF, SMB, HML, RMW, CMA (Ken French 2x3) and UMD.
- C15. BOND as specified, from GS10 (FRED monthly average of daily constant-maturity yields). D and C from the exact cash-flow sums of a 20-coupon semiannual par bond at y_{t-1} (modified duration in years, convexity in years squared, both per unit of price). Excess over the Ken French RF. Checks before use: 2022 compounded BOND total return must be large and negative; D at 1990s yields must match the closed form (1/y)(1 - (1+y/2)^-20); BOND must match the independent exact repricing return closely.
- C16. WTI: log(MCOILWTICO_t) - log(MCOILWTICO_{t-1}) (monthly average prices; the same series as the team macro file).
- C17. dVIX_t: mean of daily VIXCLS over month t minus the same for month t-1, in VIX points.
- C18. dlog EMV_t: log(EMVOVERALLEMV_t) - log(EMVOVERALLEMV_{t-1}), same month (an ex-post attribution regressor, not a trading input).
- C19. I_{t-1} = 1 if h^T_{t-1} != 0.

**Regression and inference**
- C20. D_t = alpha + sum_j beta_j F_{j,t} + sum_c gamma_c I_{t-1} F_{c,t} + e_t, with F = {Mkt-RF, SMB, HML, RMW, CMA, UMD, BOND, WTI, dVIX, dlogEMV} (10 terms) and c in {Mkt-RF, HML, BOND, dVIX} (4 terms). k = 15 estimated parameters including the intercept. No I_{t-1} main effect (the spec has none; alpha is the intercept). OLS on all window months with complete data.
- C21. Newey-West (Bartlett) covariance with 6 lags, no small-sample scaling, the team's `newey_west_regression` formula. p-values: two-sided from Student t with n - 15 degrees of freedom (one-sided upper p also reported). 12 lags reported as a check only. Alpha reported monthly and annualized (x12).
- C22. Decomposition: mean(D) = alpha + sum_j beta_j mean(F_j) + sum_c gamma_c mean(I F_c); the OLS residual has mean zero, so the identity is exact. Reported annualized, grouped as FF5+UMD, BOND (unconditional and conditional), WTI, volatility block (dVIX, dlogEMV, I x dVIX), conditional Mkt-RF and HML, and alpha.

**Pass bar components**
- C23. (i) alpha > 0 and NW(6) t >= 2.00. The two-sided t(n-15) p is reported beside it (at about 150 to 190 degrees of freedom, t = 2 implies p of about 0.047).
- C24. (ii) Calendar shuffle. Blocks = maximal runs of consecutive decision months with the timed position on, within decision months W0-1 to 2009-11 (truncated at the edges). In each of 5,000 draws (numpy `default_rng(230)`), the same blocks, in random order, are placed at random dates in that decision range, uniformly over all arrangements that do not overlap and keep at least one flat month between blocks (so the number of blocks, their lengths, and the number of entries and exits are preserved). Positions outside the decision range stay as in the real series. Each draw rebuilds the position (vol-target magnitude at the new dates), net R^T, pi, D and I_{t-1}, and reruns the same 15-parameter regression. p = (1 + #{alpha* >= alpha_hat}) / (5,000 + 1), one-sided upper; pass if p <= 0.05. A two-sided version is reported as context.
- C25. (iii) Episodes = maximal runs of consecutive decision months with the timed position on (overlapping or touching holds merge automatically), counted if the run includes at least one decision month in W0-1 to 2009-11. Pass if at least 8.
- C26. (iv) For each Brown industry in turn, the Brown leg is the equal-weighted mean of the other four; the hedge, residual, vol target, timed and always-on strategies, pi, D and the regression are rebuilt on the same window with the same hold windows. Pass if all five alphas have the sign of alpha_hat and alpha_hat > 0. The five t-stats are reported but not required.
- C27. Verdict: PASS only if (i) to (iv) all hold; anything else is FAIL and confirms "Do not implement".

**Secondary context (not part of the verdict)**
- C28. The team's original signal: EMVENRGYENVREG level, log1p, rolling z (60 months, min 36, zeros kept as values), expanding past-only p80 (min 60), crossings and 6-month holds via `cross_and_holds`, lagged one month (the decision flag at t+1 uses data month t). Same engine, same window W0 to 2009-12, its own pi, I, blocks, and the same four components, with the shuffle seeded at 230.
- C29. Crossing list for the primary rule: data month, decision month, s_t, z_t, threshold, EMVOVERALLEMV and monthly mean VIX for the data month, and their percentile ranks within 1993-2009.

**Procedure**
- C30. Code is first run on the seen validation window (2010-01 to 2022-07) and checked against the team pipeline, only to catch bugs. That dry run cannot change any choice above.
- C31. The primary 1993-2009 run is executed once. Deterministic seeds make later re-executions reproduce it exactly. Any code bug found after the primary run is fixed only if it is a clear coding error against this document; the fix and the before and after numbers are listed in FINDINGS.md under "Deviations". No choice in this file changes after the primary run.
- C32. Ledger: every statistic above goes to `outputs/tables/M8_tests_ledger.csv`; the four pass-bar statistics of the frozen rule are "primary"; the NW(12) check, the secondary signal and all context rows are "exploratory".
