# M1_signal_audit: verification report

Verifier script: `modules/M1_signal_audit/verify/verify_m1.py`. It does not import `run.py` or `helpers.py`.
Output: `modules/M1_signal_audit/verify/verify_results.csv`, 120 rows, each with a status of match, MISMATCH or info.

Run it with:

```
cd /home/hashim/projects/GA/project/research && uv run python modules/M1_signal_audit/verify/verify_m1.py
```

It takes about 3 seconds.

## What I did

**Module run.** `run.py` executes in about 18 seconds. A second run reproduced every `outputs/tables/M1_signal_audit_*` file byte for byte.

**FINDINGS.md is missing.** It is not on disk because the builder's Write was blocked. I checked the FINDINGS text from the builder's `primary_results` against the CSVs.

**Independent recomputation.** Only the `common.py` loaders were reused (team files, MCCC, CPU). Everything else was rebuilt from scratch:
- The raw FRED CSVs (EMV_env, EMV_overall, daily VIX) are read directly.
- These are hand-written:
  - Newey-West (Bartlett) HAC; it matches statsmodels to 4 decimals.
  - The rolling z-score.
  - The past-only 80th-percentile threshold.
  - The real-time AR(1) shock.
  - The rolling FF3 hedge.
  - The IC and Holm adjustment.

**Result.** 97 of 105 numeric and text comparisons match to rounding. The 8 mismatches and the overreach items are listed below.

## Per-claim verdicts

