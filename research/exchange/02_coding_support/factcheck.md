# Exchange 2 fact-check: Claude's code for the frozen 1993-2009 test

Independent code review and test run, 2026-09-26. Round 1 reviews Claude's first answer. Round 2 (at the end) reviews Claude's corrected functions.

**File names changed in round 2.** Round 1's BUG-1-only fix, first called `chatgpt_code_v2.py`, is now `checks/chatgpt_code_v1fix.py` (diff `v1_to_v1fix.diff`; same sha256, c10515a6...e44c). `chatgpt_code_v2.py` now holds the round-2 code. In sections 1 to 9, "v1fix" means that BUG-1-only fix. Round-1 output files keep their names (`null_seeds_v2_*.csv`). Apart from these renames, sections 1 to 9 are unchanged from round 1.

- Inputs: `prompt.md` (sha256 f9219080...7117247) and `claude_response.md` (sha256 0ac8e58f...0dfd0ce).
- Claude's code, extracted verbatim: `checks/chatgpt_code_v1.py`. It has 985 lines (sha256 6cdf0006...781968d), and `diff` against lines 6-990 of the response is empty.
- Line numbers below refer to `chatgpt_code_v1.py`. Add 5 to get the line in the response.

## Summary

**Verdict: the code is correct and reaches the same verdict as the reference.** Its numbers differ from the reference only through two readings that the prompt left open. "Do not implement" stands under either reading.

1. **Same verdict as the reference.** I ran the code on the real data with glue only; no line of Claude's file was edited.
   - It returns FAIL, with 1 of 4 components met (episodes).
   - Timing alpha -0.19%/yr, NW(6) t -0.25, one-sided p 0.60. Shuffle p 0.536. 10 episodes. Drop-one: 4 of 5 alphas keep the sign.
   - The reference gives -0.18%/yr, t -0.27, one-sided p 0.605, shuffle p 0.478, 10 episodes, and 3 of 5.
2. **Two readings explain every numeric gap. Neither is a coding error.**
   - **(A) z burn-in.** Claude requires 60 full calendar months of EMV history before the first z (lines 274-275). Its first z is therefore 1989-12 and its first threshold 1994-12. The reference (C5) lets the 48-nonzero minimum act as the burn-in, which gives a first z in 1989-01 and a first threshold in 1994-01. Under A:
     - the window starts at 1995-02 instead of 1994-03 (179 months, not 190);
     - the threshold moves by up to 0.076;
     - one extra crossing (data month 2002-12) opens a new hold;
     - pi rises from 0.729 to 0.809.
   - **(B) Hedge factor file.** Claude hedges with the SMB and HML of the `fac` it was given (the Ken French FF5 file) and subtracts that file's RF (lines 377-378). The team rule uses the team FF3 file. The prompt described only `fac`, so this is a gap in the prompt. SMB differs by up to 3.5 pp a month between the two files. As a result, b_t moves by up to 0.09 and m_t by up to 0.012.
   - **With both switched to the reference reading (variant AB), Claude's code reproduces every reference number to 1e-13.** That covers:
     - z, the threshold and every crossing over 1985-2026;
     - the holds, b_t, m_t, and net R^T and R^AO;
     - pi and D;
     - all 15 coefficients with their NW(6) and NW(12) t-statistics and p-values;
     - the decomposition, the 10 episodes and the five drop-one alphas;
     - all 5,000 shuffle draws, draw by draw (largest gap 8e-15; same seed and the same placement algorithm).
   - On the seen 2010-01 to 2022-07 window, AB reproduces the reference dry run exactly.
3. **One genuine bug, in the test harness, not the backtest (BUG-1).**
   - The synthetic GS10 generator (line 881) is a clipped random walk. It sits on its 0.5% floor in 76% of 1995-2009 months for seed 0, and in all 192 months of 1994-2009 for seed 16.
   - BOND is then constant, so I x BOND acts as an I main effect.
   - As a result, Claude's own positive control fails its own stop rule: only 4% of the planted effect reaches alpha (t 0.98), and I x BOND has t = -10.8.
   - Seed 16 of its null-seed check crashes on a rank-deficient design.
   - One edit fixes it (v1fix). The positive control then passes: 105% of the planted effect reaches alpha, t 4.15, shuffle p 0.005.
4. **Claude's own battery would have caught (B).** Its check (b)2 (reproduce the team trade to 1e-8) stops on the as-delivered code at a gap of 2.3e-3 a month. With the team FF3 file, the gap is 6e-17 and the check passes.
5. **Limits in the test design (not bugs):**
   - The look-ahead test compares states only. It misses 2 of 6 injected timing bugs, both on the return side.
   - Component (iv) does not require a positive alpha.
   - The burn-in reading is not a parameter, although the prompt asked for every silent reading to be one.
   - The "seen" mode includes 5 holdout months, and they flip the sign of the seen-window alpha.

## 1. Run log

All runs use `uv run --project research python ...` with bytecode writing off. The environment is Python 3.14.2, pandas 3.0.6, numpy 2.5.3 and statsmodels 0.15.0. No run produced a warning. Logs are in `checks/logs/` and outputs in `checks/out/`.

| # | Run | Code | Window / data | Result | Time |
|---|---|---|---|---|---|
| 1 | Synthetic mode exactly as delivered (`python chatgpt_code_v1.py`) | v1 | synthetic, seed 0, 500 draws | Look-ahead: 59 of 59 cuts ok. Unplanted: FAIL 0/4, alpha t 0.41. Planted 3%: FAIL 1/4, alpha t 0.98, shuffle p 0.293. **The positive control misses the planted effect.** | 13 s |
| 2 | "final" mode, real data | v1 + glue | 1995-02 to 2009-12 (start chosen by the code) | FAIL 1/4. Alpha -0.19%/yr, t -0.25. Shuffle p 0.536. 10 episodes. (iv) 4/5 | 57 s |
| 3 | "seen" mode as written | v1 + glue | 2010-01 to 2022-12 | FAIL 0/4. Alpha +0.26%/yr, t 0.37. Shuffle p 0.235. 6 episodes. (iv) 4/5 | 43 s |
| 4 | Seen, on the reference dry-run window | v1 + glue | 2010-01 to 2022-07 | FAIL 0/4. Alpha -0.16%/yr, t -0.24. Shuffle p 0.525. 6 episodes. (iv) 3/5 | 57 s |
| 5 | Look-ahead test, "seen" mode as written | v1 + glue | cuts from 2010-01 to 2024-08 | 66 of 66 cuts ok | 5 s |
| 6 | Harmonization A | v1 + A | 1994-03 to 2009-12 | FAIL 1/4. Alpha -0.18%/yr, t -0.263. Shuffle p 0.485 | 102 s |
| 7 | Harmonization B | v1 + B | 1995-02 to 2009-12 | FAIL 1/4. Alpha -0.19%/yr, t -0.249. Shuffle p 0.530 | 102 s |
| 8 | Harmonization AB | v1 + A + B | 1994-03 to 2009-12 | FAIL 1/4. **Equals the published reference to 1e-13** | 102 s |
| 9 | Harmonization AB, seen | v1 + A + B | 2010-01 to 2022-07 | Equals the reference dry run: alpha -0.1207%/yr, t -0.1878, shuffle p 0.5101, 6 episodes | 101 s |
| 10 | Component comparison (`compare.py`) | | | The reference rebuilt in memory from run.py's functions matches the published tables to 4e-16 before any comparison | 20 s |
| 11 | Claude's pre-run checks (b)1-(b)10 (`prerun_checks.py`) | v1, v1fix | real and synthetic | See section 3 | 90 s |
| 12 | Claude's null-seed check, seeds 1-20, 500 draws | v1 | synthetic | Seed 16 crashes (rank-deficient design). 0 of the other 19 have p <= 0.05 | 4 x 70 s |
| 13 | Same check | v1fix | synthetic | 0 of 20 have p <= 0.05 | 4 x 70 s |
| 14 | Mutation test of the look-ahead check (`mutation_lookahead.py`) | v1 + mutants | synthetic | 4 of 6 injected timing bugs detected | 60 s |

## 2. Edits

### 2a. Glue the prompt left unspecified (no edit to chatgpt_code_v1.py)

