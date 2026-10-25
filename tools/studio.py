#!/usr/bin/env python3
"""Install and validate Codex Game Studios using Python 3.11+ only.

This utility makes no network requests, invokes no model, and does not change
global Codex settings, project trust, or hook trust.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

try:
    import tomllib
except ImportError:
    raise SystemExit("Codex Game Studios requires Python 3.11 or later.")


ROOT = Path(__file__).resolve().parents[1]
KIT_VERSION = "1.0.0"
FRAMEWORK_VERSION = "1.2.0"
IGNORE_PARTS = {"__pycache__", ".git", "agent-memory", "worktrees"}
INSTRUCTION_MARKER = "<!-- codex-game-studios:begin -->"
IGNORE_MARKER = "# Codex Game Studios local state"


class StudioError(Exception):
    """An actionable validation or installation error."""


def read_manifest(path: Path) -> tuple[dict[str, str], str]:
    """Read this distribution's intentionally simple, two-scalar YAML header."""
    text = path.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) != 3 or parts[0].strip():
        raise StudioError(f"{path}: missing YAML frontmatter")
    fields = {}
    for line in parts[1].splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, separator, value = line.partition(":")
        if not separator or key != key.strip():
            raise StudioError(f"{path}: use simple scalar manifest fields")
        key, value = key.strip(), value.strip()
        if key in fields:
            raise StudioError(f"{path}: duplicate field {key}")
        if value.startswith('"'):
            value = json.loads(value)
        elif value.startswith("'") and value.endswith("'"):
            value = value[1:-1].replace("''", "'")
        if not isinstance(value, str) or not value:
            raise StudioError(f"{path}: empty or non-string field {key}")
        fields[key] = value
    if set(fields) != {"name", "description"}:
        raise StudioError(f"{path}: skill manifests use only name and description in frontmatter")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", fields["name"]) or len(fields["name"]) > 64:
        raise StudioError(f"{path}: invalid name {fields['name']!r}")
    return fields, parts[2].strip() + "\n"


def agent_text(role_path: Path) -> str:
    fields, body = read_manifest(role_path)
    # JSON quoted strings are a compatible subset of TOML basic strings.
    quote = lambda value: json.dumps(value, ensure_ascii=False)
    return (
        f"# Generated from .codex/roles/{role_path.name}; edit that source.\n"
        "# Regenerate with: python3 tools/studio.py sync-agents\n"
        f"name = {quote(fields['name'])}\n"
        f"description = {quote(fields['description'])}\n"
        f"developer_instructions = {quote(body)}\n"
    )


def sync_agents(root: Path, check: bool = False) -> int:
    source = root / ".codex/roles"
    destination = root / ".codex/agents"
    roles = sorted(source.glob("*.md"))
    if not roles:
        raise StudioError("No role guides found in .codex/roles")
    changed = []
    for role in roles:
        generated = agent_text(role)
        target = destination / (role.stem + ".toml")
        if target.is_symlink():
            raise StudioError(f"Refusing to overwrite symlink: {target}")
        if not target.exists() or target.read_text(encoding="utf-8") != generated:
            changed.append(role.stem)
            if not check:
                destination.mkdir(parents=True, exist_ok=True)
                target.write_text(generated, encoding="utf-8")
    if check and changed:
        raise StudioError("Agent configs need regeneration: " + ", ".join(changed))
    print(f"Agents: {len(roles)}; {'outdated' if check else 'updated'}: {len(changed)}")
    return 0


