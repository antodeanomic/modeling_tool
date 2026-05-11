#!/usr/bin/env python3
"""Simple HTTP health check for local diagram server readiness."""

from __future__ import annotations

import argparse
import sys
import time
import urllib.error
import urllib.request


def check_url(url: str, timeout: float) -> tuple[bool, str]:
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as response:
            status = response.getcode()
            if 200 <= status < 400:
                return True, f"OK: {url} responded with HTTP {status}"
            return False, f"FAIL: {url} responded with HTTP {status}"
    except urllib.error.HTTPError as exc:
        return False, f"FAIL: HTTP error from {url}: {exc.code}"
    except urllib.error.URLError as exc:
        return False, f"FAIL: URL error for {url}: {exc.reason}"
    except TimeoutError:
        return False, f"FAIL: Timeout while connecting to {url}"
    except Exception as exc:  # Defensive catch for local env differences
        return False, f"FAIL: Unexpected error for {url}: {exc}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Health check local app endpoint")
    parser.add_argument("--url", default="http://localhost:8000", help="Endpoint URL to verify")
    parser.add_argument("--attempts", type=int, default=3, help="Number of attempts before failing")
    parser.add_argument("--interval", type=float, default=0.5, help="Seconds between attempts")
    parser.add_argument("--timeout", type=float, default=1.0, help="Per-request timeout seconds")
    args = parser.parse_args()

    attempts = max(1, args.attempts)
    interval = max(0.1, args.interval)
    timeout = max(0.2, args.timeout)

    print(f"Health check: {args.url}")
    print(f"Attempts: {attempts}, interval: {interval:.1f}s, timeout: {timeout:.1f}s")

    for attempt in range(1, attempts + 1):
        ok, message = check_url(args.url, timeout)
        if ok:
            print(f"[{attempt}/{attempts}] {message}")
            return 0

        print(f"[{attempt}/{attempts}] {message}")
        if attempt < attempts:
            time.sleep(interval)

    print("FAIL: Endpoint did not become ready in time")
    return 1


if __name__ == "__main__":
    sys.exit(main())
