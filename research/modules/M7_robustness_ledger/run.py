"""M7 robustness ledger: the project-wide test census, multiple-testing families, search-adjusted tests,
deflated appraisal ratios, holdout reading, a frozen 1931-1969 run of the optimizer book, cost stress and the
verdict map. Implements exchange/03_robustness_design/adopted_checks.md (the "spec"), checks 0 to 10.

Run:  cd /home/hashim/projects/GA/project/research && uv run python modules/M7_robustness_ledger/run.py

Reads the eight module ledgers and the saved monthly return series; regenerates the M5 equal-weight variants and
screens, the team rules and the M1b real-time rules with the modules' own code (each checked against its saved
table). Writes only outputs/tables/M7_* and outputs/figures/M7_* plus first_run_record.json in this folder.

Order matters (spec check 7): the pre-registration hashes are written first, before any pre-1970 strategy
return exists; the dry run precedes the frozen run; the frozen run is computed once and its first result is
recorded in first_run_record.json, which later runs must reproduce.
"""
from __future__ import annotations

import datetime as dt
import glob
import hashlib
import json
import os
import pathlib
import sys
import time
import warnings

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SPEC_REL = "exchange/03_robustness_design/adopted_checks.md"
SPEC_PATH = ROOT / SPEC_REL
OPT_PATH = ROOT / "modules/M5_industry_momentum/optimizer.py"
M5LIB_PATH = ROOT / "modules/M5_industry_momentum/m5lib.py"
JOURNAL = pathlib.Path("/home/hashim/.claude/projects/-home-hashim-projects-GA/5d56c5f1-d319-48cb-b466-4daeaca6ed67/"
                       "subagents/workflows/wf_c1f5d333-469/journal.jsonl")
TABLES = ROOT / "outputs" / "tables"
FIGURES = ROOT / "outputs" / "figures"
PREREG_CSV = TABLES / "M7_preregistration_hash.csv"
FROZEN_RET_CSV = TABLES / "M7_frozen_pre1970_returns_monthly.csv"
FIRST_RUN = HERE / "first_run_record.json"
T0 = time.time()


def log(msg):
    print(f"[{time.time() - T0:7.1f}s] {msg}", flush=True)


# =============================================================================== check 7, step 0: pre-registration
def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def spec_bytes():
    """The adopted spec as the orchestrator saves it (lib/save_returned_files.py appends a final newline if absent).
    If the file is not on disk yet, read the same content from the workflow journal that carries it."""
    if SPEC_PATH.exists():
        return SPEC_PATH.read_bytes(), f"file {SPEC_REL}"
    content = None
    if JOURNAL.exists():
        for ln in JOURNAL.read_text().splitlines():
            d = json.loads(ln)
            if d.get("type") != "result" or not isinstance(d.get("result"), dict):
                continue
            for f in d["result"].get("files") or []:
                if f.get("path", "").endswith("03_robustness_design/adopted_checks.md"):
                    content = f["content"]            # later entries win, as in save_returned_files.py
    if content is None:
        raise SystemExit("adopted_checks.md not found on disk or in the workflow journal: cannot pre-register")
    content = content if content.endswith("\n") else content + "\n"
    return content.encode(), f"workflow journal {JOURNAL.parent.name} (file not yet on disk; hash equals the saved file)"


def preregister():
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    sb, src = spec_bytes()
    cur = {"adopted_checks.md": (SPEC_REL, src, _sha(sb)),
           "optimizer.py": ("modules/M5_industry_momentum/optimizer.py", "file", _sha(OPT_PATH.read_bytes())),
           "m5lib.py": ("modules/M5_industry_momentum/m5lib.py", "file", _sha(M5LIB_PATH.read_bytes()))}
    if not PREREG_CSV.exists():
        assert not FROZEN_RET_CSV.exists(), "a pre-1970 return file exists before pre-registration"
        rows = [{"item": k, "path": p, "source": s, "sha256": h, "first_written_utc": now, "this_run_utc": now,
                 "matches_first": True, "pre1970_returns_existed_at_first_write": False} for k, (p, s, h) in cur.items()]
        pd.DataFrame(rows).to_csv(PREREG_CSV, index=False)
        return pd.DataFrame(rows), True
    old = pd.read_csv(PREREG_CSV)
    old["this_run_utc"] = now
    old["matches_first"] = [cur[i][2] == h for i, h in zip(old["item"], old["sha256"])]
    old["source_this_run"] = [cur[i][1] for i in old["item"]]
    if not old["matches_first"].all():
        raise SystemExit("PRE-REGISTRATION VIOLATION: a hashed file changed since the first run:\n" + old.to_string())
    old.to_csv(PREREG_CSV, index=False)
    return old, False


import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

PREREG, FIRST_TIME = preregister()          # before any other computation
log(f"pre-registration hashes {'written' if FIRST_TIME else 'verified'}: " +
    ", ".join(f"{i} {h[:12]}" for i, h in zip(PREREG["item"], PREREG["sha256"])))

import statsmodels.api as sm  # noqa: E402
from scipy import stats  # noqa: E402
from scipy.cluster.hierarchy import linkage, fcluster  # noqa: E402
from scipy.spatial.distance import squareform  # noqa: E402

sys.path.insert(0, str(ROOT / "lib"))
sys.path.insert(0, str(ROOT / "modules" / "M5_industry_momentum"))
sys.path.insert(0, str(ROOT / "modules" / "M1b_alt_signals"))
import common as C  # noqa: E402
import m5lib as L5  # noqa: E402
import optimizer as OP  # noqa: E402
from team_pipeline import run_pipeline  # noqa: E402
import plotstyle as PS  # noqa: E402
from plotstyle import plt, savefig  # noqa: E402

warnings.filterwarnings("ignore")
pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 40)
MOD = "M7_robustness_ledger"
SEED, B = 20260926, 5000
EG = 0.5772156649
C6 = ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "UMD"]
F3 = ["Mkt-RF", "SMB", "HML"]
WIN = {"full": ("1970-01-31", "2026-07-31"), "post2010": ("2010-01-31", "2026-07-31"),
       "validation": ("2010-01-31", "2022-07-31"), "holdout": ("2022-08-31", "2026-07-31")}
WIN_N = {"full": 679, "post2010": 199, "validation": 151, "holdout": 48}
SKIP_FROZEN = os.environ.get("M7_SKIP_FROZEN") == "1"      # development switch only; the delivered run uses 0

# =============================================================================== ledger (G7)
LED: list[dict] = []


def led(test_id, question, stat_name, stat, p2, n, label, note="", p1=np.nan, alternative="two-sided", family=""):
    LED.append({"test_id": f"M7_{test_id}", "module": MOD, "question": question, "statistic_name": stat_name,
                "statistic": float(stat) if stat is not None and np.isfinite(stat) else np.nan,
                "p_value_two_sided": float(p2) if p2 is not None and np.isfinite(p2) else np.nan,
                "n_obs": int(n) if n is not None and np.isfinite(n) else 0, "primary_or_exploratory": label, "note": note,
                "p_value_one_sided": float(p1) if p1 is not None and np.isfinite(p1) else np.nan,
                "alternative": alternative, "family": family})


def save(df, name, index=False):
    df.to_csv(TABLES / f"M7_{name}.csv", index=index)
    return df


def tex(df: pd.DataFrame, name: str, caption: str, label: str, colfmt: str | None = None, notes: str | None = None,
        wide: bool = False):
    """booktabs table in a floating table environment; df cells should already be strings where formatting matters.
    wide=True scales the tabular to the text width (needs graphicx, loaded by the report preamble)."""
    body = df.to_latex(index=False, escape=True, column_format=colfmt or ("l" + "r" * (df.shape[1] - 1)))
    if wide:
        body = "\\resizebox{\\textwidth}{!}{%\n" + body.rstrip("\n") + "%\n}\n"
    s = ("\\begin{table}[htbp]\n\\centering\n\\footnotesize\n\\caption{" + caption + "}\n\\label{" + label + "}\n" + body)
    if notes:
        s += "\\par\\smallskip{\\scriptsize " + notes + "}\n"
    (TABLES / f"M7_{name}.tex").write_text(s + "\\end{table}\n")


def f(x, d=2):
    return "" if x is None or (isinstance(x, (float, np.floating)) and not np.isfinite(x)) else f"{x:.{d}f}"


def pc(x, d=2):
    return "" if x is None or (isinstance(x, (float, np.floating)) and not np.isfinite(x)) else f"{100 * x:.{d}f}"


# =============================================================================== statistics (G1, G2, G5, G6)
def fit(y: pd.Series, X: pd.DataFrame) -> dict:
    """G2 alpha regression with G5 appraisal-ratio inputs. y and X on the same months, no missing values."""
    d = pd.concat([y.rename("__y"), X], axis=1, sort=True)
    assert not d.isna().any().any(), "missing values in a regression window"
    Xm = sm.add_constant(d.drop(columns="__y"), has_constant="add")
    res = sm.OLS(d["__y"], Xm).fit(cov_type="HAC", cov_kwds={"maxlags": 6}, use_t=True)
    ols = sm.OLS(d["__y"], Xm).fit()
    n, k = Xm.shape
    e = ols.resid
    s_e = float(e.std(ddof=k))
    a, se, t = float(res.params["const"]), float(res.bse["const"]), float(res.tvalues["const"])
    out = {"n": n, "k": k, "df": n - k, "alpha_m": a, "alpha": 12 * a, "se_m": se, "se": 12 * se, "t": t,
           "p2": float(res.pvalues["const"]), "p1": float(stats.t.sf(t, n - k)), "t_ols": float(ols.tvalues["const"]),
           "s_e_m": s_e, "resid_vol": np.sqrt(12) * s_e, "ar_m": a / s_e, "ar": np.sqrt(12) * a / s_e,
           "skew": float(stats.skew(e, bias=False)), "kurt": float(stats.kurtosis(e, fisher=False, bias=False)),
           "r2": float(ols.rsquared), "resid": e}
    for c in X.columns:
        out[f"b_{c}"] = float(res.params[c]); out[f"t_{c}"] = float(res.tvalues[c])
    return out


def stationary_idx(T: int, B_: int, rng) -> np.ndarray:
    """G6: Politis-Romano stationary bootstrap, mean block 12. First index uniform; later ones restart with p = 1/12."""
    starts = rng.integers(0, T, size=(B_, T))
    switch = rng.random((B_, T)) < 1 / 12
    idx = np.empty((B_, T), dtype=np.int64)
    idx[:, 0] = starts[:, 0]
    for t in range(1, T):
        idx[:, t] = np.where(switch[:, t], starts[:, t], (idx[:, t - 1] + 1) % T)
    return idx


def one_sided(stat, p2):
    stat, p2 = np.asarray(stat, float), np.asarray(p2, float)
    return np.where(stat > 0, p2 / 2, 1 - p2 / 2)


def _finite_apply(p, fn):
    """Apply an adjustment to the finite p-values only (m = number of finite p-values); NaN stays NaN."""
    p = np.asarray(p, float); out = np.full(len(p), np.nan); ok = np.isfinite(p)
    if ok.any():
        out[ok] = fn(p[ok])
    return out


def _holm(p):
    m = len(p); o = np.argsort(p, kind="mergesort")
    adj = np.minimum(1, np.maximum.accumulate((m - np.arange(m)) * p[o]))
    out = np.empty(m); out[o] = adj
    return out


def _bh(p):
    m = len(p); o = np.argsort(p, kind="mergesort")
    adj = np.minimum.accumulate((p[o] * m / np.arange(1, m + 1))[::-1])[::-1]
    out = np.empty(m); out[o] = np.minimum(1, adj)
    return out


def by_const(m):
    return float(np.sum(1.0 / np.arange(1, m + 1)))


def holm_adj(p):
    return _finite_apply(p, _holm)


def bh_adj(p):
    return _finite_apply(p, _bh)


def by_adj(p):
    return _finite_apply(p, lambda q: np.minimum(1, _bh(q) * by_const(len(q))))


def nyholt_liji(resid: pd.DataFrame):
    Rm = np.corrcoef(resid.values, rowvar=False)
    lam = np.linalg.eigvalsh(Rm)
    M = Rm.shape[0]
    ny = 1 + (M - 1) * (1 - np.var(lam, ddof=1) / M)
    lc = np.clip(lam, 0, None)
    lj = float(np.sum((lc >= 1).astype(float) + (lc - np.floor(lc))))
    return float(ny), lj, Rm


def emax(N):
    return 0.0 if N <= 1 else (1 - EG) * stats.norm.ppf(1 - 1 / N) + EG * stats.norm.ppf(1 - 1 / (N * np.e))


def dsr(sr_m, T, g3, g4, N, V, t_nw, t_iid):
    sr0 = np.sqrt(V) * emax(N)
    z = (sr_m - sr0) * np.sqrt(T - 1) / np.sqrt(1 - g3 * sr_m + (g4 - 1) / 4 * sr_m ** 2)
    d_iid, d_nw = stats.norm.cdf(z), stats.norm.cdf(z * t_nw / t_iid)
    return {"SR0": sr0, "z": z, "DSR_iid": d_iid, "DSR_NW": d_nw, "DSR_gov": min(d_iid, d_nw)}


def lo_eta(x: pd.Series, q=12):
    rho = [x.autocorr(k) for k in range(1, q)]
    return q / np.sqrt(q + 2 * sum((q - k) * rho[k - 1] for k in range(1, q)))


def nw_mean_t(x: pd.Series):
    r = sm.OLS(x.values, np.ones(len(x))).fit(cov_type="HAC", cov_kwds={"maxlags": 6}, use_t=True)
    return float(r.tvalues[0]), float(r.pvalues[0])


