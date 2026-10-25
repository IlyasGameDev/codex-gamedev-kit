#!/usr/bin/env python3
"""Check the studio with Codex's native parsers without starting a model turn.

The config is copied into a disposable Codex configuration home and read through
the app-server protocol. This validates its schema, not the user's project or
hook trust. Only initialize/config-read requests are sent. Nothing is installed,
no credentials are copied, and the user's Codex configuration is not changed.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import queue
import shutil
import subprocess
import sys
import tempfile
import threading
import time


POLICY_CASES = [
    (["git", "push", "origin", "main"], "prompt"),
    (["git", "status"], None),
    (["gh", "pr", "view", "42"], None),
    (["gh", "pr", "merge", "42"], "prompt"),
    (["gh", "issue", "comment", "42", "--body-file", "note.txt"], "prompt"),
    (["gh", "release", "create", "v1.0.0", "game.zip"], "prompt"),
    (["butler", "push", "build", "owner/game:windows"], "prompt"),
    (["steamcmd", "+run_app_build", "build.vdf", "+quit"], "prompt"),
    (["npm", "publish"], "prompt"),
    (["npm", "test"], None),
    (["rm", "-rf", "temporary-build-output"], None),
]


class ProbeError(RuntimeError):
    """A native Codex parser check failed or could not run."""


def read_native_config(binary: str, config_text: str) -> dict:
    """Read a temporary copy through strict native config loading."""
    with tempfile.TemporaryDirectory(prefix="studio-codex-config-") as scratch:
        scratch_path = Path(scratch)
        (scratch_path / "config.toml").write_text(config_text, encoding="utf-8")
        process_env = os.environ.copy()
        # This environment setting applies only to this disposable child process.
        process_env["CODEX_HOME"] = scratch
        command = [
            binary, "app-server", "--stdio", "--strict-config",
            "-c", "features.hooks=false", "-c", "features.plugins=false",
        ]
        process = subprocess.Popen(
            command, cwd=scratch, env=process_env, text=True,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            encoding="utf-8", errors="replace",
        )
        events: queue.Queue[tuple[str, str | None]] = queue.Queue()

        def read_stream(stream, name: str) -> None:
            try:
                for line in stream:
                    events.put((name, line))
            finally:
                events.put((name, None))

        readers = [
            threading.Thread(target=read_stream, args=(process.stdout, "stdout"), daemon=True),
            threading.Thread(target=read_stream, args=(process.stderr, "stderr"), daemon=True),
        ]
        for reader in readers:
            reader.start()

        def send(message: dict) -> None:
            try:
                process.stdin.write(json.dumps(message) + "\n")
                process.stdin.flush()
            except (BrokenPipeError, OSError) as exc:
                raise ProbeError("Codex closed the app-server input before configuration could be read.") from exc

        diagnostic_lines: list[str] = []
        closed_streams: set[str] = set()
        deadline = time.monotonic() + 20
        result = None
        try:
            send({
                "id": 1,
                "method": "initialize",
                "params": {"clientInfo": {"name": "studio-config-validator", "version": "1.0.0"}},
            })
            while time.monotonic() < deadline:
                try:
                    stream_name, line = events.get(timeout=min(0.5, max(0.01, deadline - time.monotonic())))
                except queue.Empty:
                    if process.poll() is not None and len(closed_streams) == 2:
                        break
                    continue
                if line is None:
                    closed_streams.add(stream_name)
                    if len(closed_streams) == 2:
                        break
                    continue
                if stream_name == "stderr":
                    diagnostic_lines.append(line.rstrip())
                    continue
                try:
                    response = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if response.get("id") in (1, 2) and "error" in response:
                    raise ProbeError("Codex config protocol error: " + json.dumps(response["error"]))
                if response.get("id") == 1:
                    send({"method": "initialized"})
                    send({
                        "id": 2,
                        "method": "config/read",
                        "params": {"includeLayers": True, "cwd": scratch},
                    })
                elif response.get("id") == 2:
                    result = response["result"]
                    break
        finally:
            try:
                process.stdin.close()
            except OSError:
                pass
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.terminate()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=2)
            for reader in readers:
                reader.join(timeout=1)
            process.stdout.close()
            process.stderr.close()

        if result is None:
            detail = "\n".join(diagnostic_lines[-8:])
            raise ProbeError("Native config read failed or timed out. " + detail)
        user_layers = [layer for layer in result.get("layers", []) if layer.get("name", {}).get("type") == "user"]
        if not any(Path(layer["name"].get("file", "")).resolve() == (scratch_path / "config.toml").resolve() for layer in user_layers):
            raise ProbeError("Codex did not report loading the temporary config file.")
        return result["config"]


def check_native_config(binary: str, root: Path) -> dict:
    source = (root / ".codex" / "config.toml").read_text(encoding="utf-8")
    parsed = read_native_config(binary, source)
    # Prove strict mode is actually validating keys instead of silently ignoring
    # this configuration. The invalid field exists only in a disposable copy.
    invalid_field = "studio_validation_unknown_key"
    try:
        read_native_config(binary, f"{invalid_field} = true\n" + source)
    except ProbeError as exc:
        if f"unknown configuration field `{invalid_field}`" not in str(exc):
            raise ProbeError("Strict-mode negative control did not produce the expected schema error: " + str(exc)) from exc
    else:
        raise ProbeError("Strict mode accepted an unknown field; native validation is not reliable on this Codex version.")
    return {
        "status": "ok",
        "strict_negative_control": "rejected_unknown_field",
        "approval_policy": parsed.get("approval_policy"),
        "sandbox_mode": parsed.get("sandbox_mode"),
        "agents_enabled": (parsed.get("agents") or {}).get("enabled"),
        "max_concurrent_threads_per_session": (parsed.get("agents") or {}).get("max_concurrent_threads_per_session"),
        "scope": "Native config schema only; project and hook trust are not tested or changed.",
    }


def check_execution_policy(binary: str, root: Path) -> dict:
    policy = root / ".codex" / "rules" / "studio.rules"
    with tempfile.TemporaryDirectory(prefix="studio-codex-policy-") as scratch:
        process_env = os.environ.copy()
        process_env["CODEX_HOME"] = scratch
        for argv, expected in POLICY_CASES:
            result = subprocess.run(
                [binary, "execpolicy", "check", "--rules", str(policy), "--", *argv],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                cwd=scratch, env=process_env, timeout=10,
            )
            if result.returncode:
                raise ProbeError("Native execution-policy parsing failed: " + result.stderr[-1500:])
            try:
                decision = json.loads(result.stdout).get("decision")
            except json.JSONDecodeError as exc:
                raise ProbeError("Codex returned invalid JSON for the execution-policy check.") from exc
            if decision != expected:
                raise ProbeError(f"Policy for {argv!r}: expected {expected!r}, got {decision!r}.")
    return {"status": "ok", "cases_passed": len(POLICY_CASES)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex", default=shutil.which("codex"), help="Path to the Codex CLI executable")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--json", action="store_true", help="Print a machine-readable result")
    args = parser.parse_args()
    try:
        if not args.codex:
            raise ProbeError("Codex CLI is not on PATH. Install a current version or supply --codex /path/to/codex.")
        resolved_binary = shutil.which(args.codex)
        if not resolved_binary:
            raise ProbeError(f"Codex executable was not found: {args.codex}")
        resolved_binary = str(Path(resolved_binary).resolve())
        version_result = subprocess.run([resolved_binary, "--version"], capture_output=True, text=True, timeout=10)
        if version_result.returncode:
            raise ProbeError("Cannot run Codex CLI: " + version_result.stderr[-1500:])
        result = {
            "status": "ok",
            "codex_version": version_result.stdout.strip(),
            "native_config": check_native_config(resolved_binary, args.root.resolve()),
            "execution_policy": check_execution_policy(resolved_binary, args.root.resolve()),
            "model_turns_started": 0,
        }
    except (ProbeError, OSError, subprocess.TimeoutExpired) as exc:
        result = {"status": "failed", "error": str(exc)}
    if args.json:
        print(json.dumps(result, indent=2))
    elif result["status"] == "ok":
        print(f"PASS: {result['codex_version']} accepted config with strict validation.")
        print(f"PASS: {result['execution_policy']['cases_passed']} native execution-policy cases.")
        print("No model turns started. User configuration and project/hook trust were not changed.")
    else:
        print("FAIL: " + result["error"], file=sys.stderr)
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
