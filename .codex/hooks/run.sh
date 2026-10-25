#!/usr/bin/env bash
# Native Codex hook entry point. The JSON event is supplied on stdin.
# Python is needed for JSON and apply_patch decoding; nothing is installed here.
set -eu
studio_hook_dir="$(cd "$(dirname "$0")" && pwd)"
for studio_python in python3 python py; do
  if command -v "$studio_python" >/dev/null 2>&1 &&
      "$studio_python" -c 'import sys; sys.exit(sys.version_info < (3, 9))' >/dev/null 2>&1; then
    exec "$studio_python" "$studio_hook_dir/codex_adapter.py"
  fi
done
printf '%s\n' 'Codex Game Studios hooks require Python 3.9 or later. The validation hook could not run.' >&2
# On PreToolUse this blocks rather than silently skipping the commit validator.
exit 2
