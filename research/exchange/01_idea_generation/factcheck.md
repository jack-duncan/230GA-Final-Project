# Fact-check: exchange 01 (idea generation), Claude design review

Inputs: `prompt.md`, `claude_response.md` (this folder). Scripts: `checks/c01` to `checks/c11` (run with `cd research && uv run python exchange/01_idea_generation/checks/<script>`; each writes its CSVs next to it). Corroborating material: `logs/replication.md`, `logs/lit_digest.md`, module outputs `outputs/tables/M1_signal_audit_*` and `M4_emissions_*`, team tables in `230GA-Final-Project/outputs/tables`.

Guard for idea 1: I did not compute any pre-2010 strategy, timing or signal-to-return result. Pre-2010 data were used only for signal start dates, zero counts, industry factor betas and the team's own unconditional leg loadings. The 1993-2009 timing test stays unseen.

## Summary

52 checkable claims: 26 correct, 15 partly correct, 6 wrong, 5 unverifiable. The review is well organised, the arithmetic on our figures is right, and its literature citations are accurate. Its main weaknesses are these:

1. **It never asked what "attention" is.** The series is the EMV tracker for Energy and Environmental Regulation, a count of news articles about stock-market volatility. From 2010 to 2026 its z-score correlates +0.39 with overall EMV, +0.11 with CPU and -0.06 with MCCC. Crossings are 4.5 times as likely (odds ratio) in months of high overall EMV (p = 0.002).
2. **It got the coverage problem backwards.** It worried that early coverage "may be thin". Before 2010 the zero share is 0.8% to 4.2%. In the holdout, 31 of 48 months are exactly zero, so the holdout tests a different, near-binary signal.
3. **Idea 1 has the wrong start dates.** Under the frozen rule the first raw crossing is Jan 1993 and the first purified crossing Jan 1999, not 1990 and about 1995. Also, the team's macro-state notebook already estimated attention-to-residual slopes over 1994 to 2026.
4. **The duration story for the holdout is wrong.** The hedged Brown leg has no rate exposure in the holdout (t = 0.05). The strategies gain when yields rise. With FF5 + UMD + Δ10y + commodity controls, holdout alphas are still -2.3% to -4.8% (t about -2).
5. **Two statistical diagnoses are off.**
   - The IC flip is 1.3 to 1.6 SE for raw and purified attention, not "about one". For the continuous signals it is 2.8 to 2.9 NW SE (p < 0.01).
   - More Newey-West lags do not shrink the validation t (2.23 becomes 2.30 at 12 lags). They inflate the 24-month COVID t to 5.3. The real problem there is small-sample p-values.

Every test it proposed that I could run on seen data fails to rescue the strategy. The timed-minus-always-on FF5+UMD alpha peaks at t = 1.09. The Idea 2 post-event CAR has t = -1.08 (-0.63 ex-COVID). Momentum and commodity controls do not absorb the signal.

## Claims table

Verdicts: C = correct, P = partly correct, W = wrong, U = unverifiable. "Val" = validation 2010-01 to 2022-07, "HO" = holdout 2022-08 to 2026-07. t-stats are Newey-West with 6 lags unless stated.

### Bottom line and design critique