def wsl(s, w):
    a, b = WIN[w] if isinstance(w, str) else w
    return s.loc[a:b]


# =============================================================================== data shared by several checks
FAC = C.load_ff5_mom()
X6 = FAC[C6]
KF3 = C.load_kf_ff3()
UMD_RAW = C._kf_monthly(list(C._kf_sections(C.RAW / "kf_F-F_Momentum_Factor.csv").values())[0]).iloc[:, 0] / 100
_chk = (UMD_RAW - FAC["UMD"]).dropna()
assert len(_chk) > 700 and _chk.abs().max() < 1e-12, "raw UMD file differs from load_ff5_mom UMD"
X4 = KF3[F3].join(UMD_RAW.rename("UMD"), how="left")      # FF3+UMD for any window from 1927-01

# ===================================================================================================== CHECK 1
log("check 1: census and family map")
QC = "C1 test census and family map"
files = sorted(f for f in glob.glob(str(TABLES / "*_tests_ledger.csv")) if not pathlib.Path(f).name.startswith("M7_"))
STD = ["test_id", "module", "question", "statistic_name", "statistic", "p_value_two_sided", "n_obs", "primary_or_exploratory", "note"]
parts = []
for fp in files:
    d = pd.read_csv(fp)
    for c in ("p_value_one_sided", "alternative"):
        if c not in d.columns:
            d[c] = np.nan
    d["ledger_file"] = pathlib.Path(fp).name
    parts.append(d[STD + ["p_value_one_sided", "alternative", "ledger_file"]])
ALL = pd.concat(parts, ignore_index=True)
n_raw = len(ALL)
n_dup = int(ALL.duplicated(subset=STD).sum())
ALL = ALL.drop_duplicates(subset=STD).reset_index(drop=True)
ALL["module_id"] = ALL["module"].str.split("_").str[0]
sn, nt = ALL["statistic_name"].fillna(""), ALL["note"].fillna("")
ALL["type"] = np.select([sn.str.contains("beta-timing", case=False, regex=True),
                         sn.str.contains("loading|t_b_|t_NW6_b_", case=False, regex=True) | nt.str.contains("[loading]", case=False, regex=False),
                         sn.str.contains("alpha", case=False, regex=True), sn.str.contains("mean", case=False, regex=True)],
                        ["beta-timing", "loading", "alpha", "mean"], "other")
lab = ALL["primary_or_exploratory"]
isF = ALL["test_id"].eq("M8_share_i_alpha_nw6")
isP = lab.eq("primary") & ALL["type"].eq("alpha") & ~ALL["module_id"].eq("M8")
isD = lab.eq("primary")
isX = lab.isin(["placebo", "reference"])
isL = ALL["type"].isin(["loading", "beta-timing"])
isR = (ALL["module_id"].eq("M2") & ALL["test_id"].str.endswith("|alpha")) | (lab.eq("robustness") & ALL["type"].eq("alpha"))
ALL["family"] = np.select([isF, isP, isD, isX, isL, isR], ["F", "P", "D", "X", "L", "R"], "E")
ALL["r_subfamily"] = np.where(ALL["family"].eq("R"), np.where(ALL["module_id"].eq("M2"), "R-M2", "R-other"), "")
ALL["is_primary_label"] = lab.eq("primary")
assert n_raw == 23923, f"expected 23,923 ledger rows, found {n_raw}"

MODS = ["M1", "M1b", "M2", "M3", "M4", "M5", "M6", "M8"]
FAMS = ["F", "P", "D", "X", "L", "R", "E"]
fam_mod = pd.crosstab(ALL["family"], ALL["module_id"]).reindex(index=FAMS, columns=MODS, fill_value=0)
fam_mod["Total"] = fam_mod.sum(axis=1)
fam_mod.loc["Total"] = fam_mod.sum()
save(fam_mod.reset_index().rename(columns={"family": "family"}), "census_family_by_module")
lab_mod = pd.crosstab(ALL["module_id"], ALL["primary_or_exploratory"]).reindex(index=MODS, fill_value=0)
lab_mod["Total"] = lab_mod.sum(axis=1)
lab_mod.loc["Total"] = lab_mod.sum()
save(lab_mod.reset_index(), "census_label_by_module")
FAM_RULE = {"F": "frozen, hash-verified: M8_share_i_alpha_nw6 (+ check 7 (i))", "P": "label primary, type alpha, not M8",
            "D": "other primaries", "X": "label placebo or reference", "L": "type loading or beta-timing",
            "R": "M2 |alpha rows; other modules' robustness alpha rows", "E": "everything else"}
FAM_TREAT = {"F": "Holm, one-sided", "P": "Holm and BH, one-sided", "D": "raw p, no correction", "X": "calibration only",
             "L": "confidence intervals only", "R": "BH and BY, one-sided, as distributions", "E": "no correction"}
for fam in FAMS:
    for m in MODS:
        v = int(fam_mod.loc[fam, m])
        if v:
            led(f"C1_count_{fam}_{m}", QC, f"rows in family {fam}, module {m}", v, np.nan, v, "descriptive",
                FAM_RULE[fam], family="census")
    led(f"C1_count_{fam}", QC, f"rows in family {fam}", int(fam_mod.loc[fam, "Total"]), np.nan, int(fam_mod.loc[fam, "Total"]),
        "descriptive", f"{FAM_RULE[fam]}; treatment: {FAM_TREAT[fam]}", family="census")
for m in MODS:
    for lb in lab_mod.columns[:-1]:
        v = int(lab_mod.loc[m, lb])
        if v:
            led(f"C1_label_{m}_{lb}", QC, f"rows labelled {lb}, module {m}", v, np.nan, v, "descriptive", family="census")
for lb in lab_mod.columns[:-1]:
    led(f"C1_label_total_{lb}", QC, f"rows labelled {lb}, all modules", int(lab_mod.loc["Total", lb]), np.nan,
        int(lab_mod.loc["Total", lb]), "descriptive", family="census")
led("C1_total_rows", QC, "ledger rows, eight module ledgers", n_raw, np.nan, n_raw, "descriptive",
    f"{len(files)} ledgers; exact duplicates across the nine standard columns: {n_dup}", family="census")
n_rm2, n_ro = int((ALL.r_subfamily == "R-M2").sum()), int((ALL.r_subfamily == "R-other").sum())
led("C1_count_R-M2", QC, "rows in R-M2", n_rm2, np.nan, n_rm2, "descriptive", family="census")
led("C1_count_R-other", QC, "rows in R-other", n_ro, np.nan, n_ro, "descriptive",
    "; ".join(f"{m} {int(v)}" for m, v in ALL[ALL.r_subfamily == "R-other"].groupby("module_id").size().items()), family="census")

nom = ALL[ALL["p_value_two_sided"] < 0.05]
nc = nom.groupby("type").size().reindex(["alpha", "loading", "mean", "other", "beta-timing"], fill_value=0)
al_pos, al_neg = int(((nom.type == "alpha") & (nom.statistic > 0)).sum()), int(((nom.type == "alpha") & (nom.statistic < 0)).sum())
ncen = pd.DataFrame({"type": list(nc.index) + ["alpha, positive statistic", "alpha, negative statistic", "all"],
                     "rows_p_lt_0.05": list(nc.values) + [al_pos, al_neg, len(nom)]})
ncen["share_of_nominal"] = ncen["rows_p_lt_0.05"] / len(nom)
save(ncen, "census_nominal")
for _, r in ncen.iterrows():
    led(f"C1_nominal_{r['type'].replace(' ', '_').replace(',', '')}", QC, f"rows with two-sided p < 0.05, {r['type']}",
        r["rows_p_lt_0.05"], np.nan, len(nom), "descriptive", f"share of all nominal hits {r['share_of_nominal']:.3f}",
        family="census")
t1 = fam_mod.reset_index()
t1.insert(1, "Treatment", t1["family"].map(FAM_TREAT).fillna(""))
t1 = t1.astype({c: str for c in t1.columns})
tex(t1.rename(columns={"family": "Family"}), "census_family_by_module",
    "Project test census: ledger rows by multiple-testing family and module (spec check 1).", "tab:m7_census",
    "ll" + "r" * (t1.shape[1] - 2),
    notes=(f"{n_raw:,} rows from eight ledgers; no exact duplicates. F frozen and hash-verified; P module primary alpha tests; "
           "D other primaries; X placebo and reference; L loadings and beta-timing terms; R robustness alpha grids; E exploratory. "
           f"Rows with two-sided p below 0.05: {len(nom):,}, of which {int(nc['alpha']):,} alpha ({al_pos} positive, {al_neg} negative), "
           f"{int(nc['loading']):,} loading, {int(nc['mean'])} mean, {int(nc['other'])} other and {int(nc['beta-timing'])} beta-timing."))
log(f"  {n_raw} rows, dups {n_dup}; families {fam_mod['Total'].to_dict()}; nominal {len(nom)}")

# ===================================================================================================== CHECK 2
log("check 2: family P (Holm, BH) and family F")
QP = "C2 family P: module primary alpha tests, project-wide one-sided correction"
P = ALL[ALL.family == "P"].copy()
P["key"] = list(zip(P.module, P.n_obs, P.statistic.round(8), P.p_value_two_sided.round(10)))
P["duplicate_of"] = ""
first = {}
for i, r in P.iterrows():
    if r.key in first:
        P.at[i, "duplicate_of"] = P.at[first[r.key], "test_id"]
    else:
        first[r.key] = i
Pu = P[P.duplicate_of == ""].copy()
Pu["p1"] = one_sided(Pu.statistic, Pu.p_value_two_sided)
Pu["holm"] = holm_adj(Pu.p1)
Pu["bh"] = bh_adj(Pu.p1)
Pu["by"] = by_adj(Pu.p1)
Pu["survives_holm"], Pu["survives_bh"] = Pu.holm <= 0.05, Pu.bh <= 0.05
Pu = Pu.sort_values("p1")
pout = pd.concat([Pu, P[P.duplicate_of != ""]], ignore_index=True)[
    ["test_id", "module", "statistic_name", "statistic", "p_value_two_sided", "n_obs", "duplicate_of", "p1", "holm", "bh", "by",
     "survives_holm", "survives_bh"]]
save(pout, "family_P")
mP = len(Pu)
best = Pu.iloc[0]
sidak_P = np.log(0.95) / np.log(1 - best.p1)
for _, r in Pu.iterrows():
    led(f"C2_P_{r.test_id}", QP, f"one-sided p of {r.statistic_name}", r.statistic, r.p_value_two_sided, r.n_obs, "robustness",
        f"{r.module}; Holm p {r.holm:.4f}; BH p {r.bh:.4f}; BY p {r.by:.4f}; m = {mP}", p1=r.p1, alternative="greater", family="P")
led("C2_P_m", QP, "family P size after collapsing duplicates", mP, np.nan, mP, "robustness",
    f"{len(P)} rows, {len(P) - mP} exact duplicates collapsed (M2 {int((P.duplicate_of != '')[P.module.str.startswith('M2')].sum())}, "
    f"M3 {int((P.duplicate_of != '')[P.module.str.startswith('M3')].sum())})", family="P")
led("C2_P_min_holm", QP, "smallest Holm-adjusted one-sided p", Pu.holm.min(), Pu.holm.min(), mP, "robustness",
    f"survivors at 5%: {int(Pu.survives_holm.sum())}", family="P")
led("C2_P_min_bh", QP, "smallest BH-adjusted one-sided p", Pu.bh.min(), Pu.bh.min(), mP, "robustness",
    f"survivors at 5%: {int(Pu.survives_bh.sum())}", family="P")
led("C2_P_best_p1", QP, f"best one-sided p ({best.test_id})", best.statistic, best.p_value_two_sided, best.n_obs, "robustness",
    f"Sidak count at which it stops being significant at 5%: {sidak_P:.2f}", p1=best.p1, alternative="greater", family="P")

# family F: M8 plus check 7 (i), filled in after the frozen run
F_M8 = ALL[ALL.family == "F"].iloc[0]
F_M8_p1 = float(one_sided(F_M8.statistic, F_M8.p_value_two_sided))

# the not-adopted design, for reference: all labelled primaries as one family, two-sided
PR = ALL[ALL.is_primary_label].copy()
PR["holm"], PR["bh"], PR["by"] = holm_adj(PR.p_value_two_sided), bh_adj(PR.p_value_two_sided), by_adj(PR.p_value_two_sided)
PRs = PR[(PR.holm <= 0.05) | (PR.bh <= 0.05)].sort_values("p_value_two_sided")
save(PRs[["test_id", "module", "type", "family", "statistic_name", "statistic", "p_value_two_sided", "n_obs", "holm", "bh", "by"]],
     "all_primaries_not_adopted_survivors")
led("C2_allprimaries_holm_survivors", "C2 reference: all labelled primaries as one family (not adopted)",
    "Holm survivors, two-sided, labelled primaries with a p-value", int((PR.holm <= 0.05).sum()), np.nan,
    int(PR.p_value_two_sided.notna().sum()), "exploratory",
    f"{len(PR)} labelled primaries, {int(PR.p_value_two_sided.isna().sum())} without a p-value; BH survivors {int((PR.bh <= 0.05).sum())}, BY survivors {int((PR.by <= 0.05).sum())}; alpha-type survivors "
    f"{int(((PR.holm <= 0.05) & (PR.type == 'alpha')).sum())} (Holm), {int(((PR.bh <= 0.05) & (PR.type == 'alpha')).sum())} (BH); "
    "the spec replaces this family with P and D", family="all-primaries")

