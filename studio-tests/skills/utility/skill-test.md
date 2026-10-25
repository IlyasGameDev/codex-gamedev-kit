# Skill Test Spec: skill-test

## Skill Summary

Inspect native Codex skills and agents in static, spec, category or audit mode.
Static observations are not live behavioral execution.

## Static Assertions

- [ ] Manifest has exactly nonempty `name` and `description`.
- [ ] Invocation documents all four modes and defaults to audit.
- [ ] Reads `.codex/docs/codex-runtime.md`.
- [ ] Inspects native agent TOML and matching role guide.
- [ ] Defines seven Codex-relevant checks and missing-evidence outcomes.
- [ ] Does not require arbitrary phase counts or obsolete runtime metadata.

## Fixture Defaults

Use minimal rigor and guided automation unless the case specifies otherwise.

## Test Cases

### Case 1: Valid native skill

**Fixture:** A skill with name/description, accurate invocation, runtime contract,
one meaningful phase, existing references and a complete authoring workflow.
**Expected:** No failure solely for having one phase or no assessment verdict.
**Assertions:**
- [ ] Check 1 passes with only the two manifest keys.
- [ ] Heading counts are observations, not a mandated threshold.
- [ ] Assessment-vocabulary check is N/A for a pure authoring task.

### Case 2: Unsupported runtime dependency

**Fixture:** A skill depends on automatic shell preprocessing or an unavailable
tool without a fallback.
**Expected:** A concrete portability failure naming the active instruction.
**Assertions:**
- [ ] Does not “fix” it by adding unsupported manifest fields.
- [ ] Distinguishes an active dependency from a documentation example.

### Case 3: Agent source and runtime differ

**Fixture:** The native TOML contains older instructions than its role guide.
**Expected:** The agent is found and source synchronization is flagged.
**Assertions:**
- [ ] Reads both files.
- [ ] Identifies `python3 tools/studio.py sync-agents` as the repair.
- [ ] Does not compare against a provider-specific model alias.

### Case 4: Missing or unreadable source

**Fixture:** One selected skill cannot be read while others are readable.
**Expected:** It remains in the denominator and is `NOT ASSESSED`.
**Assertions:**
- [ ] Other results remain visible.
- [ ] Zero findings in an unread file is not a passing result.

### Case 5: Split skill and missing reference

**Fixture:** Steps live in `references/`; one named reference is absent.
**Expected:** Read available references and flag the missing one.
**Assertions:**
- [ ] Manifest checks read SKILL.md, not a reference's metadata.
- [ ] Workflow checks consider the whole available skill.

### Case 6: Specification inspection

**Fixture:** A catalog entry points to an agent case with a missing input.
**Expected:** Resolve the agent, use its spec path, and mark the corresponding
assertion `NOT ASSESSED`.
**Assertions:**
- [ ] Says the case was inspected, not executed.
- [ ] Does not invent the missing input.

### Case 7: Unknown category

**Fixture:** A catalog category has no rubric section.
**Expected:** Category dimension is `NOT ASSESSED`; static findings remain valid.

### Case 8: Audit with an uncataloged skill

**Fixture:** An additional skill exists on disk but is absent from catalog.
**Expected:** Include it as an uncovered item in the inventory.
**Assertions:**
- [ ] Derives the inventory from disk.
- [ ] Does not fabricate a test date.
- [ ] Reports missing native agents or orphan roles separately.

## Protocol Compliance

- [ ] Read-only review does not modify its target.
- [ ] Requested reports follow current authorization and preserve existing files.
- [ ] Helper output is interpreted with evidence.
- [ ] Missing execution is explicit.
