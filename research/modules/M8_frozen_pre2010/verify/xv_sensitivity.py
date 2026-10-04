"""Exploratory sensitivity of the M8 verdict to readings the rule text leaves open (NOT part of the verdict).

Re-uses the independent engine in xv_independent.py (run via runpy; no import of run.py or lib/).
Variants:
  V1 z needs a full 60-month calendar history (no burn-in from 48 months): first z 1989-12.
  V2 threshold with ">=" instead of ">" (tie handling).
  V3 threshold quantile by 'lower' / 'higher' order statistic instead of linear interpolation.
  V4 shuffle null that moves each crossing's own 6-month window (crossing-level windows, union afterwards)
     instead of merged blocks; 2,000 draws.
  V5 3-month hold instead of 6 (the other team hold; not the frozen rule).
Writes verify/xv_sensitivity.csv.
Run: cd /home/hashim/projects/GA/project/research && uv run python modules/M8_frozen_pre2010/verify/xv_sensitivity.py
"""
import math
import pathlib
import runpy

import numpy as np
import pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
G = runpy.run_path(str(HERE / "xv_independent.py"), run_name="xv")
g, E, O, logs, is_zero, missing = G["g"], G["E"], G["O"], G["logs"], G["is_zero"], G["missing"]
grid, attribution, MB, runs, decision_hold = G["grid"], G["attribution"], G["MB"], G["runs"], G["decision_hold"]
win, wpos, d_lo, d_hi = G["win"], G["wpos"], G["d_lo"], G["d_hi"]
n = len(g)


def signal(full_hist=False, ge=False, qmethod="linear"):
    z = np.full(n, np.nan)
    for t in range(n):
        lo = max(0, t - 59)
        if full_hist and t < 59:
            continue
        if missing[t] or is_zero[lo:t + 1].sum() > 6:
            continue
        w = logs[lo:t + 1]
        w = w[~np.isnan(w)]
        if len(w) < 48:
            continue
        z[t] = (logs[t] - w.mean()) / w.std(ddof=1)
    thr = np.full(n, np.nan)
    hist = []
    for t in range(n):
        if len(hist) >= 60:
            thr[t] = np.quantile(hist, 0.8, method=qmethod)
        if not np.isnan(z[t]):
            hist.append(z[t])
    valid = ~np.isnan(z) & ~np.isnan(thr)
    ext = valid & ((z >= thr) if ge else (z > thr))
    cross = np.zeros(n, bool)
    prev = False
    for t in range(n):
        if valid[t]:
            cross[t] = ext[t] and not prev
            prev = ext[t]
    return pd.Series(cross, index=g), valid


def hold_from(cross, hold_len=6):
    h = pd.Series(False, index=grid)
    for t in cross.index[cross.to_numpy()]:
        for k in range(hold_len):
            d = t + pd.offsets.MonthEnd(1 + k)
            if d in h.index:
                h[d] = True
    return h.to_numpy()


rows = []
base_cross, _ = signal()
for lab, kw in (("frozen (C5-C8)", {}), ("V1 full 60m history for z", {"full_hist": True}), ("V2 z >= threshold", {"ge": True}),
                ("V3 lower order statistic", {"qmethod": "lower"}), ("V3 higher order statistic", {"qmethod": "higher"})):
    cr, valid = signal(**kw)
    h = hold_from(cr)
    a = attribution(h, MB, 6)
    first_valid = g[valid].min()
    rows.append({"variant": lab, "first_valid_data_month": first_valid.strftime("%Y-%m"),
                 "crossings_differ_vs_frozen_pre2010": int((cr.loc[:"2009-12"] != base_cross.loc[:"2009-12"]).sum()),
                 "alpha_ann": a["alpha_ann"], "t_nw6": a["t"], "p_t(n-k)": a["p_two"], "pi": a["pi"],
                 "months_in_position": a["months_in_pos"], "note": "same window 1994-03..2009-12 for comparability"})
h3 = hold_from(base_cross, 3)
a3 = attribution(h3, MB, 6)
rows.append({"variant": "V5 3-month hold (not the frozen rule)", "first_valid_data_month": "", "crossings_differ_vs_frozen_pre2010": 0,
             "alpha_ann": a3["alpha_ann"], "t_nw6": a3["t"], "p_t(n-k)": a3["p_two"], "pi": a3["pi"],
             "months_in_position": a3["months_in_pos"], "note": ""})

# V4: crossing-level shuffle. Each crossing whose decision month is in d_lo..d_hi-5 gets a random decision month in
# d_lo..d_hi-5 (uniform, independent); holds are the union (extend-not-stack). Crossings near the edges stay put.
hP = hold_from(base_cross)
real = attribution(hP, MB, 6)["alpha_m"]
cd = np.flatnonzero(base_cross.reindex(grid, fill_value=False).shift(1, fill_value=False).to_numpy())
movable = cd[(cd >= d_lo) & (cd <= d_hi - 5)]
fixed = np.setdiff1d(cd, movable)
rng = np.random.default_rng(7)
draws, mons = [], []
for r in range(2000):
    starts = np.r_[fixed, rng.integers(d_lo, d_hi - 5 + 1, size=len(movable))]
    hb = np.zeros(len(grid), bool)
    for s in starts:
        hb[s:s + 6] = True
    a_ = attribution(hb, MB, 6)
    draws.append(a_["alpha_m"])
    mons.append(a_["months_in_pos"])
draws = np.array(draws)
rows.append({"variant": "V4 crossing-level shuffle (2,000 draws)", "first_valid_data_month": "", "crossings_differ_vs_frozen_pre2010": 0,
             "alpha_ann": 12 * real, "t_nw6": np.nan, "p_t(n-k)": (1 + (draws >= real).sum()) / (len(draws) + 1), "pi": np.nan,
             "months_in_position": np.nan,
             "note": f"one-sided p in p column; {len(movable)} movable crossings; null median {12 * np.median(draws):+.4f}, "
                     f"null mean months in position {np.mean(mons):.0f} vs real 142"})
out = pd.DataFrame(rows)
out.to_csv(HERE / "xv_sensitivity.csv", index=False)
print(out.to_string(index=False))
