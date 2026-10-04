"""Fact-check computations for exchange 04 (red team of the draft conclusion).

Run: cd /home/hashim/projects/GA/project/research && uv run python exchange/04_red_team/checks/fc04_checks.py
Writes checks/out/fc04_results.json and two CSVs. Every number here is exploratory: nothing enters a pass bar,
the 1994-2009 and 2022-2026 windows are already spent, and no module output is modified. The engine is M8's
(modules/M8_frozen_pre2010/run.py), which reproduces the team pipeline bitwise; the corrected-baseline paths come
from M3's run_baseline. Each block names the ChatGPT claim it checks.
"""
from __future__ import annotations

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
sys.path.insert(0, str(ROOT / "modules" / "M3_alpha_beta"))  # for m3lib only; M3's run.py has no main guard, never import it
import importlib.util  # noqa: E402
_spec = importlib.util.spec_from_file_location("m8run", ROOT / "modules" / "M8_frozen_pre2010" / "run.py")
m8 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m8)  # M8's run.py is main-guarded: loading it defines functions only
from m3lib import run_baseline  # noqa: E402
from team_pipeline import newey_west_regression, rolling_z  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parent / "out"
OUT.mkdir(exist_ok=True)
R: dict = {}

HO = ("2022-08-31", "2026-07-31")
COV = ("2020-01-31", "2021-12-31")
VAL = ("2010-01-31", "2022-07-31")
PRE = ("1994-03-31", "2009-12-31")
FULL = ("1994-03-31", "2026-07-31")
EPA_BROWN = ["Util", "Chems", "Other", "Agric", "Coal"]  # M4 EPA 5 highest (M4_emissions_team_rule_rerun.csv)

T, ff5, env, overall, vix, wti, gs10 = m8.load_inputs()
ff3, ind = T["ff3"], T["industries"]
rates = m8.resolve_costs(m8.HEDGE_COLS)
bf = m8.build_bond(gs10, ff5["RF"])
fac = ff5[["Mkt-RF", "SMB", "HML", "RMW", "CMA", "UMD"]].copy()
fac["BOND"], fac["WTI"] = bf["BOND"], np.log(wti).diff()
fac["dVIX"], fac["dlogEMV"] = vix.diff(), np.log(overall).diff()
sig, tsig = m8.share_signal(env, overall), m8.team_signal(env)
model = m8.brown_model(m8.TEAM_BROWN, ind, ff3)
modelE = m8.brown_model(EPA_BROWN, ind, ff3)
grid = pd.date_range(model["epsilon"].index.min(),
                     max(model["epsilon"].index.max(), sig.index.max() + pd.offsets.MonthEnd(1)), freq="ME")


def holds(cross, h):
    """Publication lag of one month, then an h-month extend-not-stack hold (M8 decision_hold with any h)."""
    c = cross.reindex(grid, fill_value=False).astype(bool)
    cd = c.shift(1, fill_value=False).astype(bool)
    return cd, cd.rolling(h, min_periods=1).max().astype(bool)


def ff3alpha(s, win):
    """FF3 alpha (%/yr as decimal), NW(6) t, and a 95% interval from t(n-4)."""
    s = s.loc[win[0]:win[1]].dropna()
    fit = newey_west_regression(s, ff3[list(m8.HEDGE_COLS)].reindex(s.index), lags=6)
    a, t = 12 * fit.loc["const", "coef"], fit.loc["const", "t_hac6"]
    tc = stats.t.ppf(0.975, len(s) - 4)
    return dict(n=len(s), alpha=a, t=t, lo=a - tc * a / t, hi=a + tc * a / t, net=12 * s.mean())


def timing(sT, sA, win):
    a = m8.attribution(sT["net_return"], sA["net_return"], sT["position"], sA["position"], fac, win)
    return dict(alpha=a["alpha_ann"], t=a["t6"], n=a["n"], k=a["k"], pi=a["pi"], meanD=12 * a["mean_D"])


always = m8.run_strategy(pd.Series(True, index=model["epsilon"].index), model, ff3, rates)
alwaysE = m8.run_strategy(pd.Series(True, index=modelE["epsilon"].index), modelE, ff3, rates)
_, holdF6 = holds(sig["cross"], 6)       # frozen EMV-share rule
cd6, holdT6 = holds(tsig["cross"], 6)    # team signal lagged one month = corrected Original/Pure 6m
cd3, holdT3 = holds(tsig["cross"], 3)
sT6 = m8.run_strategy(holdT6, model, ff3, rates)
sT3 = m8.run_strategy(holdT3, model, ff3, rates)

# ---- ChatGPT fix 1 ("lead with the frozen specification's holdout alpha"): does the frozen rule trade in 2022-2026?
w = pd.date_range(*HO, freq="ME")
R["frozen_rule_holdout"] = dict(
    months_in_position=int(holdF6.reindex(w - pd.offsets.MonthEnd(1)).sum()),
    first_off_month=str(sig.index[sig["off"]].min().date()),
    off_months_2021_10_on=int(sig.loc["2021-10-31":, "off"].sum()), months_2021_10_on=len(sig.loc["2021-10-31":]))

