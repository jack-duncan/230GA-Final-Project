"""Independent re-run of the exchange 04 red-team numbers (fc04 and fc04b tags) that the report quotes.

Run: cd /home/hashim/projects/GA/project/research && uv run python exchange/04_red_team/checks/verify_fc04b_independent.py
Writes exchange/04_red_team/checks/out/independent_rerun/recomputed.json (every recomputed statistic, by block).

Independence: this file does not import, copy or read the code of exchange/04_red_team/checks/fc04_checks.py or
fc04b_checks.py (only their docstrings and the definitions written in report.tex, revisions.md, the module
FINDINGS.md files and M8's PREREGISTRATION.md were used). It does not import any module's run.py either. It uses the
shared building blocks in lib/common.py (data loaders) and lib/team_pipeline.py (rolling hedge, signal machinery,
position sizing, P&L engine, Newey-West regression), and writes its own orchestration, BOND factor, M8-style
attribution regression, AR(1) shocks and all windowing.

Engine checks against verified module tables are run first (M3 corrected holdout alphas, M8 secondary alpha and
drop-one, M1 Q6a slopes, M1b realtime validation alphas); every new cut is computed only after they pass.
"""
from __future__ import annotations

import json
import pathlib
import sys
import warnings

import numpy as np
import pandas as pd
from scipy import stats

ROOT = pathlib.Path("/home/hashim/projects/GA/project/research")
sys.path.insert(0, str(ROOT / "lib"))
from common import load_team, load_ff5_mom, load_fred, load_cpu, load_mccc  # noqa: E402
import team_pipeline as tp  # noqa: E402

warnings.filterwarnings("ignore")
OUT = ROOT / "exchange" / "04_red_team" / "checks" / "out" / "independent_rerun"
FC = ["Mkt-RF", "SMB", "HML"]
TEAM_BROWN = ["Util", "Ships", "Aero", "Steel", "BldMt"]
TEAM_GREEN = ["Fun", "RlEst", "Drugs", "Telcm", "Fin"]
TABLES = ROOT / "outputs" / "tables"

W = {  # windows (return months, inclusive)
    "pre1994_2009": ("1994-03-31", "2009-12-31"),
    "seen2010_2022": ("2010-01-31", "2022-07-31"),
    "validation": ("2010-01-31", "2022-07-31"),
    "holdout": ("2022-08-31", "2026-07-31"),
    "covid": ("2020-01-31", "2021-12-31"),
}

# ------------------------------------------------------------------------------------------------ data
T = load_team()
IND, FF3, MACRO = T["industries"], T["ff3"], T["macro"].copy()
MACRO_I = MACRO.copy()
gap = MACRO_I["cpi"].isna() & MACRO_I["cpi"].ffill().notna() & MACRO_I["cpi"].bfill().notna()
MACRO_I["cpi"] = MACRO_I["cpi"].interpolate(method="linear", limit_area="inside")
assert list(MACRO.index[gap].strftime("%Y-%m")) == ["2025-10"], MACRO.index[gap]
CTRL_RT = tp.team_controls(MACRO_I).shift(1)          # corrected baseline: controls lagged one month
RATES = tp.resolve_costs(FC)
CFG = tp.Config()

# attribution regressors (M8 C14-C20), own construction
KF = load_ff5_mom()


def build_bond() -> pd.Series:
    """Excess return of a constant-maturity 10-year par bond from GS10 (monthly average yields)."""
    y = load_fred("GS10") / 100.0
    k = np.arange(1, 21)
    def dc(yy):
        if not np.isfinite(yy):
            return np.nan, np.nan
        cf = np.full(20, yy / 2.0); cf[-1] += 1.0
        v = (1 + yy / 2.0) ** (-k)
        p = (cf * v).sum()
        t = k / 2.0
        dmod = (t * cf * v).sum() / p / (1 + yy / 2.0)
        conv = (cf * v * t * (t + 0.5)).sum() / p / (1 + yy / 2.0) ** 2
        return dmod, conv
    d = pd.DataFrame([dc(v) for v in y.to_numpy()], index=y.index, columns=["D", "C"])
    dy = y.diff()
    r = y.shift(1) / 12 - d["D"].shift(1) * dy + 0.5 * d["C"].shift(1) * dy ** 2
    return (r - KF["RF"].reindex(r.index)).rename("BOND")


