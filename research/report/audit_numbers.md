# Number audit of report.tex (draft of 2026-09-26, 08:47)

Scope: every number in the main body and in the appendix prose of `report/report.tex`, plus the generated tables it inputs from `report/tables/` (tab_signals, tab_time, tab_frozen, tab_m1_cross, tab_ledgers). The verbatim transcripts in `appendix_transcripts.tex` are out of scope. Builder tables that the appendix re-wraps unchanged were checked only for stale captions.

Sources: module CSVs in `outputs/tables/`; the latest round of each `modules/<id>/FINDINGS.md` and `VERIFY.md`; `logs/replication.md`; the team `writeup.pdf`; `exchange/01_*` and `exchange/02_*` (fact-checks and evaluations); `logs/lit_digest.md`; the course brief.

Severity scale:
- **High**: a wrong claim or a headline that contradicts the report's own method or a cited source.
- **Medium**: a wrong count or range, overreach, or an internal inconsistency.
- **Low**: rounding, labelling, a missing qualifier, or provenance.

None of the findings changes the verdict.

## Summary

- About 260 numeric claims checked. 32 findings: 3 High, 13 Medium, 16 Low.
- The core numbers are sound:
  - Every cell of tab_time and tab_signals matches the M2 strategy grid, the M3 exposures CSV and the M1b alpha grid.
  - The ledger totals are correct (23,923 rows, 155 primary).
  - The M8 pass bar and timeline match.
  - The replication and audit numbers match `logs/replication.md`.
- The three High items are:
  - A false "no positive holdout alpha" claim, in 3 places.
  - A COVID headline that uses a different benchmark from the one Section 1.3 says every timing claim is tested against.
  - A citation of Pastor, Stambaugh and Taylor (2021) that `lit_digest.md` contradicts.

## Findings

Line numbers refer to `report/report.tex` unless stated.

