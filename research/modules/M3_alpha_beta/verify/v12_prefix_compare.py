"""V12 (round 2): check M3's claim that the round-1 fixes only ADDED columns, tables and ledger rows: compare the
pre-fix snapshot (scratchpad m3_before, 06:29, taken after round-1 verification) with the current tables."""
import pathlib
import numpy as np
import pandas as pd
from vlib import TABLES, OUT

BEFORE = pathlib.Path("/tmp/claude-1000/-home-hashim-projects-GA/5d56c5f1-d319-48cb-b466-4daeaca6ed67/scratchpad/m3_before")
rows = []
for f in sorted(BEFORE.glob("M3_alpha_beta_*.csv")):
    old = pd.read_csv(f); new = pd.read_csv(TABLES / f.name)
    rec = {"table": f.name.replace("M3_alpha_beta_", ""), "rows_old": len(old), "rows_new": len(new),
           "cols_removed": sorted(set(old.columns) - set(new.columns)), "cols_added": len(set(new.columns) - set(old.columns))}
    if f.name.endswith("tests_ledger.csv") or f.name.endswith("key_numbers.csv"):
        key = old.columns[0]
        m = old.merge(new, on=key, how="left", suffixes=("_o", "_n"), indicator=True)
        rec["old_rows_missing"] = int((m["_merge"] != "both").sum())
        diffs = []
        for c in old.columns[1:]:
            a, b = m[f"{c}_o"], m[f"{c}_n"]
            if pd.api.types.is_numeric_dtype(a) and pd.api.types.is_numeric_dtype(b):
                diffs.append(float(np.nanmax(np.abs(a.to_numpy(float) - b.to_numpy(float))) if len(a) else 0.0))
                rec[f"nan_mismatch_{c}"] = int((a.isna() != b.isna()).sum()) or None
            else:
                ne = (a.fillna("").astype(str) != b.fillna("").astype(str))
                if ne.any():
                    rec[f"text_changed_{c}"] = int(ne.sum())
        rec["max_num_diff"] = max(diffs) if diffs else 0.0
    elif len(old) == len(new):
        common = [c for c in old.columns if c in new.columns]
        num = [c for c in common if pd.api.types.is_numeric_dtype(old[c]) and not pd.api.types.is_bool_dtype(old[c])]
        rec["max_num_diff"] = float((old[num].astype(float) - new[num].astype(float)).abs().max().max()) if num else 0.0
        txt = [c for c in common if c not in num]
        rec["text_equal"] = bool((old[txt].fillna("").astype(str) == new[txt].fillna("").astype(str)).all().all()) if txt else True
    else:
        # row-added table: match on all common text columns
        common = [c for c in old.columns if c in new.columns]
        txt = [c for c in common if not pd.api.types.is_numeric_dtype(old[c])]
        m = old.merge(new[common], on=txt, how="left", suffixes=("_o", "_n"), indicator=True)
        rec["old_rows_missing"] = int((m["_merge"] != "both").sum())
        num = [c for c in common if c not in txt]
        rec["max_num_diff"] = max(float((m[f"{c}_o"] - m[f"{c}_n"]).abs().max()) for c in num) if num else 0.0
    rows.append(rec)
R = pd.DataFrame(rows)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
print(R.to_string())
new_tables = sorted({p.name for p in TABLES.glob("M3_alpha_beta_*.csv")} - {p.name for p in BEFORE.glob("*.csv")})
print("tables added:", new_tables)
R.to_csv(OUT / "v12_prefix_compare.csv", index=False)
