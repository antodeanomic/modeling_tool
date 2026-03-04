from model import Model, SequenceDef, NoteDef
from datetime import datetime
import random

FONT_SIZE = 12  # Font size for all text labels
MONOSPACE_CHAR_WIDTH = 7.2  # Width of each character in monospaced font at 12px
MESSAGE_SPACING = 7.2  # 1 character space before message and after note for symmetric layout
LABEL_NOTE_GAP = 0  # No gap between closing ) and note box - they should touch
ROW_HEIGHT = FONT_SIZE * 2  # Spacing for consecutive message rows (2x font height)
ROW_SPACING = 6  # Extra spacing between rows
LANE_WIDTH = 90  # Reduced from 200 for tighter spacing (3-character arrow width)
PARTICIPANT_BOX_WIDTH = 140
PARTICIPANT_BOX_HEIGHT = 40
STATE_BOX_PADDING = 6
STATE_TEXT_SIZE = 13
NOTE_BOX_CHARS = 2  # Note boxes are 2 characters wide
NOTE_BOX_WIDTH = NOTE_BOX_CHARS * MONOSPACE_CHAR_WIDTH  # 14.4px
NOTE_BOX_HEIGHT = 13
NOTE_FOLD_SIZE = 2
NOTE_SPACING_OFFSET = 0  # No offset needed - note positioned directly after label
PARTICIPANT_FONT_SIZE = 14
PARTICIPANT_PADDING_WIDTH = 7  # 1 character width margin (~1 char at font size 12)
PARTICIPANT_PADDING_HEIGHT = 12  # 1 character height margin (FONT_SIZE)
MIN_PARTICIPANT_WIDTH = 80
MIN_PARTICIPANT_HEIGHT = 40
MIN_GAP_BETWEEN_BOXES = 14  # Minimum 2 character wide gap between participant boxes
MIN_ARROW_LENGTH = 17  # Minimum 2.5 character wide arrow space before/after function name

# Note type colors
# REQUIREMENT: Use CORRECT unicode character for Success checkmark: ✓ (U+2713 - CHECK MARK)
# DO NOT use ✔ (U+2714 - HEAVY CHECK MARK) - it renders incorrectly
NOTE_COLORS = {
    "Info": {"fill": "#E3F2FD", "stroke": "#1976D2", "icon": "ℹ"},
    "Warning": {"fill": "#FFF3E0", "stroke": "#F57C00", "icon": "⚠"},
    "Error": {"fill": "#FFEBEE", "stroke": "#D32F2F", "icon": "✕"},
    "Success": {"fill": "#E8F5E9", "stroke": "#2E7D32", "icon": "✓"}  # ✓ U+2713 CHECK MARK - CORRECT
}

# Code styling colors
CODE_BACKGROUND_COLOR = "#E8E8E8"  # Light grey background for code
CODE_TEXT_COLOR = "#333333"  # Dark text for code

def extract_code_segments(text: str) -> list:
    """Parse text and extract backtick-enclosed code segments.
    
    Returns list of tuples: (content, is_code)
    Example: "prefix `123` suffix" -> [("prefix ", False), ("123", True), (" suffix", False)]
    """
    import re
    if not text:
        return [("", False)]
    
    segments = []
    last_end = 0
    
    # Find all `...` patterns (backtick-enclosed)
    for match in re.finditer(r'`([^`]*)`', text):
        # Add text before code segment
        if match.start() > last_end:
            segments.append((text[last_end:match.start()], False))
        
        # Add code segment (content between backticks)
        segments.append((match.group(1), True))
        last_end = match.end()
    
    # Add remaining text
    if last_end < len(text):
        segments.append((text[last_end:], False))
    
    # If no backticks found, return original text as non-code
    if not segments:
        segments = [(text, False)]
    
    return segments

def strip_code_wrappers(text: str) -> str:
    """Remove backticks from text, keeping the content inside.
    
    Example: "value: `123`" -> "value: 123"
    """
    import re
    return re.sub(r'`([^`]*)`', r'\1', text)

def measure_text_width(text: str, font_size: float = 11) -> float:
    """Rough estimate of text width in SVG (monospace-ish)."""
    return len(text) * (font_size * 0.6)

def split_participant_name(name: str) -> list:
    """Split participant name by <br> tags or newlines, return list of lines."""
    # Handle <br> tags and line breaks
    lines = name.replace('<br>', '\n').split('\n')
    return [line.strip() for line in lines if line.strip()]

def measure_participant_box(name: str) -> tuple:
    """Measure required width and height for participant box based on name.
    
    Returns (width, height) tuple.
    """
    lines = split_participant_name(name)
    
    if not lines:
        return (MIN_PARTICIPANT_WIDTH, MIN_PARTICIPANT_HEIGHT)
    
    # Find the longest line to determine width
    max_width = max(measure_text_width(line, PARTICIPANT_FONT_SIZE) for line in lines)
    
    # Add padding (separate for width and height)
    box_width = max(max_width + (PARTICIPANT_PADDING_WIDTH * 2), MIN_PARTICIPANT_WIDTH)
    
    # Height depends on number of lines
    line_height = PARTICIPANT_FONT_SIZE + 2
    box_height = max(len(lines) * line_height + (PARTICIPANT_PADDING_HEIGHT * 2), MIN_PARTICIPANT_HEIGHT)
    
    return (box_width, box_height)

def create_state_box(x: float, y: float, state_name: str, state_desc: str = "") -> str:
    """Create SVG elements for a UML state box.
    
    Returns list of SVG elements as strings.
    """
    # Calculate box size based on text
    text_width = measure_text_width(state_name, STATE_TEXT_SIZE)
    box_width = text_width + (STATE_BOX_PADDING * 2) + 4
    box_height = STATE_TEXT_SIZE + (STATE_BOX_PADDING * 2) + 4
    
    # Positions for rounded box (centered on x, starting at y)
    left = x - (box_width / 2)
    top = y
    
    svg_parts = []
    
    # Draw rounded rectangle for state box (more prominent styling)
    box = f'<rect x="{left}" y="{top}" width="{box_width}" height="{box_height}" rx="6" ry="6" fill="#e8f5e9" stroke="#2e7d32" stroke-width="2"/>'
    if state_desc:
        box = box.replace('/>', f'><title>{state_desc}</title></rect>', 1)
    svg_parts.append(box)
    
    # Draw state name text (darker color for better visibility)
    text = f'<text x="{x}" y="{top + STATE_BOX_PADDING + STATE_TEXT_SIZE}" text-anchor="middle" font-family="Arial" font-size="{STATE_TEXT_SIZE}" fill="#1b5e20" font-weight="bold">{state_name}</text>'
    if state_desc:
        text = text.replace('>', f'><title>{state_desc}</title>', 1)
    svg_parts.append(text)
    
    return svg_parts

