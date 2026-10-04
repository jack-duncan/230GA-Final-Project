# Replication of the team pipeline and code audit

Library: `/home/hashim/projects/GA/project/research/lib/team_pipeline.py`
Tests: `/home/hashim/projects/GA/project/research/lib/test_team_pipeline.py` (14 tests, all pass, about 20 s)
Source ported: `230GA-Final-Project/notebooks/climate_alpha_analysis.py` and `macro_state_dependence.py` at commit 08e7d31.

## 1. How reproduction was checked

**Step A. Can the team's committed tables be regenerated from the team code?**
I copied the clone without `.git` to `research/scratch/team_copy` and ran both scripts there with the research env (`MPLBACKEND=Agg uv run --project research python notebooks/...`). The only missing package was `ipython` (added with `uv add ipython`). numpy 2.5.3, pandas 3.0.6 and scipy 1.18.1 match the team `uv.lock` exactly.

| Regenerated file vs committed | max abs numeric diff | notes |
|---|---|---|
| comparison_table.csv | 3.8e-15 | strategy names, column order and the Holm flag identical |
| comparison_table.tex | 0 | byte-identical |
| macro_state_slopes.csv | 1.9e-14 | |
| macro_state_slopes_by_period.csv | about 1e-15 | |

The CSVs differ from the committed ones only in the last printed digit (BLAS rounding across machines). Runtime of the team scripts: 28.6 s and 7.9 s.

**Step B. Library vs committed tables** (`test_comparison_table_matches_committed`, `test_macro_state_tables_match_committed`). Every numeric cell of `comparison_table.csv` matches to 3.8e-15 (tolerance 1e-9). `macro_state_slopes.csv` and the by-period table match to 3.1e-14.

**Step C. Library vs every intermediate object of the team script** (`test_against_team_script_objects`). `scratch/capture_team_globals.py` runs the team scripts in the copy via `runpy` and pickles their globals to `scratch/team_reference.pkl`. Against a same-machine team run:
- position, gross return, net return and turnover of all 8 strategies: bitwise identical (max diff 0.0);
- rolling betas, hedged returns and residuals of all three assets: bitwise identical;
- attention z, p80 states, continuous weights: identical; purified attention and its ridge prediction: max diff 9e-16;
- the 48-row per-period table, 32-row claims table, bootstrap table, paired bootstrap table, turnover, implied lambda, sensitivity, unconditional and robustness tables: 0.0; IC table: 7e-16;
- placebo draws with 300 reps and seed 11: identical, P(placebo >= real) = 0.12.

**Step D. writeup.pdf** (`test_writeup_table1`, `test_writeup_text_claims`). All 32 Table 1 cells (validation and holdout; net return, Sharpe, FF3 alpha, t for the four discrete strategies) reproduce at two decimals. The COVID numbers in the text (5.94%, 6.03%, t = 3.21; 7.41%, 5.23%, t = 2.07) also reproduce, as do: 2 of 32 claims surviving Holm (both COVID), macro R-squared of 6.24% vs 0.83%, and raw-spread HML loadings of -0.24 and -0.35.

Only the slow pandas loops were rewritten: the rolling OLS, the walk-forward ridge and the per-row `.loc` assignments now use numpy indexing. The `lstsq` and `solve` calls run on identically built arrays, and the bootstrap uses the same RNG stream as the team code.

## 2. API

```python
import sys; sys.path.insert(0, '/home/hashim/projects/GA/project/research/lib')
from team_pipeline import run_pipeline, team_legs, team_controls
from common import load_ff5_mom, load_fred, load_cpu, load_team

res = run_pipeline()                          # exact team defaults
res["comparison_table"]                       # == committed comparison_table.csv

# Christhian's tests: 8 and 8 legs, FF5 + UMD + commodity hedge, uniform costs, cheap mode
fac = load_ff5_mom().join(load_fred("PALLFNFINDEXM").pct_change().rename("COM"))
g8, b8 = team_legs(8)                         # warns: Hardw/MedEq tie at the 8th Green slot
res = run_pipeline(green=g8, brown=b8, factors=fac,
                   factor_cols=("Mkt-RF", "SMB", "HML", "RMW", "CMA", "UMD", "COM"),
                   eval_factor_cols=("Mkt-RF", "SMB", "HML"),   # optional; default = factor_cols
                   cost_bps_uniform=10, bootstrap_reps=200)

# replacement attention series through the identical z / p80 / purification / continuous-weight machinery
res = run_pipeline(attention=load_cpu(), bootstrap_reps=0)
```