def validate(root: Path, json_output: bool = False) -> int:
    errors, warnings = [], []
    counts = {"skills": 0, "roles": 0, "agents": 0, "shell_scripts": 0}
    skill_names = set()
    role_names = set()
    legacy = re.compile(r"CLAUDE_(?:SKILL_DIR|PROJECT_DIR|CODE)|\$ARGUMENTS|^!`", re.M)
    for path in sorted((root / ".agents/skills").glob("*/SKILL.md")):
        try:
            fields, body = read_manifest(path)
            if fields["name"] != path.parent.name:
                raise StudioError(f"{path}: name must match skill folder")
            if fields["name"] in skill_names:
                raise StudioError(f"{path}: duplicate skill name")
            skill_names.add(fields["name"])
            counts["skills"] += 1
            if legacy.search(body):
                errors.append(f"{path.relative_to(root)}: legacy runtime construct")
            for reference in re.findall(r"\]\((references/[^)#]+)(?:#[^)]*)?\)", body):
                if not (path.parent / reference).is_file():
                    errors.append(f"{path.relative_to(root)}: missing {reference}")
            for reference in re.findall(r"`(references/[a-zA-Z0-9_.\-/]+\.md)`", body):
                if not (path.parent / reference).is_file():
                    errors.append(f"{path.relative_to(root)}: missing {reference}")
        except (StudioError, ValueError, OSError) as exc:
            errors.append(str(exc))
    for path in sorted((root / ".codex/roles").glob("*.md")):
        try:
            fields, body = read_manifest(path)
            role_names.add(fields["name"])
            counts["roles"] += 1
            if fields["name"] != path.stem:
                errors.append(f"{path.relative_to(root)}: role name does not match filename")
            target = root / ".codex/agents" / (path.stem + ".toml")
            config = tomllib.loads(target.read_text(encoding="utf-8"))
            counts["agents"] += 1
            if any(config.get(key) != fields[key] for key in ("name", "description")):
                errors.append(f"{target.relative_to(root)}: role metadata is out of sync")
            if config.get("developer_instructions", "").strip() != body.strip():
                errors.append(f"{target.relative_to(root)}: instructions are out of sync")
        except (StudioError, ValueError, OSError) as exc:
            errors.append(str(exc))
    for path in (root / ".codex/agents").glob("*.toml"):
        if path.stem not in role_names:
            errors.append(f"{path.relative_to(root)}: no matching role source")
    for required in ("AGENTS.md", "project.yaml", ".codex/config.toml", ".codex/hooks.json",
                     ".codex/docs/codex-runtime.md", ".codex/rules/studio.rules"):
        if not (root / required).is_file():
            errors.append(f"Missing required file: {required}")
    try:
        config = tomllib.loads((root / ".codex/config.toml").read_text(encoding="utf-8"))
        if config.get("sandbox_mode") == "danger-full-access":
            warnings.append("Project requests danger-full-access; inspect your customization.")
        hook_config = json.loads((root / ".codex/hooks.json").read_text(encoding="utf-8"))
        if not isinstance(hook_config.get("hooks"), dict):
            errors.append(".codex/hooks.json must contain a hooks object")
    except (ValueError, OSError) as exc:
        errors.append(str(exc))
    manifest_path = root / ".codex/studio-manifest.json"
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for field, actual in (("skills", skill_names), ("roles", role_names)):
            missing = set(manifest[field]) - actual
            if missing:
                errors.append(f"Missing baseline {field}: {', '.join(sorted(missing))}")
        def normalize_heading(value: str) -> str:
            return re.sub(r"(?<![\w./])/([a-z][a-z-]+)", r"$\1", value).replace(".claude/", ".codex/")

        for name, headings in manifest.get("role_domain_headings", {}).items():
            path = root / ".codex/roles" / (name + ".md")
            if not path.is_file():
                continue
            actual = {normalize_heading(value) for value in re.findall(r"(?m)^#{2,4} (.+)$", path.read_text(encoding="utf-8"))}
            missing = [heading for heading in headings if normalize_heading(heading) not in actual]
            if missing:
                errors.append(f"{path.relative_to(root)}: missing required domain sections: {', '.join(missing)}")
    if not skill_names or not role_names:
        errors.append("The studio skills or specialist roles are missing")
    bash = shutil.which("bash")
    if bash:
        for path in sorted((root / ".codex").rglob("*.sh")):
            if IGNORE_PARTS.intersection(path.relative_to(root).parts):
                continue
            checked = subprocess.run([bash, "-n", str(path)], capture_output=True, text=True)
            counts["shell_scripts"] += 1
            if checked.returncode:
                errors.append(f"{path.relative_to(root)}: {checked.stderr.strip()}")
    else:
        warnings.append("Bash is unavailable: shell syntax validation was not run")
    result = {"status": "failed" if errors else "passed", "counts": counts,
              "errors": errors, "warnings": warnings,
              "scope": "Static structure and shell syntax; no model, hook trust, or engine execution."}
    if json_output:
        print(json.dumps(result, indent=2))
    else:
        print(f"Studio validation: {result['status'].upper()}")
        print(", ".join(f"{number} {key.replace('_', ' ')}" for key, number in counts.items()))
        for error in errors:
            print("ERROR: " + error)
        for warning in warnings:
            print("NOTE: " + warning)
        print(result["scope"])
    return 1 if errors else 0


