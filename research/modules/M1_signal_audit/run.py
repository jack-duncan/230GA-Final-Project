"""M1_signal_audit: what does the team's "climate-transition attention" signal measure, and do genuine
climate-concern measures behave differently?

Run: cd /home/hashim/projects/GA/project/research && uv run python modules/M1_signal_audit/run.py
Outputs: outputs/tables/M1_signal_audit_*.csv (+ .tex for report tables), outputs/figures/M1_signal_audit_*.{pdf,png},
data/derived/attention_measures.csv. Lag convention: every signal dated t uses information through the end of month t
and is paired with the month t+1 return; hedge betas/intercepts are estimated through t-1.

Revision after independent verification (VERIFY.md):
- Q3 counterfactuals (frozen pre-regime window scaling; zeros treated as missing) test whether the zero-driven window
  arithmetic changed which months the team rule traded; base-rate tests for "entries follow a zero month".
- Correlation tests in the ledger use a direction-free delta-method HAC test (helpers.hac_corr), except the two
  pre-specified Q5 primaries, which keep their pre-specified slope test and get reverse-direction, NW(24), direction-free
  and partial-correlation robustness rows plus Holm over the two. A hypothesis reported in two tables (same series pair
  or same signal/outcome, same sample) is recorded once in the ledger; tables carry the ledger_test_id.
- Q4 adds circular-shift permutation and LPM NW(12) p-values next to each Fisher test.
- The minimum EMV_env needed to cross is solved exactly (root-finder) instead of on a grid.
"""
import sys, pathlib
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "lib")); sys.path.insert(0, str(HERE))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from common import (load_team, legs_by_emissions, leg_returns, load_fred, load_cpu, load_mccc, load_emv_env,
                    rolling_z, holm, PERIODS, DERIVED, TABLES)
from plotstyle import (SERIES, ENTITY, BLUE, VIOLET, INK, INK2, MUTED, GRID, NEUTRAL_MID, savefig)
from scipy import stats
from common import nw_ols
from helpers import (MODULE, Ledger, save_table, ym, ar1_shock_expanding, ar1_shock_full, rolling_factor_resid,
                     expanding_tail, cross_and_holds, corr_test, ic_test, reg_row, fisher_2x2, corr_key, zstd,
                     partial_corr_test, min_level_to_cross, circular_shift_p)

pd.set_option("display.width", 200); pd.set_option("display.max_columns", 40)
L = Ledger()
KEY = []


def key(name, value, source, note=""):
    KEY.append(dict(name=name, value=value, source_table=f"{MODULE}_{source}.csv", note=note))


BREAK = pd.Timestamp("2021-10-31")          # first month of the post-2021-09 zero regime
LAST_EMV = pd.Timestamp("2026-08-31")       # last month of EMV data; VIX September 2026 is a partial month
TOPICS = ["Climate Legislation/Regulations", "Carbon Tax", "Carbon Credits Market", "Renewable Energy",
          "Agreements/Actions"]
MEASURES = ["EMV_env", "EMV_overall", "VIX", "EMV_env_share", "MCCC", "MCCC_transition", "CPU"]
CLIMATE = ["MCCC", "MCCC_transition", "CPU"]

# ============================================================================= data
team = load_team()
att = team["macro"]["attention"]
emv_env = load_emv_env()
emv_all = load_fred("EMVOVERALLEMV").rename("EMV_overall")
vix = load_fred("VIXCLS", how="mean").rename("VIX").dropna().loc[:LAST_EMV]
share = (emv_env / emv_all).rename("EMV_env_share")
mccc = load_mccc("Aggregate")
mccc_tr = pd.concat([load_mccc(c) for c in TOPICS], axis=1).mean(axis=1).rename("MCCC_transition")
cpu = load_cpu()
rate = (-load_fred("GS10").diff()).rename("RATE")       # rate factor proxy: -change in 10y yield, percentage points
LEVELS = {"EMV_env": emv_env, "EMV_overall": emv_all, "VIX": vix, "EMV_env_share": share, "MCCC": mccc,
          "MCCC_transition": mccc_tr, "CPU": cpu}
LEVELS = {k: v.dropna() for k, v in LEVELS.items()}

ff3 = team["ff3"][["Mkt-RF", "SMB", "HML"]]
rf = team["ff3"]["RF"]
green_names, brown_names = legs_by_emissions(5)
assert green_names == ["Fun", "RlEst", "Drugs", "Telcm", "Fin"] and brown_names == ["Util", "Ships", "Aero", "Steel", "BldMt"]
green, brown, gb = leg_returns(team["industries"], green_names, brown_names)
brown_x = (brown - rf).rename("brown_excess"); green_x = (green - rf).rename("green_excess")
fac_rate = ff3.join(rate, how="inner")

# ============================================================================= Q1 identity
print("Q1 identity")
d = pd.concat([att.rename("team_attention"), emv_env], axis=1)
both = d.dropna()
diff = (both["team_attention"] - both["EMV_env"]).abs()
ident = pd.DataFrame([{
    "team_attention_nonmissing_months": int(att.notna().sum()), "fred_EMVENRGYENVREG_months": int(emv_env.notna().sum()),
    "overlap_months": len(both), "first_month": ym(both.index[0]), "last_month": ym(both.index[-1]),
    "months_team_only": int((d["team_attention"].notna() & d["EMV_env"].isna()).sum()),
    "months_fred_only": int((d["team_attention"].isna() & d["EMV_env"].notna()).sum()),
    "months_not_exactly_equal": int((diff > 0).sum()), "max_abs_difference": float(diff.max())}])
assert ident.loc[0, "months_not_exactly_equal"] == 0 and ident.loc[0, "months_team_only"] == 0 and ident.loc[0, "months_fred_only"] == 0
save_table(ident, "identity")
key("identity_overlap_months", len(both), "identity"); key("identity_months_not_equal", 0, "identity")

# ============================================================================= signals
Z = {k: rolling_z(np.log1p(v)).rename(f"z_{k}") for k, v in LEVELS.items()}
team_z = rolling_z(np.log1p(att))
assert np.allclose(team_z.dropna(), Z["EMV_env"].reindex(team_z.dropna().index), rtol=0, atol=1e-12)
z_env = Z["EMV_env"]
SH = {k: ar1_shock_expanding(v, min_obs=36).rename(f"{k}_shock") for k, v in LEVELS.items()}

# ============================================================================= Q2 decomposition
print("Q2 decomposition")
SUBS = {"full": (None, None), "pre_2021-10": (None, "2021-09-30"), "post_2021-10": ("2021-10-31", None),
        "validation": PERIODS["validation"], "holdout": PERIODS["holdout"]}
lev = pd.DataFrame({"EMV_env": emv_env, "EMV_overall": emv_all, "VIX": vix, "EMV_env_share": share})
lev["log_EMV_env_nonzero"] = np.log(lev["EMV_env"].where(lev["EMV_env"] > 0))
lev["log_EMV_overall"] = np.log(lev["EMV_overall"]); lev["log_VIX"] = np.log(lev["VIX"])
for k in ("EMV_env", "EMV_overall", "VIX", "EMV_env_share"):
    lev[f"z_{k}"] = Z[k]
BLOCKS = [  # (block, dependent, [regressor sets])
    ("level", "EMV_env", [["EMV_overall"], ["VIX"], ["EMV_overall", "VIX"]]),
    ("log_nonzero", "log_EMV_env_nonzero", [["log_EMV_overall"], ["log_VIX"], ["log_EMV_overall", "log_VIX"]]),
    ("team_signal_z", "z_EMV_env", [["z_VIX"], ["z_EMV_overall"], ["z_VIX", "z_EMV_overall"]]),
    ("share_level", "EMV_env_share", [["EMV_overall"], ["VIX"], ["EMV_overall", "VIX"]]),
    ("share_z", "z_EMV_env_share", [["z_VIX"], ["z_EMV_overall"], ["z_VIX", "z_EMV_overall"]]),
]
rows = []
for block, dep, xsets in BLOCKS:
    allx = sorted({c for xs in xsets for c in xs})
    base = lev[[dep] + allx].dropna()                     # common sample within a block
    for sname, (a, b) in SUBS.items():
        for xs in xsets:
            r = reg_row(base[dep], base[xs], start=a, end=b)
            if r.get("n", 0) < 12:
                continue
            row = dict(block=block, dependent=dep, regressors=" + ".join(xs), sample=sname, start=ym(r["start"]),
                       end=ym(r["end"]), n=r["n"], r2=r["r2"], wald_F=r["wald_F"], wald_p=r["wald_p"])
            for i, c in enumerate(xs, 1):
                row[f"x{i}"] = c; row[f"b{i}"] = r[f"b_{c}"]; row[f"t{i}"] = r[f"t_{c}"]
            rows.append(row)
            if len(xs) == 2:   # single-regressor slope tests are recorded once, via the correlation table below
                kind = "primary" if (block == "team_signal_z" and sname == "full") else ("robustness" if block == "team_signal_z" else "exploratory")
                L.add(f"Q2_joint_{block}_{sname}", "Q2 decomposition: joint explanatory power",
                      f"HAC Wald F, {dep} on {' + '.join(xs)} (R2={r['r2']:.3f})", r["wald_F"], r["wald_p"], r["n"], kind,
                      f"sample {ym(r['start'])} to {ym(r['end'])}")
decomp = pd.DataFrame(rows)
save_table(decomp, "decomposition")
tsz = decomp[decomp.block == "team_signal_z"].copy()
save_table(tsz[["sample", "start", "end", "n", "regressors", "r2", "b1", "t1", "b2", "t2"]], "decomposition_team_signal",
           tex=dict(caption="How much of the team signal $z_t=$ rolling\\_z(log1p(EMV\\_env)) is explained by rolling z-scores of "
                            "log1p(VIX) and log1p(overall EMV). OLS, Newey-West (6) t-statistics.",
                    label="tab:m1_decomp", fmt={"r2": "{:.3f}", "b1": "{:.2f}", "t1": "{:.1f}", "b2": "{:.2f}", "t2": "{:.1f}", "n": "{:d}"},
                    rename={"r2": "R2", "b1": "slope 1", "t1": "t 1", "b2": "slope 2", "t2": "t 2"}))
