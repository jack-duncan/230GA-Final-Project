"""Independent verification of M6_factor_timing headline numbers.

Does NOT import modules/M6_factor_timing/{run,m6lib}.py. Uses only lib/common.py raw-data loaders, rebuilds the
Green-minus-Brown (GB) spread, predictors, walk-forward ridge with time-series CV, Clark-West tests, timing
portfolios with industry-level turnover, FF5+UMD loadings and plain 12-1 industry momentum from scratch, then
compares with the module's CSVs.

Run: cd /home/hashim/projects/GA/project/research && uv run python modules/M6_factor_timing/verify/verify_m6.py
"""
from __future__ import annotations
import sys, pathlib, json
import numpy as np
import pandas as pd
from scipy import stats

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "lib"))
from common import load_team, load_kf_industries, load_fred, load_emv_env, load_ff5_mom, load_kf_ff3, load_mccc  # noqa

TAB = ROOT / "outputs" / "tables"
OUT = pathlib.Path(__file__).resolve().parent
LAST = pd.Timestamp("2026-07-31")
M1 = pd.offsets.MonthEnd(1)
GRID = np.r_[np.logspace(-4, 3, 36), 1e6]
res: dict = {}


def mod(name):
    return pd.read_csv(TAB / f"M6_factor_timing_{name}.csv")


# ------------------------------------------------------------------ statistics (own implementations)
def nw_mean_t(x, L=6):
    x = np.asarray(pd.Series(x).dropna(), float)
    n = len(x); u = x - x.mean()
    s = u @ u / n
    for l in range(1, L + 1):
        s += 2 * (1 - l / (L + 1)) * (u[l:] @ u[:-l]) / n
    return x.mean() / np.sqrt(s / n)


def nw_reg(y, X, L=6):
    d = pd.concat([y.rename("__y"), X], axis=1).dropna()
    Y = d["__y"].to_numpy(float); Xm = np.column_stack([np.ones(len(d)), d.drop(columns="__y").to_numpy(float)])
    n = len(Y)
    b = np.linalg.lstsq(Xm, Y, rcond=None)[0]; u = Y - Xm @ b
    g = Xm * u[:, None]
    S = g.T @ g / n
    for l in range(1, L + 1):
        G = g[l:].T @ g[:-l] / n
        S += (1 - l / (L + 1)) * (G + G.T)
    Qi = np.linalg.inv(Xm.T @ Xm / n)
    V = Qi @ S @ Qi / n
    names = ["const"] + list(X.columns)
    return pd.Series(b, names), pd.Series(b / np.sqrt(np.diag(V)), names), n


# ------------------------------------------------------------------ 1. GB spread from raw team data
team = load_team()
emis = team["emissions"].sort_values()
green, brown = list(emis.index[:5]), list(emis.index[-5:][::-1])
res["legs"] = {"green": green, "brown": brown}
IND = team["industries"].loc[:LAST]
GB = (IND[green].mean(axis=1) - IND[brown].mean(axis=1))
nan_legs = IND.loc["1970-01-31":, green + brown].isna().sum().sum()
res["leg_nans_since_1970"] = int(nan_legs)

# ------------------------------------------------------------------ 2. predictors built independently
bm = load_kf_industries("be_me_sum")                     # rows indexed June 30 of formation year Y
bm.index = bm.index.year
res["bm_nonpositive_in_legs_since_1969"] = int((bm.loc[1969:, green + brown] <= 0).sum().sum())
# BE/ME row timing check: if row Y uses ME at Dec Y-1, d log(BM) from row Y-1 to Y should load on calendar Y-1 returns.
calret = np.log1p(IND).groupby(IND.index.year).sum()
dlbm = np.log(bm.where(bm > 0)).diff()
cc = {}
for lag, lab in ((1, "calendar_Y_minus_1"), (0, "calendar_Y")):
    xs, ys = [], []
    for Y in range(1972, 2026):
        a = dlbm.loc[Y]; r = calret.loc[Y - lag]
        ok = a.notna() & r.notna()
        xs.append(a[ok]); ys.append(r[ok])
    cc[lab] = float(np.corrcoef(pd.concat(xs), pd.concat(ys))[0, 1])
