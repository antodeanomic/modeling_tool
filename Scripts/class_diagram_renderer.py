#!/usr/bin/env python3
"""SVG renderer for UML class diagrams."""

from model import Model, ClassDiagramDef, ClassRelationship, ClassDef
from datetime import datetime

# Layout constants
FONT_SIZE = 13
FONT_FAMILY = "Arial, Helvetica, sans-serif"
CHAR_WIDTH = 7.8  # Approximate character width for Arial at 13px
CLASS_BOX_PADDING_X = 14
CLASS_BOX_PADDING_Y = 10
CLASS_MIN_WIDTH = 120
CLASS_SECTION_SPACING = 4  # Space between name/members/functions sections
MEMBER_FONT_SIZE = 12
MEMBER_CHAR_WIDTH = 7.2
ROW_HEIGHT = 18  # Line height for members/functions
CLASS_SPACING_X = 60  # Horizontal gap between class boxes
CLASS_SPACING_Y = 50  # Vertical gap between rows of classes
MARGIN = 40
ARROW_SIZE = 10  # Arrowhead size
DIAMOND_SIZE = 10  # Diamond marker size


def _escape_xml(text):
    """Escape special XML characters."""
    return (text.replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;'))


def _measure_text(text, font_size=FONT_SIZE):
    """Estimate text width in pixels."""
    char_w = CHAR_WIDTH if font_size == FONT_SIZE else MEMBER_CHAR_WIDTH
    return len(text) * char_w


def _compute_class_box_size(class_name, class_def):
    """Compute width and height for a class box.
    
    Returns (width, height, has_members, has_functions).
    """
    # Name section
    name_width = _measure_text(class_name, FONT_SIZE) + 2 * CLASS_BOX_PADDING_X
    max_width = max(name_width, CLASS_MIN_WIDTH)
    
    has_members = False
    has_functions = False
    member_lines = 0
    function_lines = 0
    
    if class_def:
        # Members section
        for m in class_def.members:
            has_members = True
            member_lines += 1
            line_text = f"  {m.name}"
            line_width = _measure_text(line_text, MEMBER_FONT_SIZE) + 2 * CLASS_BOX_PADDING_X
            max_width = max(max_width, line_width)
        
        # Functions section
        for f in class_def.functions:
            has_functions = True
            function_lines += 1
            vis = "+" if f.visibility == "public" else "-" if f.visibility == "private" else "#"
            line_text = f"  {vis} {f.name}"
            line_width = _measure_text(line_text, MEMBER_FONT_SIZE) + 2 * CLASS_BOX_PADDING_X
            max_width = max(max_width, line_width)
    
    # Height: name section + optional member section + optional function section
    height = CLASS_BOX_PADDING_Y + FONT_SIZE + CLASS_BOX_PADDING_Y  # Name section
    if has_members:
        height += CLASS_SECTION_SPACING + member_lines * ROW_HEIGHT + CLASS_BOX_PADDING_Y
    if has_functions:
        height += CLASS_SECTION_SPACING + function_lines * ROW_HEIGHT + CLASS_BOX_PADDING_Y
    
    return max_width, height, has_members, has_functions


def _layout_classes(diagram, model):
    """Compute positions for each class box in the diagram.
    
    Returns dict: class_name -> {x, y, width, height, has_members, has_functions, class_def}
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
    
    # Compute sizes for each class
    boxes = {}
    for name in class_names:
        class_def = model.get_class(name)
        w, h, has_m, has_f = _compute_class_box_size(name, class_def)
        boxes[name] = {
            'width': w, 'height': h,
            'has_members': has_m, 'has_functions': has_f,
            'class_def': class_def
        }
    
    # Simple grid layout: arrange in rows
    # Try to keep roughly square aspect ratio
    n = len(class_names)
    cols = max(1, min(n, int(n ** 0.5) + 1))
    
    # Place classes in grid
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
            y += row_height + CLASS_SPACING_Y
            row_height = 0
        else:
            x += box['width'] + CLASS_SPACING_X
    
    return boxes


def _render_class_box(box_info, class_name):
    """Render a single UML class box as SVG elements."""
    x = box_info['x']
    y = box_info['y']
    w = box_info['width']
    h = box_info['height']
    class_def = box_info['class_def']
    has_members = box_info['has_members']
    has_functions = box_info['has_functions']
    
    parts = []
    
    # Box background and border
    parts.append(f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" '
                 f'fill="#FAFAFA" stroke="#333" stroke-width="1.5" rx="2"/>')
    
    # Class name (bold, centered)
    name_y = y + CLASS_BOX_PADDING_Y + FONT_SIZE
    name_x = x + w / 2
    parts.append(f'  <text x="{name_x}" y="{name_y}" '
                 f'font-family="{FONT_FAMILY}" font-size="{FONT_SIZE}" '
                 f'font-weight="bold" text-anchor="middle" fill="#333">'
                 f'{_escape_xml(class_name)}</text>')
    
    section_y = y + CLASS_BOX_PADDING_Y + FONT_SIZE + CLASS_BOX_PADDING_Y
    
    if class_def:
        # Members section
        if has_members:
            # Separator line
            parts.append(f'  <line x1="{x}" y1="{section_y}" x2="{x + w}" y2="{section_y}" '
                         f'stroke="#333" stroke-width="1"/>')
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
                         f'stroke="#333" stroke-width="1"/>')
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


def _render_arrow_marker_defs():
    """Render SVG marker definitions for arrow types."""
    return '''  <defs>
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
  </defs>'''


def _get_arrow_style(arrow):
    """Return (stroke_dasharray, marker_start, marker_end) for the given arrow type."""
    solid = "none"
    dashed = "6,4"
    
    styles = {
        # Structural (solid)
        '--':    (solid, None, None),
        '-->':   (solid, None, 'arrow-open'),
        '<--':   (solid, 'arrow-open', None),
        '<-->':  (solid, 'arrow-open', 'arrow-open'),
        '--\u25b7':   (solid, None, 'arrow-triangle'),        # --▷
        '\u25c1--':   (solid, 'arrow-triangle', None),        # ◁--
        '--\u25c6':   (solid, None, 'diamond-filled'),        # --◆
        '\u25c6--':   (solid, 'diamond-filled', None),        # ◆--
        '--\u25c7':   (solid, None, 'diamond-open'),          # --◇
        '\u25c7--':   (solid, 'diamond-open', None),          # ◇--
        # Behavioral (dashed)
        '..>':   (dashed, None, 'arrow-open'),
        '<..':   (dashed, 'arrow-open', None),
        '..\u25b7':   (dashed, None, 'arrow-triangle'),      # ..▷
        '\u25c1..':   (dashed, 'arrow-triangle', None),      # ◁..
    }
    
    return styles.get(arrow, (solid, None, 'arrow-open'))


def _render_relationship(rel, boxes):
    """Render a single relationship line between two class boxes."""
    if rel.source not in boxes or rel.target not in boxes:
        return ''
    
    src_box = boxes[rel.source]
    tgt_box = boxes[rel.target]
    
    # Get connection points
    sx, sy = _get_connection_points(src_box, tgt_box)
    tx, ty = _get_connection_points(tgt_box, src_box)
    
    dash, marker_start, marker_end = _get_arrow_style(rel.arrow)
    
    parts = []
    
    # Build line attributes
    attrs = f'x1="{sx}" y1="{sy}" x2="{tx}" y2="{ty}" stroke="#555" stroke-width="1.5"'
    if dash != "none":
        attrs += f' stroke-dasharray="{dash}"'
    if marker_start:
        attrs += f' marker-start="url(#{marker_start})"'
    if marker_end:
        attrs += f' marker-end="url(#{marker_end})"'
    
    parts.append(f'  <line {attrs}/>')
    
    # Multiplicity labels
    if rel.src_mult:
        # Place near source end
        mx = sx + (tx - sx) * 0.12
        my = sy + (ty - sy) * 0.12 - 8
        parts.append(f'  <text x="{mx}" y="{my}" font-family="{FONT_FAMILY}" '
                     f'font-size="11" fill="#666" text-anchor="middle">'
                     f'{_escape_xml(rel.src_mult)}</text>')
    
    if rel.tgt_mult:
        # Place near target end
        mx = tx + (sx - tx) * 0.12
        my = ty + (sy - ty) * 0.12 - 8
        parts.append(f'  <text x="{mx}" y="{my}" font-family="{FONT_FAMILY}" '
                     f'font-size="11" fill="#666" text-anchor="middle">'
                     f'{_escape_xml(rel.tgt_mult)}</text>')
    
    # Relationship label (centered on line)
    if rel.label:
        lx = (sx + tx) / 2
        ly = (sy + ty) / 2 - 8
        parts.append(f'  <text x="{lx}" y="{ly}" font-family="{FONT_FAMILY}" '
                     f'font-size="11" font-style="italic" fill="#444" text-anchor="middle">'
                     f'{_escape_xml(rel.label)}</text>')
    
    return '\n'.join(parts)


def render_class_diagram_svg(model, diagram):
    """Render a class diagram as SVG.
    
    Args:
        model: The Model containing class definitions
        diagram: A ClassDiagramDef with relationships
    
    Returns:
        SVG string
    """
    if not diagram.relationships:
        return _empty_svg(diagram.description or diagram.diagram_id)
    
    # Layout class boxes
    boxes = _layout_classes(diagram, model)
    
    if not boxes:
        return _empty_svg(diagram.description or diagram.diagram_id)
    
    # Compute canvas size
    max_x = max(b['x'] + b['width'] for b in boxes.values()) + MARGIN
    max_y = max(b['y'] + b['height'] for b in boxes.values()) + MARGIN
    
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
    
    # Arrow marker definitions
    lines.append(_render_arrow_marker_defs())
    
    # Offset all boxes down by title height
    for box in boxes.values():
        box['y'] += title_height
    
    # Render relationships (under the boxes)
    for rel in diagram.relationships:
        line_svg = _render_relationship(rel, boxes)
        if line_svg:
            lines.append(line_svg)
    
    # Render class boxes (on top of relationships)
    for name, box in boxes.items():
        lines.append(_render_class_box(box, name))
    
    lines.append('</svg>')
    return '\n'.join(lines)


def _empty_svg(title):
    """Return a minimal SVG with just a message."""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="400" height="100">'
            f'<rect width="400" height="100" fill="white"/>'
            f'<text x="200" y="55" font-family="{FONT_FAMILY}" font-size="14" '
            f'text-anchor="middle" fill="#999">No relationships in: {_escape_xml(title)}</text>'
            f'</svg>')
