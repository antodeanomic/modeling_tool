#!/usr/bin/env python3
"""2-segment arrow matrix regression test cases.

This test validates that the dedicated AR2 arrow matrix test diagram routes
as two-segment orthogonal elbows for all 14 arrow syntaxes.
"""

import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(REPO_ROOT, "Scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from parser import parse_csv
from class_diagram_renderer import _layout_classes_uml_standard, _optimize_layout_for_grid_collisions


def _path_points(connector):
    points = [(connector.source_x, connector.source_y)]
    points.extend(list(connector.segments))
    if points[-1] != (connector.target_x, connector.target_y):
        points.append((connector.target_x, connector.target_y))
    return points


def _is_orthogonal(points, tol=1e-6):
    for i in range(len(points) - 1):
        x1, y1 = points[i]
        x2, y2 = points[i + 1]
        if abs(x1 - x2) > tol and abs(y1 - y2) > tol:
            return False
    return True


def run_test() -> int:
    csv_path = os.path.join(
        REPO_ROOT,
        "Process",
        "01_System",
        "40_Tests",
        "20_Advanced",
        "test_class_diagram_two_segment_combinations.csv",
    )

    model = parse_csv(csv_path)
    diagram = next((d for d in model.class_diagrams if d.diagram_id == "OrthogonalArrowTypeTwoSegmentCombos"), None)
    if diagram is None:
        print("FAIL: OrthogonalArrowTypeTwoSegmentCombos diagram not found")
        return 1

    boxes = _layout_classes_uml_standard(diagram, model, "High", routing="orthogonal")
    _, planner, _, _ = _optimize_layout_for_grid_collisions(diagram, boxes, "orthogonal", "High", None)

    connectors = [c for c in planner.connectors if c.source_name.startswith("AR2_S")]
    if len(connectors) != 14:
        print(f"FAIL: expected 14 AR2 connectors, got {len(connectors)}")
        return 1

    failures = []
    for connector in connectors:
        points = _path_points(connector)
        if len(connector.segments) != 2:
            failures.append(
                f"{connector.source_name}->{connector.target_name}: expected 2 segments, got {len(connector.segments)}"
            )
            continue
        if not _is_orthogonal(points):
            failures.append(
                f"{connector.source_name}->{connector.target_name}: non-orthogonal path {points}"
            )

    if failures:
        print("FAIL: two-segment matrix regressions found")
        for line in failures:
            print(f"  - {line}")
        return 1

    print("OK: all AR2 matrix connectors are two-segment orthogonal elbows")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_test())
