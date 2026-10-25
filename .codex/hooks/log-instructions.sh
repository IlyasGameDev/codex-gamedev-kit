#!/usr/bin/env bash
# Optional manual diagnostic, not a Codex lifecycle hook.
# Usage: bash .codex/hooks/log-instructions.sh AGENTS.md .codex/rules/ui-code.md
# Records which instruction paths the caller says it consulted. This is not
# evidence that Codex automatically loaded any path rule or imported a file.
set -eu
studio_log_root="$(cd "$(dirname "$0")/../.." && pwd)"
if [ "$#" -eq 0 ]; then
  printf '%s\n' 'Usage: bash .codex/hooks/log-instructions.sh <instruction-path>...' >&2
  exit 2
fi
cd "$studio_log_root"
mkdir -p production/session-logs
for studio_instruction in "$@"; do
  if [ ! -f "$studio_instruction" ]; then
    printf 'Missing instruction file: %s\n' "$studio_instruction" >&2
    exit 1
  fi
  printf '%s | manual-read | %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$studio_instruction" >> production/session-logs/instructions-loaded.log
done
