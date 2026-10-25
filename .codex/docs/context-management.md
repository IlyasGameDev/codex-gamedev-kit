# Context management

Use files as checkpoints for long tasks. Follow the current runtime's compaction
behavior; do not assume a fixed context limit, token meter, or transcript format.

## Session state

Maintain `production/session-state/active.md` when `features.session_state` is
on. Use `.codex/docs/templates/session-state.md`. Keep current task, key decisions,
files changed, verification results, next steps, and unresolved questions.

| Region | Use |
| --- | --- |
| `<!-- STATUS -->` to `<!-- /STATUS -->` | Optional Epic/Feature/Task summary for readers and helpers. This kit does not install a custom status line. |
| `<!-- CHECKPOINT -->` to `<!-- /CHECKPOINT -->` | Replace with a concise current checkpoint, about 25 lines; the startup hook previews it when enabled. |
| Following narrative | Append significant decisions and evidence without expanding the checkpoint indefinitely. |

For an oversized narrative, run `bash .codex/scripts/rotate-session-state.sh
--dry-run` before rotating it. The helper preserves the checkpoint and moves
narrative to dated session logs. It does not silently discard completed work.

After compaction, a crash, or a new session, explicitly reread the checkpoint
and relevant working files. A trusted SessionStart hook also previews state at
session start; do not rely on it being replayed after every compaction.

## Incremental writing

For a large document or implementation, save complete useful sections as they
are ready. The user's request authorizes ordinary reversible writes. Keep drafts
and decisions consistent; ask only for genuinely unresolved material choices.
Checkpoint at logical milestones rather than after every tiny edit.

## Deterministic helpers

`.codex/scripts/` contains explicit, on-demand helpers such as
`gdd-structure-check.sh`, `story-status.sh`, and `review-scope.sh`.
`.codex/hooks/` contains validators plus the adapter registered by
`.codex/hooks.json`. Not every script there is an automatic hook; consult the
manifest and hook reference for actual registrations.

Run a helper with the available shell tool from the project root. No YAML tool
grant or automatic shell preprocessing is required. Honor actual command
approvals. Helpers emit observations, never verdicts; the caller applies the
project's rigor and override settings to those facts.

## Delegation and recovery

Give workers focused briefs and owned paths, and request concise results with
artifact paths and verification. Whether history is inherited depends on the
actual subagent call; provide all task-critical context explicitly.

A recovery summary should retain the objective, user decisions, active files,
next step, task ownership, test outcomes, and genuine blockers. Verify these
against the files before continuing. Never claim a check ran based only on a
saved note or an earlier worker's assertion.