BOND = build_bond()
WTI = np.log(load_fred("MCOILWTICO")).diff().rename("WTI")
DVIX = load_fred("VIXCLS", how="mean").diff().rename("dVIX")
DLEMV = np.log(load_fred("EMVOVERALLEMV")).diff().rename("dlogEMV")
XATT = pd.concat([KF[["Mkt-RF", "SMB", "HML", "RMW", "CMA", "UMD"]], BOND, WTI, DVIX, DLEMV], axis=1)
COND = ["Mkt-RF", "HML", "BOND", "dVIX"]


# ------------------------------------------------------------------------------------------------ engine
def lagged(s: pd.Series, extend_to="2026-08-31") -> pd.Series:
    """Value of month t-1 dated t (one-month publication lag) on a contiguous month-end index."""
    idx = pd.date_range(s.index.min(), pd.Timestamp(extend_to), freq="ME")
    return s.reindex(idx).shift(1)


def signals_for(att: pd.Series):
    return tp.build_signals(att, MACRO_I, CFG, controls=CTRL_RT, attention_transform="log1p")


def leg_model(brown_cols):
    y = (IND[list(brown_cols)].mean(axis=1) - FF3["RF"]).rename("y")
    al = pd.concat([y, FF3[FC]], axis=1).dropna()
    b, h, e, a = tp.rolling_factor_model(al["y"], al[FC], CFG.beta_window)
    return {"return": al["y"], "betas": b, "epsilon": e, "intercept": a}


def strategies(sig, model):
    eps = model["epsilon"]
    kw = dict(annual_vol_target=CFG.annual_vol_target, vol_window=CFG.residual_vol_window, cap=CFG.position_cap)
    run = lambda pos: tp.asset_strategy_returns(pos, model, FF3, FC, RATES)  # noqa: E731
    out = {}
    for h in (3, 6):
        out[f"O{h}"] = run(tp.state_position(sig["hold_raw"][h], eps, -1, **kw))
        out[f"P{h}"] = run(tp.state_position(sig["hold_pure"][h], eps, -1, **kw))
    out["CR"] = run(tp.continuous_position(sig["w_raw"], eps, -1, **kw))
    out["CP"] = run(tp.continuous_position(sig["w_pure"], eps, -1, **kw))
    out["AO"] = run(tp.state_position(pd.Series(True, index=eps.index), eps, -1, **kw))
    return out


def ff3_alpha(r: pd.Series, a, b, cols=FC, fac=None):
    fac = FF3 if fac is None else fac
    s = r.loc[a:b].dropna()
    fit = tp.newey_west_regression(s, fac[cols].reindex(s.index), lags=6)
    al, t = 12 * fit.loc["const", "coef"], fit.loc["const", "t_hac6"]
    n, k = len(s), len(cols) + 1
    se = al / t
    q = stats.t.ppf(0.975, n - k)
    return {"n": n, "alpha": al, "t": t, "lo": al - q * se, "hi": al + q * se}


def months(a, b, extra=None):
    idx = pd.date_range(a, b, freq="ME")
    if extra is not None:
        idx = idx.union(pd.date_range(*extra, freq="ME"))
    return idx


def attribution(rt: pd.DataFrame, ao: pd.DataFrame, idx: pd.DatetimeIndex):
    """M8 attribution (PREREGISTRATION C13, C19-C21): D = net R^T - pi net R^AO on 10 factors + 4 I_{t-1} terms."""
    hT = rt["position"].shift(1).reindex(idx)
    hA = ao["position"].shift(1).reindex(idx)
    pi = hT.abs().mean() / hA.abs().mean()
    D = (rt["net_return"].reindex(idx) - pi * ao["net_return"].reindex(idx)).rename("D")
    I = (hT != 0).astype(float)
    X = XATT.reindex(idx).copy()
    for c in COND:
        X[f"I_{c}"] = I * X[c]
    fit = tp.newey_west_regression(D, X, lags=6)
    n = int(pd.concat([D, X], axis=1).dropna().shape[0])
    k = X.shape[1] + 1
    al, t = 12 * fit.loc["const", "coef"], fit.loc["const", "t_hac6"]
    return {"alpha": al, "t": t, "n": n, "k": k, "pi": pi, "p_two": 2 * stats.t.sf(abs(t), n - k),
            "meanD": 12 * D.mean(), "se": al / t}


