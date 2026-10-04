"""M5 industry momentum, made carbon-aware. End-to-end entry point.

Run from the research folder:  uv run python modules/M5_industry_momentum/run.py
Writes outputs/tables/M5_industry_momentum_*.csv/.tex, outputs/figures/M5_industry_momentum_*.pdf/.png and the
tests ledger. Every number in FINDINGS.md comes from one of these tables.
"""
from __future__ import annotations
import sys, pathlib, time
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import numpy as np
import pandas as pd
from m5lib import (C, TABLES, PERIODS, PERIOD_ORDER, DECADES, MODELS, BASE_COST, RET_START, RET_END, F3, nw_ols,
                   load_inputs, factor_frame, mom_signal, rank_weights, backtest, to_holding_index, sl, max_dd,
                   perf_block, alpha_fit, min_obs, ir, paired_boot, carbon_maps, leg_waci, market_waci, formation_dates,
                   LEDGER, ledger_add, save, save_tex, MOD)
import optimizer as OP
import team_replica as TR
from plotstyle import *  # noqa: F401,F403  (SERIES, ENTITY, colors, savefig, plt)
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

T0 = time.time()
def log(msg):
    print(f"[{time.time() - T0:6.1f}s] {msg}", flush=True)

PLABEL = {"full_1970": "Full 1970-01 to 2026-07", "post2010": "Post-2010 (2010-01 to 2026-07)",
          "validation": "Validation 2010-01 to 2022-07", "holdout": "Holdout 2022-08 to 2026-07",
          "pre_covid": "Pre-COVID 2010-01 to 2019-12", "covid": "COVID 2020-01 to 2021-12",
          "inflation_rates": "Inflation/rates 2022-01 to 2024-12", "last18": "Last 18m 2025-02 to 2026-07",
          "last12": "Last 12m 2025-08 to 2026-07"}

# =============================================================================== 0. data and primary book
D = load_inputs(); R, ff5, ff3, cap, emis = D["R"], D["ff5"], D["ff3"], D["cap"], D["emis"]
FAC = {m: factor_frame(m, ff5, ff3) for m in MODELS}
X6 = FAC["FF5+UMD"]
sig = mom_signal(R, 11, 1)
W = rank_weights(sig, R, 8)
bt = backtest(W, R, BASE_COST)
assert bt.index[0] == RET_START and bt.index[-1] == RET_END
n_elig = (sig.loc[W.index].notna() & R.shift(-1).loc[W.index].notna()).sum(axis=1)
save(pd.DataFrame({"n_eligible": n_elig.values}, index=bt.index).join(bt), "returns_monthly")
Wh = to_holding_index(W)
save(Wh, "weights_primary")
log(f"primary book: {len(bt)} months {bt.index[0]:%Y-%m} to {bt.index[-1]:%Y-%m}; eligible industries min {n_elig.min()} max {n_elig.max()}")

# =============================================================================== 1. performance
perf = pd.DataFrame({p: perf_block(bt, p) for p in PERIOD_ORDER}).T
perf.index.name = "period"; save(perf, "perf_periods")
tex = perf[["n", "gross_ret", "net_ret", "vol", "sharpe_net", "max_dd_net", "turnover_ann", "cost_drag_ann"]].copy()
tex.index = [PLABEL[i] for i in tex.index]
tex.columns = ["Months", "Gross ret %", "Net ret %", "Vol %", "Net Sharpe", "Max DD %", "Turnover x/yr", "Cost drag %"]
save_tex(tex, "perf_periods", fmt={"Months": "d"}, pct=("Gross ret %", "Net ret %", "Vol %", "Max DD %", "Cost drag %"))
for p in PERIOD_ORDER:
    d = sl(bt["net"], p); res = nw_ols(d, lags=6)
    ledger_add(f"M5-Q1-mean-{p}", "Q1 primary momentum net mean return", "t_NW6_mean", res.tvalues.iloc[0],
               res.pvalues.iloc[0], len(d), "exploratory", f"mean net return, {PLABEL[p]}")

# decades
drows = {}
for k, per in DECADES.items():
    row = perf_block(bt, per)
    a = alpha_fit(sl(bt["net"], per), X6)
    row.update({"alpha_ff5umd": a["alpha_ann"], "t_alpha_ff5umd": a["t_alpha"], "b_UMD": a["b_UMD"],
                "b_Mkt": a["b_Mkt-RF"], "r2_ff5umd": a["r2"]})
    drows[k] = row
    ledger_add(f"M5-Q1-decade-{k}", "Q1 primary momentum FF5+UMD alpha by decade", "t_NW6_alpha", a["t_alpha"],
               a["p_alpha"], a["n"], "exploratory", f"net returns {per[0][:7]} to {per[1][:7]}")
dec = pd.DataFrame(drows).T; dec.index.name = "decade"; save(dec, "perf_decades")
tex = dec[["n", "net_ret", "vol", "sharpe_net", "max_dd_net", "alpha_ff5umd", "t_alpha_ff5umd", "b_UMD", "turnover_ann"]].copy()
tex.columns = ["Months", "Net ret %", "Vol %", "Net Sharpe", "Max DD %", "FF5+UMD alpha %", "t(alpha)", "UMD beta", "Turnover x/yr"]
save_tex(tex, "perf_decades", fmt={"Months": "d"}, pct=("Net ret %", "Vol %", "Max DD %", "FF5+UMD alpha %"))

# alphas and loadings
arows = []
for series in ("net", "gross"):
    for p in PERIOD_ORDER:
        for m, cols in MODELS.items():
            y = sl(bt[series], p)
            if len(y) < min_obs(m):
                continue
            a = alpha_fit(y, FAC[m]); a.update({"series": series, "period": p, "model": m}); arows.append(a)
            if series == "net":
                primary = (m == "FF5+UMD" and p in ("full_1970", "post2010"))
                tid = {"full_1970": "M5-P1", "post2010": "M5-P2"}.get(p) if primary else f"M5-Q1-alpha-{m}-{p}"
                ledger_add(tid, "Q1 primary momentum alpha (net of 10 bp costs)", f"t_NW6_alpha_{m}", a["t_alpha"],
                           a["p_alpha"], a["n"], "primary" if primary else "exploratory",
                           f"{m} alpha {a['alpha_ann']:.4f}/yr, {PLABEL[p]}" + ("; PRE-REGISTERED PRIMARY" if primary else ""))
alph = pd.DataFrame(arows)
for m, fac in (("FF3", "HML"), ("FF5", "HML"), ("FF5+UMD", "UMD")):       # loadings cited in FINDINGS
    r_ = alph[(alph.series == "net") & (alph.period == "full_1970") & (alph.model == m)].iloc[0]
    ledger_add(f"M5-Q1-loading-{fac}-{m}-full_1970", "Q1 primary momentum factor loading (net)", f"t_NW6_b_{fac}",
               r_[f"t_{fac}"], r_[f"p_{fac}"], r_["n"], "exploratory",
               f"[loading] b_{fac} {r_[f'b_{fac}']:.3f} in {m}, {PLABEL['full_1970']}")
lead = ["series", "period", "model", "n", "alpha_ann", "t_alpha", "p_alpha", "r2", "t_alpha_ols", "p_alpha_ols_t", "df_resid"]
alph = alph[lead + [c for c in alph.columns if c not in lead]]
save(alph, "alphas", index=False)
view = alph[(alph.series == "net") & alph.period.isin(["full_1970", "post2010"])].copy()
bcols = ["b_Mkt-RF", "b_SMB", "b_HML", "b_RMW", "b_CMA", "b_UMD"]
tex = view[["period", "model", "alpha_ann", "t_alpha"] + bcols + ["r2"]].copy()
tex["period"] = tex["period"].map({"full_1970": "Full 1970-2026", "post2010": "Post-2010"})
tex.columns = ["Period", "Model", "Alpha %/yr", "t(alpha)", "Mkt", "SMB", "HML", "RMW", "CMA", "UMD", "R2"]
save_tex(tex, "alphas", index=False, pct=("Alpha %/yr",))
log("performance and alpha tables done")

