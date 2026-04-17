#!/usr/bin/env python3
"""Golden SVG regression test for critical class-diagram scenarios.

Usage:
  python test_class_diagram_svg_golden.py
  UPDATE_GOLDEN=1 python test_class_diagram_svg_golden.py
    GOLDEN_CI_MODE=1 python test_class_diagram_svg_golden.py

CI-friendly behavior:
- In CI mode, baselines are never auto-created or updated.
- Missing baselines and mismatches fail the test.
- UPDATE_GOLDEN is rejected when CI mode is enabled.
"""

from __future__ import annotations

import difflib
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "Scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from parser import parse_csv
from class_diagram_renderer import render_class_diagram_svg

BASELINE_DIR = REPO_ROOT / "Test" / "baselines" / "class_diagram"

SCENARIOS = [
    {
        "name": "FanoutTop",
        "csv": REPO_ROOT / "Test" / "tests" / "fanout.csv",
        "diagram_id": "FanoutTop",
        "baseline": BASELINE_DIR / "FanoutTop.svg",
    },
    {
        "name": "SimpleFourBox",
        "csv": REPO_ROOT / "Test" / "tests" / "test_spacing_minimal.csv",
        "diagram_id": "SimpleFourBox",
        "baseline": BASELINE_DIR / "SimpleFourBox.svg",
    },
    {
        "name": "OrthogonalTopEntryProbe",
        "csv": REPO_ROOT / "Process" / "01_System" / "40_Tests" / "20_Advanced" / "test_class_diagram_all_connector_combinations.csv",
        "diagram_id": "OrthogonalTopEntryProbe",
        "baseline": BASELINE_DIR / "OrthogonalTopEntryProbe.svg",
    },
]


def _normalize(svg: str) -> str:
    text = svg.replace("\r\n", "\n").replace("\r", "\n")
    # Remove volatile render version stamps from root attribute and footer.
    text = re.sub(r'\sdata-render-version="[^"]+"', '', text)
    text = re.sub(r'v:\d{8}-\d{6}', 'v:STAMP', text)
    lines = [line.rstrip() for line in text.split("\n")]
    return "\n".join(lines).strip() + "\n"


def _render(csv_path: Path, diagram_id: str) -> str:
    model = parse_csv(str(csv_path))
    diagram = next(d for d in model.class_diagrams if d.diagram_id == diagram_id)
    return render_class_diagram_svg(model, diagram, verbosity_level="High")


def _env_true(name: str) -> bool:
    return os.environ.get(name, "0").strip().lower() in {"1", "true", "yes", "on"}


def run_test() -> int:
    BASELINE_DIR.mkdir(parents=True, exist_ok=True)
    update = _env_true("UPDATE_GOLDEN")
    ci_mode = _env_true("GOLDEN_CI_MODE") or _env_true("CI")

    if ci_mode and update:
        print("FAIL: UPDATE_GOLDEN cannot be used in CI mode.")
        return 1

    failures = []
    missing = []
    for scenario in SCENARIOS:
        current = _normalize(_render(scenario["csv"], scenario["diagram_id"]))
        baseline_path = scenario["baseline"]

        if not baseline_path.exists():
            if ci_mode:
                missing.append((scenario["name"], baseline_path))
                continue
            if not update:
                missing.append((scenario["name"], baseline_path))
                continue
            baseline_path.write_text(current, encoding="utf-8")
            print(f"UPDATED baseline: {baseline_path.name}")
            continue

        expected = _normalize(baseline_path.read_text(encoding="utf-8"))
        if current != expected:
            if update:
                baseline_path.write_text(current, encoding="utf-8")
                print(f"UPDATED baseline: {baseline_path.name}")
                continue
            diff = list(
                difflib.unified_diff(
                    expected.splitlines(),
                    current.splitlines(),
                    fromfile=f"baseline/{baseline_path.name}",
                    tofile=f"current/{baseline_path.name}",
                    lineterm="",
                )
            )
            failures.append((scenario["name"], baseline_path, diff[:120]))

    if missing:
        for name, baseline_path in missing:
            print(f"FAIL: missing golden baseline for {name} ({baseline_path})")
        if not ci_mode:
            print("Hint: run with UPDATE_GOLDEN=1 to create baselines intentionally.")
        return 1

    if failures:
        for name, baseline_path, diff_head in failures:
            print(f"FAIL: golden mismatch for {name} ({baseline_path})")
            for line in diff_head:
                print(line)
        if not ci_mode:
            print("Hint: run with UPDATE_GOLDEN=1 to refresh baselines intentionally.")
        return 1

    print("OK: golden SVG comparisons passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_test())
