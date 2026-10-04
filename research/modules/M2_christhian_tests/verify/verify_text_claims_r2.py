"""ROUND 2 (corrected FINDINGS text; round-1 claims updated where the text changed, new claims appended).
Check that the numbers written in the M2 FINDINGS text match the module's own CSV outputs (after a fresh rerun).

Reads only outputs/tables/M2_christhian_tests_*.csv; does not import the module code. Each claim is compared with a
tolerance of half a unit in the last printed digit (plus 1e-9). Writes verify/verify_text_claims_r2.csv.
Run: cd /home/hashim/projects/GA/project/research && uv run python modules/M2_christhian_tests/verify/verify_text_claims.py
"""
import pathlib
import sys

sys.path.insert(0, "/home/hashim/projects/GA/project/research/lib")
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from common import TABLES  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parent
M = "M2_christhian_tests"
T = lambda n: pd.read_csv(TABLES / f"{M}_{n}.csv")  # noqa: E731
rows = []


def c(section, claim, value, claimed, dec):
    tol = 0.5 * 10 ** (-dec) + 1e-9
    rows.append(dict(section=section, claim=claim, csv_value=value, claimed=claimed, tol=tol,
                     match=bool(abs(round(value, 12) - claimed) <= tol)))


SP = T("q2_spread_controls")
sp = lambda l, p, e: SP[(SP.legs == l) & (SP.period == p) & (SP.eval_id == e)].iloc[0]  # noqa: E731
# ---- Q2 spread table
claims = {"E:FF3": [(0.54, 0.41, -0.23, -4.63), (-1.12, -0.49, -0.30, -5.74), (-4.59, -0.99, -0.13, -1.34)],
          "E:FF3U": [(1.20, 0.89, -0.26, -5.20), (-0.67, -0.30, -0.32, -6.16), (-3.96, -0.85, -0.11, -1.45)],
          "E:FF5U": [(2.20, 1.60, -0.14, -2.38), (-0.16, -0.07, -0.24, -3.21), (-4.44, -0.90, 0.02, 0.14)],
          "E:FF5UC": [(1.91, 1.57, -0.11, -2.30), (-0.41, -0.22, -0.21, -2.67), (-2.37, -0.53, 0.24, 2.01)],
          "E:FF5UC+cmdty": [(1.19, 0.79, -0.09, -1.56), (-0.40, -0.22, -0.19, -2.55), (-1.90, -0.42, 0.20, 1.96)]}
for e, vals in claims.items():
    for p, (a, ta, h, th) in zip(("full_1970", "post2010", "holdout"), vals):
        r = sp("L5", p, e)
        c("Q2 spread", f"{e} {p} alpha %", 100 * r.alpha_ann, a, 2)
        c("Q2 spread", f"{e} {p} t alpha", r.t_alpha, ta, 2)
        c("Q2 spread", f"{e} {p} b_HML", r.b_HML, h, 2)
        c("Q2 spread", f"{e} {p} t_HML", r.t_HML, th, 2)
c("Q2 spread", "E:FF5UC+cmdty full n", sp("L5", "full_1970", "E:FF5UC+cmdty").n, 414, 0)
for p, (b, t) in zip(("full_1970", "post2010", "holdout"), ((-0.18, -8.70), (-0.12, -2.70), (-0.28, -3.57))):
    c("Q2 spread", f"COMEQ loading {p}", sp("L5", p, "E:FF5UC").b_COMEQ, b, 2)
    c("Q2 spread", f"COMEQ t {p}", sp("L5", p, "E:FF5UC").t_COMEQ, t, 2)
c("Q2 spread", "UMD holdout (FF5UC)", sp("L5", "holdout", "E:FF5UC").b_UMD, -0.38, 2)
c("Q2 spread", "UMD holdout t (FF5UC)", sp("L5", "holdout", "E:FF5UC").t_UMD, -6.76, 2)
c("Q2 spread", "UMD post2010 (FF5UC)", sp("L5", "post2010", "E:FF5UC").b_UMD, -0.14, 2)
c("Q2 spread", "UMD post2010 t (FF5UC)", sp("L5", "post2010", "E:FF5UC").t_UMD, -2.10, 2)
c("Q2 spread", "WTI t post2010", sp("L5", "post2010", "E:FF5UC+cmdty").t_WTI, -0.66, 2)
c("Q2 spread", "IMF t post2010", sp("L5", "post2010", "E:FF5UC+cmdty").t_IMF, 0.65, 2)
r = sp("L8H", "full_1970", "E:FF5UC")
c("Q2 spread", "8/8H FF5UC full alpha %", 100 * r.alpha_ann, 2.52, 2); c("Q2 spread", "8/8H FF5UC full t", r.t_alpha, 2.57, 2)
c("Q2 spread", "8/8H FF5UC full p", r.p_alpha, 0.010, 3)
r = sp("L8H", "full_1970", "E:FF5U")
c("Q2 spread", "8/8H FF5U full alpha %", 100 * r.alpha_ann, 2.91, 2); c("Q2 spread", "8/8H FF5U full t", r.t_alpha, 2.35, 2)
for p, (a, t) in (("post2010", (1.64, 1.11)), ("holdout", (0.88, 0.20))):
    r = sp("L8H", p, "E:FF5UC")
    c("Q2 spread", f"8/8H FF5UC {p} alpha %", 100 * r.alpha_ann, a, 2); c("Q2 spread", f"8/8H FF5UC {p} t", r.t_alpha, t, 2)
for l, p, a, t in (("L8H", "post2010", 1.09, 0.56), ("L8M", "post2010", 0.87, 0.41), ("L8H", "holdout", 1.21, 0.23), ("L8M", "holdout", -2.52, -0.44)):
    r = sp(l, p, "E:FF3")
    c("Q1 spread", f"{l} {p} FF3 alpha %", 100 * r.alpha_ann, a, 2); c("Q1 spread", f"{l} {p} FF3 t", r.t_alpha, t, 2)