g = lambda blk, s, x: decomp[(decomp.block == blk) & (decomp["sample"] == s) & (decomp.regressors == x)].iloc[0]
for s in SUBS:
    for x in ("z_VIX", "z_EMV_overall", "z_VIX + z_EMV_overall"):
        try:
            key(f"R2_teamz_on_{x.replace(' + ', '_and_')}_{s}", g("team_signal_z", s, x)["r2"], "decomposition")
        except IndexError:
            pass
    j = g("team_signal_z", s, "z_VIX + z_EMV_overall")
    key(f"joint_teamz_{s}_b_zVIX", j["b1"], "decomposition"); key(f"joint_teamz_{s}_t_zVIX", j["t1"], "decomposition")
    key(f"joint_teamz_{s}_b_zEMVoverall", j["b2"], "decomposition"); key(f"joint_teamz_{s}_t_zEMVoverall", j["t2"], "decomposition")
    key(f"joint_teamz_{s}_n", j["n"], "decomposition")
for x in ("EMV_overall", "VIX", "EMV_overall + VIX"):
    key(f"R2_EMVenv_level_on_{x.replace(' + ', '_and_')}_full", g("level", "full", x)["r2"], "decomposition")
    key(f"R2_share_level_on_{x.replace(' + ', '_and_')}_full", g("share_level", "full", x)["r2"], "decomposition")
for x in ("log_EMV_overall", "log_VIX", "log_EMV_overall + log_VIX"):
    key(f"R2_logEMVenv_nonzero_on_{x.replace(' + ', '_and_')}_full", g("log_nonzero", "full", x)["r2"], "decomposition")
key("decomp_teamz_full_start", g("team_signal_z", "full", "z_VIX")["start"], "decomposition")
# the topic-share series: level summary, and the size of nonzero shares after 2021-10
_sh = share.dropna(); _shp = _sh.loc[BREAK:]; _shp = _shp[_shp > 0]
shs = pd.DataFrame([dict(start=ym(_sh.index[0]), end=ym(_sh.index[-1]), n=len(_sh), mean_share=_sh.mean(), median_share=_sh.median(),
                         n_nonzero_post_2021_10=len(_shp), min_nonzero_share_post_2021_10=_shp.min(),
                         max_nonzero_share_post_2021_10=_shp.max())])
save_table(shs, "share_summary")
for c in shs.columns[2:]:
    key(f"share_{c}", shs.loc[0, c], "share_summary")

# pairwise correlations
PAIRS = [("level", "EMV_env", "EMV_overall"), ("level", "EMV_env", "VIX"), ("level", "EMV_overall", "VIX"),
         ("log_nonzero", "log_EMV_env_nonzero", "log_EMV_overall"), ("log_nonzero", "log_EMV_env_nonzero", "log_VIX"),
         ("team_signal_z", "z_EMV_env", "z_EMV_overall"), ("team_signal_z", "z_EMV_env", "z_VIX"),
         ("share_level", "EMV_env_share", "EMV_overall"), ("share_level", "EMV_env_share", "VIX"),
         ("share_z", "z_EMV_env_share", "z_EMV_overall"), ("share_z", "z_EMV_env_share", "z_VIX")]
rows = []
for block, a_, b_ in PAIRS:
    for sname, (s0, s1) in SUBS.items():
        c = corr_test(lev[b_], lev[a_], start=s0, end=s1)
        if pd.isna(c["pearson"]):
            continue
        kind = "robustness" if block == "team_signal_z" else "exploratory"
        tid = L.add(f"Q2_corr_{a_}_{b_}_{sname}", "Q2 decomposition: pairwise correlation",
                    f"Pearson r {a_} vs {b_} (direction-free delta-method HAC(6) test)", c["pearson"], c["p_hac"], c["n"], kind,
                    f"sample {ym(c['start'])} to {ym(c['end'])}", key=corr_key(a_, b_, c["start"], c["end"]))
        rows.append(dict(block=block, series_a=a_, series_b=b_, sample=sname, start=ym(c["start"]), end=ym(c["end"]),
                         n=c["n"], pearson=c["pearson"], t_hac=c["t_hac"], p_hac=c["p_hac"], t_slope=c["t_slope"],
                         p_slope=c["p_slope"], spearman=c["spearman"], r2=c["pearson"] ** 2, ledger_test_id=tid))
dcorr = pd.DataFrame(rows)
save_table(dcorr, "decomposition_correlations",
           tex=dict(caption="Correlations of the Energy and Environmental Regulation EMV tracker with overall EMV and monthly "
                            "average VIX. t is the direction-free delta-method HAC(6) t of the correlation.", label="tab:m1_decomp_corr",
                    columns=["series_a", "series_b", "sample", "start", "end", "n", "pearson", "t_hac", "spearman"],
                    fmt={"pearson": "{:.2f}", "t_hac": "{:.1f}", "spearman": "{:.2f}", "n": "{:d}"},
                    rename={"t_hac": "t (HAC)"}))
gc = lambda a_, b_, s: dcorr[(dcorr.series_a == a_) & (dcorr.series_b == b_) & (dcorr["sample"] == s)].iloc[0]
for a_, b_ in [("EMV_env", "EMV_overall"), ("EMV_env", "VIX"), ("log_EMV_env_nonzero", "log_EMV_overall"),
               ("log_EMV_env_nonzero", "log_VIX"), ("z_EMV_env", "z_VIX"), ("z_EMV_env", "z_EMV_overall"),
               ("EMV_env_share", "VIX"), ("EMV_env_share", "EMV_overall"), ("z_EMV_env_share", "z_VIX"), ("EMV_overall", "VIX")]:
    for s in ("full", "pre_2021-10", "post_2021-10"):
        try:
            key(f"corr_{a_}_{b_}_{s}", gc(a_, b_, s)["pearson"], "decomposition_correlations")
        except IndexError:
            pass

# ============================================================================= Q3 zeros
print("Q3 zeros")
zero = emv_env.eq(0)
ZP = {"full_1985": ("1985-01-31", "2026-08-31"), "pre_2021-10": ("1985-01-31", "2021-09-30"),
      "post_2021-10": ("2021-10-31", "2026-08-31")}
ZP.update({k: v for k, v in PERIODS.items() if k != "full_1970"})
rows = []
for k, (a, b) in ZP.items():
    s = zero.loc[a:b]
    rows.append(dict(period=k, start=ym(s.index[0]), end=ym(s.index[-1]), n_months=len(s), n_zero=int(s.sum()), zero_share=s.mean()))
zc = pd.DataFrame(rows)
pre, post = zc.set_index("period").loc["pre_2021-10"], zc.set_index("period").loc["post_2021-10"]
assert (pre.n_zero, pre.n_months, post.n_zero, post.n_months) == (12, 441, 39, 59)
orr, pf = fisher_2x2(post.n_zero, post.n_months - post.n_zero, pre.n_zero, pre.n_months - pre.n_zero)
L.add("Q3_fisher_zero_pre_post", "Q3 zero inflation", "Fisher exact odds ratio (zero month, post-2021-10 vs pre)", orr, pf,
      int(pre.n_months + post.n_months), "primary", "2x2: zero vs nonzero months, 1985-01..2021-09 vs 2021-10..2026-08")
zc["fisher_odds_ratio_post_vs_pre"] = np.nan; zc["fisher_p_post_vs_pre"] = np.nan
zc.loc[zc.period == "post_2021-10", ["fisher_odds_ratio_post_vs_pre", "fisher_p_post_vs_pre"]] = [orr, pf]
save_table(zc, "zero_counts",
           tex=dict(caption="Exact zeros in EMV\\_env (FRED EMVENRGYENVREG) by period. Fisher exact test of the zero rate "
                            "2021-10 to 2026-08 versus 1985-01 to 2021-09.", label="tab:m1_zeros",
                    columns=["period", "start", "end", "n_months", "n_zero", "zero_share"],
                    fmt={"zero_share": "{:.2f}", "n_months": "{:d}", "n_zero": "{:d}"}))
for k in zc.period:
    r = zc.set_index("period").loc[k]
    key(f"zeros_{k}", f"{int(r.n_zero)}/{int(r.n_months)}", "zero_counts"); key(f"zero_share_{k}", r.zero_share, "zero_counts")
key("fisher_zero_odds_ratio", orr, "zero_counts"); key("fisher_zero_p", pf, "zero_counts")
zshare24 = zero.astype(float).rolling(24).mean().rename("zero_share_24m")
save_table(zshare24.dropna().rename_axis("date").reset_index(), "zero_share_24m")
key("zero_share_24m_max_pre2021", zshare24.loc[:"2020-12-31"].max(), "zero_share_24m")
key("zero_share_24m_max_all", zshare24.max(), "zero_share_24m"); key("zero_share_24m_argmax", ym(zshare24.idxmax()), "zero_share_24m")

# team state machine
state, thr = expanding_tail(z_env, 0.80, 60)
cross, h3, h6 = cross_and_holds(state)
n_p80_team_window = int(state.loc["2010-01-31":"2026-07-31"].sum())
assert n_p80_team_window == 34, n_p80_team_window        # team notebook prints 34
key("team_p80_months_2010_2026-07", n_p80_team_window, "zero_mechanics", "replicates team notebook")
prev_zero = zero.shift(1, fill_value=False)
lz = np.log1p(emv_env)

# mechanics by period
MP = {"threshold_sample": (thr.first_valid_index(), LAST_EMV), "pre_2021-10": (thr.first_valid_index(), pd.Timestamp("2021-09-30")),
      "post_2021-10": (BREAK, LAST_EMV), "validation": PERIODS["validation"], "holdout": PERIODS["holdout"]}
