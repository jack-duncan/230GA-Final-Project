# Final report outline: synthesis and plan

Author voice: Hashim Almodamagha, solo extension of our team's halfway project. "I" for steps I ran, "our team" for the inherited halfway work, "we" only for conventions. Style: logs/style_guide.md (claim, number in parentheses, mechanism, short verdict; no em dashes; no "however/moreover/thus/notably"; no "honest"; label ladder used literally).

Precedence rule used throughout this outline: where a module's FINDINGS.md and its VERIFY.md disagree, the latest VERIFY round wins. Several round-2 text fixes are not yet applied to the FINDINGS files on disk (M1b, M2, M5, M8); Section 7b lists the corrected wording to use.

Path conventions: tables are `outputs/tables/<file>`, figures `outputs/figures/<file>`, modules `modules/<id>/`. All paths are relative to `/home/hashim/projects/GA/project/research/`. The team repo is `/home/hashim/projects/GA/project/230GA-Final-Project/` (read only).

---

## 1. Working title and thesis

**Working title:** *Read the Label: Climate-Attention Timing of Brown Industries, Audited and Tested Out of Sample*

Alternates (same spirit, slogan then plain subtitle):
- *Know What You Are Timing: A Pre-Registered Post-Mortem of State-Dependent Climate Alpha*
- *Short Brown, Not Climate: Why a Climate-Attention Timing Rule Earns Nothing Out of Sample*

The slogan returns as the recommendation in the Executive Summary and the closing verdict: read the label, benchmark against the always-on position, and spend the last clean window on one frozen rule.

**One-sentence thesis:** Our team's "state-dependent climate alpha" is neither climate nor alpha: its signal counts equity-volatility news, its in-sample gains belong to an untimed short of a value-tilted Brown leg, and a rule frozen before its test window earns nothing on the one unseen period (1994 to 2009), so the strategy should not be implemented.

---

## 2. Proposed strategy, verdict and decisive reasons

### 2a. What exactly was proposed

Our team's halfway strategy (writeup.pdf, Sections 1.1 and 1.3): short the equal-weighted Brown industry leg (Util, Ships, Aero, Steel, BldMt, the five highest-intensity FF49 industries in the team's emissions file) for 3 or 6 months after "climate-transition attention" crosses its past-only 80th percentile; hedge the leg with rolling 60-month FF3 betas lagged one month; size to 5% annualized residual volatility (cap 1x); pay 10 bp on the leg, 5 bp on the market overlay and 25 bp on SMB and HML per unit of turnover. Variants: a macro-purified signal and a continuous weight. Validation 2010-01 to 2022-07, holdout 2022-08 to 2026-07. Our team already concluded "Do not implement".

The version I carry as "the proposed strategy" in the Executive Summary is the best-specified form the evidence allowed: the 6-month Short-Brown rule triggered by the energy-and-environmental-regulation share of equity-volatility news (EMVENRGYENVREG / EMVOVERALLEMV, observed one month late, zero months treated as missing), frozen in `modules/M8_frozen_pre2010/PREREGISTRATION.md` before any 1994-2009 return existed.

### 2b. What was tested

1. The team rule as built, reproduced exactly, then corrected for real-time inputs (EMV lagged one month, the missing Oct-2025 CPI print interpolated): `logs/replication.md`, M1b, M2, M3.
2. What the signal measures, and whether genuine climate-concern measures (MCCC, CPU) or volatility placebos (VIX, overall EMV) do the same through the identical machinery: M1, M1b.
3. What the legs are (EPA supply-chain intensities for all 49 industries): M4.
4. Whether any return is alpha rather than static or time-varying beta (FF5, UMD, a traded 10-year BOND factor, commodity equity, Ferson-Schadt, Lewellen-Nagel, Treynor-Mazuy and Henriksson-Merton): M2, M3.
5. One pre-registered, scored-once test on the unseen 1994-2009 window: M8.
6. Alternatives on the same data, each aimed at a small defensible alpha: EPA-ranked Green-minus-Brown (M4), carbon-aware industry momentum with a Grinold-Kahn carbon frontier (M5), Lehnherr-Mehta-Nagel style shrinkage timing (M6).

### 2c. Verdict: Do not implement. Four decisive reasons, each with its number

1. **The signal is not climate attention.** The team's "attention" column is FRED EMVENRGYENVREG in 500 of 500 months (max difference 0.0) [`outputs/tables/M1_signal_audit_identity.csv`], an equity-market-volatility news tracker. Its rolling z-score is uncorrelated with media climate concern (r = -0.0004, n = 235, p = 0.996) [`M1_signal_audit_q5_primary_robustness.csv`], and the identical machinery fed MCCC or CPU earns 0 of 12 validation alphas with t >= 1.96 (EMV tracker: 4 of 6), with all six MCCC holdout alphas negative [`M1b_alt_signals_primary.csv`; M1b FINDINGS Headline].
2. **The one unseen window gives the rule nothing.** Frozen before any 1994-2009 return was computed, the EMV-share rule earns a timing alpha of -0.18% a year (NW(6) t = -0.27) over 1994-03 to 2009-12, calendar-shuffle p = 0.478, and meets 1 of 4 pre-registered pass-bar components [`M8_passbar.csv`; M8 VERIFY section 3: 128 of 128 numbers rebuilt independently].
3. **The in-sample win belongs to the position, not the timing.** In COVID 2020-21 a signal-free always-short Brown position earns 4.54% FF3 alpha (t = 1.96), 71% of the real-time rule's 6.38%, and the rule's paired edge over it is +1.84% a year (t = 0.87) [`M1b_alt_signals_covid_decomposition.csv`; `M1b_alt_signals_covid_attribution.tex`]. The 6-month rules held the always-short position in 24 of 24 COVID months [`M3_alpha_beta_position_overlap.csv`].
4. **The holdout loss is robust and not a rates or cost accident.** All six timed rules have a negative holdout alpha in 900 of 900 net-of-cost configurations, and in all 28 zero-cost runs (5-and-5 legs, FF3 and FF5+UMD+COMEQ hedges) [`M2_christhian_tests_key_numbers.csv`, keys `holdout_net_*`, `holdout_gross_*`]. Adding BOND and UMD makes every holdout alpha more negative (smallest Holm p 0.155) [`M3_alpha_beta_holdout_alpha.csv`].

### 2d. Draft Executive Summary (one paragraph, about 250 words; trim at the drafting stage)

> Our team's halfway project proposed a state-dependent climate trade: short the factor-hedged Brown industry leg (Util, Ships, Aero, Steel, BldMt) for three or six months after "climate-transition attention" crosses its past-only 80th percentile, sized to 5% residual volatility. I asked three questions of it: what the signal measures, what the legs are, and whether any version survives a window it was not designed on. The study uses Fama-French industry and factor returns, FRED news and macro series, two climate-concern indices (MCCC and CPU) and EPA supply-chain emission factors; every inference uses real-time inputs and small-sample p-values, every module has a pre-stated primary test, and an independent verifier rebuilt each one. The recommendation is **Do not implement**. First, the "attention" series is FRED's equity-volatility news tracker for energy and environmental regulation (identical in 500 of 500 months), uncorrelated with media climate concern (r = -0.0004), and the same machinery fed genuine climate measures earns 0 of 12 validation alphas at t >= 1.96. Second, a rule frozen before its test window earns -0.18% a year on 1994-2009 (t = -0.27, shuffle p = 0.48). Third, the COVID gain belongs to the position: an untimed short of the same leg earns 71% of it, and the rule's edge is +1.84% a year (t = 0.87). Fourth, every timed rule loses in the 2022-2026 holdout in 900 of 900 configurations, already before costs in every zero-cost run, and rates do not explain it. Carbon-aware industry momentum and shrinkage timing on the same data fare no better. In short: read the label, benchmark timing against the always-on position, and spend the last clean window on one frozen rule.

---

## 3. Section plan and page budget

Brief limits (MFE230GA_Final_Project_2025.pdf): Executive Summary 1 paragraph; What did you try 2 to 5 pages; What did you learn 1 to 4 pages; Appendices unlimited. Grading: thesis 40%, execution 40% (risk control, horizons, robustness, critical ChatGPT evaluation), originality 20% (novel data, prompt design).

| Part | Target pages | Exhibits |
|---|---|---|
| Title block + Executive Summary | 0.5 | none |
| 1 What did I try | 4.6 (limit 5) | Table 1, Figure 1, Figure 2, Table 2 |
| 2 What did I learn | 4.0 (limit 4) | Table 3, Figure 3, Table 4, Figure 4, Table 5 (Figure 5 optional) |
| Appendices A to E | no limit | see Section 5 |

If over length, cut in this order: Figure 5 to Appendix C (it is optional already); Table 1 to a prose list; Figure 2 to Appendix C (M4). Section 2 is the binding limit.

Placement decision: the two provenance audits (what the signal series is, what the emissions file is) are data facts, so they sit in 1.2 with Figures 1 and 2; the inferential results they lead to sit in Section 2 and point back to those figures. This keeps Section 2 inside 4 pages.

Format for every paragraph below: **Claim** (the run-in head or first sentence, written as a claim), **Evidence** (numbers), **Source** (exact file or FINDINGS/VERIFY section).

---

### Title block and Executive Summary (0.5 p)

One paragraph, the draft in 2d. Order: problem, strategy, data and test design, verdict with "Do not implement", the four reasons, what the evidence does and does not show, the slogan. Sources: as in 2c.

---

### 1 What did I try (4.6 p)

Page targets below include the exhibits and sum to about 4.5 pages.

#### 1.1 The inherited strategy and where the idea came from (0.5 p, 3 paragraphs)

**P1. Claim:** Our team's thesis was falsifiable and failed its own holdout.
- Evidence: legs and rule as in 2a; validation 6-month rules net 2.45% and 2.59% a year, FF3 alpha t 2.23 and 2.46; COVID 3-month rule 5.94% net, alpha 6.03% (t 3.21); holdout losses of 2.1% to 3.8% a year (t -1.66 to -2.19); raw spread HML loading -0.24 full sample and -0.35 since 2010.
- Source: `230GA-Final-Project/writeup.pdf` Table 1 (p.3) and Sections 2.1-2.2; all 32 Table 1 cells reproduce at two decimals (`logs/replication.md` section 1, step D; `lib/test_team_pipeline.py::test_writeup_table1`).

**P2. Claim:** The idea comes from HW1's high-versus-low-emitter tilt and from a literature that reads realized green returns as responses to concern shocks, not as a premium.
- Evidence: PST (2022) climate-concern shocks explain 2012-2020 green outperformance, shock-purged green-minus-brown mean about -4 bp a month, HML loading -0.26 (t -3.36); Eskildsen et al. (2026): no green-minus-brown alpha survives BH, and a 4-year holdout has expected t = 2 x Sharpe; Bolton and Kacperczyk (2021) brown premium in levels, not intensity; Zhang (2025) release-timing fragility.
- Source: `logs/lit_digest.md` sections 11.1, 11.3, 11.5 (claim-to-source table with page numbers); `logs/hw_context.md` sections 1.2-1.3 (HW1 emissions tilt, ChatGPT strategy ideas) and 2.6 (HW2 critique lessons); `logs/whatsapp_halfway.md` (Christhian's four tests, Charishma's Part B).

