#!/usr/bin/env python3
"""Ensure local diagram server is running and healthy.

Behavior:
- If health endpoint is already good, exits 0.
- If not healthy, starts Scripts/server.py on the requested port.
- Polls until healthy or timeout, then exits non-zero on failure.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


def check_health(url: str, timeout: float) -> tuple[bool, str]:
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as response:
            status = response.getcode()
            body = response.read().decode("utf-8", errors="replace")
            if not (200 <= status < 400):
                return False, f"HTTP {status}"

            # Prefer strict validation for our app endpoint.
            try:
                payload = json.loads(body)
                if isinstance(payload, list):
                    return True, f"OK: endpoint healthy with list payload ({len(payload)} item(s))"
                if isinstance(payload, dict):
                    if "csvs" in payload and isinstance(payload["csvs"], list):
                        return True, f"OK: endpoint healthy with csvs payload ({len(payload['csvs'])} item(s))"
                    if payload:
                        return True, "OK: endpoint healthy with JSON object payload"
                    return True, "OK: endpoint healthy with empty JSON object payload"
                return True, "OK: endpoint healthy with JSON payload"
            except json.JSONDecodeError:
                return False, "Health endpoint did not return JSON"
    except urllib.error.HTTPError as exc:
        return False, f"HTTP error {exc.code}"
    except urllib.error.URLError as exc:
        return False, f"URL error: {exc.reason}"
    except TimeoutError:
        return False, "Timeout"
    except Exception as exc:  # Defensive catch for env differences
        return False, f"Unexpected error: {exc}"


def launch_server(repo_root: Path, python_exe: str, port: int) -> tuple[bool, str]:
    cmd = [python_exe, "Scripts/server.py", str(port)]

    kwargs = {
        "cwd": str(repo_root),
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
        "stdin": subprocess.DEVNULL,
    }

    if os.name == "nt":
        kwargs["creationflags"] = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True

    try:
        subprocess.Popen(cmd, **kwargs)
        return True, f"Launched server using: {' '.join(cmd)}"
    except Exception as exc:
        return False, f"Failed to launch server: {exc}"


def resolve_python_exe(repo_root: Path) -> str:
    venv_python = repo_root / ".venv" / "Scripts" / "python.exe"
    if venv_python.exists():
        return str(venv_python)
    return sys.executable


def main() -> int:
    parser = argparse.ArgumentParser(description="Ensure local server is ready")
    parser.add_argument("--port", type=int, default=8000, help="Port for the local server")
    parser.add_argument("--attempts", type=int, default=3, help="Poll attempts")
    parser.add_argument("--interval", type=float, default=0.5, help="Seconds between attempts")
    parser.add_argument("--timeout", type=float, default=1.0, help="Per-request timeout")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    url = f"http://localhost:{args.port}/api/csvs"

    attempts = max(1, args.attempts)
    interval = max(0.1, args.interval)
    timeout = max(0.2, args.timeout)

    print(f"Ensuring server readiness at {url}")

    healthy, message = check_health(url, timeout)
    if healthy:
        print(f"OK: {message}")
        return 0

    print(f"Not healthy yet: {message}")
    python_exe = resolve_python_exe(repo_root)
    started, launch_msg = launch_server(repo_root, python_exe, args.port)
    print(launch_msg)
    if not started:
        return 1

    for attempt in range(1, attempts + 1):
        healthy, message = check_health(url, timeout)
        if healthy:
            print(f"[{attempt}/{attempts}] {message}")
            return 0
        print(f"[{attempt}/{attempts}] waiting: {message}")
        time.sleep(interval)

    print("FAIL: Server did not become healthy in time")
    return 1


if __name__ == "__main__":
    sys.exit(main())
