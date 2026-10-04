"""Verifier helpers (own implementations; no M5 module code). Shared by verify_m5.py and verify_m5_optimizer.py."""
from __future__ import annotations
import sys, pathlib
import numpy as np
import pandas as pd
from scipy import stats

RES = pathlib.Path("/home/hashim/projects/GA/project/research")
sys.path.insert(0, str(RES / "lib"))
import common as C  # loaders only
TAB = RES / "outputs" / "tables"
tab = lambda n: pd.read_csv(TAB / f"M5_industry_momentum_{n}.csv")

# ------------------------------------------------------------------ own statistics
def nw(y, X=None, L=6):
    """OLS with Bartlett-kernel Newey-West covariance, L lags, no small-sample correction. Returns dict."""
    y = pd.Series(y).astype(float)
    Xd = pd.DataFrame(index=y.index) if X is None else pd.DataFrame(X).astype(float)
    d = pd.concat([y.rename("__y"), Xd], axis=1).dropna()
    Y = d["__y"].values; Xm = np.column_stack([np.ones(len(d)), d.drop(columns="__y").values])
    names = ["const"] + list(d.drop(columns="__y").columns)
    XtX_inv = np.linalg.inv(Xm.T @ Xm); b = XtX_inv @ Xm.T @ Y; u = Y - Xm @ b
    g = Xm * u[:, None]; S = g.T @ g
    for l in range(1, L + 1):
        w = 1 - l / (L + 1); G = g[l:].T @ g[:-l]; S += w * (G + G.T)
    V = XtX_inv @ S @ XtX_inv; se = np.sqrt(np.diag(V)); t = b / se
    r2 = 1 - (u @ u) / ((Y - Y.mean()) @ (Y - Y.mean()))
    return {"b": dict(zip(names, b)), "t": dict(zip(names, t)), "p": dict(zip(names, 2 * stats.norm.sf(np.abs(t)))),
            "n": len(Y), "r2": r2}

def ann(y):
    y = y.dropna(); return 12 * y.mean(), np.sqrt(12) * y.std(ddof=1), np.sqrt(12) * y.mean() / y.std(ddof=1)

def mdd(y):
    w = (1 + y.dropna()).cumprod(); return (w / w.cummax() - 1).min()

def cbb(n, block, B, rng):
    nb = -(-n // block); st = rng.integers(0, n, size=(B, nb))
    return ((st[:, :, None] + np.arange(block)) % n).reshape(B, -1)[:, :n]

def sr(x, axis=None):
    return np.sqrt(12) * x.mean(axis=axis) / x.std(axis=axis, ddof=1)

def boot_dsr(a, b, seed=777, B=5000, block=12):
    d = pd.concat([a, b], axis=1).dropna(); A, Bv = d.iloc[:, 0].values, d.iloc[:, 1].values
    idx = cbb(len(d), block, B, np.random.default_rng(seed))
    hat = sr(A) - sr(Bv); st = sr(A[idx], 1) - sr(Bv[idx], 1)
    return hat, np.percentile(st, 2.5), np.percentile(st, 97.5), float(np.mean(np.abs(st - hat) >= abs(hat)))

# ------------------------------------------------------------------ data
T = C.load_team()
R = T["industries"].loc[:"2026-07-31"]
F5 = C.load_ff5_mom(); F3 = C.load_kf_ff3()
emis = T["emissions"]
X6 = F5[["Mkt-RF", "SMB", "HML", "RMW", "CMA", "UMD"]]
MODELS = {"CAPM": F3[["Mkt-RF"]], "FF3": F3[["Mkt-RF", "SMB", "HML"]], "FF5": F5[["Mkt-RF", "SMB", "HML", "RMW", "CMA"]], "FF5+UMD": X6}
cap = (C.load_kf_industries("nfirms") * C.load_kf_industries("size")).reindex(columns=R.columns)
R_kf = C.load_kf_industries("vw").reindex(columns=R.columns).loc[:"2026-07-31"]
P = {"full": ("1970-01-31", "2026-07-31"), "post2010": ("2010-01-31", "2026-07-31"), "holdout": ("2022-08-31", "2026-07-31"),
     "validation": ("2010-01-31", "2022-07-31"), "last18": ("2025-02-28", "2026-07-31"), "last12": ("2025-08-31", "2026-07-31")}
S = lambda s, p: s.loc[P[p][0]:P[p][1]]

# ------------------------------------------------------------------ own momentum book
def book(Rdf, L=11, Skip=1, n=8, capdf=None, long_u=None, short_u=None, c=0.0010):
    A = Rdf.values; idx = Rdf.index; cols = np.array(Rdf.columns)
    i0, i1 = idx.get_loc(pd.Timestamp("1969-12-31")), idx.get_loc(pd.Timestamp("2026-06-30"))
    Ws, rows = [], []
    prev = None
    for i in range(i0, i1 + 1):
        win = A[i - Skip - L + 1:i - Skip + 1]
        ok = ~np.isnan(win).any(axis=0)
        s = np.where(ok, np.prod(1 + np.nan_to_num(win), axis=0) - 1, np.nan)
        cand_l = ok & (np.isin(cols, long_u) if long_u is not None else True)
        order_l = [j for j in np.argsort(-np.where(cand_l, s, -np.inf), kind="stable") if cand_l[j]][:n]
        cand_s = ok & (np.isin(cols, short_u) if short_u is not None else True)
        cand_s[order_l] = False
        order_s = [j for j in np.argsort(np.where(cand_s, s, np.inf), kind="stable") if cand_s[j]][:n]
        w = np.zeros(len(cols))
        if capdf is None:
            w[order_l] = 1 / len(order_l); w[order_s] = -1 / len(order_s)
        else:
            cv = capdf.loc[idx[i]].values
            w[order_l] = cv[order_l] / cv[order_l].sum(); w[order_s] = -cv[order_s] / cv[order_s].sum()
        if prev is None:
            drifted = np.zeros(len(cols))
        else:
            r = np.nan_to_num(A[i]); drifted = prev * (1 + r) / (1 + prev @ r)
        rn = A[i + 1]
        assert not np.isnan(rn[w != 0]).any(), f"held industry lacks next return at {idx[i]}"
        rn = np.nan_to_num(rn)
        rows.append((idx[i + 1], w @ rn, np.abs(w - drifted).sum(), ok.sum()))
        Ws.append(pd.Series(w, index=cols, name=idx[i + 1])); prev = w
    bt = pd.DataFrame(rows, columns=["date", "gross", "to", "n_elig"]).set_index("date")
    bt["net"] = bt["gross"] - c * bt["to"]
    return bt, pd.DataFrame(Ws)

