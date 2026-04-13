#!/usr/bin/env python3
"""Guardrail regression checks for class diagram connector routing.

Validates every class diagram found in workspace CSV artifacts against:
1) non-orthogonal (diagonal) connector segments,
2) connector segments passing through object bodies,
3) endpoint approach direction mismatches against selected edges,
4) same-axis segment overlap for a non-trivial shared span,
5) corner point usage in connectors,
6) insufficient clearance between connectors and object edges (disabled - needs refinement),
7) minor segment overlaps on same axis.
"""

from __future__ import annotations

import itertools
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "Scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from class_diagram_connectors import GRID_CELL_SIZE_PX
from class_diagram_renderer import _layout_classes_uml_standard, _optimize_layout_for_grid_collisions
from model import ClassDiagramDef
from parser import parse_csv

EPS = 0.5
MIN_OVERLAP_SPAN = max(6.0, GRID_CELL_SIZE_PX / 2)
MIN_MINOR_OVERLAP_SPAN = EPS
NEAR_BORDER_CLEARANCE = 3.0
NEAR_BORDER_MIN_SPAN = max(8.0, GRID_CELL_SIZE_PX / 2)


@dataclass
class RoutingIssue:
    csv_path: str
    diagram_id: str
    routing_mode: str
    issue_type: str
    detail: str


def _path_points(connector) -> List[Tuple[float, float]]:
    points = [(connector.source_x, connector.source_y)]
    points.extend(list(connector.segments))
    if points[-1] != (connector.target_x, connector.target_y):
        points.append((connector.target_x, connector.target_y))
    compact: List[Tuple[float, float]] = []
    for pt in points:
        if not compact or compact[-1] != pt:
            compact.append(pt)
    return compact


def _iter_segments(points: Sequence[Tuple[float, float]]) -> Iterable[Tuple[Tuple[float, float], Tuple[float, float]]]:
    for idx in range(len(points) - 1):
        a = points[idx]
        b = points[idx + 1]
        if abs(a[0] - b[0]) <= EPS and abs(a[1] - b[1]) <= EPS:
            continue
        yield a, b


def _is_axis_aligned(a: Tuple[float, float], b: Tuple[float, float]) -> bool:
    return abs(a[0] - b[0]) <= EPS or abs(a[1] - b[1]) <= EPS


def _edge_direction_ok(edge: str, from_pt: Tuple[float, float], to_pt: Tuple[float, float], entering: bool) -> bool:
    dx = to_pt[0] - from_pt[0]
    dy = to_pt[1] - from_pt[1]

    if entering:
        if edge == "left":
            return dx > EPS and abs(dy) <= EPS
        if edge == "right":
            return dx < -EPS and abs(dy) <= EPS
        if edge == "top":
            return dy > EPS and abs(dx) <= EPS
        if edge == "bottom":
            return dy < -EPS and abs(dx) <= EPS
    else:
        if edge == "left":
            return dx < -EPS and abs(dy) <= EPS
        if edge == "right":
            return dx > EPS and abs(dy) <= EPS
        if edge == "top":
            return dy < -EPS and abs(dx) <= EPS
        if edge == "bottom":
            return dy > EPS and abs(dx) <= EPS

    return False


def _point_inside_box(x: float, y: float, box) -> bool:
    return (box.x + EPS) < x < (box.x + box.width - EPS) and (box.y + EPS) < y < (box.y + box.height - EPS)


