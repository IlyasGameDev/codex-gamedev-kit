# Contributing

The editable studio source is ordinary Markdown, Python, Bash, JSON, and TOML.
Read `AGENTS.md` and `.codex/docs/codex-runtime.md` first.

- Skills: `.agents/skills/<name>/SKILL.md` with simple `name` and `description`
  frontmatter. Keep argument hints in the invocation section. Use explicit
  commands instead of shell-preprocessing syntax.
- Roles: edit `.codex/roles/<name>.md`, then run `python3 tools/studio.py sync-agents`.
  Generated `.codex/agents/*.toml` must contain the full source body.
- Helpers: `.codex/scripts/`; emit facts, not policy verdicts.
- Hooks: `.codex/hooks/`; native payload behavior is tested in `tools/tests/test_hooks.py`.
- Templates: `.codex/docs/templates/`; preserve useful game-development expertise.
- `studio-tests/` holds behavioral rubrics; `tools/tests/` holds executable framework tests.

Run:

```bash
python3 tools/studio.py validate
python3 -m unittest discover -s tools/tests -v
python3 -m unittest discover -s studio-tests -p 'test_codex_inspectors.py' -v
```

If configuration or execution policy changed, also run
`python3 tools/check_codex_runtime.py` with a current Codex binary. Never remove
checks to conceal a failure. Avoid adding provider-specific model aliases or
claims that a hook, file import, tool grant, memory, or worktree exists without
verifying it in the target Codex runtime.

Update `.codex/studio-manifest.json` when deliberately removing baseline roles
or workflows. Preserve copyright and license notices. Publish changes
only to a repository you are authorized to update.