# ---- Q1 team baseline table and comparison/bootstrap
Q1 = T("q1_table1")
q1 = lambda l, b, p, s: Q1[(Q1.legs == l) & (Q1.baseline == b) & (Q1.period == p) & (Q1.strategy == s)].iloc[0]  # noqa: E731
for l, p, s, a, t in (("L5", "validation", "Original 3m", 1.33, 1.47), ("L8H", "validation", "Original 3m", 0.90, 1.02),
                      ("L5", "validation", "Pure 6m", 2.51, 2.46), ("L8H", "validation", "Pure 6m", 2.60, 2.31),
                      ("L5", "holdout", "Original 3m", -4.03, -2.19), ("L8H", "holdout", "Original 3m", -4.02, -2.01),
                      ("L5", "holdout", "Pure 6m", -2.71, -1.94), ("L8H", "holdout", "Pure 6m", -2.16, -1.09)):
    r = q1(l, "team", p, s)
    c("Q1 team table", f"{l} {p} {s} alpha %", r.alpha_ff3_pct, a, 2); c("Q1 team table", f"{l} {p} {s} t", r.t_alpha, t, 2)
CMP = T("q1_comparison")
cm = lambda l, b, s: CMP[(CMP.legs == l) & (CMP.baseline == b) & (CMP.strategy == s)].iloc[0]  # noqa: E731
r = cm("L8H", "corr", "Pure | Short Brown hold 6m")
c("Q1 bootstrap", "8/8 corr Pure 6m net %", 100 * r.ann_return_full, 1.79, 2); c("Q1 bootstrap", "8/8 corr Pure 6m Sharpe", r.sharpe_full, 0.41, 2)
c("Q1 bootstrap", "8/8 corr Pure 6m boot p", r.bootstrap_p, 0.050, 3)
c("Q1 bootstrap", "8/8 team Continuous pure boot p", cm("L8H", "team", "Continuous | pure attention").bootstrap_p, 0.037, 3)
c("Q1 bootstrap", "8/8 Always-short boot p (corr)", cm("L8H", "corr", "Benchmark | Always-short Brown").bootstrap_p, 0.056, 3)
c("Q1 bootstrap", "8/8 Always-short boot p (team)", cm("L8H", "team", "Benchmark | Always-short Brown").bootstrap_p, 0.056, 3)
C2 = T("q2_comparison")
c("Q2 bootstrap", "min bootstrap p over L5 FF5UC strategies (both baselines, excl. B&H GB)",
  C2[~C2.strategy.str.contains("Buy-and-hold")].bootstrap_p.min(), 0.29, 2)

# ---- Q2 hedge cost / residual HML
HC = T("q2_hedge_cost_post2010")
hc = lambda b, h, s: HC[(HC.baseline == b) & (HC.hedge == h) & (HC.strategy == s)].iloc[0]  # noqa: E731
c("Q2 hedge cost", "Original 3m turnover FF3", hc("corr", "FF3", "Original 3m").ann_turnover, 4.80, 2)
c("Q2 hedge cost", "Original 3m turnover FF5UC", hc("corr", "FF5UC", "Original 3m").ann_turnover, 5.99, 2)
c("Q2 hedge cost", "Original 3m cost drag FF3 %", 100 * hc("corr", "FF3", "Original 3m").ann_cost_drag, 0.53, 2)
c("Q2 hedge cost", "Original 3m cost drag FF5UC %", 100 * hc("corr", "FF5UC", "Original 3m").ann_cost_drag, 0.85, 2)
c("Q2 hedge cost", "Always-short gross FF3 %", 100 * hc("corr", "FF3", "Always-short Brown").ann_gross, 1.15, 2)
c("Q2 hedge cost", "Always-short gross FF5UC %", 100 * hc("corr", "FF5UC", "Always-short Brown").ann_gross, 0.44, 2)
S7 = ["Original 3m", "Pure 3m", "Original 6m", "Pure 6m", "Continuous raw", "Continuous pure", "Always-short Brown"]
inc = pd.Series({s: hc("corr", "FF5UC", s).ann_overlay_turnover / hc("corr", "FF3", s).ann_overlay_turnover - 1 for s in S7})
c("Q2 hedge cost", "overlay turnover increase, signal rules, min %", 100 * inc.drop("Always-short Brown").min(), 35, 0)
c("Q2 hedge cost", "overlay turnover increase, signal rules, max %", 100 * inc.drop("Always-short Brown").max(), 54, 0)
c("Q2 hedge cost", "overlay turnover increase, always-short %", 100 * inc["Always-short Brown"], 163, 0)
tinc = pd.Series({s: hc("corr", "FF5UC", s).ann_turnover / hc("corr", "FF3", s).ann_turnover - 1 for s in S7})
c("Q2 hedge cost", "total turnover increase, signal rules, min %", 100 * tinc.drop("Always-short Brown").min(), 24, 0)
c("Q2 hedge cost", "total turnover increase, signal rules, max %", 100 * tinc.drop("Always-short Brown").max(), 37, 0)
c("Q2 hedge cost", "total turnover increase, always-short %", 100 * tinc["Always-short Brown"], 127, 0)
HCC = T("q2_hedge_cost_change")
hcc = HCC[HCC.baseline == "corr"].set_index("strategy")
c("Q2 hedge cost", "q2_hedge_cost_change total pct min (signal rules)", hcc.drop("Always-short Brown").total_turnover_change_pct.min(), 24, 0)
c("Q2 hedge cost", "q2_hedge_cost_change overlay pct max (signal rules)", hcc.drop("Always-short Brown").overlay_turnover_change_pct.max(), 54, 0)
c("Q2 hedge cost", "q2_hedge_cost_change always-short overlay pct", hcc.loc["Always-short Brown", "overlay_turnover_change_pct"], 163, 0)
f3 = pd.DataFrame([hc("corr", "FF3", s) for s in S7])
f5c = pd.DataFrame([hc("corr", "FF5UC", s) for s in S7])
c("Q2 residual HML", "FF3 hedge post2010 b_HML max (least negative)", f3.b_HML.max(), -0.015, 3)
c("Q2 residual HML", "FF3 hedge post2010 b_HML min", f3.b_HML.min(), -0.053, 3)
c("Q2 residual HML", "FF3 hedge post2010 t_HML max", f3.t_HML.max(), -1.19, 2)
c("Q2 residual HML", "FF3 hedge post2010 t_HML min", f3.t_HML.min(), -1.95, 2)
c("Q2 residual HML", "FF5UC hedge post2010 b_HML max", f5c.b_HML.max(), -0.024, 3)
c("Q2 residual HML", "FF5UC hedge post2010 b_HML min", f5c.b_HML.min(), -0.079, 3)
SG = T("strategy_grid")
g = lambda l, b, h, co, e, p: SG[(SG.legs == l) & (SG.baseline == b) & (SG.hedge == h) & (SG.costs == co) & (SG.eval_id == e) & (SG.period == p)]  # noqa: E731
x = g("L5", "corr", "FF5UC", "team", "E:FF5UC", "holdout")
c("Q2 residual HML", "FF5UC hedge holdout b_HML min", x.b_HML.min(), 0.039, 3)
c("Q2 residual HML", "FF5UC hedge holdout b_HML max", x.b_HML.max(), 0.148, 3)
c("Q2 residual HML", "FF5UC hedge holdout t_HML max", x.t_HML.max(), 2.24, 2)
for e, a, t in (("E:FF3", 1.42, 1.65), ("E:FF5UC", 1.35, 1.74), ("E:FF5UC+cmdty", 1.34, 1.75)):
    r = g("L5", "corr", "FF3", "team", e, "post2010").query("strat == 'Pure 6m'").iloc[0]
    c("Q2 eval only", f"FF3-hedged Pure 6m post2010 on {e} alpha %", 100 * r.alpha_ann, a, 2)
    c("Q2 eval only", f"FF3-hedged Pure 6m post2010 on {e} t", r.t_alpha, t, 2)
