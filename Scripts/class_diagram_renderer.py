#!/usr/bin/env python3
"""SVG renderer for UML class/structure diagrams.

Supports element types: class, component, package, object.
Supports connector routing: diagonal, orthogonal, mixed.
Supports verbosity: Low (name only), Normal (+members), High (+operations).
Supports layer filtering to show subsets of relationships.
"""

from model import Model, ClassDiagramDef, ClassRelationship, ClassDef, ELEMENT_TYPES
from datetime import datetime

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
MARGIN = 40
ARROW_SIZE = 10  # Arrowhead size
DIAMOND_SIZE = 10  # Diamond marker size

# Element type visual styles
ELEMENT_STYLES = {
    "class": {"fill": "#FAFAFA", "stroke": "#333", "stereotype": None},
    "component": {"fill": "#E8F5E9", "stroke": "#2E7D32", "stereotype": "\u00ABcomponent\u00BB"},
    "package": {"fill": "#E3F2FD", "stroke": "#1565C0", "stereotype": "\u00ABpackage\u00BB"},
    "object": {"fill": "#FFF3E0", "stroke": "#E65100", "stereotype": None},
}


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
    
    return max_width, height, has_members, has_functions


def _layout_classes(diagram, model, verbosity="High"):
    """Compute positions for each class box in the diagram.
    
    Returns dict: class_name -> {x, y, width, height, has_members, has_functions, class_def, element_type}
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
    # Always add spacing for connector text, more on High verbosity
    spacing_x = CLASS_SPACING_X + (15 if verbosity != "High" else 30)
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


def _render_class_box(box_info, class_name):
    """Render a single UML element box as SVG elements.
    
    Supports class, component, package, and object element types.
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
        
        # Multiplicity labels for orthogonal (only on High verbosity)
        if verbosity_level == "High":
            if needs_horizontal:
                # V-H-V routing: position multiplicity on vertical segments
                if rel.src_mult:
                    # Position on the first vertical segment (left side)
                    my = sy + (mid_y - sy) * 0.2  # 20% along first vertical
                    parts.append(f'  <text x="{sx - 8}" y="{my}" font-family="{CONNECTOR_FONT_FAMILY}" '
                                 f'font-size="11" fill="#666" text-anchor="end"'
                                 f'>{_escape_xml(rel.src_mult)}</text>')
                if rel.tgt_mult:
                    # Position on the final vertical segment (right side)
                    my = mid_y + (ty - mid_y) * 0.8  # 80% along final vertical
                    parts.append(f'  <text x="{tx + 8}" y="{my}" font-family="{CONNECTOR_FONT_FAMILY}" '
                                 f'font-size="11" fill="#666" text-anchor="start"'
                                 f'>{_escape_xml(rel.tgt_mult)}</text>')
            else:
                # Vertical-only routing: position multiplicity on sides
                if rel.src_mult:
                    my = sy + (ty - sy) * 0.2  # 20% along vertical
                    parts.append(f'  <text x="{sx - 8}" y="{my}" font-family="{CONNECTOR_FONT_FAMILY}" '
                                 f'font-size="11" fill="#666" text-anchor="end"'
                                 f'>{_escape_xml(rel.src_mult)}</text>')
                if rel.tgt_mult:
                    my = sy + (ty - sy) * 0.8  # 80% along vertical
                    parts.append(f'  <text x="{sx - 8}" y="{my}" font-family="{CONNECTOR_FONT_FAMILY}" '
                                 f'font-size="11" fill="#666" text-anchor="end"'
                                 f'>{_escape_xml(rel.tgt_mult)}</text>')
        
        # Label positioning
        if rel.label:
            if needs_horizontal:
                # V-H-V routing: label on horizontal segment
                lx = (sx + tx) / 2  # Horizontal midpoint
                ly = mid_y - 3  # Slightly above the line
            else:
                # Vertical-only: label on the line
                lx = sx + 15  # Offset to the right
                ly = (sy + ty) / 2  # Vertical midpoint
            parts.append(f'  <text x="{lx}" y="{ly}" font-family="{FONT_FAMILY}" '
                         f'font-size="11" font-style="italic" fill="#444" text-anchor="middle">'
                         f'{_escape_xml(rel.label)}</text>')
    else:
        # Diagonal routing: straight line
        attrs = f'x1="{sx}" y1="{sy}" x2="{tx}" y2="{ty}" stroke="#555" stroke-width="1.5"'
        if dash != "none":
            attrs += f' stroke-dasharray="{dash}"'
        if marker_start:
            attrs += f' marker-start="url(#{marker_start})"'
        if marker_end:
            attrs += f' marker-end="url(#{marker_end})"'
        parts.append(f'  <line {attrs}/>')
        
        # Multiplicity labels (only on High verbosity) - positioned BELOW connector (1/2 character height)
        if verbosity_level == "High":
            if rel.src_mult:
                mx = sx + (tx - sx) * 0.12
                my = sy + (ty - sy) * 0.12 + 12
                parts.append(f'  <text x="{mx}" y="{my}" font-family="{CONNECTOR_FONT_FAMILY}" '
                             f'font-size="11" fill="#666" text-anchor="middle">'
                             f'{_escape_xml(rel.src_mult)}</text>')
            if rel.tgt_mult:
                mx = tx + (sx - tx) * 0.20  # Increased from 0.12 to move further from arrowhead
                my = ty + (sy - ty) * 0.20 + 12
                parts.append(f'  <text x="{mx}" y="{my}" font-family="{CONNECTOR_FONT_FAMILY}" '
                             f'font-size="11" fill="#666" text-anchor="middle">'
                             f'{_escape_xml(rel.tgt_mult)}</text>')
        # Relationship label - positioned slightly ABOVE the connector line
        if rel.label:
            lx = (sx + tx) / 2
            ly = (sy + ty) / 2 - 3  # Slightly above the line
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
    
    # Layout class boxes
    boxes = _layout_classes(filtered_diagram, model, verbosity_level)
    
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
    
    # Calculate multi-connector offsets for proper text positioning
    connector_offsets = _calculate_connector_offsets(filtered_diagram.relationships)
    
    # Render relationships (under the boxes)
    for rel in filtered_diagram.relationships:
        line_svg = _render_relationship(rel, boxes, diagram.routing, verbosity_level,
                                       connector_offsets)
        if line_svg:
            lines.append(line_svg)
    
    # Render class boxes (on top of relationships)
    for name, box in boxes.items():
        lines.append(_render_class_box(box, name))
    
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
