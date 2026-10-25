# Skill Test Spec: skill-improve

## Skill Summary

Inspect one skill, fix a demonstrated defect, retest the same checks, and keep
a verified improvement or restore only this run's changes.

## Static Assertions

- [ ] Manifest has exactly name and description.
- [ ] Uses the runtime contract and current skill-test checks.
- [ ] Checkpoints affected files before editing.
- [ ] Never restores from Git HEAD over preexisting edits.

## Fixture Defaults

Use minimal rigor and guided automation unless the case specifies otherwise.

## Test Cases

### Case 1: Correct an invalid reference

**Fixture:** A skill names a nonexistent reference while the intended reference exists.
**Expected:** Record the baseline, repair the reference, rerun the same checks.
**Assertions:**
- [ ] Targeted edit only.
- [ ] Reports actual before/after findings.
- [ ] Does not claim a behavioral test ran from static inspection.

### Case 2: Preserve uncommitted user edits

**Fixture:** Both the manifest and a reference have user edits before this run.
**Expected:** Exact pre-run bytes are retained; a failed fix restores those bytes.
**Assertions:**
- [ ] No hard reset or checkout from HEAD.
- [ ] Every affected reference is included in the checkpoint.

### Case 3: Concurrent modification

**Fixture:** Another actor edits a target after the attempted fix.
**Expected:** Preserve the competing change and report the conflict.
**Assertions:**
- [ ] Does not overwrite the new content with the checkpoint.
- [ ] Names the affected file and competing versions.

### Case 4: Unassessed required retest

**Fixture:** A change makes the target unreadable or prevents a required check.
**Expected:** Report `NOT ASSESSED` and do not call the lower raw failure count
an improvement.

### Case 5: No demonstrated defect

**Fixture:** All applicable checks pass and no behavioral problem is reported.
**Expected:** No cosmetic rewrite solely to increase a score.
**Assertions:**
- [ ] Finishes with the review result.
- [ ] Missing optional category coverage is disclosed.

### Case 6: Role resource changes

**Fixture:** A requested fix legitimately updates a companion role guide.
**Expected:** Regenerate native agent instructions and inspect the output.
**Assertions:**
- [ ] Does not leave TOML and role source inconsistent.
- [ ] Uses available Codex tools, not legacy preload metadata.

### Case 7: Execute changed helper

**Fixture:** Fix changes a deterministic script.
**Expected:** Run a relevant disposable fixture and report its result.
**Assertions:**
- [ ] Failure handling is checked when it motivated the fix.
- [ ] No live game/project state is damaged by the fixture.

## Protocol Compliance

- [ ] Ordinary authorized fixes do not trigger repeated permission questions.
- [ ] Material scope expansions still require resolution.
- [ ] Retests compare the same evidence and denominators.
