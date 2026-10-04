"""V4b: sensitivity of primary (iii) bootstrap p to the block length (12 vs 24 vs 36), since betas are 36-month rolling."""
import pandas as pd
from vlib import (build_bond_independent, factor_panel, pipelines, load_team, roll_backward, ln_terms, boot_timing, holm, OUT, POST10,
                  STRATS, BENCH, SH, FF3UB)
from team_pipeline import TEAM_GREEN, TEAM_BROWN

T = load_team(); rf = T["ff3"]["RF"]
F = factor_panel(build_bond_independent(rf)["BOND"])[FF3UB]
team, corr = pipelines()
ind = T["industries"]
assets = {"GB": ind[TEAM_GREEN].mean(axis=1) - ind[TEAM_BROWN].mean(axis=1)}
for s in STRATS:
    assets[SH[s]] = corr["strategies"][s]["net_return"]
rows = []
for nm, r in assets.items():
    d = ln_terms(r, roll_backward(r, F, 36), F, *POST10)
    rec = {"asset": nm, "timing": d["timing"]}
    for blk in (6, 12, 24, 36):
        rec[f"p_block{blk}"] = boot_timing(d["_R"], d["_B"], d["_F"], reps=5000, block=blk, seed=11)["p"]
    rows.append(rec)
R = pd.DataFrame(rows)
for blk in (6, 12, 24, 36):
    R[f"holm_block{blk}"] = holm(R[f"p_block{blk}"])
print(R.round(4).to_string())
R.to_csv(OUT / "v4b_block_sensitivity.csv", index=False)