# ---- Claim 1 (holdout): lead-rule alpha, interval, entries; industry and year split of Pure/Original 6m gross P&L
lead = {}
for h, (cd, s) in {3: (cd3, sT3), 6: (cd6, sT6)}.items():
    r = ff3alpha(s["net_return"], HO)
    r["months_in_position"] = int(s["position"].shift(1).reindex(w).ne(0).sum())
    r["entry_decision_months"] = [d.strftime("%Y-%m") for d in cd.reindex(w - pd.offsets.MonthEnd(1)).loc[lambda x: x].index]
    lead[f"corrected_{h}m"] = r
R["holdout_lead_rules"] = lead
hedge = (model["betas"].shift(1) * ff3[list(m8.HEDGE_COLS)]).sum(axis=1)
wprev = sT6["position"].shift(1)
C = pd.DataFrame({i: wprev * ((ind[i] - ff3["RF"]) - hedge) / 5.0 for i in m8.TEAM_BROWN}).reindex(w)
R["holdout6_split"] = dict(check_maxdiff=float((C.sum(axis=1) - sT6["gross_return"].reindex(w)).abs().max()),
                           gross_ann=float(12 * sT6["gross_return"].reindex(w).mean()),
                           cost_ann=float(12 * sT6["cost"].reindex(w).mean()),
                           by_industry_ann=(12 * C.mean()).to_dict(),
                           by_year_sum=C.groupby(C.index.year).sum().sum(axis=1).to_dict())
C.groupby(C.index.year).sum().to_csv(OUT / "fc04_holdout6_industry_year.csv")

# ---- Claim 1 (holdout): how many distinct return paths sit behind "900 of 900"
paths = {}
for which in ("corrected", "team"):
    rb = run_baseline(which)
    S = pd.DataFrame({k: v["net_return"] for k, v in rb["strategies"].items()}).loc[HO[0]:HO[1]]
    timed = [c for c in S.columns if "Benchmark" not in c and "Green" not in c]
    ev = np.linalg.eigvalsh(S[timed].cov().to_numpy())[::-1]
    paths[which] = dict(pc1_share=float(ev[0] / ev.sum()),
                        identical_pairs=[(a, b) for i, a in enumerate(timed) for b in timed[i + 1:] if np.allclose(S[a], S[b])])
R["holdout_paths"] = paths

# ---- Claim 2 (frozen test): standard error, bars, power
a_fz, t_fz, df_fz = -0.0018183312826055, -0.26609162371943734, 175  # M8_attribution.csv
se = a_fz / t_fz
R["frozen_power"] = dict(se=se, alpha_for_t2=2 * se, mde80=(2 + stats.norm.ppf(0.8)) * se,
                         power_at_1pct=float(stats.t.sf(2 - 0.01 / se, df_fz)))
R["timing_alpha_by_leg"] = {}
for leg, mdl, sA in (("team", model, always), ("EPA", modelE, alwaysE)):
    for sname, hd in (("frozen_share", holdF6), ("team_lagged", holdT6)):
        sT = m8.run_strategy(hd, mdl, ff3, rates)
        for wn, win in (("pre1994_2009", PRE), ("seen2010_2022", VAL)):
            R["timing_alpha_by_leg"][f"{leg}|{sname}|{wn}"] = timing(sT, sA, win)
R["team_lagged6_timing"] = {wn: timing(sT6, always, win) for wn, win in
                            (("holdout", HO), ("pre1994_2009", PRE), ("seen2010_2022", VAL), ("1994_2026", FULL))}
# the two unseen windows pooled (1994-03..2009-12 and 2022-08..2026-07), same regression as M8 C20
a = m8.attribution(sT6["net_return"], always["net_return"], sT6["position"], always["position"], fac, FULL)
idx = a["data"].index
keep = (idx <= "2009-12-31") | (idx >= "2022-08-31")
pi = sT6["position"].shift(1).reindex(idx[keep]).abs().mean() / always["position"].shift(1).reindex(idx[keep]).abs().mean()
D = sT6["net_return"].reindex(idx[keep]) - pi * always["net_return"].reindex(idx[keep])
X = a["data"].loc[keep, [c for c in a["data"].columns if c != "D"]]
fit = newey_west_regression(D, X, lags=6)
n, k = len(D), X.shape[1] + 1
R["team_lagged6_timing"]["unseen_pooled"] = dict(alpha=12 * fit.loc["const", "coef"], t=fit.loc["const", "t_hac6"], n=n, k=k,
                                                 pi=pi, p_two=float(2 * stats.t.sf(abs(fit.loc["const", "t_hac6"]), n - k)))

# ---- Claim 3 (COVID): interval on the paired edge, block bootstrap on the 71% ratio
wc = pd.date_range(*COV, freq="ME")
y1, y2 = sT3["net_return"].reindex(wc).to_numpy(), always["net_return"].reindex(wc).to_numpy()
F = ff3[list(m8.HEDGE_COLS)].reindex(wc).to_numpy()


