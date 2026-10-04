"""M2_christhian_tests: Christhian's four overlooked tests (8-and-8 legs, richer factor controls, the source of the
HML exposure, uniform cost sensitivity) and a summary of what, if anything, is left.

Run:  cd /home/hashim/projects/GA/project/research && uv run python modules/M2_christhian_tests/run.py

PRIMARY TESTS (stated in this docstring when run.py was first written, 2026-09-26 10:06 UTC). Timing record from the
build transcript: data checks (COMEQ correlations 09:59) and a smoke test (10:02) that printed the Q2-primary
configuration's alphas came before this docstring, so the Q2 primary is not strictly blind. It follows the module
brief's Q2 wording (FF5 + momentum + commodity control, corrected baseline) and its result is null.
Common template for Q1, Q2 and Q4: the 7 hedged strategies (Original 3m, Pure 3m, Original 6m, Pure 6m,
Continuous raw, Continuous pure, Always-short Brown) x 2 windows (post2010 = 2010-01..2026-07, holdout =
2022-08..2026-07) = 14 alpha t-tests; NW(6) t, two-sided p from t(n-k); Holm at 5% within the 14. "Alpha left" requires
a POSITIVE alpha whose Holm-adjusted p < 0.05.
  Q1: corrected baseline, 8-and-8 legs with the team's sort-order tie-break (Hardw), FF3 hedge, team costs, FF3 alpha.
  Q2: corrected baseline, 5-and-5 legs, FF5+UMD+COMEQ hedge, team costs, alpha on FF5+UMD+COMEQ (traded factors only).
  Q4: corrected baseline, 5-and-5 legs, FF3 hedge, uniform 5 bp (the most favourable cost), FF3 alpha.
      Primary descriptive statistic: the uniform break-even cost (bp) of each strategy's validation alpha.
  Q3: HML loading of the raw 5-and-5 Green-minus-Brown spread under FF3 and FF5+UMD in full_1970 and post2010
      (4 tests, Holm within 4), and its exact decomposition into industry contributions; the "driver" industries are
      the one or two with the largest absolute contribution in post2010 under FF3.
Everything else is robustness (other legs, hedges, evaluation sets, cost levels on the four main windows) or
exploratory (sub-periods, last 12/18 months, gross zero-cost runs, characteristic links).
Whole-grid check: Holm (and BH) over every net-of-cost alpha test in the M2 grid.
"""
from __future__ import annotations

import sys
import time
import warnings

sys.path.insert(0, "/home/hashim/projects/GA/project/research/lib")
sys.path.insert(0, "/home/hashim/projects/GA/project/research/modules/M2_christhian_tests")
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy import stats  # noqa: E402

from common import PERIODS, holm, bh, load_kf_industries  # noqa: E402
from team_pipeline import rolling_factor_model, newey_west_regression  # noqa: E402
from helpers import (Data, Ledger, run_config, live_start, window, nw_fit, perf_block, save_csv, save_tex, fmt_p,  # noqa: E402
                     STRATS, BH_GB, SHORT, LONG_PERIODS, SHORT_PERIODS, HEDGE_COLS, HEDGE_LABEL, NONTRADED,
                     LEGS_LABEL, BASE_LABEL, COST_LABEL, MODULE, END)

warnings.filterwarnings("ignore", category=RuntimeWarning)
T0 = time.perf_counter()
D = Data()
LED = Ledger()
LEGS = ["L5", "L8H", "L8M"]
BASES = ["team", "corr"]
HEDGES = ["FF3", "FF3U", "FF5U", "FF5UC", "FF5UCx"]
COSTS_Q4 = ["u0", "u5", "u10", "u25"]
MAIN_WINDOWS = ["post2010", "holdout"]

PRIMARY = {  # config key -> (question, eval id)
    ("L8H", "corr", "FF3", "team"): ("Q1", "E:FF3"),
    ("L5", "corr", "FF5UC", "team"): ("Q2", "E:FF5UC"),
    ("L5", "corr", "FF3", "u5"): ("Q4", "E:FF3"),
}

# ============================================================================ config grid
configs: dict[tuple, set] = {}
for l in LEGS:
    for b in BASES:
        configs.setdefault((l, b, "FF3", "team"), set()).add("Q1")
        for h in HEDGES:
            configs.setdefault((l, b, h, "team"), set()).add("Q2")
for b in BASES:
    for h in ("FF3", "FF5UC"):
        for c in COSTS_Q4:
            configs.setdefault(("L5", b, h, c), set()).add("Q4")
FULL_MODE = {(l, b, "FF3", "team") for l in LEGS for b in BASES} | {("L5", b, "FF5UC", "team") for b in BASES}

RES = {}
for key in configs:
    RES[key] = run_config(D, *key, full=key in FULL_MODE)
print(f"[M2] {len(RES)} pipeline runs ({len(FULL_MODE)} full mode) in {time.perf_counter() - T0:.1f}s")


def eval_sets(hedge: str, costs: str):
    """Evaluation regressor sets for a strategy hedged with `hedge`. id -> (traded X, nontraded cols, label)."""
    own = HEDGE_COLS[hedge]
    out = {f"E:{hedge}": (hedge, [], HEDGE_LABEL[hedge])}
    if costs != "team":  # cost grid: own set only
        return out
    out[f"E:{hedge}+cmdty"] = (hedge, NONTRADED["cmdty"], f"{HEDGE_LABEL[hedge]} + WTI, IMF")
    if hedge != "FF5UC":
        out["E:FF5UC"] = ("FF5UC", [], HEDGE_LABEL["FF5UC"])
        out["E:FF5UC+cmdty"] = ("FF5UC", NONTRADED["cmdty"], f"{HEDGE_LABEL['FF5UC']} + WTI, IMF")
    out["E:FF5UC+cmdty+lead"] = ("FF5UC", NONTRADED["cmdty+lead"], f"{HEDGE_LABEL['FF5UC']} + WTI, IMF and their t+1 values")
    return out


def cfg_note(key):
    l, b, h, c = key
    return f"{LEGS_LABEL[l]}; {BASE_LABEL[b]}; hedge {HEDGE_LABEL[h]}; {COST_LABEL[c]}"


def cfg_code(key):
    """Compact config code for ledger notes (legend in FINDINGS.md)."""
    l, b, h, c = key
    return f"legs={l} base={b} hedge={h} costs={c}"


# ============================================================================ strategy evaluation over the grid
rows = []
for key, res in RES.items():
    l, b, h, c = key
    qs = ";".join(sorted(configs[key]))
    gross = c == "u0"
    for s in STRATS:
        df = res["strategies"][s]
        live = live_start(res, s)
        periods = ["full_live", "post2010", "validation", "holdout"] if gross else LONG_PERIODS + SHORT_PERIODS
        for p in periods:
            a, e = window(p, live)
            pb = perf_block(df, a, e)
            base_row = dict(legs=l, baseline=b, hedge=h, costs=c, questions=qs, strategy=s, strat=SHORT[s], period=p,
                            window_start=a, window_end=e, **{f"perf_{k}": v for k, v in pb.items()})
            tid0 = f"strat|{l}|{b}|{h}|{c}|{SHORT[s]}|{p}"
            kind_base = "exploratory" if (gross or p not in ("full_live", "post2010", "validation", "holdout")) else "robustness"
            LED.add(f"{tid0}|mean", qs, "t_mean_NW6", pb.get("t_mean"), pb.get("p_mean"), pb.get("n"),
                    "exploratory" if gross else kind_base,
                    f"ann_net={100 * pb.get('ann_net', np.nan):.2f}%; {cfg_code(key)}; {a:%Y-%m}..{e:%Y-%m}"
                    + ("; gross zero-cost run (break-even input, not implementable)" if gross else ""))
            sets = eval_sets(h, c) if p in LONG_PERIODS else {"E:FF3": ("FF3", [], HEDGE_LABEL["FF3"])}
            for eid, (xh, nt, elabel) in sets.items():
                y = df["net_return"].loc[a:e]
                f = nw_fit(y, D.eval_X(xh), D.nontraded[nt] if nt else None)
                rows.append({**base_row, "eval_id": eid, "eval_label": elabel, **f})
                is_primary = key in PRIMARY and PRIMARY[key][1] == eid and p in MAIN_WINDOWS
                kind = "primary" if is_primary else kind_base
                note = (f"alpha_ann={100 * f.get('alpha_ann', np.nan):.2f}%; {cfg_code(key)} eval={eid[2:]}; "
                        f"{a:%Y-%m}..{e:%Y-%m}" + ("; gross zero-cost run (break-even input, not implementable)" if gross else ""))
                LED.add(f"{tid0}|{eid}|alpha", qs, "t_alpha_NW6", f.get("t_alpha"), f.get("p_alpha"), f.get("n"), kind, note)
                if c == "team" and eid == f"E:{h}" and p in LONG_PERIODS:
                    LED.add(f"{tid0}|{eid}|b_HML", qs, "t_b_HML_NW6", f.get("t_HML"), f.get("p_HML"), f.get("n"), "exploratory",
                            f"b_HML={f.get('b_HML', np.nan):.3f}; residual HML loading of the hedged strategy; {cfg_code(key)} eval={eid[2:]}")
