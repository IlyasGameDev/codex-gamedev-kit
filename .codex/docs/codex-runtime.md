# Codex runtime contract

This file defines how every studio workflow runs in Codex. It takes
precedence over conversational examples and tool names in the workflow
library. The user's instructions and the actual host's instructions take
precedence over this file. Never relax access controls to satisfy a workflow.

## Skills and commands

Use `$skill-name` in a Codex prompt. Read the corresponding
`.agents/skills/<name>/SKILL.md`; arguments are the rest of the user's request,
not a shell environment variable. Skills may be selected automatically except
where `agents/openai.yaml` disables implicit invocation. Run listed helper
commands explicitly. There is no automatic shell preprocessing, file import,
or skill-specific model switch in this kit.

Determine the root containing `project.yaml`, `.codex/`, and `.agents/`.
Set the shell tool's working directory there before relative commands. A
session launched in a subdirectory is not necessarily at the root. Our hook
launcher sets `STUDIO_PROJECT_ROOT` for child helpers; this is a studio variable,
not a built-in Codex variable. Inspect command failures instead of quietly
substituting defaults and claiming success.

## Portable tool mapping

| Workflow wording | Codex behavior |
| --- | --- |
| Read / Glob / Grep | Use available file tools, `rg --files`, `rg`, and bounded reads; these labels do not require identically named tools. |
| Write / Edit | Use the available patch/file tool, normally `apply_patch`, or a scoped script. |
| Bash / PowerShell | Use the actual shell tool with a known working directory. Honor approvals. |
| WebSearch / WebFetch | Use available research tools for current official engine/API references. Disclose when unavailable. |
| User decision / question tool | Ask only an unresolved question that matters. Use an interactive tool if available in this mode, otherwise ordinary prose. |
| Agent / agent_type | Use the exposed subagent tool and its actual schema. Select a registered role only if accepted; otherwise brief a generic worker with its guide. |
| Task tracking | Use an available plan/task facility or `production/session-state/active.md`. No external task service is required. |
| Skill tool | Read the selected `SKILL.md` and execute it; never call a nonexistent tool. |

Do not pass the literal words `user decision` or `task tracking` as tool names.
Tool APIs vary between Codex CLI, IDE, desktop, and hosted sessions.
Helper diagnostics may say “skill start”; invoke that workflow with `$start`.

## Complete authorized work

The user's request and prior approvals authorize reversible work necessary to
fulfill it. A stock example saying “May I write?” does not require asking again.
The shipped `guided` mode states major choices and proceeds with sound defaults.
`collaborative` requests discussion at meaningful unresolved milestones;
`autonomous` reduces those discussions. None changes sandbox or external-action
permission. Suggested next skills are navigation help, not mandatory stops when
the user requested the whole implementation.

If optional input is skipped, use existing context and a stated reasonable
assumption. Ask a blocking question only when no sound path exists without it.
Do independent useful work first. Subagents return questions to the parent;
they do not open competing conversations with the user. Respect release,
destructive-action, and material-scope decisions still lacking authorization.

## Specialist delegation

Native custom agents are `.codex/agents/<name>.toml`, each with `name`,
`description`, and `developer_instructions` generated from `.codex/roles`.
No role pins a model or reasoning effort. The config caps concurrent subagents
at four; the actual runtime may impose a lower limit. Queue or work in the parent.

Brief workers with their goal, evidence, owned paths, checks, and output.
Parallelize independent analysis and disjoint edits; serialize dependencies and
edits to the same files. Inspect results before integration. The parent owns
the final task outcome. If subagents are unavailable, use sequential role-guided
passes and do not call them independent reviews.

Working notes in `.codex/agent-memory/` are ordinary files read explicitly, not
automatic Codex memory. Preloaded skills in guides are explicit read steps.
Advice-only role scopes are instructions, not enforced tool grants. Worktrees
are created explicitly; there is no automatic isolation or fake max-turn field.

## Hooks and access controls

`.codex/hooks.json` is the native manifest. Project configuration must be trusted,
and hook hashes need approval through `/hooks`. Inspect the scripts first.
The studio does not create trust files or approve itself. Changed commands may
need approval again. See `hooks-reference/hook-input-schemas.md` for coverage.

The adapter handles shell commands and supported `apply_patch` edits including
multiple files. Arbitrary shell scripts may write files without individual edit
events, so hooks cannot guarantee every write is inspected. When hooks are
disabled, run helpers explicitly; do not claim automatic enforcement.

The `.rules` policies govern supported execution decisions. Codex's sandbox,
host policy, and approval system remain authoritative.

## Validation

`python3 tools/studio.py doctor` inspects prerequisites;
`python3 tools/studio.py validate` checks studio structure. Neither logs in,
invokes a model, launches an engine, nor proves game correctness. Run game tests
through installed engine tools and verified project commands. Preserve evidence
and disclose unavailable checks precisely.