rows = []
for k, (a, b) in MP.items():
    idx = thr.loc[a:b].dropna().index
    zz, st, cr = zero.reindex(idx), state.reindex(idx), cross.reindex(idx)
    rows.append(dict(period=k, start=ym(idx[0]), end=ym(idx[-1]), n_months=len(idx), n_zero=int(zz.sum()),
                     mean_z_zero_months=z_env.reindex(idx)[zz].mean(), mean_z_nonzero_months=z_env.reindex(idx)[~zz].mean(),
                     share_nonzero_months_above_threshold=st[~zz].mean(), share_zero_months_above_threshold=st[zz].mean() if zz.any() else np.nan,
                     n_state_months=int(st.sum()), n_crossings=int(cr.sum()),
                     n_crossings_prev_month_zero=int((cr & prev_zero.reindex(idx)).sum()),
                     share_months_in_hold3=h3.reindex(idx).mean(), share_months_in_hold6=h6.reindex(idx).mean(),
                     mean_threshold=thr.reindex(idx).mean(), min_threshold=thr.reindex(idx).min(), max_threshold=thr.reindex(idx).max(),
                     # base rate for "crossings follow a zero month": nonzero months whose previous month is zero
                     n_nonzero_months=int((~zz).sum()), n_nonzero_prev_zero=int((~zz & prev_zero.reindex(idx)).sum()),
                     n_state_prev_zero=int((st & prev_zero.reindex(idx)).sum()),
                     # how much of the continuous z (used by the IC tests, not by the rule) is the zero/nonzero split
                     corr_z_nonzero_dummy=z_env.reindex(idx).corr((~zz).astype(float))))
mech = pd.DataFrame(rows)
save_table(mech, "zero_mechanics",
           tex=dict(caption="What the zeros do to the team rule. State = z above the expanding past-only 80th percentile; "
                            "crossing = state switches on; hold3/hold6 = share of months inside a 3- or 6-month Short-Brown window.",
                    label="tab:m1_zero_mech",
                    columns=["period", "start", "end", "n_months", "n_zero", "mean_z_zero_months", "mean_z_nonzero_months",
                             "share_nonzero_months_above_threshold", "n_nonzero_prev_zero", "n_crossings", "n_crossings_prev_month_zero",
                             "share_months_in_hold6"],
                    fmt={"mean_z_zero_months": "{:.2f}", "mean_z_nonzero_months": "{:.2f}", "share_nonzero_months_above_threshold": "{:.2f}",
                         "share_months_in_hold6": "{:.2f}", "n_months": "{:d}", "n_zero": "{:d}", "n_crossings": "{:d}",
                         "n_crossings_prev_month_zero": "{:d}", "n_nonzero_prev_zero": "{:d}"},
                    rename={"mean_z_zero_months": "z|zero", "mean_z_nonzero_months": "z|nonzero",
                            "share_nonzero_months_above_threshold": "P(state|nonzero)", "n_crossings": "crossings",
                            "n_nonzero_prev_zero": "nonzero after zero",
                            "n_crossings_prev_month_zero": "crossings after zero", "share_months_in_hold6": "in hold6"}))
for _, r in mech.iterrows():
    for c in ("n_zero", "n_months", "mean_z_zero_months", "mean_z_nonzero_months", "share_nonzero_months_above_threshold",
              "share_zero_months_above_threshold", "n_crossings", "n_crossings_prev_month_zero", "share_months_in_hold3",
              "share_months_in_hold6", "mean_threshold", "min_threshold", "max_threshold", "n_state_months", "n_nonzero_months", "n_nonzero_prev_zero",
              "n_state_prev_zero", "corr_z_nonzero_dummy"):
        key(f"mech_{r.period}_{c}", r[c], "zero_mechanics")
# Fisher in holdout: is being above threshold just "nonzero this month"?
hidx = thr.loc[PERIODS["holdout"][0]:PERIODS["holdout"][1]].dropna().index
zz, st = zero.reindex(hidx), state.reindex(hidx)
o2, p2 = fisher_2x2(int((st & ~zz).sum()), int((~st & ~zz).sum()), int((st & zz).sum()), int((~st & zz).sum()))
L.add("Q3_fisher_state_nonzero_holdout", "Q3 zero inflation", "Fisher exact odds ratio (above threshold | nonzero vs zero month), holdout",
      o2, p2, len(hidx), "exploratory", "holdout 2022-08..2026-07")

# window arithmetic: EMV_env level needed to cross in month t given the trailing 59 months (exact root, not a grid)
rows = []
for t in [pd.Timestamp(x) for x in ["2019-07-31", "2020-07-31", "2021-07-31", "2021-09-30", "2022-07-31", "2023-07-31",
                                    "2024-07-31", "2025-07-31", "2026-07-31"]]:
    past = lz.loc[:t].iloc[-60:-1].to_numpy()
    win = lz.loc[:t].iloc[-60:]
    nz = emv_env.loc[:t].iloc[-60:]; nz = nz[nz > 0]
    rows.append(dict(month=ym(t), window_zero_share=(win == 0).mean(), window_mean_log1p=win.mean(), window_sd_log1p=win.std(ddof=1),
                     threshold=thr.loc[t], z_of_zero_month=(0 - np.r_[past, 0].mean()) / np.r_[past, 0].std(ddof=1),
                     min_EMV_env_to_cross=min_level_to_cross(past, thr.loc[t]),
                     window_min_nonzero_EMV_env=nz.min(), window_median_nonzero_EMV_env=nz.median()))
wa = pd.DataFrame(rows)
save_table(wa, "zero_window_arithmetic",
           tex=dict(caption="Trailing-window arithmetic of the team z-score. min\\_EMV\\_env\\_to\\_cross is the smallest EMV\\_env "
                            "value in month t that puts z above the expanding 80th-percentile threshold, given the previous 59 months.",
                    label="tab:m1_window", fmt={c: "{:.2f}" for c in wa.columns if c != "month"}))
for _, r in wa.iterrows():
    for c in ("window_zero_share", "threshold", "z_of_zero_month", "min_EMV_env_to_cross", "window_median_nonzero_EMV_env",
              "window_min_nonzero_EMV_env", "window_mean_log1p", "window_sd_log1p"):
        key(f"window_{r.month}_{c}", r[c], "zero_window_arithmetic")

# counterfactuals: did the zero-driven window arithmetic change which months the rule traded?
# (1) frozen scaling: from 2021-10 on, z_t = (log1p(EMV_env_t) - m*) / s*, with m*, s* the mean and sd of the 60-month window
#     ending 2021-09 (the last pre-regime window); threshold rebuilt past-only on this z path (and, as a variant, the team's).
# (2) zeros as missing: zero months dropped before the rolling z (60 calendar months, or the last 60 nonzero months; at least
#     12 nonzero values), so a zero month has no z and cannot enter; threshold rebuilt past-only on this z path.
print("Q3 counterfactuals")
PRE_END = pd.Timestamp("2021-09-30")
w_pre = lz.loc[:PRE_END].iloc[-60:]
m_pre, s_pre = float(w_pre.mean()), float(w_pre.std(ddof=1))
z_frozen = z_env.copy()
z_frozen.loc[BREAK:] = (lz.loc[BREAK:] - m_pre) / s_pre
lz_nz = lz.where(emv_env > 0)
z_miss_cal = (lz_nz - lz_nz.rolling(60, min_periods=12).mean()) / lz_nz.rolling(60, min_periods=12).std(ddof=1)
_ln = lz_nz.dropna()
z_miss_obs = ((_ln - _ln.rolling(60, min_periods=12).mean()) / _ln.rolling(60, min_periods=12).std(ddof=1)).reindex(lz.index)
CF = {}
for name, zz_ in (("team", z_env), ("frozen_2021-09_scaling", z_frozen), ("zeros_missing_60m_calendar", z_miss_cal),
                  ("zeros_missing_last60_nonzero", z_miss_obs)):
    st_, th_ = expanding_tail(zz_, 0.80, 60)
    cr_, _, h6_ = cross_and_holds(st_)
    CF[name] = dict(z=zz_, thr=th_, state=st_, cross=cr_, h6=h6_)
st_ = (z_frozen > thr) & thr.notna()
cr_, _, h6_ = cross_and_holds(st_)
CF["frozen_2021-09_scaling_team_threshold"] = dict(z=z_frozen, thr=thr, state=st_, cross=cr_, h6=h6_)
assert CF["team"]["state"].equals(state) and CF["team"]["cross"].equals(cross)
CFW = {"validation_tail": (BREAK, pd.Timestamp(PERIODS["validation"][1])), "holdout": tuple(pd.Timestamp(x) for x in PERIODS["holdout"]),
       "post_2021-10": (BREAK, LAST_EMV), "validation": tuple(pd.Timestamp(x) for x in PERIODS["validation"])}
rows = []
for name, v in CF.items():
    for w, (a, b) in CFW.items():
        st_, cr_ = v["state"].loc[a:b], v["cross"].loc[a:b]
        rows.append(dict(variant=name, window=w, start=ym(st_.index[0]), end=ym(st_.index[-1]), n_months=len(st_),
                         n_state=int(st_.sum()), n_crossings=int(cr_.sum()), crossing_months=" ".join(ym(t) for t in cr_[cr_].index),
                         n_state_months_differ_from_team=int((st_ != state.loc[a:b]).sum()),
                         n_crossing_months_differ_from_team=int((cr_ != cross.loc[a:b]).sum()),
                         share_months_in_hold6=v["h6"].loc[a:b].mean()))
cfs = pd.DataFrame(rows)
save_table(cfs, "zero_counterfactual_summary",
           tex=dict(caption="Counterfactual versions of the team rule after 2021-10 (validation tail 2021-10 to 2022-07 and holdout; "
                            "the CSV adds the full validation window). frozen: window mean and sd fixed at the 60 months "
                            "to 2021-09; zeros missing: zero months dropped before the rolling z-score. Differ = months whose "
                            "state or crossing flag differs from the team rule.", label="tab:m1_zero_cf",
                    columns=["variant", "window", "start", "end", "n_state", "n_crossings", "crossing_months",
                             "n_state_months_differ_from_team", "n_crossing_months_differ_from_team"],
                    fmt={"n_state": "{:d}", "n_crossings": "{:d}", "n_state_months_differ_from_team": "{:d}",
                         "n_crossing_months_differ_from_team": "{:d}"},
                    rename={"n_state": "state", "n_crossings": "crossings", "crossing_months": "crossing months",
                            "n_state_months_differ_from_team": "state differs", "n_crossing_months_differ_from_team": "crossing differs"},
                    rows=lambda t: t["window"].isin(["validation_tail", "holdout"])))
for _, r in cfs.iterrows():
    for c in ("n_state", "n_crossings", "crossing_months", "n_state_months_differ_from_team", "n_crossing_months_differ_from_team",
              "share_months_in_hold6"):
        key(f"cf_{r.variant}_{r.window}_{c}", r[c], "zero_counterfactual_summary")
