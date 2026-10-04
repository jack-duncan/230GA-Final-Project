"""Write Markdown files that workflow subagents returned in their structured output ('files': [{path, content}]).
Subagents cannot write report .md files (harness rule), so the orchestrator saves them. Later journal entries win.
Usage: uv run python lib/save_returned_files.py <journal.jsonl> [--dry]"""
import json, sys, pathlib
ROOT = pathlib.Path("/home/hashim/projects/GA/project/research").resolve()
journal, dry = sys.argv[1], "--dry" in sys.argv
latest = {}
for ln in open(journal):
    d = json.loads(ln)
    if d.get("type") != "result" or not isinstance(d.get("result"), dict):
        continue
    for f in d["result"].get("files") or []:
        p = pathlib.Path(f["path"]).resolve()
        if ROOT not in p.parents:
            print("SKIP (outside research/):", p); continue
        latest[p] = (f["content"], d.get("agentId", "?"))
for p, (content, aid) in latest.items():
    print(("DRY " if dry else "WRITE ") + str(p.relative_to(ROOT)), len(content.split()), "words", "agent", aid[:10])
    if not dry:
        p.parent.mkdir(parents=True, exist_ok=True); p.write_text(content if content.endswith("\n") else content + "\n")
