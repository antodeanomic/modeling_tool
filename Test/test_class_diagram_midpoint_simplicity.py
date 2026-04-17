#!/usr/bin/env python3
"""Regression checks for midpoint defaults and simple-route preference."""

import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(REPO_ROOT, "Scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from parser import parse_csv
from class_diagram_renderer import _layout_classes_orthogonal
from class_diagram_connectors import ConnectorPlanner


def _build_planner_for_simple_four_box() -> ConnectorPlanner:
    csv_path = os.path.join(REPO_ROOT, "Test", "tests", "test_spacing_minimal.csv")
    model = parse_csv(csv_path)
    diagram = next((d for d in model.class_diagrams if d.diagram_id == "SimpleFourBox"), None)
    if diagram is None:
        raise AssertionError("SimpleFourBox diagram not found")

    boxes = _layout_classes_orthogonal(diagram, model, verbosity="High")

    planner = ConnectorPlanner(routing_mode="orthogonal")
    for name, box in boxes.items():
        planner.add_rectangle(name, box["x"], box["y"], box["width"], box["height"])

    for rel in diagram.relationships:
        planner.add_connector(rel.source, rel.target, rel.arrow, rel.src_mult, rel.tgt_mult, rel.label, rel.layer)

    planner.plan_connectors()
    return planner


def _assert_midpoint_and_simplicity_defaults() -> None:
    planner = _build_planner_for_simple_four_box()

    by_pair = {(c.source_name, c.target_name): c for c in planner.connectors}

    b_to_d = by_pair.get(("ServiceB", "ServiceD"))
    if b_to_d is None:
        raise AssertionError("ServiceB->ServiceD connector missing")

    if b_to_d.path_type != "direct":
        raise AssertionError(f"ServiceB->ServiceD must be direct, got path_type={b_to_d.path_type}")
    if b_to_d.source_edge != "top" or b_to_d.target_edge != "bottom":
        raise AssertionError(
            f"ServiceB->ServiceD must use top->bottom, got {b_to_d.source_edge}->{b_to_d.target_edge}"
        )

    service_b = planner.grids["ServiceB"]
    service_d = planner.grids["ServiceD"]
    expected_src_mid = (len(service_b.get_points("top")) + 1) // 2
    expected_tgt_mid = (len(service_d.get_points("bottom")) + 1) // 2

    if b_to_d.source_point_idx != expected_src_mid or b_to_d.target_point_idx != expected_tgt_mid:
        raise AssertionError(
            f"ServiceB->ServiceD must use midpoint slots ({expected_src_mid}->{expected_tgt_mid}), got {b_to_d.source_point_idx}->{b_to_d.target_point_idx}"
        )

    c_to_d = by_pair.get(("ServiceC", "ServiceD"))
    if c_to_d is None:
        raise AssertionError("ServiceC->ServiceD connector missing")

    # Prefer a simple connector when geometric alternatives are similarly short.
    if c_to_d.path_type == "multi_segment" and len(c_to_d.segments) > 1:
        raise AssertionError(
            f"ServiceC->ServiceD should be simple (<=1 bend), got segments={c_to_d.segments}"
        )


if __name__ == "__main__":
    _assert_midpoint_and_simplicity_defaults()
    print("OK: midpoint defaults and simple-route preference checks passed")
