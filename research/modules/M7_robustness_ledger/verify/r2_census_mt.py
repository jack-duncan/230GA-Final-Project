"""Round-2 adversarial verification of M7 checks 1 to 3 and the M7 ledger aggregation (independent code).

Reads the eight module ledgers directly (not M7_all_tests.csv), classifies every row with a plain Python loop and
the `re` module per spec check 1, and runs Holm, BH and BY with hand-written step-down / step-up loops (cross-checked
against statsmodels.multipletests). Compares every count and adjusted p with M7's saved tables.

Run: cd /home/hashim/projects/GA/project/research && uv run python modules/M7_robustness_ledger/verify/r2_census_mt.py
"""
from __future__ import annotations

import csv
import glob
import math
import pathlib
import re
from collections import Counter, defaultdict

import numpy as np
import pandas as pd
from statsmodels.stats.multitest import multipletests

ROOT = pathlib.Path(__file__).resolve().parents[3]
T = ROOT / "outputs" / "tables"
OUT = pathlib.Path(__file__).resolve().parent / "out_r2"
OUT.mkdir(exist_ok=True)
LOG = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    LOG.append(s)


def check(name, ok, detail=""):
    say(f"[{'OK ' if ok else 'BAD'}] {name}" + (f": {detail}" if detail else ""))
    return ok


def fnum(x):
    try:
        v = float(x)
        return v if math.isfinite(v) else None
    except (TypeError, ValueError):
        return None


# ------------------------------------------------------------------ read ledgers row by row (csv module, not pandas)
files = sorted(p for p in glob.glob(str(T / "*_tests_ledger.csv")) if not pathlib.Path(p).name.startswith("M7_"))
rows = []
for fp in files:
    with open(fp, newline="") as fh:
        for r in csv.DictReader(fh):
            r["_file"] = pathlib.Path(fp).name
            rows.append(r)
say(f"ledgers: {len(files)}: {[pathlib.Path(f).name for f in files]}")
check("ledger rows = 23,923", len(rows) == 23923, str(len(rows)))
STD = ["test_id", "module", "question", "statistic_name", "statistic", "p_value_two_sided", "n_obs", "primary_or_exploratory", "note"]
keys = Counter(tuple(r[c] for c in STD) for r in rows)
check("no exact duplicates on nine standard columns", sum(v - 1 for v in keys.values()) == 0)

re_bt = re.compile(r"beta-timing", re.I)
re_ld = re.compile(r"loading|t_b_|t_NW6_b_", re.I)
re_al = re.compile(r"alpha", re.I)
re_mn = re.compile(r"mean", re.I)


def typ(r):
    sn, nt = r["statistic_name"] or "", r["note"] or ""
    if re_bt.search(sn):
        return "beta-timing"
    if re_ld.search(sn) or "[loading]" in nt.lower():
        return "loading"
    if re_al.search(sn):
        return "alpha"
    if re_mn.search(sn):
        return "mean"
    return "other"


def modid(r):
    return r["module"].split("_")[0]


def fam(r):
    lab, ty, m = r["primary_or_exploratory"], r["_type"], r["_mod"]
    if r["test_id"] == "M8_share_i_alpha_nw6":
        return "F"
    if lab == "primary" and ty == "alpha" and m != "M8":
        return "P"
    if lab == "primary":
        return "D"
    if lab in ("placebo", "reference"):
        return "X"
    if ty in ("loading", "beta-timing"):
        return "L"
    if (m == "M2" and r["test_id"].endswith("|alpha")) or (lab == "robustness" and ty == "alpha"):
        return "R"
    return "E"


for r in rows:
    r["_type"] = typ(r)
    r["_mod"] = modid(r)
    r["_fam"] = fam(r)
    r["_stat"] = fnum(r["statistic"])
    r["_p2"] = fnum(r["p_value_two_sided"])