def _segment_crosses_box(a: Tuple[float, float], b: Tuple[float, float], box) -> bool:
    x1, y1 = a
    x2, y2 = b

    if abs(y1 - y2) <= EPS:
        y = y1
        if not (box.y + EPS < y < box.y + box.height - EPS):
            return False
        seg_min = min(x1, x2)
        seg_max = max(x1, x2)
        overlap = min(seg_max, box.x + box.width - EPS) - max(seg_min, box.x + EPS)
        return overlap > EPS

    if abs(x1 - x2) <= EPS:
        x = x1
        if not (box.x + EPS < x < box.x + box.width - EPS):
            return False
        seg_min = min(y1, y2)
        seg_max = max(y1, y2)
        overlap = min(seg_max, box.y + box.height - EPS) - max(seg_min, box.y + EPS)
        return overlap > EPS

    dx = x2 - x1
    dy = y2 - y1
    steps = max(int(max(abs(dx), abs(dy)) / max(4.0, GRID_CELL_SIZE_PX / 4)), 1)
    for i in range(steps + 1):
        t = i / steps
        sx = x1 + dx * t
        sy = y1 + dy * t
        if _point_inside_box(sx, sy, box):
            return True
    return False


def _segment_overlap_span(seg_a: Tuple[Tuple[float, float], Tuple[float, float]],
                          seg_b: Tuple[Tuple[float, float], Tuple[float, float]]) -> float:
    (a1, a2), (b1, b2) = seg_a, seg_b

    if abs(a1[1] - a2[1]) <= EPS and abs(b1[1] - b2[1]) <= EPS:
        if abs(a1[1] - b1[1]) > EPS:
            return 0.0
        a_min, a_max = sorted([a1[0], a2[0]])
        b_min, b_max = sorted([b1[0], b2[0]])
        return max(0.0, min(a_max, b_max) - max(a_min, b_min))

    if abs(a1[0] - a2[0]) <= EPS and abs(b1[0] - b2[0]) <= EPS:
        if abs(a1[0] - b1[0]) > EPS:
            return 0.0
        a_min, a_max = sorted([a1[1], a2[1]])
        b_min, b_max = sorted([b1[1], b2[1]])
        return max(0.0, min(a_max, b_max) - max(a_min, b_min))

    return 0.0


def _segment_near_box_border(a: Tuple[float, float], b: Tuple[float, float], box,
                             clearance: float = NEAR_BORDER_CLEARANCE,
                             min_span: float = NEAR_BORDER_MIN_SPAN) -> bool:
    """Check whether an orthogonal segment runs very close to a box border.

    This flags "border-hugging" routes that do not enter the object but visually
    pass through/against its outline.
    """
    x1, y1 = a
    x2, y2 = b

    if abs(y1 - y2) <= EPS:
        y = y1
        near_top = abs(y - box.y) <= clearance
        near_bottom = abs(y - (box.y + box.height)) <= clearance
        if not (near_top or near_bottom):
            return False
        seg_min = min(x1, x2)
        seg_max = max(x1, x2)
        overlap = min(seg_max, box.x + box.width) - max(seg_min, box.x)
        return overlap >= min_span

    if abs(x1 - x2) <= EPS:
        x = x1
        near_left = abs(x - box.x) <= clearance
        near_right = abs(x - (box.x + box.width)) <= clearance
        if not (near_left or near_right):
            return False
        seg_min = min(y1, y2)
        seg_max = max(y1, y2)
        overlap = min(seg_max, box.y + box.height) - max(seg_min, box.y)
        return overlap >= min_span

    return False


def _edge_has_perpendicular_departure(edge: str, from_pt: Tuple[float, float], to_pt: Tuple[float, float],
                                      entering: bool) -> bool:
    """Require first/last visible segment to move perpendicular to the endpoint edge."""
    dx = to_pt[0] - from_pt[0]
    dy = to_pt[1] - from_pt[1]

    if entering:
        if edge in {"top", "bottom"}:
            return abs(dy) > EPS
        if edge in {"left", "right"}:
            return abs(dx) > EPS
        return False

    if edge in {"top", "bottom"}:
        return abs(dy) > EPS
    if edge in {"left", "right"}:
        return abs(dx) > EPS
    return False


def _connection_point_on_corner(edge: str, point_idx: int, grid) -> bool:
    """Check if a connection point index is at a corner of its edge."""
    if not grid:
        return False
    if not edge:  # Empty edge means point not assigned
        return False
    return grid.is_corner_point(edge, point_idx)