# cost sensitivity and breakeven
crow = []
for c_bp in (0, 5, 10, 25):
    net = bt["gross"] - c_bp / 1e4 * bt["turnover"]
    for p in ("full_1970", "post2010", "holdout", "last18", "last12"):
        y = sl(net, p)
        row = {"cost_bp": c_bp, "period": p, "n": len(y), "net_ret": 12 * y.mean(), "vol": np.sqrt(12) * y.std(ddof=1),
               "sharpe_net": ir(y.values), "max_dd": max_dd(y)}
        if len(y) >= 24:
            a = alpha_fit(y, X6); row.update({"alpha_ff5umd": a["alpha_ann"], "t_alpha_ff5umd": a["t_alpha"]})
            if c_bp in (0, 5, 25) and p in ("full_1970", "post2010"):
                ledger_add(f"M5-Q1-cost{c_bp}-{p}", "Q1 cost sensitivity", "t_NW6_alpha_FF5UMD", a["t_alpha"], a["p_alpha"],
                           a["n"], "exploratory", ("gross, 0 bp" if c_bp == 0 else f"net of {c_bp} bp") +
                           f"; FF5+UMD alpha {a['alpha_ann']:.4f}/yr, {PLABEL[p]}")
        crow.append(row)
cost_tab = pd.DataFrame(crow)
be = []
for p in ("full_1970", "post2010", "holdout"):
    d = sl(bt, p)
    a0 = alpha_fit(d["gross"], X6)["alpha_ann"]
    a1 = alpha_fit(d["gross"] - 0.01 * d["turnover"], X6)["alpha_ann"]      # alpha linear in cost
    m0 = d["gross"].mean()
    be.append({"period": p, "breakeven_bp_mean": 1e4 * m0 / d["turnover"].mean() if m0 > 0 else np.nan,
               "breakeven_bp_alpha_ff5umd": 1e4 * 0.01 * a0 / (a0 - a1) if a0 > 0 else np.nan,
               "gross_alpha_ff5umd": a0, "avg_monthly_turnover": d["turnover"].mean(),
               "note": "" if a0 > 0 else "gross FF5+UMD alpha is negative: no positive break-even cost exists"})
be = pd.DataFrame(be)
save(cost_tab, "cost_sensitivity", index=False); save(be, "cost_breakeven", index=False)
tex = cost_tab[cost_tab.period.isin(["full_1970", "post2010", "holdout", "last18"])][
    ["cost_bp", "period", "net_ret", "sharpe_net", "alpha_ff5umd", "t_alpha_ff5umd"]].copy()
tex["period"] = tex["period"].map(PLABEL)
tex.columns = ["Cost bp", "Period", "Net ret %", "Net Sharpe", "FF5+UMD alpha %", "t(alpha)"]
save_tex(tex, "cost_sensitivity", index=False, fmt={"Cost bp": "d"}, pct=("Net ret %", "FF5+UMD alpha %"))

# worst months, crash 2009, drawdowns, bear-state behaviour
fac_m = ff5[["Mkt-RF", "HML", "UMD"]]
wm = bt[["net", "long", "short"]].join(fac_m).nsmallest(10, "net")
wm["long_leg"] = [",".join(Wh.loc[d][Wh.loc[d] > 0].index) for d in wm.index]
wm["short_leg"] = [",".join(Wh.loc[d][Wh.loc[d] < 0].index) for d in wm.index]
wm.index = wm.index.strftime("%Y-%m"); wm.index.name = "month"
save(wm, "worst_months")
tex = wm[["net", "long", "short", "Mkt-RF", "UMD"]].copy()
tex.columns = ["Net %", "Long leg %", "Short leg %", "Mkt-RF %", "UMD %"]
save_tex(tex, "worst_months", pct=tuple(tex.columns), digits=1)

cr = bt.loc["2008-09-30":"2009-12-31", ["net", "long", "short"]].join(fac_m)
cr["long_leg"] = [",".join(Wh.loc[d][Wh.loc[d] > 0].index) for d in cr.index]
cr["short_leg"] = [",".join(Wh.loc[d][Wh.loc[d] < 0].index) for d in cr.index]
w3 = slice("2009-03-31", "2009-05-31")
cum = lambda s: float((1 + s).prod() - 1)
summ = pd.DataFrame({"net": [cum(bt.loc[w3, "net"]), cum(bt.loc["2009-01-31":"2009-12-31", "net"])],
                     "long": [cum(bt.loc[w3, "long"]), cum(bt.loc["2009-01-31":"2009-12-31", "long"])],
                     "short": [cum(bt.loc[w3, "short"]), cum(bt.loc["2009-01-31":"2009-12-31", "short"])],
                     "Mkt-RF": [cum(ff5.loc[w3, "Mkt-RF"]), cum(ff5.loc["2009-01-31":"2009-12-31", "Mkt-RF"])],
                     "HML": [cum(ff5.loc[w3, "HML"]), cum(ff5.loc["2009-01-31":"2009-12-31", "HML"])],
                     "UMD": [cum(ff5.loc[w3, "UMD"]), cum(ff5.loc["2009-01-31":"2009-12-31", "UMD"])]},
                    index=pd.Index(["cum_2009-03_to_2009-05", "cum_2009"], name="month"))
cr.index = cr.index.strftime("%Y-%m"); cr.index.name = "month"
cr = pd.concat([cr, summ]); save(cr, "crash_2009")
tex = cr[["net", "long", "short", "Mkt-RF", "UMD"]].copy()
tex.columns = ["Net %", "Long leg %", "Short leg %", "Mkt-RF %", "UMD %"]
save_tex(tex, "crash_2009", pct=tuple(tex.columns), digits=1)

wealth = (1 + bt["net"]).cumprod(); peak = wealth.cummax(); ddser = wealth / peak - 1
eps = []; in_dd = False
for d, v in ddser.items():
    if v < 0 and not in_dd:
        in_dd, pk = True, wealth.loc[:d].iloc[:-1].idxmax() if len(wealth.loc[:d]) > 1 else d
    if in_dd and v == 0:
        seg = ddser.loc[pk:d]; eps.append((pk, seg.idxmin(), d, seg.min())); in_dd = False
if in_dd:
    seg = ddser.loc[pk:]; eps.append((pk, seg.idxmin(), pd.NaT, seg.min()))
dds = pd.DataFrame(eps, columns=["peak", "trough", "recovery", "depth"]).nsmallest(5, "depth")
dds["months_peak_to_trough"] = [(t.year - p.year) * 12 + t.month - p.month for p, t in zip(dds.peak, dds.trough)]
for c in ("peak", "trough", "recovery"):
    dds[c] = dds[c].dt.strftime("%Y-%m")
save(dds, "drawdowns", index=False)

mkt_tot = ff5["Mkt-RF"] + ff5["RF"]
bear = (np.log1p(mkt_tot).rolling(24, min_periods=24).sum() < 0).shift(1)      # known at formation t, applies to t+1
dm_rows, cond_rows = [], []
for nm, y in (("momentum_net", bt["net"]), ("UMD", ff5["UMD"].loc[RET_START:RET_END])):
    d = pd.concat([y.rename("y"), ff5["Mkt-RF"].rename("M"), bear.rename("B")], axis=1, sort=True).dropna()
    d["B"] = d["B"].astype(float); d["U"] = (d["M"] > 0).astype(float)
    Xdm = pd.DataFrame({"B": d["B"], "M": d["M"], "BxM": d["B"] * d["M"], "BxUxM": d["B"] * d["U"] * d["M"]})
    res = nw_ols(d["y"], Xdm, lags=6)
    for k in res.params.index:
        dm_rows.append({"series": nm, "term": k, "coef": res.params[k], "t_nw6": res.tvalues[k], "p": res.pvalues[k], "n": int(res.nobs)})
    ledger_add(f"M5-Q1-DM-{nm}", "Q1 crash risk: bear-market rebound beta (Daniel-Moskowitz)", "t_NW6_BxUxM",
               res.tvalues["BxUxM"], res.pvalues["BxUxM"], int(res.nobs), "exploratory",
               f"{nm}; coef {res.params['BxUxM']:.3f}; bear = past 24m market return < 0 at formation")
    ledger_add(f"M5-Q1-DM-BxM-{nm}", "Q1 crash risk: change in market beta in bear states (Daniel-Moskowitz)", "t_NW6_BxM",
               res.tvalues["BxM"], res.pvalues["BxM"], int(res.nobs), "exploratory",
               f"{nm}; coef {res.params['BxM']:.3f}; bear = past 24m market return < 0 at formation")
    for bstate in (0.0, 1.0):
        for ustate in (0.0, 1.0):
            s = d.loc[(d.B == bstate) & (d.U == ustate), "y"]
            cond_rows.append({"series": nm, "bear_state": int(bstate), "market_up": int(ustate), "n": len(s),
                              "mean_monthly": s.mean(), "vol_monthly": s.std(ddof=1)})
