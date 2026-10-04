"""Fact-check C08: proposal-table rows G, C and D.

Claims checked
- G: "Signal loses a horse race to Brown's own trailing 3-12m return"
- C: "Little: Green isn't in the traded position"; "Source of the traded HML residual (that sits in Brown)"
- D: "Only a break-even cost below ~10 bp, unlikely with 3-6-month holds (guess)"; "Costs can't rescue a -2% to -4% holdout"
2010-2026 for strategy tests; leg style loadings also on 1970-2022 (team "full sample" for the raw spread).
"""
import sys
sys.path.insert(0, "/home/hashim/projects/GA/project/research/lib")
import numpy as np
import pandas as pd
from common import load_team, load_kf_industries, nw_ols
from team_pipeline import run_pipeline, TEAM_BROWN, TEAM_GREEN

pd.set_option("display.width", 220)
pd.set_option("display.max_columns", 30)
OUT = "/home/hashim/projects/GA/project/research/exchange/01_idea_generation/checks/"
T = load_team()
ff3, ind = T["ff3"], T["industries"]
fc = ["Mkt-RF", "SMB", "HML"]
res = run_pipeline(bootstrap_reps=0, extras=False, paired=False, macro_states=False)
sig = res["signals"]

# ---- G: horse race. y = next-month Brown residual; x = attention z_t, p80 state_t, trailing Brown returns at t
eps = res["models"]["Brown leg"]["epsilon"]
brown_x = res["legs"]["brown_excess"]
tr3 = brown_x.rolling(3).sum().rename("brown_ret_3m")
tr12 = brown_x.rolling(12).sum().rename("brown_ret_12m")
eps12 = eps.rolling(12).sum().rename("brown_resid_12m")
y = eps.shift(-1).rename("eps_next")
rows = []
for lab, (a, b) in (("validation", ("2010-01-31", "2022-06-30")), ("2010-2026", ("2010-01-31", "2026-06-30"))):
    for xs in (["z"], ["state"], ["brown_ret_3m", "brown_ret_12m", "brown_resid_12m"],
               ["z", "brown_ret_3m", "brown_ret_12m", "brown_resid_12m"], ["state", "brown_ret_3m", "brown_ret_12m", "brown_resid_12m"]):
        X = pd.concat([sig["raw"].rename("z"), sig["state_raw"].astype(float).rename("state"), tr3, tr12, eps12], axis=1)[xs].loc[a:b]
        f = nw_ols(y.loc[a:b], X, lags=6)
        rows.append({"period": lab, "regressors": "+".join(xs), "n": int(f.nobs),
                     **{f"t_{c}": f.tvalues[c] for c in xs}, "r2": f.rsquared})
hr = pd.DataFrame(rows)
print("=== G: next-month Brown FF3 residual on attention and trailing Brown returns (NW6 t) ===")
print(hr.round(3).to_string(index=False))
st = sig["state_raw"].astype(float).loc["2010":"2026-07"]
print("corr(p80 state_t, Brown trailing 12m excess return_t), 2010-2026:",
      round(st.corr(tr12.loc["2010":"2026-07"]), 3), "; with trailing 12m residual:", round(st.corr(eps12.loc["2010":"2026-07"]), 3))

# ---- C: where the raw spread's HML comes from
rows = []
for nm, s in [("Green leg", res["legs"]["green_excess"]), ("Brown leg", res["legs"]["brown_excess"]),
              ("Green-Brown", res["legs"]["green_minus_brown"])] + \
             [(i, ind[i] - ff3["RF"]) for i in TEAM_GREEN + TEAM_BROWN]:
    for lab, (a, b) in (("1970-Jul2022", ("1970-01-31", "2022-07-31")), ("2010-2026", ("2010-01-31", "2026-07-31"))):
        f = nw_ols(s.loc[a:b], ff3[fc].loc[a:b], lags=6)
        rows.append({"series": nm, "period": lab, "b_HML": f.params["HML"], "t_HML": f.tvalues["HML"],
                     "b_SMB": f.params["SMB"], "b_MKT": f.params["Mkt-RF"]})
hml = pd.DataFrame(rows)
print("\n=== C: FF3 HML loadings of legs and member industries ===")
print(hml.pivot_table(index="series", columns="period", values=["b_HML", "t_HML"]).round(2).to_string())
bm = load_kf_industries("be_me_vw")
bm.columns = [c.strip() for c in bm.columns]
yrs = bm.loc["2010":"2026"]
print("\nKen French value-weighted BE/ME, mean over formation years 2010-2026:")
print("  Green:", {i: round(yrs[i].mean(), 2) for i in TEAM_GREEN}, "leg mean", round(yrs[TEAM_GREEN].mean(axis=1).mean(), 2))
print("  Brown:", {i: round(yrs[i].mean(), 2) for i in TEAM_BROWN}, "leg mean", round(yrs[TEAM_BROWN].mean(axis=1).mean(), 2))
print("  All-49 median BE/ME (mean over years):", round(yrs.median(axis=1).mean(), 2))
# traded residual HML sits in Brown by construction: the strategy is position x Brown hedged return
net = res["strategies"]["Original | Short Brown hold 6m"]["net_return"].loc["2010":"2026-07"]
f = nw_ols(net, ff3[fc].reindex(net.index), lags=6)
print(f"\nTraded Original 6m residual HML loading 2010-2026: {f.params['HML']:.3f} (t {f.tvalues['HML']:.2f}); "
      "Green leg is not in the traded P&L (engine uses the Brown leg model only)")

# ---- D: gross vs net and break-even costs; uniform 5/10/25 bp
rows = []
for bp in (None, 0, 5, 10, 25):
    r = run_pipeline(bootstrap_reps=0, extras=False, paired=False, macro_states=False,
                     **({} if bp is None else {"cost_bps_uniform": bp}))
    for n in ["Original | Short Brown hold 3m", "Pure | Short Brown hold 3m", "Original | Short Brown hold 6m", "Pure | Short Brown hold 6m"]:
        df = r["strategies"][n]
        for lab, (a, b) in (("2010-2026", ("2010-01-31", "2026-07-31")), ("validation", ("2010-01-31", "2022-07-31")),
                            ("holdout", ("2022-08-31", "2026-07-31"))):
            sl = df.loc[a:b]
            gross, to = 12 * sl["gross_return"].mean(), 12 * sl["turnover"].mean()
            rows.append({"costs": "team" if bp is None else f"{bp}bp", "strategy": n, "period": lab,
                         "ann_gross": gross, "ann_net": 12 * sl["net_return"].mean(), "turnover_x": to,
                         "breakeven_bp_uniform": 1e4 * gross / to if gross > 0 else np.nan})
cst = pd.DataFrame(rows)
print("\n=== D: gross, net, turnover and uniform break-even cost ===")
print(cst[cst.costs.isin(["team", "0bp", "5bp", "25bp"])].round(4).to_string(index=False))
hr.to_csv(OUT + "c08_momentum_horse_race.csv", index=False)
hml.to_csv(OUT + "c08_hml_sources.csv", index=False)
cst.to_csv(OUT + "c08_costs.csv", index=False)
