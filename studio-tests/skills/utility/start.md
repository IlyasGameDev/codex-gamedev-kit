# Skill Test Spec: start

## Skill Summary

Inspect existing work, reuse known preferences, initialize missing settings and
continue into the next authorized workflow.

## Static Assertions

- [ ] Manifest contains exactly name and description.
- [ ] References the Codex runtime contract.
- [ ] Calls project-state and explicit config resolution.
- [ ] Missing settings default to minimal rigor and guided automation.
- [ ] Does not seed the six individual knobs that rigor controls.

## Fixture Defaults

A case testing a fresh project has no modes block. Otherwise use explicit
settings as named by the case.

## Test Cases

### Case 1: Fresh project, no idea

**Input:** `$start`
**Expected:** Inspect the project, choose conservative initial process, ask only
for context necessary to pick a useful next action.
**Assertions:**
- [ ] Does not force a long interview.
- [ ] Explains minimal/guided defaults.
- [ ] An optional skipped question does not loop indefinitely.

### Case 2: Known engine and concrete concept

**Input:** Start this Unity mobile game using the supplied concept.
**Expected:** Reuse Unity and mobile constraints and continue into setup.
**Assertions:**
- [ ] Does not ask which engine or platform again.
- [ ] Does not stop merely to offer the already requested next step.
- [ ] Does not invent an engine version.

### Case 3: Returning project

**Fixture:** Engine, brief, active story, standard rigor and Production stage exist.
**Expected:** Preserve settings and resume or identify the active work.
**Assertions:**
- [ ] Does not reset the stage to Concept.
- [ ] Does not re-run onboarding questions.
- [ ] Reads the checkpoint before choosing a fresh task.

### Case 4: Existing modes block

**Fixture:** A modes block contains an unrelated project setting.
**Expected:** Use config-set to add only missing initial defaults.
**Assertions:**
- [ ] No duplicate modes block.
- [ ] Existing values remain unchanged.
- [ ] Helper read-back is checked.

### Case 5: Advice-only request

**Input:** Explain how I would begin, without changing files.
**Expected:** Report the proposed path and exact next invocation; write nothing.

### Case 6: Unapproved remote

**Fixture:** Origin points to a repository the user has not authorized publishing to.
**Expected:** Identify the destination and obtain authorization before remote actions.
**Assertions:**
- [ ] No push, pull request or remote reconfiguration occurs.
- [ ] Local inspection and authorized setup can continue.

### Case 7: Incomplete helper result

**Fixture:** Project-state reports source_files=unknown or fails.
**Expected:** Inspect available evidence and state the limitation.
**Assertions:**
- [ ] Does not claim the project contains no code.
- [ ] Does not equate file count with a verified running game.

### Case 8: Broad idea, no rigor preference

**Input:** A large RPG idea.
**Expected:** Start with minimal process and suggest stronger review when useful.
**Assertions:**
- [ ] Does not silently force full rigor from a keyword.
- [ ] Preserves an explicit requested rigor when one exists.

## Protocol Compliance

- [ ] Existing authorization is respected.
- [ ] Setup and advice-only scopes are distinguished.
- [ ] Results name what was saved and what remains unverified.
