"""Round 2: ChatGPT's "Checks to run first" on the real data, plus integration checks of the new function contracts.

  CF1  attention_signal(env, overall, "calendar") (v2) vs the old v1 attention_signal: z, thr, extreme.
  CF1b attention_signal(env, overall, "nonzero") (v2) vs round-1 switch A (align.attention_signal_A) and vs the
       reference share_signal (modules/M8_frozen_pre2010/run.py): z, thr, extreme, crossings.
  CF2  leg_pipeline(ff49, fac[["Mkt-RF","SMB","HML","RF"]]) (v2) vs the old v1 leg_pipeline(ff49, fac, ...).
  CF2b leg_pipeline(ff49, team FF3) (v2) vs the reference brown_model (betas, residual, size).
  CF3  RF of hedge_fac (team FF3) vs RF of fac (FF5 file) (ChatGPT's choice 3: "the driver can assert that").
  N1   Literal drop-in: what the UNCHANGED v1 driver does with the new attention_signal output if no adapter is
       written (ChatGPT's reply lists no driver change for the signal's new output layout).
Writes out/r2_checks_first.csv and out/r2_dropin_crossings.csv.
"""
import sys
from dataclasses import replace

sys.dont_write_bytecode = True
CHECKS = "/home/hashim/projects/GA/project/research/exchange/02_coding_support/checks"
RESEARCH = "/home/hashim/projects/GA/project/research"
sys.path.insert(0, CHECKS)
sys.path.insert(0, f"{RESEARCH}/lib")
sys.path.insert(0, f"{RESEARCH}/modules/M8_frozen_pre2010")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import align  # noqa: E402  (round-1 switches; imports chatgpt_code_v1 as align.g)
import chatgpt_code_v2 as g2  # noqa: E402
import run as ref  # noqa: E402  (import only)
from run_v2_real import PATHS, real_fac, real_hedge_fac  # noqa: E402
from team_pipeline import TEAM_BROWN  # noqa: E402

g1 = align.g
rows = []


def rec(check, result, ok):
    rows.append({"check": check, "result": result, "status": "pass" if ok else "FAIL"})
    print(f"[{'pass' if ok else 'FAIL'}] {check}: {result}", flush=True)


def maxabs(a, b):
    a, b = a.align(b, join="inner")
    both = a.notna() & b.notna()
    return float((a[both] - b[both]).abs().max()) if both.any() else 0.0, int((a.isna() != b.isna()).sum())


cfg = g1.Config()
env = g1.load_fred_monthly(PATHS["EMVENRGYENVREG"], "EMVENRGYENVREG")
overall = g1.load_fred_monthly(PATHS["EMVOVERALLEMV"], "EMVOVERALLEMV")

# ---------------------------------------------------------------- CF1: calendar reading vs old function
align.apply("")
old = g1.attention_signal(env, overall, cfg)
new_c = g2.attention_signal(env, overall, z_burn_in="calendar")
dz, nz = maxabs(old["z"], new_c["z"])
dt, nt = maxabs(old["thr"], new_c["thr"])
old_ext_def = old["extreme"].dropna()
new_ext_on_def = new_c["extreme"].reindex(old_ext_def.index).astype(float)
ext_mis = int((old_ext_def != new_ext_on_def).sum())
undefined_true = int((new_c["extreme"] & old["extreme"].isna().reindex(new_c.index, fill_value=True)).sum())
same_idx = old.index.equals(new_c.index)
rec("CF1 attention_signal(calendar) vs v1 attention_signal (real EMV, 1985-01..2026-08)",
    f"same index {same_idx}; max|z diff| {dz:.1e}, NaN-pattern mismatches {nz}; max|thr diff| {dt:.1e}, NaN mismatches {nt}; "
    f"extreme differs in {ext_mis} of {len(old_ext_def)} months where v1 defines it; new extreme True where v1 is "
    f"undefined: {undefined_true}. v1 extreme is 1/0/NaN, v2 is bool (False where undefined).",
    same_idx and dz == 0 and nz == 0 and dt == 0 and nt == 0 and ext_mis == 0 and undefined_true == 0)

