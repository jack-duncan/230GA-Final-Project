"""Round-2 gap checks for M1_signal_audit (does NOT import run.py or helpers.py).

Written by the round-2 verifier to cover what verify_m1.py and verify_m1_round2.py do not:
  G1  Q3 counterfactuals re-implemented with pandas rolling/expanding (no loops), plus other freeze dates (info)
  G2  does the "zeros did not change the holdout" result extend beyond the Original rule? Pure rule and the
      continuous variants rebuilt with the verified team pipeline building blocks under frozen 2021-09 scaling
  G3  FINDINGS numbers not covered elsewhere (Fisher state vs nonzero, 24m zero share, share summary, Q2 slopes,
      Q4 counts and rotation counts)
Run: cd /home/hashim/projects/GA/project/research && uv run python modules/M1_signal_audit/verify/verify_m1_round2_gaps.py
Writes: modules/M1_signal_audit/verify/verify_results_round2_gaps.csv
"""
import sys, pathlib
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "lib"))

import warnings
import numpy as np
import pandas as pd
from scipy import stats
warnings.filterwarnings("ignore")
from common import load_team, TABLES, RAW  # loaders only
import team_pipeline as tp

T = lambda name: pd.read_csv(TABLES / f"M1_signal_audit_{name}.csv")
RES = []


def check(claim, builder, mine, tol, note=""):
    try:
        ok = abs(float(builder) - float(mine)) <= tol
    except (TypeError, ValueError):
        ok = str(builder) == str(mine)
    RES.append(dict(claim=claim, builder=builder, verifier=mine, tol=tol, status="match" if ok else "MISMATCH", note=note))
    print(f"[{'ok ' if ok else 'BAD'}] {claim}: builder={builder} verifier={mine} {note}")


def info(claim, mine, note=""):
    RES.append(dict(claim=claim, builder="", verifier=mine, tol=np.nan, status="info", note=note))
    print(f"[inf] {claim}: {mine} {note}")


def fred(sid):
    df = pd.read_csv(RAW / f"fred_{sid}.csv"); df.columns = ["date", "v"]
    return pd.Series(pd.to_numeric(df.v, errors="coerce").values, index=pd.to_datetime(df.date) + pd.offsets.MonthEnd(0))


def zpd(x, win=60, minp=36):
    r = x.rolling(win, min_periods=minp)
    return (x - r.mean()) / r.std(ddof=1)


def rule(z):
    thr = z.shift(1).expanding(min_periods=60).quantile(0.8)
    st = z.gt(thr) & thr.notna()
    return thr, st, st & ~st.shift(1, fill_value=False)


ym = lambda idx: " ".join(t.strftime("%Y-%m") for t in idx)
H = ("2022-08-31", "2026-07-31"); V = ("2010-01-31", "2022-07-31"); POST = ("2021-10-31", "2026-08-31")

emv = fred("EMVENRGYENVREG").loc[:"2026-08-31"]; emv_all = fred("EMVOVERALLEMV").loc[:"2026-08-31"]
lz = np.log1p(emv); zero = emv.eq(0)
z = zpd(lz); thr, st, cr = rule(z)

# ============================================================================= G1 counterfactuals, pandas implementation
print("\n== G1 counterfactuals (pandas)")
check("team holdout entries", "2023-04 2024-06 2025-02 2025-09 2025-11", ym(cr.loc[H[0]:H[1]][lambda s: s].index), 0)


def frozen(end):
    w = lz.loc[:end].iloc[-60:]; zf = z.copy(); nxt = pd.Timestamp(end) + pd.offsets.MonthEnd(1)
    zf.loc[nxt:] = (lz.loc[nxt:] - w.mean()) / w.std(ddof=1)
    return zf, w.mean(), w.std(ddof=1)


zF, mF, sF = frozen("2021-09-30")
lzn = lz.where(~zero)
zC = zpd(lzn, 60, 12).where(lzn.notna())                     # 60 calendar months, NaN-aware
zO = zpd(lzn.dropna(), 60, 12).reindex(lz.index)             # last 60 nonzero months
VAR = {"frozen_2021-09": zF, "zeros_missing_calendar": zC, "zeros_missing_last60_nonzero": zO}
for nm, zz in VAR.items():
    _, s2, c2 = rule(zz)
    check(f"{nm}: holdout entries equal team", ym(cr.loc[H[0]:H[1]][lambda s: s].index), ym(c2.loc[H[0]:H[1]][lambda s: s].index), 0)
    info(f"{nm}: post-2021-10 state / entry months that differ from team",
         f"{int((s2.loc[POST[0]:POST[1]] != st.loc[POST[0]:POST[1]]).sum())} / {int((c2.loc[POST[0]:POST[1]] != cr.loc[POST[0]:POST[1]]).sum())}")