# D, X, L summaries (reported, not corrected)
Dfam = ALL[ALL.family == "D"].copy()
save(Dfam[["test_id", "module", "type", "statistic_name", "statistic", "p_value_two_sided", "n_obs"]].sort_values("p_value_two_sided"),
     "family_D")
fam_sum = []
for fam in FAMS:
    g = ALL[ALL.family == fam]
    fam_sum.append({"family": fam, "rule": FAM_RULE[fam], "treatment": FAM_TREAT[fam], "rows": len(g),
                    "rows_p2_lt_0.05": int((g.p_value_two_sided < 0.05).sum())})
fam_sum = pd.DataFrame(fam_sum)
for fam in ("D", "X", "L", "E"):
    r = fam_sum.set_index("family").loc[fam]
    led(f"C2_{fam}_nominal", "C2 families reported without correction", f"rows with two-sided p < 0.05 in family {fam}",
        r["rows_p2_lt_0.05"], np.nan, r["rows"], "descriptive", r["treatment"], family=fam)

# ===================================================================================================== CHECK 3
log("check 3: family R (BH, BY)")
QR = "C3 family R: robustness alpha grids as distributions"
Rf = ALL[ALL.family == "R"].copy()
Rf["p1"] = one_sided(Rf.statistic, Rf.p_value_two_sided)
rrows = []
groups = [("R-M2", Rf[Rf.r_subfamily == "R-M2"])]
groups += [(f"R-other {m}", g) for m, g in Rf[Rf.r_subfamily == "R-other"].groupby("module_id")]
groups += [("R-other pooled", Rf[Rf.r_subfamily == "R-other"]), ("R pooled", Rf)]
for name, g in groups:
    bhp, byp = bh_adj(g.p1), by_adj(g.p1)
    row = {"family": name, "m": len(g), "by_divisor": by_const(len(g)), "share_positive": float((g.statistic > 0).mean()),
           "min_p1": float(g.p1.min()), "min_bh": float(bhp.min()), "min_by": float(byp.min()),
           "bh_survivors": int((bhp <= 0.05).sum()), "by_survivors": int((byp <= 0.05).sum()),
           "best_test": g.loc[g.p1.idxmin(), "test_id"]}
    rrows.append(row)
    led(f"C3_{name.replace(' ', '_')}_bh", QR, f"BH positive survivors at 5%, {name}", row["bh_survivors"], row["min_bh"], len(g),
        "robustness", f"smallest one-sided p {row['min_p1']:.2e} ({row['best_test']}); smallest BH p {row['min_bh']:.3f}",
        p1=row["min_p1"], alternative="greater", family=name)
    led(f"C3_{name.replace(' ', '_')}_by", QR, f"BY positive survivors at 5%, {name}", row["by_survivors"], row["min_by"], len(g),
        "robustness", f"BY divisor {row['by_divisor']:.3f}; smallest BY p {row['min_by']:.3f}", p1=row["min_p1"],
        alternative="greater", family=name)
    if name != "R-M2":                      # R-M2's share is in the C3_RM2_all_all_share_pos row below
        led(f"C3_{name.replace(' ', '_')}_share_pos", QR, f"share of positive alpha t, {name}", row["share_positive"], np.nan,
            len(g), "robustness", f"{int((g.statistic > 0).sum())} of {len(g)} rows", family=name)
Rsum = save(pd.DataFrame(rrows), "family_R_summary")
RM2 = Rf[Rf.r_subfamily == "R-M2"].copy()
RM2["window"] = RM2.test_id.str.split("|").str[-3]
RM2["kind"] = RM2.test_id.str.split("|").str[0]
WORDER = ["full_1970", "full_live", "post2010", "validation", "pre_covid", "covid", "holdout", "inflation_rates", "last18", "last12"]
wrows = []
for scope, g0 in (("all R-M2 rows", RM2), ("strategy rows only", RM2[RM2.kind == "strat"])):
    for w in ["all"] + WORDER:
        g = g0 if w == "all" else g0[g0.window == w]
        if not len(g):
            continue
        wrows.append({"scope": scope, "window": w, "n": len(g), "share_positive": float((g.statistic > 0).mean()),
                      "median_t": float(g.statistic.median()), "share_t_gt_1.96": float((g.statistic > 1.96).mean()),
                      "share_t_lt_-1.96": float((g.statistic < -1.96).mean())})
Rwin = save(pd.DataFrame(wrows), "grid_windows")
for _, r in Rwin.iterrows():
    sc = "all" if r.scope.startswith("all") else "strat"
    led(f"C3_RM2_{sc}_{r.window}_share_pos", QR, f"share of positive alpha t, R-M2 ({r.scope}), window {r.window}",
        r.share_positive, np.nan, r.n, "robustness", f"median t {r.median_t:.3f}", family="R-M2")
tw = Rwin[Rwin.scope == "all R-M2 rows"].merge(Rwin[Rwin.scope == "strategy rows only"], on="window", how="left", suffixes=("", "_s"))
tex(pd.DataFrame({"Window": tw.window, "Rows": tw.n.astype(int).astype(str), "Positive %": tw.share_positive.map(lambda v: pc(v, 1)),
                  "Median t": tw.median_t.map(f), "Strategy rows": tw.n_s.fillna(0).astype(int).astype(str),
                  "Positive % (strat.)": tw.share_positive_s.map(lambda v: pc(v, 1)), "Median t (strat.)": tw.median_t_s.map(f)}),
    "grid_windows", "Christhian's robustness grid (family R-M2) as a distribution: share of positive alpha t-statistics and "
    "median t by evaluation window (spec check 3).", "tab:m7_grid_windows",
    notes=("Window is the third-from-last field of the test id. Strategy rows exclude the 153 Green-minus-Brown spread rows. "
           f"One-sided BH and BY at 5\\%: {int(Rsum.set_index('family').loc['R-M2', 'bh_survivors'])} and "
           f"{int(Rsum.set_index('family').loc['R-M2', 'by_survivors'])} positive survivors in R-M2; "
           f"{int(Rsum.set_index('family').loc['R pooled', 'bh_survivors'])} and {int(Rsum.set_index('family').loc['R pooled', 'by_survivors'])} in R pooled."))

# ===================================================================================================== CHECK 4
log("check 4: search families (members, reproduction checks)")
QS = "C4 search families: Romano-Wolf max-t and Hansen SPA"
Tn = TABLES
opt = pd.read_csv(Tn / "M5_industry_momentum_optimizer_returns_monthly.csv", index_col=0, parse_dates=True)
ew = pd.read_csv(Tn / "M5_industry_momentum_returns_monthly.csv", index_col=0, parse_dates=True)
gb = pd.read_csv(Tn / "M4_emissions_gb_monthly_returns.csv", index_col=0, parse_dates=True)
rob_tab = pd.read_csv(Tn / "M5_industry_momentum_robustness.csv").set_index("variant")
scr_tab = pd.read_csv(Tn / "M5_industry_momentum_carbon_screens.csv").set_index("book")

# M5 regenerations, with the arguments M5's run.py uses
D5 = L5.load_inputs()
R5, ff5_5, cap5, emis5 = D5["R"], D5["ff5"], D5["cap"], D5["emis"]
X6_5 = ff5_5[C6]
sig5 = L5.mom_signal(R5, 11, 1)
VAR = [("window_1-0", dict(L=1, S=0, n=8)), ("window_6-1", dict(L=6, S=1, n=8)), ("window_12-1", dict(L=12, S=1, n=8)),
       ("no_skip_12-0", dict(L=12, S=0, n=8)), ("n5_per_leg", dict(L=11, S=1, n=5)), ("n10_per_leg", dict(L=11, S=1, n=10)),
       ("cap_weighted_legs", dict(L=11, S=1, n=8, cap=True)), ("KF_Aug2026_vintage", dict(L=11, S=1, n=8, kf=True))]
cm5 = L5.carbon_maps(emis5, R5.columns)
covered = cm5["covered"]
top_emit = list(emis5.sort_values(ascending=False).index)
top5, top8, all_ind = top_emit[:5], top_emit[:8], list(R5.columns)
SCR = {"A0X_long_covered_only": (covered, None), "A5X_long_excl_top5": ([c for c in covered if c not in top5], None),
       "A8X_long_excl_top8": ([c for c in covered if c not in top8], None),
       "B0X_both_covered_only": (covered, covered), "B5X_both_excl_top5": ([c for c in covered if c not in top5],) * 2,
       "B8X_both_excl_top8": ([c for c in covered if c not in top8],) * 2,
       "A5M_long_excl_top5": ([c for c in all_ind if c not in top5], None), "A8M_long_excl_top8": ([c for c in all_ind if c not in top8], None),
       "B5M_both_excl_top5": ([c for c in all_ind if c not in top5],) * 2, "B8M_both_excl_top8": ([c for c in all_ind if c not in top8],) * 2}
repro = []
m5_series = {}
for name, v in VAR:
    Rv = D5["R_kf"] if v.get("kf") else R5
    Wv = L5.rank_weights(L5.mom_signal(Rv, v["L"], v["S"]), Rv, v["n"], cap=cap5 if v.get("cap") else None)
    b_ = L5.backtest(Wv, Rv, L5.BASE_COST)
    sh = L5.perf_block(b_, "full_1970")["sharpe_net"]; al = L5.alpha_fit(L5.sl(b_["net"], "full_1970"), X6_5)["alpha_ann"]
    repro.append({"member": f"M5 EW {name}", "check": "full-sample Sharpe and FF5+UMD alpha vs M5_industry_momentum_robustness.csv",
                  "abs_diff_sharpe": abs(sh - rob_tab.loc[name, "sharpe_full_1970"]),
                  "abs_diff_alpha": abs(al - rob_tab.loc[name, "alpha_full_1970"])})
    m5_series[f"EWvar:{name}"] = b_["net"]
for name, (lu, su) in SCR.items():
    Ws = L5.rank_weights(sig5, R5, 8, long_universe=lu, short_universe=su)
    b_ = L5.backtest(Ws, R5, L5.BASE_COST)
    sh = L5.perf_block(b_, "full_1970")["sharpe_net"]; al = L5.alpha_fit(L5.sl(b_["net"], "full_1970"), X6_5)["alpha_ann"]
    repro.append({"member": f"M5 screen {name}", "check": "full-sample Sharpe and FF5+UMD alpha vs M5_industry_momentum_carbon_screens.csv",
                  "abs_diff_sharpe": abs(sh - scr_tab.loc[name, "sharpe_full_1970"]),
                  "abs_diff_alpha": abs(al - scr_tab.loc[name, "alpha_full_1970"])})
    m5_series[f"screen:{name}"] = b_["net"]

# team rules and M1b real-time rules (S-post only)
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    TP = run_pipeline(bootstrap_reps=0)
team_rules = {k: v["net_return"] for k, v in TP["strategies"].items() if not k.startswith("Benchmark")}
always_short = TP["strategies"]["Benchmark | Always-short Brown"]["net_return"]
import helpers as H1b  # noqa: E402  (M1b helpers)
MEAS1b, MAC1b, FF3team = H1b.build_measures(), H1b.macro_fixed(), C.load_team()["ff3"]
led1b = pd.read_csv(Tn / "M1b_alt_signals_tests_ledger.csv").set_index("test_id")
m1b_series, m1b_zeroed = {}, {}
for m in ("MCCC", "CPU"):
    res = H1b.run_measure(MEAS1b[m], MAC1b, "realtime", "log1p")
    end = H1b.eval_end(MEAS1b[m])
    for code, sname in H1b.STRATS.items():
        df_ = res["strategies"][sname]
        st = H1b.window_stats(df_, "2010-01-31", "2022-07-31", FF3team)
        repro.append({"member": f"M1b {m} {code}", "check": "validation FF3 alpha t vs M1b ledger",
                      "abs_diff_t": abs(st["alpha_t_hac6"] - led1b.loc[f"Q1_{m}_realtime_{code}_validation_alpha", "statistic"])})
        s = df_["net_return"].copy()
        after = s.index > end
        m1b_zeroed[f"M1b:{m}:{code}"] = int(((s[after].fillna(0) != 0) & (s[after].index <= pd.Timestamp("2026-07-31"))).sum())
        s[after] = 0.0
        m1b_series[f"M1b:{m}:{code}"] = s
m6 = pd.read_csv(Tn / "M6_factor_timing_portfolio_returns.csv", index_col=0, parse_dates=True)
m6rot = pd.read_csv(Tn / "M6_factor_timing_rotation_returns.csv", index_col=0, parse_dates=True)
m6_cols = [c for c in m6.columns if c.endswith(":net") and c.split(":")[1] in
           ("timing_ridgecv", "timing_ols_lambda0", "timing_combination", "lmn_sign", "lmn_raw")]
m6_series = {f"M6:{c[:-4]}": m6[c] for c in m6_cols}
m6_series["M6:rotation_ridge"] = m6rot["rotation_ridge"]
REP = pd.DataFrame(repro)
REP["max_abs_diff"] = REP[[c for c in REP.columns if c.startswith("abs_diff")]].max(axis=1)
REP["passes_1e-6"] = REP["max_abs_diff"] <= 1e-6
save(REP, "search_reproduction")
assert REP["passes_1e-6"].all(), "a regenerated member does not reproduce its saved table row:\n" + REP.to_string()
led("C4_reproduction", QS, "regenerated members reproducing their saved statistic to 1e-6", int(REP["passes_1e-6"].sum()), np.nan,
    len(REP), "robustness", f"largest absolute difference {REP.max_abs_diff.max():.2e}; M1b returns after eval_end set to zero: "
    + ", ".join(f"{k.split(':', 1)[1]} {v}" for k, v in m1b_zeroed.items() if v), family="S")


