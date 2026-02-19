from model import Model, SequenceDef

LANE_WIDTH = 200
ROW_HEIGHT = 80
PARTICIPANT_BOX_WIDTH = 140
PARTICIPANT_BOX_HEIGHT = 40

def render_svg(model: Model, seq: SequenceDef, verbosity_level="High") -> str:
    if not seq.lanes:
        raise ValueError("Sequence has no lanes. Did you forget SequenceObjects?")

    lanes = seq.lanes
    lane_positions = {lane: i * LANE_WIDTH + 100 for i, lane in enumerate(lanes)}

    total_rows = len(seq.steps)
    height = (total_rows + 3) * ROW_HEIGHT
    width = max(lane_positions.values()) + 200

    svg = []
    svg.append(f'<svg width="{width}" height="{height}" '
               f'xmlns="http://www.w3.org/2000/svg">')

    svg.append("""
    <defs>
      <marker id="arrow" markerWidth="10" markerHeight="10" 
              refX="10" refY="3" orient="auto" markerUnits="strokeWidth">
        <path d="M0,0 L0,6 L9,3 z" fill="#000" />
      </marker>
    </defs>
    """)

    # Draw participants
    for lane, x in lane_positions.items():
        svg.append(f'<rect x="{x - PARTICIPANT_BOX_WIDTH/2}" y="20" '
                   f'width="{PARTICIPANT_BOX_WIDTH}" height="{PARTICIPANT_BOX_HEIGHT}" '
                   f'rx="6" ry="6" fill="#e0e0e0" stroke="#000"/>')
        svg.append(f'<text x="{x}" y="45" text-anchor="middle" '
                   f'font-family="Arial" font-size="14">{lane}</text>')

        svg.append(f'<line x1="{x}" y1="60" x2="{x}" y2="{height - 20}" '
                   f'stroke="#888" stroke-dasharray="4,4"/>')

    # Draw steps
    for row_index, step in enumerate(seq.steps):
        y = 120 + row_index * ROW_HEIGHT

        cleaned = [(i, func.strip()) for i, func in enumerate(step)]
        filled = [(i, f) for i, f in cleaned if f != ""]

        if len(filled) < 1:
            continue

        src_index = filled[0][0]
        func_name = filled[1][1] if len(filled) > 1 else filled[0][1]
        dst_index = filled[1][0] if len(filled) > 1 else src_index + 1

        src_lane = lanes[src_index]
        dst_lane = lanes[dst_index]

        x1 = lane_positions[src_lane]
        x2 = lane_positions[dst_lane]

        func_def = model.get_function(src_lane, func_name)

        if func_def:
            params = [p.name for p in func_def.params]
            label = func_name + "(" + ", ".join(params) + ")"
        else:
            label = func_name + "()"

        # Forward arrow
        svg.append(f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" '
                   f'stroke="#000" marker-end="url(#arrow)"/>')

        svg.append(f'<text x="{(x1 + x2)/2}" y="{y - 10}" '
                   f'text-anchor="middle" font-family="Arial" '
                   f'font-size="12">{label}</text>')

        # Return arrow
        if func_def and func_def.returns:
            ret = ", ".join([r.name for r in func_def.returns])
            y_ret = y + 30

            svg.append(f'<line x1="{x2}" y1="{y_ret}" x2="{x1}" y2="{y_ret}" '
                       f'stroke="#000" stroke-dasharray="5,5" '
                       f'marker-end="url(#arrow)"/>')

            svg.append(f'<text x="{(x1 + x2)/2}" y="{y_ret - 10}" '
                       f'text-anchor="middle" font-family="Arial" '
                       f'font-size="12">{ret}</text>')

    svg.append("</svg>")
    return "\n".join(svg)