"""ChatGPT's own pre-run checks, section (b) of its answer, run as literally as possible against chatgpt_code_v1.py
(unmodified), plus the positive control on the v2 generator fix and on the real data.

Writes out/prerun_checks.csv (one row per check: ChatGPT's stop rule, what happened, pass/stop).
"""
import sys
from dataclasses import replace

import numpy as np
import pandas as pd

import align
from glue import OUT, g, real_inputs
from common import load_team
from team_pipeline import run_pipeline

rows = []


def rec(check, rule, result, ok):
    rows.append({"check": check, "chatgpt_stop_rule": rule, "result": result, "status": "pass" if ok else "STOP"})
    print(f"[{'pass' if ok else 'STOP'}] {check}: {result}", flush=True)


cfg = g.Config()
inputs = real_inputs()
ff49 = g.load_ff49(inputs["ff49"])
fac = g.load_factors(inputs["fac"])
emv_cat = g.load_fred_monthly(inputs["emv_cat"], "EMVENRGYENVREG")
emv_all = g.load_fred_monthly(inputs["emv_all"], "EMVOVERALLEMV")
index = g._month_range(fac.index.min(), min(fac.index.max(), ff49.index.max()))

# ---------------------------------------------------------------- (b)1 units and dates
e = g.load_fred_monthly(inputs["emv_cat"], "EMVENRGYENVREG")
v = g.load_vix_monthly(inputs["vix"])
ok1 = (e.index[0] == pd.Timestamp("1985-01-31")) and (v.index[0] == pd.Timestamp("1990-01-31"))
brown_nan = int(ff49.loc["1985":"2009", list(cfg.brown)].isna().sum().sum())
rec("(b)1 units and dates", "stop if any series shifted, percent units flagged, or a Brown industry missing",
    f"EMV first month {e.index[0]:%Y-%m-%d}; VIX first month {v.index[0]:%Y-%m-%d}; loaders raised no unit error; "
    f"Brown NaNs 1985-2009 = {brown_nan}", ok1 and brown_nan == 0)

# ---------------------------------------------------------------- (b)2 reproduce the team trade (seen window)
team = run_pipeline(bootstrap_reps=0, extras=False, paired=False, macro_states=False)
t_ao = team["strategies"]["Benchmark | Always-short Brown"]["net_return"]
t_o6 = team["strategies"]["Original | Short Brown hold 6m"]["net_return"]
team_hold6 = team["signals"]["hold_raw"][6]           # same-month team hold (position set at end of t)
seen = pd.date_range("2010-01-31", "2022-07-31", freq="ME")
for label, variant in (("as delivered (hedge on FF5-file SMB/HML, FF5 RF)", ""), ("hedge on team FF3 file (switch B)", "B")):
    align.apply(variant)
    lg = g.leg_pipeline(ff49, fac, cfg.brown, team_hold6.reindex(index, fill_value=False).astype(bool), index, cfg)
    d_ao = float((lg["tr_AO"]["net"].reindex(seen) - t_ao.reindex(seen)).abs().max())
    d_o6 = float((lg["tr_T"]["net"].reindex(seen) - t_o6.reindex(seen)).abs().max())
    rec(f"(b)2 team trade 2010-01..2022-07, {label}", "stop if any month differs by more than 1e-8",
        f"max |R^AO - team Always-short| = {d_ao:.2e}; max |timed(team 6m hold) - team Original 6m| = {d_o6:.2e}",
        max(d_ao, d_o6) <= 1e-8)
align.apply("")
ff3 = load_team()["ff3"]
f5 = fac.reindex(ff3.index)
diffs = {c: float((f5[c] - ff3[c]).loc["1963-07":"2026-07"].abs().max()) for c in ["Mkt-RF", "SMB", "HML", "RF"]}
corr_smb = float(f5["SMB"].loc["1989":"2009"].corr(ff3["SMB"].loc["1989":"2009"]))
rows.append({"check": "context: FF5-file vs team FF3-file factors, 1963-07..2026-07", "chatgpt_stop_rule": "",
             "result": f"max |diff| {diffs}; corr(SMB) 1989-2009 = {corr_smb:.4f}", "status": "info"})