# robustness ranges
for lab, (l, b, h, e), rng in (("team baseline", ("L5", "team", "FF5UC", "E:FF5UC"), ((-0.56, 1.00), (-0.66, -3.61))),
                               ("8/8 legs", ("L8H", "corr", "FF5UC", "E:FF5UC"), ((-0.12, 0.61), (-0.34, -2.70))),
                               ("COMEQ ex-Gold", ("L5", "corr", "FF5UCx", "E:FF5UCx"), ((-0.58, 0.34), (-0.80, -3.55)))):
    for p, (lo, hi) in zip(("post2010", "holdout"), rng):
        x = g(l, b, h, "team", e, p)
        a = 100 * x.alpha_ann
        c("Q2 robustness", f"{lab} {p} alpha range end 1", a.min() if p == "post2010" else a.max(), lo, 2)
        c("Q2 robustness", f"{lab} {p} alpha range end 2", a.max() if p == "post2010" else a.min(), hi, 2)
c("Q2 robustness", "team baseline post2010 max t", g("L5", "team", "FF5UC", "team", "E:FF5UC", "post2010").t_alpha.max(), 1.40, 2)
c("Q2 robustness", "WTI/IMF eval post2010 max t", g("L5", "corr", "FF5UC", "team", "E:FF5UC+cmdty", "post2010").t_alpha.max(), 0.80, 2)

# ---- Q3
DEC = T("q3_hml_decomposition")
d_ = lambda l, m, p: DEC[(DEC.legs == l) & (DEC.model == m) & (DEC.period == p)]  # noqa: E731
for (m, p), (bs, gs, tot) in {("FF5U", "post2010"): (-0.316, 0.076, -0.240), ("FF3", "holdout"): (-0.518, 0.392, -0.126),
                              ("FF3", "full_1970"): (-0.419, 0.186, -0.233), ("FF3", "post2010"): (-0.437, 0.139, -0.298)}.items():
    x = d_("L5", m, p)
    c("Q3 decomposition", f"{m} {p} Brown side", x[x.side == "Brown"].contribution.sum(), bs, 3)
    c("Q3 decomposition", f"{m} {p} Green side", x[x.side == "Green"].contribution.sum(), gs, 3)
    c("Q3 decomposition", f"{m} {p} total", x.contribution.sum(), tot, 3)
x = d_("L5", "FF3", "post2010").set_index("industry").contribution
for nm, v in {"Steel": -0.135, "Ships": -0.105, "Aero": -0.089, "BldMt": -0.071, "Util": -0.038, "RlEst": 0.090, "Fin": 0.080,
              "Telcm": 0.054, "Drugs": -0.018, "Fun": -0.067}.items():
    c("Q3 decomposition", f"post2010 FF3 contribution {nm}", x[nm], v, 3)
c("Q3 decomposition", "Steel + Ships", x["Steel"] + x["Ships"], -0.239, 3)
IR = T("q3_industry_loadings")
ir = lambda nm, m, p: IR[(IR.industry == nm) & (IR.model == m) & (IR.period == p)].iloc[0]  # noqa: E731
for nm, (b, t) in {"Fun": (-0.34, -3.1), "RlEst": (0.45, 4.8), "Drugs": (-0.09, -1.0), "Telcm": (0.27, 4.0), "Fin": (0.40, 4.9),
                   "Util": (0.19, 2.7), "Ships": (0.52, 6.8), "Aero": (0.44, 3.6), "Steel": (0.67, 4.6), "BldMt": (0.36, 6.0)}.items():
    r = ir(nm, "FF3", "post2010")
    c("Q3 industry", f"{nm} post2010 FF3 b_HML", r.b_HML, b, 2); c("Q3 industry", f"{nm} post2010 FF3 t_HML", r.t_HML, t, 1)
fb = pd.DataFrame([ir(nm, "FF3", "full_1970") for nm in ["Util", "Ships", "Aero", "Steel", "BldMt"]])
c("Q3 industry", "full Brown b_HML min", fb.b_HML.min(), 0.32, 2); c("Q3 industry", "full Brown b_HML max", fb.b_HML.max(), 0.48, 2)
c("Q3 industry", "full Brown t_HML min > 3.8 (1=yes)", float(fb.t_HML.min() > 3.8), 1, 0)
for nm, v in {"RlEst": 0.70, "Fin": 0.29, "Drugs": -0.26}.items():
    c("Q3 industry", f"full {nm} b_HML", ir(nm, "FF3", "full_1970").b_HML, v, 2)
for nm, v in {"Telcm": 0.65, "RlEst": 0.54, "Drugs": 0.52, "Fin": 0.46}.items():
    c("Q3 industry", f"holdout {nm} b_HML", ir(nm, "FF3", "holdout").b_HML, v, 2)