def _segments_overlap_on_same_axis(seg_a: Tuple[Tuple[float, float], Tuple[float, float]],
                                   seg_b: Tuple[Tuple[float, float], Tuple[float, float]], 
                                   min_span: float = MIN_MINOR_OVERLAP_SPAN) -> bool:
    """Check if two segments overlap on the same axis (not just intersect).
    
    Returns True if they occupy the same line with overlap length >= min_span.
    """
    (a1, a2), (b1, b2) = seg_a, seg_b
    
    # Both horizontal
    if abs(a1[1] - a2[1]) <= EPS and abs(b1[1] - b2[1]) <= EPS:
        if abs(a1[1] - b1[1]) > EPS:
            return False
        a_min, a_max = sorted([a1[0], a2[0]])
        b_min, b_max = sorted([b1[0], b2[0]])
        overlap = max(0.0, min(a_max, b_max) - max(a_min, b_min))
        return overlap >= min_span
    
    # Both vertical
    if abs(a1[0] - a2[0]) <= EPS and abs(b1[0] - b2[0]) <= EPS:
        if abs(a1[0] - b1[0]) > EPS:
            return False
        a_min, a_max = sorted([a1[1], a2[1]])
        b_min, b_max = sorted([b1[1], b2[1]])
        overlap = max(0.0, min(a_max, b_max) - max(a_min, b_min))
        return overlap >= min_span
    
    return False


