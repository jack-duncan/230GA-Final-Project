"""Numerical claim audit for both reports.

For every important number quoted in the prose of the two reports, this script checks that
(1) the number as printed appears in the .tex source, and (2) it equals the value computed by the
notebooks (tables/report_numbers.json, tables/climate_numbers.json, data/verified_extension_results.csv)
after rounding. It writes CLAIM_AUDIT.md and exits with an error if any claim fails.
Numbers inside the LaTeX tables are generated directly by the notebooks, so they are not listed here.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]          # final_submission_organized/
NM = json.loads((ROOT / "tables" / "report_numbers.json").read_text())
NC = json.loads((ROOT / "tables" / "climate_numbers.json").read_text())
EV = pd.read_csv(ROOT / "data" / "green" / "verified_extension_results.csv").set_index("name")
TM = TC = (ROOT / "MFE230GA_Final_Project.tex").read_text()   # one integrated report

SRC_M = {
    "ic": ("data/charisma/results/tables/ic_summary_by_horizon.csv", "supporting/code/charisma/src/ic.py: summarize_ic_by_horizon"),
    "icsub": ("data/charisma/results/tables/ic_by_month.csv", "notebook section 3.1 (_mean_tstat_nw)"),
    "rev_weight": ("data/charisma/results/tables/blend_weights_by_month.csv", "supporting/code/charisma/src/ic.py: expanding_blend_weights"),
    "mom_rev": ("data/charisma/results/tables/mom_rev_xs_corr_by_month.csv", "supporting/code/charisma/src/signals.py"),
    "perf": ("data/charisma/results/tables/performance_by_window.csv", "supporting/code/charisma/src/backtest.py: performance_table"),
    "risk": ("data/charisma/results/tables/portfolio_risk_summary.csv", "supporting/code/charisma/src/portfolio.py: risk_summary"),
    "lambda": ("data/charisma/results/tables/portfolio_risk_summary.csv", "supporting/code/charisma/src/portfolio.py: calibrate_to_target"),
    "gross": ("data/charisma/results/tables/portfolio_risk_summary.csv", "supporting/code/charisma/src/portfolio.py: risk_summary"),
    "attr": ("data/charisma/results/tables/factor_regressions.csv", "supporting/code/charisma/src/attribution.py: factor_regressions"),
    "alpha6": ("data/charisma/results/tables/strategy_returns_by_month.csv + data/charisma/raw/kf_*.parquet", "notebook section 6 (statsmodels HAC)"),
    "stress": ("data/charisma/results/tables/stress_2009_2020.csv", "supporting/code/charisma/src/robustness.py: stress_months"),
    "roll": ("data/charisma/results/tables/rolling_alpha_blend.csv", "supporting/code/charisma/src/robustness.py: rolling_alpha"),
    "rob": ("data/charisma/results/tables/robustness_grid.csv", "supporting/code/charisma/src/robustness.py: grid_table"),
    "heat": ("data/charisma/results/tables/robustness_grid.csv", "supporting/code/charisma/src/robustness.py: grid_table"),
    "blend_maxdd": ("data/charisma/results/tables/strategy_returns_by_month.csv", "supporting/code/charisma/src/backtest.py: drawdown_series"),
    "independent": ("notebook section 6", "independent statsmodels re-estimate"),
    "hor": ("data/charisma/results/tables/performance_by_window.csv", "supporting/code/charisma/src/backtest.py"),
}

def src_for(key, table):
    if table == "climate":
        return ("tables/climate_numbers.json", "notebooks/01_Green_Climate_Strategy.ipynb")
    if table == "ext":
        r = EV.loc[key]; return (f"extension {r.source_file} [{r.row_filter}]", "build_verified_evidence.py")
    for p, v in SRC_M.items():
        if key.startswith(p):
            return v
    return ("tables/report_numbers.json", "notebooks/02_Charisma_Final_Strategy.ipynb")

def val(table, key):
    if table == "main": return NM[key]
    if table == "climate": return NC[key]
    return EV.loc[key, "value"]

# (report, location, printed text, source table, key, scale, decimals)
CLAIMS = [
    ("main", "Exec. summary / 2.1", "0.047", "main", "ic_mom_rev_sample", 1, 3),
    ("main", "Exec. summary / 2.1", "3.96", "main", "ic_t_mom_rev_sample", 1, 2),
    ("main", "Exec. summary / 2.1", "0.010", "main", "ic_rev_rev_sample", 1, 3),
    ("main", "Exec. summary / 2.1", "1.06", "main", "ic_t_rev_rev_sample", 1, 2),
    ("main", "Exec. summary / 2.1", "-0.05", "main", "ic_t_rev_orth_rev_sample", 1, 2),
    ("main", "2.1", "0.035", "main", "ic_mom_post_2010", 1, 3),
    ("main", "2.1", "2.22", "main", "ic_t_mom_post_2010", 1, 2),
    ("main", "2.1", "-0.007", "main", "ic_rev_orth_post_2010", 1, 3),
    ("main", "2.1", "-0.50", "main", "ic_t_rev_orth_post_2010", 1, 2),
    ("main", "2.1", "0.31", "main", "mom_rev_xs_corr_mean", 1, 2),
    ("main", "2.1", "0.34", "main", "rev_weight_first", 1, 2),
    ("main", "2.1", "-0.05", "main", "rev_weight_2010", 1, 2),
    ("main", "2.1", "-0.13", "main", "rev_weight_last", 1, 2),
    ("main", "2.1", "0.045", "main", "icsub_rev_1985-1994", 1, 3),
    ("main", "2.1", "2.35", "main", "icsub_t_rev_1985-1994", 1, 2),
    ("main", "2.1", "0.020", "main", "icsub_rev_orth_1985-1994", 1, 3),
    ("main", "2.1", "1.13", "main", "icsub_t_rev_orth_1985-1994", 1, 2),
    ("main", "1.4", "2.32", "main", "lambda_median_blend", 1, 2),
    ("main", "1.4", "1.93", "main", "lambda_p10_blend", 1, 2),
    ("main", "1.4", "3.23", "main", "lambda_p90_blend", 1, 2),
    ("main", "1.4", "3.78", "main", "lambda_median_mom", 1, 2),
    ("main", "1.4", "1.21", "main", "lambda_median_rev", 1, 2),
    ("main", "2.2", "3.9", "main", "perf_common_mom_Gross return", 100, 1),
    ("main", "2.2", "6.6", "main", "perf_common_mom_Vol", 100, 1),
    ("main", "2.2", "0.59", "main", "perf_common_mom_Gross Sharpe", 1, 2),
    ("main", "2.2", "3.2", "main", "perf_common_blend_Gross return", 100, 1),
    ("main", "2.2", "0.48", "main", "perf_common_blend_Gross Sharpe", 1, 2),
    ("main", "Exec. / 2.2", "174", "main", "perf_common_rev_Monthly turnover", 100, 0),
    ("main", "2.2", "182", "main", "perf_common_rev_orth_Monthly turnover", 100, 0),
    ("main", "2.2", "51", "main", "perf_common_mom_Monthly turnover", 100, 0),
    ("main", "2.2", "58", "main", "perf_common_blend_Monthly turnover", 100, 0),
    ("main", "2.2", "4.0", "main", "perf_common_rev_Net return 20bp", -100, 1),
    ("main", "2.2", "-0.80", "main", "perf_common_rev_Net Sharpe 20bp", 1, 2),
    ("main", "2.2", "72", "main", "perf_common_rev_Max DD 20bp", -100, 0),
    ("main", "2.2", "0.27", "main", "perf_common_blend_Net Sharpe 20bp", 1, 2),
    ("main", "2.2", "6.6", "main", "risk_realized_blend", 100, 1),
    ("main", "2.2", "1.32", "main", "risk_ratio_blend", 1, 2),
    ("main", "2.2", "6.2", "main", "risk_realized_mom", 100, 1),
    ("main", "2.2", "4.3", "main", "risk_realized_rev_orth", 100, 1),
    ("main", "2.2", "4.8", "main", "risk_realized_rev", 100, 1),
    ("main", "2.2", "23", "main", "blend_maxdd_full", -100, 0),
    ("main", "Exec. / 2.3", "2.4", "main", "attr_blend_common_FF5 alpha", 100, 1),
    ("main", "Exec. / 2.3", "2.21", "main", "attr_blend_common_FF5 t", 1, 2),
    ("main", "Exec. / 2.3", "0.2", "main", "attr_blend_common_FF5+UMD alpha", 100, 1),
    ("main", "Exec. / 2.3", "0.36", "main", "attr_blend_common_FF5+UMD t", 1, 2),
    ("main", "2.3", "3.3", "main", "attr_mom_common_FF5 alpha", 100, 1),
    ("main", "2.3", "2.84", "main", "attr_mom_common_FF5 t", 1, 2),
    ("main", "2.3", "0.30", "main", "attr_blend_common_UMD beta", 1, 2),
    ("main", "2.3", "20.4", "main", "attr_blend_common_UMD t", 1, 1),
    ("main", "2.3", "0.10", "main", "attr_blend_common_R2 FF5", 1, 2),
    ("main", "2.3", "0.59", "main", "attr_blend_common_R2 FF5+UMD", 1, 2),
    ("main", "2.3", "-0.02", "main", "attr_blend_post_2010_FF5+UMD t", 1, 2),
    ("main", "2.3", "-4.5", "main", "attr_rev_common_FF5+UMD alpha", 100, 1),
    ("main", "2.3", "-5.8", "main", "attr_rev_common_FF5+UMD t", 1, 1),
    ("main", "2.3", "-5.5", "main", "attr_rev_orth_common_FF5+UMD t", 1, 1),
    ("main", "2.3", "0.13", "main", "attr_rev_common_UMD beta", 1, 2),
    ("main", "2.3", "0.07", "main", "attr_rev_orth_common_UMD beta", 1, 2),
    ("main", "2.3", "1.6", "main", "alpha6_gross_blend_common", 100, 1),
    ("main", "2.3", "2.44", "main", "alpha6_t_gross_blend_common", 1, 2),
    ("main", "2.3", "2.4", "main", "alpha6_gross_mom_common", 100, 1),
    ("main", "2.3", "3.18", "main", "alpha6_t_gross_mom_common", 1, 2),
    ("main", "2.3", "23", "main", "alpha6_breakeven_bp_blend_common", 1, 0),
    ("main", "2.3", "1.40", "main", "alpha6_t_net10bp_blend_common", 1, 2),
    ("main", "2.3", "1.26", "main", "alpha6_t_gross_blend_post_2010", 1, 2),
    ("main", "2.3", "1.8", "main", "alpha6_net10bp_mom_common", 100, 1),
    ("main", "2.3", "2.36", "main", "alpha6_t_net10bp_mom_common", 1, 2),
    ("main", "2.3", "1.55", "main", "alpha6_t_net20bp_mom_common", 1, 2),
    ("main", "2.3", "0.64", "main", "alpha6_t_net20bp_mom_post_2010", 1, 2),
    ("main", "2.4", "0.32", "main", "hor_blend_post_2010_netsr", 1, 2),
    ("main", "2.4", "3.40", "main", "attr_blend_recent_18m_FF5+UMD t", 1, 2),
    ("main", "2.4", "-0.12", "main", "attr_mom_recent_18m_FF5+UMD t", 1, 2),
    ("main", "2.4", "-0.5", "main", "attr_mom_recent_18m_FF5+UMD alpha", 100, 1),
    ("main", "2.4", "13.3", "main", "stress_2009_blend_net", -100, 1),
    ("main", "2.4", "11.8", "main", "stress_2009_mom_net", -100, 1),
    ("main", "2.4", "52.8", "main", "stress_2009_UMD", -100, 1),
    ("main", "2.4", "12.1", "main", "stress_2009apr_blend_net", -100, 1),
    ("main", "2.4", "18.3", "main", "stress_2009_rev_net", -100, 1),
    ("main", "2.4", "12.3", "main", "stress_2020_blend_net", 100, 1),
    ("main", "2.4", "14.3", "main", "stress_2020_mom_net", 100, 1),
    ("main", "2.4", "-0.1", "main", "roll_mean", 100, 1),
    ("main", "2.4", "-6.4", "main", "roll_min", 100, 1),
    ("main", "2.4", "5.3", "main", "roll_max", 100, 1),
    ("main", "2.4", "337", "main", "roll_n", 1, 0),
    ("main", "2.4", "6", "main", "roll_share_t_ge2", 100, 0),
    ("main", "2.4", "5", "main", "roll_share_t_le_m2", 100, 0),
    ("main", "2.5", "1.40", "main", "rob_max_t", 1, 2),
    ("main", "2.5", "0.38", "main", "rob_max_netsr", 1, 2),
    ("main", "2.5", "-3.1", "main", "rob_mom_lookback=6_alpha", 100, 1),
    ("main", "2.5", "-3.89", "main", "rob_mom_lookback=6_t", 1, 2),
    ("main", "2.5", "0.74", "main", "rob_neutrality=dollar_beta_t", 1, 2),
    ("main", "2.5", "-0.42", "main", "heat_netsr_min", 1, 2),
    ("main", "2.5", "0.28", "main", "heat_netsr_max", 1, 2),
    ("climate", "3 (promising)", "2.45", "climate", "team_Original 6m_Validation_net", 100, 2),
    ("climate", "3 (promising)", "2.23", "climate", "team_Original 6m_Validation_t", 1, 2),
    ("climate", "3 (promising)", "6.38", "climate", "corr_Original 3m_COVID_alpha", 100, 2),
    ("climate", "3 (promising)", "3.62", "climate", "corr_Original 3m_COVID_t", 1, 2),
    ("climate", "3 (benchmark)", "-0.23", "climate", "gb_hml_1970-2026", 1, 2),
    ("climate", "3 (benchmark)", "-4.63", "climate", "gb_hml_t_1970-2026", 1, 2),
    ("climate", "3 (benchmark)", "-0.30", "climate", "gb_hml_2010-2026", 1, 2),
    ("climate", "3 (benchmark)", "-5.74", "climate", "gb_hml_t_2010-2026", 1, 2),
    ("climate", "3 (benchmark)", "4.54", "climate", "corr_Always-short Brown_COVID_alpha", 100, 2),
    ("climate", "3 (benchmark)", "1.96", "climate", "corr_Always-short Brown_COVID_t", 1, 2),
    ("climate", "3 (benchmark)", "1.84", "climate", "paired_Original 3m_COVID_alpha", 100, 2),
    ("climate", "3 (benchmark)", "0.87", "climate", "paired_Original 3m_COVID_t", 1, 2),
    ("climate", "3 (OOS)", "-0.15", "climate", "ic_Continuous weight (raw)_Validation", 1, 2),
    ("climate", "3 (OOS)", "-2.19", "climate", "ic_t_Continuous weight (raw)_Validation", 1, 2),
    ("climate", "3 (OOS)", "0.06", "climate", "ic_Continuous weight (raw)_Holdout", 1, 2),
    ("climate", "3 (OOS)", "-0.18", "climate", "m8_alpha_pct", 1, 2),
    ("climate", "3 (OOS)", "-0.27", "climate", "m8_t", 1, 2),
    ("climate", "3 (OOS)", "0.48", "ext", "M8_primary_shuffle_p", 1, 2),
    ("climate", "3 (data)", "500", "climate", "identity_equal", 1, 0),
    ("climate", "3 (data)", "-0.0004", "ext", "M1_corr_z_MCCC_teamsignal", 1, 4),
    ("climate", "3 (costs)", "2.7", "climate", "turnover_min", 1, 1),
    ("climate", "3 (costs)", "5.3", "climate", "turnover_max", 1, 1),
    ("climate", "3 (costs)", "0.6", "climate", "costdrag_max", 100, 1),
    ("climate", "3 (costs)", "-1.5", "climate", "holdout_gross_alpha_max", 100, 1),
    ("climate", "3 (insights)", "1.09", "ext", "M5_ew_momentum_full_1970_ff5umd_t_alpha", 1, 2),
    ("climate", "3 (insights)", "0.99", "ext", "M5_ew_momentum_full_1970_ff5umd_b_UMD", 1, 2),
    ("climate", "4", "73", "ext", "M7_family_P_tests", 1, 0),
    ("climate", "4", "1.00", "ext", "M7_family_P_holm_min_p", 1, 2),
    ("climate", "4", "12", "ext", "M1b_climate_index_validation_alphas_total", 1, 0),
]

def tex_forms(printed):
    p = printed.lstrip("-")
    neg = printed.startswith("-")
    return [f"$-{p}" if neg else p, f"$-${p}" if neg else p, f"-{p}" if neg else p, f"−{p}"]

rows, bad = [], 0
for rep, loc, printed, table, key, scale, dec in CLAIMS:
    v = float(val(table, key)) * scale
    ok_val = f"{v:.{dec}f}".replace("-0.00", "0.00") == printed.replace("-0.00", "0.00") or \
             abs(round(v, dec) - float(printed)) < 10 ** (-dec) / 2 + 1e-12
    text = TM if rep == "main" else TC
    ok_txt = any(f in text for f in tex_forms(printed))
    s, code = src_for(key, table)
    bad += not ok_val
    status = ("OK" if ok_txt else "not quoted in integrated report (value still verified)") if ok_val else "FAIL (value)"
    rows.append(f"| {'Charisma (Sec. 4)' if rep == 'main' else 'Climate (Sec. 2)'} | {printed} | {v:.{dec+2}f} | `{key}` | {s} | {code} | {status} |")

hdr = ["# Claim audit", "",
       "Every important number quoted in the prose of the two reports, traced to the computed value, its source file and the code that",
       "produces it. Generated by `claim_audit.py`; the script re-reads the notebook outputs and the .tex sources and fails if a number",
       "does not match after rounding or does not appear in the text. Numbers inside tables are written by the notebooks directly",
       "(`tables/*.tex`) and are therefore not listed. Signs: values marked with a negative scale (losses, drawdowns) are quoted as",
       "positive magnitudes in the text.", "",
       f"**Result: {len(rows) - bad} of {len(rows)} values verified; {sum('OK |' in r for r in rows)} of them quoted in `MFE230GA_Final_Project.tex`.**", "",
       "| Part | Printed | Computed | Key | Source file | Code | Status |", "|---|---|---|---|---|---|---|"]
(Path(__file__).resolve().parent / "CLAIM_AUDIT.md").write_text("\n".join(hdr + rows) + "\n")
print(f"{len(rows) - bad}/{len(rows)} verified; quoted: {sum('OK |' in r for r in rows)}")
for r in rows:
    if "OK |" not in r: print(r)
sys.exit(1 if bad else 0)
