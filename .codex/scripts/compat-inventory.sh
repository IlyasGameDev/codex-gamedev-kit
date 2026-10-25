#!/usr/bin/env bash
# Codex Game Studios inspector. Prints observations; the invoking skill interprets them.
# Requires Python 3.11+. Read-only; never invokes a model or changes project files.
set -eu
HERE="$(cd "$(dirname "$0")" && pwd)"
PYTHON=""
for candidate in python3 python py; do
  if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' >/dev/null 2>&1; then
    PYTHON="$candidate"
    break
  fi
done
if [ -z "$PYTHON" ]; then echo "This inspector requires Python 3.11 or newer." >&2; exit 1; fi
"$PYTHON" - "$HERE/../.." "$@" <<'PYINSPECT'

import argparse
import json
import re
import sys
from pathlib import Path
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass
DEFAULT_ROOT = Path(sys.argv.pop(1)).resolve()

def read(path):
    return path.read_text(encoding="utf-8")

def manifest(text):
    """Observe the scalar-only name/description manifests used by this template."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return "missing", {}, text
    end = next((n for n in range(1, len(lines)) if lines[n].strip() == "---"), None)
    if end is None:
        return "unclosed", {}, text
    fields = {}
    state = "ok"
    for n, line in enumerate(lines[1:end], 2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = re.match(r"^([a-zA-Z][\w-]*):\s*(.*?)\s*$", line)
        if not match:
            state = "bad@%d" % n
            continue
        key, value = match.groups()
        if key in fields:
            state = "duplicate:%s" % key
        if value.startswith('"'):
            try:
                value = json.loads(value)
            except ValueError:
                state = "bad@%d" % n
        elif value.startswith("'") and value.endswith("'"):
            value = value[1:-1].replace("''", "'")
        fields[key] = value
    return state, fields, "\n".join(lines[end + 1:]).strip()

def safe_name(name):
    return bool(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name))

def outside_fences(text):
    lines = []
    fence = None
    for line in text.splitlines():
        marker = re.match(r"^\s*(`{3,}|~{3,})", line)
        if marker:
            char = marker.group(1)[0]
            if fence is None:
                fence = char
            elif fence == char:
                fence = None
            continue
        if fence is None:
            lines.append(line)
    return "\n".join(lines)

from collections import Counter
parser = argparse.ArgumentParser(description="Inventory native Codex mechanisms and potential legacy constructs.")
group = parser.add_mutually_exclusive_group()
group.add_argument("--skill")
group.add_argument("--agent")
parser.add_argument("root", nargs="?", type=Path, default=DEFAULT_ROOT)
args = parser.parse_args()
root = args.root.resolve()
if not (root / ".codex").is_dir():
    parser.error("no .codex directory under %s" % root)
for name in (args.agent, args.skill):
    if name and not safe_name(name):
        parser.error("expected a skill or agent name")
files = set()
if args.skill:
    folder = root / ".agents/skills" / args.skill
    if not (folder / "SKILL.md").is_file():
        parser.error("no such skill: %s" % args.skill)
    files.update(folder.rglob("*.md"))
    files.update(folder.rglob("*.yaml"))
elif args.agent:
    files.update(p for p in (root / ".codex/agents" / (args.agent + ".toml"), root / ".codex/roles" / (args.agent + ".md")) if p.is_file())
    if not files:
        parser.error("no such agent: %s" % args.agent)
else:
    for directory, patterns in ((".agents/skills", ("*.md", "*.yaml")), (".codex/roles", ("*.md",)), (".codex/agents", ("*.toml",)), (".codex/docs", ("*.md",)), (".codex/rules", ("*.md", "*.rules")), (".codex/hooks", ("*.sh", "*.py", "*.json"))):
        for pattern in patterns:
            files.update((root / directory).rglob(pattern))
    files.update(root.glob("**/AGENTS.md"))
    files.update(p for p in (root / ".codex/config.toml", root / ".codex/hooks.json") if p.is_file())
patterns = {
    "legacy-question-tool": r"\bAskUserQuestion\b",
    "legacy-task-tool": r"\b(?:TaskCreate|TaskGet|TaskList|TaskUpdate|TaskOutput|TaskStop|TeamCreate|TeamDelete|SendMessage|TodoWrite)\b",
    "legacy-agent-tool": r"`Agent`|\bAgent tool\b|\bsubagent_type\b",
    "legacy-variable": r"\bCLAUDE_[A-Z_]+\b|\$ARGUMENTS\b",
    "legacy-dynamic-shell": r"^\s*!`|^\s*```!",
    "legacy-auto-import": r"^\s*@(?:docs/|\.)",
    "legacy-path": r"\.claude/|\bCLAUDE\.md\b",
    "native-skill-invocation": r"\$[a-z][a-z0-9-]*",
    "native-agent-config": r"^developer_instructions\s*=",
    "native-skill-policy": r"^\s*allow_implicit_invocation:",
    "native-runtime-contract": r"\.codex/docs/codex-runtime\.md",
    "native-agent-delegation": r"\bspawn_agent\b|Codex subagent",
}
counts = Counter()
hit_files = {key: set() for key in patterns}
rows = []
read_count = 0
for path in sorted(files):
    relative = path.relative_to(root)
    try:
        text = read(path)
    except (OSError, UnicodeError) as exc:
        rows.append("NOT_READ: %s %s" % (relative, exc))
        continue
    read_count += 1
    for number, line in enumerate(text.splitlines(), 1):
        for key, pattern in patterns.items():
            if re.search(pattern, line):
                counts[key] += 1
                hit_files[key].add(str(relative))
                rows.append("FOUND: %s %s:%d" % (key, relative, number))
    if path.name == "SKILL.md":
        state, fields, _ = manifest(text)
        for key in sorted(set(fields) - {"name", "description"}):
            construct = "legacy-skill-frontmatter"
            counts[construct] += 1
            hit_files.setdefault(construct, set()).add(str(relative))
            rows.append("FOUND: %s %s key=%s" % (construct, relative, key))
print("ROOT: %s" % root)
print("FILES: read=%d selected=%d" % (read_count, len(files)))
print("Potential legacy mentions are observations, not failures; migration documentation can legitimately name old constructs.")
for key in sorted(set(patterns) | set(counts)):
    print("COUNT: %s files=%d hits=%d" % (key, len(hit_files.get(key, set())), counts[key]))
for row in rows:
    print(row)
print("FOUND_LINES: %d" % len(rows))

PYINSPECT
