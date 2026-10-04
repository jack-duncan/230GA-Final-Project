"""Round-2 independent verification of M6_factor_timing (checks added after VERIFY.md round 1).

Reuses ONLY my own round-1 verifier (verify_m6.py, imported as a module: it rebuilds GB, predictors, walk-forward
ridge, CW tests, timing portfolios and LMN from lib/common.py raw loaders) and never imports run.py or m6lib.py.
Recomputes the new module outputs: cv_design, team_target_check, scaling_sensitivity, risk_concentration,
lmn_attn_increment, timing_vs_prevmean, histmean_sign dates, timing-portfolio FF6 loadings, and ledger integrity.

Run: cd /home/hashim/projects/GA/project/research && uv run python modules/M6_factor_timing/verify/verify_m6_r2.py
"""
from __future__ import annotations
import sys, pathlib, json, importlib.util, io, contextlib
import numpy as np
import pandas as pd
from scipy import stats

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("v1", HERE / "verify_m6.py")
v1 = importlib.util.module_from_spec(spec)
with contextlib.redirect_stdout(io.StringIO()):
    spec.loader.exec_module(v1)          # rebuilds everything independently (and rewrites verify_results.json)

TAB, X, y, GB, IND, GRID, LAST, M1 = v1.TAB, v1.X, v1.y, v1.GB, v1.IND, v1.GRID, v1.LAST, v1.M1
fit, r2_cw, nw_mean_t, nw_reg, strategy, turnover, sr = (v1.fit, v1.r2_cw, v1.nw_mean_t, v1.nw_reg, v1.strategy,
                                                         v1.turnover, v1.sr)
A_COLS, B0_COLS, B_COLS, SP = v1.A_COLS, v1.B0_COLS, v1.B_COLS, v1.SP
green, brown = v1.green, v1.brown
res: dict = {}


def mod(name, **kw):
    return pd.read_csv(TAB / f"M6_factor_timing_{name}.csv", **kw)


def walk_y(cols, start, oos, target, lam=None, first=60, recent=None, grid=GRID, last="2026-06-30"):
    """Walk-forward ridge on an arbitrary target series (target[t] = realized value in t+1)."""
    d = pd.concat([X.loc[start:last, cols], target.rename("__y")], axis=1).loc[start:last].dropna(subset=cols)
    Xv, yv, rows = d[cols].to_numpy(float), d["__y"].to_numpy(float), d.index
    cache, out = {}, []
    for k, t in enumerate(rows):
        if t + M1 < pd.Timestamp(oos) or t + M1 > LAST:
            continue
        if lam is None:
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
        else:
            L = lam
        mu, sd, a, B = fit(Xv[:k], yv[:k], [L])
        out.append({"date": t + M1, "y": yv[k], "f": a + ((Xv[k] - mu) / sd) @ B[:, 0], "hm": yv[:k].mean(), "lam": L})
    return pd.DataFrame(out).set_index("date")


def cmp(mine, theirs):
    return {"mine": float(mine), "module": float(theirs), "absdiff": float(abs(mine - theirs))}


# ------------------------------------------------------------------ 1. CV-design sensitivity, incl. B0 and nested B vs B0
cvd_mod = mod("cv_design")
DES = {"recent120": {"recent": 120}, "recent60": {"recent": 60}, "first120": {"first": 120},
       "grid_max1e3": {"grid": GRID[:-1]}}
SPB0 = {**SP}
cvres, worst = {}, 0.0
mine_f = {}
for k, mname in (("A", "A_noVIX_1970"), ("B", "B_full_1990"), ("B0", "B0_noATTN_1990")):
    cols, st, oos = SP[k]
    for dn, kw in DES.items():
        f = walk_y(cols, st, oos, y, **kw)
        mine_f[(k, dn)] = f
        mx = kw.get("grid", GRID).max()
        for per, a in (("full_oos", None), ("post2010", "2010")):
            ff = f if a is None else f.loc[a:]
            r = r2_cw(ff["y"], ff["f"], ff["hm"])
            row = cvd_mod[(cvd_mod["model"] == f"{mname}_ridgecv_{dn}") & (cvd_mod["period"] == per)].iloc[0]
            d = {"share_at_max": cmp((f["lam"] >= mx).mean(), row["share_lambda_at_max"]),
                 "share_le_1": cmp((f["lam"] <= 1).mean(), row["share_lambda_le_1"]),
                 "median_lam": cmp(f["lam"].median(), row["median_lambda"]),
                 "r2": cmp(r[0], row["r2_oos_pct"])}
            # module sets CW t = 0 when degenerate; compare only when non-degenerate
            if not row["degenerate"]:
                d["cw_t"] = cmp(r[1], row["cw_t"])
            cvres[f"{k}_{dn}_{per}"] = d
            worst = max(worst, max(v["absdiff"] for kk, v in d.items() if kk != "median_lam"))
