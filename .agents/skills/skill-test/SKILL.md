---
name: skill-test
description: "Inspect Codex studio skills and native agents using static checks, behavioral specifications, category rubrics, or a coverage audit."
---

## Codex invocation

Use `$skill-test static [skill-or-agent-name | all] | spec [name] | category [name | all] | audit`. Interpret arguments from the user's message; no shell substitution is performed.
Before executing the workflow, read `.codex/docs/codex-runtime.md` for tool mapping, delegation, and approval behavior.

# Skill and Agent Quality Review

Inspect the studio framework, never the game's test suites. Source skills live at
`.agents/skills/<name>/SKILL.md`; native agent definitions live at
`.codex/agents/<name>.toml` and their editable role guides at
`.codex/roles/<name>.md`. The catalog's `skills:` and `agents:` entries are separate.

These modes inspect instructions. A static or specification pass does not prove
that Codex executed the workflow successfully. A behavioral claim requires an
actual run in a disposable project with the inputs, resulting files, and failures
recorded. Never describe reading a scenario as running its test.

Run from the project root:

~~~bash
bash .codex/hooks/yaml-helper.sh resolve_config --keys automation
~~~

A requested review authorizes its read-only checks. Save reports when requested
or when the workflow's configured automation allows it; follow the runtime
contract for any unresolved write decision. Do not repeatedly seek authorization
already supplied. Do not change the reviewed skill during this review.

## Phase 1: Resolve Scope

Default to `audit` when no mode is provided. For an invalid mode, show the
invocation syntax. Find a named skill or agent on disk, and use
`studio-tests/catalog.yaml` to locate its specification and category. Do not
interpret a name such as `help` as a request for this command's help.

A missing catalog does not stop `static`. It makes absent specification or
category coverage `NOT ASSESSED`. Derive the inventory from disk so uncataloged
skills and agents are visible.

## Phase 2: Inspect

### Static mode: seven checks for skills

Run `bash .codex/scripts/skill-lint.sh <name>` or `all`. Read the target
`SKILL.md` and its relevant references to interpret the observations.

| Check | Required evidence |
| --- | --- |
| 1. Manifest | Valid scalar YAML frontmatter containing exactly nonempty `name` and `description`. Name matches its folder. Put UI and invocation policy metadata in `agents/openai.yaml`, not unsupported keys in the manifest. |
| 2. Workflow | Clear steps that fit the task, with inputs, outputs and failure handling. The helper counts headings; it does not impose an arbitrary minimum or demand artificial phases for a simple skill. |
| 3. Verdicts | A workflow making an assessment defines its outcome vocabulary and a `NOT ASSESSED` equivalent for missing evidence. A pure authoring skill does not need a verdict merely to satisfy a word counter. |
| 4. Authorization and tools | The runtime contract is referenced and followed. Ordinary authorized edits proceed; consequential or out-of-scope actions require a concrete decision. Use available Codex tools, with a stated fallback when a required capability is absent. Skill text does not grant shell permissions. |
| 5. Completion | Explain the result, incomplete work and useful next action. Do not force a new question or another workflow after the user's request is complete. |
| 6. Portability and references | Referenced files exist; configuration commands are explicit; no automatic shell preprocessing, argument substitution or instruction imports are assumed. Native invocation policy is in `agents/openai.yaml`. |
| 7. Invocation | The body documents `$skill-name` and argument modes accurately. Read arguments from the user's request, never a magic environment variable. |

Mark each applicable check `PASS`, `WARN`, `FAIL` or `NOT ASSESSED` with a file
and heading or line reference. Unsupported runtime assumptions and missing
required manifest fields are failures. Missing access is not a pass. A check
that does not apply is marked `N/A` with its reason.

### Native agent and delegation checks

For a named agent, run:

~~~bash
bash .codex/scripts/agent-check.sh --agent <name>
~~~

For `static all`, run it without a name. Read both the native TOML and role
guide. Confirm nonempty `name`, `description` and `developer_instructions`,
a matching name, domain boundaries, and role-source synchronization. Model and
reasoning settings inherit unless the user deliberately configures valid
overrides. Do not require a legacy model alias or a turn limit.

Inspect the helper's delegation blocks: each brief should provide an objective,
relevant inputs, file ownership, output format and validation expectations.
Independent work can run in parallel, but dependent steps wait. Missing
subagent support must have a sequential-role fallback and must be disclosed.
A subagent returns unresolved questions to its parent.

### Compatibility inventory

Run `bash .codex/scripts/compat-inventory.sh`, optionally with
`--skill <name>` or `--agent <name>`. It reports native constructs and potential
legacy tokens. Interpret each hit: documentation examples may name unsupported
syntax, while an active workflow depending on an unavailable tool is a defect.
The inventory itself never declares compatibility.

### Specification mode

Read the catalog entry, its `spec:` file, the complete target instructions and
the relevant root/runtime rules. For agents include the native TOML. Evaluate
the static assertions, each case, and protocol assertions against those texts.
Respect the fixture's explicit engine, rigor and automation settings; do not
silently substitute current defaults.

Use `PASS`, `PARTIAL`, `FAIL` or `NOT ASSESSED` for each assertion. Quote only
enough of the source to identify support or contradiction. Missing input or
an unreadable target is `NOT ASSESSED`, not zero failures.

To run a real behavioral case, create an isolated fixture first, supply its raw
task and inputs to a fresh agent when available, and retain actual outputs.
Never pass the expected answer or the suspected fix into the test agent's task.
State which cases were inspected and which were executed.

### Category mode

Read the matching section of `studio-tests/quality-rubric.md` using the
catalog's category. Apply its metrics to the workflow's actual scope. Agent
tiers and rubric categories are distinct. Missing categories are
`NOT ASSESSED`. Preserve rigor and authorization distinctions in the rubric.

### Audit mode

Compare on-disk skills, native agents, role guides and catalog entries. Report:

- Total available and cataloged skills and agents.
- Missing or duplicate catalog entries and missing spec files.
- Missing native TOMLs, orphan role guides and source-sync findings.
- Last recorded inspections, and any evidence of executed behavioral tests.
- Coverage gaps and the most consequential next review.

Do not fabricate test dates or a previous result. An entry with no recorded test
is untested.

## Phase 3: Report and Optional Persistence

Show a concise table of checks, evidence and outcomes. The aggregate result is
`COMPLIANT`, `WARNINGS`, `NON-COMPLIANT` or `NOT ASSESSED`. Known failures take
priority; otherwise an unassessed required check prevents a clean result.
Report denominator counts and what was excluded.

When saving results is authorized, write
`studio-tests/results/<name>-<date>.md` and update only the corresponding
catalog entry's tracking fields. Preserve previous work and avoid replacing
an existing same-day report without inspecting it. The report must distinguish
an instruction inspection from an executed behavioral run.

Finish with the material findings. Recommend `$skill-improve <name>` only when
a concrete defect warrants it.
