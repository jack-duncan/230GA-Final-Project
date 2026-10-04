"""Independent re-implementation of the M5 Grinold-Kahn carbon frontier (convention X, bounds none/0/-1/-2).

Does NOT import module code. Own signal, own residual vol, own Ledoit-Wolf call, own cvxpy formulation
(quad_form on the eligible sub-vector instead of the builder's padded Cholesky), own drift/turnover, own block
bootstrap with a different seed. Writes verify/verify_optimizer_results.csv.

Run:  cd /home/hashim/projects/GA/project/research && uv run python modules/M5_industry_momentum/verify/verify_m5_optimizer.py
"""
from __future__ import annotations
import sys, pathlib, time
import numpy as np
import pandas as pd
import cvxpy as cp
from sklearn.covariance import LedoitWolf
from scipy import stats

RES = pathlib.Path("/home/hashim/projects/GA/project/research")
sys.path.insert(0, str(RES / "lib"))
import common as C
OUT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(OUT))
from vlib import nw, cbb, sr, book  # own verifier helpers (not module code)  # noqa: E402

T = C.load_team(); R = T["industries"].loc[:"2026-07-31"]; F5 = C.load_ff5_mom(); emis = T["emissions"]
X6 = F5[["Mkt-RF", "SMB", "HML", "RMW", "CMA", "UMD"]]
cov = [c for c in R.columns if c in emis.index]; n = len(cov)
A = R[cov].values; RF = F5["RF"].reindex(R.index).values; MK = F5["Mkt-RF"].reindex(R.index).values
logc = np.log(emis.reindex(cov).values); civ = emis.reindex(cov).values
idx = R.index; i0, i1 = idx.get_loc(pd.Timestamp("1969-12-31")), idx.get_loc(pd.Timestamp("2026-06-30"))

pre = []
for i in range(i0, i1 + 1):
    win = A[i - 59:i + 1] - RF[i - 59:i + 1, None]
    sw = A[i - 11:i]; s = np.prod(1 + sw, axis=0) - 1
    e = ~np.isnan(win).any(0) & ~np.isnan(sw).any(0) & ~np.isnan(A[i + 1])
    m = np.where(e)[0]; Xe = win[:, m]
    Z = np.column_stack([np.ones(60), MK[i - 59:i + 1]])
    res = Xe - Z @ np.linalg.lstsq(Z, Xe, rcond=None)[0]
    sres = np.sqrt((res ** 2).sum(0) / (60 - 2))
    z = (s[m] - s[m].mean()) / s[m].std(ddof=1)
    cz = (logc[m] - logc[m].mean()) / logc[m].std(ddof=1)
    V = LedoitWolf().fit(Xe).covariance_
    pre.append((i, m, 0.05 * sres * z, cz, V))
print("precompute done; eligible range", min(len(p[1]) for p in pre), max(len(p[1]) for p in pre))

def run(bound):
    rows, prev = [], None
    for (i, m, a, cz, V) in pre:
        hd = np.zeros(n) if prev is None else prev * (1 + np.nan_to_num(A[i])) / (1 + prev @ np.nan_to_num(A[i]))
        h = cp.Variable(n); he = h[m]
        mask = np.ones(n, bool); mask[m] = False
        base = [cp.quad_form(he, cp.psd_wrap(V)) <= 0.05 ** 2 / 12, cp.sum(h) == 0, cp.abs(he) <= 0.10]
        if mask.any():
            base.append(h[np.where(mask)[0]] == 0)
        cons = base + ([cz @ he <= bound] if bound is not None else [])
        pr = cp.Problem(cp.Maximize(a @ he - 0.0010 * cp.norm1(h - hd)), cons)
        pr.solve(solver=cp.CLARABEL)
        fb = False
        if pr.status not in ("optimal", "optimal_inaccurate"):
            fb = True; cp.Problem(cp.Minimize(cz @ he), base).solve(solver=cp.CLARABEL)
        hv = np.array(h.value); hv[mask] = 0.0
        rn = np.nan_to_num(A[i + 1]); lw = np.clip(hv, 0, None)
        rows.append({"date": idx[i + 1], "gross": hv @ rn, "to": np.abs(hv - hd).sum(), "fb": fb, "cz": cz @ hv[m],
                     "lwaci": (lw * civ).sum() / lw.sum(), "te": np.sqrt(12 * hv[m] @ V @ hv[m])})
        prev = hv
    out = pd.DataFrame(rows).set_index("date"); out["net"] = out.gross - 0.0010 * out.to
    return out

t0 = time.time(); paths = {}
for b in (None, 0.0, -1.0, -2.0):
    paths[b] = run(b); print(f"bound {b}: done {time.time() - t0:.0f}s; IR {sr(paths[b].net.values):.3f}; fallback {int(paths[b].fb.sum())}", flush=True)

