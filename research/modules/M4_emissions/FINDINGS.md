<!-- Saved by the orchestrator from the builder's returned text (subagent report writes are blocked by the harness). Source agent ad93de02f84e14ad3. -->
# M4_emissions: is the team's emissions ranking sound, and does a supply-chain measure change the spread?

Run: `cd /home/hashim/projects/GA/project/research && uv run python modules/M4_emissions/run.py` (about 1 minute).
All numbers below come from CSVs in `outputs/tables/` (file named in brackets). Percentages are annualized decimals from those files times 100.
Revised after independent verification (fixes F1 to F11). See "Response to verification" at the end.

## Question

1. Where did the team's `emissions_ff_industry.csv` come from, and what are its units?
2. What does a complete supply-chain GHG intensity (EPA Supply Chain GHG Emission Factors v1.3) look like for all 49 Fama-French industries?
3. Do the two rankings agree? Are Aero and Ships plausibly among the five highest emitters, or does the team file look like it put air and water transportation (which belong in FF49 Trans) onto them? Where do Oil, Coal, Mines, Chems and Trans land?
4. Does the Green-minus-Brown (GB) spread behave differently under the EPA ranking?

## Pre-specified primary test (fixed before any return was computed)

EPA 5-vs-5 GB (Green = 5 lowest EPA with-margins mean intensity among all 49 industries, Brown = 5 highest, equal-weighted legs from the team's industry file), regressed on FF5 + UMD (Mkt-RF, SMB, HML, RMW, CMA, UMD), 2010-01 to 2026-07, Newey-West 6 lags. H0: alpha = 0, two-sided, 5% level.

Everything else is labelled robustness or exploratory:
- Robustness (pre-planned EPA variants): median, without margins, any-link mapping, 8 vs 8, EPA ranking restricted to the team's 41 industries, excluding FF49 Other.
- Robustness added after independent verification (not pre-specified): leg-membership sensitivity of the primary test (Chips in place of Smoke, drop each member in turn).
- Exploratory: team-baseline numbers, Oil/Coal variants, the EPA-minus-team difference series, leg regressions, forensic tests, the team timing-rule re-run, calendar-year slices.

Every test is in `M4_emissions_tests_ledger.csv`: 802 rows, of which 1 primary, 375 robustness and 426 exploratory. The 13 post-verification sensitivity rows say so in their note column.

## Data

- Team file: `230GA-Final-Project/data/emissions_ff_industry.csv` (41 industries, read only).
- EPA Supply Chain GHG Emission Factors v1.3 by 2017 NAICS-6 (`data/raw/epa_sc_ghg_naics_v13.csv`): 1,016 codes, kg CO2e per 2022 USD (purchaser price), with and without trade/transport margins. EPA leaves out electricity (NAICS 2211xx), government and households by design.
- Census concordances, downloaded to `data/raw/`: 1987 SIC to 2002 NAICS, 2002 to 2007, 2007 to 2012, and 2012 to 2017 NAICS. SIC to FF49 through `kf_industry_sic_map()` (Ken French Siccodes49).
- USEEIO v2.0.1-411 (EPA, `data/raw/USEEIOv2.0.1-411.xlsx`; extracted rows in `data/raw/useeio201_ghg_DN.csv`). It supplies the electricity factor that EPA v1.3 omits, plus total (supply-chain) and direct (own-industry) GHG and CO2 per dollar of output, which I use only as forensic comparisons.
- Returns: the team's `ff49_industry_monthly.csv` (value-weighted industry returns). Factors: Ken French FF3, FF5, UMD (Aug 2026 vintage) via `lib/common.py`. Firm counts: Ken French 49-industry "Number of Firms". The team timing-rule re-run uses the team's own FF3 and attention files so that it reproduces the team's numbers exactly.

## Method

Intensity by FF49 industry j (no output weights anywhere):

    EPA_j        = (1 / N_j) * sum_{n in M_j} f_n            (epa_sc_mean; median over the same set = epa_sc_median)
    M_j          = 2017 NAICS codes n whose Census-chain SIC-1987 predecessors fall mostly in FF49 industry j
                   (plurality of distinct SIC codes; ties go to every tied industry)
    f_n          = EPA v1.3 supply-chain factor with margins (without margins as robustness)
    f_elec       = N_USEEIO(221100) * median_n( f_n^nomargin / N_USEEIO(n) ) = 4.491 * 0.5884 = 2.642 kg CO2e / 2022 USD

N_j counts the NAICS codes that have a factor (`n_naics`). Mapping choices: 1,015 of 1,016 EPA codes are mapped. 551114 (corporate head offices; its only SIC is "Aux") is dropped. There are 2 manual links (112130 to Agric, 541120 to BusSv), 3 overrides (the 2017 R&D codes 541713/4/5 tie Aero and Guns through R&D pieces of the aircraft and missile SIC codes, so I assign them to BusSv), and 115 plurality ties. The 10 electricity codes use the patched factor, whose median ratio has an IQR of 0.459 to 0.690 [M4_emissions_mapping_summary.csv]. Robustness mapping ("any link"): a NAICS code counts in every FF49 industry that holds any of its SIC predecessors.

Returns and costs:

    GB_t   = (1/n) sum_{i in Green} r_{i,t} - (1/n) sum_{i in Brown} r_{i,t}          (n = 5 or 8; zero-cost, no RF)
    GB_t   = a + b' F_t + e_t,  F in {Mkt-RF}, {FF3}, {FF5 + UMD};  t-stats NW(6);  alpha_ann = 12 a
    turnover_t (per leg) = sum_i | w_{i,t}^drift - 1/n |   (two-way traded notional: buys plus sells)
    cost_t = 10 bp x (turnover_t(Green) + turnover_t(Brown))
    GB_t (raw) = alpha_CAPM + beta_CAPM x mean(Mkt-RF)   (exact identity used for the recent-window decomposition)

Costs exclude the initial build of the legs and the rebalancing inside the value-weighted industry portfolios.

Aero/Ships forensic (leave two out): fit log(team_j) = c0 + c1 log(M_j) + u_j on the other 39 industries, for M = EPA, USEEIO direct GHG and USEEIO direct CO2. Then predict Aero and Ships from (a) their own manufacturing NAICS and (b) air (481) or water (483) transportation NAICS. The statistic is t = (actual - predicted) / prediction s.e., with 37 df. Multiplicity: Holm (and BH) over the 12 calibration tests (3 measures x 2 industries x 2 mappings).

Lag convention. The GB legs use a single static ranking: the 2022-vintage EPA factors, or the team's undated snapshot, applied to every month from 1970. The industry sort therefore has look-ahead (it is not point-in-time), and I say so wherever full-sample numbers appear. No macro series or BE/ME enter GB. In the exploratory timing-rule re-run I keep the team's conventions: rolling 60-month FF3 betas lagged one month, a past-only expanding 80th-percentile threshold, and a position formed at the end of month t that earns month t+1. The attention index for month t is treated as known at the end of t, as the team does.

## Results

### 1. Provenance: undocumented, and the construction cannot be identified

- The team file matches `/home/hashim/projects/GA/Emissions_FF_Industry.csv`, the course file used in PS1 [M4_emissions_provenance.csv].
- `230GA__PS1.ipynb` loads it and sorts it. `HW1_merged.tex` and `Q5_answer.md` describe it only as "emissions per unit of output", "a single snapshot", 41 of 49. `Q4_corrections.md` never mentions it. The team write-up and code add nothing. The "2020 data" in Q5 is ChatGPT's assumption, not a documented vintage. No source, units, scope, gas coverage or year is recorded anywhere [M4_emissions_provenance.csv].
- Structural fingerprints [M4_emissions_team_file_ties.csv, M4_emissions_key_numbers.csv, M4_emissions_spearman.csv]:
  - There are 3 groups of exactly equal values: {Hardw, MedEq}, {Clths, Txtls}, {Beer, Food, Smoke, Soda}. The file was probably built on a coarser industry scheme and then spread across FF49 industries.
  - Util/Fun = 6,051 and Fun/Util = 0.000165. This is a spread the EPA v1.3 supply-chain factors cannot produce: they span 135x across NAICS codes (the lowest is 0.011 of the electricity factor) and 33x across FF49 means. USEEIO v2.0.1 total intensities, a second supply-chain dataset from the same EPA model family, span 45x across FF49 means. Direct (own-emissions) intensities are far more dispersed: USEEIO direct FF49 means span 531x, though even that is well short of 6,051x.
  - The ranking points the other way. The team file's Spearman correlation is 0.700 with EPA supply-chain and 0.649 with USEEIO total, but only 0.492 with USEEIO direct GHG and 0.503 with direct CO2.
  - So the construction cannot be identified from the file. The spread looks like a direct measure, but the ranking is closer to a supply-chain measure. The supply-chain comparison rests on one model family (EPA v1.3 and USEEIO v2.0.1). All of this is inference, not documented fact.

### 2. EPA supply-chain intensity by FF49 [M4_emissions_ff49_intensity.csv; data/derived/ff49_emissions_epa.csv]

- Highest (kg CO2e per 2022 USD): Util 2.242 (n=13), Chems 0.824, Other 0.752, Agric 0.729, Coal 0.724, then Gold 0.593, Food 0.524, Trans 0.501, Steel 0.448.
- Lowest: Banks 0.068, Insur 0.076, Softw 0.079, Hardw 0.094, Smoke 0.101 (n=1), then Chips 0.102, Fin 0.104, Fun 0.110. Smoke is the 5th-lowest by only 0.0012 over Chips [M4_emissions_key_numbers.csv]; see the leg-membership robustness below.
- Util stays first without the electricity patch: its non-electricity codes alone average 0.910, still above Chems at 0.824 [M4_emissions_key_numbers.csv].
- The EPA ranking is stable to my own choices. Spearman against the primary measure is 0.970 for the median, 0.987 without margins and 0.991 for any-link [M4_emissions_spearman.csv].

### 3. Ranking comparison [M4_emissions_spearman.csv, M4_emissions_membership.csv, M4_emissions_key_industries.csv]

- The two rankings are correlated but disagree where it matters. Over the 41 common industries, Spearman(team, EPA) = 0.700 (p = 3.6e-7) and Kendall tau = 0.507 (p = 3.3e-6).
- Membership, 5 per leg:
  - EPA Green is Banks, Insur, Softw, Hardw, Smoke. It shares 0 of 5 with the team Green (Fun, RlEst, Drugs, Telcm, Fin).
  - EPA Brown is Util, Chems, Other, Agric, Coal. It shares 1 of 5 (Util) with the team Brown.
  - Restricted to the team's 41 industries, EPA Brown is Util, Chems, Agric, Coal, Food.
- Membership, 8 per leg: overlap is 4 of 8 on the Green side and 3 of 8 on the Brown side.
- Aero and Ships are not plausible top-five emitters:
  - Team ranks are Ships 2nd and Aero 3rd of 41. EPA ranks are Ships 20th and Aero 31st of 49; USEEIO direct GHG ranks are 36th and 43rd. Under direct GHG, Aero is among the 8 cleanest industries.
  - At the NAICS level [M4_emissions_aero_ships_naics.csv], aircraft manufacturing (336411-3) is 0.139 to 0.170 in EPA and 0.005 to 0.013 direct, and ship building (336611) is 0.196 and 0.017. Air transportation (481) is 0.644 in EPA and 0.726 direct; water transportation (483) is 0.816 and 0.516.
  - The team values (Aero 0.531, Ships 1.019) sit above Steel (0.403) and BldMt (0.365). They are far above what aircraft and ship manufacturing implies and much closer to air- and water-transport levels. That is consistent with, not proof of, a transport mis-mapping: air and water transportation belong in FF49 Trans (SIC 4400-4599), while FF49 Aero (SIC 3720-3729) and Ships (3730-3743) hold manufacturers.
- Leave-two-out test [M4_emissions_aero_ships_calibration.csv]. Each cell: prediction t (raw p; Holm p over the 12 tests), then team value / predicted value.

  | Measure | Aero, manufacturing | Aero, air transport | Ships, manufacturing | Ships, water transport |
  |---|---|---|---|---|
  | EPA | t 2.88 (p 0.007; Holm 0.052), 21.4x | t 0.94 (p 0.355), 2.8x | t 2.52 (p 0.016; Holm 0.114), 14.5x | t 1.21 (p 0.234), 3.8x |
  | Direct GHG | t 2.98 (p 0.005; Holm 0.050), 38.8x | t 0.74 (p 0.463), 2.5x | t 3.18 (p 0.003; Holm 0.036), 47.0x | t 1.45 (p 0.157), 6.0x |
  | Direct CO2 | t 2.99 (p 0.005; Holm 0.050), 36.9x | t 0.50 (p 0.623), 1.9x | t 3.14 (p 0.003; Holm 0.037), 42.4x | t 1.30 (p 0.202), 4.9x |

  - Under the manufacturing mapping the team values are 14 to 47 times the fitted value; under the transport mapping they are 1.9 to 6.0 times.
  - The transport mapping is not rejected, but it still under-predicts (EPA: 0.192 predicted vs 0.531 actual for Aero, 0.271 vs 1.019 for Ships). Its non-rejection partly reflects wide prediction intervals: the fit R2 is 0.54 on EPA and 0.40 to 0.42 on the direct measures.
  - After Holm over the 12 tests, the four direct-measure rejections of the manufacturing mapping survive (Holm p 0.036 to 0.050). The two EPA-based ones do not (0.052 for Aero, 0.114 for Ships), although they pass Benjamini-Hochberg (0.016 and 0.033).
  - This is exploratory evidence. The source file itself cannot be checked.
- Oil, Coal, Mines, Chems and Trans (rank from the top):

  | Industry | EPA (of 49) | Team (of 41) | Direct GHG (of 49) |
  |---|---|---|---|
  | Chems | 2 (0.824) | 6 | 6 |
  | Coal | 5 (0.724) | 9 | 2 |
  | Trans | 8 (0.501) | 7 | 7 |
  | Oil | 13 (0.377) | missing | 9 |
  | Mines | 17 (0.344) | 8 | 8 |

  Oil is mid-table because the EPA factors are cradle-to-gate per dollar of product. They count the emissions of producing crude and refined products, not of burning them.

### 4. Green-minus-Brown under both rankings

Primary test [M4_emissions_primary_test.csv]: the EPA 5v5 GB FF5+UMD alpha for 2010-01 to 2026-07 (n = 199) is 4.7% a year, t = 1.52, p = 0.129. **Not significant; H0 not rejected.**
- Loadings: Mkt 0.108, SMB -0.328 (t -3.37), HML -0.024 (t -0.24), RMW -0.035, CMA -0.380 (t -2.01), UMD 0.066. R2 = 0.148.

Performance, EPA 5v5 against team 5v5 [M4_emissions_perf.csv]. Full sample starts 1970-01; all windows end 2026-07.

| Window | EPA mean (t) | Team mean (t) | Other statistics |
|---|---|---|---|
| Full 1970 | 2.5% (1.40) | -0.5% (-0.35) | EPA vol 12.7%, Sharpe 0.20, max DD -71.2%. Team 9.7%, -0.05, -69.8% |
| Post-2010 | 6.4% (1.72, p = 0.085) | -1.8% (-0.68) | EPA vol 12.3%, Sharpe 0.52, max DD -41.5%. Team 9.9%, -0.18, -50.9% |
| Validation | 5.4% (1.22) | -0.7% (-0.22) | |
| Holdout | 9.6% (1.61) | -5.4% (-0.99) | EPA Sharpe 0.70 |
| COVID | -1.0% | +1.8% | |
| Inflation/rates | -3.5% | -7.6% | |
| Last 18 months | 13.2% (0.96) | -14.7% (-1.83) | |
| Last 12 months | 14.0% (0.70) | -19.9% (-2.19) | |

- Turnover: two-way traded notional (buys plus sells, both legs) from monthly re-equal-weighting is 0.78 a year for EPA and 0.69 for the team post-2010. At 10 bp per unit traded that costs 0.08% and 0.07% a year. This excludes the initial build and the rebalancing inside the value-weighted industry portfolios.

Alphas [M4_emissions_alpha_grid.csv, M4_emissions_alphas.csv]:

| Window | EPA CAPM (t) | EPA FF3 (t) | EPA FF5+UMD (t) | Team FF5+UMD (t) |
|---|---|---|---|---|
| Post-2010 | 5.6% (1.43) | 4.4% (1.32) | 4.7% (1.52) | -0.2% (-0.07) |
| Full 1970 | 1.4% (0.78) | 2.4% (1.43) | 4.5% (2.58) | 2.2% (1.60) |
| Holdout | 6.2% (1.09) | 5.0% (1.05) | 3.9% (0.70) | -4.4% (-0.90) |

- The FF3 HML loading survives the re-ranking: post-2010 it is -0.267 (t -4.12) for EPA and -0.298 (t -5.75) for the team. Under FF5+UMD the EPA spread's value tilt shows up as CMA (-0.380) and SMB (-0.328), not HML.
- The recent EPA gains are mostly market beta [M4_emissions_recent_beta.csv]. Over the last 18 months the CAPM beta is 0.91 and the market excess return is 11.9% a year, so beta x market is 10.8 of the 13.2 points; the CAPM alpha is 2.4%. Over the last 12 months the CAPM beta is 1.37 and beta x market is 19.9 points against a 14.0% return; the CAPM alpha is -6.0%.
- The FF5+UMD market betas over the same windows are 1.20 (t 3.72) and 1.38 (t 7.01) [M4_emissions_alphas.csv]. Those regressions fit 7 parameters to 18 and 12 observations, so all of this is descriptive.
- Beta explains little of the longer windows: 0.8 of the 6.4 points post-2010 (CAPM beta 0.06) and 3.4 of the 9.6 points in the holdout (CAPM beta 0.26).

### Robustness [M4_emissions_post2010_family.csv, M4_emissions_primary_sensitivity.csv, M4_emissions_alpha_grid.csv]

Pre-planned EPA variants:
- Post-2010, none of the 9 specifications has a significant FF5+UMD alpha. Alphas run from 1.9% (median, t 0.47) to 5.5% (any-link, t 1.74). The smallest raw p is 0.052 (EPA-within-41, 8 vs 8) and the smallest Holm p is 0.471. Excluding FF49 Other gives 3.6% (t 0.87).
- Holdout: none significant; the largest t is 1.74 (without margins).
- Full sample, 1970 to 2026: the FF5+UMD alpha is significant across most variants. 7 of 9 have raw p < 0.05 and 5 of 9 survive Holm within the family: EPA 5v5 4.5% (t 2.58, Holm p 0.049), 8 vs 8 (Holm p 0.014), without margins (0.011), any-link (0.046) and median 8 vs 8 (0.040). The two that fail are median 5v5 (t 1.72) and excluding Other (t 1.48).
- That full-sample alpha comes from the factor adjustment, not from the raw return. The raw mean is 2.5% (t 1.40), the CAPM alpha 1.4% (t 0.78) and the FF3 alpha 2.4% (t 1.43). The FF5+UMD alpha is larger because the spread is short CMA (-0.345, t -3.04) and short UMD (-0.096, t -2.02), both of which earned positive premia over the period.
- It also rests on a 2022 sort applied back to 1970 and on thin early legs: Softw had 1 firm in 1970-01, Other 4, Coal 4, Agric 5 [M4_emissions_leg_breadth.csv]. It is absent post-2010 (4.7%, t 1.52) and weak pre-2010 (4.0%, t 1.81, p 0.070, on a raw pre-2010 mean of 0.9%, t 0.46).

Leg membership (added after independent verification; not pre-specified) [M4_emissions_primary_sensitivity.csv]:
- Smoke enters EPA Green by 0.0012 kg per dollar over Chips (0.1010 vs 0.1022). It is a 1-NAICS portfolio with 10 firms in 1970-01, 6 in 2010-01 and 5 in 2026-07, and never fewer than 3 [M4_emissions_leg_breadth.csv].
- With Chips in place of Smoke, the post-2010 FF5+UMD alpha is 5.0% (t 1.68, p 0.092).
- Dropping each of the 10 leg members in turn gives post-2010 alphas of 3.1% to 5.6%, with p from 0.087 (drop Coal) to 0.264 (drop Chems).
- The primary non-rejection does not depend on any single industry. The Brown boundary is not close: Coal (0.724) is 0.131 above the next industry, Gold (0.593) [M4_emissions_key_numbers.csv].

### Exploratory: EPA minus team, the effect of the ranking alone [M4_emissions_perf.csv, M4_emissions_alpha_grid.csv]

The difference series is EPA 5v5 GB minus team 5v5 GB, so it measures how much the choice of ranking alone changes the static spread. It was labelled exploratory before any return was computed.

| Window | Raw mean (t, p) | CAPM alpha (t) | FF3 alpha (t) | FF5+UMD alpha (t) |
|---|---|---|---|---|
| Post-2010 | 8.2% (2.84, p 0.004) | 6.4% (2.30) | 5.5% (2.08) | 4.9% (1.93) |
| Holdout | 15.0% (2.31, p 0.021) | 10.2% (2.30) | 9.6% (2.03) | 8.3% (1.45) |
| Validation | 6.0% (2.01, p 0.045) | 5.1% (1.59) | 4.8% (1.52) | 3.5% (1.17) |
| Full 1970 | 3.0% (1.86, p 0.063) | 2.0% (1.24) | 1.9% (1.18) | 2.3% (1.44) |

- It is suggestive that the team's undocumented ranking itself, not only its timing rule, accounts for much of its weak Green-minus-Brown record since 2010.
- The effect weakens as factors are added (post-2010 t 2.84 raw, 1.93 under FF5+UMD), so part of it is a difference in factor loadings.
- The ledger holds 42 EPA-minus-team rows, and the table above shows 16 of them (4 windows x raw/CAPM/FF3/FF5+UMD). The post-2010 raw p of 0.004 becomes 0.071 under both Holm and BH over the 16 shown, and 0.178 under Holm over the 42. None of the 16 survives adjustment. It does not change the verdict, because the EPA spread on its own is not significant (primary test above).

### Exploratory: Oil and Coal in Brown [M4_emissions_energy.csv; figure M4_emissions_energy_legs]

Energy rally (2021-01 to 2022-12, 24 months):

| Specification | GB return a year (cumulative) | FF5+UMD alpha (t) |
|---|---|---|
| Team GB | -19.2% (-33.4%) | |
| Team Brown plus Oil and Coal | -34.8% (-51.7%) | -26.9% (-2.63) |
| EPA GB (Brown already holds Coal) | -19.4% (-33.6%) | |
| EPA GB plus Oil | -24.0% (-39.5%) | |
| EPA GB with Oil and Coal excluded (Coal replaced by Gold) | -0.7% (-2.7%) | |

- Cumulative Brown-leg returns over the rally: team +35.0%, team plus Oil and Coal +83.6%, EPA +67.9%, EPA with Oil and Coal excluded +17.0%.
- Holdout GB: team -5.4%, team plus Oil and Coal -4.0%, EPA +9.6%, EPA plus Oil +9.0%, EPA with Oil and Coal excluded +6.9% a year.
- Putting fossil-fuel producers in Brown makes the 2021-22 loss much deeper. Replacing Coal with the next industry (Gold) cuts the EPA spread's 2021-22 loss from 19.4% to 0.7% a year, so that loss comes from Coal.

### Exploratory: the team's Short-Brown timing rule with the Brown leg swapped [M4_emissions_team_rule_rerun.csv]

My re-implementation reproduces the team exactly: hold 3, 2010-2026 net 0.07%, holdout -3.8% with FF3 alpha t -2.19; hold 6 holdout t -1.66.

| Brown leg | COVID hold 3 | COVID hold 6 | Holdout hold 3 | Holdout hold 6 |
|---|---|---|---|---|
| Team Brown | +5.9% (alpha t 3.21) | +7.4% (t 2.07) | -3.8% (t -2.19) | -2.1% (t -1.66) |
| EPA Brown | +0.5% (t 0.50) | +0.8% (t 0.52) | -1.4% (t -1.30) | +0.1% (t -0.61) |
| Team Brown re-ranked without Aero and Ships (Util, Steel, BldMt, Chems, Trans) | +4.7% (t 1.47) | +1.9% (t -0.39) | -1.8% (t -1.30) | +0.3% (t 0.10) |

- On the EPA Brown leg nothing is significant in the post-2010, validation, holdout, COVID or inflation/rates windows. The largest FF3 alpha |t| there is 1.75 (hold 3, validation). Post-2010: hold 3 +0.9% (t 1.13), hold 6 +2.4% (t 1.46).
- The 12- and 18-month windows are descriptive, and on the EPA Brown leg they give opposite-signed FF3 alpha t-stats of about 2.7: +2.72 for hold 3 over the last 12 months (where the net return is -2.2% a year) and -2.77 for hold 6 over the last 18 months.
- The COVID episode's significance depends on Aero and Ships. Re-ranking the team file without them brings in Chems and Trans as next in line, so this is a substitution, not a pure removal.
  - Hold 3: the FF3 alpha t falls from 3.21 to 1.47, although most of the return survives (5.9% to 4.7% a year).
  - Hold 6: both go. The return falls from 7.4% to 1.9% a year, and the FF3 alpha from 5.2% (t 2.07) to -2.1% (t -0.39).

## Implications for the project verdict

- The team's emissions ranking is not sound as reported.
  - Its source, units, scope and vintage are undocumented, and its construction cannot be identified from the file.
  - It appears to be built on a coarser industry scheme (3 groups of identical values).
  - Two of the five Brown industries (Ships 2nd, Aero 3rd) carry values far above what aircraft and ship manufacturing implies and much closer to air- and water-transport levels. This is consistent with, not proof of, a transport mis-mapping.
  - Its Green leg shares no industry with a supply-chain Green leg.
  - The write-up's statement that "this ranking comes from the data" should be qualified.
- A complete supply-chain measure changes who is Green (Banks, Insur, Softw, Hardw, Smoke) and Brown (Util, Chems, Other, Agric, Coal). It flips the raw spread from -1.8% to +6.4% a year post-2010 and from -5.4% to +9.6% in the holdout. The ranking effect itself (EPA minus team) is 8.2% a year post-2010 (t 2.84, exploratory; not significant after multiplicity adjustment).
- It does not produce an alpha. The primary test fails (4.7%, t = 1.52), no post-2010 variant survives, the result does not hinge on any single leg member, and the recent gains are mostly market beta.
- The full-sample FF5+UMD alpha is significant in most variants, but it comes from short CMA and UMD loadings rather than the raw return, and it rests on a look-ahead static sort.
- Re-ranking also removes the significance of the COVID episode that the team's timing strategy relied on.
- "Do not implement" stands, and on firmer ground. On the EPA Brown leg the timing rule shows nothing significant in either direction (COVID t 0.50 and 0.52; holdout t -1.30 and -0.61). The COVID gain the team relied on disappears, and the holdout loss also becomes insignificant. The IC sign flip was not re-tested here.
- For the report: disclose the provenance gap and the Aero/Ships problem, and present the EPA ranking as a robustness check rather than a rescue.

## Caveats

- Static sort: both rankings are single snapshots applied to 1970-2026. There is look-ahead in industry membership, and the full-sample numbers are not tradable backtests.
- Not the team's concept: EPA factors are cradle-to-gate supply-chain intensities per purchaser dollar. They cover Scopes 1 and 2 and upstream Scope 3, not downstream use. That may be a different quantity from whatever the team file measures, so disagreement is expected, and the Aero/Ships reading rests on the forensic test rather than on rank disagreement alone.
- Unweighted aggregation: every NAICS code counts equally. FF49 industry returns are value-weighted across firms whose product mix differs from a NAICS average. Util's mean is dominated by the 10 electricity codes, which share one patched factor from a different model vintage (USEEIO v2.0.1, 2012 data), rescaled. Util's rank does not depend on the patch.
- Mapping: the SIC-to-NAICS chain has no shipment weights. Plurality is by count of SIC codes, with 115 ties, 2 manual links and 3 overrides, all documented in `data/derived/ff49_naics_mapping_epa.csv`. Any-link mapping gives Spearman 0.991 against the primary.
- Thin portfolios: Smoke (3 to 10 firms), Coal, Agric, Other and early Softw (1 firm in 1970) make EPA legs idiosyncratic. The Other portfolio is the Ken French residual group (sanitary services, steam, irrigation, cogeneration).
- Short windows: FF5+UMD on 12 to 24 observations (last12, last18, energy_rally) is descriptive. The 2021-22 window, the calendar-year slices and the pre-2010 split are my exploratory choices, not PERIODS windows.
- Costs: 10 bp on two-way traded notional from re-equal-weighting only. The initial build and the internal rebalancing of the value-weighted industry portfolios are not costed.
- Provenance of the team file is inferred from its structure. Neither the coarse-scheme reading nor the transport mis-mapping can be confirmed without the original source, and the file's construction (direct or supply-chain) cannot be identified.

## Output files

- Code: `modules/M4_emissions/run.py` (entry point), `mapping.py` (NAICS-SIC-FF49 chain, EPA and USEEIO factors, electricity patch), `team_strategy.py` (faithful re-implementation of the team's Short-Brown rule).
- Derived data: `data/derived/ff49_emissions_epa.csv` (ff49, epa_sc_mean, epa_sc_median, epa_sc_nomargin_mean, n_naics, team_intensity, rank_epa, rank_team, plus variants; rank 1 = lowest intensity), `data/derived/ff49_naics_mapping_epa.csv` (NAICS to FF49 assignment with factors, SIC codes, flags), `data/derived/naics17_sic87_ff49_links.csv` (full concordance chain).
- Raw downloads: `data/raw/census_*_NAICS.xls(x)`, `data/raw/USEEIOv2.0.1-411.xlsx`, `data/raw/useeio201_ghg_DN.csv`, `data/raw/epa_sc_ghg_v10_2016_*.xlsx` (v1.0 cross-check, not used in results), `data/raw/epa_sc_ghg_v13_About.docx`.
- Tables in `outputs/tables/`, all prefixed `M4_emissions` (a `.tex` exists where marked *):
  - Provenance and mapping: `_provenance.csv`, `_team_file_ties.csv`, `_mapping_summary.csv`, `_key_numbers.csv`
  - Intensities and rankings: `_ff49_intensity`*, `_spearman`*, `_membership`*, `_key_industries`*, `_aero_ships_naics`*, `_aero_ships_calibration`* (now with team/predicted ratio, Holm and BH over the 12 tests)
  - Spreads: `_legs`*, `_perf`*, `_alphas`* (every spec, window and model), `_alpha_grid`* (team, EPA and EPA minus team), `_primary_test`*, `_post2010_family`* (post2010, full_1970, pre2010 and holdout families with Holm and BH), `_primary_sensitivity`* (new: leg-membership sensitivity), `_recent_beta`* (new: CAPM beta decomposition), `_leg_regressions`*, `_leg_breadth`*, `_energy`*, `_team_rule_rerun`*, `_gb_monthly_returns.csv`
  - `_tests_ledger.csv` (802 rows)
- Figures in `outputs/figures/`: `M4_emissions_intensity_scatter` (team vs EPA, log levels and ranks), `M4_emissions_cum_gb` (cumulative GB under both rankings, 1970 on and post-2010), `M4_emissions_energy_legs` (Brown legs and GB with and without Oil and Coal, 2020 on).
- Verification: `modules/M4_emissions/verify/verify_m4.py`, `verify_results.csv`, `verify_sensitivity.csv` (independent verifier's code and outputs).

## Response to verification

I re-derived every point from the output tables and, where needed, new code in `run.py`. I agree with all eleven and have made each fix. Numbers in the original 750 ledger rows are unchanged (maximum difference 0).

- F1 (FINDINGS.md missing): agreed. Subagents in this pipeline cannot write report .md files, so this text was returned to the orchestrator to be saved at `modules/M4_emissions/FINDINGS.md`. VERIFY.md has the same status.
- F2 (direct-intensity inference): agreed. The Spearman correlations (0.700 EPA, 0.649 USEEIO total, 0.492 direct GHG, 0.503 direct CO2) favour a supply-chain ranking, while only the spread looks direct. Section 1 now says the construction cannot be identified, and names the EPA v1.3 spreads (135x NAICS, 33x FF49). I added a second, related supply-chain spread (USEEIO total, 45x across FF49 means) to `M4_emissions_key_numbers.csv`, and I note that even the direct FF49 spread (531x) is well short of 6,051x.
- F3 ("match" transport): agreed. The calibration table now has team/predicted ratios and Holm and BH p-values over the 12 tests. The EPA-based manufacturing rejections do not survive Holm (0.052, 0.114); the direct-measure ones do (0.036 to 0.050). The transport mapping under-predicts by 1.9x to 6.0x. The wording is now "far above what manufacturing implies, much closer to transport levels, consistent with but not proof of a mis-mapping".
- F4 (full-sample robustness wording): agreed. 7 of 9 variants have raw p < 0.05 and 5 of 9 survive Holm. The text now says so, and then explains why the alpha is not evidence for the strategy (raw 2.5%, CAPM 1.4%, FF3 2.4%, all t < 1.5; short CMA and UMD; static look-ahead sort; absent post-2010).
- F5 ("nothing significant"): agreed. The claim is now limited to the post-2010, validation, holdout, COVID and inflation/rates windows. The last-12 and last-18 results (+2.72 and -2.77) are reported as descriptive.
- F6 ("depends largely"): agreed. For hold 3, only the significance of the COVID result depends on Aero and Ships (the return mostly survives, 5.9% to 4.7%). For hold 6, both the return and the alpha go. The re-ranked leg brings in Chems and Trans, and the text says so.
- F7 (EPA-minus-team omitted): agreed, and added as its own exploratory subsection. One nuance: the effect shrinks as factors are added (post-2010 FF5+UMD t 1.93, holdout 1.45), so part of it is a difference in factor loadings.
- F8 (Smoke/Chips margin): agreed. `run.py` now produces `M4_emissions_primary_sensitivity.csv` (Chips for Smoke in post-2010, holdout and full sample; drop-one for all 10 members in post-2010), and these rows are in the ledger as post-verification robustness. It reproduces the verifier's numbers exactly (5.0%, t 1.68, p 0.092; smallest drop-one p 0.087).
- F9 (turnover label): agreed. sum|w_drift - 1/n| is buys plus sells. The docstring, the perf.tex caption and this text now say two-way and note what is not costed. No numbers change.
- F10 (ledger completeness): agreed. I added the 32 calendar-year mean tests (as exploratory, 12 observations) and the 7 Kendall tests. With the 13 F8 rows, the ledger grows from 750 to 802 rows, and every p-value printed in an M4 table is now in it.
- F11 (which beta): agreed. The new `M4_emissions_recent_beta.csv` splits the raw return into CAPM alpha plus beta x market. The text now leads with the CAPM decomposition (10.8 of 13.2 points over 18 months) and gives the FF5+UMD betas with their 7-parameter caveat.
- I also corrected four rounding slips in the earlier draft: post-2010 EPA mean t 1.72 (not 1.73), post-2010 EPA CAPM t 1.43 (not 1.44), post-2010 team FF5+UMD t -0.07 (not -0.08), and the largest holdout t 1.74 (not 1.75). In the energy figure, the team series now uses the same gray as in the cumulative-GB figure.
=====END FINDINGS.md=====