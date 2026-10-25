# $setup-engine — Sections 8 and 8.5: Verify and Read Back

## 8. Verify the Engine Reference Instruction

Read `AGENTS.md` and confirm the instruction following
`ENGINE-REFERENCE-IMPORT` is:

~~~markdown
Read `docs/engine-reference/<engine>/VERSION.md` before engine-specific work.
~~~

The directory must match `engine.name` in `project.yaml`. Read the referenced
file explicitly and confirm its version matches the configuration. A path
written in Markdown does not establish that the file exists or was loaded.

Section 4 already writes the instruction. Do not request authorization a
second time or duplicate the edit. If it is wrong, correct the incomplete
Section 4 change within the already requested engine setup.

## 8.5 Check the Engine Configuration

Run from the project root:

~~~bash
bash .codex/scripts/project-coherence.sh
~~~

The helper compares configuration, engine reference files, available project
files, the installed binary and command targets. Read its output rather than
equating exit code zero with agreement.

Resolve unexpected `[DIFFERS]` lines from this setup before finishing.
A configured test runner that the later `$test-setup` step has not installed
is an expected outstanding dependency; report its exact path and that step,
without changing the command merely to suppress the finding.

A `[NOT CHECKED]` result is not a pass. Explain missing binaries or project
files and state which comparisons could not run.

If role guides were changed in Section 9, run
`python3 tools/studio.py sync-agents` and
`bash .codex/scripts/agent-check.sh` afterwards, and report any role/config
mismatch. Role changes affect newly spawned agents after configuration reload;
do not claim they changed a subagent that is already running.