res["bm_timing_corr_dlogBM_vs_returns"] = cc


def vs_at(t):
    Y = t.year if t.month >= 7 else t.year - 1          # row Y first usable at end of July Y
    row = np.log(bm.loc[Y]) if Y in bm.index else None
    return np.nan if row is None else row[green].mean() - row[brown].mean()


dates = pd.date_range("1926-07-31", "2026-08-31", freq="ME")
VS = pd.Series([vs_at(t) for t in dates], index=dates)
lg = np.log1p(GB)
MOM12 = np.exp(lg.rolling(12, min_periods=12).sum()) - 1
gs10, tb3, baa, aaa = (load_fred(s) for s in ("GS10", "TB3MS", "BAA", "AAA"))
cpi, cfnai = load_fred("CPIAUCSL"), load_fred("CFNAI")
yoy = np.log(cpi) - np.log(cpi.shift(12))
infl = yoy.shift(1)
infl = infl.where(infl.notna(), yoy.shift(2))            # Oct-2025 CPI missing: use previous print
wti = load_fred("MCOILWTICO")
vix = load_fred("VIXCLS", "last")
emv = np.log1p(load_emv_env())
attn = (emv - emv.rolling(60, min_periods=36).mean()) / emv.rolling(60, min_periods=36).std()
X = pd.DataFrame({"VS": VS, "MOM12": MOM12, "TERM": gs10 - tb3, "CREDIT": baa - aaa, "DGS10": gs10 - gs10.shift(12),
                  "INFL": infl, "CFNAI": cfnai.shift(1), "WTI": np.log(wti) - np.log(wti.shift(12)),
                  "LVIX": np.log(vix), "ATTN": attn}).loc[:"2026-08-31"]
y = GB.shift(-1)

# compare with team macro WTI and module's predictor table
tw = team["macro"]["wti"].dropna()
res["wti_team_vs_fred_maxabs"] = float((tw - wti.reindex(tw.index)).abs().max())
pt = mod("predictors").set_index("predictor")
chk = {}
for c in ["VS", "MOM12", "TERM", "CREDIT", "DGS10", "INFL", "CFNAI", "WTI", "LVIX", "ATTN"]:
    s = X[c].loc[:"2026-06-30"].dropna()
    ss = s.loc["1990-01-31":]
    z = (ss - ss.mean()) / ss.std()
    b, t, n = nw_reg(y.reindex(z.index), z.rename("z").to_frame())
    chk[c] = {"mean_mine": s.mean(), "mean_mod": pt.loc[c, "mean"], "slope1990_mine": 100 * b["z"],
              "slope1990_mod": pt.loc[c, "slope_pct_per_sd_1990"], "t1990_mine": t["z"], "t1990_mod": pt.loc[c, "t_nw_1990"]}
res["predictors"] = pd.DataFrame(chk).T.round(4).to_dict(orient="index")


# ------------------------------------------------------------------ 3. walk-forward ridge with TS-CV (own code)
def fit(Xtr, ytr, lams):
    mu = Xtr.mean(0); sd = Xtr.std(0)
    Z = (Xtr - mu) / sd; n = len(ytr); ybar = ytr.mean()
    C = Z.T @ Z / n; c = Z.T @ (ytr - ybar) / n
    ev, Q = np.linalg.eigh(C)
    B = Q @ ((Q.T @ c)[:, None] / (ev[:, None] + np.asarray(lams)[None, :]))
    return mu, sd, ybar, B


