"""Editorial reorganization of the two executed notebooks (no re-execution).

Takes the executed notebooks from the audit-trail folder (final_submission/) and writes
notebooks/01_Green_Climate_Strategy.ipynb and notebooks/02_Charisma_Final_Strategy.ipynb:
* markdown cells are rewritten into the final section structure;
* code cells keep their executed outputs; only path/setup lines are edited for the new folder layout;
* saved figures are embedded as attachments so they are visible without running anything.
"""
from __future__ import annotations

import base64
import copy
import json
from pathlib import Path

SRC = Path("/home/claude/final_submission")
OUT = Path("/home/claude/final_submission_organized")


def md(text, attachments=None):
    c = {"cell_type": "markdown", "metadata": {}, "source": text.strip("\n")}
    if attachments:
        c["attachments"] = attachments
    return c


def fig_md(caption, png):
    name = png.name
    data = base64.b64encode(png.read_bytes()).decode()
    return md(f"**{caption}**\n\n![{name}](attachment:{name})", {name: {"image/png": data}})


def set_src(cell, text):
    cell = copy.deepcopy(cell)
    cell["source"] = text.strip("\n")
    return cell


def replace_in(cell, old, new):
    cell = copy.deepcopy(cell)
    s = "".join(cell["source"])
    assert old in s, old[:60]
    cell["source"] = s.replace(old, new)
    return cell


# ============================================================ Notebook 1: Green / Climate
nb = json.load(open(SRC / "01_climate_alpha_pivot/Climate_Alpha_Research_Summary.ipynb"))
C = nb["cells"]

setup = replace_in(C[1], '''from climate_lib.common import load_team, corrected_macro''',
'''import sys
REPO = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()   # final_submission_organized/
sys.path.insert(0, str(REPO / "supporting" / "code" / "green"))              # climate_lib (team pipeline)

from climate_lib.common import load_team, corrected_macro''')
setup = replace_in(setup, '''ROOT = Path.cwd()
DATA, FIG, TAB = ROOT / "data", ROOT / "figures", ROOT / "tables"''',
'''DATA, FIG, TAB = REPO / "data" / "green", REPO / "figures", REPO / "tables"''')

