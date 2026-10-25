---
name: skill-improve
description: "Improve one Codex studio skill using an evidence-based inspect, fix, retest and keep-or-restore loop."
---

## Codex invocation

Use `$skill-improve <skill-name>`. Interpret arguments from the user's message; no shell substitution is performed.
Before executing the workflow, read `.codex/docs/codex-runtime.md` for tool mapping, delegation, and approval behavior.

# Improve a Studio Skill

Improve the requested skill and its referenced resources. Preserve unrelated
edits. A better static score establishes better written instructions; claim
better behavior only after a corresponding executed case.

## Phase 1: Resolve and Inspect

Resolve the name to `.agents/skills/<name>/SKILL.md`. If missing, show usage or
report the missing path; do not silently select another skill. Read its
references and `studio-tests/catalog.yaml` when available.

Run `$skill-test static <name>` and, when a category exists,
`$skill-test category <name>` by reading and following that skill's instructions.
These are Codex skill invocations, not shell commands. Record failures,
warnings, unassessed checks and their evidence. A missing category is disclosed
and excluded, not counted as a passing dimension.

If the target cannot be read, report `NOT ASSESSED`. If no concrete defect is
found, finish with that result instead of rewriting for a higher superficial score.

## Phase 2: Diagnose

Name each actual problem and the file containing it. The static checks cover:

1. Manifest name/description and native metadata placement.
2. Appropriate workflow steps and failure handling.
3. Assessment vocabulary and missing-evidence outcomes.
4. Current authorization, available tools and delegation boundaries.
5. A clear completion report.
6. Existing references and supported runtime behavior.
7. An accurate invocation and argument description.

Use the category rubric to detect domain-specific weaknesses. Do not add
arbitrary phase counts, model aliases, obsolete permission metadata or
repeated approval prompts to satisfy inherited examples.

## Phase 3: Change the Smallest Necessary Scope

Explain the intended correction and then make the authorized edits. A request
to improve the skill authorizes ordinary fixes within that scope. Seek a
decision only for a material expansion or unresolved consequential choice,
following the configured automation mode.

Before editing, retain exact pre-edit bytes of each affected file in a
temporary checkpoint. Record which files are new. Do not rely on the last
Git commit, because it may not include the user's current changes.

Keep detailed steps in the appropriate reference rather than duplicating them
in `SKILL.md`. Update `agents/openai.yaml` only when UI or implicit-invocation
behavior changes. For any companion role changes, regenerate native agents
with `python3 tools/studio.py sync-agents`.

## Phase 4: Retest

Repeat the same static and applicable category review. Exercise changed helper
scripts on a representative fixture. Where a behavioral defect motivated the
change, run that case in a disposable project if the necessary runtime is
available. Report unavailable execution explicitly.

Compare the same checks and denominators before and after. A regression in a
required check, or a required check becoming `NOT ASSESSED`, is not an
improvement even if a raw failure count becomes smaller.

## Phase 5: Keep or Restore

Keep changes when the targeted defects are resolved without a demonstrated
regression. Explain the evidence and remaining limitations.

If the attempted fix regresses the skill, restore only this run's edits from
the pre-edit checkpoint when those files still match what this run wrote.
Never use `git reset --hard` or restore from HEAD to discard preexisting edits.
If another actor changed a file meanwhile, preserve both versions and report
the conflict instead of overwriting it.

If a proposed change has a deliberate tradeoff rather than a clear regression,
present that specific decision with the prepared alternatives.

## Phase 6: Report

Report the files changed, defects fixed, checks actually executed, before/after
outcomes and remaining unassessed work. Do not claim that a static reading was
a live Codex execution. Update catalog tracking only for checks actually
performed, and save a review report when requested or allowed by the workflow.