for dn in DES:
    b, b0 = mine_f[("B", dn)], mine_f[("B0", dn)]
    for per, a in (("full_oos", None), ("post2010", "2010")):
        bb, b00 = (b, b0) if a is None else (b.loc[a:], b0.loc[a:])
        r = r2_cw(bb["y"], bb["f"], b00["f"])
        row = cvd_mod[(cvd_mod["model"] == f"B_full_1990_ridgecv_{dn}") & (cvd_mod["benchmark"] != "histmean")
                      & (cvd_mod["period"] == per)].iloc[0]
        d = {"r2": cmp(r[0], row["r2_oos_pct"]), "p1": cmp(r[2], row["cw_p_one_sided"])}
        if not row["degenerate"]:
            d["cw_t"] = cmp(r[1], row["cw_t"])
        cvres[f"BvsB0_{dn}_{per}"] = d
        worst = max(worst, max(v["absdiff"] for v in d.values()))
res["cv_design"] = {"max_absdiff_excl_median": worst, "rows": cvres}
# first120 explanation: B at max post-2010, B0 vs histmean post-2010
f = mine_f[("B", "first120")].loc["2010":]
res["first120_explanation"] = {"B_post2010_share_at_max": float((f["lam"] >= 1e6).mean()),
                               "B_post2010_max_gap_to_hm": float((f["f"] - f["hm"]).abs().max()),
                               "B0_vs_hm_post2010": r2_cw(mine_f[("B0", "first120")].loc["2010":]["y"],
                                                          mine_f[("B0", "first120")].loc["2010":]["f"],
                                                          mine_f[("B0", "first120")].loc["2010":]["hm"])[:3]}

# ------------------------------------------------------------------ 2. team target: Brown-leg FF3 residual (own rebuild)
ff3t = v1.team["ff3"]
bl = (IND[brown].mean(axis=1) - ff3t["RF"].reindex(IND.index)).rename("y")
dd_ = pd.concat([bl, ff3t[["Mkt-RF", "SMB", "HML"]]], axis=1).dropna()
coefs = {}
for end in range(59, len(dd_)):
    smp = dd_.iloc[end - 59:end + 1]
    Xm = np.column_stack([np.ones(60), smp[["Mkt-RF", "SMB", "HML"]].to_numpy()])
    coefs[dd_.index[end]] = np.linalg.lstsq(Xm, smp["y"].to_numpy(), rcond=None)[0]
C = pd.DataFrame(coefs).T.reindex(dd_.index).shift(1)
eps = (dd_["y"] - C[0] - (C[[1, 2, 3]].to_numpy() * dd_[["Mkt-RF", "SMB", "HML"]].to_numpy()).sum(1)).loc[:LAST]
eps_mod = mod("team_brown_residual", index_col=0, parse_dates=True).iloc[:, 0]
res["team_eps_vs_module_maxabs"] = float((eps - eps_mod.reindex(eps.index)).abs().max())
eps_next = eps.shift(-1)
tt = mod("team_target_check")
team = {}
WIN = {"full_oos": (None, None), "post2010": ("2010-01-31", None), "validation": ("2010-01-31", "2022-07-31"),
       "holdout": ("2022-08-31", None)}
for per, a in (("from_1990", "1990-01-31"), ("from_2010", "2010-01-31")):
    z = X["ATTN"].loc[a:"2026-06-30"].dropna()
    b, t, n = nw_reg(eps_next.reindex(z.index), ((z - z.mean()) / z.std()).rename("z").to_frame())
    row = tt[(tt["test"] == "in_sample_slope") & (tt["period"] == per)].iloc[0]
    team[f"IS_{per}"] = {"slope": cmp(100 * b["z"], row["slope_pct_per_sd"]), "t": cmp(t["z"], row["t_nw"]),
                         "n": [n, int(row["n"])]}
fc = {"ATTN_ols": walk_y(["ATTN"], "1990-01-31", "2000-01-31", eps_next, lam=0.0)}
for nm, cols in (("B", B_COLS), ("B0", B0_COLS)):
    fc[f"{nm}_ridgecv"] = walk_y(cols, "1990-01-31", "2000-01-31", eps_next)
    for lam in (0.0, 1.0):
        fc[f"{nm}_fixed{lam:g}"] = walk_y(cols, "1990-01-31", "2000-01-31", eps_next, lam=lam)
