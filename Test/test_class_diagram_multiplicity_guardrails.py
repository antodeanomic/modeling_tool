#!/usr/bin/env python3
"""Regression guardrails for multiplicity placement on class-diagram connectors.

Guardrail goals:
1) Multiplicity text must stay on first or last segment only.
2) Multiplicity text must remain endpoint-adjacent (not mid-route drift).
3) FanoutTop single multiplicities (HubTop -> *) must stay near source endpoint.
"""

from __future__ import annotations

import math
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "Scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from parser import parse_csv
from class_diagram_renderer import render_class_diagram_svg

MAX_ENDPOINT_DISTANCE = 40.0
MAX_SEGMENT_DISTANCE = 14.0


def _parse_path_points(path_d: str) -> List[Tuple[float, float]]:
    points: List[Tuple[float, float]] = []
    tokens = path_d.replace(",", " ").split()
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t in {"M", "L"} and i + 2 < len(tokens):
            points.append((float(tokens[i + 1]), float(tokens[i + 2])))
            i += 3
            continue
        i += 1
    return points


def _point_to_segment_distance(px: float, py: float, a: Tuple[float, float], b: Tuple[float, float]) -> float:
    x1, y1 = a
    x2, y2 = b
    if abs(y2 - y1) < 1e-6:
        x_min, x_max = sorted((x1, x2))
        cx = min(max(px, x_min), x_max)
        return math.hypot(px - cx, py - y1)
    if abs(x2 - x1) < 1e-6:
        y_min, y_max = sorted((y1, y2))
        cy = min(max(py, y_min), y_max)
        return math.hypot(px - x1, py - cy)
    # Fallback for unexpected diagonal: distance to closer endpoint.
    return min(math.hypot(px - x1, py - y1), math.hypot(px - x2, py - y2))


def _collect_connector_blocks(svg_text: str):
    def _local_name(tag: str) -> str:
        return tag.rsplit('}', 1)[-1]

    root = ET.fromstring(svg_text)
    blocks = []
    object_boxes: List[Tuple[float, float, float, float]] = []

    for node in root.iter():
        if _local_name(node.tag) != "g":
            continue

        node_class = node.attrib.get("class")
        if node_class == "cls-object":
            for child in node:
                if _local_name(child.tag) != "rect":
                    continue
                x = float(child.attrib.get("x", "0"))
                y = float(child.attrib.get("y", "0"))
                w = float(child.attrib.get("width", "0"))
                h = float(child.attrib.get("height", "0"))
                object_boxes.append((x, y, x + w, y + h))

        if node_class != "cls-connector":
            continue

        connector_id = node.attrib.get("data-connector-id", "")
        source = node.attrib.get("data-source", "")
        target = node.attrib.get("data-target", "")
        path_node = None
        texts = []
        for child in node:
            child_name = _local_name(child.tag)
            if child_name == "path" and path_node is None:
                path_node = child
            elif child_name == "text":
                texts.append(child)
        if path_node is None:
            continue
        path_points = _parse_path_points(path_node.attrib.get("d", ""))
        if len(path_points) < 2:
            continue
        blocks.append((connector_id, source, target, path_points, texts))

    return blocks, object_boxes


def _relationship_map(csv_path: Path, diagram_id: str) -> Dict[Tuple[str, str], Tuple[str, str]]:
    model = parse_csv(str(csv_path))
    diagram = next(d for d in model.class_diagrams if d.diagram_id == diagram_id)
    rel_map: Dict[Tuple[str, str], Tuple[str, str]] = {}
    for r in diagram.relationships:
        rel_map[(r.source, r.target)] = (r.src_mult or "", r.tgt_mult or "")
    return rel_map


def _assert(condition: bool, message: str):
    if not condition:
        raise AssertionError(message)


