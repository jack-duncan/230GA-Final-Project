# M1b_alt_signals: adversarial verification

Verifier script: `modules/M1b_alt_signals/verify/verify_m1b.py` (run: `cd /home/hashim/projects/GA/project/research && uv run python modules/M1b_alt_signals/verify/verify_m1b.py`, about 30 s).
Its output is `modules/M1b_alt_signals/verify/verify_results.csv`: 231 rows, of which 214 pass, 7 are flagged and 10 are info-only.
The script does not import `helpers.py` or `run.py`. It uses only `lib/common.py` (paths, `load_team`) and `lib/team_pipeline.py` (`run_pipeline`, `team_controls`).

## 0. What was done

1. **Module re-run.** `uv run python modules/M1b_alt_signals/run.py` exited 0 in 88 s. The builder said about 3 minutes. All 24 output tables are byte-identical to the copies on disk before the run, so the run is deterministic.
2. **FINDINGS.md does not exist on disk.** The builder says the harness blocked the write. I verified the FINDINGS text that the builder returned (`primary_results`).
3. **Independent rebuild.** The verifier script rebuilds the following from scratch and compares them with the module's CSVs:
   - All five measures, parsed directly from the raw files.
   - The CPI fix, done by averaging the two neighbouring months.
   - The one-month real-time lag, done by shifting the index by one month rather than with `shift(1, freq="ME")`.
   - The Brown-leg rolling-FF3 residual.
   - A from-scratch Original-3m and Original-6m engine: log1p, rolling z, a past-only p80 computed with `np.quantile` in a loop, crossings, holds, the 5% volatility target with cap, hedged P&L, and asset plus overlay turnover costs at 10/5/25 bp charged the next month.
   - A numpy Newey-West regression (Bartlett kernel, 6 lags, no degrees-of-freedom correction).
   - Small-sample p-values, return-aligned ICs, Holm, the placebo rule, crossings and overlap chance, and a look-ahead fuzz test.

## 1. The most decision-relevant numbers, recomputed independently

| # | Number (FINDINGS) | Reported | Recomputed | Verdict |
|---|---|---|---|---|
| 1 | Q1 primary family: 40 estimates, t, p and n (MCCC and CPU, real-time) | primary.csv | max abs diff 0 (estimate, t, p); n identical | CONFIRMED |
| 1a | Min Holm p / min raw p (MCCC purified holdout IC +0.163, t 2.22) | 1.00 / 0.033 | 1.000 / 0.0333; IC 0.1627, t 2.218 | CONFIRMED |
| 1b | Q1 decision (positive holdout alpha with Holm p < 0.05) | unchanged | unchanged | CONFIRMED |
| 2 | Validation alphas with t >= 1.96: EMV env / MCCC / CPU | 4 / 0 / 0 | 4 / 0 / 0; best CPU is O6 at 1.813% (t 1.726) | CONFIRMED |
| 3 | MCCC holdout alpha range and t range; CPU holdout range | -0.56 to -2.91 (t -1.31 to -1.95); -1.62 to +0.36 | -0.558 to -2.910 (t -1.309 to -1.950); -1.623 to +0.358 | CONFIRMED |
| 4 | COVID placebo rule: EMV overall reproduces 4/6 (real-time) and 6/6 (team timing); VIX 3/6 and 3/6 | 4, 6, 3, 3 | 4, 6, 3, 3; all 60 COVID alpha cells match placebo_covid.csv exactly | CONFIRMED |
| 5 | Always-short Brown COVID alpha, and its ratio to EMV env Original 3m | 4.54% (t 1.96); 71% | 4.540% (t 1.961); 0.712, from an independently built benchmark | CONFIRMED |
| 6 | Mar-Apr 2020 Brown residuals, share of EMV env O3 COVID net, min Holm p of the 12 paired tests | -3.33%, -5.91%; 49% (7.93 of 16.08); 0.051 | -3.329%, -5.915%; 0.493 (7.926 of 16.084); 0.0514 | CONFIRMED (numbers); see issue B for interpretation |
| 7 | Crossings 26/25/23/10/14; exact 2/4; ±1m 11/12/9; chance 8.5/8.0/4.8; p 0.195/0.064/0.021 | crossings.csv | identical counts and dates, also from my own engine | CONFIRMED (counts); the chance formula understates coverage, see issue D |
| 8 | Correlation of z with EMV env z, post-2010: MCCC / CPU / VIX / EMV overall | -0.07 / 0.10 / 0.14 / 0.39 | -0.067 / 0.102 / 0.143 / 0.387 | CONFIRMED |

Also recomputed and matching within rounding:

