"""V11 (round 2): ledger completeness after Fix 5, timing-test BH counts (own BH, spot-checked regressions),
Ferson-Schadt table claims (wild p, seeds, classical F, window standardization), and a determinism / no-change check
of the rerun against (a) the pre-rerun copy of the tables and (b) my own round-1 outputs."""
import pathlib
import numpy as np
import pandas as pd
from scipy import stats
from vlib import m3_table, OUT, TABLES, build_bond_independent, factor_panel, load_team, nw, FF3UB, END, SH
from team_pipeline import TEAM_GREEN, TEAM_BROWN

pd.set_option("display.width", 260); pd.set_option("display.max_colwidth", 140); pd.set_option("display.max_columns", 40)
PRE = pathlib.Path("/tmp/claude-1000/-home-hashim-projects-GA/5d56c5f1-d319-48cb-b466-4daeaca6ed67/scratchpad/pre_r2")

# ------------------------------------------------------------------ ledger
L = m3_table("tests_ledger")
print("rows:", len(L), L.primary_or_exploratory.value_counts().to_dict(), "| dup ids:", int(L.test_id.duplicated().sum()),
      "| NaN p:", int(L.p_value_two_sided.isna().sum()))
P = L[L.primary_or_exploratory == "primary"]
print("primary rows:", len(P), "| Holm notes:", int(P.note.str.contains("Holm").sum()))
checks = {
    "24m structural attribution leak/residual": r"^Q5\.attr_(leak|residual)_24m\.",
    "  ... COVID corrected Pure 6m 24m leak": r"^Q5\.attr_leak_24m\.Pure 6m\|corrected\|covid",
    "  ... COVID corrected Pure 6m 24m residual": r"^Q5\.attr_residual_24m\.Pure 6m\|corrected\|covid",
    "in-period regression residual (pre_covid extra rows)": r"^Q5\.attr_residual_regression\.",
    "Q1 alpha corrected Pure 6m FF3+UMD+BOND covid (in-period residual)": r"^Q1\.alpha\.Pure \| Short Brown hold 6m\|corrected\|FF3\+UMD\+BOND\|covid$",
    "D mean": r"^Q3b\.D_mean\.",
    "D in-period alpha": r"^Q3b\.D_alpha_inperiod\.",
    "D timing": r"^Q3b\.ln_timing_vs_benchmark\.",
    "GB HML loading (FF3, full/post2010)": r"^Q1\.loading\.HML\..*GB.*\|FF3\|(full|post2010)",
    "FS wild bootstrap": r"^Q3a\.fs_boot_wald_c_wild\.",
    "GB classical-OLS short-window alphas": r"^Q1\.alpha_ols\.",
    "BOND-hedge baseline means": r"^Q2b\.hedged_mean\.",
    "post-hedge residual BOND loadings": r"^Q2b\.residual_bond_loading\.",
}
for k, pat in checks.items():
    m = L.test_id.str.contains(pat, regex=True)
    print(f"{k:70s} {int(m.sum()):5d}", L.loc[m, ["test_id", "statistic", "p_value_two_sided"]].head(2).round(4).values.tolist() if m.sum() <= 4 else "")
m = L.test_id.str.contains(r"^Q3b\.(D_mean|D_alpha_inperiod)\..*(covid|holdout)", regex=True)
print(L.loc[m & L.test_id.str.contains("corrected"), ["test_id", "statistic", "p_value_two_sided", "n_obs"]].round(4).to_string())
print(L[L.test_id.str.contains(r"^Q1\.loading\.HML\.", regex=True) & L.test_id.str.contains("GB")].head(6)[["test_id", "statistic", "p_value_two_sided"]].to_string())

# ------------------------------------------------------------------ timing tests: own BH, and spot-check regressions
TT = m3_table("timing_tests")
print("timing tests:", len(TT), "p<.05:", int((TT.p_gamma < .05).sum()))


def bh(p):
    p = np.asarray(p); m = len(p); o = np.argsort(p); q = np.empty(m)
    q[o] = np.minimum.accumulate((p[o] * m / np.arange(1, m + 1))[::-1])[::-1]
    return np.minimum(q, 1)


