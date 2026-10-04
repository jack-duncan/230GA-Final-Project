"""Process checks for M8: preregistration timing and hash, run records, and whether run.py changed after the primary run.

1. SHA-256 of PREREGISTRATION.md vs first_run_record.json, dryrun/first_run_record.json, M8_preregistration_hash.csv.
2. File birth/modification times (os.stat; st_birthtime where the filesystem exposes it).
3. __pycache__/run.cpython-314.pyc was compiled from the run.py that existed at 03:36:21 (header mtime), i.e. before
   the primary run at 03:37:46. Its code objects are compared with the current run.py function by function.
4. The first-run key numbers vs the published tables (they must be the same numbers).
Run: cd /home/hashim/projects/GA/project/research && uv run python modules/M8_frozen_pre2010/verify/xv_timeline.py
"""
import datetime as dt
import dis
import difflib
import hashlib
import json
import marshal
import os
import pathlib
import re
import struct
import subprocess
import types

import pandas as pd

M = pathlib.Path("/home/hashim/projects/GA/project/research/modules/M8_frozen_pre2010")
TAB = pathlib.Path("/home/hashim/projects/GA/project/research/outputs/tables")


def ts(x):
    return dt.datetime.fromtimestamp(x).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


h = hashlib.sha256((M / "PREREGISTRATION.md").read_bytes()).hexdigest()
rec = json.loads((M / "first_run_record.json").read_text())
drec = json.loads((M / "dryrun" / "first_run_record.json").read_text())
meta = pd.read_csv(TAB / "M8_preregistration_hash.csv").iloc[0]
print("1. prereg sha256 now        ", h)
print("   first_run_record          ", rec["prereg_sha256"], rec["prereg_sha256"] == h, "| run_time", rec["run_time"])
print("   dryrun first_run_record   ", drec["prereg_sha256"], drec["prereg_sha256"] == h, "| run_time", drec["run_time"])
print("   M8_preregistration_hash   ", meta["prereg_sha256"], meta["prereg_sha256"] == h, "| first_run_time", meta["first_run_time"])

print("\n2. file times (birth / modify; birth at 1 s resolution here, use `stat` for ns)")
print("   round 2: run.py was re-created (new inode) by the 06:05 correction edit, so its birth now reads 06:05:07;")
print("   the original 03:35:43.583 birth is in corrections/pre_correction_0341/manifest.json and VERIFY.md round 1.")
for p in [M, M / "PREREGISTRATION.md", M / "run.py", M / "dryrun" / "first_run_record.json", M / "verify_signal.py",
          M / "__pycache__" / "run.cpython-314.pyc", M / "first_run_record.json", TAB / "M8_passbar.csv", M / "FINDINGS.md"]:
    st = os.stat(p)
    birth = getattr(st, "st_birthtime", None)
    if birth is None:  # Linux: os.stat has no birth time; GNU stat reads it through statx
        out = subprocess.run(["stat", "--format=%W", str(p)], capture_output=True, text=True).stdout.strip()
        birth = float(out) if out and out != "0" else None
    print(f"   {str(p).replace(str(M.parent.parent.parent) + '/', ''):70s} birth {ts(birth) if birth else 'n/a':23s} modify {ts(st.st_mtime)}")

print("\n3. bytecode of run.py before the primary run vs now")
pyc = (M / "__pycache__" / "run.cpython-314.pyc").read_bytes()
_, src_mtime, src_size = struct.unpack("<III", pyc[4:16])
print(f"   pyc compiled from run.py with mtime {ts(src_mtime)} and size {src_size}; current size {(M / 'run.py').stat().st_size}")
if src_size == (M / "run.py").stat().st_size and abs(src_mtime - int((M / "run.py").stat().st_mtime)) <= 1:
    obs = json.loads((pathlib.Path(__file__).resolve().parent / "xv_pyc_observation.json").read_text())
    print("   The pre-primary pyc has been recompiled from the current run.py by another process (see xv_pyc_observation.json).")
    print("   Recorded observation:", json.dumps(obs, indent=1))
    print("   NOTE (round 2): the comparison below is then vacuous (pyc and run.py are the same source) and is NOT evidence.")
    print("   The 03:41 -> 06:05 comparison is in xv_round2.py section E (run_0341.py vs run.py).")
old = marshal.loads(pyc[16:])
new = compile((M / "run.py").read_text(), str(M / "run.py"), "exec")


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


fo, fn = funcs(old), funcs(new)
changed = []
for k in sorted(set(fo) | set(fn)):
    if k not in fo or k not in fn:
        changed.append((k, "added/removed"))
        continue
    if norm(fo[k]) != norm(fn[k]):
        d = [ln for ln in difflib.unified_diff(norm(fo[k]), norm(fn[k]), lineterm="", n=0) if ln[:1] in "+-" and ln[:3] not in ("+++", "---")]
        consts = sorted({ln[1:] for ln in d if "LOAD_CONST" in ln})[:6]
        changed.append((k, f"{len(d)} changed instructions; e.g. {consts}"))
print(f"   {len(fo)} code objects before, {len(fn)} now; unchanged: {len(fo) - len(changed)}")
for k, why in changed:
    print(f"   CHANGED {k}: {why}")
core = ["share_signal", "team_signal", "decision_hold", "brown_model", "run_strategy", "FastEngine.position", "FastEngine.net",
        "nw_numpy", "attribution", "runs", "shuffle_test", "shuffle_test.<locals>.alpha_of", "count_episodes", "evaluate",
        "build_bond", "par_bond_dc", "exact_par_return", "load_inputs"]
print("   core functions identical:", all(norm(fo[k]) == norm(fn[k]) for k in core))

print("\n4. first-run key vs published tables")
key = rec["key"]
pb = pd.read_csv(TAB / "M8_passbar.csv")
att = pd.read_csv(TAB / "M8_attribution.csv")
dro = pd.read_csv(TAB / "M8_drop_one.csv")
ep = pd.read_csv(TAB / "M8_episodes.csv")
P = "Frozen EMV-share rule (primary)"
a = att[(att.signal == P) & (att.term == "const")].iloc[0]
checks = {
    "alpha_ann": (key["alpha_ann"], round(12 * a["coef"], 10)),
    "t6": (key["t6"], round(a["t_nw6"], 8)),
    "shuffle_p": (key["shuffle_p"], round(pb[(pb.signal == P) & pb.component.str.startswith("(ii)")]["p_value"].iloc[0], 8)),
    "episodes": (key["episodes"], int((ep.signal == P).sum())),
    "drop_alphas": (key["drop_alphas"], [round(x, 10) for x in dro[dro.signal == P]["alpha_ann"]]),
    "passed": (key["passed"], bool(pb[(pb.signal == P) & (pb.component == "VERDICT")]["pass"].iloc[0])),
}
for k, (x, y) in checks.items():
    print(f"   {k:12s} record {x}  table {y}  equal {x == y}")