SG = pd.DataFrame(rows)
save_csv(SG, "strategy_grid")
print(f"[M2] strategy grid: {len(SG)} regressions, {time.perf_counter() - T0:.1f}s")


def sg(legs, base, hedge, costs, eid=None, periods=None):
    x = SG[(SG.legs == legs) & (SG.baseline == base) & (SG.hedge == hedge) & (SG.costs == costs)]
    if eid is not None:
        x = x[x.eval_id == eid]
    if periods is not None:
        x = x[x.period.isin(periods)]
    return x


def primary_family(key, name):
    q, eid = PRIMARY[key]
    x = sg(*key, eid=eid, periods=MAIN_WINDOWS).copy()
    x["order"] = x.strategy.map(STRATS.index)
    x = x.sort_values(["period", "order"], ascending=[False, True])
    assert len(x) == 14, len(x)
    x["holm_p"] = holm(x["p_alpha"]).values
    x["bh_q"] = bh(x["p_alpha"]).values
    x["positive_and_holm_sig"] = (x.alpha_ann > 0) & (x.holm_p < 0.05)
    out = x[["strat", "period", "n", "k", "alpha_ann", "t_alpha", "p_alpha", "holm_p", "bh_q", "positive_and_holm_sig",
             "b_HML", "t_HML", "perf_ann_net", "perf_sharpe"]].copy()
    out.insert(0, "question", q)
    out.insert(1, "config", cfg_note(key) + f"; eval {eid[2:]}")
    save_csv(out, f"{name}")
    return out


# ============================================================================ Q1: 8-and-8 legs
leg_rows = []
for l, (g, b) in D.legs.items():
    for side, names in (("Green", g), ("Brown", b)):
        for i, nm in enumerate(names):
            leg_rows.append({"legs": l, "legs_label": LEGS_LABEL[l], "side": side, "rank": i + 1, "industry": nm,
                             "emissions_intensity": D.emissions.get(nm, np.nan)})
save_csv(pd.DataFrame(leg_rows), "q1_leg_composition")

comp = []
for l in LEGS:
    for b in BASES:
        res = RES[(l, b, "FF3", "team")]
        ct = res["comparison_table"].copy()
        held = []
        for s in ct.strategy:
            df = res["strategies"][s]
            held.append(int((df["position"].shift(1).loc["2010-01-31":END].fillna(0) != 0).sum()) if "position" in df else np.nan)
        ct.insert(1, "months_held_2010_2026", held)
        ct.insert(0, "baseline", b)
        ct.insert(0, "legs", l)
        comp.append(ct)
# Inherited team columns renamed so nobody cites them as M2 results:
#  * significant_after_multiple_testing: the team's Holm flag over 32 claims with NORMAL p-values on NW(6) t-stats; it is
#    True only through 24-month COVID claims (replication audit item 3) and contradicts M2's t(n-k) inference;
#  * active_months_full: counts months with a nonzero net return, including exit-cost-only months (audit item 6).
TEAM_COL_RENAME = {"significant_after_multiple_testing": "team_holm_flag_normal_p",
                   "active_months_full": "team_active_months_full_nonzero_net"}
Q1COMP = pd.concat(comp, ignore_index=True).rename(columns=TEAM_COL_RENAME)
save_csv(Q1COMP, "q1_comparison")

# full-mode runs: comparison tables for the FF5+UMD+COMEQ hedge, and every bootstrap test into the ledger
comp2 = []
for b in BASES:
    ct = RES[("L5", b, "FF5UC", "team")]["comparison_table"].copy()
    ct.insert(0, "baseline", b); ct.insert(0, "legs", "L5")
    comp2.append(ct)
save_csv(pd.concat(comp2, ignore_index=True).rename(columns=TEAM_COL_RENAME), "q2_comparison")
for key in sorted(FULL_MODE):
    res = RES[key]
    qs = ";".join(sorted(configs[key]))
    for _, r in res["comparison_table"].iterrows():
        LED.add(f"boot|{'|'.join(key)}|{SHORT[r.strategy]}|2010-2026", qs, "circular_block_bootstrap_mean_12m", r.ann_return_full,
                r.bootstrap_p, 199, "robustness",
                f"statistic = annualized net mean 2010-01..2026-07; 5000 reps, 12-month blocks; CI [{r.bootstrap_ci_low:.4f}, {r.bootstrap_ci_high:.4f}]; {cfg_code(key)}")
    for _, r in res["paired_table"].iterrows():
        LED.add(f"paired|{'|'.join(key)}|{SHORT[r.new]} vs {SHORT[r.benchmark]}|holdout", qs, "paired_block_bootstrap_mean_diff",
                r.mean_ann, r.p_two_sided, 48, "exploratory",
                f"holdout 2022-08..2026-07 annualized net-return difference (unscaled positions); {cfg_code(key)}")

t1rows = []
for l in LEGS:
    for b in BASES:
        x = sg(l, b, "FF3", "team", eid="E:FF3", periods=["validation", "holdout"])
        for _, r in x.iterrows():
            t1rows.append({"legs": l, "baseline": b, "period": r.period, "strategy": r.strat, "ann_net_pct": 100 * r.perf_ann_net,
                           "sharpe": r.perf_sharpe, "alpha_ff3_pct": 100 * r.alpha_ann, "t_alpha": r.t_alpha, "p_alpha_t": r.p_alpha,
                           "b_HML": r.b_HML, "months_held": r.perf_months_held, "mean_abs_pos": r.perf_mean_abs_pos})
Q1T1 = pd.DataFrame(t1rows)
save_csv(Q1T1, "q1_table1")
# replication check vs writeup Table 1 (team baseline, 5 and 5)
chk = Q1T1[(Q1T1.legs == "L5") & (Q1T1.baseline == "team")].set_index(["period", "strategy"])
assert abs(chk.loc[("validation", "Pure 6m"), "alpha_ff3_pct"] - 2.51) < 0.005 and abs(chk.loc[("holdout", "Original 3m"), "t_alpha"] + 2.19) < 0.005

for b in BASES:
    w = []
    for s in STRATS:
        row = {"Strategy": SHORT[s]}
        for p, pl in (("validation", "Val"), ("holdout", "Hold")):
            for l, ll in (("L5", "5/5"), ("L8H", "8/8 H"), ("L8M", "8/8 M")):
                r = Q1T1[(Q1T1.legs == l) & (Q1T1.baseline == b) & (Q1T1.period == p) & (Q1T1.strategy == SHORT[s])].iloc[0]
                row[f"{pl} {ll}"] = f"{r.alpha_ff3_pct:.2f} ({r.t_alpha:.2f})"
        w.append(row)
    save_tex(pd.DataFrame(w), f"q1_table1_{b}",
             caption=f"FF3 alpha (\\% p.a., NW(6) t in parentheses) of each strategy with 5-and-5 and 8-and-8 legs, {BASE_LABEL[b]}, "
                     "FF3 hedge and team costs. Val = 2010-01 to 2022-07, Hold = 2022-08 to 2026-07. 8/8 H and 8/8 M differ only "
                     "in the tied 8th Green industry (Hardw or MedEq).",
             label=f"tab:m2_q1_{b}")
    save_csv(pd.DataFrame(w), f"q1_table1_{b}_wide")
Q1P = primary_family(("L8H", "corr", "FF3", "team"), "q1_primary")

# ============================================================================ Q2: factor controls
# COMEQ definition check
nt = D.nontraded
jus = []
cands = {"COMEQ (Oil, Coal, Mines, Gold)": D.comeq, "COMEQ ex-Gold (Oil, Coal, Mines)": D.comeq_x,
         **{f"{k} industry": (D.ind[k] - D.ff3["RF"]) for k in ("Oil", "Coal", "Mines", "Gold")}}
brown_ex = (D.ind[D.legs["L5"][1]].mean(axis=1) - D.ff3["RF"])
gb5 = D.ind[D.legs["L5"][0]].mean(axis=1) - D.ind[D.legs["L5"][1]].mean(axis=1)
CORR_DESC = {"WTI": "same-month WTI log change", "IMF": "same-month IMF log change", "WTI_lead": "next-month (t+1) WTI log change",
             "IMF_lead": "next-month (t+1) IMF log change", "Mkt-RF": "Mkt-RF", "brown": "5-and-5 Brown leg excess return",
             "gb": "5-and-5 Green-minus-Brown spread"}