| ID | What was left open | What I did | File |
|---|---|---|---|
| G1 | `fac` is described but not supplied. `__main__` reads `fac.pkl` (line 974), which does not exist. | Built `fac` as `common.load_ff5_mom()[["Mkt-RF","SMB","HML","RMW","CMA","RF","UMD"]]`: Ken French FF5 2x3 plus UMD, decimals, month-end index, 1963-07 to 2026-08. This is exactly what the prompt describes. | `glue.py` |
| G2 | `__main__` uses bare file names (`EMVENRGYENVREG.csv`, `ff49_industry_monthly.csv`, ...). | Absolute paths to the team `data/ff49_industry_monthly.csv` and `research/data/raw/fred_*.csv`. Their layouts match the prompt: `date` column; `observation_date` plus the series id. | `glue.py` |
| G3 | The mode is a constant edited inside the file (line 965). | A driver calls `run_backtest(inputs, cfg)` directly with Claude's own `Config` for each mode. | `run_chatgpt_real.py` |
| G4 | The prompt's "seen 2010-2022 window" has no end month. | Ran Claude's own 2010-01 to 2022-12 as written. Also ran 2010-01 to 2022-07, the team validation end and the reference dry-run window. | `run_chatgpt_real.py` |

No other glue was needed. The code ran the first time, with no errors and no warnings.

### 2b. Genuine bugs, fixed in chatgpt_code_v1fix.py

| ID | Line | Bug | Fix | Effect |
|---|---|---|---|---|
| BUG-1 | 881 | The synthetic GS10 is `np.clip(5 + cumsum(N(0, 0.2)), 0.5, 15)`: a driftless random walk that drifts onto the 0.5 floor and stays there. BOND is then y/12 - RF, a constant (seed 0: 76% of window months; seed 16: every month). | Same shocks, same RNG consumption, filtered as a mean-reverting AR(1) around 5% (coefficient 0.97). The clip never binds, and every other synthetic series is unchanged. | Positive control (3% planted): v1 gives alpha t 0.98, shuffle p 0.259, 4% of the D shift in alpha. v1fix gives t 4.15, shuffle p 0.005, 105%. Seed 16 of the null check no longer crashes. |

v1fix differs from v1 only at that line (`checks/v1_to_v1fix.diff`). v1fix is used only for synthetic checks; every real-data run uses v1. The bug has no effect on real-data results because real BOND varies (its correlation with -dy is 0.996 over 1993-2009).

### 2c. Diagnostic harmonization switches (not fixes)

Each switch replaces one behaviour with the reference's reading, to attribute the discrepancies (`checks/align.py`).

| Switch | Reference reading adopted | Change |
|---|---|---|
| A | C5: months before 1985-01 are unavailable, not zero, so the 48-nonzero minimum is the burn-in. | In a copy of `attention_signal`, only lines 274-275 change: the trailing-60 counts use `min_periods=1`, and `n_nz` counts nonzero months instead of `W - n_miss`. |
| B | C10: the hedge factors and the leg's RF come from the team FF3 file. | A wrapper passes the team FF3 frame to `leg_pipeline` in place of `fac`. The attribution regressors still come from `fac`. |

## 3. Claude's own checks (its section (b)), run as specified

| Check | Claude's stop rule | Result | Status |
|---|---|---|---|
| Look-ahead, synthetic (run 1) | any `ok == False` | 59 of 59 cuts ok | pass |
| Look-ahead, seen data (run 5) | same | 66 of 66 cuts ok. The label says "seen data only", but no `cut_to` is set, so the cuts run to 2024-08 | pass |
| (b)1 units and dates | series shifted, percent units, Brown industry missing | EMV starts 1985-01-31 and monthly VIX 1990-01-31. No unit error. 0 Brown NaNs in 1985-2009 | pass |
| (b)2 team trade, as delivered | any month off by more than 1e-8 | R^AO against the team Always-short Brown: 2.3e-3. Timed book fed the team's 6-month hold against the team Original 6m: 2.3e-3 | **STOP** (cause B) |
| (b)2 team trade, team FF3 file | same | 5.6e-17 on both | pass |
| (b)3 lag probe | hold not exactly one month earlier with `pub_lag=0` | Exact one-month shift in all 757 months | pass |
| (b)4 signal unit tests | any mismatch | Extreme, zero, extreme gives one crossing with bridging and two without. 6 zeros in the trailing 60 leave the signal on; 7 turn it off. Zero months have NaN z, so they never enter the history (lines 287-288) | pass |
| (b)5 hold tests | 6 months tau+1..tau+6; tau and tau+3 give one 9-month run; w in [-1, 0] | All hold | pass |
| (b)6 cost test | mismatch | Zero costs give net = gross exactly. First real entry (1995-09): hand cost 2.138e-3, charged in 1995-10 | pass |
| (b)7 BOND | D(5%) about 7.79; corr(BOND, -dy) > 0.99 | D(5%) = 7.794581, equal to the closed form. Correlation 0.996 over 1993-2009 | pass |
| (b)8 regression mechanics | k, df, identity gap, rank, lstsq = statsmodels | k = 15, n - k = 164, identity gap 1.9e-18. The built-in lstsq and df assertions (lines 813, 526) did not fire | pass |
| (b)9 shuffle placement | a draw changes K or total hold months | 0 violations in 5,000 placements of the real blocks. Seed 230 reproduces the reference draws exactly | pass |
| (b)9 null seeds, v1 | more than 4 of 20 with p <= 0.05 | **Seed 16 crashes** (BUG-1). 0 of the other 19 have p <= 0.05 | incomplete |
| (b)9 null seeds, v1fix | same | 0 of 20 | pass |
| (b)10 positive control, v1 | planted effect missed | Alpha t 0.98, shuffle p 0.26; 4% of the D shift reaches alpha | **STOP** (BUG-1) |
| (b)10 positive control, v1fix | same | t 4.15, shuffle p 0.005 | pass |
| (b)10 delta = 0 | original alpha back exactly | Gap 0.0 | pass |

Checks (b)11 to (b)13 (seen-window run, coverage, freeze) are procedural and are covered by runs 3, 4 and 9 and by the manifest.

The 20-seed null check has little power as a size test: 0 of 20 is what a correctly sized 5% test gives 36% of the time. It catches only gross over-rejection.

**Positive control on the real data** (AB, 200 draws, planted cut in Brown returns during hold months):

| Planted per month | mean(D) shift, %/yr | Alpha, %/yr | t | Shuffle p | Share of the shift in alpha |
|---|---|---|---|---|---|
| 0.5% | +0.81 | +0.61 | 0.86 | 0.124 | 99% |
| 1% | +1.59 | +1.39 | 1.87 | 0.020 | 99% |
| 3% | +4.36 | +4.16 | 4.95 | 0.005 | 100% |