cells = [
    md("""
# Notebook 1 — Green / Climate Alpha Strategy (initial research direction)

**MFE 230GA Active Asset Management — Final Project, Group 4**
Hashim Almodamagha, Aditya Aryan, Jack Duncan, Charishma Takkallapalli, Cristhian Ruiz Cardozo

This notebook is the analytical record of our **first** research direction and of why we did **not**
implement it. The final strategy is in `02_Charisma_Final_Strategy.ipynb`; the full discussion is in
`MFE230GA_Final_Project.pdf` (Section 2 and Appendix A).

The outputs shown are from the executed, validated run. Cells marked *imported verified evidence* load
results computed in the team's research extension (`230GA-Final-Project-hashim-research-extension`),
where each number was produced twice by independent code; they are not rerun here.

## 1. Research question

Can differences in industry carbon intensity, timed by climate-transition attention, produce a
tradable, factor-neutral return across the Fama–French 49 industries?

The idea came from Homework 1, where we compared high- and low-emission industries and used an AI
assistant to propose strategies. The mechanism: if investors re-price transition risk when climate
concern rises unexpectedly (Pástor, Stambaugh and Taylor, 2021, 2022), high-emission ("Brown")
industries should underperform after spikes in climate attention, even without a permanent green premium.
**Falsification:** if a holdout never used in design shows no such profit, the thesis is wrong.
"""),
    setup,
    md("""
## 2. Data

Files in `data/green/` (the team's inputs, unchanged): Ken French 49 value-weighted industry returns and
FF3 factors (July 1926–July 2026), one cross-section of emissions intensity for 41 of the 49 industries
(the Homework 1 course file), and macro series including the "climate attention" column. We add FRED series
EMVENRGYENVREG to check what that column is, the team's committed results table, and the imported verified
extension results.
"""),
    C[3],
    md("""
## 3. Green/Brown signal

* **Legs:** Green = five lowest-intensity industries, Brown = five highest, equal-weighted.
* **Hedge:** rolling 60-month FF3 regression of the Brown leg; betas estimated through month t hedge month t+1.
  The traded object is the hedged Brown return.
* **Signal:** 60-month z-score of log(1 + attention). When it crosses its past-only 80th percentile, the rule
  shorts the hedged Brown leg for 3 or 6 months ("Original"; "Pure" first removes the part of attention
  explained by lagged macro data). Size targets 5% residual volatility, capped at 1.
* **Costs:** 10 bp on the leg, 5 bp on the market overlay, 25 bp on SMB/HML overlays, per unit turnover.

### 3.1 What is the "attention" series?
"""),
    C[5],
    md("""
**Interpretation.** EMVENRGYENVREG is the Baker, Bloom, Davis and Kost (2019) Equity Market Volatility tracker
for energy and environmental regulation: a count of newspaper articles about **stock-market volatility** that
mention that topic. It is not a climate-concern index, and since late 2021 it is mostly exact zeros. We did not
know this when we designed the rule.
"""),
    md("""
## 4. Baseline strategy: the team's timing rules as first implemented

`run_pipeline()` with default arguments reproduces the team's committed comparison table exactly (checked below).
Design window: 2010-01 to 2022-07. Holdout, never used in design: 2022-08 to 2026-07.
"""),
    C[10],
    md("""
**Interpretation.** In the design window the 6-month rules earned about 2.5% a year net with FF3 alpha t above 2.
In the holdout every discrete rule lost 2.1% to 3.8% a year.
"""),
    md("""
## 5. Key alternative implementations: the corrected baseline

Two input problems were fixed before any further test: (1) attention and the purification controls are lagged one
month, because month-t attention may not be published by the end of month t; (2) the October 2025 CPI print, never
published, is interpolated. The table also shows the continuous version of the rule (position scales smoothly with the
signal) and the untimed always-short benchmark. No verdict changes.
"""),
    C[12],
    md("""
## 6. Out-of-sample and regime evidence

### 6.1 Does COVID certify the timing? Compare the rule with an untimed short of the same leg.

The always-short position uses the same leg, hedge and volatility target but ignores the signal. The paired alpha is
the FF3 alpha of (rule return − always-short return).
"""),
    C[14],
    md("**Interpretation.** In COVID the rule's edge over simply being short the same leg is 1.84% a year (t = 0.87): the gain is mostly exposure, not timing."),
    md("### 6.2 Does the signal still point the right way out of sample?"),
    C[16],
    md("**Interpretation.** The continuous signal's IC is −0.15 (t = −2.19) in design and +0.06 in the holdout: the relationship reversed out of sample."),
    md("### 6.3 Figure: timed rule vs. untimed always-short position"),
    C[18],
    fig_md("Figure C1. Cumulative net return, corrected baseline, January 2010–July 2026. Grey: COVID; shaded: holdout.",
           SRC / "01_climate_alpha_pivot/figures/C1_timed_vs_always_short.png"),
    md("""
## 7. Factor interpretation and costs

### 7.1 The raw Green-minus-Brown spread is a value bet
"""),
    C[8],
    md("**Interpretation.** The raw spread loads −0.23 on HML over 1970–2026 (t = −4.63) and −0.30 since 2010 (t = −5.74), with no significant alpha."),
    md("### 7.2 Are costs the reason? Turnover, cost drag and gross holdout alpha"),
    C[20],
    md("**Interpretation.** Costs take at most about 0.6 percentage points a year, but holdout alphas are negative before costs (at best −1.5%). Costs are not why the strategy fails."),
    md("""
## 8. Robustness evidence already obtained (imported verified evidence)

The research extension ran further modules whose inputs (EPA supply-chain factors, Census crosswalks, MCCC and CPU
climate-concern indices, pre-1970 data) are not part of this package: the signal audit (M1, M1b), the frozen 1994–2009
test (M8), the EPA emissions rebuild (M4), carbon-aware industry momentum (M5) and the project-wide multiple-testing
ledger (M7). Each headline number was computed twice by independent code. `supporting/code/green/build_verified_evidence.py`
copied the numbers we quote, with source file and row, into `data/green/verified_extension_results.csv`. **These results
are loaded, not recomputed.**
"""),
    C[22],
    md("### 8.1 Summary of the experiments that changed our view"),
    C[24],
    md("""
## 9. Decision: do not implement

In order of importance:

1. **Out-of-sample failure.** The untouched holdout lost money for every rule, the frozen 1994–2009 test failed
   (timing alpha −0.18% a year, t = −0.27), and the signal's IC changed sign in the holdout.
2. **The signal is mislabeled.** It is a stock-market-volatility news count, uncorrelated with climate-concern
   measures; climate indices fed through the same rules earn nothing (0 of 12 validation alphas with t ≥ 1.96).
3. **Timing cannot be separated from exposure.** The best window (COVID) is mostly earned by an untimed short of the
   same Brown leg.
4. **Factor exposure and data limits.** The raw spread is a short-value bet; the emissions file is one undated snapshot
   applied backward (look-ahead in leg membership), and an EPA rebuild moves two of the five Brown industries to mid-table.
5. **Multiple testing.** Across 73 module primary alphas the smallest Holm-adjusted p is 1.00.

Costs are not the reason: gross holdout alphas were already negative.

**The economic idea was plausible, but the evidence was not stable or clean enough to support implementation.**

## 10. Why we pivoted

We did not search for another specification to rescue the strategy. One lesson carried over: every alternative that
looked profitable was a known factor in disguise, and an equal-weight industry momentum book was essentially UMD
(beta ≈ 1). That led to the sharper question tested in `02_Charisma_Final_Strategy.ipynb`: **do analyst EPS revisions
contain information beyond industry momentum, after FF5 and UMD?**

---
*Appendix: export of the tables used in the final report (writes to `tables/`).*
"""),
    C[26],
]
nb1 = copy.deepcopy(nb); nb1["cells"] = cells
json.dump(nb1, open(OUT / "notebooks/01_Green_Climate_Strategy.ipynb", "w"), indent=1, ensure_ascii=False)

