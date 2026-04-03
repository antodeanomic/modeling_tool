#!/usr/bin/env python3
"""SVG renderer for UML class/structure diagrams.

Supports element types: class, component, package, object.
Supports connector routing: diagonal, orthogonal, mixed.
Supports verbosity: Low (name only), Normal (+members), High (+operations).
Supports layer filtering to show subsets of relationships.
"""

from model import Model, ClassDiagramDef, ClassRelationship, ClassDef, ELEMENT_TYPES
from class_diagram_connectors import ConnectorPlanner
from datetime import datetime
from typing import Tuple

# Layout constants
FONT_SIZE = 13
FONT_FAMILY = "Arial, Helvetica, sans-serif"
CHAR_WIDTH = 7.8  # Approximate character width for Arial at 13px
CONNECTOR_FONT_FAMILY = "monospace"  # Monospace for connector labels (multiplicity, labels)
CONNECTOR_CHAR_WIDTH = 7.5  # Approximate character width for monospace at 11px
CLASS_BOX_PADDING_X = 14
CLASS_BOX_PADDING_Y = 10
CLASS_MIN_WIDTH = 120
CLASS_SECTION_SPACING = 4  # Space between name/members/functions sections
MEMBER_FONT_SIZE = 12
MEMBER_CHAR_WIDTH = 7.2
ROW_HEIGHT = 18  # Line height for members/functions
CLASS_SPACING_X = 60  # Horizontal gap between class boxes
CLASS_SPACING_Y = 50  # Vertical gap between rows of classes
GRID_BLOCK_HEIGHT = 40  # Grid block height (boxes sized in multiples of this)
GRID_CELL_SIZE_PX = 20  # Mandatory object grid cell size (square)
MARGIN = 40
ARROW_SIZE = 10  # Arrowhead size
DIAMOND_SIZE = 10  # Diamond marker size

# Checkerboard color palette - alternating light fills with darker strokes
# Extended color palette - 30 distinct color pairs
# Sequential assignment ensures no color reuse until all colors are exhausted
COLOR_PALETTE = [
    {"light_fill": "#E8F1FF", "dark_stroke": "#0057B8"},
    {"light_fill": "#FFE9EC", "dark_stroke": "#B00020"},
    {"light_fill": "#EAF7EA", "dark_stroke": "#006E1C"},
    {"light_fill": "#FFF1E6", "dark_stroke": "#C45A00"},
    {"light_fill": "#F3E9FF", "dark_stroke": "#6A1B9A"},
    {"light_fill": "#E6FAFC", "dark_stroke": "#007C91"},
    {"light_fill": "#F5ECE6", "dark_stroke": "#6D4C41"},
    {"light_fill": "#ECEFF3", "dark_stroke": "#37474F"},
    {"light_fill": "#FFF7D6", "dark_stroke": "#A66A00"},
    {"light_fill": "#EAF4FF", "dark_stroke": "#1A237E"},
    {"light_fill": "#FDEBF5", "dark_stroke": "#AD1457"},
    {"light_fill": "#E9F8F1", "dark_stroke": "#00796B"},
    {"light_fill": "#FBEFE3", "dark_stroke": "#BF360C"},
    {"light_fill": "#EFEAFE", "dark_stroke": "#4527A0"},
    {"light_fill": "#E8F8FB", "dark_stroke": "#006064"},
    {"light_fill": "#F3F3F3", "dark_stroke": "#263238"},
]

# Element type visual styles (fallback if no color assigned)
ELEMENT_STYLES = {
    "class": {"fill": "#FAFAFA", "stroke": "#333", "stereotype": None},
    "component": {"fill": "#E8F5E9", "stroke": "#2E7D32", "stereotype": "\u00ABcomponent\u00BB"},
    "package": {"fill": "#E3F2FD", "stroke": "#1565C0", "stereotype": "\u00ABpackage\u00BB"},
    "object": {"fill": "#FFF3E0", "stroke": "#E65100", "stereotype": None},
}

# Connector text layout constants
CONNECTOR_MULTIPLICITY_MAX = 4  # Worst case: "1..*" = 4 characters
TEXT_SPACING = 2  # Spaces between connector elements
ARROW_MARKER_WIDTH = 10  # Approximate width for arrow/diamond markers


def _assign_box_colors(boxes):
    """Assign colors to boxes sequentially (non-repeating).
    
    Colors are assigned in order as boxes are encountered.
    Once all colors in the palette are used, the sequence repeats.
    This ensures maximum color diversity before any color is reused.
    
    Args:
        boxes: Dictionary of class_name -> {x, y, width, height, ...}
    
    Returns:
        Dictionary of class_name -> {light_fill, dark_stroke}
    """
    colors = {}
    
    # Group boxes by row (Y coordinate) for consistent ordering
    rows = {}
    for name, box in boxes.items():
        y = box['y']
        if y not in rows:
            rows[y] = []
        rows[y].append((box['x'], name))
    
    # Assign colors sequentially across all boxes
    box_index = 0
    sorted_rows = sorted(rows.keys())
    for row_idx, y in enumerate(sorted_rows):
        # Sort boxes in this row by X coordinate for consistent left-to-right ordering
        row_boxes = sorted(rows[y])
        
        for col_idx, (x, name) in enumerate(row_boxes):
            # Sequential assignment: colors cycle through palette without repeating until exhausted
            color_idx = box_index % len(COLOR_PALETTE)
            colors[name] = COLOR_PALETTE[color_idx].copy()
            box_index += 1
    
    return colors


def _calculate_connector_text_width(multiplicity: str, label: str = "", char_width: float = CONNECTOR_CHAR_WIDTH) -> float:
    """Calculate width in pixels for connector text elements.
    
    Args:
        multiplicity: Multiplicity string (e.g., "1", "0..*")
        label: Connector label text (optional)
        char_width: Character width (default: monospace at font size 11)
    
    Returns:
        Width in pixels
    """
    width = 0
    if multiplicity:
        width += len(multiplicity) * char_width
    if label:
        width += len(label) * char_width
    return width


def _calculate_required_spacing(diagram, verbosity="High") -> float:
    """Calculate minimum horizontal spacing needed for connector elements on horizontal lines.
    
    For horizontal connectors, we need space for:
      - Arrow/diamond marker: ~10px
      - Source multiplicity (max "1..*"): ~30px
      - 2 spaces gap: ~15px
      - Connector text: varies
      - 2 spaces gap: ~15px
      - Target multiplicity: ~30px
      - Arrow/diamond marker: ~10px
    
    Also computes vertical spacing needed for vertical connectors.
    
    Args:
        diagram: ClassDiagramDef with relationships
        verbosity: "Low", "Normal", or "High"
    
    Returns:
        Recommended minimum spacing in pixels
    """
    if not diagram.relationships:
        return CLASS_SPACING_X
    
    # Base spacing for connector elements
    max_width_needed = 0
    
    for rel in diagram.relationships:
        # Calculate width for this relationship's connector text
        width = ARROW_MARKER_WIDTH * 2  # Start and end arrows
        
        # Add multiplicity widths
        if verbosity == "High":
            src_mult_width = len(rel.src_mult) * CONNECTOR_CHAR_WIDTH if rel.src_mult else CONNECTOR_MULTIPLICITY_MAX * CONNECTOR_CHAR_WIDTH
            tgt_mult_width = len(rel.tgt_mult) * CONNECTOR_CHAR_WIDTH if rel.tgt_mult else CONNECTOR_MULTIPLICITY_MAX * CONNECTOR_CHAR_WIDTH
            width += src_mult_width + tgt_mult_width
            width += (TEXT_SPACING * 2) * CONNECTOR_CHAR_WIDTH  # 2 spaces before and after label
        
        # Add label width
        if rel.label:
            width += len(rel.label) * CONNECTOR_CHAR_WIDTH
        
        max_width_needed = max(max_width_needed, width)
    
    # Return recommended spacing (this gets added to the base spacing)
    # We want to ensure the gap between boxes is at least this wide
    return max(CLASS_SPACING_X, int(max_width_needed * 0.8))  # Use 80% as recommended gap


def _get_segment_type(x1: float, y1: float, x2: float, y2: float) -> str:
    """Determine if a line segment is horizontal or vertical.
    
    Args:
        x1, y1: Start point
        x2, y2: End point
    
    Returns:
        "horizontal" if primarily horizontal, "vertical" if primarily vertical
    """
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    return "horizontal" if dx > dy else "vertical"


def _place_text_perpendicular(x: float, y: float, text: str, segment_type: str, 
                              is_final: bool = False, offset_px: float = 8) -> str:
    """Generate SVG text element positioned perpendicular to segment.
    
    Args:
        x, y: Text position
        text: Text content
        segment_type: "horizontal" or "vertical"  
        is_final: If True, position on opposite side
        offset_px: Distance from line
    
    Returns:
        SVG text element string
    """
    if segment_type == "vertical":
        # Vertical segment: place text to the right
        if is_final:
            x_pos = x + offset_px
            anchor = "start"
        else:
            x_pos = x + offset_px
            anchor = "start"
        y_pos = y
    else:
        # Horizontal segment: place text above
        x_pos = x
        y_pos = y - offset_px
        anchor = "middle"
    
    return f'  <text x="{x_pos}" y="{y_pos}" font-family="{CONNECTOR_FONT_FAMILY}" ' \
           f'font-size="11" fill="#666" text-anchor="{anchor}">' \
           f'{_escape_xml(text)}</text>'


