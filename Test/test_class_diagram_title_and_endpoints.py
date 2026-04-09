#!/usr/bin/env python3
"""Regression checks for class-diagram title placement and endpoint directions."""

import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(REPO_ROOT, "Scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from parser import parse_csv
from class_diagram_renderer import render_class_diagram_svg, _final_path_direction
from class_diagram_connectors import ConnectorPlanner, ConnectorPath


def _source_edge_from_first_segment(points):
    x1, y1 = points[0]
    x2, y2 = points[1]
    dx = x2 - x1
    dy = y2 - y1
    if abs(dx) >= abs(dy):
        return "right" if dx > 0 else "left"
    return "bottom" if dy > 0 else "top"


def _assert_title_above_diagram_body() -> None:
    csv_path = os.path.join(REPO_ROOT, "Process", "02_Architecture", "class_diagrams.csv")
    model = parse_csv(csv_path)
    diagram = model.get_class_diagram("ParserToModel")
    if diagram is None:
        raise AssertionError("ParserToModel class diagram not found")

    svg = render_class_diagram_svg(model, diagram, verbosity_level="High")

    title_match = re.search(
        r'<text x="([0-9.\-]+)" y="([0-9.\-]+)" font-family="[^"]+" font-size="16" font-weight="bold" text-anchor="middle" fill="#333">',
        svg,
    )
    if not title_match:
        raise AssertionError("diagram title text not found in SVG")

    title_y = float(title_match.group(2))

    box_rect_matches = re.findall(
        r'<rect x="([0-9.\-]+)" y="([0-9.\-]+)" width="([0-9.\-]+)" height="([0-9.\-]+)" fill="#[0-9A-Fa-f]{6}" stroke="#[0-9A-Fa-f]{3,6}" stroke-width="1\.5" rx="2"/>',
        svg,
    )
    if not box_rect_matches:
        raise AssertionError("no class box rectangles found in SVG")

    min_box_y = min(float(match[1]) for match in box_rect_matches)
    if min_box_y <= title_y + 24:
        raise AssertionError(
            f"diagram body starts too close to title: title_y={title_y}, min_box_y={min_box_y}"
        )


def _assert_endpoint_directions() -> None:
    planner = ConnectorPlanner()

    # Complex orthogonal paths that end in each possible target approach direction.
    cases = {
        "top": [
            (40.0, 40.0),
            (120.0, 40.0),
            (120.0, 10.0),
            (170.0, 10.0),
            (170.0, 40.0),
            (200.0, 40.0),
            (200.0, 80.0),
        ],
        "bottom": [
            (40.0, 140.0),
            (120.0, 140.0),
            (120.0, 180.0),
            (170.0, 180.0),
            (170.0, 140.0),
            (200.0, 140.0),
            (200.0, 80.0),
        ],
        "left": [
            (40.0, 120.0),
            (40.0, 70.0),
            (120.0, 70.0),
            (120.0, 40.0),
            (160.0, 40.0),
            (160.0, 80.0),
            (200.0, 80.0),
        ],
        "right": [
            (260.0, 120.0),
            (260.0, 70.0),
            (300.0, 70.0),
            (300.0, 120.0),
            (240.0, 120.0),
            (240.0, 80.0),
            (200.0, 80.0),
        ],
    }

    opposite = {"top": "bottom", "bottom": "top", "left": "right", "right": "left"}

    for target_edge, points in cases.items():
        connector = ConnectorPath(source_name="A", target_name="B", arrow_type="-->")
        connector.source_x, connector.source_y = points[0]
        connector.target_x, connector.target_y = points[-1]
        connector.source_edge = _source_edge_from_first_segment(points)
        connector.target_edge = target_edge

        if not planner._path_respects_connector_edges(connector, points):
            raise AssertionError(f"expected path to respect target edge {target_edge}, but it did not")

        connector.target_edge = opposite[target_edge]
        if planner._path_respects_connector_edges(connector, points):
            raise AssertionError(
                f"expected path to reject opposite target edge {opposite[target_edge]}, but it was accepted"
            )

    # Explicitly lock the reported user pattern: up-left-down and left-up-left-down.
    user_pattern_paths = [
        [
            (200.0, 200.0),
            (200.0, 140.0),
            (140.0, 140.0),
            (140.0, 180.0),
            (160.0, 180.0),
            (160.0, 220.0),
        ],
        [
            (260.0, 200.0),
            (200.0, 200.0),
            (200.0, 140.0),
            (140.0, 140.0),
            (140.0, 180.0),
            (160.0, 180.0),
            (160.0, 220.0),
        ],
    ]

    for path in user_pattern_paths:
        if _final_path_direction(path) != "down":
            raise AssertionError(f"unexpected final direction for user-pattern path: {_final_path_direction(path)}")

        connector = ConnectorPath(source_name="A", target_name="B", arrow_type="-->")
        connector.source_x, connector.source_y = path[0]
        connector.target_x, connector.target_y = path[-1]
        connector.source_edge = _source_edge_from_first_segment(path)
        connector.target_edge = "top"
        if not planner._path_respects_connector_edges(connector, path):
            raise AssertionError("user-pattern down-approach path should enter target from top edge")


def run_test() -> int:
    _assert_title_above_diagram_body()
    _assert_endpoint_directions()
    print("OK: title band and endpoint direction regressions pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_test())