builder = pd.read_csv(RES / "outputs/tables/M5_industry_momentum_optimizer_returns_monthly.csv", index_col=0, parse_dates=True)
fr = pd.read_csv(RES / "outputs/tables/M5_industry_momentum_optimizer_frontier.csv").set_index("key")
ct = pd.read_csv(RES / "outputs/tables/M5_industry_momentum_carbon_cost_test.csv")
rows = []
def rec(claim, builder_v, mine, tol, note=""):
    v = "confirmed" if abs(mine - builder_v) <= tol else "DISCREPANCY"
    rows.append({"claim": claim, "builder": builder_v, "mine": mine, "tol": tol, "verdict": v, "note": note})
    print(f"{v:12s} {claim:55s} builder {builder_v:>9.4f} mine {mine:9.4f} {note}")

KEY = {None: "X_unc", 0.0: "X_b+0.00", -1.0: "X_b-1.00", -2.0: "X_b-2.00"}
for b, k in KEY.items():
    d = pd.concat([paths[b].net, builder[k]], axis=1).dropna()
    print(f"  {k}: corr(mine, builder) {d.corr().iloc[0, 1]:.5f}; max |diff| {np.abs(d.iloc[:, 0] - d.iloc[:, 1]).max():.2e}; "
          f"ex-ante TE mean {paths[b].te.mean():.4f}; realized vol {np.sqrt(12) * paths[b].net.std():.4f}; turnover {12 * paths[b].to.mean():.2f}")
u = paths[None]; ra = nw(u.net, X6)
rec("X_unc IR full", 0.555, sr(u.net.values), 0.0015); rec("X_unc FF5+UMD alpha (%)", 2.17, 1200 * ra["b"]["const"], 0.02)
rec("X_unc alpha t", 3.07, ra["t"]["const"], 0.02); rec("X_unc realized vol (%)", 6.95, 100 * np.sqrt(12) * u.net.std(), 0.02)
rec("X_unc turnover x/yr", 2.92, 12 * u.to.mean(), 0.02); rec("X_unc long WACI", 0.159, u.lwaci.mean(), 0.0015)
rec("X_unc mean c'h", -0.09, u.cz.mean(), 0.02)
rh = nw(u.net.loc["2022-08-31":], X6); rec("X_unc holdout alpha (%)", -0.34, 1200 * rh["b"]["const"], 0.02); rec("X_unc holdout t", -0.15, rh["t"]["const"], 0.02)
dec_t = {}
for k_, (s_, e_) in {"1970s": ("1970", "1979"), "1980s": ("1980", "1989"), "1990s": ("1990", "1999"), "2000s": ("2000", "2009"),
                     "2010s": ("2010", "2019"), "2020s": ("2020", "2026")}.items():
    dec_t[k_] = nw(u.net.loc[s_:e_], X6)["t"]["const"]
print("  X_unc decade alpha t:", {k: round(v, 2) for k, v in dec_t.items()})
rec("X_unc largest decade alpha t", 1.97, max(dec_t.values()), 0.02)

rng_seed = 4242
def boot(a, b, B=5000):
    Av, Bv = a.values, b.values; ix = cbb(len(Av), 12, B, np.random.default_rng(rng_seed))
    hat = sr(Av) - sr(Bv); st = sr(Av[ix], 1) - sr(Bv[ix], 1)
    return hat, np.percentile(st, 2.5), np.percentile(st, 97.5), float(np.mean(np.abs(st - hat) >= abs(hat)))
for b, (bd, bp, blo, bhi, bw) in {0.0: (0.010, 0.328, -0.010, 0.031, -11.6), -1.0: (-0.005, 0.93, -0.110, 0.096, -60),
                                  -2.0: (-0.284, 0.038, -0.555, -0.015, -82)}.items():
    hat, lo, hi, p = boot(paths[b].net, u.net)
    rec(f"b={b} dIR", bd, hat, 0.0015); rec(f"b={b} p boot (own seed; MC tol)", bp, p, 0.03)
    rec(f"b={b} CI lo", blo, lo, 0.01); rec(f"b={b} CI hi", bhi, hi, 0.01)
    rec(f"b={b} long WACI change (%)", bw, 100 * (paths[b].lwaci.mean() / u.lwaci.mean() - 1), 0.6)
    if b == 0.0:
        rec("b=0 binding share (%)", 26.5, 100 * (paths[b].cz >= -1e-5).mean(), 0.6)
        dd = nw(paths[b].net - u.net, X6); rec("b=0 alpha change (%)", 0.08, 1200 * dd["b"]["const"], 0.006); rec("b=0 alpha change t", 1.00, dd["t"]["const"], 0.02)
    if b == -2.0:
        rec("b=-2 fallback months", 64, paths[b].fb.sum(), 0)
# optimizer vs primary equal-weight book
bt, _ = book(R)
hat, lo, hi, p = boot(u.net, bt.net); rec("X_unc minus primary dIR", 0.082, hat, 0.0015); rec("X_unc minus primary p boot", 0.436, p, 0.03)
pd.DataFrame(rows).to_csv(OUT / "verify_optimizer_results.csv", index=False)
for b, k in KEY.items():
    paths[b].to_csv(OUT / f"verify_opt_path_{k}.csv")
print("\nDISCREPANCIES:"); print(pd.DataFrame(rows).query("verdict == 'DISCREPANCY'").to_string())
