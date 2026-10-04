"""Compare the post-verification rerun of M8 with the 03:41 outputs saved in corrections/pre_correction_0341/.
Run: cd /home/hashim/projects/GA/project/research && uv run python modules/M8_frozen_pre2010/corrections/compare_rerun.py
Writes corrections/rerun_comparison.csv: one row per file, with byte identity, shared-column max abs diff, and added columns.
"""
import hashlib
import pathlib

import numpy as np
import pandas as pd

R = pathlib.Path("/home/hashim/projects/GA/project/research")
OLD = R / "modules/M8_frozen_pre2010/corrections/pre_correction_0341/tables"
NEW = R / "outputs/tables"
rows = []
for f in sorted(OLD.glob("M8_*")):
    g = NEW / f.name
    same_bytes = hashlib.sha256(f.read_bytes()).digest() == hashlib.sha256(g.read_bytes()).digest()
    row = {"file": f.name, "byte_identical": same_bytes, "shared_numeric_maxdiff": np.nan, "shared_text_cells_changed": np.nan,
           "columns_added": "", "columns_removed": "", "rows_old": np.nan, "rows_new": np.nan}
    if f.suffix == ".csv":
        a, b = pd.read_csv(f), pd.read_csv(g)
        row.update(rows_old=len(a), rows_new=len(b), columns_added=";".join(c for c in b.columns if c not in a.columns),
                   columns_removed=";".join(c for c in a.columns if c not in b.columns))
        shared = [c for c in a.columns if c in b.columns]
        if len(a) == len(b):
            num = [c for c in shared if pd.api.types.is_numeric_dtype(a[c]) and pd.api.types.is_numeric_dtype(b[c])]
            txt = [c for c in shared if c not in num]
            d = (a[num].astype(float) - b[num].astype(float)).abs().to_numpy()
            row["shared_numeric_maxdiff"] = float(np.nanmax(d)) if d.size else 0.0
            ch = [(c, i) for c in txt for i in range(len(a)) if str(a[c].iloc[i]) != str(b[c].iloc[i])]
            row["shared_text_cells_changed"] = len(ch)
            row["text_columns_changed"] = ";".join(sorted({c for c, _ in ch}))
    rows.append(row)
out = pd.DataFrame(rows)
out.to_csv(R / "modules/M8_frozen_pre2010/corrections/rerun_comparison.csv", index=False)
print(out.to_string(index=False))