# ---------------------------------------------------------------- CF1b: nonzero reading vs switch A and vs the reference
align.apply("A")
oldA = g1.attention_signal(env, overall, cfg)
align.apply("")
new_n = g2.attention_signal(env, overall, z_burn_in="nonzero")
T, ff5, renv, roverall, *_ = ref.load_inputs()
rsig = ref.share_signal(renv, roverall)
dzA, nzA = maxabs(oldA["z"], new_n["z"])
dtA, ntA = maxabs(oldA["thr"], new_n["thr"])
dzR, nzR = maxabs(rsig["z"], new_n["z"])
dtR, ntR = maxabs(rsig["threshold"], new_n["thr"])
ext_R = int((rsig["extreme"].reindex(new_n.index).astype(bool) != new_n["extreme"]).sum())
drv = g2._driver_signal(new_n, cfg)
cr2 = g1.crossings(drv["extreme"], cfg)                      # unchanged v1 crossings on the adapted flags
cr_ref = rsig["cross"].reindex(cr2.index, fill_value=False)
cross_mis = int((cr2 != cr_ref).sum())
rec("CF1b attention_signal(nonzero) vs round-1 switch A and vs the reference share_signal",
    f"vs A: max|z| {dzA:.1e} ({nzA} NaN mismatches), max|thr| {dtA:.1e} ({ntA}); vs reference: max|z| {dzR:.1e} ({nzR}), "
    f"max|thr| {dtR:.1e} ({ntR}), extreme differs in {ext_R} months; crossings (adapter + v1 crossings) differ from the "
    f"reference's in {cross_mis} of {len(cr2)} months; first z {new_n['z'].first_valid_index():%Y-%m}, "
    f"first thr {new_n['thr'].first_valid_index():%Y-%m}",
    max(dzA, dtA) < 1e-12 and nzA + ntA == 0 and dzR < 1e-12 and dtR < 1e-12 and nzR + ntR == 0 and ext_R == 0 and cross_mis == 0)

# ---------------------------------------------------------------- CF2: leg_pipeline on FF5-file columns vs old leg
ff49 = g1.load_ff49(PATHS["ff49"])
fac = g1.load_factors(real_fac())
index = g1._month_range(fac.index.min(), min(fac.index.max(), ff49.index.max()))
hold0 = pd.Series(False, index=index)
old_leg = g1.leg_pipeline(ff49, fac, cfg.brown, hold0, index, cfg)
new_leg = g2.leg_pipeline(ff49, fac[["Mkt-RF", "SMB", "HML", "RF"]]).reindex(index)
pairs = {"RB": (old_leg["rb"], new_leg["RB"]), "a": (old_leg["a"], new_leg["a"]), "e": (old_leg["e"], new_leg["e"]),
         "sd": (old_leg["sd"], new_leg["sd"]), "m": (old_leg["m"], new_leg["m"])}
for k in cfg.hedge_factors:
    pairs[f"b_{k}"] = (old_leg["b"][k], new_leg[f"b_{k}"])
res2 = {k: maxabs(*v) for k, v in pairs.items()}
worst = max(v[0] for v in res2.values())
nanmis = sum(v[1] for v in res2.values())
rec("CF2 leg_pipeline(ff49, fac[Mkt-RF,SMB,HML,RF]) vs v1 leg_pipeline(ff49, fac)",
    f"max |diff| over RB, a, b, e, sd, m = {worst:.1e}; NaN-pattern mismatches {nanmis}; per column "
    + ", ".join(f"{k} {v[0]:.0e}" for k, v in res2.items()), worst == 0 and nanmis == 0)

