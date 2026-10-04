"""Independent helpers for the adversarial verification of M3_alpha_beta.

Deliberately does NOT import modules/M3_alpha_beta/m3lib.py or run.py. Allowed imports: lib/common.py,
lib/team_pipeline.py and (for comparison only) M8's build_bond. Everything statistical is re-coded here.
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np
import pandas as pd
from scipy import stats

RESEARCH = pathlib.Path("/home/hashim/projects/GA/project/research")
sys.path.insert(0, str(RESEARCH / "lib"))
from common import load_team, load_ff5_mom, load_fred, TABLES  # noqa: E402

VDIR = pathlib.Path(__file__).resolve().parent
OUT = VDIR / "out"
OUT.mkdir(exist_ok=True)
M3DATA = VDIR.parent / "data"
END = "2026-07-31"
HOLD = ("2022-08-31", END)
POST10 = ("2010-01-31", END)
COVID = ("2020-01-31", "2021-12-31")
STRATS = ["Original | Short Brown hold 3m", "Pure | Short Brown hold 3m", "Original | Short Brown hold 6m",
          "Pure | Short Brown hold 6m", "Continuous | raw attention", "Continuous | pure attention"]
BENCH = "Benchmark | Always-short Brown"
SH = dict(zip(STRATS + [BENCH], ["Orig 3m", "Pure 3m", "Orig 6m", "Pure 6m", "Cont raw", "Cont pure", "AlwaysShort"]))


def m3_table(name: str) -> pd.DataFrame:
    """Read an M3 output table (reading outputs is allowed; importing M3 code is not)."""
    return pd.read_csv(TABLES / f"M3_alpha_beta_{name}.csv")


# ----------------------------------------------------------------------------- BOND, independent construction
def _par_price(c, y, n_periods, m=2):
    """Price per 100 of a bond with annual coupon rate c paying m times a year, n_periods remaining, at yield y (BEY)."""
    i = np.arange(1, n_periods + 1)
    v = (1 + y / m) ** (-i)
    return 100 * (c / m) * v.sum() + 100 * v[-1]


def dur_conv_numeric(y0: float, h: float = 1e-5):
    """Modified duration and convexity of a 10y semiannual par bond at y0, by central finite differences of price."""
    P0 = _par_price(y0, y0, 20)
    Pu, Pd = _par_price(y0, y0 + h, 20), _par_price(y0, y0 - h, 20)
    D = -(Pu - Pd) / (2 * h) / P0
    C = (Pu - 2 * P0 + Pd) / h ** 2 / P0
    return D, C


def exact_month_return(y0: float, y1: float) -> float:
    """Hold a 10y semiannual par bond (coupon y0) bought at 100 for one month, reprice at y1 with 119 months left.
    Dirty price with fractional first period (street convention: discount by (1+y/2)^(k - 1/6))."""
    frac = 1 / 6                                   # one month elapsed of a 6-month coupon period
    i = np.arange(1, 21)
    ex = i - frac                                  # periods from t to each remaining cash flow
    cf = np.full(20, 100 * y0 / 2); cf[-1] += 100
    dirty = (cf * (1 + y1 / 2) ** (-ex)).sum()
    return dirty / 100 - 1


def build_bond_independent(rf: pd.Series, source: str = "gs10") -> pd.DataFrame:
    if source == "gs10":
        y = load_fred("GS10") / 100
    else:
        s = pd.read_csv(M3DATA / "tsy_10y_eom.csv", parse_dates=["date"]).set_index("date")["y10_eom"].astype(float) / 100
        s.index = pd.DatetimeIndex(s.index) + pd.offsets.MonthEnd(0)
        y = s
    y0 = y.shift(1)
    rows = {}
    for t in y.index:
        a, b = y0.get(t), y.get(t)
        if pd.isna(a) or pd.isna(b):
            continue
        D, C = dur_conv_numeric(a)
        dy = b - a
        rows[t] = {"y": b, "y0": a, "D": D, "C": C, "ret": a / 12 - D * dy + 0.5 * C * dy * dy,
                   "ret_exact": exact_month_return(a, b)}
    out = pd.DataFrame(rows).T
    out["RF"] = rf.reindex(out.index)
    out["BOND"] = out["ret"] - out["RF"]
    return out


# ----------------------------------------------------------------------------- regression
def nw(y: pd.Series, X: pd.DataFrame | None = None, lags: int = 6) -> dict:
    """OLS + Bartlett HAC (no small-sample scaling). p from t(n-k) and N(0,1)."""
    X = pd.DataFrame(index=y.index) if X is None else X
    d = pd.concat([y.rename("_y"), X], axis=1, sort=True).dropna()
    names = ["const"] + list(X.columns)
    Z = np.column_stack([np.ones(len(d))] + [d[c].to_numpy(float) for c in X.columns])
    Y = d["_y"].to_numpy(float)
    n, k = Z.shape
    ZZi = np.linalg.inv(Z.T @ Z)
    b = ZZi @ Z.T @ Y
    e = Y - Z @ b
    g = Z * e[:, None]
    S = g.T @ g
    for L in range(1, lags + 1):
        w = 1 - L / (lags + 1)
        G = g[L:].T @ g[:-L]
        S += w * (G + G.T)
    V = ZZi @ S @ ZZi
    se = np.sqrt(np.diag(V))
    t = b / se
    return {"b": pd.Series(b, names), "t": pd.Series(t, names), "V": pd.DataFrame(V, names, names),
            "p": pd.Series(2 * stats.t.sf(np.abs(t), n - k), names), "pn": pd.Series(2 * stats.norm.sf(np.abs(t)), names),
            "n": n, "k": k, "e": pd.Series(e, d.index), "idx": d.index}


def wald_F(fit: dict, names: list[str]) -> tuple[float, float]:
    b = fit["b"][names].to_numpy(); V = fit["V"].loc[names, names].to_numpy()
    W = float(b @ np.linalg.solve(V, b)); q = len(names)
    return W / q, float(stats.f.sf(W / q, q, fit["n"] - fit["k"]))


def holm(p) -> np.ndarray:
    p = np.asarray(p, float); m = len(p); o = np.argsort(p)
    adj = np.empty(m); run = 0.0
    for r, i in enumerate(o):
        run = max(run, (m - r) * p[i]); adj[i] = min(1.0, run)
    return adj


def roll_backward(y: pd.Series, F: pd.DataFrame, window: int) -> pd.DataFrame:
    """Betas for month t from OLS on months t-window..t-1 only (predetermined). Loop written from scratch."""
    d = pd.concat([y.rename("_y"), F], axis=1, sort=True)
    out = pd.DataFrame(np.nan, index=d.index, columns=list(F.columns))
    for j in range(window, len(d)):
        w = d.iloc[j - window:j]
        if w.isna().any().any():
            continue
        Z = np.column_stack([np.ones(window), w[F.columns].to_numpy(float)])
        b = np.linalg.lstsq(Z, w["_y"].to_numpy(float), rcond=None)[0]
        out.iloc[j] = b[1:]
    return out


def ln_terms(r: pd.Series, B: pd.DataFrame, F: pd.DataFrame, a, e) -> dict:
    d = pd.concat([r.rename("r"), B.add_prefix("b_"), F], axis=1, sort=True).loc[a:e].dropna()
    cols = list(F.columns)
    Bm = d[["b_" + c for c in cols]].to_numpy(); Fm = d[cols].to_numpy(); R = d["r"].to_numpy()
    cov = ((Bm - Bm.mean(0)) * (Fm - Fm.mean(0))).mean(0)
    return {"n": len(d), "mean": 12 * R.mean(), "cond_alpha": 12 * (R - (Bm * Fm).sum(1)).mean(),
            "static": 12 * float(Bm.mean(0) @ Fm.mean(0)), "timing": 12 * cov.sum(),
            **{f"cov_{c}": 12 * cov[j] for j, c in enumerate(cols)}, "_R": R, "_B": Bm, "_F": Fm}


def cbb_idx(n: int, block: int, rng) -> np.ndarray:
    """Circular block bootstrap indices (own implementation)."""
    k = -(-n // block)
    s = rng.integers(0, n, k)
    return (s[:, None] + np.arange(block)[None, :]).reshape(-1)[:n] % n


def boot_timing(R, Bm, Fm, reps=5000, block=12, seed=20260926) -> dict:
    rng = np.random.default_rng(seed)
    n = len(R); draws = np.empty(reps)
    for i in range(reps):
        ix = cbb_idx(n, block, rng)
        b, f = Bm[ix], Fm[ix]
        draws[i] = 12 * ((b - b.mean(0)) * (f - f.mean(0))).mean(0).sum()
    return {"lo": np.quantile(draws, .025), "hi": np.quantile(draws, .975),
            "p": 2 * min((draws > 0).mean(), (draws < 0).mean())}


# ----------------------------------------------------------------------------- pipeline runs (team_pipeline allowed)
def pipelines():
    from team_pipeline import run_pipeline, team_controls
    team = run_pipeline(bootstrap_reps=0, extras=False, paired=False, macro_states=False)
    mac = load_team()["macro"].copy()
    mac["cpi"] = mac["cpi"].interpolate(limit_area="inside")
    corr = run_pipeline(macro=mac, attention=mac["attention"].shift(1), controls=team_controls(mac).shift(1),
                        bootstrap_reps=0, extras=False, paired=False, macro_states=False)
    return team, corr


def factor_panel(bond: pd.Series) -> pd.DataFrame:
    T = load_team()
    ff3 = T["ff3"][["Mkt-RF", "SMB", "HML", "RF"]]
    k = load_ff5_mom()[["Mkt-RF", "SMB", "HML", "RMW", "CMA", "UMD"]].add_suffix("_k")
    F = ff3.join(k, how="left").join(bond.rename("BOND"), how="left")
    F["UMD"] = F["UMD_k"]
    return F.loc[:END]


FF3 = ["Mkt-RF", "SMB", "HML"]
FF3UB = ["Mkt-RF", "SMB", "HML", "UMD", "BOND"]
FF5UB = ["Mkt-RF_k", "SMB_k", "HML_k", "RMW_k", "CMA_k", "UMD", "BOND"]
