#!/usr/bin/env python3
"""Regression checks for 2-segment orthogonal connector geometry.

Guards against diagonal regressions introduced by segment-length post-processing.
"""

import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(REPO_ROOT, "Scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from parser import parse_csv
from model import ClassDiagramDef
from class_diagram_renderer import _layout_classes_uml_standard, _optimize_layout_for_grid_collisions
from class_diagram_connectors import ConnectorPlanner, ConnectorPath


def _path_points(connector):
    points = [(connector.source_x, connector.source_y)]
    points.extend(list(connector.segments))
    if points[-1] != (connector.target_x, connector.target_y):
        points.append((connector.target_x, connector.target_y))
    return points


def _segment_axis(a, b, tol=1e-6):
    x1, y1 = a
    x2, y2 = b
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    if dx <= tol and dy <= tol:
        return "Z"
    if dx <= tol:
        return "V"
    if dy <= tol:
        return "H"
    return "D"


def _assert_path_right_angled(connector, context):
    points = _path_points(connector)
    axes = []
    for i in range(len(points) - 1):
        axis = _segment_axis(points[i], points[i + 1])
        if axis == "D":
            raise AssertionError(
                f"FAIL: diagonal segment in {context}: "
                f"{connector.source_name}->{connector.target_name} "
                f"segment#{i} {points[i]} -> {points[i + 1]} "
                f"source_edge={connector.source_edge} target_edge={connector.target_edge}"
            )
        if axis != "Z":
            axes.append(axis)

    for i in range(len(axes) - 1):
        if axes[i] == axes[i + 1]:
            raise AssertionError(
                f"FAIL: non-right-angle turn in {context}: "
                f"{connector.source_name}->{connector.target_name} "
                f"axes={axes} source_edge={connector.source_edge} target_edge={connector.target_edge}"
            )


def _run_diagram(csv_path, diagram_id, layers):
    model = parse_csv(csv_path)
    diagram = next((d for d in model.class_diagrams if d.diagram_id == diagram_id), None)
    if diagram is None:
        raise AssertionError(f"FAIL: diagram {diagram_id} not found in {csv_path}")

    rels = [r for r in diagram.relationships if (not layers or not r.layer or r.layer in layers)]
    if not rels:
        raise AssertionError(f"FAIL: no relationships for layers={layers} in {diagram_id}")

    filtered = ClassDiagramDef(
        diagram_id=diagram.diagram_id,
        description=diagram.description,
        relationships=rels,
        routing=diagram.routing,
        element_types=diagram.element_types,
    )

    boxes = _layout_classes_uml_standard(filtered, model, "High", routing="orthogonal")
    _, planner, _, _ = _optimize_layout_for_grid_collisions(
        filtered, boxes, "orthogonal", "High", layers
    )
    return planner.connectors


def _build_two_segment_variation_cases():
    planner = ConnectorPlanner(routing_mode="orthogonal")

    # Build one representative two-segment elbow per source-edge variation.
    # Segment list intentionally includes target endpoint as second point to
    # exercise the historical regression path.
    cases = []

    c_right = ConnectorPath("A", "B", "-->", src_mult="1", tgt_mult="0..*", label="lbl")
    c_right.source_edge = "right"
    c_right.target_edge = "bottom"
    c_right.source_x, c_right.source_y = (100.0, 200.0)
    c_right.target_x, c_right.target_y = (300.0, 80.0)
    c_right.segments = [(300.0, 200.0), (300.0, 80.0)]
    cases.append(c_right)

    c_left = ConnectorPath("A", "B", "-->", src_mult="1", tgt_mult="0..*", label="lbl")
    c_left.source_edge = "left"
    c_left.target_edge = "top"
    c_left.source_x, c_left.source_y = (300.0, 200.0)
    c_left.target_x, c_left.target_y = (100.0, 80.0)
    c_left.segments = [(100.0, 200.0), (100.0, 80.0)]
    cases.append(c_left)

    c_top = ConnectorPath("A", "B", "-->", src_mult="1", tgt_mult="0..*", label="lbl")
    c_top.source_edge = "top"
    c_top.target_edge = "right"
    c_top.source_x, c_top.source_y = (200.0, 300.0)
    c_top.target_x, c_top.target_y = (340.0, 120.0)
    c_top.segments = [(200.0, 120.0), (340.0, 120.0)]
    cases.append(c_top)

    c_bottom = ConnectorPath("A", "B", "-->", src_mult="1", tgt_mult="0..*", label="lbl")
    c_bottom.source_edge = "bottom"
    c_bottom.target_edge = "left"
    c_bottom.source_x, c_bottom.source_y = (200.0, 120.0)
    c_bottom.target_x, c_bottom.target_y = (60.0, 300.0)
    c_bottom.segments = [(200.0, 300.0), (60.0, 300.0)]
    cases.append(c_bottom)

    # Add target-edge variations that historically interacted with last-segment extension.
    c_target_left = ConnectorPath("A", "B", "-->", src_mult="1", tgt_mult="0..*", label="lbl")
    c_target_left.source_edge = "bottom"
    c_target_left.target_edge = "left"
    c_target_left.source_x, c_target_left.source_y = (260.0, 140.0)
    c_target_left.target_x, c_target_left.target_y = (100.0, 260.0)
    c_target_left.segments = [(260.0, 260.0), (100.0, 260.0)]
    cases.append(c_target_left)

    c_target_right = ConnectorPath("A", "B", "-->", src_mult="1", tgt_mult="0..*", label="lbl")
    c_target_right.source_edge = "top"
    c_target_right.target_edge = "right"
    c_target_right.source_x, c_target_right.source_y = (100.0, 260.0)
    c_target_right.target_x, c_target_right.target_y = (260.0, 140.0)
    c_target_right.segments = [(100.0, 140.0), (260.0, 140.0)]
    cases.append(c_target_right)

    c_target_top = ConnectorPath("A", "B", "-->", src_mult="1", tgt_mult="0..*", label="lbl")
    c_target_top.source_edge = "right"
    c_target_top.target_edge = "top"
    c_target_top.source_x, c_target_top.source_y = (80.0, 120.0)
    c_target_top.target_x, c_target_top.target_y = (260.0, 300.0)
    c_target_top.segments = [(260.0, 120.0), (260.0, 300.0)]
    cases.append(c_target_top)

    c_target_bottom = ConnectorPath("A", "B", "-->", src_mult="1", tgt_mult="0..*", label="lbl")
    c_target_bottom.source_edge = "left"
    c_target_bottom.target_edge = "bottom"
    c_target_bottom.source_x, c_target_bottom.source_y = (260.0, 120.0)
    c_target_bottom.target_x, c_target_bottom.target_y = (80.0, 300.0)
    c_target_bottom.segments = [(80.0, 120.0), (80.0, 300.0)]
    cases.append(c_target_bottom)

    return planner, cases


def run_test() -> int:
    # 1) Real regression context: dense stress test layer variants.
    csv_path = os.path.join(
        REPO_ROOT,
        "Process",
        "01_System",
        "40_Tests",
        "20_Advanced",
        "test_class_diagram_orthogonal_stress.csv",
    )

    for layers in (["core"], ["core", "security"]):
        connectors = _run_diagram(csv_path, "OrthogonalStressDense", layers)
        two_seg = [c for c in connectors if len(c.segments) == 2]
        if not two_seg:
            print(f"FAIL: no 2-segment connectors found for layers={layers}")
            return 1
        for connector in two_seg:
            _assert_path_right_angled(connector, f"OrthogonalStressDense layers={layers}")

    # Explicit user-reported connector check.
    connectors_core = _run_diagram(csv_path, "OrthogonalStressDense", ["core"])
    gateway_order = next(
        (c for c in connectors_core if (c.source_name, c.target_name) == ("Gateway", "OrderService")),
        None,
    )
    if gateway_order is None:
        print("FAIL: Gateway->OrderService not found in core layer")
        return 1
    _assert_path_right_angled(gateway_order, "Gateway->OrderService core")

    # 1b) Appended AR2 rows inside the existing arrow matrix should be true two-segment elbows.
    arrow_matrix_connectors = _run_diagram(
        os.path.join(
            REPO_ROOT,
            "Process",
            "01_System",
            "40_Tests",
            "20_Advanced",
            "test_class_diagram_all_connector_combinations.csv",
        ),
        "OrthogonalArrowTypeAndRoutes",
        None,
    )
    ar2_connectors = [c for c in arrow_matrix_connectors if c.source_name.startswith("AR2_")]
    if len(ar2_connectors) < 14:
        print(
            f"FAIL: expected at least 14 AR2 connectors in OrthogonalArrowTypeAndRoutes, got {len(ar2_connectors)}"
        )
        return 1

    for connector in ar2_connectors:
        if len(connector.segments) != 2:
            print(
                f"FAIL: expected 2 segments for {connector.source_name}->{connector.target_name}, got {len(connector.segments)}"
            )
            return 1
        _assert_path_right_angled(connector, "OrthogonalArrowTypeAndRoutes AR2")

    # 2) Synthetic 2-segment variation suite.
    planner, cases = _build_two_segment_variation_cases()
    for idx, connector in enumerate(cases, start=1):
        planner._extend_first_segment_for_label_clearance(connector)
        planner._extend_last_segment_for_label_clearance(connector)
        _assert_path_right_angled(connector, f"synthetic_case_{idx}")

    print("OK: all 2-segment variation cases preserve right angles")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_test())