# ---------------------------------------------------------------- CF2b: leg on team FF3 vs the reference model
ff3 = real_hedge_fac()
leg3 = g2.leg_pipeline(ff49, ff3)
rmodel = ref.brown_model(TEAM_BROWN, T["industries"], T["ff3"])
w = pd.date_range("1990-01-31", "2026-07-31", freq="ME")
db = float((leg3[[f"b_{k}" for k in cfg.hedge_factors]].reindex(w).to_numpy() - rmodel["betas"].reindex(w).to_numpy()).__abs__().max())
de = float((leg3["e"].reindex(w) - rmodel["epsilon"].reindex(w)).abs().max())
rec("CF2b leg_pipeline(ff49, team FF3) vs reference brown_model, 1990-01..2026-07",
    f"max |b diff| {db:.1e}; max |residual diff| {de:.1e}", db < 1e-12 and de < 1e-12)

# ---------------------------------------------------------------- CF3: RF identity
ff5 = real_fac()
common = ff3.index.intersection(ff5.index)
d_rf = float((ff3.loc[common, "RF"] - ff5.loc[common, "RF"]).abs().max())
d_smb = float((ff3.loc[common, "SMB"] - ff5.loc[common, "SMB"]).abs().max())
d_mkt = float((ff3.loc[common, "Mkt-RF"] - ff5.loc[common, "Mkt-RF"]).abs().max())
rec("CF3 hedge_fac RF == fac RF (ChatGPT choice 3)",
    f"{common[0]:%Y-%m}..{common[-1]:%Y-%m}: max |RF diff| {d_rf:.1e}; for context max |SMB diff| {d_smb:.4f}, "
    f"max |Mkt-RF diff| {d_mkt:.4f}", d_rf == 0)

# ---------------------------------------------------------------- N1: literal drop-in without an adapter
new_sig = new_n                                                           # what the new function returns
# (a) diagnostics_summary reads sig["off"]
try:
    sw = new_sig.reindex(g1._month_range("1994-01", "2009-11"))
    _ = sw["off"]
    off_err = "no error"
except KeyError as e:
    off_err = f"KeyError {e}"
# (b) test_window takes the first non-NaN flag
fs_bool = new_sig["extreme"].dropna().index[0]
fs_adapt = drv["extreme"].dropna().index[0]
win_bool = g1.test_window(new_sig, index, cfg)[3]
win_adapt = g1.test_window(drv, index, cfg)[3]
# (c) crossings bridge only NaN flags
cr_bool = g1.crossings(new_sig["extreme"].astype(float), cfg)
extra = cr_bool & ~cr2
extra_list = [t.strftime("%Y-%m") for t in extra.index[extra.to_numpy()]]
# (d) diagnostics' zero count reads s == 0
zeros_bool = int((new_sig["s"] == 0).sum())
zeros_adapt = int((drv["s"] == 0).sum())
rec("N1 literal drop-in of the new attention_signal into the unchanged v1 driver",
    f"(a) diagnostics_summary: {off_err}; (b) first 'defined' flag {fs_bool:%Y-%m} (adapter {fs_adapt:%Y-%m}) -> window "
    f"{win_bool[0]:%Y-%m}..{win_bool[-1]:%Y-%m}, n = {len(win_bool)} (adapter {win_adapt[0]:%Y-%m}, n = {len(win_adapt)}); "
    f"(c) crossings: {int(cr_bool.sum())} vs {int(cr2.sum())} with the adapter over 1985-2026; extra crossings in data "
    f"months {extra_list}; (d) zero months counted {zeros_bool} (adapter {zeros_adapt})",
    off_err == "no error" and fs_bool == fs_adapt and not extra_list)
pd.DataFrame({"data_month": extra_list}).to_csv(f"{CHECKS}/out/r2_dropin_crossings.csv", index=False)
pd.DataFrame(rows).to_csv(f"{CHECKS}/out/r2_checks_first.csv", index=False)