def walk(cols, start, oos, last="2026-06-30", lam=None):
    d = pd.concat([X.loc[start:last, cols], y.rename("__y")], axis=1).loc[start:last].dropna(subset=cols)
    Xv, yv, rows = d[cols].to_numpy(float), d["__y"].to_numpy(float), d.index
    cache, out = {}, []
    for k, t in enumerate(rows):
        tgt = t + M1
        if tgt < pd.Timestamp(oos) or tgt > LAST:
            continue
        if lam is None:
            sse = np.zeros(len(GRID))
            for v in range(60, k, 12):
                e = min(v + 12, k)
                if (v, e) not in cache:
                    mu, sd, a, B = fit(Xv[:v], yv[:v], GRID)
                    cache[(v, e)] = ((yv[v:e, None] - (a + ((Xv[v:e] - mu) / sd) @ B)) ** 2).sum(0)
                sse += cache[(v, e)]
            j_strict = len(GRID) - 1 - int(np.argmin(sse[::-1]))     # exact argmin, ties to the larger penalty
            L = GRID[j_strict]
            cv_rel_min = sse.min() / sse[-1]
        else:
            L, cv_rel_min = lam, np.nan
        mu, sd, a, B = fit(Xv[:k], yv[:k], [L])
        f = a + ((Xv[k] - mu) / sd) @ B[:, 0]
        out.append({"date": tgt, "origin": t, "y": yv[k], "f": f, "hm": yv[:k].mean(), "lam": L, "n_train": k})
    return pd.DataFrame(out).set_index("date")