def a_of(y, F):
    return 12 * np.linalg.lstsq(np.column_stack([np.ones(len(y)), F]), y, rcond=None)[0][0]


rng = np.random.default_rng(230)
ratios = []
for _ in range(5000):
    st = rng.integers(0, len(wc), size=8)
    ii = np.concatenate([(np.arange(s, s + 3) % len(wc)) for s in st])[:len(wc)]
    A1, A2 = a_of(y1[ii], F[ii]), a_of(y2[ii], F[ii])
    ratios.append(A2 / A1 if A1 > 0 else np.nan)
ratios = np.array(ratios)
edge, t_edge = 0.018408079681854633, 0.8713954542354011  # M1b_alt_signals_covid_decomposition.csv, realtime EMV_env O3
tc = stats.t.ppf(0.975, 20)
R["covid"] = dict(orig3=ff3alpha(sT3["net_return"], COV), always=ff3alpha(always["net_return"], COV),
                  ratio=a_of(y2, F) / a_of(y1, F),
                  ratio_boot_p05=float(np.nanpercentile(ratios, 5)), ratio_boot_p95=float(np.nanpercentile(ratios, 95)),
                  ratio_boot_undefined_share=float(np.isnan(ratios).mean()),
                  edge_ci95=(edge - tc * edge / t_edge, edge + tc * edge / t_edge))

# ---- Claim 4 (signal): crossings in top-quintile CPU / MCCC months (60-month z of log level, expanding p80)
Mm = pd.read_csv(ROOT / "outputs/tables/M1b_alt_signals_measures_monthly.csv", parse_dates=["date"]).set_index("date")
Mm.index = Mm.index + pd.offsets.MonthEnd(0)
ov = {}
for meas in ("CPU", "MCCC"):
    z = rolling_z(np.log(Mm[meas].dropna()), 60, 36)
    top = (z > z.expanding(min_periods=36).quantile(0.8)).where(z.expanding(min_periods=36).quantile(0.8).notna()).dropna()
    for nm, cr in (("team_crossings", tsig["cross"]), ("frozen_crossings", sig["cross"])):
        cm = [d for d in cr[cr].index if d in top.index]
        kk = int(top.reindex(cm).sum())
        ov[f"{nm}|{meas}"] = dict(n_cross=len(cm), n_top=kk, base=float(top.mean()),
                                  p_binom=float(stats.binomtest(kk, len(cm), float(top.mean())).pvalue))
R["trigger_overlap_top_quintile"] = ov

# ---- Alternative 3 (commodity / inflation): WTI and 10-year breakeven changes in the holdout evaluation
dBE = m8.load_fred("T10YIE", how="last").diff().rename("dBE")
wr = np.log(wti).diff().rename("WTI")
alt3 = {}
for h, s in ((3, sT3), (6, sT6)):
    y = s["net_return"].loc[HO[0]:HO[1]]
    for nm, cols in (("FF3", []), ("FF3+dBE", [dBE]), ("FF3+WTI", [wr]), ("FF3+dBE+WTI", [dBE, wr])):
        f_ = newey_west_regression(y, pd.concat([ff3[list(m8.HEDGE_COLS)]] + cols, axis=1).reindex(y.index), lags=6)
        alt3[f"corrected_{h}m|{nm}"] = dict(alpha=12 * f_.loc["const", "coef"], t=f_.loc["const", "t_hac6"],
                                           **{f"t_{c}": f_.loc[c, "t_hac6"] for c in ("dBE", "WTI") if c in f_.index})
R["alt3_breakeven_wti_holdout"] = alt3

# ---- Case against / alternative 4: the untimed EPA-ranked Brown short, by window
R["always_short_EPA_brown"] = {wn: ff3alpha(alwaysE["net_return"], win) for wn, win in
                               (("holdout", HO), ("covid", COV), ("validation", VAL), ("pre1994_2009", PRE),
                                ("post2010", ("2010-01-31", "2026-07-31")), ("1994_2026", FULL))}
R["always_short_team_brown"] = {wn: ff3alpha(always["net_return"], win) for wn, win in
                                (("holdout", HO), ("pre1994_2009", PRE), ("post2010", ("2010-01-31", "2026-07-31")),
                                 ("1994_2026", FULL))}

json.dump(R, open(OUT / "fc04_results.json", "w"), indent=1, default=float)
rows = []
for sec, d in R.items():
    if isinstance(d, dict):
        for kk, v in d.items():
            if isinstance(v, dict):
                for m, x in v.items():
                    if isinstance(x, (int, float, np.floating)):
                        rows.append((sec, kk, m, float(x)))
            elif isinstance(v, (int, float, np.floating)):
                rows.append((sec, "", kk, float(v)))
pd.DataFrame(rows, columns=["section", "item", "stat", "value"]).to_csv(OUT / "fc04_results_long.csv", index=False)
print(json.dumps(R, indent=1, default=float))
