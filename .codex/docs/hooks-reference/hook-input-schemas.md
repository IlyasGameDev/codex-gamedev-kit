# Native Codex hooks and the studio adapter

The active configuration is **.codex/hooks.json**. It calls **.codex/hooks/run.sh**,
which selects Python 3 and invokes **codex_adapter.py**. The adapter reads one
native event from stdin and emits one JSON object. It never executes a proposed
shell command or applies a proposed patch.

Official reference: [Codex hooks](https://learn.chatgpt.com/docs/hooks).

## Setup and trust

Open the project folder in a current Codex CLI or desktop version with lifecycle
hooks support. Review the project before trusting its local configuration.
Then open **/hooks** and review and trust the configured hooks. Project trust
and hook trust are separate. Changed hook definitions require another review.
No script in this project writes trust records or bypasses that review.

Bash and Python 3 are required. Git is needed for commit validation and history.
Use Git Bash or WSL on Windows. If Python is unavailable, the hook entry point
exits with status 2; a PreToolUse call cannot quietly bypass validation.

Hooks run from the session working directory. The configured entry command walks
up to the nearest folder containing .codex/hooks/run.sh, including before a ZIP
has been initialized as a Git repository. The adapter then runs each validator
at that studio root and supplies STUDIO_PROJECT_ROOT itself. That environment
variable is a studio implementation detail, not a built-in Codex variable.

## Registered events

| Native event | Matcher | Studio behavior |
| --- | --- | --- |
| SessionStart | all sources | Present repository state, checkpoint, and missing setup |
| PreToolUse | Bash | Validate recognized Git commits; report push and release cautions |
| PreToolUse | apply_patch | Reconstruct proposed files, then check registry and write rules |
| PostToolUse | apply_patch | Validate actual data JSON and asset naming; suggest skill validation |
| PreCompact | all triggers | Record a compaction event |
| Stop | all turns | Archive a changed existing checkpoint and repository activity |
| SubagentStart | all roles | Log the role and session ID |
| SubagentStop | all roles | Complete the role's audit record |

Stop is synchronous and time-bounded in this kit. It does not create a
checkpoint from conversation history; the parent must update the checkpoint
during work. After compaction, follow AGENTS.md and read that file explicitly.

There is no registered Notification event. Native transcripts are not parsed to
infer whether an agent produced an artifact; the parent checks the output paths
from its delegation brief.

## Native shell input

Codex exposes shell and unified exec calls to hooks as **Bash**. A later polling
call can deliver PostToolUse when the original command finishes.

~~~json
{
  "hook_event_name": "PreToolUse",
  "session_id": "session-example",
  "cwd": "/work/my-game",
  "tool_name": "Bash",
  "tool_input": {
    "command": "git commit -m 'Implement player movement'"
  }
}
~~~

The bridge preserves the command as data. The existing commit validator reads
the index, and, for recognized add/commit or commit-all forms, relevant working
copies. Invalid gameplay data JSON blocks the pending command. Missing
validators and timeouts during a recognized commit are surfaced as a denial.

This is a command classifier, not a shell interpreter or a security sandbox.
A script, alias, unknown wrapper, external process, or MCP tool can make changes
it cannot predict. Use normal Git/CI validation as well for required gates.

## Native patch input

~~~json
{
  "hook_event_name": "PreToolUse",
  "cwd": "/work/my-game",
  "tool_name": "apply_patch",
  "tool_input": {
    "command": "*** Begin Patch\n*** Add File: assets/data/player.json\n+{\"health\": 100}\n*** End Patch"
  }
}
~~~

Native apply_patch input contains the patch in **tool_input.command**, not a
single file_path. Its tool name stays apply_patch even when a hook matcher uses
the Edit or Write aliases.

The bridge recognizes adds, updates, multiple hunks, deletes, and moves. It
resolves relative file paths against the event's working directory and never
reads a path outside this studio root, including a symlink that escapes it.

For pre-edit checks it reconstructs proposed text without changing the file.
It uses exact context matching. If native apply_patch accepts a fuzzy whitespace
match that the bridge cannot reconstruct, or the old file is binary or over
4 MiB, the bridge explicitly reports the skipped content check. PostToolUse
still checks the actual resulting file. It never reports a skipped check as
passed.

Write/Edit objects passed to the shell validators are **internal compatibility
payloads**. They do not describe Codex's native tools. On an update, the bridge
supplies the original and reconstructed content as an Edit; on an add or delete,
it supplies a Write with the proposed content. This lets the existing registry
comparison examine the old and proposed versions.

## Output and blocking

A successful check returns an empty JSON object or no actionable message.
An advisory result uses hookSpecificOutput.additionalContext, and does not
automatically approve the tool.

~~~json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "additionalContext": "The proposed registry change removes an existing ID."
  }
}
~~~

A pre-tool denial uses the documented decision:

~~~json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "assets/data/player.json is not valid JSON."
  }
}
~~~

The adapter never returns permissionDecision: ask, continue: false, or
suppressOutput for PreToolUse; those are not supported decisions in the
verified Codex version. It never emits allow just to silence a permission
prompt.

PostToolUse runs **after** the edit. A failed JSON check supplies actionable
feedback and states that the edit already happened. It cannot undo or prevent
that write.

Each adapter run has a 40-second internal budget inside the 45-second configured
hook timeout. Individual helper calls are bounded to 15 seconds. Output is
bounded, and skipped checks are reported.

## Coverage limits and manual helpers

- Registry and write rules are advisory. They detect common mistakes; they do
  not replace Codex's sandbox and approval controls.
- Patch checks cover apply_patch edits. Arbitrary shell writes and filesystem
  MCP tools are not inspected as patches.
- The legacy Read-shaped validator is not registered. Use the section-reading
  workflow and .codex/scripts/read-guard.sh when reading large design files.
- notify.sh is an optional manual Windows notification helper.
- log-instructions.sh accepts explicit instruction paths and records that the
  caller consulted them. It is not an automatic instruction-load event.
- validate-agent-artifact.sh accepts expected output paths explicitly and
  reports whether each exists. It is a parent-side check, not a registered
  SubagentStop hook or an inference from private transcript contents.
- update-check.sh is deliberately a network-free no-op. Review kit updates
  manually using UPGRADING.md.

The other documents in this directory are optional Git-hook or workflow
examples. They are not automatically installed by .codex/hooks.json.
