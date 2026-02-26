from model import Model, SequenceDef, NoteDef

FONT_SIZE = 12  # Font size for all text labels
ROW_HEIGHT = FONT_SIZE * 2  # Spacing for consecutive message rows (2x font height)
ROW_SPACING = 6  # Extra spacing between rows
LANE_WIDTH = 200
PARTICIPANT_BOX_WIDTH = 140
PARTICIPANT_BOX_HEIGHT = 40
STATE_BOX_PADDING = 6
STATE_TEXT_SIZE = 13
NOTE_BOX_WIDTH = 17
NOTE_BOX_HEIGHT = 13
NOTE_FOLD_SIZE = 2

# Note type colors
NOTE_COLORS = {
    "Info": {"fill": "#E3F2FD", "stroke": "#1976D2", "icon": "ℹ"},
    "Warning": {"fill": "#FFF3E0", "stroke": "#F57C00", "icon": "⚠"},
    "Error": {"fill": "#FFEBEE", "stroke": "#D32F2F", "icon": "✕"}
}

def measure_text_width(text: str, font_size: float = 11) -> float:
    """Rough estimate of text width in SVG (monospace-ish)."""
    return len(text) * (font_size * 0.6)

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

def create_note_box(x: float, y: float, note: NoteDef, show_text: bool = False) -> list:
    """Create SVG elements for a note box with UML note style (folded corner).
    
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
    
    # Draw main rectangle
    rect = f'<rect x="{left}" y="{y}" width="{NOTE_BOX_WIDTH}" height="{NOTE_BOX_HEIGHT}" fill="{colors["fill"]}" stroke="{colors["stroke"]}" stroke-width="1"/>'
    if note.content:
        rect = rect.replace('/>', f'><title>{note.content}</title></rect>', 1)
    svg_parts.append(rect)
    
    # Draw folded corner (small triangle in top-right)
    fold_right = left + NOTE_BOX_WIDTH
    fold_points = f"{fold_right - NOTE_FOLD_SIZE},{y} {fold_right},{y} {fold_right},{y + NOTE_FOLD_SIZE}"
    fold = f'<polygon points="{fold_points}" fill="{colors["stroke"]}" opacity="0.3"/>'
    svg_parts.append(fold)
    
    # Draw icon/indicator
    icon_x = left + 3
    icon_y = y + 4
    icon = f'<text x="{icon_x}" y="{icon_y}" font-size="5" font-weight="bold" fill="{colors["stroke"]}" text-anchor="middle">{colors["icon"]}</text>'
    if note.content:
        icon = icon.replace('>', f'><title>{note.content}</title>', 1)
    svg_parts.append(icon)
    
    # If show_text is True, add the content text (truncated to fit)
    if show_text and note.content:
        # Truncate text to fit in the box
        truncated = note.content[:10] + ".." if len(note.content) > 10 else note.content
        text = f'<text x="{x}" y="{y + NOTE_BOX_HEIGHT - 2}" font-size="5" fill="{colors["stroke"]}" text-anchor="middle">{truncated}</text>'
        svg_parts.append(text)
    
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
    RECTANGLE_WIDTH = 2  # 2px wide rectangle for duration indicator
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
        text_elem = f'<text x="{text_x}" y="{text_baseline_y}" text-anchor="end" font-family="Arial" font-size="12" fill="#000">{label}</text>'
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

    lane_positions = {lane: i * LANE_WIDTH + 100 for i, lane in enumerate(lanes)}

    # Pre-calculate required lane width based on message text overlap
    # If text overlaps arrow endpoints, increase LANE_WIDTH
    adjusted_lane_width = LANE_WIDTH
    for step in seq.steps:
        func_def = model.get_function(step.src_obj, step.function)
        if func_def and step.src_obj != step.dst_obj:
            # Build label
            param_labels = []
            if step.param_values:
                for i, param_def in enumerate(func_def.params):
                    if i < len(step.param_values):
                        param_labels.append(f"{param_def.name}={step.param_values[i]}")
            label = step.function + "(" + ", ".join(param_labels) + ")"
            
            # Measure text width
            text_width = measure_text_width(label, font_size=12)
            
            # Check if text would overlap endpoints
            # Text is centered, so each side extends text_width/2 from center
            src_x = lane_positions.get(step.src_obj, 100)
            dst_x = lane_positions.get(step.dst_obj, 100)
            center_x = (src_x + dst_x) / 2
            
            # Text bounds: [center_x - text_width/2, center_x + text_width/2]
            text_start = center_x - text_width / 2
            text_end = center_x + text_width / 2
            
            # Check overlap with endpoints (with 5px safety margin)
            min_x = min(src_x, dst_x)
            max_x = max(src_x, dst_x)
            
            if text_start < min_x + 5 or text_end > max_x - 5:
                # Text overlaps, need wider lane spacing
                required_width = text_width + 20  # 10px margin on each side
                adjusted_lane_width = max(adjusted_lane_width, required_width)
    
    # Update LANE_WIDTH if needed (but keep minimum)
    effective_lane_width = max(LANE_WIDTH, adjusted_lane_width)
    lane_positions = {lane: i * effective_lane_width + 100 for i, lane in enumerate(lanes)}

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
    sorted_rows = sorted(row_to_steps.keys())
    for row_index, row_num in enumerate(sorted_rows):
        row_to_y[row_num] = 120 + row_index * (ROW_HEIGHT + ROW_SPACING)
    
    # Store Y position for each filtered step
    for step in filtered_steps:
        step.y = row_to_y[step.row]

    total_rows = len(row_to_y)
    # Calculate height based on actual last row position plus padding
    max_y = max(row_to_y.values()) if row_to_y else 120
    height = max_y + 60  # Add 60px padding after last row
    width = max(lane_positions.values()) + 200

    svg = []
    svg.append(f'<svg width="{width}" height="{height}" '
               f'xmlns="http://www.w3.org/2000/svg">')

    # Add white background for visibility in dark mode viewers
    svg.append(f'<rect width="{width}" height="{height}" fill="white"/>')

    svg.append("""
    <defs>
      <marker id="arrow" markerWidth="10" markerHeight="10" 
              refX="10" refY="3" orient="auto" markerUnits="strokeWidth">
        <path d="M0,0 L0,6 L9,3 z" fill="#000" />
      </marker>
    </defs>
    """)

    # Draw participants with tooltip descriptions
    for lane, x in lane_positions.items():
        # Get class description if available
        class_def = None
        for c in model.classes:
            if c.name == lane:
                class_def = c
                break
        
        class_description = class_def.description if class_def else ""
        
        # Draw participant box
        box_elem = f'<rect x="{x - PARTICIPANT_BOX_WIDTH/2}" y="20" width="{PARTICIPANT_BOX_WIDTH}" height="{PARTICIPANT_BOX_HEIGHT}" rx="6" ry="6" fill="#e0e0e0" stroke="#000"/>'
        if class_description:
            box_elem = box_elem.replace('/>', f'><title>{class_description}</title></rect>', 1)
        svg.append(box_elem)
        
        # Draw participant name text
        text_elem = f'<text x="{x}" y="45" text-anchor="middle" font-family="Arial" font-size="14">{lane}</text>'
        if class_description:
            text_elem = text_elem.replace('>', f'><title>{class_description}</title>', 1)
        svg.append(text_elem)

        # Draw lifeline extending to the end of the diagram (based on actual last row position)
        svg.append(f'<line x1="{x}" y1="60" x2="{x}" y2="{height - 20}" '
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
        # Use the full function name from the definition (includes signature for self-messages)
        display_func_name = func_def.name if func_def else func_name
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
                        value = step.param_values[i]
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
        else:  # Normal or High
            # Include params in parentheses
            param_labels = []
            if func_def and step.param_values:
                for i, param_def in enumerate(func_def.params):
                    if i < len(step.param_values):
                        param_labels.append(f"{param_def.name}={step.param_values[i]}")
            elif func_def:
                # If no values provided, just show param names
                param_labels = [p.name for p in func_def.params]
            
            label = func_name + "(" + ", ".join(param_labels) + ")"

        # Handle self-messages (where source and destination are the same)
        if x1 == x2:
            # All self-messages use spanning brackets
            # The spanning bracket is rendered by render_spanning_bracket() with label text
            # So we skip rendering the message arrow text label here to avoid duplication
            pass
        else:
            # Regular message between different objects
            # Forward arrow
            svg.append(f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" '
                       f'stroke="#000" marker-end="url(#arrow)"/>')

            # Forward arrow text with white background box
            # More accurate text width: ~6.2px per character for 12px Arial font
            text_width = len(label) * 6.2
            box_padding = 0
            box_x = (x1 + x2) / 2 - text_width / 2 - box_padding
            box_y = y - 7
            box_width = text_width + (box_padding * 2)
            box_height = 14
            
            # Draw white rectangle behind text (rendered first, so it goes behind)
            svg.append(f'<rect x="{box_x}" y="{box_y}" width="{box_width}" height="{box_height}" '
                       f'fill="white" stroke="none"/>')
            
            # Draw text on top of the white box, vertically centered on the arrow
            text_elem = f'<text x="{(x1 + x2)/2}" y="{y}" text-anchor="middle" font-family="Arial" font-size="12" dominant-baseline="middle">{label}</text>'
            if func_tooltip:
                # Escape special characters in tooltip
                func_tooltip_escaped = func_tooltip.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\"", "&quot;")
                text_elem = text_elem.replace('>', f'><title>{func_tooltip_escaped}</title>', 1)
            svg.append(text_elem)

        # Return arrow with tooltip (only for non-self messages and Normal/High verbosity)
        # Self-messages skip the separate return arrow since the loop's return edge serves that purpose
        if x1 != x2 and verbosity_level.lower() != "low" and func_def and func_def.returns and step.return_value:
            # Use the first return value name with the provided value
            ret_name = func_def.returns[0].name if func_def.returns else "Value"
            ret_label = f"{ret_name}={step.return_value}"
            ret_def = func_def.returns[0]
            
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
                deferred_return_arrows[return_row].append((x1, x2, ret_label, ret_tooltip, y_ret))
            else:
                # Render immediately
                svg.append(f'<line x1="{x2}" y1="{y_ret}" x2="{x1}" y2="{y_ret}" '
                           f'stroke="#000" stroke-dasharray="5,5" '
                           f'marker-end="url(#arrow)"/>')
                
                # Return arrow text centered over the arrow (arrow passes through text center)
                # Text baseline positioned so arrow passes through visual center of text
                ret_text_baseline_y = y_ret + 4  # Visual center of 12px text is roughly 4px above baseline
                ret_text_elem = f'<text x="{(x1 + x2)/2}" y="{ret_text_baseline_y}" text-anchor="middle" font-family="Arial" font-size="12" fill="white" stroke="white" stroke-width="4" paint-order="stroke">{ret_label}</text>'
                # Add the actual text on top
                ret_text_elem += f'<text x="{(x1 + x2)/2}" y="{ret_text_baseline_y}" text-anchor="middle" font-family="Arial" font-size="12">{ret_label}</text>'
                if ret_tooltip:
                    ret_tooltip_escaped = ret_tooltip.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\"", "&quot;")
                    ret_text_elem = ret_text_elem.replace('>', f'><title>{ret_tooltip_escaped}</title>', 1)
                svg.append(ret_text_elem)
        
        # Render function note if present (only in High verbosity)
        if step.function_note and verbosity_level.lower() == "high":
            # Calculate text width to position note to the right of all text
            label_width = measure_text_width(label, font_size=12)
            text_center = (x1 + x2) / 2
            note_x = text_center + (label_width / 2) + 15  # Position after text with padding
            note_y = y - 20
            # Show text inline (we're in high verbosity)
            note_elements = create_note_box(note_x, note_y, step.function_note, show_text=False)
            svg.extend(note_elements)
        
        # Render lane notes for this step (only in High verbosity)
        if verbosity_level.lower() == "high":
            for lane_name, note in step.lane_notes.items():
                if lane_name in lane_positions:
                    x_lane = lane_positions[lane_name]
                    note_y = y + 60  # Position below state changes (which are at y+50) with space to next function
                    # Never show inline text, rely on hover tooltip
                    note_elements = create_note_box(x_lane, note_y, note, show_text=False)
                    svg.extend(note_elements)
        
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
        for x1, x2, ret_label, ret_tooltip, _ in deferred_return_arrows[end_row]:
            svg.append(f'<line x1="{x2}" y1="{y_ret}" x2="{x1}" y2="{y_ret}" '
                       f'stroke="#000" stroke-dasharray="5,5" '
                       f'marker-end="url(#arrow)"/>')
            
            # Return arrow text centered over the arrow
            ret_text_baseline_y = y_ret + 4
            ret_text_elem = f'<text x="{(x1 + x2)/2}" y="{ret_text_baseline_y}" text-anchor="middle" font-family="Arial" font-size="12" fill="white" stroke="white" stroke-width="4" paint-order="stroke">{ret_label}</text>'
            ret_text_elem += f'<text x="{(x1 + x2)/2}" y="{ret_text_baseline_y}" text-anchor="middle" font-family="Arial" font-size="12">{ret_label}</text>'
            if ret_tooltip:
                ret_tooltip_escaped = ret_tooltip.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\"", "&quot;")
                ret_text_elem = ret_text_elem.replace('>', f'><title>{ret_tooltip_escaped}</title>', 1)
            svg.append(ret_text_elem)

    svg.append("</svg>")
    return "\n".join(svg)