- EMV env corrected-baseline figures:
  - Original 3m validation: 1.62% (t 1.97).
  - Holdout alphas over the matched windows: -1.17% (t -2.08) to 2025-07, -1.04% (t -1.97) to 2025-10, and -2.16% (t -1.90) to 2026-07.
  - Mean validation alpha: 1.45% for EMV env, 0.34% for MCCC and 0.88% for CPU.
- COVID alphas and t-stats, real-time Original 3m:

  | Measure | Alpha | t |
  |---|---|---|
  | EMV env | 6.38% | 3.62 |
  | VIX | 2.41% | 2.03 |
  | EMV overall | 1.65% | 1.29 |
  | CPU | 6.44% | 4.46 |

- COVID alphas excluding Mar-Apr 2020:

  | Measure | Alpha | t |
  |---|---|---|
  | EMV env | 3.48% | 2.68 |
  | CPU | 3.81% | 2.44 |
  | VIX | 2.20% | 1.25 |
  | EMV overall | 1.18% | 0.67 |

- Team baseline Original 3m COVID alpha: 6.03% (t 3.21).
- Every robustness figure quoted in FINDINGS §8 was checked against results_long.csv and bootstrap.csv:
  - team timing
  - level transform
  - MCCC transition composite
  - EMV env share
  - live-window validation
  - post-2010 and full-live samples
  - the four bootstrap CIs
  - the MCCC Continuous-raw minus Original-3m paired result, +1.82% with Holm p 0.048

## 2. Method checks

- **Look-ahead: clean.**
  - For all five measures, the real-time z at t equals the same-month z at t-1 exactly. For MCCC and CPU the same holds for the purified signal and both continuous weights, so the controls are lagged consistently.
  - Fuzz test: I multiplied the MCCC or CPU values by random factors from each of three cut dates (2014-06, 2018-01, 2021-03) onward, and did the same to every macro input (rate10y, wti, cpi, activity). Net returns of all six strategies through cut+1 changed by exactly 0, while later returns did change, so the test has power.
- **Corrected-baseline definition: matches.** My construction reproduces the module's real-time runs exactly: CPI gap filled (exactly one gap after 1990, 2025-10), attention lagged one month, and `team_controls(mac).shift(1)`. It is the same convention as `scratch/audit_battery.py` (attention and controls shifted one month), with the CPI fix added.
- **Engine: clean.**
  - My from-scratch Brown residual equals the pipeline's (max diff 0).
  - My from-scratch Original 3m and 6m net returns for EMV env, MCCC, CPU, VIX and EMV overall equal the pipeline's (max diff 0).
  - So `run_pipeline` handles series with different start dates, and NaN tails after the data ends, correctly.
- **Windows: correct.**
  - The holdout ends are MCCC 2025-07 (n 36), CPU 2025-10 (n 39) and 2026-07 for the rest (n 48). Each is the last data month + 1, which the measure drives under both timings.
  - The MCCC Original rules are live from 2011-02 (138 validation months) and the Pure rules from 2016-02 (78).
- **Annualization and signs: correct.** Alpha and mean are x12 and vol is x sqrt(12). Position = -magnitude x hold. IC is the slope of z(eps_{t+1}) on z(signal_t), and a negative IC favors Short-Brown, as FINDINGS says.
- **Costs: correct.** 10 bp on the asset, 5 bp on Mkt-RF and 25 bp on SMB and HML per unit of turnover, charged at t+1; the from-scratch engine reproduces them exactly.
- **NW lags and p-values: correct.**
  - NW uses 6 lags, Bartlett kernel, no small-sample correction, the same as the team.
  - Two-sided p comes from t(n-4) for alphas and t(n-2) for ICs when n < 60, and from the normal otherwise; the COVID window uses t(20).
  - The team baseline COVID O3 p is 0.0044 under t(20). That is consistent with the audit item that nothing survives Holm under t p-values.
- **Factor construction: not applicable.** The module uses only the team FF3 file. There is no BOND or commodity factor here.
- **Data: clean.**
  - Raw-file parses of EMV env, MCCC, CPU, VIX (monthly mean of daily) and EMV overall equal measures_monthly.csv, with max diff 3.6e-15 for VIX and 0 for the rest.
  - EMV env is identical to the team `attention`. It is 0 in 64.6% of holdout months (31 of 48); the other measures have no zeros.
  - The CPU normalization window runs to 2022-08, but CPU levels are about 40-500, where log1p is nearly scale-invariant. The MCCC level-transform robustness, which is exactly scale-invariant, gives the same conclusion, so index vintage and normalization cannot drive the MCCC result.