x8 = d_("L8H", "FF3", "post2010")
c("Q3 8/8", "8/8 post2010 FF3 GB loading", x8.contribution.sum(), -0.35, 2)
c("Q3 8/8", "Autos contribution post2010", x8.set_index("industry").contribution["Autos"], -0.060, 3)
c("Q3 8/8", "Autos contribution holdout", d_("L8H", "FF3", "holdout").set_index("industry").contribution["Autos"], -0.219, 3)
RS = T("q3_rolling_summary")
rs = lambda m, e, s: RS[(RS.model == m) & (RS.era == e) & (RS.series == s)].iloc[0]  # noqa: E731
c("Q3 rolling", "GB share neg 1975-2026 %", 100 * rs("FF3", "1975-2026", "Green-Brown").share_negative, 78, 0)
c("Q3 rolling", "GB mean 1975-2026", rs("FF3", "1975-2026", "Green-Brown")["mean"], -0.19, 2)
c("Q3 rolling", "GB share neg 2010-2026 %", 100 * rs("FF3", "2010-2026", "Green-Brown").share_negative, 76, 0)
c("Q3 rolling", "GB share neg holdout %", 100 * rs("FF3", "2022-08-2026", "Green-Brown").share_negative, 100, 0)
c("Q3 rolling", "GB mean holdout", rs("FF3", "2022-08-2026", "Green-Brown")["mean"], -0.31, 2)
c("Q3 rolling", "GB max 1975-2026", rs("FF3", "1975-2026", "Green-Brown")["max"], 0.53, 2)
c("Q3 rolling", "Brown leg mean", rs("FF3", "1975-2026", "Brown leg")["mean"], 0.29, 2)
c("Q3 rolling", "Brown leg share neg %", 100 * rs("FF3", "1975-2026", "Brown leg").share_negative, 9, 0)
c("Q3 rolling", "Green leg mean", rs("FF3", "1975-2026", "Green leg")["mean"], 0.10, 2)
c("Q3 rolling", "FF5U GB share neg 1975-2026 %", 100 * rs("FF5U", "1975-2026", "Green-Brown").share_negative, 63, 0)
c("Q3 rolling", "FF5U GB share neg 2010-2026 %", 100 * rs("FF5U", "2010-2026", "Green-Brown").share_negative, 75, 0)
RH = T("q3_rolling_hml").set_index("date")["FF3|Green-Brown"]
PR = T("q3_rolling_positive_runs")
pr = PR[PR.model == "FF3"].sort_values("n_windows", ascending=False).reset_index(drop=True)
for i, (f_, l_, n_, pk_, pb_, bb_) in enumerate((("2008-02", "2013-10", 69, "2008-12", 0.53, -0.12), ("1983-12", "1987-03", 40, "1985-03", 0.25, -0.04))):
    r = pr.iloc[i]
    c("Q3 rolling", f"run {f_}..{l_} dates and peak month (1=yes)", float(r.first_window_end[:7] == f_ and r.last_window_end[:7] == l_ and r.peak_window_end[:7] == pk_), 1, 0)
    c("Q3 rolling", f"run {f_}..{l_} n windows", r.n_windows, n_, 0)
    c("Q3 rolling", f"run {f_}..{l_} peak", r.peak_gb_beta, pb_, 2)
    c("Q3 rolling", f"run {f_}..{l_} Brown leg beta at peak", r.brown_leg_beta_at_peak, bb_, 2)
c("Q3 rolling", "other FF3 runs max n windows", pr.iloc[2:].n_windows.max(), 9, 0)
c("Q3 rolling", "other FF3 runs max peak", pr.iloc[2:].peak_gb_beta.max(), 0.10, 2)
c("Q3 rolling", "GB 1975-2026 max beta equals 2008-12 peak", RH.loc["1975":].max(), 0.53, 2)
LK = T("q3_bm_link").set_index("series")
c("Q3 BE/ME", "GB share negative %", 100 * LK.loc["Green-Brown", "share_rel_logbm_negative"], 88.5, 1)
c("Q3 BE/ME", "GB mean rel log BE/ME", LK.loc["Green-Brown", "mean_rel_logbm"], -0.255, 3)
c("Q3 BE/ME", "cross-section mean Spearman", LK.iloc[-1]["corr"], 0.468, 3)
c("Q3 BE/ME", "cross-section t", LK.iloc[-1]["t_slope_nw4"], 10.5, 1)
c("Q3 BE/ME", "GB beta vs BE/ME corr", LK.loc["Green-Brown", "corr"], -0.08, 2)
c("Q3 BE/ME", "GB beta vs BE/ME t", LK.loc["Green-Brown", "t_slope_nw4"], -0.34, 2)

# ---- Q4
BE = T("q4_breakeven")
be = lambda b, h, s: BE[(BE.baseline == b) & (BE.hedge == h) & (BE.strategy == s)].iloc[0]  # noqa: E731
for s, v in zip(S7, (42, 40, 93, 100, 46, 47, 211)):
    c("Q4 break-even", f"corr FF3 {s} validation bp", be("corr", "FF3", s).validation_breakeven_bp, v, 0)
for s, v in zip(S7, (37, 37, 111, 108, 53, 53, 211)):
    c("Q4 break-even", f"team FF3 {s} validation bp", be("team", "FF3", s).validation_breakeven_bp, v, 0)
for s, v in zip(S7, (5.1, 5.8, 2.4, 2.5, 1.3, 1.5, 0.7)):
    c("Q4 turnover", f"corr FF3 {s} validation turnover", be("corr", "FF3", s).validation_ann_turnover, v, 1)
for b, lo, hi in (("corr", 19, 50), ("team", 16, 68)):
    v = pd.Series([be(b, "FF5UC", s).validation_breakeven_bp for s in S7])
    c("Q4 break-even", f"{b} FF5UC validation min bp", v.min(), lo, 0); c("Q4 break-even", f"{b} FF5UC validation max bp", v.max(), hi, 0)