def r2_cw(yy, fm, fb, L=6):
    d = pd.concat([yy.rename("y"), fm.rename("m"), fb.rename("b")], axis=1).dropna()
    em, eb = d["y"] - d["m"], d["y"] - d["b"]
    r2 = 1 - (em ** 2).sum() / (eb ** 2).sum()
    cw = eb ** 2 - (em ** 2 - (d["b"] - d["m"]) ** 2)
    t = nw_mean_t(cw, min(L, max(len(cw) // 4, 1))) if cw.std() > 0 else np.nan
    return 100 * r2, t, 1 - stats.norm.cdf(t) if np.isfinite(t) else np.nan, len(d)


A_COLS = ["VS", "MOM12", "TERM", "CREDIT", "DGS10", "INFL", "CFNAI"]
B0_COLS = A_COLS + ["WTI", "LVIX"]
B_COLS = B0_COLS + ["ATTN"]
SP = {"A": (A_COLS, "1970-01-31", "1990-01-31"), "B": (B_COLS, "1990-01-31", "2000-01-31"),
      "B0": (B0_COLS, "1990-01-31", "2000-01-31")}
cv = {k: walk(*v) for k, v in SP.items()}
fcm = pd.read_csv(TAB / "M6_factor_timing_forecasts.csv", index_col=0, parse_dates=True)
res["gb_realized_vs_module_maxabs"] = float((cv["A"]["y"] - fcm["gb_realized"].reindex(cv["A"].index)).abs().max())
q1 = {}
for k in ("A", "B", "B0"):
    f = cv[k]
    q1[k] = {"n": len(f), "first_n_train": int(f["n_train"].iloc[0]), "share_lambda_1e6": float((f["lam"] >= 1e6).mean()),
             "share_lambda_ge_100": float((f["lam"] >= 100).mean()), "max_abs_f_minus_hm": float((f["f"] - f["hm"]).abs().max()),
             "r2_full_pct": r2_cw(f["y"], f["f"], f["hm"])[0], "r2_post2010_pct": r2_cw(f["y"].loc["2010":], f["f"].loc["2010":], f["hm"].loc["2010":])[0]}
    if k in ("A", "B"):
        spec = {"A": "A_noVIX_1970", "B": "B_full_1990"}[k]
        q1[k]["hm_vs_module_maxabs"] = float((f["hm"] - fcm[f"{spec}_histmean"].reindex(f.index)).abs().max())
        pos = f["hm"] > 0
        q1[k]["share_hm_positive"] = float(pos.mean())
        q1[k]["last_target_month_hm_positive"] = f.index[pos].max().strftime("%Y-%m")
        q1[k]["hm_end_ann_pct"] = 1200 * f["hm"].iloc[-1]
res["Q1_ridge_cv"] = q1

# fixed penalties (sensitivity) and nested B vs B0
fixed = {}
for k in ("A", "B", "B0"):
    for lam in (0.0, 0.01, 0.1, 1.0, 10.0):
        fixed[(k, lam)] = walk(*SP[k], lam=lam)
fx = {}
for k in ("A", "B"):
    for lam in (0.0, 0.01, 0.1, 1.0, 10.0):
        f = fixed[(k, lam)]
        full = r2_cw(f["y"], f["f"], f["hm"]); post = r2_cw(f["y"].loc["2010":], f["f"].loc["2010":], f["hm"].loc["2010":])
        fx[f"{k}_lam{lam:g}"] = {"r2_full": full[0], "cw_t_full": full[1], "r2_post2010": post[0], "cw_t_post2010": post[1],
                                 "p1_post2010": post[2]}
for lam in (0.0, 0.01, 0.1, 1.0, 10.0):
    b, b0 = fixed[("B", lam)], fixed[("B0", lam)]
    full = r2_cw(b["y"], b["f"], b0["f"]); post = r2_cw(b["y"].loc["2010":], b["f"].loc["2010":], b0["f"].loc["2010":])
    fx[f"BvsB0_lam{lam:g}"] = {"r2_full": full[0], "cw_t_full": full[1], "r2_post2010": post[0], "cw_t_post2010": post[1]}
res["fixed_penalty"] = pd.DataFrame(fx).T.round(4).to_dict(orient="index")

# full-sample CV curve relative to the historical mean (interpretation)
cvc = {}
for k in ("A", "B"):
    cols, st, _ = SP[k]
    d = pd.concat([X.loc[st:"2026-06-30", cols], y.rename("__y")], axis=1).loc[st:"2026-06-30"].dropna()
    Xv, yv = d[cols].to_numpy(float), d["__y"].to_numpy(float)
    g = np.array([1e-4, 0.1, 1.0, 10.0, 1e6])
    sse = np.zeros(len(g))
    for v in range(60, len(yv), 12):
        e = min(v + 12, len(yv))
        mu, sd, a, B = fit(Xv[:v], yv[:v], g)
        sse += ((yv[v:e, None] - (a + ((Xv[v:e] - mu) / sd) @ B)) ** 2).sum(0)
    cvc[k] = dict(zip(["1e-4", "0.1", "1", "10"], np.round(sse[:-1] / sse[-1], 4)))
res["cv_curve_rel_histmean"] = cvc


# ------------------------------------------------------------------ 4. timing portfolios, turnover, costs
def turnover(H, R):
    R = R.reindex(H.index)[H.columns]
    out = pd.Series(np.nan, index=H.index)
    for i in range(1, len(H)):
        hp, rp = H.iloc[i - 1].to_numpy(), R.iloc[i - 1].to_numpy()
        pre = hp * (1 + rp) / (1 + hp @ rp)
        out.iloc[i] = np.abs(H.iloc[i].to_numpy() - pre).sum()
    return out


def strategy(w_raw, win):
    g = w_raw * GB.reindex(w_raw.index)
    k = 0.05 / (np.sqrt(12) * g.loc[win[0]:win[1]].std())
    w = k * w_raw
    H = pd.DataFrame({**{i: w / 5 for i in green}, **{i: -w / 5 for i in brown}})
    to = turnover(H, IND)
    gross = w * GB.reindex(w.index)
    return pd.DataFrame({"w": w, "gross": gross, "net": gross - 10e-4 * to.fillna(0), "to": to})


def sr(r):
    r = r.dropna(); return np.sqrt(12) * r.mean() / r.std()


fac = load_ff5_mom()
FF6 = ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "UMD"]
var60 = GB.rolling(60).var()
pf = {}
PP = {}
for k, oos in (("A", "1990-01-31"), ("B", "2000-01-31")):
    f = cv[k]
    v = var60.reindex(f["origin"]).to_numpy()
    win = (pd.Timestamp(oos), LAST)
    tim = strategy(pd.Series(f["f"].to_numpy() / (5 * v), f.index), win)
    pm = strategy(pd.Series(f["hm"].to_numpy() / (5 * v), f.index), win)
    st = strategy(pd.Series(1.0, index=f.index), win)
    ols = strategy(pd.Series(fixed[(k, 0.0)]["f"].to_numpy() / (5 * v), f.index), win)
    PP[k] = (tim, st)
    dd = tim["net"] - st["net"]
    b, t, n = nw_reg(st["net"], fac.reindex(st.index)[FF6])
    ba, ta, _ = nw_reg(tim["net"], fac.reindex(tim.index)[FF6])
    pf[k] = {"timing_net_ret_full_pct": 1200 * tim["net"].mean(), "timing_sr_net_full": sr(tim["net"]),
             "timing_sr_net_last12": sr(tim["net"].loc["2025-08-31":]), "timing_sr_net_last18": sr(tim["net"].loc["2025-02-28":]),
             "timing_vol_post2010_pct": 100 * np.sqrt(12) * tim["gross"].loc["2010":].std(),
             "timing_eq_prevmean_maxabs": float((tim["net"] - pm["net"]).abs().max()),
             "timing_frac_long": float((tim["w"] > 0).mean()),
             "static_net_ret_full_pct": 1200 * st["net"].mean(), "static_sr_net_full": sr(st["net"]),
             "static_sr_net_last12": sr(st["net"].loc["2025-08-31":]),
             "timing_minus_static_pct": 1200 * dd.mean(), "timing_minus_static_t": nw_mean_t(dd),
             "turnover_timing_ann": 12 * tim["to"].mean(), "turnover_static_ann": 12 * st["to"].mean(),
             "ols_sr_net_full": sr(ols["net"]), "turnover_ols_ann": 12 * ols["to"].mean(),
             "timing_alpha_ff6_net_pct": 1200 * ba["const"], "timing_t_alpha": ta["const"],
             "static_alpha_ff6_net_pct": 1200 * b["const"], "static_t_alpha": t["const"]}
    for c in FF6:
        pf[k][f"static_b_{c}"] = b[c]; pf[k][f"static_t_{c}"] = t[c]
    # sensitivity: difference test with the static leg scaled to the timing rule's mean |w| (gross, no costs)
    # instead of both at equal ex-post vol (the relative scale is not innocuous for a difference of two strategies)
    pf[k]["timing_minus_static_equal_raw_scale_t"] = nw_mean_t(
        (pd.Series(f["hm"].to_numpy() / (5 * v), f.index) * GB.reindex(f.index)) - GB.reindex(f.index) *
        (pd.Series(f["hm"].to_numpy() / (5 * v), f.index).abs().mean()))
res["portfolio"] = pd.DataFrame(pf).round(4).to_dict()

# ------------------------------------------------------------------ 5. plain 12-1 industry momentum, top 8 - bottom 8
R = IND
mom = np.exp(np.log1p(R).shift(1).rolling(11, min_periods=11).sum()) - 1        # months t-11..t-1
size = load_kf_industries("size")
Wd = {}; Wd_all = {}
for t in R.loc["1989-12-31":"2026-06-30"].index:
    Y = t.year if t.month >= 7 else t.year - 1
    bmrow = bm.loc[Y] if Y in bm.index else pd.Series(dtype=float)
    ok_all = mom.loc[t].notna() & R.shift(-1).loc[t].notna()
    ok = ok_all & (bmrow.reindex(R.columns) > 0) & (size.reindex([t]).iloc[0].reindex(R.columns) > 0)
    for store, mask in ((Wd, ok), (Wd_all, ok_all)):
        s = mom.loc[t][mask].sort_values()
        w = pd.Series(0.0, index=R.columns)
        w[s.index[-8:]] = 1 / 8; w[s.index[:8]] = -1 / 8
        store[t + M1] = w
mres = {}
for lab, Wx in (("module_universe", Wd), ("all_industries", Wd_all)):
    W = pd.DataFrame(Wx).T
    gross = (W * R.reindex(W.index)).sum(axis=1)
    to = turnover(W, R)
    net = gross - 10e-4 * to.fillna(0)
    b, t, _ = nw_reg(net, fac.reindex(net.index)[FF6])
    mres[lab] = {"n": len(net), "net_ret_pct": 1200 * net.mean(), "vol_pct": 100 * np.sqrt(12) * gross.std(), "sr_net": sr(net),
                 "t_mean_net": nw_mean_t(net), "sr_net_post2010": sr(net.loc["2010":]), "turnover_ann": 12 * to.mean(),
                 "alpha_pct": 1200 * b["const"], "t_alpha": t["const"], "b_UMD": b["UMD"], "t_UMD": t["UMD"]}
    if lab == "module_universe":
        mom_net = net
rr = pd.read_csv(TAB / "M6_factor_timing_rotation_returns.csv", index_col=0, parse_dates=True)
mres["module_mom_net_vs_mine_maxabs"] = float((rr["industry_mom_12_1"] - mom_net.reindex(rr.index)).abs().max())
dd = rr["rotation_ridge"] - mom_net.reindex(rr.index)
mres["ridge_minus_mom_pct"] = 1200 * dd.mean(); mres["ridge_minus_mom_t"] = nw_mean_t(dd)
mres["ridge_sr_net_from_module_returns"] = sr(rr["rotation_ridge"])
res["rotation"] = mres

# ------------------------------------------------------------------ 5b. extra checks: MCCC increment, univariate DGS10,
# CV-design sensitivity, LMN variant (own implementation), and ATTN on the team's actual target (Brown-leg FF3 residual)
X["MCCC"] = np.log(load_mccc())
ex = {}
c0 = walk(B0_COLS, "2003-01-31", "2013-01-31", last="2025-06-30", lam=0.1)
cm = walk(B0_COLS + ["MCCC"], "2003-01-31", "2013-01-31", last="2025-06-30", lam=0.1)
r = r2_cw(cm["y"], cm["f"], c0["f"]); ex["MCCC_increment_lam0.1"] = {"r2": r[0], "cw_t": r[1], "p1": r[2], "n": r[3]}
for k, (st, oos) in (("A", ("1970-01-31", "1990-01-31")), ("B", ("1990-01-31", "2000-01-31"))):
    cols = SP[k][0]
    f = walk(["DGS10"], st, oos, lam=0.0)
    f = f.loc["2010":]
    r = r2_cw(f["y"], f["f"], f["hm"]); ex[f"univ_DGS10_{k}_post2010"] = {"r2": r[0], "cw_t": r[1], "p1": r[2]}


def walk_cv_variant(cols, start, oos, first=60, recent=None, grid=GRID):
    """CV-design sensitivity: first training fold length and/or validate only on the most recent `recent` months."""
    d = pd.concat([X.loc[start:"2026-06-30", cols], y.rename("__y")], axis=1).loc[start:"2026-06-30"].dropna(subset=cols)
    Xv, yv, rows = d[cols].to_numpy(float), d["__y"].to_numpy(float), d.index
    cache, out = {}, []
    for k, t in enumerate(rows):
        if t + M1 < pd.Timestamp(oos):
            continue
        sse = np.zeros(len(grid))
        for v in range(first, k, 12):
            e = min(v + 12, k)
            if recent is not None and e <= k - recent:
                continue
            if (v, e) not in cache:
                mu, sd, a, B = fit(Xv[:v], yv[:v], grid)
                cache[(v, e)] = ((yv[v:e, None] - (a + ((Xv[v:e] - mu) / sd) @ B)) ** 2).sum(0)
            sse += cache[(v, e)]
        L = grid[len(grid) - 1 - int(np.argmin(sse[::-1]))]
        mu, sd, a, B = fit(Xv[:k], yv[:k], [L])
        out.append({"date": t + M1, "y": yv[k], "f": a + ((Xv[k] - mu) / sd) @ B[:, 0], "hm": yv[:k].mean(), "lam": L})
    return pd.DataFrame(out).set_index("date")


for k in ("A", "B"):
    cols, st, oos = SP[k]
    for lab, kw in (("first120", {"first": 120}), ("recent120", {"recent": 120}), ("recent60", {"recent": 60}),
                    ("grid_no_1e6", {"grid": GRID[:-1]})):
        f = walk_cv_variant(cols, st, oos, **kw)
        mx = kw.get("grid", GRID).max()
        full = r2_cw(f["y"], f["f"], f["hm"]); post = r2_cw(f["y"].loc["2010":], f["f"].loc["2010":], f["hm"].loc["2010":])
        ex[f"cv_{lab}_{k}"] = {"share_at_max": float((f["lam"] >= mx).mean()), "share_lam_le_1": float((f["lam"] <= 1).mean()),
                               "median_lam": float(f["lam"].median()), "r2_full": full[0], "cw_t_full": full[1],
                               "r2_post2010": post[0], "cw_t_post2010": post[1]}

# LMN (K=1) portfolio-shrinkage variant, own implementation of the method as described in FINDINGS section 3
from sklearn.covariance import LedoitWolf
LGRID = np.r_[0.0, np.logspace(-1, 5, 25), 1e9]


def lmn(cols, start, sign=True):
    d = pd.concat([X.loc[start:"2026-06-30", cols], y.rename("__y")], axis=1).loc[start:"2026-06-30"].dropna(subset=cols)
    Xv, yv, rows = d[cols].to_numpy(float), d["__y"].to_numpy(float), d.index
    blocks = []
    for k in [k for k, t in enumerate(rows) if t.month == 12 and k >= 119]:
        mu_x, sd_x = Xv[:k].mean(0), Xv[:k].std(0)
        Z = (Xv[:k] - mu_x) / sd_x
        G = np.column_stack([yv[:k], Z * yv[:k, None]]); T = k
        S = LedoitWolf().fit(G).covariance_; Dg = np.diag(np.diag(S)); m = G.mean(0)
        w0 = np.zeros_like(m); w0[0] = m[0]
        app = np.arange(k, min(k + 12, len(rows)))
        Za = (Xv[app] - mu_x) / sd_x
        H = []
        for lam in LGRID:
            w = np.linalg.solve(S + lam / T * Dg, m + lam / T * w0)
            h = w[0] + Za @ w[1:]
            H.append(np.sign(h) if sign else h)
        blocks.append((app, np.array(H)))
    out = {}
    for i in range(1, len(blocks)):
        pr = np.concatenate([Hp * yv[ap][None, :] for ap, Hp in blocks[:i]], axis=1)
        pr = pr[:, ~np.isnan(pr).any(0)]
        s = pr.mean(1) / pr.std(1)
        s = np.where(np.isfinite(s), s, -np.inf)
        j = len(LGRID) - 1 - int(np.argmax(s[::-1]))
        app, H = blocks[i]
        for jj, rr_ in enumerate(app):
            if rows[rr_] + M1 <= LAST:
                out[rows[rr_] + M1] = H[j, jj]
    return pd.Series(out)


for nm, cols in (("B0", B0_COLS), ("B", B_COLS), ("A", A_COLS)):
    st = "1970-01-31" if nm == "A" else "1990-01-31"
    oos = "1990-01-31" if nm == "A" else "2000-01-31"
    for sg in (True, False):
        h = lmn(cols, st, sg)
        h = h.loc[max(pd.Timestamp(oos), h.index.min()):]
        S_ = strategy(h, (h.index.min(), LAST))
        ex[f"LMN_{nm}_{'sign' if sg else 'raw'}"] = {"start": h.index.min().strftime("%Y-%m"), "n": len(h),
                                                    "sr_gross": sr(S_["gross"]), "sr_net": sr(S_["net"]),
                                                    "turnover_ann": 12 * S_["to"].mean()}

# ATTN vs the team's actual target: next-month Brown-leg excess return FF3 residual (rolling 60m, betas lagged 1m)
ff3t = team["ff3"]
bl = (IND[brown].mean(axis=1) - ff3t["RF"].reindex(IND.index)).rename("y")
dd_ = pd.concat([bl, ff3t[["Mkt-RF", "SMB", "HML"]]], axis=1).dropna()
coefs = {}
for end in range(59, len(dd_)):
    smp = dd_.iloc[end - 59:end + 1]
    Xm = np.column_stack([np.ones(60), smp[["Mkt-RF", "SMB", "HML"]].to_numpy()])
    coefs[dd_.index[end]] = np.linalg.lstsq(Xm, smp["y"].to_numpy(), rcond=None)[0]
C = pd.DataFrame(coefs).T.reindex(dd_.index).shift(1)
eps = dd_["y"] - C[0] - (C[[1, 2, 3]].to_numpy() * dd_[["Mkt-RF", "SMB", "HML"]].to_numpy()).sum(1)
eps_next = eps.shift(-1)
for per, a in (("1990on", "1990-01-31"), ("2010on", "2010-01-31")):
    z = X["ATTN"].loc[a:"2026-06-30"].dropna()
    b, t, n = nw_reg(eps_next.reindex(z.index), ((z - z.mean()) / z.std()).rename("z").to_frame())
    ex[f"ATTN_on_team_brown_resid_IS_{per}"] = {"slope_pct_per_sd": 100 * b["z"], "t": t["z"], "n": n}
# expanding univariate OLS OOS forecast of the Brown residual from ATTN vs expanding mean (team direction: slope < 0)
dz = pd.concat([X["ATTN"], eps_next.rename("__y")], axis=1).loc["1990-01-31":"2026-06-30"].dropna()
recs = []
for k in range(len(dz)):
    t = dz.index[k]
    if t + M1 < pd.Timestamp("2000-01-31"):
        continue
    xa, ya = dz["ATTN"].to_numpy()[:k], dz["__y"].to_numpy()[:k]
    bb = np.polyfit(xa, ya, 1)
    recs.append({"date": t + M1, "y": dz["__y"].iloc[k], "f": np.polyval(bb, dz["ATTN"].iloc[k]), "hm": ya.mean()})
ob = pd.DataFrame(recs).set_index("date")
for per, a in (("2000on", "2000"), ("2010on", "2010"), ("holdout", "2022-08")):
    r = r2_cw(ob["y"].loc[a:], ob["f"].loc[a:], ob["hm"].loc[a:])
    ex[f"ATTN_team_brown_resid_OOS_{per}"] = {"r2": r[0], "cw_t": r[1], "p1": r[2], "n": r[3]}
res["extra"] = pd.DataFrame(ex).T.to_dict(orient="index")

# ------------------------------------------------------------------ 6. ledger consistency
led = mod("tests_ledger")
chk = {}
chk["counts"] = led["primary_or_exploratory"].value_counts().to_dict()
chk["duplicate_ids"] = int(led["test_id"].duplicated().sum())
# two-sided p from the statistic (normal) vs recorded
zp = 2 * (1 - stats.norm.cdf(led["statistic"].abs()))
cw_rows = led["statistic_name"].str.contains("Clark-West")
chk["max_abs_p_mismatch_cw_rows"] = float((zp[cw_rows] - led.loc[cw_rows, "p_value_two_sided"]).abs().max())
chk["cw_rows_with_negative_t_and_p2_lt_0.10"] = led.loc[cw_rows & (led["statistic"] < 0) & (led["p_value_two_sided"] < 0.10),
                                                        ["test_id", "statistic", "p_value_two_sided"]].round(4).to_dict(orient="records")
res["ledger"] = chk


def default(o):
    if isinstance(o, (np.floating, np.integer)):
        return o.item()
    if isinstance(o, (pd.Timestamp,)):
        return str(o)
    return str(o)


(OUT / "verify_results.json").write_text(json.dumps(res, indent=1, default=default))
print(json.dumps(res, indent=1, default=default))