| # | Claim (quoted) | Verdict | Evidence | Source |
|---|---|---|---|---|
| 1 | "timing beats always-on Short-Brown by roughly 0.3% a year (1.3% vs 1.0%)" | C | Original 6m 1.344% vs always-short 1.049% net, 2010-2026: 0.29 pp. Incomplete: the difference has t = 0.52, and the two rules carry different exposure (mean abs position 0.43 vs 0.66; Sharpe 0.32 vs 0.20). "Best" is picked from six versions. | c01 |
| 2 | "the one period nobody has looked at, 1990-2009" | P | Timed-strategy returns before 2010 were never computed. But the team's macro-state notebook regresses next-month Brown residuals on attention from 1994-01 (n = 390, 192 of those months pre-2010). The unconditional spread table covers 1970 to Jul 2022, and the 2010 thresholds embed all 1987-2009 z values. The error is inherited from the prompt's "every result so far starts in 2010". | team_pipeline.macro_state_tables; macro_state_slopes.csv |
| 3 | "Timed returns are tested against zero." | C | Period alphas, the 32 Holm claims and the bootstrap all test against zero. Always-short Brown is only a reported row. The team's four paired-bootstrap pairs are continuous vs discrete, never timed vs always-on. | c01 |
| 4 | "the traded position has no Green leg" | C | The P&L engine uses the Brown-leg model only. The Green model is built but unused. | replication.md, design notes |
| 5 | "Both Holm survivors are COVID; the 3-month rule's 2020-21 alpha (t = 3.21)" | C | Writeup p.5: 3m t = 3.21 and continuous t = 3.28, both in COVID. | writeup.pdf; replication.md |
| 6 | "[the 3-month rule's COVID alpha] carries the result" | P | True for the 3m rules: Val t 1.47 and 1.50 fall to 0.41 and 0.50 without Mar 2020 to Dec 2021. The headline 6m rules fall only from 2.23 and 2.46 to 1.42 and 1.65 (net 2.45% to 1.53%). COVID carries most, not all, of the 6m result. | c02 |
| 7 | "Aero (Boeing-heavy: 737 MAX grounding plus the travel collapse)" | P | Summed FF3-hedged Aero returns were -9.5% (2019, the grounding year), -32.0% (2020) and -28.5% (2021). Aero is 16 to 17 firms with $429bn to $478bn total cap (Dec 2018, Dec 2019). A Boeing cap of about $180bn (not in our data) would be about 40%, so "Boeing-heavy" is plausible but not checked. | c02 |
| 8 | "Ships and Util took COVID-specific hits" | P | Util: -14.3% in 2020 and +4.2% in 2021, so a COVID hit. Ships: -15.2% (2019), -22.1% (2020), -16.2% (2021), which is persistent underperformance, not COVID-specific. | c02 |
| 9 | "[hits] unrelated to transition risk" | U | This is an interpretation. The data cannot separate the causes. | |
| 10 | "With five equal-weighted industries, each is 20% of the leg." | C | True by construction. Unflagged consequence: Ships (9 to 10 firms, about $30bn) weighs the same as Util (76 firms, about $1.1tn). | c02 |
| 11 | "The high-rate interaction was found with 47 of its 74 months in the holdout." | C | 27 pre-holdout months plus 47 holdout months. Difference t = 1.83, Holm p = 0.585. | macro_state_slopes(_by_period).csv |
| 12 | "the IC's standard error is roughly 1/sqrt(48) = 0.14 (a rough approximation that ignores overlap)" | P | 1/sqrt(48) = 0.144, and the team's NW SE for the holdout IC is 0.111 (IC 0.123, t 1.11, n 47). The overlap caveat does not apply: the IC uses one-month-ahead residuals. | c03 |
| 13 | "-0.08 to +0.13 is about one standard error of the difference" | W | Raw and purified ICs move 0.21. That is 1.3 SE with naive SEs, 1.5 SE with Claude's own 0.14, and 1.6 SE with NW SEs (p 0.10 to 0.11). For the continuous-weight ICs the change of 0.33 is 2.8 to 2.9 NW SE (p 0.003 to 0.004), so that flip is significant. | c03 |
| 14 | "The honest reading is 'failed to confirm,' not 'flipped.'" | P | Right for the raw and purified ICs. But holdout returns are significantly negative (FF3 alpha t -1.66 to -2.19; in-state dummy t -1.5 to -2.1), and the continuous IC flip is significant. The holdout signal is mostly zeros (row 36), which is the bigger caveat. | c01, c03 |
| 15 | "eight industries missing, including Oil" | C | The team file has 41 industries and no Oil. | c05 |
| 16 | "Aircraft and Shipbuilding in the top five by emissions intensity is surprising" | C | EPA v1.3 supply-chain ranks (of 49): Aero 31, Ships 20. USEEIO direct GHG ranks: Aero 43, Ships 36. Aircraft NAICS factors are 0.139 to 0.170 kg CO2e/$, against 0.787 for steel mills, 0.841 for coal and 3.924 for cement. | c05; M4 |
| 17 | "check ... where Coal ranks"; "rerun with Oil and Coal in" | P | Coal is already in the file, ranked 9th of 41 (0.163). EPA ranks it 5th and direct GHG 2nd. Oil ranks 13th on EPA (0.377), so it would not enter a five-industry Brown leg. The EPA top 5 is Util, Chems, Other, Agric, Coal. Intensity per $ of output leaves out the use-phase emissions that make Oil a transition-risk industry. | c05; M4 |
| 18 | "Rebuild intensity from EPA supply-chain GHG factors ... covering all 49" | P | Feasible (M4 built it). But EPA v1.3 has no electricity-generation codes (none of its 1,016 NAICS codes is 2211xx), so Util needs a patch from USEEIO. Claude did not flag this. | c05; M4_emissions_key_numbers |
| 19 | "Residual HML = -0.05 (t = -2) in every version" | C | Range -0.040 to -0.061. Original 6m: -0.061 (t -2.36). | c08; replication.md item 8 |
| 20 | "no control for momentum, profitability/investment, rates or commodities" | C | The hedge is FF3 only. Rates and oil enter only the purification of the signal. | team_pipeline |
| 21 | "Util, BldMt and Steel are rate- and commodity-sensitive." | P | Util: Δ10y beta -0.027 (t -3.4, 1992-2026) and -0.038 (t -3.5, 2010-2026); commodity 0.15 (t 3.3). Steel: commodity 0.23 (t 3.2) over 1992-2026 but 0.16 (t 1.6) after 2010; its rate beta is positive, so it is not bond-like. BldMt: neither (Δ10y t -0.1 and +1.7; commodity t -1.0 and -1.7). | c04 |
| 22 | "A 2022-2026 holdout dominated by rates can lose money through unhedged duration, not climate." | W | The hedged Brown leg's HO Δ10y beta has t = 0.05 (commodity t = -0.74). The strategies' Δ10y beta is positive (t 0.7 to 2.0): short Util gains when yields rise. The 10-year yield rose 1.70 pp over the HO, so rates helped. After FF5+UMD+Δ10y+commodity, HO alphas are still -2.3% to -4.8% (t -2.0 to -2.3). | c04 |
| 23 | "Overlapping 3-6-month holds, few independent crossings" | C | 2010-2026: 26 raw crossings, which merge into 16 events (6-month gap). Val 21 into 12, HO 5 into 4, COVID 3 into 2. | c03 |
| 24 | "4+ variants" | C | 6 timed variants plus 2 benchmarks, giving 32 Holm claims. | c01 |
| 25 | "a purified signal built from CPI, CFNAI and GSCPI" | P | The traded purified signal uses Δ10y, oil return, lagged CPI inflation (level and change) and lagged CFNAI. GSCPI and the recession flag appear only in an ex-post diagnostic, which the team excluded exactly because of lags and revisions (writeup p.2). | c06; team_controls |
| 26 | "Too few Newey-West lags overstate t" (fix: "NW lags >= hold length") | W | Not true for these results, and the team already reported 12 and 18 lags. Val t: Original 6m 2.23, 2.30, 2.27; Pure 6m 2.46, 2.45, 2.44 (6, 12, 18 lags). COVID t rises with lags (3.21, 4.00, 5.32 on n = 24), so HAC is unreliable there. The binding problem is small-sample p-values: with t(n-4) p-values, 0 of 32 claims survive Holm. | c03; replication.md item 3 |
| 27 | "final-vintage macro data is look-ahead"; "lag macro inputs 1-2 months" | P | CPI and CFNAI already enter with a one-month lag. The CFNAI revision point is valid. It missed the attention series itself: month-t EMV is used at the close of month t. Lagging it one month moves Original 3m full-sample net from 0.07% to 0.73%, and Pure 6m HO from -3.04% to -2.00%. | c06; replication.md item 5 |
| 28 | "The continuous variant's lower vol and drawdown is partly mechanical (lower average exposure)" | C | Mean abs position over 2010-2026: 0.14 and 0.16, against 0.26 to 0.47 for the discrete rules and 0.66 for always-on. Its own fix (always-on at matched exposure, i.e. compare Sharpe): 0.24 and 0.30 vs 0.20 over 2010-2026, but -0.60 and -0.47 vs -0.21 in the HO. At equal exposure it does worse than always-on out of sample. | c01; replication.md item 4 |
| 29 | "consistent with placebo p = 0.12" | C | Consistent, but weak: the placebo shuffles timing at the same exposure, so p = 0.12 only says the timing is not significant. | replication.md |

