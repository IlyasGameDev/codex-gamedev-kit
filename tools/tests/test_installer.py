"""Behavior checks for installing into existing games; standard-library only."""

from __future__ import annotations

from contextlib import redirect_stdout
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


STUDIO_PATH = Path(__file__).resolve().parents[1] / "studio.py"
SPEC = importlib.util.spec_from_file_location("studio_installer_under_test", STUDIO_PATH)
studio = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(studio)


def write_file(root: Path, relative: str, content: str | bytes) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content.encode("utf-8") if isinstance(content, str) else content)
    return path


def snapshot(root: Path) -> dict | None:
    if not root.exists():
        return None
    result = {}
    for path in sorted(root.rglob("*")):
        name = path.relative_to(root).as_posix()
        if path.is_symlink():
            result[name] = ("symlink", os.readlink(path))
        elif path.is_file():
            result[name] = ("file", path.read_bytes())
        else:
            result[name] = ("directory", None)
    return result


class InstallerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="studio-installer-tests-")
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name).resolve()
        self.source = self.base / "Studio Template With Spaces"
        self.target = self.base / "Existing Unity Game With Spaces"
        files = {
            "AGENTS.md": "# Studio defaults\nUse the studio workflows when relevant.\n",
            "LICENSE": "MIT license fixture; preserve this attribution.\n",
            "START-HERE.md": "# Start here\nOpen the game root in Codex.\n",
            ".codex/config.toml": 'approval_policy = "on-request"\nsandbox_mode = "workspace-write"\n',
            ".codex/hooks.json": '{"hooks": {"SessionStart": []}}\n',
            ".codex/docs/codex-runtime.md": "# Runtime\nUse the actual exposed tools.\n",
            ".codex/rules/studio.rules": "# Native policy fixture\n",
            ".codex/roles/unity-specialist.md": (
                '---\nname: unity-specialist\ndescription: "Review Unity engine work."\n---\n'
                "# Unity specialist\nPreserve existing scenes and metadata.\n"
            ),
            ".agents/skills/start/SKILL.md": (
                '---\nname: start\ndescription: "Start a studio workflow."\n---\n'
                "# Start\nRead project.yaml.\n"
            ),
            ".agents/skills/start/references/introduction.md": "# Introduction\n",
            "studio-tests/catalog.json": '{"skills": ["start"]}\n',
            "tools/studio.py": STUDIO_PATH.read_bytes(),
            "docs/engine-reference/unity/VERSION.md": "# Unity version reference\nVerify the installed editor.\n",
            # Engine/game content in the source must not be copied into a game.
            "Assets/Scripts/Player.cs": "TEMPLATE GAME SOURCE MUST NOT BE INSTALLED\n",
            "design/gdd/example.md": "TEMPLATE GAME DESIGN MUST NOT BE INSTALLED\n",
        }
        for relative, content in files.items():
            write_file(self.source, relative, content)
        write_file(
            self.source,
            ".codex/agents/unity-specialist.toml",
            studio.agent_text(self.source / ".codex/roles/unity-specialist.md"),
        )

    def make_unity_game(self) -> dict[str, bytes]:
        files = {
            "Assets/Scripts/Player.cs": b"public class Player { public int Coins = 10; }\n",
            "Assets/Scripts/Player.cs.meta": b"fileFormatVersion: 2\nguid: existing-player-guid\n",
            "Assets/Scenes/Main.unity": b"%YAML 1.1\n# existing scene fixture\n",
            "Packages/manifest.json": b'{"dependencies": {"com.unity.inputsystem": "1.0.0"}}\n',
            "ProjectSettings/ProjectVersion.txt": b"m_EditorVersion: 6000.3.8f1\nm_EditorVersionWithRevision: fixture\n",
        }
        for relative, content in files.items():
            write_file(self.target, relative, content)
        return files

    def install(self, *, target: Path | None = None, engine: str | None = None, dry_run: bool = False) -> str:
        output = io.StringIO()
        with redirect_stdout(output):
            code = studio.install(self.source, str(target or self.target), engine, dry_run)
        self.assertEqual(code, 0)
        return output.getvalue()

    def symlink(self, destination: Path, target: Path, *, directory: bool = False) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            destination.symlink_to(target, target_is_directory=directory)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"Symlinks are unavailable for this test user: {exc}")

    def assert_refused_without_writes(self, *, target: Path | None = None, engine: str | None = None) -> str:
        before = snapshot(self.target)
        with self.assertRaises(studio.StudioError) as raised:
            self.install(target=target, engine=engine)
        self.assertEqual(snapshot(self.target), before)
        return str(raised.exception)

    def test_install_into_existing_unity_root_preserves_game_files(self) -> None:
        game_files = self.make_unity_game()
        self.install()
        for relative, expected in game_files.items():
            self.assertEqual((self.target / relative).read_bytes(), expected, relative)
        config = (self.target / "project.yaml").read_text()
        self.assertIn("name: Unity", config)
        self.assertIn('version: "6000.3.8f1"', config)
        self.assertIn("ui: unity-ui-specialist", config)
        self.assertTrue((self.target / ".agents/skills/start/SKILL.md").is_file())
        self.assertTrue((self.target / ".codex/agents/unity-specialist.toml").is_file())
        self.assertEqual((self.target / ".codex/KIT-LICENSE").read_bytes(), (self.source / "LICENSE").read_bytes())
        self.assertFalse((self.target / "design/gdd/example.md").exists())
        self.assertFalse((self.target / ".git").exists())

    def test_cli_accepts_source_and_target_paths_containing_spaces(self) -> None:
        self.make_unity_game()
        result = subprocess.run(
            [sys.executable, str(STUDIO_PATH), "--root", str(self.source), "install", str(self.target), "--engine", "unity"],
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.target / ".codex/config.toml").is_file())

    def test_existing_project_yaml_and_custom_agents_instructions_are_preserved(self) -> None:
        self.make_unity_game()
        project = b"engine:\n  name: Unity\nmodes:\n  rigor: full\ncustom_key: keep-me\n"
        instructions = "# Our game\nKeep our architecture and C# style.\n"
        write_file(self.target, "project.yaml", project)
        write_file(self.target, "AGENTS.md", instructions)
        self.install()
        self.assertEqual((self.target / "project.yaml").read_bytes(), project)
        merged = (self.target / "AGENTS.md").read_text()
        self.assertTrue(merged.startswith(instructions.rstrip()))
        self.assertEqual(merged.count(studio.INSTRUCTION_MARKER), 1)
        self.assertIn("specific rules take precedence", merged)
        self.assertEqual((self.target / ".codex/STUDIO.md").read_bytes(), (self.source / "AGENTS.md").read_bytes())

    def test_second_install_is_idempotent_with_custom_project_files(self) -> None:
        self.make_unity_game()
        write_file(self.target, "AGENTS.md", "# Custom instructions\nKeep these.\n")
        write_file(self.target, ".gitignore", "Library/\nTemp/\n")
        write_file(self.target, ".gitattributes", "*.unity text eol=lf\n")
        self.install()
        before = snapshot(self.target)
        output = self.install()
        self.assertEqual(snapshot(self.target), before)
        self.assertIn("Install: 0 file changes", output)

    def test_dry_run_does_not_create_a_missing_target(self) -> None:
        self.assertFalse(self.target.exists())
        output = self.install(engine="unity", dry_run=True)
        self.assertIn("Plan:", output)
        self.assertIn(".agents/skills/start/SKILL.md", output)
        self.assertFalse(self.target.exists())

    def test_dry_run_does_not_change_an_existing_game(self) -> None:
        self.make_unity_game()
        write_file(self.target, "AGENTS.md", "# Existing instructions\n")
        before = snapshot(self.target)
        self.install(dry_run=True)
        self.assertEqual(snapshot(self.target), before)

    def test_conflicting_skill_refuses_before_any_file_is_written(self) -> None:
        self.make_unity_game()
        write_file(self.target, ".agents/skills/start/SKILL.md", "Custom skill; do not overwrite.\n")
        message = self.assert_refused_without_writes()
        self.assertIn("No files were written", message)
        self.assertIn(".agents/skills/start/SKILL.md", message)
        self.assertFalse((self.target / ".codex/config.toml").exists())

    def test_existing_codex_config_and_hooks_are_preserved_with_examples(self) -> None:
        self.make_unity_game()
        config = 'approval_policy = "on-request"\n# Personal project customizations.\n'
        hooks = json.dumps({"hooks": {"Stop": []}, "description": "Existing project hooks"})
        write_file(self.target, ".codex/config.toml", config)
        write_file(self.target, ".codex/hooks.json", hooks)
        self.install()
        self.assertEqual((self.target / ".codex/config.toml").read_text(), config)
        self.assertEqual((self.target / ".codex/hooks.json").read_text(), hooks)
        for name in ("config.toml", "hooks.json"):
            path = Path(name)
            example = path.stem + ".studio-example" + path.suffix
            self.assertEqual((self.target / ".codex" / example).read_bytes(), (self.source / ".codex" / name).read_bytes())
        before = snapshot(self.target)
        self.install()
        self.assertEqual(snapshot(self.target), before)

    def test_conflicting_example_refuses_before_any_file_is_written(self) -> None:
        self.make_unity_game()
        write_file(self.target, ".codex/config.toml", "# Existing project config\n")
        write_file(self.target, ".codex/config.studio-example.toml", "# Existing manually reviewed example\n")
        message = self.assert_refused_without_writes()
        self.assertIn("config.studio-example.toml", message)

    def test_existing_engine_reference_is_preserved(self) -> None:
        self.make_unity_game()
        reference = "# Our pinned editor version\nDo not replace this snapshot.\n"
        write_file(self.target, "docs/engine-reference/unity/VERSION.md", reference)
        self.install()
        self.assertEqual((self.target / "docs/engine-reference/unity/VERSION.md").read_text(), reference)

    def test_target_directory_symlink_is_refused(self) -> None:
        self.make_unity_game()
        alias = self.base / "Game Alias"
        self.symlink(alias, self.target, directory=True)
        message = self.assert_refused_without_writes(target=alias)
        self.assertIn("symlink", message.lower())

    def test_symlinked_target_ancestor_is_refused(self) -> None:
        actual_parent = self.base / "Actual Parent"
        actual_parent.mkdir()
        alias_parent = self.base / "Linked Parent"
        self.symlink(alias_parent, actual_parent, directory=True)
        target = alias_parent / "New Game"
        before = snapshot(actual_parent)
        with self.assertRaises(studio.StudioError):
            self.install(target=target, engine="unity")
        self.assertEqual(snapshot(actual_parent), before)

    def test_nested_destination_directory_symlink_is_refused(self) -> None:
        self.make_unity_game()
        outside = self.base / "External Codex Folder"
        outside.mkdir()
        self.symlink(self.target / ".codex", outside, directory=True)
        self.assert_refused_without_writes()
        self.assertEqual(snapshot(outside), {})

    def test_existing_instructions_symlink_is_refused(self) -> None:
        self.make_unity_game()
        outside = write_file(self.base, "external-instructions.md", "# Do not modify\n")
        self.symlink(self.target / "AGENTS.md", outside)
        self.assert_refused_without_writes()
        self.assertEqual(outside.read_text(), "# Do not modify\n")

    def test_template_codex_file_symlink_is_refused(self) -> None:
        self.make_unity_game()
        outside = write_file(self.base, "external-template-content.md", "Do not import this file.\n")
        self.symlink(self.source / ".codex/unexpected.md", outside)
        message = self.assert_refused_without_writes()
        self.assertIn("template symlink", message.lower())

    def test_template_engine_reference_symlink_is_refused(self) -> None:
        self.make_unity_game()
        outside = write_file(self.base, "external-reference.md", "Do not import this file.\n")
        self.symlink(self.source / "docs/engine-reference/unity/unexpected.md", outside)
        message = self.assert_refused_without_writes()
        self.assertIn("symlink", message.lower())

    def test_existing_file_in_required_directory_position_is_refused(self) -> None:
        self.make_unity_game()
        write_file(self.target, ".codex", "This is a file, not a directory.\n")
        message = self.assert_refused_without_writes()
        self.assertIn("directory", message.lower())

    def test_engine_mismatch_refuses_before_any_file_is_written(self) -> None:
        self.make_unity_game()
        message = self.assert_refused_without_writes(engine="godot")
        self.assertIn("Requested godot", message)
        self.assertIn("existing unity project", message)

    def test_installing_into_template_itself_is_refused(self) -> None:
        before = snapshot(self.source)
        with self.assertRaises(studio.StudioError):
            self.install(target=self.source)
        self.assertEqual(snapshot(self.source), before)


if __name__ == "__main__":
    unittest.main()