# ============================================================ Notebook 2: Charisma
nb = json.load(open(SRC / "02_main_project/MFE230GA_Final_Analysis.ipynb"))
C = nb["cells"]

setup = replace_in(C[1], '''ROOT = Path.cwd()
if not (ROOT / "config.py").exists():          # allow running from another directory
    ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import config  # noqa: E402

PT = config.TABLES          # pipeline tables  (pipeline_results/tables)
FIG = ROOT / "figures"      # report figures
TAB = ROOT / "tables"       # report tables (CSV + LaTeX)''',
'''REPO = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()   # final_submission_organized/
sys.path.insert(0, str(REPO / "supporting" / "code" / "charisma"))          # project code: config.py, src/
import config  # noqa: E402

PT = config.TABLES          # validated pipeline tables (data/charisma/results/tables)
FIG = REPO / "figures"      # report figures
TAB = REPO / "tables"       # report tables (CSV + LaTeX)''')
setup = replace_in(setup, '''RUN_PIPELINE = True     # Phases 4-7 from data/processed/signals.parquet (~90 s)
RUN_ROBUSTNESS = False  # Phase 8 grid takes ~7 min; False reads the saved grid output''',
'''RUN_PIPELINE = False    # False: load the validated results in data/charisma/results (default).
                        # True: recompute Phases 4-7 from data/charisma/processed/signals.parquet (~90 s).
RUN_ROBUSTNESS = False  # True reruns the Phase 8 grid (~7 min); False reads the saved grid output.''')

pipe = copy.deepcopy(C[3])

