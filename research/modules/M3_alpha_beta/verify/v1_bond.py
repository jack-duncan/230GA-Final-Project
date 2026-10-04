"""V1: BOND construction, independent of M3 code (own finite-difference duration/convexity and own exact repricing).
Compared against M8.build_bond (allowed) and against M3's published bond_monthly / bond_validation_summary tables."""
import importlib.util
import numpy as np
import pandas as pd
from vlib import build_bond_independent, load_team, m3_table, OUT, RESEARCH, M3DATA, END

rf = load_team()["ff3"]["RF"]
b = build_bond_independent(rf, "gs10")
res = {}

# --- 1. vs M8 build_bond (allowed import) and vs M3's published table
spec = importlib.util.spec_from_file_location("m8", RESEARCH / "modules/M8_frozen_pre2010/run.py")
m8 = importlib.util.module_from_spec(spec); spec.loader.exec_module(m8)
from common import load_fred  # noqa: E402
m8b = m8.build_bond(load_fred("GS10"), rf)
res["max|mine - M8 ret_total|"] = float((b["ret"] - m8b["ret_total"].reindex(b.index)).abs().max())
res["max|mine - M8 D_mod|"] = float((b["D"] - m8b["D_mod"].reindex(b.index)).abs().max())
res["max|mine - M8 ret_exact|"] = float((b["ret_exact"] - m8b["ret_exact"].reindex(b.index)).abs().max())
pub = m3_table("bond_monthly").set_index("date")
pub.index = pd.to_datetime(pub.index)
res["max|mine BOND - M3 published BOND| 1970-2026"] = float((b["BOND"] - pub["BOND"]).loc["1970":END].abs().max())

# --- 2. timing: BOND_t uses y_{t-1} (duration, carry) and y_t; RF_t same month
chk = b.loc["2022-06-30"]
res["2022-06 y0 (should be GS10 May-2022 = 2.90%)"] = chk["y0"]
res["2022-06 y (should be GS10 Jun-2022 = 3.14%)"] = chk["y"]

# --- 3. validation numbers quoted in FINDINGS
b70 = b.loc["1970-01-31":END]
x = b70["BOND"]
res["1970-2026 excess mean ann (claim 2.16%)"] = 12 * x.mean()
res["1970-2026 vol ann (claim 6.95%)"] = np.sqrt(12) * x.std()
res["Sharpe (claim 0.31)"] = np.sqrt(12) * x.mean() / x.std()
res["AR1 (claim 0.31)"] = x.autocorr()
res["mean D (claim 7.56)"] = b70["D"].mean(); res["min D (5.04)"] = b70["D"].min(); res["max D (9.68)"] = b70["D"].max()
res["max |approx - exact| bp (claim 5.4)"] = 1e4 * (b70["ret"] - b70["ret_exact"]).abs().max()
res["corr approx vs exact (claim 0.99999)"] = b70["ret"].corr(b70["ret_exact"])
res["holdout mean excess ann (claim -3.68%)"] = 12 * b["BOND"].loc["2022-08-31":END].mean()
res["2022-2024 mean excess ann (claim -8.37%)"] = 12 * b["BOND"].loc["2022-01-31":"2024-12-31"].mean()
yr = b.loc["1954-01-31":"2025-12-31"]
ann = (1 + yr["ret"]).groupby(yr.index.year).prod() - 1
res["2022 total (claim -15.0%)"] = ann.loc[2022]
res["worst year since 1954 (claim 2022)"] = int(ann.idxmin())
res["second worst year"] = int(ann.nsmallest(2).index[-1]); res["second worst value"] = ann.nsmallest(2).iloc[-1]
d = pd.read_excel(M3DATA / "histretSP.xls", "T. Bond yield & return", header=None).iloc[7:, :3].dropna()
d.columns = ["year", "y", "ret"]; d = d[pd.to_numeric(d["year"], errors="coerce").notna()]
dam = pd.Series(d["ret"].astype(float).to_numpy(), index=d["year"].astype(int).to_numpy())
c = pd.concat([ann.rename("bond"), dam.rename("dam")], axis=1).dropna()
res["n years Damodaran overlap (claim 72)"] = len(c)
res["corr annual vs Damodaran 1954-2025 (claim 0.991)"] = c.corr().iloc[0, 1]
res["corr 1993-2025 (claim 0.987)"] = c.loc[1993:2025].corr().iloc[0, 1]
res["mean abs diff pp (claim 0.85)"] = 100 * (c.bond - c.dam).abs().mean()
res["Damodaran 2022 (claim -17.8%)"] = dam.loc[2022]; res["Damodaran worst year"] = int(c.dam.idxmin())

# --- 4. month-end version
be = build_bond_independent(rf, "eom")
res["BOND_eom AR1 (claim 0.08)"] = be["BOND"].loc["1990":END].autocorr()
res["BOND_eom holdout mean ann"] = 12 * be["BOND"].loc["2022-08-31":END].mean()
res["corr BOND vs BOND_eom monthly 1990-2026"] = pd.concat([b["BOND"], be["BOND"]], axis=1).loc["1990":END].corr().iloc[0, 1]
res["corr BOND_t vs BOND_eom_{t-1}"] = b["BOND"].loc["1990":END].corr(be["BOND"].shift(1).loc["1990":END])

s = pd.Series(res, name="value")
s.to_csv(OUT / "v1_bond.csv")
b.to_csv(OUT / "v1_bond_monthly_independent.csv")
be.to_csv(OUT / "v1_bond_eom_independent.csv")
print(s.to_string())
