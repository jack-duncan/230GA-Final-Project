"""V4: primary (iii) Lewellen-Nagel beta-timing term, backward 36m betas (t-36..t-1) on Mkt-RF, SMB, HML, UMD, BOND,
post-2010, own circular block bootstrap (block 12, 5000 reps, different seed), Holm over GB + six corrected strategies.
Also: look-ahead fuzz test of the rolling betas, Always-short Brown, hedged Brown, 24m windows, and the exposure-matched
benchmark difference D = strategy - pi x Always-short Brown."""
import numpy as np
import pandas as pd
from vlib import (build_bond_independent, factor_panel, pipelines, load_team, roll_backward, ln_terms, boot_timing, holm, nw,
                  OUT, POST10, COVID, HOLD, STRATS, BENCH, SH, FF3UB, END)
from team_pipeline import TEAM_GREEN, TEAM_BROWN

T = load_team()
rf = T["ff3"]["RF"]
F = factor_panel(build_bond_independent(rf)["BOND"])
FL = F[FF3UB]
team, corr = pipelines()
ind = T["industries"]
GB = ind[TEAM_GREEN].mean(axis=1) - ind[TEAM_BROWN].mean(axis=1)
assets = {"GB": GB}
for s in STRATS + [BENCH]:
    assets[SH[s]] = corr["strategies"][s]["net_return"]
assets["Hedged Brown"] = team["models"]["Brown leg"]["hedged"]
assets["Brown leg"] = ind[TEAM_BROWN].mean(axis=1) - rf

# ---- look-ahead fuzz: perturb r and f from 2015-06 on; betas up to and including 2015-06 must not change
y0 = assets["Pure 6m"]
b_ref = roll_backward(y0, FL, 36)
rng = np.random.default_rng(1)
y1 = y0.copy(); F1 = FL.copy()
cut = pd.Timestamp("2015-06-30")
y1.loc[cut:] = rng.normal(0, .05, (y1.index >= cut).sum())
F1.loc[cut:] = rng.normal(0, .05, F1.loc[cut:].shape)
b_pert = roll_backward(y1, F1, 36)
dif = (b_ref - b_pert).abs().max(axis=1)
print("look-ahead fuzz: max beta change for months <= 2015-06:", float(dif.loc[:cut].max()), "; first changed month:", dif[dif > 0].index.min())

rows = []
for nm, r in assets.items():
    for W in (36, 24):
        B = roll_backward(r, FL, W)
        d = ln_terms(r, B, FL, *POST10)
        bt = boot_timing(d["_R"], d["_B"], d["_F"], reps=5000 if W == 36 else 2000, block=12)
        rows.append({"asset": nm, "window": W, "n": d["n"], "mean": d["mean"], "cond_alpha": d["cond_alpha"], "static": d["static"],
                     "timing": d["timing"], "cov_BOND": d["cov_BOND"], "lo": bt["lo"], "hi": bt["hi"], "p_boot": bt["p"],
                     "gap": d["mean"] - d["cond_alpha"] - d["static"] - d["timing"]})
R = pd.DataFrame(rows)
fam = R[(R.window == 36) & R.asset.isin(["GB", "Orig 3m", "Pure 3m", "Orig 6m", "Pure 6m", "Cont raw", "Cont pure"])].copy()
fam["holm"] = holm(fam.p_boot)
pd.set_option("display.width", 250)
print(R.round(4).to_string())
print(fam[["asset", "timing", "p_boot", "holm"]].round(4).to_string())
pub = pd.read_csv("/home/hashim/projects/GA/project/research/outputs/tables/M3_alpha_beta_primary_iii.csv")
print(pub[["asset", "n", "mean_r", "cond_alpha", "static_beta", "timing_cov", "timing_ci_low", "timing_ci_high", "timing_p_boot", "holm_p_timing"]].round(4).to_string())

# ---- COVID: backward 36m conditional alpha of Pure 6m and Always-short (claim 8.3% and 8.9%)
for nm in ("Pure 6m", "AlwaysShort"):
    B = roll_backward(assets[nm], FL, 36)
    d = ln_terms(assets[nm], B, FL, *COVID)
    print(f"COVID backward-36m {nm}: mean {d['mean']:.4f}, cond alpha {d['cond_alpha']:.4f}, timing {d['timing']:.4f}")

# ---- exposure-matched difference D (post-2010 timing term and D mean t)
brows = []
pos_ao = corr["strategies"][BENCH]["position"].shift(1).loc[POST10[0]:POST10[1]]
for s in STRATS:
    pos_s = corr["strategies"][s]["position"].shift(1).loc[POST10[0]:POST10[1]]
    pi = pos_s.abs().mean() / pos_ao.abs().mean()
    D = assets[SH[s]] - pi * assets["AlwaysShort"]
    B = roll_backward(D, FL, 36)
    d = ln_terms(D, B, FL, *POST10)
    bt = boot_timing(d["_R"], d["_B"], d["_F"], reps=5000)
    m = nw(D.loc[POST10[0]:POST10[1]])
    mc = nw(D.loc[COVID[0]:COVID[1]]); ac = nw(D.loc[COVID[0]:COVID[1]], FL)
    mh = nw(D.loc[HOLD[0]:HOLD[1]])
    brows.append({"s": SH[s], "pi": pi, "timing": d["timing"], "p_boot": bt["p"], "t_meanD": m["t"]["const"],
                  "covid_D": 12 * mc["b"]["const"], "t_covid_D": mc["t"]["const"], "covid_alphaD": 12 * ac["b"]["const"],
                  "t_covid_alphaD": ac["t"]["const"], "p_covid_alphaD": ac["p"]["const"], "hold_D": 12 * mh["b"]["const"], "t_hold_D": mh["t"]["const"]})
BR = pd.DataFrame(brows)
print(BR.round(4).to_string())
R.to_csv(OUT / "v4_ln.csv", index=False); BR.to_csv(OUT / "v4_ln_vs_benchmark.csv", index=False)