v = pd.Series([be("corr", "FF3", s).post2010_breakeven_bp for s in S7], index=S7)
c("Q4 break-even", "corr FF3 post2010 min bp (signal rules)", v.drop("Always-short Brown").min(), 27, 0); c("Q4 break-even", "corr FF3 post2010 max bp (signal rules)", v.drop("Always-short Brown").max(), 60, 0)
c("Q4 break-even", "corr FF3 post2010 always-short bp", v["Always-short Brown"], 124, 0)
v = pd.Series([be("corr", "FF3", s).full_live_breakeven_bp for s in S7], index=S7)
c("Q4 break-even", "corr FF3 full_live min bp (signal rules)", v.drop("Always-short Brown").min(), 10, 0); c("Q4 break-even", "corr FF3 full_live max bp (signal rules)", v.drop("Always-short Brown").max(), 61, 0)
c("Q4 break-even", "corr FF3 full_live always-short bp", v["Always-short Brown"], 131, 0)
c("Q4 gross holdout", "corr FF3 Original 3m gross holdout alpha %", 100 * be("corr", "FF3", "Original 3m").holdout_gross_alpha, -1.67, 2)
c("Q4 gross holdout", "corr FF3 Always-short gross holdout alpha %", 100 * be("corr", "FF3", "Always-short Brown").holdout_gross_alpha, -1.65, 2)
c("Q4 gross holdout", "max gross holdout alpha over both baselines x {FF3, FF5UC} x 7 (<0)", BE.holdout_gross_alpha.max(), -0.0039, 4)
Q4 = T("q4_costs")
x = Q4[(Q4.baseline == "corr") & (Q4.hedge == "FF3") & (Q4.costs == "u5") & (Q4.period == "last18")]
c("Q4 last18", "corr FF3 u5 last18: all alphas negative (1=yes)", float((x.alpha_ann < 0).all()), 1, 0)
r = x[x.strategy == "Always-short Brown"].iloc[0]
c("Q4 last18", "Always-short last18 alpha %", 100 * r.alpha_ann, -6.19, 2); c("Q4 last18", "Always-short last18 t", r.t_alpha, -1.86, 2)
x = Q4[(Q4.baseline == "corr") & (Q4.hedge == "FF3") & (Q4.costs == "u5") & (Q4.period == "last12")].set_index("strategy")
c("Q4 last12", "Original 3m last12 alpha %", 100 * x.loc["Original 3m", "alpha_ann"], 1.15, 2)
c("Q4 last12", "Original 3m last12 t", x.loc["Original 3m", "t_alpha"], 0.28, 2)
c("Q4 last12", "Original 6m last12 alpha %", 100 * x.loc["Original 6m", "alpha_ann"], 1.51, 2)
c("Q4 last12", "Original 6m last12 t", x.loc["Original 6m", "t_alpha"], 0.28, 2)
for s_, s2 in (("Pure 3m", "Original 3m"), ("Pure 6m", "Original 6m")):
    c("Q4 last12", f"{s_} last12 alpha == {s2}", x.loc[s_, "alpha_ann"], x.loc[s2, "alpha_ann"], 12)
    c("Q4 last12", f"{s_} last12 t == {s2}", x.loc[s_, "t_alpha"], x.loc[s2, "t_alpha"], 12)
c("Q4 last12", "continuous rules and always-short negative (1=yes)", float((x.loc[["Continuous raw", "Continuous pure", "Always-short Brown"]].alpha_ann < 0).all()), 1, 0)

# ---- grid / key numbers / best case / ledger
KN = T("key_numbers").set_index("key")["value"]
c("grid", "n grid", float(KN["n_grid_alpha_family"]), 8091, 0)
c("grid", "positive p<0.05", float(KN["n_grid_positive_p_below_05"]), 368, 0)
c("grid", "negative p<0.05", float(KN["n_grid_negative_p_below_05"]), 531, 0)
c("grid", "min Holm", float(KN["min_grid_holm"]), 0.082, 3)
c("grid", "best positive p", float(KN["best_positive_grid_p"]), 0.00035, 5)
c("grid", "best positive BH", float(KN["best_positive_grid_bh"]), 0.062, 3)
c("grid", "best post2010/holdout positive p", float(KN["best_positive_post2010_or_holdout_p"]), 0.049, 3)
r = g("L5", "team", "FF5UC", "u5", "E:FF5UC", "post2010").query("strat == 'Original 6m'").iloc[0]
c("grid", "best post2010 Original 6m alpha %", 100 * r.alpha_ann, 1.36, 2); c("grid", "best post2010 Original 6m t", r.t_alpha, 1.98, 2)
L = T("tests_ledger")
c("ledger", "n tests", len(L), 13482, 0)
for k, v in {"primary": 46, "robustness": 5562, "exploratory": 7874}.items():
    c("ledger", f"n {k}", float((L.primary_or_exploratory == k).sum()), v, 0)
fam = L[(L.statistic_name == "t_alpha_NW6") & ~L.note.str.contains("gross zero-cost") & L.test_id.str.match(r"^(strat|spread)\|") & L.p_value_two_sided.notna()]
c("grid", "raw-spread alphas in family", float(fam.test_id.str.startswith("spread").sum()), 153, 0)
c("grid", "strategy alphas in family", float(fam.test_id.str.startswith("strat").sum()), 7938, 0)
c("grid", "key_numbers n_grid_strategy_alphas_net_of_cost", float(KN["n_grid_strategy_alphas_net_of_cost"]), 7938, 0)
c("grid", "key_numbers n_grid_raw_spread_alphas", float(KN["n_grid_raw_spread_alphas_unhedged_cost_free"]), 153, 0)
c("ledger", "comeq rows", float(L.test_id.str.startswith("comeq|").sum()), 42, 0)
SB = T("summary_best_case").set_index("strategy")
for s, (a, t) in {"Original 3m": (6.15, 4.36), "Pure 3m": (6.48, 4.33), "Original 6m": (4.41, 3.05), "Pure 6m": (4.27, 2.93),
                  "Continuous raw": (1.99, 3.48), "Continuous pure": (1.99, 3.46), "Always-short Brown": (3.87, 2.76)}.items():
    c("best case", f"{s} best any alpha %", 100 * SB.loc[s, "best_any_alpha_ann"], a, 2)
    c("best case", f"{s} best any t", SB.loc[s, "best_any_t"], t, 2)
    c("best case", f"{s} best any is COVID (1=yes)", float(SB.loc[s, "best_any_period"] == "covid"), 1, 0)
