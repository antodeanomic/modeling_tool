#!/usr/bin/env python3
"""Regression checks for class-diagram connector edge selection and overlap."""

import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(REPO_ROOT, "Scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from parser import parse_csv
from model import ClassDiagramDef
from class_diagram_renderer import _layout_classes_uml_standard, _optimize_layout_for_grid_collisions


def _path_points(connector):
    points = [(connector.source_x, connector.source_y)]
    points.extend(list(connector.segments))
    if points[-1] != (connector.target_x, connector.target_y):
        points.append((connector.target_x, connector.target_y))
    return points


def _final_direction(connector):
    points = _path_points(connector)
    prev_idx = len(points) - 2
    while prev_idx >= 0 and points[prev_idx] == (connector.target_x, connector.target_y):
        prev_idx -= 1
    prev_x, prev_y = points[prev_idx]
    dx = connector.target_x - prev_x
    dy = connector.target_y - prev_y
    if dx > 0:
        return "right"
    if dx < 0:
        return "left"
    if dy > 0:
        return "down"
    if dy < 0:
        return "up"
    return "none"


def run_test() -> int:
    csv_path = os.path.join(
        REPO_ROOT,
        "Process",
        "01_System",
        "40_Tests",
        "20_Advanced",
        "test_class_diagram_orthogonal_stress.csv",
    )

    model = parse_csv(csv_path)
    if not model.class_diagrams:
        print("FAIL: no class diagrams parsed")
        return 1

    diagram = model.class_diagrams[0]
    layers = ["core", "security"]
    filtered_rels = [r for r in diagram.relationships if (not r.layer or r.layer in layers)]
    filtered = ClassDiagramDef(
        diagram_id=diagram.diagram_id,
        description=diagram.description,
        relationships=filtered_rels,
        routing=diagram.routing,
        element_types=diagram.element_types,
    )

    boxes = _layout_classes_uml_standard(filtered, model, "High", routing="orthogonal")
    _boxes, planner, _hard_count, _details = _optimize_layout_for_grid_collisions(
        filtered, boxes, "orthogonal", "High", layers
    )

    gateway_order = None
    auth_user = None
    ending_cases = {}
    for connector in planner.connectors:
        if (connector.source_name, connector.target_name) == ("Gateway", "OrderService"):
            gateway_order = connector
            ending_cases[(connector.source_name, connector.target_name)] = connector
        elif (connector.source_name, connector.target_name) == ("AuthService", "UserService"):
            auth_user = connector
        elif (connector.source_name, connector.target_name) in {
            ("Gateway", "SessionStore"),
            ("Gateway", "TraceContext"),
            ("AuthService", "AuditLog"),
        }:
            ending_cases[(connector.source_name, connector.target_name)] = connector

    if gateway_order is None or auth_user is None:
        print("FAIL: required connectors not found in filtered diagram")
        return 1

    if gateway_order.target_edge != "bottom":
        print(
            f"FAIL: Gateway->OrderService target edge should be bottom for left-to-up routing, got {gateway_order.target_edge}"
        )
        return 1

    gateway_cells = planner._collect_path_cells(_path_points(gateway_order))
    auth_cells = planner._collect_path_cells(_path_points(auth_user))
    shared_cells = sorted(gateway_cells & auth_cells)
    if shared_cells:
        print(f"FAIL: Gateway->OrderService overlaps AuthService->UserService at {shared_cells[:5]}")
        return 1

    expected_final_dirs = {
        ("Gateway", "SessionStore"): "right",
        ("Gateway", "TraceContext"): "up",
        ("AuthService", "AuditLog"): "up",
        ("Gateway", "OrderService"): "up",
    }
    for pair, expected_dir in expected_final_dirs.items():
        connector = ending_cases.get(pair)
        if connector is None:
            print(f"FAIL: missing connector for ending regression {pair}")
            return 1
        actual_dir = _final_direction(connector)
        if actual_dir != expected_dir:
            print(
                f"FAIL: {pair[0]}->{pair[1]} should end with final direction {expected_dir}, got {actual_dir}"
            )
            return 1

    print(
        "OK: connector edge selection, overlap avoidance, and ending directions are correct"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(run_test())