def timing_ff3(rt, ao, a, b):
    """Exposure-matched edge with pi and FF3 fitted in the window, plus the paired (pi = 1) edge."""
    idx = months(a, b)
    hT = rt["position"].shift(1).reindex(idx)
    hA = ao["position"].shift(1).reindex(idx)
    pi = hT.abs().mean() / hA.abs().mean()
    D = rt["net_return"].reindex(idx) - pi * ao["net_return"].reindex(idx)
    P = rt["net_return"].reindex(idx) - ao["net_return"].reindex(idx)
    d, p = ff3_alpha(D, a, b), ff3_alpha(P, a, b)
    r, al = ff3_alpha(rt["net_return"], a, b), ff3_alpha(ao["net_return"], a, b)
    return {"n": d["n"], "pi": pi, "rule_alpha": r["alpha"], "rule_t": r["t"], "always_alpha": al["alpha"],
            "always_t": al["t"], "D_alpha": d["alpha"], "D_t": d["t"], "paired_alpha": p["alpha"], "paired_t": p["t"]}


def rnd(x, nd=6):
    if isinstance(x, dict):
        return {k: rnd(v, nd) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [rnd(v, nd) for v in x]
    if isinstance(x, (float, np.floating)):
        return None if not np.isfinite(x) else round(float(x), nd)
    if isinstance(x, (np.integer,)):
        return int(x)
    return x


R: dict = {"engine_checks": {}}
chk = R["engine_checks"]

# ------------------------------------------------------------------------------------------------ team legs, corrected baseline
SIG_TEAM = signals_for(lagged(MACRO["attention"].dropna()))
MOD_TEAM = leg_model(TEAM_BROWN)
ST_TEAM = strategies(SIG_TEAM, MOD_TEAM)

# check 1: M3 corrected holdout FF3 alphas (verified table)
m3 = pd.read_csv(TABLES / "M3_alpha_beta_holdout_alpha.csv")
m3c = m3[m3.baseline == "corrected"].set_index("short")
smap = {"Orig 3m": "O3", "Pure 3m": "P3", "Orig 6m": "O6", "Pure 6m": "P6", "Cont raw": "CR", "Cont pure": "CP"}
c1 = {}
for sh, key in smap.items():
    mine = ff3_alpha(ST_TEAM[key]["net_return"], *W["holdout"])
    c1[sh] = {"mine": mine["alpha"], "mine_t": mine["t"], "M3": m3c.loc[sh, "alpha_FF3"], "M3_t": m3c.loc[sh, "t_FF3"],
              "absdiff": abs(mine["alpha"] - m3c.loc[sh, "alpha_FF3"])}
chk["M3_corrected_holdout_FF3"] = c1

# check 1b: bitwise against run_pipeline with the same substitutions
rp = tp.run_pipeline(macro=MACRO_I, attention=lagged(MACRO["attention"].dropna()), controls=CTRL_RT, bootstrap_reps=0,
                     macro_states=False, paired=False, extras=False)
chk["run_pipeline_maxdiff_P6"] = float((rp["strategies"]["Pure | Short Brown hold 6m"]["net_return"]
                                        - ST_TEAM["P6"]["net_return"]).abs().max())
chk["run_pipeline_maxdiff_AO"] = float((rp["strategies"]["Benchmark | Always-short Brown"]["net_return"]
                                        - ST_TEAM["AO"]["net_return"]).abs().max())

# check 2: M8 secondary (team EMV_env level lagged 1m, 6m hold), 1994-03..2009-12, and its drop-one alphas
m8 = attribution(ST_TEAM["O6"], ST_TEAM["AO"], months(*W["pre1994_2009"]))
m8s = pd.read_csv(TABLES / "M8_strategy_summary.csv")
m8a = pd.read_csv(TABLES / "M8_attribution.csv")
sec = m8a[(m8a.signal.str.contains("secondary")) & (m8a.term == "const")].iloc[0]
chk["M8_secondary"] = {"mine_alpha": m8["alpha"], "mine_t": m8["t"], "mine_pi": m8["pi"], "mine_n": m8["n"],
                       "M8_alpha": 12 * sec["coef"], "M8_t": sec["t_nw6"],
                       "M8_pi": float(m8s[m8s.signal.str.contains("secondary")]["pi"].iloc[0])}
m8d = pd.read_csv(TABLES / "M8_drop_one.csv")
m8d = m8d[m8d.signal.str.contains("secondary")].set_index("dropped")

# check 3: BOND against M3's monthly BOND table (verified module output)
try:
    bm = pd.read_csv(TABLES / "M3_alpha_beta_bond_monthly.csv")
    dcol = [c for c in bm.columns if "date" in c.lower() or "month" in c.lower()][0]
    bm.index = pd.to_datetime(bm[dcol]) + pd.offsets.MonthEnd(0)
    bcol = [c for c in bm.columns if c.upper().startswith("BOND") and "eom" not in c.lower()][0]
    j = pd.concat([BOND, bm[bcol]], axis=1).dropna()
    chk["BOND_vs_M3_maxdiff"] = float((j.iloc[:, 0] - j.iloc[:, 1]).abs().max())
except Exception as exc:  # pragma: no cover
    chk["BOND_vs_M3_maxdiff"] = f"not compared: {exc}"

# ------------------------------------------------------------------------------------------------ [fc04b] team lagged timing by window
tl = {}
for h, key in ((6, "O6"), (3, "O3")):
    for wn in ("pre1994_2009", "holdout", "seen2010_2022"):
        tl[f"{h}m|{wn}"] = attribution(ST_TEAM[key], ST_TEAM["AO"], months(*W[wn]))
    tl[f"{h}m|unseen_pooled"] = attribution(ST_TEAM[key], ST_TEAM["AO"], months(*W["pre1994_2009"], extra=W["holdout"]))
R["team_lagged_timing_by_window"] = tl

# [fc04b] pooled power (two-sided 5% test, 80% power, t(n-k) critical value)
pu = tl["6m|unseen_pooled"]
se = pu["alpha"] / pu["t"]
q = stats.t.ppf(0.975, pu["n"] - pu["k"])
R["pooled_unseen_power"] = {"alpha": pu["alpha"], "t": pu["t"], "n": pu["n"], "se": se, "t_crit": q,
                            "mde80": (q + stats.norm.ppf(0.80)) * se, "mde80_2.8": 2.8 * se,
                            "mde80_normal": (stats.norm.ppf(0.975) + stats.norm.ppf(0.80)) * se}

# ------------------------------------------------------------------------------------------------ [fc04b] drop-one industry
dro = {}
for drop in [None] + TEAM_BROWN:
    legs = [b for b in TEAM_BROWN if b != drop]
    mod = leg_model(legs)
    st = strategies(SIG_TEAM, mod)
    tag = "drop_none" if drop is None else f"drop_{drop}"
    for h in (6, 3):
        o, p = st[f"O{h}"], st[f"P{h}"]
        hold_eq = float((o["net_return"].loc[W["holdout"][0]:W["holdout"][1]] - p["net_return"].loc[W["holdout"][0]:W["holdout"][1]]).abs().max())
        row = {"ff3_holdout": ff3_alpha(o["net_return"], *W["holdout"]),
               "always_ff3_holdout": ff3_alpha(st["AO"]["net_return"], *W["holdout"]),
               "timing_holdout": attribution(o, st["AO"], months(*W["holdout"])),
               "orig_vs_pure_holdout_maxdiff": hold_eq}
        if h == 6:
            row["timing_pre"] = attribution(o, st["AO"], months(*W["pre1994_2009"]))
            if drop is not None:
                row["M8_drop_one_check"] = {"M8_alpha": float(m8d.loc[drop, "alpha_ann"]), "M8_t": float(m8d.loc[drop, "t_nw6"])}
        dro[f"{h}m|{tag}"] = row
R["drop_one_holdout"] = dro

# ------------------------------------------------------------------------------------------------ [fc04] lead rules, paths, split, COVID
lead = {}
for key in ("O6", "P6", "O3", "P3"):
    df = ST_TEAM[key]
    a, b = W["holdout"]
    pos = df["position"]
    # decision months: position set at end of month t earns t+1; holdout decision months 2022-07 .. 2026-06
    dec = pos.loc["2022-07-31":"2026-06-30"]
    on = dec != 0
    entries_from_flat = int((on & ~on.shift(1, fill_value=bool(pos.loc[:"2022-06-30"].iloc[-1] != 0))).sum())
    lead[key] = {**ff3_alpha(df["net_return"], a, b), "net": 12 * df["net_return"].loc[a:b].mean(),
                 "months_in_position": int((pos.shift(1).loc[a:b] != 0).sum()),
                 "entries_from_flat": entries_from_flat}
cross = SIG_TEAM["cross_raw"]
cross_dec = cross.loc["2022-07-31":"2026-06-30"]
lead["crossings_in_holdout_decision_months"] = [d.strftime("%Y-%m") for d in cross_dec[cross_dec].index]
crossp = SIG_TEAM["cross_pure"].loc["2022-07-31":"2026-06-30"]
lead["pure_crossings_in_holdout_decision_months"] = [d.strftime("%Y-%m") for d in crossp[crossp].index]
R["holdout_lead_rules"] = lead

hold_ret = pd.DataFrame({k: ST_TEAM[k]["net_return"].loc[W["holdout"][0]:W["holdout"][1]] for k in ("O3", "P3", "O6", "P6", "CR", "CP")})
ev_cov = np.linalg.eigvalsh(np.cov(hold_ret.to_numpy().T))
ev_cor = np.linalg.eigvalsh(np.corrcoef(hold_ret.to_numpy().T))
R["holdout_paths"] = {"pc1_share_cov": ev_cov[-1] / ev_cov.sum(), "pc1_share_corr": ev_cor[-1] / ev_cor.sum(),
                      "O3_eq_P3": float((hold_ret.O3 - hold_ret.P3).abs().max()),
                      "O6_eq_P6": float((hold_ret.O6 - hold_ret.P6).abs().max())}

# gross holdout P&L of corrected Pure 6m split by industry: h_{t-1}/5 * (r_i,t - RF_t - beta_{t-1}' f_t)
p6 = ST_TEAM["P6"]
a, b = W["holdout"]
idx = months(a, b)
h_l = p6["position"].shift(1).reindex(idx)
hedge = (MOD_TEAM["betas"].shift(1).reindex(idx) * FF3[FC].reindex(idx)).sum(axis=1)
split = {c: 12 * (h_l / 5 * (IND[c].reindex(idx) - FF3["RF"].reindex(idx) - hedge)).mean() for c in TEAM_BROWN}
gross = 12 * p6["gross_return"].reindex(idx).mean()
R["holdout6_split"] = {"gross_ann": gross, "cost_ann": 12 * p6["cost"].reindex(idx).mean(),
                       "net_ann": 12 * p6["net_return"].reindex(idx).mean(), "by_industry_ann": split,
                       "check_sum_minus_gross": sum(split.values()) - gross}

# COVID: Original 3m vs always-short, realtime timing (M1b primary timing = corrected baseline)
a, b = W["covid"]
o3c, aoc = ff3_alpha(ST_TEAM["O3"]["net_return"], a, b), ff3_alpha(ST_TEAM["AO"]["net_return"], a, b)
edge = ff3_alpha(ST_TEAM["O3"]["net_return"] - ST_TEAM["AO"]["net_return"], a, b)
ex = (ST_TEAM["O3"]["net_return"] - ST_TEAM["AO"]["net_return"]).loc[a:b].drop([pd.Timestamp("2020-03-31"), pd.Timestamp("2020-04-30")])
edge_ex = ff3_alpha(ex, ex.index.min(), ex.index.max())
R["covid"] = {"orig3": o3c, "always": aoc, "ratio": aoc["alpha"] / o3c["alpha"], "edge": edge, "edge_ex_mar_apr_2020": edge_ex}

# frozen-test power (derived from M8's verified primary alpha and t)
prim = m8a[(m8a.signal.str.contains("primary")) & (m8a.term == "const")].iloc[0]
se_f = 12 * prim["coef"] / prim["t_nw6"]
R["frozen_power"] = {"alpha": 12 * prim["coef"], "t": prim["t_nw6"], "se": se_f, "alpha_for_t2": 2 * se_f,
                     "mde80_2.84": 2.84 * se_f}

# ------------------------------------------------------------------------------------------------ [fc04b] Q6a same-month slopes
def rt_shock(m: pd.Series, min_pairs=36) -> pd.Series:
    """shock_t = m_t - a_hat - b_hat m_{t-1}, AR(1) fitted by OLS on pairs (m_{s-1}, m_s) with s <= t-1."""
    m = m.dropna()
    vals, out = m.to_numpy(), np.full(len(m), np.nan)
    for i in range(2, len(m)):
        x, y = vals[:i - 1], vals[1:i]          # pairs ending at s = 1..i-1 (i.e. t-1)
        if len(y) < min_pairs:
            continue
        X = np.column_stack([np.ones(len(x)), x])
        coef, *_ = np.linalg.lstsq(X, y, rcond=None)
        out[i] = vals[i] - coef[0] - coef[1] * vals[i - 1]
    return pd.Series(out, index=m.index)


epa = pd.read_csv(TABLES / "M4_emissions_legs.csv").set_index("spec")
EPA_GREEN = [s.strip() for s in epa.loc["epa5", "green"].split(",")]
EPA_BROWN = [s.strip() for s in epa.loc["epa5", "brown"].split(",")]
LEGS = {"team": (TEAM_GREEN, TEAM_BROWN), "EPA": (EPA_GREEN, EPA_BROWN)}
SHOCK = {"MCCC": rt_shock(load_mccc()), "CPU": rt_shock(load_cpu())}
q6 = {}
for ln, (g, br) in LEGS.items():
    gb = (IND[g].mean(axis=1) - IND[br].mean(axis=1)).rename("GB")
    for mn, sh in SHOCK.items():
        s = sh.dropna()
        d = pd.concat([gb, s.rename("x")], axis=1).dropna()
        zx = (d["x"] / d["x"].std(ddof=1)).to_frame("shock_sd")
        f0 = tp.newey_west_regression(d["GB"], zx, lags=6)
        Xc = pd.concat([zx, FF3[FC].reindex(d.index)], axis=1)
        f1 = tp.newey_west_regression(d["GB"], Xc, lags=6)
        q6[f"{ln}|{mn}"] = {"n": len(d), "start": d.index.min().strftime("%Y-%m"), "end": d.index.max().strftime("%Y-%m"),
                             "slope_pct": 100 * f0.loc["shock_sd", "coef"], "t": f0.loc["shock_sd", "t_hac6"],
                             "slope_pct_FF3": 100 * f1.loc["shock_sd", "coef"], "t_FF3": f1.loc["shock_sd", "t_hac6"]}
R["q6a_same_month"] = q6

# ------------------------------------------------------------------------------------------------ [fc04b] climate indices on EPA legs
END = {"MCCC": "2025-07-31", "CPU": "2025-10-31"}
MEAS = {"MCCC": load_mccc(), "CPU": load_cpu()}
civ, counts = {}, {}
m1b = pd.read_csv(TABLES / "M1b_alt_signals_alpha_grid_realtime.csv")
for mn, ser in MEAS.items():
    sig = signals_for(lagged(ser))
    for ln, (g, br) in LEGS.items():
        st = strategies(sig, leg_model(br))
        vals = []
        for key in ("O3", "P3", "O6", "P6", "CR", "CP"):
            row = {"validation": timing_ff3(st[key], st["AO"], *W["validation"]),
                   "holdout": timing_ff3(st[key], st["AO"], W["holdout"][0], END[mn])}
            if mn == "CPU":
                row["pre1994_2009"] = timing_ff3(st[key], st["AO"], *W["pre1994_2009"])
            if ln == "team":
                mm = m1b[(m1b.period == "validation") & (m1b.measure == mn) & (m1b.strategy == key)]
                if len(mm):
                    row["M1b_validation_alpha"] = float(mm["alpha_ann"].iloc[0])
                    row["M1b_validation_t"] = float(mm["t"].iloc[0])
            civ[f"{ln}|{mn}|{key}"] = row
            vals.append(row["validation"])
        counts[f"{ln}|{mn}"] = {"n_t_ge_196": int(sum(v["rule_t"] >= 1.96 for v in vals)),
                                "n_positive": int(sum(v["rule_alpha"] > 0 for v in vals))}
R["climate_index_validation"] = civ
R["climate_index_validation_counts"] = counts

# summaries of the ranges the report quotes (EPA legs)
def rng(ln, mn, win, field):
    v = [civ[f"{ln}|{mn}|{k}"][win][field] for k in ("O3", "P3", "O6", "P6", "CR", "CP")]
    return {"min": min(v), "max": max(v), "values": v}

R["epa_ranges"] = {
    "CPU_holdout_rule_alpha": rng("EPA", "CPU", "holdout", "rule_alpha"),
    "CPU_holdout_rule_t": rng("EPA", "CPU", "holdout", "rule_t"),
    "CPU_holdout_always_alpha": civ["EPA|CPU|O3"]["holdout"]["always_alpha"],
    "CPU_holdout_always_t": civ["EPA|CPU|O3"]["holdout"]["always_t"],
    "CPU_holdout_n": civ["EPA|CPU|O3"]["holdout"]["n"],
    "CPU_holdout_D_alpha": rng("EPA", "CPU", "holdout", "D_alpha"),
    "CPU_holdout_D_t": rng("EPA", "CPU", "holdout", "D_t"),
    "CPU_pre_D_alpha": rng("EPA", "CPU", "pre1994_2009", "D_alpha"),
    "MCCC_holdout_D_alpha": rng("EPA", "MCCC", "holdout", "D_alpha"),
    "EPA_validation_t": {mn: rng("EPA", mn, "validation", "rule_t") for mn in MEAS},
    "EPA_validation_alpha": {mn: rng("EPA", mn, "validation", "rule_alpha") for mn in MEAS},
}

# M1b team-leg realtime validation alphas (engine check for the climate-index block)
R["engine_checks"]["M1b_team_validation_maxabsdiff"] = max(
    abs(v["validation"]["rule_alpha"] - v["M1b_validation_alpha"]) for k, v in civ.items() if "M1b_validation_alpha" in v)
R["engine_checks"]["M1b_team_validation_n_compared"] = sum("M1b_validation_alpha" in v for v in civ.values())

# ------------------------------------------------------------------------------------------------ M3 numbers quoted beside fc04b
# timing alpha against the pi-scaled always-short, in-window FF3 (team) + UMD + BOND; pi over post-2010 (M3 ln_vs_benchmark)
lnb = pd.read_csv(TABLES / "M3_alpha_beta_ln_vs_benchmark.csv")
lnb = lnb[lnb.baseline == "corrected"]
FAC = pd.concat([FF3[FC], KF["UMD"], BOND], axis=1)
m3ln = {}
for sh, key in (("Orig 3m", "O3"), ("Pure 3m", "P3"), ("Orig 6m", "O6"), ("Pure 6m", "P6")):
    rt, ao = ST_TEAM[key], ST_TEAM["AO"]
    ip = months("2010-01-31", "2026-07-31")
    pi = rt["position"].shift(1).reindex(ip).abs().mean() / ao["position"].shift(1).reindex(ip).abs().mean()
    D = rt["net_return"] - pi * ao["net_return"]
    for per in ("holdout", "covid"):
        a, b = W[per]
        mine = ff3_alpha(D, a, b, cols=["Mkt-RF", "SMB", "HML", "UMD", "BOND"], fac=FAC)
        ref = lnb[(lnb.short == sh) & (lnb.period == per)].iloc[0]
        m3ln[f"{sh}|{per}"] = {"pi": pi, "alpha": mine["alpha"], "t": mine["t"], "M3_pi": ref["pi"],
                               "M3_alpha": ref["alpha_D_inperiod"], "M3_t": ref["t_alpha_D_inperiod"],
                               "M3_p": ref["p_alpha_D_inperiod"], "meanD_ann": 12 * D.loc[a:b].mean()}
R["M3_ln_vs_benchmark_recomputed"] = m3ln

(OUT / "recomputed.json").write_text(json.dumps(rnd(R, 8), indent=1))

# ------------------------------------------------------------------------------------------------ compare with the red team's outputs
def flatten(d, pre=""):
    out = {}
    if isinstance(d, dict):
        for k, v in d.items():
            out.update(flatten(v, f"{pre}/{k}" if pre else str(k)))
    elif isinstance(d, (int, float)) and not isinstance(d, bool):
        out[pre] = float(d)
    return out


cmp = {}
for name in ("fc04b_results.json", "fc04_results.json"):
    theirs = flatten(json.loads((ROOT / "exchange/04_red_team/checks/out" / name).read_text()))
    mine = flatten(json.loads(json.dumps(rnd(R, 12))))
    # key aliases between their layout and mine
    alias = {}
    if name == "fc04_results.json":
        for k in list(theirs):
            if k.startswith("team_lagged6_timing/"):
                alias[k] = k.replace("team_lagged6_timing/", "team_lagged_timing_by_window/6m|").replace("|1994_2026", "|x")
            if k.startswith("holdout_lead_rules/corrected_6m/"):
                alias[k] = k.replace("holdout_lead_rules/corrected_6m/", "holdout_lead_rules/O6/")
            if k.startswith("holdout_lead_rules/corrected_3m/"):
                alias[k] = k.replace("holdout_lead_rules/corrected_3m/", "holdout_lead_rules/O3/")
            if k == "holdout_paths/corrected/pc1_share":
                alias[k] = "holdout_paths/pc1_share_cov"
            if k.startswith("holdout6_split/"):
                alias[k] = k
            if k.startswith("covid/") and k.count("/") == 2:
                alias[k] = k
            if k == "covid/ratio":
                alias[k] = k
            if k.startswith("always_short_team_brown/holdout/") and k.split("/")[-1] in ("alpha", "t", "n", "lo", "hi"):
                alias[k] = "drop_one_holdout/6m|drop_none/always_ff3_holdout/" + k.split("/")[-1]
            if k.startswith("frozen_power/"):
                alias[k] = k.replace("mde80", "mde80_2.84")
    else:
        for k in list(theirs):
            alias[k] = k.replace("/holdout_alpha", "/holdout/rule_alpha").replace("/holdout_t", "/holdout/rule_t")
            if k.startswith("climate_index_validation/") and "|timing/" in k:
                alias[k] = k.replace("|timing/", "/")
            if k.startswith("climate_index_validation/") and "|timing" not in k and k.endswith(("/alpha", "/t")):
                alias[k] = k[: k.rfind("/")] + ("/validation/rule_alpha" if k.endswith("/alpha") else "/validation/rule_t")
            if k.startswith("q6a_same_month/"):
                parts = k.split("/")
                lab = parts[1].split("|")
                if len(lab) == 3 and lab[2] in ("GB", "GB_FF3"):
                    suffix = "" if lab[2] == "GB" else "_FF3"
                    fld = {"slope_pct": f"slope_pct{suffix}", "t": f"t{suffix}", "n": "n"}.get(parts[2])
                    if fld:
                        alias[k] = f"q6a_same_month/{lab[0]}|{lab[1]}/{fld}"
            if k.startswith("pooled_unseen_power/"):
                alias[k] = k.replace("mde80_rule_of_thumb", "mde80_2.8")
    rows = []
    for k, v in theirs.items():
        mk = alias.get(k, k)
        if mk in mine:
            rows.append({"key": k, "theirs": v, "mine": mine[mk], "absdiff": abs(v - mine[mk])})
    df = pd.DataFrame(rows)
    cmp[name] = {"n_compared": len(df), "n_their_numeric": len(theirs),
                 "max_absdiff": float(df["absdiff"].max()) if len(df) else None,
                 "worst": df.sort_values("absdiff").tail(5).to_dict("records") if len(df) else [],
                 "not_compared": sorted(k for k in theirs if alias.get(k, k) not in mine)}
(OUT / "comparison.json").write_text(json.dumps(rnd(cmp, 10), indent=1))
print(json.dumps(rnd(R["engine_checks"], 6), indent=1))
print({k: (v["n_compared"], v["n_their_numeric"], v["max_absdiff"]) for k, v in cmp.items()})
print("written", OUT / "recomputed.json", OUT / "comparison.json")