### Proposal ranking (section 2)

| # | Claim (quoted) | Verdict | Evidence | Source |
|---|---|---|---|---|
| 30 | D: "Only a break-even cost below ~10 bp [changes the conclusion], unlikely with 3-6-month holds (guess)"; "Costs can't rescue a -2% to -4% holdout" | C | HO gross returns are negative for every rule (-1.7% to -3.4%). Uniform break-even over 2010-2026: 12 bp (Original 3m), 21 bp (Pure 3m), 55 to 61 bp (6m). At 25 bp both 3m rules turn negative. The column's logic is muddled: a low break-even can only reinforce "Do not implement". | c08 |
| 31 | C: "Little: Green isn't in the traded position"; the traded HML residual "sits in Brown" | C | Right for the traded P&L. Leg loadings also show the raw spread's value tilt is mostly Brown's: HML +0.41 and +0.44 for Brown vs +0.17 and +0.14 for Green (1970-2022 and 2010-2026). Green is not a growth leg (BE/ME 0.38, against an all-49 median of 0.33). | c08 |

### New ideas (section 3)

| # | Claim (quoted) | Verdict | Evidence | Source |
|---|---|---|---|---|
| 32 | Idea 1: "Signal from Jan 1990 (60-month z-score uses 1985-89)" | W | Frozen rule: z from 1987-12 (36-month minimum), then 60 months of z history for the expanding p80. The first possible crossing is 1992-12 and the first actual one 1993-01. The window is 1993-2009, not 1990-2009. | c06 |
| 33 | Idea 1: "purified variant from ~1995 (120-month ridge)" | W | Controls are complete from 1989-01 (WTI starts 1986-01). The ridge needs 60 observations, so the purified signal starts 1994-01. Its p80 then needs 60 more months, so the first crossing is 1999-01. The purified test covers only 1999-2009. | c06 |
| 34 | Idea 1: "(c) Data: In hand." | C | Industries from 1926, FF3 and FF5+UMD downloaded, attention from 1985. | c06 |
| 35 | "transition risk was arguably unpriced before ~2005" | U | No paper dates this. Partial support: Bolton and Kacperczyk (2021) find no significant premium in the 1990s with imputed emissions (Table 16B). | lit_digest section 4 |
| 36 | "early index coverage may be thin" | W | Backwards. Zero share: 1.7% (1985-89), 0.8% (1990s), 4.2% (2000s), 3.3% (2010s), against 66% from 2021-10 (39 of 59) and 65% in the HO (31 of 48). Median level is 0.22 to 0.23 before 2010 and 0 in the HO. HO zero months get z between -1.39 and -0.59, and all 7 in-state HO months are nonzero. | c06; M1_signal_audit_zero_counts |
| 37 | "Ardia, Bluteau, Boudt & Inghelbrecht (2023) find green stocks rise and brown stocks fall on days of unexpected increases in climate-change concerns" | C | Management Science 69(12), 2023, main result. Checked from general knowledge; the paper is not in the folder. PST 2022 uses their MCCC index. | lit_digest section 3 |
| 38 | "Pastor, Stambaugh & Taylor (2022) attribute green outperformance over 2012-2020 to unanticipated strengthening of climate concerns" | C | Nov 2012 to Dec 2020 sample. Climate-shock coefficient 4.08 (t 2.70); the shock-purged mean is about -4 bp a month (Table 4, p.415). Earnings shocks also contribute. | lit_digest section 3 |
| 39 | "If the repricing is contemporaneous, a post-spike rule has nothing left to harvest." | P | PST Table 8: large caps react in the same month, small caps with a lag. But in our data Brown residuals are positive in the spike month (+0.47% raw, +1.07% pure, t 0.7 to 1.8), the opposite sign. So the idea's "if it fails" story is not supported either. | c07 |
| 40 | Idea 3: "CPU late 1980s, MCCC ~2003" | C | CPU 1987-04 to 2025-09; MCCC 2003-01 to 2025-06. Missed: they cover only 38 and 35 of the 48 HO months. | c06 |
| 41 | "the 60-month z-score burns five years of a short index" | P | Under the team rule the z needs 36 months and the p80 needs 60 more, so 95 months (about 8 years) are burned. The first possible MCCC signal is 2010-12, CPU 1995-03. | c06 |
| 42 | Idea 4: "Bolton & Kacperczyk (2021) find a positive carbon premium at the firm level; this tests the industry analogue" | P | The first half is right. But the BK premium is in emission levels and growth; intensity is unpriced (scope 1 intensity -0.010, SE 0.012, Table 8), and industry fixed effects strengthen the premium. An across-industry intensity sort is closer to Zhang (2025), where US intensity H-L is -0.39% a month and mostly cross-industry. | lit_digest sections 4, 6 |
| 43 | "a NAICS to SIC crosswalk (not listed; public concordances exist)" | C | Census concordances are in data/raw; M4 used them. | data/raw; M4 |
| 44 | "supply-chain factors include upstream emissions, a different concept from your snapshot" | U | Likely true, but the snapshot's source, units and scope are undocumented. The dispersion differs sharply: team Util/Fun = 6,051x, against 135x across EPA NAICS codes and 33x at FF49 level. Spearman correlation of team vs EPA = 0.70 across 41 industries. | c05; M4_emissions_provenance, M4_emissions_spearman |
| 45 | Idea 5: "Engle, Giglio, Kelly, Lee & Stroebel (2020) ... build mimicking portfolios that hedge innovations in a climate news index" | C | RFS 2020, "Hedging Climate Change News", WSJ climate news index. PST 2021 cites it (p.562). Their hedges use firm E-score characteristics; sorting FF49 industries on rolling betas is a looser analogue. | lit_digest section 2 |
| 46 | Idea 5: "1995-2026 ... (c) Data: In hand." | C | Attention from 1985 leaves room for AR(1) innovations plus a 60-month beta window by the mid-1990s. | c06 |