def group_of(name):
    return name.split(":")[0]


full_members = {**{f"opt:{c}": opt[c] for c in opt.columns}, "EW:primary": ew["net"], **m5_series,
                **{f"GB:{c}": gb[c] for c in gb.columns if c != "epa5_minus_team5"}}
post_members = {**full_members, **{f"team:{k}": v for k, v in team_rules.items()}, **m1b_series, **m6_series}
GROUP_LABEL = {"opt": "M5 optimizer paths", "EW": "M5 EW book", "EWvar": "M5 EW variants", "screen": "M5 carbon screens",
               "GB": "M4 green-minus-brown", "team": "Team rules", "M1b": "M1b MCCC/CPU rules", "M6": "M6 timing"}


def family_frame(members: dict, w: str) -> pd.DataFrame:
    a, b = WIN[w]
    Y = pd.DataFrame({k: v.loc[a:b] for k, v in members.items()})
    assert len(Y) == WIN_N[w], (w, len(Y))
    bad = Y.columns[Y.isna().any()]
    assert not len(bad), f"members without a return in every month of {w}: {list(bad)}"
    return Y


SF = {"S-full": family_frame(full_members, "full"), "S-post": family_frame(post_members, "post2010")}
assert SF["S-full"].shape[1] == 58 and SF["S-post"].shape[1] == 89, {k: v.shape for k, v in SF.items()}
log(f"  S-full {SF['S-full'].shape}, S-post {SF['S-post'].shape}; reproduction max diff {REP.max_abs_diff.max():.1e}")

log("check 4: bootstrap (Romano-Wolf, SPA)")
search_rows, search_sum, FIT, RESID, BOOTMAX = [], [], {}, {}, {}
for fam, Y in SF.items():
    Fm = X6.loc[Y.index]
    fits = {c: fit(Y[c], Fm) for c in Y.columns}
    FIT[fam] = fits
    RESID[fam] = pd.DataFrame({c: fits[c]["resid"] for c in Y.columns})
    t_hat = np.array([fits[c]["t"] for c in Y.columns])
    a_m = np.array([fits[c]["alpha_m"] for c in Y.columns])
    s_m = np.array([fits[c]["se_m"] for c in Y.columns])
    T_, M_ = Y.shape
    X = np.column_stack([np.ones(T_), Fm.values])
    Yd = Y.values - a_m[None, :]
    rng = np.random.default_rng(SEED)
    idx = stationary_idx(T_, B, rng)
    tau = np.empty((B, M_))
    for bb in range(B):
        ii = idx[bb]; Xb = X[ii]
        tau[bb] = np.linalg.solve(Xb.T @ Xb, Xb.T @ Yd[ii])[0] / s_m
    order = np.argsort(-t_hat, kind="mergesort")
    ts, taus = t_hat[order], tau[:, order]
    suff = np.maximum.accumulate(taus[:, ::-1], axis=1)[:, ::-1]
    ptil = (1 + (suff >= ts[None, :]).sum(axis=0)) / (B + 1)
    padj_sorted = np.maximum.accumulate(ptil)
    padj = np.empty(M_); padj[order] = padj_sorted
    thr = np.sqrt(2 * np.log(np.log(T_)))
    T_spa = max(0.0, t_hat.max())
    Tb = np.maximum(0, (tau + (t_hat * (t_hat < -thr))[None, :]).max(axis=1))
    p_spa = (1 + (Tb >= T_spa).sum()) / (B + 1)
    maxtau = tau.max(axis=1)
    BOOTMAX[fam] = maxtau
    crit95 = float(np.quantile(maxtau, 0.95))
    ny, lj, _ = nyholt_liji(RESID[fam])
    ibest = int(np.argmax(t_hat)); bestname = Y.columns[ibest]
    p1b = fits[bestname]["p1"]
    sidak = np.log(0.95) / np.log(1 - p1b)
    for j, c in enumerate(Y.columns):
        ff_ = fits[c]
        search_rows.append({"family": fam, "member": c, "group": GROUP_LABEL[group_of(c)], "n": ff_["n"], "alpha": ff_["alpha"],
                            "se": ff_["se"], "t": ff_["t"], "p1": ff_["p1"], "rw_adj_p": padj[j], "rw_pass": padj[j] <= 0.05,
                            "ar": ff_["ar"], "resid_vol": ff_["resid_vol"]})
        led(f"C4_{fam}_{c}", QS, f"FF5+UMD alpha NW(6) t, {fam} member", ff_["t"], ff_["p2"], ff_["n"], "robustness",
            f"alpha {ff_['alpha']:.4f}/yr; Romano-Wolf adjusted p {padj[j]:.4f}", p1=ff_["p1"], alternative="greater", family=fam)
    srow = {"family": fam, "M": M_, "n_months": T_, "best_member": bestname, "best_t": t_hat[ibest], "best_p1": p1b,
            "best_rw_adj_p": padj[ibest], "rw_survivors": int((padj <= 0.05).sum()), "spa_stat": T_spa, "spa_p": p_spa,
            "maxt_crit95": crit95, "spa_threshold": thr, "nyholt_meff": ny, "liji_meff": lj, "sidak_count_best": sidak,
            "second_member": Y.columns[order[1]], "second_t": t_hat[order[1]]}
    search_sum.append(srow)
    led(f"C4_{fam}_spa", QS, "Hansen SPA (consistent) p-value", T_spa, np.nan, T_, "robustness",
        f"M = {M_}; threshold sqrt(2 ln ln n) = {thr:.3f}; B = {B}, stationary bootstrap block 12, seed {SEED}", p1=p_spa,
        alternative="greater", family=fam)
    led(f"C4_{fam}_maxt_crit", QS, "95th percentile of the bootstrap max-t", crit95, np.nan, T_, "robustness",
        f"best member {bestname} t {t_hat[ibest]:.3f}, RW adjusted p {padj[ibest]:.4f}", family=fam)
    led(f"C4_{fam}_meff", QS, "Nyholt effective number of tests (FF5+UMD residuals)", ny, np.nan, T_, "robustness",
        f"Li-Ji {lj:.2f}; M = {M_}", family=fam)
    led(f"C4_{fam}_sidak", QS, "Sidak count at which the best t stops being significant at 5%", sidak, np.nan, T_, "robustness",
        f"best {bestname}, one-sided p {p1b:.5f}", family=fam)
    log(f"  {fam}: best {bestname} t {t_hat[ibest]:.3f} RW p {padj[ibest]:.4f} SPA p {p_spa:.4f} crit {crit95:.3f} "
        f"Nyholt {ny:.2f} Li-Ji {lj:.2f} Sidak {sidak:.1f}")
SM = save(pd.DataFrame(search_rows), "search_members")
SS = save(pd.DataFrame(search_sum), "search_summary")
tex(pd.DataFrame({"Family": SS.family, "Members": SS.M.astype(str), "Months": SS.n_months.astype(str),
                  "Best member": SS.best_member.str.replace("opt:", "optimizer ").str.replace("_", " "),
                  "Best t": SS.best_t.map(f), "RW adj. p": SS.best_rw_adj_p.map(lambda v: f(v, 3)),
                  "RW survivors": SS.rw_survivors.astype(str), "SPA p": SS.spa_p.map(lambda v: f(v, 3)),
                  "Max-t 95%": SS.maxt_crit95.map(f), "Nyholt": SS.nyholt_meff.map(lambda v: f(v, 1)),
                  "Li-Ji": SS.liji_meff.map(lambda v: f(v, 1)), "Sidak N": SS.sidak_count_best.map(lambda v: f(v, 0))}),
    "search_summary", "Search-adjusted tests of the best FF5+UMD alpha: Romano--Wolf stepdown and Hansen's SPA over every "
    "series that could have been presented as the strategy (spec check 4).", "tab:m7_search",
    "lrrlrrrrrrrr", wide=True,
    notes=(f"Stationary bootstrap, mean block 12, B = {B:,}, seed {SEED}; returns demeaned by each member's alpha, factors "
           "resampled jointly. Nyholt and Li--Ji effective numbers of tests from FF5+UMD residual correlations. Sidak N: number "
           "of independent tests at which the best one-sided p stops being significant at 5\\%. M2's grid is not in either "
           "family (its series are not saved), which makes both tests slightly lenient."))
top = SM.sort_values(["family", "t"], ascending=[True, False]).groupby("family").head(8)
tex(pd.DataFrame({"Family": top.family, "Member": top.member.str.replace("_", " "), "Alpha %": top.alpha.map(pc),
                  "t": top.t.map(f), "One-sided p": top.p1.map(lambda v: f(v, 4)), "RW adj. p": top.rw_adj_p.map(lambda v: f(v, 3))}),
    "search_top", "The eight largest alpha t-statistics in each search family with Romano--Wolf adjusted p-values.",
    "tab:m7_search_top", "llrrrr")

# ===================================================================================================== CHECK 5
log("check 5: deflated appraisal ratio")
QD = "C5 deflated appraisal ratio (Bailey and Lopez de Prado 2014)"
CAND = {"book (X_unc)": "opt:X_unc", "EPA 5v5 spread": "GB:epa5"}
dsr_rows, dsr_sens = [], []
for fam, w in (("S-full", "full"), ("S-post", "post2010")):
    Y = SF[fam]; Fm = X6.loc[Y.index]; T_ = len(Y)
    ny, lj, Rm = nyholt_liji(RESID[fam])
    M_ = Y.shape[1]
    K = int(round(ny))
    Dm = np.sqrt(np.clip(0.5 * (1 - Rm), 0, None)); np.fill_diagonal(Dm, 0)
    Z = linkage(squareform(Dm, checks=False), method="average")
    cl = fcluster(Z, t=K, criterion="maxclust")
    clus = {k: list(Y.columns[cl == k]) for k in sorted(set(cl))}
    cser = pd.DataFrame({k: Y[v].mean(axis=1) for k, v in clus.items()})
    car = np.array([fit(cser[k], Fm)["ar_m"] for k in cser.columns])
    csr = np.array([cser[k].mean() / cser[k].std(ddof=1) for k in cser.columns])
    V_cl = float(np.var(car, ddof=1)); V = max(1 / (T_ - 1), V_cl)
    V_cl_raw = float(np.var(csr, ddof=1)); V_raw = max(1 / (T_ - 1), V_cl_raw)
    save(pd.DataFrame([{"family": fam, "cluster": k, "n_members": len(v), "members": "; ".join(v),
                        "cluster_ar_monthly": car[i], "cluster_sr_monthly": csr[i]} for i, (k, v) in enumerate(clus.items())]),
         f"dsr_clusters_{fam.replace('-', '_').lower()}")
    for cname, col in CAND.items():
        ft = FIT[fam][col]
        y = Y[col]
        base = dict(candidate=cname, member=col, family=fam, window=w, T=T_, alpha=ft["alpha"], t_NW=ft["t"], t_OLS=ft["t_ols"],
                    AR_monthly=ft["ar_m"], AR_annual=ft["ar"], resid_skew=ft["skew"], resid_kurt=ft["kurt"], M=M_,
                    N_nyholt=ny, N_liji=lj, K=K, V_cl=V_cl, V=V, V_floor=1 / (T_ - 1))
        main = dsr(ft["ar_m"], T_, ft["skew"], ft["kurt"], ny, V, ft["t"], ft["t_ols"])
        psr0 = dsr(ft["ar_m"], T_, ft["skew"], ft["kurt"], 1, V, ft["t"], ft["t_ols"])
        row = {**base, "E_N": emax(ny), **main, "PSR0_iid": psr0["DSR_iid"], "PSR0_NW": psr0["DSR_NW"], "PSR0_gov": psr0["DSR_gov"],
               "pass_0.95": main["DSR_gov"] >= 0.95}
        # sensitivities
        for lab_, N_, V_ in (("N = Li-Ji", lj, V), ("N = raw M", M_, V), ("V = 1/(T-1), N = Nyholt", ny, 1 / (T_ - 1)),
                             ("N = Li-Ji, V = 1/(T-1)", lj, 1 / (T_ - 1)), ("N = raw M, V = 1/(T-1)", M_, 1 / (T_ - 1))):
            s_ = dsr(ft["ar_m"], T_, ft["skew"], ft["kurt"], N_, V_, ft["t"], ft["t_ols"])
            dsr_sens.append({"candidate": cname, "family": fam, "variant": lab_, "N": N_, "V": V_, **s_})
            row[f"DSR_gov[{lab_}]"] = s_["DSR_gov"]
        # smallest N at which the governing DSR drops below 0.95 with V fixed
        Ngrid = np.arange(1, 501)
        ok = [n_ for n_ in Ngrid if dsr(ft["ar_m"], T_, ft["skew"], ft["kurt"], n_, V, ft["t"], ft["t_ols"])["DSR_gov"] >= 0.95]
        row["max_N_pass"] = int(max(ok)) if ok else 0
        # context: raw-Sharpe DSR and Lo's annualized Sharpe
        srm = y.mean() / y.std(ddof=1)
        g3r, g4r = float(stats.skew(y, bias=False)), float(stats.kurtosis(y, fisher=False, bias=False))
        tnw_m, _ = nw_mean_t(y)
        raw = dsr(srm, T_, g3r, g4r, ny, V_raw, tnw_m, srm * np.sqrt(T_))
        eta = lo_eta(y)
        row.update({"raw_SR_annual": np.sqrt(12) * srm, "raw_skew": g3r, "raw_kurt": g4r, "raw_V": V_raw,
                    "raw_DSR_iid": raw["DSR_iid"], "raw_DSR_NW": raw["DSR_NW"], "raw_DSR_gov": raw["DSR_gov"],
                    "lo_eta12": eta, "lo_SR_annual": eta * srm})
        dsr_rows.append(row)
        led(f"C5_{fam}_{col}_dsr", QD, "governing DSR of the monthly appraisal ratio (min of iid and NW-scaled)", main["DSR_gov"],
            np.nan, T_, "robustness", f"AR {ft['ar']:.3f}/yr; N_eff Nyholt {ny:.2f}; V {V:.5f}; SR0 {main['SR0']:.4f}; iid "
            f"{main['DSR_iid']:.3f}, NW {main['DSR_NW']:.3f}; pass bar 0.95", family=fam)
        led(f"C5_{fam}_{col}_psr0", QD, "PSR(0) of the monthly appraisal ratio, governing", psr0["DSR_gov"], np.nan, T_, "robustness",
            f"iid {psr0['DSR_iid']:.4f}, NW {psr0['DSR_NW']:.4f}", family=fam)
        for lab_ in ("N = Li-Ji", "N = raw M", "V = 1/(T-1), N = Nyholt", "N = Li-Ji, V = 1/(T-1)", "N = raw M, V = 1/(T-1)"):
            led(f"C5_{fam}_{col}_dsr_{lab_.replace(' ', '').replace(',', '_').replace('/', '')}", QD,
                f"governing DSR, sensitivity {lab_}", row[f"DSR_gov[{lab_}]"], np.nan, T_, "robustness", family=fam)
        led(f"C5_{fam}_{col}_max_N_pass", QD, "largest N at which the governing DSR is at least 0.95, V at its step-3 value",
            row["max_N_pass"], np.nan, T_, "robustness", f"V {V:.5f}; grid N = 1 to 500; 0 means no N passes", family=fam)
        led(f"C5_{fam}_{col}_rawdsr", QD, "raw-Sharpe DSR, governing (context only)", raw["DSR_gov"], np.nan, T_, "descriptive",
            f"annual SR {np.sqrt(12) * srm:.3f}; Lo-adjusted annual SR {eta * srm:.3f}", family=fam)
    log(f"  {fam}: Nyholt {ny:.2f} Li-Ji {lj:.2f} K {K} V_cl {V_cl:.5f} floor {1 / (T_ - 1):.5f}")