# ------------------------------------------------------------------ check 1 counts
MODS = ["M1", "M1b", "M2", "M3", "M4", "M5", "M6", "M8"]
FAMS = ["F", "P", "D", "X", "L", "R", "E"]
fm = Counter((r["_fam"], r["_mod"]) for r in rows)
m7fm = pd.read_csv(T / "M7_census_family_by_module.csv").set_index("family")
bad = [(f, m, fm[(f, m)], int(m7fm.loc[f, m])) for f in FAMS for m in MODS if fm[(f, m)] != int(m7fm.loc[f, m])]
check("family x module table equals M7_census_family_by_module.csv", not bad, str(bad))
famtot = Counter(r["_fam"] for r in rows)
say("family totals:", {f: famtot[f] for f in FAMS})
exp = {"F": 1, "P": 81, "D": 73, "X": 170, "L": 4850, "R": 9337, "E": 9411}
check("family totals equal the spec and FINDINGS", all(famtot[f] == exp[f] for f in FAMS))
for f_, want in (("P", {"M1b": 24, "M2": 42, "M3": 12, "M4": 1, "M5": 2}),
                 ("D", {"M1": 15, "M1b": 16, "M2": 4, "M3": 21, "M5": 2, "M6": 8, "M8": 7})):
    got = {m: fm[(f_, m)] for m in MODS if fm[(f_, m)]}
    check(f"{f_} by module = FINDINGS", got == want, str(got))
rsub = Counter(("R-M2" if r["_mod"] == "M2" else "R-other:" + r["_mod"]) for r in rows if r["_fam"] == "R")
say("R subfamilies:", dict(rsub))
check("R-M2 8,161 and R-other 1,176 (M1b 736, M4 282, M3 156, M6 2)",
      rsub["R-M2"] == 8161 and rsub["R-other:M1b"] == 736 and rsub["R-other:M4"] == 282 and rsub["R-other:M3"] == 156
      and rsub["R-other:M6"] == 2 and sum(v for k, v in rsub.items() if k.startswith("R-other")) == 1176)

lm = Counter((r["_mod"], r["primary_or_exploratory"]) for r in rows)
m7lm = pd.read_csv(T / "M7_census_label_by_module.csv").set_index("module_id")
labs = [c for c in m7lm.columns if c != "Total"]
bad = [(m, l, lm[(m, l)], int(m7lm.loc[m, l])) for m in MODS for l in labs if lm[(m, l)] != int(m7lm.loc[m, l])]
check("label x module table equals M7_census_label_by_module.csv", not bad, str(bad))
FIND_LAB = {"M1": (435, 217, 15, 0, 0), "M1b": (588, 1102, 40, 88, 82), "M2": (7874, 5562, 46, 0, 0), "M3": (5590, 737, 33, 0, 0),
            "M4": (426, 375, 1, 0, 0), "M5": (412, 0, 4, 0, 0), "M6": (146, 120, 8, 0, 0), "M8": (14, 0, 8, 0, 0)}
bad = [(m, v, tuple(lm[(m, l)] for l in ("exploratory", "robustness", "primary", "placebo", "reference")))
       for m, v in FIND_LAB.items() if v != tuple(lm[(m, l)] for l in ("exploratory", "robustness", "primary", "placebo", "reference"))]
check("FINDINGS label-by-module table (every cell)", not bad, str(bad))
tot = Counter(r["primary_or_exploratory"] for r in rows)
say("label totals:", dict(tot))
check("label totals 15,485 / 8,113 / 155 / 88 / 82", (tot["exploratory"], tot["robustness"], tot["primary"], tot["placebo"],
                                                     tot["reference"]) == (15485, 8113, 155, 88, 82))

