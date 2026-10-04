"""Check that the numbers written in the M2 FINDINGS text match the module's own CSV outputs (after a fresh rerun).

Reads only outputs/tables/M2_christhian_tests_*.csv; does not import the module code. Each claim is compared with a
tolerance of half a unit in the last printed digit (plus 1e-9). Writes verify/verify_text_claims.csv.
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
c("Q2 spread", "IMF t post2010", sp("L5", "post2010", "E:FF5UC+cmdty").t_IMF, 0.66, 2)
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
c("Q2 hedge cost", "overlay turnover increase, signal rules, min %", 100 * inc.drop("Always-short Brown").min(), 24, 0)
c("Q2 hedge cost", "overlay turnover increase, signal rules, max %", 100 * inc.drop("Always-short Brown").max(), 37, 0)
c("Q2 hedge cost", "overlay turnover increase, always-short %", 100 * inc["Always-short Brown"], 127, 0)
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
c("Q3 decomposition", "Steel + Ships", x["Steel"] + x["Ships"], -0.240, 3)
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
c("Q3 rolling", "year of GB beta peak in 2009-2013 (1=yes)", float(2009 <= pd.Timestamp(RH.loc["1975":].idxmax()).year <= 2013), 1, 0)
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
v = pd.Series([be("corr", "FF3", s).post2010_breakeven_bp for s in S7])
c("Q4 break-even", "corr FF3 post2010 min bp", v.min(), 27, 0); c("Q4 break-even", "corr FF3 post2010 max bp", v.max(), 60, 0)
v = pd.Series([be("corr", "FF3", s).full_live_breakeven_bp for s in S7])
c("Q4 break-even", "corr FF3 full_live min bp", v.min(), 10, 0); c("Q4 break-even", "corr FF3 full_live max bp", v.max(), 61, 0)
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
c("Q4 last12", "others negative (1=yes)", float((x.drop(["Original 3m", "Original 6m"]).alpha_ann < 0).all()), 1, 0)

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
c("ledger", "n tests", len(L), 13452, 0)
for k, v in {"primary": 46, "robustness": 5562, "exploratory": 7844}.items():
    c("ledger", f"n {k}", float((L.primary_or_exploratory == k).sum()), v, 0)
fam = L[(L.statistic_name == "t_alpha_NW6") & ~L.note.str.contains("gross zero-cost") & L.test_id.str.match(r"^(strat|spread)\|") & L.p_value_two_sided.notna()]
c("grid", "spread (cost-free, unhedged) tests inside the 'net-of-cost' family", float(fam.test_id.str.startswith("spread").sum()), 0, 0)
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

R = pd.DataFrame(rows)
R.to_csv(OUT / "verify_text_claims.csv", index=False, float_format="%.8g")
print(f"{len(R)} text claims, {int(R.match.sum())} match, {int((~R.match).sum())} mismatch")
print(R[~R.match].to_string())
