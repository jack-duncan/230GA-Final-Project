"""V8: tests-ledger completeness. Counts, primary Holm notes, and whether each inferential number quoted in FINDINGS
has a ledger row."""
import pandas as pd
from vlib import m3_table, OUT

L = m3_table("tests_ledger")
print("rows:", len(L), "| by kind:", L.primary_or_exploratory.value_counts().to_dict())
P = L[L.primary_or_exploratory == "primary"]
print("primary rows:", len(P), "| with Holm note:", int(P.note.str.contains("Holm-adjusted").sum()))
print("duplicate test_ids:", int(L.test_id.duplicated().sum()), "| NaN p:", int(L.p_value_two_sided.isna().sum()))
print(P.groupby(P.test_id.str.split(".").str[0] + "." + P.test_id.str.split(".").str[1]).size().to_string())

checks = {
    "COVID 24m structural leakage p 0.006 / residual p 0.72 (Sec 6)": r"^Q5\.attr_(leak|residual)\..*24",
    "COVID in-period regression residual t 0.24 (Sec 6)": r"^Q5\..*inperiod|^Q5\..*regression",
    "D = strategy - pi x benchmark: mean / COVID D / in-window alpha of D / holdout D (Sec 4 iii, 6, 7)": r"^Q3b\.ln_(meanD|alphaD|D_)|vs_benchmark.*(mean|alpha)",
    "D timing term (Sec 4 iii)": r"^Q3b\.ln_timing_vs_benchmark\.",
    "hedged Brown holdout alpha FF3 / FF3+UMD+BOND (Sec 4 ii)": r"^Q1\.alpha\.Brown leg FF3-hedged\|legs\|FF3(\+UMD\+BOND)?\|holdout$",
    "FS COVID / holdout dummy alphas (Sec 5, 6)": r"^Q3a\.fs_(covid|holdout)_alpha\.",
    "FS bootstrap joint test (Sec 5)": r"^Q3a\.fs_boot_wald_c\.",
    "macro-state corrected / BOND-control diffs (Sec 4 ii)": r"^Q2c\.state_diff\.",
    "GB FF3 HML loading t -4.63 / -5.74 (Sec 4 i)": r"^Q1\.hml|HML loading",
    "COVID FF5+UMD+BOND UMD t 4.49 / BOND t 2.29 (Sec 6)": r"^Q1\.bond\.Pure 6m\|corrected\|FF5\+UMD\+BOND\|covid$",
    "BOND-hedged rerun holdout means (Sec 4 ii table)": r"^Q2b\.hedged_mean\..*holdout",
    "timing tests (Sec 5), expect 1,080": r"^Q4\.",
}
rows = []
for k, pat in checks.items():
    m = L.test_id.str.contains(pat, regex=True) | L.statistic_name.str.contains(pat, regex=True)
    rows.append({"claim": k, "ledger_rows": int(m.sum())})
R = pd.DataFrame(rows)
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 120)
print(R.to_string())
R.to_csv(OUT / "v8_ledger.csv", index=False)