for nm, s in cands.items():
    # correlations: common sample where every series exists; the t+1 leads end it at 2026-06
    d = pd.concat([s.rename("x"), nt, D.ff3["Mkt-RF"], brown_ex.rename("brown"), gb5.rename("gb")], axis=1).loc["1992-02-29":END].dropna()
    # spanning regression on FF5+UMD: its own sample, 1992-02 to 2026-07 (no lead needed)
    f = nw_fit(s.loc["1992-02-29":END], D.eval_X("FF5U"))
    row = {"series": nm, "start": d.index.min(), "end": d.index.max(), "n": len(d), "ann_mean": 12 * d.x.mean(),
           "ann_vol": np.sqrt(12) * d.x.std(), **{f"corr_{c}": d.x.corr(d[c]) for c in ["WTI", "WTI_lead", "IMF", "IMF_lead", "Mkt-RF", "brown", "gb"]},
           "ff5u_start": f["start"], "ff5u_end": f["end"], "ff5u_n": f["n"],
           "ff5u_alpha_ann": f["alpha_ann"], "ff5u_t_alpha": f["t_alpha"], "ff5u_p_alpha": f["p_alpha"], "ff5u_r2": f["r2"],
           "ff5u_b_mkt": f["b_Mkt-RF"]}
    jus.append(row)
    for c in ["WTI", "IMF", "WTI_lead", "IMF_lead", "Mkt-RF", "brown"]:
        r_ = d.x.corr(d[c]); n_ = len(d); tt = r_ * np.sqrt((n_ - 2) / (1 - r_ ** 2))
        LED.add(f"comeq|{nm}|corr_{c}", "Q2", "t_corr_iid", tt, 2 * stats.t.sf(abs(tt), n_ - 2), n_, "exploratory",
                f"corr={r_:.3f} of {nm} with {CORR_DESC[c]}, {d.index.min():%Y-%m}..{d.index.max():%Y-%m} (COMEQ justification)")
    LED.add(f"comeq|{nm}|ff5u_alpha", "Q2", "t_alpha_NW6", f["t_alpha"], f["p_alpha"], f["n"], "exploratory",
            f"alpha_ann={100 * f['alpha_ann']:.2f}%, R2={f['r2']:.3f}; spanning regression of {nm} excess return on FF5+UMD, "
            f"{f['start']:%Y-%m}..{f['end']:%Y-%m} (COMEQ justification; not part of the strategy/spread alpha grid)")
JUS = pd.DataFrame(jus)
save_csv(JUS, "q2_comeq_justification")
jw =(f"{JUS.start.min():%Y-%m} to {JUS.end.max():%Y-%m}, n = {int(JUS.n.iloc[0])}")
fw = (f"{JUS.ff5u_start.min():%Y-%m} to {JUS.ff5u_end.max():%Y-%m}, n = {int(JUS.ff5u_n.iloc[0])}")
save_tex(JUS[["series", "ann_mean", "ann_vol", "corr_WTI", "corr_WTI_lead", "corr_IMF", "corr_IMF_lead", "corr_Mkt-RF", "corr_brown", "ff5u_r2"]]
         .assign(ann_mean=lambda x: 100 * x.ann_mean, ann_vol=lambda x: 100 * x.ann_vol)
         .rename(columns={"series": "Series", "ann_mean": "Mean %", "ann_vol": "Vol %", "corr_WTI": "WTI t", "corr_WTI_lead": "WTI t+1",
                          "corr_IMF": "IMF t", "corr_IMF_lead": "IMF t+1", "corr_Mkt-RF": "Mkt", "corr_brown": "Brown leg", "ff5u_r2": "R2 on FF5+UMD"}),
         "q2_comeq_justification",
         caption="Commodity-equity proxy COMEQ: annualized excess return and correlations with WTI and IMF all-commodity log changes "
                 f"(month t and t+1), the market and the 5-and-5 Brown leg, {jw} (the t+1 leads end the sample one month early). "
                 f"R-squared on FF5+UMD from the spanning regression, {fw}.",
         label="tab:m2_comeq")

# raw Green-minus-Brown spread across control sets
SPREAD_EVALS = {"E:FF3": ("FF3", []), "E:FF3U": ("FF3U", []), "E:FF5U": ("FF5U", []), "E:FF5UC": ("FF5UC", []),
                "E:FF5UCx": ("FF5UCx", []), "E:FF5UC+cmdty": ("FF5UC", NONTRADED["cmdty"]),
                "E:FF5UC+cmdty+lead": ("FF5UC", NONTRADED["cmdty+lead"])}
SPREAD_LABEL = {k: (HEDGE_LABEL[v[0]] + ("" if not v[1] else " + WTI, IMF" + (" (t and t+1)" if len(v[1]) == 4 else ""))) for k, v in SPREAD_EVALS.items()}
SP_PERIODS = ["full_1970", "post2010", "validation", "holdout", "pre_covid", "covid", "inflation_rates", "last18", "last12"]
sp_rows = []
GB = {}
for l, (g, b) in D.legs.items():
    GB[l] = (D.ind[g].mean(axis=1) - D.ind[b].mean(axis=1)).rename("GB")
    for p in SP_PERIODS:
        a, e = window(p)
        y = GB[l].loc[a:e]
        evs = SPREAD_EVALS if p not in SHORT_PERIODS else {"E:FF3": ("FF3", [])}
        for eid, (xh, ntc) in evs.items():
            f = nw_fit(y, D.eval_X(xh), nt[ntc] if ntc else None)
            sp_rows.append({"legs": l, "period": p, "eval_id": eid, "eval_label": SPREAD_LABEL[eid], **f})
            q3_primary = (l == "L5" and eid in ("E:FF3", "E:FF5U") and p in ("full_1970", "post2010"))
            kind = "exploratory" if p not in ("full_1970", "post2010", "validation", "holdout") else "robustness"
            note = f"raw GB spread {LEGS_LABEL[l]}; eval {SPREAD_LABEL[eid]}; window {f['start']:%Y-%m}..{f['end']:%Y-%m}"
            LED.add(f"spread|{l}|{p}|{eid}|alpha", "Q2", "t_alpha_NW6", f.get("t_alpha"), f.get("p_alpha"), f.get("n"), kind,
                    f"alpha_ann={100 * f.get('alpha_ann', np.nan):.2f}%; " + note)
            LED.add(f"spread|{l}|{p}|{eid}|b_HML", "Q2;Q3", "t_b_HML_NW6", f.get("t_HML"), f.get("p_HML"), f.get("n"),
                    "primary" if q3_primary else kind, f"b_HML={f.get('b_HML', np.nan):.3f}; " + note)
SP = pd.DataFrame(sp_rows)
save_csv(SP, "q2_spread_controls")
# team replication check: raw spread FF3 HML loading, 1970..2022-07 = -0.238 and 2010..2022-07 = -0.351
chk1 = nw_fit(GB["L5"].loc["1970-01-31":"2022-07-31"], D.eval_X("FF3"))
chk2 = nw_fit(GB["L5"].loc["2010-01-31":"2022-07-31"], D.eval_X("FF3"))
assert abs(chk1["b_HML"] + 0.237951) < 1e-5 and abs(chk2["b_HML"] + 0.350514) < 1e-5, (chk1["b_HML"], chk2["b_HML"])

wide = []
for eid in SPREAD_EVALS:
    row = {"Controls": SPREAD_LABEL[eid]}
    for p, pl in (("full_1970", "Full"), ("post2010", "Post-2010"), ("holdout", "Holdout")):
        r = SP[(SP.legs == "L5") & (SP.period == p) & (SP.eval_id == eid)].iloc[0]
        row[f"{pl} alpha"] = f"{100 * r.alpha_ann:.2f} ({r.t_alpha:.2f})"
        row[f"{pl} HML"] = f"{r.b_HML:.2f} ({r.t_HML:.2f})"
    wide.append(row)
save_tex(pd.DataFrame(wide), "q2_spread_controls",
         caption="Raw 5-and-5 Green-minus-Brown spread: alpha (\\% p.a.) and HML loading, NW(6) t in parentheses, across control "
                 "sets. Full = 1970-01 to 2026-07 (from 1992-02 when WTI and IMF controls are included). WTI and IMF are non-traded "
                 "and demeaned within the window.",
         label="tab:m2_spread_controls")

Q2P = primary_family(("L5", "corr", "FF5UC", "team"), "q2_primary")
t1q2 = []
for b in BASES:
    for h in ("FF3", "FF5UC"):
        x = sg("L5", b, h, "team", eid=f"E:{h}", periods=["validation", "holdout"])
        for _, r in x.iterrows():
            t1q2.append({"baseline": b, "hedge": h, "period": r.period, "strategy": r.strat, "ann_net_pct": 100 * r.perf_ann_net,
                         "sharpe": r.perf_sharpe, "alpha_pct": 100 * r.alpha_ann, "t_alpha": r.t_alpha, "p_alpha_t": r.p_alpha,
                         "b_HML": r.b_HML, "t_HML": r.t_HML})
