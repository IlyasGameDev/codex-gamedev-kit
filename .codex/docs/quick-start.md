# Quick start

Read `START-HERE.md` at the project root for installation and Unity examples.

1. Run `python3 tools/studio.py doctor` and `python3 tools/studio.py validate`.
2. Open the game root in Codex and inspect/trust the project configuration.
3. Review optional lifecycle hooks through `/hooks` before enabling them.
4. Use `$start`, or `$setup-engine unity` for an existing Unity game.
5. Use `$help` for the next useful workflow, or ask for the concrete work directly.

The studio has 74 skills, 49 native specialist configurations, and 62 templates.
Models inherit your session settings. Workflows run with available tools and
fall back to sequential role passes when subagents are unavailable.

Skills are in `.agents/skills/`; native agents in `.codex/agents/`; editable role
guides in `.codex/roles/`. Codex settings are in `.codex/config.toml`, hooks in
`.codex/hooks.json`, and game configuration in `project.yaml`.

The default is minimal rigor with guided collaboration. See
`.codex/docs/codex-runtime.md` for authorization and platform behavior, and
`docs/WORKFLOW-GUIDE.md` for the complete game-development pipeline.