nom = [r for r in rows if r["_p2"] is not None and r["_p2"] < 0.05]
nt = Counter(r["_type"] for r in nom)
apos = sum(1 for r in nom if r["_type"] == "alpha" and (r["_stat"] or 0) > 0)
aneg = sum(1 for r in nom if r["_type"] == "alpha" and (r["_stat"] or 0) < 0)
say(f"nominal: {len(nom)}; {dict(nt)}; alpha +{apos} -{aneg}; loading share {nt['loading'] / len(nom):.4f}; alpha share {nt['alpha'] / len(nom):.4f}")
check("nominal census 4,184: alpha 1,624 (783+, 841-), loading 1,325, mean 561, other 536, beta-timing 138",
      (len(nom), nt["alpha"], apos, aneg, nt["loading"], nt["mean"], nt["other"], nt["beta-timing"]) ==
      (4184, 1624, 783, 841, 1325, 561, 536, 138))
fam_nom = Counter(r["_fam"] for r in nom)
check("nominal D 15, X 33, L 1,452, E 1,636", (fam_nom["D"], fam_nom["X"], fam_nom["L"], fam_nom["E"]) == (15, 33, 1452, 1636),
      str({k: fam_nom[k] for k in "DXLE"}))


# ------------------------------------------------------------------ my own adjusters (explicit loops)
def holm(p):
    p = list(p); m = len(p); o = sorted(range(m), key=lambda i: (p[i], i))
    out = [0.0] * m; run = 0.0
    for rank, i in enumerate(o):
        run = max(run, min(1.0, (m - rank) * p[i]))
        out[i] = run
    return out


def bh(p):
    p = list(p); m = len(p); o = sorted(range(m), key=lambda i: (p[i], i))
    out = [0.0] * m; run = 1.0
    for rank in range(m - 1, -1, -1):
        i = o[rank]
        run = min(run, p[i] * m / (rank + 1))
        out[i] = min(1.0, run)
    return out


def by(p):
    c = sum(1.0 / k for k in range(1, len(p) + 1))
    return [min(1.0, x * c) for x in bh(p)]


def p1of(stat, p2):
    return p2 / 2 if stat > 0 else 1 - p2 / 2


def xcheck(p, mine, method):
    ref = multipletests(np.asarray(p), method=method)[1]
    return float(np.max(np.abs(np.asarray(mine) - ref)))


# ------------------------------------------------------------------ check 2: family P
P = [r for r in rows if r["_fam"] == "P"]
seen, uniq, dups = {}, [], []
for r in P:
    k = (r["module"], int(float(r["n_obs"])), round(r["_stat"], 8), round(r["_p2"], 10))
    if k in seen:
        dups.append((r["test_id"], seen[k]["test_id"], r["_mod"]))
    else:
        seen[k] = r; uniq.append(r)
dmod = Counter(d[2] for d in dups)
check("P: 81 rows, 8 exact duplicates (M2 6, M3 2), m = 73", len(P) == 81 and len(uniq) == 73 and dmod == Counter({"M2": 6, "M3": 2}),
      f"{len(P)}, {len(uniq)}, {dict(dmod)}")
for d in dups:
    say("   duplicate:", d[0], "==", d[1])
p1 = [p1of(r["_stat"], r["_p2"]) for r in uniq]
hP, bP, yP = holm(p1), bh(p1), by(p1)
say(f"P xcheck vs statsmodels: holm {xcheck(p1, hP, 'holm'):.1e}, bh {xcheck(p1, bP, 'fdr_bh'):.1e}, by {xcheck(p1, yP, 'fdr_by'):.1e}")
ib = int(np.argmin(p1))
say(f"P best: {uniq[ib]['test_id']} ({uniq[ib]['module']}) t {uniq[ib]['_stat']:.4f} p1 {p1[ib]:.5f}; "
    f"Sidak count {math.log(0.95) / math.log(1 - p1[ib]):.3f}")
say(f"P min Holm {min(hP):.4f}, min BH {min(bP):.4f}, min BY {min(yP):.4f}; survivors Holm {sum(x <= 0.05 for x in hP)}, "
    f"BH {sum(x <= 0.05 for x in bP)}, BY {sum(x <= 0.05 for x in yP)}")