save_csv(pd.DataFrame(t1q2), "q2_table1")
# strategies across hedge sets, corrected baseline, 5 and 5
wide = []
for s in STRATS:
    for p in MAIN_WINDOWS:
        row = {"Strategy": SHORT[s], "Window": "Post-2010" if p == "post2010" else "Holdout"}
        for h in ["FF3", "FF3U", "FF5U", "FF5UC"]:
            r = sg("L5", "corr", h, "team", eid=f"E:{h}", periods=[p]).query("strategy == @s").iloc[0]
            row[HEDGE_LABEL[h].replace(" (team)", "")] = f"{100 * r.alpha_ann:.2f} ({r.t_alpha:.2f})"
        r = sg("L5", "corr", "FF5UC", "team", eid="E:FF5UC+cmdty", periods=[p]).query("strategy == @s").iloc[0]
        row["+WTI, IMF"] = f"{100 * r.alpha_ann:.2f} ({r.t_alpha:.2f})"
        wide.append(row)
save_tex(pd.DataFrame(wide), "q2_strategy_controls",
         caption="Net alpha (\\% p.a., NW(6) t in parentheses) of each strategy when the hedge and the evaluation regression use the "
                 "same traded control set; corrected baseline, 5-and-5 legs, team costs. The last column keeps the FF5+UMD+COMEQ "
                 "hedge and adds demeaned WTI and IMF commodity changes to the evaluation regression.",
         label="tab:m2_strategy_controls")
save_csv(pd.DataFrame(wide), "q2_strategy_controls_wide")
# hedge-cost and residual-HML summary by hedge set (team costs, 5 and 5, post2010)
hc = []
for b in BASES:
    for h in HEDGES:
        for s in STRATS:
            r = sg("L5", b, h, "team", eid=f"E:{h}", periods=["post2010"]).query("strategy == @s").iloc[0]
            hc.append({"baseline": b, "hedge": h, "strategy": SHORT[s], "ann_turnover": r.perf_ann_turnover,
                       "ann_overlay_turnover": r.perf_ann_overlay_turnover, "ann_cost_drag": r.perf_ann_cost_drag,
                       "ann_gross": r.perf_ann_gross, "ann_net": r.perf_ann_net, "alpha_ann": r.alpha_ann, "t_alpha": r.t_alpha,
                       "b_HML": r.b_HML, "t_HML": r.t_HML})
HC = pd.DataFrame(hc)
save_csv(HC, "q2_hedge_cost_post2010")
# change from the FF3 hedge to the FF5+UMD+COMEQ hedge, post2010. "total" turnover = asset + overlay; "overlay" = factor legs only
hcc = []
for b in BASES:
    for s in STRATS:
        a_ = HC[(HC.baseline == b) & (HC.hedge == "FF3") & (HC.strategy == SHORT[s])].iloc[0]
        c_ = HC[(HC.baseline == b) & (HC.hedge == "FF5UC") & (HC.strategy == SHORT[s])].iloc[0]
        hcc.append({"baseline": b, "strategy": SHORT[s],
                    "total_turnover_FF3": a_.ann_turnover, "total_turnover_FF5UC": c_.ann_turnover,
                    "total_turnover_change_pct": 100 * (c_.ann_turnover / a_.ann_turnover - 1),
                    "overlay_turnover_FF3": a_.ann_overlay_turnover, "overlay_turnover_FF5UC": c_.ann_overlay_turnover,
                    "overlay_turnover_change_pct": 100 * (c_.ann_overlay_turnover / a_.ann_overlay_turnover - 1),
                    "cost_drag_FF3": a_.ann_cost_drag, "cost_drag_FF5UC": c_.ann_cost_drag,
                    "gross_FF3": a_.ann_gross, "gross_FF5UC": c_.ann_gross})
save_csv(pd.DataFrame(hcc), "q2_hedge_cost_change")

# ============================================================================ Q3: source of the HML loading
INDS = {"Green": list(D.legs["L5"][0]), "Brown": list(D.legs["L5"][1])}
EXTRA = {"Green": ["Autos", "Insur", "Hardw", "MedEq"], "Brown": ["Chems", "Trans", "Mines"]}
Q3_WIN = ["full_1970", "post2010", "validation", "holdout"]
Q3_MODELS = {"FF3": "FF3", "FF5U": "FF5U"}
ind_rows = []
for side in ("Green", "Brown"):
    for nm in INDS[side] + EXTRA[side]:
        y = D.ind[nm] - D.ff3["RF"]
        for m in Q3_MODELS:
            for p in Q3_WIN:
                a, e = window(p)
                f = nw_fit(y.loc[a:e], D.eval_X(m))
                core = nm in INDS[side]
                ind_rows.append({"industry": nm, "side": side, "in_5x5": core, "model": m, "period": p, **f})
                for c in ["const"] + HEDGE_COLS[m]:
                    stat = f.get("t_alpha") if c == "const" else f.get(f"t_{c}")
                    pv = f.get("p_alpha") if c == "const" else f.get(f"p_{c}")
                    val = f.get("alpha_ann") if c == "const" else f.get(f"b_{c}")
                    LED.add(f"industry|{nm}|{m}|{p}|{c}", "Q3", f"t_{'alpha' if c == 'const' else 'b_' + c}_NW6", stat, pv, f.get("n"),
                            "exploratory", f"{'alpha_ann' if c == 'const' else 'b_' + c}={val:.4f}; {nm} excess return on "
                            f"{HEDGE_LABEL[m]}, window {f['start']:%Y-%m}..{f['end']:%Y-%m}; {side} side{'' if core else ' (8-and-8 addition)'}")
IR = pd.DataFrame(ind_rows)
save_csv(IR, "q3_industry_loadings")

# exact decomposition: b_HML(GB) = mean(b_HML green) - mean(b_HML brown)
dec = []
for l in LEGS:
    g, b = D.legs[l]
    for m in Q3_MODELS:
        for p in Q3_WIN:
            a, e = window(p)
            direct = nw_fit(GB[l].loc[a:e], D.eval_X(m))
            tot = 0.0
            for side, names in (("Green", g), ("Brown", b)):
                for nm in names:
                    r = IR[(IR.industry == nm) & (IR.model == m) & (IR.period == p)]
                    if len(r):
                        bh_ = r.iloc[0]["b_HML"]; th_ = r.iloc[0]["t_HML"]
                    else:  # industry only in 8/8 legs not in the regression table
                        f = nw_fit((D.ind[nm] - D.ff3["RF"]).loc[a:e], D.eval_X(m)); bh_, th_ = f["b_HML"], f["t_HML"]
                    contrib = (bh_ if side == "Green" else -bh_) / len(names)
                    tot += contrib
                    dec.append({"legs": l, "model": m, "period": p, "industry": nm, "side": side, "b_HML": bh_, "t_HML": th_,
                                "contribution": contrib})
            for r_ in dec[-(len(g) + len(b)):]:
                r_["share_of_total"] = r_["contribution"] / tot
                r_["gb_b_HML_direct"] = direct["b_HML"]
                r_["gb_t_HML_direct"] = direct["t_HML"]
                r_["decomposition_error"] = tot - direct["b_HML"]
DEC = pd.DataFrame(dec)
assert DEC.decomposition_error.abs().max() < 1e-10, DEC.decomposition_error.abs().max()
save_csv(DEC, "q3_hml_decomposition")
# drivers (pre-specified: largest absolute contribution, post2010, FF3, 5 and 5)
drv = DEC[(DEC.legs == "L5") & (DEC.model == "FF3") & (DEC.period == "post2010")].copy()
drv["abs"] = drv.contribution.abs()
DRIVERS = drv.sort_values("abs", ascending=False).head(2).industry.tolist()

# tex: HML loadings and contributions, 5 and 5
tw = []
for side in ("Green", "Brown"):
    for nm in INDS[side]:
        row = {"Industry": nm, "Leg": side}
        for m in Q3_MODELS:
            for p, pl in (("full_1970", "Full"), ("post2010", "Post-2010"), ("validation", "Val"), ("holdout", "Hold")):
                r = DEC[(DEC.legs == "L5") & (DEC.model == m) & (DEC.period == p) & (DEC.industry == nm)].iloc[0]
                row[f"{'FF3' if m == 'FF3' else 'FF5U'} {pl}"] = f"{r.b_HML:.2f} ({r.t_HML:.1f})"
        tw.append(row)
row = {"Industry": "GB spread", "Leg": ""}
for m in Q3_MODELS:
    for p, pl in (("full_1970", "Full"), ("post2010", "Post-2010"), ("validation", "Val"), ("holdout", "Hold")):
        r = DEC[(DEC.legs == "L5") & (DEC.model == m) & (DEC.period == p)].iloc[0]
        row[f"{'FF3' if m == 'FF3' else 'FF5U'} {pl}"] = f"{r.gb_b_HML_direct:.2f} ({r.gb_t_HML_direct:.1f})"
