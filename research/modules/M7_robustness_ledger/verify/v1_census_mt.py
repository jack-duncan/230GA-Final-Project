"""M7 adversarial verification, part 1: census counts and multiple-testing families, recomputed independently.

Reads the eight module ledgers directly (not M7_all_tests.csv), classifies each row with plain `re` per the spec
(adopted_checks.md check 1), and runs Holm / BH / BY with statsmodels.multipletests instead of M7's own code.
Compares every count and adjusted p with the M7 output tables. Writes nothing outside this verify folder.

Run: cd /home/hashim/projects/GA/project/research && uv run python modules/M7_robustness_ledger/verify/v1_census_mt.py
"""
import glob
import pathlib
import re

import numpy as np
import pandas as pd
from statsmodels.stats.multitest import multipletests

ROOT = pathlib.Path(__file__).resolve().parents[3]
T = ROOT / "outputs" / "tables"
OUT = pathlib.Path(__file__).resolve().parent / "out"
OUT.mkdir(exist_ok=True)

files = sorted(p for p in glob.glob(str(T / "*_tests_ledger.csv")) if not pathlib.Path(p).name.startswith("M7"))
assert len(files) == 8, files
STD = ["test_id", "module", "question", "statistic_name", "statistic", "p_value_two_sided", "n_obs", "primary_or_exploratory", "note"]
A = pd.concat([pd.read_csv(p)[STD] for p in files], ignore_index=True)
print("rows", len(A), "exact dups (9 std cols)", int(A.duplicated().sum()))


def typ(sn, note):
    sn = "" if pd.isna(sn) else str(sn)
    note = "" if pd.isna(note) else str(note)
    if re.search("beta-timing", sn, re.I):
        return "beta-timing"
    if re.search("loading|t_b_|t_NW6_b_", sn, re.I) or "[loading]" in note.lower():
        return "loading"
    if re.search("alpha", sn, re.I):
        return "alpha"
    if re.search("mean", sn, re.I):
        return "mean"
    return "other"


A["mod"] = A["module"].map(lambda s: s.split("_")[0])
A["typ"] = [typ(a, b) for a, b in zip(A.statistic_name, A.note)]
lab = A.primary_or_exploratory


def fam(r):
    if r.test_id == "M8_share_i_alpha_nw6":
        return "F"
    if r.primary_or_exploratory == "primary" and r.typ == "alpha" and r["mod"] != "M8":
        return "P"
    if r.primary_or_exploratory == "primary":
        return "D"
    if r.primary_or_exploratory in ("placebo", "reference"):
        return "X"
    if r.typ in ("loading", "beta-timing"):
        return "L"
    if (r["mod"] == "M2" and str(r.test_id).endswith("|alpha")) or (r.primary_or_exploratory == "robustness" and r.typ == "alpha"):
        return "R"
    return "E"


A["fam"] = A.apply(fam, axis=1)
MODS = ["M1", "M1b", "M2", "M3", "M4", "M5", "M6", "M8"]
ct = pd.crosstab(A.fam, A["mod"]).reindex(index=list("FPDXLRE"), columns=MODS, fill_value=0)
print(ct, "\n", ct.sum(axis=1).to_dict())
m7 = pd.read_csv(T / "M7_census_family_by_module.csv").set_index("family")
diff_fam = (m7.loc[list("FPDXLRE"), MODS].astype(int) - ct).abs().to_numpy().sum()
print("family-by-module diff vs M7:", diff_fam)
lb = pd.crosstab(A["mod"], lab).reindex(index=MODS, fill_value=0)
m7l = pd.read_csv(T / "M7_census_label_by_module.csv").set_index("module_id")
print(lb, "\nlabel diff vs M7:", int((m7l.loc[MODS, lb.columns].astype(int) - lb).abs().to_numpy().sum()))
R = A[A.fam == "R"]
print("R-M2", int((R["mod"] == "M2").sum()), "R-other", int((R["mod"] != "M2").sum()),
      R[R["mod"] != "M2"].groupby("mod").size().to_dict())
Dm = A[A.fam == "D"].groupby("mod").size().to_dict(); print("D by module", Dm)
Pm = A[A.fam == "P"].groupby("mod").size().to_dict(); print("P by module", Pm)

nom = A[A.p_value_two_sided < 0.05]
nc = nom.typ.value_counts().to_dict()
print("nominal", len(nom), nc, "alpha+", int(((nom.typ == "alpha") & (nom.statistic > 0)).sum()),
      "alpha-", int(((nom.typ == "alpha") & (nom.statistic < 0)).sum()), "loading share", nc["loading"] / len(nom))
for f_ in "DXLE":
    g = A[A.fam == f_]
    print(f"family {f_}: rows {len(g)}, p2<0.05 {int((g.p_value_two_sided < 0.05).sum())}")


def p1(stat, p2):
    stat, p2 = np.asarray(stat, float), np.asarray(p2, float)
    return np.where(stat > 0, p2 / 2, 1 - p2 / 2)


