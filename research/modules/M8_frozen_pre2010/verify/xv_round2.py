"""Round-2 verification of M8 after the post-verification corrections (06:05 PDT rerun).

Independent of run.py, lib/team_pipeline.py and lib/common.py (none is imported). Checks:
 A. the 03:41 snapshot (corrections/pre_correction_0341) is faithful: a sandbox run of run_0341.py, with tables and
    figures redirected to the scratch folder given as SANDBOX (SANDBOX/wrap.py patches common.TABLES/FIGURES; the
    M3 Damodaran xls is symlinked at SANDBOX/M3_alpha_beta/data because bond_checks reads it relative to run.py),
    reproduces every snapshot file byte for byte (except the this_run_time and prereg_file cells and the PDF
    /CreationDate stamp);
 B. manifest.json hashes match the snapshot copies and the untouched files;
 C. the current outputs (verifier rerun of run.py) equal the 06:05 outputs saved in SNAP0605 (except this_run_time);
 D. the current outputs vs the 03:41 snapshot: which files changed, shared numeric columns, added columns (own code);
 E. run_0341.py vs run.py: normalized bytecode per function and module-level constants;
 F. the new one-sided p columns against t.sf of the verifier's own t-stats (xv_results.json), and column order;
 G. the four i_alpha ledger notes; ledger size;
 H. prereg_written / prereg_file_mtime against the file stamp and statx times; birth times after the correction;
 I. free shuffle months from the verifier's own block lengths; engine_check_maxdiff;
 J. p-values quoted in the corrected FINDINGS;
 K. every M8 .tex (current and 03:41) compiled with tectonic in four page geometries; overfull boxes reported;
 L. annual BOND (verifier's own construction, xv_independent.py) vs Damodaran's 10y T-bond return, 1993-2025.
Run: cd /home/hashim/projects/GA/project/research && uv run python modules/M8_frozen_pre2010/verify/xv_round2.py
Writes verify/xv_round2.json and verify/xv_round2_tex.csv. Sections A and C need the session scratch folders and are
skipped when those are gone; their results are recorded in VERIFY.md round 2 and in the xv_round2.json of 06:18.
"""
import dis
import hashlib
import json
import os
import pathlib
import re
import subprocess
import tempfile
import types

import numpy as np
import pandas as pd
from scipy import stats

RES = pathlib.Path("/home/hashim/projects/GA/project/research")
M = RES / "modules/M8_frozen_pre2010"
TAB, FIG = RES / "outputs/tables", RES / "outputs/figures"
SNAP = M / "corrections/pre_correction_0341"
SCR = pathlib.Path("/tmp/claude-1000/-home-hashim-projects-GA/5d56c5f1-d319-48cb-b466-4daeaca6ed67/scratchpad")
SANDBOX = SCR / "sb0341"          # run_0341.py run with TABLES/FIGURES redirected here (wrap.py)
SNAP0605 = SCR / "state_0605"     # cp -p of outputs taken just before the verifier's rerun
OUT = pathlib.Path(__file__).resolve().parent
X = json.loads((OUT / "xv_results.json").read_text())
R = {}


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def csv_cmp(a_path, b_path):
    """Byte identity; for CSVs also shared numeric max diff, changed text cells, added/removed columns, column order."""
    a_path, b_path = pathlib.Path(a_path), pathlib.Path(b_path)
    out = {"byte_identical": a_path.read_bytes() == b_path.read_bytes()}
    if a_path.suffix == ".pdf":
        strip = lambda x: re.sub(rb"/CreationDate \([^)]*\)", b"", x)
        out["identical_except_CreationDate"] = strip(a_path.read_bytes()) == strip(b_path.read_bytes())
    if a_path.suffix == ".csv":
        a, b = pd.read_csv(a_path), pd.read_csv(b_path)
        shared = [c for c in a.columns if c in b.columns]
        out["added"] = [c for c in b.columns if c not in a.columns]
        out["removed"] = [c for c in a.columns if c not in b.columns]
        out["old_columns_keep_positions"] = list(b.columns[:len(a.columns)]) == list(a.columns)
        out["rows"] = (len(a), len(b))
        if len(a) == len(b):
            num = [c for c in shared if pd.api.types.is_numeric_dtype(a[c]) and pd.api.types.is_numeric_dtype(b[c])]
            txt = [c for c in shared if c not in num]
            d = np.abs(a[num].to_numpy(float) - b[num].to_numpy(float))
            out["numeric_maxdiff"] = float(np.nanmax(d)) if d.size else 0.0
            out["numeric_nan_pattern_same"] = bool((np.isnan(a[num].to_numpy(float)) == np.isnan(b[num].to_numpy(float))).all())
            ch = {c: int((a[c].astype(str) != b[c].astype(str)).sum()) for c in txt}
            out["text_cells_changed"] = {c: n for c, n in ch.items() if n}
    return out