tw.append(row)
save_tex(pd.DataFrame(tw), "q3_industry_hml",
         caption="HML loading (NW(6) t in parentheses) of each 5-and-5 leg industry's excess return, under FF3 and FF5+UMD. "
                 "Full = 1970-01 to 2026-07, Val = 2010-01 to 2022-07, Hold = 2022-08 to 2026-07. The last row is the "
                 "Green-minus-Brown spread, which equals the mean Green loading minus the mean Brown loading.",
         label="tab:m2_industry_hml")
cw = []
for side in ("Green", "Brown"):
    for nm in INDS[side]:
        row = {"Industry": nm, "Leg": side}
        for m in Q3_MODELS:
            for p, pl in (("full_1970", "Full"), ("post2010", "Post-2010"), ("validation", "Val"), ("holdout", "Hold")):
                r = DEC[(DEC.legs == "L5") & (DEC.model == m) & (DEC.period == p) & (DEC.industry == nm)].iloc[0]
                row[f"{'FF3' if m == 'FF3' else 'FF5U'} {pl}"] = r.contribution
        cw.append(row)
row = {"Industry": "Total = GB loading", "Leg": ""}
for m in Q3_MODELS:
    for p, pl in (("full_1970", "Full"), ("post2010", "Post-2010"), ("validation", "Val"), ("holdout", "Hold")):
        row[f"{'FF3' if m == 'FF3' else 'FF5U'} {pl}"] = DEC[(DEC.legs == "L5") & (DEC.model == m) & (DEC.period == p)].contribution.sum()
cw.append(row)
CW = pd.DataFrame(cw)
save_csv(CW, "q3_hml_contributions_wide")
save_tex(CW, "q3_hml_contributions",
         caption="Contribution of each industry to the Green-minus-Brown HML loading: +loading/5 for Green industries, "
                 "-loading/5 for Brown industries. Contributions sum exactly to the spread's loading (last row).",
         label="tab:m2_hml_contrib")

# rolling 60-month HML betas (FF3 and FF5+UMD), windows ending at t (descriptive, not a trading input)
roll = {}
for m in Q3_MODELS:
    X = D.eval_X(m)
    cols = {}
    for nm in INDS["Green"] + INDS["Brown"]:
        bet = rolling_factor_model(D.ind[nm] - D.ff3["RF"], X, 60)[0]
        cols[nm] = bet["HML"]
    cols["Green leg"] = rolling_factor_model(D.ind[INDS["Green"]].mean(axis=1) - D.ff3["RF"], X, 60)[0]["HML"]
    cols["Brown leg"] = rolling_factor_model(D.ind[INDS["Brown"]].mean(axis=1) - D.ff3["RF"], X, 60)[0]["HML"]
    cols["Green-Brown"] = rolling_factor_model(GB["L5"], X, 60)[0]["HML"]
    roll[m] = pd.DataFrame(cols)
ROLL = pd.concat(roll, axis=1)
ROLL.columns = [f"{m}|{c}" for m, c in ROLL.columns]
save_csv(ROLL.loc["1970-01-31":].reset_index(names="date"), "q3_rolling_hml")
rs = []
for m in Q3_MODELS:
    r_ = roll[m]
    for era, (a, e) in {"1975-2026": ("1975-01-31", END), "1975-2009": ("1975-01-31", "2009-12-31"), "2010-2026": ("2010-01-31", END),
                        "2022-08-2026": ("2022-08-31", END)}.items():
        for c in r_.columns:
            s = r_[c].loc[a:e].dropna()
            rs.append({"model": m, "era": era, "series": c, "n_windows": len(s), "mean": s.mean(), "min": s.min(), "max": s.max(),
                       "share_negative": (s < 0).mean()})
RS = pd.DataFrame(rs)
save_csv(RS, "q3_rolling_summary")
# runs of consecutive windows (ending 1975-01..2026-07) with a positive GB rolling HML beta, and leg betas at each run's peak
runs = []
for m in Q3_MODELS:
    r_ = roll[m].loc["1975-01-31":END]
    gbb = r_["Green-Brown"].dropna()
    grp = (gbb.le(0)).cumsum()
    for _, seg in gbb[gbb > 0].groupby(grp[gbb > 0]):
        pk = seg.idxmax()
        runs.append({"model": m, "first_window_end": seg.index.min(), "last_window_end": seg.index.max(), "n_windows": len(seg),
                     "peak_window_end": pk, "peak_gb_beta": seg.max(), "green_leg_beta_at_peak": r_.loc[pk, "Green leg"],
                     "brown_leg_beta_at_peak": r_.loc[pk, "Brown leg"],
                     **{f"{nm}_beta_at_peak": r_.loc[pk, nm] for nm in INDS["Green"] + INDS["Brown"]}})
save_csv(pd.DataFrame(runs), "q3_rolling_positive_runs")

# characteristics: log BE/ME (sum BE / sum ME), annual at June; relative to the cross-industry median
bm = load_kf_industries("be_me_sum")
lbm = np.log(bm.where(bm > 0))
rel = lbm.sub(lbm.median(axis=1), axis=0)
bmdf = pd.DataFrame({**{f"logbm|{c}": lbm[c] for c in INDS["Green"] + INDS["Brown"]},
                     **{f"rel|{c}": rel[c] for c in INDS["Green"] + INDS["Brown"]},
                     "rel|Green avg": rel[INDS["Green"]].mean(axis=1), "rel|Brown avg": rel[INDS["Brown"]].mean(axis=1)})
bmdf["rel|Green minus Brown"] = bmdf["rel|Green avg"] - bmdf["rel|Brown avg"]
bmdf["median_logbm_49"] = lbm.median(axis=1)
save_csv(bmdf.loc["1970":].reset_index(names="june_of_year"), "q3_log_bm")
# links: rolling FF3 HML beta at June Y vs relative log BE/ME at June Y
june = roll["FF3"].loc[roll["FF3"].index.month == 6]
june.index = pd.to_datetime(june.index.year.astype(str) + "-06-30")
link = []
yrs = slice("1975-06-30", "2026-06-30")
for nm in INDS["Green"] + INDS["Brown"] + ["Green-Brown"]:
    xb = june[nm].loc[yrs]
    xc = (bmdf["rel|Green minus Brown"] if nm == "Green-Brown" else bmdf[f"rel|{nm}"]).loc[yrs]
    d = pd.concat([xb.rename("beta"), xc.rename("bm")], axis=1).dropna()
    fz = nw_fit((d.beta - d.beta.mean()) / d.beta.std(), ((d.bm - d.bm.mean()) / d.bm.std()).to_frame("bm"), lags=4)
    link.append({"series": nm, "n_years": len(d), "corr": d.beta.corr(d.bm), "slope_z": fz.get("b_bm"), "t_slope_nw4": fz.get("t_bm"),
                 "p": fz.get("p_bm"), "mean_rel_logbm": d.bm.mean(), "share_rel_logbm_negative": (d.bm < 0).mean(),
                 "mean_beta": d.beta.mean()})
    LED.add(f"bmlink|{nm}", "Q3", "t_slope_NW4", fz.get("t_bm"), fz.get("p_bm"), len(d), "exploratory",
            f"time-series slope of June rolling FF3 HML beta on relative log BE/ME (both z-scored), {nm}, 1975-2026, NW(4) annual")
# cross-sectional (all 49 industries) each June: corr(rolling HML beta, log BE/ME); average over years
allb = {}
for nm in D.ind.columns:
    y = D.ind[nm] - D.ff3["RF"]
    if y.loc["1970":].isna().mean() > 0.5:
        continue
    allb[nm] = rolling_factor_model(y, D.eval_X("FF3"), 60)[0]["HML"]
allb = pd.DataFrame(allb)
allj = allb.loc[allb.index.month == 6]
allj.index = pd.to_datetime(allj.index.year.astype(str) + "-06-30")
cs = []
for yv in allj.loc[yrs].index:
    d = pd.concat([allj.loc[yv].rename("beta"), rel.loc[yv].rename("bm")], axis=1).dropna()
    cs.append({"june": yv, "n_ind": len(d), "corr": d.beta.corr(d.bm, method="spearman")})
CS = pd.DataFrame(cs).set_index("june")
fcs = nw_fit(CS["corr"], None, lags=4)
link.append({"series": "Cross-section of 49 industries (mean yearly Spearman corr)", "n_years": len(CS), "corr": CS["corr"].mean(),
             "slope_z": np.nan, "t_slope_nw4": fcs["t_alpha"], "p": fcs["p_alpha"], "mean_rel_logbm": np.nan,
             "share_rel_logbm_negative": np.nan, "mean_beta": np.nan})
LED.add("bmlink|cross_section_49", "Q3", "t_mean_corr_NW4", fcs["t_alpha"], fcs["p_alpha"], len(CS), "exploratory",
        f"mean yearly Spearman corr across industries of June rolling FF3 HML beta and relative log BE/ME = {CS['corr'].mean():.3f}, 1975-2026")
LINK = pd.DataFrame(link)
save_csv(LINK, "q3_bm_link")
save_csv(CS.reset_index(), "q3_bm_cross_section")

