#!/usr/bin/env python3
"""Regression matrix for class-diagram fanout routing.

This suite captures all currently-agreed fanout options:
- top fanout
- bottom fanout
- left fanout
- right fanout
- direct connectors stay perpendicular to the source side
- near/far ordering is based on total connector path length

The assertions intentionally encode the requirement language rather than the
current implementation behavior. If routing is incomplete, these tests should
fail with concrete geometry messages.
"""

import math
import os
import sys
import re
import xml.etree.ElementTree as ET

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(REPO_ROOT, "Scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from class_diagram_connectors import ConnectorPlanner
from parser import parse_csv
from class_diagram_renderer import _layout_classes_uml_standard, render_class_diagram_svg

MIN_LANE_STEP = 26.0
CONNECTOR_CHAR_WIDTH = 7.5


def _path_points(connector):
    points = [(connector.source_x, connector.source_y)]
    points.extend(list(connector.segments))
    if points[-1] != (connector.target_x, connector.target_y):
        points.append((connector.target_x, connector.target_y))
    return points


def _nonzero_axes(connector, tol=1e-6):
    axes = []
    pts = _path_points(connector)
    for idx in range(len(pts) - 1):
        x1, y1 = pts[idx]
        x2, y2 = pts[idx + 1]
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        if dx <= tol and dy <= tol:
            continue
        if dx <= tol:
            axes.append("V")
        elif dy <= tol:
            axes.append("H")
        else:
            axes.append("D")
    return axes


def _first_axis(connector):
    axes = _nonzero_axes(connector)
    return axes[0] if axes else None


def _first_bend_coordinate(connector):
    pts = _path_points(connector)
    if len(pts) < 3:
        return None
    axes = _nonzero_axes(connector)
    if not axes:
        return None

    first_axis = axes[0]
    prev = pts[0]
    for pt in pts[1:]:
        dx = abs(pt[0] - prev[0])
        dy = abs(pt[1] - prev[1])
        if dx <= 1e-6 and dy <= 1e-6:
            continue
        axis = "V" if dx <= 1e-6 else "H" if dy <= 1e-6 else "D"
        if axis != first_axis:
            return prev[1] if first_axis == "V" else prev[0]
        prev = pt
    return prev[1] if first_axis == "V" else prev[0]


def _total_path_length(connector):
    pts = _path_points(connector)
    total = 0.0
    for idx in range(len(pts) - 1):
        x1, y1 = pts[idx]
        x2, y2 = pts[idx + 1]
        total += math.hypot(x2 - x1, y2 - y1)
    return total


def _get_connector_map(planner):
    return {(c.source_name, c.target_name): c for c in planner.connectors}


def _assert(condition, message):
    if not condition:
        raise AssertionError(message)


def _assert_source_edge(connectors, expected_edge, context):
    for target_name, connector in connectors.items():
        _assert(
            connector.source_edge == expected_edge,
            f"FAIL [{context}] {target_name}: expected source_edge={expected_edge}, got {connector.source_edge}",
        )


def _assert_first_axis_all(connectors, expected_axis, context):
    for target_name, connector in connectors.items():
        actual = _first_axis(connector)
        _assert(
            actual == expected_axis,
            f"FAIL [{context}] {target_name}: expected first axis {expected_axis}, got {actual}; path={_path_points(connector)}",
        )


def _assert_distinct_starts(connectors, coord_name, context):
    if coord_name == "x":
        values = [connector.source_x for connector in connectors.values()]
    else:
        values = [connector.source_y for connector in connectors.values()]
    _assert(
        len(set(round(v, 3) for v in values)) == len(values),
        f"FAIL [{context}] source {coord_name}-starts are not distinct: {values}",
    )


def _assert_lane_spacing(connectors, context):
    bends = []
    for target_name, connector in connectors.items():
        bend = _first_bend_coordinate(connector)
        _assert(bend is not None, f"FAIL [{context}] {target_name}: no bend coordinate found")
        bends.append((target_name, bend))

    bends_sorted = sorted(bends, key=lambda item: item[1])
    for idx in range(len(bends_sorted) - 1):
        gap = bends_sorted[idx + 1][1] - bends_sorted[idx][1]
        _assert(
            gap >= MIN_LANE_STEP,
            f"FAIL [{context}] lane gap too small ({gap:.1f}px < {MIN_LANE_STEP}px): {bends_sorted}",
        )


def _assert_direct_is_straight(connector, expected_axis, context, target_name):
    axes = [axis for axis in _nonzero_axes(connector) if axis != "Z"]
    _assert(
        axes and all(axis == expected_axis for axis in axes),
        f"FAIL [{context}] {target_name}: direct connector must remain straight/perpendicular; axes={axes} path={_path_points(connector)}",
    )


def _assert_direct_slots_are_centered(connectors, center_value, coord_name, direct_names, context):
    if coord_name == "x":
        values = {name: connector.source_x for name, connector in connectors.items()}
    else:
        values = {name: connector.source_y for name, connector in connectors.items()}

    ranked = sorted(values.items(), key=lambda item: (abs(item[1] - center_value), item[1]))
    expected = set(direct_names)
    actual = {name for name, _value in ranked[:len(direct_names)]}
    _assert(
        actual == expected,
        f"FAIL [{context}] direct connectors must occupy the center slots; ranked={ranked}, expected={sorted(expected)}",
    )


def _assert_total_length_order(connectors, ordered_targets, descending, context):
    lengths = [(_total_path_length(connectors[name]), name) for name in ordered_targets]
    values = [item[0] for item in lengths]
    expected = sorted(values, reverse=descending)
    _assert(
        all(abs(a - b) < 1e-6 for a, b in zip(values, expected)),
        f"FAIL [{context}] total path lengths are not {'descending' if descending else 'ascending'} for {ordered_targets}: {lengths}",
    )


def _build_top_fanout_planner():
    planner = ConnectorPlanner(routing_mode="orthogonal")
    planner.add_rectangle("Hub", 320, 520, 240, 40)
    targets = {
        "L_far": (20, -140, 120, 40),
        "L_mid": (120, -100, 120, 40),
        "L_near": (220, -60, 120, 40),
        "L_dir": (360, -20, 120, 40),
        "R_dir": (400, -20, 120, 40),
        "R_near": (540, -60, 120, 40),
        "R_mid": (640, -100, 120, 40),
        "R_far": (740, -140, 120, 40),
    }
    for name, rect in targets.items():
        planner.add_rectangle(name, *rect)
        planner.add_connector("Hub", name, "-->", tgt_mult="1..*", label=name)
    planner.plan_connectors()
    return planner


def _build_top_even_fanout_planner():
    planner = ConnectorPlanner(routing_mode="orthogonal")
    planner.add_rectangle("Hub", 320, 520, 240, 40)
    targets = {
        "L_far": (20, -140, 120, 40),
        "L_mid": (120, -100, 120, 40),
        "L_near": (220, -60, 120, 40),
        "R_near": (540, -60, 120, 40),
        "R_mid": (640, -100, 120, 40),
        "R_far": (740, -140, 120, 40),
    }
    for name, rect in targets.items():
        planner.add_rectangle(name, *rect)
        planner.add_connector("Hub", name, "-->", tgt_mult="1..*", label=name)
    planner.plan_connectors()
    return planner


def _build_top_side_entry_mode_planner():
    class _NoForcedEntryPlanner(ConnectorPlanner):
        def _detect_one_sided_group_edges(self):
            return {}, {}

    planner = _NoForcedEntryPlanner(routing_mode="orthogonal")
    planner.add_rectangle("Hub", 320, 520, 240, 40)
    targets = {
        "L_far": (-20, -120, 120, 40),
        "L_mid": (120, -120, 120, 40),
        "L_near": (240, -120, 120, 40),
        "T_dir": (360, -120, 120, 40),
        "R_near": (520, -120, 120, 40),
        "R_mid": (640, -120, 120, 40),
        "R_far": (780, -120, 120, 40),
    }
    labels = {
        "L_far": "L_far",
        "L_mid": "L_mid",
        "L_near": "L_near",
        "T_dir": "T_dir",
        "R_near": "R_near",
        "R_mid": "R_mid",
        "R_far": "R_far",
    }
    for name, rect in targets.items():
        planner.add_rectangle(name, *rect)
        planner.add_connector("Hub", name, "-->", tgt_mult="1..*", label=labels[name])
    planner.plan_connectors()
    return planner


def _build_top_left_heavy_fanout_planner():
    planner = ConnectorPlanner(routing_mode="orthogonal")
    planner.add_rectangle("Hub", 320, 520, 240, 40)
    targets = {
        "L_far": (20, -160, 120, 40),
        "L_mid": (120, -120, 120, 40),
        "L_near": (220, -80, 120, 40),
        "L_dir": (360, -20, 120, 40),
    }
    for name, rect in targets.items():
        planner.add_rectangle(name, *rect)
        planner.add_connector("Hub", name, "-->", tgt_mult="1..*", label=name)
    planner.plan_connectors()
    return planner


def _build_bottom_fanout_planner():
    planner = ConnectorPlanner(routing_mode="orthogonal")
    planner.add_rectangle("Hub", 320, 40, 240, 40)
    targets = {
        "L_far": (20, 700, 120, 40),
        "L_mid": (120, 660, 120, 40),
        "L_near": (220, 620, 120, 40),
        "L_dir": (360, 580, 120, 40),
        "R_dir": (400, 580, 120, 40),
        "R_near": (540, 620, 120, 40),
        "R_mid": (640, 660, 120, 40),
        "R_far": (740, 700, 120, 40),
    }
    for name, rect in targets.items():
        planner.add_rectangle(name, *rect)
        planner.add_connector("Hub", name, "-->", tgt_mult="1..*", label=name)
    planner.plan_connectors()
    return planner


def _build_left_fanout_planner():
    planner = ConnectorPlanner(routing_mode="orthogonal")
    planner.add_rectangle("Hub", 560, 200, 40, 240)
    targets = {
        "T_near": (300, 150, 120, 40),
        "T_mid": (220, 90, 120, 40),
        "T_far": (100, 30, 120, 40),
        "T_dir": (360, 280, 120, 40),
        "B_dir": (360, 300, 120, 40),
        "B_far": (100, 570, 120, 40),
        "B_mid": (220, 510, 120, 40),
        "B_near": (300, 450, 120, 40),
    }
    for name, rect in targets.items():
        planner.add_rectangle(name, *rect)
        planner.add_connector("Hub", name, "-->", tgt_mult="1..*", label=name)
    planner.plan_connectors()
    return planner


def _build_right_fanout_planner():
    planner = ConnectorPlanner(routing_mode="orthogonal")
    planner.add_rectangle("Hub", 200, 200, 40, 240)
    targets = {
        "T_near": (380, 150, 120, 40),
        "T_mid": (460, 90, 120, 40),
        "T_far": (560, 30, 120, 40),
        "T_dir": (320, 280, 120, 40),
        "B_dir": (320, 300, 120, 40),
        "B_far": (560, 570, 120, 40),
        "B_mid": (460, 510, 120, 40),
        "B_near": (380, 450, 120, 40),
    }
    for name, rect in targets.items():
        planner.add_rectangle(name, *rect)
        planner.add_connector("Hub", name, "-->", tgt_mult="1..*", label=name)
    planner.plan_connectors()
    return planner


def _load_csv_fanout_layout(diagram_id):
    model = parse_csv(os.path.join(REPO_ROOT, "Test", "tests", "fanout.csv"))
    diagram = next(d for d in model.class_diagrams if d.diagram_id == diagram_id)
    boxes = _layout_classes_uml_standard(diagram, model, "High", routing="orthogonal")
    return boxes


def _build_csv_fanout_planner(diagram_id):
    model = parse_csv(os.path.join(REPO_ROOT, "Test", "tests", "fanout.csv"))
    diagram = next(d for d in model.class_diagrams if d.diagram_id == diagram_id)
    boxes = _layout_classes_uml_standard(diagram, model, "High", routing="orthogonal")
    planner = ConnectorPlanner(routing_mode="orthogonal")
    for name, box in boxes.items():
        planner.add_rectangle(name, box['x'], box['y'], box['width'], box['height'])
    for rel in diagram.relationships:
        planner.add_connector(rel.source, rel.target, rel.arrow, rel.src_mult, rel.tgt_mult, rel.label, rel.layer)
    planner.plan_connectors()
    return planner


def _assert_all_targets_on_side(boxes, hub_name, target_names, side, context):
    hub = boxes[hub_name]
    hub_left = hub['x']
    hub_right = hub['x'] + hub['width']
    hub_top = hub['y']
    hub_bottom = hub['y'] + hub['height']

    for target_name in target_names:
        target = boxes[target_name]
        target_left = target['x']
        target_right = target['x'] + target['width']
        target_top = target['y']
        target_bottom = target['y'] + target['height']

        if side == 'top':
            _assert(
                target_bottom <= hub_top,
                f"FAIL [{context}] {target_name} must be above {hub_name}; target_bottom={target_bottom}, hub_top={hub_top}",
            )
        elif side == 'bottom':
            _assert(
                target_top >= hub_bottom,
                f"FAIL [{context}] {target_name} must be below {hub_name}; target_top={target_top}, hub_bottom={hub_bottom}",
            )
        elif side == 'left':
            _assert(
                target_right <= hub_left,
                f"FAIL [{context}] {target_name} must be left of {hub_name}; target_right={target_right}, hub_left={hub_left}",
            )
        elif side == 'right':
            _assert(
                target_left >= hub_right,
                f"FAIL [{context}] {target_name} must be right of {hub_name}; target_left={target_left}, hub_right={hub_right}",
            )


def _validate_csv_top_bottom_layout(diagram_id, hub_name, target_names, expected_side, context):
    boxes = _load_csv_fanout_layout(diagram_id)
    _assert_all_targets_on_side(boxes, hub_name, target_names, expected_side, context)


def _validate_csv_target_gaps(diagram_id, ordered_target_names, min_gap, context):
    boxes = _load_csv_fanout_layout(diagram_id)
    gaps = []
    for left_name, right_name in zip(ordered_target_names, ordered_target_names[1:]):
        left_box = boxes[left_name]
        right_box = boxes[right_name]
        gap = right_box['x'] - (left_box['x'] + left_box['width'])
        gaps.append((left_name, right_name, gap))
        _assert(
            gap >= min_gap,
            f"FAIL [{context}] gap too small between {left_name} and {right_name}: {gap}px < {min_gap}px",
        )

    baseline = gaps[0][2] if gaps else 0
    for left_name, right_name, gap in gaps[1:]:
        _assert(
            abs(gap - baseline) <= 1.0,
            f"FAIL [{context}] inconsistent gap between {left_name} and {right_name}: {gap}px vs baseline {baseline}px",
        )


def _validate_csv_source_edge(diagram_id, expected_edge, context):
    planner = _build_csv_fanout_planner(diagram_id)
    for connector in planner.connectors:
        _assert(
            connector.source_edge == expected_edge,
            f"FAIL [{context}] {connector.target_name}: expected source_edge={expected_edge}, got {connector.source_edge}",
        )


def _validate_csv_target_edge(diagram_id, expected_edge, context):
    planner = _build_csv_fanout_planner(diagram_id)
    for connector in planner.connectors:
        _assert(
            connector.target_edge == expected_edge,
            f"FAIL [{context}] {connector.target_name}: expected target_edge={expected_edge}, got {connector.target_edge}",
        )


def _validate_csv_top_slot_order(context):
    planner = _build_csv_fanout_planner("FanoutTop")
    connector_map = _get_connector_map(planner)
    top = {name: connector_map[("HubTop", name)] for name in [
        "Top_L_far", "Top_L_mid", "Top_L_near", "Top_dir",
        "Top_R_near", "Top_R_mid", "Top_R_far",
    ]}

    _assert(
        top["Top_L_far"].source_x < top["Top_L_mid"].source_x < top["Top_L_near"].source_x < top["Top_dir"].source_x,
        (
            f"FAIL [{context}] left-to-right slot order must be L_far, L_mid, L_near, T_dir; "
            f"got far={top['Top_L_far'].source_x}, mid={top['Top_L_mid'].source_x}, "
            f"near={top['Top_L_near'].source_x}, dir={top['Top_dir'].source_x}"
        ),
    )
    _assert(
        top["Top_R_near"].source_x < top["Top_R_mid"].source_x < top["Top_R_far"].source_x,
        (
            f"FAIL [{context}] right-side slot order must be center-outward R_near, R_mid, R_far; "
            f"got near={top['Top_R_near'].source_x}, mid={top['Top_R_mid'].source_x}, far={top['Top_R_far'].source_x}"
        ),
    )


def _is_direct_connector(connector):
    label = (connector.label or "").strip().lower()
    target = (connector.target_name or "").strip().lower()
    return label == "dir" or label.endswith("_dir") or target.endswith("_dir")


def _validate_csv_single_direct_connection(diagram_id, context):
    planner = _build_csv_fanout_planner(diagram_id)
    direct = [
        connector for connector in planner.connectors
        if _is_direct_connector(connector)
    ]
    _assert(
        len(direct) == 1,
        f"FAIL [{context}] expected exactly one direct connector, got {len(direct)}",
    )


def _validate_csv_top_slot_spacing_from_multiplicity(context):
    planner = _build_csv_fanout_planner("FanoutTop")
    top_connectors = [
        connector for connector in planner.connectors
        if connector.source_name == "HubTop" and connector.source_edge == "top"
    ]
    _assert(top_connectors, f"FAIL [{context}] no top-exit connectors found")

    max_chars = max(
        max(len(connector.src_mult or ""), len(connector.tgt_mult or ""))
        for connector in top_connectors
    )
    required_gap = max(40.0, max_chars * CONNECTOR_CHAR_WIDTH + 10.0)

    xs = sorted(connector.source_x for connector in top_connectors)
    for left, right in zip(xs, xs[1:]):
        gap = right - left
        _assert(
            gap >= required_gap,
            (
                f"FAIL [{context}] source slot gap {gap:.1f}px is smaller than required {required_gap:.1f}px "
                f"for multiplicity readability"
            ),
        )


def _validate_csv_top_first_segment_depth_order(context):
    planner = _build_csv_fanout_planner("FanoutTop")
    connector_map = _get_connector_map(planner)

    def _depth(name):
        connector = connector_map[("HubTop", name)]
        pts = _path_points(connector)
        _assert(len(pts) >= 2, f"FAIL [{context}] {name}: missing path points")
        source_y = pts[0][1]
        bend_y = pts[1][1]
        return source_y - bend_y

    left_far = _depth("Top_L_far")
    left_mid = _depth("Top_L_mid")
    left_near = _depth("Top_L_near")
    right_far = _depth("Top_R_far")
    right_mid = _depth("Top_R_mid")
    right_near = _depth("Top_R_near")

    _assert(
        left_near > left_mid > left_far,
        (
            f"FAIL [{context}] left first-segment depth must be near > mid > far; "
            f"got near={left_near}, mid={left_mid}, far={left_far}"
        ),
    )
    _assert(
        right_near > right_mid > right_far,
        (
            f"FAIL [{context}] right first-segment depth must be near > mid > far; "
            f"got near={right_near}, mid={right_mid}, far={right_far}"
        ),
    )


def _validate_csv_bottom_first_segment_depth_order(context):
    planner = _build_csv_fanout_planner("FanoutBottom")
    connector_map = _get_connector_map(planner)

    def _depth(name):
        connector = connector_map[("HubBottom", name)]
        pts = _path_points(connector)
        _assert(len(pts) >= 2, f"FAIL [{context}] {name}: missing path points")
        source_y = pts[0][1]
        bend_y = pts[1][1]
        return bend_y - source_y

    left_far = _depth("Bottom_L_far")
    left_mid = _depth("Bottom_L_mid")
    left_near = _depth("Bottom_L_near")
    right_far = _depth("Bottom_R_far")
    right_mid = _depth("Bottom_R_mid")
    right_near = _depth("Bottom_R_near")

    _assert(
        left_near > left_mid > left_far,
        (
            f"FAIL [{context}] left first-segment depth must be near > mid > far; "
            f"got near={left_near}, mid={left_mid}, far={left_far}"
        ),
    )
    _assert(
        right_near > right_mid > right_far,
        (
            f"FAIL [{context}] right first-segment depth must be near > mid > far; "
            f"got near={right_near}, mid={right_mid}, far={right_far}"
        ),
    )


def _validate_csv_top_no_fanout_crossings(context):
    planner = _build_csv_fanout_planner("FanoutTop")
    fanout = [
        connector for connector in planner.connectors
        if connector.source_name == "HubTop" and connector.source_edge == "top"
    ]

    def _segments(connector):
        pts = _path_points(connector)
        return list(zip(pts, pts[1:]))

    def _is_between(v, a, b):
        low, high = (a, b) if a <= b else (b, a)
        return low <= v <= high

    def _intersects(seg_a, seg_b):
        (ax1, ay1), (ax2, ay2) = seg_a
        (bx1, by1), (bx2, by2) = seg_b

        a_vertical = abs(ax1 - ax2) <= 1e-6
        b_vertical = abs(bx1 - bx2) <= 1e-6

        if a_vertical == b_vertical:
            return False

        if a_vertical:
            ix, iy = ax1, by1
            return _is_between(ix, bx1, bx2) and _is_between(iy, ay1, ay2)
        ix, iy = bx1, ay1
        return _is_between(ix, ax1, ax2) and _is_between(iy, by1, by2)

    for idx, a in enumerate(fanout):
        for b in fanout[idx + 1:]:
            for seg_a in _segments(a):
                for seg_b in _segments(b):
                    if _intersects(seg_a, seg_b):
                        _assert(
                            False,
                            (
                                f"FAIL [{context}] fanout connectors cross: {a.target_name} path={_path_points(a)} "
                                f"vs {b.target_name} path={_path_points(b)}"
                            ),
                        )


def _validate_csv_top_render_text_positions(context):
    model = parse_csv(os.path.join(REPO_ROOT, "Test", "tests", "fanout.csv"))
    diagram = next(d for d in model.class_diagrams if d.diagram_id == "FanoutTop")
    svg = render_class_diagram_svg(model, diagram, verbosity_level="High")
    root = ET.fromstring(svg)
    ns = {'svg': 'http://www.w3.org/2000/svg'}

    planner = _build_csv_fanout_planner("FanoutTop")
    by_target = {c.target_name: c for c in planner.connectors}

    for group in root.findall('.//svg:g[@class="cls-connector"]', ns):
        target_name = group.get('data-target')
        if target_name not in by_target:
            continue
        connector = by_target[target_name]
        if connector.source_edge != 'top':
            continue

        path = group.find('svg:path', ns)
        _assert(path is not None, f"FAIL [{context}] {target_name}: missing connector path")
        d_attr = path.get('d', '')
        numbers = [float(v) for v in re.findall(r'-?\d+(?:\.\d+)?', d_attr)]
        pts = list(zip(numbers[0::2], numbers[1::2]))
        _assert(len(pts) >= 3, f"FAIL [{context}] {target_name}: expected multi-point path, got {pts}")

        source_x, source_y = pts[0]
        bend_x, bend_y = pts[1]

        label_text = None
        mult_text = None
        for text_elem in group.findall('svg:text', ns):
            if text_elem.get('font-style') == 'italic':
                label_text = text_elem
            else:
                mult_text = text_elem

        _assert(label_text is not None, f"FAIL [{context}] {target_name}: missing label text")
        _assert(mult_text is not None, f"FAIL [{context}] {target_name}: missing multiplicity text")

        label_x = float(label_text.get('x'))
        label_y = float(label_text.get('y'))
        mult_x = float(mult_text.get('x'))
        mult_y = float(mult_text.get('y'))

        y_low = min(source_y, bend_y)
        y_high = max(source_y, bend_y)
        second_dx = 0.0
        if len(pts) >= 3:
            second_dx = pts[2][0] - pts[1][0]
        is_direct_vertical = abs(source_x - bend_x) <= 1e-6 and abs(second_dx) <= 1e-6
        if is_direct_vertical:
            y_low = min(source_y, pts[-1][1])
            y_high = max(source_y, pts[-1][1])
        _assert(
            y_low <= label_y <= y_high,
            f"FAIL [{context}] {target_name}: label must be on first vertical segment before bend; label_y={label_y}, source_y={source_y}, bend_y={bend_y}",
        )
        _assert(
            y_low <= mult_y <= y_high,
            f"FAIL [{context}] {target_name}: multiplicity must be on first vertical segment before bend; mult_y={mult_y}, source_y={source_y}, bend_y={bend_y}",
        )
        _assert(
            abs(label_x - source_x) <= 60,
            f"FAIL [{context}] {target_name}: label must stay attached to the first segment; label_x={label_x}, source_x={source_x}",
        )
        _assert(
            abs(mult_x - source_x) <= 60,
            f"FAIL [{context}] {target_name}: multiplicity must stay attached to the first segment; mult_x={mult_x}, source_x={source_x}",
        )
        _assert(
            mult_x > source_x,
            f"FAIL [{context}] {target_name}: multiplicity must be to the right of the connector; mult_x={mult_x}, source_x={source_x}",
        )
        if is_direct_vertical:
            _assert(
                label_y < mult_y,
                f"FAIL [{context}] {target_name}: direct-label must sit farther up the straight segment than multiplicity; label_y={label_y}, mult_y={mult_y}",
            )
        else:
            _assert(
                abs(label_y - bend_y) < abs(mult_y - bend_y),
                f"FAIL [{context}] {target_name}: label must be closer to bend than multiplicity; label_y={label_y}, mult_y={mult_y}, bend_y={bend_y}",
            )
            if second_dx > 0:
                _assert(
                    label_y >= bend_y + 10.0,
                    (
                        f"FAIL [{context}] {target_name}: right-end bend label must be below the bend line; "
                        f"label_y={label_y}, bend_y={bend_y}"
                    ),
                )
            if second_dx < 0:
                _assert(
                    label_y >= bend_y + 10.0,
                    (
                        f"FAIL [{context}] {target_name}: left-end bend label must be below the bend line; "
                        f"label_y={label_y}, bend_y={bend_y}"
                    ),
                )


def _validate_even_fanout_has_no_direct(planner, context):
    connector_map = _get_connector_map(planner)
    targets = ["L_far", "L_mid", "L_near", "R_near", "R_mid", "R_far"]
    connectors = [connector_map[("Hub", name)] for name in targets]
    straight = []
    for connector in connectors:
        axes = [axis for axis in _nonzero_axes(connector) if axis != "Z"]
        if axes and all(axis == "V" for axis in axes):
            straight.append(connector.target_name)
    _assert(
        not straight,
        f"FAIL [{context}] even fanout must not have direct vertical connectors; got {straight}",
    )


def _validate_top_side_entry_mode_order(planner, context):
    connector_map = _get_connector_map(planner)
    connectors = {
        name: connector_map[("Hub", name)]
        for name in ["L_far", "L_mid", "L_near", "T_dir", "R_near", "R_mid", "R_far"]
    }
    # Side-entry mode order from center outward:
    # left: near -> mid -> far
    # right: far -> mid -> near
    _assert(
        connectors["T_dir"].source_x > connectors["L_near"].source_x > connectors["L_mid"].source_x > connectors["L_far"].source_x,
        (
            f"FAIL [{context}] left side order must be T_dir, L_near, L_mid, L_far in side-entry mode; "
            f"got dir={connectors['T_dir'].source_x}, near={connectors['L_near'].source_x}, "
            f"mid={connectors['L_mid'].source_x}, far={connectors['L_far'].source_x}"
        ),
    )
    _assert(
        connectors["T_dir"].source_x < connectors["R_far"].source_x < connectors["R_mid"].source_x < connectors["R_near"].source_x,
        (
            f"FAIL [{context}] right side order must be T_dir, R_far, R_mid, R_near in side-entry mode; "
            f"got dir={connectors['T_dir'].source_x}, far={connectors['R_far'].source_x}, "
            f"mid={connectors['R_mid'].source_x}, near={connectors['R_near'].source_x}"
        ),
    )


def _validate_csv_top_odd_direct_centered(context):
    planner = _build_csv_fanout_planner("FanoutTop")
    direct = [connector for connector in planner.connectors if _is_direct_connector(connector)]
    _assert(
        len(direct) == 1,
        f"FAIL [{context}] odd fanout must have exactly one direct connector; got {len(direct)}",
    )
    hub_center = planner.grids["HubTop"].get_center()[0]
    direct_conn = direct[0]
    _assert(
        abs(direct_conn.source_x - hub_center) <= 1e-6,
        (
            f"FAIL [{context}] direct connector must use centered source slot; "
            f"source_x={direct_conn.source_x}, hub_center={hub_center}"
        ),
    )


def _validate_csv_bottom_odd_direct_centered(context):
    planner = _build_csv_fanout_planner("FanoutBottom")
    direct = [connector for connector in planner.connectors if _is_direct_connector(connector)]
    _assert(
        len(direct) == 1,
        f"FAIL [{context}] odd fanout must have exactly one direct connector; got {len(direct)}",
    )
    hub_center = planner.grids["HubBottom"].get_center()[0]
    direct_conn = direct[0]
    _assert(
        abs(direct_conn.source_x - hub_center) <= 1e-6,
        (
            f"FAIL [{context}] direct connector must use centered source slot; "
            f"source_x={direct_conn.source_x}, hub_center={hub_center}"
        ),
    )


def _validate_top_bottom(planner, expected_edge, context):
    connector_map = _get_connector_map(planner)
    targets = ["L_far", "L_mid", "L_near", "L_dir", "R_dir", "R_near", "R_mid", "R_far"]
    connectors = {name: connector_map[("Hub", name)] for name in targets}
    _assert_source_edge(connectors, expected_edge, context)
    _assert_first_axis_all(connectors, "V", context)
    _assert_distinct_starts(connectors, "x", context)
    left_group = {name: connectors[name] for name in ["L_far", "L_mid", "L_near"]}
    right_group = {name: connectors[name] for name in ["R_near", "R_mid", "R_far"]}
    _assert_lane_spacing(left_group, f"{context} left group")
    _assert_lane_spacing(right_group, f"{context} right group")
    _assert_total_length_order(connectors, ["L_far", "L_mid", "L_near"], True, f"{context} left order")
    _assert_total_length_order(connectors, ["R_near", "R_mid", "R_far"], False, f"{context} right order")
    center_x = planner.grids["Hub"].get_center()[0]
    _assert_direct_slots_are_centered(connectors, center_x, "x", ["L_dir", "R_dir"], context)
    _assert_direct_is_straight(connectors["L_dir"], "V", context, "L_dir")
    _assert_direct_is_straight(connectors["R_dir"], "V", context, "R_dir")


def _validate_top_left_heavy(planner, context):
    connector_map = _get_connector_map(planner)
    targets = ["L_far", "L_mid", "L_near", "L_dir"]
    connectors = {name: connector_map[("Hub", name)] for name in targets}
    _assert_source_edge(connectors, "top", context)
    _assert_first_axis_all(connectors, "V", context)
    _assert_distinct_starts(connectors, "x", context)

    # Direct route should stay closest to center among a one-sided fanout.
    center_x = planner.grids["Hub"].get_center()[0]
    _assert_direct_slots_are_centered(connectors, center_x, "x", ["L_dir"], context)
    _assert_direct_is_straight(connectors["L_dir"], "V", context, "L_dir")

    # Left near/mid/far should consume source slots from center outward.
    _assert(
        connectors["L_near"].source_x > connectors["L_mid"].source_x > connectors["L_far"].source_x,
        (
            f"FAIL [{context}] expected source slots to progress near->mid->far from center outward; "
            f"got near={connectors['L_near'].source_x}, mid={connectors['L_mid'].source_x}, far={connectors['L_far'].source_x}"
        ),
    )

    # Left near/mid/far should route with increasing bend depth near->far.
    bends = {
        name: _first_bend_coordinate(connectors[name])
        for name in ["L_near", "L_mid", "L_far"]
    }
    _assert(
        bends["L_near"] > bends["L_mid"] > bends["L_far"],
        f"FAIL [{context}] expected bend depths near->mid->far (top fanout): {bends}",
    )

    _assert_total_length_order(connectors, ["L_far", "L_mid", "L_near"], True, f"{context} left order")


def _validate_left_right(planner, expected_edge, context):
    connector_map = _get_connector_map(planner)
    targets = ["T_near", "T_mid", "T_far", "T_dir", "B_dir", "B_far", "B_mid", "B_near"]
    connectors = {name: connector_map[("Hub", name)] for name in targets}
    _assert_source_edge(connectors, expected_edge, context)
    _assert_first_axis_all(connectors, "H", context)
    _assert_distinct_starts(connectors, "y", context)
    top_group = {name: connectors[name] for name in ["T_near", "T_mid", "T_far"]}
    bottom_group = {name: connectors[name] for name in ["B_far", "B_mid", "B_near"]}
    _assert_lane_spacing(top_group, f"{context} top group")
    _assert_lane_spacing(bottom_group, f"{context} bottom group")
    _assert_total_length_order(connectors, ["T_far", "T_mid", "T_near"], True, f"{context} top order")
    _assert_total_length_order(connectors, ["B_far", "B_mid", "B_near"], True, f"{context} bottom order")
    center_y = planner.grids["Hub"].get_center()[1]
    _assert_direct_slots_are_centered(connectors, center_y, "y", ["T_dir", "B_dir"], context)
    _assert_direct_is_straight(connectors["T_dir"], "H", context, "T_dir")
    _assert_direct_is_straight(connectors["B_dir"], "H", context, "B_dir")


def run_test() -> int:
    checks = [
        (
            "top even fanout no direct",
            _build_top_even_fanout_planner,
            lambda p: _validate_even_fanout_has_no_direct(p, "top even fanout no direct"),
        ),
        ("bottom fanout", _build_bottom_fanout_planner, lambda p: _validate_top_bottom(p, "bottom", "bottom fanout")),
        ("left fanout", _build_left_fanout_planner, lambda p: _validate_left_right(p, "left", "left fanout")),
        ("right fanout", _build_right_fanout_planner, lambda p: _validate_left_right(p, "right", "right fanout")),
        (
            "csv top fanout layout",
            lambda: None,
            lambda _p: _validate_csv_top_bottom_layout(
                "FanoutTop",
                "HubTop",
                [
                    "Top_L_far", "Top_L_mid", "Top_L_near", "Top_dir",
                    "Top_R_near", "Top_R_mid", "Top_R_far",
                ],
                "top",
                "csv top fanout layout",
            ),
        ),
        (
            "csv top fanout target gaps",
            lambda: None,
            lambda _p: _validate_csv_target_gaps(
                "FanoutTop",
                [
                    "Top_L_far", "Top_L_mid", "Top_L_near", "Top_dir",
                    "Top_R_near", "Top_R_mid", "Top_R_far",
                ],
                40,
                "csv top fanout target gaps",
            ),
        ),
        (
            "csv top fanout source edges",
            lambda: None,
            lambda _p: _validate_csv_source_edge("FanoutTop", "top", "csv top fanout source edges"),
        ),
        (
            "csv top single direct",
            lambda: None,
            lambda _p: _validate_csv_single_direct_connection("FanoutTop", "csv top single direct"),
        ),
        (
            "csv top odd direct centered",
            lambda: None,
            lambda _p: _validate_csv_top_odd_direct_centered("csv top odd direct centered"),
        ),
        (
            "csv top fanout slot order",
            lambda: None,
            lambda _p: _validate_csv_top_slot_order("csv top fanout slot order"),
        ),
        (
            "csv top first-segment depth order",
            lambda: None,
            lambda _p: _validate_csv_top_first_segment_depth_order("csv top first-segment depth order"),
        ),
        (
            "csv top slot spacing",
            lambda: None,
            lambda _p: _validate_csv_top_slot_spacing_from_multiplicity("csv top slot spacing"),
        ),
        (
            "csv top fanout target edges",
            lambda: None,
            lambda _p: _validate_csv_target_edge("FanoutTop", "bottom", "csv top fanout target edges"),
        ),
        (
            "csv top fanout render text",
            lambda: None,
            lambda _p: _validate_csv_top_render_text_positions("csv top fanout render text"),
        ),
        (
            "csv top no fanout crossings",
            lambda: None,
            lambda _p: _validate_csv_top_no_fanout_crossings("csv top no fanout crossings"),
        ),
        (
            "csv bottom fanout layout",
            lambda: None,
            lambda _p: _validate_csv_top_bottom_layout(
                "FanoutBottom",
                "HubBottom",
                [
                    "Bottom_L_far", "Bottom_L_mid", "Bottom_L_near", "Bottom_dir",
                    "Bottom_R_near", "Bottom_R_mid", "Bottom_R_far",
                ],
                "bottom",
                "csv bottom fanout layout",
            ),
        ),
        (
            "csv bottom fanout source edges",
            lambda: None,
            lambda _p: _validate_csv_source_edge("FanoutBottom", "bottom", "csv bottom fanout source edges"),
        ),
        (
            "csv bottom first-segment depth order",
            lambda: None,
            lambda _p: _validate_csv_bottom_first_segment_depth_order("csv bottom first-segment depth order"),
        ),
        (
            "csv bottom odd direct centered",
            lambda: None,
            lambda _p: _validate_csv_bottom_odd_direct_centered("csv bottom odd direct centered"),
        ),
        (
            "csv bottom single direct",
            lambda: None,
            lambda _p: _validate_csv_single_direct_connection("FanoutBottom", "csv bottom single direct"),
        ),
        (
            "csv bottom fanout target edges",
            lambda: None,
            lambda _p: _validate_csv_target_edge("FanoutBottom", "top", "csv bottom fanout target edges"),
        ),
    ]

    failures = []
    for label, builder, validator in checks:
        try:
            planner = builder()
            validator(planner)
            print(f"OK: {label}")
        except AssertionError as exc:
            failures.append(str(exc))

    if failures:
        for failure in failures:
            print(failure)
        print(f"FAIL: {len(failures)} fanout case(s) failed")
        return 1

    print("PASS: all fanout option geometry requirements satisfied")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_test())