m7P = pd.read_csv(T / "M7_family_P.csv")
m7P = m7P[m7P.duplicate_of.isna()].set_index("test_id")
dd = max(max(abs(hP[i] - m7P.loc[r["test_id"], "holm"]), abs(bP[i] - m7P.loc[r["test_id"], "bh"]),
             abs(yP[i] - m7P.loc[r["test_id"], "by"]), abs(p1[i] - m7P.loc[r["test_id"], "p1"])) for i, r in enumerate(uniq))
check("P adjusted p equal M7_family_P.csv", dd < 1e-12 and len(m7P) == 73, f"max diff {dd:.1e}")
check("P: FINDINGS best p 0.0299, t 1.89, Sidak < 1.69; min Holm 1.00, BH 0.718, BY 1.00; 0 survivors",
      round(p1[ib], 4) == 0.0299 and round(uniq[ib]["_stat"], 2) == 1.89 and math.log(0.95) / math.log(1 - p1[ib]) < 1.69
      and round(min(hP), 2) == 1.0 and round(min(bP), 3) == 0.718 and round(min(yP), 2) == 1.0
      and sum(x <= 0.05 for x in hP + bP + yP) == 0)

# family F: M8 row from its ledger, check 7 (i) from M7's ledger row
m8 = [r for r in rows if r["_fam"] == "F"][0]
m7led = pd.read_csv(T / "M7_robustness_tests_ledger.csv")
c7 = m7led[m7led.test_id == "M7_C7_i_alpha_ff3umd"].iloc[0]
fp1 = [p1of(m8["_stat"], m8["_p2"]), float(c7.p_value_one_sided)]
fh = holm(fp1)
say(f"F: M8 t {m8['_stat']:.3f} p1 {fp1[0]:.4f} Holm {fh[0]:.4f}; C7(i) t {c7.statistic:.4f} p1 {fp1[1]:.5f} Holm {fh[1]:.5f}")
check("F Holm: M8 0.605 (no), C7(i) 0.0147 (yes)", round(fh[0], 3) == 0.605 and round(fh[1], 4) == 0.0147 and fh[1] <= 0.05 < fh[0])

# all 155 labelled primaries (not adopted), two-sided
PR = [r for r in rows if r["primary_or_exploratory"] == "primary"]
PRp = [r for r in PR if r["_p2"] is not None]
say(f"all primaries: {len(PR)}, with p {len(PRp)}; missing: {[r['test_id'] for r in PR if r['_p2'] is None]}")
p2s = [r["_p2"] for r in PRp]
hA, bA, yA = holm(p2s), bh(p2s), by(p2s)
sH = [PRp[i]["test_id"] for i in range(len(PRp)) if hA[i] <= 0.05]
sB = [PRp[i]["test_id"] for i in range(len(PRp)) if bA[i] <= 0.05]
sY = [PRp[i]["test_id"] for i in range(len(PRp)) if yA[i] <= 0.05]
say("  Holm:", sH); say("  BH:", sB); say("  BY:", sY)
say("  types of BH survivors:", [(PRp[i]["test_id"], PRp[i]["_mod"], PRp[i]["_type"]) for i in range(len(PRp)) if bA[i] <= 0.05])
check("all-primaries: 4 Holm, 6 BH, 4 BY, Holm set == BY set, none alpha",
      len(sH) == 4 and len(sB) == 6 and len(sY) == 4 and set(sH) == set(sY)
      and all(PRp[i]["_type"] != "alpha" for i in range(len(PRp)) if bA[i] <= 0.05))

# ------------------------------------------------------------------ check 3: family R
Rr = [r for r in rows if r["_fam"] == "R"]
groups = [("R-M2", [r for r in Rr if r["_mod"] == "M2"])]
for m in sorted({r["_mod"] for r in Rr if r["_mod"] != "M2"}):
    groups.append((f"R-other {m}", [r for r in Rr if r["_mod"] == m]))