DSRT = save(pd.DataFrame(dsr_rows), "dsr")
save(pd.DataFrame(dsr_sens), "dsr_sensitivity")
dsr_pass = DSRT.groupby("candidate")["pass_0.95"].all()
tex(pd.DataFrame({"Candidate": DSRT.candidate, "Window": DSRT.window.map({"full": "1970-2026", "post2010": "2010-2026"}),
                  "AR": DSRT.AR_annual.map(f), "t NW": DSRT.t_NW.map(f), "N Nyholt": DSRT.N_nyholt.map(lambda v: f(v, 1)),
                  "V x1000": (1000 * DSRT.V).map(lambda v: f(v, 2)), "SR0 x sqrt12": (np.sqrt(12) * DSRT.SR0).map(f),
                  "DSR iid": DSRT.DSR_iid.map(lambda v: f(v, 3)), "DSR NW": DSRT.DSR_NW.map(lambda v: f(v, 3)),
                  "DSR (gov.)": DSRT.DSR_gov.map(lambda v: f(v, 3)), "Li-Ji": DSRT["DSR_gov[N = Li-Ji]"].map(lambda v: f(v, 3)),
                  "Raw M": DSRT["DSR_gov[N = raw M]"].map(lambda v: f(v, 3)),
                  "V floor": DSRT["DSR_gov[V = 1/(T-1), N = Nyholt]"].map(lambda v: f(v, 3)), "Max N": DSRT.max_N_pass.astype(str)}),
    "dsr", "Deflated appraisal ratio of the two candidates (spec check 5). Pass bar: governing DSR of at least 0.95 in both windows.",
    "tab:m7_dsr", "llrrrrrrrrrrrr", wide=True,
    notes=("AR: annualized FF5+UMD appraisal ratio. N: Nyholt effective number of trials from the family's residual correlations "
           "(S-full, 58 series; S-post, 89). V: cross-trial variance of the monthly AR over K = round(N) clusters, floored at "
           "1/(T-1). SR0: expected maximum AR under the null. Governing DSR: the smaller of the iid DSR and the DSR with z scaled by "
           "t(NW)/t(OLS). The last four columns: governing DSR with N = Li--Ji, N = raw M, V = 1/(T-1); and the largest N that "
           "still passes at the step-3 V."))

# ===================================================================================================== CHECK 6
log("check 6: holdout reading in appraisal-ratio units")
QH = "C6 holdout reading, 2022-08 to 2026-07"
hold_series = {"optimizer book (X_unc)": opt["X_unc"], "EW momentum book": ew["net"], "EPA 5v5 spread": gb["epa5"],
               **{f"team: {k}": v for k, v in team_rules.items()}, "reference: Always-short Brown": always_short}
hrows = []
for nm, s in hold_series.items():
    for model, Xf in (("FF5+UMD", X6), ("FF3", KF3[F3])):
        if model == "FF3" and not nm.startswith("team"):
            continue
        y = wsl(s, "holdout")
        ft = fit(y, Xf.loc[y.index])
        tc, tp = stats.t.ppf(0.95, ft["df"]), stats.t.ppf(0.80, ft["df"])
        Lo, Up = ft["alpha"] - tc * ft["se"], ft["alpha"] + tc * ft["se"]
        delta = 0.25 * ft["resid_vol"]
        if Lo > 0 and Up < delta:
            reading = "positive but below the worthwhile margin"
        elif Lo > 0:
            reading = "confirms a positive alpha"
        elif Up < delta:
            reading = "rejects a worthwhile alpha"
        else:
            reading = "inconclusive"
        hrows.append({"series": nm, "model": model, "n": ft["n"], "df": ft["df"], "alpha": ft["alpha"], "se": ft["se"], "t": ft["t"],
                      "t_crit_90": tc, "ci90_lo": Lo, "ci90_hi": Up, "resid_vol": ft["resid_vol"], "delta": delta,
                      "mde_80": (tc + tp) * ft["se"], "reading": reading})
        led(f"C6_{nm.replace(' ', '_').replace(':', '').replace('|', '')}_{model}", QH, f"holdout {model} alpha NW(6) t",
            ft["t"], ft["p2"], ft["n"], "robustness" if not nm.startswith("reference") else "descriptive",
            f"alpha {ft['alpha']:.4f}; 90% CI [{Lo:.4f}, {Up:.4f}]; delta {delta:.4f}; MDE80 {(tc + tp) * ft['se']:.4f}; {reading}",
            p1=ft["p1"], alternative="greater", family="C6")
HO = save(pd.DataFrame(hrows), "holdout_reading")
tex(pd.DataFrame({"Series": HO.series.str.replace("team: ", "").str.replace("reference: ", "Ref.: "), "Model": HO.model,
                  "Alpha %": HO.alpha.map(pc), "SE %": HO.se.map(pc), "90% CI low": HO.ci90_lo.map(pc),
                  "90% CI high": HO.ci90_hi.map(pc), "Margin delta %": HO.delta.map(pc), "MDE80 %": HO.mde_80.map(pc),
                  "Reading": HO.reading}),
    "holdout_reading", "Holdout (2022-08 to 2026-07, 48 months) alphas read against a margin of a quarter of an appraisal ratio "
    "(spec check 6).", "tab:m7_holdout", "llrrrrrrl", wide=True,
    notes=("Alpha: annualized intercept, NW(6) standard error. 90\\% interval from t(n-k). Margin delta = 0.25 times the annualized "
           "residual volatility of the same regression. MDE80: minimum detectable alpha at 80\\% power. Reading, first match: "
           "L > 0 and U < delta, positive but below the margin; L > 0, confirms; U < delta, rejects a worthwhile alpha; otherwise "
           "inconclusive."))

# ===================================================================================================== CHECK 8
log("check 8: cost stress on the book")
QK = "C8 cost stress on the optimizer book"
paths = pd.read_csv(Tn / "M5_industry_momentum_optimizer_paths_monthly.csv", header=[0, 1], index_col=0, skiprows=[2], parse_dates=True)
g_, to_ = paths[("X_unc", "gross")].astype(float), paths[("X_unc", "turnover")].astype(float)
assert (g_ - 0.001 * to_ - opt["X_unc"]).abs().max() < 1e-12
krows = []
for w in ("full", "post2010", "holdout"):
    Fm = X6.loc[wsl(g_, w).index]
    a_g, a_t = fit(wsl(g_, w), Fm), fit(wsl(to_, w), Fm)
    cstar = a_g["alpha_m"] / a_t["alpha_m"] if a_g["alpha_m"] > 0 else np.nan
    for c in (0, 10, 25, 50):
        ft = fit(wsl(g_ - c / 1e4 * to_, w), Fm)
        krows.append({"window": w, "cost_bp": c, "n": ft["n"], "alpha": ft["alpha"], "t": ft["t"], "p1": ft["p1"],
                      "turnover_ann": 12 * wsl(to_, w).mean(), "breakeven_bp": 1e4 * cstar,
                      "alpha_gross": a_g["alpha"], "alpha_turnover_monthly": a_t["alpha_m"]})
        led(f"C8_{w}_{c}bp", QK, f"FF5+UMD alpha NW(6) t of net returns at {c} bp", ft["t"], ft["p2"], ft["n"], "robustness",
            f"alpha {ft['alpha']:.4f}/yr; holdings fixed at the 10 bp solution", p1=ft["p1"], alternative="greater", family="C8")
    led(f"C8_{w}_breakeven", QK, "break-even cost c* = alpha(gross)/alpha(turnover), bp", 1e4 * cstar if np.isfinite(cstar) else np.nan,
        np.nan, a_g["n"], "robustness", f"alpha(gross) {a_g['alpha']:.4f}/yr" + ("" if np.isfinite(cstar) else "; gross alpha not positive"),
        family="C8")
KS = save(pd.DataFrame(krows), "cost_stress")
k25 = KS[(KS.window == "full") & (KS.cost_bp == 25)].iloc[0]
cost_pass = bool(k25.alpha > 0)
led("C8_pass", QK, "pass bar: full-sample alpha above zero at 25 bp", float(cost_pass), np.nan, int(k25.n), "robustness",
    f"alpha at 25 bp {k25.alpha:.4f}/yr (t {k25.t:.2f}); {'PASS' if cost_pass else 'FAIL'}", family="C8")
kp = KS.pivot_table(index="cost_bp", columns="window", values=["alpha", "t"])
tex(pd.DataFrame({"Cost bp": kp.index.astype(str),
                  **{f"{lab_} alpha %": kp[("alpha", w)].map(pc) for w, lab_ in (("full", "Full"), ("post2010", "Post-2010"), ("holdout", "Holdout"))},
                  **{f"{lab_} t": kp[("t", w)].map(f) for w, lab_ in (("full", "Full"), ("post2010", "Post-2010"), ("holdout", "Holdout"))}}),
    "cost_stress", "Cost stress on the optimizer book (spec check 8): FF5+UMD alpha of gross returns less c times turnover, "
    "holdings fixed.", "tab:m7_cost",
    notes=(f"Break-even cost: {KS[KS.window == 'full'].breakeven_bp.iloc[0]:.0f} bp (full), "
           f"{KS[KS.window == 'post2010'].breakeven_bp.iloc[0]:.0f} bp (post-2010); the holdout gross alpha is "
           f"{'negative' if KS[KS.window == 'holdout'].alpha_gross.iloc[0] <= 0 else 'positive'}. Annual turnover "
           f"{KS[KS.window == 'full'].turnover_ann.iloc[0]:.2f} (full). Pass bar: full-sample alpha above zero at 25 bp: "
           f"{'PASS' if cost_pass else 'FAIL'}."))

# ===================================================================================================== CHECK 9
log("check 9: descriptive and exploratory rows")
QX = "C9 descriptive and exploratory rows"
bk = opt["X_unc"]
wealth = (1 + bk).cumprod(); ddser = wealth / wealth.cummax() - 1
roll3 = (1 + bk).rolling(3).apply(np.prod, raw=True) - 1
crash = {"worst_month": bk.min(), "worst_month_date": bk.idxmin().strftime("%Y-%m"), "mar_may_2009": float((1 + bk.loc["2009-03-31":"2009-05-31"]).prod() - 1),
         "worst_3m": roll3.min(), "worst_3m_end": roll3.idxmin().strftime("%Y-%m"), "max_dd": ddser.min(),
         "max_dd_trough": ddser.idxmin().strftime("%Y-%m")}
for k_, v in crash.items():
    if not isinstance(v, str):
        led(f"C9_book_crash_{k_}", QX, f"book crash profile after 1970: {k_}", v, np.nan, len(bk), "descriptive",
            f"worst month {crash['worst_month_date']}; worst 3m ends {crash['worst_3m_end']}; max DD trough {crash['max_dd_trough']}",
            family="C9")
att = pd.read_csv(ROOT / "data" / "derived" / "attention_measures.csv", parse_dates=["date"]).set_index("date")
yE = wsl(gb["epa5"], "post2010")
ex_rows = []
specs = [("FF5+UMD, same sample", C6, []), ("FF5+UMD + MCCC shock", C6, ["MCCC_shock"]),
         ("FF5+UMD + MCCC shock lag 1", C6, ["MCCC_shock_l1"]), ("FF5+UMD + shock + lag 1", C6, ["MCCC_shock", "MCCC_shock_l1"]),
         ("FF5+UMD + MCCC transition shock", C6, ["MCCC_transition_shock"]), ("FF5+UMD + CPU shock", C6, ["CPU_shock"]),
         ("FF3 + MCCC shock", F3, ["MCCC_shock"])]
