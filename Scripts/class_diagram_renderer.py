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
MARGIN = 40
ARROW_SIZE = 10  # Arrowhead size
DIAMOND_SIZE = 10  # Diamond marker size

# Checkerboard color palette - alternating light fills with darker strokes
# Extended color palette - 30 distinct color pairs
# Sequential assignment ensures no color reuse until all colors are exhausted
COLOR_PALETTE = [
    {"light_fill": "#E8F5E9", "dark_stroke": "#2E7D32"},  # Green
    {"light_fill": "#FFFDE7", "dark_stroke": "#F57F17"},  # Amber
    {"light_fill": "#E3F2FD", "dark_stroke": "#1565C0"},  # Blue
    {"light_fill": "#F3E5F5", "dark_stroke": "#6A1B9A"},  # Purple
    {"light_fill": "#FCE4EC", "dark_stroke": "#C2185B"},  # Pink
    {"light_fill": "#E0F2F1", "dark_stroke": "#00796B"},  # Teal
    {"light_fill": "#FFF9C4", "dark_stroke": "#F9A825"},  # Yellow
    {"light_fill": "#FFEBEE", "dark_stroke": "#D32F2F"},  # Red
    {"light_fill": "#F1F8E9", "dark_stroke": "#558B2F"},  # Light Green
    {"light_fill": "#E0F2F1", "dark_stroke": "#004D40"},  # Dark Teal
    {"light_fill": "#FCE4EC", "dark_stroke": "#880E4F"},  # Deep Pink
    {"light_fill": "#F3E5F5", "dark_stroke": "#4A148C"},  # Deep Purple
    {"light_fill": "#EDE7F6", "dark_stroke": "#311B92"},  # Indigo
    {"light_fill": "#E8EAF6", "dark_stroke": "#1A237E"},  # Deep Blue
    {"light_fill": "#F1F5FE", "dark_stroke": "#0D47A1"},  # Cobalt
    {"light_fill": "#E0F2F1", "dark_stroke": "#00695C"},  # Dark Teal Alt
    {"light_fill": "#E8F5E9", "dark_stroke": "#1B5E20"},  # Dark Green
    {"light_fill": "#FFFCE4", "dark_stroke": "#E65100"},  # Deep Orange
    {"light_fill": "#FBE9E7", "dark_stroke": "#BF360C"},  # Dark Orange
    {"light_fill": "#EFEBE9", "dark_stroke": "#3E2723"},  # Brown
    {"light_fill": "#F5F5F5", "dark_stroke": "#424242"},  # Grey
    {"light_fill": "#ECEFF1", "dark_stroke": "#37474F"},  # Blue Grey
    {"light_fill": "#FFF3E0", "dark_stroke": "#E65100"},  # Light Orange
    {"light_fill": "#FFE0B2", "dark_stroke": "#E65100"},  # Orange Lighter
    {"light_fill": "#FFCCBC", "dark_stroke": "#BF360C"},  # Deep Orange Light
    {"light_fill": "#D1C4E9", "dark_stroke": "#512DA8"},  # Purple Light
    {"light_fill": "#C5CAE9", "dark_stroke": "#283593"},  # Indigo Light
    {"light_fill": "#BBDEFB", "dark_stroke": "#1565C0"},  # Blue Light
    {"light_fill": "#B3E5FC", "dark_stroke": "#0277BD"},  # Cyan
    {"light_fill": "#B2DFDB", "dark_stroke": "#00897B"},  # Teal Light
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
    
    return max_width, _snap_height_to_grid(height), has_members, has_functions


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


def _layout_classes_tree_based(diagram, model, verbosity="High"):
    """Compute positions using level-based tree hierarchical layout.
    
    Layout Strategy:
    1. Calculate abstraction level for each class
    2. Group classes by level (level 0 at top, increasing downward)
    3. Within each level, organize into tree groups (ownership trees)
    4. Position trees horizontally in 2x2 grid blocks
    
    Returns dict: class_name -> {x, y, width, height, has_members, has_functions, class_def, element_type}
    """
    # Collect unique class names
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
            'width': w,
            'height': h,
            'has_members': has_m,
            'has_functions': has_f,
            'class_def': class_def,
            'element_type': element_type,
        }
    
    # Calculate abstraction levels (0 = most general, highest = most specific)
    levels = _calculate_abstraction_level(diagram)
    
    if verbosity != "High":
        print(f"DEBUG: Calculated levels = {levels}")
    
    # Build ownership trees
    trees = _build_ownership_trees(diagram)
    
    # Spacing parameters
    required_spacing = _calculate_required_spacing(diagram, verbosity)
    spacing_x = max(required_spacing, CLASS_SPACING_X + (15 if verbosity != "High" else 30))
    spacing_y = CLASS_SPACING_Y + (10 if verbosity != "High" else 15)
    
    # Group classes by level
    level_groups = {}
    for cls in class_names:
        level = levels.get(cls, 0)
        if level not in level_groups:
            level_groups[level] = []
        level_groups[level].append(cls)
    
    # Pre-calculate Y positions for each level (level 0 at top, higher levels below)
    level_positions = {}
    current_y = MARGIN
    for level_num in sorted(level_groups.keys()):
        level_positions[level_num] = current_y
        # Height of all classes at this level
        level_height = max(boxes[c]['height'] for c in level_groups[level_num])
        current_y += level_height + spacing_y * 2
    
    # Position classes level by level
    positions = {}
    
    for level_num in sorted(level_groups.keys()):
        classes_at_level = level_groups[level_num]
        level_y = level_positions[level_num]
        
        # For each level, organize into trees and position horizontally
        # Each tree has a root that owns other classes at this or lower levels
        
        current_x = MARGIN
        row_y = level_y  # Track row within this level (for wrapping)
        row_height = 0
        
        for class_name in classes_at_level:
            # Position this class at current location
            positions[class_name] = {
                'x': current_x,
                'y': row_y,
                'width': boxes[class_name]['width'],
                'height': boxes[class_name]['height'],
                'has_members': boxes[class_name]['has_members'],
                'has_functions': boxes[class_name]['has_functions'],
                'class_def': boxes[class_name]['class_def'],
                'element_type': boxes[class_name]['element_type'],
            }
            
            row_height = max(row_height, boxes[class_name]['height'])
            current_x += boxes[class_name]['width'] + spacing_x
            
            # Wrap to next row if too wide (but stay within same level row)
            if current_x > MARGIN + 1200:
                current_x = MARGIN
                row_y += row_height + spacing_y
                row_height = 0
    
    return positions