groups += [("R-other pooled", [r for r in Rr if r["_mod"] != "M2"]), ("R pooled", Rr)]
m7R = pd.read_csv(T / "M7_family_R_summary.csv").set_index("family")
say("R family: m, share pos, min p1, min BH, min BY, BH surv, BY surv, BY divisor, best")
allok = True
for name, g in groups:
    pp = [p1of(r["_stat"], r["_p2"]) for r in g]
    b_, y_ = bh(pp), by(pp)
    sp = sum(1 for r in g if r["_stat"] > 0) / len(g)
    c = sum(1.0 / k for k in range(1, len(g) + 1))
    best = g[int(np.argmin(pp))]["test_id"]
    say(f"  {name:15s} {len(g):5d} {sp:.4f} {min(pp):.3e} {min(b_):.4f} {min(y_):.4f} {sum(x <= 0.05 for x in b_)} "
        f"{sum(x <= 0.05 for x in y_)} {c:.3f} {best}")
    mr = m7R.loc[name]
    ok = (len(g) == mr.m and abs(sp - mr.share_positive) < 1e-12 and abs(min(pp) - mr.min_p1) < 1e-15 and abs(min(b_) - mr.min_bh) < 1e-12
          and abs(min(y_) - mr.min_by) < 1e-12 and sum(x <= 0.05 for x in b_) == mr.bh_survivors
          and sum(x <= 0.05 for x in y_) == mr.by_survivors and best == mr.best_test)
    allok &= ok
    if name == "R pooled":
        say(f"    xcheck statsmodels BH {xcheck(pp, b_, 'fdr_bh'):.1e}, BY {xcheck(pp, y_, 'fdr_by'):.1e}")
check("every R row equals M7_family_R_summary.csv", allok)
g1b = [r for r in Rr if r["_mod"] == "M1b"]
pp = [p1of(r["_stat"], r["_p2"]) for r in g1b]
b_ = bh(pp)
surv = [(g1b[i]["test_id"], g1b[i]["_stat"], g1b[i]["n_obs"], g1b[i]["note"][:120]) for i in range(len(g1b)) if b_[i] <= 0.05]
say("  R-other M1b BH survivors:", surv)

# R-M2 windows
RM2 = [r for r in Rr if r["_mod"] == "M2"]
say("R-M2 by window (all rows | strategy rows): n, share>0, median t")
wins = defaultdict(list); wins_s = defaultdict(list)
for r in RM2:
    parts = r["test_id"].split("|")
    wins[parts[-3]].append(r["_stat"]); wins["all"].append(r["_stat"])
    if parts[0] == "strat":
        wins_s[parts[-3]].append(r["_stat"]); wins_s["all"].append(r["_stat"])
m7W = pd.read_csv(T / "M7_grid_windows.csv")
wok = True
for w in ["all", "full_1970", "full_live", "post2010", "validation", "pre_covid", "covid", "holdout", "inflation_rates", "last18", "last12"]:
    a, s = wins.get(w, []), wins_s.get(w, [])
    ra = (len(a), np.mean(np.array(a) > 0), float(np.median(a)))
    rs = (len(s), np.mean(np.array(s) > 0), float(np.median(s))) if s else (0, np.nan, np.nan)
    say(f"  {w:16s} {ra[0]:5d} {100 * ra[1]:5.1f}% {ra[2]:6.3f} | {rs[0]:5d} {100 * rs[1]:5.1f}% {rs[2]:6.3f}")
    mw = m7W[(m7W.scope == "all R-M2 rows") & (m7W.window == w)].iloc[0]
    wok &= (mw.n == ra[0] and abs(mw.share_positive - ra[1]) < 1e-12 and abs(mw.median_t - ra[2]) < 1e-12)
    if s:
        ms = m7W[(m7W.scope == "strategy rows only") & (m7W.window == w)].iloc[0]
        wok &= (ms.n == rs[0] and abs(ms.share_positive - rs[1]) < 1e-12 and abs(ms.median_t - rs[2]) < 1e-12)
