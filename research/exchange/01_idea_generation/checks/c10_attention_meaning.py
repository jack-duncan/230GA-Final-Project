"""Fact-check C10: what the 'climate-transition attention' series measures (a point ChatGPT did not raise).

The team column is FRED EMVENRGYENVREG, the Baker-Bloom-Davis-Kost Equity Market Volatility tracker for Energy and
Environmental Regulation: newspaper articles about stock-market volatility that also mention the category, scaled to
the VIX. Checks: co-movement with overall EMV and VIX, and with the two climate-specific indices (CPU, MCCC);
whether p80 crossings coincide with high overall-EMV months.
"""
import sys
sys.path.insert(0, "/home/hashim/projects/GA/project/research/lib")
import numpy as np
import pandas as pd
from scipy import stats
from common import load_team, load_fred, load_cpu, load_mccc, rolling_z
from team_pipeline import Config, build_signals

T = load_team()
sig = build_signals(T["macro"]["attention"], T["macro"], Config())
env = T["macro"]["attention"]
emv = load_fred("EMVOVERALLEMV")
vix = load_fred("VIXCLS", how="mean")
cpu, mccc = load_cpu(), load_mccc()
z = lambda s: rolling_z(np.log1p(s))  # noqa: E731  team transform
D = pd.concat([env.rename("EMV_env"), emv.rename("EMV_overall"), vix.rename("VIX"), cpu.rename("CPU"), mccc.rename("MCCC")], axis=1)
Z = pd.concat([sig["raw"].rename("team_z"), z(emv).rename("EMV_overall_z"), z(vix).rename("VIX_z"),
               z(cpu).rename("CPU_z"), z(mccc).rename("MCCC_z")], axis=1)
for lab, (a, b) in (("1993-2026", ("1993-01", "2026-07")), ("2010-2026", ("2010-01", "2026-07")),
                    ("validation", ("2010-01", "2022-07")), ("holdout", ("2022-08", "2026-07"))):
    c = Z.loc[a:b].corr()["team_z"].drop("team_z")
    n = Z.loc[a:b][["team_z", "EMV_overall_z"]].dropna().shape[0]
    print(f"{lab:11s} corr(team z, .): " + ", ".join(f"{k} {v:+.2f}" for k, v in c.items()) + f"  (n={n} with EMV overall)")
print("\nLevel correlations 1990-2025:")
print(D.loc["1990":"2025-06"].corr().round(2).to_string())

# Crossing months vs overall-EMV z above its own expanding p80
thr = Z["EMV_overall_z"].shift(1).expanding(min_periods=60).quantile(0.8)
hi = (Z["EMV_overall_z"] > thr).where(thr.notna())
cross = sig["cross_raw"]
for lab, (a, b) in (("1993-2026", ("1993-01", "2026-07")), ("2010-2026", ("2010-01", "2026-07"))):
    c, h = cross.loc[a:b], hi.loc[a:b]
    ok = h.notna()
    c, h = c[ok].astype(bool), h[ok].astype(bool)
    tab = pd.crosstab(c, h)
    odds, p = stats.fisher_exact(tab.values)
    print(f"\n{lab}: crossings {int(c.sum())}; share in high overall-EMV months {h[c].mean():.2f} vs {h[~c].mean():.2f} otherwise; "
          f"Fisher odds {odds:.2f}, p {p:.4f}")
cov = sig["cross_raw"].loc["2020":"2021"]
print("\nCOVID-window crossings and context:")
for d in cov[cov].index:
    print(f"  {d:%Y-%m}: EMV_env {env[d]:.2f}, EMV_overall {emv[d]:.1f}, VIX(mean) {vix[d]:.1f}, team z {sig['raw'][d]:.2f}")
