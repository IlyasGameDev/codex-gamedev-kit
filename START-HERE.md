# Start here

## Existing Unity game

From the extracted `codex-game-studios` folder, replace the sample path:

```bash
python3 tools/studio.py install "/path/to/MyUnityGame" --engine unity
```

The installer keeps game scripts/assets and existing project configuration.
It refuses conflicting studio files and does not install dependencies.
If it reports existing `.codex/config.toml` or `.codex/hooks.json`, review and
merge the supplied `.studio-example` files to enable those settings.

Open the Unity project's root in Codex. Inspect and trust the project settings.
For automatic lifecycle checks, review and approve hooks with `/hooks`.

Then type in Codex:

```text
$setup-engine unity
```

Follow with a concrete task, for example:

```text
Use $code-review to inspect my current Unity scripts and report the most
important bugs with file paths and proposed fixes.
```

## New project

Open the extracted template folder and run:

```bash
python3 tools/studio.py doctor
python3 tools/studio.py validate
git init
codex
```

In Codex, use `$start`, then `$setup-engine` when the engine is known. Try
`$brainstorm` for a game idea or `$help` for workflow guidance.

## Requirements and conventions

- Current Codex; Python 3.11+; Git; Bash. Windows: Git Bash/WSL and Python on PATH.
- On Windows, `python` or `py -3.11` can replace `python3`.
- `$name` invokes a studio skill; `/skills` is Codex's skill picker.
- The studio inherits your selected Codex model.
- Default workflow rigor is minimal and interaction mode is guided.
- Install the engine and build tools separately. Configuration checks are not
  game builds or playtests.