# ---------------------------------------------------------------- A. snapshot faithful (sandbox run of run_0341.py)
if (SANDBOX / "tables").exists():
    A = {}
    for f in sorted((SNAP / "tables").glob("M8_*")):
        A[f.name] = csv_cmp(f, SANDBOX / "tables" / f.name)
    for f in sorted((SNAP / "figures").glob("M8_*")):
        A[f.name] = csv_cmp(f, SANDBOX / "figures" / f.name)
    R["A_sandbox_0341_vs_snapshot"] = {k: v for k, v in A.items() if not v["byte_identical"]}
    R["A_byte_identical"] = f"{sum(v['byte_identical'] for v in A.values())} of {len(A)}"
    R["A_sandbox_source_is_run_0341"] = sha(SANDBOX / "mod/run.py") == sha(SNAP / "run_0341.py")
else:
    R["A_sandbox_0341_vs_snapshot"] = "skipped: scratch sandbox absent (see docstring to rebuild it)"

# ---------------------------------------------------------------- B. manifest
man = json.loads((SNAP / "manifest.json").read_text())["files"]
B = {}
for rel, meta in man.items():
    p = pathlib.Path(rel)
    if rel.startswith("outputs/tables/"):
        copy = SNAP / "tables" / p.name
    elif rel.startswith("outputs/figures/"):
        copy = SNAP / "figures" / p.name
    elif rel.endswith("run.py"):
        copy = SNAP / "run_0341.py"
    else:
        copy = RES / rel          # PREREGISTRATION.md, first_run_record.json: must still be the live file
    cst = os.stat(copy)
    B[rel] = {"sha_match": sha(copy) == meta["sha256"], "size_match": cst.st_size == meta["size"],
              "copy_mtime_preserved": abs(cst.st_mtime - pd.Timestamp(meta["modify"]).timestamp()) < 1e-3,
              "manifest_birth": meta["birth"]}
R["B_manifest_all_sha_match"] = all(v["sha_match"] for v in B.values())
R["B_manifest_all_mtime_preserved"] = all(v["copy_mtime_preserved"] for v in B.values())
R["B_manifest_n"] = len(B)
R["B_manifest_run_py_birth"] = man["modules/M8_frozen_pre2010/run.py"]["birth"]
R["B_run_0341_matches_round1_observation"] = (os.stat(SNAP / "run_0341.py").st_size == 44443)

# ---------------------------------------------------------------- C. verifier rerun vs the 06:05 outputs
if (SNAP0605 / "tables").exists():
    C = {}
    for f in sorted((SNAP0605 / "tables").glob("M8_*")):
        C[f.name] = csv_cmp(f, TAB / f.name)
    for f in sorted((SNAP0605 / "figures").glob("M8_*")):
        C[f.name] = csv_cmp(f, FIG / f.name)
    R["C_rerun_vs_0605_not_identical"] = {k: v for k, v in C.items() if not v["byte_identical"]}
    R["C_byte_identical"] = f"{sum(v['byte_identical'] for v in C.values())} of {len(C)}"
