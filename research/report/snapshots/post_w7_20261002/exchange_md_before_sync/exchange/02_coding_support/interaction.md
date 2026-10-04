# Coding support: A second implementation of the frozen 1993–2009 test

Tool: ChatGPT
Date: 2026-09-26
Purpose: coding support

## Prompt

### Message 1 (initial prompt: code for the pre-registered 1993–2009 backtest)

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

### Message 2 (follow-up, sent after running and fact-checking Reply 1)

I ran your script on the real data and through your checks. It ran the first time, with only file paths and `fac` supplied, and reaches the same verdict as my own implementation (FAIL, 1 of 4). The numbers differ, and one of your stop rules fires.

1. `make_synthetic_inputs`. GS10 is a random walk clipped at 0.5 that sits on the floor (76% of 1995-2009 months for seed 0, every month for seed 16). BOND is then constant, I x BOND acts as an I main effect, and your positive control fails check (b)10: 4% of the planted 3% effect reaches alpha (t 0.98), while I x BOND has t -10.8. Seed 16 crashes the null-seed loop (rank-deficient design).

2. `attention_signal`. Requiring 60 full calendar months before the first z is a silent reading you hard-coded. I treat pre-1985 months as unavailable, not zero, so the 48-nonzero minimum is the burn-in. Your reading moves the first threshold from 1994-01 to 1994-12, adds a 2002-12 crossing and starts the window at 1995-02, not 1994-03: pi 0.809 vs. 0.729, shuffle p 0.536 vs. 0.478.

3. `leg_pipeline`. You hedge with the Mkt-RF, SMB and HML in `fac`, the FF5 file. The team hedge uses its FF3 file, which my prompt never said (my gap). SMB differs by up to 3.5 pp a month, b_t moves by up to 0.09, and your check (b)2 stops at 2.3e-3 a month (6e-17 with FF3).

4. `pass_fail_table`. (iv) passes a negative alpha whose five drop-one alphas are also negative.

With readings 2 and 3 switched to mine, your code matches my implementation to 1e-13, all 5,000 shuffle draws included.

Two smaller gaps. `check_no_lookahead` compares end-of-T states only, so it missed both return-side bugs I injected (month-t return hedged with b_t; a position earning its own month). Seen mode ends at 2022-12; its five holdout months flip the seen alpha from -0.16%/yr (t -0.24) to +0.26%/yr (t 0.37).

Please send corrected versions of these functions only, each with a unit test:
- `make_synthetic_inputs`: BOND varies in every window for seeds 0-20, and the positive control puts at least 80% of the planted shift in alpha with t > 2.
- `attention_signal`: a `z_burn_in` parameter with both readings; on a zero-free series from 1985-01, the first z falls in month 48 under mine and month 60 under yours.
- `leg_pipeline`: a separate `hedge_fac` input; changing its SMB moves b_t but not the attribution regressors.
- `pass_fail_table`: a negative alpha fails (iv).
- `check_no_lookahead`: a return-side comparison that flags both injected bugs.
- `__main__`: seen mode ends at 2022-07, with `cut_to` on its look-ahead call.

These fixes are for reproducibility; the frozen rule stays.

## Output summary

### Reply 1: one backtest script, 25 assumptions and 13 checks

ChatGPT returned one self-contained script, `brown_attention_prereg.py` (985 lines; pandas, numpy and statsmodels only), and stated up front: "I have not executed this code. Treat the checks in (b) as mandatory before the single real run." The full reply is in `chatgpt_response.md`.

- **Structure.** A frozen `Config` dataclass holds every number (windows, costs, signal thresholds, pass bars, seed 230). Each step is one function with a docstring that states its timing: loaders with guards against percent units, calendar gaps and French's −99.99 code; the Brown leg; the rolling 60-month hedge; the out-of-sample residual and vol-target size; the signal, crossings and hold; the trade engine; BOND from exact cash-flow duration and convexity; the attribution regressors; the test window; D and π; the 15-column design matrix and the NW(6)/NW(12) regression; the mean decomposition; episodes; a stars-and-bars calendar shuffle; leave-one-out; and the pass/fail table. `run_backtest` prints the five requested outputs. The code raises on missing regressors, rank deficiency, a df mismatch, or disagreement between the lstsq and statsmodels alphas.
- **Pre-run tooling.** A synthetic generator in the raw file layouts, a truncation look-ahead test (`check_no_lookahead`) and a planted-effect positive control (`plant_timing_effect`). `__main__` has three modes: "synthetic", "seen" (2010-01 to 2022-12) and "final" (1993-01 to 2009-12, once, with no edits after "seen").
- **The three silent points I named, as parameters** (indentation trimmed here and in every excerpt below):

