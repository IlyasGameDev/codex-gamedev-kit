# Setup requirements

| Tool | Purpose |
| --- | --- |
| Current Codex client | Loads AGENTS.md and skills; native agent/hook support depends on client/version. |
| Python 3.11+ | Installer, validation, hook adapter, and project-config helpers; no pip dependencies. |
| Bash | Existing studio helpers and hook launcher; use Git Bash or WSL on Windows. |
| Git | History and commit checks; inspect an unpacked template before `git init`. |

Install Codex following https://developers.openai.com/codex/cli/ . For npm:

```bash
npm install -g @openai/codex
```

The studio installer does not install dependencies, sign in, or change global
Codex settings. From the project root:

```bash
python3 tools/studio.py doctor
python3 tools/studio.py validate
```

On Windows, `py -3.11` or a Python 3.11+ `python` can replace `python3`. Ensure
Bash and Python 3 are visible on the PATH Codex uses. `jq` is optional.

## Trust

Inspect and trust the project configuration in Codex. Separately inspect and
enable hooks through `/hooks` if desired. No script approves itself. Skills
remain usable with hooks disabled, but checks will not run automatically.
Native configuration was checked with Codex CLI 0.163.0. Older clients may need
updating or the sequential role fallback. Hosted interfaces may not load local
CLI configuration.

## Engines

Install the engine and build tools separately. `$setup-engine` detects or
configures the selected version; writing configuration does not install Unity,
Godot, Unreal, Xcode, or Android SDKs. Verify against the actual engine project.