key("cf_frozen_window_mean_log1p", m_pre, "zero_counterfactual_months"); key("cf_frozen_window_sd_log1p", s_pre, "zero_counterfactual_months")
# month by month from 2021-10: reading, the level needed to enter under each scaling, and each variant's flags
rows = []
thF = CF["frozen_2021-09_scaling"]["thr"]
for t in emv_env.loc[BREAK:LAST_EMV].index:
    past = lz.loc[:t].iloc[-60:-1].to_numpy()
    bar_t = min_level_to_cross(past, thr.loc[t]); bar_f = float(np.expm1(m_pre + thF.loc[t] * s_pre))
    row = dict(month=ym(t), period=("holdout" if pd.Timestamp(PERIODS["holdout"][0]) <= t <= pd.Timestamp(PERIODS["holdout"][1])
                                    else ("validation" if t <= pd.Timestamp(PERIODS["validation"][1]) else "after_returns")),
               EMV_env=emv_env.loc[t], zero=bool(zero.loc[t]), prev_month_zero=bool(prev_zero.loc[t]),
               bar_team=bar_t, bar_frozen=bar_f,
               reading_between_bars=bool(emv_env.loc[t] > min(bar_t, bar_f) and emv_env.loc[t] <= max(bar_t, bar_f)))
    for name, lab in (("team", "team"), ("frozen_2021-09_scaling", "frozen"), ("zeros_missing_60m_calendar", "zeros_missing_cal"),
                      ("zeros_missing_last60_nonzero", "zeros_missing_obs")):
        row[f"z_{lab}"] = CF[name]["z"].loc[t]; row[f"threshold_{lab}"] = CF[name]["thr"].loc[t]
        row[f"state_{lab}"] = bool(CF[name]["state"].loc[t]); row[f"crossing_{lab}"] = bool(CF[name]["cross"].loc[t])
    rows.append(row)
cfm = pd.DataFrame(rows)
save_table(cfm, "zero_counterfactual_months")
hnz = cfm[(cfm.period == "holdout") & ~cfm.zero]
save_table(hnz[["month", "EMV_env", "prev_month_zero", "bar_team", "bar_frozen", "z_team", "state_team", "crossing_team",
                "crossing_frozen", "crossing_zeros_missing_cal", "crossing_zeros_missing_obs"]],
           "zero_counterfactual_holdout_nonzero",
           tex=dict(caption="Holdout months with a nonzero EMV\\_env reading. bar = smallest EMV\\_env that puts the month above the "
                            "threshold, under the team's rolling window (team) or with the window frozen at the 60 months to 2021-09 "
                            "(frozen). Crossing flags for the team rule and the three counterfactuals.", label="tab:m1_holdout_nonzero",
                    fmt={"EMV_env": "{:.2f}", "bar_team": "{:.2f}", "bar_frozen": "{:.2f}", "z_team": "{:.2f}"},
                    rename={"prev_month_zero": "prev zero", "bar_team": "bar (team)", "bar_frozen": "bar (frozen)", "z_team": "z",
                            "state_team": "state", "crossing_team": "entry (team)", "crossing_frozen": "entry (frozen)",
                            "crossing_zeros_missing_cal": "entry (zeros missing, 60m)", "crossing_zeros_missing_obs": "entry (zeros missing, 60 obs)"}))
entries = hnz[hnz.crossing_team]; cand = hnz[hnz.prev_month_zero]
key("cf_holdout_entry_readings_min", entries.EMV_env.min(), "zero_counterfactual_holdout_nonzero")
key("cf_holdout_entry_readings_max", entries.EMV_env.max(), "zero_counterfactual_holdout_nonzero")
key("cf_holdout_nonzero_after_zero", len(cand), "zero_counterfactual_holdout_nonzero")
key("cf_holdout_nonzero_after_zero_no_entry", int((~cand.crossing_team).sum()), "zero_counterfactual_holdout_nonzero")
key("cf_holdout_nonzero_after_zero_no_entry_min", cand[~cand.crossing_team].EMV_env.min(), "zero_counterfactual_holdout_nonzero")
key("cf_holdout_nonzero_after_zero_no_entry_max", cand[~cand.crossing_team].EMV_env.max(), "zero_counterfactual_holdout_nonzero")
key("cf_holdout_readings_between_bars", int(hnz.reading_between_bars.sum()), "zero_counterfactual_holdout_nonzero")
key("cf_holdout_bar_team_min", hnz.bar_team.min(), "zero_counterfactual_holdout_nonzero")
key("cf_holdout_bar_team_max", hnz.bar_team.max(), "zero_counterfactual_holdout_nonzero")
key("cf_holdout_bar_frozen_min", hnz.bar_frozen.min(), "zero_counterfactual_holdout_nonzero")
key("cf_holdout_bar_frozen_max", hnz.bar_frozen.max(), "zero_counterfactual_holdout_nonzero")
# is "entries follow a zero month" more than the base rate? Among holdout nonzero months: state vs previous month zero
a_, b_ = int((hnz.state_team & hnz.prev_month_zero).sum()), int((~hnz.state_team & hnz.prev_month_zero).sum())
c_, d_ = int((hnz.state_team & ~hnz.prev_month_zero).sum()), int((~hnz.state_team & ~hnz.prev_month_zero).sum())
o3, p3 = fisher_2x2(a_, b_, c_, d_)
L.add("Q3_fisher_state_prevzero_holdout_nonzero", "Q3 zero inflation",
      "Fisher exact odds ratio (state | previous month zero vs previous month nonzero), holdout nonzero months", o3, p3, len(hnz),
      "exploratory", f"state after zero {a_}/{a_ + b_}; state after nonzero {c_}/{c_ + d_}")
base = (a_ + b_) / len(hnz)
n_entries, n_entries_pz = len(entries), int(entries.prev_month_zero.sum())
bt = stats.binomtest(n_entries_pz, n_entries, base, alternative="two-sided")
p_one = float(stats.binom.sf(n_entries_pz - 1, n_entries, base))
L.add("Q3_binom_entries_after_zero_holdout", "Q3 zero inflation",
      "share of holdout entries that follow a zero month vs base rate among holdout nonzero months (binomial)",
      n_entries_pz / n_entries, bt.pvalue, n_entries, "exploratory",
      f"{n_entries_pz}/{n_entries} entries vs base rate {a_ + b_}/{len(hnz)} = {base:.3f}; one-sided P(>= {n_entries_pz}) = {p_one:.3f}")
bz = pd.DataFrame([dict(window="holdout nonzero months", n_nonzero=len(hnz), n_nonzero_prev_zero=a_ + b_,
                        n_nonzero_prev_nonzero=c_ + d_, base_rate=base, n_state_prev_zero=a_, n_state_prev_nonzero=c_,
                        fisher_odds_ratio=o3, fisher_p=p3, n_entries=n_entries, n_entries_prev_zero=n_entries_pz,
                        binom_p_one_sided=p_one, binom_p_two_sided=bt.pvalue)])
save_table(bz, "zero_entry_base_rate")
for c in bz.columns[1:]:
    key(f"baserate_{c}", bz.loc[0, c], "zero_entry_base_rate")

# ============================================================================= Q4 crossings
print("Q4 crossings")
vix_med = vix.shift(1).expanding(min_periods=36).median()
emv_med = emv_all.shift(1).expanding(min_periods=36).median()
cm = pd.DataFrame({"EMV_env": emv_env, "z": z_env, "threshold": thr, "state": state, "crossing": cross, "prev_month_zero": prev_zero,
                   "VIX": vix, "VIX_past_median": vix_med, "EMV_overall": emv_all, "EMV_overall_past_median": emv_med})
cm = cm[cm.threshold.notna()]
cm["high_VIX"] = (cm.VIX > cm.VIX_past_median).where(cm.VIX_past_median.notna())
cm["high_EMV_overall"] = (cm.EMV_overall > cm.EMV_overall_past_median).where(cm.EMV_overall_past_median.notna())


def period_of(t):
    if t < pd.Timestamp("2010-01-31"): return "pre2010"
    if t <= pd.Timestamp("2022-07-31"): return "validation"
    if t <= pd.Timestamp("2026-07-31"): return "holdout"
    return "after_returns"


cm["period"] = [period_of(t) for t in cm.index]
ctab = cm[cm.crossing].copy()
ctab.insert(0, "month", [ym(t) for t in ctab.index])
ctab = ctab.drop(columns=["state", "crossing"])
save_table(ctab, "crossings")
ctex = ctab[ctab.period != "pre2010"][["month", "period", "EMV_env", "z", "threshold", "prev_month_zero", "VIX", "VIX_past_median", "high_VIX", "EMV_overall", "high_EMV_overall"]]
save_table(ctex, "crossings_post2010",
           tex=dict(caption="Team extreme-attention crossing months since 2010 (z above the expanding past-only 80th percentile after "
                            "being below it). high\\_VIX: monthly average VIX above its expanding past-only median.",
                    label="tab:m1_crossings", fmt={"EMV_env": "{:.2f}", "z": "{:.2f}", "threshold": "{:.2f}", "VIX": "{:.1f}",
                                                   "VIX_past_median": "{:.1f}", "EMV_overall": "{:.1f}"}))
CW = {"all_threshold_sample": (None, None), "since_2010": ("2010-01-31", "2026-07-31"), "pre2010": (None, "2009-12-31"),
      "validation": PERIODS["validation"], "holdout": PERIODS["holdout"]}