def _validate_connector_shapes(csv_path: Path, diagram_id: str, routing_mode: str, planner) -> List[RoutingIssue]:
    issues: List[RoutingIssue] = []

    connector_segments: Dict[Tuple[str, str], List[Tuple[Tuple[float, float], Tuple[float, float]]]] = {}

    for connector in planner.connectors:
        points = _path_points(connector)
        segment_list = list(_iter_segments(points))
        connector_key = (connector.source_name, connector.target_name)
        connector_segments[connector_key] = segment_list

        # Check for corner point usage
        src_grid = planner.grids.get(connector.source_name)
        tgt_grid = planner.grids.get(connector.target_name)
        
        if src_grid and connector.source_edge and _connection_point_on_corner(connector.source_edge, connector.source_point_idx, src_grid):
            issues.append(RoutingIssue(
                csv_path=str(csv_path),
                diagram_id=diagram_id,
                routing_mode=routing_mode,
                issue_type="corner_usage",
                detail=(
                    f"{connector.source_name}->{connector.target_name} exits from corner: "
                    f"{connector.source_edge}#{connector.source_point_idx} of {connector.source_name}"
                ),
            ))
        
        if tgt_grid and connector.target_edge and _connection_point_on_corner(connector.target_edge, connector.target_point_idx, tgt_grid):
            issues.append(RoutingIssue(
                csv_path=str(csv_path),
                diagram_id=diagram_id,
                routing_mode=routing_mode,
                issue_type="corner_usage",
                detail=(
                    f"{connector.source_name}->{connector.target_name} enters corner: "
                    f"{connector.target_edge}#{connector.target_point_idx} of {connector.target_name}"
                ),
            ))

        for idx, (a, b) in enumerate(segment_list):
            if not _is_axis_aligned(a, b):
                issues.append(RoutingIssue(
                    csv_path=str(csv_path),
                    diagram_id=diagram_id,
                    routing_mode=routing_mode,
                    issue_type="diagonal_segment",
                    detail=(
                        f"{connector.source_name}->{connector.target_name} segment#{idx} "
                        f"is non-orthogonal: {a} -> {b}"
                    ),
                ))

        if len(points) >= 2:
            first_idx = 1
            while first_idx < len(points) and points[first_idx] == points[0]:
                first_idx += 1
            if first_idx < len(points) and connector.source_edge:
                if not _edge_direction_ok(connector.source_edge, points[0], points[first_idx], entering=False):
                    issues.append(RoutingIssue(
                        csv_path=str(csv_path),
                        diagram_id=diagram_id,
                        routing_mode=routing_mode,
                        issue_type="source_orientation",
                        detail=(
                            f"{connector.source_name}->{connector.target_name} exits from {connector.source_edge} "
                            f"but first segment is {points[0]} -> {points[first_idx]}"
                        ),
                    ))
                if not _edge_has_perpendicular_departure(connector.source_edge, points[0], points[first_idx], entering=False):
                    issues.append(RoutingIssue(
                        csv_path=str(csv_path),
                        diagram_id=diagram_id,
                        routing_mode=routing_mode,
                        issue_type="corner_like_endpoint",
                        detail=(
                            f"{connector.source_name}->{connector.target_name} leaves {connector.source_edge} "
                            f"without perpendicular departure: {points[0]} -> {points[first_idx]}"
                        ),
                    ))

            prev_idx = len(points) - 2
            while prev_idx >= 0 and points[prev_idx] == points[-1]:
                prev_idx -= 1
            if prev_idx >= 0 and connector.target_edge:
                if not _edge_direction_ok(connector.target_edge, points[prev_idx], points[-1], entering=True):
                    issues.append(RoutingIssue(
                        csv_path=str(csv_path),
                        diagram_id=diagram_id,
                        routing_mode=routing_mode,
                        issue_type="target_orientation",
                        detail=(
                            f"{connector.source_name}->{connector.target_name} enters {connector.target_edge} "
                            f"but final segment is {points[prev_idx]} -> {points[-1]}"
                        ),
                    ))
                if not _edge_has_perpendicular_departure(connector.target_edge, points[prev_idx], points[-1], entering=True):
                    issues.append(RoutingIssue(
                        csv_path=str(csv_path),
                        diagram_id=diagram_id,
                        routing_mode=routing_mode,
                        issue_type="corner_like_endpoint",
                        detail=(
                            f"{connector.source_name}->{connector.target_name} enters {connector.target_edge} "
                            f"without perpendicular arrival: {points[prev_idx]} -> {points[-1]}"
                        ),
                    ))

        obstacle_boxes = {
            name: box
            for name, box in planner.grids.items()
            if name not in {connector.source_name, connector.target_name}
        }
        for idx, (a, b) in enumerate(segment_list):
            for obstacle_name, obstacle_box in obstacle_boxes.items():
                if _segment_crosses_box(a, b, obstacle_box):
                    issues.append(RoutingIssue(
                        csv_path=str(csv_path),
                        diagram_id=diagram_id,
                        routing_mode=routing_mode,
                        issue_type="under_object",
                        detail=(
                            f"{connector.source_name}->{connector.target_name} segment#{idx} "
                            f"crosses object {obstacle_name}: {a} -> {b}"
                        ),
                    ))
                elif _segment_near_box_border(a, b, obstacle_box):
                    issues.append(RoutingIssue(
                        csv_path=str(csv_path),
                        diagram_id=diagram_id,
                        routing_mode=routing_mode,
                        issue_type="near_object_border",
                        detail=(
                            f"{connector.source_name}->{connector.target_name} segment#{idx} "
                            f"runs too close to border of {obstacle_name}: {a} -> {b}"
                        ),
                    ))

    connector_items = sorted(connector_segments.items(), key=lambda item: item[0])
    for (conn_a, segs_a), (conn_b, segs_b) in itertools.combinations(connector_items, 2):
        for seg_a in segs_a:
            for seg_b in segs_b:
                # Check large overlaps (existing check)
                overlap = _segment_overlap_span(seg_a, seg_b)
                if overlap >= MIN_OVERLAP_SPAN:
                    issues.append(RoutingIssue(
                        csv_path=str(csv_path),
                        diagram_id=diagram_id,
                        routing_mode=routing_mode,
                        issue_type="segment_overlap",
                        detail=(
                            f"{conn_a[0]}->{conn_a[1]} overlaps {conn_b[0]}->{conn_b[1]} "
                            f"for span {overlap:.1f}px"
                        ),
                    ))
                
                # Check any overlap on same axis (even small ones)
                if _segments_overlap_on_same_axis(seg_a, seg_b, min_span=MIN_MINOR_OVERLAP_SPAN):
                    overlap = _segment_overlap_span(seg_a, seg_b)
                    if overlap < MIN_OVERLAP_SPAN:  # Only report if not already caught above
                        issues.append(RoutingIssue(
                            csv_path=str(csv_path),
                            diagram_id=diagram_id,
                            routing_mode=routing_mode,
                            issue_type="segment_overlap_minor",
                            detail=(
                                f"{conn_a[0]}->{conn_a[1]} overlaps {conn_b[0]}->{conn_b[1]} "
                                f"for span {overlap:.1f}px on same axis"
                            ),
                        ))

    return issues


