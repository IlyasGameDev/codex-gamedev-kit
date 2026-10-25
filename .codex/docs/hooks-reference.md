# Active Codex hooks

The active configuration is **.codex/hooks.json**. Each registered event invokes
**.codex/hooks/run.sh**, then the Python adapter **.codex/hooks/codex_adapter.py**.
The adapter calls the relevant existing validators and emits one native Codex
response.

Project configuration must be trusted, and each hook definition must be reviewed
and trusted through **/hooks**, before these hooks run. Hook definitions that
change require review again. The template does not create trust records or
bypass approval controls. Bash and Python are required.

The authoritative external reference is
[Codex hooks](https://learn.chatgpt.com/docs/hooks). See the
[wire schemas and coverage limits](hooks-reference/hook-input-schemas.md) for
native payload examples, timeout behavior, and adapter details.

## Registered events and checks

| Codex event | Native tool or trigger | Studio behavior |
| --- | --- | --- |
| SessionStart | Any startup source | session-start.sh presents branch, sprint, milestone, configured review mode, engine-reference agreement, and the existing session checkpoint. detect-gaps.sh reports missing setup or documentation. |
| PreToolUse | Bash | validate-commit.sh checks recognized Git commits, including gameplay-data JSON in the staged version. validate-push.sh reports push and release cautions. |
| PreToolUse | apply_patch | The adapter reconstructs proposed files. validate-registry.sh compares registry entries, and validate-write.sh checks guarded files, configuration, prototype boundaries, and localization freezes. These are advisory. |
| PostToolUse | apply_patch | validate-assets.sh checks actual data JSON and asset naming. validate-skill-change.sh suggests the relevant skill test. |
| PreCompact | Any compaction trigger | pre-compact.sh records the event; the parent is responsible for maintaining and rereading the checkpoint. |
| Stop | Every completed turn | session-stop.sh synchronously archives a changed checkpoint and repository activity, and updates the per-session subagent count. |
| SubagentStart | Any agent type | log-agent.sh records the role and session ID. |
| SubagentStop | Any agent type | log-agent-stop.sh records completion. The parent checks expected artifact paths directly. |

There are seven event types. The separate rows for Bash and apply_patch describe
the two branches of the same PreToolUse handler.

## Native inputs and outputs

Codex exposes shell and unified-exec calls to these hooks as **Bash**. For
**apply_patch**, tool_input.command contains the complete patch. It does not
supply a single file_path or a separate old_string/new_string pair.

The adapter converts a patch into internal per-file Write/Edit objects for the
existing shell validators. Those objects are a compatibility interface inside
the studio, not a description of Codex's native tools. File additions, updates,
multiple hunks, deletions, and moves are recognized. Exact-context reconstruction
failures are reported as skipped pre-edit checks; post-edit checks still inspect
the real resulting files.

Invalid staged gameplay-data JSON blocks a recognized pending commit with a
native PreToolUse denial. A missing or timed-out commit validator also blocks
that recognized commit instead of silently passing it. Advisory output does not
automatically approve a tool or change Codex's normal approval policy.

PostToolUse happens after the edit. Its feedback can ask the model to fix a
problem, but cannot undo or prevent the completed write.

These checks do not form a general filesystem or shell security boundary.
Arbitrary shell writes, unknown command wrappers, aliases, and filesystem MCP
tools are outside patch inspection. Keep required repository checks in Git or
CI as appropriate.

## Checkpoints and compaction

The parent writes **production/session-state/active.md** as work proceeds.
SessionStart presents an existing checkpoint. The Stop handler archives it only
when its content changes, avoiding a full duplicate on every turn.

Stop runs synchronously with the adapter's timeout. It does not infer missing
state from conversation history. After a compaction or resumed session, follow
AGENTS.md and read the checkpoint explicitly; do not rely on every client
emitting another SessionStart event.

## Agent audit and counts

The audit file is **production/session-logs/agent-audit.log**. Start records keep
this format because session-stop.sh uses it for the per-session count:

~~~text
YYYYMMDD_HHMMSS | <session_id> | Agent invoked: <agent_type>
~~~

The count and role breakdown are written to
**production/session-logs/session-cost.md**. This is a count of observed lifecycle
events, not a token-usage measurement or monetary cost estimate. Without a
session ID, no cross-session total is fabricated.

## Manual helpers and omitted behavior

- **validate-agent-artifact.sh** accepts the expected output paths from a
  delegation brief and reports which exist. It does not parse private transcripts
  and is not registered as a SubagentStop hook.
- **log-instructions.sh** records explicitly supplied instruction paths that the
  caller says it consulted. Codex instruction loads are not intercepted.
- **validate-read.sh** remains a manual compatibility helper; there is no native
  Read matcher in the shipped configuration. Use section reads and
  .codex/scripts/read-guard.sh for large design documents.
- **notify.sh** is an optional manual Windows notification example. No
  Notification event is configured.
- **update-check.sh** is a network-free compatibility no-op. Review kit
  updates using `UPGRADING.md`.
- Other files in **.codex/docs/hooks-reference/** are optional Git-hook or
  workflow examples. The template does not install them into .git/hooks.

The template does not install UserPromptSubmit, PermissionRequest, PostCompact,
SessionEnd, or Interrupt handlers. Its existing checkpoint and validation
workflows do not require them. It does not assume unsupported events such as
InstructionsLoaded, ConfigChange, or FileChanged are available.