rows = []
for flag in ("high_VIX", "high_EMV_overall"):
    for which in ("crossing", "state"):
        for k, (a, b) in CW.items():
            s = cm.loc[a:b]; s = s[s[flag].notna()]
            ev, non = s[s[which]], s[~s[which]]
            if len(ev) == 0:
                continue
            o, p = fisher_2x2(int(ev[flag].sum()), int((~ev[flag].astype(bool)).sum()), int(non[flag].sum()), int((~non[flag].astype(bool)).sum()))
            # dependence-robust versions: Fisher treats persistent monthly flags as independent draws
            d_share, p_circ, n_sh = circular_shift_p(s[flag].astype(bool), s[which].astype(bool), min_shift=12)
            lpm = nw_ols(s[flag].astype(float), s[which].astype(float).to_frame("event"), lags=12)
            rows.append(dict(flag=flag, event=which, window=k, start=ym(s.index[0]), end=ym(s.index[-1]), n_months=len(s), n_events=len(ev),
                             n_events_flag=int(ev[flag].sum()), frac_events_flag=ev[flag].mean(), n_other=len(non),
                             frac_other_flag=non[flag].mean(), fisher_odds_ratio=o, fisher_p=p, diff_share=d_share,
                             p_circular_shift=p_circ, n_shifts=n_sh, lpm_slope=float(lpm.params["event"]),
                             t_lpm_nw12=float(lpm.tvalues["event"]), p_lpm_nw12=float(lpm.pvalues["event"])))
            kind = "primary" if (flag == "high_VIX" and which == "crossing" and k == "all_threshold_sample") else \
                   ("robustness" if k == "all_threshold_sample" else "exploratory")
            L.add(f"Q4_{flag}_{which}_{k}", "Q4 crossings vs volatility", f"Fisher exact odds ratio ({flag} share, {which} months vs other months)",
                  o, p, len(s), kind, f"{len(ev)} events, {ym(s.index[0])}..{ym(s.index[-1])}; flag vs expanding past-only median")
            rkind = "robustness" if kind in ("primary", "robustness") else "exploratory"
            L.add(f"Q4_{flag}_{which}_{k}_circshift", "Q4 crossings vs volatility",
                  f"difference in {flag} share ({which} minus other months), circular-shift permutation p", d_share, p_circ, len(s), rkind,
                  f"{n_sh} rotations of the {which} indicator by 12..n-12 months; p resolution 1/{n_sh}")
            L.add(f"Q4_{flag}_{which}_{k}_lpm_nw12", "Q4 crossings vs volatility",
                  f"linear probability slope of {flag} on {which} indicator, NW(12) t", float(lpm.params["event"]),
                  float(lpm.pvalues["event"]), len(s), rkind, f"{ym(s.index[0])}..{ym(s.index[-1])}")
csum = pd.DataFrame(rows)
save_table(csum, "crossings_vix_summary",
           tex=dict(caption="Share of extreme-attention months that are high-volatility months, versus all other months in the same "
                            "window. p-values: Fisher exact (treats months as independent), circular-shift permutation of the event "
                            "indicator, and a linear probability model with NW(12) errors.", label="tab:m1_cross_vix",
                    columns=["flag", "event", "window", "start", "end", "n_events", "frac_events_flag", "frac_other_flag", "fisher_p",
                             "p_circular_shift", "p_lpm_nw12"],
                    fmt={"frac_events_flag": "{:.2f}", "frac_other_flag": "{:.2f}", "fisher_p": "{:.3f}", "p_circular_shift": "{:.3f}",
                         "p_lpm_nw12": "{:.3f}", "n_events": "{:d}"},
                    rename={"frac_events_flag": "share events", "frac_other_flag": "share other", "fisher_p": "p Fisher",
                            "p_circular_shift": "p shift", "p_lpm_nw12": "p LPM"}))
for _, r in csum.iterrows():
    for c in ("n_events", "n_events_flag", "frac_events_flag", "frac_other_flag", "fisher_p", "fisher_odds_ratio", "p_circular_shift",
              "n_shifts", "p_lpm_nw12", "t_lpm_nw12", "n_months"):
        key(f"cross_{r.flag}_{r.event}_{r.window}_{c}", r[c], "crossings_vix_summary")
key("cross_n_holdout", int(ctab[ctab.period == "holdout"].shape[0]), "crossings")
key("cross_n_holdout_prev_zero", int(ctab[(ctab.period == "holdout") & ctab.prev_month_zero].shape[0]), "crossings")
key("cross_n_validation", int(ctab[ctab.period == "validation"].shape[0]), "crossings")
key("cross_threshold_first_month", ym(cm.index[0]), "crossings")

# ============================================================================= Q5 measures and correlations
print("Q5 measures")
TRANS = {"level": LEVELS, "z": Z, "shock": SH}
COMMON = (max(SH[k].first_valid_index() for k in MEASURES), min(SH[k].last_valid_index() for k in MEASURES))
NAME = {"level": lambda k: k, "z": lambda k: f"z_{k}", "shock": lambda k: f"shock_{k}"}   # same names as the Q2 table
rows = []


def q5_row(m, tr, ref, samp, c, tid, p_led, kind):
    return dict(measure=m, transform=tr, reference=ref, sample=samp, start=ym(c["start"]), end=ym(c["end"]), n=c["n"],
                pearson=c["pearson"], t_hac=c["t_hac"], p_hac=c["p_hac"], t_slope=c["t_slope"], p_slope=c["p_slope"],
                spearman=c["spearman"], ledger_test_id=tid, ledger_p=p_led, ledger_kind=kind)


for m in MEASURES:
    for tr, dct in TRANS.items():
        for ref in ("EMV_env", "VIX"):
            if m == ref:
                continue
            for samp, (a, b) in {"overlap": (None, None), "common": COMMON}.items():
                c = corr_test(dct[ref], dct[m], start=a, end=b)
                prim = (m in ("MCCC", "CPU") and tr == "z" and ref == "EMV_env" and samp == "overlap")
                # the two pre-specified primaries keep their pre-specified test (NW(6) slope of the standardized measure on the
                # standardized EMV_env z); every other correlation uses the direction-free HAC test and is recorded once
                p_led = c["p_slope"] if prim else c["p_hac"]
                kind = "primary" if prim else "exploratory"
                tid = L.add(f"Q5_corr_{m}_{tr}_{ref}_{samp}", "Q5 climate measures vs EMV_env and VIX",
                            f"Pearson r ({tr}) {m} vs {ref}" + (" (pre-specified NW(6) slope test, measure on EMV_env)" if prim
                                                                else " (direction-free HAC(6) test)"),
                            c["pearson"], p_led, c["n"], kind, f"{ym(c['start'])}..{ym(c['end'])}",
                            key=corr_key(NAME[tr](m), NAME[tr](ref), c["start"], c["end"]))
                rows.append(q5_row(m, tr, ref, samp, c, tid, p_led, kind))
    for ref_name, ref in (("RATE", rate), ("Mkt-RF", ff3["Mkt-RF"])):     # shocks vs contemporaneous rate factor and market
        c = corr_test(ref, SH[m])
        tid = L.add(f"Q5_corr_{m}_shock_{ref_name}", "Q5 climate measures vs rates", f"Pearson r shock {m} vs {ref_name} (direction-free HAC(6) test)",
                    c["pearson"], c["p_hac"], c["n"], "exploratory", f"{ym(c['start'])}..{ym(c['end'])}",
                    key=corr_key(f"shock_{m}", ref_name, c["start"], c["end"]))
        rows.append(q5_row(m, "shock", ref_name, "overlap", c, tid, c["p_hac"], "exploratory"))
# the topic-share component against the climate-concern measures (headline numbers; robustness of the Q5 primary)
for m in ("MCCC", "CPU", "MCCC_transition"):
    for samp, (a, b) in {"overlap": (None, None), "common": COMMON}.items():
        c = corr_test(Z["EMV_env_share"], Z[m], start=a, end=b)
        tid = L.add(f"Q5_corr_{m}_z_EMV_env_share_{samp}", "Q5 climate measures vs the EMV_env topic share",
                    f"Pearson r (z) {m} vs EMV_env_share (direction-free HAC(6) test)", c["pearson"], c["p_hac"], c["n"], "robustness",
                    f"{ym(c['start'])}..{ym(c['end'])}", key=corr_key(f"z_{m}", "z_EMV_env_share", c["start"], c["end"]))
        rows.append(q5_row(m, "z", "EMV_env_share", samp, c, tid, c["p_hac"], "robustness"))
mcorr = pd.DataFrame(rows)
pm5 = mcorr["measure"].isin(["MCCC", "CPU"]) & (mcorr["transform"] == "z") & (mcorr["reference"] == "EMV_env") & (mcorr["sample"] == "overlap")
assert pm5.sum() == 2
mcorr["holm_p_primary"] = np.nan
mcorr.loc[pm5, "holm_p_primary"] = holm(mcorr.loc[pm5, "p_slope"]).values
save_table(mcorr, "measure_correlations")
# robustness of the two Q5 primaries: test direction, HAC bandwidth, direction-free test, and the overall-EMV channel
rows = []
for m in ("MCCC", "CPU"):
    d5 = pd.concat([Z[m].rename(m), z_env.rename("z_EMV_env")], axis=1, sort=True).dropna()
    c6, c24, rev = corr_test(d5["z_EMV_env"], d5[m]), corr_test(d5["z_EMV_env"], d5[m], lags=24), corr_test(d5[m], d5["z_EMV_env"])
    pc = partial_corr_test(d5[m], d5["z_EMV_env"], Z["EMV_overall"])
    hp = float(mcorr.loc[pm5 & (mcorr.measure == m), "holm_p_primary"].iloc[0])
    rows.append(dict(measure=m, start=ym(c6["start"]), end=ym(c6["end"]), n=c6["n"], pearson=c6["pearson"],
                     t_primary=c6["t_slope"], p_primary=c6["p_slope"], holm_p_primary=hp,
                     p_reverse_direction=rev["p_slope"], p_slope_nw24=c24["p_slope"], p_hac_direction_free=c6["p_hac"],
                     p_hac_direction_free_nw24=c24["p_hac"], partial_r_given_z_EMV_overall=pc["partial_r"],
                     p_partial_hac=pc["p_hac"], n_partial=pc["n"]))
    for tag, stat_, p_, nm_ in (("reverse_direction", rev["pearson"], rev["p_slope"], "NW(6) slope of z_EMV_env on the measure"),
                                ("nw24", c24["pearson"], c24["p_slope"], "pre-specified slope test with NW(24)"),
                                ("hac_direction_free", c6["pearson"], c6["p_hac"], "direction-free delta-method HAC(6)"),
                                ("partial_given_z_EMV_overall", pc["partial_r"], pc["p_hac"], "partial r given z_EMV_overall, HAC(6)")):
        L.add(f"Q5_primary_{m}_{tag}", "Q5 climate measures vs EMV_env (primary robustness)", f"Pearson r (z) {m} vs EMV_env: {nm_}",
              stat_, p_, pc["n"] if tag.startswith("partial") else c6["n"], "robustness", f"{ym(c6['start'])}..{ym(c6['end'])}")