On real data, the I x F interactions do not absorb a pure timing effect, so the missing I main effect (Claude's assumption 19) costs almost nothing here. The table also shows the power limit noted in the reference's caveat 3: a planted 1%/month effect in hold months (+1.4%/yr of alpha) still fails (i).

**Mutation test of `check_no_lookahead`** (synthetic, 59 cuts):

| Injected bug | Cuts flagged | Detected | Changes the synthetic alpha? |
|---|---|---|---|
| M1 publication lag dropped | 12 | yes | yes |
| M2 month-t return hedged with b_t (estimated using R^B_t) | 0 | **no** | yes |
| M3 signal uses next month's EMV | 12 | yes | yes |
| M4 size m_t uses next month's sd | 59 | yes | yes |
| M5 hedge betas from a centered window | 54 | yes | yes |
| M6 position earns its own month | 0 | **no** | yes (alpha changes sign) |

The test compares only states set at the end of T: hold, w, m, the overlay and b (lines 915-916, 935). It cannot see return-side timing. Check (b)2 covers that gap only if it is run against the team engine.

## 4. Component comparison: Claude as delivered vs the reference

The reference is the published `outputs/tables/M8_*.csv`, rebuilt in memory from run.py to 4e-16. "AB gap" is Claude under both switches minus the reference.

| Component | Claude as delivered | Reference | Cause | AB gap |
|---|---|---|---|---|
| First data month with z | 1989-12 | 1989-01 | A | 0 |
| z on common months (373) | identical | | none | 0 |
| First data month with threshold | 1994-12 | 1994-01 | A | 0 |
| Threshold, 1995-2009 | max gap 0.076, falling to 0.002 by 2009 and 0.001 by 2022 | | A (11 fewer early z values in the history) | 0 |
| Crossings, data months 1993-01 to 2009-10 | 35. Adds 1997-04, 2002-12 and 2007-07; lacks 1997-05 | 33 | A | identical over 1985-2026 |
| Hold months, decision months 1994-02 to 2009-11 | 6 differ: 2003-01 to 2003-06, from the 2002-12 crossing. The 1997 and 2007 differences fall inside running holds | | A | 0 |
| Test window | 1995-02 to 2009-12, n = 179 | 1994-03 to 2009-12, n = 190 | A | same |
| Hedge betas b_t, 1994-2009 | max gap 0.092 | | B | 0 |
| Vol-target size m_t | max gap 0.012 | | B | 7.8e-16 |
| Net R^AO | max gap 0.0015/month | | B | 3.5e-17 |
| Net R^T | max gap 0.014/month | | A (holds) + B | 3.5e-17 |
| pi | 0.809 | 0.729 | A (B alone: 4e-5) | 0 |
| Months in position | 148 of 179 | 142 of 190 | A | same |
| D_t | max gap 0.013/month | | A + B | 1.0e-16 |
| 10 regressors (FF5 + UMD, BOND, WTI, dVIX, dlogEMV) | identical | | none | 4.4e-16 |
| k | 15 | 15 | none | same |
| Alpha | -0.19%/yr | -0.18%/yr | mainly A | 1e-14 |
| NW(6) t / NW(12) t | -0.252 / -0.277 | -0.266 / -0.287 | A | 8e-14 |
| p, two-sided / one-sided, t(n-k) | 0.802 / 0.599 | 0.790 / 0.605 | A | 6e-14 |
| Shuffle one-sided p | 0.536 | 0.478 | A (B alone: 0.007) | 0 (exact) |
| Shuffle null median | -0.14%/yr | -0.22%/yr | A | 4e-13 |
| Shuffle draws, draw by draw | differ (different N and blocks) | | A | 8.3e-15 |
| Episodes | 10; lengths 6, 6, 16, 6, 11, 25, **20**, 25, 23, 10 | 10; 7th is 14 | A | identical |
| Drop Util / Ships / Aero / Steel / BldMt, %/yr | -0.54 / +0.03 / **-0.12** / -0.25 / -0.09 | -0.61 / +0.03 / +0.01 / -0.19 / -0.11 | A | 4e-14 |
| (iv) | 4/5 same sign, FAIL | alpha <= 0 and 2 flips, FAIL | A, plus the (iv) reading (D4) | same |
| Decomposition identity gap | 1.9e-18 | 9e-18 | none | |
| Verdict | FAIL, 1/4 | FAIL, 1/4 | | same |

Decomposition in %/yr, as delivered vs reference: mean(D) +0.10 vs +0.04; alpha -0.19 vs -0.18; FF5+UMD +1.34 vs +0.89; BOND +0.01 vs +0.28; WTI +0.03 vs -0.01; volatility block +0.10 vs +0.00; conditional Mkt-RF/HML -1.19 vs -0.69; conditional BOND +0.01 vs -0.25.

**The conditional-beta terms depend on the window start.** As delivered:

| Term | Claude coefficient (t) | Reference coefficient (t) |
|---|---|---|
| dVIX | 0.0021 (3.23) | 0.0010 (1.57) |
| I x dVIX | -0.0020 (-2.89) | -0.0008 (-1.25) |
| Mkt-RF | 0.104 (1.78) | 0.052 (0.99) |
| BOND | 0.003 (0.02) | 0.094 (1.34) |

Under switch A alone, every t lies within 0.08 of the reference. So these moves come from dropping the 11 flat months 1994-03 to 1995-01, not from the factor file. It supports the reference's statement that the pooled conditional-beta reading "is not robust on its own terms". Alpha barely moves.

## 5. Root-cause audit by component

| Component | Finding |
|---|---|
| Look-ahead | None in Claude's pipeline. Its truncation test passes on synthetic (59/59) and real data (66/66). Under AB its net returns equal the team engine's to 3.5e-17. The test itself is blind to return-side errors (M2, M6), but none is present. |
| Zero handling | Same as the reference. A zero is missing, dropped from the z window and the history, and cannot trigger. The signal is off above 6 zeros in 60. The bridge limit of 6 (line 308) never binds: under A, crossings equal the reference's skip-all rule in every month of 1985-2026. There are 0 off months before 2010; the first is 2022-07. |
| Percentile history | Same construction: past-only, valid z only, linear interpolation, minimum 60 (lines 283-288). It differs only through A, because Claude's history lacks the 11 z values of 1989-01 to 1989-11. |
| Holds | Same: extend-not-stack rolling max, then the one-month publication shift (lines 324-325). All 6 differing months come from A's extra 2002-12 crossing. |
| Hedge lag | Same: b_{t-1} applied to the month-t return and e_t = R^B_t - a_{t-1} - b_{t-1}'f_t (lines 239, 362). The betas differ only through the factor file (B). |
| Vol target | Same: 36-month std with ddof 1, 5% target, cap 1 (line 242). m_t differs only through B. |
| Costs | Same: 10 bp on the asset, 5 bp on the Mkt-RF overlay, 25 bp on the SMB and HML overlays, charged in t+1. The cost test passes and the AB net matches to 3.5e-17. |
| pi | Same definition (line 484). The value differs only through A: the window drops 11 flat months and adds 6 hold months. |
| Regressors | Identical to 4.4e-16. BOND uses exact cash-flow D and C, as the reference does. |
| k, p-values | k = 15 in both. statsmodels HAC (Bartlett, no small-sample correction) with `use_t=True` equals the team NW formula with t(n-15) p-values to 3e-13. Claude's assumption 22 and the prompt's claim are both correct. |
| Shuffle | Same stars-and-bars placement, with the same RNG call order (`permutation`, then `choice`; lines 653-654). Under AB the null draws are identical. It is one-sided with ties counted as >= (line 701), and it recomputes pi and I in every draw, as C24 does. |
| Episodes | Same definition, and a run cut by the window edge counts once. 10 in both; the 7th differs in length through A. |
| Leave-one-out | Same rebuild. As delivered, the Aero alpha flips sign (-0.12% vs +0.01%) through A. |

## 6. Bug and issue list (most severe first)

1. **BUG-1, genuine (test harness), line 881.**
   - Cause: the synthetic GS10 random walk sticks to its 0.5% clip, so BOND is constant.
   - Consequences: (a) I x BOND stands in for an I main effect and absorbs 96% of the planted effect, so Claude's positive control, check (b)10, would STOP the protocol before the real run; (b) seed 16 gives a constant BOND over the whole window, so the rank check (line 521) raises and the (b)9 null-seed loop aborts.
   - The docstring expectation at lines 948-949 (alpha of about delta(1 - pi)mean(I m)) holds only if no regressor spans I. That is true on real data (99%) but false for this generator.
   - Fixed in v1fix by one edit. There is no effect on real-data numbers.
2. **D1, spec reading, not a parameter (discrepancy A), lines 274-275.**
   - Claude requires a full 60-month calendar window, so the "at least 48 nonzero months" clause can never bind. Its assumption 11 says so explicitly.
   - The prompt asked that each silent reading be a parameter. The three points the prompt named are parameters (lines 66-72), but this fourth one is hard-coded.
   - The reference reading (C5) gives the clause a role as the burn-in.
   - Impact: window 1995-02 instead of 1994-03, pi 0.81 instead of 0.73, shuffle p 0.54 instead of 0.48. The verdict does not change.
3. **D2, input gap in the prompt (discrepancy B), lines 377-378.**
   - The hedge and the leg's RF use `fac`, the FF5 file, whose SMB is built differently from the FF3 SMB. The Mkt-RF vintages also differ by up to 8 bp; HML and RF are identical.
   - The prompt never said that the team hedge uses the team FF3 file, so this is not Claude's error.
   - Impact on alpha: 0.004%/yr. Claude's own check (b)2 stops on it.
4. **D3, test coverage, lines 895-941.** `check_no_lookahead` compares only states set at the end of T. It misses the injected same-month hedge (M2) and same-month earning (M6) bugs, and it is conditional on `cfg.pub_lag` itself being right. Claude's separate lag probe (b)3 covers that last point.
5. **D4, pass-bar logic, lines 730, 744, 754.**
   - (iv) passes when every drop-one alpha has the sign of the full alpha, even if that sign is negative. So a negative alpha with five negative drop-one alphas would print "(iv) PASS".
   - This is a literal reading of "keeps its sign". The reference (C26) also requires alpha > 0; the one-line fix is `bool(a > 0 and same == nl)`.
   - No effect here: (i) fails, and as delivered (iv) is 4/5.
6. **D5, "seen" mode, lines 979-980.**
   - The seen window ends at 2022-12, so it includes holdout months 2022-08 to 2022-12. They flip the seen alpha from -0.16%/yr (t -0.24, through 2022-07) to +0.26%/yr (t 0.37).
   - The look-ahead call in that mode sets no `cut_to`, so its cuts reach 2024-08 despite the "seen data only" label.
   - This is cosmetic for the frozen test.

## 7. Claude's stated assumptions, checked

| # | Claim | Check |
|---|---|---|
| (a)1 | Bridge a zero month; limit of 6 | Consistent with the reference's C8. Never binds in 1985-2026. |
| (a)2 | Shuffle: same blocks, gap >= 1, pi and I recomputed per draw | Identical to C24, draw by draw. |
| (a)3 | Truncate a hold still open at 2009-12 | Same as the reference (decision months after 2009-11 are ignored). |
| 4-6 | Decimal guard, -0.99 mask, month-end mapping, no forward fill | Correct and harmless. 0 Brown NaNs. |
| 7 | Hedge needs 60 complete months and sizing 36, estimated from 1963-07, so results do not depend on the start | Correct. It hedges on `fac`, though (D2). |
| 8-9 | Overlay drift turnover; timed book starts flat; always-on book on since the 1970s | Matches the team engine (AB gap 3.5e-17). |
| 10 | z over nonzero months of t-59..t, ddof 1 | Matches C5. |
| 11 | Full 60-month window, first z 1989-12, the 48 minimum never binds | Accurate description of its own reading. It is the source of A (D1). |
| 12-13 | NaN EMV treated as zero; off months treated as zero months; running holds continue | Matches C6 and C9. No NaN exists. |
| 14 | numpy linear percentile, strict >, history from 1989-12 | Matches C7 except the start (A). |
| 15 | The first defined month can be a crossing | Matches C8. |
| 16 | First return month about 1995-02 | Correct under its reading (exactly 1995-02). The reference gives 1994-03. |
| 17-18 | pi ex post from w_{t-1}; I_{t-1} = hold state at t-1 | Match C13 and C19. |
| 19 | No I main effect, so alpha is the average timing alpha | A correct flag. On real data 99% of a planted pure timing effect reaches alpha, so it matters little here. |
| 20 | Exact cash-flow D and C; GS10 monthly average used as the month-end yield | Correct. D(5%) = 7.7946. |
| 21 | dVIX from monthly means; month-over-month log changes for WTI and EMV | Identical to the reference. |
| 22 | statsmodels HAC default = no small-sample correction = the team convention | Verified to 3e-13. |
| 23-24 | Edge episodes count once; hold fixed in drop-one; sign equal to the full alpha | 23 matches C25. On 24, see D4. |
| 25 | Current vintages; the EMV share cancels full-sample scaling, "so it creates no look-ahead" | The cancellation is right, but "no look-ahead" is too strong. The share is still a current-vintage series, as the reference's caveat 5 keeps. |

## 8. Code quality

Strengths:

- The structure is clean: one function per step, docstrings that state timing, a frozen `Config`, and a fixed seed.
- It fails loudly: it raises on missing regressors, rank deficiency, a df mismatch, or disagreement between the lstsq and statsmodels alphas (lines 521, 526, 813).
- The three silent points the prompt named are parameters, each with a reason.
- It delivers all five required outputs.
- It says honestly that it was not executed.
- It ran unchanged on pandas 3 and numpy 2.5.
- Its mathematics is identical to the reference: under AB, every quantity agrees to rounding error.

Weaknesses:

- BUG-1.
- One silent reading is hard-coded (D1).
- The look-ahead test is state-only (D3).
- (iv) accepts a negative alpha (D4).
- The shuffle rebuilds the pandas book on every draw. That takes about 50 s per 5,000 draws, which is acceptable; the reference uses a numpy engine checked against the team engine.

## 9. Files

All in `/home/hashim/projects/GA/project/research/exchange/02_coding_support/checks/`:

- Code:
  - `chatgpt_code_v1.py`: verbatim extraction;
  - `chatgpt_code_v1fix.py` and `v1_to_v1fix.diff` (named `chatgpt_code_v2.py` and `v1_to_v2.diff` in round 1): BUG-1 fix only;
  - `glue.py` and `run_chatgpt_real.py`: glue G1-G4;
  - `align.py`: switches A and B;
  - `compare.py`: section 4;
  - `prerun_checks.py`: section 3;
  - `null_seeds.py`;
  - `mutation_lookahead.py`.
- Outputs (`out/`):
  - every run's tables, as `final_{asis,A,B,AB}_*.csv`, `seen_asis_*`, `seen0722_{asis,AB}_*`;
  - `compare_components.csv`, `compare_attribution.csv`, `compare_crossings.csv`, `compare_summary.json`;
  - `prerun_checks.csv`, `positive_control.csv`, `null_seeds_v1_all.csv`, `null_seeds_v2_all.csv`, `mutation_lookahead.csv`, `lookahead_seen_asis.csv`;
  - `manifest.json`: sha256 of every file above.
- Logs: `logs/run01` to `run09`.

Nothing was written to the team repo, `modules/M8_frozen_pre2010/` or `outputs/`. The reference module's bytecode (06:07:47) and PREREGISTRATION.md (sha256 e926c3ae...0b51) are unchanged.

## Note on file times (outside this task)

Every `outputs/tables/M8_*` file has modify time 06:10:07, and `M8_preregistration_hash.csv` records this_run_time 06:09:57 PDT. So run.py was executed once more after the 06:05:14 rerun that FINDINGS documents ("their modify times are now 06:05"). The content is unchanged: 16 of 20 tables are byte-identical to `corrections/pre_correction_0341/tables`, and the same 4 changed, as FINDINGS describes. Only FINDINGS' timeline sentence is stale.

---

# Round 2: Claude's corrected functions

Code test run 2026-09-26, 07:00 to 07:30 PDT. Same environment and conventions as round 1. Round-2 logs are `checks/logs/r2_run*`, and outputs are `checks/out/r2_*` and `checks/out/v2_unit_tests_*`.

- Input: Claude's follow-up reply, as pasted from the chat. It contains six replaced functions (`make_synthetic_inputs`, `attention_signal`, `leg_pipeline`, `pass_fail_table`, `check_no_lookahead`, `__main__`), one unit test for each, shared raw-input helpers, the adapter `run_panel`, and four driver changes.
- The reply's code block, transcribed verbatim: `checks/chatgpt_round2_block.py` (704 lines, sha256 13676a4e...bcd4827).
- The assembled round-2 code: `checks/chatgpt_code_v2.py` (1,560 lines, sha256 d087bfb1...c189fc). Its diff against v1 is `checks/v1_to_v2_round2.diff` (717 lines added, 213 removed).

## R2 Summary

**Verdict: the corrected code is correct.** With its defaults (`z_burn_in="nonzero"`, hedge on the team FF3 file), it reproduces the reference to rounding error on every component and reaches the same verdict: FAIL, 1 of 4 (episodes only). "Do not implement" stands.

1. **All six round-1 items are fixed: BUG-1 and D1 to D5.** Claude's six unit tests pass the first time, with no edit to Claude's code. So do its three "checks to run first" and its checks (b)2, (b)9 and (b)10.
2. **The test-window run equals the reference.**
   - Result: FAIL 1/4. Alpha -0.18%/yr (NW(6) t -0.27, NW(12) t -0.29, p 0.790, one-sided 0.605). Shuffle p 0.478. 10 episodes. (iv) FAIL.
   - Largest gaps over all 15 terms: coefficients 3.8e-14, t-statistics 3.3e-13, p-values 1.9e-13.
   - The shuffle p is exact, and the 5,000 null draws agree draw by draw to 8.3e-15.
   - Every pass/fail row matches: (i) FAIL, (ii) FAIL, (iii) PASS, (iv) FAIL, overall FAIL.
3. **The two readings are now switches, and each does what it says.**
   - `z_burn_in="calendar"` reproduces Claude's old signal exactly. The full run equals round-1 v1 + B to 1e-14.
   - The new `hedge_fac` input puts the team FF3 file into the leg, the hedge and the overlay. The attribution still uses FF5 + UMD.
   - The verdict is FAIL 1/4 under either burn-in reading.
4. **The seen window equals the reference dry run:** alpha -0.12%/yr, t -0.19, shuffle p 0.510, 6 episodes, 0 of 4. Claude's instruction to report -0.16%/yr and t -0.24 for this window is wrong for its own new code. Those are round-1 numbers with the FF5-file hedge (N2).
5. **The new look-ahead audit works.**
   - It passes all 361 rows on four runs (synthetic, test under both readings, seen). Its largest return-side error is 5e-17.
   - It flags 7 of 8 injected timing bugs, including round 1's two misses (M2, M6). The eighth (M5) makes the audited pipeline raise an error, which also stops the protocol.
6. **One new issue matters: an integration gap (N1).**
   - The new `attention_signal` changes its output layout, and the reply's driver instructions do not mention it.
   - A literal drop-in crashes (`KeyError 'off'`). The obvious one-line patch then runs silently on a window 14 months too long (1993-01, n = 204): alpha -0.13%/yr, t -0.21. The verdict is still FAIL 1/4.
   - I bridged the gap with a value-preserving adapter.
7. **Other items are minor:** three inaccurate claims (N2 to N4) and some dead or incompatible code (N5).
8. **Extra observation (not about Claude's code).** On 100 further null seeds, the calendar shuffle is correctly sized, but the pre-registered NW(6) t over-rejects (13 of 100 beyond the 5% two-sided critical value). This affects the reference's component (i) as much as Claude's. It cannot turn a FAIL into a PASS (R2.9).

## R2.1 Run log

| # | Run | Code | Window / data | Result |
|---|---|---|---|---|
| R1 | Claude's `run_unit_tests()` as delivered | v2 | synthetic | 6 of 6 ok, 33 s |
| R2 | Synthetic mode (`__main__` statements; unit tests run in R1) | v2 + glue | synthetic seed 0, 1993-01 to 2009-12 | Audit 91/91 ok. FAIL 1/4: alpha t -0.58, shuffle p 0.512, 12 episodes |
| R3 | Test mode, `z_burn_in="nonzero"` (default) | v2 + glue | 1993-01 to 2009-12; the code moves the start to 1994-03 | Audit 89/89 ok. FAIL 1/4: alpha -0.18%/yr, t -0.27, shuffle p 0.478, 10 episodes. **Equals the reference** |
| R4 | Test mode, `"calendar"` | v2 + glue | same; start 1995-02 | Audit 89/89 ok. FAIL 1/4: alpha -0.19%/yr, t -0.25, shuffle p 0.530. Equals round-1 v1 + B to 1e-14 |
| R5 | Seen mode, `"nonzero"` | v2 + glue | 2010-01 to 2022-07, inputs cut at 2022-07 before the audit | Audit 92/92 ok. FAIL 0/4: alpha -0.12%/yr, t -0.19, shuffle p 0.510, 6 episodes. **Equals the reference dry run** |
| R6 | Seen mode, `"calendar"`, no audit | v2 + glue | same | Identical to R5 (every gap 0.0) |
| R7 | Claude's "checks to run first", plus contract checks (`checks_first_v2.py`) | v1, v2, reference | real | Section R2.3 |
| R8 | Check (b)2, team trade (`team_trade_v2.py`) | v2 | 2010-01 to 2022-07 | 2.8e-17 on both books: pass |
| R9 | Component comparison (`compare_v2.py`) | | | Section R2.8. The in-memory reference matches the published primary and dry-run tables to 2.2e-16 first |
| R10 | Check (b)10, positive control, seeds 0-2, plus delta = 0 (`pc_null_v2.py pc`) | v2 | synthetic, 500 draws | t 3.5 to 6.1, shuffle p 0.002, 97% to 104% of the shift in alpha |
| R11 | Check (b)9, null seeds 1-20 | v2 | synthetic, 500 draws | 1 of 20 with p <= 0.05; no crash |
| R12 | Extra: null seeds 21-120 | v2 | synthetic, 200 draws | Shuffle p <= 0.05 in 6 of 100; NW(6) t beyond the 5% critical value in 13 of 100 |
| R13 | Mutation test of the new audit (`mutation_lookahead_v2.py`) | v2 + mutants | synthetic seed 0 | 7 of 8 flagged; M5 makes the audit raise |
| R14 | Literal drop-in of the new `attention_signal` (`dropin_variant_v2.py`) | v2, adapter I1 replaced by the minimal patch | real, test window | Window 1993-01 to 2009-12, n = 204. FAIL 1/4: alpha -0.13%/yr, t -0.21 |

## R2.2 How v2 was built

### R2.2a What is in chatgpt_code_v2.py

| Part | Source |
|---|---|
| Everything in v1 except six definitions | v1, unchanged. This includes functions that are now unused: `brown_leg`, `rolling_hedge`, `hedge_residual_and_size`, `plant_timing_effect`. |
| Removed from v1 | The old `attention_signal`, `leg_pipeline`, `pass_fail_table`, `make_synthetic_inputs`, `check_no_lookahead` and `__main__`. |
| Claude's block, verbatim, at the end of the file | The six replacements, their tests, helpers, `positive_control`, `run_panel` and the new `__main__`. `diff` against `chatgpt_round2_block.py` is empty. It sits after `Config` because the block redefines `BROWN` as a list (see N5). |
| Claude's driver changes | `run_backtest` and `leave_one_out`, each marked "ROUND 2" (table R2.2b). |
| Three adapters, not from Claude | `_driver_signal`, `_leg_books`, `_panel` (table R2.2c). None changes a value. |

### R2.2b Claude's driver changes, as implemented

| # | Claude's instruction | Implementation |
|---|---|---|
| 1 | `run_backtest` takes `hedge_fac` and `z_burn_in`. Pass `hedge_fac` to every `leg_pipeline` call (the main run and all five leave-one-out rebuilds), and `z_burn_in` to `attention_signal`. | Signature exactly as `run_panel` calls it: `run_backtest(paths, fac, start, end, *, hedge_fac, z_burn_in, n_shuffle, run_loo, verbose)`. `leave_one_out` takes `hedge_fac`. `n_shuffle = 0` and `run_loo = False` skip those steps, which the unit tests rely on. |
| 2 | The overlay return and costs use the leg's `f_*` and `b_*` (FF3), not `fac`. | Both books are built by the unchanged `run_trade` on the leg's own `f` and `b` (adapter I2). |
| 3 | `pass_fail_table` takes plain numbers. | Called with the alpha, NW(6) t, two-sided p, shuffle p, episode count and the five drop-one alphas. The verdict is read from the `overall` row. |
| 4 | `run_panel` assumes this signature and the output keys in its docstring. | Met: `run_backtest` also returns `panel`, `alpha` and `alpha_t`, and already returned `D` and `X`. `run_panel` is unedited. |

### R2.2c Adapters (mine, value-preserving)

| ID | What it does | Why it is needed |
|---|---|---|
| I1 `_driver_signal` | Maps the new signal frame onto the v1 layout the unchanged driver reads. `extreme` becomes 1/0 where z and the threshold are defined and NaN elsewhere; zero months get `s` = 0 back; `missing` and `off` are added. | The new layout breaks four unchanged readers (N1). |
| I2 `_leg_books` | Turns the new leg DataFrame into the v1 leg dict (`rb`, `f`, `a`, `b`, `e`, `sd`, `m`, `tr_T`, `tr_AO`). | The new `leg_pipeline` no longer takes the hold or builds the books. Driver change 2 implies this but does not spell it out. |
| I3 `_panel` | Builds the panel that `run_panel`'s docstring promises: `w`, `w_ao`, `RT`, `RAO`, `m`, `hold`, `b_*`, `I`. | `run_panel` returns `out["panel"]`. |

Checks CF1b and CF2 and the final comparison show that the adapters change no value.

### R2.2d Glue (same as round 1, plus the new input)

| ID | What | File |
|---|---|---|
| G1 | `fac` = `common.load_ff5_mom()` FF5 + RF + UMD, as in round 1 (`__main__` leaves `fac = None`). | `run_v2_real.py` |
| G2 | Absolute paths for the team FF49 file and `research/data/raw/fred_<id>.csv` (`__main__` uses bare names). | `run_v2_real.py` |
| G3 | The mode is taken from the command line instead of the `MODE` constant. Each mode runs the same statements as `__main__`. | `run_v2_real.py` |
| G4 | Not needed now: the windows are Claude's constants, `TEST_WINDOW` and `SEEN_WINDOW` (which ends 2022-07). | |
| G5 | `hedge_fac` = the team FF3 file (`Mkt-RF`, `SMB`, `HML`, `RF`; `__main__` leaves it `None`). This is the same frame as round-1 switch B. | `run_v2_real.py` |

Preserving round 1: `chatgpt_code_v2.py` (BUG-1 only) was renamed `chatgpt_code_v1fix.py`, and `prerun_checks.py` now imports it under that name. That is the only edit to a round-1 script.

## R2.3 Claude's tests and checks

**Unit tests** (R1; also run one at a time, `run_v2_tests.py`):

| Test | Result | Time | What it covers |
|---|---|---|---|
| `test_attention_signal` | ok | 0.1 s | First z at month 48 (nonzero) or 60 (calendar); the same z once the window is full; hand-checked z; past-only threshold; zero handling; 7 zeros in 60 switch the signal off |
| `test_pass_fail_table` | ok | 0.0 s | Negative alpha with negative drop-ones now fails (iv); bar boundaries; NaN shuffle p; 4 drop-ones |
| `test_seen_cut` | ok | 0.1 s | Truncation at 2022-07 removes all later rows |
| `test_leg_pipeline` | ok | 0.9 s | Hand OLS to 1e-12; residual uses t-1 coefficients; month T+1 cannot reach row T; the hedge SMB moves b but not X; the FF5 frame is refused |
| `test_check_no_lookahead` | ok | 15.1 s | The toy pipeline passes; its three toy bugs (hedge with b_t, own-month earning, signal lag) are each caught by the intended test |
| `test_make_synthetic_inputs` | ok | 20.9 s | 21 seeds: GS10 > 0.5 and moves every month; full-rank design with only the constant flat, in 42 runs; R2 of I on X < 0.5; positive control for seeds 0-2 |

**Claude's "checks to run first", and the contract checks** (R7, `out/r2_checks_first.csv`):

| Check | Result | Status |
|---|---|---|
| CF1 `attention_signal(env, overall, "calendar")` vs the old function on the real EMV files | Same index (1985-01 to 2026-08). z and threshold differ by 0.0, with the same NaN pattern. `extreme` agrees in all 313 months where v1 defines it and is never True where v1 leaves it undefined. | pass |
| CF1b `"nonzero"` vs round-1 switch A and vs the reference `share_signal` | z and threshold 0.0 against both. `extreme` identical. Crossings (I1 plus the unchanged v1 `crossings`) equal the reference's in all 500 months of 1985-01 to 2026-08. First z 1989-01, first threshold 1994-01. | pass |
| CF2 `leg_pipeline(ff49, fac[["Mkt-RF","SMB","HML","RF"]])` vs the old leg | RB, a, b, e, sd and m all differ by 0.0 over 1963-07 to 2026-07, with no NaN mismatch. | pass |
| CF2b `leg_pipeline(ff49, team FF3)` vs the reference `brown_model` | Betas 0.0; residual 1.4e-17 (1990-2026). | pass |
| CF3 full backtest with (`"nonzero"`, FF3) vs the reference, row by row | Section R2.8: equal to 3.3e-13 at worst, and every pass/fail row identical. | pass |
| Claude's choice 3: `hedge_fac` RF equals `fac` RF, "the driver can assert that" | Equal only to 1.0e-16. 162 of 757 months differ by one ulp (0.0028 vs 0.0028000000000000004), because the FF5 file is converted from percent. An exact assert fails (N3). SMB differs by up to 0.0351, Mkt-RF by up to 0.0008. | fails if exact |
| N1 contract: the new `attention_signal` output fed to the unchanged driver with no adapter | Section R2.6, N1. | integration gap |

**Claude's own section-(b) checks, rerun on v2:**

| Check | Stop rule | Round 2 result | Status | Round 1 |
|---|---|---|---|---|
| (b)2 team trade, 2010-01 to 2022-07 | any month off by more than 1e-8 | Always-short Brown and Original 6m both 2.8e-17 | pass | STOP at 2.3e-3 |
| (b)9 null seeds 1-20, 500 draws | more than 4 of 20 with p <= 0.05 | 1 of 20 (seed 3: p 0.002, t 3.34, 8 episodes). Seed 16 runs (p 0.491). | pass | seed 16 crashed |
| (b)10 positive control, 3% | planted effect missed | Table below | pass | STOP |
| (b)10 delta = 0 | original alpha back | Gap 0.0 | pass | pass |

Seed 3's p of 0.002 is the smallest value that 500 draws allow. At least one such seed in 20 happens 3.9% of the time under a correct null, so it is unusual but consistent with chance. R12 checks the size properly (R2.9).

**Positive control on the new generator** (R10, 500 draws; Brown returns lowered by 3% in every held month):

| Seed | Held months | Alpha before / after, %/month | t after | Shuffle p after | Share of the mean(D) shift in alpha | Largest other \|t\| |
|---|---|---|---|---|---|---|
| 0 | 112 | -0.027 / +0.312 | 6.07 | 0.002 | 104% | dlogEMV, -1.63 |
| 1 | 114 | -0.087 / +0.240 | 3.50 | 0.002 | 97% | RMW, 1.86 |
| 2 | 109 | -0.093 / +0.273 | 4.00 | 0.002 | 100% | UMD, -1.78 |
| 0, delta = 0 | 112 | -0.027 / -0.027 | -0.58 | 0.505 | | |

Round 1 as delivered: t 0.98, with 4% of the shift in alpha and I x BOND at t -10.8. With v1fix: t 4.15, 105%. No regressor now stands in for I.

## R2.4 The new look-ahead audit

**On the four runs** (`out/r2_lookahead_*.csv`): 24 months are audited per run, drawn from entries and exits, held months and flat months.

| Run | Rows | post_window | truncate | rb_perturb | f_perturb | signal_perturb | Passed | Largest return error |
|---|---|---|---|---|---|---|---|---|
| Synthetic | 91 | 1 | 18 | 24 | 24 | 24 | 91 | 4.2e-17 |
| Test, nonzero | 89 | 1 | 16 | 24 | 24 | 24 | 89 | 2.8e-17 |
| Test, calendar | 89 | 1 | 16 | 24 | 24 | 24 | 89 | 4.9e-17 |
| Seen, nonzero | 92 | 0 (data end at the window end) | 20 | 24 | 24 | 24 | 92 | 4.9e-17 |

The state gaps are exactly 0 in every row. The measured return responses equal the expected ones: w_{T-1} delta for a Brown shock, and -w_{T-1} delta sum(b_{T-1}) for a hedge-factor shock.

**Mutation test** (R13, `out/r2_mutation_summary.csv`). The same bugs as round 1, adapted to the v2 signatures, plus M7. The audit runs through the real v2 driver on synthetic seed 0, exactly as `__main__` calls it.

| Injected bug | Rows flagged (of 91) | Flagged by | `truncate` rows flagged | Round 1 (v1 audit) |
|---|---|---|---|---|
| none | 0 | | 0 | 0 of 59 |
| M1 publication lag dropped | 10 | signal_perturb | 0 | detected (12) |
| M2 month-t return hedged with b_t | 48 | rb_perturb, f_perturb | 0 | **missed** |
| M3 signal uses next month's EMV | 10 | signal_perturb | 0 | detected (12) |
| M4 size m_t uses next month's sd | 49 | rb_perturb, f_perturb, post_window | 0 | detected (59) |
| M5 hedge betas from a centered window (NaN in the last 30 months) | audit raised `ValueError: non-finite strategy values inside the test window` in its first truncated run | stops loudly | | detected (54) |
| M5b same, with the tail filled by the last centered beta | 67 | truncate, rb_perturb, f_perturb, post_window | 18 | not run |
| M6 position earns its own month | 59 | rb_perturb, f_perturb, signal_perturb | 0 | **missed** |
| M7 cost charged in the trade month (new) | 59 | rb_perturb, f_perturb, signal_perturb | 0 | not run |

D3 is fixed: return-side timing is now tested, and both round-1 misses are caught. Detection rests on the three perturbation tests. The renamed `truncate` test flags only M5b (N4).

## R2.5 Status of the round-1 bugs and issues

| Round-1 item | Status | Evidence |
|---|---|---|
| BUG-1 synthetic GS10 stuck on its clip | **Fixed** | log(GS10) is a stationary AR(1). In seeds 0-20 it stays above 0.5 and moves every month, and the design is full rank in all 42 runs. Positive control t 3.5 to 6.1, with 97% to 104% of the shift in alpha. Seed 16 runs. |
| D1 burn-in hard-coded | **Fixed** | `z_burn_in` parameter; the default `"nonzero"` is the C5 reading. `"calendar"` reproduces v1 exactly (CF1 0.0; full run equals v1 + B to 1e-14). |
| D2 hedge on the FF5 file | **Fixed** | New `hedge_fac` input feeds the leg's RF, the hedge and the overlay. A frame with RMW or CMA is refused. (b)2 passes at 2.8e-17. The leg equals the reference `brown_model`. |
| D3 state-only look-ahead test | **Fixed** | Return-side perturbation tests. 7 of 8 injected bugs are flagged, including M2 and M6; M5 stops the audit with an error. |
| D4 (iv) accepts a negative alpha | **Fixed** | (iv) needs the full alpha and all five drop-one alphas > 0, as in C26. Unit test, and on the real run (iv) FAILs at min -0.051%/month. |
| D5 seen mode reaches into the holdout | **Fixed** | `SEEN_WINDOW` ends 2022-07, and the inputs are cut there before the audit and the run. The seen panel ends 2022-07 and has no post-window row. |
| Round-1 finding 4: (b)2 stops on the as-delivered code | **Resolved** | By the D2 fix. |
| Round-1 precision | **Correction** | Round 1 said AB reproduces the reference "to 1e-13". The exact maximum was 3.3e-13, on a t-statistic (coefficients 3.8e-14). v2 has the same maxima. |

## R2.6 New issues in round 2 (most severe first)

1. **N1, integration gap: the new `attention_signal` output layout breaks the unchanged driver.**
   - The reply says "Everything not defined here is unchanged". Its four driver changes do not mention that `attention_signal` now returns a boolean `extreme` (False where undefined), NaN `s` on zero months, and no `missing`, `off` or `n_missing60` columns. Four unchanged v1 functions read the old layout.
   - `diagnostics_summary` reads `sig["off"]`, so a literal drop-in raises `KeyError: 'off'`. That failure is loud.
   - `test_window` takes the first non-NaN `extreme` as the first defined flag. With a boolean it gets 1985-01 instead of 1994-01, so if only the KeyError is patched, the window starts at 1993-01 (n = 204). C12 excludes 1993-01 to 1994-02 because no position can exist then. R14 shows the effect: pi 0.674 (true 0.729), alpha -0.13%/yr (t -0.21, p 0.836) instead of -0.18%/yr, shuffle p 0.464. The verdict is still FAIL 1/4.
   - `diagnostics_summary` counts `s == 0`, so it would report 0 zero months (true: 51 in the file, 6 feeding the window) and name 1985-01 as the first defined flag.
   - `crossings` bridges only NaN flags. With booleans, an extreme, zero, extreme run would restart. No such sequence occurs in 1985-2026 (58 crossings either way), so this has no numeric effect.
   - Fix: adapter I1 (value-preserving), or have `attention_signal` also return the v1 columns. The same kind of gap, a new return type, applies to `leg_pipeline`, but driver change 2 implies it (adapter I2).
2. **N2, claim: the seen-window numbers Claude tells us to report are stale.**
   - Claude says "alpha of -0.16%/yr, t -0.24". Those are round-1 v1 numbers as delivered, with the FF5-file hedge (run 4).
   - v2 with its own defaults gives -0.1207%/yr and t -0.1878, the reference dry run. The burn-in has no effect on this window (R6 is identical to R5), so the whole gap comes from the hedge file.
3. **N3, claim: "the driver can assert" that the two RF series are equal.**
   - They are equal only to 1e-16 (CF3 row). An exact `assert (a == b).all()` would stop the run; it needs a tolerance such as 1e-12.
   - No effect on results: the reference also takes the leg's RF from the team FF3 file.
4. **N4, description of the audit: `truncate` is not "the old check".**
   - The docstring calls `truncate` "the old check". The unit test says "the old state-only check misses all three" toy bugs.
   - v1's check cut EMV at T-1 and compared the state at T. It caught the publication-lag bug (round-1 M1, 12 cuts) as well as M3, M4 and M5.
   - The new `truncate` keeps month T's EMV and compares only through T-1, so on its own it flags only M5b.
   - Coverage is not lost, because the perturbation tests catch M1-M4, M6 and M7. Only the description is wrong.
5. **N5, cosmetic: dead or incompatible code, and a placement hazard.** None affects a result.
   - `plant_timing_effect` (not replaced, now unused) still calls `attention_signal(emv_cat, emv_all, cfg)`. Under the new signature, `cfg` lands in `z_burn_in` and the call raises `ValueError`. Nothing calls it.
   - `brown_leg`, `rolling_hedge` and `hedge_residual_and_size` are unused.
   - The new `attention_signal` drops v1's `sd > 0` guard. The reference has one; EMV never has zero dispersion.
   - The new `leg_pipeline` averages with `skipna=False` (team: `skipna=True`). No Brown industry has a missing month since 1963 (CF2 is exact).
   - The block's `BROWN` is a list. Pasted above `Config`, it would make the frozen dataclass raise at import (a mutable default for `brown`). Pasted below, as here, it is harmless.
6. **Observation, not a bug: a bug that leaves NaN at the sample end crashes the audit instead of being reported.** Every audit call runs the full backtest, and `timing_difference` raises on non-finite values (M5). The protocol still stops loudly.

## R2.7 Claude's round-2 claims, checked

| Claim | Check |
|---|---|
| "`z_burn_in="calendar"` should give the same z, thr and extreme as the old function" | True, exactly (CF1). |
| "`leg_pipeline(ff49, fac[[...]])` should reproduce the old leg exactly" | True, 0.0 (CF2). |
| "With ("nonzero", FF3), the full backtest should again match your implementation to 1e-13" | True to 3.3e-13 at worst (a t-statistic). Coefficients 3.8e-14. |
| "Compare each pass/fail row, not just the count" | Done. All five rows are identical on the test window and on the seen window. |
| "(iv) used to pass when it shouldn't have" | Overstated. The flaw was latent: (iv) never passed wrongly in any round-1 run (as delivered 4/5, AB 3/5, both FAIL). |
| Driver change 2: the old overlay used `fac`, so the FF5 SMB entered the overlay as well as the hedge | True. v1 passed the same `fac` columns to the hedge and to `run_trade`. Fixed. |
| Choice 1: zeros counted in the trailing 60 calendar months; pre-1985 months not zeros; off above 6 | True; matches C6. |
| Choice 2: off months get no z and stay out of the history | True; matches C6. |
| Choice 3: RF from `hedge_fac` is the same series, and an assert is possible | Equal to 1e-16 only (N3). |
| Choice 4: (iv) read as "stays positive" | Matches C26. |
| Choice 5: planted shift = mean(D) with minus without, same seed; 3% deliberately large | True. The hold schedule is identical with and without the plant (`same_I` in all three seeds). |
| Choice 6: the audit compares positions and returns, not D, because pi is ex post | True, and it is the right design. 0 false alarms in 361 rows. |
| "The verdict is FAIL ... under either burn-in reading" | True: FAIL 1/4 under both. |
| Seen window: "alpha of -0.16%/yr, t -0.24" | Wrong for v2: -0.12%/yr, t -0.19 (N2). |
| "I can't run code, so none of this has been tested" | Noted. Once integrated, every function and test ran the first time. The only thing that did not run as instructed is the N1 layout change. |

## R2.8 Final component comparison: v2 vs the reference

The reference is `modules/M8_frozen_pre2010/run.py`, rebuilt in memory and checked against the published `outputs/tables/M8_*` (primary) and `dryrun/M8dry_*` (seen) tables to 2.2e-16 before any comparison (`out/r2_compare_*`). "Gap" is v2 minus the reference: monthly decimals for returns, %/yr where the row says so.

| Component | v2 default ("nonzero", FF3) | Reference | Gap | v2 "calendar" (for contrast) | Seen: v2 vs dry run, gap |
|---|---|---|---|---|---|
| First data month with z / threshold | 1989-01 / 1994-01 | 1989-01 / 1994-01 | same | 1989-12 / 1994-12 | same |
| z, common months | 384 months | | 0.0 | 0.0 on 373 | 0.0 |
| Threshold, 1985-2026 | | | 0.0 | 0.076 | 0.0 |
| Crossings, 1985-01 to 2026-08 | 58 | 58 | identical | 60 (adds 1997-04, 2002-12, 2007-07; lacks 1997-05) | identical |
| Hold months differing, decision months of the window | 0 | | 0 | 6 (2003-01 to 2003-06) | 0 |
| Window | 1994-03 to 2009-12, n = 190 | same | same | 1995-02 to 2009-12, n = 179 | 2010-01 to 2022-07, n = 151, same |
| Hedge betas b_t | | | 2.2e-16 | 2.2e-16 | 2.2e-16 |
| Vol-target size m_t | | | 1.7e-15 | 1.7e-15 | 6.7e-16 |
| Net R^T / net R^AO | | | 1.0e-16 / 1.2e-16 | 0.014 / 1.0e-16 | 1.0e-16 / 1.0e-16 |
| pi | 0.7294 | 0.7294 | 1.1e-16 | 0.8086 | 1.1e-16 (0.7628) |
| Months in position | 142 | 142 | same | 148 | 112, same |
| D_t | | | 1.1e-16 | 0.013 | 1.0e-16 |
| 10 unconditional regressors | | | 4.4e-16 | 4.4e-16 | 8.9e-16 |
| k | 15 | 15 | same | 15 | same |
| Alpha, %/yr | -0.1818 | -0.1818 | 1.0e-14 | -0.1862 | 1.0e-13 (-0.1207) |
| NW(6) t / NW(12) t | -0.2661 / -0.2872 | -0.2661 / -0.2872 | 7.7e-14 / 8.3e-14 | -0.2487 / -0.2732 | 3.3e-14 / 3.9e-14 (-0.1878 / -0.2074) |
| p, two-sided / one-sided, t(n-k) | 0.7905 / 0.6048 | 0.7905 / 0.6048 | 5.9e-14 / 3.0e-14 | 0.8039 / 0.5981 | 2.6e-14 / 1.3e-14 |
| All 15 terms: coefficient / NW(6) t / NW(12) t / p | | | 3.8e-14 / 3.3e-13 / 3.3e-13 / 1.9e-13 | 0.089 / 1.70 / 2.52 / 0.77 | 2.4e-14 / 8.3e-13 / 8.8e-13 / 2.5e-13 |
| Decomposition terms | | | 1.3e-16 | | 8.3e-17 |
| Decomposition identity gap | 1.2e-18 | 9.0e-18 | | 1.2e-18 | |
| Shuffle one-sided p | 0.4779 | 0.4779 | 0 (exact) | 0.5303 | 0 (exact, 0.5101) |
| Shuffle null median, %/yr | -0.2207 | -0.2207 | 4.2e-13 | -0.1476 | 8.9e-13 |
| 5,000 null draws, draw by draw | | | 8.3e-15 | differ (different blocks) | 5.7e-15 |
| Episodes | 10: 6, 6, 16, 6, 11, 25, 14, 25, 23, 10 | same | identical | 10, 7th is 20 | 6: 63, 9, 6, 13, 15, 6, identical |
| Drop Util / Ships / Aero / Steel / BldMt, alpha %/yr | -0.61 / +0.03 / +0.01 / -0.19 / -0.11 | same | 4.6e-14 (t 1.3e-13) | -0.54 / +0.03 / -0.12 / -0.25 / -0.08 | 1.5e-13 (t 1.8e-13) |
| Pass/fail rows (i) / (ii) / (iii) / (iv) | FAIL / FAIL / PASS / FAIL | FAIL / FAIL / PASS / FAIL | identical | FAIL / FAIL / PASS / FAIL | all FAIL, identical |
| Verdict | FAIL, 1 of 4 | FAIL, 1 of 4 | same | FAIL, 1 of 4 | FAIL, 0 of 4, same |

The calendar column is round-1 variant B (A switched off), reproduced to 1e-14 in attribution, 1.0e-16 in D and in every null draw, and 3.7e-19 in the drop-one alphas. It is shown only to confirm that the switch works. The default is the pre-registered reading.

## R2.9 Extra check: size of the two tests on the synthetic null (not about Claude's code)

R12 ran 100 further null seeds (21-120, 200 draws each, no planted effect; `out/r2_null_seeds_d200_all.csv`).

| Statistic | Nominal | Observed (100 seeds) | Reading |
|---|---|---|---|
| Shuffle p <= 0.05 | 5 | 6 (P(>= 6) = 0.38) | Correctly sized. Kolmogorov-Smirnov against uniform: p 0.23 |
| Shuffle p <= 0.10 | 10 | 11 | Correctly sized |
| \|NW(6) t\| above the two-sided 5% t(175) critical value | 5 | 13 (P(>= 13) = 0.0015) | Over-rejects: the sd of t is 1.24 over 120 seeds |
| NW(6) t >= 2 (the (i) bar) | 2.4 | 5 (P(>= 5) = 0.09) | Probably oversized |

This concerns the pre-registered inference (C21), which v2 and the reference share. It is not a coding error in either. The likely cause is that D_t switches regime in blocks of 6 to 63 months, and 6 Newey-West lags do not span that. The calendar shuffle is built from the same blocks and stays correctly sized. The verdict is unaffected: the real alpha is negative, and a PASS needs all four components, including (ii).

## R2.10 Files (round 2)

All in `/home/hashim/projects/GA/project/research/exchange/02_coding_support/checks/`:

- Code:
  - `chatgpt_round2_block.py`: Claude's reply code, verbatim;
  - `chatgpt_code_v2.py`: v1 plus the block, the driver changes and adapters I1-I3; `v1_to_v2_round2.diff`;
  - `chatgpt_code_v1fix.py` and `v1_to_v1fix.diff`: round-1 BUG-1 fix, renamed;
  - `run_v2_real.py`: glue G1-G5 and the `__main__` modes;
  - `run_v2_tests.py`: unit tests one at a time;
  - `checks_first_v2.py`: CF1-CF3 and the N1 contract check;
  - `team_trade_v2.py`: check (b)2;
  - `compare_v2.py`: section R2.8;
  - `pc_null_v2.py`: checks (b)9 and (b)10, plus R12;
  - `mutation_lookahead_v2.py`: R13;
  - `dropin_variant_v2.py`: R14;
  - `manifest_round2.py`.
- Outputs (`out/`):
  - `r2_{test_nonzero,test_calendar,seen_nonzero,seen_calendar,synthetic_nonzero,dropin_test}_*.csv`;
  - `r2_lookahead_*.csv`;
  - `r2_compare_components.csv`, `r2_compare_attribution.csv`, `r2_compare_summary.json`;
  - `r2_checks_first.csv`, `r2_dropin_crossings.csv`, `r2_team_trade.csv`;
  - `r2_positive_control.csv`, `r2_null_seeds_d500_all.csv`, `r2_null_seeds_d200_all.csv`;
  - `r2_mutation_*.csv` and `r2_mutation_summary.csv`;
  - `v2_unit_tests_*.csv`;
  - `manifest_round2.json`: sha256 of all 336 files under `02_coding_support/`. The round-1 `manifest.json` is kept as written.
- Logs: `logs/r2_run01` to `r2_run10`.

Nothing was written to the team repo, `modules/M8_frozen_pre2010/` or `outputs/`. The reference module's bytecode (06:07:47), the `M8_*` tables (06:10:07) and PREREGISTRATION.md (sha256 e926c3ae...0b51) are unchanged. No new `.pyc` was written anywhere.
