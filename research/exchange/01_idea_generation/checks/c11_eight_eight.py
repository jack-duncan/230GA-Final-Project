"""Fact-check C11: proposal A ("8+8 industries ... Timing alpha survives broader legs and dropping Aero"). 2010-2026 only."""
import sys
import warnings
sys.path.insert(0, "/home/hashim/projects/GA/project/research/lib")
import pandas as pd
from common import load_team, nw_ols
from team_pipeline import run_pipeline, team_legs

ff3 = load_team()["ff3"][["Mkt-RF", "SMB", "HML"]]
rows = []
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    g8, b8 = team_legs(8)
    print("8+8 legs:", g8, b8, "| warnings:", [str(x.message) for x in w])
for lab, kw in (("5+5 team", {}), ("8+8", {"green": g8, "brown": b8}),
                ("8+8 ex Aero", {"green": g8, "brown": [b for b in b8 if b != "Aero"]})):
    r = run_pipeline(bootstrap_reps=0, extras=False, paired=False, macro_states=False, **kw)
    for n in ["Original | Short Brown hold 3m", "Pure | Short Brown hold 3m", "Original | Short Brown hold 6m", "Pure | Short Brown hold 6m"]:
        net = r["strategies"][n]["net_return"]
        for p, (a, b) in (("validation", ("2010-01-31", "2022-07-31")), ("covid", ("2020-01-31", "2021-12-31")),
                          ("holdout", ("2022-08-31", "2026-07-31"))):
            s = net.loc[a:b]
            f = nw_ols(s, ff3.reindex(s.index), lags=6)
            rows.append({"legs": lab, "strategy": n, "period": p, "ann_net": 12 * s.mean(), "alpha": 12 * f.params["const"], "t": f.tvalues["const"]})
df = pd.DataFrame(rows)
print(df.pivot_table(index=["strategy", "period"], columns="legs", values="t").round(2).to_string())
df.to_csv("/home/hashim/projects/GA/project/research/exchange/01_idea_generation/checks/c11_eight_eight.csv", index=False)
