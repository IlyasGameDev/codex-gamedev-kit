# Personal settings

Use `project.local.yaml` for studio preferences accepted by the configuration
resolver, for example:

```yaml
modes:
  automation: guided
  review_mode: solo
```

It is gitignored. `$settings --local` validates supported keys and writes them.
A shared `project.yaml` must exist first. Do not store secrets in either file.

Codex's own account/model/client settings belong in its supported user
configuration, usually `~/.codex/config.toml`. Project-wide settings use
`.codex/config.toml`. This kit does not invent a `settings.local.json` or
`config.local.toml` layer. Use the client's supported profile/settings controls.

For personal project instructions, Codex supports `AGENTS.override.md`, but it
replaces `AGENTS.md` at that directory level. Include an explicit instruction
to read `AGENTS.md` if you need to retain this project's normal instructions.
See `.codex/docs/AGENTS-local-template.md`.