res["team_B_ridgecv_share_at_max"] = cmp((fc["B_ridgecv"]["lam"] >= 1e6).mean(),
                                         tt[tt["model"] == "TEAMTGT_B_full_1990_ridgecv"]["share_lambda_at_max"].iloc[0])


def sl(s, w):
    a, b = WIN[w]
    return s.loc[a:b] if (a or b) else s


pairs = [("TEAMTGT_ATTN_ols", "histmean", "ATTN_ols", None), ("TEAMTGT_B_full_1990_ridgecv", "histmean", "B_ridgecv", None)]
pairs += [(f"TEAMTGT_B_full_1990_{k}", f"TEAMTGT_B0_noATTN_1990_{k}", f"B_{k}", f"B0_{k}") for k in ("ridgecv", "fixed0", "fixed1")]
worst = 0.0
for model, bench, mk, bk in pairs:
    for w in WIN:
        fm = sl(fc[mk], w)
        fb = fm["hm"] if bk is None else sl(fc[bk], w)["f"]
        r = r2_cw(fm["y"], fm["f"], fb)
        row = tt[(tt["model"] == model) & (tt["benchmark"] == bench) & (tt["period"] == w)].iloc[0]
        d = {"r2": cmp(r[0], row["r2_oos_pct"]), "n": [r[3], int(row["n"])]}
        if not row["degenerate"]:
            d["cw_t"] = cmp(r[1], row["cw_t"])
            worst = max(worst, d["cw_t"]["absdiff"])
        worst = max(worst, d["r2"]["absdiff"])
        team[f"{model}_vs_{bench}_{w}"] = d
res["team_target"] = {"max_absdiff": worst, "rows": team}

