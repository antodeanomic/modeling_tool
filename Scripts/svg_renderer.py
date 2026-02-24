from model import Model, SequenceDef, NoteDef

LANE_WIDTH = 200
ROW_HEIGHT = 60
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

def create_self_message_loop(x: float, y: float, label: str, tooltip: str = "") -> list:
    """Create a self-message (call to same object) as a rectangular loop.
    
    A self-message is drawn as a rectangle extending to the right of the lane,
    with the label positioned in the middle of the top horizontal segment.
    
    Args:
        x: X position of the lane (center of lifeline)
        y: Y position of the message
        label: Text label for the message
        tooltip: Optional tooltip content
    
    Returns list of SVG elements as strings.
    """
    LOOP_WIDTH = 30  # Make equal to LOOP_HEIGHT for balanced proportions
    LOOP_HEIGHT = 30  # Vertical distance for the loop
    
    svg_parts = []
    
    # Calculate positions for the loop
    right_x = x + LOOP_WIDTH
    bottom_y = y + LOOP_HEIGHT
    
    # Draw the loop: vertical line down, horizontal right, vertical down, horizontal back
    # Vertical line going down from source
    svg_parts.append(f'<line x1="{x}" y1="{y}" x2="{x}" y2="{y + LOOP_HEIGHT/2}" stroke="#000" stroke-width="1"/>')
    
    # Horizontal line extending right
    svg_parts.append(f'<line x1="{x}" y1="{y + LOOP_HEIGHT/2}" x2="{right_x}" y2="{y + LOOP_HEIGHT/2}" stroke="#000" stroke-width="1"/>')
    
    # Vertical line extending down
    svg_parts.append(f'<line x1="{right_x}" y1="{y + LOOP_HEIGHT/2}" x2="{right_x}" y2="{bottom_y}" stroke="#000" stroke-width="1"/>')
    
    # Horizontal line returning to lifeline with arrow
    svg_parts.append(f'<line x1="{right_x}" y1="{bottom_y}" x2="{x}" y2="{bottom_y}" stroke="#000" stroke-width="1" marker-end="url(#arrow)"/>')
    
    # Draw label on the top horizontal segment
    label_y = y + LOOP_HEIGHT/2 - 5
    label_x = x + LOOP_WIDTH/2
    text_elem = f'<text x="{label_x}" y="{label_y}" text-anchor="middle" font-family="Arial" font-size="12">{label}</text>'
    if tooltip:
        tooltip_escaped = tooltip.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\"", "&quot;")
        text_elem = text_elem.replace('>', f'><title>{tooltip_escaped}</title>', 1)
    svg_parts.append(text_elem)
    
    # Draw return label to the right of vertical segment, aligned with bottom horizontal
    return_label_x = right_x + 8  # Clear margin to the right of vertical line
    return_label_y = y + LOOP_HEIGHT - 3  # Aligned with bottom horizontal (vertical segment)
    return_text_elem = f'<text x="{return_label_x}" y="{return_label_y}" font-family="Arial" font-size="11" fill="#666">{label}</text>'
    if tooltip:
        tooltip_escaped = tooltip.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\"", "&quot;")
        return_text_elem = return_text_elem.replace('>', f'><title>return: {tooltip_escaped}</title>', 1)
    svg_parts.append(return_text_elem)
    
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
        row_to_y[row_num] = 120 + row_index * ROW_HEIGHT
    
    # Store Y position for each filtered step
    for step in filtered_steps:
        step.y = row_to_y[step.row]

    total_rows = len(row_to_y)
    height = (total_rows + 3) * ROW_HEIGHT
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

    # Draw steps
    # Track self-messages per row for vertical offset
    self_message_count = {}  # Maps row number to count of self-messages processed
    
    for step in filtered_steps:
        # Skip if lanes aren't in our filtered set
        if step.src_obj not in lane_positions or step.dst_obj not in lane_positions:
            continue
        
        y = step.y
        
        # For self-messages on the same row, apply vertical offset
        if step.src_obj == step.dst_obj:
            if step.row not in self_message_count:
                self_message_count[step.row] = 0
            else:
                self_message_count[step.row] += 1
            # Apply offset for each subsequent self-message on the same row
            # Each self-message is 30 pixels tall (LOOP_HEIGHT) plus 20 pixel spacing
            y += self_message_count[step.row] * 50
        
        src_lane = step.src_obj
        dst_lane = step.dst_obj
        func_name = step.function

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
            # Self-message: draw as a rectangular loop
            self_msg_elements = create_self_message_loop(x1, y, label, func_tooltip)
            svg.extend(self_msg_elements)
        else:
            # Regular message between different objects
            # Forward arrow
            svg.append(f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" '
                       f'stroke="#000" marker-end="url(#arrow)"/>')

            # Forward arrow text with tooltip
            text_elem = f'<text x="{(x1 + x2)/2}" y="{y - 10}" text-anchor="middle" font-family="Arial" font-size="12">{label}</text>'
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
            
            y_ret = y + 30

            svg.append(f'<line x1="{x2}" y1="{y_ret}" x2="{x1}" y2="{y_ret}" '
                       f'stroke="#000" stroke-dasharray="5,5" '
                       f'marker-end="url(#arrow)"/>')
            
            # Return arrow text overlaps the arrow to save vertical space
            ret_text_elem = f'<text x="{(x1 + x2)/2}" y="{y_ret - 2}" text-anchor="middle" font-family="Arial" font-size="12" fill="white" stroke="white" stroke-width="4" paint-order="stroke">{ret_label}</text>'
            # Add the actual text on top
            ret_text_elem += f'<text x="{(x1 + x2)/2}" y="{y_ret - 2}" text-anchor="middle" font-family="Arial" font-size="12">{ret_label}</text>'
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

    svg.append("</svg>")
    return "\n".join(svg)