save(pd.DataFrame(dm_rows), "crash_dm_regression", index=False)
save(pd.DataFrame(cond_rows), "crash_conditional_means", index=False)
log("cost, worst months, crash tables done")

# =============================================================================== 2. robustness (exploratory)
cm = carbon_maps(emis, R.columns)
VAR = [("primary_11-1_n8_EW", dict(L=11, S=1, n=8)),
       ("window_1-0", dict(L=1, S=0, n=8)), ("window_6-1", dict(L=6, S=1, n=8)),
       ("window_12-1", dict(L=12, S=1, n=8)), ("no_skip_12-0", dict(L=12, S=0, n=8)),
       ("n5_per_leg", dict(L=11, S=1, n=5)), ("n10_per_leg", dict(L=11, S=1, n=10)),
       ("cap_weighted_legs", dict(L=11, S=1, n=8, cap=True)), ("KF_Aug2026_vintage", dict(L=11, S=1, n=8, kf=True))]
DESC = {"primary_11-1_n8_EW": "months t-11..t-1 at formation t (t-12..t-2 vs holding month), 8 per leg, equal weight",
        "window_1-0": "month t only (no skip)", "window_6-1": "months t-6..t-1", "window_12-1": "months t-12..t-1",
        "no_skip_12-0": "months t-11..t (primary window plus the skipped month)", "n5_per_leg": "5 per leg",
        "n10_per_leg": "10 per leg", "cap_weighted_legs": "legs weighted by nfirms x average firm size at t",
        "KF_Aug2026_vintage": "Ken French Aug-2026 vintage VW returns instead of the team file"}
rob, rob_bt = [], {}
for name, v in VAR:
    Rv = D["R_kf"] if v.get("kf") else R
    s = mom_signal(Rv, v["L"], v["S"])
    Wv = rank_weights(s, Rv, v["n"], cap=cap if v.get("cap") else None)
    assert np.isfinite(Wv.values).all()
    b_ = backtest(Wv, Rv, BASE_COST); rob_bt[name] = b_
    row = {"variant": name, "description": DESC[name]}
    for p in ("full_1970", "post2010", "holdout", "last18"):
        pb = perf_block(b_, p)
        row.update({f"net_ret_{p}": pb["net_ret"], f"sharpe_{p}": pb["sharpe_net"]})
    for p in ("full_1970", "post2010", "holdout"):
        a = alpha_fit(sl(b_["net"], p), X6)
        row.update({f"alpha_{p}": a["alpha_ann"], f"t_alpha_{p}": a["t_alpha"], f"p_alpha_{p}": a["p_alpha"],
                    f"t_alpha_ols_{p}": a["t_alpha_ols"], f"p_alpha_ols_t_{p}": a["p_alpha_ols_t"]})
        if name != "primary_11-1_n8_EW":
            ledger_add(f"M5-Q2-{name}-{p}", "Q2 robustness variant FF5+UMD alpha (net)", "t_NW6_alpha_FF5UMD",
                       a["t_alpha"], a["p_alpha"], a["n"], "exploratory", f"{DESC[name]}; {PLABEL[p]}")
    a = alpha_fit(sl(b_["net"], "full_1970"), X6)
    row.update({"b_UMD_full": a["b_UMD"], "r2_full": a["r2"], "turnover_ann": 12 * b_["turnover"].mean(),
                "corr_with_primary": b_["net"].corr(bt["net"])})
    rob.append(row)
rob = pd.DataFrame(rob); save(rob, "robustness", index=False)

# how the Ken French Aug-2026 vintage differs from the team file (documents the KF robustness row)
dK = (D["R_kf"] - R).loc[:RET_END]
m_diff = dK.abs().max(axis=1); diff_months = m_diff[m_diff > 1e-6]
LASTM = RET_END
w_last = Wh.loc[LASTM]                      # weights held in the final month
changed_last = dK.loc[LASTM][dK.loc[LASTM].abs() > 1e-6]
bk = rob_bt["KF_Aug2026_vintage"]
kfv = pd.DataFrame([{
    "months_differing": len(diff_months), "first_month_differing": diff_months.index.min().strftime("%Y-%m"),
    "last_month_differing": diff_months.index.max().strftime("%Y-%m"), "cells_differing": int((dK.abs() > 1e-6).sum().sum()),
    "max_abs_diff_excl_last_month": float(m_diff.drop(LASTM).max()),
    "month_of_max_excl_last": m_diff.drop(LASTM).idxmax().strftime("%Y-%m"),
    "last_month_industries_differing": len(changed_last), "last_month_max_abs_diff": float(changed_last.abs().max()),
    "last_month_max_industry": changed_last.abs().idxmax(),
    "last_month_changed_in_short_leg": ",".join(c for c in changed_last.index if w_last[c] < 0 and abs(changed_last[c]) > 0.01),
    "last_month_changed_in_long_leg": ",".join(c for c in changed_last.index if w_last[c] > 0 and abs(changed_last[c]) > 0.01),
    "months_with_different_weights": int(((to_holding_index(rank_weights(mom_signal(D["R_kf"], 11, 1), D["R_kf"], 8)) - Wh).abs().sum(axis=1) > 1e-9).sum()),
    "last_month_net_team": float(bt.loc[LASTM, "net"]), "last_month_net_kf": float(bk.loc[LASTM, "net"]),
    "last_month_rank_worst_team": int((bt["net"] < bt.loc[LASTM, "net"]).sum() + 1),
    "last_month_rank_worst_kf": int((bk["net"] < bk.loc[LASTM, "net"]).sum() + 1)}]).T
kfv.columns = ["value"]; kfv.index.name = "item"; save(kfv, "kf_vintage_diff")
chg = changed_last.rename("kf_minus_team").to_frame(); chg.index.name = "industry"
chg["leg_2026_07"] = ["long" if w_last[c] > 0 else ("short" if w_last[c] < 0 else "-") for c in chg.index]
save(chg.sort_values("kf_minus_team"), "kf_vintage_diff_last_month")
tex = rob[["variant", "sharpe_full_1970", "sharpe_post2010", "sharpe_holdout", "alpha_full_1970", "t_alpha_full_1970",
           "alpha_post2010", "t_alpha_post2010", "b_UMD_full", "turnover_ann"]].copy()
tex.columns = ["Variant", "Sharpe full", "Sharpe post-2010", "Sharpe holdout", "Alpha full %", "t", "Alpha post-2010 %", "t ",
               "UMD beta", "Turnover x/yr"]
save_tex(tex, "robustness", index=False, pct=("Alpha full %", "Alpha post-2010 %"))
log("robustness done")

# =============================================================================== 3. carbon
covered, missing, med = cm["covered"], cm["missing"], cm["median"]
top_emit = list(emis.sort_values(ascending=False).index)
top5, top8 = top_emit[:5], top_emit[:8]
hold_dates = bt.index
mw_X = market_waci(cap.shift(0), cm["X"], W.index); mw_X.index = hold_dates
mw_M = market_waci(cap, cm["M"], W.index); mw_M.index = hold_dates
wX, wM = leg_waci(Wh, cm["X"]), leg_waci(Wh, cm["M"])
wmon = pd.concat([wX.add_suffix("_X"), wM.add_suffix("_M"), mw_X.rename("market41_waci_X"), mw_M.rename("market49_waci_M")], axis=1)
save(wmon, "waci_monthly")
crow = []
for p in PERIOD_ORDER:
    d = sl(wmon, p)
    crow.append({"period": p, "n": len(d), "long_waci_X": d.long_waci_X.mean(), "short_waci_X": d.short_waci_X.mean(),
                 "net_waci_X": d.net_waci_X.mean(), "long_cov_X": d.long_cov_X.mean(), "short_cov_X": d.short_cov_X.mean(),
                 "long_waci_M": d.long_waci_M.mean(), "short_waci_M": d.short_waci_M.mean(), "net_waci_M": d.net_waci_M.mean(),
                 "market41_waci": d.market41_waci_X.mean(), "market49_waci_M": d.market49_waci_M.mean(),
                 "long_over_market_X": d.long_waci_X.mean() / d.market41_waci_X.mean(),
                 "share_months_long_above_market_X": float((d.long_waci_X > d.market41_waci_X).mean())})
