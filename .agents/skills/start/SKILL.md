---
name: start
description: "Start a game project with Codex Game Studios, inspect existing work, choose the appropriate amount of process, and continue into the next useful workflow."
---

## Codex invocation

Use `$start [game idea or existing-project goal]`. Interpret arguments from the user's message; no shell substitution is performed.
Before executing the workflow, read `.codex/docs/codex-runtime.md` for tool mapping, delegation, and approval behavior.

# Start the Studio

Inspect what is already known and move toward the user's stated goal. Reuse
engine, platform, concept and preferences already provided. Do not run a
mandatory interview or ask permission for routine setup already requested.

## Phase 1: Inspect the Project

From the project root, run:

~~~bash
bash .codex/scripts/project-state.sh
bash .codex/hooks/yaml-helper.sh resolve_config --keys workflow,review_mode,automation,team.size
~~~

Read `project.yaml` and any relevant `project.local.yaml` settings. Inspect an
existing session checkpoint before recommending a fresh workflow.

Use the helper's engine, source-file, concept, GDD, ADR, prototype, sprint,
milestone and story observations. A source count of `unknown` is not zero.
If a helper fails, disclose it and inspect the same files directly. A file
count is not evidence that a playable game works.

Check the repository remote before any later remote action. Publish only to
the destination authorized by the user. Inspection itself does not modify
remotes or publish anything.

## Phase 2: Resolve the Goal

Use the current request and existing files to choose a route:

| Situation | Useful next action |
| --- | --- |
| No idea yet | `$brainstorm open` |
| Theme or vague idea | `$brainstorm <their idea>` |
| Clear concept, no configured engine | `$setup-engine <known engine>`, then capture a short brief |
| Existing game or design documents | `$project-stage-detect`; use `$adopt` when format compatibility needs checking |
| Engine, concept and active stories already exist | Resume the relevant story or use `$help` to identify the next unmet step |

Ask a short context question only when its answer materially changes this
route. If an optional question is skipped, use conservative defaults and state
the assumption. Do not repeat the question indefinitely. Never treat a missing
answer as permission for a consequential action.

## Phase 3: Set the Initial Process

Keep existing `modes.rigor` and `modes.automation`. For a new project without an
explicit preference, use `minimal` rigor and `guided` automation. A large game
idea is a reason to suggest a stronger review mode later, not a reason to
silently impose a lengthy documentation pipeline.

Rigor sets six underlying defaults. Do not seed those six keys in
`project.yaml`: `modes.review_mode`, `modes.workflow`, `docs.density`,
`qa.level`, `modes.story_granularity` or `team.size`. Explicit values would
override future rigor changes.

When the user requested project setup, summarize the proposed initial settings
and save the missing values using the helpers:

~~~bash
bash .codex/scripts/config-set.sh modes.rigor minimal
bash .codex/scripts/config-set.sh modes.automation guided
~~~

If this is a fresh project with no recorded stage, set `Concept` using
`bash .codex/scripts/set-stage.sh "Concept"`. Preserve an existing stage;
moving an existing project through a release or phase gate requires the
appropriate evidence and authorization. If the user requested advice only,
show the proposed settings without writing them.

Confirm the helper read-back matches each write. If one fails, name the
setting that was not saved and continue with unaffected work.

## Phase 4: Explain the Path and Continue

For `minimal` rigor, the normal path is:

1. `$setup-engine` — configure the existing or chosen engine.
2. `$brainstorm` — save a short `design/game-brief.md`.
3. `$create-stories` — turn the MVP into a small set of stories.
4. `$dev-story` and `$story-done` — implement and verify one playable slice.

The first two may swap when the user wants to explore an idea first.
For `standard` or `full`, consult `.codex/docs/workflow-catalog.yaml` and
`.codex/docs/workflow-modes.md` for the applicable design, architecture,
review and QA requirements; do not dump the whole catalog into the reply.

If the current request authorizes the next concrete step, read that skill and
continue. If the user asked only how to begin, provide the exact next invocation
and its purpose. Never claim an engine project exists until its actual project
files have been found or generated and verified.

Finish with the selected engine or the remaining engine choice, effective rigor
and automation, what was saved, and the next concrete result.