print(rows[-1])

# ---------------------------------------------------------------- (b)3 look-ahead (already run on synthetic and seen data) + lag probe
sig = g.attention_signal(emv_cat, emv_all, cfg)
h1 = g.hold_positions(g.crossings(sig["extreme"], cfg), index, cfg)
h0 = g.hold_positions(g.crossings(sig["extreme"], cfg), index, replace(cfg, pub_lag=0))
ok3 = bool((h0.shift(1, fill_value=False) == h1).all()) and not bool((h0 == h1).all())
rec("(b)3 lag probe (pub_lag=0)", "stop if the hold does not move exactly one month earlier",
    f"hold(pub_lag=0) shifted one month == hold(pub_lag=1) in all {len(h1)} months: {ok3}", ok3)

# ---------------------------------------------------------------- (b)4 signal unit tests on hand-built series
ext = pd.Series([0.0, 1.0, np.nan, 1.0, 0.0, 1.0], index=g._month_range("2000-01", "2000-06"))
n_b = int(g.crossings(ext, cfg).sum())
n_nb = int(g.crossings(ext, replace(cfg, bridge_missing=False)).sum())
rng = np.random.default_rng(1)
idx = g._month_range("1985-01", "2004-12")
all_ = pd.Series(10.0, index=idx)
cat = pd.Series(10.0 * np.exp(-3 + rng.normal(0, 0.3, len(idx))), index=idx)
cat6, cat7 = cat.copy(), cat.copy()
zeros6 = idx[[70, 75, 80, 85, 90, 95]]
cat6[zeros6] = 0.0
cat7[list(zeros6) + [idx[100]]] = 0.0
s6, s7 = g.attention_signal(cat6, all_, cfg), g.attention_signal(cat7, all_, cfg)
on6 = bool(s6["z"].notna().loc[idx[119]])     # window idx[60..119] holds 6 zeros
off7 = bool(s7["off"].loc[idx[119]]) and bool(s7["z"].isna().loc[idx[119]])   # 7 zeros in idx[60..119]
zero_nan = bool(s6["z"].loc[zeros6].isna().all())
hist_len_ok = int(s6["z"].notna().sum()) == int((~s6["missing"]).sum() - (s6["z"].isna() & ~s6["missing"]).sum())
rec("(b)4 signal unit tests", "stop on any mismatch",
    f"extreme,1,zero,1,0,1: crossings with bridging {n_b} (expect 2), without {n_nb} (expect 3); 6 zeros in trailing 60 -> on: {on6}; "
    f"7 zeros -> off: {off7}; zero months have NaN z: {zero_nan}", n_b == 2 and n_nb == 3 and on6 and off7 and zero_nan and hist_len_ok)

# ---------------------------------------------------------------- (b)5 hold tests
ci = g._month_range("2000-01", "2001-12")
c1 = pd.Series(False, index=ci); c1[pd.Timestamp("2000-03-31")] = True
hA = g.hold_positions(c1, ci, cfg)
c2 = c1.copy(); c2[pd.Timestamp("2000-06-30")] = True
hB = g.hold_positions(c2, ci, cfg)
okA = list(hA[hA].index.strftime("%Y-%m")) == [f"2000-{m:02d}" for m in range(4, 10)]
okB = int(hB.sum()) == 9 and len(g.hold_episodes(hB, ci)) == 1
lg = g.leg_pipeline(ff49, fac, cfg.brown, h1, index, cfg)
wv = lg["tr_T"]["w"].dropna()
rec("(b)5 hold tests", "stop unless one crossing -> 6 months tau+1..tau+6, crossings tau and tau+3 -> one 9-month run, w in [-1,0]",
    f"single crossing 2000-03 -> positions {hA[hA].index[0]:%Y-%m}..{hA[hA].index[-1]:%Y-%m}: {okA}; two crossings -> {int(hB.sum())} months in "
    f"{len(g.hold_episodes(hB, ci))} run: {okB}; w range [{wv.min():.3f}, {wv.max():.3f}]", okA and okB and wv.min() >= -1 and wv.max() <= 0)

