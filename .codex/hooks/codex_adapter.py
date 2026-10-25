#!/usr/bin/env python3
"""Bridge native Codex events to the studio's independently reusable validators.

Only the actual native wire schema is configured in hooks.json. Write/Edit
objects below are an INTERNAL compatibility format for existing shell helpers.
This program never executes a tool's command or applies its patch.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MAX_INPUT_BYTES = 16 * 1024 * 1024
MAX_FILE_BYTES = 4 * 1024 * 1024
MAX_OUTPUT_CHARS = 12000
EVENT_BUDGET_SECONDS = 40
HELPER_TIMEOUT_SECONDS = 15
PATCH_HEADERS = ("*** Add File: ", "*** Update File: ", "*** Delete File: ")


class PatchError(ValueError):
    """A patch cannot be reconstructed safely without running the real tool."""


@dataclass
class Change:
    path: Path
    action: str
    before: str | None
    after: str | None
    note: str = ""


def project_path(name: str, cwd: Path, root: Path) -> Path:
    """Resolve patch paths as Codex does, without following them outside root."""
    if not name or "\x00" in name or "\n" in name or "\r" in name:
        raise PatchError("The patch contains an invalid file path.")
    candidate = Path(name)
    path = (candidate if candidate.is_absolute() else cwd / candidate).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise PatchError(f"Path outside this studio project was not inspected: {name}") from exc
    return path


def read_text(path: Path) -> str | None:
    if not path.exists():
        return None
    if not path.is_file():
        raise PatchError(f"Not a regular text file: {path.name}")
    if path.stat().st_size > MAX_FILE_BYTES:
        raise PatchError(f"File exceeds the {MAX_FILE_BYTES // 1048576} MiB pre-edit inspection limit: {path.name}")
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise PatchError(f"Text could not be read for {path.name}: {type(exc).__name__}") from exc


def matching_index(lines: list[str], wanted: list[str], start: int, at_end: bool) -> int:
    """Use the first exact context match, as native apply_patch does."""
    if not wanted:
        # Native apply_patch appends an insertion with no old/context lines.
        return len(lines)
    end = len(lines) - len(wanted)
    candidates = [i for i in range(start, end + 1) if lines[i:i + len(wanted)] == wanted]
    if at_end:
        candidates = [i for i in candidates if i + len(wanted) == len(lines)]
    if not candidates:
        raise PatchError("Patch context did not match exactly; pre-edit content validation was skipped.")
    return candidates[0]


def update_text(before: str, body: list[str]) -> str:
    """Rebuild standard apply_patch update hunks, including @@ anchors and EOF."""
    lines = before.splitlines()
    cursor, index = 0, 0
    while index < len(body):
        anchor = ""
        if body[index] == "@@":
            index += 1
        elif body[index].startswith("@@ "):
            anchor = body[index][3:]
            index += 1
        elif body[index].startswith("***"):
            raise PatchError("Unexpected patch marker in an update hunk.")
        if anchor:
            cursor = matching_index(lines, [anchor], cursor, False) + 1
        old, new = [], []
        at_end = False
        while index < len(body) and not body[index].startswith("@@"):
            line = body[index]
            if line == "*** End of File":
                at_end = True
                index += 1
                break
            if line.startswith(" "):
                old.append(line[1:])
                new.append(line[1:])
            elif line.startswith("-"):
                old.append(line[1:])
            elif line.startswith("+"):
                new.append(line[1:])
            elif line == "":
                # The native patch parser accepts unprefixed blank context.
                old.append("")
                new.append("")
            else:
                raise PatchError("Unsupported line in a patch hunk.")
            index += 1
        if not old and not new:
            raise PatchError("An empty update hunk cannot be reconstructed.")
        position = matching_index(lines, old, cursor, at_end)
        lines[position:position + len(old)] = new
        cursor = position + len(new)
    # apply_patch writes updated files with a terminating newline.
    return "\n".join(lines) + ("\n" if lines else "")


def patch_changes(command: str, cwd: Path, root: Path, *, after_tool: bool = False) -> list[Change]:
    """Return per-file proposed content (pre) or affected paths (post).

    Adds, updates, deletes, moves, and multiple hunks are recognized. The parser
    never writes. Failed reconstruction retains the affected path with a warning
    so that the post-edit validator can still inspect the real result.
    """
    lines = command.strip().splitlines()
    if not lines or lines[0] != "*** Begin Patch" or lines[-1] != "*** End Patch":
        raise PatchError("The hook received an unsupported apply_patch envelope.")
    changes: dict[Path, Change] = {}
    virtual: dict[Path, str | None] = {}

    def current(path: Path) -> str | None:
        if path not in virtual:
            virtual[path] = read_text(path)
        return virtual[path]

    def record(path: Path, action: str, before: str | None, after: str | None, note: str = "") -> None:
        initial = changes[path].before if path in changes else before
        changes[path] = Change(path, action, initial, after, note)
        virtual[path] = after

    index = 1
    while index < len(lines) - 1:
        line = lines[index]
        kind = next((header for header in PATCH_HEADERS if line.startswith(header)), None)
        if kind is None:
            raise PatchError("Expected an Add, Update, or Delete File patch marker.")
        path = project_path(line[len(kind):], cwd, root)
        index += 1
        move_path = None
        if kind == "*** Update File: " and index < len(lines) and lines[index].startswith("*** Move to: "):
            move_path = project_path(lines[index][len("*** Move to: "):], cwd, root)
            index += 1
        body = []
        while index < len(lines) - 1 and not lines[index].startswith(PATCH_HEADERS):
            body.append(lines[index])
            index += 1
        if after_tool:
            if kind == "*** Delete File: ":
                record(path, "delete", None, None)
            else:
                record(move_path or path, "write", None, None)
                if move_path:
                    record(path, "delete", None, None)
            continue
        try:
            before = current(path)
            if kind == "*** Delete File: ":
                if body:
                    raise PatchError("Delete File unexpectedly has a body.")
                record(path, "delete", before, "")
            elif kind == "*** Add File: ":
                if any(not item.startswith("+") for item in body):
                    raise PatchError("Add File contains a line without a '+' prefix.")
                after = "\n".join(item[1:] for item in body) + ("\n" if body else "")
                record(path, "add", before, after)
            else:
                if before is None:
                    raise PatchError("The file to update does not exist.")
                after = update_text(before, body)
                if move_path:
                    record(move_path, "add", current(move_path), after)
                    record(path, "delete", before, "")
                else:
                    record(path, "update", before, after)
        except PatchError as exc:
            record(move_path or path, "unread", None, None, str(exc))
    return list(changes.values())


def compatibility_payload(payload: dict, change: Change, root: Path) -> dict:
    """Internal normalized input for validators, never a claim about Codex tools."""
    output = dict(payload)
    # Project-relative paths avoid MSYS/Python drive-path spelling differences.
    target = change.path.relative_to(root).as_posix()
    if change.action == "update" and change.before is not None and change.after is not None:
        output["tool_name"] = "Edit"
        output["tool_input"] = {"file_path": target, "old_string": change.before, "new_string": change.after}
    else:
        output["tool_name"] = "Write"
        output["tool_input"] = {"file_path": target}
        if change.after is not None:
            output["tool_input"]["content"] = change.after
    return output


class Dispatcher:
    def __init__(self, root: Path, payload: dict):
        self.root = root.resolve()
        self.payload = payload
        self.event = str(payload.get("hook_event_name", ""))
        self.messages: list[str] = []
        self.denials: list[str] = []
        self.deadline = time.monotonic() + EVENT_BUDGET_SECONDS

    def add(self, message: str, *, deny: bool = False) -> None:
        message = message.strip()
        if message and message not in self.messages:
            self.messages.append(message)
        if deny and message and message not in self.denials:
            self.denials.append(message)

    def helper(self, name: str, payload: dict | None = None, *, critical: bool = False) -> None:
        source = self.root / ".codex/hooks" / name
        remaining = self.deadline - time.monotonic()
        if not source.is_file() or remaining <= 0:
            self.add(f"SKIPPED: {name} is unavailable or the hook time budget was reached.", deny=critical)
            return
        current_payload = payload or self.payload
        environment = dict(
            os.environ, STUDIO_PROJECT_ROOT=str(self.root),
            STUDIO_TOOL_CWD=str(current_payload.get("cwd") or self.root),
        )
        try:
            result = subprocess.run(
                ["bash", str(source)], input=json.dumps(current_payload, ensure_ascii=False),
                text=True, encoding="utf-8", errors="replace", capture_output=True, cwd=self.root,
                env=environment, timeout=min(HELPER_TIMEOUT_SECONDS, remaining),
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            self.add(f"SKIPPED: {name} could not finish ({type(exc).__name__}).", deny=critical)
            return
        raw = result.stdout.strip()
        parsed = None
        if raw:
            try:
                parsed = json.loads(raw)
            except ValueError:
                self.add(raw)
        if isinstance(parsed, dict):
            specific = parsed.get("hookSpecificOutput", {})
            if isinstance(specific, dict):
                for key in ("additionalContext", "permissionDecisionReason"):
                    value = specific.get(key)
                    if isinstance(value, str):
                        self.add(value, deny=specific.get("permissionDecision") == "deny")
            if isinstance(parsed.get("systemMessage"), str):
                self.add(parsed["systemMessage"])
            if parsed.get("decision") == "block":
                self.add(str(parsed.get("reason", f"{name} reported a blocking condition.")), deny=True)
        if result.stderr.strip():
            self.add(result.stderr, deny=result.returncode == 2 or (critical and result.returncode != 0))
        elif result.returncode != 0:
            self.add(f"{name} exited with status {result.returncode}.", deny=result.returncode == 2 or critical)

    def dispatch(self) -> dict:
        tool = self.payload.get("tool_name")
        tool_input = self.payload.get("tool_input", {})
        tool_input = tool_input if isinstance(tool_input, dict) else {}
        if self.event == "SessionStart":
            self.helper("session-start.sh")
            self.helper("detect-gaps.sh")
        elif self.event == "PreCompact":
            self.helper("pre-compact.sh")
        elif self.event == "Stop":
            # Synchronous and time-bounded: archive writes finish before exit.
            self.helper("session-stop.sh")
        elif self.event == "SubagentStart":
            self.helper("log-agent.sh")
        elif self.event == "SubagentStop":
            self.helper("log-agent-stop.sh")
            # Transcript content is intentionally not parsed: it is not a stable
            # Codex interface. The parent verifies the files named in its brief.
        elif self.event == "PreToolUse" and tool in ("Bash", "exec_command", "shell_command", "PowerShell"):
            normalized = dict(self.payload)
            command = tool_input.get("command", tool_input.get("cmd", ""))
            if not isinstance(command, str):
                self.add("Shell validation was skipped: no command string was supplied.")
            else:
                normalized["tool_name"] = "PowerShell" if tool == "PowerShell" else "Bash"
                normalized["tool_input"] = dict(tool_input, command=command)
                # Some local clients preserve a per-call working directory.
                if isinstance(tool_input.get("workdir"), str):
                    normalized["cwd"] = tool_input["workdir"]
                is_commit = bool(re.search(r"\bgit(?:\.exe)?\b[\s\S]*\bcommit\b", command, re.I))
                self.helper("validate-commit.sh", normalized, critical=is_commit)
                self.helper("validate-push.sh", normalized)
        elif self.event in ("PreToolUse", "PostToolUse") and tool == "apply_patch":
            command = tool_input.get("command")
            if not isinstance(command, str):
                self.add("Patch validation was skipped: tool_input.command is not a string.")
            else:
                cwd = Path(self.payload.get("cwd") or self.root).resolve()
                try:
                    changes = patch_changes(command, cwd, self.root, after_tool=self.event == "PostToolUse")
                except (PatchError, OSError) as exc:
                    self.add(str(exc))
                    changes = []
                for change in changes:
                    path = change.path.relative_to(self.root).as_posix()
                    if change.note:
                        self.add(f"SKIPPED pre-edit content check for {path}: {change.note}")
                    normalized = compatibility_payload(self.payload, change, self.root)
                    if self.event == "PreToolUse":
                        if change.action == "delete":
                            self.add(f"Patch deletes {path}. Confirm it is within the authorized task and preserve any needed data.")
                        if path in ("design/registry/entities.yaml", "docs/architecture/tr-registry.yaml"):
                            self.helper("validate-registry.sh", normalized)
                        self.helper("validate-write.sh", normalized)
                    elif change.action != "delete":
                        if path.startswith(("assets/", "Assets/", "Content/")):
                            self.helper("validate-assets.sh", normalized)
                        if path.startswith(".agents/skills/"):
                            self.helper("validate-skill-change.sh", normalized)
        return self.output()

    def output(self) -> dict:
        if not self.messages:
            return {}
        message = "\n\n".join(self.messages)
        if len(message) > MAX_OUTPUT_CHARS:
            message = message[:MAX_OUTPUT_CHARS] + "\n[Hook output truncated; run the named validators for all findings.]"
        if self.event in ("PreCompact", "PostCompact", "Stop", "SubagentStop"):
            # These events accept common output, not additionalContext.
            # Archival/audit failures must not accidentally continue an agent.
            return {"systemMessage": message}
        specific = {"hookEventName": self.event, "additionalContext": message}
        output = {"hookSpecificOutput": specific}
        if self.event == "PreToolUse" and self.denials:
            specific["permissionDecision"] = "deny"
            specific["permissionDecisionReason"] = "\n".join(self.denials)[:MAX_OUTPUT_CHARS]
            output["systemMessage"] = "Studio validation blocked this tool call. " + specific["permissionDecisionReason"]
        elif self.event == "PostToolUse" and self.denials:
            # Deliberately do not suggest the completed edit was prevented.
            output["systemMessage"] = "Studio validation found a problem after the edit. The edit has already happened."
        return output


def main() -> int:
    try:
        raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
        if len(raw) > MAX_INPUT_BYTES:
            raise ValueError("Hook input exceeded 16 MiB.")
        payload = json.loads(raw)
        if not isinstance(payload, dict) or not isinstance(payload.get("hook_event_name"), str):
            raise ValueError("Hook input must be an object with hook_event_name.")
        output = Dispatcher(PROJECT_ROOT, payload).dispatch()
    except (OSError, ValueError, TypeError) as exc:
        # A malformed native event cannot be inspected. Exit 2 makes this visible
        # and prevents silently bypassing the pre-commit JSON validator.
        print(f"Studio hook input could not be processed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(output, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
