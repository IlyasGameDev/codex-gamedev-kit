# Codex Game Studios

A game-development studio with 49 specialist roles and 74 reusable workflows.
Use the expertise needed for the task; do not activate the whole studio for a
small change. This repository supports Unity, Godot, and Unreal Engine.

## Start with the project

1. Read `project.yaml`, relevant `project.local.yaml` overrides, and the latest
   `production/session-state/active.md` if it exists. Confirm facts against files.
2. Read `.codex/docs/codex-runtime.md` before the first studio workflow or
   delegation. It defines the kit's runtime behavior and takes precedence over
   examples that assume other tools or repeated approval prompts.
3. Inspect the actual engine project before changing settings. Unity's
   `ProjectSettings/ProjectVersion.txt`, Godot's `project.godot`, and Unreal's
   `.uproject` files are evidence; the template's example versions are not.
4. Resolve settings with `bash .codex/hooks/yaml-helper.sh resolve_config`
   from this project root. Commands in skills are steps to run, not automatic
   shell interpolation. A failed helper is not an empty project.

## Technology Stack

- **Engine**: [CHOOSE: Godot / Unity / Unreal Engine]
- **Language**: [CHOOSE: GDScript / C# / C++ / Blueprint]
- **Version Control**: Git; preserve existing branch and release conventions.
- **Build System**: [DETECT from the actual engine project]
- **Asset Pipeline**: [DETECT from the actual engine project]

## Engine Version Reference

<!-- ENGINE-REFERENCE-IMPORT: setup-engine updates the explicit read below. -->
Read `docs/engine-reference/<engine>/VERSION.md` before engine-specific work.
Resolve `<engine>` from `engine.name` in `project.yaml`; verify the actual engine
version and current official API documentation when a snapshot is stale.

## Workflows and roles

- Skills live in `.agents/skills/<name>/SKILL.md`. Invoke them as `$start`,
  `$setup-engine`, `$brainstorm`, `$dev-story`, `$code-review`, or `$help`.
  `/skills` is Codex's skill browser; studio skills do not add slash commands.
- Native agents live in `.codex/agents/*.toml`; their editable role guides are
  `.codex/roles/*.md`. Run `python3 tools/studio.py sync-agents` after editing a
  role guide. Agent models inherit the user's selected model.
- Use available Codex subagent tools for independent tasks with distinct file
  ownership. Give each agent its objective, inputs, allowed paths, and expected
  output. Wait for dependencies before integration. The parent owns completion.
- If native subagents or a named role are unavailable, read the role guide and
  perform the work in this session. Report this plainly; never invent a tool or
  claim an independent review occurred.
- Read `.codex/docs/coordination-rules.md` for larger multi-domain work and
  `.codex/docs/directory-structure.md` for engine-specific paths.

## Authorization and scope

An explicit request to implement, fix, configure, or run a workflow authorizes
ordinary reversible work required to complete it. Do not ask again before each
file edit. Resolve routine implementation details and keep working. Ask only
when a material decision is unresolved, the requested scope must expand, or a
destructive/external action lacks authorization. Existing approval carries
forward. User instructions override template preferences.

`modes.automation` tunes collaboration, not Codex permissions. The shipped
project uses `guided`; `collaborative` is available for users who want draft
approval at meaningful milestones. Never infer permission to publish, message
others, spend money, or weaken sandbox/approval policy from an automation mode.
Prepare a concrete result before asking for a necessary final approval.

## Coding and validation

- Follow existing architecture and naming. Keep gameplay tuning data separate
  from implementation when useful, and use frame-independent time calculations.
- Keep normal C# statements on one line; wrap only lines that are too long to
  read comfortably. Preserve the project's established brace style.
- Put Unity code under `Assets/` or appropriate `Packages/`; Unreal module code
  under `Source/<Module>/`; Godot may use `src/`. Preserve an existing layout.
- Make validation proportional to the change. Test meaningful behavior and
  regressions; avoid tests that only mirror trivial implementation.
- A parse/build check is not a playtest. Player-visible game changes need a real
  engine run and retained observation where available. State precisely when an
  engine, device, or tool is absent and what was not tested.
- For framework changes, run `python3 tools/studio.py validate` and relevant
  tests under `tools/tests/`. `studio-tests/` evaluates the studio; game tests
  remain in their engine's proper test directories.

## Conditional rules

Markdown in `.codex/rules/` is reference material, not automatically matched
Codex policy. Explicitly read the matching rule before changing that area:

| Area | Read |
| --- | --- |
| Gameplay, movement, combat | `.codex/rules/gameplay-code.md` |
| Engine/core systems | `.codex/rules/engine-code.md` |
| AI or networking | `.codex/rules/ai-code.md` or `.codex/rules/network-code.md` |
| UI or shaders | `.codex/rules/ui-code.md` or `.codex/rules/shader-code.md` |
| Design or narrative | `.codex/rules/design-docs.md` or `.codex/rules/narrative.md` |
| Data, scenes, resources | `.codex/rules/data-files.md` or `.codex/rules/scene-files.md` |
| Game tests, prototypes | `.codex/rules/test-standards.md` or `.codex/rules/prototype-code.md` |
| Studio skills, role memory | `.codex/rules/skill-authoring.md` or `.codex/rules/agent-memory.md` |

Native command policies use `.rules` files. Codex's sandbox and approvals are
the access controls; Markdown instructions and hooks are not full boundaries.

## State and handoff

Keep useful progress in `production/session-state/active.md` when session state
is enabled. After context loss, reread it and verify against actual files.
Read `.codex/docs/context-management.md` when a task needs a longer checkpoint.
Helpers in `.codex/scripts/` emit observations, never verdicts. Interpret their
findings with effective project settings. Finish with what changed, what was
verified, and concrete remaining limitations.