cw = pd.DataFrame(crow).set_index("period"); save(cw, "carbon_waci")
tex = cw.loc[["full_1970", "post2010", "holdout", "last18", "last12"],
             ["long_waci_X", "short_waci_X", "market41_waci", "long_over_market_X", "share_months_long_above_market_X",
              "long_cov_X", "long_waci_M", "short_waci_M"]].copy()
tex.index = [PLABEL[i] for i in tex.index]
tex.columns = ["Long WACI (X)", "Short WACI (X)", "Market WACI (41)", "Long/market", "Months long>mkt %",
               "Long covered %", "Long WACI (M)", "Short WACI (M)"]
save_tex(tex, "carbon_waci", fmt={c: ".3f" for c in ["Long WACI (X)", "Short WACI (X)", "Market WACI (41)", "Long WACI (M)", "Short WACI (M)"]},
         pct=("Months long>mkt %", "Long covered %"), digits=0)

memb = []
for p in ("full_1970", "post2010"):
    d = sl(Wh, p)
    for c in R.columns:
        memb.append({"period": p, "industry": c, "intensity": emis.get(c, np.nan), "covered": c in emis.index,
                     "pct_long": float((d[c] > 0).mean()), "pct_short": float((d[c] < 0).mean())})
memb = pd.DataFrame(memb); save(memb, "membership", index=False)
gset, bset = C.legs_by_emissions(5)
gbexp = pd.DataFrame({"w_green5": Wh[gset].sum(axis=1), "w_brown5": Wh[bset].sum(axis=1)})
gbexp["net_green_minus_brown"] = gbexp.w_green5 - gbexp.w_brown5
save(gbexp, "gb_weight_exposure")

# carbon screens (equal weight, 10 bp)
all_ind = list(R.columns)
SCR = {"A0X_long_covered_only": (covered, None), "A5X_long_excl_top5": ([c for c in covered if c not in top5], None),
       "A8X_long_excl_top8": ([c for c in covered if c not in top8], None),
       "B0X_both_covered_only": (covered, covered), "B5X_both_excl_top5": ([c for c in covered if c not in top5],) * 2,
       "B8X_both_excl_top8": ([c for c in covered if c not in top8],) * 2,
       "A5M_long_excl_top5": ([c for c in all_ind if c not in top5], None), "A8M_long_excl_top8": ([c for c in all_ind if c not in top8], None),
       "B5M_both_excl_top5": ([c for c in all_ind if c not in top5],) * 2, "B8M_both_excl_top8": ([c for c in all_ind if c not in top8],) * 2}
scr_rows, scr_bt, scr_W = [], {"primary": bt}, {"primary": Wh}
for name, (lu, su) in {"primary": (None, None), **SCR}.items():
    if name != "primary":
        Ws = rank_weights(sig, R, 8, long_universe=lu, short_universe=su)
        scr_bt[name] = backtest(Ws, R, BASE_COST); scr_W[name] = to_holding_index(Ws)
    b_, w_ = scr_bt[name], scr_W[name]
    wx, wm_ = leg_waci(w_, cm["X"]), leg_waci(w_, cm["M"])
    row = {"book": name, "convention": "X" if name[2:3] == "X" else ("M" if name[2:3] == "M" else "-")}
    for p in ("full_1970", "post2010", "holdout", "last18"):
        pb = perf_block(b_, p); row.update({f"net_ret_{p}": pb["net_ret"], f"sharpe_{p}": pb["sharpe_net"]})
    for p in ("full_1970", "post2010"):
        a = alpha_fit(sl(b_["net"], p), X6); row.update({f"alpha_{p}": a["alpha_ann"], f"t_alpha_{p}": a["t_alpha"]})
        if name != "primary":                       # primary book's alphas are P1/P2 already
            ledger_add(f"M5-Q3-screen-{name}-alpha-{p}", "Q3 carbon-screened momentum book FF5+UMD alpha (net)",
                       "t_NW6_alpha_FF5UMD", a["t_alpha"], a["p_alpha"], a["n"], "exploratory",
                       f"{name}; alpha {a['alpha_ann']:.4f}/yr, {PLABEL[p]}")
    row.update({"turnover_ann": 12 * b_["turnover"].mean(), "vol_full": np.sqrt(12) * b_["net"].std(ddof=1),
                "long_waci_X": wx.long_waci.mean(), "short_waci_X": wx.short_waci.mean(), "long_cov_X": wx.long_cov.mean(),
                "long_waci_M": wm_.long_waci.mean(), "short_waci_M": wm_.short_waci.mean(),
                "long_waci_X_post2010": sl(wx.long_waci, "post2010").mean()})
    if name != "primary":
        pbt = paired_boot(b_["net"], bt["net"], X6)
        dres = nw_ols(b_["net"] - bt["net"], X6, lags=6)
        row.update({"d_sharpe_vs_primary": pbt["d_ir"], "d_sharpe_lo": pbt["d_ir_lo"], "d_sharpe_hi": pbt["d_ir_hi"],
                    "p_d_sharpe_boot": pbt["p_d_ir"], "d_alpha_vs_primary": 12 * dres.params["const"],
                    "t_d_alpha_nw6": dres.tvalues["const"], "p_d_alpha_boot": pbt["p_d_alpha_boot"]})
        ledger_add(f"M5-Q3-screen-{name}-dIR", "Q3 carbon screen vs primary: difference in net Sharpe", "d_sharpe_boot",
                   pbt["d_ir"], pbt["p_d_ir"], pbt["n"], "exploratory", "paired circular block bootstrap, block 12, B 5000, full sample")
        ledger_add(f"M5-Q3-screen-{name}-dalpha", "Q3 carbon screen vs primary: difference in FF5+UMD alpha", "t_NW6_d_alpha",
                   dres.tvalues["const"], dres.pvalues["const"], int(dres.nobs), "exploratory", "alpha of (screen - primary) net returns")
        # same comparison post-2010 (the brief's window; Sharpe gaps are larger there)
        y1, y0 = sl(b_["net"], "post2010"), sl(bt["net"], "post2010")
        pbp = paired_boot(y1, y0, X6); dresp = nw_ols(y1 - y0, X6, lags=6)
        row.update({"d_sharpe_post2010": pbp["d_ir"], "d_sharpe_lo_post2010": pbp["d_ir_lo"], "d_sharpe_hi_post2010": pbp["d_ir_hi"],
                    "p_d_sharpe_boot_post2010": pbp["p_d_ir"], "d_alpha_post2010": 12 * dresp.params["const"],
                    "t_d_alpha_nw6_post2010": dresp.tvalues["const"], "p_d_alpha_boot_post2010": pbp["p_d_alpha_boot"]})
        ledger_add(f"M5-Q3-screen-{name}-dIR-post2010", "Q3 carbon screen vs primary: difference in net Sharpe", "d_sharpe_boot",
                   pbp["d_ir"], pbp["p_d_ir"], pbp["n"], "exploratory", "paired circular block bootstrap, block 12, B 5000, post-2010")
        ledger_add(f"M5-Q3-screen-{name}-dalpha-post2010", "Q3 carbon screen vs primary: difference in FF5+UMD alpha",
                   "t_NW6_d_alpha", dresp.tvalues["const"], dresp.pvalues["const"], int(dresp.nobs), "exploratory",
                   "alpha of (screen - primary) net returns, post-2010")
    scr_rows.append(row)