A_ = att[["MCCC_shock", "MCCC_transition_shock", "CPU_shock"]].copy()
A_["MCCC_shock_l1"] = att["MCCC_shock"].shift(1)
mccc_months = A_["MCCC_shock"].reindex(yE.index).dropna().index
for lab_, fc, extra in specs:
    Xd = X6[fc].join(A_[extra]) if extra else X6[fc]
    idx_ = mccc_months if lab_ == "FF5+UMD, same sample" else Xd.reindex(yE.index).dropna().index
    ft = fit(yE.loc[idx_], Xd.loc[idx_])
    row = {"spec": lab_, "n": ft["n"], "alpha": ft["alpha"], "t": ft["t"]}
    for c in extra:
        sd_c = float(Xd.loc[idx_, c].std(ddof=1))
        row[f"b_{c}"] = ft[f"b_{c}"]; row[f"t_{c}"] = ft[f"t_{c}"]; row[f"b_{c}_per_sd"] = ft[f"b_{c}"] * sd_c
    ex_rows.append(row)
    led(f"C9_epa_{lab_.replace(' ', '_').replace(',', '').replace('+', 'p')}", QX, f"EPA 5v5 post-2010 alpha NW(6) t, {lab_}",
        ft["t"], ft["p2"], ft["n"], "exploratory",
        f"alpha {ft['alpha']:.4f}/yr" + "".join(f"; b_{c} {row[f'b_{c}_per_sd']:.5f} per sd a month (t {ft[f't_{c}']:.2f})" for c in extra) +
        "; not a pass test (seen before the spec)", p1=ft["p1"], alternative="greater", family="C9")
EX = save(pd.DataFrame(ex_rows), "epa_shock_controls")
# data provenance (ALFRED vintages saved by the exchange-3 fact-check)
CO = ROOT / "exchange" / "03_robustness_design" / "checks" / "out"


def fred_csv(p):
    d = pd.read_csv(p); d.columns = ["date", "v"]; d["date"] = pd.to_datetime(d["date"])
    return pd.to_numeric(d.set_index("date")["v"], errors="coerce")


emv_now = fred_csv(C.RAW / "fred_EMVENRGYENVREG.csv")
prov = []
for vint in ("2024-06-15", "2022-09-15"):
    old = fred_csv(CO / f"alfred_EMVENRGYENVREG_vintage_{vint}.csv")
    j = pd.concat([old.rename("old"), emv_now.rename("now")], axis=1).dropna()
    diff = j[(j.old - j.now).abs() > 1e-9]
    prov.append({"item": f"EMVENRGYENVREG vintage {vint} vs current file", "months_compared": len(j), "months_differing": len(diff),
                 "differing": "; ".join(f"{d:%Y-%m} {r.old:.5f} vs {r.now:.5f}" for d, r in diff.iterrows())})
cpi_v = fred_csv(CO / "alfred_CPIAUCSL_vintage_2025-12-20.csv")
cpi_now = fred_csv(C.RAW / "fred_CPIAUCSL.csv")
prov.append({"item": "CPIAUCSL vintage 2025-12-20: 2025-10 value", "months_compared": int(cpi_v.notna().sum()),
             "months_differing": int(pd.isna(cpi_v.get(pd.Timestamp("2025-10-01")))),
             "differing": f"2025-10 missing in vintage: {pd.isna(cpi_v.get(pd.Timestamp('2025-10-01')))}; missing in current file: "
                          f"{pd.isna(cpi_now.get(pd.Timestamp('2025-10-01')))}"})
emf = pd.read_csv(C.TEAM_DATA / "emissions_ff_industry.csv")
prov.append({"item": "team emissions_ff_industry.csv", "months_compared": len(emf), "months_differing": np.nan,
             "differing": f"columns {list(emf.columns)}; no source, units, scope or date field"})
PRV = save(pd.DataFrame(prov), "data_provenance")
for i, r in PRV.iterrows():
    led(f"C9_provenance_{i}", QX, r["item"], r["months_differing"] if np.isfinite(r["months_differing"]) else np.nan, np.nan,
        r["months_compared"], "descriptive", str(r["differing"])[:300], family="C9")


# ===================================================================================================== CHECK 7
def book_path(form_dates, fac_frame, b=1e3):
    pre = OP.precompute(R5, fac_frame, sig5, covered, cm5["X"], form_dates)
    out, Hh = OP.run_path(pre, R5, cm5["X"], b, kappa=L5.BASE_COST, cost=L5.BASE_COST)
    return out, Hh, pre


def realized_ic(pre):
    rows = []
    pos = {d: i for i, d in enumerate(R5.index)}
    for mon in pre["months"]:
        z = pd.Series(mon["z"]); i = pos[mon["t"]]
        r = R5.iloc[i + 1][z.index]
        rows.append((R5.index[i + 1], float(stats.spearmanr(z.values, r.values)[0])))
    return pd.Series(dict(rows)).rename("rank_ic")


def frozen_stats(out: pd.DataFrame, out_b: pd.DataFrame, pre, halves, s1_window):
    """All check 7 statistics for a book path. Used unchanged on the dry-run window (development test) and on 1931-1969."""
    net = out["net"]
    Xw = X4.loc[net.index]
    assert not Xw.isna().any().any()
    main = fit(net, Xw)
    h = [fit(net.loc[a:b], Xw.loc[a:b]) for a, b in halves]
    tc = stats.t.ppf(0.95, main["df"])
    U = main["alpha"] + tc * main["se"]
    delta = 0.25 * main["resid_vol"]
    passed = (main["alpha"] > 0) and (main["t"] >= 2.00) and all(x["alpha"] > 0 for x in h)
    verdict = "PASS" if passed else ("REJECT" if U < delta else "INCONCLUSIVE")
    s1y = net.loc[s1_window[0]:s1_window[1]]
    s1 = fit(s1y, X6.loc[s1y.index])
    pb = L5.paired_boot(out_b["net"], net, Xw, block=12, B=B, seed=SEED)
    w_ = (1 + net).cumprod(); dd = w_ / w_.cummax() - 1
    r3 = (1 + net).rolling(3).apply(np.prod, raw=True) - 1
    s4 = fit(out["gross"] - 0.0025 * out["turnover"], Xw)
    ic = realized_ic(pre)
    ic_t, ic_p = nw_mean_t(ic)
    ic_t05, _ = nw_mean_t(ic - 0.05)
    return {"n": main["n"], "df": main["df"], "alpha": main["alpha"], "se": main["se"], "t": main["t"], "p1": main["p1"],
            "p2": main["p2"], "t_crit_90": tc, "U": U, "L": main["alpha"] - tc * main["se"], "resid_vol": main["resid_vol"],
            "delta": delta, "b_UMD": main["b_UMD"], "t_UMD": main["t_UMD"], "b_Mkt": main["b_Mkt-RF"], "r2": main["r2"],
            "ar": main["ar"],
            "h1_window": f"{halves[0][0][:7]} to {halves[0][1][:7]}", "h1_n": h[0]["n"], "h1_alpha": h[0]["alpha"], "h1_t": h[0]["t"],
            "h2_window": f"{halves[1][0][:7]} to {halves[1][1][:7]}", "h2_n": h[1]["n"], "h2_alpha": h[1]["alpha"], "h2_t": h[1]["t"],
            "verdict": verdict,
            "S1_n": s1["n"], "S1_alpha": s1["alpha"], "S1_se": s1["se"], "S1_t": s1["t"],
            "S2_d_ir": pb["d_ir"], "S2_d_ir_lo": pb["d_ir_lo"], "S2_d_ir_hi": pb["d_ir_hi"], "S2_p": pb["p_d_ir"],
            "S2_d_alpha": pb["d_alpha"], "S2_d_alpha_lo": pb["d_alpha_lo"], "S2_d_alpha_hi": pb["d_alpha_hi"],
            "S2_no_carbon_cost": bool(pb["d_ir_lo"] > -0.10), "S2_fallback_months": int(out_b["fallback"].sum()),
            "S2_binding_share": float(out_b["binding"].mean()),
            "S3_worst_month": float(net.min()), "S3_worst_month_date": net.idxmin().strftime("%Y-%m"),
            "S3_worst_3m": float(r3.min()), "S3_worst_3m_end": r3.idxmin().strftime("%Y-%m"), "S3_max_dd": float(dd.min()),
            "S3_max_dd_trough": dd.idxmin().strftime("%Y-%m"),
            "S4_alpha_25bp": s4["alpha"], "S4_t_25bp": s4["t"],
            "S5_ic_mean": float(ic.mean()), "S5_ic_t": ic_t, "S5_ic_p": ic_p, "S5_ic_t_vs_0.05": ic_t05, "S5_n": len(ic),
            "net_ann": 12 * net.mean(), "vol_ann": np.sqrt(12) * net.std(ddof=1), "turnover_ann": 12 * out["turnover"].mean(),
            "n_elig_min": int(out["n_elig"].min()), "n_elig_max": int(out["n_elig"].max()),
            "inaccurate_months": int(out["inaccurate"].sum()), "fallback_months": int(out["fallback"].sum()),
            "first_month": net.index[0].strftime("%Y-%m"), "last_month": net.index[-1].strftime("%Y-%m")}


log("check 7: dry run")
QF = "C7 frozen 1931-1969 run of the optimizer book (pre-registered)"
f5_m5 = ff5_5                                           # M5's own factor frame
f3_frame = KF3[["Mkt-RF", "RF"]].loc[:L5.RET_END]
assert set(f3_frame.index) <= set(R5.index)
dry_dates = R5.index[(R5.index >= "1969-12-31") & (R5.index <= "1970-11-30")]
dry1, _, _ = book_path(dry_dates, f5_m5)
d1 = float((dry1["net"] - opt["X_unc"].loc[dry1.index]).abs().max())
dry2, _, _ = book_path(dry_dates, f3_frame)
d2 = float((dry2["net"] - opt["X_unc"].loc[dry2.index]).abs().max())
assert len(dry1) == 12 and dry1.index[0] == pd.Timestamp("1970-01-31") and dry1.index[-1] == pd.Timestamp("1970-12-31")
dry_ok = d1 <= 1e-8
led("C7_dryrun_m5_inputs", QF, "dry run: max |net - M5 X_unc|, 1970-01 to 1970-12, M5 factor inputs", d1, np.nan, 12,
    "robustness", f"must be <= 1e-8: {'OK' if dry_ok else 'FAILED'}", family="F")
led("C7_dryrun_ff3_inputs", QF, "dry run: max |net - M5 X_unc|, 1970-01 to 1970-12, FF3 Mkt-RF and RF inputs", d2, np.nan, 12,
    "robustness", "reported only; cannot change a choice", family="F")
log(f"  dry run: M5 inputs max diff {d1:.2e}; FF3 inputs max diff {d2:.2e}")
if not dry_ok:
    raise SystemExit("dry run failed to reproduce M5: frozen run not executed")

FROZEN = None
if SKIP_FROZEN:
    log("  M7_SKIP_FROZEN=1: frozen run skipped (development only); exercising frozen_stats on post-1970 months")
    tst_dates = R5.index[(R5.index >= "1969-12-31") & (R5.index <= "2008-05-31")]
    tz, _, pre_t = book_path(tst_dates, f3_frame, b=1e3)
    tzb, _, _ = book_path(tst_dates, f3_frame, b=-1.0)
    TST = frozen_stats(tz, tzb, pre_t, [("1970-01-31", "1989-03-31"), ("1989-04-30", "2008-06-30")], ("1995-01-31", "2001-06-30"))
    print(pd.Series(TST).to_string())