cells = [
    md("""
# Notebook 2 — Charisma: Final Strategy (analyst revisions vs. industry momentum)

**MFE 230GA Active Asset Management — Final Project, Group 4**
Hashim Almodamagha, Aditya Aryan, Jack Duncan, Charishma Takkallapalli, Cristhian Ruiz Cardozo

This is the **main empirical analysis** of the final project, discussed in `MFE230GA_Final_Project.pdf` (Section 4).
It builds every table and figure of that section from the validated results. The outputs shown are from the executed run.
No WRDS access is needed to read or rerun it: the industry-level signal panels are in `data/charisma/processed/`.

## 1. Research question and falsification criterion

**Question.** Do industry-level analyst EPS revisions contain information about next-month industry returns *beyond*
industry momentum, and does that information survive portfolio construction, risk control, trading costs, factor
attribution and robustness tests?

**Thesis (fixed before testing).** Earnings news diffuses slowly, so industries with net upward analyst revisions
outperform over the next month, and this signal carries information beyond price momentum.

**Falsification criterion (fixed before testing).** If the revision signal or the blended strategy shows no FF5+UMD
alpha with t ≥ 2, net of costs, particularly after 2010, we conclude **"do not implement"**. Windows with fewer than
36 months are reported but labeled low power.
"""),
    setup,
    md("""
### Final analysis pipeline

With `RUN_PIPELINE = False` (default) the notebook reads the validated pipeline output in `data/charisma/results/`.
With `True` it recomputes Phases 4–7 (IC and blend, risk model and holdings, backtest and costs, factor attribution) from
the industry signal panel using the project code in `supporting/code/charisma/src/`. The phases that build that panel from
licensed I/B/E/S and CRSP security-level data (pulls, cleaning, industry aggregation) need WRDS and are not part of this
notebook. *The log below is from the validated run (`RUN_PIPELINE = True`) that produced the result files.*
"""),
    pipe,
    md("""
## 2. Data

* **Industry returns:** Ken French 49 value-weighted industry portfolios, monthly (`data/charisma/raw/kf_ind49_vw.parquet`).
* **Revisions:** I/B/E/S summary statistics (annual EPS, FY1, US firms), linked to CRSP through the WRDS I/B/E/S–CRSP
  link table (score ≤ 2), aggregated to industries. Only the industry-level panel is included (`signals.parquet`);
  the security-level WRDS data are licensed and not redistributed.
* **Factors:** FF5 (2×3), UMD and short-term reversal (`data/charisma/raw/`).

The link table has no valid links in 2026, so REV is missing from January 2026; we keep it missing and report coverage.
"""),
    C[5],
    md("""
## 3. Signals

* **MOM:** compounded industry return over months t−11 to t−1 (skips month t).
* **REV:** firm REV = (#up − #down)/#estimates with ≥ 3 estimates; industry REV = market-cap-weighted mean, requiring ≥ 5 covered firms.
* **REV orthogonal:** residual of a monthly cross-sectional regression of REV on MOM — the direct test of the thesis.
* **Blend:** HW2 rule w ∝ R⁻¹·IC, with R and IC estimated on an expanding window using only months before t (60-month minimum, first blend January 1995).

Each signal is z-scored across industries every month and winsorized at ±3.

## 4. IC analysis

Monthly Spearman IC between the signal at the end of month t and industry returns in month t+1; Newey–West (6 lags)
t-statistics. The `1985-2025` columns use only months where REV exists (492), so all signals are compared on the same months.
"""),
    C[7],
    md("**Interpretation.** MOM predicts (IC 0.047, t = 3.96). REV is weak alone (0.010, t = 1.06) and its part orthogonal to momentum is zero (−0.000, t = −0.05; post-2010 −0.007, t = −0.50)."),
    set_src(C[8], """
### 4.1 Evolution through time: is the REV signal decaying?

The expanding blend weight on REV falls from about 0.34 in 1990 to below zero by 2010. To see why, we split the REV sample
into three blocks. This split was chosen after seeing the blend weights, so it is descriptive and plays no role in the verdict.
"""),
    C[9],
    md("**Interpretation.** REV had a significant IC in 1985–1994 (0.045, t = 2.35) and none since 1995. Even then its orthogonal part was not significant (0.020, t = 1.13)."),
    md("### 4.2 Figure 1 — cumulative IC and the blend weights"),
    C[11],
    fig_md("Figure 1. (a) Cumulative Spearman IC over the 492 REV months, 1985–2025. (b) Expanding IC-based blend weights.",
           SRC / "02_main_project/figures/fig1_ic_and_weights.png"),
    md("""
## 5. Portfolio construction

Grinold–Kahn alphas α = IC · ω · z (demeaned, so dollar neutral). Mean-variance holdings h = Σ⁻¹α/(2λ) with
Σ h = 0 and |hₙ| ≤ 10% of gross; λ is reset every month so ex-ante active risk is exactly 5% a year. Σ is an EWMA
covariance of the 49 industries (30-month half-life, the HW1 choice; 60-month minimum), shrunk 50% toward its
diagonal because the unshrunk model realized about 10% risk with roughly 4× gross. ω is each industry's volatility
residual to the equal-weighted industry average.

## 6. Risk
"""),
    C[13],
    md("**Interpretation.** Ex-ante risk is 5% by construction. The blend realizes 6.6% (1.32× target) and MOM 6.2%, mainly because of the 2009 momentum crash. Median λ for the blend is 2.32 (10th–90th percentile 1.93–3.23)."),
    md("""
## 7. Portfolio performance

Gross return in month t+1 is h(t)·r(t+1). Turnover is measured against last month's weights after they drift with
returns; the one-way cost is charged on the next month's return. The `common` window (formation months Jan 1995–Dec 2025)
is the only window in which all four strategies trade.
"""),
    C[15],
    C[17],
    fig_md("Figure 2. (a) Growth of $1, net of 20 bp, February 1995–January 2026, log scale. (b) Blend drawdown, net of 20 bp.",
           SRC / "02_main_project/figures/fig2_cumulative_drawdown.png"),
    md("""
## 8. Turnover and transaction costs

From the table in Section 7: REV books trade about 174% of capital a month (182% for REV orthogonal) against 51% for MOM
and 58% for the blend. REV's break-even one-way cost is about 1 bp, so at 20 bp it loses 4.0% a year (net Sharpe −0.80).
Industry revision ranks change too much month to month to be traded profitably. The cost level at which the blend's
**6-factor** alpha disappears is in Section 9.3, because it needs the factor data loaded in Section 9.
"""),
    set_src(C[18], """
## 9. Factor attribution: is the alpha new, or is it momentum?

Net returns (20 bp) regressed on FF5, FF5+UMD (primary) and FF5+UMD+short-term reversal, with NW(6) t-statistics.
Each return month t+1 is matched to factor returns of month t+1.
"""),
    C[19],
    md("**Interpretation.** Against FF5 the blend shows 2.4% a year (t = 2.21). Adding UMD cuts it to 0.2% (t = 0.36), with a UMD loading of 0.30 (t = 20.4); after 2010 it is −0.0% (t = −0.02). REV and REV orthogonal have significantly negative net alphas. **The blend's apparent alpha is momentum exposure.**"),
    set_src(C[20], """
### 9.1 Independent check of the key regression

We re-estimate the blend's FF5 and FF5+UMD alphas with statsmodels directly (not through `src/attribution.py`).
"""),
    C[21],
    md("### 9.2 Figure 3 — alpha before and after controlling for UMD"),
    C[25],
    fig_md("Figure 3. Annual net alpha (20 bp) with 95% Newey–West intervals against FF5 (grey) and FF5+UMD (blue).",
           SRC / "02_main_project/figures/fig3_alpha_ff5_vs_umd.png"),
    set_src(C[22], """
### 9.3 Gross alpha and the cost that erases it

Gross returns and returns net of 10, 20 and 30 bp regressed on FF5+UMD. Dividing the monthly gross alpha by mean monthly
turnover gives the one-way cost at which the 6-factor alpha is exactly zero. The pre-registered criterion uses 20 bp.
"""),
    C[23],
    md("**Interpretation.** The blend's gross 6-factor alpha (1.6%, t = 2.44) is smaller than MOM's alone (2.4%, t = 3.18): revisions dilute rather than add. It is fully consumed at 23 bp and not significant at 10 bp (t = 1.40) or after 2010."),
    set_src(C[26], """
## 10. Horizon and regime analysis

Required windows: full sample, post-2010, and the most recent 18 signal months (March 2025–August 2026). REV is missing
after December 2025, so the REV-based strategies have only 10 return months in the recent window. Regressions on fewer
than 36 months are labeled **LOW POWER** and not used for the verdict.
"""),
    C[27],
    md("### 10.1 Stress years (2009, 2020) and rolling 36-month alpha"),
    C[28],
    fig_md("Rolling 36-month FF5+UMD alpha of the blend, net of 20 bp (pipeline output).",
           SRC / "02_main_project/pipeline_results/figures/rolling_alpha_blend.png"),
    md("**Interpretation.** The blend's recent t = 3.40 comes from 10 observations and carries no information. In 2009 the blend lost 13.3% (UMD −52.8%) and REV did not hedge the crash (−18.3%). The rolling alpha averages −0.1% a year with no persistent positive regime."),
    set_src(C[29], """
## 11. Robustness

One design choice changes at a time around the base case; each row reruns signals → IC blend → holdings → backtest for
the blend and is scored on formation months Jan 1995–Dec 2025. Rows marked (*) need WRDS stock-level files; a teammate
ran them on a different cleaned CRSP panel, so they are shown separately and flagged.
"""),
    C[30],
    fig_md("Net Sharpe (20 bp) of the blend over momentum lookback × covariance half-life (pipeline output).",
           SRC / "02_main_project/pipeline_results/figures/robustness_heatmap_sharpe.png"),
    md("**Interpretation.** No reasonable specification reverses the conclusion: the highest FF5+UMD t in the grid is 1.40 (10 bp costs) and the highest net Sharpe 0.38."),
    set_src(C[31], """
## 12. Final decision

The pre-registered criterion requires a positive FF5+UMD net alpha with t ≥ 2. No strategy meets it in the 1995–2025 or
post-2010 window, and no robustness row meets it. The only window with t ≥ 2 is the blend's 10-month recent window
(low power).

**Do not implement the analyst-revision overlay in its current form.** Industry revisions mostly reflect the same news as
industry momentum (average cross-sectional correlation 0.31, zero orthogonal IC), the small independent part they had in
the late 1980s disappeared, and their month-to-month rank changes make them expensive to trade.
"""),
    C[32],
    md("---\n*Appendix: export of the tables and numbers used in the final report (writes to `tables/`).*"),
    C[34],
]
nb2 = copy.deepcopy(nb); nb2["cells"] = cells
json.dump(nb2, open(OUT / "notebooks/02_Charisma_Final_Strategy.ipynb", "w"), indent=1, ensure_ascii=False)
print("written")