else:
    R["C_rerun_vs_0605_not_identical"] = "skipped: 06:05 scratch copy absent (result recorded in VERIFY.md round 2)"

# ---------------------------------------------------------------- D. current vs 03:41
D = {}
for f in sorted((SNAP / "tables").glob("M8_*")):
    D[f.name] = csv_cmp(f, TAB / f.name)
for f in sorted((SNAP / "figures").glob("M8_*")):
    D[f.name] = csv_cmp(f, FIG / f.name)
R["D_current_vs_0341_changed"] = {k: v for k, v in D.items() if not v["byte_identical"]}
R["D_tables_byte_identical"] = f"{sum(v['byte_identical'] for k, v in D.items() if 'share_signal' not in k)} of {sum('share_signal' not in k for k in D)}"
R["D_shared_numeric_maxdiff_all_csv"] = max(v.get("numeric_maxdiff", 0.0) for v in D.values())
R["D_rerun_comparison_csv_agrees"] = None
rc = pd.read_csv(M / "corrections/rerun_comparison.csv")
R["D_rerun_comparison_csv_agrees"] = bool(all(bool(r.byte_identical) == D[r.file]["byte_identical"] for r in rc.itertuples()))


# ---------------------------------------------------------------- E. bytecode run_0341.py vs run.py
def funcs(co):
    out = {}
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            out[c.co_qualname] = c
            out.update(funcs(c))
    return out


def norm(c):
    out = []
    for ins in dis.get_instructions(c):
        if ins.opname in ("EXTENDED_ARG", "NOP", "CACHE"):
            continue
        a = re.sub(r"<code object (\S+) at 0x[0-9a-f]+, file \"[^\"]+\", line \d+>", r"<code \1>", ins.argrepr)
        out.append(f"{ins.opname} {re.sub(r'to L[0-9]+', 'to L', a)}")
    return out


old = compile((SNAP / "run_0341.py").read_text(), "run.py", "exec")
new = compile((M / "run.py").read_text(), "run.py", "exec")
fo, fn = funcs(old), funcs(new)
changed = sorted(k for k in set(fo) | set(fn) if k not in fo or k not in fn or norm(fo[k]) != norm(fn[k]))
R["E_code_objects"] = (len(fo), len(fn))
R["E_changed_functions"] = changed
R["E_module_level_same"] = norm(old) == norm(new)
R["E_module_level_diff"] = [ln for ln in __import__("difflib").unified_diff(norm(old), norm(new), lineterm="", n=0)
                            if ln[:1] in "+-" and ln[:3] not in ("+++", "---")]
stat_fns = ["share_signal", "team_signal", "decision_hold", "brown_model", "run_strategy", "FastEngine.position",
            "FastEngine.net", "nw_numpy", "attribution", "runs", "shuffle_test", "shuffle_test.<locals>.alpha_of",
            "count_episodes", "evaluate", "build_bond", "par_bond_dc", "exact_par_return", "bond_checks", "load_inputs",
            "monthly_grid", "make_figure", "fmt"]
R["E_statistical_and_figure_functions_identical"] = all(norm(fo[k]) == norm(fn[k]) for k in stat_fns if k in fo)
R["E_missing_names_checked"] = [k for k in stat_fns if k not in fo]

# ---------------------------------------------------------------- F. one-sided p columns
att = pd.read_csv(TAB / "M8_attribution.csv")
F = {}
for lab, key in (("Frozen EMV-share rule (primary)", "primary"), ("Team EMV_env level, lagged 1m (secondary)", "secondary")):
    sub = att[att.signal == lab].set_index("term")
    df_ = X[key]["df"]
    own6 = {t: stats.t.sf(v[1], df_) for t, v in X[key]["coef_t"].items()}
    F[key] = {"const_p_upper_nw6": float(sub.loc["const", "p_upper_nw6_t(n-k)"]),
              "const_p_upper_nw12": float(sub.loc["const", "p_upper_nw12_t(n-k)"]),
              "own_const_p_upper_nw6": float(own6["const"]),
              "own_const_p_upper_nw12": float(stats.t.sf(X[key]["t_nw12"], df_)),
              "max_abs_diff_all_terms_nw6": float(max(abs(sub.loc[t, "p_upper_nw6_t(n-k)"] - own6[t]) for t in own6)),
              "p_upper_eq_sf_of_published_t_nw12": float((sub["p_upper_nw12_t(n-k)"] - stats.t.sf(sub["t_nw12"], df_)).abs().max()),
              "two_sided_consistency": float((sub["p_nw6_t(n-k)"] - 2 * np.minimum(sub["p_upper_nw6_t(n-k)"], 1 - sub["p_upper_nw6_t(n-k)"])).abs().max())}