else:
    log("check 7: FROZEN RUN 1931-07 to 1969-12")
    fz_dates = R5.index[(R5.index >= "1931-06-30") & (R5.index <= "1969-11-30")]
    fz, Hfz, pre_fz = book_path(fz_dates, f3_frame, b=1e3)
    fzb, _, _ = book_path(fz_dates, f3_frame, b=-1.0)
    assert len(fz) == 462 and fz.index[0] == pd.Timestamp("1931-07-31") and fz.index[-1] == pd.Timestamp("1969-12-31")
    halves = [("1931-07-31", "1950-09-30"), ("1950-10-31", "1969-12-31")]
    FROZEN = frozen_stats(fz, fzb, pre_fz, halves, ("1963-07-31", "1969-12-31"))
    assert FROZEN["h1_n"] == 231 and FROZEN["h2_n"] == 231 and FROZEN["S1_n"] == 78
    ret_out = fz[["gross", "turnover", "cost", "net", "n_elig", "exante_te_ann", "inaccurate", "fallback"]].copy()
    ret_out["net_25bp"] = fz["gross"] - 0.0025 * fz["turnover"]
    ret_out["net_b-1"] = fzb["net"]
    ret_out.to_csv(FROZEN_RET_CSV)
    Hfz.to_csv(TABLES / "M7_frozen_pre1970_holdings.csv")
    rec = {k: (float(v) if isinstance(v, (float, np.floating)) else (int(v) if isinstance(v, (int, np.integer)) and not isinstance(v, bool)
                                                                        else v)) for k, v in FROZEN.items()}
    rec["net_sha256_1e12"] = _sha(np.round(fz["net"].values, 12).tobytes())
    if not FIRST_RUN.exists():
        rec["first_run_utc"] = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        FIRST_RUN.write_text(json.dumps(rec, indent=1, default=str))
        FROZEN["reproduces_first_run"] = True
        FROZEN["first_run_utc"] = rec["first_run_utc"]
    else:
        fr = json.loads(FIRST_RUN.read_text())
        same = fr["net_sha256_1e12"] == rec["net_sha256_1e12"] and fr["verdict"] == rec["verdict"] and abs(fr["t"] - rec["t"]) < 1e-9
        FROZEN["reproduces_first_run"] = bool(same)
        FROZEN["first_run_utc"] = fr.get("first_run_utc", "")
        if not same:
            log("  WARNING: the frozen run does not reproduce first_run_record.json")
    log(f"  frozen: alpha {FROZEN['alpha']:.4f} t {FROZEN['t']:.3f} p1 {FROZEN['p1']:.4f}; halves {FROZEN['h1_alpha']:.4f} / "
        f"{FROZEN['h2_alpha']:.4f}; U {FROZEN['U']:.4f} delta {FROZEN['delta']:.4f}: {FROZEN['verdict']}")
    FT = pd.DataFrame([FROZEN]).T.reset_index(); FT.columns = ["item", "value"]
    save(FT, "frozen_pre1970")
    led("C7_i_alpha_ff3umd", "C7 (i) frozen confirmatory test: FF3+UMD alpha of the optimizer book, 1931-07 to 1969-12",
        "FF3+UMD alpha NW(6) t, one-sided p from t(457)", FROZEN["t"], FROZEN["p2"], FROZEN["n"], "primary",
        f"alpha {FROZEN['alpha']:.4f}/yr (SE {FROZEN['se']:.4f}); pass needs t >= 2.00 and both halves > 0; verdict {FROZEN['verdict']}; "
        f"hashes in M7_preregistration_hash.csv", p1=FROZEN["p1"], alternative="greater", family="F")
    for hh in ("h1", "h2"):
        led(f"C7_ii_{hh}", QF, f"(ii) half {FROZEN[hh + '_window']}: FF3+UMD alpha NW(6) t", FROZEN[f"{hh}_t"], np.nan,
            FROZEN[f"{hh}_n"], "robustness", f"alpha {FROZEN[hh + '_alpha']:.4f}/yr; pass needs alpha > 0", family="F")
    led("C7_U_delta", QF, "U = alpha + t(0.95, 457) SE against delta = 0.25 residual vol", FROZEN["U"], np.nan, FROZEN["n"],
        "robustness", f"delta {FROZEN['delta']:.4f}; residual vol {FROZEN['resid_vol']:.4f}; L {FROZEN['L']:.4f}", family="F")
    led("C7_S1", QF, "S1: FF5+UMD alpha NW(6) t, 1963-07 to 1969-12", FROZEN["S1_t"], np.nan, FROZEN["S1_n"], "robustness",
        f"alpha {FROZEN['S1_alpha']:.4f}/yr, SE {FROZEN['S1_se']:.4f}; secondary, uninformative by design", family="F")
    led("C7_S2", QF, "S2: net IR difference, b = -1 book minus unconstrained, paired circular block bootstrap",
        FROZEN["S2_d_ir"], FROZEN["S2_p"], FROZEN["n"], "robustness",
        f"95% interval [{FROZEN['S2_d_ir_lo']:.3f}, {FROZEN['S2_d_ir_hi']:.3f}]; 'no carbon cost' only if lower bound > -0.10: "
        f"{FROZEN['S2_no_carbon_cost']}; FF3+UMD alpha difference {FROZEN['S2_d_alpha']:.4f}", family="F")
    for k_ in ("S3_worst_month", "S3_worst_3m", "S3_max_dd"):
        led(f"C7_{k_}", QF, f"S3 crash profile: {k_[3:]}", FROZEN[k_], np.nan, FROZEN["n"], "robustness",
            f"worst month {FROZEN['S3_worst_month_date']}; worst 3m ends {FROZEN['S3_worst_3m_end']}; trough {FROZEN['S3_max_dd_trough']}",
            family="F")
    led("C7_S4", QF, "S4: FF3+UMD alpha NW(6) t at 25 bp realized costs", FROZEN["S4_t_25bp"], np.nan, FROZEN["n"], "robustness",
        f"alpha {FROZEN['S4_alpha_25bp']:.4f}/yr", family="F")
    led("C7_S5", QF, "S5: mean realized rank IC of the 11-1 signal, NW(6) t", FROZEN["S5_ic_t"], FROZEN["S5_ic_p"], FROZEN["S5_n"],
        "robustness", f"mean IC {FROZEN['S5_ic_mean']:.4f} against assumed 0.05 (t vs 0.05 {FROZEN['S5_ic_t_vs_0.05']:.2f})", family="F")
    for k_ in ("net_ann", "vol_ann", "turnover_ann", "b_UMD", "t_UMD", "b_Mkt", "r2", "ar", "se", "L", "n_elig_min", "n_elig_max",
               "fallback_months", "inaccurate_months", "S2_fallback_months", "S2_binding_share", "S2_d_alpha", "S2_d_alpha_lo",
               "S2_d_alpha_hi", "S1_se"):
        led(f"C7_context_{k_}", QF, f"frozen run context: {k_}", FROZEN[k_], np.nan, FROZEN["n"], "descriptive",
            "reported, never part of the verdict", family="F")
    # difference of the two half-sample alphas, halves treated as independent (context for caveat 3; output only)
    _se1, _se2 = FROZEN["h1_alpha"] / FROZEN["h1_t"], FROZEN["h2_alpha"] / FROZEN["h2_t"]
    _td = (FROZEN["h1_alpha"] - FROZEN["h2_alpha"]) / np.sqrt(_se1 ** 2 + _se2 ** 2)
    led("C7_context_halves_diff_t", QF, "t of first-half minus second-half FF3+UMD alpha, halves treated as independent", _td,
        2 * stats.norm.sf(abs(_td)), FROZEN["n"], "descriptive",
        f"difference {FROZEN['h1_alpha'] - FROZEN['h2_alpha']:.4f}/yr; SEs {_se1:.4f}, {_se2:.4f} (alpha / t); normal p", family="F")

    fzrows = [("(i) FF3+UMD alpha, 1931-07 to 1969-12", pc(FROZEN["alpha"]), f(FROZEN["t"]), f(FROZEN["p1"], 3), str(FROZEN["n"])),
              (f"(ii) first half, {FROZEN['h1_window']}", pc(FROZEN["h1_alpha"]), f(FROZEN["h1_t"]), "", str(FROZEN["h1_n"])),
              (f"(ii) second half, {FROZEN['h2_window']}", pc(FROZEN["h2_alpha"]), f(FROZEN["h2_t"]), "", str(FROZEN["h2_n"])),
              ("S1 FF5+UMD alpha, 1963-07 to 1969-12", pc(FROZEN["S1_alpha"]), f(FROZEN["S1_t"]), "", str(FROZEN["S1_n"])),
              ("S4 FF3+UMD alpha at 25 bp", pc(FROZEN["S4_alpha_25bp"]), f(FROZEN["S4_t_25bp"]), "", str(FROZEN["n"])),
              ("S5 mean rank IC (t against 0)", f(FROZEN["S5_ic_mean"], 3), f(FROZEN["S5_ic_t"]), "", str(FROZEN["S5_n"]))]
    tex(pd.DataFrame(fzrows, columns=["Statistic", "Alpha % / value", "t", "One-sided p", "Months"]), "frozen_pre1970",
        "Frozen 1931--1969 run of the optimizer book (spec check 7, pre-registered).", "tab:m7_frozen", "lrrrr",
        notes=(f"Verdict: {FROZEN['verdict']}. 90\\% upper bound U = {pc(FROZEN['U'])}\\% against the margin delta = "
               f"{pc(FROZEN['delta'])}\\% (a quarter of the residual volatility of {pc(FROZEN['resid_vol'])}\\%). UMD beta "
               f"{f(FROZEN['b_UMD'])}. S2 (b = -1 minus unconstrained) net IR difference {f(FROZEN['S2_d_ir'], 3)}, 95\\% interval "
               f"[{f(FROZEN['S2_d_ir_lo'], 3)}, {f(FROZEN['S2_d_ir_hi'], 3)}]. S3: worst month {pc(FROZEN['S3_worst_month'], 1)}\\% "
               f"({FROZEN['S3_worst_month_date']}), worst three months {pc(FROZEN['S3_worst_3m'], 1)}\\%, maximum drawdown "
               f"{pc(FROZEN['S3_max_dd'], 1)}\\%. Hashes of the spec, optimizer.py and m5lib.py were written before the run."))

# post-1970 comparisons for the check 7 caveats (the book's saved X_unc returns; output only, no check 7 input changes)
_bk = wsl(opt["X_unc"], "full")
for _tag, _Xc, _desc in (("kf3umd", X4, "load_kf_ff3 Mkt-RF, SMB, HML plus UMD (the frozen test's factor files)"),
                         ("ff5file_ff3umd", FAC[["Mkt-RF", "SMB", "HML", "UMD"]], "Mkt-RF, SMB, HML of the FF5 file plus UMD")):
    _ft = fit(_bk, _Xc.loc[_bk.index])
    led(f"C7_context_post1970_{_tag}", QF, "post-1970 (1970-01 to 2026-07) FF3+UMD alpha NW(6) t of the book (comparison)",
        _ft["t"], _ft["p2"], _ft["n"], "descriptive", f"alpha {_ft['alpha']:.4f}/yr; {_desc}", p1=_ft["p1"],
        alternative="greater", family="F")
_bk7 = opt["X_unc"].loc["1970-01-31":"2009-12-31"]
_ft = fit(_bk7, X6.loc[_bk7.index])
led("C7_context_ff5umd_1970_2009", QF, "FF5+UMD alpha NW(6) t of the book, 1970-01 to 2009-12 (comparison)", _ft["t"], _ft["p2"],
    _ft["n"], "descriptive", f"alpha {_ft['alpha']:.4f}/yr; the 2010-2026 row is C4_S-post_opt:X_unc", p1=_ft["p1"],
    alternative="greater", family="F")

# family F Holm (M8 plus check 7 (i))
F_rows = [{"test": "M8_share_i_alpha_nw6", "t": F_M8.statistic, "p1": F_M8_p1}]
if FROZEN is not None:
    F_rows.append({"test": "M7_C7_i_alpha_ff3umd", "t": FROZEN["t"], "p1": FROZEN["p1"]})
FF = pd.DataFrame(F_rows)
FF["holm"] = holm_adj(FF.p1)
FF["survives"] = FF.holm <= 0.05
save(FF, "family_F")
for _, r in FF.iterrows():
    led(f"C2_F_{r.test}", "C2 family F: frozen, hash-verified tests, Holm one-sided", "Holm-adjusted one-sided p", r.holm, np.nan,
        len(FF), "robustness", f"raw one-sided p {r.p1:.4f}; t {r.t:.3f}", p1=r.p1, alternative="greater", family="F")

# ===================================================================================================== CHECK 10
log("check 10: verdict map")
SMi = SM.set_index(["family", "member"])
HOi = HO[HO.model == "FF5+UMD"].set_index("series")
DSi = DSRT.set_index(["candidate", "family"])
vrows = []
for cname, col, hname in (("Optimizer book (X_unc)", "opt:X_unc", "optimizer book (X_unc)"),
                          ("EPA 5v5 spread", "GB:epa5", "EPA 5v5 spread")):
    ckey = "book (X_unc)" if col == "opt:X_unc" else "EPA 5v5 spread"
    if col == "opt:X_unc":
        a_ok = (FROZEN is not None) and FROZEN["verdict"] == "PASS"
        a_txt = f"check 7 {FROZEN['verdict'] if FROZEN else 'not run'}"
    else:
        a_ok, a_txt = False, "no confirmatory test exists"
    rw_f, rw_p = SMi.loc[("S-full", col), "rw_adj_p"], SMi.loc[("S-post", col), "rw_adj_p"]
    b_ok = (rw_f <= 0.05) and (rw_p <= 0.05)
    d_f, d_p = DSi.loc[(ckey, "S-full"), "DSR_gov"], DSi.loc[(ckey, "S-post"), "DSR_gov"]
    c_ok = (d_f >= 0.95) and (d_p >= 0.95)
    h = HOi.loc[hname]
    d_ok = (h.alpha > 0) and (h.reading != "rejects a worthwhile alpha")
    verdict = "Implement" if (a_ok and b_ok and c_ok and d_ok) else ("Paper-trade (report verdict stays Do not implement)" if a_ok else "Do not implement")
    vrows.append({"candidate": cname, "a_confirmatory": a_ok, "a_detail": a_txt, "b_rw": b_ok, "rw_p_full": rw_f, "rw_p_post": rw_p,
                  "c_dsr": c_ok, "dsr_full": d_f, "dsr_post": d_p, "d_holdout": d_ok, "holdout_alpha": h.alpha,
                  "holdout_reading": h.reading, "verdict": verdict})
    led(f"C10_{col.split(':')[1]}", "C10 verdict map", f"verdict for {cname} (1 = implement)", float(verdict == "Implement"), np.nan,
        0, "robustness", f"(a) {a_ok} [{a_txt}]; (b) {b_ok} [RW p {rw_f:.3f} / {rw_p:.3f}]; (c) {c_ok} [DSR {d_f:.3f} / {d_p:.3f}]; "
        f"(d) {d_ok} [holdout alpha {h.alpha:.4f}, {h.reading}]; {verdict}", family="C10")
VM = save(pd.DataFrame(vrows), "verdict_map")

