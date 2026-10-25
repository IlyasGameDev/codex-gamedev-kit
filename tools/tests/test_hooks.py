"""Native hook integration tests; fixtures are isolated disposable repositories."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SOURCE_ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("studio_codex_hooks", SOURCE_ROOT / ".codex/hooks/codex_adapter.py")
hooks = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = hooks
SPEC.loader.exec_module(hooks)


class HookTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="studio hooks ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "game"
        self.root.mkdir()
        for name in ("hooks", "scripts"):
            shutil.copytree(SOURCE_ROOT / ".codex" / name, self.root / ".codex" / name,
                            ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copy2(SOURCE_ROOT / ".codex/hooks.json", self.root / ".codex/hooks.json")
        self.put("project.yaml", "schema_version: 1\nengine:\n  name: godot\nmodes:\n  rigor: minimal\n")
        (self.root / "src").mkdir()
        self.git("init", "-q")

    def put(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def git(self, *args, cwd=None):
        return subprocess.run(["git", *args], cwd=cwd or self.root, check=True,
                              capture_output=True, text=True).stdout

    def event(self, name, tool=None, command=None, cwd=None, **extra):
        result = {"hook_event_name": name, "cwd": str(cwd or self.root), "session_id": "test-session"}
        if tool:
            result["tool_name"] = tool
            result["tool_input"] = {"command": command}
        result.update(extra)
        return result

    def dispatch(self, payload):
        return hooks.Dispatcher(self.root, payload).dispatch()

    def message(self, result):
        return result.get("hookSpecificOutput", {}).get("additionalContext", result.get("systemMessage", ""))

    def denied(self, result):
        return result.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"

    def test_multi_file_patch_reconstructs_without_writing(self):
        self.put("src/player.cs", "class Player\n{\n    int health = 10;\n}\n")
        deleted = self.put("src/old.cs", "old\n")
        patch_text = (
            "*** Begin Patch\n"
            "*** Update File: src/player.cs\n"
            "@@\n"
            "-    int health = 10;\n"
            "+    int health = 20;\n"
            "*** Add File: src/new.cs\n+new\n"
            "*** Delete File: src/old.cs\n"
            "*** End Patch"
        )
        changes = hooks.patch_changes(patch_text, self.root, self.root)
        by_name = {c.path.name: c for c in changes}
        self.assertEqual(by_name["player.cs"].after, "class Player\n{\n    int health = 20;\n}\n")
        self.assertEqual(by_name["new.cs"].after, "new\n")
        self.assertEqual(by_name["old.cs"].action, "delete")
        self.assertTrue(deleted.exists())
        self.assertFalse((self.root / "src/new.cs").exists())
        self.assertIn("health = 10", (self.root / "src/player.cs").read_text())

    def test_update_with_anchor_multiple_hunks_and_eof(self):
        original = "first\none\nunchanged\nmethod\nlast\n"
        body = ["@@", "-one", "+two", "@@ method", "-last", "+final", "*** End of File"]
        self.assertEqual(hooks.update_text(original, body), "first\ntwo\nunchanged\nmethod\nfinal\n")

    def test_insertion_without_context_appends_as_native_apply_patch_does(self):
        self.assertEqual(hooks.update_text("first\nsecond\n", ["@@", "+last"]), "first\nsecond\nlast\n")
        self.assertEqual(hooks.update_text("first\n", ["@@", "-first"]), "")

    def test_move_validates_destination_and_source(self):
        source = self.put("src/old name.cs", "before\n")
        patch_text = ("*** Begin Patch\n*** Update File: src/old name.cs\n"
                      "*** Move to: src/new name.cs\n@@\n-before\n+after\n*** End Patch")
        changes = hooks.patch_changes(patch_text, self.root, self.root)
        by_name = {c.path.name: c for c in changes}
        self.assertEqual(by_name["new name.cs"].after, "after\n")
        self.assertEqual(by_name["old name.cs"].action, "delete")
        self.assertEqual(source.read_text(), "before\n")

    def test_paths_resolve_from_session_subdirectory(self):
        path = self.put("src/nested/item.cs", "before\n")
        patch_text = "*** Begin Patch\n*** Update File: item.cs\n@@\n-before\n+after\n*** End Patch"
        changes = hooks.patch_changes(patch_text, path.parent, self.root)
        self.assertEqual(changes[0].path, path)
        self.assertEqual(changes[0].after, "after\n")

    def test_outside_paths_are_not_read(self):
        outside = Path(self.temp.name) / "private.txt"
        outside.write_text("do not read")
        with patch.object(hooks, "read_text", side_effect=AssertionError("outside file read")):
            with self.assertRaises(hooks.PatchError):
                hooks.patch_changes("*** Begin Patch\n*** Delete File: ../private.txt\n*** End Patch",
                                    self.root, self.root)

    @unittest.skipIf(os.name == "nt", "Creating symlinks may require Windows privileges")
    def test_symlink_escape_is_not_followed(self):
        outside = Path(self.temp.name) / "outside"
        outside.mkdir()
        (self.root / "link").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(hooks.PatchError):
            hooks.project_path("link/file.cs", self.root, self.root)

    def test_unknown_patch_and_fuzzy_context_are_reported(self):
        result = self.dispatch(self.event("PreToolUse", "apply_patch", "not a patch"))
        self.assertIn("unsupported apply_patch envelope", self.message(result))
        self.put("project.yaml", "modes:\n  rigor: minimal\n")
        patch_text = "*** Begin Patch\n*** Update File: project.yaml\n@@\n-  rigor: full\n+  rigor: standard\n*** End Patch"
        result = self.dispatch(self.event("PreToolUse", "apply_patch", patch_text))
        self.assertIn("SKIPPED pre-edit content check", self.message(result))
        self.assertFalse(self.denied(result))
        self.assertIn("minimal", (self.root / "project.yaml").read_text())

    def test_proposed_config_is_checked_before_disk_changes(self):
        patch_text = ("*** Begin Patch\n*** Update File: project.yaml\n@@\n"
                      "-  rigor: minimal\n+  rigor: imaginary\n*** End Patch")
        result = self.dispatch(self.event("PreToolUse", "apply_patch", patch_text))
        self.assertIn("imaginary", self.message(result))
        self.assertFalse(self.denied(result))  # Existing write guard is advisory.
        self.assertIn("minimal", (self.root / "project.yaml").read_text())

    def test_registry_removal_is_checked_against_proposed_content(self):
        self.put("design/registry/entities.yaml",
                 "entities:\n  - name: goblin\n    status: active\n    source: design/gdd/combat.md\n")
        patch_text = ("*** Begin Patch\n*** Update File: design/registry/entities.yaml\n@@\n"
                      "-entities:\n-  - name: goblin\n-    status: active\n"
                      "-    source: design/gdd/combat.md\n+entities: []\n*** End Patch")
        result = self.dispatch(self.event("PreToolUse", "apply_patch", patch_text))
        self.assertIn("removes", self.message(result).lower())
        self.assertIn("goblin", self.message(result))
        self.assertIn("goblin", (self.root / "design/registry/entities.yaml").read_text())

    def test_post_edit_invalid_json_reports_feedback_without_denial(self):
        self.put("assets/data/player.json", '{"health":}\n')
        patch_text = "*** Begin Patch\n*** Add File: assets/data/player.json\n+{}\n*** End Patch"
        result = self.dispatch(self.event("PostToolUse", "apply_patch", patch_text))
        self.assertIn("JSON", self.message(result))
        self.assertIn("already happened", result["systemMessage"])
        self.assertFalse(self.denied(result))
        self.assertEqual((self.root / "assets/data/player.json").read_text(), '{"health":}\n')

    def test_skill_edit_returns_literal_codex_invocation(self):
        self.put(".agents/skills/example/SKILL.md", "---\nname: example\ndescription: example\n---\n")
        patch_text = "*** Begin Patch\n*** Add File: .agents/skills/example/SKILL.md\n+example\n*** End Patch"
        result = self.dispatch(self.event("PostToolUse", "apply_patch", patch_text))
        self.assertIn("$skill-test static example", self.message(result))
        self.assertNotIn("Run -test", self.message(result))

    def test_commit_blocks_corrupt_index_even_with_valid_working_copy(self):
        file = self.put("assets/data/player.json", '{"health":}\n')
        self.git("add", "--", "assets/data/player.json")
        file.write_text('{"health":100}\n')
        result = self.dispatch(self.event("PreToolUse", "Bash", "git commit -m 'test'"))
        self.assertTrue(self.denied(result), result)
        self.assertIn("not valid JSON", self.message(result))

    def test_commit_valid_index_does_not_block_for_corrupt_unstaged_copy(self):
        file = self.put("assets/data/player.json", '{"health":100}\n')
        self.git("add", "--", "assets/data/player.json")
        file.write_text('{"health":}\n')
        result = self.dispatch(self.event("PreToolUse", "Bash", "git commit -m 'test'"))
        self.assertFalse(self.denied(result), result)

    def test_add_then_commit_checks_untracked_data(self):
        self.put("assets/data/player.json", '{"health":}\n')
        result = self.dispatch(self.event("PreToolUse", "Bash", "git add -A && git commit -m 'test'"))
        self.assertTrue(self.denied(result), result)
        self.assertEqual(self.git("diff", "--cached", "--name-only"), "")  # No command was executed.

    def test_commit_from_subdirectory_is_validated(self):
        self.put("assets/data/player.json", '{"health":}\n')
        self.git("add", "--", "assets/data/player.json")
        result = self.dispatch(self.event("PreToolUse", "Bash", "git commit -m 'test'", cwd=self.root / "src"))
        self.assertTrue(self.denied(result), result)

    def test_git_relative_change_directory_uses_tool_directory(self):
        self.put("assets/data/player.json", '{"health":}\n')
        self.git("add", "--", "assets/data/player.json")
        other = Path(self.temp.name) / "other"
        other.mkdir()
        self.git("init", "-q", cwd=other)
        result = self.dispatch(self.event("PreToolUse", "Bash", "git -C ../../other commit -m 'test'",
                                         cwd=self.root / "src"))
        self.assertFalse(self.denied(result), result)

    def test_missing_commit_validator_is_not_a_silent_pass(self):
        (self.root / ".codex/hooks/validate-commit.sh").unlink()
        result = self.dispatch(self.event("PreToolUse", "Bash", "git commit -m 'test'"))
        self.assertTrue(self.denied(result), result)
        self.assertIn("unavailable", self.message(result))

    def test_plain_shell_command_has_no_false_denial(self):
        result = self.dispatch(self.event("PreToolUse", "Bash", "git status --short"))
        self.assertFalse(self.denied(result), result)

    def test_real_launcher_works_from_subdirectory_with_spaces(self):
        config = json.loads((self.root / ".codex/hooks.json").read_text())
        command = config["hooks"]["SessionStart"][0]["hooks"][0]["command"]
        payload = self.event("SessionStart", cwd=self.root / "src", source="startup")
        result = subprocess.run(["bash", "-c", command], cwd=self.root / "src",
                                input=json.dumps(payload), text=True, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Session Context", self.message(json.loads(result.stdout)))
        self.assertFalse((self.root / "src/production").exists())

    def test_engine_reference_diagnostic_reads_explicit_instruction(self):
        instruction = ("# Engine Version Reference\n"
                       "<!-- ENGINE-REFERENCE-IMPORT: explicit read below. -->\n"
                       "Read " + chr(96) + "docs/engine-reference/unity/VERSION.md" + chr(96)
                       + " before engine-specific work.\n")
        self.put("AGENTS.md", instruction)
        result = self.dispatch(self.event("SessionStart", source="startup"))
        self.assertIn("ENGINE REFERENCE MISMATCH", self.message(result))
        self.assertIn("AGENTS.md reads", self.message(result))
        self.assertNotIn("AGENTS.md imports", self.message(result))
        self.put("AGENTS.md", instruction.replace("/unity/", "/godot/"))
        result = self.dispatch(self.event("SessionStart", source="startup"))
        self.assertNotIn("ENGINE REFERENCE MISMATCH", self.message(result))

    def test_subagent_lifecycle_logs_without_reading_transcript(self):
        payload = self.event("SubagentStart", agent_type="unity-specialist", agent_id="child-1")
        self.dispatch(payload)
        payload["hook_event_name"] = "SubagentStop"
        payload["agent_transcript_path"] = str(self.root / "does-not-exist.jsonl")
        self.dispatch(payload)
        text = (self.root / "production/session-logs/agent-audit.log").read_text()
        self.assertIn("test-session | Agent invoked: unity-specialist", text)
        self.assertIn("test-session | Agent completed: unity-specialist", text)

    def test_stop_failure_uses_common_output_without_continuation(self):
        (self.root / ".codex/hooks/session-stop.sh").unlink()
        result = self.dispatch(self.event("Stop"))
        self.assertEqual(set(result), {"systemMessage"})
        self.assertIn("unavailable", result["systemMessage"])

    def test_update_helper_has_no_network_calls(self):
        result = subprocess.run(["bash", ".codex/hooks/update-check.sh", "refresh"],
                                cwd=self.root, text=True, capture_output=True, timeout=3)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("disabled", result.stderr)
        source = (self.root / ".codex/hooks/update-check.sh").read_text()
        self.assertNotIn("curl ", source)
        self.assertNotIn("wget ", source)

    def test_manual_artifact_check_uses_explicit_destinations(self):
        self.put("docs/existing.md", "review\n")
        result = subprocess.run(["bash", ".codex/hooks/validate-agent-artifact.sh",
                                 "docs/existing.md", "docs/missing.md"],
                                cwd=self.root, text=True, capture_output=True, timeout=3)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("ARTIFACT\tdocs/existing.md\tpresent", result.stdout)
        self.assertIn("ARTIFACT\tdocs/missing.md\tmissing", result.stdout)

    def test_manifest_registers_only_documented_native_matchers(self):
        manifest = json.loads((self.root / ".codex/hooks.json").read_text())
        self.assertNotIn("Notification", manifest["hooks"])
        self.assertEqual(manifest["hooks"]["PreToolUse"][0]["matcher"], "^(Bash|apply_patch)$")
        self.assertEqual(manifest["hooks"]["PostToolUse"][0]["matcher"], "^apply_patch$")
        self.assertFalse(manifest["hooks"]["Stop"][0]["hooks"][0].get("async", False))


if __name__ == "__main__":
    unittest.main()