```python
# readings of the points the spec leaves open -- see notes (a)1-(a)3
bridge_missing: bool = True       # extreme, zero, extreme = one run (no new crossing)
bridge_limit: int = 6             # ... unless more than 6 consecutive missing months
end_policy: str = "truncate"      # "truncate" or "liquidate" a hold still open at test_end
shuffle_draws: int = 5000
shuffle_min_gap: int = 1          # shuffled episodes never touch, so K is preserved
shuffle_recompute_pi_I: bool = True
```

- **Timing core.** The hold is a rolling maximum of crossings (a new crossing extends, positions never stack), shifted by the publication lag. Each month's return uses last month's position, last month's betas and last month's trade cost.

```python
hold_sig = c.rolling(cfg.hold_months, min_periods=1).max() > 0
return hold_sig.shift(cfg.pub_lag, fill_value=False).astype(bool).rename("hold")
```

```python
out["w_prev"] = out["w"].shift(1)
out["hedged"] = rb - (b.shift(1) * f).sum(axis=1, min_count=len(hf))
out["gross"] = out["w_prev"] * out["hedged"]
out["cost"] = out["trade_cost"].shift(1)
out["net"] = out["gross"] - out["cost"]
```

- **(a) 25 numbered assumptions.** The three silent points came with reasons. A zero month between two extreme months is bridged, because a zero "should neither end an episode nor start one", for at most 6 months (the hold length and the most zeros a valid window can contain). The shuffle places the K actual episodes at random with at least one flat month between blocks and recomputes π and I_{t−1} in every draw, because "the null statistic has to be computed exactly like the actual one"; p = (1 + #{null ≥ actual}) / (1 + 5000), one-sided. A hold still open at 2009-12 is truncated, because its return and trade cost fall in 2010-01. The other 22 cover units, calendars, costs and inference. Four mattered later. Assumption 11: "The z window must be a full 60 calendar months of EMV history, so the first z is 1989-12", so the 48-nonzero clause never binds. Assumption 16: the window should start "roughly 1995-02 rather than 1993-01". Assumption 19: the regression has "no I_{t−1} main effect", so alpha is the average timing alpha. Assumption 24: "Keeps its sign" means "the same sign as the full-sample alpha, for all five industries."
- **(b) 13 checks, each with a stop rule.** Units and dates; reproduce the team trade on 2010–2022 to 1e-8; the look-ahead test on synthetic data and the seen window, plus a `pub_lag=0` probe; signal and hold unit tests; a cost test; BOND (modified duration about 7.79 at 5%, correlation with −Δy above 0.99); regression mechanics (k = 15, n − k = df_resid, identity gap below 1e-12); shuffle validity, including 20 null seeds (stop if more than 4 have p ≤ 0.05); the positive control at delta = 0.03 (stop "if the planted effect is missed or has the wrong sign"); the seen-window run; coverage without peeking; and a SHA-256 freeze before the single run.

I later traced each of the six problems in the evaluation to these lines.

The burn-in, in `attention_signal`:

```python
n_miss = missing.astype(float).rolling(W, min_periods=W).sum()
n_nz = W - n_miss
```

The hedge factors and the leg's RF, in `leg_pipeline`, taken from `fac` (the FF5 file):

```python
f = fac.reindex(index)[list(cfg.hedge_factors)]
rb = brown_leg(ff49.reindex(index), fac["RF"].reindex(index), industries)
```

The synthetic 10-year yield, in `make_synthetic_inputs`:

```python
gs10 = np.clip(5.0 + np.cumsum(rng.normal(0.0, 0.2, len(g_idx))), 0.5, 15.0)
```

Criterion (iv), in `leave_one_out` and `pass_fail_table`, which compares signs only:

```python
"same_sign": bool(np.sign(a) == np.sign(alpha_full))})
```

```python
f"{same}/{nl}", bool(same == nl)],
```

The look-ahead comparison, in `check_no_lookahead`, which checks only the states set at the end of T:

```python
a, b = part.loc[T], full.loc[T]
```

Seen mode, in `__main__`:

```python
cfg = replace(Config(), test_start="2010-01", test_end="2022-12")
_show("LOOK-AHEAD TEST (seen data only)", check_no_lookahead(inputs, cfg, cut_from="2010-01"))
```

### Reply 2: six corrected functions, each with a unit test

ChatGPT returned a 704-line block that replaces the six definitions, with one unit test each, plus shared raw-input helpers (`read_raw`, `write_raw_csvs`, `truncate_raw`) and one adapter, `run_panel`, "the only place the tests call the rest of the script". It said again that it could not run code: "Please run the tests before anything else, and if one fails, send me the assertion message." The full reply is in `chatgpt_followup_response.md`.

- **Four driver changes.** `run_backtest` gains `hedge_fac` and `z_burn_in`, and `hedge_fac` goes to every `leg_pipeline` call, including the five leave-one-out rebuilds. The overlay return and costs use the leg's FF3 `f_*` and `b_*`, while the attribution keeps `fac`. `pass_fail_table` takes plain numbers. `run_panel` assumes a stated driver signature and output keys.
- **`make_synthetic_inputs`.** log(GS10) becomes a stationary AR(1); a separate synthetic FF3 `hedge_fac` is generated, whose SMB differs from `fac`'s; and the plant is applied inside the generator on given months, so the hold schedule is identical with and without it. A new `positive_control` reports the share of the planted mean(D) shift that reaches alpha. The test requires, for seeds 0 to 20, that GS10 stays above 0.5 and moves every month and in every 24-month window, and that the design is full rank with only the constant flat and an R² of I on the regressors below 0.5; for seeds 0 to 2, it requires a share of at least 0.8 and t > 2.

```python
y10 = np.exp(ar1(n, np.log(5.0), 0.985, 0.045, np.log(3.5)))            # percent, roughly 2-11
```

- **`attention_signal`.** A `z_burn_in` parameter: "nonzero" (the default, my reading) or "calendar" (its earlier reading). Months before the first observation are unavailable, not zero. The test checks a first z in month 48 vs. month 60 on a zero-free series from 1985-01, a hand-computed z, the past-only threshold, zero handling, and the switch-off at 7 zeros in 60.

```python
n_nonzero = good.astype(int).rolling(window, min_periods=1).sum()
n_zero = zero.astype(int).rolling(window, min_periods=1).sum()
max_zero = int(np.floor(max_zero_frac * window + 1e-9))
on = good & (n_nonzero >= min_nonzero) & (n_zero <= max_zero)
if z_burn_in == "calendar":
    on &= pd.Series(np.arange(len(idx)) >= window - 1, index=idx)
```

- **`leg_pipeline`.** Takes `hedge_fac` (the team FF3 file) for R^B's RF, the hedge regressors and the overlay factor returns, refuses a frame that carries RMW or CMA, and now returns one DataFrame. The test checks the betas against hand OLS, the residual's use of t−1 coefficients, that month T+1 cannot reach row T, that a perturbed hedge SMB moves b_SMB but leaves the attribution design unchanged, and that the FF5 frame is refused.

```python
if {"RMW", "CMA"} & set(hedge_fac.columns):
    raise ValueError("hedge_fac has RMW/CMA: that is the FF5 file; the team hedge uses its FF3 file")
```

- **`pass_fail_table`.** (iv) now requires the full alpha and all five drop-one alphas to be positive, and a missing drop-one alpha fails:

```python
ok4 = len(loo) == n_brown and bool(all_a.notna().all()) and bool((all_a > 0).all())
```

- **`check_no_lookahead`.** Up to eight audited months each from entries and exits, held months and flat months, with five tests: `post_window`, `truncate` and three perturbations. A +delta shock to the Brown industries or to the hedge factors in month T must leave everything before T unchanged and move R^T_T by exactly what the position held entering T implies; a spike in the EMV value for T must leave states through T and returns through T+1 unchanged. It compares positions and returns, not D, because π is an ex post constant. A toy pipeline with three injected bugs (hedge with b_t, own-month earning, signal lag) tests the auditor.

```python
p = run_fn(_bump(raw, "ff49", T, list(brown), lambda v: v + delta))
exp = {r: base.at[Tm1, c] * delta for r, c in pos_of.items()}
add("rb_perturb", T, _maxdiff(before, p, all_cols), _ret_err(base, p, T, exp))
```

- **`__main__`.** `SEEN_WINDOW` ends 2022-07-31, and seen mode cuts every input there before the audit and the run; synthetic mode runs the six unit tests first.

```python
cut_to = end if MODE == "seen" else None
if cut_to is not None:
    raw = truncate_raw(raw, cut_to)            # nothing after 2022-07 reaches the audit or the run
```

- **Checks to run first, and six stated choices.** "calendar" should reproduce the old signal exactly; `leg_pipeline` on the FF5 columns should reproduce the old leg; and ("nonzero", FF3) "should again match your implementation to 1e-13", compared row by row because "(iv) used to pass when it shouldn't have". The choices: zeros counted in the trailing 60 calendar months, with pre-1985 months not counted; off months kept out of the percentile history; RF taken from `hedge_fac`, which "the driver can assert" equals `fac`'s; (iv) read as "stays positive"; a deliberately large plant of 3 percentage points, "because the check tests the pipeline, not statistical power"; and an audit on positions and returns rather than D. It closed with "The verdict is FAIL in your run and in mine, under either burn-in reading" and said the seen-window numbers "should be reported with the 2022-07 end: alpha of −0.16%/yr, t −0.24."

## Evaluation

ChatGPT wrote a correct backtest inside a flawed test harness. I never used it as the run of record: I ran it on the real data as a second implementation and compared every component with my own (M8), which reproduces the team pipeline bitwise.

**The core mathematics matched mine.** The 985-line script ran the first time, with only file paths and `fac` supplied, and reached the same verdict (FAIL, 1 of 4; alpha −0.19%/yr, NW(6) t −0.25, vs. −0.18%/yr, t −0.27). Two readings explain every numeric gap. With both switched to mine, it reproduces all 15 coefficients, the decomposition, the drop-one alphas and all 5,000 shuffle draws, to 3.3e-13 at worst. The timing conventions (lagged hedge, publication lag, extend-not-stack holds, costs paid in t+1) needed no correction.

**Three of the six problems came from my prompt.** It described only the FF5 `fac`, so the code hedged with FF5 SMB (up to 3.5 pp a month off the team FF3 SMB); b_t moved by up to 0.09, and ChatGPT's own check (b)2 stopped at 2.3e-3 a month. "Keeps its sign" let (iv) pass a negative alpha, and "the seen 2010-2022 window" let seen mode run to 2022-12, where five holdout months flip the seen alpha from −0.16%/yr (t −0.24) to +0.26%/yr (t 0.37). The other three are ChatGPT's: a broken instruction, a bug and a blind spot. It hard-coded a 60-calendar-month burn-in and disclosed it (assumption 11), although the prompt asked for every silent reading to be a parameter; the window start moved from 1994-03 to 1995-02, π from 0.729 to 0.809 and the shuffle p from 0.478 to 0.536. Its synthetic GS10, a random walk clipped at 0.5, sat on the floor (76% of 1995–2009 months for seed 0), so BOND went constant and I × BOND stood in for an I main effect: the positive control failed its own stop rule (4% of the planted effect in alpha, t 0.98), and seed 16 crashed the null-seed check. Its look-ahead test compared end-of-month states only and missed the two return-side bugs among the six I injected.

**The follow-up fixed all six and broke one interface.** All six unit tests passed the first time without edits. The defaults reproduce my implementation to 3.3e-13 and the seen dry run (−0.12%/yr, t −0.19), the positive control puts 97–104% of the planted shift in alpha (t 3.5 to 6.1), and the new audit flags 7 of 8 injected timing bugs, including both earlier misses. But the new `attention_signal` changed its output layout while the reply said everything else was unchanged. A literal drop-in crashes, and the obvious one-line patch runs without error on a window 14 months too long (from 1993-01, n = 204, alpha −0.13%/yr). It also told me to report a stale seen-window alpha (−0.16%/yr, from its first version). It cannot run code, and the numbers it quotes about its own code are not computed.

**Trust its formulas and audit its interfaces.** Where the spec was exact, the code was exact. The errors sat outside the formulas: in readings the spec left open, in test scaffolding, and at the seam between old and new functions. None changed the verdict or the frozen rule. The independent reference made the exchange useful: each discrepancy became a switch tied to specific lines, and mutation tests measured what its checks could see. Its own acceptance test for the fix ("should again match your implementation to 1e-13") presumes that reference exists. The repaired harness also audited our own inference: on 100 null seeds the calendar shuffle is correctly sized (6 rejections at 5%), but the pre-registered NW(6) t over-rejects (13), a bias that cannot rescue a negative alpha. Run against a reference and never trusted blind, ChatGPT is a cheap second implementation for backtest code, not a verifier of it.