| # | Location | Claim as written | Correct value | Source | Severity |
|---|---|---|---|---|---|
| H1 | l.123 (Table 2, M1b row); l.401 (App. C M1b); l.632 (Table E.2) | "no positive holdout alpha" for MCCC and CPU | False. CPU Original 3m +0.36% (t 0.37) and CPU Pure 6m +0.20% (t 0.20) are positive. All six MCCC holdout alphas are negative. None is significant. | `M1b_alt_signals_primary.csv`; tab_signals (CPU holdout column); M1b FINDINGS s5 "Four of the six CPU holdout alphas are negative" | High |
| H2 | l.44 (Exec. Summary); l.229 (s2.4); l.406 (Fig. C caption) | "the rule's edge over that short is +1.84% a year (t=0.87)" | The +1.84% is the unscaled (pi = 1) paired FF3 alpha from M1b. Section 1.3 says every timing claim is tested against the pi-scaled D_t. On that benchmark, corrected Original 3m in COVID has pi 0.390, mean D t 2.35 (p 0.028), and in-window factor alpha of D 2.98% (t 1.67, p 0.113). Pure 3m: t 3.15; alpha 3.43% (t 1.79). Both are verified numbers that the report omits. The conclusion (no significant edge after factors) holds, but the headline must say which benchmark it uses. | `M3_alpha_beta_ln_vs_benchmark.csv` (recomputed); M3 FINDINGS s6; M1b FINDINGS s6 | High |
| H3 | l.56 | "Shorting Brown after a concern spike is the trading form of the \citet{pst2021} mechanism." | PST 2021 Proposition 6 (p.557): green outperforms when concern rises unexpectedly. A known spike carries no positive expected GMB and, through the investor channel, lowers it afterwards. The digest's implication (a) says such a rule "is a bet that concerns keep surprising upward, not a bet on a known premium". | `logs/lit_digest.md` s2 | High |
| M1 | l.142 | "In validation the discrete rules turn over 1.8 to 5.8 times a year" | 2.4 to 5.8 for the team signal (O3 5.12, P3 5.76, O6 2.37, P6 2.50). The 1.8 minimum is taken across MCCC, CPU and the placebos. The 0.63% maximum drag is correct. | `M1b_alt_signals_compact.csv` (EMV_env, validation); M2 FINDINGS Q4 | Medium |
| M2 | l.108; l.347 (Table B.1 item 3) | "Every t-statistic is ... NW(6), and p-values come from t(n-k)"; "t(n-k) p-values everywhere" | Not true of every module. M1 uses normal HAC p-values and NW(12) for its LPM test. M1b uses t(n-4) only when n < 60. M4 and M5 use normal p-values; the M5 COVID BH 0.022 quoted in App. E comes from a normal p of 0.0015. M6 Clark-West p-values are normal and one-sided. | M1 FINDINGS caveats; M1b FINDINGS s4; M4 VERIFY C8; M5 FINDINGS s4 | Medium |
| M3 | l.44 | "every inference uses real-time inputs" | Several inferences do not. Static emissions sorts (team and 2022 EPA) are applied back to 1970, which the Limitations call a look-ahead. The M3 centered-window attribution quoted in s2.3 and s2.4 is ex post. Table 5 note b uses the team's same-month timing. | Limitations (l.261); M3 FINDINGS s3 and s6; M4 caveats | Medium |
| M4 | l.44 | "the rule frozen before its test window earns -0.18% a year" | -0.18% is the timing alpha of D. The frozen rule's net return was +0.51%/yr (t 0.42), and always-on earned +0.65%. | M8 FINDINGS, CONTEXT | Medium |
| M5 | l.110 vs l.261 | "the pre-specification of M1b and M3 cannot be dated" | Understated, and inconsistent with the Limitations ("timestamped only for M8"). M1, M4, M5 and M6 have no timestamp evidence either. M2 has a builder-transcript record. | M1b, M3 and M2 VERIFY; `research/` has no version control | Medium |
| M6 | l.259 | "and the families had power" | Overclaim. M1b's 40-test holdout family needed p < 0.00125 on 36 to 39 months, so Holm = 1.00 was "close to mechanical". M5's carbon test "has low power". M8's "power is limited". | M1b FINDINGS s5; M5 FINDINGS s7; M8 caveat 3 | Medium |
| M7 | l.259 | "the four nominal positives are retired in Appendix E" | App. E lists six: M5 COVID, M6 DGS10, M1b paired COVID, M4 EPA-minus-team, M4 full-sample, M3 HML convexity. | report l.646 to 654 | Medium |
| M8 | l.147; l.266 | "unseen 1994--2009 data"; "the unseen pre-2010 window" | Pre-2010 data informed the team's macro-state notebook (192 months of forward Brown residuals), and the rule was designed after 2010 to 2026 had been seen. The window is out of sample for returns, not for design, as s2.5 itself says. | M8 caveats 1 and 2; exchange 01 evaluation | Medium |
| M9 | l.222 | "None of the 900 ... is positive; adding BOND and UMD makes every one more negative (smallest Holm p=0.155)" | "Every one" reads as the 900. The BOND and UMD test covers the 12 primary-test holdout alphas (6 rules x 2 baselines). Holm 0.155 is the team baseline. | M3 FINDINGS s4(ii); M3 VERIFY R2.6 | Medium |
| M10 | l.250; l.477 | "flips the raw spread but produces no alpha" | No post-2010 alpha. The full-sample FF5+UMD alpha is 4.5% (t 2.58): 7 of 9 variants have raw p < 0.05 and 5 of 9 survive Holm. The verifier (F4) flagged exactly this selective wording. | M4 FINDINGS robustness; M4 VERIFY F4 | Medium |
| M11 | App. C tab:m1cross (l.378 caption; `make_tables.py` l.190) | Shift p printed as "<0.003" in every row with zero extreme rotations; caption says "381 or 382 rotations" | Since-2010 rows have 176 rotations (bound <0.006). Validation rows have 128 (bound <0.008). Rotations range from 25 (holdout) to 382 by window. The holdout LPM p of 0.023 is unreliable because all 5 events are flagged. | `M1_signal_audit_crossings_vix_summary.csv` (n_shifts); M1 VERIFY R2 note b | Medium |
| M12 | l.94 | "Aero, Util and Ships carry 86% of the 3-month rule's COVID gross P&L" | The arithmetic checks: (2.74 + 1.71 + 1.30) / 6.70 = 85.8%. But the only source is the exchange 01 fact-check, not a verified module. Cite it. | `exchange/01_idea_generation/factcheck.md` row 50 | Medium |
| M13 | l.110 | "A number enters this report only after independent code produced it too." | Overclaim. The 86% figure, the 100-seed null counts (6 and 13) and ChatGPT's -0.19% come from the exchanges, not from a module verifier. | `exchange/*/evaluation.md` | Medium |
| L1 | l.54 | "the 3-month rule 5.94% in COVID 2020--21 (t=3.21)" | 5.94% is the net return. t 3.21 belongs to the FF3 alpha of 6.03%. | writeup p.3; replication s1 | Low |
| L2 | l.252 | "12-1 month momentum" | The M5 primary is its "11-1" signal: months t-11 to t-1 at formation, 11 returns. M5's own "window 12-1" is a different variant (1.87%, t 1.30) in the appendix robustness table, so the label clashes with that table. | M5 FINDINGS s2 and s6; M5 run.py l.211 to 217 | Low |
| L3 | l.207 | "Outside COVID, the only t above 2 is in the validation sample" | Add "positive". Table 5 itself shows t -2.19 (Continuous raw, last 18), -2.79 and -5.65 (GB, last 18 and last 12). | tab_time; M1b VERIFY R2-2 | Low |
| L4 | l.200 | "In FF5 it is short HML, RMW and CMA (-0.11, -0.15, -0.25)" | Values correct. HML and RMW each have t -1.90 (p about 0.058). Only CMA is significant (t -2.80). | `M3_alpha_beta_exposures.csv` (GB, FF5, full_1970) | Low |
| L5 | l.140 | "BOND is the excess return ... (-15.0% in 2022 ...; annual correlation 0.991)" | -15.0% is the 2022 total return. The 0.991 correlation is over 1954 to 2025 (0.987 over 1993 to 2025). | M3 FINDINGS s2; M8 BOND CHECK | Low |
| L6 | l.602 | "M1 20 seconds", "M3 3 to 4 minutes" | M1 20 to 60 s. M3 146 s (verifier) to about 250 s (builder). | M1, M3 FINDINGS and VERIFY | Low |
| L7 | l.110 | "a verifier who imported none of the builder's code" | M1b, M1 (round 2) and M3 verifiers used the shared `lib/team_pipeline.py`. M3 also used M8's `build_bond`, only for comparison. "None of the module's own code" is accurate. | M1b, M1, M3 VERIFY | Low |
| L8 | l.229, l.222 | "market 1.97 and size 2.14 of 6.87 points"; "net -1.84% = leakage ..." | Numbers correct, but they come from centered (ex post) 36-month betas; say so. Leakage is 4.76 of 6.87; the residual 2.21 (t 1.27) is not zero. | M3 FINDINGS s6 and s7 | Low |
| L9 | l.142 | "all 28 zero-cost runs (highest -0.39%)" | Correct, but zero-cost runs exist only for 5-and-5 legs with the FF3 and FF5+UMD+COMEQ hedges. | M2 FINDINGS Q4 and caveats | Low |
| L10 | l.331 | "raw-spread HML loadings of -0.24 and -0.35" | These are the write-up's windows, 1970 to 2022-07 and 2010-01 to 2022-07. The main text uses -0.233 (1970 to 2026) and -0.298 (2010 to 2026), so a reader sees two "since 2010" values. | `M3_alpha_beta_exposures.csv` (validation -0.351); M2 VERIFY R2 | Low |
| L11 | l.266 | "more Newey--West lags raise the COVID t (3.21 to 5.32)" | 3.21 at 6 lags, 4.00 at 12 and 5.32 at 18. State the lags. | exchange 01 factcheck row 26; replication item 3 | Low |
| L12 | l.650 | M1b paired edge "against overall EMV it vanishes under team timing (t=0.87)" | Correct, but against VIX it stays nominally significant under team timing: Original 3m +4.08% (t 2.34, p 0.030); Pure 3m t 2.15. | M1b VERIFY R2-1; `M1b_alt_signals_placebo_covid.csv` | Low |
| L13 | l.185 | "all through overall EMV (slope 0.43, t=5.07; VIX t=-0.35)" | True in the full sample, as stated. The verifier flagged "VIX adds nothing" as overreach: in validation VIX enters negatively (t -2.51). | M1 VERIFY H2b and fix 3 | Low |
| L14 | Fig. 1 caption | "Climate concern rose through 2022--2025" | MCCC ends 2025-06 and CPU 2025-09. The MCCC 12-month mean rose from 1.22 (2021-12) to 1.82 (2025-06), so "to mid-2025". | `M1_signal_audit_standardized_measures_12m.csv` | Low |
| L15 | Bibliography | ardia2023, bbdk2019, gavriilidis2021, fs1996, gk2000, holm1979, bh1995, nw1987, ct2008, cw2007 | None of these ten has an entry in `lit_digest.md`, whose s12 covers only MG1999, ZA2024, TM1966, HM1981 and LN2006. The details look right, but check them against the originals before submission. | `logs/lit_digest.md` s0 and s12 | Low |
| L16 | l.123 | Adjusted p for M1b printed as "$\ge1.00$" | An adjusted p cannot exceed 1; print 1.00. Folded into the H1a fix. | M1b primary | Low |