Signature:
```
run_pipeline(industries=None, factors=None, macro=None, green=None, brown=None,
             factor_cols=("Mkt-RF","SMB","HML"), attention=None, costs=None, cost_bps_uniform=None,
             bootstrap_reps=5000, seed=230, eval_factor_cols=None, controls=None,
             attention_transform="log1p", placebo_reps=0, macro_states=True, paired=True, extras=True,
             **cfg) -> dict
```
- `industries`: industry returns, decimal, month-end index (default: team FF49 file, which is Ken French VW). `factors`: factor columns plus `RF` (default: team FF3). `macro`: team macro file layout.
- `costs`: `{"asset": r, "Mkt-RF": r, "<factor>": r, "other_factor": r}` as decimals per unit of turnover. The default is the team's 10bp asset, 5bp Mkt-RF and 25bp for every other factor. `cost_bps_uniform=5|10|25` applies one rate to the asset leg and every overlay factor, and overrides `costs`.
- `attention`: any `pd.Series`. It is coerced to month-end on a contiguous monthly grid, then transformed (`log1p` by default; `"log"`, `"none"` or a callable also work), rolling-z scored, thresholded, purified and turned into continuous weights. `controls` replaces the purification controls; the default is `team_controls(macro)`.
- `**cfg` overrides any field of `Config`: `beta_window, residual_vol_window, annual_vol_target, position_cap, z_window, z_min_periods, tail_q, tail_min_history, holds, macro_window, min_macro_obs, ridge, cont_floor, cont_halflife, cont_min_history, traded ("Brown leg"|"Green leg"|"Green-Brown"), direction, nw_lags, bootstrap_block, full_start, full_end, holdout_start, covid_start, covid_end, placebo_seed, state_min_months`.
- Cheap mode: `bootstrap_reps=0` sets the bootstrap CI and p columns to NaN. Adding `extras=False, paired=False, macro_states=False` also skips the side tables.

Returned dict:
- `legs`: green/brown lists and return series (`green_ret`, `brown_ret`, `green_minus_brown`, `green_excess`, `brown_excess`).
- `models[asset]` for "Green-Brown", "Green leg" and "Brown leg": `return, betas, intercept, hedged, epsilon`.
- `signals`: `attention_input, raw, controls, prediction, pure`, and for each of raw and pure: `threshold_*, state_*, cross_*, hold_*` (a dict keyed by hold length) and `w_*` (continuous weight).
- `strategies[name]`: DataFrame with `position, gross_return, cost` (charged that month), `net_return, turnover, cost_incurred` (trade at t), `asset_turnover, overlay_turnover`. The names match the team's, e.g. "Pure | Short Brown hold 6m" and "Benchmark | Always-short Brown".
- Tables: `comparison_table, period_table` (every strategy x 8 team periods, with loadings and t for every eval factor), `ic_table` (4 signals x 3 windows), `claims_table` (Holm over 32 claims), `bootstrap_table, paired_table, unconditional, robustness, diagnostics, turnover_table, lambda_table, sensitivity, macro_state_table, macro_state_by_period`, plus `placebo` when `placebo_reps > 0`.
- `config, cost_rates, timings`.

Building blocks exposed: `rolling_factor_model, newey_west_regression, rolling_z, expanding_threshold, expanding_tail, rolling_oos_prediction, ridge_predict, team_controls, build_signals, cross_and_holds, expanding_percentile_rank, continuous_conditioning_weight, state_position, continuous_position, asset_strategy_returns, resolve_costs, period_stats, all_period_stats, information_coefficient, circular_block_bootstrap` (alias `bootstrap`), `paired_bootstrap_improvement, holm_bonferroni, holm, team_legs, macro_state_tables, state_slopes, team_states, placebo_test, macro_r_squared`.