def wrap_text(text: str, max_width: int = 80) -> list:
    """Wrap text at a maximum width (character count).
    
    Returns list of text lines.
    """
    if len(text) <= max_width:
        return [text]
    
    lines = []
    words = text.split(' ')
    current_line = ""
    
    for word in words:
        if len(current_line) + len(word) + 1 <= max_width:
            if current_line:
                current_line += " " + word
            else:
                current_line = word
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    
    if current_line:
        lines.append(current_line)
    
    return lines if lines else [text]

def render_text_with_code_styling(content: str, x: float, y: float, font_size: int = 11, 
                                   text_color: str = "black", code_bg_color: str = CODE_BACKGROUND_COLOR, 
                                   note_bg_color: str = None, line_spacing: float = 1.3) -> tuple:
    """Render text as plain text (code styling removed).
    
    Args:
        content: Text to render
        x, y: Starting position
        font_size: Font size in pixels
        text_color: Color for text
        code_bg_color: Unused (kept for backwards compatibility)
        note_bg_color: Unused (kept for backwards compatibility)
        line_spacing: Line spacing multiplier
    
    Returns tuple (svg_elements_list, total_height, max_width)
    """
    svg_parts = []
    lines = content.split('\n')
    line_height = font_size * line_spacing
    current_y = y
    max_width = 0
    char_width = font_size * 0.65
    
    for line_text in lines:
        # Render line as simple text element
        text_element = f'<text x="{x}" y="{current_y + font_size}" font-family="monospace" font-size="{font_size}" dominant-baseline="baseline" fill="{text_color}">{line_text}</text>'
        svg_parts.append(text_element)
        
        max_width = max(max_width, len(line_text) * char_width)
        current_y += line_height
    
    total_height = current_y - y + 4
    return (svg_parts, total_height, max_width)

def create_note_box(x: float, y: float, note: NoteDef, show_text: bool = False) -> list:
    """Create SVG elements for a note box with UML note style (folded corner).
    
    Includes a styled tooltip that appears on hover with note content using code styling.
    
    Args:
        x: X coordinate (center of note)
        y: Y coordinate (top of note)
        note: NoteDef containing note type and content
        show_text: If True, show the note content inline; otherwise show only on hover
    
    Returns list of SVG elements as strings.
    """
    colors = NOTE_COLORS.get(note.note_type, NOTE_COLORS["Info"])
    svg_parts = []
    
    left = x - (NOTE_BOX_WIDTH / 2)
    right = left + NOTE_BOX_WIDTH
    
    # Create note content with type prefix (keep backticks for code styling)
    prefixed_content = f"{note.note_type}: {note.content}" if note.content else note.note_type
    
    # Open a group for hover interaction with data attribute for note content (for easy copying)
    # Escape quotes in note content for HTML attribute
    escaped_content = prefixed_content.replace('"', '&quot;')
    svg_parts.append(f'<g class="note-box-group" data-note-content="{escaped_content}">')
    
    # Draw main rectangle (path that accommodates folded corner)
    # Rectangle with top-right corner cut out for fold
    fold_right = right
    fold_bottom = y + NOTE_FOLD_SIZE
    
    # Create path: Start top-left, go right to fold start, up to fold, diagonal cut, down left side
    rect_path = (f'<path d="M {left},{y} L {fold_right - NOTE_FOLD_SIZE},{y} '
                 f'L {fold_right},{y + NOTE_FOLD_SIZE} L {fold_right},{y + NOTE_BOX_HEIGHT} '
                 f'L {left},{y + NOTE_BOX_HEIGHT} Z" '
                 f'fill="{colors["fill"]}" stroke="{colors["stroke"]}" stroke-width="1"/>')
    svg_parts.append(rect_path)
    
    # Draw folded corner (darker shade)
    fold_left = fold_right - NOTE_FOLD_SIZE
    fold_path = (f'<path d="M {fold_left},{y} L {fold_right},{y} L {fold_right},{y + NOTE_FOLD_SIZE} Z" '
                 f'fill="{colors["stroke"]}" opacity="0.4"/>') 
    svg_parts.append(fold_path)
    
    # Draw fold line (diagonal crease)
    fold_line = (f'<line x1="{fold_left}" y1="{y}" x2="{fold_right}" y2="{y + NOTE_FOLD_SIZE}" '
                 f'stroke="{colors["stroke"]}" stroke-width="0.5" opacity="0.6"/>')
    svg_parts.append(fold_line)
    
    # Draw icon/indicator (centered both horizontally and vertically)
    icon_x = left + NOTE_BOX_WIDTH / 2
    icon_y = y + NOTE_BOX_HEIGHT / 2
    # Use baseline dominant with exact y position for proper centering
    icon = f'<text x="{icon_x}" y="{icon_y}" font-size="11" font-weight="bold" fill="{colors["stroke"]}" text-anchor="middle" dominant-baseline="central">{colors["icon"]}</text>'
    svg_parts.append(icon)
    
    # If show_text is True, add the content text (truncated to fit)
    if show_text and note.content:
        # Truncate text to fit in the box
        truncated = prefixed_content[:12] + ".." if len(prefixed_content) > 12 else prefixed_content
        text = f'<text x="{x}" y="{y + NOTE_BOX_HEIGHT - 2}" font-size="5" fill="{colors["stroke"]}" text-anchor="middle">{truncated}</text>'
        svg_parts.append(text)
    
    # Create styled tooltip that shows on hover
    if note.content:
        # Wrap text to max 80 characters
        wrapped_lines = wrap_text(prefixed_content, max_width=80)
        wrapped_text = '\n'.join(wrapped_lines)
        
        # Render content with code styling to get dimensions
        text_elements, text_height, text_width = render_text_with_code_styling(
            wrapped_text, 0, 0,  # Dummy coords, we'll position later
            font_size=11, text_color=colors["stroke"],
            code_bg_color=CODE_BACKGROUND_COLOR,
            note_bg_color=colors["fill"])
        
        # Calculate tooltip dimensions based on content
        tooltip_padding_h = 10
        tooltip_padding_v = 8
        tooltip_width = text_width + (tooltip_padding_h * 2)
        tooltip_height = text_height + (tooltip_padding_v * 2)
        
        # Ensure minimum size
        tooltip_width = max(120, tooltip_width)
        tooltip_height = max(35, tooltip_height)
        
        tooltip_y = y - tooltip_height - 8  # Position above the note
        tooltip_x = x - tooltip_width / 2
        
        # Clamp tooltip to visible area horizontally
        max_x_pos = 1200  # Assume reasonable canvas width
        if tooltip_x < 10:
            tooltip_x = 10
        elif tooltip_x + tooltip_width > max_x_pos:
            tooltip_x = max_x_pos - tooltip_width
        
        # Create tooltip group with overflow visible
        svg_parts.append('<g class="note-tooltip" overflow="visible">')
        
        # Tooltip background with rounded corners
        tooltip_bg = (f'<rect x="{tooltip_x}" y="{tooltip_y}" width="{tooltip_width}" height="{tooltip_height}" '
                     f'fill="{colors["fill"]}" stroke="{colors["stroke"]}" stroke-width="1.5" rx="4" ry="4"/>')
        svg_parts.append(tooltip_bg)
        
        # Render tooltip text with proper positioning
        text_start_y = tooltip_y + tooltip_padding_v
        text_start_x = tooltip_x + tooltip_padding_h
        
        text_elements, _, _ = render_text_with_code_styling(
            wrapped_text, text_start_x, text_start_y,
            font_size=11, text_color=colors["stroke"],
            code_bg_color=CODE_BACKGROUND_COLOR,
            note_bg_color=colors["fill"])
        svg_parts.extend(text_elements)
        
        # Close tooltip group
        svg_parts.append('</g>')
    
    # Close note group
    svg_parts.append('</g>')
    
    return svg_parts

