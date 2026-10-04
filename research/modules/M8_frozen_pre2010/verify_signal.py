"""Signal-only verification of run.py (no strategy returns): brute-force loops for the frozen rule (C3-C9),
the team signal lag, and the calendar-shuffle placement (non-overlap, gap >= 1, lengths preserved, uniform start)."""
import sys
sys.path.insert(0, "/home/hashim/projects/GA/project/research/lib")
sys.path.insert(0, "/home/hashim/projects/GA/project/research/modules/M8_frozen_pre2010")
import numpy as np
import pandas as pd
from common import load_fred
import run as M

env, overall = load_fred("EMVENRGYENVREG"), load_fred("EMVOVERALLEMV")
sig = M.share_signal(env, overall)
idx = sig.index
e, o = env.reindex(idx).to_numpy(), overall.reindex(idx).to_numpy()
n = len(idx)
z = np.full(n, np.nan)
for t in range(n):
    lo = max(0, t - 59)
    we, wo = e[lo:t + 1], o[lo:t + 1]
    nz = we != 0
    zeros = (we == 0).sum()
    if e[t] == 0 or nz.sum() < 48 or zeros > 6:
        continue
    ls = np.log(we[nz] / wo[nz])
    z[t] = (np.log(e[t] / o[t]) - ls.mean()) / ls.std(ddof=1)
thr = np.full(n, np.nan)
for t in range(n):
    past = z[:t][~np.isnan(z[:t])]
    if len(past) >= 60:
        thr[t] = np.quantile(past, 0.8)          # linear interpolation, same as pandas
valid = ~np.isnan(z) & ~np.isnan(thr)
ext = valid & (z > thr)
cross = np.zeros(n, bool)
prev = False
for t in range(n):
    if not valid[t]:
        continue                                  # C8: missing month skipped
    cross[t] = ext[t] and not prev
    prev = ext[t]
print("z max|diff|:", np.nanmax(np.abs(z - sig["z"].to_numpy())), "; NaN pattern equal:", (np.isnan(z) == sig["z"].isna().to_numpy()).all())
print("threshold max|diff|:", np.nanmax(np.abs(thr - sig["threshold"].to_numpy())), "; NaN pattern equal:", (np.isnan(thr) == sig["threshold"].isna().to_numpy()).all())
print("crossings identical:", (cross == sig["cross"].to_numpy()).all())
pre = sig.loc[:"2009-12"]
print("pre-2010: zero months", int(pre["zero"].sum()), "; off months", int(pre["off"].sum()), "; first valid z", pre["z"].first_valid_index().date(),
      "; first threshold", pre["threshold"].first_valid_index().date())
# would the team crossing rule (no skipping) differ from C8 anywhere before 2010?
st = pd.Series(ext, idx)
team_style = st & ~st.shift(1, fill_value=False)
print("months where C8 skipping changes a crossing before 2010:", int((team_style.loc[:"2009-12"] != sig["cross"].loc[:"2009-12"]).sum()),
      "; after 2010:", int((team_style.loc["2010":] != sig["cross"].loc["2010":]).sum()))

# decision-time hold equals rolling max of lagged crossings and team cross_and_holds on the lagged cross
grid = pd.date_range("1980-01-31", "2026-09-30", freq="ME")
cd, hold = M.decision_hold(sig["cross"], grid)
from team_pipeline import cross_and_holds
_, h2 = cross_and_holds(cd, (6,))
print("hold == team cross_and_holds(lagged crossings):", bool((h2[6] == hold).all()))
c_idx = np.flatnonzero(cd.to_numpy())
ok = all(hold.iloc[i:i + 6].all() for i in c_idx)
print("every lagged crossing starts a 6-month on-window:", ok)

# shuffle placement: same generator as run.shuffle_test
rng = np.random.default_rng(0)
L = np.array([9, 6, 13, 6, 15])
N = 190
m = len(L)
free = N - L.sum() - (m - 1)
first_start = []
for _ in range(20000):
    order = rng.permutation(m)
    pos = np.sort(rng.choice(free + m, size=m, replace=False))
    Ls = L[order]
    starts = pos + np.r_[0, np.cumsum(Ls)[:-1]]
    arr = np.zeros(N, bool)
    for s_, l_ in zip(starts, Ls):
        assert not arr[s_:s_ + l_].any()
        arr[s_:s_ + l_] = True
    r = M.runs(arr)
    assert len(r) == m and sorted(e_ - s_ + 1 for s_, e_ in r) == sorted(L) and arr.sum() == L.sum() and r[-1][1] < N
    first_start.append(arr.argmax())
occ = np.zeros(N)
print("shuffle placement: 20000 draws, blocks never overlap or touch, lengths preserved; min/max first start", min(first_start), max(first_start))