### Plan and stated assumptions (sections 4, 5) and compliance

| # | Claim (quoted) | Verdict | Evidence | Source |
|---|---|---|---|---|
| 47 | "Idea 1. The only clean out-of-sample test left ... don't touch pre-2010 attention data before then." | P | Pre-2010 strategy returns are unseen, but see row 2. "Don't touch pre-2010 attention" is already impossible, because every 2010 threshold is built from 1987-2009 z values. The workable rule is: compute no pre-2010 strategy or residual returns until the rule is written down. | c06; row 2 |
| 48 | Assumption 1: "the attention index has usable coverage in 1985-2009" | C | Yes (row 36). The coverage failure is in the holdout, which the answer never mentions. | c06 |
| 49 | Assumption 1: "the emissions ranking is stable enough to apply backward" | U | One undocumented snapshot, and the EPA factors are a single recent vintage, so no historical intensities are available. | M4_emissions_provenance |
| 50 | Assumption 2: "the COVID gains come from Aero, Util and Ships shocks" | C | Exact decomposition of COVID gross P&L. Original 3m: 6.70% a year = Aero 2.74 + Util 1.71 + Ships 1.30 + BldMt 0.89 + Steel 0.06 (86% from the three). Original 6m: Aero 4.42 + Ships 2.35 + Util 1.12, which is 101% of 7.78. Dropping Aero takes the COVID 6m t from 2.07 to 0.03. Dropping Util takes the COVID 3m t from 3.21 to 2.11. | c02 |
| 51 | Every hour estimate (table, ideas, assumption 3) | U | Not checkable. | |
| 52 | Format: under 1,800 words, at most six problems, exactly five ideas (at least two of each type), no invented results | C | About 1,700 to 1,770 words; 6 problems; ideas split 3 extension and 2 alternative; 0 em dashes; no fabricated backtests. Minor: ideas 4 and 5 omit an explicit benchmark, and idea 4 has no pass bar beyond its rejection rule. | c09 |