c("best case", "Always-short best holdout alpha %", 100 * SB.loc["Always-short Brown", "best_holdout_alpha_ann"], 0.42, 2)
# full-live start dates
x = SG[(SG.legs == "L5") & (SG.hedge == "FF3") & (SG.costs == "team") & (SG.period == "full_live") & (SG.eval_id == "E:FF3")]
for b, shift in (("team", 0), ("corr", 1)):
    for s, ym in {"Original 3m": "1993-01", "Always-short Brown": "1993-01", "Continuous raw": "1992-12", "Pure 3m": "1999-02",
                  "Continuous pure": "1999-01"}.items():
        st = pd.Timestamp(x[(x.baseline == b) & (x.strat == s)].window_start.iloc[0])
        exp = pd.Timestamp(ym + "-01") + pd.offsets.MonthEnd(1 + shift)
        c("full_live", f"{b} {s} start == {exp:%Y-%m} (1=yes)", float(st == exp), 1, 0)

# ============================================================================ ROUND 2 additions
# ---- Answer / census (key_numbers)
c("census", "holdout_net_regressions", float(KN["holdout_net_regressions"]), 1050, 0)
c("census", "holdout_net_positive", float(KN["holdout_net_positive"]), 24, 0)
c("census", "holdout_net_positive_signal_rules", float(KN["holdout_net_positive_signal_rules"]), 0, 0)
c("census", "holdout_net_max_alpha %", 100 * float(KN["holdout_net_max_alpha"]), 0.42, 2)
c("census", "holdout_net_max_alpha_t", float(KN["holdout_net_max_alpha_t"]), 0.22, 2)
c("census", "holdout_net_max_signal_rule_alpha %", 100 * float(KN["holdout_net_max_signal_rule_alpha"]), -0.03, 2)
c("census", "holdout_gross_regressions", float(KN["holdout_gross_regressions"]), 28, 0)
c("census", "holdout_gross_positive", float(KN["holdout_gross_positive"]), 0, 0)
c("census", "holdout_gross_max_alpha %", 100 * float(KN["holdout_gross_max_alpha"]), -0.39, 2)
c("census", "holdout_gross_max_alpha_t", float(KN["holdout_gross_max_alpha_t"]), -1.35, 2)
c("census", "gross max config is Continuous pure|L5|team|FF3 (1=yes)", float(KN["holdout_gross_max_alpha_config"].startswith("Continuous pure|L5|team|FF3|")), 1, 0)
c("census", "net max config is Always-short|L8H|team|FF5U|team|E:FF5UC+cmdty (1=yes)",
  float(KN["holdout_net_max_alpha_config"] == "Always-short Brown|L8H|team|FF5U|team|E:FF5UC+cmdty"), 1, 0)
c("census", "signal-rule max config is Continuous pure|L8H|team|FF3|team|E:FF5UC+cmdty (1=yes)",
  float(KN["holdout_net_max_signal_rule_config"] == "Continuous pure|L8H|team|FF3|team|E:FF5UC+cmdty"), 1, 0)
hsg = SG[(SG.period == "holdout") & (SG.costs != "u0")]
r = hsg[(hsg.strat == "Continuous pure") & (hsg.legs == "L8H") & (hsg.baseline == "team") & (hsg.hedge == "FF3") & (hsg.eval_id == "E:FF5UC+cmdty")].iloc[0]
c("census", "signal-rule max t", r.t_alpha, -0.08, 2)
c("census", "always-short 5/5 max holdout alpha %", 100 * hsg[(hsg.strat == "Always-short Brown") & (hsg.legs == "L5")].alpha_ann.max(), -0.91, 2)
c("census", "always-short 8/8 net rows", float(((hsg.strat == "Always-short Brown") & hsg.legs.isin(["L8H", "L8M"])).sum()), 92, 0)
c("census", "KN n_ledger_primary", float(KN["n_ledger_primary"]), 46, 0)
c("census", "KN n_ledger_robustness", float(KN["n_ledger_robustness"]), 5562, 0)
c("census", "KN n_ledger_exploratory", float(KN["n_ledger_exploratory"]), 7874, 0)
c("census", "KN n_pipeline_runs", float(KN["n_pipeline_runs"]), 46, 0)
c("census", "KN n_strategy_regressions", float(KN["n_strategy_regressions"]), 8050, 0)
c("grid", "BH negatives by period string", float(KN["grid_bh_negative_by_period"] == "last18:23; holdout:4"), 1, 0)
# ---- COMEQ justification (q2_comeq_justification.csv) and caption
J = T("q2_comeq_justification").set_index("series")
jc = J.loc["COMEQ (Oil, Coal, Mines, Gold)"]
for col, v in (("corr_WTI", 0.23), ("corr_WTI_lead", 0.40), ("corr_IMF", 0.33), ("corr_IMF_lead", 0.47), ("corr_brown", 0.66), ("corr_Mkt-RF", 0.55),
               ("ff5u_r2", 0.37), ("ff5u_t_alpha", -0.24), ("ff5u_p_alpha", 0.81)):
    c("COMEQ", f"COMEQ {col}", jc[col], v, 2)
c("COMEQ", "COMEQ ff5u alpha %", 100 * jc.ff5u_alpha_ann, -0.89, 2)
c("COMEQ", "corr n", jc.n, 413, 0); c("COMEQ", "ff5u n", jc.ff5u_n, 414, 0)
c("COMEQ", "corr end 2026-06 (1=yes)", float(str(jc.end).startswith("2026-06")), 1, 0)
c("COMEQ", "ff5u end 2026-07 (1=yes)", float(str(jc.ff5u_end).startswith("2026-07")), 1, 0)
jx = J.loc["COMEQ ex-Gold (Oil, Coal, Mines)"]
c("COMEQ", "COMEQx R2", jx.ff5u_r2, 0.45, 2); c("COMEQ", "COMEQx alpha %", 100 * jx.ff5u_alpha_ann, -1.42, 2); c("COMEQ", "COMEQx t", jx.ff5u_t_alpha, -0.35, 2)
c("COMEQ", "Gold corr WTI", J.loc["Gold industry", "corr_WTI"], 0.06, 2)
tex = (TABLES / f"{M}_q2_comeq_justification.tex").read_text()
c("COMEQ", "tex caption states 1992-02 to 2026-06, n = 413 and 2026-07, n = 414 (1=yes)",
  float("1992-02 to 2026-06, n = 413" in tex and "1992-02 to 2026-07, n = 414" in tex), 1, 0)
