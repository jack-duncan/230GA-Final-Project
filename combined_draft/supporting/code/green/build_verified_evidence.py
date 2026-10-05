"""Extract the extension's verified results into one small provenance table.

The research extension (230GA-Final-Project-hashim-research-extension/research) ran nine
analysis modules (M1-M8 plus a replication). Each module's headline numbers were computed by its
own code and again by an independent re-implementation (see each module's VERIFY.md). Rerunning
all of them needs ~70 MB of raw downloads (EPA, Census, MCCC, FRED) and several hours, so the
summary notebook does not rerun them. Instead this script copies the specific numbers the Climate
note quotes, with the exact source file, row filter and column, into
data/verified_extension_results.csv. The notebook reads that file.

Usage (needs a copy of the extension repository; output goes to data/green/):
    python build_verified_evidence.py --ext <path>/230GA-Final-Project-hashim-research-extension/research
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

ROWS = []


def take(tables: Path, name: str, file: str, query: dict, col: str, note: str = ""):
    df = pd.read_csv(tables / file)
    sel = df
    for k, v in query.items():
        sel = sel[sel[k].astype(str) == str(v)]
    if len(sel) != 1:
        raise ValueError(f"{name}: {len(sel)} rows match {query} in {file}")
    ROWS.append({"name": name, "value": sel.iloc[0][col], "source_file": f"outputs/tables/{file}",
                 "row_filter": "; ".join(f"{k}={v}" for k, v in query.items()), "column": col, "note": note})


def main(ext: Path) -> None:
    t = ext / "outputs" / "tables"
    kn = "M1_signal_audit_key_numbers.csv"
    for n in ["identity_overlap_months", "identity_months_not_equal", "zeros_pre_2021-10", "zeros_post_2021-10",
              "R2_teamz_on_z_VIX_and_z_EMV_overall_full"]:
        take(t, f"M1_{n}", kn, {"name": n}, "value", "signal audit")
    mc = "M1_signal_audit_measure_correlations.csv"
    take(t, "M1_corr_z_MCCC_teamsignal", mc, {"measure": "MCCC", "transform": "z", "reference": "EMV_env", "sample": "overlap"},
         "pearson", "z-score correlation, 2005-12 to 2025-06")
    take(t, "M1_corr_z_CPU_teamsignal", mc, {"measure": "CPU", "transform": "z", "reference": "EMV_env", "sample": "overlap"},
         "pearson", "z-score correlation, 1990-03 to 2025-09")
    m1b = pd.read_csv(t / "M1b_alt_signals_primary.csv")
    v = m1b[(m1b.kind == "FF3 alpha") & (m1b.period == "validation") & m1b.measure.isin(["MCCC", "CPU"])]
    ROWS.append({"name": "M1b_climate_index_validation_alphas_total", "value": len(v),
                 "source_file": "outputs/tables/M1b_alt_signals_primary.csv",
                 "row_filter": "kind=FF3 alpha; period=validation; measure in (MCCC, CPU)", "column": "count", "note": ""})
    ROWS.append({"name": "M1b_climate_index_validation_alphas_t_ge_1.96", "value": int((v.t >= 1.96).sum()),
                 "source_file": "outputs/tables/M1b_alt_signals_primary.csv",
                 "row_filter": "same rows, t >= 1.96", "column": "t", "note": ""})
    pb = "M8_passbar.csv"
    for comp, short in [("(i) timing alpha, NW(6)", "timing_alpha"), ("(ii) calendar shuffle", "shuffle"),
                        ("(iv) drop-one Brown industry", "drop_one")]:
        take(t, f"M8_primary_{short}_statistic", pb, {"signal": "Frozen EMV-share rule (primary)", "component": comp}, "statistic")
        take(t, f"M8_primary_{short}_pass", pb, {"signal": "Frozen EMV-share rule (primary)", "component": comp}, "pass")
    take(t, "M8_primary_shuffle_p", pb, {"signal": "Frozen EMV-share rule (primary)", "component": "(ii) calendar shuffle"}, "p_value")
    take(t, "M8_primary_verdict_pass", pb, {"signal": "Frozen EMV-share rule (primary)", "component": "VERDICT"}, "pass")
    take(t, "M8_team_lagged_timing_alpha_statistic", pb, {"signal": "Team EMV_env level, lagged 1m (secondary)", "component": "(i) timing alpha, NW(6)"}, "statistic")
    take(t, "M8_window", "M8_strategy_summary.csv", {"signal": "Frozen EMV-share rule (primary)"}, "window")
    take(t, "M4_epa_gb_post2010_ff5umd_alpha", "M4_emissions_primary_test.csv", {"n": 199}, "alpha_ann")
    take(t, "M4_epa_gb_post2010_ff5umd_t", "M4_emissions_primary_test.csv", {"n": 199}, "t_alpha")
    m5 = "M5_industry_momentum_alphas.csv"
    for per in ["full_1970", "post2010"]:
        for c in ["alpha_ann", "t_alpha", "b_UMD"]:
            take(t, f"M5_ew_momentum_{per}_ff5umd_{c}", m5, {"series": "net", "period": per, "model": "FF5+UMD"}, c)
    fz = pd.read_csv(t / "M7_frozen_pre1970.csv").set_index("item")["value"]
    for k in ["alpha", "t", "first_month", "last_month", "verdict"]:
        ROWS.append({"name": f"M7_optimizer_frozen_1931_1969_{k}", "value": fz[k], "source_file": "outputs/tables/M7_frozen_pre1970.csv",
                     "row_filter": f"item={k}", "column": "value", "note": "optimized industry-momentum book, hash-frozen"})
    take(t, "M7_optimizer_evidence_against", "M7_verdict_table.csv", {"Candidate": "Optimizer book (X_unc)"}, "Evidence against")
    take(t, "M7_family_P_tests", "M7_multiple_testing_summary.csv", {"Family": "P (module primary alphas)", "Method": "Holm, one-sided"}, "Tests")
    take(t, "M7_family_P_holm_min_p", "M7_multiple_testing_summary.csv", {"Family": "P (module primary alphas)", "Method": "Holm, one-sided"}, "Smallest adjusted p")
    out = Path(__file__).resolve().parents[3] / "data" / "green" / "verified_extension_results.csv"
    pd.DataFrame(ROWS).to_csv(out, index=False)
    print(pd.DataFrame(ROWS)[["name", "value"]].to_string(index=False))
    print("wrote", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--ext", type=Path, required=True, help="path to the extension's research/ folder")
    main(ap.parse_args().ext)