**P3. Claim (framing and stance, stated once):** For the team's result to be climate alpha, three things had to hold: the signal measures climate concern, the gain comes from timing rather than exposure, and the rule survives a window it was not designed on. I tested each one, and the study favours transparent reporting over good-looking results.
- Evidence: none (roadmap paragraph); pointer to Table 2.
- Note for drafting: this is the one place for the reporting-stance sentence (style guide 1, "Stance").

#### 1.2 Data, and what the data turned out to be (1.0 p, Table 1, Figures 1 and 2)

**P1. Claim:** The study uses only public data, and every input used at the end of month t is published by then.
- Evidence (Table 1 rows): team files (FF49 value-weighted returns 1926-07 to 2026-07, FF3 and RF, the emissions snapshot covering 41 of 49 industries, the macro file); Ken French FF5 (2x3), UMD, industry BE/ME and firm counts; FRED EMVENRGYENVREG and EMVOVERALLEMV (1985-01 to 2026-08), VIXCLS, GS10, TB3MS, BAA, AAA, CPI, CFNAI, MCOILWTICO, PALLFNFINDEXM; MCCC aggregate (Ardia et al., 2025 update, 2003-01 to 2025-06); CPU (Gavriilidis, 1987-04 to 2025-09); EPA Supply Chain GHG Emission Factors v1.3 (1,016 NAICS-6 codes), USEEIO v2.0.1 (electricity factor), Census SIC-NAICS concordances; US Treasury month-end par yields and Damodaran annual T-bond returns (BOND validation).
- Source: M1 FINDINGS "Data"; M1b FINDINGS section 3; M2 FINDINGS "Data"; M3 FINDINGS section 2; M4 FINDINGS "Data"; M6 FINDINGS section 2.

**P2. Claim: The "attention" series is an equity-volatility news count, and since late 2021 it is mostly exact zeros.** [Figure 1]
- Evidence: team `attention` equals FRED EMVENRGYENVREG in 500 of 500 months, max difference 0.0; the series is the Baker-Bloom-Davis-Kost tracker of newspaper articles on stock-market volatility that mention energy or environmental regulation. Exact zeros: 12 of 441 months before 2021-10 against 39 of 59 after (Fisher p = 1.3e-32), 31 of 48 holdout months. Zero months can never trigger (0 of 50 above threshold).
- Source: `M1_signal_audit_identity.csv`; `M1_signal_audit_zero_counts.csv`; `M1_signal_audit_zero_mechanics.csv`; M1 FINDINGS Q1, Q3.
- Mandatory scope sentence (M1 VERIFY H3c, round 2 G1-G2): the zeros did not change which months the rule traded. Frozen 2021-09 scaling and zeros-as-missing give the same 5 holdout entries, and every team strategy still loses under every counterfactual. Source: `M1_signal_audit_zero_counterfactual_summary.csv`; M1 VERIFY round 2, G2 table. Landing: the label was wrong and the zeros are a data problem, but neither excuses the holdout.

**P3. Claim: The Brown leg is partly an artifact of an undocumented emissions file.** [Figure 2]
- Evidence: the team file is identical to the PS1 course file and records no source, units, scope or vintage; it has 3 groups of exactly equal values and a Util/Fun ratio of 6,051x against 33x across FF49 means for EPA factors. Spearman with EPA is 0.700 over 41 industries. Ships and Aero rank 2nd and 3rd of 41 in the team file but 20th and 31st of 49 on EPA. EPA Green shares 0 of 5 industries with team Green; EPA Brown shares 1 of 5 (Util). The team's Aero and Ships values are 14 to 47 times what their manufacturing NAICS codes imply and 1.9 to 6.0 times the air- and water-transport levels: consistent with, not proof of, a transport mis-mapping (direct-measure rejections survive Holm at 0.036 to 0.050; EPA-based ones do not, 0.052 and 0.114). Aero, Util and Ships deliver 86% of the Original 3m rule's COVID gross P&L.
- Source: `M4_emissions_provenance.csv`; `M4_emissions_team_file_ties.csv`; `M4_emissions_key_numbers.csv`; `M4_emissions_spearman.csv`; `M4_emissions_key_industries.csv`; `M4_emissions_membership.csv`; `M4_emissions_aero_ships_calibration.csv`; M4 FINDINGS Results 1 and 3; 86% from `exchange/01_idea_generation/checks/c02_covid_contributions.csv` (fact-check row 50).

#### 1.3 Evaluation framework, fixed before testing (0.6 p)

**P1. Claim: Two input errors in the team pipeline were fixed before any new test ran.**
- Evidence: (a) the team traded at the close of month t on month-t EMV; the corrected baseline lags EMV and all purification controls one month (Original 3m 2010-2026 net 0.07% becomes 0.73%, verdict unchanged). (b) The missing Oct-2025 CPI print (government shutdown) silenced the purified signal for two months and explains the entire Pure-versus-Original holdout gap (Pure 3m holdout -2.17% becomes -3.82% once CPI is interpolated). Corrected validation alphas: Original 3m 1.62% (t 1.97), Pure 6m 2.33% (t 2.59).
- Source: `logs/replication.md` section 4, items 2 and 5; `M1b_alt_signals_primary.csv`.

**P2. Claim: Every timing claim is tested against the always-on position, with small-sample p-values.**
- Evidence: the null for a timing rule is always-short Brown with the same hedge, scaled by pi = mean |timed position| / mean |always-on position| (D = R^T - pi R^AO). NW(6) t-statistics everywhere, p from t(n-k). The team's normal p-values on 24-month NW(6) t-stats produced "2 of 32 survive Holm"; with t(n-4), 0 of 32 survive (smallest Holm p 0.119). The COVID t is also unstable in the lag: 2.36 (OLS), 2.70 (3 lags), 3.21 (6), 4.00 (12).
- Source: `logs/replication.md` section 4, item 3; M8 PREREGISTRATION section 1 (attribution spec); exchange 01 evaluation ("Three contributions changed the plan", first item); `M3_alpha_beta_ln_vs_benchmark.csv`.

**P3. Claim: A number enters this report only after independent code has produced it too.**
- Evidence: each module has a primary test stated before results and a verifier who imported none of the builder's code, run to a second round; every inferential statistic is logged (8 ledgers, 23,923 rows, 155 primary). M8's pre-registration was written and hashed (SHA-256 e926c3ae...0b51) before run.py existed. Disclosures: M1b and M3 pre-specification cannot be dated (no version control); M2's Q2 primary configuration was printed in a smoke test four minutes before its docstring was written.
- Source: `modules/*/VERIFY.md` (for example M1: 104 + 257 + 34 checks match; M8: 128 of 128); `outputs/tables/*_tests_ledger.csv` (row counts in Section 5E); M8 FINDINGS "PROCESS"; M8 VERIFY section 1; M1b FINDINGS section 10; M3 FINDINGS caveat 6; M2 FINDINGS "Timing record".

#### 1.4 Implementation: risk model, turnover and costs (0.7 p)

**P1. Claim: The traded object is the Brown-leg residual, hedged with a lagged 60-month FF3 model and sized to 5% volatility.**
- Evidence: betas estimated on t-59..t hedge t+1; magnitude min(1, 0.05 / (sqrt(12) sd36)); only the Brown leg is traded (the Green leg never enters the P&L); a look-ahead fuzz test that randomizes every input after three cut dates changes nothing before them.
- Source: `logs/replication.md` "Checked and clean" and "Design notes"; `lib/test_team_pipeline.py::test_no_lookahead`; M8 PREREGISTRATION C10.

**P2. Claim: I widened the risk model three ways, and none rescues the strategy.**
- Evidence: (a) FF5 + UMD + COMEQ, a traded commodity-equity factor (mean of Oil, Coal, Mines, Gold minus RF; correlation 0.66 with the Brown leg; FF5+UMD explain 37% of its variance and leave an insignificant alpha of -0.89%, t -0.24). (b) BOND, the excess return of a constant-maturity 10-year Treasury built from GS10 with duration and convexity (2022 return -15.0% against Damodaran's -17.8%; annual correlation 0.991 over 1954-2025). (c) Conditional betas (Ferson-Schadt) and the Lewellen-Nagel beta-timing decomposition. For M5, a Grinold-Kahn optimizer with a Ledoit-Wolf covariance, a 5% ex-ante tracking limit, a 0.10 box and a carbon bound c'h <= b.
- Source: `M2_christhian_tests_q2_comeq_justification.csv` (use M2 VERIFY round-2 wording, Section 7b); `M3_alpha_beta_bond_validation_summary.csv`; M3 FINDINGS sections 2-3; M5 FINDINGS section 4.

**P3. Claim: Costs are not the binding constraint; the gross return is.**
- Evidence: team costs 10/5/25 bp; discrete rules turn over 1.7 to 5.8 times a year with cost drag at most 0.63%; continuous rules 0.7 to 1.5 times. Uniform break-even costs of the validation alpha (corrected, FF3 hedge): 40 to 100 bp for the signal rules, 211 bp for always-short. The richer FF5+UMD+COMEQ hedge raises overlay turnover 35% to 54% and cuts break-evens to 19 to 50 bp. The holdout alpha is already negative before costs in all 28 zero-cost runs (highest -0.39%).
- Source: `M1b_alt_signals_compact.csv`; `M2_christhian_tests_q4_breakeven.csv`; `M2_christhian_tests_q2_hedge_cost_change.csv`; `M2_christhian_tests_key_numbers.csv` (`holdout_gross_*`); M2 FINDINGS Q4.

#### 1.5 The research program, simplest first (0.8 p, Table 2)

**P1. Claim (roadmap):** The program ran in the order each result demanded, and Table 2 is the study in one table.
- One sentence per stage, with a pointer: replicate and audit (Appendix B); M1 what the signal is; M1b the same machinery fed genuine climate measures and volatility placebos; M2 Christhian's four tests; M3 alpha versus beta (Charishma's Part B); M4 the emissions file; M8 the pre-registered test; then the brief's suggested drivers as alternatives on the same data: emissions tilt (M4), industry momentum (M5), macro-driven timing (M6).
- Landing ("the summary to keep in mind throughout"): no module finds a positive alpha that survives its own pre-specified family; the certified results are negative or descriptive.
- Source: Table 2 rows (Section 4); each module FINDINGS "Primary results".

#### 1.6 ChatGPT as a research assistant: the prompts (0.9 p)

**P1. Claim: The prompts were written as specifications, and every reply was fact-checked with code before the follow-up.**
- Evidence: role ("skeptical buy-side quant refereeing"), our numbers, required headings, pass bars, "label any number you have not computed as a guess", word caps; exchange 01 fact-check scored 52 claims; exchange 02 ran the reply's code on real data.
- Source: `exchange/01_idea_generation/prompt.md`; `exchange/02_coding_support/prompt.md`; both `factcheck.md` files.

**P2. Exchange 01, idea generation (design review).** Asked for at most six design problems ranked by verdict impact, a ranking of the seven teammate proposals (A to G), exactly five new ideas with falsifiable tests, a plan and its three weakest assumptions (993-word prompt, 1,772-word reply). Follow-up (396 words) sent five corrections and asked for one frozen rule for 1993-2009 and an attribution spec; the reply (733 words) supplied the rule M8 pre-registered.
- Source: `exchange/01_idea_generation/interaction.md`; `followup_prompt.md`; `chatgpt_followup_response.md`.