# ===================================================================================================== ledger, all-tests
LEDF = pd.DataFrame(LED)
# G7: rows of checks 2 to 8 are 'robustness' except check 7 (i); checks 1 and 9 keep 'descriptive' or 'exploratory'
chk = LEDF.test_id.str.extract(r"^M7_C(\d+)_")[0].astype(float)
ctx = chk.between(2, 8) & ~LEDF.primary_or_exploratory.eq("primary") & ~LEDF.primary_or_exploratory.eq("robustness")
LEDF.loc[ctx, "note"] = LEDF.loc[ctx, "note"].astype(str).str.cat(
    LEDF.loc[ctx, "primary_or_exploratory"].map(lambda v: f"[context: {v}]"), sep="; ").str.lstrip("; ")
LEDF.loc[ctx, "primary_or_exploratory"] = "robustness"
assert (LEDF.primary_or_exploratory == "primary").sum() <= 1
assert set(LEDF.loc[chk.isin([1, 9]), "primary_or_exploratory"]) <= {"descriptive", "exploratory"}
LEDF.to_csv(TABLES / "M7_robustness_tests_ledger.csv", index=False)
m7part = LEDF.assign(ledger_file="M7_robustness_tests_ledger.csv", module_id="M7", type="", r_subfamily="",
                     is_primary_label=LEDF.primary_or_exploratory.eq("primary"))
m7part["family"] = "M7:" + m7part["family"].astype(str)
m7part.loc[m7part.test_id.eq("M7_C7_i_alpha_ff3umd"), "family"] = "F"
ALLOUT = pd.concat([ALL, m7part[ALL.columns]], ignore_index=True)
# one-sided p used by M7 for families P, R and F (as the spec defines it)
p1c = pd.Series(np.nan, index=ALLOUT.index)
msk = ALLOUT.family.isin(["P", "R"]) | ALLOUT.test_id.eq("M8_share_i_alpha_nw6")
p1c[msk] = one_sided(ALLOUT.loc[msk, "statistic"], ALLOUT.loc[msk, "p_value_two_sided"])
# check 7 (i): the t(457) one-sided p that family F's Holm used (output only; copied, not recomputed)
m7i = ALLOUT.test_id.eq("M7_C7_i_alpha_ff3umd")
p1c[m7i] = ALLOUT.loc[m7i, "p_value_one_sided"].astype(float)
ALLOUT["p1_m7"] = p1c
_fchk = ALLOUT[ALLOUT.family.eq("F")].set_index("test_id")["p1_m7"]
assert _fchk.notna().all() and np.allclose(_fchk.loc[FF.test].to_numpy(), FF.p1.to_numpy(), rtol=0, atol=1e-15)
ALLOUT.to_csv(TABLES / "M7_all_tests.csv", index=False)
log(f"ledger {len(LEDF)} rows ({LEDF.primary_or_exploratory.value_counts().to_dict()}); all-tests {len(ALLOUT)} rows")

# multiple-testing summary table (families and survivors)
mt = [("F (frozen, hash-verified)", len(FF), "Holm, one-sided", f(FF.holm.min(), 3), str(int(FF.survives.sum()))),
      ("P (module primary alphas)", mP, "Holm, one-sided", f(Pu.holm.min(), 3), str(int(Pu.survives_holm.sum()))),
      ("P (module primary alphas)", mP, "BH, one-sided", f(Pu.bh.min(), 3), str(int(Pu.survives_bh.sum())))]
for _, r in Rsum.iterrows():
    mt.append((r.family, int(r.m), "BH / BY, one-sided", f"{f(r.min_bh, 3)} / {f(r.min_by, 3)}", f"{r.bh_survivors} / {r.by_survivors}"))
for _, r in SS.iterrows():
    mt.append((f"{r.family} (search)", int(r.M), "Romano-Wolf; SPA", f"{f(r.best_rw_adj_p, 3)}; {f(r.spa_p, 3)}", str(int(r.rw_survivors))))
MT = pd.DataFrame(mt, columns=["Family", "Tests", "Method", "Smallest adjusted p", "Survivors at 5%"])
save(MT, "multiple_testing_summary")
tex(MT, "multiple_testing_summary", "Multiple-testing families and survivors across the project (spec checks 2 to 4).",
    "tab:m7_mt", "lrlrr",
    notes=(f"P: {len(P)} labelled primary alpha rows, {len(P) - mP} exact duplicates collapsed; best one-sided p "
           f"{best.p1:.3f} ({best.module.split('_')[0]}). R: robustness alpha grids, positive side only. Search families: FF5+UMD "
           "alphas of every saved or regenerated strategy series (58 over 1970-2026, 89 over 2010-2026). D (73 other primaries), "
           "X (170 placebo and reference rows), L (4,850 loadings) and E (9,411 exploratory rows) are not corrected."))

vt = []
for _, r in VM.iterrows():
    is_book = r.candidate.startswith("Optimizer")
    col_ = "opt:X_unc" if is_book else "GB:epa5"
    fam_ = "S-full" if is_book else "S-post"
    mrow = SMi.loc[(fam_, col_)]
    ev_for = (f"FF5+UMD alpha {pc(mrow.alpha)}%, t {f(mrow.t)}, {'1970-2026' if is_book else '2010-2026'}; "
              f"RW adj. p {f(r.rw_p_full, 3)} (1970-2026), {f(r.rw_p_post, 3)} (2010-2026)")
    pre_txt = (f"; pre-1970 FF3+UMD alpha {pc(FROZEN['alpha'])}%, t {f(FROZEN['t'])} ({FROZEN['verdict']})"
               if (is_book and FROZEN is not None) else "")
    if FROZEN is not None and is_book and FROZEN["verdict"] == "PASS":
        ev_for += pre_txt; pre_txt = ""
    ev_ag = f"holdout alpha {pc(r.holdout_alpha)}% ({r.holdout_reading}); DSR {f(r.dsr_full, 3)} / {f(r.dsr_post, 3)}"
    if is_book:
        ev_ag += pre_txt + "; validation-to-holdout decay"
    else:
        ev_ag += "; no confirmatory test; 2022 intensities applied back to 1970"
    vt.append({"Candidate": r.candidate, "Evidence for": ev_for, "Evidence against": ev_ag,
               "Adjusted significance": f"RW {f(r.rw_p_full, 3)} / {f(r.rw_p_post, 3)}",
               "Deflated Sharpe (AR)": f"{f(r.dsr_full, 3)} / {f(r.dsr_post, 3)}", "Verdict": r.verdict})
vt.append({"Candidate": "Attention thesis (Short-Brown rules)",
           "Evidence for": "validation-window alphas (team, M2 grid 89% positive)",
           "Evidence against": f"M8 frozen FAIL; family P smallest Holm p {f(Pu.holm.min(), 2)}; holdout rejects a worthwhile alpha for "
                               f"{int(((HO.series.str.startswith('team')) & (HO.model == 'FF5+UMD') & (HO.reading == 'rejects a worthwhile alpha')).sum())} of 6 rules",
           "Adjusted significance": f"Holm {f(Pu.holm.min(), 2)}, BH {f(Pu.bh.min(), 2)}", "Deflated Sharpe (AR)": "not a candidate",
           "Verdict": "Do not implement"})
VT = save(pd.DataFrame(vt), "verdict_table")
tex(VT, "verdict_table", "Final verdict by candidate (spec check 10).", "tab:m7_verdict",
    "p{2.1cm}p{3.3cm}p{3.3cm}p{1.7cm}p{1.5cm}p{1.9cm}",
    notes=("Implement requires (a) a hash-verified confirmatory alpha test, (b) Romano--Wolf adjusted p at most 0.05 in both search "
           "families, (c) governing DSR at least 0.95 in both windows and (d) a positive holdout alpha whose reading is not "
           "'rejects'. Paper-trade: (a) holds and any of (b) to (d) fails. Do not implement: (a) fails."))

# ===================================================================================================== figures
log("figures")
SHORT_G = {"M5 optimizer paths": "Optimizer\npaths", "M5 EW book": "EW\nbook", "M5 EW variants": "EW\nvariants",
           "M5 carbon screens": "Carbon\nscreens", "M4 green-minus-brown": "M4 green-\nminus-brown", "Team rules": "Team\nrules",
           "M1b MCCC/CPU rules": "M1b MCCC/\nCPU rules", "M6 timing": "M6\ntiming"}
fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2), sharey=True, gridspec_kw={"width_ratios": [5, 8]})
for ax, fam in zip(axes, ("S-full", "S-post")):
    s = SM[SM.family == fam].copy()
    grp = [g for g in GROUP_LABEL.values() if g in set(s.group)]
    for gi, g in enumerate(grp):
        vv = s[s.group == g].sort_values("t")
        xs = gi + np.linspace(-0.28, 0.28, len(vv)) if len(vv) > 1 else np.array([gi])
        ax.scatter(xs, vv.t, s=13, color=PS.BLUE, alpha=0.75, linewidths=0, zorder=3)
        if g in ("M5 optimizer paths", "M4 green-minus-brown"):
            for cname, col in (("book", "opt:X_unc"), ("EPA 5v5", "GB:epa5")):
                if col in set(vv.member):
                    j = list(vv.member).index(col)
                    r = vv.iloc[j]
                    ax.scatter([xs[j]], [r.t], s=48, facecolors="none", edgecolors=PS.ORANGE, linewidths=1.5, zorder=4)
                    ax.annotate(f"{cname}, RW p {r.rw_adj_p:.2f}", (xs[j], r.t), xytext=(-10, 12), textcoords="offset points",
                                fontsize=7, color=PS.INK, ha="right", va="bottom", zorder=6,
                                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.9),
                                arrowprops=dict(arrowstyle="-", color=PS.MUTED, lw=0.6))
    crit = SS.set_index("family").loc[fam, "maxt_crit95"]
    ax.axhline(crit, color=PS.INK2, lw=1, ls="--")
    ax.text(0.55, crit + 0.05, f"max-t 5% critical value {crit:.2f}", ha="left", va="bottom", fontsize=7, color=PS.INK2)
    ax.axhline(stats.norm.ppf(0.95), color=PS.MUTED, lw=0.8, ls=":")
    ax.text(0.55, stats.norm.ppf(0.95) - 0.05, "single test at 5%", ha="left", va="top", fontsize=7, color=PS.MUTED)
    ax.axhline(0, color=PS.MUTED, lw=0.6)
    ax.set_xticks(range(len(grp)))
    ax.set_xticklabels([SHORT_G[g] for g in grp], fontsize=7)
    ax.set_title(f"{fam}: {'1970-01 to 2026-07' if fam == 'S-full' else '2010-01 to 2026-07'}, {len(s)} series")
    ax.set_xlim(-0.6, len(grp) - 0.4)
axes[0].set_ylabel("FF5+UMD alpha t (NW 6)")
savefig(fig, "M7_search_family_t")

fig, ax = plt.subplots(figsize=(7.2, 3.4))
g0 = RM2[RM2.kind == "strat"]
wl = [w for w in ["full_live", "post2010", "validation", "pre_covid", "covid", "holdout", "inflation_rates", "last18", "last12"] if (g0.window == w).any()]
data = [g0[g0.window == w].statistic.values for w in wl]
bp = ax.boxplot(data, positions=range(len(wl)), widths=0.55, showfliers=False, patch_artist=True,
                medianprops=dict(color=PS.INK, lw=1.2), boxprops=dict(facecolor=PS.SEQ_BLUE[1], edgecolor=PS.BLUE),
                whiskerprops=dict(color=PS.BLUE), capprops=dict(color=PS.BLUE))
ax.axhline(0, color=PS.MUTED, lw=0.8)
ax.set_xticks(range(len(wl)))
ax.set_xticklabels([w.replace("_", " ") for w in wl], fontsize=7.5)
ax.set_ylabel("alpha t-statistic (NW 6)")
ax.set_title(f"Robustness grid ({len(g0):,} strategy alphas) by evaluation window")
for i, w in enumerate(wl):
    sp = (g0[g0.window == w].statistic > 0).mean()
    ax.text(i, ax.get_ylim()[1], f"{100 * sp:.0f}% > 0", ha="center", va="top", fontsize=7, color=PS.INK2)
savefig(fig, "M7_grid_windows")

if FROZEN is not None:
    fzr = pd.read_csv(FROZEN_RET_CSV, index_col=0, parse_dates=True)
    Xw = X4.loc[fzr.index]
    ftm = fit(fzr["net"], Xw)
    beta = np.array([ftm[f"b_{c}"] for c in Xw.columns])
    hedged = fzr["net"] - Xw.values @ beta
    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    ax.plot(fzr.index, 100 * (np.log1p(fzr["net"]).cumsum()), color=PS.BLUE, label="book, net of 10 bp")
    ax.plot(fzr.index, 100 * hedged.cumsum(), color=PS.ORANGE, label="book less its FF3+UMD exposures (alpha + residual)")
    ax.axvline(pd.Timestamp("1950-09-30"), color=PS.MUTED, lw=0.8, ls="--")
    ax.text(pd.Timestamp("1950-12-31"), ax.get_ylim()[1], "second half", fontsize=7, color=PS.INK2, va="top")
    ax.axhline(0, color=PS.MUTED, lw=0.6)
    ax.set_ylabel("cumulative return, % (log / sum)")
    ax.set_title(f"Frozen 1931-07 to 1969-12 run: FF3+UMD alpha {100 * FROZEN['alpha']:.2f}%, t {FROZEN['t']:.2f}, {FROZEN['verdict']}")
    ax.legend(loc="upper left")
    savefig(fig, "M7_frozen_pre1970")

log(f"done. verdicts: {VM[['candidate', 'verdict']].values.tolist()}")