- **Ledger: counts confirmed but incomplete.**
  - It has 1664 rows: primary 40, placebo 88, reference 70, robustness 1052 and exploratory 414.
  - All 40 primary test ids are present and no p-value is missing.
  - What is missing is listed in issue F.

## 3. Per-claim verdicts (builder headline bullets)

1. **Q1: no change; "Do not implement" stands and gets stronger; min Holm p 1.00; no significant positive MCCC or CPU holdout alpha.** CONFIRMED.
   - Note that min Holm = 1.00 is mechanical here: 40 x 0.033 > 1.
   - The decision rule needed p < 0.00125 on a 36-39 month holdout, so it could hardly have flipped.
   - The substantive evidence is the sign pattern, which is robust: MCCC is negative in 6 of 6.
2. **Validation alpha is specific to the EMV tracker (4/6 vs 0/6 and 0/6; correlations -0.07 and 0.10).** CONFIRMED. The phrase "specific to the EMV volatility tracker" should read "specific to the EMV tracker family". EMV overall gets a mean validation alpha of 1.07%, against 1.45% for EMV env, with O6 t 2.05, as FINDINGS §8 itself says.
3. **Holdout by measure (MCCC all negative, wrong-sign ICs; CPU near zero; VIX and EMV overall near zero).** CONFIRMED. The largest holdout |t| for VIX and EMV overall is 1.01.
4. **Q2: by the pre-specified rule the climate reading of the COVID gain fails (4/6 and 6/6; VIX 3/6; always-short 4.54%, t 1.96, 71%).** CONFIRMED as a rule outcome. The wording needs qualifying (issue A).
5. **Exception for the 3-month holds, attributed to one pandemic event.** Numbers CONFIRMED; the interpretation is PLAUSIBLE but overreaches (issues A and B).
6. **Crossings (25/23/10/14 vs 26; exact 2 and 4; ±1m 11 and 12 is not above chance; EMV overall 9 vs 4.8, p 0.021).** Counts CONFIRMED. The chance and p figures depend on an approximation (issue D); the qualitative conclusions survive.
7. **FINDINGS.md not written.** CONFIRMED. The file is absent and must be saved (fix 1).

## 4. Discrepancies and required fixes

**Issue A. The Q2 headline and the "exception" are timing-dependent and not stated that way (wording, material).**

- "For the 3-month holds, both placebos fall short" is true only under real-time timing. Under team timing, EMV overall reproduces both 3-month rules:
  - Original 3m: 4.64% (t 2.18), 77% of the EMV env 6.03%.
  - Pure 3m: 3.30%, 53%.
- The rule's "fails" verdict under real-time timing comes entirely from the 6-month and continuous rules (O6, P6, CR, CP). There, the EMV env COVID alpha is itself weak for the 6-month rules: O6 t 1.79 (p 0.089) and P6 t 1.96 (p 0.064) under t(20).
- For the team's headline COVID number (Original 3m), neither volatility placebo reproduces the gain under real-time timing, but CPU does exactly: 6.44% vs 6.38%, paired t -0.06.
- Required: state this in the headline and in §6. Suggested wording: "By the pre-specified rule, fails (EMV overall 4/6, driven by the 6-month and continuous rules). For Original 3m, the placebos fall short under real-time timing (EMV overall reaches 77% under team timing), and the climate-policy index CPU matches it."

**Issue B. "One pandemic event, not climate evidence" overreaches (interpretation, material).**

- The Mar-Apr 2020 share of the Original 3m COVID net return is:
  - 49% under real-time timing;
  - only 23% under team timing (`covid_decomposition.csv`, same_month), where only March 2020 was held.
- Excluding Mar-Apr 2020, the 3-month COVID alphas stay positive for the climate-linked measures and are weaker for the placebos and the signal-free benchmark:

  | Measure, timing | Alpha ex Mar-Apr | t |
  |---|---|---|
  | EMV env, real-time | 3.48% | 2.68 |
  | EMV env, team timing | 4.25% | 2.41 |
  | CPU, real-time | 3.81% | 2.44 |
  | VIX | 2.20% | 1.25 |
  | EMV overall | 1.18% | 0.67 |
  | Always-short Brown | 3.06% | 1.05 |

  The always-short figure is not in FINDINGS.
- The December 2019 crossing is shared with a genuine climate-policy index, which is the one result in the module that is consistent with a climate trigger.
- Required: replace "one pandemic event, not climate evidence" and "one dominant event" with a statement the data support. Suggested: "a single 24-month window with about 13 held months, half of the real-time gain in two crash months, timing-dependent across placebos, exploratory inference (n = 22-24, NW(6)), and no holdout support. It is not a basis for implementation, but it cannot be attributed to the pandemic alone." Report the team-timing share (23%) and the ex-crash benchmark (3.06%, t 1.05).
- A minor imprecision: under real-time timing, EMV env was already short from an earlier crossing (data month 2019-09), which earned January 2020. The December 2019 crossing extends the hold to earn February to April.