_, s2, c2 = rule(zF); zFt = zF.gt(thr) & thr.notna(); c2t = zFt & ~zFt.shift(1, fill_value=False)
check("frozen + team threshold path: post-2021-10 state months differ", 0, int((zFt.loc[POST[0]:POST[1]] != st.loc[POST[0]:POST[1]]).sum()), 0)
check("frozen m*, s*", "0.281/0.171", f"{mF:.3f}/{sF:.3f}", 0)
for end in ("2019-09-30", "2020-09-30"):
    zf, m_, s_ = frozen(end); _, s2, c2 = rule(zf)
    info(f"other freeze date {end[:7]}: holdout entries (m*={m_:.3f}, s*={s_:.3f})", ym(c2.loc[H[0]:H[1]][lambda s: s].index))

# ============================================================================= G2 strategy-level extension
print("\n== G2 does the counterfactual extend to Pure and Continuous variants?")
res = tp.run_pipeline(bootstrap_reps=0, extras=False, paired=False, macro_states=False)
raw_team = res["signals"]["raw"]
check("team pipeline raw z = my pandas z (max abs diff, 1992-2026)", 0.0, float((raw_team - z.reindex(raw_team.index)).loc["1992-12-31":].abs().max()), 1e-9)
C = tp.Config(); tm = res["models"]["Brown leg"]; eps = tm["epsilon"]; fac = load_team()["ff3"]
ctrl = res["signals"]["controls"]; rates = tp.resolve_costs(list(tp.TEAM_FACTOR_COLS))
pk = dict(annual_vol_target=C.annual_vol_target, vol_window=C.residual_vol_window, cap=C.position_cap)
run = lambda pos: tp.asset_strategy_returns(pos, tm, fac, list(tp.TEAM_FACTOR_COLS), rates)


def strategies(zz):
    zz = zz.reindex(raw_team.index)
    pred = tp.rolling_oos_prediction(zz, ctrl, C.macro_window, C.min_macro_obs, C.ridge).reindex(zz.index)
    out = {}
    for key, sig in (("Original", zz), ("Pure", zz - pred)):
        th = tp.expanding_threshold(sig, C.tail_q, C.tail_min_history); s_ = sig.gt(th) & th.notna()
        c_, holds = tp.cross_and_holds(s_, C.holds)
        out[f"{key} entries"] = c_
        for h in C.holds:
            out[f"{key} hold {h}m"] = run(tp.state_position(holds[h], eps, C.direction, **pk))["net_return"]
        w = tp.continuous_conditioning_weight(sig, C.cont_floor, C.cont_halflife, C.cont_min_history)
        out[f"Continuous {key.lower()}"] = run(tp.continuous_position(w, eps, C.direction, **pk))["net_return"]
    return out


ST_team = strategies(raw_team); ST_frz = strategies(zF); ST_cal = strategies(zC); ST_obs = strategies(zO)
pt = res["period_table"].set_index(["strategy", "period"])
name_map = {"Original hold 3m": "Original | Short Brown hold 3m", "Original hold 6m": "Original | Short Brown hold 6m",
            "Pure hold 3m": "Pure | Short Brown hold 3m", "Pure hold 6m": "Pure | Short Brown hold 6m",
            "Continuous original": "Continuous | raw attention", "Continuous pure": "Continuous | pure attention"}
for k, team_name in name_map.items():
    s = ST_team[k].loc[H[0]:H[1]].dropna()
    check(f"rebuild reproduces team holdout ann_net: {k}", round(pt.loc[(team_name, "Holdout Aug2022-Jul2026"), "ann_net"], 6), round(12 * s.mean(), 6), 1e-6)
for key in ("Original", "Pure"):
    a = ST_team[f"{key} entries"].loc[H[0]:H[1]]; b = ST_frz[f"{key} entries"].loc[H[0]:H[1]]
    info(f"{key} holdout entries team | frozen", f"{ym(a[a].index)} | {ym(b[b].index)}")
for k in name_map:
    a = ST_team[k].loc[H[0]:H[1]].dropna(); b = ST_frz[k].loc[H[0]:H[1]].dropna()
    sr = lambda s: 12 * s.mean() / (np.sqrt(12) * s.std(ddof=1)) if s.std(ddof=1) > 0 else np.nan
    info(f"holdout ann_net % / Sharpe, team -> frozen 2021-09: {k}",
         f"{100 * 12 * a.mean():.2f}/{sr(a):.2f} -> {100 * 12 * b.mean():.2f}/{sr(b):.2f}",
         f"max |return diff| {float((a - b.reindex(a.index)).abs().max()):.2e}")
    RES[-1]["team_ann_net"] = 12 * a.mean(); RES[-1]["frozen_ann_net"] = 12 * b.mean()