# ---- Q1 primary and corrected table, comparison CI, renamed flag
Q1P = T("q1_primary")
for p, (lo, hi, tlo, thi) in (("post2010", (0.17, 1.56, 0.56, 1.67)), ("holdout", (-2.51, -0.39, -1.81, -0.19))):
    x = Q1P[Q1P.period == p]
    c("Q1 primary", f"{p} alpha min %", 100 * x.alpha_ann.min(), lo, 2); c("Q1 primary", f"{p} alpha max %", 100 * x.alpha_ann.max(), hi, 2)
    c("Q1 primary", f"{p} t min", x.t_alpha.min(), tlo, 2); c("Q1 primary", f"{p} t max", x.t_alpha.max(), thi, 2)
c("Q1 primary", "post2010 all positive (1=yes)", float((Q1P[Q1P.period == "post2010"].alpha_ann > 0).all()), 1, 0)
c("Q1 primary", "min raw p", Q1P.p_alpha.min(), 0.077, 3)
c("Q1 primary", "min-p test negative (1=yes)", float(Q1P.loc[Q1P.p_alpha.idxmin(), "alpha_ann"] < 0), 1, 0)
c("Q1 primary", "min Holm p", Q1P.holm_p.min(), 1.00, 2)
r = cm("L8H", "corr", "Pure | Short Brown hold 6m")
c("Q1 bootstrap", "8/8 corr Pure 6m CI low", r.bootstrap_ci_low, 0.000, 3); c("Q1 bootstrap", "8/8 corr Pure 6m CI high", r.bootstrap_ci_high, 0.037, 3)
c("Q1 flags", "old column absent from q1/q2 comparison (1=yes)", float("significant_after_multiple_testing" not in CMP.columns and "significant_after_multiple_testing" not in C2.columns), 1, 0)
c("Q1 flags", "renamed active-months column present (1=yes)", float("team_active_months_full_nonzero_net" in CMP.columns and "team_active_months_full_nonzero_net" in C2.columns), 1, 0)
fl = CMP[CMP.team_holm_flag_normal_p.astype(str) == "True"]
c("Q1 flags", "True rows are exactly L5 team {Original 3m, Continuous raw} and L5 corr {Original 3m, Pure 3m} (1=yes)",
  float(set(zip(fl.legs, fl.baseline, fl.strategy)) == {("L5", "team", "Original | Short Brown hold 3m"), ("L5", "team", "Continuous | raw attention"),
                                                        ("L5", "corr", "Original | Short Brown hold 3m"), ("L5", "corr", "Pure | Short Brown hold 3m")}), 1, 0)
c("Q1 flags", "no True in q2_comparison", float((C2.team_holm_flag_normal_p.astype(str) == "True").sum()), 0, 0)
c("Q1 team anchors", "team 5/5 Pure 6m validation alpha", q1("L5", "team", "validation", "Pure 6m").alpha_ff3_pct, 2.51, 2)
c("Q1 team anchors", "team 5/5 Original 3m holdout t", q1("L5", "team", "holdout", "Original 3m").t_alpha, -2.19, 2)
v6 = Q1[(Q1.strategy.isin(["Original 6m", "Pure 6m"])) & (Q1.period == "validation")].alpha_ff3_pct
c("Implications", "6m rules validation FF3 alpha min (q1_table1)", v6.min(), 1.80, 2); c("Implications", "6m rules validation FF3 alpha max", v6.max(), 2.60, 2)
# ---- Q2 strategy table post2010 t (hedge = eval), Q2 primary counts, hedge-set holdout ranges
for s, (t3, t5) in {"Original 3m": (1.04, 0.39), "Pure 3m": (1.10, 0.08), "Original 6m": (1.36, 0.83), "Pure 6m": (1.65, 0.75),
                    "Continuous raw": (0.83, 0.34), "Continuous pure": (0.93, 0.29), "Always-short Brown": (0.67, -0.00)}.items():
    c("Q2 strategies", f"{s} FF3 post2010 t", g("L5", "corr", "FF3", "team", "E:FF3", "post2010").query("strat == @s").t_alpha.iloc[0], t3, 2)
    c("Q2 strategies", f"{s} FF5UC post2010 t", g("L5", "corr", "FF5UC", "team", "E:FF5UC", "post2010").query("strat == @s").t_alpha.iloc[0], t5, 2)
hs = pd.concat([g("L5", "corr", h, "team", f"E:{h}", "holdout") for h in ("FF3", "FF3U", "FF5U", "FF5UC")])
c("Q2 strategies", "holdout alpha max across 4 hedge sets %", 100 * hs.alpha_ann.max(), -0.58, 2)
c("Q2 strategies", "holdout alpha min across 4 hedge sets %", 100 * hs.alpha_ann.min(), -3.44, 2)
c("Q2 strategies", "holdout t max", hs.t_alpha.max(), -1.01, 2); c("Q2 strategies", "holdout t min", hs.t_alpha.min(), -2.27, 2)
Q2P = T("q2_primary")
x = Q2P[Q2P.period == "post2010"]
c("Q2 primary", "post2010 positive point estimates", float((x.alpha_ann > 0).sum()), 6, 0)
c("Q2 primary", "post2010 min %", 100 * x.alpha_ann.min(), -0.005, 3); c("Q2 primary", "post2010 max %", 100 * x.alpha_ann.max(), 0.59, 2)
c("Q2 primary", "post2010 max t", x.t_alpha.max(), 0.83, 2)
x = Q2P[Q2P.period == "holdout"]
c("Q2 primary", "holdout max %", 100 * x.alpha_ann.max(), -0.61, 2); c("Q2 primary", "holdout min %", 100 * x.alpha_ann.min(), -3.28, 2)
c("Q2 primary", "holdout t max", x.t_alpha.max(), -1.28, 2); c("Q2 primary", "holdout t min", x.t_alpha.min(), -2.27, 2)
c("Q2 primary", "min p", Q2P.p_alpha.min(), 0.028, 3); c("Q2 primary", "Holm of min p", Q2P.loc[Q2P.p_alpha.idxmin(), "holm_p"], 0.397, 3)
f3t = pd.DataFrame([hc("team", "FF3", s) for s in S7])
c("Q2 residual HML", "team FF3 hedge post2010 b_HML max (least negative)", f3t.b_HML.max(), -0.019, 3)
c("Q2 residual HML", "team FF3 hedge post2010 b_HML min", f3t.b_HML.min(), -0.061, 3)
c("Q2 residual HML", "team FF3 hedge post2010 t_HML max", f3t.t_HML.max(), -1.35, 2)
c("Q2 residual HML", "team FF3 hedge post2010 t_HML min", f3t.t_HML.min(), -2.36, 2)
c("Q2 residual HML", "FF5UC corr post2010 t_HML max", f5c.t_HML.max(), -0.78, 2)
c("Q2 residual HML", "FF5UC corr post2010 t_HML min", f5c.t_HML.min(), -1.69, 2)
# ---- Q3 BE/ME shares (text: 'above' = not below the median, from share_rel_logbm_negative)
for nm, side, v in (("Util", "above", 100), ("Steel", "above", 100), ("Ships", "above", 94), ("Drugs", "below", 98), ("Fun", "below", 69),
                    ("Fin", "above", 96), ("RlEst", "above", 87), ("Telcm", "above", 85)):
    sh = LK.loc[nm, "share_rel_logbm_negative"]
    c("Q3 BE/ME", f"{nm} {side} (1 - share negative if above) %", 100 * (1 - sh if side == "above" else sh), v, 0)