**Issue C. The figure `M1b_alt_signals_covid_paths` has a bug (confirmed).**

- The cumulative paths start at 2019-12-31 and are forced to 0 there, but the compounding includes the December 2019 return. That return is +2.95% for EMV env, CPU, EMV overall, MCCC and the benchmark, and 0 for VIX.
- As a result, the EMV env Original 3m path ends at 20.55% instead of the COVID-window 17.09%, which exaggerates its gap over VIX (7.50%).
- Required: compound from 2020-01-31 and prepend a 0 at 2019-12-31. In run.py (§11c), use `r = ...net_return.loc["2020-01-31":"2021-12-31"]` and then add the zero start point. Apply the same fix to the benchmark line.

**Issue D. The crossing-overlap chance approximation understates chance (minor; conclusions unchanged).**

- The expected ±1m overlap is computed as n x (1 - (1 - p)^3), where p is the team crossing rate in the measure's window. Over the full window (p = 26/199) that gives 0.343; it is about 0.34 in the shorter windows too.
- The exact share of months within ±1 of a team crossing is 0.376-0.381, because team crossings cannot be adjacent and there are edge effects.
- With the exact share, the chance counts become 9.4 for MCCC, 8.8 for CPU and 5.3 for EMV overall, and the one-sided binomial p-values become 0.32, 0.12 and 0.040 (instead of 0.195, 0.064 and 0.021).
- MCCC and CPU remain indistinguishable from chance, and EMV overall stays below 0.05.
- Required: use the exact coverage share, or label the figure as an approximation.

**Issue E. `full_mode_comparison.csv` carries misleading pipeline flags.**

- `significant_after_multiple_testing` is True for EMV env Original 3m, EMV env Pure 3m and CPU Original 3m. That flag comes from the pipeline's normal-p Holm on 24-month COVID NW(6) t-stats (audit item 3), placed in a full-sample row (audit item 8).
- `active_months_full` is the overstated count (audit item 6).
- The table is a module deliverable, and a reader could take "CPU Original 3m significant after multiple testing" from it.
- Required: drop both columns, or annotate them in the CSV and in FINDINGS §11 as not valid inference.

**Issue F. The ledger is incomplete.**

- The 20 full-mode paired-bootstrap tests in `full_mode_paired.csv` are not in `tests_ledger.csv`. FINDINGS §8 cites one of them: MCCC Continuous raw minus Original 3m, +1.82%, Holm p 0.048.
- The 40 per-strategy `bootstrap_p` values in `full_mode_comparison.csv` are not in the ledger either.
- The six `CROSS_*` rows store one-sided binomial p-values in the `p_value_two_sided` column. Only the note says one-sided.
- Required:
  - add the paired and per-strategy bootstrap tests (label them robustness or exploratory);
  - either double the one-sided p-values or add a sidedness column.

**Issue G. The recent 12- and 18-month windows are missing from the text (brief requirement).**

- FINDINGS says only that MCCC and CPU lack coverage. It gives no last-12 or last-18 numbers for EMV env or the placebos, although they are in `compact.csv`.
- Required: add one line with the Original 3m real-time figures:

  | Measure | Last 18 | Last 12 |
  |---|---|---|
  | EMV env | -4.05% (t -1.55, p 0.14, n 18); net -4.51% | +1.20% (t 0.30); net -5.21% |
  | VIX | +0.79% (t 0.86) | +0.82% (t 0.90) |
  | EMV overall | -1.56% (t -0.45) | +1.30% (t 0.18) |

**Issue H. Cosmetic text mismatches.**

- **Turnover.** "Discrete rules turn over 2 to 6 times a year, with cost drag at or below 0.6%." The actual range is 1.7-5.8x (1.8-5.8x for the primary and placebo measures), and the maximum drag is 0.63% (EMV env Pure 3m).
- **Runtime.** FINDINGS says "about 3 minutes"; the measured runtime is 88 s.

**Issue I. Pre-specification is unverifiable (note, no fix possible).** `research/` has no version control, so the claim that the docstring was "written before any alternative measure was run" cannot be checked. The rule choices (50% threshold, 4 of 6) are reasonable. The 4-of-6 threshold is met exactly by EMV overall under real-time timing.

## 5. Bottom line