for lab, STx in (("zeros missing, 60 calendar months", ST_cal), ("zeros missing, last 60 nonzero", ST_obs)):
    for k in name_map:
        a = ST_team[k].loc[H[0]:H[1]].dropna(); b = STx[k].loc[H[0]:H[1]].dropna()
        info(f"holdout ann_net %, team -> {lab}: {k}", f"{100 * 12 * a.mean():.2f} -> {100 * 12 * b.mean():.2f}",
             "zero months get no z, so the continuous weight is 0 there (a design change, not only a rescaling)" if k.startswith("Continuous") else "")

# ============================================================================= G3 remaining FINDINGS numbers
print("\n== G3 remaining text numbers")
hs = st.loc[H[0]:H[1]]; hn = ~zero.loc[H[0]:H[1]]
tab = [[int((hs & hn).sum()), int((~hs & hn).sum())], [int((hs & ~hn).sum()), int((~hs & ~hn).sum())]]
check("Fisher state vs nonzero month, holdout (text 0.00026)", 0.00026, round(stats.fisher_exact(tab)[1], 5), 5e-6, f"table {tab}")
z24 = zero.astype(float).rolling(24).mean()
check("24m zero share max before 2021 (text <= 12.5%)", 0.125, round(z24.loc[:"2020-12-31"].max(), 4), 1e-4)
check("24m zero share peak (text 79.2% in 2024-02)", "0.792 2024-02", f"{z24.max():.3f} {z24.idxmax():%Y-%m}", 0)
sh = (emv / emv_all)
check("share mean (text 0.0136)", 0.0136, round(sh.mean(), 4), 5e-5)
nzp = sh.loc["2021-10-31":][lambda s: s > 0]
check("nonzero share after 2021-10: n / min / max (text 20, 0.006, 0.054)", "20/0.006/0.054", f"{len(nzp)}/{nzp.min():.3f}/{nzp.max():.3f}", 0)
vix = fred("VIXCLS").dropna(); vix = vix.groupby(vix.index).mean().loc[:"2026-08-31"]
zv = zpd(np.log1p(vix)); zo = zpd(np.log1p(emv_all))
d = pd.concat([z.rename("y"), zv.rename("v"), zo.rename("o")], axis=1).dropna()
import statsmodels.api as sm
f = sm.OLS(d.y, sm.add_constant(d[["v", "o"]])).fit(cov_type="HAC", cov_kwds={"maxlags": 6})
check("Q2 joint slopes (text -0.03 t -0.35; 0.43 t 5.07)", "-0.03/-0.35/0.43/5.07",
      f"{f.params.v:.2f}/{f.tvalues.v:.2f}/{f.params.o:.2f}/{f.tvalues.o:.2f}", 0, f"n={int(f.nobs)} (statsmodels HAC as an independent estimator)")
cv = T("crossings_vix_summary").set_index(["flag", "event", "window"])
for key, cl in ((("high_VIX", "crossing", "all_threshold_sample"), "31/50/0.620/0.489/381"),
                (("high_EMV_overall", "crossing", "all_threshold_sample"), "44/50/0.880/0.645/382"),
                (("high_VIX", "state", "all_threshold_sample"), "59/82/0.720/0.450/381"),
                (("high_EMV_overall", "crossing", "since_2010"), "23/26/0.885/0.561/176"),
                (("high_VIX", "crossing", "since_2010"), "13/26/0.500/0.416/176"),
                (("high_VIX", "crossing", "holdout"), "2/5/0.400/0.465/25"),
                (("high_EMV_overall", "crossing", "holdout"), "5/5/1.000/0.814/25")):
    r = cv.loc[key]
    check(f"Q4 counts {'/'.join(key)}", cl, f"{r.n_events_flag}/{r.n_events}/{r.frac_events_flag:.3f}/{r.frac_other_flag:.3f}/{r.n_shifts}", 0)
    check(f"Q4 rotations = n_months - 23 {'/'.join(key)}", r.n_months - 23, r.n_shifts, 0)
check("Q4 since-2010 VIX LPM p (text 0.34)", 0.34, round(cv.loc[("high_VIX", "crossing", "since_2010")].p_lpm_nw12, 2), 0.005)
led = T("tests_ledger")
check("ledger rows added in fix round vs text '35 rows were added'", 35,
      6 + int(led.test_id.str.startswith("Q5_primary").sum()) + int(led.test_id.str.contains("_circshift|_lpm_nw12").sum()) + 2, 0,
      "6 share + 8 Q5 primary robustness + 40 Q4 + 2 Q3 = 56 added; 632 + 56 - 21 merged = 667; 35 is the net change")

out = pd.DataFrame(RES)
out.to_csv(HERE / "verify_results_round2_gaps.csv", index=False)
print(f"\n{(out.status == 'match').sum()} match, {(out.status == 'MISMATCH').sum()} mismatch, {(out.status == 'info').sum()} info rows")
print(out[out.status == "MISMATCH"][["claim", "builder", "verifier", "note"]].to_string())