def _escape_xml(text):
    """Escape special XML characters."""
    return (text.replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;'))


def _snap_height_to_grid(height: float) -> float:
    """Snap box height to nearest grid block multiple.
    
    Ensures all boxes have heights that are multiples of GRID_BLOCK_HEIGHT.
    This guarantees that connection points on different-sized boxes will align
    when they are on the same row.
    
    Args:
        height: Calculated box height in pixels
    
    Returns:
        Height rounded up to nearest GRID_BLOCK_HEIGHT multiple
    """
    import math
    blocks = math.ceil(height / GRID_BLOCK_HEIGHT)
    return blocks * GRID_BLOCK_HEIGHT


def _snap_width_to_grid(width: float) -> float:
    """Snap box width to fixed-size object grid cells (20px per column)."""
    import math
    return math.ceil(width / GRID_CELL_SIZE_PX) * GRID_CELL_SIZE_PX


def _measure_text(text, font_size=FONT_SIZE):
    """Estimate text width in pixels."""
    char_w = CHAR_WIDTH if font_size == FONT_SIZE else MEMBER_CHAR_WIDTH
    return len(text) * char_w


def _grid_cell_key(x, y, cell_size=GRID_CELL_SIZE_PX):
    """Convert pixel coordinates to a discrete grid cell key."""
    return int(x // cell_size), int(y // cell_size)


def _path_points_from_connector(connector):
    """Return connector path points including source and target endpoints."""
    points = [(connector.source_x, connector.source_y)]
    if connector.segments:
        points.extend(list(connector.segments))
    if points[-1] != (connector.target_x, connector.target_y):
        points.append((connector.target_x, connector.target_y))
    return points


def _segment_direction(dx, dy):
    """Return the cardinal direction for a segment delta."""
    if abs(dx) >= abs(dy):
        return 'right' if dx > 0 else 'left'
    return 'down' if dy > 0 else 'up'


def _final_path_direction(points):
    """Return the direction of the last non-zero segment in a polyline."""
    for idx in range(len(points) - 1, 0, -1):
        x2, y2 = points[idx]
        x1, y1 = points[idx - 1]
        dx = x2 - x1
        dy = y2 - y1
        if abs(dx) > 0 or abs(dy) > 0:
            return _segment_direction(dx, dy)
    return 'right'


def _directed_marker_id(marker_id, direction):
    """Return the directional marker id for end-marker rendering."""
    if not marker_id:
        return None
    return f"{marker_id}-{direction}"


def _source_label_anchor(connector, points):
    """Place connector labels close to the source, following source multiplicity.

    This keeps labels away from the middle of dense routes where collision
    detection is weaker and clutter is harder to read.
    """
    first_pt = points[1] if len(points) >= 2 else points[0]
    src_mult_gap = ((len(connector.src_mult or "") + 2) * CONNECTOR_CHAR_WIDTH)

    if abs(first_pt[0] - connector.source_x) >= abs(first_pt[1] - connector.source_y):
        direction = 1 if first_pt[0] >= connector.source_x else -1
        base_gap = 10 + src_mult_gap
        x = connector.source_x + direction * base_gap
        y = connector.source_y - 8
        anchor = 'start' if direction > 0 else 'end'
        return x, y, anchor

    travel = first_pt[1] - connector.source_y
    fraction = 0.55 if connector.src_mult else 0.35
    x = connector.source_x + 8
    y = connector.source_y + travel * fraction
    return x, y, 'start'


def _mark_box_cells(occupancy, box_name, box):
    """Mark all grid cells occupied by an object box."""
    min_cx = int(box['x'] // GRID_CELL_SIZE_PX)
    max_cx = int((box['x'] + box['width'] - 1) // GRID_CELL_SIZE_PX)
    min_cy = int(box['y'] // GRID_CELL_SIZE_PX)
    max_cy = int((box['y'] + box['height'] - 1) // GRID_CELL_SIZE_PX)
    token = f"object:{box_name}"

    for cx in range(min_cx, max_cx + 1):
        for cy in range(min_cy, max_cy + 1):
            occupancy.setdefault((cx, cy), set()).add(token)


def _mark_polyline_cells(occupancy, token, points):
    """Mark grid cells occupied by a connector polyline."""
    for i in range(len(points) - 1):
        x1, y1 = points[i]
        x2, y2 = points[i + 1]
        dx = x2 - x1
        dy = y2 - y1
        steps = max(int(max(abs(dx), abs(dy)) // GRID_CELL_SIZE_PX), 1)

        for step in range(steps + 1):
            t = step / max(steps, 1)
            sx = x1 + dx * t
            sy = y1 + dy * t
            occupancy.setdefault(_grid_cell_key(sx, sy), set()).add(token)


def _estimate_connector_text_items(connector, verbosity_level):
    """Estimate connector text anchor points for grid-collision auditing."""
    points = _path_points_from_connector(connector)

    if verbosity_level != "High":
        if connector.label:
            if len(points) >= 2:
                lx, ly, anchor = _source_label_anchor(connector, points)
                return [{'text': connector.label, 'x': lx, 'y': ly, 'anchor': anchor, 'kind': 'label'}]
        return []

    text_items = []
    first_pt = points[1] if len(points) >= 2 else points[0]

    has_source_marker = _arrow_has_marker(connector.arrow_type, "start")
    has_target_marker = _arrow_has_marker(connector.arrow_type, "end")

    if connector.src_mult:
        if not has_source_marker:
            x = connector.source_x - 12
            y = _calculate_grid_cell_position(connector.source_y)
            anchor = 'end'
        else:
            if abs(first_pt[0] - connector.source_x) > abs(first_pt[1] - connector.source_y):
                x = connector.source_x + (first_pt[0] - connector.source_x) * 0.20
                y = connector.source_y - 8
                anchor = 'middle'
            else:
                x = connector.source_x + 8
                y = connector.source_y + (first_pt[1] - connector.source_y) * 0.30
                anchor = 'start'
        text_items.append({'text': connector.src_mult, 'x': x, 'y': y, 'anchor': anchor, 'kind': 'src_mult'})

    if connector.label:
        lx, ly, anchor = _source_label_anchor(connector, points)
        text_items.append({'text': connector.label, 'x': lx, 'y': ly, 'anchor': anchor, 'kind': 'label'})

    if connector.tgt_mult:
        if not has_target_marker:
            x = connector.target_x - 12
            y = _calculate_grid_cell_position(connector.target_y)
            anchor = 'end'
        else:
            prev_pt = points[-2] if len(points) >= 2 else points[-1]
            if abs(connector.target_x - prev_pt[0]) > abs(connector.target_y - prev_pt[1]):
                x = connector.target_x + (prev_pt[0] - connector.target_x) * 0.20
                y = connector.target_y - 8
                anchor = 'middle'
            else:
                x = connector.target_x + 8
                y = connector.target_y + (prev_pt[1] - connector.target_y) * 0.70
                anchor = 'start'
        text_items.append({'text': connector.tgt_mult, 'x': x, 'y': y, 'anchor': anchor, 'kind': 'tgt_mult'})

    return text_items


def _mark_text_cells(occupancy, text_item, connector_id):
    """Mark all grid cells occupied by a text bounding box."""
    width = max(len(text_item['text']) * CONNECTOR_CHAR_WIDTH, 8)
    height = 14
    anchor = text_item.get('anchor', 'start')
    x = text_item['x']
    y = text_item['y']

    if anchor == 'middle':
        left = x - width / 2
    elif anchor == 'end':
        left = x - width
    else:
        left = x
    top = y - height

    min_cx = int(left // GRID_CELL_SIZE_PX)
    max_cx = int((left + width - 1) // GRID_CELL_SIZE_PX)
    min_cy = int(top // GRID_CELL_SIZE_PX)
    max_cy = int((top + height - 1) // GRID_CELL_SIZE_PX)
    token = f"text:{connector_id}:{text_item['kind']}"

    for cx in range(min_cx, max_cx + 1):
        for cy in range(min_cy, max_cy + 1):
            occupancy.setdefault((cx, cy), set()).add(token)


def _evaluate_grid_cell_collisions(planner, boxes, verbosity_level="High", strict=True):
    """Return strict whole-diagram grid-cell collision diagnostics.

    A collision is reported when a grid cell is occupied by multiple distinct
    entities (object, connector segment/endpoint, connector text).
    """
    occupancy = {}

    for name, box in boxes.items():
        _mark_box_cells(occupancy, name, box)

    for connector in planner.connectors:
        cid = f"{connector.source_name}->{connector.target_name}"
        points = _path_points_from_connector(connector)
        _mark_polyline_cells(occupancy, f"connector:{cid}", points)
        occupancy.setdefault(_grid_cell_key(connector.source_x, connector.source_y), set()).add(f"endpoint:{cid}:source")
        occupancy.setdefault(_grid_cell_key(connector.target_x, connector.target_y), set()).add(f"endpoint:{cid}:target")

        for text_item in _estimate_connector_text_items(connector, verbosity_level):
            _mark_text_cells(occupancy, text_item, cid)

    collisions = []
    for cell, tokens in occupancy.items():
        if len(tokens) <= 1:
            continue

        token_list = sorted(tokens)
        if strict:
            collisions.append((cell, token_list))
            continue

        has_text = any(t.startswith('text:') for t in token_list)
        connector_ids = set()
        object_names = set()

        for token in token_list:
            if token.startswith('object:'):
                object_names.add(token.split(':', 1)[1])
            elif token.startswith('connector:'):
                connector_ids.add(token.split(':', 1)[1])
            elif token.startswith('endpoint:'):
                parts = token.split(':', 2)
                if len(parts) >= 2:
                    connector_ids.add(parts[1])
            elif token.startswith('text:'):
                parts = token.split(':', 2)
                if len(parts) >= 2:
                    connector_ids.add(parts[1])

        # Always treat text collisions as hard.
        if has_text:
            collisions.append((cell, token_list))
            continue

        # Connector-connector crossing is hard.
        if len(connector_ids) >= 2:
            collisions.append((cell, token_list))
            continue

        # Single connector crossing a non-endpoint object is hard.
        if len(connector_ids) == 1 and object_names:
            conn = next(iter(connector_ids))
            if '->' in conn:
                src, tgt = conn.split('->', 1)
                if any(obj not in {src, tgt} for obj in object_names):
                    collisions.append((cell, token_list))

    return len(collisions), collisions


def _clone_boxes(boxes):
    """Deep-copy layout boxes dictionary for what-if planning."""
    copied = {}
    for name, box in boxes.items():
        copied[name] = dict(box)
    return copied


def _longest_segment_anchor(points):
    """Return a label anchor based on the longest segment in a polyline."""
    best = None
    best_len = -1.0
    for i in range(len(points) - 1):
        x1, y1 = points[i]
        x2, y2 = points[i + 1]
        seg_len = abs(x2 - x1) + abs(y2 - y1)
        if seg_len > best_len:
            best_len = seg_len
            best = (x1, y1, x2, y2)

    if best is None:
        return points[0][0], points[0][1] - 8, 'middle'

    x1, y1, x2, y2 = best
    if abs(x2 - x1) >= abs(y2 - y1):
        return (x1 + x2) / 2, min(y1, y2) - 8, 'middle'
    return max(x1, x2) + 8, (y1 + y2) / 2, 'start'


def _collect_collision_entities(collision_details):
    """Aggregate colliding connectors and objects from collision token lists."""
    connector_hits = {}
    object_hits = {}

    for _cell, tokens in collision_details:
        for token in tokens:
            if token.startswith('object:'):
                obj_name = token.split(':', 1)[1]
                object_hits[obj_name] = object_hits.get(obj_name, 0) + 1
            elif token.startswith('connector:'):
                conn_id = token.split(':', 1)[1]
                if '->' in conn_id:
                    src, tgt = conn_id.split('->', 1)
                    key = (src, tgt)
                    connector_hits[key] = connector_hits.get(key, 0) + 1
            elif token.startswith('text:'):
                parts = token.split(':', 2)
                if len(parts) >= 2 and '->' in parts[1]:
                    src, tgt = parts[1].split('->', 1)
                    key = (src, tgt)
                    connector_hits[key] = connector_hits.get(key, 0) + 1
            elif token.startswith('endpoint:'):
                parts = token.split(':', 2)
                if len(parts) >= 2 and '->' in parts[1]:
                    src, tgt = parts[1].split('->', 1)
                    key = (src, tgt)
                    connector_hits[key] = connector_hits.get(key, 0) + 1

    return connector_hits, object_hits


def _optimize_layout_for_grid_collisions(filtered_diagram, boxes, effective_routing, verbosity_level, layers_filter):
    """Iteratively reduce strict grid-cell collisions by rerouting and shifting.

    Strategy per pass:
    1. Identify highest-collision connectors/objects.
    2. Try rerouting those connectors with forced elbows.
    3. Try one-cell right/down object shifts for top colliding objects.
    4. Keep the best candidate if collision count improves.
    """

    def _build_planner(test_boxes, forced_elbows=None):
        p = ConnectorPlanner(routing_mode=effective_routing, forced_elbows=forced_elbows)
        for name, box in test_boxes.items():
            p.add_rectangle(name, box['x'], box['y'], box['width'], box['height'])
        for rel in filtered_diagram.relationships:
            p.add_connector(rel.source, rel.target, rel.arrow,
                            rel.src_mult, rel.tgt_mult, rel.label, rel.layer)
        p.plan_connectors()
        return p

    # Keep optimization bounded and only active for the core+security baseline view.
    if layers_filter is None or set(layers_filter) != {'core', 'security'}:
        base_planner = _build_planner(_clone_boxes(boxes), set())
        base_count, base_details = _evaluate_grid_cell_collisions(base_planner, boxes, verbosity_level, strict=False)
        return boxes, base_planner, base_count, base_details

    import time
    start_time = time.perf_counter()
    time_budget_s = 0.35

    best_boxes = _clone_boxes(boxes)
    forced_elbows = set()
    best_planner = _build_planner(best_boxes, forced_elbows)
    best_count, best_details = _evaluate_grid_cell_collisions(best_planner, best_boxes, verbosity_level, strict=False)

    # Preserve existing baseline nudge behavior as one starting candidate.
    if 'OrderService' in best_boxes:
        nudged_boxes = _clone_boxes(best_boxes)
        nudged_boxes['OrderService']['x'] += GRID_CELL_SIZE_PX
        nudged_planner = _build_planner(nudged_boxes, forced_elbows)
        nudged_count, nudged_details = _evaluate_grid_cell_collisions(nudged_planner, nudged_boxes, verbosity_level, strict=False)
        if nudged_count < best_count:
            best_boxes = nudged_boxes
            best_planner = nudged_planner
            best_count = nudged_count
            best_details = nudged_details

    max_passes = 2
    for _ in range(max_passes):
        if time.perf_counter() - start_time > time_budget_s:
            break
        if best_count == 0:
            break

        connector_hits, object_hits = _collect_collision_entities(best_details)
        top_connectors = [k for k, _v in sorted(connector_hits.items(), key=lambda item: item[1], reverse=True)[:2]]
        top_objects = [k for k, _v in sorted(object_hits.items(), key=lambda item: item[1], reverse=True)[:1]]

        candidates = []

        if top_connectors:
            candidates.append((_clone_boxes(best_boxes), forced_elbows.union(set(top_connectors))))

        for obj_name in top_objects:
            if obj_name not in best_boxes:
                continue
            for dx, dy in [(1, 0), (0, 1)]:
                moved = _clone_boxes(best_boxes)
                moved[obj_name]['x'] += dx * GRID_CELL_SIZE_PX
                moved[obj_name]['y'] += dy * GRID_CELL_SIZE_PX
                candidates.append((moved, set(forced_elbows)))
                if top_connectors:
                    candidates.append((moved, forced_elbows.union(set(top_connectors))))

        improved = False
        trial_best = best_count
        trial_boxes = best_boxes
        trial_planner = best_planner
        trial_details = best_details
        trial_elbows = forced_elbows

        for candidate_boxes, candidate_elbows in candidates:
            if time.perf_counter() - start_time > time_budget_s:
                break
            candidate_planner = _build_planner(candidate_boxes, candidate_elbows)
            candidate_count, candidate_details = _evaluate_grid_cell_collisions(
                candidate_planner, candidate_boxes, verbosity_level, strict=False
            )
            if candidate_count < trial_best:
                improved = True
                trial_best = candidate_count
                trial_boxes = candidate_boxes
                trial_planner = candidate_planner
                trial_details = candidate_details
                trial_elbows = set(candidate_elbows)

        if not improved:
            break

        best_count = trial_best
        best_boxes = trial_boxes
        best_planner = trial_planner
        best_details = trial_details
        forced_elbows = trial_elbows

    return best_boxes, best_planner, best_count, best_details


def _compute_class_box_size(class_name, class_def, verbosity="High", element_type="class"):
    """Compute width and height for a class box.
    
    Verbosity levels:
      Low: name only
      Normal: name + members
      High: name + members + functions
    
    Returns (width, height, has_members, has_functions).
    """
    # Determine if this is an object (underlined Name:Type display)
    style = ELEMENT_STYLES.get(element_type, ELEMENT_STYLES["class"])
    stereotype = style["stereotype"]
    
    # Name section - account for stereotype text above name
    display_name = class_name
    if element_type == "object" and ":" in class_name:
        display_name = class_name  # Will be rendered underlined
    
    name_width = _measure_text(display_name, FONT_SIZE) + 2 * CLASS_BOX_PADDING_X
    if stereotype:
        stereo_width = _measure_text(stereotype, MEMBER_FONT_SIZE) + 2 * CLASS_BOX_PADDING_X
        name_width = max(name_width, stereo_width)
    max_width = max(name_width, CLASS_MIN_WIDTH)
    
    has_members = False
    has_functions = False
    member_lines = 0
    function_lines = 0
    
    if class_def and verbosity != "Low":
        # Members section (shown at Normal and High)
        for m in class_def.members:
            has_members = True
            member_lines += 1
            line_text = f"  {m.name}"
            line_width = _measure_text(line_text, MEMBER_FONT_SIZE) + 2 * CLASS_BOX_PADDING_X
            max_width = max(max_width, line_width)
        
        # Functions section (shown only at High)
        if verbosity == "High":
            for f in class_def.functions:
                has_functions = True
                function_lines += 1
                vis = "+" if f.visibility == "public" else "-" if f.visibility == "private" else "#"
                line_text = f"  {vis} {f.name}"
                line_width = _measure_text(line_text, MEMBER_FONT_SIZE) + 2 * CLASS_BOX_PADDING_X
                max_width = max(max_width, line_width)
    
    # Height: stereotype line + name section + optional member section + optional function section
    height = CLASS_BOX_PADDING_Y
    if stereotype:
        height += MEMBER_FONT_SIZE + 2  # stereotype line
    height += FONT_SIZE + CLASS_BOX_PADDING_Y  # Name section
    if has_members:
        height += CLASS_SECTION_SPACING + member_lines * ROW_HEIGHT + CLASS_BOX_PADDING_Y
    if has_functions:
        height += CLASS_SECTION_SPACING + function_lines * ROW_HEIGHT + CLASS_BOX_PADDING_Y
    
    # Component gets extra width for the icon
    if element_type == "component":
        max_width += 20  # Space for component icon
    
    snapped_width = _snap_width_to_grid(max_width)
    return snapped_width, _snap_height_to_grid(height), has_members, has_functions


def _get_relationship_type(arrow):
    """Classify the relationship type from the arrow symbol.
    
    Returns one of: 'generalization', 'realization', 'aggregation', 'composition', 
                    'association', 'dependency'
    """
    if arrow in ['--▷', '◁--']:
        return 'generalization'
    elif arrow in ['..▷', '◁..']:
        return 'realization'
    elif arrow in ['--◆', '◆--']:
        return 'composition'
    elif arrow in ['--◇', '◇--']:
        return 'aggregation'
    elif arrow in ['..>', '<..']:
        return 'dependency'
    elif arrow in ['--', '-->', '<--', '<-->']:
        return 'association'
    return 'association'  # default


def _build_uml_layout_graph(diagram):
    """Build position constraints based on UML standard conventions.
    
    Returns:
        {
            'above': [(superclass, subclass), ...],     # superclass above subclass
            'below': [(subclass, superclass), ...],      # inverse of above
            'left_of': [(whole, part), ...],              # whole left of part (aggregation/composition)
            'right_of': [(part, whole), ...],             # inverse of left_of
            'left_to_right': [(source, target), ...],     # general left-to-right
        }
    """
    constraints = {
        'above': [],      # Superclass/Interface above
        'below': [],
        'left_of': [],    # Whole/Client left of part/supplier
        'right_of': [],
        'left_to_right': [],
        'peers': [],      # Horizontal peers (associations)
    }
    
    for rel in diagram.relationships:
        rel_type = _get_relationship_type(rel.arrow)
        
        if rel_type == 'generalization':
            # Superclass above subclass
            if rel.arrow == '--▷':  # source is subclass, target is superclass
                constraints['below'].append((rel.source, rel.target))
                constraints['above'].append((rel.target, rel.source))
            else:  # ◁-- : source is superclass, target is subclass
                constraints['above'].append((rel.source, rel.target))
                constraints['below'].append((rel.target, rel.source))
        
        elif rel_type == 'realization':
            # Interface above, implementing class below
            if rel.arrow == '..▷':  # source implements, target is interface
                constraints['below'].append((rel.source, rel.target))
                constraints['above'].append((rel.target, rel.source))
            else:  # ◁.. : source is interface, target implements
                constraints['above'].append((rel.source, rel.target))
                constraints['below'].append((rel.target, rel.source))
        
        elif rel_type in ['composition', 'aggregation']:
            # Whole on left, part on right
            if rel.arrow in ['--◆', '--◇']:  # source is whole, target is part
                constraints['left_of'].append((rel.source, rel.target))
                constraints['right_of'].append((rel.target, rel.source))
            else:  # ◆--, ◇-- : source is part, target is whole
                constraints['right_of'].append((rel.source, rel.target))
                constraints['left_of'].append((rel.target, rel.source))
        
        elif rel_type == 'dependency':
            # Client/source on left, supplier/target on right
            if rel.arrow == '..>':  # source depends on target
                constraints['left_to_right'].append((rel.source, rel.target))
            else:  # <.. : target depends on source
                constraints['left_to_right'].append((rel.target, rel.source))
        
        elif rel_type == 'association':
            # Peers - keep horizontal
            constraints['peers'].append((rel.source, rel.target))
    
    return constraints


def _build_ownership_trees(diagram):
    """Build ownership hierarchies from composition/aggregation relationships.
    
    Returns:
        {
            'owner_to_children': {owner: [children]},
            'child_to_owner': {child: owner},
            'roots': [classes with no owner]
        }
    """
    owner_to_children = {}
    child_to_owner = {}
    
    for rel in diagram.relationships:
        rel_type = _get_relationship_type(rel.arrow)
        
        if rel_type in ['composition', 'aggregation']:
            # Determine owner (whole) and child (part)
            if rel.arrow in ['--◆', '--◇']:  # source is owner
                owner, child = rel.source, rel.target
            else:  # ◆--, ◇-- : target is owner
                owner, child = rel.target, rel.source
            
            if owner not in owner_to_children:
                owner_to_children[owner] = []
            owner_to_children[owner].append(child)
            child_to_owner[child] = owner
    
    # Find roots (no owner)
    all_classes = set(owner_to_children.keys()) | set(child_to_owner.keys())
    roots = [c for c in all_classes if c not in child_to_owner]
    
    return {
        'owner_to_children': owner_to_children,
        'child_to_owner': child_to_owner,
        'roots': roots,
    }


def _layout_tree_vertical(root_name, trees, boxes, spacing_x, spacing_y, x_base, y_base):
    """Layout a single ownership tree vertically (parent at top, children cascading down).
    
    Tree Structure (example):
        FunctionDef           (depth 0, row 0)
            -> ParamDef       (depth 1, row 1)
            -> ReturnDef      (depth 1, row 2)
                -> MemberVar  (depth 2, row 3)
    
    Returns:
        {
            'positions': {class: {x, y, ...}},
            'width': tree width,
            'height': tree height,
        }
    """
    positions = {}
    owner_to_children = trees['owner_to_children']
    
    row_counter = [0]  # Track current row index
    indent_width = 60  # Horizontal indent per depth level
    
    def place_node(name, depth):
        """Recursively place node and all its descendants."""
        if name in positions:
            return
        
        # Position this node at current row, indented by depth
        x = x_base + depth * indent_width
        y = y_base + row_counter[0] * (boxes[name]['height'] + spacing_y)
        
        positions[name] = {
            'x': x,
            'y': y,
            'width': boxes[name]['width'],
            'height': boxes[name]['height'],
            'box_info': boxes[name],
        }
        
        row_counter[0] += 1  # Move to next row for siblings/children
        
        # Place all children at next depth level
        children = owner_to_children.get(name, [])
        for child in children:
            place_node(child, depth + 1)
    
    # Start placement from root
    place_node(root_name, 0)
    
    # Calculate tree dimensions
    if positions:
        min_x = min(p['x'] for p in positions.values())
        max_x = max(p['x'] + p['width'] for p in positions.values())
        min_y = min(p['y'] for p in positions.values())
        max_y = max(p['y'] + p['height'] for p in positions.values())
        
        tree_width = max_x - min_x
        tree_height = max_y - min_y
    else:
        tree_width = boxes[root_name]['width']
        tree_height = boxes[root_name]['height']
    
    return {
        'positions': positions,
        'width': tree_width,
        'height': tree_height,
        'row_count': row_counter[0],
    }


def _calculate_abstraction_level(diagram):
    """Calculate abstraction level for each class.
    
    Level 0: Classes with no incoming edges (most general, appear at TOP)
    Level N: Classes that depend on level N-1 (more specific, appear at BOTTOM)
    
    Considers ALL hierarchies: generalization, realization, composition, aggregation, dependency
    
    Returns: {class_name: level}
    """
    # Count incoming edges from more-specific-to-more-general relationships
    in_degree = {}
    outgoing = {}  # Track outgoing edges for topological sort
    all_classes = set()
    
    for rel in diagram.relationships:
        rel_type = _get_relationship_type(rel.arrow)
        all_classes.add(rel.source)
        all_classes.add(rel.target)
        
        # Determine parent (more general) and child (more specific)
        parent = None
        child = None
        
        if rel_type == 'generalization':
            # Subclass depends on superclass -> superclass is parent
            if rel.arrow == '--▷':  # source is subclass
                child, parent = rel.source, rel.target
            else:  # ◁--: source is superclass
                parent, child = rel.source, rel.target
                
        elif rel_type == 'realization':
            # Implementing class depends on interface -> interface is parent
            if rel.arrow == '..▷':  # source implements
                child, parent = rel.source, rel.target
            else:  # ◁..: source is interface
                parent, child = rel.source, rel.target
                
        elif rel_type in ['composition', 'aggregation']:
            # Part depends on owner -> owner is parent (more general)
            # Arrow notation: marker position indicates owner
            # --◆ or --◇: marker at target (target is owner)
            # ◆-- or ◇--: marker at source (source is owner)
            if rel.arrow in ['--◆', '--◇']:  # marker at target = target is owner
                parent, child = rel.target, rel.source
            elif rel.arrow in ['◆--', '◇--']:  # marker at source = source is owner
                parent, child = rel.source, rel.target
            else:  # default to target as owner
                parent, child = rel.target, rel.source
                
        elif rel_type == 'dependency':
            # Client depends on supplier -> supplier is parent (more general)
            if rel.arrow == '..>':  # source depends on target
                child, parent = rel.source, rel.target
            else:  # <..: target depends on source
                child, parent = rel.target, rel.source
        
        if parent and child:
            in_degree[child] = in_degree.get(child, 0) + 1
            if parent not in outgoing:
                outgoing[parent] = []
            outgoing[parent].append(child)
    
    # Initialize all classes
    for cls in all_classes:
        if cls not in in_degree:
            in_degree[cls] = 0
        if cls not in outgoing:
            outgoing[cls] = []
    
    # Topological sort with level assignment
    levels = {}
    queue = []
    in_degree_copy = in_degree.copy()
    
    # Initialize queue with root nodes (no incoming edges)
    for cls in all_classes:
        if in_degree_copy[cls] == 0:
            queue.append((cls, 0))
            levels[cls] = 0
    
    # Process queue (Kahn's algorithm)
    while queue:
        cls, level = queue.pop(0)
        
        # Process all children
        for child in outgoing.get(cls, []):
            in_degree_copy[child] -= 1
            if in_degree_copy[child] == 0:
                # All parents of this child have been visited
                # Child level = max(parent levels) + 1
                child_level = level + 1
                levels[child] = child_level
                queue.append((child, child_level))
    
    return levels


# ---------------------------------------------------------------------------
# Layout helpers: tree-centered iterative layout
# ---------------------------------------------------------------------------

def _collect_and_size_classes(diagram, model, verbosity):
    """Collect all class names from diagram relationships and compute their box sizes."""
    class_names = []
    seen = set()
    for rel in diagram.relationships:
        for nm in (rel.source, rel.target):
            if nm not in seen:
                class_names.append(nm)
                seen.add(nm)

    boxes = {}
    for name in class_names:
        class_def = model.get_class(name)
        element_type = diagram.element_types.get(name, "class")
        w, h, has_m, has_f = _compute_class_box_size(name, class_def, verbosity, element_type)
        boxes[name] = {
            'width': w, 'height': h,
            'has_members': has_m, 'has_functions': has_f,
            'class_def': class_def, 'element_type': element_type,
        }
    return class_names, boxes


def _build_spanning_forest(diagram, levels):
    """Build a spanning forest for tree-centered layout.

    For each relationship where source.level != target.level the lower-level
    node is the parent and the higher-level node is the child.  Each child is
    claimed by the first parent encountered so every node appears in at most
    one subtree.

    Returns:
        parent_children   - {parent: [children, ...]}
        claimed_children  - set of nodes that have been assigned a parent
    """
    parent_children = {}
    claimed_children = set()

    for rel in diagram.relationships:
        s_lvl = levels.get(rel.source, 0)
        t_lvl = levels.get(rel.target, 0)
        if s_lvl < t_lvl:
            parent, child = rel.source, rel.target
        elif t_lvl < s_lvl:
            parent, child = rel.target, rel.source
        else:
            continue  # same level - no parent-child relationship for layout

        if child not in claimed_children:
            parent_children.setdefault(parent, [])
            if child not in parent_children[parent]:
                parent_children[parent].append(child)
            claimed_children.add(child)

    return parent_children, claimed_children


def _apply_source_cluster_alignment(positions, diagram, levels, spacing_x):
    """Apply column clustering in filtered views to bring dependencies closer.
    
    When displaying a filtered subset of layers, adjacent dependency targets
    are shifted horizontally closer to their sources (within the same row band)
    to reduce connector lengths and improve local readability.
    
    This only applies to same-level dependencies and respects grid spacing and
    minimum box buffers. Does not modify row (Y) positions or create new overlaps.
    
    Args:
        positions: Layout dict {class_name -> {x, y, width, height, ...}}
        diagram: ClassDiagramDef with relationships
        levels: Dict {class_name -> abstraction_level}
        spacing_x: Minimum horizontal spacing between boxes
    
    Returns:
        Modified positions dict with adjusted X coordinates
    """
    # Identify dependency edges within the same level
    same_level_deps = []
    for rel in diagram.relationships:
        # Check if this is a dotted/dashed dependency arrow
        if '..' in rel.arrow:  # Dashed lines: .., <.., ..▷, ◁..
            s_lvl = levels.get(rel.source, 0)
            t_lvl = levels.get(rel.target, 0)
            if s_lvl == t_lvl:
                same_level_deps.append((rel.source, rel.target))
    
    if not same_level_deps:
        return positions  # No same-level dependencies, no adjustment needed
    
    # For each same-level dependency, try to move target closer to source
    # by shifting it left if there's space, without creating new overlaps
    min_buffer = spacing_x * 0.3  # Min gap between boxes
    
    for source, target in same_level_deps:
        if source not in positions or target not in positions:
            continue  # One or both not in current layout
        
        src_pos = positions[source]
        tgt_pos = positions[target]
        
        # Only move target if it's to the right of source
        src_right = src_pos['x'] + src_pos['width']
        tgt_x = tgt_pos['x']
        
        if tgt_x <= src_right:
            continue  # Target already left of or overlapping source
        
        # Desired position: just after source with min buffer
        desired_x = src_right + min_buffer
        
        # Check if target can move left without hitting boxes in between or before
        can_move = True
        for other_name, other_pos in positions.items():
            if other_name in (source, target):
                continue  # Skip source and target themselves
            if abs(other_pos['y'] - tgt_pos['y']) < 1:  # On same row
                # Check if other box would block the move
                other_left = other_pos['x']
                other_right = other_pos['x'] + other_pos['width']
                # If moving target to desired_x would overlap other, can't move
                if desired_x < other_right + min_buffer and tgt_x > other_left - min_buffer:
                    can_move = False
                    break
        
        if can_move and desired_x < tgt_x:
            # Move target closer to source
            tgt_pos['x'] = desired_x
    
    return positions


def _aligned_tree_layout(class_names, boxes, levels, parent_children,
                         claimed_children, base_sx, spacing_y, diagram):
    """Top-left anchored tree layout with iterative spacing refinement.

    Algorithm
    ---------
    1. Place objects in fixed horizontal level-bands (same Y for each level).
    2. Keep the hierarchy root at the top-left and layout each subtree from
       left-to-right (tree view format is mandatory).
    3. Detect same-level overlaps and connectors whose horizontal segment
       would pass through another box.
    4. If conflicts exist, widen the horizontal spacing and redo (max 3 passes).
    """
    # Group by level
    level_groups = {}
    for cls in class_names:
        level_groups.setdefault(levels.get(cls, 0), []).append(cls)

    def make_level_y():
        ly = {}
        cy = MARGIN
        for lvl in sorted(level_groups):
            ly[lvl] = cy
            cy += max(boxes[c]['height'] for c in level_groups[lvl]) + spacing_y
        return ly

    def do_layout(sx):
        """One full top-left anchored placement pass with spacing sx."""
        level_y = make_level_y()
        memo = {}

        def sw(name):
            """Occupied width of name's subtree using current sibling spacing rules."""
            if name in memo:
                return memo[name]
            children = parent_children.get(name, [])
            if not children:
                v = boxes[name]['width']
            else:
                lvl = levels.get(name, 0)
                child_left = 0.0
                max_right = boxes[name]['width']
                for child in children:
                    child_span = sw(child)
                    max_right = max(max_right, child_left + child_span)

                    if lvl <= 0:
                        # Top-level branches reserve full child branch span.
                        child_left += child_span + sx
                    else:
                        # Inner branches compact by child box width.
                        child_left += boxes[child]['width'] + sx
                v = max_right
            memo[name] = v
            return v

        out = {}

        def place(name, left_x):
            """Place name at left_x, then place children left-to-right below it."""
            lvl = levels.get(name, 0)
            out[name] = {
                'x':          left_x,
                'y':          level_y.get(lvl, MARGIN),
                'width':      boxes[name]['width'],
                'height':     boxes[name]['height'],
                'has_members':  boxes[name]['has_members'],
                'has_functions': boxes[name]['has_functions'],
                'class_def':  boxes[name]['class_def'],
                'element_type': boxes[name]['element_type'],
            }
            children = parent_children.get(name, [])
            if not children:
                return
            xl = left_x
            lvl = levels.get(name, 0)
            for child in children:
                place(child, xl)
                if lvl <= 0:
                    # At top levels, reserve full subtree width so independent
                    # branches do not overlap each other.
                    xl += sw(child) + sx
                else:
                    # Inside a branch, compact siblings by their own box width
                    # to avoid unnecessary horizontal expansion.
                    xl += boxes[child]['width'] + sx

        # Place each root tree left-to-right
        roots = [c for c in class_names if c not in claimed_children]
        cur_x = MARGIN
        for root in roots:
            root_sw = sw(root)
            place(root, cur_x)
            cur_x += root_sw + sx

        # Orphaned nodes not reached by any tree
        for cls in class_names:
            if cls not in out:
                lvl = levels.get(cls, 0)
                out[cls] = {
                    'x':          cur_x,
                    'y':          level_y.get(lvl, MARGIN),
                    'width':      boxes[cls]['width'],
                    'height':     boxes[cls]['height'],
                    'has_members':  boxes[cls]['has_members'],
                    'has_functions': boxes[cls]['has_functions'],
                    'class_def':  boxes[cls]['class_def'],
                    'element_type': boxes[cls]['element_type'],
                }
                cur_x += boxes[cls]['width'] + sx
        return out

    # ----- Phase 1: initial placement -----
    current_sx = base_sx
    positions = do_layout(current_sx)

    # ----- Phases 2-4: iterative refinement -----
    MAX_ITER = 3
    for _iter in range(MAX_ITER):
        extra_needed = 0.0
        desired_gap = max(base_sx * 0.25, 30)

        # Check 1: same-level boxes that are too close together (or overlapping)
        level_nodes = {}
        for cls, pos in positions.items():
            level_nodes.setdefault(levels.get(cls, 0), []).append((cls, pos))

        for lvl, lnodes in level_nodes.items():
            lnodes.sort(key=lambda t: t[1]['x'])
            for i in range(len(lnodes) - 1):
                _, a = lnodes[i]
                _, b = lnodes[i + 1]
                gap = b['x'] - (a['x'] + a['width'])
                if gap < desired_gap:
                    extra_needed = max(extra_needed, desired_gap - gap + 10)

        # Check 2: connector horizontal mid-segments blocked by an intermediate box
        for rel in diagram.relationships:
            sp = positions.get(rel.source)
            tp = positions.get(rel.target)
            if not sp or not tp:
                continue
            if sp['y'] >= tp['y']:
                continue  # same-level or upward – skip
            s_cx = sp['x'] + sp['width'] / 2
            t_cx = tp['x'] + tp['width'] / 2
            if abs(s_cx - t_cx) < 5:
                continue  # nearly-vertical connector needs no horizontal segment
            mid_y = (sp['y'] + sp['height'] + tp['y']) / 2
            x_lo = min(s_cx, t_cx) - 5
            x_hi = max(s_cx, t_cx) + 5
            for obs_cls, obs in positions.items():
                if obs_cls in (rel.source, rel.target):
                    continue
                if (obs['y'] < mid_y < obs['y'] + obs['height'] and
                        obs['x'] < x_hi and obs['x'] + obs['width'] > x_lo):
                    extra_needed = max(extra_needed, desired_gap + 15)

        if extra_needed < 5:
            break  # converged

        current_sx += extra_needed
        positions = do_layout(current_sx)

    # Apply source-cluster alignment for filtered views (post-processing)
    positions = _apply_source_cluster_alignment(positions, diagram, levels, current_sx)

    return positions


def _layout_classes_tree_based(diagram, model, verbosity="High"):
    """Tree-centered layout for diagonal/mixed routing.

    Parents are centred directly above their children subtrees so that
    hierarchy connectors run in straight vertical (or near-vertical) lines
    instead of long diagonals.  An iterative spacing pass widens the layout
    when connectors would otherwise route through other boxes.
    """
    class_names, boxes = _collect_and_size_classes(diagram, model, verbosity)
    if not class_names:
        return {}

    levels = _calculate_abstraction_level(diagram)
    if verbosity != "High":
        print(f"DEBUG: Calculated levels = {levels}")

    parent_children, claimed_children = _build_spanning_forest(diagram, levels)

    required_spacing = _calculate_required_spacing(diagram, verbosity)
    spacing_x = max(required_spacing, CLASS_SPACING_X + 30)
    spacing_y = CLASS_SPACING_Y + 15

    return _aligned_tree_layout(
        class_names, boxes, levels, parent_children, claimed_children,
        spacing_x, spacing_y, diagram
    )


def _layout_classes_orthogonal(diagram, model, verbosity="High"):
    """Tree-centered layout for orthogonal (right-angle) routing.

    Parents are centred directly above their children subtrees so that
    hierarchy connectors become straight vertical lines.  Extra horizontal
    spacing accommodates the side-track segments needed for right-angle
    routing.  An iterative refinement pass widens the layout further when
    connector horizontal segments would otherwise pass through other boxes.

    Returns dict: class_name -> {x, y, width, height, ...}
    """
    class_names, boxes = _collect_and_size_classes(diagram, model, verbosity)
    if not class_names:
        return {}

    levels = _calculate_abstraction_level(diagram)
    parent_children, claimed_children = _build_spanning_forest(diagram, levels)

    required_spacing = _calculate_required_spacing(diagram, verbosity)
    # Extra spacing compared to diagonal mode to accommodate routing tracks
    spacing_x = max(required_spacing, CLASS_SPACING_X + 40)
    spacing_y = CLASS_SPACING_Y + 30

    return _aligned_tree_layout(
        class_names, boxes, levels, parent_children, claimed_children,
        spacing_x, spacing_y, diagram
    )


def _layout_classes_uml_standard(diagram, model, verbosity="High", routing="diagonal"):
    """Select layout strategy based on routing mode.
    
    Args:
        diagram: ClassDiagramDef with relationships
        model: Model with class definitions
        verbosity: Verbosity level for box sizing
        routing: Routing mode - "diagonal", "orthogonal", or "mixed"
    
    Returns:
        Dictionary of class positions
    """
    # Temporary policy: class diagrams use orthogonal routing only.
    return _layout_classes_orthogonal(diagram, model, verbosity)


def _layout_classes(diagram, model, verbosity="High"):
    """Compute positions for each class box in the diagram.
    
    Returns dict: class_name -> {x, y, width, height, has_members, has_functions, class_def, element_type}
    
    Layout Strategy:
    - Group closely related objects (ownership hierarchy) together
    - Parent object is placed before its children in the layout
    - This ensures connectors to children don't pass through unrelated objects
    """
    # Collect unique class names from relationships
    class_names = []
    seen = set()
    for rel in diagram.relationships:
        if rel.source not in seen:
            class_names.append(rel.source)
            seen.add(rel.source)
        if rel.target not in seen:
            class_names.append(rel.target)
            seen.add(rel.target)
    
    if not class_names:
        return {}
    
    # Reorder class names: place children immediately after their owner
    # Build a map of source -> [targets]
    children_map = {}
    for rel in diagram.relationships:
        if rel.source not in children_map:
            children_map[rel.source] = []
        if rel.target not in children_map[rel.source]:
            children_map[rel.source].append(rel.target)
    
    # Rebuild class_names with children clustered after parents
    reordered = []
    processed = set()
    
    for name in class_names:
        if name in processed:
            continue
        
        # Add the parent
        reordered.append(name)
        processed.add(name)
        
        # Add all its children immediately after
        if name in children_map:
            for child in children_map[name]:
                if child not in processed:
                    reordered.append(child)
                    processed.add(child)
    
    # Add any remaining unprocessed names (orphans)
    for name in class_names:
        if name not in processed:
            reordered.append(name)
    
    class_names = reordered
    
    # Compute sizes for each class
    boxes = {}
    for name in class_names:
        class_def = model.get_class(name)
        element_type = diagram.element_types.get(name, "class")
        w, h, has_m, has_f = _compute_class_box_size(name, class_def, verbosity, element_type)
        boxes[name] = {
            'width': w, 'height': h,
            'has_members': has_m, 'has_functions': has_f,
            'class_def': class_def, 'element_type': element_type
        }
    
    # Simple grid layout: arrange in rows
    # Try to keep roughly square aspect ratio
    n = len(class_names)
    cols = max(1, min(n, int(n ** 0.5) + 1))
    
    # Place classes in grid
    # Calculate required spacing based on connector text dimensions
    required_spacing = _calculate_required_spacing(diagram, verbosity)
    spacing_x = max(required_spacing, CLASS_SPACING_X + (15 if verbosity != "High" else 30))
    spacing_y = CLASS_SPACING_Y + (10 if verbosity != "High" else 15)
    
    x = MARGIN
    y = MARGIN
    col = 0
    row_height = 0
    
    for name in class_names:
        box = boxes[name]
        box['x'] = x
        box['y'] = y
        row_height = max(row_height, box['height'])
        
        col += 1
        if col >= cols:
            col = 0
            x = MARGIN
            y += row_height + spacing_y
            row_height = 0
        else:
            x += box['width'] + spacing_x
    
    return boxes


def _render_class_box(box_info, class_name, box_color=None):
    """Render a single UML element box as SVG elements.
    
    Supports class, component, package, and object element types.
    
    Args:
        box_info: Dictionary with box layout info (x, y, width, height, etc.)
        class_name: Name of the class to render
        box_color: Optional dict with 'light_fill' and 'dark_stroke' color overrides
    """
    x = box_info['x']
    y = box_info['y']
    w = box_info['width']
    h = box_info['height']
    class_def = box_info['class_def']
    has_members = box_info['has_members']
    has_functions = box_info['has_functions']
    element_type = box_info.get('element_type', 'class')
    
    style = ELEMENT_STYLES.get(element_type, ELEMENT_STYLES["class"])
    fill = style["fill"]
    stroke = style["stroke"]
    stereotype = style["stereotype"]
    
    # Use assigned colors if provided
    if box_color:
        fill = box_color.get("light_fill", fill)
        stroke = box_color.get("dark_stroke", stroke)
    
    parts = []
    
    if element_type == "package":
        # Package: tabbed folder shape
        tab_w = min(w * 0.4, 80)
        tab_h = 16
        # Tab
        parts.append(f'  <rect x="{x}" y="{y}" width="{tab_w}" height="{tab_h}" '
                     f'fill="{fill}" stroke="{stroke}" stroke-width="1.5" rx="2"/>')
        # Body (below tab)
        parts.append(f'  <rect x="{x}" y="{y + tab_h}" width="{w}" height="{h - tab_h}" '
                     f'fill="{fill}" stroke="{stroke}" stroke-width="1.5" rx="2"/>')
    elif element_type == "component":
        # Component: rectangle with small component icon
        parts.append(f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" '
                     f'fill="{fill}" stroke="{stroke}" stroke-width="1.5" rx="2"/>')
        # Component icon (two small rectangles on left edge)
        icon_x = x + 6
        icon_y = y + 6
        icon_w = 12
        icon_h = 6
        parts.append(f'  <rect x="{icon_x - 3}" y="{icon_y}" width="{icon_w}" height="{icon_h}" '
                     f'fill="{fill}" stroke="{stroke}" stroke-width="1"/>')
        parts.append(f'  <rect x="{icon_x - 3}" y="{icon_y + icon_h + 3}" width="{icon_w}" height="{icon_h}" '
                     f'fill="{fill}" stroke="{stroke}" stroke-width="1"/>')
    else:
        # Class or Object: standard rectangle
        parts.append(f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" '
                     f'fill="{fill}" stroke="{stroke}" stroke-width="1.5" rx="2"/>')
    
    # Track current Y position for content rendering
    content_y = y + CLASS_BOX_PADDING_Y
    
    # Stereotype text (for component and package)
    if stereotype:
        content_y += MEMBER_FONT_SIZE
        parts.append(f'  <text x="{x + w / 2}" y="{content_y}" '
                     f'font-family="{FONT_FAMILY}" font-size="{MEMBER_FONT_SIZE}" '
                     f'text-anchor="middle" fill="#666">'
                     f'{_escape_xml(stereotype)}</text>')
        content_y += 2
    
    # Class/element name (bold, centered)
    content_y += FONT_SIZE
    name_x = x + w / 2
    # Object names are underlined
    text_decoration = ' text-decoration="underline"' if element_type == "object" else ''
    parts.append(f'  <text x="{name_x}" y="{content_y}" '
                 f'font-family="{FONT_FAMILY}" font-size="{FONT_SIZE}" '
                 f'font-weight="bold" text-anchor="middle" fill="#333"'
                 f'{text_decoration}>'
                 f'{_escape_xml(class_name)}</text>')
    
    section_y = content_y + CLASS_BOX_PADDING_Y
    
    if class_def:
        # Members section
        if has_members:
            # Separator line
            parts.append(f'  <line x1="{x}" y1="{section_y}" x2="{x + w}" y2="{section_y}" '
                         f'stroke="{stroke}" stroke-width="1"/>')
            section_y += CLASS_SECTION_SPACING
            
            for m in class_def.members:
                section_y += ROW_HEIGHT
                text_x = x + CLASS_BOX_PADDING_X
                parts.append(f'  <text x="{text_x}" y="{section_y - 3}" '
                             f'font-family="{FONT_FAMILY}" font-size="{MEMBER_FONT_SIZE}" '
                             f'fill="#555">{_escape_xml(m.name)}</text>')
            section_y += CLASS_BOX_PADDING_Y
        
        # Functions section
        if has_functions:
            # Separator line
            parts.append(f'  <line x1="{x}" y1="{section_y}" x2="{x + w}" y2="{section_y}" '
                         f'stroke="{stroke}" stroke-width="1"/>')
            section_y += CLASS_SECTION_SPACING
            
            for f in class_def.functions:
                section_y += ROW_HEIGHT
                vis = "+" if f.visibility == "public" else "-" if f.visibility == "private" else "#"
                text_x = x + CLASS_BOX_PADDING_X
                parts.append(f'  <text x="{text_x}" y="{section_y - 3}" '
                             f'font-family="{FONT_FAMILY}" font-size="{MEMBER_FONT_SIZE}" '
                             f'fill="#555">{_escape_xml(vis + " " + f.name)}</text>')
            section_y += CLASS_BOX_PADDING_Y
    
    return '\n'.join(parts)


def _get_connection_points(box, other_box):
    """Find the best edge point on `box` facing toward `other_box`.
    
    Returns (x, y) on the border of `box`.
    """
    bx = box['x'] + box['width'] / 2
    by = box['y'] + box['height'] / 2
    ox = other_box['x'] + other_box['width'] / 2
    oy = other_box['y'] + other_box['height'] / 2
    
    dx = ox - bx
    dy = oy - by
    
    if abs(dx) < 1 and abs(dy) < 1:
        # Same position, default to right side
        return box['x'] + box['width'], by
    
    # Determine which edge to use based on angle
    if abs(dx) * box['height'] > abs(dy) * box['width']:
        # Left or right edge
        if dx > 0:
            return box['x'] + box['width'], by  # Right edge
        else:
            return box['x'], by  # Left edge
    else:
        # Top or bottom edge
        if dy > 0:
            return bx, box['y'] + box['height']  # Bottom edge
        else:
            return bx, box['y']  # Top edge


def _render_arrow_marker_defs(box_colors=None):
    """Render SVG marker definitions for arrow types with optional color variants.
    
    Args:
        box_colors: Optional dict of class_name -> {light_fill, dark_stroke}
                   If provided, generates colored markers for each dark_stroke color used
    
    Returns:
        SVG marker definitions as a string
    """
    direction_angles = {
        'right': '0',
        'down': '90',
        'left': '180',
        'up': '270',
    }

    def _directional_marker_variants(marker_id, view_box, ref_x, ref_y, marker_width,
                                     marker_height, path_d, stroke, stroke_width,
                                     fill='none'):
        variants = []
        for direction, angle in direction_angles.items():
            variants.append(
                f'''    <marker id="{marker_id}-{direction}" viewBox="{view_box}" refX="{ref_x}" refY="{ref_y}"
            markerWidth="{marker_width}" markerHeight="{marker_height}" orient="{angle}">
      <path d="{path_d}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"/>
    </marker>
'''
            )
        return ''.join(variants)

    # Always include base markers
    markers = '''  <defs>
    <!-- Open arrowhead (directed association) -->
    <marker id="arrow-open" viewBox="0 0 10 10" refX="10" refY="5"
            markerWidth="8" markerHeight="8" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10" fill="none" stroke="#555" stroke-width="1.5"/>
    </marker>
    <!-- Closed triangle (generalization/realization) -->
    <marker id="arrow-triangle" viewBox="0 0 10 10" refX="10" refY="5"
            markerWidth="10" markerHeight="10" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 Z" fill="white" stroke="#555" stroke-width="1.2"/>
    </marker>
    <!-- Filled diamond (composition) -->
    <marker id="diamond-filled" viewBox="0 0 12 8" refX="12" refY="4"
            markerWidth="12" markerHeight="8" orient="auto-start-reverse">
      <path d="M 0 4 L 6 0 L 12 4 L 6 8 Z" fill="#555" stroke="#555" stroke-width="1"/>
    </marker>
    <!-- Open diamond (aggregation) -->
    <marker id="diamond-open" viewBox="0 0 12 8" refX="12" refY="4"
            markerWidth="12" markerHeight="8" orient="auto-start-reverse">
      <path d="M 0 4 L 6 0 L 12 4 L 6 8 Z" fill="white" stroke="#555" stroke-width="1"/>
    </marker>
'''

    markers += _directional_marker_variants('arrow-open', '0 0 10 10', '10', '5', '8', '8', 'M 0 0 L 10 5 L 0 10', '#555', '1.5')
    markers += _directional_marker_variants('arrow-triangle', '0 0 10 10', '10', '5', '10', '10', 'M 0 0 L 10 5 L 0 10 Z', '#555', '1.2', fill='white')
    markers += _directional_marker_variants('diamond-filled', '0 0 12 8', '12', '4', '12', '8', 'M 0 4 L 6 0 L 12 4 L 6 8 Z', '#555', '1', fill='#555')
    markers += _directional_marker_variants('diamond-open', '0 0 12 8', '12', '4', '12', '8', 'M 0 4 L 6 0 L 12 4 L 6 8 Z', '#555', '1', fill='white')
    
    # Generate colored marker variants if colors are provided
    if box_colors:
        # Collect unique stroke colors with their COLOR_PALETTE indices (must match _get_arrow_style)
        unique_colors_with_indices = {}
        for color_dict in box_colors.values():
            stroke = color_dict.get("dark_stroke", "#555")
            if stroke not in unique_colors_with_indices and stroke != "#555":
                # Find this color's index in COLOR_PALETTE (to match _get_arrow_style logic)
                for idx, palette_color in enumerate(COLOR_PALETTE):
                    if palette_color["dark_stroke"] == stroke:
                        unique_colors_with_indices[stroke] = idx
                        break
        
        # Generate colored marker variants using COLOR_PALETTE indices
        for stroke_color, color_idx in unique_colors_with_indices.items():
            # Colored filled diamond
            markers += f'''    <!-- Filled diamond - Color {color_idx} -->
    <marker id="diamond-filled-{color_idx}" viewBox="0 0 12 8" refX="12" refY="4"
            markerWidth="12" markerHeight="8" orient="auto-start-reverse">
      <path d="M 0 4 L 6 0 L 12 4 L 6 8 Z" fill="{stroke_color}" stroke="{stroke_color}" stroke-width="1"/>
    </marker>
    <!-- Open diamond - Color {color_idx} -->
    <marker id="diamond-open-{color_idx}" viewBox="0 0 12 8" refX="12" refY="4"
            markerWidth="12" markerHeight="8" orient="auto-start-reverse">
      <path d="M 0 4 L 6 0 L 12 4 L 6 8 Z" fill="white" stroke="{stroke_color}" stroke-width="1.5"/>
    </marker>
    <!-- Arrow open - Color {color_idx} -->
    <marker id="arrow-open-{color_idx}" viewBox="0 0 10 10" refX="10" refY="5"
            markerWidth="8" markerHeight="8" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10" fill="none" stroke="{stroke_color}" stroke-width="1.5"/>
    </marker>
'''
            markers += _directional_marker_variants(f'diamond-filled-{color_idx}', '0 0 12 8', '12', '4', '12', '8', 'M 0 4 L 6 0 L 12 4 L 6 8 Z', stroke_color, '1', fill=stroke_color)
            markers += _directional_marker_variants(f'diamond-open-{color_idx}', '0 0 12 8', '12', '4', '12', '8', 'M 0 4 L 6 0 L 12 4 L 6 8 Z', stroke_color, '1.5', fill='white')
            markers += _directional_marker_variants(f'arrow-open-{color_idx}', '0 0 10 10', '10', '5', '8', '8', 'M 0 0 L 10 5 L 0 10', stroke_color, '1.5')
    
    markers += '  </defs>'
    return markers

def _get_arrow_style(arrow, stroke_color=None):
    """Return (stroke_dasharray, marker_start, marker_end) for the given arrow type.
    
    Args:
        arrow: Arrow type string (e.g., '→', '◆--')
        stroke_color: Optional stroke color to use colored markers
    
    Returns:
        (stroke_dasharray, marker_start, marker_end)
    """
    solid = "none"
    dashed = "6,4"
    
    # If stroke_color is provided and not default gray, use its COLOR_PALETTE index
    color_suffix = ""
    if stroke_color and stroke_color != "#555":
        # Map color to its index in COLOR_PALETTE (must match _render_arrow_marker_defs)
        for idx, color_def in enumerate(COLOR_PALETTE):
            if color_def["dark_stroke"] == stroke_color:
                color_suffix = f"-{idx}"
                break
    
    styles = {
        # Structural (solid)
        '--':    (solid, None, None),
        '-->':   (solid, None, f'arrow-open{color_suffix}' if color_suffix else 'arrow-open'),
        '<--':   (solid, f'arrow-open{color_suffix}' if color_suffix else 'arrow-open', None),
        '<-->':  (solid, f'arrow-open{color_suffix}' if color_suffix else 'arrow-open', f'arrow-open{color_suffix}' if color_suffix else 'arrow-open'),
        '--\u25b7':   (solid, None, 'arrow-triangle'),        # --▷
        '\u25c1--':   (solid, 'arrow-triangle', None),        # ◁--
        '--\u25c6':   (solid, None, f'diamond-filled{color_suffix}' if color_suffix else 'diamond-filled'),        # --◆
        '\u25c6--':   (solid, f'diamond-filled{color_suffix}' if color_suffix else 'diamond-filled', None),        # ◆--
        '--\u25c7':   (solid, None, f'diamond-open{color_suffix}' if color_suffix else 'diamond-open'),          # --◇
        '\u25c7--':   (solid, f'diamond-open{color_suffix}' if color_suffix else 'diamond-open', None),          # ◇--
        # Behavioral (dashed)
        '..>':   (dashed, None, f'arrow-open{color_suffix}' if color_suffix else 'arrow-open'),
        '<..':   (dashed, f'arrow-open{color_suffix}' if color_suffix else 'arrow-open', None),
        '..\u25b7':   (dashed, None, 'arrow-triangle'),      # ..▷
        '\u25c1..':   (dashed, 'arrow-triangle', None),      # ◁..
    }
    
    return styles.get(arrow, (solid, None, f'arrow-open{color_suffix}' if color_suffix else 'arrow-open'))


def _render_connectors_with_planner(planner, boxes, box_colors=None, verbosity_level="High", layers_filter=None):
    """Render all connectors using the grid-based connector planner system.
    
    Handles text placement for:
    - Direct paths (single line): horizontal or diagonal positioning
    - Multi-segment paths (V-H-V): distributed text on segments
    
    Args:
        planner: ConnectorPlanner with all connectors planned
        boxes: Dictionary of class box positions and dimensions
        box_colors: Optional dict of class_name -> {light_fill, dark_stroke}
        verbosity_level: "Low", "Normal", or "High" for multiplicity display
        layers_filter: Optional list of layers to include
    
    Returns:
        SVG string with all connector lines
    """
    parts = []

    def _nudge_text_outside_boxes(x: float, y: float) -> Tuple[float, float]:
        """Move text out of any class box if it lands inside one."""
        tx, ty = x, y
        for _ in range(8):
            moved = False
            for box in boxes.values():
                left = box['x'] - 4
                right = box['x'] + box['width'] + 4
                top = box['y'] - 4
                bottom = box['y'] + box['height'] + 4
                if left <= tx <= right and top <= ty <= bottom:
                    # Push text above or below the box depending on nearest side.
                    dist_top = abs(ty - top)
                    dist_bottom = abs(bottom - ty)
                    if dist_top <= dist_bottom:
                        ty = top - 8
                    else:
                        ty = bottom + 14
                    moved = True
                    break
            if not moved:
                break
        return tx, ty
    
    # Get planned connectors (filtered by layer if needed)
    connectors = planner.get_connectors(layer_filter=None)
    
    if layers_filter is not None:
        connectors = [c for c in connectors if not c.layer or c.layer in layers_filter]
    
    for connector in connectors:
        if connector.source_name not in boxes or connector.target_name not in boxes:
            continue
        
        # Get connector color from source box (use source object's dark color)
        connector_color = "#555"  # Default fallback
        if box_colors and connector.source_name in box_colors:
            connector_color = box_colors[connector.source_name].get("dark_stroke", "#555")
        
        dash, marker_start, marker_end = _get_arrow_style(connector.arrow_type, connector_color)
        path_points = _path_points_from_connector(connector)
        end_direction = _final_path_direction(path_points)
        rendered_marker_end = _directed_marker_id(marker_end, end_direction)
        
        # Render connector path
        if connector.path_type == "direct":
            # Simple line (horizontal or diagonal)
            is_horizontal = abs(connector.source_y - connector.target_y) < 2

            path_d = (
                f"M {connector.source_x} {connector.source_y} "
                f"L {connector.target_x} {connector.target_y}"
            )
            parts.append(f'  <path d="{path_d}" fill="none" '
                        f'stroke="{connector_color}" stroke-width="1.5"')
            if dash != "none":
                parts.append(f' stroke-dasharray="{dash}"')
            if marker_start:
                parts.append(f' marker-start="url(#{marker_start})"')
            if rendered_marker_end:
                parts.append(f' marker-end="url(#{rendered_marker_end})"')
            parts.append('/>')
            
            # Text placement for direct paths
            if verbosity_level == "High":
                if is_horizontal:
                    # Horizontal straight connector: keep multiplicity near endpoints
                    # and place label near the source after the source multiplicity.
                    direction = 1 if connector.target_x >= connector.source_x else -1
                    base_y = min(connector.source_y, connector.target_y) - 8

                    if connector.src_mult:
                        src_x = connector.source_x + direction * 10
                        src_anchor = 'start' if direction > 0 else 'end'
                        src_x, src_y = _nudge_text_outside_boxes(src_x, base_y)
                        parts.append(f'  <text x="{src_x}" y="{src_y}" font-family="{CONNECTOR_FONT_FAMILY}" '
                                     f'font-size="11" fill="#666" text-anchor="{src_anchor}">'
                                     f'{_escape_xml(connector.src_mult)}</text>')

                    if connector.label:
                        label_gap = 10 + ((len(connector.src_mult or "") + 2) * CONNECTOR_CHAR_WIDTH)
                        label_x = connector.source_x + direction * label_gap
                        label_anchor = 'start' if direction > 0 else 'end'
                        label_x, label_y = _nudge_text_outside_boxes(label_x, base_y)
                        parts.append(f'  <text x="{label_x}" y="{label_y}" font-family="{FONT_FAMILY}" '
                                     f'font-size="11" font-style="italic" fill="#444" text-anchor="{label_anchor}">'
                                     f'{_escape_xml(connector.label)}</text>')

                    if connector.tgt_mult:
                        tgt_x = connector.target_x - direction * 10
                        tgt_anchor = 'end' if direction > 0 else 'start'
                        tgt_x, tgt_y = _nudge_text_outside_boxes(tgt_x, base_y)
                        parts.append(f'  <text x="{tgt_x}" y="{tgt_y}" font-family="{CONNECTOR_FONT_FAMILY}" '
                                     f'font-size="11" fill="#666" text-anchor="{tgt_anchor}">'
                                     f'{_escape_xml(connector.tgt_mult)}</text>')
                else:
                    # Diagonal line: determine if vertical or horizontal-dominant
                    dx = abs(connector.target_x - connector.source_x)
                    dy = abs(connector.target_y - connector.source_y)
                    is_vertical_dominant = dy > dx
                    
                    if is_vertical_dominant:
                        # Nearly vertical: text to the right
                        if connector.src_mult:
                            mx = connector.source_x + 8
                            my = connector.source_y + (connector.target_y - connector.source_y) * 0.2
                            mx, my = _nudge_text_outside_boxes(mx, my)
                            parts.append(f'  <text x="{mx}" y="{my}" font-family="{CONNECTOR_FONT_FAMILY}" '
                                         f'font-size="11" fill="#666" text-anchor="start">'
                                         f'{_escape_xml(connector.src_mult)}</text>')
                        
                        if connector.label:
                            mx = connector.source_x + 8
                            my = (connector.source_y + connector.target_y) / 2
                            mx, my = _nudge_text_outside_boxes(mx, my)
                            parts.append(f'  <text x="{mx}" y="{my}" font-family="{FONT_FAMILY}" '
                                         f'font-size="11" font-style="italic" fill="#444" text-anchor="start">'
                                         f'{_escape_xml(connector.label)}</text>')
                        
                        if connector.tgt_mult:
                            mx = connector.target_x + 8
                            my = connector.target_y + (connector.source_y - connector.target_y) * 0.2
                            mx, my = _nudge_text_outside_boxes(mx, my)
                            parts.append(f'  <text x="{mx}" y="{my}" font-family="{CONNECTOR_FONT_FAMILY}" '
                                         f'font-size="11" fill="#666" text-anchor="start">'
                                         f'{_escape_xml(connector.tgt_mult)}</text>')
                    else:
                        # Nearly horizontal diagonal: text positioned ABOVE the line as single formatted string
                        # Format: [arrow]  [src_mult]  [label]  [tgt_mult]
                        # Example: ◇--  1  contains  0.*
                        
                        src_mult_str = connector.src_mult if connector.src_mult else ""
                        label_str = connector.label if connector.label else ""
                        tgt_mult_str = connector.tgt_mult if connector.tgt_mult else ""
                        
                        # Build single formatted text string with 2-space gaps (no arrow symbol - already rendered graphically)
                        total_text = f"{src_mult_str}  {label_str}  {tgt_mult_str}"
                        
                        # Calculate text width and center it on the connector
                        text_width = len(total_text) * CONNECTOR_CHAR_WIDTH
                        line_center_x = (connector.source_x + connector.target_x) / 2
                        text_start_x = line_center_x - (text_width / 2)
                        text_y = min(connector.source_y, connector.target_y) - 8  # ABOVE the line (consistent with orthogonal)
                        text_start_x, text_y = _nudge_text_outside_boxes(text_start_x, text_y)
                        
                        # Render as single text element
                        parts.append(f'  <text x="{text_start_x}" y="{text_y}" font-family="{CONNECTOR_FONT_FAMILY}" '
                                     f'font-size="11" fill="#666" text-anchor="start">'
                                     f'{_escape_xml(total_text)}</text>')
            elif connector.label:
                # No multiplicity, just label
                lx = (connector.source_x + connector.target_x) / 2
                ly = (connector.source_y + connector.target_y) / 2 - 3
                parts.append(f'  <text x="{lx}" y="{ly}" font-family="{FONT_FAMILY}" '
                             f'font-size="11" font-style="italic" fill="#444" text-anchor="middle">'
                             f'{_escape_xml(connector.label)}</text>')
        else:
            # Multi-segment path (V-H-V orthogonal routing)
            if connector.segments:
                path_d = f"M {connector.source_x} {connector.source_y}"
                for x, y in path_points[1:]:
                    path_d += f" L {x} {y}"
                
                parts.append(f'  <path d="{path_d}" fill="none" stroke="{connector_color}" stroke-width="1.5"')
                if dash != "none":
                    parts.append(f' stroke-dasharray="{dash}"')
                if marker_start:
                    parts.append(f' marker-start="url(#{marker_start})"')
                if rendered_marker_end:
                    parts.append(f' marker-end="url(#{rendered_marker_end})"')
                parts.append('/>')
                
                # Text placement for multi-segment paths
                # Analyze segments to determine if V-H-V or other pattern
                if verbosity_level == "High" and len(connector.segments) >= 2:
                    path_points = [(connector.source_x, connector.source_y)] + list(connector.segments)
                    if path_points[-1] != (connector.target_x, connector.target_y):
                        path_points.append((connector.target_x, connector.target_y))

                    first_seg = (path_points[0], path_points[1])
                    last_seg = (path_points[-2], path_points[-1])

                    horizontal_seg = None
                    for i in range(len(path_points) - 1):
                        p1 = path_points[i]
                        p2 = path_points[i + 1]
                        if abs(p1[1] - p2[1]) < 1:
                            horizontal_seg = (p1, p2)
                            break
                    
                    if horizontal_seg is not None:
                        (hx1, hy1), (hx2, hy2) = horizontal_seg
                        src_text_x = connector.source_x + 8
                        src_text_y = connector.source_y - 8
                        src_text_anchor = 'start'

                        # Place source multiplicity very close to the source endpoint.
                        if connector.src_mult:
                            if abs(first_seg[0][1] - first_seg[1][1]) < 1:
                                direction = 1 if first_seg[1][0] >= first_seg[0][0] else -1
                                text_x = connector.source_x + direction * 10
                                text_y = connector.source_y - 8
                                anchor = 'start' if direction > 0 else 'end'
                            else:
                                text_x = connector.source_x + 8
                                text_y = connector.source_y + (hy1 - connector.source_y) * 0.3
                                anchor = 'start'
                            src_text_x = text_x
                            src_text_y = text_y
                            src_text_anchor = anchor
                            text_x, text_y = _nudge_text_outside_boxes(text_x, text_y)
                            parts.append(f'  <text x="{text_x}" y="{text_y}" '
                                         f'font-family="{CONNECTOR_FONT_FAMILY}" font-size="11" '
                                         f'fill="#666" text-anchor="{anchor}">'
                                         f'{_escape_xml(connector.src_mult)}</text>')

                        # Place connector label near the source after source multiplicity.
                        if connector.label:
                            lx, ly, anchor = _source_label_anchor(connector, path_points)
                            lx, ly = _nudge_text_outside_boxes(lx, ly)
                            parts.append(f'  <text x="{lx}" y="{ly}" font-family="{FONT_FAMILY}" '
                                         f'font-size="11" font-style="italic" fill="#444" text-anchor="{anchor}">'
                                         f'{_escape_xml(connector.label)}</text>')

                        # Place target multiplicity close to the target endpoint.
                        if connector.tgt_mult:
                            if abs(last_seg[0][1] - last_seg[1][1]) < 1:
                                direction = 1 if last_seg[1][0] >= last_seg[0][0] else -1
                                text_x = connector.target_x - direction * 10
                                text_y = connector.target_y - 8
                                anchor = 'end' if direction > 0 else 'start'
                            else:
                                text_x = connector.target_x + 8
                                text_y = hy1 + (connector.target_y - hy1) * 0.7
                                anchor = 'start'
                            text_x, text_y = _nudge_text_outside_boxes(text_x, text_y)
                            parts.append(f'  <text x="{text_x}" y="{text_y}" '
                                         f'font-family="{CONNECTOR_FONT_FAMILY}" font-size="11" '
                                         f'fill="#666" text-anchor="{anchor}">'
                                         f'{_escape_xml(connector.tgt_mult)}</text>')
                    else:
                        # Fallback: simple perpendicular positioning for multi-segment without clear horizontal
                        if connector.src_mult:
                            mx = connector.source_x + (connector.target_x - connector.source_x) * 0.12
                            my = connector.source_y + (connector.target_y - connector.source_y) * 0.12 + 12
                            text = f"{connector.src_mult}"
                            mx, my = _nudge_text_outside_boxes(mx, my)
                            parts.append(f'  <text x="{mx}" y="{my}" font-family="{CONNECTOR_FONT_FAMILY}" '
                                         f'font-size="11" fill="#666" text-anchor="middle">'
                                         f'{_escape_xml(text)}</text>')
                        
                        if connector.label:
                            lx, ly, anchor = _source_label_anchor(connector, path_points)
                            text = f"{connector.label}"
                            lx, ly = _nudge_text_outside_boxes(lx, ly)
                            parts.append(f'  <text x="{lx}" y="{ly}" font-family="{FONT_FAMILY}" '
                                         f'font-size="11" fill="#444" text-anchor="{anchor}">'
                                         f'{_escape_xml(text)}</text>')
                        
                        if connector.tgt_mult:
                            mx = connector.target_x + (connector.source_x - connector.target_x) * 0.20
                            my = connector.target_y + (connector.source_y - connector.target_y) * 0.20 + 12
                            text = f"{connector.tgt_mult}"
                            mx, my = _nudge_text_outside_boxes(mx, my)
                            parts.append(f'  <text x="{mx}" y="{my}" font-family="{CONNECTOR_FONT_FAMILY}" '
                                         f'font-size="11" fill="#666" text-anchor="middle">'
                                         f'{_escape_xml(text)}</text>')
                elif connector.label:
                    # Multi-segment with label only (no multiplicity)
                    lx, ly, anchor = _source_label_anchor(connector, path_points)

                    lx, ly = _nudge_text_outside_boxes(lx, ly)
                    
                    parts.append(f'  <text x="{lx}" y="{ly}" font-family="{FONT_FAMILY}" '
                                 f'font-size="11" font-style="italic" fill="#444" text-anchor="{anchor}">'
                                 f'{_escape_xml(connector.label)}</text>')
    
    return '\n'.join(parts)


def _calculate_connector_offsets(relationships):
    """Pre-calculate Y offsets for multi-connector scenarios.
    
    When multiple connectors originate from or target the same box,
    space them vertically to avoid overlap.
    
    Returns:
        Dict mapping id(rel) -> (src_offset_y, tgt_offset_y)
    """
    if not relationships:
        return {}
    
    # Group relationships by source and target
    by_source = {}
    by_target = {}
    
    for rel in relationships:
        if rel.source not in by_source:
            by_source[rel.source] = []
        by_source[rel.source].append(rel)
        
        if rel.target not in by_target:
            by_target[rel.target] = []
        by_target[rel.target].append(rel)
    
    # Calculate offsets for each relationship
    offsets = {}
    CONNECTOR_SPACING = 15  # Vertical spacing between connectors in pixels
    
    for rel in relationships:
        # Source offset: distribute vertically if multiple connectors from same source
        src_rels = by_source[rel.source]
        src_idx = src_rels.index(rel) if rel in src_rels else 0
        src_total = len(src_rels)
        if src_total > 1:
            # Center around the default connection point
            src_offset = (src_idx - (src_total - 1) / 2) * CONNECTOR_SPACING
        else:
            src_offset = 0
        
        # Target offset: distribute vertically if multiple connectors to same target
        tgt_rels = by_target[rel.target]
        tgt_idx = tgt_rels.index(rel) if rel in tgt_rels else 0
        tgt_total = len(tgt_rels)
        if tgt_total > 1:
            # Center around the default connection point
            tgt_offset = (tgt_idx - (tgt_total - 1) / 2) * CONNECTOR_SPACING
        else:
            tgt_offset = 0
        
        offsets[id(rel)] = (src_offset, tgt_offset)
    
    return offsets


def _arrow_has_marker(arrow, position="end"):
    """Check if an arrow has a marker at the specified position.
    
    Args:
        arrow: Arrow type string (e.g., '--', '-->',◆--', '--◆', etc.)
        position: "start" or "end"
    
    Returns:
        True if marker exists at the specified position, False otherwise
    """
    # Get style information
    dash, marker_start, marker_end = _get_arrow_style(arrow)
    
    if position == "start":
        return marker_start is not None
    else:  # position == "end"
        return marker_end is not None


def _calculate_grid_cell_position(point_y, grid_height=32):
    """Calculate which grid cell a Y coordinate falls into.
    
    Args:
        point_y: SVG Y coordinate
        grid_height: Height of each grid cell (default 32px = 2 line heights)
    
    Returns:
        Y coordinate of the center of that grid cell
    """
    grid_row = int(point_y / grid_height)
    grid_cell_y = grid_row * grid_height + grid_height / 2
    return grid_cell_y


def _render_multiplicity_at_grid_cells(rel, sx, sy, tx, ty, parts):
    """Render multiplicity text at grid cells instead of along connector line.
    
    Used when endpoints don't have markers. Places source multiplicity at
    source grid cell and target multiplicity at target grid cell.
    
    Args:
        rel: ClassRelationship with src_mult and tgt_mult
        sx, sy: Source connection point (x, y)
        tx, ty: Target connection point (x, y)
        parts: List to append SVG text elements to
    """
    # Grid parameters
    GRID_HEIGHT = 32  # pixels per grid row
    TEXT_OFFSET_X = -12  # pixels left of connector
    
    # Check which endpoints lack markers
    has_source_marker = _arrow_has_marker(rel.arrow, "start")
    has_target_marker = _arrow_has_marker(rel.arrow, "end")
    
    # Place source multiplicity at source grid cell if no marker
    if rel.src_mult and not has_source_marker:
        grid_y = _calculate_grid_cell_position(sy, GRID_HEIGHT)
        text_x = sx + TEXT_OFFSET_X
        text_y = grid_y
        parts.append(f'  <text x="{text_x}" y="{text_y}" font-family="{CONNECTOR_FONT_FAMILY}" '
                     f'font-size="11" fill="#666" text-anchor="end">'
                     f'{_escape_xml(rel.src_mult)}</text>')
    
    # Place target multiplicity at target grid cell if no marker
    if rel.tgt_mult and not has_target_marker:
        grid_y = _calculate_grid_cell_position(ty, GRID_HEIGHT)
        text_x = tx + TEXT_OFFSET_X
        text_y = grid_y
        parts.append(f'  <text x="{text_x}" y="{text_y}" font-family="{CONNECTOR_FONT_FAMILY}" '
                     f'font-size="11" fill="#666" text-anchor="end">'
                     f'{_escape_xml(rel.tgt_mult)}</text>')


def _render_relationship(rel, boxes, routing="diagonal", verbosity_level="High", 
                         connector_offsets=None):
    """Render a single relationship line between two class boxes.
    
    Routing modes:
      diagonal: straight line between connection points
      orthogonal: right-angle paths (horizontal-vertical-horizontal)
      mixed: use orthogonal for same-row, diagonal for different-row
    
    Args:
        rel: ClassRelationship to render
        boxes: Dictionary of class box positions and dimensions
        routing: Connection routing style
        verbosity_level: "Low", "Normal", or "High" - multiplicity only shown on High
        connector_offsets: Optional dict mapping id(rel) -> (src_offset_y, tgt_offset_y)
    """
    if rel.source not in boxes or rel.target not in boxes:
        return ''
    
    src_box = boxes[rel.source]
    tgt_box = boxes[rel.target]
    
    # Get connection points
    sx, sy = _get_connection_points(src_box, tgt_box)
    tx, ty = _get_connection_points(tgt_box, src_box)
    
    # Apply multi-connector offsets if provided
    # Only apply offsets perpendicular to the connection direction
    if connector_offsets and id(rel) in connector_offsets:
        src_offset, tgt_offset = connector_offsets[id(rel)]
        # Determine connection direction
        dx = tx - sx
        dy = ty - sy
        # If primarily vertical (|dy| > |dx|), apply horizontal offsets
        if abs(dy) > abs(dx):
            sx += src_offset
            tx += tgt_offset
        # If primarily horizontal (|dx| > |dy|), apply vertical offsets
        elif abs(dx) > abs(dy):
            sy += src_offset
            ty += tgt_offset
        # If roughly diagonal, apply as both (preserves original behavior)
        else:
            sy += src_offset
            ty += tgt_offset
    
    dash, marker_start, marker_end = _get_arrow_style(rel.arrow)
    
    parts = []
    
    use_orthogonal = (routing == "orthogonal" or 
                      (routing == "mixed" and abs(sy - ty) < src_box['height']))
    
    # Check if we need H separation (different X coordinates)
    needs_horizontal = abs(sx - tx) > 1
    
    if use_orthogonal and abs(sy - ty) > 1:
        if needs_horizontal:
            # Orthogonal routing: vertical-horizontal-vertical path (V-H-V)
            # Ensures at least 3 segments for clarity in multi-connector diagrams
            mid_y = (sy + ty) / 2
            path_d = f"M {sx} {sy} L {sx} {mid_y} L {tx} {mid_y} L {tx} {ty}"
        else:
            # Simple vertical line when no horizontal separation needed
            path_d = f"M {sx} {sy} L {tx} {ty}"
        attrs = f'd="{path_d}" fill="none" stroke="#555" stroke-width="1.5"'
        if dash != "none":
            attrs += f' stroke-dasharray="{dash}"'
        if marker_start:
            attrs += f' marker-start="url(#{marker_start})"'
        if marker_end:
            attrs += f' marker-end="url(#{marker_end})"'
        parts.append(f'  <path {attrs}/>')
        
        # Text placement for orthogonal connectors (only on High verbosity)
        if verbosity_level == "High":
            # Check if endpoints have markers for positioning decision
            has_source_marker = _arrow_has_marker(rel.arrow, "start")
            has_target_marker = _arrow_has_marker(rel.arrow, "end")
            
            if needs_horizontal:
                # V-H-V routing: vertical-horizontal-vertical path
                # Segment 1 (vertical sy->mid_y): source multiplicity on right
                if rel.src_mult:
                    if not has_source_marker:
                        # No marker: place in source grid cell
                        grid_y = _calculate_grid_cell_position(sy)
                        parts.append(f'  <text x="{sx - 12}" y="{grid_y}" font-family="{CONNECTOR_FONT_FAMILY}" '
                                     f'font-size="11" fill="#666" text-anchor="end"'
                                     f'>{_escape_xml(rel.src_mult)}</text>')
                    else:
                        # Has marker: place along segment as normal
                        my = sy + (mid_y - sy) * 0.3  # 30% along first vertical segment
                        parts.append(f'  <text x="{sx + 8}" y="{my}" font-family="{CONNECTOR_FONT_FAMILY}" '
                                     f'font-size="11" fill="#666" text-anchor="start"'
                                     f'>{_escape_xml(rel.src_mult)}</text>')
                
                # Segment 2 (horizontal mid_y): connector label above the line
                if rel.label:
                    lx = (sx + tx) / 2  # Horizontal midpoint
                    ly = mid_y - 8  # Positioned above the line
                    parts.append(f'  <text x="{lx}" y="{ly}" font-family="{FONT_FAMILY}" '
                                 f'font-size="11" font-style="italic" fill="#444" text-anchor="middle">'
                                 f'{_escape_xml(rel.label)}</text>')
                
                # Segment 3 (vertical mid_y->ty): target multiplicity on right
                if rel.tgt_mult:
                    if not has_target_marker:
                        # No marker: place in target grid cell
                        grid_y = _calculate_grid_cell_position(ty)
                        parts.append(f'  <text x="{tx - 12}" y="{grid_y}" font-family="{CONNECTOR_FONT_FAMILY}" '
                                     f'font-size="11" fill="#666" text-anchor="end"'
                                     f'>{_escape_xml(rel.tgt_mult)}</text>')
                    else:
                        # Has marker: place along segment as normal
                        my = mid_y + (ty - mid_y) * 0.7  # 70% along final vertical segment
                        parts.append(f'  <text x="{tx + 8}" y="{my}" font-family="{CONNECTOR_FONT_FAMILY}" '
                                     f'font-size="11" fill="#666" text-anchor="start"'
                                     f'>{_escape_xml(rel.tgt_mult)}</text>')
            else:
                # Vertical-only routing: single vertical segment
                # Position source multiplicity at 25% along vertical
                if rel.src_mult:
                    if not has_source_marker:
                        # No marker: place in source grid cell
                        grid_y = _calculate_grid_cell_position(sy)
                        parts.append(f'  <text x="{sx - 12}" y="{grid_y}" font-family="{CONNECTOR_FONT_FAMILY}" '
                                     f'font-size="11" fill="#666" text-anchor="end"'
                                     f'>{_escape_xml(rel.src_mult)}</text>')
                    else:
                        # Has marker: place along segment as normal
                        my = sy + (ty - sy) * 0.25
                        parts.append(f'  <text x="{sx + 8}" y="{my}" font-family="{CONNECTOR_FONT_FAMILY}" '
                                     f'font-size="11" fill="#666" text-anchor="start"'
                                     f'>{_escape_xml(rel.src_mult)}</text>')
                
                # Position connector label in the middle
                if rel.label:
                    ly = (sy + ty) / 2
                    parts.append(f'  <text x="{sx + 8}" y="{ly}" font-family="{FONT_FAMILY}" '
                                 f'font-size="11" font-style="italic" fill="#444" text-anchor="start"'
                                 f'>{_escape_xml(rel.label)}</text>')
                
                # Position target multiplicity at 75% along vertical
                if rel.tgt_mult:
                    if not has_target_marker:
                        # No marker: place in target grid cell
                        grid_y = _calculate_grid_cell_position(ty)
                        parts.append(f'  <text x="{tx - 12}" y="{grid_y}" font-family="{CONNECTOR_FONT_FAMILY}" '
                                     f'font-size="11" fill="#666" text-anchor="end"'
                                     f'>{_escape_xml(rel.tgt_mult)}</text>')
                    else:
                        # Has marker: place along segment as normal
                        my = sy + (ty - sy) * 0.75
                        parts.append(f'  <text x="{sx + 8}" y="{my}" font-family="{CONNECTOR_FONT_FAMILY}" '
                                     f'font-size="11" fill="#666" text-anchor="start"'
                                     f'>{_escape_xml(rel.tgt_mult)}</text>')
    else:
        # Diagonal routing: straight line between boxes
        # Check if this is a horizontal line (same Y coordinates within tolerance)
        is_horizontal = abs(sy - ty) < 2
        
        attrs = f'x1="{sx}" y1="{sy}" x2="{tx}" y2="{ty}" stroke="#555" stroke-width="1.5"'
        if dash != "none":
            attrs += f' stroke-dasharray="{dash}"'
        if marker_start:
            attrs += f' marker-start="url(#{marker_start})"'
        if marker_end:
            attrs += f' marker-end="url(#{marker_end})"'
        parts.append(f'  <line {attrs}/>')
        
        # For horizontal connectors, place all text centered ABOVE the line
        if is_horizontal and verbosity_level == "High":
            # Check for markers at endpoints
            has_source_marker = _arrow_has_marker(rel.arrow, "start")
            has_target_marker = _arrow_has_marker(rel.arrow, "end")
            
            # If either endpoint lacks a marker, use grid cell positioning
            if not has_source_marker or not has_target_marker:
                if rel.src_mult and not has_source_marker:
                    grid_y = _calculate_grid_cell_position(sy)
                    parts.append(f'  <text x="{sx - 12}" y="{grid_y}" font-family="{CONNECTOR_FONT_FAMILY}" '
                                 f'font-size="11" fill="#666" text-anchor="end">'
                                 f'{_escape_xml(rel.src_mult)}</text>')
                
                if rel.tgt_mult and not has_target_marker:
                    grid_y = _calculate_grid_cell_position(ty)
                    parts.append(f'  <text x="{tx - 12}" y="{grid_y}" font-family="{CONNECTOR_FONT_FAMILY}" '
                                 f'font-size="11" fill="#666" text-anchor="end">'
                                 f'{_escape_xml(rel.tgt_mult)}</text>')
            else:
                # Both endpoints have markers: use normal centered positioning
                # Calculate total width of all text elements
                src_mult_text = rel.src_mult or ""
                tgt_mult_text = rel.tgt_mult or ""
                label_text = rel.label or ""
                
                # Build text sequences with proper spacing
                # Format: "mult1  label  mult2" or "mult1  mult2" if no label
                if label_text:
                    total_text = f"{src_mult_text}  {label_text}  {tgt_mult_text}"
                else:
                    total_text = f"{src_mult_text}   {tgt_mult_text}"
                
                # Calculate position to center the entire text above the line
                text_width = len(total_text) * CONNECTOR_CHAR_WIDTH
                line_center_x = (sx + tx) / 2
                text_start_x = line_center_x - (text_width / 2)
                text_y = min(sy, ty) - 8  # Place above the line
                
                parts.append(f'  <text x="{text_start_x}" y="{text_y}" font-family="{CONNECTOR_FONT_FAMILY}" '
                             f'font-size="11" fill="#666" text-anchor="start">'
                             f'{_escape_xml(total_text)}</text>')
        elif not is_horizontal and verbosity_level == "High":
            # Diagonal connector: determine if primarily vertical or primarily horizontal
            dx = abs(tx - sx)
            dy = abs(ty - sy)
            is_vertical_diagonal = dy > dx  # More vertical than horizontal
            
            # Check for markers at endpoints
            has_source_marker = _arrow_has_marker(rel.arrow, "start")
            has_target_marker = _arrow_has_marker(rel.arrow, "end")
            
            if is_vertical_diagonal:
                # Nearly vertical diagonal: place text to the RIGHT of the line
                # Source multiplicity near source
                if rel.src_mult:
                    if not has_source_marker:
                        # No marker: place in source grid cell
                        grid_y = _calculate_grid_cell_position(sy)
                        parts.append(f'  <text x="{sx - 12}" y="{grid_y}" font-family="{CONNECTOR_FONT_FAMILY}" '
                                     f'font-size="11" fill="#666" text-anchor="end">'
                                     f'{_escape_xml(rel.src_mult)}</text>')
                    else:
                        # Has marker: place along connector
                        mx = sx + 8  # To the right of the line
                        my = sy + (ty - sy) * 0.2  # 20% along the connector
                        parts.append(f'  <text x="{mx}" y="{my}" font-family="{CONNECTOR_FONT_FAMILY}" '
                                     f'font-size="11" fill="#666" text-anchor="start">'
                                     f'{_escape_xml(rel.src_mult)}</text>')
                
                # Connector label in the middle
                if rel.label:
                    mx = sx + 8
                    my = (sy + ty) / 2
                    parts.append(f'  <text x="{mx}" y="{my}" font-family="{FONT_FAMILY}" '
                                 f'font-size="11" font-style="italic" fill="#444" text-anchor="start">'
                                 f'{_escape_xml(rel.label)}</text>')
                
                # Target multiplicity near target
                if rel.tgt_mult:
                    if not has_target_marker:
                        # No marker: place in target grid cell
                        grid_y = _calculate_grid_cell_position(ty)
                        parts.append(f'  <text x="{tx - 12}" y="{grid_y}" font-family="{CONNECTOR_FONT_FAMILY}" '
                                     f'font-size="11" fill="#666" text-anchor="end">'
                                     f'{_escape_xml(rel.tgt_mult)}</text>')
                    else:
                        # Has marker: place along connector
                        mx = tx + 8  # To the right of the line
                        my = ty + (sy - ty) * 0.2  # 20% back from target
                        parts.append(f'  <text x="{mx}" y="{my}" font-family="{CONNECTOR_FONT_FAMILY}" '
                                     f'font-size="11" fill="#666" text-anchor="start">'
                                     f'{_escape_xml(rel.tgt_mult)}</text>')
            else:
                # More horizontal diagonal: text positioned based on markers
                if not has_source_marker or not has_target_marker:
                    # At least one endpoint lacks marker: use grid cell positioning
                    if rel.src_mult and not has_source_marker:
                        grid_y = _calculate_grid_cell_position(sy)
                        parts.append(f'  <text x="{sx - 12}" y="{grid_y}" font-family="{CONNECTOR_FONT_FAMILY}" '
                                     f'font-size="11" fill="#666" text-anchor="end">'
                                     f'{_escape_xml(rel.src_mult)}</text>')
                    
                    if rel.tgt_mult and not has_target_marker:
                        grid_y = _calculate_grid_cell_position(ty)
                        parts.append(f'  <text x="{tx - 12}" y="{grid_y}" font-family="{CONNECTOR_FONT_FAMILY}" '
                                     f'font-size="11" fill="#666" text-anchor="end">'
                                     f'{_escape_xml(rel.tgt_mult)}</text>')
                else:
                    # Both have markers: use normal formatting
                    src_mult_str = rel.src_mult if rel.src_mult else ""
                    label_str = rel.label if rel.label else ""
                    tgt_mult_str = rel.tgt_mult if rel.tgt_mult else ""
                    
                    # Build single formatted text string with 2-space gaps
                    total_text = f"{rel.arrow}  {src_mult_str}  {label_str}  {tgt_mult_str}"
                    
                    # Calculate text width and center it on the connector
                    text_width = len(total_text) * CONNECTOR_CHAR_WIDTH
                    line_center_x = (sx + tx) / 2
                    text_start_x = line_center_x - (text_width / 2)
                    text_y = min(sy, ty) - 12  # ABOVE the line
                    
                    # Render as single text element
                    parts.append(f'  <text x="{text_start_x}" y="{text_y}" font-family="{CONNECTOR_FONT_FAMILY}" '
                                 f'font-size="11" fill="#666" text-anchor="start">'
                                 f'{_escape_xml(total_text)}</text>')
        elif is_horizontal and rel.label:
            # Horizontal connector without multiplicity: just place label
            lx = (sx + tx) / 2
            ly = min(sy, ty) - 8
            parts.append(f'  <text x="{lx}" y="{ly}" font-family="{FONT_FAMILY}" '
                         f'font-size="11" font-style="italic" fill="#444" text-anchor="middle">'
                         f'{_escape_xml(rel.label)}</text>')
        elif not is_horizontal and rel.label and verbosity_level != "High":
            # Diagonal connector with label only (no multiplicity)
            lx = (sx + tx) / 2
            ly = (sy + ty) / 2 - 3
            parts.append(f'  <text x="{lx}" y="{ly}" font-family="{FONT_FAMILY}" '
                         f'font-size="11" font-style="italic" fill="#444" text-anchor="middle">'
                         f'{_escape_xml(rel.label)}</text>')
    
    return '\n'.join(parts)


def render_class_diagram_svg(model, diagram, verbosity_level="High", layers_filter=None):
    """Render a class diagram as SVG.
    
    Args:
        model: The Model containing class definitions
        diagram: A ClassDiagramDef with relationships
        verbosity_level: "Low" (name only), "Normal" (+members), "High" (+operations)
        layers_filter: Optional list of layer names to include. None = show all.
    
    Returns:
        SVG string
    """
    # Filter relationships by layer if requested
    if layers_filter is not None:
        filtered_rels = [r for r in diagram.relationships if not r.layer or r.layer in layers_filter]
        # Create a temporary diagram with filtered relationships
        from model import ClassDiagramDef
        filtered_diagram = ClassDiagramDef(
            diagram_id=diagram.diagram_id,
            description=diagram.description,
            relationships=filtered_rels,
            routing=diagram.routing,
            element_types=diagram.element_types
        )
    else:
        filtered_diagram = diagram
    
    if not filtered_diagram.relationships:
        return _empty_svg(diagram.description or diagram.diagram_id)
    
    # Layout class boxes using routing-aware positioning
    # Orthogonal routing uses grid-aligned layout, diagonal uses tree-based layout
    effective_routing = "orthogonal"
    boxes = _layout_classes_uml_standard(filtered_diagram, model, verbosity_level, routing=effective_routing)
    
    if not boxes:
        return _empty_svg(diagram.description or diagram.diagram_id)

    
    # Compute canvas size with extra space for connector text positioning
    # Connector text is positioned 8px above lines with ~15px font height
    # This ensures text won't be clipped by the SVG viewBox
    CONNECTOR_TEXT_VERTICAL_MARGIN = 40  # Extra space for connector text above/below boxes
    
    max_x = max(b['x'] + b['width'] for b in boxes.values()) + MARGIN
    max_y = max(b['y'] + b['height'] for b in boxes.values()) + MARGIN + CONNECTOR_TEXT_VERTICAL_MARGIN
    
    # Title height
    title_height = 30
    total_height = max_y + title_height
    
    render_version = datetime.now().strftime('%Y%m%d-%H%M%S')
    
    lines = []
    lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" '
                 f'width="{max_x}" height="{total_height}" '
                 f'data-render-version="{render_version}" '
                 f'data-diagram-type="class_diagram">')
    
    # Background
    lines.append(f'  <rect width="{max_x}" height="{total_height}" fill="white"/>')
    
    # Title
    title_text = diagram.description or diagram.diagram_id
    lines.append(f'  <text x="{max_x / 2}" y="22" font-family="{FONT_FAMILY}" '
                 f'font-size="16" font-weight="bold" text-anchor="middle" fill="#333">'
                 f'{_escape_xml(title_text)}</text>')
    
    # Offset all boxes down by title height
    for box in boxes.values():
        box['y'] += title_height
    
    boxes, planner, collision_count, collision_details = _optimize_layout_for_grid_collisions(
        filtered_diagram, boxes, effective_routing, verbosity_level, layers_filter
    )

    strict_collision_count, _ = _evaluate_grid_cell_collisions(planner, boxes, verbosity_level, strict=True)

    if strict_collision_count > 0:
        # Runtime diagnostics in server log; ASCII-only output for Windows terminals.
        print(f"WARN GridCollisionCheck: hard={collision_count}, strict={strict_collision_count} in diagram '{diagram.diagram_id}'")
    
    # Assign colors to boxes (needed for marker generation)
    box_colors = _assign_box_colors(boxes)
    
    # Arrow marker definitions (with colored variants)
    lines.append(_render_arrow_marker_defs(box_colors))
    
    # Render relationships using the planner (under the boxes)
    connector_svg = _render_connectors_with_planner(planner, boxes, box_colors, verbosity_level, layers_filter)
    if connector_svg:
        lines.append(connector_svg)
    
    # Render class boxes (on top of relationships)
    for name, box in boxes.items():
        color = box_colors.get(name)
        lines.append(_render_class_box(box, name, color))
    
    # Show render version in bottom-right when High verbosity
    if verbosity_level == "High":
        version_x = max_x - 8
        version_y = total_height - 5
        lines.append(f'  <text x="{version_x}" y="{version_y}" text-anchor="end" '
                     f'font-family="{FONT_FAMILY}" font-size="9" fill="#ccc">'
                     f'v:{render_version}</text>')
    
    lines.append('</svg>')
    return '\n'.join(lines)


def _empty_svg(title):
    """Return a minimal SVG with just a message."""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="400" height="100">'
            f'<rect width="400" height="100" fill="white"/>'
            f'<text x="200" y="55" font-family="{FONT_FAMILY}" font-size="14" '
            f'text-anchor="middle" fill="#999">No relationships in: {_escape_xml(title)}</text>'
            f'</svg>')