scr = pd.DataFrame(scr_rows); save(scr, "carbon_screens", index=False)
tex = scr[["book", "sharpe_full_1970", "sharpe_post2010", "sharpe_holdout", "alpha_full_1970", "t_alpha_full_1970",
           "long_waci_X", "short_waci_X", "d_sharpe_vs_primary", "p_d_sharpe_boot", "d_sharpe_post2010", "p_d_sharpe_boot_post2010"]].copy()
tex.columns = ["Book", "Sharpe full", "Sharpe post-2010", "Sharpe holdout", "Alpha full %", "t", "Long WACI (X)",
               "Short WACI (X)", "dSharpe full", "p boot full", "dSharpe post-2010", "p boot post-2010"]
save_tex(tex, "carbon_screens", index=False, pct=("Alpha full %",),
         fmt={"Long WACI (X)": ".3f", "Short WACI (X)": ".3f", "p boot full": ".3f", "p boot post-2010": ".3f"})
log("carbon WACI and screens done")

# Grinold-Kahn optimizer frontier
BGRID = [None, 1.0, 0.5, 0.25, 0.0, -0.25, -0.5, -0.75, -1.0, -1.25, -1.5, -2.0]
opt_ret, fr_rows, opt_paths = {}, [], {}
for conv, univ in (("X", covered), ("M", all_ind)):
    pre = OP.precompute(R, ff5, sig, univ, cm[conv], W.index)
    for b in BGRID:
        out, H = OP.run_path(pre, R, cm[conv], 1e3 if b is None else b, kappa=BASE_COST, cost=BASE_COST)
        key = f"{conv}_{'unc' if b is None else f'b{b:+.2f}'}"
        opt_paths[key] = out; opt_ret[key] = out["net"]
        row = {"key": key, "convention": conv, "b": np.nan if b is None else b}
        for p in ("full_1970", "post2010", "holdout", "last18"):
            y = sl(out["net"], p); row[f"ir_{p}"] = ir(y.values)
        a = alpha_fit(out["net"], X6); ap = alpha_fit(sl(out["net"], "post2010"), X6)
        row.update({"net_ret_full": 12 * out["net"].mean(), "vol_full": np.sqrt(12) * out["net"].std(ddof=1),
                    "alpha_full": a["alpha_ann"], "t_alpha_full": a["t_alpha"], "b_UMD_full": a["b_UMD"],
                    "alpha_post2010": ap["alpha_ann"], "t_alpha_post2010": ap["t_alpha"],
                    "turnover_ann": 12 * out["turnover"].mean(), "cost_drag_ann": 12 * out["cost"].mean(),
                    "exante_te_ann": out["exante_te_ann"].mean(), "cz_exposure_mean": out["cz_exposure"].mean(),
                    "long_waci": out["long_waci"].mean(), "short_waci": out["short_waci"].mean(),
                    "net_intensity_per_long": out["net_intensity_per_long"].mean(),
                    "long_waci_post2010": sl(out["long_waci"], "post2010").mean(),
                    "binding_share": float(out["binding"].mean()) if b is not None else 0.0,
                    "fallback_months": int(out["fallback"].sum()), "inaccurate_months": int(out["inaccurate"].sum()),
                    "gross_long_mean": out["gross_long"].mean(), "max_dd_full": max_dd(out["net"]),
                    "ret_2009_04": float(out.loc["2009-04-30", "net"])})
        for pp, aa in (("full_1970", a), ("post2010", ap)):
            ledger_add(f"M5-Q3-optalpha-{key}-{pp}", "Q3 GK optimizer book FF5+UMD alpha (net)", "t_NW6_alpha_FF5UMD",
                       aa["t_alpha"], aa["p_alpha"], aa["n"], "exploratory", f"optimizer {key}, {PLABEL[pp]}")
        fr_rows.append(row)
        log(f"optimizer {key}: IR {row['ir_full_1970']:.3f} long WACI {row['long_waci']:.3f} fallback {row['fallback_months']}")
fr = pd.DataFrame(fr_rows); save(fr, "optimizer_frontier", index=False)
save(pd.DataFrame(opt_ret), "optimizer_returns_monthly")
save(pd.concat({k: v[["gross", "net", "turnover", "cz_exposure", "long_waci", "short_waci", "exante_te_ann", "binding", "fallback", "inaccurate"]]
                for k, v in opt_paths.items()}, axis=1), "optimizer_paths_monthly")
tex = fr[["convention", "b", "ir_full_1970", "ir_post2010", "ir_holdout", "alpha_full", "t_alpha_full", "cz_exposure_mean",
          "long_waci", "short_waci", "binding_share", "turnover_ann"]].copy()
tex["b"] = tex["b"].map(lambda v: "none" if pd.isna(v) else f"{v:+.2f}")
tex.columns = ["Conv.", "Bound b", "IR full", "IR post-2010", "IR holdout", "Alpha full %", "t", "Mean c'h", "Long WACI",
               "Short WACI", "Binding %", "Turnover x/yr"]
save_tex(tex, "optimizer_frontier", index=False, pct=("Alpha full %", "Binding %"),
         fmt={"Long WACI": ".3f", "Short WACI": ".3f"})

# selected optimizer books by period (exploratory): is the optimizer alpha stable across subperiods?
OPT_SHOW = ["X_unc", "X_b+0.00", "X_b-1.00", "M_unc", "M_b+0.00"]
op_rows = []
for key in OPT_SHOW:
    out = opt_paths[key]
    for p in list(PERIOD_ORDER) + list(DECADES):
        per = DECADES.get(p, p)
        y = sl(out["net"], per)
        row = {"key": key, "period": p, "n": len(y), "net_ret": 12 * y.mean(), "vol": np.sqrt(12) * y.std(ddof=1),
               "ir": ir(y.values), "max_dd": max_dd(y), "turnover_ann": 12 * sl(out["turnover"], per).mean(),
               "long_waci": sl(out["long_waci"], per).mean()}
        if len(y) >= 24:
            a = alpha_fit(y, X6)
            row.update({"alpha_ff5umd": a["alpha_ann"], "t_alpha": a["t_alpha"], "p_alpha": a["p_alpha"], "b_UMD": a["b_UMD"],
                        "b_Mkt": a["b_Mkt-RF"], "r2": a["r2"]})
            if p not in ("full_1970", "post2010"):
                ledger_add(f"M5-Q3-optalpha-{key}-{p}", "Q3 GK optimizer book FF5+UMD alpha by period (net)", "t_NW6_alpha_FF5UMD",
                           a["t_alpha"], a["p_alpha"], a["n"], "exploratory", f"optimizer {key}, {p}")
        g25 = sl(out["gross"] - 0.0025 * out["turnover"], per)
        row["ir_25bp_fixed_path"] = ir(g25.values)
        op_rows.append(row)
opp = pd.DataFrame(op_rows); save(opp, "optimizer_periods", index=False)
tex = opp[opp.key.isin(["X_unc", "X_b+0.00", "X_b-1.00"]) & opp.period.isin(["full_1970", "post2010", "validation", "holdout", "last18", "last12"] + list(DECADES))][
    ["key", "period", "n", "net_ret", "vol", "ir", "alpha_ff5umd", "t_alpha", "b_UMD", "max_dd"]].copy()
tex["period"] = tex["period"].map(lambda v: PLABEL.get(v, v))
tex.columns = ["Book", "Period", "Months", "Net ret %", "Vol %", "IR", "FF5+UMD alpha %", "t", "UMD beta", "Max DD %"]
save_tex(tex, "optimizer_periods", index=False, fmt={"Months": "d"}, pct=("Net ret %", "Vol %", "FF5+UMD alpha %", "Max DD %"))
ovp = []
for p in ("full_1970", "post2010"):
    y1, y0 = sl(opt_ret["X_unc"], p), sl(bt["net"], p)
    pb_eo = paired_boot(y1, y0, X6)
    ovp.append({"comparison": "X_unc optimizer minus primary EW (net)", "period": p, "ir_optimizer": ir(y1.values),
                "ir_primary": ir(y0.values), **pb_eo})
    ledger_add("M5-Q3-opt-vs-primary-dIR" + ("" if p == "full_1970" else f"-{p}"),
               "Q3 unconstrained GK optimizer vs primary equal-weight book: net IR difference", "d_IR_boot",
               pb_eo["d_ir"], pb_eo["p_d_ir"], pb_eo["n"], "exploratory", f"paired circular block bootstrap, block 12, B 5000, {PLABEL[p]}")
