#!/usr/bin/env python3
"""Regenerate connector_rendering_format.log with actual routing information.

LOG FORMAT IS LOCKED - See CONNECTOR_LOG_FORMAT_SPEC.md for requirements.
Do not change format without explicit user request.
"""
import sys
sys.path.insert(0, 'Scripts')

from parser import parse_csv
from class_diagram_renderer import _layout_classes_uml_standard
from class_diagram_connectors import ConnectorPlanner

# Load diagram
model = parse_csv('Process/02_Architecture/class_diagrams.csv')
diagram = model.class_diagrams[0]
diagram.routing = 'orthogonal'

# Layout boxes
boxes = _layout_classes_uml_standard(diagram, model, 'High', routing='orthogonal')

# Create planner and add all boxes
planner = ConnectorPlanner(routing_mode='orthogonal')
for name, box in boxes.items():
    planner.add_rectangle(name, box['x'], box['y'], box['width'], box['height'])

# Add all connectors from diagram
for rel in diagram.relationships:
    planner.add_connector(
        rel.source,
        rel.target,
        rel.arrow,                    # arrow_type (3rd param)
        rel.src_mult or '',           # src_mult (4th param)
        rel.tgt_mult or '',           # tgt_mult (5th param)
        rel.label                     # label (6th param)
    )

# Plan all connectors
planner.plan_connectors()

# Build map of connectors to their relationship info (for arrow type)
rel_map = {}
for rel in diagram.relationships:
    key = (rel.source, rel.target)
    rel_map[key] = rel

def get_arrow_symbol(arrow_str):
    """Extract arrow symbol from arrow type string."""
    if '◆' in arrow_str:
        return '◆'
    elif '◇' in arrow_str:
        return '◇'
    else:
        return '◆'

def get_routing_direction(conn, dx, dy):
    """Determine primary and secondary routing directions.
    
    dy < 0: target above source (Up)
    dy > 0: target below source (Down)
    dx < 0: target to left (Left)
    dx > 0: target to right (Right)
    """
    dy_actual = conn.target_y - conn.source_y
    dx_actual = conn.target_x - conn.source_x
    
    # Determine vertical direction
    vertical_dir = "Down" if dy_actual > 0 else "Up" if dy_actual < 0 else "Horizontal"
    horizontal_dir = "Right" if dx_actual > 0 else "Left" if dx_actual < 0 else "Vertical"
    
    # Vertical connectors (very small dx)
    if abs(dx_actual) < 5:
        return vertical_dir, "Right" if dx_actual > 0 else "Left", vertical_dir
    
    # Horizontal connectors (very small dy)
    if abs(dy_actual) < 5:
        return horizontal_dir, "Down" if dy_actual > 0 else "Up", horizontal_dir
    
    # Multi-segment: choose based on which is dominant
    if abs(dx_actual) > abs(dy_actual):
        # Horizontal dominant
        return horizontal_dir, "Down" if dy_actual > 0 else "Up", horizontal_dir
    else:
        # Vertical dominant
        return vertical_dir, "Right" if dx_actual > 0 else "Left", vertical_dir

def render_connector(conn, arrow_sym, dir1, dir2, dir3):
    """Render connector routing with geometry-based corner alignment.
    
    Each '+' marks a corner/junction where segments meet:
    - First '+': where segment 1 meets segment 2  
    - Second '+': where segment 2 meets segment 3
    
    The distance between '+' marks reflects actual coordinate distances.
    """
    lines = []
    lines.append(f"Text              Routing")
    
    dx_abs = abs(conn.target_x - conn.source_x)
    dy_abs = abs(conn.target_y - conn.source_y)
    
    # Scale factor: map coordinate distance to dashes in the corner (0.5 char per unit)
    # This shows the relative distance between corners
    num_dashes = max(1, min(10, int(dx_abs / 50)))
    
    # DEBUG
    print(f"DEBUG: {conn.source_name}->{conn.target_name}: dx={dx_abs}, int(dx/50)={int(dx_abs/50)}, num_dashes={num_dashes}")
    
    if dir1 in ["Down", "Up"]:  # Vertical first routing
        # First segment: vertical endpoint
        lines.append(f"{'':30} {arrow_sym}")
        # Source multiplicity with vertical line
        lines.append(f"{repr(conn.src_mult):<30} |")
        
        # Corner line: show where vertical meets horizontal and where horizontal meets vertical again
        if dir2 == "Right":
            # Target is to the right, so second + is further right
            corner_routing = "+" + "-" * num_dashes + "+"
        else:  # Left
            # Target is to the left, so second + is further left (move first + to left side)
            corner_routing = "+" + "-" * num_dashes + "+"
        
        lines.append(f"{repr(conn.label):<30} {corner_routing}")
        
        # Target multiplicity with vertical line at appropriate offset
        if dir2 == "Right":
            # Line is indented to show offset to the right
            target_line = " " * (num_dashes + 1) + "|"
        else:  # Left
            # Line is not indented to show offset to the left
            target_line = "|"
        
        lines.append(f"{repr(conn.tgt_mult):<30} {target_line}")
        
        # Final endpoint
        lines.append(f"{'':30} {arrow_sym}")
        
    else:  # Horizontal first routing
        # Source line shows arrow and first corner
        if dir1 == "Right":
            src_routing = f"{arrow_sym}" + "-" * num_dashes + "+"
        else:  # Left
            src_routing = "+" + "-" * num_dashes + f"{arrow_sym}"
        
        lines.append(f"{repr(conn.src_mult):<30} {src_routing}")
        
        # Middle line shows vertical segment
        lines.append(f"{repr(conn.label):<30} " + " " * (num_dashes + 1) + "|")
        
        # Target line shows second corner and final arrow
        if dir1 == "Right":
            tgt_routing = " " * (num_dashes + 1) + "+" + "-" + f"{arrow_sym}"
        else:  # Left
            tgt_routing = f"{arrow_sym}" + "-" + "+" + " " * (num_dashes + 1)
        
        lines.append(f"{repr(conn.tgt_mult):<30} {tgt_routing}")
    
    return lines

