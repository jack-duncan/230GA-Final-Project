"""Round 2 manifest: sha256 and size of every file in checks/ (code, logs, outputs) plus the two exchange inputs.
Writes out/manifest_round2.json (the round-1 out/manifest.json is left as written in round 1)."""
import hashlib
import json
import pathlib
import time

root = pathlib.Path("/home/hashim/projects/GA/project/research/exchange/02_coding_support")
files = {}
for p in sorted(root.rglob("*")):
    if p.is_file() and "__pycache__" not in p.parts and p.name != "manifest_round2.json":
        files[str(p.relative_to(root))] = {"sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "bytes": p.stat().st_size}
out = {"created": time.strftime("%Y-%m-%d %H:%M:%S %Z"), "note": "round 2; chatgpt_code_v2.py = round-2 code; "
       "chatgpt_code_v1fix.py = round-1 BUG-1-only fix (named chatgpt_code_v2.py in round 1, sha256 unchanged)",
       "files": files}
(root / "checks" / "out" / "manifest_round2.json").write_text(json.dumps(out, indent=1))
print(len(files), "files")