R["F_one_sided"] = F
R["F_attribution_old_columns_keep_positions"] = D["M8_attribution.csv"]["old_columns_keep_positions"]

# ---------------------------------------------------------------- G. ledger notes
led = pd.read_csv(TAB / "M8_tests_ledger.csv")
rows = led[led.iloc[:, 0].str.contains("i_alpha")]
R["G_ledger_rows"] = int(len(led))
R["G_ledger_primary_rows"] = int((led["kind"] == "primary").sum()) if "kind" in led.columns else None
R["G_i_alpha_notes"] = {r.iloc[0]: re.findall(r"one-sided upper p=([0-9.]+)", r["note"]) for _, r in rows.iterrows()}

# ---------------------------------------------------------------- H. prereg times and birth times
meta = pd.read_csv(TAB / "M8_preregistration_hash.csv").iloc[0]
stamp = re.search(r"Written: (\S+ \S+ \S+)", (M / "PREREGISTRATION.md").read_text()).group(1)


def statx(p):
    o = subprocess.run(["stat", "--format=%w|%y", str(p)], capture_output=True, text=True).stdout.strip().split("|")
    return {"birth": o[0], "modify": o[1]}


R["H_prereg_written_col"] = meta["prereg_written"]
R["H_prereg_stamp_in_file"] = stamp
R["H_prereg_file_mtime_col"] = meta["prereg_file_mtime"]
R["H_statx"] = {str(p.relative_to(RES)): statx(p) for p in
                [M, M / "PREREGISTRATION.md", M / "run.py", M / "first_run_record.json", M / "dryrun/first_run_record.json",
                 M / "verify_signal.py", TAB / "M8_passbar.csv", TAB / "M8_attribution.csv", FIG / "M8_share_signal.png"]}
R["H_prereg_sha"] = sha(M / "PREREGISTRATION.md")
R["H_first_run_record_sha"] = sha(M / "first_run_record.json")

# ---------------------------------------------------------------- I. free months, engine check
for key in ("primary", "secondary"):
    b = X[key]["shuffle_replicate"]
    R[f"I_free_{key}"] = {"N": b["N"], "in_position": int(sum(b["blocks"])), "flat": b["N"] - int(sum(b["blocks"])),
                          "separators": b["m"] - 1, "free": b["N"] - int(sum(b["blocks"])) - (b["m"] - 1)}
ss = pd.read_csv(TAB / "M8_strategy_summary.csv")
R["I_engine_check_maxdiff"] = ss["engine_check_maxdiff"].tolist() if "engine_check_maxdiff" in ss.columns else None

# ---------------------------------------------------------------- J. p-values quoted in FINDINGS
pr, se = X["primary"], X["secondary"]
R["J"] = {"primary_two_sided_nw6": pr["p_two"], "primary_upper_nw6": stats.t.sf(pr["t"], 175),
          "primary_two_sided_nw12": pr["p_nw12"], "primary_upper_nw12": stats.t.sf(pr["t_nw12"], 175),
          "bar_t2_one_sided": stats.t.sf(2.0, 175),
          "secondary_two_sided_nw6": se["p_two"], "secondary_upper_nw6": stats.t.sf(se["t"], 175),
          "secondary_t_nw12": se["t_nw12"], "secondary_upper_nw12": stats.t.sf(se["t_nw12"], 175)}