## Recomputed from CSVs (all match unless listed above)

- **tab_time, every cell**:
  - M2 `strategy_grid.csv`: L5, corrected, FF3, team costs, E:FF3.
  - GB column: M3 `exposures.csv`, FF3. GB validation -0.55 (t -0.22) and COVID -1.04 (t -0.24) confirmed.
  - Full-sample starts: 1993-02 for the rules and always-short; 1993-01 for Continuous raw (n 403). GB n 679.
- **Table 5 note b**:
  - GB classical OLS abs t: 1.41 (last 18, FF3) and 1.37 (last 12).
  - Team-timing Original 3m: -10.82% (t -4.75) and -11.31% (t -2.68).
- **Last-18 losses**: every one of the six rules on the team signal lost money over the last 18 months (O3 and P3 -4.51%, O6 and P6 -1.35%, CR -0.73%, CP -0.80%). Over the last 12, O6 and P6 net +0.02%.
- **Smallest post-2010 p**: 0.053 over 7 models x 2 baselines x 6 rules (corrected Pure 6m, FF5, 1.58%, t 1.95).
- **tab_signals**: counts (4, 0, 0 validation t >= 1.96; 6, 6, 4 holdout negative) and means (1.45, 0.34, 0.88).
- **Ledgers**: 667 + 1,900 + 13,482 + 6,360 + 802 + 416 + 274 + 22 = 23,923 rows; primaries 15 + 40 + 46 + 33 + 1 + 4 + 8 + 8 = 155.
- **Arithmetic checks**:
  - 71% = 4.54 / 6.38.
  - 86% = 5.75 / 6.70.
  - 758 = 439 + 319 refits.
  - -1.84 = -0.24 - 1.14 - 0.46.
  - 36.5 s = 28.6 + 7.9.
  - Five minutes from pre-registration save (03:30:46) to first code (03:35:43).
