"""Walk-forward Grinold-Kahn mean-variance industry momentum book with a net carbon-exposure constraint.

At each formation month-end t (information through t only):
  z_i      = cross-sectional z-score of the 11-1 momentum signal over eligible industries
  sigma_i  = std of residuals from an OLS of industry excess return on Mkt-RF, trailing 60 months t-59..t
  alpha_i  = IC * sigma_i * z_i, IC = 0.05 (monthly units)
  V        = Ledoit-Wolf shrunk covariance of trailing 60-month industry excess returns
  c_i      = cross-sectional z-score of log emissions intensity over eligible industries (static intensities)
  maximize alpha'h - kappa * sum|h - h_drift|   (kappa = 10 bp per unit traded)
  s.t.     h'Vh <= (0.05^2)/12,  sum h = 0,  |h_i| <= 0.10,  c'h <= b
The risk constraint is the Lagrangian form of alpha'h - lambda h'Vh with lambda chosen each month so that the
ex-ante tracking volatility is 5% a year; writing it as a constraint keeps the box and carbon limits exact
(post-hoc rescaling of h would break them). Eligible: 60 complete months of returns, a momentum signal, and a
return in t+1. If c'h <= b is infeasible under the other constraints, the month falls back to the minimum-carbon
book (minimize c'h under the same constraints) and is counted.
"""
from __future__ import annotations
import warnings
import numpy as np
import pandas as pd
import cvxpy as cp
warnings.filterwarnings("ignore", message="Solution may be inaccurate")
from sklearn.covariance import LedoitWolf

IC = 0.05
TE_ANN = 0.05
BOX = 0.10
WINDOW = 60


def precompute(R: pd.DataFrame, ff5: pd.DataFrame, sig: pd.DataFrame, universe: list, ci: pd.Series, dates) -> dict:
    """Per-month optimizer inputs over a fixed universe (ineligible names get zero bounds)."""
    Ru = R[universe]; Rx = Ru.sub(ff5["RF"], axis=0); mkt = ff5["Mkt-RF"]
    pos = {d: i for i, d in enumerate(R.index)}
    logc = np.log(ci.reindex(universe))
    n = len(universe); out = []
    for t in dates:
        i = pos[t]
        win = Rx.iloc[i - WINDOW + 1:i + 1]
        elig = win.notna().all() & sig.loc[t, universe].notna() & Ru.iloc[i + 1].notna() & logc.notna()
        cols = list(elig[elig].index); m = np.array([universe.index(c) for c in cols])
        X = win[cols].values; mk = mkt.reindex(win.index).values
        A = np.column_stack([np.ones(WINDOW), mk])
        res = X - A @ np.linalg.lstsq(A, X, rcond=None)[0]
        sres = res.std(axis=0, ddof=2)
        s = sig.loc[t, cols].values; z = (s - s.mean()) / s.std(ddof=1)
        lc = logc[cols].values; cz = (lc - lc.mean()) / lc.std(ddof=1)
        V = LedoitWolf().fit(X).covariance_
        L = np.linalg.cholesky(V)
        a = np.zeros(n); a[m] = IC * sres * z
        c = np.zeros(n); c[m] = cz
        u = np.zeros(n); u[m] = BOX
        Lt = np.zeros((n, n)); Lt[np.ix_(m, m)] = L.T
        out.append({"t": t, "alpha": a, "cz": c, "u": u, "Lt": Lt, "n_elig": len(cols), "z": dict(zip(cols, z))})
    return {"universe": universe, "months": out}


class GKProblem:
    def __init__(self, n: int, kappa: float):
        self.h = cp.Variable(n)
        self.a, self.hp, self.cz = cp.Parameter(n), cp.Parameter(n), cp.Parameter(n)
        self.u = cp.Parameter(n, nonneg=True); self.Lt = cp.Parameter((n, n)); self.b = cp.Parameter()
        te2 = TE_ANN ** 2 / 12
        base = [cp.sum_squares(self.Lt @ self.h) <= te2, cp.sum(self.h) == 0, self.h <= self.u, self.h >= -self.u]
        self.main = cp.Problem(cp.Maximize(self.a @ self.h - kappa * cp.norm1(self.h - self.hp)),
                               base + [self.cz @ self.h <= self.b])
        self.mincarb = cp.Problem(cp.Minimize(self.cz @ self.h), base)
        assert self.main.is_dcp(dpp=True) and self.mincarb.is_dcp(dpp=True)

    def solve(self, mon: dict, hp: np.ndarray, b: float):
        self.a.value, self.cz.value, self.u.value, self.Lt.value = mon["alpha"], mon["cz"], mon["u"], mon["Lt"]
        self.hp.value = hp; self.b.value = b
        fallback = False
        try:
            self.main.solve(solver=cp.CLARABEL)
            ok = self.main.status in ("optimal", "optimal_inaccurate")
            status = self.main.status
        except cp.SolverError:
            ok, status = False, "solver_error"
        if not ok:
            fallback = True
            self.mincarb.solve(solver=cp.CLARABEL)
            status = "fallback_" + str(self.mincarb.status)
        self.last_status = status
        h = np.array(self.h.value, dtype=float)
        h[mon["u"] == 0] = 0.0
        h = np.clip(h, -mon["u"], mon["u"]); h -= 0.0  # tiny solver noise only
        return h, fallback


def run_path(pre: dict, R: pd.DataFrame, ci: pd.Series, b: float, kappa: float, cost: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Walk forward for one carbon bound b. Returns (per-holding-month results, holdings indexed by formation month)."""
    from m5lib import drift
    universe = pre["universe"]; n = len(universe)
    prob = GKProblem(n, kappa)
    Ru = R[universe]; pos = {d: i for i, d in enumerate(R.index)}
    civ = ci.reindex(universe).values
    hp = np.zeros(n); prev = None; rows, H = [], []
    for mon in pre["months"]:
        t = mon["t"]; i = pos[t]
        if prev is not None:
            hp = drift(prev, Ru.iloc[i].values)
        h, fb = prob.solve(mon, hp, b)
        to = float(np.abs(h - hp).sum())
        rn = np.nan_to_num(Ru.iloc[i + 1].values)
        lw, sw = np.clip(h, 0, None), np.clip(-h, 0, None)
        Lt = mon["Lt"]
        rows.append({"date": R.index[i + 1], "gross": float(h @ rn), "turnover": to,
                     "exante_te_ann": float(np.sqrt(12) * np.linalg.norm(Lt @ h)),
                     "cz_exposure": float(mon["cz"] @ h), "binding": float(mon["cz"] @ h) >= b - 1e-5,
                     "fallback": fb, "inaccurate": "inaccurate" in prob.last_status, "gross_long": float(lw.sum()),
                     "long_waci": float(np.nansum(lw * civ) / lw.sum()) if lw.sum() > 0 else np.nan,
                     "short_waci": float(np.nansum(sw * civ) / sw.sum()) if sw.sum() > 0 else np.nan,
                     "net_intensity_per_long": float(np.nansum(h * civ) / lw.sum()) if lw.sum() > 0 else np.nan,
                     "exante_alpha_ann": float(12 * mon["alpha"] @ h), "n_elig": mon["n_elig"]})
        H.append(pd.Series(h, index=universe, name=t))
        prev = h
    out = pd.DataFrame(rows).set_index("date")
    out["cost"] = cost * out["turnover"]; out["net"] = out["gross"] - out["cost"]
    return out, pd.DataFrame(H)