save(pd.DataFrame(ovp), "optimizer_vs_primary", index=False)

# cost of the carbon constraint: paired block bootstrap vs the unconstrained optimizer
ct_rows = []
for conv in ("X", "M"):
    base = opt_ret[f"{conv}_unc"]
    for b in BGRID[1:]:
        key = f"{conv}_b{b:+.2f}"
        for p in ("full_1970", "post2010"):
            y1, y0 = sl(opt_ret[key], p), sl(base, p)
            pbt = paired_boot(y1, y0, X6)
            dres = nw_ols(y1 - y0, X6, lags=6)
            primary = (conv == "X" and b == 0.0 and p == "full_1970")
            ct_rows.append({"convention": conv, "b": b, "period": p, "n": pbt["n"], "ir_constrained": ir(y1.values),
                            "ir_unconstrained": ir(y0.values), "d_ir": pbt["d_ir"], "d_ir_lo": pbt["d_ir_lo"],
                            "d_ir_hi": pbt["d_ir_hi"], "p_d_ir_boot": pbt["p_d_ir"], "d_alpha": pbt["d_alpha"],
                            "d_alpha_lo": pbt["d_alpha_lo"], "d_alpha_hi": pbt["d_alpha_hi"], "p_d_alpha_boot": pbt["p_d_alpha_boot"],
                            "t_d_alpha_nw6": dres.tvalues["const"], "p_d_alpha_nw6": dres.pvalues["const"],
                            "long_waci_constrained": sl(opt_paths[key]["long_waci"], p).mean(),
                            "long_waci_unconstrained": sl(opt_paths[f"{conv}_unc"]["long_waci"], p).mean(),
                            "primary": primary})
            ledger_add("M5-Q3-PRIMARY" if primary else f"M5-Q3-opt-{key}-{p}-dIR",
                       "Q3 cost of carbon constraint: net IR(b) - IR(unconstrained), GK optimizer", "d_IR_boot",
                       pbt["d_ir"], pbt["p_d_ir"], pbt["n"], "primary" if primary else "exploratory",
                       f"convention {conv}, b={b:+.2f}, {PLABEL[p]}; paired circular block bootstrap block 12 B 5000" +
                       ("; PRE-REGISTERED PRIMARY" if primary else ""))
            ledger_add(f"M5-Q3-opt-{key}-{p}-dalpha", "Q3 cost of carbon constraint: FF5+UMD alpha difference", "t_NW6_d_alpha",
                       dres.tvalues["const"], dres.pvalues["const"], int(dres.nobs), "exploratory",
                       f"convention {conv}, b={b:+.2f}, {PLABEL[p]}")
ct = pd.DataFrame(ct_rows)
ct["long_waci_change_pct"] = ct.long_waci_constrained / ct.long_waci_unconstrained - 1
save(ct, "carbon_cost_test", index=False)
tex = ct[(ct.period == "full_1970")][["convention", "b", "ir_constrained", "d_ir", "d_ir_lo", "d_ir_hi", "p_d_ir_boot",
                                      "d_alpha", "t_d_alpha_nw6", "long_waci_change_pct"]].copy()
tex.columns = ["Conv.", "Bound b", "IR", "dIR", "dIR 2.5%", "dIR 97.5%", "p boot", "dAlpha %", "t NW", "Long WACI chg %"]
save_tex(tex, "carbon_cost_test", index=False, pct=("dAlpha %", "Long WACI chg %"), fmt={"Bound b": "+.2f", "p boot": ".3f"})
log("carbon cost tests done")

# realized IC of the momentum signal (check on the IC = 0.05 assumption)
nxt = R.shift(-1)
ic_rows = []
for t in W.index:
    s, r = sig.loc[t], nxt.loc[t]
    m = s.notna() & r.notna()
    ic_rows.append({"date": t + pd.offsets.MonthEnd(1), "rank_ic": s[m].rank().corr(r[m].rank()), "pearson_ic": s[m].corr(r[m])})
ics = pd.DataFrame(ic_rows).set_index("date")
icr = []
for p in ("full_1970", "post2010", "holdout", "last18"):
    for c in ("rank_ic", "pearson_ic"):
        y = sl(ics[c], p); res = nw_ols(y, lags=6)
        icr.append({"period": p, "measure": c, "mean_ic": y.mean(), "t_nw6": res.tvalues.iloc[0], "p": res.pvalues.iloc[0], "n": len(y)})
        if c == "rank_ic":
            ledger_add(f"M5-Q3-IC-{p}", "Realized cross-sectional rank IC of the 11-1 signal", "t_NW6_mean_IC",
                       res.tvalues.iloc[0], res.pvalues.iloc[0], len(y), "exploratory", f"{PLABEL[p]}; optimizer assumes IC=0.05")
save(pd.DataFrame(icr), "realized_ic", index=False)

# =============================================================================== 4. link to green-minus-brown
team = D["team"]
TRp = TR.build(team, gset, bset)
TRl = TR.build(team, gset, bset, att_lag=1)      # timing check: EMV for month t-1 used at the end of month t
GB = TRp["GB"]
# replica check against the team's own published comparison table (read-only file in the team clone)
tc = pd.read_csv(C.TEAM / "outputs" / "tables" / "comparison_table.csv").drop_duplicates("strategy").set_index("strategy")
rc = []
for k, lab in (("short_brown_h3", "Original | Short Brown hold 3m"), ("short_brown_h6", "Original | Short Brown hold 6m")):
    for lag, src in ((0, TRp), (1, TRl)):
        y = sl(src[k], "post2010")
        rc.append({"strategy": lab, "attention_lag": lag, "n": len(y), "ann_return_replica": 12 * y.mean(),
                   "ann_vol_replica": np.sqrt(12) * y.std(ddof=1),
                   "ann_return_team_table": tc.loc[lab, "ann_return_full"] if lag == 0 else np.nan,
                   "ann_vol_team_table": tc.loc[lab, "ann_vol_full"] if lag == 0 else np.nan})
rc = pd.DataFrame(rc); rc["abs_diff_return"] = (rc.ann_return_replica - rc.ann_return_team_table).abs()
save(rc, "team_replica_check", index=False)
mom_g = bt["gross"].rename("INDMOM"); umd = ff5["UMD"]
cor_rows = []
for p in ("full_1970", "post2010", "validation", "holdout"):
    d = sl(pd.concat([GB, mom_g, umd, TRp["brown_eps"], TRp["short_brown_h3"], TRp["short_brown_h6"]], axis=1), p)
    for a_, b_ in (("GB", "INDMOM"), ("GB", "UMD"), ("INDMOM", "UMD"), ("brown_eps", "INDMOM"),
                   ("short_brown_h3", "INDMOM"), ("short_brown_h6", "INDMOM")):
        if a_.startswith("short_brown") and p == "full_1970":
            continue                      # team strategy is structurally zero before its attention signal exists
        dd = d[[a_, b_]].dropna()
        if len(dd) < 24:
            continue
        z = (dd - dd.mean()) / dd.std(ddof=1); res = nw_ols(z[a_], z[[b_]], lags=6)
        cor_rows.append({"period": p, "x": a_, "y": b_, "n": len(dd), "corr": dd[a_].corr(dd[b_]),
                         "t_nw6": res.tvalues[b_], "p": res.pvalues[b_]})
        ledger_add(f"M5-Q4-corr-{a_}-{b_}-{p}", "Q4 correlation with industry momentum / UMD", "t_NW6_corr",
                   res.tvalues[b_], res.pvalues[b_], len(dd), "exploratory", f"corr({a_},{b_}) {PLABEL[p]}")
cor = pd.DataFrame(cor_rows); save(cor, "gb_correlations", index=False)

SPECS = {"FF3": F3, "FF3+UMD": F3 + ["UMD"], "FF3+INDMOM": F3 + ["INDMOM"], "FF3+UMD+INDMOM": F3 + ["UMD", "INDMOM"],
         "FF5+UMD": ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "UMD"], "FF5+UMD+INDMOM": ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "UMD", "INDMOM"]}