# ============================================================================ Q4: uniform costs
q4 = []
for b in BASES:
    for h in ("FF3", "FF5UC"):
        for c in ["team"] + COSTS_Q4:
            x = sg("L5", b, h, c, eid=f"E:{h}", periods=["full_live", "post2010", "validation", "holdout"])
            if c != "u0":
                x = pd.concat([x[x.period.isin(["full_live", "post2010", "validation", "holdout"])],
                               sg("L5", b, h, c, eid="E:FF3", periods=SHORT_PERIODS)])
            for _, r in x.iterrows():
                q4.append({"baseline": b, "hedge": h, "costs": c, "strategy": r.strat, "period": r.period, "eval": r.eval_id,
                           "n": r.n, "ann_net": r.perf_ann_net, "sharpe": r.perf_sharpe, "t_mean": r.perf_t_mean,
                           "alpha_ann": r.alpha_ann, "t_alpha": r.t_alpha, "p_alpha": r.p_alpha,
                           "ann_turnover": r.perf_ann_turnover, "ann_asset_turnover": r.perf_ann_asset_turnover,
                           "ann_overlay_turnover": r.perf_ann_overlay_turnover, "ann_cost_drag": r.perf_ann_cost_drag})
Q4 = pd.DataFrame(q4)
save_csv(Q4, "q4_costs")
be = []
for b in BASES:
    for h in ("FF3", "FF5UC"):
        for s in STRATS:
            row = {"baseline": b, "hedge": h, "strategy": SHORT[s]}
            for p in ["validation", "post2010", "holdout", "full_live"]:
                g_ = Q4[(Q4.baseline == b) & (Q4.hedge == h) & (Q4.strategy == SHORT[s]) & (Q4.period == p) & (Q4["eval"] == f"E:{h}")].set_index("costs")
                a0, a10 = g_.loc["u0", "alpha_ann"], g_.loc["u10", "alpha_ann"]
                slope = (a0 - a10) / 10.0  # alpha lost per bp of uniform cost (exactly linear)
                lin = max(abs(g_.loc[c_, "alpha_ann"] - (a0 - slope * int(c_[1:]))) for c_ in ("u5", "u25"))
                assert lin < 1e-12, lin
                m0, m10 = g_.loc["u0", "ann_net"], g_.loc["u10", "ann_net"]
                row[f"{p}_gross_alpha"] = a0
                row[f"{p}_alpha_loss_per_bp"] = slope
                row[f"{p}_breakeven_bp"] = a0 / slope if (a0 > 0 and slope > 0) else np.nan
                row[f"{p}_breakeven_mean_bp"] = m0 / ((m0 - m10) / 10) if (m0 > 0 and m0 > m10) else np.nan
                row[f"{p}_ann_turnover"] = g_.loc["u10", "ann_turnover"]
            be.append(row)
BE = pd.DataFrame(be)
save_csv(BE, "q4_breakeven")
for b in BASES:
    w = []
    for s in STRATS:
        row = {"Strategy": SHORT[s]}
        for p, pl in (("validation", "Val"), ("holdout", "Hold")):
            for c in ("u5", "u10", "u25"):
                r = Q4[(Q4.baseline == b) & (Q4.hedge == "FF3") & (Q4.costs == c) & (Q4.strategy == SHORT[s]) & (Q4.period == p) & (Q4["eval"] == "E:FF3")].iloc[0]
                row[f"{pl} {c[1:]}bp"] = f"{100 * r.alpha_ann:.2f} ({r.t_alpha:.2f})"
        rb = BE[(BE.baseline == b) & (BE.hedge == "FF3") & (BE.strategy == SHORT[s])].iloc[0]
        row["Turnover"] = f"{rb.validation_ann_turnover:.1f}"
        row["Break-even bp"] = "none" if pd.isna(rb.validation_breakeven_bp) else f"{rb.validation_breakeven_bp:.0f}"
        w.append(row)
    save_tex(pd.DataFrame(w), f"q4_costs_{b}",
             caption=f"FF3 alpha (\\% p.a., NW(6) t in parentheses) at uniform costs of 5, 10 and 25 bp per unit of turnover "
                     f"(asset and every overlay factor), {BASE_LABEL[b]}, 5-and-5 legs, FF3 hedge. Turnover is annual validation "
                     "turnover (asset plus overlay). Break-even is the uniform cost at which validation alpha reaches zero; "
                     "none = gross validation alpha is not positive.",
             label=f"tab:m2_costs_{b}")
    save_csv(pd.DataFrame(w), f"q4_costs_{b}_wide")
Q4P = primary_family(("L5", "corr", "FF3", "u5"), "q4_primary")

# ============================================================================ ledger, grid-wide multiple testing, summary
LEDF = LED.frame()
is_alpha = LEDF.statistic_name.eq("t_alpha_NW6") & ~LEDF.note.str.contains("gross zero-cost") & LEDF.test_id.str.match(r"^(strat|spread)\|")
fam = LEDF[is_alpha & LEDF.p_value_two_sided.notna()].copy()
fam["holm_grid"] = holm(fam.p_value_two_sided)
fam["bh_grid"] = bh(fam.p_value_two_sided)
N_GRID = len(fam)
N_GRID_STRAT = int(fam.test_id.str.startswith("strat|").sum())
N_GRID_SPREAD = int(fam.test_id.str.startswith("spread|").sum())
assert N_GRID_STRAT + N_GRID_SPREAD == N_GRID
save_csv(LEDF, "tests_ledger")

# primary families summary (Q1, Q2, Q4) and Q3 HML primary
PR = pd.concat([Q1P, Q2P, Q4P], ignore_index=True)
save_csv(PR, "primary_all")
q3p = SP[(SP.legs == "L5") & SP.eval_id.isin(["E:FF3", "E:FF5U"]) & SP.period.isin(["full_1970", "post2010"])][
    ["period", "eval_id", "n", "b_HML", "t_HML", "p_HML", "alpha_ann", "t_alpha"]].copy()
q3p["holm_p_HML"] = holm(q3p.p_HML).values
q3p["drivers_post2010_ff3"] = ", ".join(DRIVERS)
save_csv(q3p, "q3_primary")

# best-case evidence per strategy (implementable net-of-cost grid only)
SGn = SG[(SG.costs != "u0") & SG.p_alpha.notna()].copy()
SGn["test_id"] = ("strat|" + SGn.legs + "|" + SGn.baseline + "|" + SGn.hedge + "|" + SGn.costs + "|" + SGn.strat + "|" + SGn.period
                  + "|" + SGn.eval_id + "|alpha")
SGn = SGn.merge(fam[["test_id", "holm_grid", "bh_grid"]], on="test_id", how="left")
SPn = SP[SP.p_alpha.notna()].copy()
SPn["test_id"] = "spread|" + SPn.legs + "|" + SPn.period + "|" + SPn.eval_id + "|alpha"
SPn = SPn.merge(fam[["test_id", "holm_grid", "bh_grid"]], on="test_id", how="left")
summ = []
for s in STRATS + ["GB spread"]:
    x = SGn[SGn.strategy == s] if s != "GB spread" else SPn
    xp = x[x.alpha_ann > 0]
    row = {"strategy": SHORT.get(s, "Raw GB spread (unhedged)"), "n_tests_in_grid": len(x), "share_positive_alpha": (x.alpha_ann > 0).mean()}
    for lab, sel in (("any", xp), ("post2010", xp[xp.period == "post2010"]), ("holdout", xp[xp.period == "holdout"])):
        if len(sel) == 0:
            row.update({f"best_{lab}_t": np.nan})
            continue
        r = sel.sort_values("t_alpha", ascending=False).iloc[0]
        cfg = (f"{r.legs}|{r.baseline}|{r.hedge}|{r.costs}|{r.eval_id}" if s != "GB spread" else f"{r.legs}|{r.eval_id}")
        row.update({f"best_{lab}_config": cfg, f"best_{lab}_period": r.period, f"best_{lab}_alpha_ann": r.alpha_ann,
                    f"best_{lab}_t": r.t_alpha, f"best_{lab}_n": r.n, f"best_{lab}_p": r.p_alpha,
                    f"best_{lab}_holm_grid": r.holm_grid, f"best_{lab}_bh_grid": r.bh_grid})
    if s in STRATS:
        for q, P in (("Q1", Q1P), ("Q2", Q2P), ("Q4", Q4P)):
            for p in MAIN_WINDOWS:
                r = P[(P.strat == SHORT[s]) & (P.period == p)].iloc[0]
                row[f"{q}_{p}_alpha_ann"] = r.alpha_ann
                row[f"{q}_{p}_t"] = r.t_alpha
                row[f"{q}_{p}_holm_p"] = r.holm_p
    row["survives_holm_grid"] = bool(((x.alpha_ann > 0) & (x.holm_grid < 0.05)).any())
    row["survives_bh_grid"] = bool(((x.alpha_ann > 0) & (x.bh_grid < 0.05)).any())
    summ.append(row)