# ------------------------------------------------------------------ 3. portfolios: scaling, risk concentration, prevmean,
# timing FF6 loadings, histmean dates (own timing portfolios from round 1)
fac = v1.fac
FF6 = v1.FF6
sc_mod = mod("scaling_sensitivity")
rc_mod = mod("risk_concentration")
lo_mod = mod("portfolio_ff6_loadings").set_index("strategy")
hs_mod = mod("histmean_sign").set_index("spec")
var60 = v1.var60
port = {}
for k, name, oos in (("A", "A_noVIX_1970", "1990-01-31"), ("B", "B_full_1990", "2000-01-31")):
    f = v1.cv[k]
    vv = var60.reindex(f["origin"]).to_numpy()
    win = (pd.Timestamp(oos), LAST)
    tim = strategy(pd.Series(f["f"].to_numpy() / (5 * vv), f.index), win)
    pm = strategy(pd.Series(f["hm"].to_numpy() / (5 * vv), f.index), win)
    st = strategy(pd.Series(1.0, index=f.index), win)
    mabs = float(tim["w"].abs().mean())
    # static at the timing rule's mean |w| (no vol targeting), with costs
    H = pd.DataFrame({**{i: pd.Series(mabs, index=f.index) / 5 for i in green},
                      **{i: pd.Series(-mabs, index=f.index) / 5 for i in brown}})
    to = turnover(H, IND)
    g_eq = mabs * GB.reindex(f.index)
    st_eq = pd.DataFrame({"gross": g_eq, "net": g_eq - 10e-4 * to.fillna(0)})
    d = {"timing_mean_abs_w": cmp(mabs, sc_mod[(sc_mod["spec"] == name)]["timing_mean_abs_w"].iloc[0])}
    for kind in ("net", "gross"):
        for sname, S in (("equal_vol_5pct", st), ("equal_mean_abs_w", st_eq)):
            dd = tim[kind] - S[kind]
            row = sc_mod[(sc_mod["spec"] == name) & (sc_mod["static_scaling"] == sname) & (sc_mod["returns"] == kind)].iloc[0]
            d[f"{sname}_{kind}_t"] = cmp(nw_mean_t(dd), row["t_nw"])
            d[f"{sname}_{kind}_mean_pct"] = cmp(1200 * dd.mean(), 100 * row["mean_diff_ann"])
    # risk concentration
    for lab, S in (("timing_ridgecv", tim), ("static_long", st)):
        g = S["gross"]
        tot = (g ** 2).sum()
        for _, row in rc_mod[(rc_mod["spec"] == name) & (rc_mod["strategy"] == lab)].iterrows():
            gw = g[(g.index >= pd.Timestamp(row["start"])) & (g.index <= pd.Timestamp(row["end"]) + pd.offsets.MonthEnd(0))]
            d[f"risk_{lab}_{row['window']}_share"] = cmp((gw ** 2).sum() / tot, row["share_sum_sq_gross"])
            d[f"risk_{lab}_{row['window']}_maxabs_signed"] = cmp(gw.loc[gw.abs().idxmax()], row["max_abs_month_signed"])
            d[f"risk_{lab}_{row['window']}_maxabs_date"] = [gw.abs().idxmax().strftime("%Y-%m"), row["max_abs_month_date"]]
            d[f"risk_{lab}_{row['window']}_vol"] = cmp(np.sqrt(12) * gw.std(), row["ann_vol_gross"])
    d["signed_max_month"] = [tim["gross"].idxmax().strftime("%Y-%m"), float(tim["gross"].max())]
    d["signed_min_month"] = [tim["gross"].idxmin().strftime("%Y-%m"), float(tim["gross"].min())]
    # timing vs prevailing mean
    d["max_abs_diff_net_vs_prevmean"] = float((tim["net"] - pm["net"]).abs().max())
    d["cost_drag_bp_timing"] = 1e4 * 12 * 10e-4 * tim["to"].mean()
    d["cost_drag_bp_prevmean"] = 1e4 * 12 * 10e-4 * pm["to"].mean()
    # FF6 loadings of the timing portfolio (new claims) and static R2
    for lab, S in (("timing_ridgecv", tim), ("static_long", st)):
        b, t, n = nw_reg(S["net"], fac.reindex(S.index)[FF6])
        Xf = fac.reindex(S.index)[FF6].dropna()
        yy = S["net"].reindex(Xf.index)
        Xm = np.column_stack([np.ones(len(Xf)), Xf.to_numpy()])
        u = yy.to_numpy() - Xm @ np.linalg.lstsq(Xm, yy.to_numpy(), rcond=None)[0]
        r2 = 1 - (u ** 2).sum() / ((yy - yy.mean()) ** 2).sum()
        mrow = lo_mod.loc[f"{name}:{lab}"]
        d[f"ff6_{lab}_r2"] = cmp(r2, mrow["r2"])
        for c in FF6:
            d[f"ff6_{lab}_{c}_b"] = cmp(b[c], mrow[f"b_{c}"])
            d[f"ff6_{lab}_{c}_t"] = cmp(t[c], mrow[f"t_{c}"])
    # histmean sign dates: first month short and short thereafter
    pos = f["hm"] > 0
    last_pos = f.index[pos].max()
    d["first_month_short"] = [(last_pos + M1).strftime("%Y-%m"), hs_mod.loc[name, "first_month_short_thereafter"]]
    d["short_every_month_after"] = [bool((f.loc[last_pos + M1:, "hm"] < 0).all()),
                                    bool(hs_mod.loc[name, "short_every_month_thereafter"])]
    d["w_negative_every_month_after"] = bool((tim["w"].loc[last_pos + M1:] < 0).all())
    port[name] = d
res["portfolio_r2"] = port
res["portfolio_r2_max_absdiff_numeric"] = max(v["absdiff"] for p in port.values() for v in p.values()
                                              if isinstance(v, dict) and "absdiff" in v)

# ------------------------------------------------------------------ 4. LMN attention increment (own LMN from round 1)
li_mod = mod("lmn_attn_increment")
lmn = {}
for sg, lab in ((True, "lmn_sign"), (False, "lmn_raw")):
    hb = v1.lmn(B_COLS, "1990-01-31", sg)
    hb0 = v1.lmn(B0_COLS, "1990-01-31", sg)
    hb, hb0 = hb.loc["2000-01-31":], hb0.loc["2000-01-31":]
    Sb = strategy(hb, (hb.index.min(), LAST))
    Sb0 = strategy(hb0, (hb0.index.min(), LAST))
    for kind in ("net", "gross"):
        dd = (Sb[kind] - Sb0[kind]).dropna()
        row = li_mod[(li_mod["variant"] == lab) & (li_mod["returns"] == kind)].iloc[0]
        lmn[f"{lab}_{kind}"] = {"mean_pct": cmp(1200 * dd.mean(), 100 * row["mean_diff_ann"]),
                                "t": cmp(nw_mean_t(dd), row["t_nw"]), "n": [len(dd), int(row["n"])],
                                "start": [dd.index.min().strftime("%Y-%m"), row["start"]]}