**P3. Exchange 02, coding support (a second implementation).** Asked for a pandas/statsmodels implementation of the frozen test with docstrings, a fixed seed, parameters for every silent reading and pre-run checks (997-word prompt; 985-line script). Follow-up asked for six corrected functions, each with a unit test.
- Source: `exchange/02_coding_support/interaction.md`; `checks/chatgpt_code_v1.py` (verbatim extraction, empty diff against the reply); `checks/chatgpt_code_v2.py`.

**P4. Exchanges 03 and 04 (placeholders).** 03 robustness design (being run now): fill in prompt purpose, reply summary and fact-check counts; if it shaped M7's multiple-testing design, say so here and in 2.7. 04 red team of this draft (to be run): send the compiled draft and ask for the weakest claims and missing tests; record each critique and the action taken.
- Source: `exchange/03_*/` and `exchange/04_*/` when they exist (same file set as 01 and 02).

Landing: full prompts and replies are in Appendix A; the critical evaluation is Section 2.8.

---

### 2 What did I learn (4.0 p)

Page targets below include the exhibits and sum to about 4.0 pages, so Section 2 prose must be terse: at most about 90 words per paragraph, numbers in parentheses, one landing sentence. Not every listed number has to appear; the evidence lists are the menu, and the claim sentence is fixed.

Opening roadmap sentence (one line): "Four findings define the story: the signal is not climate, the trade is a Brown-leg exposure, the in-sample gain is the position rather than the timing, and the one clean test fails."

#### 2.1 The signal is volatility news, and genuine climate measures do not reproduce the result (0.6 p, Table 3; points back to Figure 1)

**P1. Claim: The team signal is overall volatility news plus a topic share that has nothing to do with climate concern.**
- Evidence: joint regression of the team z on z_VIX and z_EMV_overall, 1992-12 to 2026-08: R2 0.169 (HAC F 27.1, p 8.8e-12), overall EMV slope 0.43 (t 5.07), VIX -0.03 (t -0.35); in validation VIX enters negatively (t -2.51). corr(z_MCCC, z_EMV_env) = -0.0004 (p 0.996); corr(z_CPU, z_EMV_env) = 0.123 (p 0.037, Holm 0.074), and its partial correlation given overall EMV is 0.05 (p 0.36). Crossings fall in high overall-EMV months 88% of the time against 64.5% otherwise (Fisher p 0.0006; 0 of 382 circular shifts as extreme); the high-VIX link is borderline (62% against 48.9%; Fisher 0.097, shift 0.113, LPM 0.049). Over 2022-2024, MCCC ran 1.19 to 1.49 sd above its mean and CPU 0.88 to 1.39 sd while the EMV series sat at -1.16 to -0.08 sd, a gap made by its exact zeros (Figure 1, dashed line).
- Source: `M1_signal_audit_decomposition_team_signal.csv`; `M1_signal_audit_decomposition.csv`; `M1_signal_audit_q5_primary_robustness.csv`; `M1_signal_audit_crossings_vix_summary.csv`; `M1_signal_audit_standardized_measures_12m.csv`; M1 FINDINGS Q2, Q4, Q5.

**P2. Claim: Fed genuine climate concern, the same machinery produces neither the in-sample result nor an out-of-sample one.** [Table 3]
- Evidence: validation alphas with t >= 1.96: EMV tracker 4 of 6, MCCC 0 of 6, CPU 0 of 6 (best climate cell CPU Original 6m, 1.81%, t 1.73). All six MCCC holdout alphas are negative (-0.56% to -2.91%); CPU's lie between -1.62% and +0.36%. Smallest Holm p over the 40 primary tests is 1.00 (near-mechanical with 36-39 holdout months; the sign pattern is the evidence). The pure volatility tracker EMV overall comes close to the team signal in validation (mean alpha 1.07% against 1.45%). Predictive ICs of MCCC and CPU for next-month GB and the Brown residual: 8 of 8 null (smallest Holm p 0.62); contemporaneous PST-style slopes have the wrong sign (MCCC -0.093% per sd, t -0.49).
- Source: `M1b_alt_signals_primary.csv`; `M1b_alt_signals_key_numbers.csv` (`*_validation_mean_alpha_6strats`); `M1_signal_audit_predictive_ic_summary.csv`; `M1_signal_audit_contemporaneous_summary.csv`.
- Scope sentence: our legs are low-emission industries, not MSCI-green firms, so this is a null about these legs, not a refutation of PST (M1 FINDINGS Caveats).
- Landing: the validation alpha belongs to the EMV tracker family, not to climate.

#### 2.2 Style and risk exposures: a Brown-leg value and commodity bet with a leaky hedge (0.55 p, Figure 3)

**P1. Claim: The raw spread is short value, profitability and investment, and the value tilt lives in the Brown leg.**
- Evidence: FF3 HML loading -0.233 (t -4.63) over 1970-2026 and -0.298 (t -5.74) post-2010; FF5 alone: HML -0.11, RMW -0.15, CMA -0.25. Exact decomposition post-2010: Brown side -0.437, Green side +0.139; Steel and Ships alone contribute -0.239 of -0.298; Fin, RlEst and Telcm make the Green leg mildly value. COMEQ loading -0.18 (t -8.70) over 1970-2026. GB alpha is insignificant in every long window under seven models (full-sample FF5+UMD 2.2%, t 1.60).
- Source: `M3_alpha_beta_exposures.csv`; M3 VERIFY round 2, fix 6c (FF5 loadings); `M2_christhian_tests_q3_hml_decomposition.csv`; `M2_christhian_tests_q2_spread_controls.csv`; M2 FINDINGS Q3 (use the round-2 wording on rolling flips, Section 7b).
- Suggested wording (M2 FINDINGS Implications): GB is "long financials and real estate plus a few growth industries, short value-priced commodity and industrial producers".

**P2. Claim: The hedge removes most of the factor exposure, and what it misses is market and size leakage, not climate.** [Figure 3]
- Evidence: residual HML after the team hedge is -0.015 to -0.053 post-2010 (corrected baseline). The strategies' Lewellen-Nagel beta-timing term is negative (-0.57% to -1.07% a year; 4 of 6 significant after Holm), and the untimed always-short position carries the same term (-1.35%, p 0.035), so it is a property of the hedged Brown leg. A small momentum tilt (INDMOM loadings +0.038 and +0.054, t 2.12 and 2.59) disappears once UMD enters (t 1.10 and 1.22) and fails BH. GB's BOND loading is 0.132 (t 2.60, Holm 0.019) over 1970-2026 and 0.088 (t 0.60) post-2010. Conditional betas do not move robustly with macro instruments (wild block bootstrap p 0.40 to 0.62).
- Source: `M2_christhian_tests_q2_hedge_cost_post2010.csv`; `M3_alpha_beta_primary_iii.csv`; `M3_alpha_beta_primary_i.csv`; `M3_alpha_beta_ferson_schadt.csv` and `M3_alpha_beta_fs_boot_seeds.csv`; `M5_industry_momentum_gb_regressions.csv`; M5 FINDINGS section 8.
- Landing: the trade is a Brown-leg value and commodity position with a lagged hedge.

#### 2.3 Time patterns: full sample, post-2010, and the last 18 and 12 months (0.6 p, Table 4)

**P1. Claim: Outside COVID, the only t above 2 is in the validation sample the rules were designed on.**
- Evidence (corrected baseline, FF3 hedge, team costs): full live sample (from 1993) Original 6m net 1.08%, alpha 1.32% (t 1.85); post-2010 1.19% and 1.21% (t 1.36); validation 2.09% (t 2.18). Always-short post-2010 alpha 0.73% (t 0.67). Across seven factor models, both baselines and all six rules, the smallest post-2010 p is 0.053 (corrected Pure 6m, FF5). Raw GB: -0.50% a year over 1970-2026, -1.79% post-2010.
- Source: `M2_christhian_tests_strategy_grid.csv` (filter in Section 4, Table 4); `M3_alpha_beta_exposures.csv`; M3 VERIFY round 2, R2.4.

**P2. Claim: The holdout loss is residual Brown performance plus costs, not rates.**
- Evidence: corrected holdout net -0.48% to -2.57% a year; 0 of 900 net-of-cost holdout alphas positive for the six timed rules. With BOND and UMD added, every holdout alpha falls further (team baseline smallest Holm p 0.155; Wald test of UMD = BOND = 0, p 0.25 to 0.73). Rates moved holdout returns by at most about half a point a year, with a sign that depends on the attribution method. Corrected Pure 6m: net -1.84% = leakage -0.24% + residual -1.14% - cost 0.46%. The FF3-hedged Brown leg itself earned +2.82% alpha (t 0.95) in the holdout: Brown beat its hedge. Against the exposure-matched benchmark the 3-month rules lost a further 2.1% a year (t -2.23 to -2.28).
- Source: `M2_christhian_tests_key_numbers.csv`; `M3_alpha_beta_holdout_alpha.csv`; `M3_alpha_beta_attribution.csv`; `M3_alpha_beta_hedged_brown_holdout.csv`; `M3_alpha_beta_ln_vs_benchmark.csv`; M3 FINDINGS 4(ii), 7.

**P3. Claim: The last 18 months are losses for every timed rule, and the last 12 are too short to split into alpha and beta.**
- Evidence: corrected Original 3m last 18 months net -4.51% (alpha -4.05%, t -1.55); last 12 net -5.21% with alpha +1.20% (t 0.30), an uninformative split on 12 observations. Under the team's own same-month timing, Original 3m lost -10.82% alpha (t -4.75) over the last 18 months and -11.31% (t -2.68) over the last 12. Under real-time timing, five recent-window cells have |t| above 2, all losses. Raw GB lost 14.7% and 19.9% a year; its FF3 alphas (-19.2%, NW t -2.79; -32.8%) are not significant with classical OLS standard errors (|t| 0.82 to 1.67).
- Source: `M2_christhian_tests_strategy_grid.csv` (periods last18, last12); `M1b_alt_signals_recent.csv`; M1b VERIFY round 2, R2-2 and R2-3; `M3_alpha_beta_gb_short_window_alpha.csv`.
- Landing: Brown beat Green by a wide margin, the wrong sign for this trade, and the window is too short to call it anything.

#### 2.4 COVID rewarded the position, not the timing (0.45 p, Figure 4)

**P1. Claim: An untimed short of the same leg earns most of the COVID gain.**
- Evidence: real-time EMV Original 3m COVID alpha 6.38% (t 3.62); always-short 4.54% (t 1.96), 71%; paired edge +1.84% (t 0.87, p 0.39); excluding March-April 2020, +0.42% (t 0.18). Corrected Pure 6m held the always-short position in 24 of 24 months. The gain came through leakage of the lagged FF3 hedge (4.76% of 6.87% net: market 1.97, SMB 2.14 points), with a residual of 2.21% (t 1.27); UMD earned -0.58% a year, so momentum added nothing. Aero, Util and Ships carry 86% of the Original 3m COVID gross P&L; dropping Aero takes the 6-month COVID t from 2.07 to 0.03, and on the EPA Brown leg the COVID t-stats are 0.50 and 0.52.
- Source: `M1b_alt_signals_covid_decomposition.csv`; `M1b_alt_signals_covid_attribution.tex`; `M3_alpha_beta_position_overlap.csv`; `M3_alpha_beta_attribution.csv`; `M3_alpha_beta_factor_means.csv`; `exchange/01_idea_generation/checks/c02_covid_contributions.csv` and `c02_leave_one_out.csv`; `M4_emissions_team_rule_rerun.csv`.