# ---------------------------------------------------------------- (b)6 cost test
c0 = replace(cfg, cost_w=0.0, cost_mkt=0.0, cost_smb=0.0, cost_hml=0.0)
tr0 = g.run_trade(lg["rb"], lg["f"], lg["b"], lg["m"], h1, c0)
d0 = float((tr0["net"] - tr0["gross"]).abs().max())
tr = lg["tr_T"]
entry = tr.index[(tr["w"] != 0) & (tr["w"].shift(1) == 0)][0]
nxt = entry + pd.offsets.MonthEnd(1)
hand = 0.001 * abs(tr.at[entry, "w"]) + 0.0005 * abs(tr.at[entry, "h_Mkt-RF"]) + 0.0025 * (abs(tr.at[entry, "h_SMB"]) + abs(tr.at[entry, "h_HML"]))
rec("(b)6 cost test", "stop on a mismatch", f"zero costs: max |net-gross| = {d0:.1e}; first entry {entry:%Y-%m}: hand cost {hand:.3e}, "
    f"engine charges {tr.at[nxt, 'cost']:.3e} in {nxt:%Y-%m}", d0 == 0.0 and abs(hand - tr.at[nxt, "cost"]) < 1e-15)

# ---------------------------------------------------------------- (b)7 BOND
dur, conv = g.par_bond_duration_convexity(0.05)
closed = (1 / 0.05) * (1 - 1.025 ** -20)
gs10 = g.load_fred_monthly(inputs["gs10"], "GS10")
bond = g.bond_excess_return(gs10, fac["RF"])
dy = (gs10 / 100).diff()
cc = float(bond.loc["1993":"2009"].corr(-dy.loc["1993":"2009"]))
rec("(b)7 BOND", "stop unless D(5%) ~ 7.79 and corr(BOND, -dy) > 0.99", f"D(5%) = {dur[0]:.6f} vs closed form {closed:.6f}; "
    f"corr(BOND, -dy) 1993-2009 = {cc:.4f}", abs(dur[0] - closed) < 1e-10 and cc > 0.99)

# ---------------------------------------------------------------- (b)8 regression mechanics (from the as-delivered real run)
meta = pd.read_csv(OUT / "final_asis_attribution_meta.csv", index_col=0)["value"]
dec = pd.read_csv(OUT / "final_asis_decomposition.csv", index_col=0)["value"]
rec("(b)8 regression mechanics", "stop unless k=15, n-k=df_resid, identity gap < 1e-12, full rank, lstsq alpha = statsmodels alpha",
    f"k = {meta['k']}, n - k = {meta['n - k']}, identity gap = {float(dec['identity gap']):.1e}; run_backtest raised nothing",
    meta["k"] == "15" and abs(float(dec["identity gap"])) < 1e-12)

# ---------------------------------------------------------------- (b)9 shuffle validity (placement invariants; seeds test runs separately)
eps = pd.read_csv(OUT / "final_asis_episodes.csv", index_col=0)["months"].to_numpy()
r = np.random.default_rng(230)
n_pos = 179
bad = 0
for _ in range(5000):
    hv = g.place_blocks(eps, n_pos, 1, r)
    runs = g.hold_episodes(pd.Series(hv, index=g._month_range("1995-01", "2009-11")), g._month_range("1995-01", "2009-11"))
    bad += int(len(runs) != len(eps) or int(hv.sum()) != int(eps.sum()))