F3df = ff3[F3].join(ff5[["RMW", "CMA", "UMD"]]).join(mom_g)
# FF5 columns: use the 5-factor file's SMB for FF5 specs
F5df = ff5[["Mkt-RF", "SMB", "HML", "RMW", "CMA", "UMD"]].join(mom_g)
reg_rows = []
for yname, y, periods in (("GB", GB, ("full_1970", "post2010", "validation", "holdout")),
                          ("brown_eps", TRp["brown_eps"], ("post2010",)),
                          ("short_brown_h3", TRp["short_brown_h3"], ("post2010",)),
                          ("short_brown_h6", TRp["short_brown_h6"], ("post2010",)),
                          ("short_brown_h3_attlag1", TRl["short_brown_h3"], ("post2010",)),
                          ("short_brown_h6_attlag1", TRl["short_brown_h6"], ("post2010",))):
    for p in periods:
        for spec, cols in SPECS.items():
            Xs = (F5df if spec.startswith("FF5") else F3df)[cols]
            yy = sl(y, p)
            a = alpha_fit(yy, Xs.loc[yy.index])
            a.update({"y": yname, "period": p, "spec": spec}); reg_rows.append(a)
            primary = (yname == "GB" and p == "full_1970" and spec == "FF3+INDMOM")
            if "INDMOM" in cols:
                ledger_add("M5-Q4-PRIMARY" if primary else f"M5-Q4-{yname}-{spec}-{p}",
                           "Q4 loading of green-minus-brown (or team strategy) on industry momentum", "t_NW6_b_INDMOM",
                           a["t_INDMOM"], a["p_INDMOM"], a["n"],
                           "primary" if primary else "exploratory",
                           f"y={yname}, spec {spec}, {PLABEL[p]}" + ("; PRE-REGISTERED PRIMARY" if primary else ""))
reg = pd.DataFrame(reg_rows)
lead = ["y", "period", "spec", "n", "alpha_ann", "t_alpha", "r2"]
reg = reg[lead + [c for c in reg.columns if c not in lead and c != "p_alpha"] + ["p_alpha"]]
save(reg, "gb_regressions", index=False)
# how much of the HML loading does industry momentum (or UMD) absorb?
hml_rows = []
for (yname, p), g in reg.groupby(["y", "period"], sort=False):
    g = g.set_index("spec")
    h0 = g.loc["FF3", "b_HML"]
    hml_rows.append({"y": yname, "period": p, "hml_ff3": h0, "t_hml_ff3": g.loc["FF3", "t_HML"],
                     "hml_ff3_indmom": g.loc["FF3+INDMOM", "b_HML"], "t_hml_ff3_indmom": g.loc["FF3+INDMOM", "t_HML"],
                     "hml_ff3_umd": g.loc["FF3+UMD", "b_HML"], "t_hml_ff3_umd": g.loc["FF3+UMD", "t_HML"],
                     "pct_hml_absorbed_by_indmom": 1 - g.loc["FF3+INDMOM", "b_HML"] / h0,
                     "pct_hml_absorbed_by_umd": 1 - g.loc["FF3+UMD", "b_HML"] / h0,
                     "r2_ff3": g.loc["FF3", "r2"], "r2_ff3_indmom": g.loc["FF3+INDMOM", "r2"],
                     "b_indmom_ff3_indmom": g.loc["FF3+INDMOM", "b_INDMOM"], "t_indmom_ff3_indmom": g.loc["FF3+INDMOM", "t_INDMOM"],
                     "t_indmom_ff3_umd_indmom": g.loc["FF3+UMD+INDMOM", "t_INDMOM"],
                     "hml_ff3_umd_indmom": g.loc["FF3+UMD+INDMOM", "b_HML"],
                     "pct_hml_absorbed_by_umd_and_indmom": 1 - g.loc["FF3+UMD+INDMOM", "b_HML"] / h0})
    for spec in ("FF3", "FF3+INDMOM", "FF3+UMD"):          # HML loadings cited in FINDINGS
        ledger_add(f"M5-Q4-loading-HML-{yname}-{spec}-{p}", "Q4 HML loading of green-minus-brown (or team strategy)",
                   "t_NW6_b_HML", g.loc[spec, "t_HML"], g.loc[spec, "p_HML"], g.loc[spec, "n"], "exploratory",
                   f"[loading] b_HML {g.loc[spec, 'b_HML']:.3f}; y={yname}, spec {spec}, {PLABEL[p]}")
save(pd.DataFrame(hml_rows), "gb_hml_attribution", index=False)
tex = reg[(reg.period.isin(["full_1970", "post2010"])) & (reg.y.isin(["GB", "short_brown_h3", "short_brown_h6"]))][
    ["y", "period", "spec", "alpha_ann", "t_alpha", "b_HML", "t_HML", "b_UMD", "t_UMD", "b_INDMOM", "t_INDMOM", "r2"]].copy()
tex["period"] = tex["period"].map({"full_1970": "1970-2026", "post2010": "2010-2026"})
tex.columns = ["Series", "Period", "Spec", "Alpha %", "t(a)", "HML", "t(HML)", "UMD", "t(UMD)", "INDMOM", "t(INDMOM)", "R2"]
save_tex(tex, "gb_regressions", index=False, pct=("Alpha %",))

# does GB itself trend? (time-series momentum of the green-minus-brown spread)
gsig = mom_signal(GB.to_frame(), 11, 1)["GB"]
d = pd.concat([GB.rename("y"), gsig.shift(1).rename("gb_11_1")], axis=1).loc[RET_START:RET_END].dropna()
res = nw_ols(d["y"], d[["gb_11_1"]], lags=6)
tsm = pd.DataFrame([{"n": int(res.nobs), "slope": res.params["gb_11_1"], "t_nw6": res.tvalues["gb_11_1"],
                     "p": res.pvalues["gb_11_1"], "r2": res.rsquared}])
save(tsm, "gb_tsmom", index=False)
ledger_add("M5-Q4-GB-tsmom", "Q4 does the green-minus-brown spread have time-series momentum", "t_NW6_slope",
           res.tvalues["gb_11_1"], res.pvalues["gb_11_1"], int(res.nobs), "exploratory", "GB_{t+1} on GB 11-1 cumulative return at t, 1970-2026")
gexp = []
for p in ("full_1970", "post2010", "validation", "holdout"):
    d = sl(gbexp, p)
    gexp.append({"period": p, "mean_w_green5": d.w_green5.mean(), "mean_w_brown5": d.w_brown5.mean(),
                 "mean_net_green_minus_brown": d.net_green_minus_brown.mean(),
                 "share_months_brown_in_long": float((sl(Wh[bset], p) > 0).any(axis=1).mean()),
                 "share_months_brown_in_short": float((sl(Wh[bset], p) < 0).any(axis=1).mean()),
                 "corr_exposure_with_next_GB": d.net_green_minus_brown.corr(GB.reindex(d.index))})
save(pd.DataFrame(gexp), "gb_exposure_summary", index=False)
log("GB link done")

# =============================================================================== figures
def plain_log(ax, subs=(1, 2, 5)):
    ax.yaxis.set_major_locator(mtick.LogLocator(base=10, subs=subs))
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: f"{v:g}"))
    ax.yaxis.set_minor_formatter(mtick.NullFormatter())


def rolling_alpha(y, X, win=36):
    d = pd.concat([y.rename("y"), X], axis=1, sort=True).dropna(); out = []
    for e in range(win - 1, len(d)):
        s = d.iloc[e - win + 1:e + 1]; r_ = nw_ols(s["y"], s[X.columns], lags=6)
        out.append((d.index[e], 12 * r_.params["const"], 12 * r_.bse["const"]))
    return pd.DataFrame(out, columns=["date", "alpha", "se"]).set_index("date")

ra_p = rolling_alpha(bt["net"], X6); ra_s = rolling_alpha(scr_bt["A8X_long_excl_top8"]["net"], X6)
save(ra_p.add_prefix("primary_").join(ra_s.add_prefix("A8X_")), "rolling_alpha")

