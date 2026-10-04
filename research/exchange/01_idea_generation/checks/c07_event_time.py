"""Fact-check C07: idea 2 (event-time profile) run as ChatGPT specified, on 2010-2026 only.

Idea 2: "Hedged Brown residuals are more negative in t+1..t+6 after crossings than unconditionally. Rejected if the
post-event cumulative residual is within one SE of zero, or the move sits in spike month t itself."
Test: event-time averages t-3..t+6; residual on a post-event dummy, NW 6 lags; pass: dummy t > 2 excluding 2020-21.
Also checks the idea-2 (f) premise that repricing is contemporaneous (month t).
"""
import sys
sys.path.insert(0, "/home/hashim/projects/GA/project/research/lib")
import numpy as np
import pandas as pd
from common import nw_ols
from team_pipeline import run_pipeline

pd.set_option("display.width", 200)
OUT = "/home/hashim/projects/GA/project/research/exchange/01_idea_generation/checks/"
res = run_pipeline(bootstrap_reps=0, extras=False, paired=False, macro_states=False)
eps = res["models"]["Brown leg"]["epsilon"]          # FF3 residual of Brown excess (rolling, lagged betas and intercept)
hed = res["models"]["Brown leg"]["hedged"]
A, B = "2010-01-31", "2026-07-31"


def merged_events(cross, a, b, gap=6):
    c = cross.loc[a:b]
    out = []
    for d in c[c].index:
        if not out or (d.to_period("M") - out[-1].to_period("M")).n > gap:
            out.append(d)
    return out


rows, prof_rows = [], []
for key in ("raw", "pure"):
    ev = merged_events(res["signals"][f"cross_{key}"], A, B)
    for series_name, s in (("epsilon", eps), ("hedged", hed)):
        s = s.loc["2009-06":"2026-07"]
        for sample, events in (("all", ev), ("ex 2020-21 events", [e for e in ev if not (2020 <= e.year <= 2021)])):
            mat = []
            for e in events:
                i = s.index.get_loc(e)
                mat.append([s.iloc[i + k] if 0 <= i + k < len(s) else np.nan for k in range(-3, 7)])
            M = pd.DataFrame(mat, columns=[f"t{k:+d}" for k in range(-3, 7)])
            car = M[[f"t{k:+d}" for k in range(1, 7)]].sum(axis=1)
            prof = M.mean()
            prof_rows.append({"signal": key, "series": series_name, "sample": sample, "n_events": len(events),
                              **{c: 100 * v for c, v in prof.items()},
                              "CAR_t+1..t+6_pct": 100 * car.mean(), "CAR_se_pct": 100 * car.std(ddof=1) / np.sqrt(car.notna().sum()),
                              "CAR_t": car.mean() / (car.std(ddof=1) / np.sqrt(car.notna().sum()))})
        # post-event dummy regression (months t+1..t+6 after a merged event)
        post = pd.Series(0.0, index=s.index)
        for e in ev:
            i = s.index.get_loc(e)
            post.iloc[i + 1:i + 7] = 1.0
        spike = pd.Series(0.0, index=s.index)
        for e in ev:
            spike.loc[e] = 1.0
        for sample in ("2010-2026", "2010-2026 ex 2020-21"):
            y = s.loc[A:B]
            X = pd.concat([post.rename("post"), spike.rename("spike_month")], axis=1).loc[A:B]
            if "ex" in sample:
                keep = ~((y.index.year >= 2020) & (y.index.year <= 2021))
                y, X = y[keep], X[keep]
            f = nw_ols(y, X, lags=6)
            rows.append({"signal": key, "series": series_name, "sample": sample, "n": int(f.nobs),
                         "post_months": int(X.post.sum()), "ann_post_effect": 12 * f.params["post"], "t_post": f.tvalues["post"],
                         "spike_month_effect_pct": 100 * f.params["spike_month"], "t_spike": f.tvalues["spike_month"]})
prof = pd.DataFrame(prof_rows)
reg = pd.DataFrame(rows)
print("=== Event-time mean Brown residual (% per month), merged events (6-month gap) ===")
print(prof.round(2).to_string(index=False))
print("\n=== Residual on post-event (t+1..t+6) dummy and spike-month dummy, NW6 ===")
print(reg.round(3).to_string(index=False))
print("\nNote: a Short-Brown rule gains when these residuals are negative.")
prof.to_csv(OUT + "c07_event_profile.csv", index=False)
reg.to_csv(OUT + "c07_post_event_regression.csv", index=False)