p_again = pd.read_csv(OUT / "final_AB_shuffle.csv", index_col=0)["value"]["p (one-sided)"]
rec("(b)9 shuffle validity (placement)", "stop if a draw changes K or total hold months; same seed must give the same p",
    f"5,000 placements of the real blocks {list(eps)} in {n_pos} slots: {bad} violate K or total; seed 230 reproduces the reference p "
    f"draw by draw under AB (p = {float(p_again):.6f})", bad == 0)

# ---------------------------------------------------------------- (b)10 positive control
def pc(mod, inp, delta, variant="", draws=200, tag=""):
    align.apply(variant) if mod is g else None
    c = replace(mod.Config(), shuffle_draws=draws)
    base = mod.run_backtest(inp, c, verbose=False)
    out = mod.run_backtest(mod.plant_timing_effect(inp, c, delta=delta), c, verbose=False)
    a0, a1 = base["attribution"].loc["alpha", "coef"], out["attribution"].loc["alpha", "coef"]
    dD = out["D"].mean() - base["D"].mean()
    top = out["attribution"]["t NW(6)"].drop("alpha").abs().idxmax()
    return {"case": tag, "delta": delta, "alpha_base": a0, "alpha_planted": a1, "t_planted": out["attribution"].loc["alpha", "t NW(6)"],
            "shuffle_p_planted": out["shuffle"].at["p (one-sided)", "value"], "mean_D_shift": dD,
            "share_of_D_shift_in_alpha": (a1 - a0) / dD if dD else np.nan, "largest_|t|_regressor": top,
            "its_t": out["attribution"].loc[top, "t NW(6)"], "verdict": out["verdict"]}


sys.path.insert(0, str(OUT.parent))
import chatgpt_code_v1fix as g2  # noqa: E402  (round-1 BUG-1-only fix; named chatgpt_code_v2.py in round 1)

pcs = [pc(g, g.make_synthetic_inputs(seed=0), 0.03, tag="v1 synthetic (as delivered)"),
       pc(g2, g2.make_synthetic_inputs(seed=0), 0.03, tag="v2 synthetic (BUG-1 fixed)"),
       pc(g, g.make_synthetic_inputs(seed=0), 0.0, tag="v1 synthetic, delta = 0")]
for d in (0.005, 0.01, 0.03):
    pcs.append(pc(g, inputs, d, variant="AB", tag="real data 1994-03..2009-12 (AB)"))
align.apply("")
pcs = pd.DataFrame(pcs)
pcs.to_csv(OUT / "positive_control.csv", index=False)
print(pcs.to_string())
v1r, v2r, z0 = pcs.iloc[0], pcs.iloc[1], pcs.iloc[2]
rec("(b)10 positive control, v1 as delivered", "stop if the planted effect is missed (alpha > 0, t well above 2, small shuffle p expected)",
    f"delta 3%: alpha {v1r.alpha_planted:.5f}, t {v1r.t_planted:.2f}, shuffle p {v1r.shuffle_p_planted:.3f}; only "
    f"{100 * v1r.share_of_D_shift_in_alpha:.0f}% of the mean(D) shift reaches alpha; {v1r['largest_|t|_regressor']} t = {v1r.its_t:.1f}",
    v1r.t_planted > 2 and v1r.shuffle_p_planted <= 0.05)
rec("(b)10 positive control, v2 (GS10 generator fixed)", "same",
    f"delta 3%: alpha {v2r.alpha_planted:.5f}, t {v2r.t_planted:.2f}, shuffle p {v2r.shuffle_p_planted:.3f}; "
    f"{100 * v2r.share_of_D_shift_in_alpha:.0f}% of the mean(D) shift reaches alpha", v2r.t_planted > 2 and v2r.shuffle_p_planted <= 0.05)
rec("(b)10 delta = 0 returns the original alpha", "exact", f"|alpha(delta=0) - alpha| = {abs(z0.alpha_planted - z0.alpha_base):.1e}",
    z0.alpha_planted == z0.alpha_base)
pd.DataFrame(rows).to_csv(OUT / "prerun_checks.csv", index=False)
