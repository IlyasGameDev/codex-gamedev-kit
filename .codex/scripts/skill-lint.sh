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

parser = argparse.ArgumentParser(description="Observe Codex skill structure (seven checks, no verdicts).")
parser.add_argument("name", help="Skill folder name, or all")
parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
args = parser.parse_args()
root = args.root.resolve()
skills = root / ".agents/skills"
if not skills.is_dir():
    parser.error("no .agents/skills directory under %s" % root)
if args.name != "all" and not safe_name(args.name):
    parser.error("expected a skill folder name")
names = sorted(p.name for p in skills.iterdir() if p.is_dir())
selected = names if args.name == "all" else [args.name]
if args.name != "all" and args.name not in names:
    parser.error("no such skill: %s" % args.name)
print("skills\t%d\t.agents/skills" % len(selected))
checked = 0
for name in selected:
    folder = skills / name
    try:
        source = read(folder / "SKILL.md")
    except (OSError, UnicodeError) as exc:
        print("NOT_READ\t%s\t%s" % (name, exc))
        continue
    checked += 1
    texts = [source]
    for reference in sorted((folder / "references").rglob("*.md")):
        try:
            texts.append(read(reference))
        except (OSError, UnicodeError) as exc:
            print("NOT_READ\t%s\t%s: %s" % (name, reference.relative_to(root), exc))
    all_text = "\n".join(texts)
    state, fields, body = manifest(source)
    clean = outside_fences(all_text)
    headings = re.findall(r"^##\s+(.+)$", clean, re.M)
    phases = {h for h in headings if re.match(r"(?:Phase\s+\d|\d+\.)", h)}
    missing = [key for key in ("name", "description") if not fields.get(key)]
    unknown = sorted(set(fields) - {"name", "description"})
    name_match = "match" if fields.get("name") == name else "mismatch:%s" % fields.get("name", "absent")
    print("skill\t%s\tfiles=%d\tlines=%d" % (name, len(texts), len(all_text.splitlines())))
    print("check1\t%s\tfrontmatter=%s\tmissing=%s\tname=%s\textra=%s" % (name, state, ",".join(missing) or "-", name_match, ",".join(unknown) or "-"))
    print("check2\t%s\tphases=%d\th2=%d\th2_total=%d" % (name, len(phases), len(set(headings)), len(headings)))
    verdicts = []
    for word in ("PASS", "FAIL", "CONCERNS", "APPROVED", "BLOCKED", "COMPLETE", "READY", "COMPLIANT", "NON-COMPLIANT", "NOT ASSESSED", "PROCEED", "PIVOT", "KILL", "GO", "NO-GO", "CRITICAL", "HIGH", "MEDIUM", "LOW"):
        count = len(re.findall(r"(?<![\w-])" + re.escape(word) + r"(?![\w-])", all_text))
        if count:
            verdicts.append("%s:%d" % (word, count))
    print("check3\t%s\tverdicts=%s" % (name, ",".join(verdicts) or "-"))
    contract = ".codex/docs/codex-runtime.md" in source
    print("check4\t%s\truntime_contract=%s\tauthorization_mentions=%d\tapproval_mentions=%d" % (name, "yes" if contract else "no", len(re.findall(r"authoriz|authoris", all_text, re.I)), len(re.findall(r"approv", all_text, re.I))))
    body_clean = outside_fences(body)
    last = list(re.finditer(r"^##\s+(.+)$", body_clean, re.M))
    last_heading = last[-1].group(1) if last else "-"
    tail = body_clean[last[-1].end():] if last else body_clean
    named = sorted(set(re.findall(r"\$([a-z][a-z0-9-]+)", tail)) & set(names))
    print("check5\t%s\tlast_section=%s\tskills_named=%s" % (name, last_heading, ",".join(named) or "-"))
    refs = sorted(set(re.findall(r"(?<![\w./-])references/[\w./-]+\.md", all_text)))
    missing_refs = [reference for reference in refs if not (folder / reference).is_file()]
    implicit = "default"
    metadata_path = folder / "agents/openai.yaml"
    if metadata_path.is_file():
        metadata = read(metadata_path)
        match = re.search(r"^\s*allow_implicit_invocation:\s*(true|false)\s*$", metadata, re.M)
        implicit = match.group(1) if match else "default"
    legacy_count = len(re.findall(r"(?m)^\s*!`|\$ARGUMENTS\b|CLAUDE_[A-Z_]+|^@(?:docs/|\.)", all_text))
    print("check6\t%s\timplicit_invocation=%s\treferences=%d\tmissing_references=%s\tlegacy_constructs=%d" % (name, implicit, len(refs), ",".join(missing_refs) or "-", legacy_count))
    hint_match = re.search(r"^Use\s+`([^`]+)`", body, re.M)
    hint = hint_match.group(1) if hint_match else "absent"
    args_heading = next((h for h in headings if re.search(r"argument|parse|invocation", h, re.I)), "-")
    print("check7\t%s\thint=%s\targs_section=%s" % (name, hint, args_heading))
print("checked\t%d\tof\t%d" % (checked, len(selected)))

PYINSPECT