Q3P = T("q3_primary")
c("Q3 primary", "largest Holm p within 4", Q3P.holm_p_HML.max(), 0.017, 3)
# ---- Q4 table vs q4_costs.csv, Q4 primary
Q4TXT = {"Original 3m": ((1.92, 1.66, 0.89), (2.31, 2.02, 1.09), (-1.87, -2.08, -2.69)),
         "Pure 3m": ((2.05, 1.76, 0.89), (2.37, 2.06, 1.07), (-1.87, -2.08, -2.69)),
         "Original 6m": ((2.25, 2.12, 1.74), (2.36, 2.22, 1.80), (-1.70, -1.89, -2.47)),
         "Pure 6m": ((2.51, 2.37, 1.98), (2.80, 2.63, 2.13), (-1.70, -1.89, -2.47)),
         "Continuous raw": ((0.54, 0.47, 0.27), None, (-0.51, -0.56, -0.70)),
         "Continuous pure": ((0.60, 0.53, 0.31), None, (-0.52, -0.57, -0.72)),
         "Always-short Brown": ((1.47, 1.43, 1.33), (1.18, None, None), (-1.67, -1.70, -1.78))}
qc = Q4[(Q4.baseline == "corr") & (Q4.hedge == "FF3")]
for s, (va, vt, ha) in Q4TXT.items():
    for i, co in enumerate(("u5", "u10", "u25")):
        rv = qc[(qc.costs == co) & (qc.period == "validation") & (qc.strategy == s)].iloc[0]
        rh = qc[(qc.costs == co) & (qc.period == "holdout") & (qc.strategy == s)].iloc[0]
        c("Q4 table", f"{s} validation {co} alpha %", 100 * rv.alpha_ann, va[i], 2)
        if vt is not None and vt[i] is not None:
            c("Q4 table", f"{s} validation {co} t", rv.t_alpha, vt[i], 2)
        c("Q4 table", f"{s} holdout {co} alpha %", 100 * rh.alpha_ann, ha[i], 2)
Q4P = T("q4_primary")
c("Q4 primary", "best Holm p", Q4P.holm_p.min(), 0.838, 3)
bq = Q4P.loc[Q4P.holm_p.idxmin()]
c("Q4 primary", "best is Pure 6m post2010 (1=yes)", float(bq.strat == "Pure 6m" and bq.period == "post2010"), 1, 0)
c("Q4 primary", "raw p of best", bq.p_alpha, 0.060, 3)
c("Q4 primary", "holdout u5 max %", 100 * Q4P[Q4P.period == "holdout"].alpha_ann.max(), -0.51, 2)
# ---- best-case table
for s, (a, t, ho) in {"Original 3m": (1.08, 1.41, 0.397), "Pure 3m": (1.20, 1.50, 0.397), "Original 6m": (1.36, 1.98, 0.752),
                      "Pure 6m": (1.41, 1.98, 0.752), "Continuous raw": (0.32, 1.09, 1.0), "Continuous pure": (0.40, 1.56, 1.0),
                      "Always-short Brown": (1.29, 1.36, 1.0)}.items():
    c("best case", f"{s} best post2010 alpha %", 100 * SB.loc[s, "best_post2010_alpha_ann"], a, 2)
    c("best case", f"{s} best post2010 t", SB.loc[s, "best_post2010_t"], t, 2)
    c("best case", f"{s} Q2 post2010 Holm", SB.loc[s, "Q2_post2010_holm_p"], 1.0, 2)
    c("best case", f"{s} Q2 holdout Holm", SB.loc[s, "Q2_holdout_holm_p"], ho, 2)
    c("best case", f"{s} best any Holm grid", SB.loc[s, "best_any_holm_grid"], 1.0, 2)
gbs = SB.loc["Raw GB spread (unhedged)"]
c("best case", "raw GB best any %", 100 * gbs.best_any_alpha_ann, 2.52, 2); c("best case", "raw GB best any t", gbs.best_any_t, 2.57, 2)
c("best case", "raw GB best post2010 %", 100 * gbs.best_post2010_alpha_ann, 1.71, 2); c("best case", "raw GB best post2010 t", gbs.best_post2010_t, 1.17, 2)
c("best case", "raw GB best holdout %", 100 * gbs.best_holdout_alpha_ann, 1.55, 2); c("best case", "raw GB best holdout t", gbs.best_holdout_t, 0.33, 2)
c("best case", "Always-short best holdout t", SB.loc["Always-short Brown", "best_holdout_t"], 0.22, 2)
c("best case", "no row survives Holm (1=yes)", float((~SB.survives_holm_grid.astype(bool)).all()), 1, 0)

R = pd.DataFrame(rows)
R.to_csv(OUT / "verify_text_claims_r2.csv", index=False, float_format="%.8g")
print(f"{len(R)} text claims, {int(R.match.sum())} match, {int((~R.match).sum())} mismatch")
print(R[~R.match].to_string())
