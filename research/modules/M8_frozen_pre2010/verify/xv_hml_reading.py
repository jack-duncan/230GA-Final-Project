"""Checks the FINDINGS reading of the HML / I x HML pair and computes the one-sided upper p that C21 asks to report.
Run: cd /home/hashim/projects/GA/project/research && uv run python modules/M8_frozen_pre2010/verify/xv_hml_reading.py
"""
import runpy, numpy as np
G = runpy.run_path("modules/M8_frozen_pre2010/verify/xv_independent.py", run_name="xv")
aP, fac, win, nw = G["aP"], G["fac"], G["win"], G["nw"]
cols = ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "UMD", "BOND", "WTI", "dVIX", "dlogEMV"]
X = fac.loc[win, cols].to_numpy(); I = aP["I"].astype(bool); D = aP["D"]; pi = aP["pi"]
h = cols.index("HML") + 1
for lab, m in (("D out-of-position", ~I), ("D in-position", I)):
    b, se, _ = nw(D[m], X[m], 6); print(f"{lab:20s} n={m.sum()} HML {b[h]:+.3f} (t {b[h]/se[h]:.2f})")
# simple one-factor view: HML only
for lab, m in (("D out (HML only)", ~I), ("D in (HML only)", I), ("AO out (HML only)", ~I), ("AO in (HML only)", I)):
    y = D[m] if lab.startswith("D") else aP["netA"][m]
    b, se, _ = nw(y, X[m][:, [2]], 6); print(f"{lab:20s} HML {b[1]:+.3f} (t {b[1]/se[1]:.2f})")
print("mean HML (ann) out vs in:", round(12*X[~I,2].mean(),4), round(12*X[I,2].mean(),4))
from scipy import stats
for lab, a in (("primary", aP), ("secondary", G["aS"])):
    print(lab, "one-sided upper p from t(n-k):", round(stats.t.sf(a["t"], a["df"]), 4))