fig, axes = plt.subplots(2, 1, figsize=(7.2, 6.4), sharex=True)
ax = axes[0]
for k, lab, col in (("primary", "Primary 11-1, 8/8 equal weight", ENTITY["momentum"]),
                    ("A8X_long_excl_top8", "Long leg excludes 8 highest emitters (and 8 uncovered)", ENTITY["carbon_constrained"]),
                    ("B8X_both_excl_top8", "Both legs exclude 8 highest emitters (and 8 uncovered)", VIOLET)):
    ax.plot((1 + scr_bt[k]["net"]).cumprod(), color=col, label=lab)
ax.set_yscale("log"); plain_log(ax); ax.set_ylabel("Growth of $1, net of 10 bp (log)"); ax.set_title("A. Equal-weight momentum books")
ax.legend(loc="upper left")
ax = axes[1]
for k, lab, col in (("X_unc", "Optimizer, no carbon bound", ENTITY["momentum"]),
                    ("X_b+0.00", "Optimizer, net carbon exposure <= 0", ENTITY["carbon_constrained"]),
                    ("X_b-1.00", "Optimizer, net carbon exposure <= -1", VIOLET)):
    ax.plot((1 + opt_ret[k]).cumprod(), color=col, label=lab)
ax.set_yscale("log"); plain_log(ax); ax.set_ylabel("Growth of $1, net of 10 bp (log)")
ax.set_title("B. Grinold-Kahn optimizer, 5% ex-ante tracking volatility (41 covered industries)")
ax.legend(loc="upper left")
savefig(fig, f"{MOD}_cumulative")

fig, axes = plt.subplots(1, 2, figsize=(8.6, 3.8))
for conv, col, lab in (("X", ENTITY["momentum"], "Optimizer, 41 covered industries"),
                       ("M", VIOLET, "Optimizer, 49 industries (median fill)")):
    f = fr[fr.convention == conv].sort_values("cz_exposure_mean")
    axes[0].plot(f["cz_exposure_mean"], f["ir_full_1970"], marker="o", color=col, label=lab)
    axes[1].plot(f["long_waci"], f["ir_full_1970"], marker="o", color=col, label=lab)
    u = f[f.b.isna()]
    axes[0].scatter(u["cz_exposure_mean"], u["ir_full_1970"], s=70, facecolors="none", edgecolors=INK, zorder=5)
    axes[1].scatter(u["long_waci"], u["ir_full_1970"], s=70, facecolors="none", edgecolors=INK, zorder=5)
axes[0].set_xlabel("Mean net carbon exposure c'h (z-units of log intensity)"); axes[0].set_ylabel("Realized net IR, 1970-2026")
axes[0].set_title("A. IR vs constrained exposure (circled: no bound)"); axes[0].legend(loc="lower right")
e = scr.set_index("book")
pts = ["primary", "A5X_long_excl_top5", "A8X_long_excl_top8", "B5X_both_excl_top5", "B8X_both_excl_top8"]
axes[1].scatter(e.loc[pts, "long_waci_X"], e.loc[pts, "sharpe_full_1970"], color=ENTITY["carbon_constrained"], marker="s",
                label="Equal-weight books (primary and screens)", zorder=4)
axes[1].annotate("primary", (e.loc["primary", "long_waci_X"], e.loc["primary", "sharpe_full_1970"]), textcoords="offset points",
                 xytext=(4, 5), fontsize=7, color=INK2)
axes[1].annotate("exclusion screens\n(A5X, A8X, B5X, B8X)", (e.loc["A5X_long_excl_top5", "long_waci_X"], e.loc["A5X_long_excl_top5", "sharpe_full_1970"]),
                 textcoords="offset points", xytext=(10, -26), fontsize=7, color=INK2,
                 arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.6))
axes[1].axvline(cw.loc["full_1970", "market41_waci"], color=MUTED, ls="--", lw=1, label="Cap-weighted market (41 covered)")
axes[1].set_xlabel("Mean long-book WACI (team intensity units)"); axes[1].set_ylabel("Realized net IR / Sharpe, 1970-2026")
axes[1].set_title("B. IR vs long-book carbon intensity"); axes[1].legend(loc="lower right", fontsize=7)
savefig(fig, f"{MOD}_carbon_frontier")

fig, ax = plt.subplots(figsize=(7.2, 3.6))
ax.fill_between(ra_p.index, ra_p.alpha - 2 * ra_p.se, ra_p.alpha + 2 * ra_p.se, color=ENTITY["momentum"], alpha=0.15, lw=0,
                label="Primary, +/- 2 NW s.e.")
ax.plot(ra_p.index, ra_p.alpha, color=ENTITY["momentum"], label="Primary 11-1, 8/8 equal weight")
ax.plot(ra_s.index, ra_s.alpha, color=ENTITY["carbon_constrained"], label="Long leg excludes 8 highest emitters (A8X)")
ax.axhline(0, color=INK2, lw=0.8)
ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0, decimals=0))
ax.set_ylabel("FF5+UMD alpha, annualized"); ax.set_title("Rolling 36-month FF5+UMD alpha of net returns")
ax.legend(loc="upper left")
savefig(fig, f"{MOD}_rolling_alpha")

fig, ax = plt.subplots(figsize=(7.2, 3.6))
ww = wmon.rolling(12, min_periods=12).mean()
ax.plot(ww.index, ww["long_waci_X"], color=ENTITY["momentum"], label="Momentum long leg")
ax.plot(ww.index, ww["short_waci_X"], color=VIOLET, label="Momentum short leg")
ax.plot(ww.index, ww["market41_waci_X"], color=MUTED, label="Cap-weighted market, 41 covered industries")
ax.set_yscale("log"); plain_log(ax, subs=(1, 2, 3, 5)); ax.set_ylabel("WACI, 12-month average (log)")
ax.set_title("Carbon intensity of the primary momentum legs (covered industries only)")
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.08), ncol=3)
savefig(fig, f"{MOD}_waci")
log("figures done")

# =============================================================================== ledger and multiple testing
led = pd.DataFrame(LEDGER)
prim = led[led.primary_or_exploratory == "primary"].set_index("test_id")["p_value_two_sided"]
expl = led[led.primary_or_exploratory == "exploratory"].set_index("test_id")["p_value_two_sided"]
led["p_holm_within_primary"] = led.test_id.map(C.holm(prim))
led["p_bh_within_exploratory"] = led.test_id.map(C.bh(expl))
# sensitivity: BH over the exploratory hypothesis tests only, leaving out the descriptive factor loadings ([loading])
expl_nl = led[(led.primary_or_exploratory == "exploratory") & ~led.note.str.startswith("[loading]")].set_index("test_id")["p_value_two_sided"]
led["p_bh_exploratory_excl_loadings"] = led.test_id.map(C.bh(expl_nl))
assert led.test_id.is_unique and led.p_value_two_sided.notna().all()
save(led[["test_id", "module", "question", "statistic_name", "statistic", "p_value_two_sided", "n_obs",
          "primary_or_exploratory", "note"]], "tests_ledger", index=False)
save(led[["test_id", "primary_or_exploratory", "p_value_two_sided", "p_holm_within_primary", "p_bh_within_exploratory",
          "p_bh_exploratory_excl_loadings"]], "multiple_testing", index=False)
mts = pd.DataFrame([{"n_tests": len(led), "n_primary": int((led.primary_or_exploratory == "primary").sum()),
                     "n_exploratory": len(expl), "n_exploratory_loadings": len(expl) - len(expl_nl),
                     "n_primary_holm_lt_0.05": int((led.p_holm_within_primary < 0.05).sum()),
                     "n_exploratory_bh_lt_0.05": int((led.p_bh_within_exploratory < 0.05).sum()),
                     "n_exploratory_excl_loadings_bh_lt_0.05": int((led.p_bh_exploratory_excl_loadings < 0.05).sum())}]).T
mts.columns = ["value"]; mts.index.name = "item"; save(mts, "multiple_testing_summary")
print(led[led.primary_or_exploratory == "primary"][["test_id", "statistic", "p_value_two_sided", "p_holm_within_primary", "n_obs"]])
log(f"ledger rows: {len(led)} ({(led.primary_or_exploratory == 'primary').sum()} primary). Done.")