def doctor(root: Path) -> int:
    print(f"Codex Game Studios {KIT_VERSION}")
    print(f"Python: {sys.version.split()[0]} ({sys.executable})")
    missing = []
    for tool in ("git", "bash", "codex"):
        found = shutil.which(tool)
        print(f"{tool}: {found or 'not on PATH'}")
        if not found:
            missing.append(tool)
    print("jq: " + (shutil.which("jq") or "optional; not on PATH"))
    print("Engine: " + (detect_engine(root)[0] or "not detected; use $setup-engine"))
    print("Hook trust: inspect and approve with /hooks in Codex; this utility cannot query or grant it.")
    print("Optional native parser check: python3 tools/check_codex_runtime.py")
    return 1 if missing else 0


def detect_engine(root: Path) -> tuple[str | None, str | None]:
    unity = root / "ProjectSettings/ProjectVersion.txt"
    if unity.is_file():
        match = re.search(r"^m_EditorVersion:\s*(\S+)", unity.read_text(encoding="utf-8"), re.M)
        return "unity", match.group(1) if match else None
    if (root / "project.godot").is_file():
        return "godot", None
    unreal = list(root.glob("*.uproject"))
    if unreal:
        try:
            version = json.loads(unreal[0].read_text(encoding="utf-8")).get("EngineAssociation")
        except (ValueError, OSError):
            version = None
        return "unreal", version
    return None, None


def project_config(engine: str | None, version: str | None) -> str:
    text = (
        "# Codex Game Studios; see .codex/docs/config-resolution.md\n"
        f"schema_version: 1\nframework:\n  version: {FRAMEWORK_VERSION}\n"
        f"  runtime: codex\n  kit_version: {KIT_VERSION}\n"
        "modes:\n  automation: guided\nupdates:\n  check: false\n"
        "# Rigor defaults to minimal. Do not pin its six derived settings here.\n"
    )
    if engine:
        labels = {"unity": ("Unity", "C#", "unity-specialist", "unity-shader-specialist", "unity-ui-specialist"),
                  "godot": ("Godot", "GDScript", "godot-gdscript-specialist", "godot-shader-specialist", "godot-specialist"),
                  "unreal": ("Unreal", "C++", "unreal-specialist", "unreal-specialist", "ue-umg-specialist")}
        name, language, code, shader, ui = labels[engine]
        text += f"engine:\n  name: {name}\n  language: {json.dumps(language)}\n"
        if version:
            text += f"  version: {json.dumps(version)}\n"
        text += f"specialists:\n  code: {code}\n  shader: {shader}\n  ui: {ui}\n"
    return text