def detect_spanning_brackets(steps) -> dict:
    """Detect spanning brackets based on nesting depth from indentation.
    
    A spanning bracket represents the scope of a function call:
    - Starts when a function is called (defining row)
    - Ends when nesting depth decreases (next row/step with lower depth) or at file end
    
    Returns: Dict mapping (start_row, nesting_depth) -> (end_row, function_name, src_obj, dst_obj)
    where end_row is the last row where this function's scope is active.
    Keys use (start_row, nesting_depth) tuple to allow multiple brackets per row.
    """
    spanning_brackets = {}
    scope_stack = []  # Stack of (step_index, row, depth, src_obj, dst_obj, function) tuples
    
    for i, step in enumerate(steps):
        # Close any scopes that are deeper than or equal to current step's depth
        # (when nesting decreases, close the deeper scopes)
        while scope_stack and scope_stack[-1][2] >= step.depth:
            step_index, start_row, depth, src_obj, dst_obj, func_name = scope_stack.pop()
            # Scope ends at the step before current
            end_row = steps[i-1].row if i > 0 else start_row
            # Use (start_row, depth) as key to allow multiple brackets per row
            spanning_brackets[(start_row, depth)] = (end_row, func_name, src_obj, dst_obj)
        
        # Open new scope for current step
        scope_stack.append((i, step.row, step.depth, step.src_obj, step.dst_obj, step.function))
    
    # Close any remaining open scopes at end of sequence
    last_row = steps[-1].row if steps else 0
    while scope_stack:
        step_index, start_row, depth, src_obj, dst_obj, func_name = scope_stack.pop()
        spanning_brackets[(start_row, depth)] = (last_row, func_name, src_obj, dst_obj)
    
    return spanning_brackets

def render_spanning_bracket(x: float, y_start: float, y_end: float, label: str, 
                           tooltip: str = "", nesting_depth: int = 0, is_self_message: bool = False) -> list:
    """Render a spanning bracket as a filled rectangle on the lane, offset left for nesting.
    
    For nesting, brackets are offset to the left of the lifeline.
    Nesting layout:
      - Depth 0: centered at x (lifeline center)
      - Depth 1: centered at x-4 (4px left of lifeline)
      - Depth n: centered at x-(n*4)
    
    The function name label is positioned to the left of the bracket at the top,
    but only for self-messages (where source and destination objects are the same).
    
    Minimum height is enforced to match text font height (approximately 15px).
    
    Args:
        x: X position of the lane center (lifeline)
        y_start: Y position of bracket start
        y_end: Y position of bracket end
        label: Text label for the message (displayed to left of bracket for self-messages)
        tooltip: Optional tooltip content
        nesting_depth: Indentation level (0 = outermost, increases for nested)
        is_self_message: If True, render the function name label; if False, omit label
    
    Returns list of SVG elements as strings.
    """
    RECTANGLE_WIDTH = 4  # 4px wide rectangle for duration indicator (doubled for visibility)
    MIN_HEIGHT = 15  # Minimum height matching text font height (12px font + padding)
    TEXT_PADDING = 5  # Space between bracket and label text
    
    # Calculate rectangle position centered over lane with left offset for nesting
    # Depth 0: centered at x (no offset)
    # Deeper nesting: offset further left by nesting_depth * 4px
    center_x = x - (nesting_depth * 4)
    left_x = center_x - (RECTANGLE_WIDTH / 2)
    right_x = center_x + (RECTANGLE_WIDTH / 2)
    
    svg_parts = []
    
    # Draw filled rectangle spanning the bracket duration
    height = max(MIN_HEIGHT, y_end - y_start)  # Enforce minimum height
    rect_elem = f'<rect x="{left_x}" y="{y_start}" width="{RECTANGLE_WIDTH}" height="{height}" fill="#666" opacity="0.7"/>'
    if tooltip:
        tooltip_escaped = tooltip.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\"", "&quot;")
        rect_elem = rect_elem.replace('/>', f'><title>{tooltip_escaped}</title></rect>', 1)
    elif label:
        # If no explicit tooltip but we have a label, use it
        label_escaped = label.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\"", "&quot;")
        rect_elem = rect_elem.replace('/>', f'><title>{label_escaped}</title></rect>', 1)
    svg_parts.append(rect_elem)
    
    # Add function name label to the left of the bracket at the top (only for self-messages)
    if label and is_self_message:
        # Position text so that the TOP of the text aligns with the top of the bracket (y_start)
        # For SVG text, y is the baseline. For a 12px font, ascent is roughly 10px.
        # So baseline = y_start + ascent positions the top of text at y_start
        text_x = left_x - TEXT_PADDING
        text_baseline_y = y_start + 10  # Ascent for 12px font
        text_elem = f'<text x="{text_x}" y="{text_baseline_y}" text-anchor="end" font-family="monospace" font-size="12" fill="#000">{label}</text>'
        if tooltip:
            tooltip_escaped = tooltip.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\"", "&quot;")
            text_elem = text_elem.replace('>', f'><title>{tooltip_escaped}</title>', 1)
        svg_parts.append(text_elem)
    
    return svg_parts