- Every reported number I recomputed matches to rounding, and there is no look-ahead, timing, window, sign, cost or p-value error.
- The Q1 conclusion (a climate-concern measure does not rescue the strategy, and "Do not implement" stands) is solid.
- Four items are required before the module feeds the report:
  - The Q2 narrative must be softened (issues A and B).
  - The COVID-paths figure must be fixed (issue C).
  - The ledger and the full-mode flag columns must be fixed (issues E and F).
  - FINDINGS.md must be saved to disk.

## Round 2

This round verifies the fixer's corrected FINDINGS.md (returned as text; it is not on disk yet) and the revised run.py outputs.

- **Round-2 script:** `modules/M1b_alt_signals/verify/verify_m1b_r2.py`.
  - Run: `cd /home/hashim/projects/GA/project/research && uv run python modules/M1b_alt_signals/verify/verify_m1b_r2.py` (about 21-30 s).
  - Output: `modules/M1b_alt_signals/verify/verify_results_r2.csv`, 478 rows: 460 pass, 4 flagged, 14 info-only.
  - Round-1 `verify_results.csv` is left untouched.
- **What the script contains:**
  - The round-1 script, with its claims and column names updated to the corrected text and the revised outputs.
  - A new section 9 with a check for every number that changed or was added.
  - EMV env share and MCCC transition, rebuilt from raw files.
  - A cell-by-cell comparison of the corrected FINDINGS tables (§5, §6 real-time, §6 team timing, §6 ex-crash and §7 crossings) against independently computed values.
  - Like round 1, it does not import `helpers.py` or `run.py`.

### R2.0 What was done

1. **Module re-run.** `run.py` exited 0 in 51.9 s wall time, which is consistent with FINDINGS' "about one minute (measured 45 s and 68 s)". Every output table is byte-identical to the copy on disk before the re-run, so the run is still deterministic.
2. **Round-1 script re-run unmodified.** It stops at line 428 with an AttributeError, because crossings.csv renamed `p_overlap_ge_observed_if_independent`. That rename is part of the Issue D fix, so the stop is expected. The same checks, with column names and claims updated, all pass inside `verify_m1b_r2.py`.
3. **Diff against the round-1 output snapshot.**
   - Byte-identical (17 of 24 tables): primary, placebo_covid, the two alpha grids, ic, bootstrap, compact, signal_availability, measures_monthly, crossings_events and full_mode_paired (.csv and .tex where both exist).
   - Changed as intended:
     - covid_decomposition: new minus-benchmark columns.
     - crossings (.csv and .tex).
     - full_mode_comparison.
     - key_numbers.
     - results_long: 2 added rows for the benchmark's last 12 and last 18 months; all 1158 existing rows identical.
     - tests_ledger: all 1664 round-1 rows kept; exactly 7 intended p changes (6 CROSS rows now two-sided, and BOOT_MCCC_realtime_P3_holdout moved from 0 to the 2/5000 bound); 236 new rows.
   - New: recent (.csv and .tex) and covid_attribution.tex.
   - So none of the primary, placebo or robustness estimates moved.
4. **Figure.** The corrected `M1b_alt_signals_covid_paths.png` starts at 0 on 2019-12-31 and ends at 17.09% (EMV env. Original 3m), 7.50% (VIX) and 14.21% (always-short). The Mar-Apr shading covers the March and April return segments.

### R2.1 Status of the round-1 required fixes

| Item | Status | Evidence |
|---|---|---|
| FINDINGS.md not on disk | RESOLVED once the orchestrator writes it | The full text was returned. The FINDINGS.md now on disk (05:44) is still the round-1 text and must be replaced, with the round-2 text fixes below applied. |
| A. Q2 headline and "exception" timing-dependent | RESOLVED, one new error | The headline, §6 and §9 adopt the suggested wording and add the team-timing table; all 24 team-timing cells match my values. The new sentence on paired significance is wrong for VIX; see R2-1. |
| B. "One pandemic event" overreach | RESOLVED | The phrase is removed. I reproduced the team-timing Mar-Apr share (23%: 2.71 of 11.87), the ex-crash table under both timings (12 cells) and the ex-crash benchmark (3.06%, t 1.05). The hold timing is now stated correctly: real time holds 2019-11 to 2020-04, from crossings in data months 2019-09 and 2019-12; team timing holds 2019-10 to 2020-03, so of the crash months only March. |
| C. covid_paths compounding bug | RESOLVED | `covid_path` compounds 2020-01 to 2021-12 and prepends 0. My own compounding gives 17.09%, 7.50% and 14.21%, and key_numbers matches for all 11 paths (max diff 0). My check of the old value (20.55%) confirms what was fixed. |
| D. Crossing chance approximation | RESOLVED | The exact coverage share (0.376 to 0.381), chance counts, one- and two-sided binomial p, circular-shift p, Jaccard and the val/hold/COVID counts all equal my own computation for all 7 measures. The 63 text-table cells in §7 have 0 mismatches. |
| E. Misleading full-mode flag columns | RESOLVED | Both columns are dropped. `months_held_full` from my from-scratch engine equals the CSV for Original 3m and 6m on all 5 measures; EMV env. Original 3m is 75 of 199. |
| F. Ledger incomplete, one-sided p | RESOLVED | See the ledger checks in R2.2. |
| G. Recent windows missing | RESOLVED for real-time timing; the added text has two errors | All 50 rows of recent.csv (alpha, t, p, net, n) equal my values exactly, and the 8 Original 3m text rows match. Two new errors are in R2-2 and R2-3. |
| H. Turnover and runtime text | RESOLVED | Discrete turnover is 1.7 to 5.8x (1.8 to 5.8x for the team, primary and placebo measures), with maximum drag 0.63% (EMV env. Pure 3m). Continuous turnover is 0.7 to 1.5x with drag 0.07% to 0.16%. Runtime about one minute. |
| I. Pre-specification unverifiable | ACKNOWLEDGED | Stated in §2 and §10. No round-1 copy of run.py exists, so "docstring unchanged" cannot be checked either; the docstring still matches the round-1 description. |
| Wording "EMV tracker family" | ADOPTED | Headline, §5 and §9. |

