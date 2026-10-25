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

import tomllib
from itertools import combinations
parser = argparse.ArgumentParser(description="Observe native Codex agents, source roles and delegation briefs.")
parser.add_argument("--agent")
parser.add_argument("--skill")
parser.add_argument("root", nargs="?", type=Path, default=DEFAULT_ROOT)
args = parser.parse_args()
for name in (args.agent, args.skill):
    if name and not safe_name(name):
        parser.error("expected a folder or agent name")
root = args.root.resolve()
agent_dir, role_dir, skill_dir = (root / p for p in (".codex/agents", ".codex/roles", ".agents/skills"))
if not agent_dir.is_dir():
    parser.error("no .codex/agents directory under %s" % root)
native = {p.stem: p for p in sorted(agent_dir.glob("*.toml"))}
roles = {p.stem: p for p in sorted(role_dir.glob("*.md"))}
skills = {p.parent.name: p for p in sorted(skill_dir.glob("*/SKILL.md"))}
if args.agent and args.agent not in set(native) | set(roles):
    parser.error("no such agent: %s" % args.agent)
if args.skill and args.skill not in skills:
    parser.error("no such skill: %s" % args.skill)
print("ROOT: %s" % root)
print("AGENTS: %d  ROLE_GUIDES: %d  SKILLS: %d" % (len(native), len(roles), len(skills)))
descriptions = {}
for name in sorted(set(native) | set(roles)):
    notes = []
    config = {}
    status = "missing"
    if name in native:
        try:
            config = tomllib.loads(read(native[name]))
            status = "ok"
        except (OSError, UnicodeError, tomllib.TOMLDecodeError) as exc:
            status = "invalid"
            notes.append(("config", str(exc)))
    for key in ("name", "description", "developer_instructions"):
        if not isinstance(config.get(key), str) or not config[key].strip():
            notes.append(("required", "missing or empty %s" % key))
    if config.get("name") != name:
        notes.append(("name", "file stem and configured name differ"))
    descriptions[name] = str(config.get("description", ""))
    if name not in roles:
        notes.append(("role", "no corresponding .codex/roles/%s.md" % name))
    else:
        try:
            fm_state, fields, body = manifest(read(roles[name]))
            if fm_state != "ok" or fields.get("name") != name:
                notes.append(("role-frontmatter", fm_state))
            if body and body not in config.get("developer_instructions", ""):
                notes.append(("stale-role", "run python3 tools/studio.py sync-agents"))
        except (OSError, UnicodeError) as exc:
            notes.append(("role", str(exc)))
    for key in ("maxTurns", "disallowedTools", "tools", "skills", "memory", "isolation"):
        if key in config:
            notes.append(("unsupported-legacy-key", key))
    if args.skill or (args.agent and args.agent != name):
        continue
    print("AGENT: %s config=%s model=%s effort=%s sandbox=%s" % (name, status, config.get("model", "inherited"), config.get("model_reasoning_effort", "inherited"), config.get("sandbox_mode", "inherited")))
    print("  description: %s" % descriptions[name])
    for kind, detail in notes:
        print("  NOTE: %s %s" % (kind, detail.replace("\n", " ")))
stopwords = set("a an and are as at be by for from in is it of on or the this to use when with your agent specialist".split())
print("OVERLAP_THRESHOLD: 0.30 (description word Jaccard; observations only)")
for a, b in combinations(descriptions, 2):
    if args.agent and args.agent not in (a, b):
        continue
    if args.skill:
        break
    wa = set(re.findall(r"[a-z]+", descriptions[a].lower())) - stopwords
    wb = set(re.findall(r"[a-z]+", descriptions[b].lower())) - stopwords
    score = len(wa & wb) / len(wa | wb) if wa | wb else 0
    if score >= 0.30:
        print("OVERLAP: %s %s jaccard=%.2f shared=%s" % (a, b, score, ",".join(sorted(wa & wb))))
blocks = 0
for name, path in skills.items():
    if args.skill and name != args.skill:
        continue
    paths = [path] + sorted((path.parent / "references").rglob("*.md"))
    for source in paths:
        text = read(source)
        for section in re.split(r"(?m)(?=^#{1,6}\s)", text):
            found = sorted(n for n in native if re.search(r"(?<![\w-])" + re.escape(n) + r"(?![\w-])", section))
            if args.agent:
                found = [n for n in found if n == args.agent]
            if not found or not re.search(r"spawn|delegat|subagent|brief", section, re.I):
                continue
            blocks += 1
            heading = section.splitlines()[0][:100] if section.splitlines() else "-"
            print("DELEGATION: %s %s %s agents=%s" % (name, source.relative_to(root), heading, ",".join(found)))
            patterns = {"objective": r"objective|goal|task|review|implement", "output": r"return|output|report|write", "sources": r"read|inputs?|sources?|\.md", "boundaries": r"do not|never|only|must not|scope", "recheck": r"recheck|re-check|verify|validate"}
            print("  markers: " + " ".join("%s=%d" % (key, len(re.findall(pattern, section, re.I))) for key, pattern in patterns.items()))
print("DELEGATION_BLOCKS: %d" % blocks)
if not blocks:
    print("NOTE: no-delegations no matching delegation block found")

PYINSPECT