def render_svg(model: Model, seq: SequenceDef, verbosity_level="High", lanes_filter=None) -> str:
    """Render sequence diagram as SVG.
    
    Args:
        model: Model containing class definitions
        seq: Sequence definition to render
        verbosity_level: "Low", "Normal", or "High"
        lanes_filter: List of lane names to include. If None, includes all lanes.
    """
    lanes = seq.get_lanes()
    if not lanes:
        raise ValueError("Sequence has no lanes. Did you forget to add steps?")
    
    # Filter lanes if specified
    if lanes_filter:
        lanes = [lane for lane in lanes if lane in lanes_filter]
    
    if not lanes:
        raise ValueError("No lanes selected after filtering.")

    # Pre-calculate participant box widths to ensure proper margins
    max_box_width = 0
    for lane in lanes:
        box_width, _ = measure_participant_box(lane)
        max_box_width = max(max_box_width, box_width)
    
    # Calculate lane positions with left margin accounting for first participant box
    # Margin must be at least half the participant box width to avoid clipping
    left_margin = max(14, max_box_width / 2 + 5)  # 5px safety margin

    # UNIFIED REQUIREMENT: The lane width must satisfy BOTH criteria:
    # 1. Minimum 2-character gap between participant box EDGES (not centers)
    # 2. Minimum MIN_ARROW_LENGTH arrow space on each side of message labels
    # Result = MAX of these two requirements
    
    # Criterion 1: Calculate minimum lane width for 2-char gap between participants
    min_lane_width_for_gap = LANE_WIDTH  # Start with default
    
    for i in range(len(lanes) - 1):
        lane1, lane2 = lanes[i], lanes[i + 1]
        box_width1, _ = measure_participant_box(lane1)
        box_width2, _ = measure_participant_box(lane2)
        
        # For adjacent lanes: distance between lane centers must accommodate both boxes + gap
        # Required distance = (box_width1/2) + MIN_GAP_BETWEEN_BOXES + (box_width2/2)
        required_distance = (box_width1 / 2) + MIN_GAP_BETWEEN_BOXES + (box_width2 / 2)
        min_lane_width_for_gap = max(min_lane_width_for_gap, required_distance)
        print(f"[Gap Calc] {lane1} + gap + {lane2}: box1={box_width1:.0f}, box2={box_width2:.0f}, required_distance={required_distance:.0f}px")
    
    # Criterion 2: Calculate minimum lane width for arrow spacing around message labels
    # IMPORTANT: Must account for BOTH forward messages AND return value arrows
    min_lane_width_for_arrows = LANE_WIDTH
    arrow_space_requirements = []  # Track what each message requires
    
    print(f"\n[DEBUG] ========== ARROW SPACING CALCULATION ==========")
    print(f"[DEBUG] Processing {len(seq.steps)} steps for arrow spacing")
    print(f"[DEBUG] Available lanes: {lanes}")
    
    for idx, step in enumerate(seq.steps):
        print(f"[DEBUG] Step {idx}: {step.src_obj} -> {step.dst_obj}, func={step.function}")
        
        # Look up function in the SOURCE object (where the method is defined)
        # User->Logger: LogEvent means User.LogEvent() is being called
        func_def = model.get_function(step.src_obj, step.function)
        print(f"[DEBUG]   func_def found: {func_def is not None}")
        print(f"[DEBUG]   src_obj != dst_obj: {step.src_obj != step.dst_obj}")
        
        if func_def and step.src_obj != step.dst_obj:
            # Find lane indices
            try:
                src_idx = lanes.index(step.src_obj)
                dst_idx = lanes.index(step.dst_obj)
                print(f"[DEBUG]   Lane indices: src={src_idx}, dst={dst_idx}")
            except (ValueError, IndexError):
                print(f"[DEBUG]   Lane index error - skipping")
                continue  # Skip if lanes not in list
            
            # Calculate distance between lanes in terms of lane separations
            lane_distance = abs(dst_idx - src_idx)
            print(f"[DEBUG]   Lane distance: {lane_distance}")
            if lane_distance == 0:
                print(f"[DEBUG]   Self-message, skipping")
                continue  # Self-message, skip
            
            # ===== FORWARD MESSAGE ARROW =====
            # Measure the full label: function name + parameters
            full_label = step.function
            if step.param_values:
                full_label += "(" + ", ".join(strip_code_wrappers(v) for v in step.param_values) + ")"
            else:
                full_label += "()"
            
            # Use monospaced character width for accurate calculation
            full_label_width = len(full_label) * MONOSPACE_CHAR_WIDTH
            
            # Include note width ONLY if note exists AND verbosity is High (notes only render in High)
            note_width = 0
            label_note_gap = 0
            note_padding = 0  # Extra padding when note is present
            if step.function_note and verbosity_level.lower() == "high":
                note_width = NOTE_BOX_WIDTH  # 2-char note width (~14px)
                label_note_gap = LABEL_NOTE_GAP  # Gap to prevent overlap (currently 0)
                note_padding = 8  # Extra 8px padding on right side of note for message with icon
            
            total_width_for_spacing = full_label_width + label_note_gap + note_width + note_padding
            
            # For all messages: ensure MIN_ARROW_LENGTH space on each side of text
            # Total needed = text_width + (2 * MIN_ARROW_LENGTH)
            # Distribute across lane_distance
            total_needed = total_width_for_spacing + (2 * MIN_ARROW_LENGTH)
            min_lane_width_needed = total_needed / lane_distance
            
            print(f"[DEBUG] {step.src_obj}->{step.dst_obj}: label={full_label_width:.0f}px, note={note_width:.0f}px, total={total_width_for_spacing:.0f}px, dist={lane_distance} lanes, total_needed={total_needed:.0f}px, per_lane={min_lane_width_needed:.0f}px")
            arrow_space_requirements.append({
                'message': f"{step.src_obj}->{step.dst_obj}: {step.function}",
                'type': 'forward',
                'label_width': full_label_width,
                'note_width': note_width,
                'total_width': total_width_for_spacing,
                'lane_distance': lane_distance,
                'required_width': min_lane_width_needed
            })
            min_lane_width_for_arrows = max(min_lane_width_for_arrows, min_lane_width_needed)
            
            # ===== RETURN VALUE ARROW =====
            # Only include return value if this message has one
            if func_def.returns and step.return_value:
                ret_label = step.return_value
                ret_label_width = len(ret_label) * MONOSPACE_CHAR_WIDTH
                
                # Return values have no additional notes, just the value label
                total_needed_return = ret_label_width + (2 * MIN_ARROW_LENGTH)
                min_lane_width_needed_return = total_needed_return / lane_distance
                
                print(f"[DEBUG]   Return: {step.dst_obj}->{step.src_obj}: label={ret_label_width:.0f}px, total_needed={total_needed_return:.0f}px, per_lane={min_lane_width_needed_return:.0f}px")
                arrow_space_requirements.append({
                    'message': f"{step.dst_obj}->{step.src_obj}: {ret_label} (return)",
                    'type': 'return',
                    'label_width': ret_label_width,
                    'note_width': 0,
                    'total_width': ret_label_width,
                    'lane_distance': lane_distance,
                    'required_width': min_lane_width_needed_return
                })
                min_lane_width_for_arrows = max(min_lane_width_for_arrows, min_lane_width_needed_return)
    
    # UNIFIED REQUIREMENT: Use the maximum of both criteria
    effective_lane_width = max(min_lane_width_for_gap, min_lane_width_for_arrows)
    
    # Debug output
    print(f"\n[Gap Analysis]")
    print(f"  Criterion 1 (Participant gap): {min_lane_width_for_gap:.0f}px")
    print(f"  Criterion 2 (Arrow spacing): {min_lane_width_for_arrows:.0f}px")
    print(f"  FINAL effective_lane_width: {effective_lane_width:.0f}px (was {LANE_WIDTH}px)\n")
    
    if arrow_space_requirements:
        print(f"[Arrow Requirements Summary]:")
        for req in arrow_space_requirements:
            print(f"  {req['message']}: label={req['label_width']:.0f}px + note={req['note_width']:.0f}px = {req['total_width']:.0f}px, needs {req['required_width']:.0f}px per lane")
    
    # Calculate final lane positions using the unified effective lane width
    lane_positions = {lane: i * effective_lane_width + left_margin for i, lane in enumerate(lanes)}
    
    print(f"[Lane Positions]")
    for lane, pos in lane_positions.items():
        box_width, _ = measure_participant_box(lane)
        print(f"  {lane}: center={pos:.0f}px, box_width={box_width:.0f}px, left_edge={pos - box_width/2:.0f}px, right_edge={pos + box_width/2:.0f}px")

    # Filter steps to only include those between selected lanes
    filtered_steps = []
    if lanes_filter:
        filtered_steps = [
            step for step in seq.steps
            if step.src_obj in lanes and step.dst_obj in lanes
        ]
    else:
        filtered_steps = seq.steps

    # Calculate y positions based on row numbers
    # Group steps by row number to allow multiple steps on same Y coordinate
    row_to_y = {}  # Maps row number to y coordinate
    row_to_steps = {}  # Maps row number to list of steps in that row
    
    for step in filtered_steps:
        if step.row not in row_to_steps:
            row_to_steps[step.row] = []
        row_to_steps[step.row].append(step)
    
    # Assign Y positions based on unique row numbers
    # First message at y=90 (reduced from 120 to cut space between participant and first message by 1/2)
    sorted_rows = sorted(row_to_steps.keys())
    for row_index, row_num in enumerate(sorted_rows):
        row_to_y[row_num] = 90 + row_index * (ROW_HEIGHT + ROW_SPACING)
    
    # Store Y position for each filtered step
    for step in filtered_steps:
        step.y = row_to_y[step.row]

    total_rows = len(row_to_y)
    # Calculate height based on actual last row position plus padding
    max_y = max(row_to_y.values()) if row_to_y else 90
    
    # Track the last activity y position for each participant (for lifeline endpoints)
    participant_max_y = {lane: 90 for lane in lanes}  # Initialize with first message y position
    
    # Update participant_max_y based on steps (messages and return values)
    for step in filtered_steps:
        if step.src_obj in participant_max_y:
            participant_max_y[step.src_obj] = max(participant_max_y[step.src_obj], step.y)
        if step.dst_obj in participant_max_y:
            participant_max_y[step.dst_obj] = max(participant_max_y[step.dst_obj], step.y)
    
    # Also account for lane notes - scan all steps for lane notes that come later
    for step in filtered_steps:
        for lane_name in step.lane_notes.keys():
            if lane_name in participant_max_y:
                participant_max_y[lane_name] = max(participant_max_y[lane_name], step.y)
    
    # Account for notes at the end of the sequence: notes are positioned at y+60, note height is 13
    # Bottom margin is 1 character height (FONT_SIZE) plus note space
    height = max_y + 60 + NOTE_BOX_HEIGHT + FONT_SIZE  # Reduced bottom padding
    # Right margin must account for last participant box width
    right_margin = max(14, max_box_width / 2 + 5)  # 5px safety margin
    width = max(lane_positions.values()) + right_margin if lane_positions else left_margin + right_margin

    svg = []
    # Tight top margin: 1 character height
    top_margin = FONT_SIZE
    
    # Generate render version with timestamp and random component
    render_time = datetime.now().isoformat().split('T')[1][:8]  # HH:MM:SS
    render_version = f"{render_time}-{random.randint(1000, 9999)}"
    
    svg.append(f'<svg width="{width}" height="{height + top_margin}" '
               f'xmlns="http://www.w3.org/2000/svg" overflow="visible" data-render-version="{render_version}">')
    
    # Add SVG comment with render version for debugging
    svg.append(f'<!-- Render Version: {render_version} -->')

    # Add white background for visibility in dark mode viewers
    svg.append(f'<rect width="{width}" height="{height + top_margin}" fill="white"/>')

    svg.append("""
    <defs>
      <marker id="arrow" markerWidth="10" markerHeight="10" 
              refX="10" refY="3" orient="auto" markerUnits="strokeWidth">
        <path d="M0,0 L0,6 L9,3 z" fill="#000" />
      </marker>
      <style>
        .note-tooltip { display: none; pointer-events: none; }
        .note-box-group:hover .note-tooltip { display: block; pointer-events: auto; }
      </style>
    </defs>
    """)

    # Draw participants with tooltip descriptions and dynamic sizing
    participant_boxes = {}  # Store box dimensions for lifeline positioning
    
    for lane, x in lane_positions.items():
        # Get class description if available
        class_def = None
        for c in model.classes:
            if c.name == lane:
                class_def = c
                break
        
        class_description = class_def.description if class_def else ""
        
        # Measure box dimensions based on participant name
        box_width, box_height = measure_participant_box(lane)
        participant_boxes[lane] = (box_width, box_height)
        
        # Draw participant box with dynamic sizing (top margin = 1 character)
        box_x = x - (box_width / 2)
        box_y = top_margin
        box_elem = f'<rect x="{box_x}" y="{box_y}" width="{box_width}" height="{box_height}" rx="6" ry="6" fill="#e0e0e0" stroke="#000"/>'
        if class_description:
            box_elem = box_elem.replace('/>', f'><title>{class_description}</title></rect>', 1)
        svg.append(box_elem)
        
        # Draw participant name text with multi-line support
        lines = split_participant_name(lane)
        text_group_y = box_y + PARTICIPANT_PADDING_HEIGHT + PARTICIPANT_FONT_SIZE
        
        # Create text element with tspans for each line
        text_elem = f'<text x="{x}" y="{text_group_y}" text-anchor="middle" font-family="Arial" font-size="{PARTICIPANT_FONT_SIZE}"'
        if class_description:
            text_elem += f'><title>{class_description}</title>'
        else:
            text_elem += '>'
        
        # Add first line
        if lines:
            text_elem += f'<tspan x="{x}" dy="0">{strip_code_wrappers(lines[0])}</tspan>'
            
            # Add subsequent lines with proper spacing
            for line in lines[1:]:
                line_spacing = PARTICIPANT_FONT_SIZE + 2
                text_elem += f'<tspan x="{x}" dy="{line_spacing}">{strip_code_wrappers(line)}</tspan>'
        
        text_elem += '</text>'
        svg.append(text_elem)

        # Draw lifeline extending only 1 character height below the last message/note for this participant
        lifeline_y_start = box_y + box_height
        # Lifelines extend to the last activity for this specific participant
        participant_last_y = participant_max_y.get(lane, 90)
        lifeline_y_end = participant_last_y + 60 + FONT_SIZE  # 60px for note positioning + font size
        svg.append(f'<line x1="{x}" y1="{lifeline_y_start}" x2="{x}" y2="{lifeline_y_end}" '
                   f'stroke="#888" stroke-dasharray="4,4"/>')
    
    # Track and render states for each lane
    current_states = {}  # lane_name -> state_name
    
    # Initialize states from state machines
    for lane in lanes:
        state_machine = model.get_state_machine(lane)
        if state_machine and state_machine.states:
            # Use first state as initial state
            current_states[lane] = state_machine.states[0].name
    
    # Render initial states if any exist
    if current_states:
        for lane, state_name in current_states.items():
            x = lane_positions[lane]
            state_machine = model.get_state_machine(lane)
            state_def = None
            if state_machine:
                for s in state_machine.states:
                    if s.name == state_name:
                        state_def = s
                        break
            
            state_desc = state_def.description if state_def else ""
            state_elements = create_state_box(x, 70, state_name, state_desc)
            svg.extend(state_elements)

    # Detect and render spanning message brackets
    spanning_brackets = detect_spanning_brackets(filtered_steps)
    bracket_render_info = {}  # Stores bracket rendering info
    bracket_end_for_start_row = {}  # Maps start_row -> end_row
    step_return_row = {}  # Maps step id -> the row where its return arrow should appear
    parent_scope_end_y = {}  # Maps parent bracket start_row -> final y position including return arrows
    deferred_notes = []  # Collect notes to render at the end (so they appear on top)
    RETURN_ARROW_SPACING = FONT_SIZE  # Space between message and return arrow (matches font height)
    
    for (start_row, nesting_depth), (end_row, func_name, src_obj, dst_obj) in spanning_brackets.items():
        # Bracket appears on DESTINATION lane (where work is performed)
        bracket_lane = dst_obj
        x = lane_positions[bracket_lane]
        y_start = row_to_y[start_row]
        y_end = row_to_y[end_row]
        
        # Store bracket info for rendering
        func_def = model.get_function(src_obj, func_name)
        func_tooltip = func_def.description if func_def else ""
        # Build the full function signature with parameters for display
        display_func_name = func_name
        if func_def:
            # Include func_def.name (which has the proper signature) with parameters in parentheses
            param_labels = []
            # Get the step to access parameter values
            step_with_params = None
            for step in filtered_steps:
                if step.row == start_row and step.depth == nesting_depth and step.src_obj == src_obj and step.dst_obj == dst_obj and step.function == func_name:
                    step_with_params = step
                    break
            
            if step_with_params and step_with_params.param_values:
                for i, param_def in enumerate(func_def.params):
                    if i < len(step_with_params.param_values):
                        param_labels.append(strip_code_wrappers(step_with_params.param_values[i]))
            elif func_def.params:
                # If no values provided, just show param names
                param_labels = [p.name for p in func_def.params]
            
            display_func_name = func_def.name + "(" + ", ".join(param_labels) + ")"
        
        # Store src_obj and dst_obj to determine if this is a self-message
        bracket_render_info[(start_row, nesting_depth)] = (x, y_start, y_end, display_func_name, func_tooltip, nesting_depth, src_obj, dst_obj)
        
        # Track bracket end for return arrow deferral
        bracket_end_for_start_row[(start_row, nesting_depth)] = end_row
        
        # Calculate final y position including return arrow spacing
        # Return arrow appears after the last message in the bracket
        parent_scope_end_y[(start_row, nesting_depth)] = y_end + RETURN_ARROW_SPACING
        
        # For the starting step, its return should appear at the ending row
        for step in filtered_steps:
            if step.row == start_row and step.depth == nesting_depth and step.src_obj == src_obj and step.dst_obj == dst_obj and step.function == func_name:
                step_return_row[id(step)] = end_row  # Return appears at end_row
                break
    
    # Extend parent scopes to include child return arrow positions
    # If a message at depth N is inside a bracket from depth N-1, 
    # the parent bracket should extend to include the child's return arrow position
    for (start_row, nesting_depth), (end_row, func_name, src_obj, dst_obj) in spanning_brackets.items():
        # Find all nested messages (higher depth that fall within this bracket)
        for (inner_start_row, inner_depth), (inner_end_row, _, _, _) in spanning_brackets.items():
            if inner_start_row != start_row and start_row < inner_start_row <= end_row and inner_depth > nesting_depth:
                # This inner bracket is nested within the current bracket
                # Extend parent to include inner's return arrow position
                inner_return_y = row_to_y[inner_end_row] + RETURN_ARROW_SPACING
                if parent_scope_end_y[(start_row, nesting_depth)] < inner_return_y:
                    parent_scope_end_y[(start_row, nesting_depth)] = inner_return_y
    
    # Update bracket_render_info with final parent scope end positions
    for (start_row, nesting_depth) in bracket_render_info:
        x, y_start, _, func_name, func_tooltip, nesting_depth_val, src_obj, dst_obj = bracket_render_info[(start_row, nesting_depth)]
        # Use parent_scope_end_y for the final y_end (already includes return arrow spacing)
        bracket_render_info[(start_row, nesting_depth)] = (x, y_start, parent_scope_end_y[(start_row, nesting_depth)], func_name, func_tooltip, nesting_depth_val, src_obj, dst_obj)
    
    # Render spanning brackets now that end positions are calculated
    for (start_row, nesting_depth), (x, y_start, y_end, func_name, func_tooltip, nesting_depth_val, src_obj, dst_obj) in bracket_render_info.items():
        # Only show label for self-messages (where src and dst are the same object)
        is_self_message = (src_obj == dst_obj)
        # For cross-object messages, the bracket on the destination object is depth 0 (new scope)
        bracket_depth = nesting_depth_val if is_self_message else 0
        bracket_elements = render_spanning_bracket(x, y_start, y_end, func_name, func_tooltip, bracket_depth, is_self_message)
        svg.extend(bracket_elements)

    # Track deferred return arrows: end_row -> list of (x1, x2, label, tooltip, y_pos)
    deferred_return_arrows = {}
    
    # Draw steps
    
    for step in filtered_steps:
        # Skip if lanes aren't in our filtered set
        if step.src_obj not in lane_positions or step.dst_obj not in lane_positions:
            continue
        
        y = step.y
        
        src_lane = step.src_obj
        dst_lane = step.dst_obj
        func_name = step.function

        # Calculate arrow endpoints at object lifelines (always)
        # Nesting depth is shown visually via bracket positions, but arrows always connect lifelines
        x1 = lane_positions[src_lane]
        x2 = lane_positions[dst_lane]

        func_def = model.get_function(src_lane, func_name)

        # Build tooltip with comprehensive information
        func_tooltip = ""
        if func_def:
            func_tooltip = func_def.description
            # Add parameter descriptions to tooltip
            if func_def.params and step.param_values:
                param_descriptions = []
                for i, param_def in enumerate(func_def.params):
                    if i < len(step.param_values):
                        value = strip_code_wrappers(step.param_values[i])
                        param_descriptions.append(f"{param_def.name}={value} ({param_def.description})")
                if param_descriptions:
                    func_tooltip += "\n\nParameters:\n" + "\n".join(param_descriptions)
            elif func_def.params:
                param_descriptions = [f"{p.name} ({p.description})" for p in func_def.params]
                if param_descriptions:
                    func_tooltip += "\n\nParameters:\n" + "\n".join(param_descriptions)

        # Build forward arrow label based on verbosity level
        # Low: function name only
        # Normal: function name + params + return value
        # High: normal + descriptions (as tooltips)
        if verbosity_level.lower() == "low":
            label = func_name
            has_code_syntax = False
        else:  # Normal or High
            # Include params in parentheses (value only, no param names)
            param_labels = []
            has_code_syntax = False  # Track if any param has code() syntax
            if func_def and step.param_values:
                for i, param_def in enumerate(func_def.params):
                    if i < len(step.param_values):
                        # Check if original value has backtick syntax before stripping
                        if "`" in step.param_values[i]:
                            has_code_syntax = True
                        param_labels.append(strip_code_wrappers(step.param_values[i]))
            elif func_def:
                # If no values provided, just show param names
                param_labels = [p.name for p in func_def.params]
            
            label = func_name + "(" + ", ".join(param_labels) + ")"

        # Calculate function note position early (if present)
        function_note_x = None
        note_tooltip = None
        if step.function_note and verbosity_level.lower() == "high":
            # Store tooltip for when we render the note box
            note_tooltip = f"{step.function_note.note_type}: {step.function_note.content}"

        # Handle self-messages (where source and destination are the same)
        if x1 == x2:
            # All self-messages use spanning brackets
            # The spanning bracket is rendered by render_spanning_bracket() with label text
            # So we skip rendering the message arrow text label here to avoid duplication
            pass
        else:
            # Regular message between different objects
            # Forward arrow (no shortening needed - note is now inline with label)
            svg.append(f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" '
                       f'stroke="#000" marker-end="url(#arrow)"/>')

            # Forward arrow text with white background box
            # Use monospaced font for accurate character width calculation
            # Calculate total width: 1-char space + message label + gap + optional note + 1-char space
            label_width = len(label) * MONOSPACE_CHAR_WIDTH
            
            # If note exists, include it with gap for centering
            note_width = 0
            label_note_gap = 0
            if step.function_note and verbosity_level.lower() == "high":
                note_width = NOTE_BOX_WIDTH  # 2-char note width
                label_note_gap = LABEL_NOTE_GAP  # Gap to prevent overlap
            
            # Total width for centering: spacing + label + gap + note + spacing
            total_width_for_centering = MESSAGE_SPACING + label_width + label_note_gap + note_width + MESSAGE_SPACING
            
            # Center the combined width on the arrow
            total_left_x = (x1 + x2) / 2 - total_width_for_centering / 2
            
            # Label starts after initial spacing
            box_x = total_left_x + MESSAGE_SPACING
            text_width = label_width
            
            # White background box spans the entire message + gap + note (if present)
            # This makes the note appear as part of the message
            box_width = label_width + label_note_gap + note_width
            
            box_padding = 0
            box_y = y - 7
            box_height = 14
            
            # DEBUG: Add comment showing label box positioning
            svg.append(f'<!-- Label "{label}": box_x={box_x:.1f}px, box_width={box_width:.1f}px, ends_at={box_x + box_width:.1f}px -->')
            
            # Draw white rectangle behind text (rendered first, so it goes behind)
            # Check if label contains code() syntax - if so, use grey background instead
            label_display = label  # label is already stripped
            bg_color = CODE_BACKGROUND_COLOR if has_code_syntax else "white"
            svg.append(f'<rect x="{box_x}" y="{box_y}" width="{box_width}" height="{box_height}" '
                       f'fill="{bg_color}" stroke="none"/>')
            
            # Draw text on top of the white box, vertically centered on the arrow
            # Text x position should be at the center of the label box
            text_x = box_x + text_width / 2
            text_color = CODE_TEXT_COLOR if has_code_syntax else "black"
            text_elem = f'<text x="{text_x}" y="{y}" text-anchor="middle" font-family="monospace" font-size="12" dominant-baseline="middle" fill="{text_color}">{label_display}</text>'
            if func_tooltip:
                # Escape special characters in tooltip
                func_tooltip_escaped = func_tooltip.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\"", "&quot;")
                text_elem = text_elem.replace('>', f'><title>{func_tooltip_escaped}</title>', 1)
            elif note_tooltip:
                # Use note tooltip if no function tooltip
                note_tooltip_escaped = note_tooltip.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\"", "&quot;")
                text_elem = text_elem.replace('>', f'><title>{note_tooltip_escaped}</title>', 1)
            svg.append(text_elem)

            # Render function note box if present (High verbosity only)
            note_box_end_x = None
            if step.function_note and verbosity_level.lower() == "high":
                # Position note box immediately after label with no gap
                label_end_x = box_x + label_width
                # Note center: label_end_x + NOTE_BOX_WIDTH/2 (directly adjacent, no LABEL_NOTE_GAP)
                note_x = label_end_x + NOTE_BOX_WIDTH / 2
                note_box_end_x = label_end_x + NOTE_BOX_WIDTH
                note_y = y - 7  # Match the vertical center of the text
                note_elements = create_note_box(note_x, note_y, step.function_note, show_text=False)
                svg.extend(note_elements)

        # Return arrow with tooltip (only for non-self messages and Normal/High verbosity)
        # Self-messages skip the separate return arrow since the loop's return edge serves that function
        if x1 != x2 and verbosity_level.lower() != "low" and func_def and func_def.returns and step.return_value:
            # Use the first return value name with the provided value
            ret_name = func_def.returns[0].name if func_def.returns else "Value"
            ret_label = step.return_value  # Just show the value, not the name
            ret_def = func_def.returns[0]
            
            # Check if return value has backtick syntax
            has_return_code_syntax = "`" in step.return_value
            
            # Build return value tooltip
            ret_tooltip = f"{ret_name}: {ret_def.description}" if ret_def else ""
            
            # Check if this message has a deferred return row (spanning bracket)
            return_row = step_return_row.get(id(step), step.row)  # Use actual return row if deferred, else current row
            
            # Return arrow positioned below message with 10px spacing
            # This spacing applies to both immediate and deferred returns
            if return_row != step.row:
                # Deferred: use the end_row's y position plus spacing
                y_ret = row_to_y[return_row] + 12
            else:
                # Position below message
                y_ret = y + 12

            # If deferred, store for later rendering at the end_row
            if return_row != step.row:
                if return_row not in deferred_return_arrows:
                    deferred_return_arrows[return_row] = []
                # Return arrow always goes from x2 (source) to x1 (destination)
                deferred_return_arrows[return_row].append((x1, x2, ret_label, ret_tooltip, y_ret, has_return_code_syntax))
            else:
                # Render immediately
                # Return arrow always goes from x2 (source) back to x1 (destination)
                svg.append(f'<line x1="{x2}" y1="{y_ret}" x2="{x1}" y2="{y_ret}" '
                           f'stroke="#000" stroke-dasharray="5,5" '
                           f'marker-end="url(#arrow)"/>')
                
                # Return arrow text centered over the arrow (arrow passes through text center)
                # Text baseline positioned so arrow passes through visual center of text
                ret_text_baseline_y = y_ret + 4  # Visual center of 12px text is roughly 4px above baseline
                ret_label_display = strip_code_wrappers(ret_label)
                ret_text_color = CODE_TEXT_COLOR if has_return_code_syntax else "black"
                
                # Draw background rectangle if backtick syntax is present
                if has_return_code_syntax:
                    ret_text_width = len(ret_label_display) * MONOSPACE_CHAR_WIDTH
                    ret_box_x = (x1 + x2) / 2 - ret_text_width / 2
                    ret_box_y = ret_text_baseline_y - 7
                    ret_box_height = 14
                    svg.append(f'<rect x="{ret_box_x}" y="{ret_box_y}" width="{ret_text_width}" height="{ret_box_height}" '
                               f'fill="{CODE_BACKGROUND_COLOR}" stroke="none"/>')
                    # With grey background, just render text directly without white stroke
                    ret_text_elem = f'<text x="{(x1 + x2)/2}" y="{ret_text_baseline_y}" text-anchor="middle" font-family="monospace" font-size="12" fill="{ret_text_color}">{ret_label_display}</text>'
                else:
                    # Without background, use white stroke for visibility over dashed line
                    ret_text_elem = f'<text x="{(x1 + x2)/2}" y="{ret_text_baseline_y}" text-anchor="middle" font-family="monospace" font-size="12" fill="white" stroke="white" stroke-width="4" paint-order="stroke">{ret_label_display}</text>'
                    # Add the actual text on top
                    ret_text_elem += f'<text x="{(x1 + x2)/2}" y="{ret_text_baseline_y}" text-anchor="middle" font-family="monospace" font-size="12" fill="{ret_text_color}">{ret_label_display}</text>'
                
                if ret_tooltip:
                    ret_tooltip_escaped = ret_tooltip.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\"", "&quot;")
                    ret_text_elem = ret_text_elem.replace('>', f'><title>{ret_tooltip_escaped}</title>', 1)
                svg.append(ret_text_elem)
        
        # Defer lane notes for this step to render at the end (so they appear on top)
        if verbosity_level.lower() == "high":
            for lane_name, note in step.lane_notes.items():
                if lane_name in lane_positions:
                    x_lane = lane_positions[lane_name]
                    note_y = y + 60  # Position below state changes (which are at y+50) with space to next function
                    
                    # Check if this note's lane is the destination of any spanning bracket that overlaps with this step's rows
                    for (bracket_start_row, bracket_depth), (bracket_end_row, bracket_func_name, bracket_src, bracket_dst) in spanning_brackets.items():
                        # Spanning brackets appear on the destination lane
                        if lane_name == bracket_dst:
                            # Check if this step falls within the bracket's row range
                            if step.row >= bracket_start_row and step.row <= bracket_end_row:
                                # Position note well below the bracket's end row to avoid overlap
                                bracket_end_y = row_to_y[bracket_end_row]
                                note_y = max(note_y, bracket_end_y + 85)  # 85px to clear the bracket (increased from 70px)
                    
                    # Defer note rendering to later (will appear on top)
                    deferred_notes.append((x_lane, note_y, note))
        
        # Render state changes after this step
        if step.state_changes:
            state_y = y + 50
            for lane_name, new_state in step.state_changes.items():
                if lane_name in lane_positions:
                    current_states[lane_name] = new_state
                    x = lane_positions[lane_name]
                    
                    # Get state description
                    state_machine = model.get_state_machine(lane_name)
                    state_def = None
                    if state_machine:
                        for s in state_machine.states:
                            if s.name == new_state:
                                state_def = s
                                break
                    
                    state_desc = state_def.description if state_def else ""
                    state_elements = create_state_box(x, state_y, new_state, state_desc)
                    svg.extend(state_elements)

    # Render deferred return arrows (for messages with spanning brackets)
    for end_row in sorted(deferred_return_arrows.keys()):
        y_ret = row_to_y[end_row] + 12  # Add 12px spacing below the last message row
        for item in deferred_return_arrows[end_row]:
            # Unpack - may have 5 or 6 elements depending on when it was stored
            x1, x2, ret_label, ret_tooltip = item[:4]
            has_return_code_syntax = item[5] if len(item) > 5 else "`" in ret_label
            
            svg.append(f'<line x1="{x2}" y1="{y_ret}" x2="{x1}" y2="{y_ret}" '
                       f'stroke="#000" stroke-dasharray="5,5" '
                       f'marker-end="url(#arrow)"/>')
            
            # Return arrow text centered over the arrow
            ret_text_baseline_y = y_ret + 4
            ret_label_display = strip_code_wrappers(ret_label)
            ret_text_color = CODE_TEXT_COLOR if has_return_code_syntax else "black"
            
            # Draw background rectangle if backtick syntax is present
            if has_return_code_syntax:
                ret_text_width = len(ret_label_display) * MONOSPACE_CHAR_WIDTH
                ret_box_x = (x1 + x2) / 2 - ret_text_width / 2
                ret_box_y = ret_text_baseline_y - 7
                ret_box_height = 14
                svg.append(f'<rect x="{ret_box_x}" y="{ret_box_y}" width="{ret_text_width}" height="{ret_box_height}" '
                           f'fill="{CODE_BACKGROUND_COLOR}" stroke="none"/>')
                # With grey background, just render text directly without white stroke
                ret_text_elem = f'<text x="{(x1 + x2)/2}" y="{ret_text_baseline_y}" text-anchor="middle" font-family="monospace" font-size="12" fill="{ret_text_color}">{ret_label_display}</text>'
            else:
                # Without background, use white stroke for visibility over dashed line
                ret_text_elem = f'<text x="{(x1 + x2)/2}" y="{ret_text_baseline_y}" text-anchor="middle" font-family="monospace" font-size="12" fill="white" stroke="white" stroke-width="4" paint-order="stroke">{ret_label_display}</text>'
                ret_text_elem += f'<text x="{(x1 + x2)/2}" y="{ret_text_baseline_y}" text-anchor="middle" font-family="monospace" font-size="12" fill="{ret_text_color}">{ret_label_display}</text>'
            
            if ret_tooltip:
                ret_tooltip_escaped = ret_tooltip.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\"", "&quot;")
                ret_text_elem = ret_text_elem.replace('>', f'><title>{ret_tooltip_escaped}</title>', 1)
            svg.append(ret_text_elem)

    # Render deferred notes at the end so they always appear on top
    # Add 4px spacing before each note to prevent overlap with other elements
    NOTE_VERTICAL_SPACING = 4
    for x_lane, note_y, note in deferred_notes:
        spaced_note_y = note_y + NOTE_VERTICAL_SPACING
        note_elements = create_note_box(x_lane, spaced_note_y, note, show_text=False)
        svg.extend(note_elements)

    # Add render version in bottom right corner for cache debugging
    version_x = width - 8
    version_y = height + top_margin - 5
    svg.append(f'<text x="{version_x}" y="{version_y}" text-anchor="end" font-family="Arial" '
               f'font-size="9" fill="#ccc">v:{render_version}</text>')

    svg.append("</svg>")
    return "\n".join(svg)