### R2.2 Changed or new numbers, recomputed independently

All were recomputed with my own NW(6) and p-values. The always-short benchmark is my own from-scratch construction. Original 3m and 6m use my from-scratch engine; the other rules use pipeline returns built from my own inputs.

| Claim (corrected FINDINGS) | Reported | Recomputed | Verdict |
|---|---|---|---|
| §5 primary table, 36 cells | alpha (t) | max diff within 2-dp rounding | CONFIRMED |
| §6 real-time COVID table incl. the two paired columns, 42 cells; team-timing table, 24 cells | alpha (t) | within rounding | CONFIRMED |
| Reproduced strategies | EMV overall: O6, P6, CR, CP (real time) and 6 of 6 (team); VIX: P6, CR, CP under both timings | identical lists | CONFIRMED |
| Ratios to EMV env. | O3: VIX 38%, EMV overall 26%; P3: 8% and 40%; team O3: 77%, 53%, 32%, 12%; CPU team 1.05; CR: 0.62 / 0.83 / 0.76 / 1.06 | all 13 within 0.005 | CONFIRMED |
| EMV env. O6 and P6 COVID | t 1.79 (p 0.089), t 1.96 (p 0.064) | same | CONFIRMED |
| EMV env. P6 real-time is the always-short position in COVID | short in 24 of 24 | 24 of 24; net identical to my benchmark (max diff 0) | CONFIRMED |
| Paired EMV env. O3 minus always-short, COVID | +1.84% (t 0.87, p 0.39) real time; +1.49% (t 0.45) team | +1.84% (t 0.871, p 0.394); +1.49% (t 0.453) | CONFIRMED |
| Paired CPU O3 minus always-short, COVID | +1.90% (t 1.02) | +1.90% (t 1.017) | CONFIRMED |
| Paired minus always-short, ex Mar-Apr | EMV env. +0.42% (t 0.18); CPU +0.75% (t 0.44) | same | CONFIRMED |
| All 168 minus-benchmark cells in covid_decomposition.csv, and all 86 rows' sums, shares and ex-crash alpha/t/n | CSV | max diff 0. The 2 degenerate cells (EMV env. P6 real-time, both windows) are identically 0 and stored as t 0, p 1. | CONFIRMED |
| Always-short alpha as a share of team-timing EMV env. O3 | 75% | 0.753 | CONFIRMED |
| Team-timing paired EMV env. minus EMV overall, O3 | +1.39% (t 0.87) | +1.39% (t 0.868) | CONFIRMED |
| EMV env. minus CPU, O3 real time | paired t -0.06 | -0.06 | CONFIRMED |
| Hold timing | EMV env. real time short 2019-11 to 2020-04; team only March 2020; VIX and EMV overall real time April only, team both months; MCCC real time both months; CPU and EMV env. cross in data month 2019-12, VIX and EMV overall in 2020-02 | all identical | CONFIRMED |
| Recent windows, Original 3m real time (8 rows) | e.g. EMV env. last 18 -4.05% (t -1.55, p 0.14, n 18), net -4.51% | identical; EMV env. share equals EMV env. for O3 (max diff 0) | CONFIRMED |
| "The only recent-window \|t\| above 2" | 1 (EMV env. CR last 18) | 5 cells under real-time timing | WRONG (R2-2) |
| §9 "no \|t\| above 1.6 for Original 3m" in the last 12 and 18 months | below 1.6 | 1.55 under real-time timing; 4.75 under team timing | TRUE ONLY UNDER REAL-TIME TIMING (R2-3) |
| §6 "paired differences ... nominally significant only under real-time timing" | none significant under team timing | EMV env. minus VIX under team timing: O3 t 2.34 (p 0.030), P3 t 2.15 (p 0.044) | WRONG FOR VIX (R2-1) |
| Crossings §7 | chance 9.4 / 8.8 / 3.8 / 5.3 / 10.9 / 6.4; binomial one-sided 0.32 / 0.12 / 0.56 / 0.040 / 0.002 / 0.29; circular 0.32 / 0.059 / 0.56 / 0.035 / 0.010 / 0.32; EMV overall two-sided 0.052 / 0.071; Jaccard 0.24 / 0.34 / 0.34 | identical from my own coverage, own pmf-sum two-sided binomial and own circular shift. EMV env. share and MCCC transition crossing dates from my from-scratch engine equal the pipeline's. | CONFIRMED |
| Full-window bootstrap | 0 of 30 attention p < 0.05; smallest EMV overall O6 0.064; MCCC CR minus O3 +1.82%, p 0.018 | same. My re-implementation of the circular block bootstrap reproduces the paired result and the four holdout CIs in §8. | CONFIRMED |
| §5 and §8 ICs, level transform, transition composite, share variant | e.g. EMV env. validation ICs -0.024 / -0.045 / -0.147 / -0.162; MCCC level holdout IC 0.121 to 0.216; transition purified 0.267 (t 2.92) | all match; level-transform figures come from my own `attention_transform="none"` runs | CONFIRMED, except CPU holdout IC minimum -0.0295, which rounds to -0.029, not -0.030 (R2-4) |
| Other §3 and §4 figures | EMV env. share z correlation 0.88; team baseline O3 COVID net 5.94% | 0.88; 5.94% | CONFIRMED |
| Ledger | 1900 rows: primary 40, placebo 88, reference 82, robustness 1102, exploratory 588 | same. New rows: COVIDB 168, FULLBOOT 40 (30 robustness, 10 reference), FULLPAIR 20, CROSSPERM 6, and 2 benchmark reference rows. 3 rows at the 0.0004 bound. No missing statistic or p. Test ids unique. The primary id set is unchanged from round 1. CROSS and CROSSPERM two-sided p equal my own. All 168 COVIDB t, p and n equal my own (max diff 0). | CONFIRMED |