- **M8 pass bar and drop-one**: match `M8_passbar.csv` and `M8_drop_one.csv`, including 2 of 5 drop-one alphas positive and 2 of 4 components passed for the team signal.

## Verified without issue (selection)

- **Replication and team numbers**:
  - All replication and audit-table figures.
  - 2.45%, 2.59%, t 2.23 and 2.46; holdout losses of 2.1% to 3.8%.
  - 0.07% to 0.73%; 0 of 32 (smallest Holm 0.119).
- **M1**:
  - 500 of 500 months; 12 of 441 and 39 of 59 zeros (Fisher 1.3e-32); 31 of 48 holdout months.
  - R2 0.169 (p 8.8e-12), slope 0.43 (t 5.07).
  - Correlations -0.0004 (p 0.996, n 235) and 0.123 (Holm 0.074); partial correlation 0.05.
  - Crossings in high overall-EMV months: 88% against 64.5% (p 0.0006).
  - Verification counts 104, 257 and 34.
- **M1b**:
  - 0 of 12 validation alphas with t >= 1.96; means 1.07% against 1.45%.
  - COVID: 6.38 (3.62), 4.54 (1.96), +0.42 ex-crash; EMV overall 4 of 6.
  - Holdout windows of 48, 36 and 39 months; verification counts 460 of 478.
