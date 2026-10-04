"""V3b: rerun the team pipeline with BOND (and UMD) in the rolling 60m hedge; holdout net mean and NW t."""
import pandas as pd
from vlib import build_bond_independent, factor_panel, load_team, nw, OUT, HOLD, STRATS, SH, FF3UB
from team_pipeline import run_pipeline, team_controls

T = load_team(); rf = T["ff3"]["RF"]
F = factor_panel(build_bond_independent(rf)["BOND"])
fac = F[["Mkt-RF", "SMB", "HML", "UMD", "BOND", "RF"]]
mac = T["macro"].copy(); mac["cpi"] = mac["cpi"].interpolate(limit_area="inside")
costs = {"asset": 10e-4, "Mkt-RF": 5e-4, "BOND": 5e-4, "other_factor": 25e-4}
kw = dict(bootstrap_reps=0, extras=False, paired=False, macro_states=False)
rows = []
for hname, cols in (("FF3", ("Mkt-RF", "SMB", "HML")), ("FF3+BOND", ("Mkt-RF", "SMB", "HML", "BOND")),
                    ("FF3+UMD+BOND", ("Mkt-RF", "SMB", "HML", "UMD", "BOND"))):
    c = None if hname == "FF3" else costs
    runs = {"team": run_pipeline(factors=fac if hname != "FF3" else None, factor_cols=cols, costs=c, **kw),
            "corrected": run_pipeline(macro=mac, attention=mac["attention"].shift(1), controls=team_controls(mac).shift(1),
                                      factors=fac if hname != "FF3" else None, factor_cols=cols, costs=c, **kw)}
    for bl, res in runs.items():
        for s in STRATS:
            y = res["strategies"][s]["net_return"].loc[HOLD[0]:HOLD[1]]
            f0 = nw(y); f5 = nw(y, F[FF3UB])
            rows.append({"hedge": hname, "baseline": bl, "s": SH[s], "net": round(1200 * y.mean(), 2), "t": round(f0["t"]["const"], 2),
                         "resid_bBOND": round(f5["b"]["BOND"], 3), "t_bBOND": round(f5["t"]["BOND"], 2)})
R = pd.DataFrame(rows)
print(R.pivot_table(index=["baseline", "s"], columns="hedge", values=["net", "t"], sort=False).to_string())
print(R[R.hedge == "FF3+BOND"][["baseline", "s", "resid_bBOND", "t_bBOND"]].to_string())
R.to_csv(OUT / "v3b_bond_hedge.csv", index=False)