### R2.3 Remaining required fixes (text only; no code or number changes needed)

**R2-1. §6, the paired-significance sentence is wrong for VIX (material to the placebo narrative).** Under team timing, EMV env. minus VIX stays nominally significant for both 3-month rules:

| Rule | Paired alpha | t | p |
|---|---|---|---|
| Original 3m | +4.08% | 2.34 | 0.030 |
| Pure 3m | +5.53% | 2.15 | 0.044 |

These values are in placebo_covid.csv (`emv_minus_measure_*`, same_month) and match my recomputation. Only against EMV overall does significance vanish under team timing (t 0.87 and 1.29).

- Replace: "The paired differences EMV env. minus placebo are nominally significant only under real-time timing: Original 3m t 2.67 vs VIX and 3.22 vs EMV overall; Pure 3m t 2.70 and 2.75. After Holm within the 12 real-time paired tests none survives (smallest Holm p 0.051; placebo_covid.csv holm_p_paired_placebo_family). Under team timing the Original 3m difference vs EMV overall is +1.39% (t 0.87)."
- With: "Real-time timing: the paired differences EMV env. minus placebo are nominally significant for both 3-month rules (Original 3m t 2.67 vs VIX and 3.22 vs EMV overall; Pure 3m t 2.70 and 2.75), but after Holm within the 12 real-time paired tests none survives (smallest Holm p 0.051; placebo_covid.csv holm_p_paired_placebo_family). Team timing: against EMV overall the differences are not significant (Original 3m +1.39%, t 0.87; Pure 3m t 1.29), while against VIX they remain nominally significant (Original 3m +4.08%, t 2.34, p 0.030; Pure 3m +5.53%, t 2.15, p 0.044; placebo_covid.csv emv_minus_measure_*)."

**R2-2. §5 recent windows, the "only |t| above 2" sentence is wrong.** Under real-time timing, recent.csv has five cells with |t| > 2, all of them losses.