q5r = pd.DataFrame(rows)
save_table(q5r, "q5_primary_robustness",
           tex=dict(caption="Q5 primary correlations of climate-concern z-scores with the team signal: pre-specified NW(6) slope test, "
                            "Holm over the two tests, the reverse regression direction, NW(24), a direction-free HAC test, and the "
                            "partial correlation given the overall-EMV z-score.", label="tab:m1_q5",
                    columns=["measure", "start", "end", "n", "pearson", "p_primary", "holm_p_primary", "p_reverse_direction",
                             "p_slope_nw24", "p_hac_direction_free", "partial_r_given_z_EMV_overall", "p_partial_hac"],
                    fmt={"pearson": "{:.3f}", "p_primary": "{:.3f}", "holm_p_primary": "{:.3f}", "p_reverse_direction": "{:.3f}",
                         "p_slope_nw24": "{:.3f}", "p_hac_direction_free": "{:.3f}", "partial_r_given_z_EMV_overall": "{:.3f}",
                         "p_partial_hac": "{:.3f}", "n": "{:d}"},
                    rename={"pearson": "r", "p_primary": "p", "holm_p_primary": "Holm p", "p_reverse_direction": "p reverse",
                            "p_slope_nw24": "p NW(24)", "p_hac_direction_free": "p HAC", "partial_r_given_z_EMV_overall": "partial r",
                            "p_partial_hac": "p partial"}))
for _, r in q5r.iterrows():
    for c in q5r.columns[1:]:
        key(f"q5prim_{r.measure}_{c}", r[c], "q5_primary_robustness")
mc_tex = mcorr[(mcorr["sample"] == "overlap")].pivot_table(index="measure", columns=["transform", "reference"], values="pearson").reindex(MEASURES)
mc_tex.columns = [f"{t} vs {r}" for t, r in mc_tex.columns]
mc_tex = mc_tex[[c for c in ["level vs EMV_env", "z vs EMV_env", "shock vs EMV_env", "level vs VIX", "z vs VIX", "shock vs VIX",
                             "shock vs RATE", "z vs EMV_env_share"] if c in mc_tex.columns]]
save_table(mc_tex.reset_index(), "measure_correlations_wide",
           tex=dict(caption="Pearson correlations of each attention or concern measure with the team measure (EMV\\_env) and with VIX, "
                            "each on its own overlapping sample. z = rolling 60-month z-score of log1p(level); shock = real-time "
                            "expanding AR(1) innovation. RATE = $-\\Delta$GS10.", label="tab:m1_measure_corr",
                    fmt={c: "{:.2f}" for c in mc_tex.columns}))
for _, r in mcorr.iterrows():
    b_ = f"corr_{r['measure']}_{r['transform']}_vs_{r['reference']}_{r['sample']}"
    key(b_, r.pearson, "measure_correlations"); key(f"{b_}_p_hac", r.p_hac, "measure_correlations")
    key(f"{b_}_t_hac", r.t_hac, "measure_correlations"); key(f"{b_}_n", r.n, "measure_correlations")
# correlation matrices on the common sample
zmat = pd.DataFrame({k: Z[k] for k in MEASURES}).loc[COMMON[0]:COMMON[1]].corr()
smat = pd.DataFrame({k: SH[k] for k in MEASURES}).loc[COMMON[0]:COMMON[1]].corr()
save_table(zmat.reset_index().rename(columns={"index": "measure"}), "zsignal_corr_matrix_common")
save_table(smat.reset_index().rename(columns={"index": "measure"}), "shock_corr_matrix_common")
key("common_sample_start", ym(COMMON[0]), "zsignal_corr_matrix_common"); key("common_sample_end", ym(COMMON[1]), "zsignal_corr_matrix_common")

# ============================================================================= Q6a contemporaneous
print("Q6a contemporaneous")
SH6 = dict(SH)
SH6["MCCC_fullAR1"] = ar1_shock_full(mccc).rename("MCCC_fullAR1_shock")       # ex-post AR(1), 2003-02 on
SH6["CPU_fullAR1"] = ar1_shock_full(cpu).rename("CPU_fullAR1_shock")
A_ORDER = ["MCCC", "CPU", "MCCC_fullAR1", "MCCC_transition", "CPU_fullAR1", "EMV_env", "EMV_env_share", "EMV_overall", "VIX"]
A_KIND = {"MCCC": "primary", "CPU": "primary", "MCCC_fullAR1": "robustness", "MCCC_transition": "robustness",
          "CPU_fullAR1": "robustness"}
A_PER = {"full": (None, None), **{k: PERIODS[k] for k in ("post2010", "validation", "holdout", "covid", "inflation_rates", "last18", "last12")}}
SPECS = {"none": None, "FF3": ff3, "FF3_RATE": fac_rate}
rows = []
for sname in A_ORDER:
    shock = SH6[sname].dropna(); x = (shock / shock.std(ddof=1)).rename("shock_sd")
    for spec, ctrl in SPECS.items():
        for per, (a, b) in A_PER.items():
            if spec != "none" and per not in ("full", "post2010", "validation", "holdout"):
                continue
            X = x.to_frame() if ctrl is None else x.to_frame().join(ctrl, how="inner")
            r = reg_row(gb, X, start=a, end=b)
            if r.get("n", 0) < 12:
                continue
            rows.append(dict(shock=sname, outcome="green_minus_brown", spec=spec, period=per, start=ym(r["start"]), end=ym(r["end"]),
                             n=r["n"], slope_pct_per_sd=100 * r["b_shock_sd"], t_nw=r["t_shock_sd"], p_nw=r["p_shock_sd"], r2=r["r2"],
                             b_RATE=r.get("b_RATE", np.nan), t_RATE=r.get("t_RATE", np.nan)))
            kind = A_KIND.get(sname, "exploratory") if (spec == "none" and per == "full") else \
                   ("robustness" if sname in A_KIND else "exploratory")
            L.add(f"Q6a_{sname}_{spec}_{per}", "Q6a contemporaneous GB on concern shock",
                  f"slope of GB on 1-sd {sname} shock (%/month), NW t", 100 * r["b_shock_sd"], r["p_shock_sd"], r["n"], kind,
                  f"controls={spec}; {ym(r['start'])}..{ym(r['end'])}; PST predict positive",
                  key=("q6a", sname, "green_minus_brown", spec, ym(r["start"]), ym(r["end"])))
    for leg_name, leg in (("green_excess", green_x), ("brown_excess", brown_x)):
        if sname not in ("MCCC", "CPU"):
            continue
        r = reg_row(leg, x.to_frame())
        rows.append(dict(shock=sname, outcome=leg_name, spec="none", period="full", start=ym(r["start"]), end=ym(r["end"]), n=r["n"],
                         slope_pct_per_sd=100 * r["b_shock_sd"], t_nw=r["t_shock_sd"], p_nw=r["p_shock_sd"], r2=r["r2"]))
        L.add(f"Q6a_{sname}_leg_{leg_name}", "Q6a contemporaneous leg on concern shock", f"slope of {leg_name} on 1-sd {sname} shock (%/month)",
              100 * r["b_shock_sd"], r["p_shock_sd"], r["n"], "exploratory", f"{ym(r['start'])}..{ym(r['end'])}")
contemp = pd.DataFrame(rows)
prim = (contemp.spec == "none") & (contemp.period == "full") & contemp.shock.isin(["MCCC", "CPU"]) & (contemp.outcome == "green_minus_brown")
contemp["holm_p_primary"] = np.nan
contemp.loc[prim, "holm_p_primary"] = holm(contemp.loc[prim, "p_nw"]).values
save_table(contemp, "contemporaneous")
ct = contemp[(contemp.outcome == "green_minus_brown") & contemp.period.isin(["full", "validation", "holdout"]) &
             contemp.shock.isin(["MCCC", "CPU", "MCCC_fullAR1", "MCCC_transition", "EMV_env"])]
ct = ct.pivot_table(index=["shock", "spec"], columns="period", values=["slope_pct_per_sd", "t_nw", "n"]).reindex(
    pd.MultiIndex.from_product([["MCCC", "CPU", "MCCC_fullAR1", "MCCC_transition", "EMV_env"], ["none", "FF3", "FF3_RATE"]]))
ct.columns = [f"{v}_{p}" for v, p in ct.columns]
ct = ct[[f"{v}_{p}" for p in ("full", "validation", "holdout") for v in ("slope_pct_per_sd", "t_nw", "n")]].reset_index().rename(columns={"level_0": "shock", "level_1": "controls"})
save_table(ct, "contemporaneous_summary",
           tex=dict(caption="Contemporaneous regression of the Green-minus-Brown spread on a one-standard-deviation climate-concern "
                            "shock (percent per month). Pastor, Stambaugh and Taylor predict a positive slope. NW(6) t.",
                    label="tab:m1_contemp", fmt={**{c: "{:.2f}" for c in ct.columns if c.startswith("slope")},
                                                 **{c: "{:.1f}" for c in ct.columns if c.startswith("t_")},
                                                 **{c: "{:.0f}" for c in ct.columns if c.startswith("n_")}}))
for _, r in contemp.iterrows():
    if r.period not in ("full", "validation", "holdout", "covid", "post2010"):
        continue
    base = f"contemp_{r.shock}_{r.outcome}_{r.spec}_{r.period}"
    key(f"{base}_slope_pct", r.slope_pct_per_sd, "contemporaneous"); key(f"{base}_t", r.t_nw, "contemporaneous")
    key(f"{base}_p", r.p_nw, "contemporaneous"); key(f"{base}_n", r.n, "contemporaneous"); key(f"{base}_start", r.start, "contemporaneous")
    if not pd.isna(r.holm_p_primary):
        key(f"{base}_holm_p", r.holm_p_primary, "contemporaneous")