res["lmn_attn_increment"] = lmn

# ------------------------------------------------------------------ 5. ledger integrity
led = mod("tests_ledger")
L = {}
L["n_rows"] = len(led)
L["counts"] = led["primary_or_exploratory"].value_counts().to_dict()
L["duplicate_ids"] = led.loc[led["test_id"].duplicated(keep=False), "test_id"].tolist()
cw = led["statistic_name"].str.contains("Clark-West")
L["n_cw_rows"] = int(cw.sum())
L["cw_rows_missing_p1"] = int(led.loc[cw, "p_value_one_sided"].isna().sum())
p1_calc = 1 - stats.norm.cdf(led.loc[cw, "statistic"])
L["cw_max_abs_p1_mismatch"] = float((p1_calc - led.loc[cw, "p_value_one_sided"]).abs().max())
L["cw_alternative_values"] = led.loc[cw, "alternative"].value_counts().to_dict()
L["noncw_p1_nonnull"] = int(led.loc[~cw, "p_value_one_sided"].notna().sum())
neg = cw & (led["statistic"] < 0)
L["cw_neg_t_rows"] = int(neg.sum())
L["cw_neg_t_rows_without_WORSE_note"] = int((neg & ~led["note"].fillna("").str.contains("WORSE")).sum())
L["cw_neg_t_p2_lt_0.10"] = int((neg & (led["p_value_two_sided"] < 0.10)).sum())
L["cw_p1_lt_0.05"] = led.loc[cw & (led["p_value_one_sided"] < 0.05), ["test_id", "statistic", "p_value_one_sided",
                                                                         "primary_or_exploratory"]].round(4).to_dict("records")
L["p2_matches_normal_all_rows_maxabs"] = float((2 * (1 - stats.norm.cdf(led["statistic"].abs()))
                                                - led["p_value_two_sided"]).abs().max())
nonnormal = led[(2 * (1 - stats.norm.cdf(led["statistic"].abs())) - led["p_value_two_sided"]).abs() > 1e-6]
L["rows_where_p2_not_normal_p"] = nonnormal[["test_id", "statistic", "p_value_two_sided"]].head(10).round(5).to_dict("records")
L["n_rows_where_p2_not_normal_p"] = len(nonnormal)
L["IS_MCCC_ids"] = led.loc[led["test_id"].str.startswith("IS_univariate_MCCC"), "test_id"].tolist()
L["IS_ids"] = led.loc[led["test_id"].str.startswith("IS_univariate_"), "test_id"].tolist()
L["FF6_rows"] = int(led["test_id"].str.startswith("FF6_").sum())
L["FF6_strategies"] = sorted({t.rsplit("_", 1)[0] for t in led.loc[led["test_id"].str.startswith("FF6_"), "test_id"]})
L["ROT_rows"] = led.loc[led["test_id"].str.startswith("ROT_"), ["test_id", "statistic", "note"]].to_dict("records")
L["LMN_rows"] = led.loc[led["test_id"].str.startswith("LMN_B_minus_B0"), ["test_id", "statistic", "p_value_two_sided",
                                                                           "primary_or_exploratory"]].round(4).to_dict("records")
L["UMD_rot_rows"] = led.loc[led["test_id"].str.contains("rot|ROT|mom", regex=True) & led["test_id"].str.endswith("UMD"),
                            ["test_id", "statistic", "note"]].to_dict("records")
L["meanabsw_rows"] = led.loc[led["test_id"].str.contains("meanabsw"), ["test_id", "statistic"]].round(4).to_dict("records")
L["new_row_family_counts"] = {
    "cv_design": int(led["test_id"].str.contains("recent120|recent60|first120|grid_max1e3").sum()),
    "team_target": int(led["test_id"].str.startswith("TEAMTGT").sum()),
    "meanabsw": int(led["test_id"].str.contains("meanabsw").sum()),
    "lmn_b_minus_b0": int(led["test_id"].str.startswith("LMN_B_minus_B0").sum()),
    "ff6": L["FF6_rows"], "rot": len(L["ROT_rows"])}
res["ledger"] = L


def default(o):
    if isinstance(o, (np.floating, np.integer)):
        return o.item()
    if isinstance(o, (np.bool_,)):
        return bool(o)
    return str(o)


(HERE / "verify_results_r2.json").write_text(json.dumps(res, indent=1, default=default))
print(json.dumps(res, indent=1, default=default))