- **M2**:
  - HML -0.233 and -0.298; Brown side -0.437; Steel and Ships -0.239; COMEQ -0.18 (t -8.70).
  - COMEQ correlation 0.66; COMEQ alpha -0.89% (t -0.24).
  - Residual HML -0.015 to -0.053; break-evens 40 to 100 bp, 211 bp, 19 to 50 bp.
  - 900 holdout alphas, 28 zero-cost runs, highest -0.39%; 8,091 tests, BH 27 negative; Holm 0.397 and 0.017; smoke test four minutes before the docstring.
- **M3**:
  - BOND 0.132 (Holm 0.019) and 0.088 (t 0.60).
  - Timing term -0.57% to -1.07%, 4 of 6 survive Holm; always-short -1.35%.
  - Hedged Brown leg +2.82% (t 0.95); half a point for rates; COVID attribution 1.97, 2.14 and 6.87.
  - BOND 2022 -15.0% against -17.8%; 45 of 48 BH survivors are HML; TM t 3.24.
- **M4**:
  - 6,051x, 33x, Spearman 0.700; ranks 2nd, 3rd, 20th and 31st; 14 to 47x and 1.9 to 6.0x.
  - 4.7% (t 1.52, p 0.129); 10.8 of 13.2 points; 8.2% (t 2.84, Holm 0.071 and 0.178); 4.5% (t 2.58); 433 checks.
- **M5**:
  - 8.52% net; alphas 1.74% (t 1.09) and 1.86% (t 0.71); UMD beta 0.99.
  - IR change -0.005 [-0.110, +0.096] at a 60% WACI cut; IR change +0.010 (Holm 0.823).
  - COVID 15.80% (t 3.18, OLS t 1.58, p 0.132); 163 of 163 checks.
- **M6**: 758 refits; R2 0.000%; +0.84% (t 1.17, p 0.24) and p 0.65; DGS10 p 0.018 and 0.020, q 0.34.
- **M8**:
  - Alpha -0.18% (t -0.27); shuffle median -0.22% (p 0.478); drop-one -0.61% to +0.03%; pass bar about +0.9%.
  - 32 choices; 128 of 128 numbers matched; all timestamps; ChatGPT -0.19% (t -0.25); 3.3e-13.
- **Exchanges**: 993 and 997 words; 1,772 words; 985 lines; 52, 26 and 6 claims (the six wrong ones confirmed in factcheck rows 13, 22, 26, 32, 33 and 36); 2 of 6 bugs missed; 6 and 13 null-seed rejections.
- **Literature**: PST 2022 (-4 bp, HML -0.26), EIJP (no BH survivor), BK against Zhang on sign, and the 2 x SR holdout arithmetic are all supported by `lit_digest.md`.

## Notes for the orchestrator (no fix needed in report.tex)

- `outputs/tables/M7_robustness_tests_ledger.csv` (422 rows) was written at 08:51, after this draft compiled at 08:48. When M7 is integrated, the totals at l.110 and l.259 and in tab_ledgers will change.
- Two FINDINGS files on disk still carry round-2 text errors their verifiers flagged. The report does not repeat either.
  - M1b s6: the paired-significance sentence, R2-1.
  - M2: "-0.019", "8-factor", "above the median".
- After applying fix M11, regenerate the tables with `cd research && uv run python report/make_tables.py`. The other fixes are text-only.
