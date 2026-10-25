# $setup-engine — Section 4: Update AGENTS.md

## 4. Update the Technology Stack

Use the engine, version and language already established by the user, the
existing project and the preceding steps. For Godot, read
`references/godot-language-config.md` for the GDScript, C# or mixed variant.
For Unreal, determine whether the existing project uses C++, Blueprints or
both; ask only if that material choice remains unresolved.

Read `AGENTS.md` before editing. Update its Technology Stack section and keep
unrelated project instructions. Configuring the requested engine authorizes
these routine settings changes; apply the current automation mode to any
unresolved consequential choice.

For Unity:

~~~markdown
- **Engine**: Unity [verified version]
- **Language**: C#
- **Build System**: Unity Build Pipeline
- **Asset Pipeline**: Unity Asset Import Pipeline [plus packages actually installed]
~~~

For Unreal:

~~~markdown
- **Engine**: Unreal Engine [verified version]
- **Language**: [C++, Blueprint, or both, according to the project]
- **Build System**: Unreal Build Tool
- **Asset Pipeline**: Unreal Content Pipeline
~~~

Do not assume Addressables or a rendering pipeline is installed merely because
it is a common choice. Read project packages and settings first.

### Explicit engine reference

Codex does not expand automatic `@` file imports. In the same `AGENTS.md`
edit, locate the `ENGINE-REFERENCE-IMPORT` marker and replace the following
instruction with:

~~~markdown
Read `docs/engine-reference/<engine>/VERSION.md` before engine-specific work.
~~~

Use the lowercase directory name `godot`, `unity` or `unreal`. The marker name
is retained for upgrade compatibility; it marks an ordinary instruction, not
a runtime import. Do not create a second marker or duplicate the section.
When adopting an existing `AGENTS.md` without the marker, add one compact
Engine Version Reference section while preserving its existing contents.

Section 7 creates the target reference directory if necessary. Reconfiguring
the engine rewrites this one instruction rather than accumulating references
to unrelated engines.