check("R-M2 window table equals M7_grid_windows.csv", wok)
check("spread rows 153, strategy rows 8,008", len(wins_s["all"]) == 8008 and len(RM2) - len(wins_s["all"]) == 153)

# ------------------------------------------------------------------ M7 ledger aggregation (G7) and all-tests file
L = m7led
lc = L.primary_or_exploratory.value_counts().to_dict()
say(f"M7 ledger: {len(L)} rows; {lc}")
check("M7 ledger 481 rows: 1 primary, 387 robustness, 86 descriptive, 7 exploratory",
      len(L) == 481 and lc == {"robustness": 387, "descriptive": 86, "exploratory": 7, "primary": 1})
ncd = int(L.note.fillna("").str.contains(r"[context: descriptive]", regex=False).sum())
nce = int(L.note.fillna("").str.contains(r"[context: exploratory]", regex=False).sum())
check("context tags: 33 descriptive, 1 exploratory", (ncd, nce) == (33, 1), f"{ncd}, {nce}")
say("  exploratory-tag row:", L[L.note.fillna("").str.contains("[context: exploratory]", regex=False)].test_id.tolist())
chk = L.test_id.str.extract(r"^M7_C(\d+)_")[0].astype(float)
check("only C7_i is primary", L[L.primary_or_exploratory == "primary"].test_id.tolist() == ["M7_C7_i_alpha_ff3umd"])
check("checks 1 and 9 rows are descriptive or exploratory",
      set(L.loc[chk.isin([1, 9]), "primary_or_exploratory"]) <= {"descriptive", "exploratory"})
check("checks 2 to 8 rows other than C7(i) are robustness",
      set(L.loc[chk.between(2, 8) & ~L.test_id.eq("M7_C7_i_alpha_ff3umd"), "primary_or_exploratory"]) == {"robustness"})
say("  rows by check:", chk.value_counts().sort_index().to_dict())
cols = STD + ["p_value_one_sided", "alternative", "family"]
check("M7 ledger has the 12 G7 columns", list(L.columns) == cols, str(list(L.columns)))
AT = pd.read_csv(T / "M7_all_tests.csv", low_memory=False)
check("M7_all_tests.csv 24,404 rows = 23,923 module + 481 M7", len(AT) == 24404 and (AT.module_id == "M7").sum() == 481)
fam_at = AT[AT.module_id != "M7"].family.value_counts().to_dict()
check("M7_all_tests family column (module rows) equals my classification", fam_at == {f: famtot[f] for f in FAMS if famtot[f]},
      str(fam_at))
# every module row identical: same test_id order, statistic and p to float precision, same label
atm = AT[AT.module_id != "M7"].reset_index(drop=True)
mine = pd.DataFrame([{"test_id": r["test_id"], "lab": r["primary_or_exploratory"], "stat": r["_stat"], "p2": r["_p2"],
                      "fam": r["_fam"], "typ": r["_type"]} for r in rows])
same_id = (atm.test_id.astype(str).values == mine.test_id.values).all()
ds = np.nanmax(np.abs(atm.statistic.astype(float).values - mine.stat.astype(float).values))
dp = np.nanmax(np.abs(atm.p_value_two_sided.astype(float).values - mine.p2.astype(float).values))
check("M7_all_tests module rows: same order, test_id, label, family and type; statistic and p equal",
      same_id and (atm.primary_or_exploratory.values == mine.lab.values).all() and (atm.family.values == mine.fam.values).all()
      and (atm.type.values == mine.typ.values).all() and ds < 1e-12 and dp < 1e-12,
      f"max |d stat| {ds:.1e}, max |d p| {dp:.1e} (pandas fast float parser)")
(OUT / "r2_census_mt_log.txt").write_text("\n".join(LOG) + "\n")