def _check_probe_label_positions(
    blocks,
    object_boxes: List[Tuple[float, float, float, float]],
    diagram_id: str,
) -> None:
    if diagram_id != "OrthogonalTopEntryProbe":
        return

    expected = {("Obj1", "Obj3"), ("Obj4", "Obj1")}
    checked = set()

    for _cid, source, target, pts, texts in blocks:
        key = (source, target)
        if key not in expected:
            continue

        label_nodes = [t for t in texts if t.attrib.get("font-family") != "monospace" and (t.text or "").strip()]
        _assert(label_nodes, f"FAIL [{diagram_id}] missing connector label for {source}->{target}")

        label = label_nodes[0]
        lx = float(label.attrib.get("x", "0"))
        ly = float(label.attrib.get("y", "0"))

        vertical_dists = []
        horizontal_dists = []
        for i in range(len(pts) - 1):
            a = pts[i]
            b = pts[i + 1]
            d = _point_to_segment_distance(lx, ly, a, b)
            if abs(a[0] - b[0]) < 1e-6:
                vertical_dists.append(d)
            elif abs(a[1] - b[1]) < 1e-6:
                horizontal_dists.append(d)

        _assert(vertical_dists, f"FAIL [{diagram_id}] no vertical segment found for {source}->{target}")
        d_vert = min(vertical_dists)
        d_horiz = min(horizontal_dists) if horizontal_dists else 1e9
        _assert(
            d_vert <= MAX_SEGMENT_DISTANCE,
            f"FAIL [{diagram_id}] {source}->{target} label is not on/near vertical segment (d_vert={d_vert:.1f})",
        )
        _assert(
            d_vert + 0.5 <= d_horiz,
            f"FAIL [{diagram_id}] {source}->{target} label drifts toward horizontal segment (d_vert={d_vert:.1f}, d_horiz={d_horiz:.1f})",
        )

        for left, top, right, bottom in object_boxes:
            inside = (left - 2.0) <= lx <= (right + 2.0) and (top - 2.0) <= ly <= (bottom + 2.0)
            _assert(
                not inside,
                f"FAIL [{diagram_id}] {source}->{target} label intersects object box at ({lx:.1f},{ly:.1f})",
            )

        checked.add(key)

    _assert(
        checked == expected,
        f"FAIL [{diagram_id}] expected probe label checks for {sorted(expected)}, got {sorted(checked)}",
    )


def _check_svg(csv_path: Path, diagram_id: str) -> None:
    model = parse_csv(str(csv_path))
    diagram = next(d for d in model.class_diagrams if d.diagram_id == diagram_id)
    svg_text = render_class_diagram_svg(model, diagram, verbosity_level="High")

    blocks, object_boxes = _collect_connector_blocks(svg_text)
    rels = _relationship_map(csv_path, diagram_id)

    checked_count = 0
    for _cid, source, target, pts, texts in blocks:
        first_seg = (pts[0], pts[1])
        last_seg = (pts[-2], pts[-1])
        middle_segments = [(pts[i], pts[i + 1]) for i in range(1, len(pts) - 2)]
        rel_src_mult, rel_tgt_mult = rels.get((source, target), ("", ""))

        for t in texts:
            if t.attrib.get("font-family") != "monospace":
                continue
            txt = (t.text or "").strip()
            if not txt:
                continue

            checked_count += 1
            x = float(t.attrib.get("x", "0"))
            y = float(t.attrib.get("y", "0"))

            d_first = _point_to_segment_distance(x, y, *first_seg)
            d_last = _point_to_segment_distance(x, y, *last_seg)
            d_mid = min((_point_to_segment_distance(x, y, a, b) for a, b in middle_segments), default=1e9)

            _assert(
                min(d_first, d_last) <= MAX_SEGMENT_DISTANCE,
                f"FAIL [{diagram_id}] {source}->{target} multiplicity '{txt}' is not on first/last segment (d_first={d_first:.1f}, d_last={d_last:.1f})",
            )
            _assert(
                min(d_first, d_last) <= d_mid + 0.5,
                f"FAIL [{diagram_id}] {source}->{target} multiplicity '{txt}' is closer to middle segment than first/last",
            )

            ds = math.hypot(x - pts[0][0], y - pts[0][1])
            dt = math.hypot(x - pts[-1][0], y - pts[-1][1])
            _assert(
                min(ds, dt) <= MAX_ENDPOINT_DISTANCE,
                f"FAIL [{diagram_id}] {source}->{target} multiplicity '{txt}' is not endpoint-adjacent (ds={ds:.1f}, dt={dt:.1f})",
            )

            if diagram_id == "FanoutTop" and source == "HubTop" and (not rel_src_mult) and rel_tgt_mult:
                _assert(
                    ds < dt,
                    f"FAIL [FanoutTop] {source}->{target} single multiplicity '{txt}' must stay near source endpoint (ds={ds:.1f}, dt={dt:.1f})",
                )

    _assert(checked_count > 0, f"FAIL [{diagram_id}] no multiplicity texts were checked")
    _check_probe_label_positions(blocks, object_boxes, diagram_id)


def run_test() -> int:
    _check_svg(REPO_ROOT / "Test" / "tests" / "fanout.csv", "FanoutTop")
    _check_svg(
        REPO_ROOT / "Process" / "01_System" / "40_Tests" / "20_Advanced" / "test_class_diagram_all_connector_combinations.csv",
        "OrthogonalTopEntryProbe",
    )
    print("OK: multiplicity guardrail checks passed (first/last segment + endpoint adjacency)")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_test())