- Replace: "The only recent-window |t| above 2 is a loss: EMV env. Continuous raw over the last 18 months, -1.74% (t -2.19, p 0.046, exploratory)."
- With: "Under real-time timing, five recent-window cells have |t| above 2, all of them losses (recent.csv, exploratory): EMV env. Continuous raw and Continuous pure over the last 18 months (-1.74%, t -2.19, p 0.046; -1.99%, t -2.59, p 0.021), the same two rules for the EMV env. share variant (-1.64%, t -2.33; -2.07%, t -2.64), and EMV overall Pure 6m over the last 12 months (-8.73%, t -2.21, p 0.058)."

**R2-3. §9 overstates "add nothing"; §5 omits the team-timing recent result.** Under the team's own timing, EMV env. Original 3m loses heavily in both recent windows. Team timing is same-month, which I confirmed is identical to the team baseline for Original 3m (alpha diff 0). My from-scratch engine reproduces these figures exactly; they are in results_long.csv, timing same_month and team_baseline.

| Window | FF3 alpha | t | p | Net |
|---|---|---|---|---|
| Last 18 months | -10.82% | -4.75 | 0.0003 | -8.10% |
| Last 12 months | -11.31% | -2.68 | 0.028 | -8.84% |

This strengthens "Do not implement", but the text as written is true only under real-time timing.

- §9, replace: "The last 12 and 18 months add nothing (no |t| above 1.6 for Original 3m)."
- With: "The last 12 and 18 months add no support: under real-time timing no Original 3m |t| exceeds 1.6, and under the team's own timing EMV env. Original 3m lost -10.82% alpha (t -4.75) over the last 18 months and -11.31% (t -2.68) over the last 12."
- §5, add after the recent-window table bullets: "Under the team's same-month timing (identical to the team baseline for Original 3m), EMV env. Original 3m earns -10.82% alpha (t -4.75, p 0.0003; net -8.10%) over the last 18 months and -11.31% (t -2.68, p 0.028; net -8.84%) over the last 12 (results_long.csv, timing same_month, periods last18 and last12; exploratory)."

**R2-4. §5 ICs, rounding (cosmetic).** The CPU holdout IC minimum is -0.0295 (Continuous weight pure, ic.csv).

- Replace: "CPU holdout ICs are near zero (-0.030 to 0.065)."
- With: "CPU holdout ICs are near zero (-0.029 to 0.065)."

**R2-5. §4, the description of this verification is slightly overstated (minor).** My from-scratch engine covers the Original 3m and 6m rules. The Pure and Continuous rules and the ICs were recomputed with my own statistics on pipeline signals and returns built from my own inputs.

- Replace: "The verifier's independent from-scratch engine reproduces every primary estimate exactly (VERIFY.md)."
- With: "The verifier's independent statistics reproduce every primary estimate exactly, and its from-scratch engine reproduces the Original 3m and 6m net returns exactly (VERIFY.md)."

### R2.4 Notes (no fix required)

- **Circular-shift convention.** The permutation uses shifts 1 to M-1 and excludes the identity arrangement. The usual convention includes it, which gives one-sided p of:
  - 0.040 for EMV overall (instead of 0.035);
  - 0.063 for CPU (instead of 0.059);
  - 0.015 for EMV env. share (instead of 0.010);
  - 0.32 for MCCC (unchanged).

  No conclusion changes.
- **Boundary case.** Under team timing, VIX Original 6m reaches 49.0% of the EMV env. alpha, just under the 50% threshold. VIX's 3 of 6 under team timing is therefore also near the boundary, alongside the 4-of-6 boundary already noted in §10.
- **Accurate as stated.** In §12, "a copy of the verifier's script ... passes all 211 value checks" is accurate as 211 of 217. The 6 misses are the round-1 text claims and the ledger growth, as the fixer says.
- **No other check failed.** The checks carried over from round 1 (look-ahead fuzz, engine equality, data parses, windows, primary family, Holm, placebo rule, benchmark) all pass on the revised outputs.

### R2.5 Bottom line (round 2)

- All nine round-1 required fixes are resolved or acknowledged. The code and outputs changed only where intended, and every changed or new number I recomputed matches.
- No estimate, window, timing or inference changed. The Q1 conclusion ("Do not implement" stands) and the Q2 rule outcome (fails, 4 of 6, boundary) are unchanged.
- Four text corrections remain before FINDINGS.md is saved and feeds the report:
  - R2-1: the paired-significance sentence vs VIX.
  - R2-2: the count of recent-window |t| > 2.
  - R2-3: the "add nothing" qualifier, plus the team-timing recent result.
  - R2-5: the description of the verification.
- R2-4 is cosmetic.
- None of them changes the verdict. R2-3 strengthens it.
- The FINDINGS.md currently on disk is the stale round-1 text and must be overwritten.
