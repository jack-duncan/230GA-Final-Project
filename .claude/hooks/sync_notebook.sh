#!/bin/bash
# Sync a notebooks/ script or notebook with its jupytext pair.
# Runs before Read/Edit (pull in notebook edits) and after Edit/Write (push script edits).
f=$(jq -r '.tool_input.file_path // empty')
case "$f" in
  */notebooks/*.py|*/notebooks/*.ipynb) ;;
  *) exit 0 ;;
esac
[ -f "$f" ] || exit 0
cd "$CLAUDE_PROJECT_DIR" || exit 0
if ! out=$(uv run --quiet jupytext --sync "$f" 2>&1); then
  echo "jupytext sync failed for $f:" >&2
  echo "$out" >&2
  exit 2
fi
exit 0