| # | Claim (builder) | Builder | Verifier | Verdict |
|---|---|---|---|---|
| H1 | Team `attention` = FRED EMVENRGYENVREG | 500 months, 0 differences | 500 months, 0 differences, 0 one-sided months (raw FRED file) | Confirmed |
| H2a | Joint R2 of z_EMV_env on z_VIX + z_EMV_overall | 0.169, n = 405, F = 27.1, p = 8.8e-12 | 0.169, n = 405, F = 27.1, p = 8.8e-12; at NW(24) p = 9.9e-9, at NW(60) p = 2.1e-6 | Confirmed; robust to longer HAC lags |
| H2b | "VIX adds nothing once overall EMV is included" (t = -0.35) | t = -0.35 | Full sample t = -0.35 (ΔR2 = 0.0005). Validation: t = -2.51, R2 rises 0.126 to 0.166. Post-2021-10: t = -1.92 | Overreach: true only in the full sample |
| H2c | Share component: corr 0.865 with the signal; -0.05 with z_VIX; -0.01 with MCCC; 0.01 with CPU | as stated | 0.865; -0.05; -0.01; 0.01 | Confirmed. The -0.01 and 0.01 are on the 2006-02 to 2025-06 common sample and have no ledger p-value |
| H3a | Zeros: 39/59 against 12/441, Fisher p = 1.3e-32 | as stated | 39/59, 12/441, OR 69.7, p = 1.3e-32; period counts 12/151, 31/48, 25/36, 9/18, 8/12 all match | Confirmed |
| H3b | Holdout: z of zero months -0.95, nonzero +0.95; 5/5 entries after a zero month (validation 2/21); 7/17 nonzero months in state; hold6 share 0.646 against 0.642 | as stated | identical | Confirmed (numbers) |
| H3c | "The holdout traded a different signal from the one the team designed on"; "failure is partly mechanical"; "rule collapses to a nonzero reading right after a zero month"; "the trigger has changed" | see text | Two counterfactuals give the same 5 holdout entries (2023-04, 2024-06, 2025-02, 2025-09, 2025-11). (B) freezes the window mean and sd at the pre-regime 2021-09 window. (A) treats zeros as missing. The entries were readings of 0.64 to 0.94, above the 0.527 bar that applied in 2021-09. 6 of the 11 nonzero-after-zero holdout months (0.16 to 0.36) did not trigger. 11 of 17 nonzero holdout months follow a zero, so 5/5 has probability 0.11 at the base rate | **Overreach**: the zero-driven window arithmetic changed no holdout trade |
| H3d | Minimum EMV_env needed to cross fell from 0.527 to 0.406 | 0.527 / 0.406 | 0.526 / 0.406 (bisection; the builder's 0.0005 grid rounds up) | Confirmed. The lower bar was never binding in the holdout (see H3c) |
| H4a | Primary: 31/50 crossings high-VIX (62%) against 48.9%, p = 0.097 | as stated | 62.0% against 48.9%, Fisher p = 0.097; circular-shift permutation p = 0.113; LPM NW(12) p = 0.049 | Confirmed (numbers). "Not significant" depends on the test, so call it borderline |
| H4b | Crossings in high overall-EMV months: 88% against 64.5%, p = 0.0006 | as stated | 88.0% against 64.5%, p = 0.0006; circular-shift p < 0.003 (0 of about 380 shifts); LPM NW(12) p = 0.0003 | Confirmed; robust to serial dependence |
| H5a | Q6a PST slopes: MCCC -0.093 (t -0.49); CPU -0.160 (t -1.24); Holm 0.62 / 0.43 | as stated | MCCC -0.093, t -0.49, n 233; CPU -0.160, **t -1.23** (CSV -1.2347), n 425; Holm 0.62 / 0.43 | Discrepancy: CPU t should read -1.23 |
| H5b | 8 primary ICs are null; smallest Holm p = 0.62 | as stated | All 8 ICs match to 3 dp; smallest raw p = 0.077, Holm 0.62 | Confirmed |
| H5c | Lag1 and FF3+RATE variants change nothing | as stated | lag1 shock_CPU on Brown -0.034 (p 0.54); shock_CPU holdout t 1.85 / -1.93 match | Confirmed |
| R1 | Team replication: IC -0.0915 (validation, n 151) and 0.1234 (holdout, n 47); 34 p80 months | as stated | -0.0915, 0.1234, 34; also matches the executed team notebook output | Confirmed |
| Q5 | corr(z_MCCC, z_EMV_env) = -0.0004 (p 0.996); corr(z_CPU, z_EMV_env) = 0.123 (p 0.037) | as stated | identical. For CPU: reverse-direction p = 0.048, NW(24) p = 0.050, Holm over the 2 primary tests = 0.074. Partial correlation given z_EMV_overall = 0.05 | Confirmed. The CPU link runs through overall volatility news; FINDINGS should say so |
| T1 | "MCCC shows no consistent sign" between validation and holdout | as stated | z_MCCC keeps its sign in both halves: GB +0.006 / +0.114; Brown +0.058 / +0.016, the wrong sign in both. Only shock_MCCC flips | Discrepancy (wording) |
| T2 | "The team measure was at its lowest when climate concern was at its highest" (-1.16 to -0.08 sd, 2022-2024) | -1.16 to -0.08 | Reproduced. With exact zeros excluded the range is -0.23 to +1.20 sd, and the median nonzero reading rose (0.30 before 2021-10, 0.36 in 2022-2024) | Overreach: the low level is the zero regime, not low attention |
| T3 | Exploratory: EMV-family sign flips; 26/184 exploratory Q6b p < 0.05; MCCC shock lifts both legs (+0.75, +0.84); MCCC shock corr 0.14 with Mkt-RF | as stated | All match the CSVs | Confirmed |
| L1 | Ledger: 632 tests, 15 primary, summary counts | as stated | 632 unique ids, 15 primary. Ledger p-values equal the source tables exactly (298 Q6b, 134 Q6a, 20 Q4 rows). Summary recount matches | Confirmed |
| L2 | Ledger integrity | (not claimed) | 4 correlation hypotheses are recorded twice (Q2_corr_* and Q5_corr_*) with different p-values. Example: EMV_env vs VIX level has r = 0.205 in both, but p = 5.1e-5 in one row and 0.038 in the other. `corr_test`'s NW t depends on which series is the dependent variable. The headline share-vs-MCCC and share-vs-CPU correlations have no ledger row | Discrepancy |

## Checks with no issue found

**Look-ahead**
- The past-only threshold, the real-time AR(1) shocks and the one-month-lagged hedge all reproduce exactly from independent code.
- The high-VIX and high-EMV flags use expanding past-only medians.
- `ar1_shock_full` is look-ahead, but it is labelled robustness.
- The within-window standardization in the IC is a correlation device, not a trading rule.
- There is no BE/ME use in M1.

**Sample windows**
- MCCC runs 2003-01 to 2025-06, so the first z is 2005-12 and the first shock 2006-02.
- CPU runs 1987-04 to 2025-09, so the first z is 1990-03 and the first shock 1990-05.
- VIX covers 1990-01 to 2026-08; the partial 2026-09 month (16 days) is dropped.
- The holdout ICs have 47 months (team) and 35 or 38 months (MCCC, CPU).
- All match.

**Signs**
- GB = Green minus Brown.
- PST predicts a positive GB slope on a concern shock.
- The team hypothesis is IC > 0 for GB and IC < 0 for the Brown residual.
- All are applied correctly.

**Newey-West**
- NW(6) is used throughout: Bartlett kernel, no small-sample correction, normal p-values.
- My hand-coded HAC matches.

**Annualization and costs.** Not applicable. M1 reports % per month per sd and ICs; there are no strategy returns and no trading costs.

**Figures and tables.** All 5 figures exist as pdf and png. The spot-checked .tex tables match the CSVs.

## Required fixes

1. **Remove the "mechanical holdout failure / different signal" claim.** Rewrite headline 3, the last paragraph of Q3, "the trigger has changed" and Implication 2.
   - Two counterfactuals give the same 5 holdout entries and the same 7 state months: pre-regime (2021-09) window scaling, and zeros treated as missing.
   - The entries were readings of 0.64 to 0.94, not "roughly median" readings.
   - 6 of the 11 nonzero-after-zero holdout months did not trigger.
   - "All 5 after a zero month" is close to the 65% base rate (P = 0.11).
   - Keep the supported statements: the input is two-thirds exact zeros from 2021-10, and zero months can never trigger. Say the holdout losses cannot be attributed to the zero-driven window arithmetic.
   - Add the counterfactual to `run.py` and the tables.
2. **Q6a CPU t-statistic.** Change -1.24 to -1.23 in headline 5 and in the Q6a table (CSV value -1.2347).
3. **Qualify "VIX adds nothing".** It holds in the full sample only. In the validation window z_VIX enters at t = -2.51 and adds 0.04 of R2; after 2021-10 t = -1.92.
4. **Correct "MCCC shows no consistent sign".** z_MCCC keeps its sign in both halves (positive for GB, positive and so the wrong sign for the Brown residual). Only shock_MCCC flips.
5. **Qualify "at its lowest when climate concern was at its highest".** The -1.16 to -0.08 sd range comes from exact zeros. Excluding zeros gives -0.23 to +1.20 sd.
6. **Ledger.** Needs three changes:
   - Record each of the 4 duplicated correlation pairs once, with a direction-free test. The current duplicates disagree by up to 3 orders of magnitude.
   - Add rows with p-values for the headline share-vs-MCCC and share-vs-CPU correlations.
   - Report Holm over the 2 Q5 primary tests (CPU Holm p = 0.074).
7. **Q5 text.** Say the primary CPU correlation is nominally significant but fragile: p 0.037, Holm 0.074, NW(24) 0.050. Its partial correlation given z_EMV_overall is 0.05, so it comes through overall volatility news. This supports the builder's reading, but the headline currently shows only the share-component numbers.
8. **Q4 text.** Next to the Fisher p-values, report dependence-robust p-values (circular shift or LPM with NW), because Fisher treats persistent monthly flags as independent.
   - Primary VIX result: 0.049 to 0.113, so call it borderline, not flatly null.
   - EMV-overall link: stays below 0.003.
9. **Add a caveat on leg membership.** The legs use a single undated emissions-intensity cross-section applied back to 1985. This is inherited from the team, but the CPU tests from 1990 use a leg composition chosen with later information.
10. **Save FINDINGS.md.** It does not exist on disk. The orchestrator must save it, with fixes 1 to 9 applied.

## Bottom line

The numbers are sound: every decision-relevant statistic reproduces from independent code, the ledger p-values are consistent with the tables, and there is no look-ahead in the signal, the threshold, the shocks or the hedge.

The "Do not implement" support holds. Genuine concern measures give null contemporaneous and predictive results, and the team signal is overall volatility news plus a topic share.

The main overreach is the story that the holdout failed for mechanical reasons. The zero regime is real, but it did not change which months the rule traded.

# Round 2

This round checks the revised FINDINGS.md (saved by the orchestrator) against the round-1 required fixes, reruns everything, and adds checks for what the fix round did not cover.

## Scripts

Rerun this round, all from `cd /home/hashim/projects/GA/project/research && uv run python <script>`:
- `modules/M1_signal_audit/run.py`.
- `modules/M1_signal_audit/verify/verify_m1.py`: the round-1 checks, with builder claims updated to the revised text.
- `modules/M1_signal_audit/verify/verify_m1_round1.py`: the round-1 checks with the original round-1 claims.
- `modules/M1_signal_audit/verify/verify_m1_round2.py`: fix-round checks (counterfactuals, direction-free test, Q5 robustness, Q4 dependence-robust p-values, ledger integrity, Q2 subsamples, standardized levels, Q6a/Q6b robustness).
- New: `modules/M1_signal_audit/verify/verify_m1_round2_gaps.py`, output `verify_results_round2_gaps.csv`. It does not import `run.py` or `helpers.py`. Part G2 uses the verified `lib/team_pipeline.py` building blocks.

Notes:
- `verify_m1.py` and `verify_m1_round1.py` write the same `verify_results.csv`. Run `verify_m1.py` last. The file on disk is the `verify_m1.py` output.
- `verify_m1_round2.py` and the claim updates in `verify_m1.py` were written against the fix agent's draft text, before the orchestrator saved FINDINGS.md. I spot-checked their hard-coded claims against the saved FINDINGS.md and found no difference.

## Runs

| Script | Result |
|---|---|
| `run.py` | Runs in 18.5 s. All 45 M1 tables are byte-identical to the copies on disk before the run. The 5 figures (pdf and png) and `data/derived/attention_measures.csv` are regenerated. |
| `verify_m1.py` | 104 match, 0 mismatch, 13 info. This includes the team IC replication (-0.0915, 0.1234, 34 p80 months) and every primary test. |
| `verify_m1_round1.py` | 96 match, 5 mismatch, 15 info. All 5 are claims the revised FINDINGS changed on purpose: CPU t -1.24 to -1.23 (twice), ledger 632 to 667 rows, and "MCCC shows no consistent sign" (twice). |
| `verify_m1_round2.py` | 257 match, 0 mismatch, 1 info |
| `verify_m1_round2_gaps.py` | 34 match, 1 mismatch, 25 info. The mismatch is the ledger row arithmetic (see Remaining issues). |

## Round-1 required fixes

| # | Fix | Status | Evidence |
|---|---|---|---|
| 1 | Remove the "mechanical failure / different signal" claim | Resolved | "partly mechanical" and "the trigger has changed" are gone. "Different signal" now appears only as "Not supported". Q3 ends with the counterfactual result, and Implication 2 is rewritten. The counterfactual is in `run.py` and in 4 tables. Frozen 2021-09 scaling (with the rebuilt threshold or the team's threshold path) and both zeros-missing variants give the same 5 holdout entries. Two independent implementations reproduce this: loops in `verify_m1_round2.py`, pandas rolling and expanding windows in the gap script. Also reproduced: entry readings 0.64 to 0.94; bars 0.37 to 0.53 (team) and 0.518 to 0.521 (frozen); no holdout reading between the two bars; 6 of 11 nonzero-after-zero months not triggering, at 0.16 to 0.36; base rate 11/17, P(5 of 5) = 0.113, binomial two-sided 0.169, Fisher 1.0. |
| 2 | CPU t -1.23 | Resolved | The table and text read -1.23 (CSV -1.2347, my OLS -1.23). The builder also corrected the FF3 + RATE CPU t to -1.43, which reproduces. |
| 3 | Qualify "VIX adds nothing" | Resolved | Reproduced z_VIX t: full -0.35; pre-2021-10 0.16; validation -2.51 (slope -0.30, R2 0.126 to 0.166); post-2021-10 -1.92 (R2 0.245 to 0.281); holdout -1.13. z_EMV_overall t is 3.2 to 5.4 across these subsamples. The builder is right that the result also holds before 2021-10, not only in the full sample. |
| 4 | MCCC sign wording | Resolved | The text now says z_MCCC keeps its sign (GB +0.006 / +0.114; Brown +0.058 / +0.016) and only shock_MCCC flips (-0.015 / +0.078; +0.042 / -0.115). All reproduce. |
| 5 | Qualify "lowest when concern was highest" | Resolved | Reproduced: -0.23 to +1.20 sd with at least 3 nonzero months (24 of 36 months have a value); -0.05 to +0.35 with at least 6 (5 months); the 11 nonzero months average +0.37 sd; medians 0.36 (2022-2024), 0.306 (60 months to 2021-09), 0.24 (1985-01 to 2021-09). The builder is right that the upper end depends on the minimum count, and both versions are reported. The figure's zeros-excluded series equals mine to 1e-9. |
| 6 | Ledger | Resolved | 667 rows with unique ids: 15 primary, 217 robustness, 435 exploratory. No correlation pair is recorded twice on the same sample. The only exception is the Q5 primary robustness family, which by design holds different tests of the same pair. 17 correlation and 4 IC duplicates are merged. The direction-free test reproduces from raw moments by the delta method: t matches after the n/(n-1) factor, and the p-value is the same in both directions. EMV_env vs VIX level now has one p, 0.0035. The 6 share rows (vs MCCC, CPU, MCCC_transition) are added. Holm over the 2 Q5 primaries is 0.996 and 0.074, reported in `q5_primary_robustness` and the text. The ledger has no Holm column for any family, so this is consistent. Every table row's p equals its ledger row. |
| 7 | Q5 text | Resolved | Reproduced: p 0.037, Holm 0.074, reverse direction 0.048, NW(24) 0.050, direction-free 0.040, partial r 0.05 (p 0.36). |
| 8 | Q4 dependence-robust p-values | Resolved | All 20 rows reproduce to 1e-8 or better: Fisher, circular shift and LPM NW(12). Primary: 0.097 / 0.113 / 0.049, now called borderline. EMV_overall: 0 of 382 rotations, LPM 0.0003. The builder's rotation count of n - 23 (381) is correct for shifts 12 to n - 12. My round-1 count of 380 left out the upper bound. |
| 9 | Leg-membership caveat | Resolved | It is in Data and in Caveats. |
| 10 | Save FINDINGS.md | Resolved | Saved by the orchestrator; the header comment says so. |

## New checks this round

**G1: robustness of the counterfactual.**
- The pandas re-implementation gives the same 5 holdout entries under every variant.
- Post-2021-10 state months that differ from the team: 0 (frozen), 1 (zeros missing, 60 calendar months: 2022-08), 0 (last 60 nonzero). Entry months that differ: 0 in all three.
- Other freeze dates give the same 5 entries: 2019-09 (m* 0.247, s* 0.153) and 2020-09 (0.268, 0.169).

**G2: does the result extend beyond the Original rule?** The builder tested only the Original rule, but Implication 2 says the zeros are "not the explanation of the holdout losses" in general. I rebuilt all six team-baseline strategies with the `team_pipeline` building blocks. The rebuild reproduces each team holdout net return exactly. I then swapped in each counterfactual z.

| Strategy | Holdout ann. net, team | Frozen 2021-09 | Zeros missing, 60 calendar months | Zeros missing, last 60 nonzero |
|---|---|---|---|---|
| Original 3m | -3.82% | -3.82% | -3.82% | -3.82% |
| Original 6m | -2.14% | -2.14% | -2.14% | -2.14% |
| Pure 3m | -2.17% | -2.17% | -2.09% | -2.09% |
| Pure 6m | -3.04% | -3.04% | -2.15% | -2.15% |
| Continuous raw | -0.65% | -0.71% | -0.74% | -0.80% |
| Continuous pure | -0.48% | -0.56% | -0.73% | -0.80% |

- Under frozen scaling, the Original and Pure rules have identical returns month by month. The Pure holdout entries are identical in every version: 2023-04, 2024-06, 2025-02, 2025-09. The 2025-11 Pure entry is lost to the team's CPI gap in all versions.
- Under zeros-missing, the Pure difference comes from the 2022-07 validation-tail Pure entry. It disappears, which removes exposure in 2022-08 to 2023-02. The Pure holdout entries are unchanged.
- The continuous variants lose slightly more under frozen scaling. Holdout Sharpe goes from -0.60 to -0.74 (raw) and from -0.47 to -0.61 (pure).
- Every team strategy still loses in the holdout under every counterfactual. Implication 2 therefore holds for all six strategies, which is broader than the builder showed.

**G3: text numbers not covered elsewhere.** All of these match:
- Fisher test of state against nonzero months in the holdout: p = 0.00026 (table [[7, 10], [0, 31]]).
- The 24-month zero share is at most 12.5% before 2021 and peaks at 79.2% in 2024-02.
- Share mean 0.0136. There are 20 nonzero shares after 2021-10, ranging from 0.006 to 0.054.
- Q2 joint slopes -0.03 (t -0.35) and 0.43 (t 5.07), recomputed with statsmodels HAC as a second estimator.
- Q4 counts, shares and rotation counts for the 7 rows quoted in the text. Since-2010 VIX LPM p = 0.34.

**CPU lag claim.** Implication 3 says CPU's stable IC sign "does not survive an extra month of lag". Confirmed:
- With one more month of lag, shock_CPU on the Brown residual is -0.081 in validation and +0.063 in the holdout.
- z_CPU flips sign in the holdout for both outcomes.

**Figures.** Both render correctly:
- `rule_mechanics` has the frozen-scaling panel ("0 holdout entry months differ").
- `standardized_measures` shows the zeros-excluded line (at least 3 nonzero months).

**Look-ahead, signs, NW.** No change from round 1. In the new code, the counterfactual thresholds are past-only (expanding over months up to t-1), and the frozen window uses data only up to 2021-09. The direction-free test uses NW(6). No em dashes in FINDINGS.md.

## Remaining issues

**Required (text only, no rerun needed)**

1. "Response to verification", item 6, ledger bullet. The arithmetic is wrong. 6 + 8 + 40 + 2 = 56 rows were added, and 632 + 56 - 21 = 667, so 35 is the net change, not the number added.
   - Current: "35 rows were added: 6 share correlations, 8 Q5 primary robustness rows, 40 Q4 dependence-robust rows and 2 Q3 base-rate rows. 21 duplicates were merged."
   - Replace with: "56 rows were added: 6 share correlations, 8 Q5 primary robustness rows, 40 Q4 dependence-robust rows and 2 Q3 base-rate rows. 21 duplicates were merged, a net change of 35 rows (632 + 56 - 21 = 667)."

**Recommended (not required)**

- a. Caveats, "Limits of the Q3 counterfactuals": add the strategy-level result so the evidence matches the scope of Implication 2. After "Because the entries and the lagged hedge are identical, the counterfactual holdout returns are identical too." add: "The same holds for the Pure rule under frozen scaling. The continuous variants, which use the level of z, lose slightly more under frozen scaling (Continuous raw -0.65% to -0.71% a year, Continuous pure -0.48% to -0.56%), so no team strategy would have done better with pre-regime scaling."
- b. Q4, holdout bullet: the LPM p of 0.023 for high overall-EMV crossings is not reliable. All 5 events are flagged, so the event-month residuals are zero and the HAC standard error ignores the sampling error of the 5-of-5 share. Suggested wording: "LPM 0.023, unreliable here because all 5 events are flagged".
- c. LaTeX: `crossings_vix_summary.tex` prints p = 0.000 for Fisher, circular shift and LPM. Print "<0.001" for Fisher and LPM, and "<0.003" or "0/382" for the shift test. `q5_primary_robustness.tex` prints r = -0.000 for MCCC; print -0.0004.

## Round 2 bottom line

All ten round-1 fixes are resolved. The builder's refinements are correct: the rotation count, the calendar-window variant, the pre-2021-10 VIX result, the sensitivity to the minimum nonzero count, and the medians.

Nothing broke. `run.py` reproduces every table byte for byte, and the independent checks all match (104 + 257 + 34), except one ledger-arithmetic sentence.

The zero-regime conclusion is now well supported. It holds for every team strategy, not only the Original rule, and for other freeze dates.

One text-only fix remains, in the response section. The "Do not implement" support is unchanged.