# ============================================================================= Q6b predictive IC
print("Q6b predictive")
brown_res = rolling_factor_resid(brown_x, ff3, 60).rename("brown_resid_FF3")
brown_res_rate = rolling_factor_resid(brown_x, fac_rate, 60).rename("brown_resid_FF3_RATE")
# replication check against the team notebook's printed IC table (raw attention, Brown-leg residual)
rep = []
for per, target in (("validation", -0.0915), ("holdout", 0.1234)):
    r = ic_test(z_env, brown_res, *PERIODS[per])
    rep.append(dict(period=per, ic_this_module=r["ic"], ic_team_notebook=target, n=r["n"], t_nw_this_module=r["t_nw"]))
    assert abs(r["ic"] - target) < 5e-4, (per, r["ic"])
r = ic_test(z_env, brown_res, "2010-01-31", "2026-07-31")
rep.append(dict(period="2010-01..2026-07", ic_this_module=r["ic"], ic_team_notebook=-0.0288, n=r["n"], t_nw_this_module=r["t_nw"]))
save_table(pd.DataFrame(rep), "ic_replication")

SIGNALS = {**{f"z_{k}": Z[k] for k in MEASURES}, **{f"shock_{k}": SH[k] for k in MEASURES}}
OUTCOMES = {"GB": (gb, None), "GB_ctrl_FF3": (gb, ff3), "GB_ctrl_FF3_RATE": (gb, fac_rate),
            "brown_resid_FF3": (brown_res, None), "brown_resid_FF3_RATE": (brown_res_rate, None)}
IC_PER = {"full_overlap": (None, None), "common": COMMON, "post2010": PERIODS["post2010"], "validation": PERIODS["validation"],
          "holdout": PERIODS["holdout"], "last18": PERIODS["last18"], "last12": PERIODS["last12"]}
PRIMARY_SIG = ["z_MCCC", "shock_MCCC", "z_CPU", "shock_CPU"]
rows = []
for sname, sig in SIGNALS.items():
    for oname, (out, ctrl) in OUTCOMES.items():
        for per, (a, b) in IC_PER.items():
            if oname not in ("GB", "brown_resid_FF3") and per not in ("full_overlap", "validation", "holdout"):
                continue
            r = ic_test(sig, out, a, b, controls=ctrl)
            if pd.isna(r["ic"]):
                rows.append(dict(signal=sname, outcome=oname, period=per, n=r["n"]))
                continue
            rows.append(dict(signal=sname, outcome=oname, period=per, start=ym(r["start"]), end=ym(r["end"]), n=r["n"],
                             ic=r["ic"], t_nw=r["t_nw"], p_nw=r["p_nw"]))
            is_prim = sname in PRIMARY_SIG and oname in ("GB", "brown_resid_FF3") and per == "full_overlap"
            if is_prim:
                kind = "primary"
            elif sname in PRIMARY_SIG or sname in ("z_MCCC_transition", "shock_MCCC_transition"):
                kind = "robustness"
            else:
                kind = "exploratory"
            tid = L.add(f"Q6b_{sname}_{oname}_{per}", "Q6b predictive IC", f"IC: slope of z(outcome t+1) on z(signal t), {oname}",
                        r["ic"], r["p_nw"], r["n"], kind,
                        f"{ym(r['start'])}..{ym(r['end'])} (signal dates); team hypothesis sign: {'+' if oname.startswith('GB') else '-'}",
                        key=("ic", sname, oname, ym(r["start"]), ym(r["end"])))
            rows[-1]["ledger_test_id"] = tid
# robustness: one extra month of publication lag (signal dated t-1 paired with the month t+1 outcome)
for sname in PRIMARY_SIG:
    for oname in ("GB", "brown_resid_FF3"):
        out = OUTCOMES[oname][0]
        r = ic_test(SIGNALS[sname].shift(1), out)
        rows.append(dict(signal=f"{sname}_lag1", outcome=oname, period="full_overlap", start=ym(r["start"]), end=ym(r["end"]),
                         n=r["n"], ic=r["ic"], t_nw=r["t_nw"], p_nw=r["p_nw"]))
        rows[-1]["ledger_test_id"] = L.add(f"Q6b_{sname}_lag1_{oname}_full_overlap", "Q6b predictive IC",
                                           f"IC with one extra month of publication lag, {oname}", r["ic"], r["p_nw"], r["n"], "robustness",
                                           f"signal t-1 vs outcome t+1; {ym(r['start'])}..{ym(r['end'])} (signal t dates)",
                                           key=("ic", f"{sname}_lag1", oname, ym(r["start"]), ym(r["end"])))
ics = pd.DataFrame(rows)
pm = ics.signal.isin(PRIMARY_SIG) & ics.outcome.isin(["GB", "brown_resid_FF3"]) & (ics.period == "full_overlap")
ics["holm_p_primary"] = np.nan
ics.loc[pm, "holm_p_primary"] = holm(ics.loc[pm, "p_nw"]).values
save_table(ics, "predictive_ic")
# report table: IC and t by period for GB and Brown residual
it = ics[ics.outcome.isin(["GB", "brown_resid_FF3"]) & ics.period.isin(["full_overlap", "validation", "holdout"])]
it = it.pivot_table(index=["outcome", "signal"], columns="period", values=["ic", "t_nw"])
it.columns = [f"{v}_{p}" for v, p in it.columns]
order = [f"z_{k}" for k in MEASURES] + [f"shock_{k}" for k in MEASURES]
it = it.reindex(pd.MultiIndex.from_product([["GB", "brown_resid_FF3"], order]))
it = it[[f"{v}_{p}" for p in ("full_overlap", "validation", "holdout") for v in ("ic", "t_nw")]].reset_index().rename(columns={"level_0": "outcome", "level_1": "signal"})
starts = ics[ics.period == "full_overlap"].set_index(["outcome", "signal"])["start"]
it.insert(2, "full_start", [starts.get((o, s), "") for o, s in zip(it.outcome, it.signal)])
save_table(it, "predictive_ic_summary",
           tex=dict(caption="Predictive information coefficients: slope of the standardized next-month outcome on the standardized "
                            "signal (NW(6) t). GB = Green-minus-Brown; brown\\_resid\\_FF3 = Brown-leg residual from the team's lagged "
                            "rolling FF3 hedge. The team hypothesis implies IC $>0$ for GB and IC $<0$ for the Brown residual.",
                    label="tab:m1_ic", fmt={**{c: "{:.2f}" for c in it.columns if c.startswith("ic_")},
                                            **{c: "{:.1f}" for c in it.columns if c.startswith("t_")}}))
for _, r in ics.iterrows():
    if pd.isna(r.get("ic")) or r.outcome not in ("GB", "brown_resid_FF3", "brown_resid_FF3_RATE", "GB_ctrl_FF3_RATE") or \
            r.period not in ("full_overlap", "validation", "holdout", "common"):
        continue
    base = f"ic_{r.signal}_{r.outcome}_{r.period}"
    key(f"{base}", r.ic, "predictive_ic"); key(f"{base}_t", r.t_nw, "predictive_ic"); key(f"{base}_p", r.p_nw, "predictive_ic")
    key(f"{base}_n", r.n, "predictive_ic"); key(f"{base}_start", r.start, "predictive_ic"); key(f"{base}_end", r.end, "predictive_ic")
    if not pd.isna(r.holm_p_primary):
        key(f"{base}_holm_p", r.holm_p_primary, "predictive_ic")
# sign-flip count (validation vs holdout) for GB and Brown residual, no controls
fl = ics[ics.outcome.isin(["GB", "brown_resid_FF3"]) & ics.period.isin(["validation", "holdout"])].pivot_table(
    index=["outcome", "signal"], columns="period", values="ic")
fl["sign_flip"] = np.sign(fl["validation"]) != np.sign(fl["holdout"])
fl = fl.reset_index()
save_table(fl, "ic_sign_stability")
for o in ("GB", "brown_resid_FF3"):
    s = fl[fl.outcome == o]
    key(f"ic_sign_flips_{o}", f"{int(s.sign_flip.sum())}/{len(s)}", "ic_sign_stability")

# ============================================================================= Q7 derived series
print("Q7 derived")
der = pd.DataFrame({**{k: LEVELS[k] for k in MEASURES}, **{f"{k}_shock": SH[k] for k in MEASURES},
                    **{f"z_{k}": Z[k] for k in MEASURES}})
der.index.name = "date"
der = der.loc["1985-01-31":LAST_EMV]
der.to_csv(DERIVED / "attention_measures.csv", float_format="%.8g")
key("derived_rows", len(der), "identity", "rows written to data/derived/attention_measures.csv")

# ============================================================================= figures
print("figures")
YL = mdates.YearLocator(5); YF = mdates.DateFormatter("%Y")


def shade_holdout(ax):
    ax.axvspan(pd.Timestamp(PERIODS["holdout"][0]), pd.Timestamp(PERIODS["holdout"][1]), color=NEUTRAL_MID, zorder=0, lw=0)


# F1: EMV_env vs VIX, stacked panels
fig, ax = plt.subplots(2, 1, figsize=(7.5, 5.2), sharex=True)
shade_holdout(ax[0]); shade_holdout(ax[1])
ax[0].plot(emv_env.index, emv_env.values, color=ENTITY["emv"], lw=1.1, label="EMV: energy and environmental regulation")
zm = emv_env[emv_env == 0]
ax[0].plot(zm.index, np.zeros(len(zm)), "|", color=INK, ms=7, mew=1.0, label=f"exact zero ({len(zm)} months)")
ax[0].set_ylabel("EMV_env (index)"); ax[0].set_title("Team 'attention' = FRED EMVENRGYENVREG")
ax[0].legend(loc="upper left")
ax[1].plot(vix.index, vix.values, color=INK2, lw=1.1, label="VIX, monthly average")
ax[1].set_ylabel("VIX"); ax[1].set_title("Monthly average VIX (shaded: team holdout 2022-08 to 2026-07)")
ax[1].xaxis.set_major_locator(YL); ax[1].xaxis.set_major_formatter(YF)
ax[1].set_xlim(pd.Timestamp("1985-01-01"), pd.Timestamp("2026-10-01"))
savefig(fig, f"{MODULE}_emv_vs_vix")

# F2: rolling zero share
fig, ax = plt.subplots(figsize=(7.5, 3.0))
shade_holdout(ax)
ax.plot(zshare24.index, 100 * zshare24.values, color=ENTITY["emv"], lw=1.5)
ax.axvline(BREAK, color=INK2, lw=0.8, ls="--")
ax.annotate("2021-10: zeros begin to dominate", xy=(BREAK, 50), xytext=(pd.Timestamp("2004-01-31"), 55), color=INK2, fontsize=8,
            arrowprops=dict(arrowstyle="-", color=INK2, lw=0.6))
