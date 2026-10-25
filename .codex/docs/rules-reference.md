# Rule references

Root `AGENTS.md` routes explicit reads of the Markdown rules below. Their
`paths:` metadata documents intended scope; Codex does not automatically match
it. Folder-scoped `AGENTS.md` files are also supported by Codex.

Native execution decisions use `.codex/rules/studio.rules`. Markdown standards,
advisory hooks, and role scopes are not filesystem access controls. The sandbox
and approval system remain authoritative.

Paths below describe Godot, Unity, and Unreal layouts. Match the actual project
layout and file type before choosing a rule; no case-insensitive matching
behavior is assumed.

| Rule File | Path Pattern | Guidance |
| ---- | ---- | ---- |
| `gameplay-code.md` | `src/gameplay/**` · `Assets/**/Gameplay/**/*.cs` · `Source/**/Gameplay/**/*.{h,cpp}` | Data-driven values, delta time, no UI references |
| `engine-code.md` | `src/core/**` · `Assets/**/Core/**/*.cs` · `Source/**/Core/**/*.{h,cpp}` | Zero allocs in hot paths, thread safety, API stability |
| `ai-code.md` | `src/ai/**` · `Assets/**/AI/**/*.cs` · `Source/**/AI/**/*.{h,cpp}` | Performance budgets, debuggability, data-driven params |
| `network-code.md` | `src/networking/**` · `Assets/**/Network(ing)/**/*.cs` · `Source/**/Network(ing)/**/*.{h,cpp}` | Server-authoritative, versioned messages, security |
| `ui-code.md` | `src/ui/**` · `Assets/**/UI/**/*.cs` · `Source/**/UI/**/*.{h,cpp}` | No game state ownership, localization-ready, accessibility |
| `design-docs.md` | `design/gdd/**` | Required sections per `modes.workflow` (8 at `full`, 5 at `standard`), formula format, edge cases |
| `narrative.md` | `design/narrative/**` | Lore consistency, character voice, canon levels |
| `data-files.md` | `assets/data/**/*.json` · `Assets/**/Data/**/*.json` · `Content/**/Data/**/*.json` | JSON validity, naming conventions, schema rules |
| `test-standards.md` | `tests/**` · `Assets/Tests/**/*.cs` · `Source/**/Tests/**/*.{h,cpp}` | Test naming, coverage requirements, fixture patterns |
| `prototype-code.md` | `prototypes/**` | Relaxed standards, README required, hypothesis documented |
| `shader-code.md` | `assets/shaders/**`, `**/*.gdshader` · `Assets/**/*.{shader,hlsl,cginc,compute,shadergraph}` · `Shaders/**`, `**/*.{usf,ush}` | Naming conventions, performance targets, cross-platform rules |
| `scene-files.md` | `**/*.tscn`, `**/*.tres` · `**/*.unity`, `**/*.prefab`, `Assets/**/*.asset` · — | Hand-edit limits for editor-written scene and asset files; Unreal `.uasset`/`.umap` are binary, and they require the engine/editor or appropriate binary-asset tooling |
| `agent-memory.md` | `.codex/agent-memory/**` | Explicit working notes; never record temporary absence as a durable fact |
| `skill-authoring.md` | `.agents/skills/**`, `.codex/roles/**` | A check must be able to report that it did not run — the five obligations for verdicts, defaults, skips, sourcing and derived coverage |


For a new file, read the relevant rule before creating it. For a manual audit
record, `log-instructions.sh` can log explicitly supplied paths; it is not an
automatic instruction-loading hook. Keep shared standards and role guidance
consistent. Unreal binary assets require suitable editor or asset tooling.
