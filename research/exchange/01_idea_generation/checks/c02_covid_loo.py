"""Fact-check C02: ChatGPT critique #2, proposal A, assumption 2.

Claims checked
- "Both Holm survivors are COVID; the 3-month rule's 2020-21 alpha (t = 3.21) carries the result."
- "Aero (Boeing-heavy ...), Ships and Util took COVID-specific hits"; assumption 2: "the COVID gains come from
  Aero, Util and Ships shocks"
- Fix: leave-one-industry-out, and rerun excluding Mar 2020-Dec 2021; "If the 6-month t-stats drop below ~1.5"
- "Aero (Boeing-heavy)": Aero industry total market cap from Ken French firm counts x average size
Data 2010-2026 only for strategy returns.
"""
import sys
sys.path.insert(0, "/home/hashim/projects/GA/project/research/lib")
import numpy as np
import pandas as pd
from common import load_team, load_kf_industries, nw_ols
from team_pipeline import run_pipeline, rolling_factor_model, TEAM_BROWN

pd.set_option("display.width", 220)
pd.set_option("display.max_columns", 30)
OUT = "/home/hashim/projects/GA/project/research/exchange/01_idea_generation/checks/"
T = load_team()
ff3 = T["ff3"]
fcols = ["Mkt-RF", "SMB", "HML"]
names = ["Original | Short Brown hold 3m", "Pure | Short Brown hold 3m",
         "Original | Short Brown hold 6m", "Pure | Short Brown hold 6m"]


def alpha_t(r, a, b, drop=None):
    r = r.loc[a:b].dropna()
    if drop is not None:
        r = r[~((r.index >= drop[0]) & (r.index <= drop[1]))]
    f = nw_ols(r, ff3[fcols].reindex(r.index), lags=6)
    return 12 * r.mean(), 12 * f.params["const"], f.tvalues["const"], len(r)


# 1. Validation excluding Mar 2020 - Dec 2021 (ChatGPT's window) and Jan 2020 - Dec 2021 (team COVID window)
base = run_pipeline(bootstrap_reps=0, extras=False, paired=False, macro_states=False)
rows = []
for n in names:
    net = base["strategies"][n]["net_return"]
    for lab, drop in (("validation", None), ("validation ex Mar20-Dec21", ("2020-03-31", "2021-12-31")),
                      ("validation ex Jan20-Dec21", ("2020-01-31", "2021-12-31")), ("covid 2020-21", None)):
        a, b = ("2020-01-31", "2021-12-31") if lab.startswith("covid") else ("2010-01-31", "2022-07-31")
        m, al, t, k = alpha_t(net, a, b, drop)
        rows.append({"strategy": n, "sample": lab, "n": k, "ann_net": m, "ff3_alpha": al, "t": t})
ex = pd.DataFrame(rows)
print("=== Validation with and without the COVID window (FF3 alpha, NW6) ===")
print(ex.round(4).to_string(index=False))

# 2. Leave-one-Brown-industry-out
rows = []
for drop in [None] + TEAM_BROWN:
    brown = [b for b in TEAM_BROWN if b != drop]
    r = run_pipeline(brown=brown, bootstrap_reps=0, extras=False, paired=False, macro_states=False)
    for n in names:
        net = r["strategies"][n]["net_return"]
        for lab, (a, b) in (("validation", ("2010-01-31", "2022-07-31")), ("covid", ("2020-01-31", "2021-12-31")),
                            ("holdout", ("2022-08-31", "2026-07-31"))):
            m, al, t, k = alpha_t(net, a, b)
            rows.append({"dropped": drop or "none", "strategy": n, "period": lab, "ann_net": m, "ff3_alpha": al, "t": t})
loo = pd.DataFrame(rows)
piv = loo.pivot_table(index=["strategy", "period"], columns="dropped", values="t").round(2)
print("\n=== Leave-one-industry-out: FF3 alpha t (NW6) ===")
print(piv[["none"] + TEAM_BROWN].to_string())

# 3. Exact decomposition of COVID gross P&L by Brown industry.
# OLS is linear in y, so the leg's rolling betas equal the mean of industry betas; the leg hedged return is the mean
# of industry hedged returns. Strategy gross_t = position_{t-1} * leg_hedged_t.
ind = T["industries"]
hedged = {}
for i in TEAM_BROWN:
    y = (ind[i] - ff3["RF"]).rename(i)
    al = pd.concat([y, ff3[fcols]], axis=1).dropna()
    b_, h_, e_, a_ = rolling_factor_model(al[i], al[fcols], 60)
    hedged[i] = h_
H = pd.DataFrame(hedged)
leg_h = base["models"]["Brown leg"]["hedged"]
chk = (H.mean(axis=1) - leg_h).loc["2010":"2026"].abs().max()
print(f"\nmax |mean industry hedged - leg hedged| 2010-2026 = {chk:.2e}")
rows = []
for n in names:
    df = base["strategies"][n]
    pos_lag = df["position"].shift(1)
    for lab, (a, b) in (("covid 2020-21", ("2020-01-31", "2021-12-31")), ("validation", ("2010-01-31", "2022-07-31")),
                        ("holdout", ("2022-08-31", "2026-07-31"))):
        idx = df.loc[a:b].index
        contrib = H.reindex(idx).mul(pos_lag.reindex(idx), axis=0) / len(TEAM_BROWN)
        tot = 12 * contrib.sum(axis=1).mean()
        row = {"strategy": n, "period": lab, "ann_gross_total": tot, "check_vs_engine": 12 * df["gross_return"].reindex(idx).mean()}
        for i in TEAM_BROWN:
            row[i] = 12 * contrib[i].mean()
        rows.append(row)
dec = pd.DataFrame(rows)
print("\n=== Annualized gross contribution by Brown industry (short position x industry hedged return / 5) ===")
print(dec.round(4).to_string(index=False))

# 4. Industry hedged returns in 2020 and 2021 by calendar year, and Boeing-heavy check (Aero total cap)
yr = H.loc["2019":"2021"].groupby(H.loc["2019":"2021"].index.year).sum()
print("\n=== Sum of monthly FF3-hedged excess returns by year (per industry) ===")
print(yr.round(3).to_string())
nf = load_kf_industries("nfirms")
sz = load_kf_industries("size")   # average firm size, $ millions
cap = (nf * sz)
print("\n=== Ken French industry totals (n firms x avg size, $bn) at Dec 2018 / Dec 2019 ===")
for d in ("2018-12-31", "2019-12-31"):
    print(d, {i: (int(nf.loc[d, i]), round(cap.loc[d, i] / 1000, 1)) for i in TEAM_BROWN})

ex.to_csv(OUT + "c02_validation_ex_covid.csv", index=False)
loo.to_csv(OUT + "c02_leave_one_out.csv", index=False)
dec.to_csv(OUT + "c02_covid_contributions.csv", index=False)
