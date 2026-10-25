# Upgrading Codex GameDev Kit

Keep project configuration and game content. Review updates from this
repository on a branch and check `CHANGELOG.md` for changes.

1. Check your working tree and preserve existing work.
2. Compare `.agents/skills`, `.codex/roles`, `.codex/docs`, helpers, and tests.
3. Merge customized `AGENTS.md`, `project.yaml`, `.codex/config.toml`, and
   `.codex/hooks.json` deliberately. Do not replace them wholesale.
4. Regenerate agents with `python3 tools/studio.py sync-agents`.
5. Run `python3 tools/studio.py validate` and the relevant tests.
6. Review changed hook commands through Codex's `/hooks` interface; old trust
   does not automatically authorize a new command hash.
7. Open a new Codex session if changed instructions are not picked up.

The installer's conflict report is a merge checklist, not a reason to delete
customized files. It intentionally has no force-overwrite switch.