**P2. Claim (scope): The COVID window cannot separate a climate trigger from being short the Brown residual in 2020-21.**
- Evidence: the December 2019 crossing is shared with CPU, the one climate-consistent fact in the module. The pre-specified placebo rule says the climate reading fails (EMV overall reproduces the gain in 4 of 6 rules under real-time timing, exactly on the boundary; 6 of 6 under team timing), but for Original 3m the volatility placebos fall short under real-time timing and CPU matches it (6.44% against 6.38%). Inference rests on 22 to 24 observations with NW(6); with t(n-4) p-values none of the team's 32 claims survives Holm.
- Source: `M1b_alt_signals_placebo_covid.csv`; M1b FINDINGS section 6 with VERIFY round-2 R2-1 wording; `logs/replication.md` item 3.

#### 2.5 The pre-registered 1994-2009 test (0.45 p, Table 5; Figure 5 optional)

**P1. Claim: The rule was frozen before the window was touched, and the protocol is on the record.**
- Evidence: rule adopted from exchange 01's follow-up (share of overall EMV, zeros as missing, the 6-month rule, a four-part pass bar) with my two amendments (a one-month publication lag, and a start set by the first month the rule can fire), plus a GS10 bond return with duration and convexity in place of its guessed -8 x change-in-yield duration term; PREREGISTRATION.md saved once at 03:30:46 PDT, before run.py (03:35:43) and the primary run (03:37:46); 32 implementation choices C1-C32; SHA-256 e926c3ae...0b51; window 1994-03 to 2009-12 (190 months), the first month the rule can fire. Disclosed contamination: the rule was chosen after 2010-2026 had been seen, and our team's macro-state notebook used 192 pre-2010 months of residuals, so the window is out of sample for returns, not for design.
- Source: M8 FINDINGS "PROCESS", "WINDOW", Caveats 1-2; M8 VERIFY section 1 and round 2 (run.py birth time now reads 06:05:07; original birth recorded in `corrections/pre_correction_0341/manifest.json`).

**P2. Claim: The rule meets one of four components and sits at the centre of its own null.**
- Evidence: (i) timing alpha -0.18% a year, NW(6) t -0.27 (one-sided p 0.605): FAIL. (ii) calendar shuffle p 0.478; shuffled alphas have median -0.22% and 5th to 95th percentiles -1.30% to +0.91%: FAIL. (iii) 10 independent episodes: PASS. (iv) drop-one alphas Util -0.61%, Ships +0.03%, Aero +0.01%, Steel -0.19%, BldMt -0.11%: FAIL. Timed net +0.51% a year against always-on +0.65%. The team's own signal, lagged, through the same engine: +0.69% (t 1.00), shuffle p 0.128, FAIL. The crossings are not volatility events (7 of 33 in the top quintile of overall EMV against a 20% base rate).
- Source: `M8_passbar.csv`; `M8_attribution.csv`; `M8_strategy_summary.csv`; `M8_shuffle_draws.csv`; `M8_crossings.csv`; M8 FINDINGS (i)-(iv), SECONDARY, CROSSINGS.

**P3. Claim: The test had limited power, and the failure does not depend on any open reading.**
- Evidence: in position 142 of 190 months; the shuffle had 39 free months to move 10 blocks, so a pass needed alpha above about +0.9% a year. The verifier rebuilt all 128 published numbers from raw files; no alternative reading comes near t = 2 (a 3-month hold gives -0.96%, t -1.30). ChatGPT's independent implementation reaches the same verdict (-0.19%, t -0.25).
- Source: M8 FINDINGS Caveat 3 (39 free months); M8 VERIFY sections 3-4; `exchange/02_coding_support/factcheck.md` Summary.
- Landing: a pass would have been weak evidence; a fail is not weakened.

#### 2.6 Alternatives on the same data (0.45 p)

**P1. Claim: A complete supply-chain ranking flips the raw spread but does not produce an alpha.**
- Evidence: EPA 5v5 GB FF5+UMD alpha post-2010 4.7% (t 1.52, p 0.129), the pre-specified primary; no post-2010 variant significant (smallest Holm p 0.471); robust to leg membership (drop-one p 0.087 to 0.264). The raw spread moves from -1.8% to +6.4% a year post-2010, but 10.8 of the 13.2 points over the last 18 months are market beta. The ranking effect alone (EPA minus team, 8.2% a year, t 2.84) is suggestive only (Holm 0.071 over the 16 shown, 0.178 over 42). The full-sample alpha comes from short CMA and UMD loadings on a sort applied back to 1970.
- Source: `M4_emissions_primary_test.csv`; `M4_emissions_post2010_family.csv`; `M4_emissions_primary_sensitivity.csv`; `M4_emissions_perf.csv`; `M4_emissions_recent_beta.csv`; M4 FINDINGS "Exploratory: EPA minus team".

**P2. Claim: Carbon-aware industry momentum is the UMD premium in industry form, and a carbon limit costs no detectable IR on it.**
- Evidence: net 8.52% a year (Sharpe 0.47) but FF5+UMD alpha 1.74% (t 1.09) full sample and 1.86% (t 0.71) post-2010 (Holm 0.823); UMD beta 0.99, R2 0.67; alpha break-even about 24 bp one-way; worst month -38.75% (2009-04); every variant's holdout alpha negative. At bound b = -1 the long book's WACI falls 60% with an IR change of -0.005 (95% CI -0.110 to +0.096), so the test cannot rule out a loss of about 0.1; post-2010 the screened books' Sharpes are 0.02 to 0.12 lower, none significant under convention X. The optimizer's post-2010 alpha (3.12%, t 2.18) does not beat equal weight (p 0.155) and is -0.34% in the holdout. Last 18 and 12 months: net 3.90% and 8.58%, CAPM alphas -2.60% and -5.19%.
- Source: `M5_industry_momentum_alphas.csv`; `M5_industry_momentum_perf_periods.csv`; `M5_industry_momentum_cost_breakeven.csv`; `M5_industry_momentum_worst_months.csv`; `M5_industry_momentum_optimizer_frontier.csv`; `M5_industry_momentum_carbon_cost_test.csv`; `M5_industry_momentum_carbon_screens.csv`; `M5_industry_momentum_optimizer_periods.csv`; `M5_industry_momentum_optimizer_vs_primary.csv`.

**P3. Claim: A disciplined shrinkage model refuses to time the spread, and attention makes forecasts worse.**
- Evidence: pre-registered ridge CV picks the maximum penalty in 439 of 439 (Spec A) and 319 of 319 (Spec B) monthly refits, so every forecast is the historical mean (R2_OOS 0.000%). At every fixed penalty, adding attention lowers R2_OOS (-1.07% to -0.08% over 2000-2026); in the LMN variant attention costs 1.04% a year (t -2.38); on the team's own Brown-residual target its OOS R2 is -0.74%. The recent timing Sharpe (0.64 and 0.99 over the last 12 months) is the prevailing-mean portfolio, short GB since 2022-05 (A) and 2021-12 (B).
- Source: `M6_factor_timing_oos_primary.csv`; `M6_factor_timing_oos_robustness.csv`; `M6_factor_timing_lmn_attn_increment.csv`; `M6_factor_timing_team_target_check.csv`; `M6_factor_timing_histmean_sign.csv`; `M6_factor_timing_timing_vs_prevmean.csv`; `M6_factor_timing_cv_design.csv` (scope: the 100% share belongs to the pre-registered CV design).
- Landing: every alternative lands where the audit did: exposure, not alpha.

#### 2.7 Robustness, multiple testing and limitations (0.4 p)

**P1. Claim: Across 23,923 logged tests, no positive alpha survives its pre-specified family, and the tests had the power to find effects that exist.**
- Evidence: 8 ledgers, 155 primary, 8,113 robustness, 15,485 exploratory, 82 reference, 88 placebo rows. M2 grid: 8,091 alpha tests, 0 Holm survivors, 0 positive and 27 negative BH survivors. Power: the same families certify negative or descriptive effects (M3 beta-timing term 4 of 6 Holm; M2 Q3 HML loadings Holm <= 0.017; M1 zero-rate break p 1.3e-32); on 100 synthetic null seeds the calendar shuffle rejects 6 times at 5% while the pre-registered NW(6) t over-rejects (13), a bias that cannot rescue a negative alpha. [M7 placeholder: project-wide Holm/BH counts, adjusted p of the best positive result in each module.]
- Source: `outputs/tables/*_tests_ledger.csv` (counts in Section 5E); `M2_christhian_tests_key_numbers.csv`; `exchange/02_coding_support/factcheck.md` R2.9; M7 outputs when delivered.
- Nominal positives to name and retire in one sentence each (all exploratory): M5 COVID alpha 15.80% (BH 0.022, classical t 1.58); M6 DGS10 post-2010 (one-sided p 0.018 and 0.020, BH q 0.34); M1b paired COVID edge over placebos (smallest Holm 0.051); M4 EPA-minus-team (Holm 0.071).

**P2. Limitations (heading "Limitations"; opens "Several limitations should be kept in mind."; one limit per sentence):**
- One undated emissions snapshot (team) or one 2022-vintage factor set (EPA) is applied back to 1970: look-ahead in leg membership (M4 Caveats).
- FRED, EMV and MCCC series are final vintages, not real-time; the one-month EMV lag is an assumption, not a verified release calendar (M3 caveat 7).
- MCCC and CPU end in 2025 (36 and 39 holdout months) and cover neither recent window (M1b section 10).
- A 48-month holdout has expected t = 2 x Sharpe, so it cannot confirm a small edge, though a significantly negative holdout is still evidence (`logs/lit_digest.md` 11.3).
- COVID, last-18 and last-12 inference rests on 12 to 24 observations; NW(6) there is unreliable.
- Pre-specification is timestamped only for M8 (and M2 through a transcript); M1b and M3 cannot be dated.
- M8's rule was designed after 2010-2026 was seen.
- Costs are linear, with no market impact or shorting costs; the test is industry-level, so it says nothing about firm-level carbon premia (Bolton-Kacperczyk).
- BOND is built from monthly-average yields (AR(1) 0.31) and is partly realized a month early (M3 caveat 1).

#### 2.8 Critical evaluation of ChatGPT (0.45 p)