# ---------------- family P
P = A[A.fam == "P"].copy()
P["k"] = list(zip(P.module, P.n_obs, P.statistic.round(8), P.p_value_two_sided.round(10)))
Pu = P[~P.k.duplicated()].copy()
print("P rows", len(P), "unique", len(Pu), "dups by module", P[P.k.duplicated()].groupby("mod").size().to_dict())
Pu["p1"] = p1(Pu.statistic, Pu.p_value_two_sided)
for meth, nm in (("holm", "holm"), ("fdr_bh", "bh"), ("fdr_by", "by")):
    rej, adj, _, _ = multipletests(Pu.p1, alpha=0.05, method=meth)
    Pu[nm] = adj
    print(f"P {nm}: min adj p {adj.min():.4f}, survivors {int(rej.sum())}")
b = Pu.sort_values("p1").iloc[0]
print("best P:", b.test_id, b.statistic, b.p1, "Sidak N", np.log(0.95) / np.log(1 - b.p1))
m7P = pd.read_csv(T / "M7_family_P.csv")
m7Pu = m7P[m7P.duplicate_of.isna()].set_index("test_id")
cmpP = Pu.set_index("test_id")[["p1", "holm", "bh", "by"]].join(m7Pu[["p1", "holm", "bh", "by"]], rsuffix="_m7")
print("P max abs diff p1/holm/bh/by:", *[float((cmpP[c] - cmpP[c + "_m7"]).abs().max()) for c in ("p1", "holm", "bh", "by")])

# ---------------- family F (M8 + check 7 (i) from the frozen record)
m8 = A[A.test_id == "M8_share_i_alpha_nw6"].iloc[0]
fz = pd.read_csv(T / "M7_frozen_pre1970.csv").set_index("item")["value"]
pF = np.array([float(p1(m8.statistic, m8.p_value_two_sided)), float(fz["p1"])])
rej, adj, _, _ = multipletests(pF, alpha=0.05, method="holm")
print("F: raw", pF, "holm", adj, "survivors", rej)

# ---------------- all primaries (not adopted), two-sided
PR = A[lab == "primary"]
ok = PR.p_value_two_sided.notna()
print("all primaries", len(PR), "with p", int(ok.sum()), "missing:", PR[~ok].test_id.tolist())
for meth in ("holm", "fdr_bh", "fdr_by"):
    rej, adj, _, _ = multipletests(PR.p_value_two_sided[ok], alpha=0.05, method=meth)
    s = PR[ok][rej]
    print(f"all-primaries {meth}: survivors {int(rej.sum())}; alpha-type {int((s.typ == 'alpha').sum())}")
    print(s[["test_id", "typ", "statistic_name", "p_value_two_sided"]].to_string())

# ---------------- family R
R = A[A.fam == "R"].copy()
R["p1"] = p1(R.statistic, R.p_value_two_sided)
groups = [("R-M2", R[R["mod"] == "M2"])] + [(f"R-other {m}", g) for m, g in R[R["mod"] != "M2"].groupby("mod")] + \
         [("R-other pooled", R[R["mod"] != "M2"]), ("R pooled", R)]
rows = []
for nm, g in groups:
    rb, ab, _, _ = multipletests(g.p1, alpha=0.05, method="fdr_bh")
    ry, ay, _, _ = multipletests(g.p1, alpha=0.05, method="fdr_by")
    rows.append({"family": nm, "m": len(g), "share_pos": (g.statistic > 0).mean(), "min_p1": g.p1.min(), "min_bh": ab.min(),
                 "min_by": ay.min(), "bh_surv": int(rb.sum()), "by_surv": int(ry.sum()),
                 "bh_surv_ids": "; ".join(g.test_id[rb]), "by_div": float(np.sum(1 / np.arange(1, len(g) + 1)))})
RR = pd.DataFrame(rows)
print(RR.drop(columns="bh_surv_ids").to_string())
print("R BH survivors:", RR.loc[RR.bh_surv > 0, ["family", "bh_surv_ids"]].to_string())
m7R = pd.read_csv(T / "M7_family_R_summary.csv").set_index("family")
cm = RR.set_index("family").join(m7R, rsuffix="_m7")
print("R diffs: min_bh", float((cm.min_bh - cm.min_bh_m7).abs().max()), "min_by", float((cm.min_by - cm.min_by_m7).abs().max()),
      "bh surv", int((cm.bh_surv - cm.bh_survivors).abs().sum()), "by surv", int((cm.by_surv - cm.by_survivors).abs().sum()))
sv = A[A.test_id == "CPU_realtime_none_O3_covid_alpha"]
print(sv[["test_id", "statistic_name", "statistic", "p_value_two_sided", "n_obs", "note"]].to_string())

# R-M2 by window
RM2 = R[R["mod"] == "M2"].copy()
RM2["w"] = RM2.test_id.str.split("|").str[-3]
RM2["kind"] = RM2.test_id.str.split("|").str[0]
print("kinds", RM2.kind.value_counts().to_dict())
for scope, g0 in (("all", RM2), ("strat", RM2[RM2.kind == "strat"])):
    out = g0.groupby("w").statistic.agg(n="size", pos=lambda s: (s > 0).mean(), med="median")
    out.loc["ALL"] = [len(g0), (g0.statistic > 0).mean(), g0.statistic.median()]
    print(scope, "\n", out.round(4).to_string())