def _iter_model_csvs() -> Iterable[Path]:
    include_roots = [REPO_ROOT / "Source", REPO_ROOT / "Process", REPO_ROOT / "Test" / "tests"]
    for root in include_roots:
        if not root.exists():
            continue
        for csv_path in sorted(root.rglob("*.csv")):
            yield csv_path


def run_test() -> int:
    all_issues: List[RoutingIssue] = []
    inspected_csvs = 0
    inspected_diagrams = 0
    diagrams_by_status: Dict[str, List[str]] = {"passed": [], "failed": []}

    for csv_path in _iter_model_csvs():
        try:
            model = parse_csv(str(csv_path))
        except Exception as ex:
            print(f"WARN: failed to parse {csv_path}: {ex}")
            continue

        if not model.class_diagrams:
            continue

        inspected_csvs += 1
        inspected_diagrams += len(model.class_diagrams)

        for diagram in model.class_diagrams:
            any_issues_for_diagram = False
            for routing_mode in ("diagonal", "orthogonal"):
                filtered = ClassDiagramDef(
                    diagram_id=diagram.diagram_id,
                    description=diagram.description,
                    relationships=diagram.relationships,
                    routing=routing_mode,
                    element_types=diagram.element_types,
                )

                boxes = _layout_classes_uml_standard(filtered, model, "High", routing=routing_mode)
                _, planner, _, _ = _optimize_layout_for_grid_collisions(
                    filtered,
                    boxes,
                    routing_mode,
                    "High",
                    None,
                )
                issues_for_this = _validate_connector_shapes(csv_path, diagram.diagram_id, routing_mode, planner)
                all_issues.extend(issues_for_this)
                if issues_for_this:
                    any_issues_for_diagram = True

            diagram_key = f"{csv_path.name}::{diagram.diagram_id}"
            if any_issues_for_diagram:
                diagrams_by_status["failed"].append(diagram_key)
            else:
                diagrams_by_status["passed"].append(diagram_key)

    if not all_issues:
        print(
            f"OK: routing guardrails passed across {inspected_diagrams} class diagrams in {inspected_csvs} CSV files"
        )
        return 0

    print(
        f"FAIL: found {len(all_issues)} routing issue(s) across "
        f"{inspected_diagrams} class diagrams in {inspected_csvs} CSV files"
    )
    print("")
    print(f"PASSED DIAGRAMS: {len(diagrams_by_status['passed'])}")
    for diagram_key in sorted(diagrams_by_status["passed"])[:20]:
        print(f"  [OK] {diagram_key}")
    if len(diagrams_by_status["passed"]) > 20:
        print(f"  ... {len(diagrams_by_status['passed']) - 20} more")

    print("")
    print(f"FAILED DIAGRAMS: {len(diagrams_by_status['failed'])}")
    for diagram_key in sorted(diagrams_by_status["failed"]):
        print(f"  [FAIL] {diagram_key}")

    print("")
    for issue in all_issues[:120]:
        print(
            f" - [{issue.issue_type}] {issue.csv_path} :: {issue.diagram_id} :: "
            f"{issue.routing_mode} :: {issue.detail}"
        )
    if len(all_issues) > 120:
        print(f" ... {len(all_issues) - 120} additional issue(s) not shown")

    return 1


if __name__ == "__main__":
    raise SystemExit(run_test())
