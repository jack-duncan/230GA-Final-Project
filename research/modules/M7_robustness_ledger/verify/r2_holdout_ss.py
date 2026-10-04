"""Round-2 verification: small-sample sensitivity of the check 6 holdout readings (not part of the spec).

The spec fixes NW(6) without small-sample scaling on 48 months with k = 7. NW standard errors are biased down in
short samples, so this script re-reads each series with (a) classic OLS standard errors, (b) NW(6) scaled by
n/(n-k), and (c) NW(3), and reports whether the "rejects a worthwhile alpha" readings survive.

Run: cd /home/hashim/projects/GA/project/research && uv run python modules/M7_robustness_ledger/verify/r2_holdout_ss.py
"""
from __future__ import annotations

import pathlib
import sys
import warnings

import numpy as np
import pandas as pd
from scipy.stats import t as tdist

warnings.filterwarnings("ignore")
ROOT = pathlib.Path(__file__).resolve().parents[3]
T = ROOT / "outputs" / "tables"
OUT = pathlib.Path(__file__).resolve().parent / "out_r2"
sys.path.insert(0, str(ROOT / "lib"))
import common as C  # noqa: E402
from team_pipeline import run_pipeline  # noqa: E402

X6 = C.load_ff5_mom()[["Mkt-RF", "SMB", "HML", "RMW", "CMA", "UMD"]]
TP = run_pipeline(bootstrap_reps=0)
ser = {k: v["net_return"] for k, v in TP["strategies"].items() if not k.startswith("Benchmark")}
ser["Always-short Brown"] = TP["strategies"]["Benchmark | Always-short Brown"]["net_return"]
opt = pd.read_csv(T / "M5_industry_momentum_optimizer_returns_monthly.csv", index_col=0, parse_dates=True)
gb = pd.read_csv(T / "M4_emissions_gb_monthly_returns.csv", index_col=0, parse_dates=True)
ser["optimizer book"] = opt["X_unc"]; ser["EPA 5v5"] = gb["epa5"]


def se_alpha(X, e, kind, lags=6):
    n, k = X.shape
    XtXi = np.linalg.inv(X.T @ X)
    if kind == "ols":
        return np.sqrt(XtXi[0, 0] * (e @ e) / (n - k))
    u = X * e[:, None]; S = u.T @ u
    for L in range(1, lags + 1):
        G = u[L:].T @ u[:-L]; S += (1 - L / (lags + 1)) * (G + G.T)
    V = XtXi @ S @ XtXi
    if kind == "nw_scaled":
        V *= n / (n - k)
    return np.sqrt(V[0, 0])


rows = []
for nm, s in ser.items():
    y = s.loc["2022-08-31":"2026-07-31"]
    X = np.column_stack([np.ones(len(y)), X6.loc[y.index].values])
    b = np.linalg.lstsq(X, y.values, rcond=None)[0]; e = y.values - X @ b
    n, k = X.shape; tc = tdist.ppf(0.95, n - k)
    delta = 0.25 * np.sqrt(12) * np.sqrt(e @ e / (n - k))
    row = {"series": nm, "alpha_%": 1200 * b[0], "delta_%": 100 * delta}
    for kind, lg in (("nw", 6), ("ols", 0), ("nw_scaled", 6), ("nw3", 3)):
        se = se_alpha(X, e, "nw" if kind == "nw3" else kind, lags=lg if kind != "ols" else 6)
        U = 12 * (b[0] + tc * se)
        row[f"U_{kind}_%"] = 100 * U
        row[f"read_{kind}"] = "rejects" if U < delta and 12 * (b[0] - tc * se) <= 0 else ("inconclusive" if U >= delta else "other")
    rows.append(row)
df = pd.DataFrame(rows)
with pd.option_context("display.width", 250, "display.max_columns", 20, "display.float_format", "{:.2f}".format):
    print(df.to_string(index=False))
df.to_csv(OUT / "r2_holdout_small_sample.csv", index=False)
