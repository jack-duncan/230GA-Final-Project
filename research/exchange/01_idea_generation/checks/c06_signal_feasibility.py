"""Fact-check C06: data and feasibility claims (idea 1, idea 3, idea 5, critique #6, assumptions 1 and 3).

Claims checked
- Idea 1: "Signal from Jan 1990 (60-month z-score uses 1985-89); purified variant from ~1995 (120-month ridge)"
- Idea 1 pitfall / assumption 1: "early index coverage may be thin"; "the attention index has usable coverage in 1985-2009"
- Critique 6: "a purified signal built from CPI, CFNAI and GSCPI, which are published with a lag and revised"
- Idea 3 / assumption 3: "CPU late 1980s, MCCC ~2003"; "the 60-month z-score burns five years of a short index"
- Idea 5: "1995-2026 ... attention innovations (past-only AR(1) residual)"
Signals only: no pre-2010 strategy returns are computed here (the pre-2010 return test is left clean for idea 1).
"""
import sys
sys.path.insert(0, "/home/hashim/projects/GA/project/research/lib")
import numpy as np
import pandas as pd
from common import load_team, load_cpu, load_mccc, load_emv_env
from team_pipeline import Config, build_signals, team_controls

pd.set_option("display.width", 200)
OUT = "/home/hashim/projects/GA/project/research/exchange/01_idea_generation/checks/"
T = load_team()
macro = T["macro"]
C = Config()
sig = build_signals(macro["attention"], macro, C)


def first(s):
    s = s.dropna()
    s = s[s != False] if s.dtype == bool else s  # noqa: E712
    return s.index.min().strftime("%Y-%m") if len(s) else None


att = macro["attention"].dropna()
print("attention first/last:", att.index.min().strftime("%Y-%m"), att.index.max().strftime("%Y-%m"), "n =", len(att))
print("raw z first non-NaN:", first(sig["raw"]))
print("raw p80 threshold first non-NaN (first month a crossing is possible):", first(sig["threshold_raw"]))
print("first raw crossing:", first(sig["cross_raw"][sig["cross_raw"]]))
print("purification controls complete from:", sig["controls"].dropna().index.min().strftime("%Y-%m"))
print("purified signal first non-NaN:", first(sig["pure"]))
print("purified p80 threshold first non-NaN:", first(sig["threshold_pure"]))
print("first pure crossing:", first(sig["cross_pure"][sig["cross_pure"]]))
print("continuous weight (raw) first non-NaN:", first(sig["w_raw"]))
print("\nmacro file first non-NaN by column:")
for c in macro.columns:
    s = macro[c].dropna()
    print(f"  {c:13s} {s.index.min().strftime('%Y-%m')} .. {s.index.max().strftime('%Y-%m')}")
print("\nDefault purification controls (team_controls, extended=False):", list(team_controls(macro).columns))
print("Extended (ex-post check only) adds:", [c for c in team_controls(macro, extended=True).columns if c not in team_controls(macro).columns])

# Coverage by period: zero share and level of the attention series
emv = load_emv_env()
assert (emv.reindex(att.index) == att).all()
rows = []
for lab, (a, b) in (("1985-1989", ("1985", "1989")), ("1990-1999", ("1990", "1999")), ("2000-2009", ("2000", "2009")),
                    ("2010-2019", ("2010", "2019")), ("2020-2021", ("2020", "2021")), ("validation 2010-01..2022-07", ("2010-01", "2022-07")),
                    ("holdout 2022-08..2026-07", ("2022-08", "2026-07")), ("pre 2021-10", ("1985-01", "2021-09")), ("2021-10..2026-08", ("2021-10", "2026-08"))):
    s = att.loc[a:b]
    rows.append({"period": lab, "n": len(s), "n_zero": int((s == 0).sum()), "zero_share": (s == 0).mean(),
                 "mean": s.mean(), "median": s.median()})
cov = pd.DataFrame(rows)
print("\n=== EMV Energy & Environmental Regulation tracker: zeros and level by period ===")
print(cov.round(3).to_string(index=False))

# Holdout: z-score of zero months and share of in-state months with attention > 0
z = sig["raw"].loc["2022-08":"2026-07"]
a = att.loc["2022-08":"2026-07"]
print("\nholdout months with attention == 0:", int((a == 0).sum()), "of", len(a), "; z range on zero months:",
      round(z[a == 0].min(), 2), "to", round(z[a == 0].max(), 2))
st = sig["state_raw"].loc["2022-08":"2026-07"]
print("holdout p80-state months:", int(st.sum()), "; all with attention > 0:", bool((a[st] > 0).all()))

# Alternative indices
cpu, mccc = load_cpu(), load_mccc()
print("\nCPU:", cpu.dropna().index.min().strftime("%Y-%m"), "..", cpu.dropna().index.max().strftime("%Y-%m"))
print("MCCC:", mccc.dropna().index.min().strftime("%Y-%m"), "..", mccc.dropna().index.max().strftime("%Y-%m"))
for nm, s in (("CPU", cpu), ("MCCC", mccc)):
    zz = (np.log1p(s) - np.log1p(s).rolling(60, min_periods=36).mean()) / np.log1p(s).rolling(60, min_periods=36).std()
    thr = zz.shift(1).expanding(min_periods=60).quantile(0.8)
    print(f"  {nm}: z from {zz.dropna().index.min():%Y-%m}; p80 threshold from {thr.dropna().index.min():%Y-%m}; "
          f"months of index burned before first possible signal = {len(s.loc[:thr.dropna().index.min()]) - 1}")
    cover = s.reindex(pd.date_range("2022-08-31", "2026-07-31", freq="ME")).notna().sum()
    print(f"  {nm}: holdout months covered = {cover} of 48")

# Correlations of the team's raw z with z-scores of the alternatives (2010-2026, overlapping months)
def zsc(s):
    s = np.log1p(s)
    return (s - s.rolling(60, min_periods=36).mean()) / s.rolling(60, min_periods=36).std()
cmp = pd.concat([sig["raw"].rename("team_z"), zsc(cpu).rename("CPU_z"), zsc(mccc).rename("MCCC_z")], axis=1).loc["2010":"2026-07"].dropna()
print("\nCorrelation of team z with CPU z and MCCC z, 2010 onward (common months n=%d):" % len(cmp))
print(cmp.corr().round(3).to_string())

cov.to_csv(OUT + "c06_attention_coverage.csv", index=False)