SUMM = pd.DataFrame(summ)
save_csv(SUMM, "summary_best_case")
PERIOD_LABEL = {"full_1970": "1970-2026", "full_live": "full live", "post2010": "2010-2026", "validation": "validation",
                "holdout": "holdout", "pre_covid": "2010-2019", "covid": "COVID 2020-21", "inflation_rates": "2022-2024",
                "last18": "last 18m", "last12": "last 12m"}
sw = []
for _, r in SUMM.iterrows():
    sw.append({"Strategy": r.strategy,
               "Best any window": "--" if pd.isna(r.get("best_any_t")) else f"{100 * r.best_any_alpha_ann:.2f} ({r.best_any_t:.2f}), {PERIOD_LABEL.get(r.best_any_period, r.best_any_period)}",
               "Best post-2010": "--" if pd.isna(r.get("best_post2010_t")) else f"{100 * r.best_post2010_alpha_ann:.2f} ({r.best_post2010_t:.2f})",
               "Best holdout": "--" if pd.isna(r.get("best_holdout_t")) else f"{100 * r.best_holdout_alpha_ann:.2f} ({r.best_holdout_t:.2f})",
               "Grid Holm p (best)": fmt_p(r.get("best_any_holm_grid")),
               "Q2 primary Holm p (post-2010 / holdout)": "--" if pd.isna(r.get("Q2_post2010_holm_p")) else
               f"{fmt_p(r.Q2_post2010_holm_p)} / {fmt_p(r.Q2_holdout_holm_p)}",
               "Survives": "yes" if r.survives_holm_grid else "no"})
save_tex(pd.DataFrame(sw), "summary_best_case",
         caption=f"Best-case evidence per strategy over the whole M2 grid of {N_GRID:,} alpha tests ({N_GRID_STRAT:,} net-of-cost "
                 f"strategy alphas and {N_GRID_SPREAD} raw-spread alphas, which are unhedged and cost-free), over all leg designs, "
                 "baselines, hedge sets, evaluation sets, cost levels and windows. Alpha in \\% p.a. with NW(6) t in parentheses; "
                 "grid Holm p is the Holm-adjusted p of the single best test. Q2 primary: corrected baseline, 5-and-5, "
                 "FF5+UMD+COMEQ hedge and alpha, Holm over 14 tests.",
         label="tab:m2_summary")

# key numbers for FINDINGS traceability
kn = {"n_pipeline_runs": len(RES), "n_strategy_regressions": len(SG), "n_ledger_tests": len(LEDF), "n_grid_alpha_family": N_GRID,
      "grid_holm_survivors_positive": int(((fam.holm_grid < 0.05) & fam.note.str.contains(r"alpha_ann=[0-9]")).sum()),
      "grid_bh_survivors_positive": int(((fam.bh_grid < 0.05) & fam.note.str.contains(r"alpha_ann=[0-9]")).sum()),
      "grid_holm_survivors_negative": int(((fam.holm_grid < 0.05) & fam.note.str.contains(r"alpha_ann=-")).sum()),
      "grid_bh_survivors_negative": int(((fam.bh_grid < 0.05) & fam.note.str.contains(r"alpha_ann=-")).sum()),
      "min_grid_p": fam.p_value_two_sided.min(), "min_grid_holm": fam.holm_grid.min(),
      "q1_primary_survivors": int(Q1P.positive_and_holm_sig.sum()), "q2_primary_survivors": int(Q2P.positive_and_holm_sig.sum()),
      "q4_primary_survivors": int(Q4P.positive_and_holm_sig.sum()), "q3_drivers": ", ".join(DRIVERS),
      "tie_warning": D.tie_warning}
fam["period"] = fam.test_id.str.split("|").map(lambda z: z[6] if z[0] == "strat" else z[2])
neg_bh = fam[(fam.bh_grid < 0.05) & fam.note.str.contains(r"alpha_ann=-")]
kn["grid_bh_negative_by_period"] = "; ".join(f"{k}:{v}" for k, v in neg_bh.period.value_counts().items())
pos = fam[fam.note.str.contains(r"alpha_ann=[0-9]")].sort_values("p_value_two_sided")
kn["best_positive_grid_test"] = pos.test_id.iloc[0]
kn["best_positive_grid_p"] = pos.p_value_two_sided.iloc[0]
kn["best_positive_grid_holm"] = pos.holm_grid.iloc[0]
kn["best_positive_grid_bh"] = pos.bh_grid.iloc[0]
pos_main = pos[pos.period.isin(["post2010", "holdout"])]
kn["best_positive_post2010_or_holdout_test"] = pos_main.test_id.iloc[0]
kn["best_positive_post2010_or_holdout_p"] = pos_main.p_value_two_sided.iloc[0]
kn["best_positive_post2010_or_holdout_holm"] = pos_main.holm_grid.iloc[0]
kn["n_grid_positive_p_below_05"] = int((pos.p_value_two_sided < 0.05).sum())
kn["n_grid_negative_p_below_05"] = int((fam.note.str.contains(r"alpha_ann=-") & (fam.p_value_two_sided < 0.05)).sum())
kn["n_grid_strategy_alphas_net_of_cost"] = N_GRID_STRAT
kn["n_grid_raw_spread_alphas_unhedged_cost_free"] = N_GRID_SPREAD
# holdout sign census over every strategy regression (net-of-cost runs and, separately, the zero-cost runs)
hold = SG[(SG.period == "holdout") & SG.alpha_ann.notna()]
hn, hg = hold[hold.costs != "u0"], hold[hold.costs == "u0"]
hpos = hn[hn.alpha_ann > 0]
kn["holdout_net_regressions"] = len(hn)
kn["holdout_net_positive"] = len(hpos)
kn["holdout_net_positive_signal_rules"] = int((hpos.strat != "Always-short Brown").sum())
kn["holdout_net_positive_strategies"] = ", ".join(sorted(hpos.strat.unique()))
kn["holdout_net_positive_legs"] = ", ".join(sorted(hpos.legs.unique()))
kn["holdout_net_positive_hedges"] = ", ".join(sorted(hpos.hedge.unique()))
kn["holdout_net_positive_evals"] = ", ".join(sorted(hpos.eval_id.unique()))
kn["holdout_net_max_alpha"] = hn.alpha_ann.max()
kn["holdout_net_max_alpha_t"] = hn.loc[hn.alpha_ann.idxmax(), "t_alpha"]
hmax = hn.loc[hn.alpha_ann.idxmax()]
kn["holdout_net_max_alpha_config"] = f"{hmax.strat}|{hmax.legs}|{hmax.baseline}|{hmax.hedge}|{hmax.costs}|{hmax.eval_id}"
hs = hn[hn.strat != "Always-short Brown"]
kn["holdout_net_max_signal_rule_alpha"] = hs.alpha_ann.max()
smax = hs.loc[hs.alpha_ann.idxmax()]
kn["holdout_net_max_signal_rule_config"] = f"{smax.strat}|{smax.legs}|{smax.baseline}|{smax.hedge}|{smax.costs}|{smax.eval_id}"
kn["holdout_gross_regressions"] = len(hg)
kn["holdout_gross_configs"] = "; ".join(sorted({f"{a}|{b}" for a, b in zip(hg.legs, hg.hedge)}))
kn["holdout_gross_positive"] = int((hg.alpha_ann > 0).sum())
gmax = hg.loc[hg.alpha_ann.idxmax()]
kn["holdout_gross_max_alpha"] = gmax.alpha_ann
kn["holdout_gross_max_alpha_config"] = f"{gmax.strat}|{gmax.legs}|{gmax.baseline}|{gmax.hedge}|{gmax.eval_id}"
kn["holdout_gross_max_alpha_t"] = gmax.t_alpha
# ledger composition by label
for kind_, n_ in LEDF.primary_or_exploratory.value_counts().items():
    kn[f"n_ledger_{kind_}"] = int(n_)
save_csv(pd.Series(kn, name="value").rename_axis("key").reset_index(), "key_numbers")
fam_out = fam[["test_id", "p_value_two_sided", "holm_grid", "bh_grid", "note"]]
save_csv(fam_out.sort_values("p_value_two_sided").head(40), "grid_top40")
print(f"[M2] tables done, {len(LEDF)} ledger tests, grid alpha family {N_GRID}, {time.perf_counter() - T0:.1f}s")

# ============================================================================ figures
from plotstyle import *  # noqa: E402,F401,F403
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

IND_COLOR = {**dict(zip(INDS["Green"], SERIES[:5])), **dict(zip(INDS["Brown"], SERIES[:5]))}

