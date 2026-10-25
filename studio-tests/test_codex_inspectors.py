"""Behavioral fixtures for the Codex studio inspectors; no model or network access."""
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / ".codex" / "scripts"


@unittest.skipUnless(shutil.which("bash"), "Bash is required for the studio helper scripts")
class InspectorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="cgs-inspector-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for directory in (".agents/skills/fixture-skill/references", ".codex/agents", ".codex/roles", "nested"):
            (self.root / directory).mkdir(parents=True)
        self.skill = self.root / ".agents/skills/fixture-skill/SKILL.md"
        self.skill.write_text(
            "---\nname: fixture-skill\ndescription: Inspect a fixture.\n---\n"
            "## Codex invocation\nUse `$fixture-skill <target>`.\n"
            "Read `.codex/docs/codex-runtime.md`.\n"
            "## Phase 1: Inspect\nRead the input and report findings.\n",
            encoding="utf-8",
        )

    def run_helper(self, name, *args):
        result = subprocess.run(
            ["bash", str(SCRIPTS / name), *args],
            cwd=self.root / "nested",
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout

    def lint(self):
        return self.run_helper("skill-lint.sh", "all", "--root", str(self.root))

    def write_agent(self, instructions):
        role = "# Fixture Role\n\nInspect only the delegated input."
        (self.root / ".codex/roles/fixture-agent.md").write_text(
            "---\nname: fixture-agent\ndescription: Inspect a fixture.\n---\n\n" + role + "\n",
            encoding="utf-8",
        )
        config = (
            'name = "fixture-agent"\ndescription = "Inspect a fixture."\n'
            "developer_instructions = " + json.dumps(instructions) + "\n"
        )
        (self.root / ".codex/agents/fixture-agent.toml").write_text(config, encoding="utf-8")
        return role

    def test_native_manifest_and_body_invocation(self):
        output = self.lint()
        self.assertIn("frontmatter=ok\tmissing=-\tname=match\textra=-", output)
        self.assertIn("hint=$fixture-skill <target>", output)
        self.assertIn("checked\t1\tof\t1", output)

    def test_missing_required_field_is_visible(self):
        self.skill.write_text(self.skill.read_text().replace("description: Inspect a fixture.\n", ""))
        self.assertIn("missing=description", self.lint())

    def test_old_manifest_field_is_not_treated_as_native(self):
        self.skill.write_text(self.skill.read_text().replace("name: fixture-skill", "name: fixture-skill\nmodel: sonnet"))
        self.assertIn("extra=model", self.lint())

    def test_missing_reference_is_reported_then_resolves(self):
        self.skill.write_text(self.skill.read_text() + "\nRead `references/check.md`.\n")
        self.assertIn("missing_references=references/check.md", self.lint())
        (self.skill.parent / "references/check.md").write_text("# Check\nReport the actual input.\n")
        self.assertIn("missing_references=-", self.lint())

    def test_native_agent_source_sync(self):
        role = "# Fixture Role\n\nInspect only the delegated input."
        self.write_agent("Runtime preamble.\n\n" + role)
        output = self.run_helper("agent-check.sh", "--agent", "fixture-agent", str(self.root))
        self.assertIn("config=ok model=inherited", output)
        self.assertNotIn("NOTE: stale-role", output)
        self.write_agent("An older role body.")
        output = self.run_helper("agent-check.sh", "--agent", "fixture-agent", str(self.root))
        self.assertIn("NOTE: stale-role", output)

    def test_invalid_agent_toml_is_not_reported_ok(self):
        self.write_agent("The role")
        (self.root / ".codex/agents/fixture-agent.toml").write_text('name = "unfinished\n')
        output = self.run_helper("agent-check.sh", "--agent", "fixture-agent", str(self.root))
        self.assertIn("config=invalid", output)
        self.assertIn("NOTE: required", output)

    def test_compatibility_inventory_detects_runtime_dependencies(self):
        self.skill.write_text(
            self.skill.read_text() + "\n!`echo injected`\nUse $ARGUMENTS and AskUserQuestion.\n"
        )
        output = self.run_helper("compat-inventory.sh", "--skill", "fixture-skill", str(self.root))
        self.assertIn("COUNT: legacy-dynamic-shell files=1 hits=1", output)
        self.assertIn("COUNT: legacy-variable files=1 hits=1", output)
        self.assertIn("COUNT: legacy-question-tool files=1 hits=1", output)

    def test_unreadable_manifest_remains_in_denominator(self):
        self.skill.unlink()
        output = self.lint()
        self.assertIn("NOT_READ\tfixture-skill", output)
        self.assertIn("checked\t0\tof\t1", output)


if __name__ == "__main__":
    unittest.main()
