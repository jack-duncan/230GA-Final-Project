"""V3: primary (ii) holdout alphas FF3 vs FF3+UMD+BOND, Wald F(UMD=BOND=0), Holm within 6, both baselines.
Also FF5+UMD+BOND range, the FF3-hedged Brown leg's holdout alpha and the exchange-1 d10y/BOND fact-check."""
import numpy as np
import pandas as pd
from vlib import (build_bond_independent, factor_panel, nw, wald_F, holm, pipelines, load_team, OUT, HOLD, STRATS, BENCH, SH,
                  FF3, FF3UB, FF5UB)
from common import load_fred

rf = load_team()["ff3"]["RF"]
F = factor_panel(build_bond_independent(rf)["BOND"])
team, corr = pipelines()
rows = []
for bname, res in (("team", team), ("corrected", corr)):
    for s in STRATS + [BENCH]:
        y = res["strategies"][s]["net_return"].loc[HOLD[0]:HOLD[1]]
        f3, f5, ff5 = nw(y, F[FF3]), nw(y, F[FF3UB]), nw(y, F[FF5UB])
        Fw, pw = wald_F(f5, ["UMD", "BOND"])
        rows.append({"baseline": bname, "s": SH[s], "n": f5["n"], "net": 12 * y.mean(),
                     "a_FF3": 12 * f3["b"]["const"], "t_FF3": f3["t"]["const"], "p_FF3": f3["p"]["const"],
                     "a_FF3UB": 12 * f5["b"]["const"], "t_FF3UB": f5["t"]["const"], "p_FF3UB": f5["p"]["const"],
                     "pnorm_FF3UB": f5["pn"]["const"], "bBOND": f5["b"]["BOND"], "tBOND": f5["t"]["BOND"],
                     "wald_p": pw, "a_FF5UB": 12 * ff5["b"]["const"], "t_FF5UB": ff5["t"]["const"]})
R = pd.DataFrame(rows)
for b in ("team", "corrected"):
    m = (R.baseline == b) & (R.s != "AlwaysShort")
    R.loc[m, "holm_FF3UB"] = holm(R.loc[m, "p_FF3UB"]); R.loc[m, "holm_wald"] = holm(R.loc[m, "wald_p"])
pd.set_option("display.width", 250)
print(R.round(4).to_string())

pub = pd.read_csv("/home/hashim/projects/GA/project/research/outputs/tables/M3_alpha_beta_holdout_alpha.csv")
cmp_ = pub.merge(R, left_on=["baseline", "short"], right_on=["baseline", "s"])
print("max |alpha FF3+UMD+BOND diff| vs published:", float((cmp_["alpha_FF3+UMD+BOND"] - cmp_["a_FF3UB"]).abs().max()))
print("max |wald p diff| vs published:", float((cmp_["wald_UMD_BOND_p"] - cmp_["wald_p"]).abs().max()))

# FF3-hedged Brown leg (team 60m FF3 hedge, unscaled), holdout
hb = team["models"]["Brown leg"]["hedged"]
for nm, cols in (("FF3", FF3), ("FF3+UMD+BOND", FF3UB)):
    f = nw(hb.loc[HOLD[0]:HOLD[1]], F[cols])
    print(f"hedged Brown holdout {nm}: alpha {12*f['b']['const']:.4f} (t {f['t']['const']:.2f})")
# exchange-1 fact-check: FF5+UMD+d10y+COM on strategies, d10y+COM on hedged Brown
F["d10y"] = load_fred("GS10").diff().reindex(F.index)
F["COM"] = load_fred("PALLFNFINDEXM").pct_change().reindex(F.index)
for nm, cols in (("d10y+COM", ["d10y", "COM"]), ("BOND+COM", ["BOND", "COM"]), ("FF5+UMD+BOND", FF5UB)):
    f = nw(hb.loc[HOLD[0]:HOLD[1]], F[cols]); rc = "d10y" if "d10y" in cols else "BOND"
    print(f"hedged Brown holdout {nm}: {rc} {f['b'][rc]:.4f} (t {f['t'][rc]:.2f})")
spec = ["Mkt-RF_k", "SMB_k", "HML_k", "RMW_k", "CMA_k", "UMD"]
for nm, extra in (("FF5+UMD+d10y+COM", ["d10y", "COM"]), ("FF5+UMD+BOND+COM", ["BOND", "COM"])):
    al = []
    for s in STRATS:
        f = nw(team["strategies"][s]["net_return"].loc[HOLD[0]:HOLD[1]], F[spec + extra])
        al.append((SH[s], round(1200 * f["b"]["const"], 2), round(f["t"]["const"], 2)))
    print(nm, "team:", al)
R.to_csv(OUT / "v3_holdout_alpha.csv", index=False)