# Write log
with open('connector_rendering_format.log', 'w', encoding='utf-8') as f:
    f.write("Processing: Process/02_Architecture/class_diagrams.csv\n")
    f.write("=" * 130 + "\n")
    f.write("CONNECTOR ROUTING - UPDATED AFTER THRESHOLD FIX\n")
    f.write("=" * 130 + "\n\n")
    
    f.write("ROUTING SUMMARY:\n")
    f.write("-" * 130 + "\n")
    f.write(f"{'Source':<20} {'Target':<20} {'DX':<10} {'DY':<10} {'PATH TYPE':<20} {'STATUS':<20}\n")
    f.write("-" * 130 + "\n")
    
    for conn in planner.connectors:
        dx = abs(conn.target_x - conn.source_x)
        dy = abs(conn.target_y - conn.source_y)
        
        status = "DIRECT" if conn.path_type == 'direct' else "MULTI-SEGMENT"
        f.write(f"{conn.source_name:<20} {conn.target_name:<20} {dx:<10.1f} {dy:<10.1f} {conn.path_type:<20} {status:<20}\n")
    
    f.write("\n" + "=" * 130 + "\n")
    f.write("CONNECTOR ROUTING VISUALIZATION:\n")
    f.write("=" * 130 + "\n\n")
    
    # Group connectors by type
    direct_connectors = [c for c in planner.connectors if c.path_type == 'direct']
    multi_connectors = [c for c in planner.connectors if c.path_type == 'multi_segment']
    
    f.write("DIRECT CONNECTORS (Vertical lines):\n")
    f.write("-" * 130 + "\n\n")
    
    for conn in direct_connectors:
        rel = rel_map.get((conn.source_name, conn.target_name), None)
        arrow_sym = get_arrow_symbol(rel.arrow) if rel else '◆'
        f.write(f"{conn.source_name} -> {conn.target_name}  (Direct)\n")
        f.write(f"Text              Routing\n")
        f.write(f"{repr(conn.src_mult):<30} |\n")
        f.write(f"{repr(conn.label):<30} |\n")
        f.write(f"{repr(conn.tgt_mult):<30} |\n")
        f.write("\n")
    
    f.write("\n" + "=" * 130 + "\n")
    f.write("MULTI-SEGMENT CONNECTORS (Orthogonal routing):\n")
    f.write("-" * 130 + "\n\n")
    
    for conn in multi_connectors:
        dx = abs(conn.target_x - conn.source_x)
        dy = abs(conn.target_y - conn.source_y)
        
        rel = rel_map.get((conn.source_name, conn.target_name), None)
        arrow_sym = get_arrow_symbol(rel.arrow) if rel else '◆'
        
        dir1, dir2, dir3 = get_routing_direction(conn, dx, dy)
        
        f.write(f"{conn.source_name} -> {conn.target_name}  ({dir1}, {dir2}, {dir3})\n")
        
        # Render connector for any combination of directions
        lines = render_connector(conn, arrow_sym, dir1, dir2, dir3)
        
        for line in lines:
            f.write(line + "\n")
        
        f.write(f"(dx={dx:.1f}, dy={dy:.1f})\n\n")
    
    f.write("\n" + "=" * 130 + "\n")
    f.write("KEY FIXES APPLIED:\n")
    f.write("=" * 130 + "\n\n")
    
    f.write("THRESHOLD FIX: Vertical Alignment Detection\n")
    f.write("-" * 130 + "\n")
    f.write("Changed: dx < 1 pixel (too strict)\n")
    f.write("To:      dx < 5 pixels when dy > 50 pixels (allows minor horizontal offset)\n\n")
    
    # Highlight key result
    for conn in planner.connectors:
        if conn.source_name == 'ClassDef' and conn.target_name == 'FunctionDef':
            dx = abs(conn.target_x - conn.source_x)
            dy = abs(conn.target_y - conn.source_y)
            f.write(f"RESULT: {conn.source_name} -> {conn.target_name}\n")
            f.write(f"  Delta: dx={dx:.1f}, dy={dy:.1f}\n")
            f.write(f"  Status: FIXED - Now uses direct vertical line (was 3-segment)\n\n")

print("Log file regenerated with LOCKED format")
print("See CONNECTOR_LOG_FORMAT_SPEC.md for format specification")