def _layout_classes_orthogonal(diagram, model, verbosity="High"):
    """Layout for orthogonal (right-angle) routing with grid-aligned objects.
    
    Objects are positioned on a grid where:
    - Connected objects tend to share X or Y coordinates
    - Reduces multi-segment connectors to direct H or V lines
    - Uses hierarchical levels with column-based positioning
    
    Returns dict: class_name -> {x, y, width, height, ...}
    """
    # Collect unique class names
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
            'width': w,
            'height': h,
            'has_members': has_m,
            'has_functions': has_f,
            'class_def': class_def,
            'element_type': element_type,
        }
    
    # Calculate abstraction levels (depth from leaves)
    levels = _calculate_abstraction_level(diagram)
    
    # Spacing parameters
    required_spacing = _calculate_required_spacing(diagram, verbosity)
    # For orthogonal, use more spacing to accommodate grid alignment
    spacing_x = max(required_spacing, CLASS_SPACING_X + 40)
    spacing_y = CLASS_SPACING_Y + 30
    
    # Pre-calculate fixed grid column positions based on max width at each level
    level_groups = {}
    for cls in class_names:
        level = levels.get(cls, 0)
        if level not in level_groups:
            level_groups[level] = []
        level_groups[level].append(cls)
    
    # Pre-calculate column widths (max width of any box at that level + spacing)
    column_widths = {}
    for level_num in level_groups:
        max_width = max(boxes[c]['width'] for c in level_groups[level_num])
        column_widths[level_num] = max_width + spacing_x
    
    # Pre-calculate Y positions for each level (fixed grid rows)
    level_positions = {}
    current_y = MARGIN
    for level_num in sorted(level_groups.keys()):
        level_positions[level_num] = current_y
        # All boxes at this level share the same Y coordinate (grid row alignment)
        level_height = max(boxes[c]['height'] for c in level_groups[level_num])
        current_y += level_height + spacing_y
    
    # Position classes on the grid
    positions = {}
    level_x_offset = {}  # Track X offset for next object at each level
    
    for level_num in sorted(level_groups.keys()):
        classes_at_level = level_groups[level_num]
        level_y = level_positions[level_num]
        
        if level_num not in level_x_offset:
            level_x_offset[level_num] = MARGIN
        
        current_x = level_x_offset[level_num]
        
        for class_name in classes_at_level:
            # Position this class at fixed grid aligned to level's Y
            positions[class_name] = {
                'x': current_x,
                'y': level_y,
                'width': boxes[class_name]['width'],
                'height': boxes[class_name]['height'],
                'has_members': boxes[class_name]['has_members'],
                'has_functions': boxes[class_name]['has_functions'],
                'class_def': boxes[class_name]['class_def'],
                'element_type': boxes[class_name]['element_type'],
            }
            
            # Move to next X position (grid column)
            current_x += boxes[class_name]['width'] + spacing_x
            
            # Wrap to next row if too wide
            if current_x > MARGIN + 1400:
                current_x = MARGIN
                level_y += boxes[class_name]['height'] + spacing_y
        
        level_x_offset[level_num] = current_x
    
    return positions


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
    if routing == "orthogonal":
        return _layout_classes_orthogonal(diagram, model, verbosity)
    else:
        # Use tree-based layout for diagonal and mixed routing
        return _layout_classes_tree_based(diagram, model, verbosity)


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
        
        # Render connector path
        if connector.path_type == "direct":
            # Simple line (horizontal or diagonal)
            is_horizontal = abs(connector.source_y - connector.target_y) < 2
            
            parts.append(f'  <line x1="{connector.source_x}" y1="{connector.source_y}" '
                        f'x2="{connector.target_x}" y2="{connector.target_y}" '
                        f'stroke="{connector_color}" stroke-width="1.5"')
            if dash != "none":
                parts.append(f' stroke-dasharray="{dash}"')
            if marker_start:
                parts.append(f' marker-start="url(#{marker_start})"')
            if marker_end:
                parts.append(f' marker-end="url(#{marker_end})"')
            parts.append('/>')
            
            # Text placement for direct paths
            if verbosity_level == "High":
                if is_horizontal:
                    # Horizontal line: center all text ABOVE (safe distance from markers)
                    src_mult_text = connector.src_mult or ""
                    tgt_mult_text = connector.tgt_mult or ""
                    label_text = connector.label or ""
                    
                    # Account for marker width (diamonds/arrows are ~10px each)
                    # Format: "  mult  label  mult  " with marker clearance
                    if label_text:
                        total_text = f"  {src_mult_text}  {label_text}  {tgt_mult_text}  "
                    else:
                        total_text = f"  {src_mult_text}     {tgt_mult_text}  "
                    
                    text_width = len(total_text) * CONNECTOR_CHAR_WIDTH
                    line_center_x = (connector.source_x + connector.target_x) / 2
                    text_start_x = line_center_x - (text_width / 2)
                    text_y = min(connector.source_y, connector.target_y) - 12  # Further above to avoid markers
                    
                    parts.append(f'  <text x="{text_start_x}" y="{text_y}" font-family="{CONNECTOR_FONT_FAMILY}" '
                                 f'font-size="11" fill="#666" text-anchor="start">'
                                 f'{_escape_xml(total_text)}</text>')
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
                            parts.append(f'  <text x="{mx}" y="{my}" font-family="{CONNECTOR_FONT_FAMILY}" '
                                         f'font-size="11" fill="#666" text-anchor="start">'
                                         f'{_escape_xml(connector.src_mult)}</text>')
                        
                        if connector.label:
                            mx = connector.source_x + 8
                            my = (connector.source_y + connector.target_y) / 2
                            parts.append(f'  <text x="{mx}" y="{my}" font-family="{FONT_FAMILY}" '
                                         f'font-size="11" font-style="italic" fill="#444" text-anchor="start">'
                                         f'{_escape_xml(connector.label)}</text>')
                        
                        if connector.tgt_mult:
                            mx = connector.target_x + 8
                            my = connector.target_y + (connector.source_y - connector.target_y) * 0.2
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
                        text_y = min(connector.source_y, connector.target_y) - 12  # ABOVE the line
                        
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
                for x, y in connector.segments:
                    path_d += f" L {x} {y}"
                path_d += f" L {connector.target_x} {connector.target_y}"
                
                parts.append(f'  <path d="{path_d}" fill="none" stroke="{connector_color}" stroke-width="1.5"')
                if dash != "none":
                    parts.append(f' stroke-dasharray="{dash}"')
                if marker_start:
                    parts.append(f' marker-start="url(#{marker_start})"')
                if marker_end:
                    parts.append(f' marker-end="url(#{marker_end})"')
                parts.append('/>')
                
                # Text placement for multi-segment paths
                # Analyze segments to determine if V-H-V or other pattern
                if verbosity_level == "High" and len(connector.segments) >= 2:
                    # Find the first horizontal segment (if V-H-V path)
                    mid_x = None
                    mid_y = None
                    for i, (x, y) in enumerate(connector.segments):
                        if i > 0:
                            prev_x, prev_y = connector.segments[i-1]
                            # Check if this segment is horizontal (same Y)
                            if abs(prev_y - y) < 1:
                                mid_x = x
                                mid_y = y
                                break
                    
                    if mid_x is not None and mid_y is not None:
                        # V-H-V routing detected - text distributed across segments
                        # Each segment gets: [arrow]  [text_for_segment]
                        
                        # Segment 1: Source multiplicity on first vertical segment
                        if connector.src_mult:
                            my = connector.source_y + (mid_y - connector.source_y) * 0.3
                            text_seg1 = f"{connector.src_mult}"
                            parts.append(f'  <text x="{connector.source_x + 8}" y="{my}" '
                                         f'font-family="{CONNECTOR_FONT_FAMILY}" font-size="11" '
                                         f'fill="#666" text-anchor="start">'
                                         f'{_escape_xml(text_seg1)}</text>')
                        
                        # Segment 2: Label on horizontal segment
                        if connector.label:
                            lx = mid_x
                            ly = mid_y - 8
                            text_seg2 = f"{connector.label}"
                            parts.append(f'  <text x="{lx}" y="{ly}" font-family="{FONT_FAMILY}" '
                                         f'font-size="11" font-style="italic" fill="#444" text-anchor="middle">'
                                         f'{_escape_xml(text_seg2)}</text>')
                        
                        # Segment 3: Target multiplicity on final vertical segment
                        if connector.tgt_mult:
                            my = mid_y + (connector.target_y - mid_y) * 0.7
                            text_seg3 = f"{connector.tgt_mult}"
                            parts.append(f'  <text x="{connector.target_x + 8}" y="{my}" '
                                         f'font-family="{CONNECTOR_FONT_FAMILY}" font-size="11" '
                                         f'fill="#666" text-anchor="start">'
                                         f'{_escape_xml(text_seg3)}</text>')
                    else:
                        # Fallback: simple perpendicular positioning for multi-segment without clear horizontal
                        if connector.src_mult:
                            mx = connector.source_x + (connector.target_x - connector.source_x) * 0.12
                            my = connector.source_y + (connector.target_y - connector.source_y) * 0.12 + 12
                            text = f"{connector.src_mult}"
                            parts.append(f'  <text x="{mx}" y="{my}" font-family="{CONNECTOR_FONT_FAMILY}" '
                                         f'font-size="11" fill="#666" text-anchor="middle">'
                                         f'{_escape_xml(text)}</text>')
                        
                        if connector.label:
                            lx = (connector.source_x + connector.target_x) / 2
                            ly = (connector.source_y + connector.target_y) / 2
                            text = f"{connector.label}"
                            parts.append(f'  <text x="{lx}" y="{ly}" font-family="{FONT_FAMILY}" '
                                         f'font-size="11" fill="#444" text-anchor="middle">'
                                         f'{_escape_xml(text)}</text>')
                        
                        if connector.tgt_mult:
                            mx = connector.target_x + (connector.source_x - connector.target_x) * 0.20
                            my = connector.target_y + (connector.source_y - connector.target_y) * 0.20 + 12
                            text = f"{connector.tgt_mult}"
                            parts.append(f'  <text x="{mx}" y="{my}" font-family="{CONNECTOR_FONT_FAMILY}" '
                                         f'font-size="11" fill="#666" text-anchor="middle">'
                                         f'{_escape_xml(text)}</text>')
                elif connector.label:
                    # Multi-segment with label only (no multiplicity)
                    if len(connector.segments) >= 1:
                        mid_pt = connector.segments[len(connector.segments) // 2]
                        lx = mid_pt[0]
                        ly = mid_pt[1] - 3
                    else:
                        lx = (connector.source_x + connector.target_x) / 2
                        ly = (connector.source_y + connector.target_y) / 2 - 3
                    
                    parts.append(f'  <text x="{lx}" y="{ly}" font-family="{FONT_FAMILY}" '
                                 f'font-size="11" font-style="italic" fill="#444" text-anchor="middle">'
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
    boxes = _layout_classes_uml_standard(filtered_diagram, model, verbosity_level, routing=filtered_diagram.routing)
    
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
    
    # Create connector planner with routing mode from diagram
    planner = ConnectorPlanner(routing_mode=filtered_diagram.routing)
    for name, box in boxes.items():
        planner.add_rectangle(name, box['x'], box['y'], box['width'], box['height'])
    
    # Add all relationships to the planner
    for rel in filtered_diagram.relationships:
        planner.add_connector(rel.source, rel.target, rel.arrow,
                            rel.src_mult, rel.tgt_mult, rel.label, rel.layer)
    
    # Plan all connectors
    planner.plan_connectors()
    
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