pb = pd.read_csv(TAB / "M8_passbar.csv")
R["J_passbar_rows"] = pb.to_dict("records")

# ---------------------------------------------------------------- K. TeX layout
GEOM = {"portrait_1in_10pt": ("10pt", "letterpaper,margin=1in"), "portrait_1in_11pt": ("11pt", "letterpaper,margin=1in"),
        "landscape_1in_10pt": ("10pt", "letterpaper,landscape,margin=1in"),
        "landscape_0.5in_10pt": ("10pt", "letterpaper,landscape,margin=0.5in")}
rows_k = []
texs = [(f"current/{p.name}", p) for p in sorted(TAB.glob("M8_*.tex"))] + \
       [(f"0341/{p.name}", p) for p in sorted((SNAP / "tables").glob("M8_*.tex"))]
with tempfile.TemporaryDirectory(dir=SCR) as td:
    td = pathlib.Path(td)
    for lab, p in texs:
        for g, (pt, geo) in GEOM.items():
            doc = td / "doc.tex"
            doc.write_text(f"\\documentclass[{pt}]{{article}}\\usepackage[{geo}]{{geometry}}\\usepackage{{booktabs}}\n"
                           f"\\begin{{document}}\n\\input{{{p}}}\n\\end{{document}}\n")
            r = subprocess.run(["tectonic", "--keep-logs", "--chatter", "minimal", "--outdir", str(td), str(doc)],
                               capture_output=True, text=True)
            log = (td / "doc.log").read_text(errors="ignore") if (td / "doc.log").exists() else ""
            ov = [float(x) for x in re.findall(r"Overfull \\hbox \(([0-9.]+)pt too wide\)", log)]
            rows_k.append({"file": lab, "geometry": g, "compiled": r.returncode == 0 and (td / "doc.pdf").exists(),
                           "overfull_pt_max": max(ov) if ov else 0.0})
            for q in td.glob("doc.*"):
                q.unlink()
K = pd.DataFrame(rows_k)
# ---------------------------------------------------------------- L. Damodaran correlation (own BOND construction)
import runpy  # noqa: E402
G = runpy.run_path(str(OUT / "xv_independent.py"), run_name="xv")
bt = G["bond_tot"].dropna()
ann_own = (1 + bt).groupby(bt.index.year).prod() - 1
nmon = bt.groupby(bt.index.year).size()
dmx = pd.read_excel(RES / "modules/M3_alpha_beta/data/histretSP.xls", sheet_name="Returns by year", header=None)
yr = pd.to_numeric(dmx.iloc[:, 0], errors="coerce")
dam = pd.Series(pd.to_numeric(dmx.iloc[:, 4], errors="coerce").to_numpy(), index=yr.to_numpy()).dropna()
dam = dam[pd.notna(dam.index)]
dam.index = dam.index.astype(int)
yrs = [y for y in range(1993, 2026) if y in dam.index and nmon.get(y, 0) == 12]
R["L_damodaran_corr_1993_2025"] = {"n_years": len(yrs), "corr": float(np.corrcoef(ann_own[yrs], dam[yrs])[0, 1]),
                                   "dam_1994_2008_2022": [float(dam[y]) for y in (1994, 2008, 2022)]}
K.to_csv(OUT / "xv_round2_tex.csv", index=False)
R["K_all_compiled"] = bool(K.compiled.all())
R["K_overfull"] = K[K.overfull_pt_max > 0].to_dict("records")


def clean(o):
    if isinstance(o, dict):
        return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, (np.floating, np.integer)):
        return o.item()
    if isinstance(o, np.bool_):
        return bool(o)
    return o


(OUT / "xv_round2.json").write_text(json.dumps(clean(R), indent=1, default=str))
print(json.dumps(clean({k: v for k, v in R.items() if k not in ("J_passbar_rows",)}), indent=1, default=str))
print(K.pivot(index="file", columns="geometry", values="overfull_pt_max").to_string())