TT["q_pool"] = bh(TT.p_gamma.to_numpy())
print("pooled BH q<.05:", int((TT.q_pool < .05).sum()), TT[TT.q_pool < .05].groupby("factor").size().to_dict())
print(TT[(TT.q_pool < .05) & (TT.factor == "BOND")][["asset", "baseline", "period", "test", "spec", "gamma", "p_gamma", "q_pool"]].round(4).to_string())
grp = []
for (sp, fa, te), g in TT.groupby(["spec", "factor", "test"]):
    q = bh(g.p_gamma.to_numpy())
    grp.append({"spec": sp, "factor": fa, "test": te, "n": len(g), "p<.05": int((g.p_gamma < .05).sum()), "pos_sig": int(((g.p_gamma < .05) & (g.gamma > 0)).sum()),
                "bh_within": int((q < .05).sum())})
print(pd.DataFrame(grp).to_string())
gbt = TT[(TT.asset.str.startswith("GB")) & (TT.p_gamma < .05)]
print("GB timing tests p<.05:\n", gbt[["asset", "period", "n", "factor", "test", "spec", "gamma", "t_gamma", "p_gamma"]].round(3).to_string())
ab = TT[TT.asset.str.contains("Always") & (TT.factor == "HML") & (TT.test == "TM")]
print("Always-short HML TM:\n", ab[["baseline", "period", "spec", "t_gamma", "p_gamma"]].round(3).to_string())

# own regressions for a handful of rows (multifactor spec = FF3+UMD+BOND controls)
T = load_team(); rf = T["ff3"]["RF"]
F = factor_panel(build_bond_independent(rf)["BOND"])
ind = T["industries"]; GB = ind[TEAM_GREEN].mean(axis=1) - ind[TEAM_BROWN].mean(axis=1)
X = F[FF3UB].copy()
y = GB.loc["1970-01-31":END]
for kind in ("TM", "HM"):
    Xk = F[["Mkt-RF"]].copy(); Xk["g"] = F["Mkt-RF"] ** 2 if kind == "TM" else F["Mkt-RF"].clip(lower=0)
    f = nw(y, Xk); print(f"own GB full {kind} Mkt-RF single: gamma {f['b']['g']:.4f} t {f['t']['g']:.2f}")
    Xm = X.copy(); Xm["g"] = F["Mkt-RF"] ** 2 if kind == "TM" else F["Mkt-RF"].clip(lower=0)
    f = nw(y, Xm); print(f"own GB full {kind} Mkt-RF multi : gamma {f['b']['g']:.4f} t {f['t']['g']:.2f}")
print(TT[(TT.asset.str.startswith("GB")) & (TT.period.str.contains("full")) & (TT.factor == "Mkt-RF")][["asset", "period", "test", "spec", "gamma", "t_gamma"]].round(4).to_string())

# ------------------------------------------------------------------ Ferson-Schadt table claims
FS = m3_table("ferson_schadt")
print(FS.columns.tolist())
cols = [c for c in ("asset", "baseline", "period", "n", "alpha_uncond", "alpha_cond", "t_alpha_cond", "p_alpha_cond", "boot_wald_c_p", "boot_wald_c_wild_p",
                    "ols_F_c_p", "boot_wald_null_q95", "boot_wald_wild_null_q95", "alpha_cond_windowstd") if c in FS.columns]
print(FS[cols].round(4).to_string())
SEEDS = m3_table("fs_boot_seeds")
print(SEEDS.groupby(["asset", "baseline", "period"]).agg(pf_min=("p_fixed", "min"), pf_max=("p_fixed", "max"), pw_min=("p_wild", "min"),
                                                          pw_max=("p_wild", "max")).round(3).to_string())

# ------------------------------------------------------------------ determinism and no-change
rows = []
for f in sorted(PRE.glob("M3_alpha_beta_*.csv")):
    new = pd.read_csv(TABLES / f.name); old = pd.read_csv(f)
    same_shape = new.shape == old.shape and list(new.columns) == list(old.columns)
    md = np.nan
    if same_shape:
        num = new.select_dtypes("number").columns
        md = float((new[num] - old[num]).abs().max().max()) if len(num) else 0.0
        nonnum = [c for c in new.columns if c not in num]
        eq_txt = bool((new[nonnum].fillna("") == old[nonnum].fillna("")).all().all()) if nonnum else True
    else:
        eq_txt = False
    rows.append({"table": f.name.replace("M3_alpha_beta_", ""), "same_shape": same_shape, "max_num_diff": md, "text_equal": eq_txt})
Dd = pd.DataFrame(rows); print(Dd.to_string())
Dd.to_csv(OUT / "v11_determinism.csv", index=False)