## 3. Runtime (WSL2, warm imports, median of 3)

| Call | Time |
|---|---|
| `run_pipeline()` (default, 5000 bootstrap reps, all tables) | 1.9 s (up to 3.3 s under load) |
| `run_pipeline(placebo_reps=300)` (everything the team notebook computes) | 7.0 s |
| `run_pipeline(bootstrap_reps=200)` | 1.5 s |
| `run_pipeline(bootstrap_reps=0, extras=False, paired=False, macro_states=False)` | 1.2 s |
| Team scripts, for reference | 28.6 s + 7.9 s |

About 70% of a cheap run is spent on the roughly 150 Newey-West regressions in the period tables.

## 4. Audit: verified issues, ordered by impact on conclusions

Every item below was checked by running code. Scripts: `scratch/audit_attention.py`, `scratch/audit_battery.py`, `scratch/audit_cpi_holm.py`, `scratch/writeup_claims.py`.

1. **The attention series is mostly zeros in the holdout.** The FRED series EMVENRGYENVREG (identical to the team's `attention`, same-month alignment confirmed) is exactly 0 in 31 of 48 holdout months (65%). The share is 12 of 151 in validation (8%) and 6 of 240 in 1990-2009 (2.5%). In the holdout, a zero month has z between -1.39 and -0.59, and every p80 month has attention > 0. The holdout therefore tests a different, near-binary signal ("was any article counted this month"), not the validated one. This weakens the holdout as a test of the thesis, in either direction.

2. **A missing CPI print (Oct 2025, the government shutdown) explains the entire Pure-vs-Original holdout gap.** The writeup says no missing values matter, but this one does. The NaN CPI makes both inflation controls NaN, so the purified signal is NaN in Nov and Dec 2025 and the Nov 2025 crossing is lost. With CPI linearly interpolated, the Pure hold windows in the holdout become identical to the Original ones:
   - Pure 3m holdout: -2.17% (t -1.93) becomes -3.82% (t -2.19);
   - Pure 6m holdout: -3.04% (t -1.94) becomes -2.14% (t -1.66);
   - last-12m Pure 3m: -2.25% becomes -8.84%.

   The writeup's statement that purified variants "lose somewhat less in the holdout, a small point in favor of macro purification" is an artifact of this data gap. The Pure continuous weight is also forced flat for those two months.

3. **"2 of 32 survive Holm" does not survive a small-sample correction.** Both survivors are 24-month COVID regressions, and their p-values come from a normal distribution applied to NW(6) t-stats. With t(n-4) p-values, 0 of 32 survive (smallest Holm p = 0.119). The COVID t is also unstable in the lag choice:
   - Original 3m: 2.36 with OLS standard errors, 2.70 with 3 lags, 3.21 with 6 lags, 4.00 with 12 lags;
   - Continuous raw: 1.63, 2.87, 3.28, 4.43.

   HAC with 6 lags on 24 observations is unreliable. This only strengthens "Do not implement".

4. **The continuous variant's "improvement" is mostly de-leveraging.** Its mean |position| since 2010 is 0.14-0.16, against 0.26-0.47 for the discrete rules, so its lower vol, drawdown and holdout loss are largely mechanical. On holdout Sharpe, Continuous raw (-0.60) is worse than Original 6m (-0.49). After scaling each continuous strategy to its comparator's full-sample volatility, the holdout paired-bootstrap p-values rise:

   | Pair | unscaled p | vol-matched p |
   |---|---|---|
   | Continuous raw vs Original 3m | 0.014 | 0.062 |
   | Continuous raw vs Original 6m | 0.072 | 0.829 |
   | Continuous pure vs Pure 3m | 0.031 | 0.145 |
   | Continuous pure vs Pure 6m | 0.023 | 0.148 |

   The claim that it "loses 75-85% less" compares strategies at different risk levels.

5. **Timing assumption for attention (sensitivity; release timing not verifiable offline).** The code trades at the close of month t on EMV for month t. If the value only becomes available after month-end, the correct rule lags the signal one month. I ran that by shifting the attention and control inputs one month, which shifts every signal by exactly one month:
   - Original 3m full-sample: net 0.07% (t 0.11) becomes 0.73% (t 1.04);
   - Pure 3m validation t: 1.50 becomes 2.01;
   - Pure 6m holdout: -3.04% (t -1.94) becomes -2.00% (t -1.24);
   - Continuous pure holdout: -0.48% becomes 0.00%.

   The verdict is unchanged, but the Table 1 figures depend on this assumption.

6. **`active_months` is overstated.** It counts months with a nonzero net return, which includes the month after each exit, when only the exit cost is charged.

   | Strategy | reported | months actually holding a position |
   |---|---|---|
   | Original 3m | 96 | 75 |
   | Pure 3m | 104 | 81 |
   | Original 6m | 140 | 128 |
   | Pure 6m | 150 | 138 |

7. **Emissions file limits.**
   - Coverage is 41 of 49 industries; Oil, Chips, FabPr, Gold, Hshld, LabEq, Other and Toys are missing.
   - A single static snapshot ranks industries for the whole sample. That is mild look-ahead in leg formation, and I cannot quantify it without historical intensities.
   - Some intensities are exact duplicates (Hardw = MedEq = 0.0126581; Clths = Txtls; Beer = Food = Smoke = Soda), which suggests several FF industries were mapped to one NAICS factor. For 8-and-8 legs the 8th Green slot is a tie between Hardw and MedEq, decided by sort order; `team_legs` now warns about it.
   - Coal (0.163) ranks below Mines, Trans and Chems, so it is not Brown even at N = 8.

8. **Writeup text numbers slightly off** (Table 1 itself is exact).

   | Claim | Writeup | Code output |
   |---|---|---|
   | Continuous vs discrete volatility cut | 55-65% | 52-67% |
   | Holdout loss cut | 75-85% | 70-84% |
   | Traded HML loading | -0.05 to -0.06 | -0.040 to -0.061 |

   In `comparison_table`, `significant_after_multiple_testing` is True for Original 3m and Continuous raw only because of their COVID-window claims, even though the flag sits in a full-sample row.

9. **IC window boundary (negligible).** The windows filter on the signal date, so the validation IC includes the Aug 2022 return, which belongs to the holdout, and the holdout IC omits it. Aligning the windows on the return date moves every IC by at most 0.008 and every t by at most 0.11.

10. **Cost timing (negligible).** The cost of a trade at t is deducted in t+1, and the final trade's cost is never charged. Deducting it in the same month changes full-sample annual net by under 0.001 pp and holdout annual net by at most 0.04 pp.

11. **Data vintage (negligible).** The team FF49 file is Ken French value-weighted, not equal-weighted. Against the Aug 2026 download, 113 cells differ, mostly in Jul 2026 non-leg industries (PerSv by 7 pp). FF3 differs by at most 4 bp. Rerunning on the current vintage moves comparison-table cells by at most 1e-5 and t-stats by at most 0.005.

**Checked and clean:**
- A look-ahead fuzz test randomized every input (industries, factors, macro) after 2012-06, 2016-12 and 2020-03; signals and monthly strategy series up to each date changed by exactly 0 (kept as `test_no_lookahead`).
- The rolling hedge uses betas estimated through t on t+1 returns.
- Annualization (12 x mean, sqrt(12) x std) is correct.
- The Holm implementation is correct.
- The bootstrap p-value is a valid percentile-interval inversion.
- FF49 portfolios include dead firms, so there is no survivorship bias at the industry level; the survivorship-like concern is emissions coverage (item 7).
- The writeup's check at 12 and 18 lags holds: Table 1 signs are unchanged, validation Pure 6m t is 2.45 and 2.44, and holdout t-stats get more negative (Pure 6m: -2.12 and -2.78).

**Design notes (not bugs):**
- Only the Brown leg is traded. The Green leg model is built but never used in a strategy.
- The "Buy-and-hold Green-Brown" benchmark is unhedged, not vol-targeted and cost-free, so its row is not like-for-like with the others.
