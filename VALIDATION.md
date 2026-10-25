# Validation — Codex Game Studios 1.0.0

Checked on 2026-10-25.

## Results

| Check | Result |
| --- | --- |
| Skill manifests and local workflow references | 74 valid skills |
| Role guides and generated native agent TOML | 49 guides and 49 matching configurations |
| Required specialist domain headings | All present; checked by the validator |
| Bash syntax | 52 shell files pass |
| Native hook fixtures | 26 tests pass |
| Existing-project installer fixtures | 19 tests pass |
| Framework inspector regressions | 8 tests pass |
| Native Codex strict configuration parsing | Pass with Codex CLI 0.163.0 |
| Strict parser negative control | Unknown field rejected |
| Native execution-policy behavior | 11 cases pass |
| Native hooks/list manifest discovery | Seven handlers accepted without errors or warnings; left untrusted |
| Configuration root/subdirectory agreement | Same minimal/solo/guided/individual values |
| Unity fixture detection | Engine and Assets code root detected; editor settings preserved |

## Reproduce

```bash
python3 tools/studio.py validate
python3 -m unittest discover -s tools/tests -v
python3 -m unittest discover -s studio-tests -p 'test_codex_inspectors.py' -v
python3 tools/check_codex_runtime.py
```

The optional native probe accepts `--codex /path/to/codex`. It starts no model
turn, reads no credentials, changes no actual user configuration, and grants
no trust. Its strict config test uses a disposable copy as a temporary config
layer, so it validates the schema, not the user's project trust.

## What the fixtures cover

Hooks: add/update/move/delete patches; multiple hunks; exact-context failures;
path boundaries; symlink escapes; proposed config and registry checks; actual
post-edit JSON; staged versus unstaged JSON; chained add/commit; subdirectory
and git -C behavior; missing validators; checkpoint/lifecycle logging; explicit
engine-reference reads; disabled automatic updates.

Installer: existing Unity assets/scripts/scenes/meta/package/version files are
preserved; custom AGENTS.md receives one scoped integration block; existing
project.yaml and Codex configuration are retained; repeat installs are
idempotent; dry runs write nothing; collisions stop before writing; path and
source symlinks are refused; mismatched engine requests are refused.

Inspectors: missing/invalid metadata and references, malformed TOML, stale
role generation, and unreadable inputs remain visible rather than appearing as
successful checks.

## Limits

No paid model session was launched. These checks do not prove that all 74 skills
will satisfy every real game task, that the user's client has granted hook
trust, or that a complete Unity, Godot, or Unreal game runs correctly. No
engine build, visual playtest, iOS/Android device test, or Windows/macOS engine
execution was performed here. Native agents fall back to explicitly disclosed
sequential role passes when a host lacks delegation.

The shell/patch hook adapter covers documented payloads; arbitrary shell scripts
can change files without an individual edit event. Sandbox and approvals remain
the access controls.
