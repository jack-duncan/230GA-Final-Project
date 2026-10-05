Write Python code for a pre-registered backtest I will run exactly once. You do not have the data, so report no results.

CONTEXT. This is my MFE 230GA final project at Berkeley. Our team's strategy shorts a factor-hedged "Brown" industry leg after attention spikes. It failed its 2022-2026 holdout, and we recommend "Do not implement". I froze one rule for 1993-2009, the one tradable window nobody has backtested. I will debug your code on synthetic data and the seen 2010-2022 window first, so the test window is a parameter and nothing is tuned.

INPUTS. Returns are monthly decimals.
1. `ff49_industry_monthly.csv`: a `date` column (month-end, e.g. 1926-07-31) and 49 Fama-French industry columns of value-weighted returns, NaN before an industry exists. Brown = Util, Ships, Aero, Steel, BldMt. The Brown leg R^B_t is their equal-weighted mean minus RF.
2. `fac`: a DataFrame parsed from Ken French's FF5 and momentum files, month-end DatetimeIndex from 1963-07, columns Mkt-RF, SMB, HML, RMW, CMA, RF, UMD.
3. FRED CSVs with columns `observation_date` (first of month; map to month-end) and the series id: EMVENRGYENVREG and EMVOVERALLEMV (monthly from 1985-01; the first has exact zeros, the second none), GS10 (monthly average 10-year yield, percent), MCOILWTICO (monthly average WTI price, from 1986-01), VIXCLS (daily closes from 1990-01-02, blank on holidays).

THE TEAM TRADE (validated, unchanged).
- Hedge: OLS of R^B on a constant and f = (Mkt-RF, SMB, HML) over months t-59 to t gives (a_t, b_t); residual e_t = R^B_t - a_{t-1} - b_{t-1}'f_t.
- Size: m_t = min(1, 0.05 / (sqrt(12) * sd_t)), sd_t = 36-month rolling std (ddof=1) of e through t.
- Position w_t = -m_t in a hold month, else 0, set at the end of month t; it earns w_t*R^B_{t+1} - w_t*b_t'f_{t+1}.
- Costs per unit of turnover: 10 bp on |Δw|, 5 bp on the Mkt-RF overlay change, 25 bp on SMB and HML overlay changes; a trade at the end of t pays in t+1.
- A crossing is an extreme month whose previous month was not extreme. The hold covers the crossing month and the next five. With the publication lag, the hold state at the end of t uses the extreme flag of t-1.
- Always-on benchmark R^AO: every month is a hold month.

THE FROZEN RULE.
1. Signal: s_t = EMVENRGYENVREG_t / EMVOVERALLEMV_t, observed one month late (the value for month t is usable at the end of month t+1).
2. Zeros: a zero month is missing, not low attention. It cannot trigger a position, and it is dropped from both the z-score window and the percentile history. The z-score needs at least 48 nonzero months in the trailing 60; if more than 10% of the trailing 60 months are zero, the signal is off.
3. Extreme month: z_t = 60-month rolling z-score of log(s_t) over nonzero months; extreme when z_t exceeds its expanding, past-only 80th percentile (team convention: at least 60 prior z observations).
4. Trade: the 6-month rule above. A new crossing during a hold extends the hold; positions never stack.
5. Sample: 1993-01 to 2009-12 (or from the first month the rule can fire, if later), run once.
6. Pass bar, all four required: (i) the timing alpha below is positive with t >= 2 and p from t(n-k); (ii) calendar-shuffle p <= 0.05 (move the same hold windows to random dates, 5,000 times, recompute alpha); (iii) at least 8 independent episodes (merge holds that touch or overlap); (iv) alpha keeps its sign when each Brown industry is dropped in turn (rebuild leg, hedge, sizing, R^AO and pi each time).

ATTRIBUTION. D_t = R^T_t - pi*R^AO_t, net of costs, with R^T the timed strategy and pi = mean |timed position| / mean |always-on position| over the test window. Regress D_t on FF5 + UMD, BOND, the WTI log return, dVIX_t (change in the monthly mean of daily VIX), dlog EMVOVERALLEMV_t, and I_{t-1} x {Mkt-RF, HML, BOND, dVIX}, where I_{t-1} = 1 if the strategy held a position entering month t. Alpha is the intercept. Newey-West with 6 lags (12 as a check); p from t(n-k), k = number of estimated parameters. Report mean(D) = alpha + sum beta*mean(F) + sum gamma*mean(I*F).

BOND is the monthly excess return of a constant-maturity 10-year Treasury from GS10 (percent to decimal): r_t = y_{t-1}/12 - D_{t-1}*(y_t - y_{t-1}) + 0.5*C_{t-1}*(y_t - y_{t-1})^2, with D and C the modified duration and convexity of a 10-year semiannual par bond at yield y_{t-1}, minus RF.

CONSTRAINTS.
- No look-ahead: every input used at the end of month t is known then (the signal a month later). Attribution regressors are contemporaneous by design; do not lag them.
- pandas, numpy and statsmodels only. `sm.OLS(...).fit(cov_type="HAC", cov_kwds={"maxlags": 6}, use_t=True)` matches our team's Newey-West t and gives p from t(n-k). Count k from the design matrix.
- One function per step, each with a docstring giving inputs, outputs and timing convention. Fixed seed, no parameter search, no plots.

Where the spec is silent, pick one reading, make it a parameter and say why. Three I see: whether a zero month between two extreme months makes the next one a new crossing; how the shuffle places windows and whether pi and I are recomputed per draw; what happens to a hold still open in 2009-12.

OUTPUTS, as DataFrames, also printed.
1. Pass/fail table: one row per component (i) to (iv), with statistic, bar, value, pass/fail; then the overall verdict.
2. Attribution: coefficient, NW(6) t, NW(12) t and p per regressor; n, k, R-squared, pi, window dates.
3. Decomposition: mean(D), alpha, every beta*mean(F) and gamma*mean(I*F) term, and the identity gap (zero to machine precision).
4. Diagnostics: first month the rule can fire, zero-month counts, crossing dates, episode list, leave-one-out alphas and t.
5. Shuffle: actual alpha, null quantiles, p.

AFTER THE CODE.
(a) Number every assumption you made beyond this spec.
(b) The checks you would run before my single real run, each with the result that would make you stop, including a look-ahead test.
