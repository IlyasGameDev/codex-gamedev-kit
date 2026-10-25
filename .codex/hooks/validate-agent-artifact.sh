#!/usr/bin/env bash
# Optional parent-side artifact check, not a SubagentStop hook.
# Native Codex transcript formats are not parsed. Pass the exact destination
# paths from the delegation brief and inspect the present/missing rows.
# Usage: bash .codex/hooks/validate-agent-artifact.sh docs/review.md tests/result.md
set -eu
studio_artifact_root="$(cd "$(dirname "$0")/../.." && pwd)"
if [ "$#" -eq 0 ]; then
  printf '%s\n' 'Usage: bash .codex/hooks/validate-agent-artifact.sh <expected-path>...' >&2
  exit 2
fi
exec bash "$studio_artifact_root/.codex/scripts/write-guard.sh" --root "$studio_artifact_root" artifact "$@"
