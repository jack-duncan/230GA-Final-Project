"""Fact-check computations for exchange 04, round 2 (red team of the revised draft conclusion).

Run: cd /home/hashim/projects/GA/project/research && uv run python exchange/04_red_team/checks/fc04b_checks.py
Writes checks/out/fc04b_results.json. Exploratory only: nothing enters a pass bar, both unseen windows are spent,
and no module output is modified. Engines: M8's run.py (bitwise team pipeline) for the Brown-leg rules, M1's Q6a
regression for same-month shock slopes, and run_pipeline (via M1b's conventions) for climate-index triggers.
Each block names the ChatGPT claim it checks.
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import sys
import warnings

import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings("ignore")
ROOT = pathlib.Path("/home/hashim/projects/GA/project/research")
sys.path.insert(0, str(ROOT / "lib"))
_spec = importlib.util.spec_from_file_location("m8run", ROOT / "modules" / "M8_frozen_pre2010" / "run.py")
m8 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m8)  # main-guarded: defines functions only
_spec1 = importlib.util.spec_from_file_location("m1help", ROOT / "modules" / "M1_signal_audit" / "helpers.py")
m1h = importlib.util.module_from_spec(_spec1)
_spec1.loader.exec_module(m1h)
_spec1b = importlib.util.spec_from_file_location("m1bhelp", ROOT / "modules" / "M1b_alt_signals" / "helpers.py")
m1bh = importlib.util.module_from_spec(_spec1b)
_spec1b.loader.exec_module(m1bh)
from common import load_cpu, load_fred, load_mccc, load_team, leg_returns, nw_ols  # noqa: E402
from team_pipeline import newey_west_regression, run_pipeline  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parent / "out"
OUT.mkdir(exist_ok=True)
R: dict = {}

HO = ("2022-08-31", "2026-07-31")
VAL = ("2010-01-31", "2022-07-31")
PRE = ("1994-03-31", "2009-12-31")
FULL = ("1994-03-31", "2026-07-31")
TEAM_GREEN = ["Fun", "RlEst", "Drugs", "Telcm", "Fin"]
EPA_GREEN = ["Banks", "Insur", "Softw", "Hardw", "Smoke"]   # M4 EPA 5 lowest
EPA_BROWN = ["Util", "Chems", "Other", "Agric", "Coal"]     # M4 EPA 5 highest

T, ff5, env, overall, vix, wti, gs10 = m8.load_inputs()
ff3, ind = T["ff3"], T["industries"]
rates = m8.resolve_costs(m8.HEDGE_COLS)
bf = m8.build_bond(gs10, ff5["RF"])
fac = ff5[["Mkt-RF", "SMB", "HML", "RMW", "CMA", "UMD"]].copy()
fac["BOND"], fac["WTI"] = bf["BOND"], np.log(wti).diff()
fac["dVIX"], fac["dlogEMV"] = vix.diff(), np.log(overall).diff()
tsig = m8.team_signal(env)


def grid_for(model):
    return pd.date_range(model["epsilon"].index.min(),
                         max(model["epsilon"].index.max(), tsig.index.max() + pd.offsets.MonthEnd(1)), freq="ME")


def holds(cross, h, grid):
    c = cross.reindex(grid, fill_value=False).astype(bool)
    cd = c.shift(1, fill_value=False).astype(bool)
    return cd.rolling(h, min_periods=1).max().astype(bool)


def ff3alpha(s, win):
    s = s.loc[win[0]:win[1]].dropna()
    fit = newey_west_regression(s, ff3[list(m8.HEDGE_COLS)].reindex(s.index), lags=6)
    a, t = 12 * fit.loc["const", "coef"], fit.loc["const", "t_hac6"]
    return dict(n=len(s), alpha=a, t=t)


def timing(sT, sA, win):
    a = m8.attribution(sT["net_return"], sA["net_return"], sT["position"], sA["position"], fac, win)
    return dict(alpha=a["alpha_ann"], t=a["t6"], n=a["n"], pi=a["pi"])


def book(brown, h):
    mdl = m8.brown_model(brown, ind, ff3)
    g = grid_for(mdl)
    sT = m8.run_strategy(holds(tsig["cross"], h, g), mdl, ff3, rates)
    sA = m8.run_strategy(pd.Series(True, index=mdl["epsilon"].index), mdl, ff3, rates)
    return sT, sA


# ---- Weak claim 2 / "a holdout loss that comes from one industry": drop-one holdout alphas, corrected 6m and 3m
drop = {}
for h in (6, 3):
    for out_ in [None] + list(m8.TEAM_BROWN):
        br = [i for i in m8.TEAM_BROWN if i != out_]
        sT, sA = book(br, h)
        key = f"{h}m|drop_{out_ or 'none'}"
        drop[key] = dict(ff3_holdout=ff3alpha(sT["net_return"], HO), timing_holdout=timing(sT, sA, HO),
                         always_ff3_holdout=ff3alpha(sA["net_return"], HO))
        if h == 6:
            drop[key]["timing_pre"] = timing(sT, sA, PRE)
R["drop_one_holdout"] = drop

# ---- "positive in both unseen windows": the team lagged rule's timing alpha by window (6m and 3m)
sT6, sA6 = book(m8.TEAM_BROWN, 6)
sT3, sA3 = book(m8.TEAM_BROWN, 3)
R["team_lagged_timing_by_window"] = {f"{h}m|{wn}": timing(s, a, win) for h, s, a in ((6, sT6, sA6), (3, sT3, sA3))
                                      for wn, win in (("pre1994_2009", PRE), ("holdout", HO), ("seen2010_2022", VAL))}

# ---- Alternative 3 (crisis hedge): does the timing differential concentrate in VIX > 30 or NBER recession months?
usrec = load_fred("USREC", how="last")
usrec.index = usrec.index + pd.offsets.MonthEnd(0)
crisis_res = {}
for h, sT, sA in ((6, sT6, sA6), (3, sT3, sA3)):
    a = m8.attribution(sT["net_return"], sA["net_return"], sT["position"], sA["position"], fac, FULL)
    D = a["data"]["D"]
    for cname, flag in (("VIX_gt_30", vix.reindex(D.index) > 30),
                        ("NBER_recession", usrec.reindex(D.index).fillna(0) > 0)):
        flag = flag.fillna(False).astype(bool)
        for wn, keep in (("1994_2026", pd.Series(True, index=D.index)),
                         ("unseen_pooled", pd.Series((D.index <= "2009-12-31") | (D.index >= "2022-08-31"), index=D.index))):
            d = D[keep]
            f = flag[keep]
            X = pd.DataFrame({"crisis": f.astype(float), "calm": (~f).astype(float)}, index=d.index)
            fit = nw_ols(d, X, lags=6, const=False)
            # timing alpha (M8 regression) refit on calm months only
            Xa = a["data"].loc[keep[keep].index, [c for c in a["data"].columns if c != "D"]]
            calm_idx = f[~f].index
            fa = newey_west_regression(d.loc[calm_idx], Xa.loc[calm_idx], lags=6)
            crisis_res[f"{h}m|{cname}|{wn}"] = dict(
                n_crisis=int(f.sum()), n_calm=int((~f).sum()),
                meanD_crisis_ann=12 * float(fit.params["crisis"]), t_crisis=float(fit.tvalues["crisis"]),
                meanD_calm_ann=12 * float(fit.params["calm"]), t_calm=float(fit.tvalues["calm"]),
                sumD_crisis=float(d[f].sum()), sumD_calm=float(d[~f].sum()),
                timing_alpha_calm_only=12 * fa.loc["const", "coef"], t_timing_alpha_calm_only=fa.loc["const", "t_hac6"])
R["crisis_split"] = crisis_res

# ---- Alternative 2 (direction of regulation news): holdout P&L by position episode, with the Steel contribution
w = pd.date_range(*HO, freq="ME")
mdl = m8.brown_model(m8.TEAM_BROWN, ind, ff3)
hedge = (mdl["betas"].shift(1) * ff3[list(m8.HEDGE_COLS)]).sum(axis=1)
wprev = sT6["position"].shift(1)
C = pd.DataFrame({i: wprev * ((ind[i] - ff3["RF"]) - hedge) / 5.0 for i in m8.TEAM_BROWN}).reindex(w)
on = wprev.reindex(w).ne(0)
ep = (on != on.shift(1, fill_value=False)).cumsum().where(on)
episodes = []
for k, g in C[on].groupby(ep[on]):
    episodes.append(dict(start=g.index[0].strftime("%Y-%m"), end=g.index[-1].strftime("%Y-%m"), months=len(g),
                         gross_total=float(g.sum().sum()), steel=float(g["Steel"].sum()), util=float(g["Util"].sum()),
                         administration="Biden" if g.index[0] < pd.Timestamp("2025-01-31") else "Trump"))
R["holdout6_episodes"] = episodes

# ---- Alternative 1 (wrong legs), part (a): same-month GB slopes on real-time MCCC and CPU shocks, team vs EPA legs
rf = ff3["RF"]
mccc, cpu = load_mccc("Aggregate").dropna(), load_cpu().dropna()
SH = {"MCCC": m1h.ar1_shock_expanding(mccc, 36), "CPU": m1h.ar1_shock_expanding(cpu, 36)}
q6a = {}
for legs, (gn, bn) in (("team", (TEAM_GREEN, m8.TEAM_BROWN)), ("EPA", (EPA_GREEN, EPA_BROWN))):
    green, brown, gb = leg_returns(ind, gn, bn)
    for s, shock in SH.items():
        x = (shock.dropna() / shock.dropna().std(ddof=1)).rename("shock_sd").to_frame()
        for oname, y in (("GB", gb), ("brown_excess", brown - rf), ("green_excess", green - rf)):
            r = m1h.reg_row(y, x)
            q6a[f"{legs}|{s}|{oname}"] = dict(n=r["n"], slope_pct=100 * r["b_shock_sd"], t=r["t_shock_sd"], p=r["p_shock_sd"])
        r = m1h.reg_row(gb, x.join(ff3[list(m8.HEDGE_COLS)], how="inner"))   # M1's FF3-controlled robustness row
        q6a[f"{legs}|{s}|GB_FF3"] = dict(n=r["n"], slope_pct=100 * r["b_shock_sd"], t=r["t_shock_sd"], p=r["p_shock_sd"])
R["q6a_same_month"] = q6a

# ---- Alternative 1, part (b): MCCC and CPU through the team machinery (real-time timing), team vs EPA legs, validation
MEAS = m1bh.build_measures()
MAC = m1bh.macro_fixed()
FF3F = load_team()["ff3"]
val = {}
for legs, (gn, bn) in (("team", (None, None)), ("EPA", (EPA_GREEN, EPA_BROWN))):
    for m in ("MCCC", "CPU"):
        att, ctrl = m1bh.timed_inputs(MEAS[m], MAC, "realtime")
        kw = dict(macro=MAC, attention=att, controls=ctrl, attention_transform="log1p", full_end="2026-07-31", **m1bh.CHEAP)
        if gn is not None:
            kw.update(green=gn, brown=bn)
        res = run_pipeline(**kw)
        hend = m1bh.eval_end(MEAS[m])
        for code, sname in m1bh.STRATS.items():
            st = m1bh.window_stats(res["strategies"][sname], *VAL, FF3F)
            sh = m1bh.window_stats(res["strategies"][sname], HO[0], hend, FF3F)
            val[f"{legs}|{m}|{code}"] = dict(alpha=st["alpha_ann"], t=st["alpha_t_hac6"], n=st["n_months"],
                                             holdout_alpha=sh["alpha_ann"], holdout_t=sh["alpha_t_hac6"],
                                             holdout_n=sh["n_months"], holdout_end=str(hend.date()))
        # timing versus position: FF3 alpha of D = r_T - pi r_AO (pi = mean |held position| ratio in-window, as M3/M8),
        # and the unscaled paired alpha of r_T - r_AO (as M1b), plus the always-short's own FF3 alpha, per window
        AO = res["strategies"]["Benchmark | Always-short Brown"]
        wins = {"validation": VAL, "holdout": (HO[0], str(hend.date()))}
        if m == "CPU":
            wins["pre1994_2009"] = PRE
        for code, sname in m1bh.STRATS.items():
            S = res["strategies"][sname]
            for wn, (a0, b0) in wins.items():
                idx = pd.date_range(a0, b0, freq="ME")
                hT, hA = S["position"].shift(1).reindex(idx), AO["position"].shift(1).reindex(idx)
                pi = hT.abs().mean() / hA.abs().mean()
                D = (S["net_return"].reindex(idx) - pi * AO["net_return"].reindex(idx)).dropna()
                P = (S["net_return"].reindex(idx) - AO["net_return"].reindex(idx)).dropna()
                fD = newey_west_regression(D, FF3F[list(m8.HEDGE_COLS)].reindex(D.index), lags=6)
                fP = newey_west_regression(P, FF3F[list(m8.HEDGE_COLS)].reindex(P.index), lags=6)
                fT = ff3alpha(S["net_return"], (a0, b0))
                fA = ff3alpha(AO["net_return"], (a0, b0))
                val.setdefault(f"{legs}|{m}|{code}|timing", {})[wn] = dict(
                    n=len(D), pi=float(pi), rule_alpha=fT["alpha"], rule_t=fT["t"], always_alpha=fA["alpha"], always_t=fA["t"],
                    D_alpha=12 * fD.loc["const", "coef"], D_t=fD.loc["const", "t_hac6"],
                    paired_alpha=12 * fP.loc["const", "coef"], paired_t=fP.loc["const", "t_hac6"])
R["climate_index_validation"] = val
VALC = {k: v for k, v in val.items() if not k.endswith("|timing")}
R["climate_index_validation_counts"] = {
    f"{legs}|{m}": dict(n_t_ge_196=sum(1 for c in m1bh.STRATS if val[f"{legs}|{m}|{c}"]["t"] >= 1.96),
                        n_positive=sum(1 for c in m1bh.STRATS if val[f"{legs}|{m}|{c}"]["alpha"] > 0),
                        mean_alpha=float(np.mean([val[f"{legs}|{m}|{c}"]["alpha"] for c in m1bh.STRATS])))
    for legs in ("team", "EPA") for m in ("MCCC", "CPU")}

# ---- Edit 1 arithmetic: minimum detectable timing alpha for the pooled unseen estimate (+0.36%, t 0.70)
a_u, t_u, n_u, k_u = 0.0036133395104758215, 0.6989435154139517, 238, 15  # fc04_results.json team_lagged6_timing.unseen_pooled
se_u = a_u / t_u
R["pooled_unseen_power"] = dict(se=se_u, mde80=(stats.t.ppf(0.975, n_u - k_u) + stats.norm.ppf(0.8)) * se_u,
                                mde80_rule_of_thumb=2.8 * se_u)

json.dump(R, open(OUT / "fc04b_results.json", "w"), indent=1, default=float)
print(json.dumps(R, indent=1, default=float))