**P1. Claim: ChatGPT was a sharp referee on the numbers it was given and changed the plan three times.**
- Evidence: exchange 01 fact-check: 52 checkable claims, 26 correct, 15 partly correct, 6 wrong, 5 unverifiable; arithmetic and citations sound. The three contributions: test timing against the always-on position (on seen data the timed-minus-always-on FF5+UMD alpha peaks at t 1.09); the unseen pre-2010 window (became M8); Aero and Ships as odd Brown members (86% of COVID gross P&L with Util). Wrong claims: the holdout was lost to duration (the hedged Brown leg's holdout rate beta has t 0.05); more NW lags fix inference (they push the COVID t from 3.21 to 5.32); the IC flip is "about one SE" (1.3-1.6 SE raw and purified, 2.8-2.9 for the continuous signals); idea-1 dates.
- Source: `exchange/01_idea_generation/evaluation.md`; `factcheck.md` Summary and rows 13, 22, 26, 32-33.

**P2. Claim: It never asked what the signal measures, and it did not push back on a confident user.**
- Evidence: my prompt passed on the label "climate-transition attention" with no source and ChatGPT accepted it, placing the coverage risk in the wrong period (pre-2010 zero share 0.8% to 4.2%). My follow-up told it that the holdout "tested a near-binary signal, not the one we validated"; it accepted and amplified that premise ("the holdout ran on a different, near-binary signal. That explains the holdout") and built its zero rule on it, and the M1 verifier later showed the zeros changed no holdout trade. A failure of my prompt as much as of the tool.
- Source: `exchange/01_idea_generation/evaluation.md` ("It never asked what attention measures"); `followup_prompt.md`; `chatgpt_followup_response.md` (opening paragraph); M1 VERIFY H3c and round 2 G2.

**P3. Claim: Trust its formulas and audit its interfaces.**
- Evidence: the 985-line script ran first time and reached the same verdict (-0.19%, t -0.25, against -0.18%, t -0.27). Two readings explain every numeric gap; aligned, it reproduces all 15 coefficients and all 5,000 shuffle draws to 3.3e-13. Of six problems, three came from my prompt (FF5 SMB in the hedge, a sign-only drop-one test, an open "seen" window end) and three from ChatGPT (a hard-coded burn-in, a clipped synthetic GS10 that broke its own positive control, 4% of a planted effect reaching alpha, and a look-ahead test that missed 2 of 6 injected bugs). The follow-up fixed all six and broke one interface: a literal drop-in crashes, and the obvious patch runs silently on a window 14 months too long.
- Source: `exchange/02_coding_support/evaluation.md`; `factcheck.md` Summary, sections 3-6, R2.5-R2.8.

**P4. Claim (moral, scoped):** ChatGPT is a cheap second implementation and a useful referee on stated numbers, never a verifier and never a source of facts about our data; this is a result about these prompts, not the tool. [Placeholders: 03 robustness design outcome; 04 red-team findings and the changes they forced.]

#### 2.9 Verdict (0.1 p, 3 to 4 sentences)

Restate the question in past tense ("Our team asked whether ..."), answer in one word, then the three-rule playbook (read the label; benchmark timing against the always-on position; freeze one rule for the last clean window), then the practitioner value of the negative results ("each one retired an idea before it could cost money").

---

## 4. Main-body exhibits (5 figures maximum, 5 tables maximum)

Caption rules (style guide section 4): figure captions below, table captions above; each has a short title fragment, how to read it, and the takeaway as a full sentence. The existing .tex tables carry builder captions inside their own `\begin{table}` wrappers, so no main-body table is `\input` unchanged. Recommended mechanics: a small `report/make_tables.py` that writes tabular-only `.tex` files (in `report/tables/`) from the CSVs, so the report controls captions. Existing figure files are used as is via `\graphicspath{{../outputs/figures/}}`.

### Figures

**Figure 1 (Section 1.2, referenced in 2.1).** `outputs/figures/M1_signal_audit_standardized_measures.pdf`. Shows the 12-month trailing standardized levels of the team series, MCCC and CPU, 2003-2025, with the zeros-excluded team series dashed.
> **Figure 1:** What the signal measures. Twelve-month trailing means of standardized log levels, 2003-01 to 2025-06: our team's "attention" series (FRED EMVENRGYENVREG, orange), the Ardia et al. media climate-concern index (green) and the Gavriilidis climate policy uncertainty index (purple); the dashed line drops the series' exact zeros. Climate concern rose through 2022-2025 while the team series fell into its zero regime, and over their common sample the two z-scores are uncorrelated (r = -0.0004).

**Figure 2 (Section 1.2).** `outputs/figures/M4_emissions_intensity_scatter.pdf`. Team file against EPA supply-chain intensity in levels (a) and ranks (b).
> **Figure 2:** The Brown leg as delivered. Panel (a) plots the team's undocumented intensity file against EPA supply-chain GHG intensity (kg CO2e per 2022 dollar, log scales) for the 41 common industries; panel (b) compares ranks, with the top five of each ranking shaded. The rankings agree broadly (Spearman 0.70), but two of the five Brown industries, Ships and Aero, rank 20th and 31st of 49 on EPA factors, and EPA's Green leg shares no industry with the team's.

**Figure 3 (Section 2.2).** `outputs/figures/M3_alpha_beta_attribution.pdf`. Per-period split of net return into factor leakage, residual and cost for corrected Pure 6m and Continuous pure.
> **Figure 3:** What the traded position earned, window by window. Each bar splits the annualized net return of corrected Pure 6m (top) and Continuous pure (bottom) into leakage of the lagged FF3 hedge by factor (market, SMB, HML, UMD, BOND), the residual non-factor return and trading cost; diamonds mark the net return. Betas come from centered 36-month windows, so the split is descriptive and ex post. The COVID gain is mostly market and size leakage, and the holdout loss is residual Brown performance plus costs, not rates.

**Figure 4 (Section 2.4).** `outputs/figures/M1b_alt_signals_covid_paths.pdf` (the corrected version: compounds 2020-01 to 2021-12 from 0; M1b VERIFY round 2 issue C resolved).
> **Figure 4:** The COVID window. Cumulative net return over 2020-01 to 2021-12 of the Original 3m rule (left) and the continuous rule (right) under real-time timing, one line per attention measure, against the signal-free always-short Brown position (dashed); shading marks March and April 2020. The untimed position earns 71% of the team signal's alpha, and the rule's edge over it (+1.84% a year, t = 0.87) is within noise.

**Figure 5 (Section 2.5, optional; first to move to Appendix C).** New one-panel figure `outputs/figures/M8_shuffle_null.pdf` built from `outputs/tables/M8_shuffle_draws.csv` (histogram of 5,000 shuffled timing alphas, vertical line at the real alpha, dashed line at the approximate pass threshold of +0.9% a year). Fallback: the existing `outputs/figures/M8_share_signal.pdf` (three stacked panels, taller). Follow the `dataviz` skill and the existing plot style (`lib/plotstyle.py`).
> **Figure 5:** The frozen test in one figure. Timing alpha of the rule in 5,000 calendar shuffles that move its ten hold blocks to random dates inside 1994-03 to 2009-12, with the rule's own alpha marked (-0.18% a year, t = -0.27). The rule sits at the centre of its own null (one-sided p = 0.478), so the one unseen window gives its timing no credit.

### Tables

**Table 1 (Section 1.2). Data.** New compact table (about 10 rows: source, series, span, role). Built by hand from the FINDINGS "Data" sections listed in 1.2 P1; no existing .tex.
> **Table 1:** Data. Each series, its source, span and role in the study. Returns are monthly decimals at month-end; every input used at the end of month t is published by then, with the EMV trackers lagged one month.

**Table 2 (Section 1.5). The research program in one table.** New compact table, one row per module (Replication, M1, M1b, M2, M3, M4, M5, M6, M8, M7), columns: question; primary test fixed in advance; headline statistic; adjusted p within the pre-specified family; verdict. Row content (all from the FINDINGS "Primary" sections and ledgers):
- Replication: 32 of 32 team Table 1 cells reproduce; 11 audit findings (Appendix B).
- M1: team z on VIX and overall EMV, R2 0.169 (p 8.8e-12); corr with MCCC -0.0004 (Holm 0.996), CPU 0.123 (Holm 0.074); 8 predictive ICs null (min Holm 0.62). Verdict: not climate concern.
- M1b: 40 primary tests, no positive holdout alpha (min Holm 1.00); placebo rule fails on its boundary (4 of 6). Verdict: validation alpha is EMV-family specific.
- M2: Q1, Q2, Q4 (14 tests each) 0 positive survivors; Q3 HML loadings -0.233/-0.298 FF3 (Holm <= 0.017). Verdict: no alpha left; value tilt is Brown.
- M3: (i) BOND loading 0.132 (Holm 0.019) full, 0.088 post-2010; (ii) holdout alphas more negative with BOND and UMD (min Holm 0.155); (iii) beta-timing term negative, 4 of 6 Holm, shared by always-short. Verdict: beta, not alpha.
- M4: EPA 5v5 post-2010 FF5+UMD alpha 4.7% (t 1.52, p 0.129). Verdict: ranking unsound, no alpha.
- M5: P1 1.74% (t 1.09), P2 1.86% (t 0.71), Holm 0.823; carbon b = 0 IR change +0.010 (p 0.328, weak test); INDMOM in GB -0.062 (Holm 0.211). Verdict: UMD in industry form.
- M6: R2_OOS 0.000% (Holm 1.00, 4 tests); attention increment 0 (Holm 1.00); timing minus static +0.84% (t 1.17), +0.66% (t 0.45). Verdict: nothing to time.
- M8: FAIL, 1 of 4 (alpha -0.18%, t -0.27; shuffle p 0.478).
- M7: [placeholder: ledger-wide counts and survivors].
> **Table 2:** The study in one table. Each row is one module: the question it asked, the primary test fixed before its results, the headline statistic, the adjusted p-value within its pre-specified family, and the verdict. No module finds a positive alpha that survives its own family; the results that do survive correction are negative or descriptive.

**Table 3 (Section 2.1). The same machinery, three signals.** New compact tabular from `outputs/tables/M1b_alt_signals_primary.csv` (six strategy rows; keep the two continuous-weight IC rows at most). The existing `M1b_alt_signals_primary.tex` has the right content but a builder caption inside its own float; use it only in Appendix C.
> **Table 3:** The same machinery, three signals. FF3 alpha (% a year, NW(6) t) of our team's six rules under real-time timing when fed the EMV tracker, the media climate-concern index (MCCC) or climate policy uncertainty (CPU). Validation is 2010-01 to 2022-07; the holdout runs from 2022-08 to each measure's last usable month (48, 36 and 39 months). Only the EMV tracker produces validation alphas near t = 2, and every MCCC holdout alpha is negative.

**Table 4 (Section 2.3). Time patterns.** New compact table. Filter `outputs/tables/M2_christhian_tests_strategy_grid.csv` on legs = L5, baseline = corr, hedge = FF3, costs = team, eval_id = E:FF3; columns Original 3m, Original 6m, Continuous raw, Always-short Brown (net return and alpha with t); add the raw GB spread from `outputs/tables/M3_alpha_beta_exposures.csv` (asset GB, model FF3). Rows: full live, post-2010, validation, holdout, COVID, last 18, last 12. Add one note row with the team-timing Original 3m last 18 and 12 months (baseline = team). Preview of the values (FF3 alpha %, t; regenerate from the CSVs):

| Window | Original 3m | Original 6m | Continuous raw | Always-short | GB raw mean; FF3 alpha |
|---|---|---|---|---|---|
| Full live (from 1993; GB from 1970) | 0.44 (0.75) | 1.32 (1.85) | 0.36 (1.18) | 0.79 (0.92) | -0.50; 0.54 (0.41) |
| Post-2010 | 0.79 (1.04) | 1.21 (1.36) | 0.24 (0.83) | 0.73 (0.67) | -1.79; -1.12 (-0.49) |
| Validation | 1.62 (1.97) | 2.09 (2.18) | 0.46 (1.40) | 1.39 (1.12) | -0.65; -0.55 (-0.22) |
| Holdout | -2.16 (-1.90) | -1.97 (-1.30) | -0.58 (-1.33) | -1.72 (-1.09) | -5.38; -4.59 (-0.99) |
| COVID 2020-21 | 6.38 (3.62) | 3.99 (1.79) | 1.95 (2.68) | 4.54 (1.96) | 1.78; -1.04 (-0.24) |
| Last 18 | -4.05 (-1.55) | -4.06 (-1.80) | -1.74 (-2.19) | -6.25 (-1.87) | -14.70; -19.19 (-2.79) |
| Last 12 | 1.20 (0.30) | 1.03 (0.18) | -1.25 (-0.72) | -3.39 (-0.52) | -19.94; -32.80 (-5.65) |

Net returns for the same cells are in the same CSV (`perf_ann_net`), for example last 18 months net -4.51%, -1.35%, -0.73%, -1.07%. Footnote the GB last-18/12 alphas: 4 to 14 degrees of freedom, not significant with classical OLS standard errors (`M3_alpha_beta_gb_short_window_alpha.csv`).
> **Table 4:** Time patterns. Annualized net return and FF3 alpha (NW(6) t) of three corrected-baseline rules, the signal-free always-short Brown position and the raw Green-minus-Brown spread, by window. p-values use t(n-4), so with 18 and 12 observations p < 0.05 needs |t| above 2.14 and 2.31. Outside the 24-month COVID window, the only positive t above 2 is in the validation sample the rules were designed on, and over the last 18 months every timed rule lost money.

**Table 5 (Section 2.5). The frozen test.** New compact portrait table from `outputs/tables/M8_passbar.csv` plus `M8_strategy_summary.csv` (rows (i) to (iv) and the verdict; columns bar, primary result, secondary result). The existing `M8_passbar.tex` is 216 pt too wide for a portrait page at 1 in margins (35 pt too wide even in landscape at 1 in; M8 VERIFY round 2), so it goes to Appendix C only in landscape.
> **Table 5:** The frozen 1994-2009 test. Pre-registered pass bar for the EMV-share rule (primary) and, for context, our team's own signal lagged one month (secondary), 1994-03 to 2009-12; all four components had to pass. The rule meets one of four and our team's signal two of four, so both fail and the recommendation stands.

### Existing .tex tables that can be `\input` directly (Appendix C only; each carries its own float and builder caption)

Checked to compile with tectonic by the module verifiers unless noted:
- M1: `M1_signal_audit_zero_counts.tex`, `M1_signal_audit_decomposition_team_signal.tex`, `M1_signal_audit_predictive_ic_summary.tex`, `M1_signal_audit_contemporaneous_summary.tex`, `M1_signal_audit_zero_counterfactual_summary.tex`. Fix before use: `M1_signal_audit_crossings_vix_summary.tex` prints p = 0.000 (print "<0.001", "0/382"); `M1_signal_audit_q5_primary_robustness.tex` prints r = -0.000 (print -0.0004) (M1 VERIFY round 2, recommended c).
- M1b: `M1b_alt_signals_covid_attribution.tex`, `M1b_alt_signals_placebo_covid.tex`, `M1b_alt_signals_recent.tex`, `M1b_alt_signals_crossings.tex`, `M1b_alt_signals_primary.tex`.
- M2: `M2_christhian_tests_summary_best_case.tex`, `M2_christhian_tests_q3_hml_contributions.tex`, `M2_christhian_tests_q1_table1_corr.tex`, `M2_christhian_tests_q2_spread_controls.tex`, `M2_christhian_tests_q4_costs_corr.tex`.
- M3 (tabular only, no float; wrap with a caption): `M3_alpha_beta_holdout_alpha.tex` (13 columns: needs `\resizebox` or landscape), `M3_alpha_beta_ln_post2010.tex`, `M3_alpha_beta_attribution.tex`, `M3_alpha_beta_ferson_schadt.tex`, `M3_alpha_beta_bond_hedge_rerun.tex`, `M3_alpha_beta_bond_validation.tex`.
- M4: `M4_emissions_key_industries.tex`, `M4_emissions_aero_ships_calibration.tex`, `M4_emissions_membership.tex`, `M4_emissions_post2010_family.tex`, `M4_emissions_primary_sensitivity.tex`, `M4_emissions_team_rule_rerun.tex`, `M4_emissions_recent_beta.tex`.
- M5: `M5_industry_momentum_perf_periods.tex`, `M5_industry_momentum_alphas.tex`, `M5_industry_momentum_cost_sensitivity.tex`, `M5_industry_momentum_carbon_screens.tex`, `M5_industry_momentum_optimizer_frontier.tex`, `M5_industry_momentum_carbon_cost_test.tex`, `M5_industry_momentum_gb_regressions.tex`.
- M6: `M6_factor_timing_oos_primary.tex`, `M6_factor_timing_cv_design.tex`, `M6_factor_timing_oos_robustness.tex`, `M6_factor_timing_team_target_check.tex`, `M6_factor_timing_portfolio.tex`.
- M8: `M8_attribution.tex`, `M8_decomposition.tex`, `M8_drop_one.tex`, `M8_crossings.tex` (new layout fits portrait), `M8_bond_check.tex`; `M8_passbar.tex` and `M8_strategy_summary.tex` landscape only.

---

## 5. Appendix plan

### Appendix A. ChatGPT interactions (all four)

For each exchange, in this order: purpose and date; prompt verbatim; reply verbatim (or a faithful summary with the full text in A.5); follow-up prompt verbatim; follow-up reply; fact-check verdict counts; evaluation verbatim. Each exchange opens with a four-line box: what I asked, what came back, what I verified, what I kept.

- **A.1 Exchange 01, idea generation (design review).** Files: `exchange/01_idea_generation/prompt.md` (993 words, verbatim), `chatgpt_response.md` (1,772 words, verbatim), `followup_prompt.md` (verbatim), `chatgpt_followup_response.md` (733 words, verbatim), `evaluation.md` (verbatim). Fact-check: summary paragraph plus a condensed claims table (52 claims: 26 C, 15 P, 6 W, 5 U) from `factcheck.md`, and the "Proposed tests that I ran" table. Check scripts listed from `exchange/01_idea_generation/checks/` (c01 to c11).
- **A.2 Exchange 02, coding support (second implementation).** Files: `exchange/02_coding_support/prompt.md` (verbatim), a faithful summary of `chatgpt_response.md` (7,110 words, mostly the 985-line script) with the prose sections (assumptions list, pre-run checks) verbatim; `followup_prompt.md` (verbatim); summary of `chatgpt_followup_response.md` (4,745 words) with its prose verbatim; `evaluation.md` (verbatim); from `factcheck.md` the Summary, the run log table, the bug list (section 6), R2 Summary and R2.9 (null-seed size check). Full code in A.5.
- **A.3 Exchange 03, robustness design (being run now).** Same layout. Slot its outcome into 1.6 P4, 2.7 P1 (if it designed the M7 family or corrections) and 2.8 P4.
- **A.4 Exchange 04, red team of the draft (to be run).** Same layout, plus a table: critique, whether I accepted it, what changed in the report (section and sentence). Slot into 2.8 P4.
- **A.5 Full transcripts.** Full text of every reply, including `exchange/02_coding_support/checks/chatgpt_code_v1.py` (985 lines) and `checks/chatgpt_code_v2.py` (1,560 lines) via `\lstinputlisting`. Compile risk: the transcripts contain non-ASCII characters (en dash, minus sign, arrows, approximately-equal, less-or-equal, greater-or-equal, square root, Delta). Tectonic is XeTeX, but the preamble loads T1 lmodern, so glyphs may drop silently. Test one transcript early; if glyphs drop, either load a Unicode mono font for listings only (DejaVu Sans Mono is installed) or write ASCII copies with a disclosed character map (`report/transcripts/`, built by a small script). pandoc is not installed.

### Appendix B. Replication and audit of our team's pipeline

Source: `logs/replication.md` (all sections) and `lib/test_team_pipeline.py`.
- B.1 How reproduction was checked: steps A to D (regenerated team tables max diff 3.8e-15; library vs committed tables; bitwise match to every intermediate object; all 32 write-up Table 1 cells and the text claims); 14 tests pass in about 20 s; runtime 1.9 s against 36.5 s for the team scripts.
- B.2 Audit findings, ordered by impact, as a compact table (item, effect on conclusions, status now):
  1. Zeros in the holdout (65%). Status: real, but superseded as an explanation by M1 (the zeros changed no holdout trade; M1 VERIFY H3c).
  2. Missing Oct-2025 CPI explains the whole Pure-versus-Original holdout gap.
  3. "2 of 32 survive Holm" becomes 0 of 32 with t(n-4); COVID t unstable in lags.
  4. The continuous variant's improvement is mostly de-leveraging (mean |position| 0.14-0.16 against 0.26-0.47); vol-matched paired p-values rise (0.014 to 0.062; 0.072 to 0.829; 0.031 to 0.145; 0.023 to 0.148).
  5. Same-month EMV timing (lag sensitivity).
  6. `active_months` overstated (96 reported against 75 held for Original 3m).
  7. Emissions file limits (41 of 49, static snapshot, ties, Coal 9th).
  8. Write-up text numbers slightly off (volatility cut 52-67%, holdout loss cut 70-84%, residual HML -0.040 to -0.061).
  9 to 11. IC window boundary, cost timing, data vintage (negligible).
- B.3 Checked and clean (look-ahead fuzz test, hedge timing, annualization, Holm, bootstrap inversion, FF49 includes dead firms).
- B.4 Design notes (only the Brown leg is traded; the buy-and-hold benchmark is not like-for-like).

### Appendix C. Module-by-module supporting tables and figures

One subsection per module, each opening with two sentences (question, verdict) and a pointer to its FINDINGS and VERIFY files. Suggested content (about two tables and one or two figures each):
- **C.1 M1 signal audit.** Tables `M1_signal_audit_zero_counts.tex`, `M1_signal_audit_decomposition_team_signal.tex`, `M1_signal_audit_crossings_vix_summary.tex` (after the p-format fix), `M1_signal_audit_predictive_ic_summary.tex`. Figures `M1_signal_audit_emv_vs_vix.pdf` (level with zero ticks and VIX), `M1_signal_audit_rule_mechanics.pdf` (frozen-scaling counterfactual panel), `M1_signal_audit_ic_by_period.pdf`.
- **C.2 M1b alternative signals.** Tables `M1b_alt_signals_primary.tex` (full, with ICs), `M1b_alt_signals_placebo_covid.tex`, `M1b_alt_signals_covid_attribution.tex`, `M1b_alt_signals_recent.tex`. Figures `M1b_alt_signals_alpha_t_heatmap.pdf`, `M1b_alt_signals_crossings.pdf`.
- **C.3 M2 Christhian's four tests.** Tables `M2_christhian_tests_q1_table1_corr.tex`, `M2_christhian_tests_q2_spread_controls.tex`, `M2_christhian_tests_q3_hml_contributions.tex`, `M2_christhian_tests_q4_costs_corr.tex`, `M2_christhian_tests_summary_best_case.tex`. Figures `M2_christhian_tests_hml_decomposition.pdf`, `M2_christhian_tests_rolling_hml_industries.pdf`, `M2_christhian_tests_cost_sensitivity.pdf`.
- **C.4 M3 alpha versus beta.** Tables `M3_alpha_beta_holdout_alpha.tex` (landscape or resizebox), `M3_alpha_beta_ln_post2010.tex`, `M3_alpha_beta_ferson_schadt.tex`, `M3_alpha_beta_bond_hedge_rerun.tex`, `M3_alpha_beta_bond_validation.tex`. Figures `M3_alpha_beta_rolling_betas.pdf`, `M3_alpha_beta_decomposition.pdf`, `M3_alpha_beta_holdout_alpha_bond.pdf`, `M3_alpha_beta_bond_validation.pdf`.
- **C.5 M4 emissions audit.** Tables `M4_emissions_key_industries.tex`, `M4_emissions_aero_ships_calibration.tex`, `M4_emissions_post2010_family.tex`, `M4_emissions_primary_sensitivity.tex`, `M4_emissions_team_rule_rerun.tex`. Figures `M4_emissions_cum_gb.pdf`, `M4_emissions_energy_legs.pdf` (and Figure 2 if it is cut from the body).
- **C.6 M5 industry momentum.** Tables `M5_industry_momentum_perf_periods.tex`, `M5_industry_momentum_alphas.tex`, `M5_industry_momentum_carbon_screens.tex`, `M5_industry_momentum_carbon_cost_test.tex`, `M5_industry_momentum_gb_regressions.tex`. Figures `M5_industry_momentum_carbon_frontier.pdf` (the Grinold-Kahn carbon frontier), `M5_industry_momentum_cumulative.pdf`, `M5_industry_momentum_waci.pdf`.
- **C.7 M6 shrinkage timing.** Tables `M6_factor_timing_oos_primary.tex`, `M6_factor_timing_cv_design.tex`, `M6_factor_timing_oos_robustness.tex`, `M6_factor_timing_team_target_check.tex`. Figures `M6_factor_timing_shrinkage_path.pdf`, `M6_factor_timing_timing_vs_static.pdf`, `M6_factor_timing_gw_cumsse.pdf`.
- **C.8 M8 frozen test.** The full PREREGISTRATION.md text (it is short and is the protocol of record); tables `M8_attribution.tex`, `M8_decomposition.tex`, `M8_drop_one.tex`, `M8_crossings.tex`, `M8_bond_check.tex`, `M8_passbar.tex` and `M8_strategy_summary.tex` (landscape). Figure `M8_share_signal.pdf` (and Figure 5 if cut).

### Appendix D. Code snippets (which functions, from which files)

Show short excerpts with `\lstinputlisting[firstline=..,lastline=..]` so the code in the report is the code that ran:
- D.1 The team trade, ported: `lib/team_pipeline.py` `rolling_factor_model` (the one-month-lagged hedge), `state_position` and `_magnitude` (5% volatility target, cap), `asset_strategy_returns` (asset and overlay costs charged at t+1), `expanding_threshold` and `cross_and_holds`.
- D.2 The frozen rule: `modules/M8_frozen_pre2010/run.py` `share_signal` (zeros as missing, 48 of 60, off rule), `decision_hold` (publication lag), `attribution` (D_t regression, k = 15, t(n-k)), `shuffle_test` (block placement), `par_bond_dc` and `build_bond` (the BOND factor, reused by M3).
- D.3 Alpha versus beta: `modules/M3_alpha_beta/m3lib.py` `ln_decomposition` and `timing_cov_bootstrap` (Lewellen-Nagel term), the wild-bootstrap block inside `ferson_schadt`.
- D.4 Shrinkage timing: `modules/M6_factor_timing/m6lib.py` `walk_forward_ridge` (expanding-fold CV, ties to the larger penalty) and `oos_stats` (Campbell-Thompson R2, Clark-West).
- D.5 Carbon frontier: `modules/M5_industry_momentum/optimizer.py` `run_path` (cvxpy problem: alpha'h minus cost, tracking limit, dollar neutrality, box, c'h <= b).
- D.6 Emissions mapping: `modules/M4_emissions/mapping.py` `naics_factors` (electricity patch from USEEIO) and `aggregate_ff49`.
- D.7 Look-ahead discipline: `lib/test_team_pipeline.py::test_no_lookahead` (fuzz test) and `exchange/02_coding_support/checks/mutation_lookahead_v2.py` (mutation test of ChatGPT's look-ahead audit, 7 of 8 injected bugs flagged).
- D.8 Reproducibility note (style guide section 5): every module runs with `cd /home/hashim/projects/GA/project/research && uv run python modules/<id>/run.py`; run times (M1 about 20 s, M1b about 1 min, M2 2 to 4 min, M3 about 2.5 to 4 min, M4 about 1 min, M5 4 to 10.5 min, M6 about 1 min, M8 under 1 min); seeds (230 for bootstraps and the M8 shuffle; 20260926 for M5); the M8 pre-registration hash; the date of the last clean run of each module; which script makes each exhibit.

### Appendix E. Tests ledger and multiple-testing summary (M7)

- E.1 Ledger schema: nine shared columns (`test_id, module, question, statistic_name, statistic, p_value_two_sided, n_obs, primary_or_exploratory, note`; M6 adds `p_value_one_sided, alternative`) and the rule that a hypothesis reported in two tables is logged once.
- E.2 Counts per module (computed from the ledgers now; M7 will confirm):

| Module | Rows | Primary | Robustness | Exploratory | Other |
|---|---|---|---|---|---|
| M1 | 667 | 15 | 217 | 435 | |
| M1b | 1,900 | 40 | 1,102 | 588 | 82 reference, 88 placebo |
| M2 | 13,482 | 46 | 5,562 | 7,874 | |
| M3 | 6,360 | 33 | 737 | 5,590 | |
| M4 | 802 | 1 | 375 | 426 | |
| M5 | 416 | 4 | 0 | 412 | |
| M6 | 274 | 8 | 120 | 146 | |
| M8 | 22 | 8 | 0 | 14 | |
| Total | 23,923 | 155 | 8,113 | 15,485 | 170 |

- E.3 Primary families and their Holm results, one row per family (from each FINDINGS "Primary" section; see Table 2).
- E.4 M7 project-wide correction: [placeholder: Holm and BH across all primaries and across everything, the best positive result in each module with its adjusted p, and a p-value histogram per label]. State the rule: only a primary-family Holm survivor is called "certified"; nothing else is.
- E.5 Nominal positives and why each is not a discovery (the list in 2.7 P1), plus M3's HML convexity (45 of the 48 pooled BH survivors among 1,080 timing tests are HML tests; a property of the hedged Brown leg, shared by always-short, TM t 3.24) and M4's full-sample EPA alpha (short CMA and UMD, static sort).

---

## 6. The story arc and the numbers to remember

### Arc (each step answers the question the previous one raised)

1. **Label check.** Our team called the signal "climate-transition attention". It is FRED EMVENRGYENVREG in 500 of 500 months, and 31 of 48 holdout months are exact zeros. So what does it measure?
2. **What the signal measures.** Overall volatility news (R2 0.169, overall EMV t 5.07) plus a topic share uncorrelated with climate concern (r = -0.0004 with MCCC). Genuine concern measures through the same machinery earn 0 of 12 validation alphas at t >= 1.96. So whatever the rule earned, it did not earn it from climate. What was it holding?
3. **What the legs are.** A Brown leg picked by an undocumented file in which Aero and Ships rank 3rd and 2nd, against 31st and 20th of 49 on EPA factors. So the position is a set of industries, not a carbon exposure. What is that position exposed to?
4. **What the spread is exposed to.** Value, profitability and commodity producers (HML -0.298, t -5.74; Brown side -0.437), with a lagged hedge that leaks market and size. COVID's gain is that leakage plus being short Brown (untimed short earns 71%; edge +1.84%, t 0.87); the holdout loss is residual Brown outperformance, not rates. Is there any timing left once exposure is removed?
5. **Pre-registered test.** The last clean window, 1994-2009, frozen before it was touched: -0.18% a year (t -0.27), shuffle p 0.478, 1 of 4 components. No.
6. **Alternatives.** The brief's other drivers on the same data: an EPA-ranked spread (4.7%, t 1.52), carbon-aware industry momentum (UMD in industry form, 1.74%, t 1.09) and shrinkage timing (never times). Each lands on exposure, not alpha.
7. **Verdict.** Do not implement; read the label, benchmark against the always-on position, and spend the last clean window on one frozen rule.

### The seven numbers the reader must remember

1. **500 of 500 months**: the "attention" series is FRED's EMV energy-and-environmental-regulation tracker, identical to the team column (`M1_signal_audit_identity.csv`).
2. **r = -0.0004**: its correlation with media climate concern (MCCC), p 0.996 (`M1_signal_audit_q5_primary_robustness.csv`).
3. **0 of 12**: validation alphas with t >= 1.96 when the same machinery is fed MCCC or CPU, against 4 of 6 for the EMV tracker (`M1b_alt_signals_primary.csv`).
4. **71%**: the share of the COVID alpha an untimed short of the same leg earns; the rule's edge is +1.84% a year, t 0.87 (`M1b_alt_signals_covid_decomposition.csv`).
5. **0 of 900**: positive holdout alphas for the six timed rules across the M2 grid; 0 of 28 before costs (`M2_christhian_tests_key_numbers.csv`).
6. **-0.18% a year, t -0.27, shuffle p 0.478**: the frozen rule on 1994-2009, 1 of 4 components (`M8_passbar.csv`).
7. **HML -0.298 (t -5.74)**: the spread's post-2010 value loading, -0.437 of it from the Brown side (`M3_alpha_beta_exposures.csv`; `M2_christhian_tests_q3_hml_decomposition.csv`).

---

## 7. Claims not to make

### 7a. Overreaches flagged by verifiers (and by the replication audit)

Signal and data:
1. Do not say the holdout failed for mechanical reasons, or that "the holdout tested a different, near-binary signal". The zeros changed no holdout entry, and every team strategy loses under every counterfactual (M1 VERIFY H3c, round 2 G1-G2). This supersedes `logs/replication.md` item 1 and the exchange 01 follow-up prompt.
2. Do not say "VIX adds nothing" without scope: it holds in the full sample and before 2021-10, but in validation z_VIX enters at t -2.51 (M1 VERIFY H2b).
3. Do not say the team series was "at its lowest when climate concern was highest" without saying the low level comes from exact zeros; nonzero readings were typical or above (M1 VERIFY T2).
4. Do not call the CPU link significant: p 0.037, Holm 0.074, partial r 0.05 through overall EMV (M1 VERIFY Q5, fix 7).
5. Do not call the high-VIX crossing result flatly null or significant: it is borderline (Fisher 0.097, shift 0.113, LPM 0.049) (M1 VERIFY fix 8).
6. Do not say MCCC "shows no consistent sign": z_MCCC keeps its sign in both halves; only the MCCC shock flips (M1 VERIFY T1).
7. Do not present the null as a refutation of Pastor-Stambaugh-Taylor: our legs are low-emission industries, not MSCI-green firms (M1 FINDINGS Caveats).
8. Do not repeat "this ranking comes from the data" (team write-up 1.3): the file is undocumented (M4).
9. Do not say the team file is a direct (Scope 1) intensity: its construction cannot be identified; the spread looks direct, the ranking looks supply-chain (M4 VERIFY F2).
10. Do not say the team's Aero and Ships values "match" air and water transport: consistent with, not proof of, a transport mis-mapping; EPA-based rejections do not survive Holm (M4 VERIFY F3).

COVID and timing:
11. Do not call the COVID gain "one pandemic event, not climate evidence": it cannot be attributed to the pandemic alone, and the window does not separate a climate trigger from being short the Brown residual (M1b VERIFY issue B).
12. Do not say the volatility placebos "reproduce" the COVID gain without timing and rule scope: for Original 3m they fall short under real-time timing, and CPU matches it (M1b VERIFY issue A).
13. Do not say the paired EMV-minus-placebo differences are significant only under real-time timing: against VIX they stay nominally significant under team timing (t 2.34 and 2.15) (M1b VERIFY R2-1).
14. Do not say the COVID gain came through momentum; it came through market and size leakage, and duration's contribution depends on the method (M3 VERIFY fix 2).
15. Do not cite "2 of 32 survive Holm" or any `significant_after_multiple_testing` / `team_holm_flag_normal_p` column: with t(n-4) p-values, 0 of 32 survive (replication item 3; M1b VERIFY issue E; M2 VERIFY fix 12).
16. Do not say the continuous variant "loses 75-85% less" or is a real improvement: it is mostly de-leveraging; at matched exposure it does worse than always-on out of sample (replication item 4; exchange 01 fact-check row 28).
17. Do not say purified signals "lose somewhat less in the holdout": an artifact of the missing Oct-2025 CPI print (replication item 2).
18. Do not say the IC "flipped sign" as if significant for every signal: raw and purified moved 1.3-1.6 SE; only the continuous-weight flip (2.8-2.9 NW SE) is significant (exchange 01 fact-check row 13).

Holdout, recent windows and alpha:
19. Do not say every hedged strategy has a negative holdout alpha under every design including zero cost: always-short with 8-and-8 legs has 24 small positive rows (max 0.42%, t 0.22), and zero-cost runs exist only for 5-and-5 legs with two hedges (M2 VERIFY fixes 1-2).
20. Do not say the last 12 and 18 months "add nothing" or that only one recent cell has |t| > 2: under team timing Original 3m lost -10.82% alpha (t -4.75) over 18 months, and under real-time timing five cells have |t| > 2, all losses (M1b VERIFY R2-2, R2-3).
21. Do not say "no return in this project is alpha" or that GB is insignificant in every window: say no return shows alpha that survives out of sample; GB's last 12-18 month alphas are nominally significant with NW(6) but not with classical OLS errors (M3 VERIFY fix 1).
22. Do not say rates helped (or hurt) the holdout: rates were immaterial either way, at most about half a point a year, sign method-dependent (M3 VERIFY fix 3).
23. Do not say the continuous strategies' betas move with macro instruments: no robust evidence (wild bootstrap p 0.40-0.62) (M3 VERIFY fix 4).
24. Do not say "factor adjustment raises GB's alpha above its raw mean" for all models: it fails for CAPM (M3 VERIFY R2.5, point 2).
25. Do not say "no positive commodity-controlled alpha exists": no commodity-controlled alpha is significantly positive (6 of 7 post-2010 point estimates are positive) (M2 VERIFY fix 7).
26. Do not say COMEQ is "not spanned" by FF5+UMD: most of its variance is unexplained, and its alpha is insignificant, so it is a distinct exposure, not an alpha source (M2 VERIFY round 2, recommended).

Emissions and alternatives:
27. Do not say the EPA spread's full-sample alpha "does not hold up": 5 of 9 variants survive Holm, but the alpha comes from short CMA and UMD on a look-ahead sort, and it is absent post-2010 (M4 VERIFY F4).
28. Do not say the ranking alone explains the team's weak record: EPA minus team is suggestive only (Holm 0.071 and 0.178) (M4 VERIFY N2).
29. Do not say the COVID episode "depends largely" on Aero and Ships: its significance does; the hold-3 return mostly survives (5.9% to 4.7%), and the re-ranked leg substitutes Chems and Trans (M4 VERIFY F6).
30. Do not say re-ranking weakens the positive evidence more than the negative: on the EPA Brown leg both the COVID gain and the holdout loss become insignificant; the IC was not re-tested (M4 VERIFY N1).
31. Do not say a carbon constraint on industry momentum "costs nothing" or is "close to free": no detectable cost with low power; the CI allows an IR loss of about 0.1, and post-2010 screens are 0.02-0.12 lower in Sharpe (M5 VERIFY fix 9).
32. Do not say "a client who can hold UMD gets the same premium more cheaply": unsupported (M5 VERIFY fix 8).
33. Do not call the Short-Brown momentum tilt an industry-momentum effect: it is a generic momentum tilt that fails BH (M5 VERIFY fix 10).
34. Do not say the optimizer is "not significant in any decade": nominally significant in 2020-2026 (p 0.049), not after BH (M5 VERIFY fix 4).
35. Do not say the ridge model "puts zero weight on predictors" as a general fact: it is a property of the pre-registered CV design; recent-window designs time in 14% to 48% of months without gain (M6 VERIFY fix 4).
36. Do not say M6 re-tested the team's event rule: it tests continuous forecasting (M6 VERIFY fix 5).
37. Do not present M6's recent timing Sharpe (0.64-0.99) as skill: it is the historical mean turning negative (M6 FINDINGS Headline 4).

Pre-registration and process:
38. Do not call the 1994-2009 test "fully blind" or "the only clean test ever": it is out of sample for returns, not for design; our team's macro-state notebook used 192 pre-2010 months (M8 FINDINGS Caveats 1-2; exchange 01 fact-check row 2).
39. Do not say the M8 pass bar's episode threshold and sign-only drop-one test were principled choices: they were ChatGPT's guesses, and the verdict does not depend on them (M8 FINDINGS Caveat 6).
40. Do not claim M1b or M3 primaries were provably fixed before results; say "stated in the run.py docstring" (M1b VERIFY issue I; M3 caveat 6). Do not claim M2's Q2 primary was blind (M2 FINDINGS timing record).
41. Do not quote M8 "38 free months" (it is 39) or say M8's wide tables "fit a landscape page" without "with 0.5 in margins" (M8 VERIFY).
42. Do not cite run.py's on-disk birth time as the pre-primary evidence: it now reads 06:05:07; the original 03:35:43 is in `corrections/pre_correction_0341/manifest.json` (M8 VERIFY round 2).
43. Do not say ChatGPT's code had "bugs in the backtest": the backtest mathematics matched; the problems sat in open readings, test scaffolding and one interface (exchange 02 evaluation).
44. Do not say "more Newey-West lags" fixes the COVID inference: they raise the t (exchange 01 fact-check row 26).

Language:
45. Do not use "significant" for anything that has not passed its test; use the ladder (not significant, within noise, nominally significant, suggestive not certified, survives Holm).
46. Do not use the label "climate-transition attention" unqualified; call it "the EMV energy-and-environmental-regulation tracker (our team's 'attention')".

### 7b. Corrected wording to use (VERIFY latest round supersedes the FINDINGS text on disk)

- **M1b, placebo pairs (R2-1):** "Real-time timing: the paired differences EMV env. minus placebo are nominally significant for both 3-month rules (Original 3m t 2.67 vs VIX and 3.22 vs EMV overall; Pure 3m t 2.70 and 2.75), but after Holm within the 12 real-time paired tests none survives (smallest Holm p 0.051). Team timing: against EMV overall the differences are not significant (Original 3m +1.39%, t 0.87; Pure 3m t 1.29), while against VIX they remain nominally significant (Original 3m +4.08%, t 2.34, p 0.030; Pure 3m +5.53%, t 2.15, p 0.044)."
- **M1b, recent windows (R2-2, R2-3):** "Under real-time timing, five recent-window cells have |t| above 2, all of them losses. Under the team's same-month timing, EMV env. Original 3m earns -10.82% alpha (t -4.75, p 0.0003; net -8.10%) over the last 18 months and -11.31% (t -2.68, p 0.028; net -8.84%) over the last 12."
- **M1b, CPU holdout IC (R2-4):** "-0.029 to 0.065".
- **M2, rolling HML flips (round 2 fix 3):** "At both peaks the Brown leg's own HML beta was slightly negative (-0.04 and -0.12) while the Green leg's was well above its 0.10 average (0.21 and 0.41); both sustained flips combine a temporary loss of the Brown leg's value tilt with an unusually value-tilted Green leg."
- **M2, characteristics (fix 4):** "at or above the 49-industry median" (Util and Steel 100%, Ships 94%; Fin, RlEst, Telcm 96%, 87%, 85%).
- **M2, hedge (fix 5):** "the seven-factor FF5+UMD+COMEQ hedge" (not eight).
- **M2, residual HML (fix 6):** team baseline "-0.018 to -0.061".
- **M2, COMEQ spanning (recommended):** "Most of its variance is not explained by FF5+UMD (R-squared 0.37), and its alpha on them is small and insignificant (-0.89% a year, t -0.24): it is a distinct exposure, not a source of alpha."
- **M3, strategies' full window (R2.5, point 1):** "the common window 1999-03 to 2026-07 (329 months), the first month every strategy in both baselines can hold a position; the raw-attention rules trade from 1993, so this window omits their earliest months."
- **M3, Ferson-Schadt null quantiles (R2.5, point 3):** label 71 to 241 as the fixed-design range; the wild bootstrap's null 95th percentile runs 72 to 403.
- **M5, multiple testing caveat (R2-1, R2-2):** "the optimizer's full-sample alphas for the unconstrained book and at every bound from +1 to -1.5 (11)"; "NW t-statistics that fall by half or more with classic OLS standard errors (the COVID FF5 alpha's t goes from 6.44 to 1.99), and all four have classic Student-t p-values between 0.06 and 0.19".
- **M5, ledger (R2-3):** 30 descriptive loading rows, 10 of them logged but not cited.
- **M6 (optional polish):** "no design has a one-sided p below 0.24" and "a penalty of 1 or less in at most 23% of months" hold for Specs A and B only (B0: 0.226 and 24.5%); the static portfolios' risk is spread "much more evenly (no window above 34% of squared returns)".
- **M8 (round 2, R2.6):** add the run.py birth-time sentence; "their modify times show the latest rerun"; the passbar and strategy-summary tables "fit a landscape letter page only with 0.5 in margins (35 pt too wide at 1 in) and are 216 pt too wide for portrait at 1 in margins (10pt; 263 to 266 pt at 11pt)".
- **M1, ledger arithmetic (round 2):** "56 rows were added ... 21 duplicates were merged, a net change of 35 rows (632 + 56 - 21 = 667)."

---

## 8. Open items and dependencies before drafting

1. **M7 (being built):** fills Table 2's M7 row, 2.7 P1's placeholder and Appendix E.3-E.4. Confirm the ledger totals above (23,923 rows, 155 primary) against M7's own count.
2. **Exchange 03 (being run):** fills 1.6 P4, 2.8 P4 and Appendix A.3; if it proposed robustness tests that were run, add them to 2.7.
3. **Exchange 04 (red team, after the first full draft):** fills 2.8 P4 and Appendix A.4; run it on the compiled PDF with Section 7 withheld, then check whether it finds anything Section 7 missed.
4. **New exhibit scripts:** `report/make_tables.py` (Tables 1-5 as tabular-only .tex) and, if kept, `report/make_fig_m8_null.py` (Figure 5). Load the `dataviz` skill before writing the figure code.
5. **Compile checks:** transcripts' Unicode glyphs under T1 lmodern (Appendix A.5); wide tables (M3 holdout alpha, M8 passbar and strategy summary) need landscape or `\resizebox`; tables are `\input{../outputs/tables/...}` since `\graphicspath` covers figures only.
6. **Team details to confirm:** the team roster and group number (HW1 header said Group 4, footer Group 5; `logs/hw_context.md` section 1) and the spelling "Christhian" (WhatsApp) versus "Cristhian" (HW1).
7. **Words to watch in the draft:** no em dashes; no "however, moreover, furthermore, thus, notably, crucially, honest"; no contractions; "significant" only in the statistical sense.
