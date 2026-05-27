#!/usr/bin/env python3
"""Regression checks for class-diagram title placement and endpoint directions."""

import os
import re
import sys
import xml.etree.ElementTree as ET

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
    csv_path = os.path.join(REPO_ROOT, "Process", "02_Architecture", "10_Diagrams", "parser_to_model.csv")
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


def _path_points(connector):
    points = [(connector.source_x, connector.source_y)]
    points.extend(list(connector.segments))
    if points[-1] != (connector.target_x, connector.target_y):
        points.append((connector.target_x, connector.target_y))
    return points


def _segment_overlap_span(seg_a, seg_b):
    (a1, a2), (b1, b2) = seg_a, seg_b
    if abs(a1[1] - a2[1]) <= 1e-6 and abs(b1[1] - b2[1]) <= 1e-6:
        if abs(a1[1] - b1[1]) > 1e-6:
            return 0.0
        a_min, a_max = sorted([a1[0], a2[0]])
        b_min, b_max = sorted([b1[0], b2[0]])
        return max(0.0, min(a_max, b_max) - max(a_min, b_min))
    if abs(a1[0] - a2[0]) <= 1e-6 and abs(b1[0] - b2[0]) <= 1e-6:
        if abs(a1[0] - b1[0]) > 1e-6:
            return 0.0
        a_min, a_max = sorted([a1[1], a2[1]])
        b_min, b_max = sorted([b1[1], b2[1]])
        return max(0.0, min(a_max, b_max) - max(a_min, b_min))
    return 0.0


def _assert_parser_to_model_fanout_guardrails() -> None:
    csv_path = os.path.join(REPO_ROOT, "Process", "02_Architecture", "10_Diagrams", "parser_to_model.csv")
    model = parse_csv(csv_path)
    diagram = model.get_class_diagram("ParserToModel")
    if diagram is None:
        raise AssertionError("ParserToModel class diagram not found")

    planner = ConnectorPlanner(routing_mode="orthogonal")
    from class_diagram_renderer import _layout_classes_uml_standard
    boxes = _layout_classes_uml_standard(diagram, model, "High", routing="orthogonal")
    for name, box in boxes.items():
        planner.add_rectangle(name, box['x'], box['y'], box['width'], box['height'])
    for rel in diagram.relationships:
        planner.add_connector(rel.source, rel.target, rel.arrow, rel.src_mult, rel.tgt_mult, rel.label, rel.layer)
    planner.plan_connectors()

    conns = {(c.source_name, c.target_name): c for c in planner.connectors}
    c_model = conns.get(("CsvParser", "Model"))
    c_classdef = conns.get(("CsvParser", "ClassDef"))
    c_cddiag = conns.get(("CsvParser", "ClassDiagramDef"))

    if not c_model or not c_classdef or not c_cddiag:
        raise AssertionError("missing expected CsvParser connectors for ParserToModel")

    if not (c_model.source_x < c_classdef.source_x):
        raise AssertionError(
            f"expected CsvParser->Model source slot to be left of CsvParser->ClassDef; "
            f"got model_x={c_model.source_x}, classdef_x={c_classdef.source_x}"
        )

    first_len = abs(c_cddiag.segments[0][1] - c_cddiag.source_y) if c_cddiag.segments else 0.0
    if first_len < 40.0:
        raise AssertionError(
            f"CsvParser->ClassDiagramDef first vertical segment too short for text clearance: {first_len}"
        )

    csv_parser_conns = [c for c in planner.connectors if c.source_name == "CsvParser"]
    center_x = sum(c.source_x for c in csv_parser_conns) / len(csv_parser_conns)
    left_first = []
    right_first = []
    for c in csv_parser_conns:
        if not c.segments:
            continue
        seg0 = c.segments[0]
        first = abs(seg0[1] - c.source_y)
        if c.source_x < center_x:
            left_first.append(first)
        else:
            right_first.append(first)
    if len(left_first) == len(right_first) and left_first:
        for l, r in zip(sorted(left_first), sorted(right_first)):
            if abs(l - r) > 2.0:
                raise AssertionError(
                    f"CsvParser fanout first-segment asymmetry: left={sorted(left_first)}, right={sorted(right_first)}"
                )

    segments = {}
    for c in csv_parser_conns:
        pts = _path_points(c)
        segs = []
        for idx in range(len(pts) - 1):
            if abs(pts[idx][0] - pts[idx + 1][0]) <= 1e-6 and abs(pts[idx][1] - pts[idx + 1][1]) <= 1e-6:
                continue
            segs.append((pts[idx], pts[idx + 1]))
        segments[(c.source_name, c.target_name)] = segs

    keys = list(segments.keys())
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            a_key = keys[i]
            b_key = keys[j]
            for seg_a in segments[a_key]:
                for seg_b in segments[b_key]:
                    overlap = _segment_overlap_span(seg_a, seg_b)
                    if overlap > 1.0:
                        raise AssertionError(
                            f"CsvParser connector overlap detected: {a_key} vs {b_key}, overlap={overlap}"
                        )

    svg = render_class_diagram_svg(model, diagram, verbosity_level="High")
    root = ET.fromstring(svg)
    ns = {'svg': 'http://www.w3.org/2000/svg'}
    label_y = None
    mult_y = None
    for group in root.findall('.//svg:g[@class="cls-connector"]', ns):
        if group.get('data-source') != 'CsvParser' or group.get('data-target') != 'ClassDiagramDef':
            continue
        for text_elem in group.findall('svg:text', ns):
            txt = (text_elem.text or '').strip().lower()
            if text_elem.get('font-style') == 'italic' and txt == 'parses':
                label_y = float(text_elem.get('y'))
            if txt == '1':
                y = float(text_elem.get('y'))
                if mult_y is None or abs(y - c_cddiag.source_y) < abs(mult_y - c_cddiag.source_y):
                    mult_y = y
    if label_y is None or mult_y is None:
        raise AssertionError("failed to find CsvParser->ClassDiagramDef label/multiplicity text")
    if abs(label_y - mult_y) < 10.0:
        raise AssertionError(
            f"CsvParser->ClassDiagramDef label/multiplicity overlap risk: label_y={label_y}, mult_y={mult_y}"
        )


def run_test() -> int:
    _assert_title_above_diagram_body()
    _assert_endpoint_directions()
    _assert_parser_to_model_fanout_guardrails()
    print("OK: title band and endpoint direction regressions pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_test())