# (1) rolling 60-month FF3 HML betas by industry
fig, axes = plt.subplots(2, 1, figsize=(8.2, 6.2), sharex=True)
for ax, side in zip(axes, ("Green", "Brown")):
    for nm in INDS[side]:
        s = roll["FF3"][nm].loc["1975-01-31":]
        ax.plot(s.index, s, color=IND_COLOR[nm], label=nm, lw=1.3 if nm in DRIVERS else 1.0)
    ax.axhline(0, color=MUTED, lw=0.8)
    ax.axvspan(pd.Timestamp("2022-08-31"), pd.Timestamp(END), color=NEUTRAL_MID, zorder=0)
    ax.set_title(f"{side} leg industries: rolling 60-month HML beta (FF3)", loc="left")
    ax.set_ylabel("HML beta")
    ax.legend(loc="center left", bbox_to_anchor=(1.0, 0.5))
axes[-1].text(pd.Timestamp("2022-10-31"), axes[-1].get_ylim()[0] * 0.92, "holdout", color=INK2, fontsize=7)
savefig(fig, f"{MODULE}_rolling_hml_industries")

# (2) spread decomposition over time + characteristic tilt
fig, axes = plt.subplots(2, 1, figsize=(8.4, 5.8), sharex=True)
ax = axes[0]
for c, col in (("Green leg", ENTITY["green"]), ("Brown leg", ENTITY["brown"]), ("Green-Brown", ENTITY["green_minus_brown"])):
    s = roll["FF3"][c].loc["1975-01-31":]
    ax.plot(s.index, s, color=col, label=c, lw=1.6 if c == "Green-Brown" else 1.2)
ax.axhline(0, color=MUTED, lw=0.8)
ax.set_title("Rolling 60-month HML beta (FF3): legs and spread", loc="left"); ax.set_ylabel("HML beta")
ax.legend(loc="center left", bbox_to_anchor=(1.0, 0.5))
ax = axes[1]
for c, col in (("rel|Green avg", ENTITY["green"]), ("rel|Brown avg", ENTITY["brown"]), ("rel|Green minus Brown", ENTITY["green_minus_brown"])):
    s = bmdf[c].loc["1975":]
    ax.plot(s.index, s, color=col, label=c.split("|")[1], lw=1.6 if "minus" in c else 1.2, marker="o", ms=2.5)
ax.axhline(0, color=MUTED, lw=0.8)
ax.set_title("log BE/ME relative to the 49-industry median (June of each year)", loc="left"); ax.set_ylabel("log BE/ME minus median")
ax.legend(loc="center left", bbox_to_anchor=(1.0, 0.5))
savefig(fig, f"{MODULE}_hml_spread_and_bm")

# (3) log BE/ME by industry
fig, axes = plt.subplots(2, 1, figsize=(8.4, 5.8), sharex=True)
for ax, side in zip(axes, ("Green", "Brown")):
    for nm in INDS[side]:
        s = bmdf[f"rel|{nm}"].loc["1975":]
        ax.plot(s.index, s, color=IND_COLOR[nm], label=nm, lw=1.3 if nm in DRIVERS else 1.0)
    ax.axhline(0, color=MUTED, lw=0.8)
    ax.set_title(f"{side} leg industries: log BE/ME relative to the 49-industry median", loc="left")
    ax.set_ylabel("log BE/ME minus median"); ax.legend(loc="center left", bbox_to_anchor=(1.0, 0.5))
savefig(fig, f"{MODULE}_log_bm_industries")

# (4) contribution bars
fig, axes = plt.subplots(2, 4, figsize=(10, 5.8), sharey=True, sharex=True, layout="constrained")
order = INDS["Green"] + INDS["Brown"]
for i, m in enumerate(Q3_MODELS):
    for j, (p, pl) in enumerate((("full_1970", "1970-2026"), ("post2010", "2010-2026"), ("validation", "2010-2022/07"), ("holdout", "2022/08-2026"))):
        ax = axes[i, j]
        x = DEC[(DEC.legs == "L5") & (DEC.model == m) & (DEC.period == p)].set_index("industry").loc[order]
        cols = [ENTITY["green"] if sd == "Green" else ENTITY["brown"] for sd in x.side]
        ax.barh(range(len(order)), x.contribution, color=cols, height=0.7)
        ax.axvline(0, color=MUTED, lw=0.8)
        tot = x.contribution.sum()
        ax.set_title(f"{HEDGE_LABEL[m].replace(' (team)', '')}, {pl}\nspread loading {tot:.2f}", loc="left", fontsize=8.5)
        ax.set_yticks(range(len(order))); ax.set_yticklabels(order); ax.invert_yaxis()
        if i == 1:
            ax.set_xlabel("contribution to HML loading")
fig.legend(handles=[Line2D([], [], color=ENTITY["green"], lw=6, label="Green industry (+loading/5)"),
                    Line2D([], [], color=ENTITY["brown"], lw=6, label="Brown industry (-loading/5)")], loc="outside lower center", ncol=2)
savefig(fig, f"{MODULE}_hml_decomposition")

# (5) strategy alpha t across control sets (corrected baseline, 5 and 5)
sets = [("FF3", "E:FF3"), ("FF3U", "E:FF3U"), ("FF5U", "E:FF5U"), ("FF5UC", "E:FF5UC"), ("FF5UC", "E:FF5UC+cmdty")]
labels = ["FF3", "FF3+UMD", "FF5+UMD", "FF5+UMD+COMEQ", "FF5+UMD+COMEQ, eval + WTI, IMF"]
fig, axes = plt.subplots(1, 2, figsize=(9, 4.2), sharey=True, layout="constrained")
for ax, p in zip(axes, MAIN_WINDOWS):
    n_ = int(Q2P[Q2P.period == p].n.iloc[0]); k_ = int(Q2P[Q2P.period == p].k.iloc[0])
    crit = stats.t.isf(0.05 / 14 / 2, n_ - k_)
    for i, ((h, eid), lab) in enumerate(zip(sets, labels)):
        x = sg("L5", "corr", h, "team", eid=eid, periods=[p]).set_index("strategy").loc[STRATS]
        ax.scatter(x.t_alpha, np.arange(len(STRATS)) + (i - 2) * 0.12, color=SERIES[i], s=22, label=lab, zorder=3,
                   edgecolor=SURFACE, linewidth=0.6)
    ax.axvline(0, color=MUTED, lw=0.8)
    for v in (-1.96, 1.96):
        ax.axvline(v, color=MUTED, lw=0.8, ls="--")
    ax.axvline(crit, color=INK2, lw=0.9, ls=":")
    ax.text(crit, len(STRATS) - 0.4, f" Holm 1st step\n t = {crit:.2f}", color=INK2, fontsize=7, va="top")
    ax.set_yticks(range(len(STRATS))); ax.set_yticklabels([SHORT[s] for s in STRATS]); ax.invert_yaxis()
    ax.set_title(f"{'Post-2010 (2010-01 to 2026-07)' if p == 'post2010' else 'Holdout (2022-08 to 2026-07)'}", loc="left")
    ax.set_xlabel("alpha t-stat (NW 6 lags)")
h_, l_ = axes[0].get_legend_handles_labels()
fig.legend(h_, l_, loc="outside lower center", ncol=3)
savefig(fig, f"{MODULE}_alpha_t_by_controls")

# (6) cost sensitivity
fig, axes = plt.subplots(2, 2, figsize=(9, 6.4), sharey=True, layout="constrained")
cost_col = {"u0": MUTED, "u5": SEQ_BLUE[2], "u10": SEQ_BLUE[4], "u25": SEQ_BLUE[6]}
cost_lab = {"u0": "0 bp (gross)", "u5": "5 bp", "u10": "10 bp", "u25": "25 bp"}
for i, b in enumerate(BASES):
    for j, p in enumerate(["validation", "holdout"]):
        ax = axes[i, j]
        for k_, c in enumerate(COSTS_Q4):
            x = Q4[(Q4.baseline == b) & (Q4.hedge == "FF3") & (Q4.costs == c) & (Q4.period == p) & (Q4["eval"] == "E:FF3")].set_index("strategy")
            x = x.loc[[SHORT[s] for s in STRATS]]
            ax.scatter(100 * x.alpha_ann, np.arange(len(STRATS)), color=cost_col[c], s=26 if c != "u0" else 18,
                       marker="o" if c != "u0" else "|", label=cost_lab[c], zorder=3, edgecolor=SURFACE if c != "u0" else None, linewidth=0.6)
        ax.axvline(0, color=MUTED, lw=0.8)
        ax.set_yticks(range(len(STRATS))); ax.set_yticklabels([SHORT[s] for s in STRATS]); ax.invert_yaxis()
        ax.set_title(f"{BASE_LABEL[b].capitalize()}, {'validation 2010-2022/07' if p == 'validation' else 'holdout 2022/08-2026'}", loc="left")
        if i == 1:
            ax.set_xlabel("FF3 alpha, % per year")
h_, l_ = axes[0, 0].get_legend_handles_labels()
fig.legend(h_, l_, loc="outside lower center", ncol=4, title="uniform cost per unit of turnover")
savefig(fig, f"{MODULE}_cost_sensitivity")
print(f"[M2] done in {time.perf_counter() - T0:.1f}s")