def ensure_safe_destination(target: Path, relative: Path) -> Path:
    if relative.is_absolute() or ".." in relative.parts:
        raise StudioError(f"Unsafe destination: {relative}")
    destination = target / relative
    for part in (destination, *destination.parents):
        if part == target.parent:
            break
        if part.is_symlink():
            raise StudioError(f"Refusing to write through symlink: {part}")
    if destination.exists() and not destination.is_file():
        raise StudioError(f"Expected a file at: {destination}")
    for parent in destination.parents:
        if parent == target.parent:
            break
        if parent.exists() and not parent.is_dir():
            raise StudioError(f"Expected a directory at: {parent}")
    return destination


def install(root: Path, target_path: str, engine: str | None, dry_run: bool = False) -> int:
    supplied = Path(target_path).expanduser().absolute()
    if any(part.is_symlink() for part in (supplied, *supplied.parents)):
        raise StudioError("Choose an actual destination path without symlinked ancestors")
    target = supplied.resolve()
    if target == root.resolve():
        raise StudioError("This folder is already the template; choose your game's project root")
    for source_folder in (".codex", ".agents", "studio-tests", "tools", "docs/engine-reference"):
        if target.is_relative_to((root / source_folder).resolve()):
            raise StudioError("Do not install inside the template's infrastructure directories")
    if target.exists() and not target.is_dir():
        raise StudioError(f"Not a directory: {target}")
    inferred, version = detect_engine(target)
    if engine and inferred and engine != inferred:
        raise StudioError(f"Requested {engine}, but the target contains an existing {inferred} project")
    engine = engine or inferred
    planned: dict[Path, bytes] = {}
    notes, conflicts = [], []

    def queue(relative: str | Path, data: bytes, preserve: bool = False) -> None:
        relative = Path(relative)
        destination = ensure_safe_destination(target, relative)
        if destination.exists():
            if destination.read_bytes() == data:
                return
            if preserve:
                notes.append(f"Kept existing {relative.as_posix()}")
                return
            conflicts.append(relative.as_posix())
            return
        planned[relative] = data

    for folder in (".codex", ".agents/skills", "studio-tests", "tools"):
        for source in sorted((root / folder).rglob("*")):
            relative = source.relative_to(root)
            if not source.is_file() or IGNORE_PARTS.intersection(relative.parts):
                continue
            if source.is_symlink():
                raise StudioError(f"Unexpected template symlink: {relative}")
            if relative.as_posix() in (".codex/config.toml", ".codex/hooks.json"):
                destination = ensure_safe_destination(target, relative)
                if destination.exists() and destination.read_bytes() != source.read_bytes():
                    example = relative.with_name(relative.stem + ".studio-example" + relative.suffix)
                    queue(example, source.read_bytes())
                    notes.append(f"Kept existing {relative}; review and merge {example} to enable studio settings")
                    continue
            queue(relative, source.read_bytes())
    for source in sorted((root / "docs/engine-reference").rglob("*")):
        if source.is_symlink():
            raise StudioError(f"Unexpected template symlink: {source.relative_to(root)}")
        if source.is_file():
            queue(source.relative_to(root), source.read_bytes(), preserve=True)
    queue(".codex/KIT-LICENSE", (root / "LICENSE").read_bytes())
    queue(".codex/STUDIO.md", (root / "AGENTS.md").read_bytes())
    queue("project.yaml", project_config(engine, version).encode(), preserve=True)
    if (root / "START-HERE.md").is_file():
        queue("docs/CODEX-STUDIO.md", (root / "START-HERE.md").read_bytes(), preserve=True)
    instructions = ensure_safe_destination(target, Path("AGENTS.md"))
    current = instructions.read_text(encoding="utf-8") if instructions.exists() else ""
    if not current:
        planned[Path("AGENTS.md")] = (root / "AGENTS.md").read_bytes()
    elif INSTRUCTION_MARKER not in current and current != (root / "AGENTS.md").read_text(encoding="utf-8"):
        block = ("\n\n" + INSTRUCTION_MARKER + "\n## Codex Game Studios\n\n"
                 "Read `.codex/STUDIO.md` before studio work. Preserve this project's existing\n"
                 "instructions; its specific rules take precedence over studio defaults.\n"
                 "Use `.agents/skills/` workflows and `.codex/agents/` specialists as relevant.\n"
                 "<!-- codex-game-studios:end -->\n")
        planned[Path("AGENTS.md")] = (current.rstrip() + block).encode()
    ignore = ensure_safe_destination(target, Path(".gitignore"))
    current_ignore = ignore.read_text(encoding="utf-8") if ignore.exists() else ""
    if IGNORE_MARKER not in current_ignore:
        block = ("\n\n" + IGNORE_MARKER + "\nproject.local.yaml\nAGENTS.override.md\n"
                 ".codex/agent-memory/\n.codex/worktrees/\nproduction/session-state/\n"
                 "production/session-logs/\n__pycache__/\n*.pyc\n")
        planned[Path(".gitignore")] = (current_ignore.rstrip() + block).encode()
    attributes = ensure_safe_destination(target, Path(".gitattributes"))
    current_attributes = attributes.read_text(encoding="utf-8") if attributes.exists() else ""
    if "# Codex Game Studios line endings" not in current_attributes:
        block = ("\n\n# Codex Game Studios line endings\n.codex/**/*.sh text eol=lf\n"
                 ".codex/**/*.py text eol=lf\n.codex/**/*.awk text eol=lf\n"
                 ".agents/skills/**/*.md text eol=lf\n")
        planned[Path(".gitattributes")] = (current_attributes.rstrip() + block).encode()
    if conflicts:
        raise StudioError("No files were written. Existing studio files differ:\n  " +
                          "\n  ".join(conflicts[:25]) +
                          (f"\n  ... {len(conflicts) - 25} more" if len(conflicts) > 25 else "") +
                          "\nReview/merge those files before retrying; there is no force-overwrite option.")
    print(f"{'Plan' if dry_run else 'Install'}: {len(planned)} file changes in {target}")
    for note in notes:
        print("NOTE: " + note)
    if dry_run:
        for relative in sorted(planned):
            print("  " + relative.as_posix())
        return 0
    for relative, data in planned.items():
        destination = ensure_safe_destination(target, relative)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
    print("Ready. Open the game root in Codex, inspect project settings, and use $setup-engine then $help.")
    print("Inspect and enable optional hooks with /hooks. Existing engine assets and scripts were not edited.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="Studio root (defaults to this tool's repository)")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor", help="Report prerequisites without installing anything")
    validation = commands.add_parser("validate", help="Check structure, manifests, generated agents, and shell syntax")
    validation.add_argument("--json", action="store_true")
    sync = commands.add_parser("sync-agents", help="Regenerate native agent TOML from role Markdown")
    sync.add_argument("--check", action="store_true", help="Report out-of-date files without writing")
    setup = commands.add_parser("install", help="Add the studio to a game without overwriting conflicting files")
    setup.add_argument("target", help="Game project root")
    setup.add_argument("--engine", choices=("unity", "godot", "unreal"))
    setup.add_argument("--dry-run", action="store_true", help="Preview every path without writing")
    commands.add_parser("catalog", help="List available skills and specialist roles")
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        if args.command == "doctor":
            return doctor(root)
        if args.command == "validate":
            return validate(root, args.json)
        if args.command == "sync-agents":
            return sync_agents(root, args.check)
        if args.command == "install":
            return install(root, args.target, args.engine, args.dry_run)
        for path in sorted((root / ".agents/skills").glob("*/SKILL.md")):
            fields, _ = read_manifest(path)
            print(f"${fields['name']}: {fields['description']}")
        print("\nSpecialist roles:")
        print(", ".join(path.stem for path in sorted((root / ".codex/roles").glob("*.md"))))
        return 0
    except (StudioError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