ax.set_ylabel("Months with EMV_env = 0 (%)"); ax.set_ylim(0, 100)
ax.set_title("Share of exact-zero months in EMV_env, trailing 24 months")
ax.xaxis.set_major_locator(YL); ax.xaxis.set_major_formatter(YF)
ax.set_xlim(pd.Timestamp("1986-01-01"), pd.Timestamp("2026-10-01"))
savefig(fig, f"{MODULE}_zero_share")

# F3: standardized comparison on the common window of the three levels
a0, a1 = mccc.index[0], min(mccc.index[-1], cpu.index[-1], emv_env.index[-1])
STD12 = {}
fig, ax = plt.subplots(figsize=(7.5, 3.4))
for k, col, lab in (("EMV_env", ENTITY["emv"], "Team “attention” (FRED EMVENRGYENVREG)"), ("MCCC", ENTITY["mccc"], "MCCC aggregate (Ardia et al.)"),
                    ("CPU", ENTITY["cpu"], "Climate policy uncertainty (Gavriilidis)")):
    x = np.log1p(LEVELS[k].loc[a0:a1]); zx = (x - x.mean()) / x.std(ddof=1)
    sm12 = zx.rolling(12).mean()
    STD12[k] = sm12
    ax.plot(sm12.index, sm12.values, color=col, lw=1.6, label=lab)
# EMV_env with the exact zeros removed: standardized on the nonzero months of the same window; 12-month mean of the nonzero
# months in the window, shown when at least 3 of the 12 months are nonzero (the 6-month minimum is kept in the table)
x_e = np.log1p(emv_env.loc[a0:a1]); x_nz = x_e.where(emv_env.loc[a0:a1] > 0)
z_nz = (x_nz - x_nz.mean()) / x_nz.std(ddof=1)
STD12["EMV_env_nonzero_min3"] = z_nz.rolling(12, min_periods=3).mean()
STD12["EMV_env_nonzero_min6"] = z_nz.rolling(12, min_periods=6).mean()
STD12["EMV_env_n_nonzero_12m"] = x_nz.notna().astype(float).rolling(12).sum()
ax.plot(STD12["EMV_env_nonzero_min3"].index, STD12["EMV_env_nonzero_min3"].values, color=ENTITY["emv"], lw=1.2, ls="--",
        label="Team “attention”, exact zeros dropped")
ax.axhline(0, color=MUTED, lw=0.7)
ax.set_ylabel("Standard deviations")
ax.legend(loc="upper left", fontsize=7.5)
ax.xaxis.set_major_locator(mdates.YearLocator(2)); ax.xaxis.set_major_formatter(YF)
savefig(fig, f"{MODULE}_standardized_measures")
std12 = pd.DataFrame(STD12).dropna(how="all").rename_axis("date")
save_table(std12.reset_index(), "standardized_measures_12m")
for k in [c for c in STD12 if c != "EMV_env_n_nonzero_12m"]:
    key(f"std12_{k}_max", std12[k].max(), "standardized_measures_12m"); key(f"std12_{k}_argmax", ym(std12[k].idxmax()), "standardized_measures_12m")
    key(f"std12_{k}_min_2022_2024", std12[k].loc["2022":"2024"].min(), "standardized_measures_12m")
    key(f"std12_{k}_max_2022_2024", std12[k].loc["2022":"2024"].max(), "standardized_measures_12m")
    key(f"std12_{k}_n_2022_2024", int(std12[k].loc["2022":"2024"].notna().sum()), "standardized_measures_12m")
# typical size of a nonzero EMV_env reading by window (is the low 2022-2024 level low attention, or zeros?)
NZW = {"pre_2021-10": ("1985-01-31", "2021-09-30"), "window_60m_to_2021-09": ("2016-10-31", "2021-09-30"),
       "2003-01_to_2021-09": ("2003-01-31", "2021-09-30"), "2022-2024": ("2022-01-31", "2024-12-31"),
       "holdout": PERIODS["holdout"], "post_2021-10": ("2021-10-31", "2026-08-31")}
rows = []
for k, (a, b) in NZW.items():
    s_ = emv_env.loc[a:b]; nz_ = s_[s_ > 0]
    zin = z_nz.loc[a:b].dropna()
    rows.append(dict(window=k, start=ym(s_.index[0]), end=ym(s_.index[-1]), n_months=len(s_), n_nonzero=len(nz_),
                     median_nonzero=nz_.median(), mean_nonzero=nz_.mean(), mean_all_months=s_.mean(),
                     mean_std_nonzero_fig_scale=zin.mean() if len(zin) else np.nan, n_std_nonzero_fig_scale=len(zin)))
nzl = pd.DataFrame(rows)
save_table(nzl, "emv_nonzero_levels")
for _, r in nzl.iterrows():
    for c in nzl.columns[3:]:
        key(f"nonzero_{r.window}_{c}", r[c], "emv_nonzero_levels")

# F4: mechanics of the rule around the zero regime
w0 = pd.Timestamp("2017-01-31")
fig, ax = plt.subplots(3, 1, figsize=(7.5, 7.2), sharex=True)
for a_ in ax:
    shade_holdout(a_)
e_ = emv_env.loc[w0:]
ax[0].bar(e_.index, e_.values, width=20, color=ENTITY["emv"], label="EMV_env")
zm = e_[e_ == 0]
ax[0].plot(zm.index, np.zeros(len(zm)), "|", color=INK, ms=7, mew=1.0, label="exact zero")
ax[0].set_ylabel("EMV_env"); ax[0].set_title("Input: EMV_env by month"); ax[0].legend(loc="upper left")
n_h_cf = int(cfs.set_index(["variant", "window"]).loc[("frozen_2021-09_scaling", "holdout"), "n_crossing_months_differ_from_team"])
for axx, (v, ttl) in zip(ax[1:], ((CF["team"], "Team rule: rolling 60-month z and threshold (shaded: holdout)"),
                                   (CF["frozen_2021-09_scaling"], f"Window frozen at the 60 months to 2021-09: "
                                                                  f"{n_h_cf} holdout entry months differ"))):
    zz_, tt_, cc_ = v["z"].loc[w0:], v["thr"].loc[w0:], v["cross"].loc[w0:]
    axx.plot(zz_.index, zz_.values, color=ENTITY["emv"], lw=1.3, label="signal z")
    axx.plot(tt_.index, tt_.values, color=INK2, lw=1.0, ls="--", label="expanding past-only 80th percentile")
    axx.plot(zz_[cc_].index, zz_[cc_].values, "o", color=INK, ms=4.5, label="crossing (Short-Brown entry)")
    axx.axvline(BREAK, color=MUTED, lw=0.7, ls=":")
    axx.set_ylabel("z"); axx.set_title(ttl)
ax[2].xaxis.set_major_locator(mdates.YearLocator(1)); ax[2].xaxis.set_major_formatter(YF)
h_, l_ = ax[1].get_legend_handles_labels()
fig.legend(h_, l_, loc="outside lower center", ncol=3, fontsize=7.5)
savefig(fig, f"{MODULE}_rule_mechanics")

# F5: IC by period, validation vs holdout
fig, axes = plt.subplots(1, 2, figsize=(7.5, 5.2), sharey=True)
ylab = order
for axx, oname, ttl in ((axes[0], "GB", "Next-month Green-minus-Brown"), (axes[1], "brown_resid_FF3", "Next-month Brown residual (FF3)")):
    for j, (per, col) in enumerate((("validation", BLUE), ("holdout", VIOLET))):
        s = ics[(ics.outcome == oname) & (ics.period == per)].set_index("signal").reindex(ylab)
        se = (s.ic / s.t_nw).abs()
        yy = np.arange(len(ylab)) + (-0.18 if j == 0 else 0.18)
        axx.errorbar(s.ic, yy, xerr=1.96 * se, fmt="o", color=col, ms=4, lw=1.0, capsize=0,
                     label=("validation 2010-01..2022-07" if per == "validation" else "holdout 2022-08..2026-07"))
    axx.axvline(0, color=INK2, lw=0.8)
    axx.set_title(ttl)
    axx.grid(axis="y", visible=False)
axes[0].set_yticks(np.arange(len(ylab))); axes[0].set_yticklabels(ylab); axes[0].invert_yaxis()
fig.supxlabel("IC: slope of standardized next-month outcome on standardized signal (bars: 95% Newey-West band)", fontsize=8, color=INK2)
h_, l_ = axes[0].get_legend_handles_labels()
fig.legend(h_, l_, loc="outside upper center", ncol=2)
savefig(fig, f"{MODULE}_ic_by_period")

# ============================================================================= ledger and key numbers
led = L.frame()
led.to_csv(TABLES / f"{MODULE}_tests_ledger.csv", index=False)
lsum = led.assign(qid=led.test_id.str.split("_").str[0], valid=led.p_value_two_sided.notna(),
                  rej05=led.p_value_two_sided < 0.05).groupby(["qid", "primary_or_exploratory"]).agg(
    n_tests=("test_id", "size"), n_with_p=("valid", "sum"), n_p_below_05=("rej05", "sum")).reset_index()
lsum["share_p_below_05"] = lsum.n_p_below_05 / lsum.n_with_p
save_table(lsum, "tests_ledger_summary")
key("ledger_rows", len(led), "tests_ledger"); key("ledger_primary", int((led.primary_or_exploratory == "primary").sum()), "tests_ledger")
key("ledger_duplicates_merged", len(L.aliases), "tests_ledger", "same hypothesis and sample reported twice; recorded once")
kn = pd.DataFrame(KEY)
kn["value"] = kn["value"].map(lambda v: v if isinstance(v, str) else (int(v) if isinstance(v, (bool, np.bool_)) else v))
kn.to_csv(TABLES / f"{MODULE}_key_numbers.csv", index=False)
print(f"ledger rows: {len(led)} (primary {int((led.primary_or_exploratory == 'primary').sum())}); merged duplicates: {len(L.aliases)}; key numbers: {len(kn)}")
print("done")
