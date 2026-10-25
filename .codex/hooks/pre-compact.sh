#!/bin/bash

# --- work from the project root ----------------------------------------------
# Every path below is repo-relative, so a hook invoked with a working directory
# that is not the repo root would silently read and write the WRONG TREE --
# returning a near-empty result instead of the session-recovery block, and
# creating stray trees such as docs/production/session-logs/ on write.
#
# PRECEDENCE IS LOAD-BEARING. A cwd that IS a project root carries real
# information and must win: a caller sitting inside another project means that
# project, not this one. Resolving to the script's own location first would
# override them. So, in order:
#   1. cwd holds project.yaml   -> cwd   (a project root)
#   2. cwd holds .codex/       -> cwd   (a project root not yet configured),
#      unless cwd is itself named .codex: a stray .codex/.codex/ would
#      make .codex/ a root, and the hooks would write .codex/production/
#   3. STUDIO_PROJECT_ROOT       -> that  (set by the studio adapter),
#      unless it names a .codex folder, for the same reason as rule 2
#   4. this script's location   -> <root>/.codex/hooks/../.. by construction
# Rule 4 always works and needs no environment at all; rules 1-2 stop it from
# overriding a caller that legitimately means somewhere else.
#
# NOT an upward search: that resolves a nested project to its parent's config.
if [ -f "project.yaml" ] || { [ -d ".codex" ] && [ "${PWD##*/}" != ".codex" ]; }; then
  CGS_ROOT="$PWD"
elif [ -n "${STUDIO_PROJECT_ROOT:-}" ] && [ -d "${STUDIO_PROJECT_ROOT}" ] && case "${STUDIO_PROJECT_ROOT%/}" in */.codex|*\\.codex) false ;; *) true ;; esac; then
  CGS_ROOT="$STUDIO_PROJECT_ROOT"
else
  CGS_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." 2>/dev/null && pwd)"
fi
[ -n "$CGS_ROOT" ] && cd "$CGS_ROOT" 2>/dev/null || true

# Codex PreCompact hook: log the compaction. Nothing else.
#
# Record only the event. The parent updates production/session-state/active.md
# during work and explicitly reads it after compaction. SessionStart also
# presents it when that event fires with source compact. This script cannot
# infer task state or guarantee that every client replays SessionStart.

# features.session_state: off => this hook is a no-op. Default `on`; see
# session_state_enabled() in yaml-helper.sh.
if [ -f .codex/hooks/yaml-helper.sh ]; then
    . .codex/hooks/yaml-helper.sh
    session_state_enabled || exit 0
fi

SESSION_LOG_DIR="production/session-logs"
mkdir -p "$SESSION_LOG_DIR" 2>/dev/null
echo "Context compaction occurred at $(date)." \
    >> "$SESSION_LOG_DIR/compaction-log.txt" 2>/dev/null

exit 0