## Proposed tests that I ran on seen data (2010-2026), and what they show

| Test (Claude's spec) | Result | Script |
|---|---|---|
| E / critique 1: alpha of (timed minus always-on) after FF5+UMD | Never significant. 2010-2026 t -0.93 to 0.78; Val at most 1.09; HO -1.11 to 1.10. The in-position dummy (unit position) gives Val t of 2.68 to 2.75 for 6m holds, but at most 1.14 for 2010-2026 excluding Mar 2020 to Dec 2021, and -1.5 to -2.1 in the HO. | c01 |
| Critique 2: drop Mar 2020 to Dec 2021; leave one industry out | 6m Val t 1.42 and 1.65 (Claude's bar is 1.5); 3m 0.41 and 0.50. Leave-one-out 6m Val t 1.62 to 2.77; COVID 6m t collapses without Aero (0.03, 0.07). HO stays negative in every case (-1.17 to -2.56). | c02 |
| A: 8+8 legs (Hardw and MedEq tie for the 8th Green slot) | 6m Val t 2.16 and 2.31; 3m 1.02 and 1.08. Without Aero: 6m 1.61 and 1.85, 3m 0.67 and 0.69. HO -0.72 to -2.13. The 6m validation edge survives broader legs; nothing else changes. | c11 |
| B / critique 5: FF5 + UMD + Δ10y + commodity attribution | Val 6m alpha 2.2% to 2.5% (t 2.46 and 2.72, slightly higher than FF3); HO -2.3% to -4.8% (t -2.0 to -2.3). Commodity beta t -0.4 to -0.7. It does not "fall below ~1.5". | c04 |
| G: horse race with Brown's trailing 3m and 12m returns | Attention is not absorbed. Val z t is -1.26 alone and -1.84 with the controls; trailing 12m Brown return t is +2.0 (continuation). 2010-2026 z t -0.39 alone, -0.90 with controls. The p80 state correlates -0.25 with trailing 12m Brown return. | c08 |
| Idea 2: event-time profile, merged events, post-event dummy, pass if t > 2 ex 2020-21 | Rejected by its own rule. CAR over t+1 to t+6: -1.29% (t -1.08, raw) and -1.01% (t -0.94, pure); ex-2020-21 -0.82% (t -0.63) and -0.67% (t -0.57), within one SE of zero. Post-event dummy t -0.40 and +0.54; ex-COVID -0.17 and +0.29. | c07 |
| Critique 6: continuous rule vs always-on at the same exposure | Sharpe over 2010-2026: 0.24 and 0.30 vs 0.20. HO: -0.60 and -0.47 vs -0.21. | c01 |
| Idea 3 premise: do the attention indices agree? | Team z vs CPU z +0.11 and vs MCCC z -0.06 (2010-2026). CPU and MCCC levels correlate 0.70 with each other, but only 0.15 and -0.04 with the team series. Running the frozen rule on CPU and MCCC belongs to module M1b and was not run here. | c06, c10 |

Not run: idea 1 (kept clean on purpose), idea 4 (covered by M4), idea 5, proposal F.

## What Claude missed

1. **What the attention variable measures.** The prompt gave the variable as "climate-transition attention" with no source, and Claude accepted that label. The series is FRED EMVENRGYENVREG, a count of newspaper articles about stock-market volatility that mention energy or environmental regulation, scaled to the VIX.
   - Its z-score correlates +0.41 with overall EMV and +0.29 with VIX (1993-2026), but +0.13 with CPU and 0.00 with MCCC.
   - Since 2010, crossings fall in high overall-EMV months 38% of the time, against 12% otherwise (odds ratio 4.5, p = 0.002).
   - The rule partly times general market-volatility news. A careful referee would have ranked idea 3 (swap in CPU or MCCC) first. (c10; M1_signal_audit_decomposition)
2. **The holdout signal is degenerate.** There are 39 zeros in 59 months from 2021-10, against 12 in 441 before. In the holdout, zero months map to z between -1.39 and -0.59, and entries require any nonzero print. The IC "flip" and the holdout losses test a near-binary signal, not the validated one. Claude placed the coverage risk in the wrong period. (c06)
3. **Same-month look-ahead in the signal itself.** Month-t EMV is used to trade at the close of month t. Claude flagged vintage issues in the macro controls but not in the traded series, which moves the headline numbers (row 27).
4. **Small-sample inference in COVID.** Both Holm survivors are NW(6) t-stats on 24 months. With t(n-4) p-values none survive. Asking for more lags makes that t larger, not smaller.
5. **Unequal exposure in the benchmark comparison.** The "0.3% a year" compares a rule with mean exposure 0.43 to one with 0.66, and picks the best of six. The comparison should be exposure- or volatility-matched and should correct for selection.
6. **Leg weighting.** Equal weights give Ships (9 to 10 firms, about $30bn) the same 20% as Util (about $1.1tn). Ships alone accounts for 1.60 pp of the Original 3m rule's 3.36% annual holdout gross loss. (c02)
7. **Power of a 48-month holdout.** Eskildsen, Ibert, Jensen and Pedersen (2026) give the relevant arithmetic: expected t = 2 x Sharpe over 4 years, so even a true Sharpe of 0.5 gives an expected t of 1.0. This would have sharpened critique 3 more than the IC standard error does. (lit_digest section 7)
8. **Emissions-measure gaps.** EPA v1.3 has no electricity codes, so Util needs a patch. No intensity-per-output measure captures the downstream emissions that make Oil and Coal transition-exposed. Under EPA, Oil still does not make a five-industry Brown leg. (c05)
9. **Alternative indices end early.** CPU ends Sep 2025 and MCCC Jun 2025, leaving 10 and 13 holdout months uncovered. With the team's rule each also burns about 8 years at the start. (c06)
10. Not inferable from the prompt, listed for completeness: the missing Oct 2025 CPI print explains the whole purified-vs-original holdout gap (replication.md item 2).
