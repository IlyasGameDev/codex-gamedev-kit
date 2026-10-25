# Studio Framework Validation

This folder contains specifications for the studio framework. Game tests belong
in the game's configured test root. Read the root `AGENTS.md` and
`.codex/docs/codex-runtime.md` before evaluating these specifications.

## Sources and Scope

- Skills: `.agents/skills/<name>/SKILL.md` and their references.
- Native agents: `.codex/agents/<name>.toml`.
- Editable agent role guides: `.codex/roles/<name>.md`.
- Catalog: `studio-tests/catalog.yaml`; its `spec:` path and `category:` are authoritative.
- Category metrics: `studio-tests/quality-rubric.md`.
- Results: `studio-tests/results/` when saving a report is authorized.

Read both the native TOML and role guide for an agent. Runtime instructions
must reflect the role source. Follow explicit read instructions; do not assume
that `@` imports or files merely named in prose were automatically loaded.

## What the Modes Establish

`$skill-test static` checks structure and runtime compatibility.
`spec` inspects written scenario coverage; `category` applies a domain rubric;
`audit` inventories coverage. None of those modes alone establishes that a
workflow ran successfully.

Label a real executed behavioral test separately and retain its task, fixture,
outputs and failures. Use a disposable project and raw task inputs. Do not leak
the expected answer or the proposed fix into a fresh agent's test prompt.
A failed helper, unreadable file or unexecuted case is never a passing test.

## Platform and Authorization Interpretation

Test the supported Codex runtime mechanics: native
`name`/`description` skill manifests, native TOML agents and explicit helper
execution. Do not reintroduce obsolete model aliases, manifest tool grants,
automatic preloads, argument substitution or shell preprocessing.

The current request and runtime authorization contract take precedence over
legacy conversational examples. In `guided` mode, already authorized ordinary
edits should proceed. Consequential decisions, scope changes and publication
must still respect their actual authorization. A prose question is an
acceptable fallback when an optional question widget is unavailable.
Do not fail a workflow solely because it lacks the literal phrase “May I write”.

## Fixture Defaults

Unless a case specifies otherwise, historical domain cases explicitly use:

~~~yaml
modes:
  rigor: minimal
  automation: collaborative
~~~

The explicit fixture is independent of the template's new `guided` default.
A case testing absent settings omits this block. Explicit sub-knobs override
rigor expansion, and `project.local.yaml` exists only when the case names it.
Respect the intended engine, state and input data. Do not alter a fixture to
make an implementation pass.

## Reporting

Apply `PASS`, `PARTIAL`, `FAIL` or `NOT ASSESSED` to specification assertions.
Name missing inputs and preserve denominator counts. Known failures take
priority over missing evidence; unassessed required evidence prevents a clean
aggregate result. Distinguish inapplicable checks from checks that could not run.

Preserve valid domain expectations when adapting platform-specific assertions.
Fix a wrong assertion toward documented behavior, never merely toward the
current output. Record only checks actually performed and real execution dates.

This folder can be removed from a game project: static inspection still works,
while specification/category coverage becomes unavailable and must be reported.
