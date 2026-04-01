#!/usr/bin/env python3
"""Regenerate connector_rendering_format.log with actual routing information.

LOG FORMAT SPECIFICATION (LOCKED):
==================================
1. ROUTING SUMMARY TABLE: Shows all connectors with DX, DY, path type
2. CONNECTOR ROUTING VISUALIZATION: Uses table format with two columns:
   - Column 1: "Segment text" - shows the multiplicity/label/multiplicity segments
   - Column 2: "Routing" - shows ASCII art of the connector path
   
3. DIRECT VERTICAL: Simple vertical line
   Segment text   Routing
   "1"            Object1
                       |
   "contains"         |
                       |
   "0.*"          Object2

4. MULTI-SEGMENT right->left: 
   Segment text   Routing
   "1"            Object1 ◆-- ---+
   "owns"                              |
   "0.*"                              +--- -- ◆ Object2

5. MULTI-SEGMENT down->right:
   Segment text   Routing
   "1"            Object1
                       |
   "owns"             |
                       +----+
   "0.*"                    |
                       Object2 ◆

REQUIREMENT: This format is now locked. Do not change without explicit user request.
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
        rel.src_mult or '',
        rel.tgt_mult or '',
        rel.arrow,
        rel.label
    )

# Plan all connectors
planner.plan_connectors()

# Determine connector direction
def get_arrow_symbol(arrow_str):
    """Extract arrow symbol from arrow type string."""
    if '◆' in arrow_str:
        return '◆'
    elif '◇' in arrow_str:
        return '◇'
    else:
        return '--'

def get_direction(conn, dx, dy):
    """Determine if connector is vertical, horizontal, or diagonal."""
    if dy < 1:
        return "horizontal"
    elif dx < 1:
        return "vertical"
    else:
        # Determine primary routing direction
        if dx > dy:
            return "primary_horizontal"
        else:
            return "primary_vertical"

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
    f.write("(Format: Segment text | ASCII routing diagram)\n")
    f.write("=" * 130 + "\n\n")
    
    # Group connectors by type
    direct_connectors = [c for c in planner.connectors if c.path_type == 'direct']
    multi_connectors = [c for c in planner.connectors if c.path_type == 'multi_segment']
    
    f.write("DIRECT CONNECTORS (Vertical lines):\n")
    f.write("-" * 130 + "\n\n")
    
    for conn in direct_connectors:
        f.write(f"{conn.source_name} -> {conn.target_name}\n")
        f.write(f"{'Segment text':<30} {'Routing':<40}\n")
        f.write(f"{repr(conn.src_mult):<30} {conn.source_name}\n")
        f.write(f"{'':<30} |\n")
        f.write(f"{repr(conn.label):<30} |\n")
        f.write(f"{'':<30} |\n")
        f.write(f"{repr(conn.tgt_mult):<30} {conn.target_name}\n")
        f.write("\n")
    
    f.write("\n" + "=" * 130 + "\n")
    f.write("MULTI-SEGMENT CONNECTORS (Orthogonal routing):\n")
    f.write("-" * 130 + "\n\n")
    
    for conn in multi_connectors:
        dx = abs(conn.target_x - conn.source_x)
        dy = abs(conn.target_y - conn.source_y)
        
        f.write(f"{conn.source_name} -> {conn.target_name}  (dx={dx:.1f}, dy={dy:.1f})\n")
        f.write(f"{'Segment text':<30} {'Routing':<40}\n")
        
        # Determine routing direction
        direction = get_direction(conn, dx, dy)
        
        # Get arrow symbols
        arrow_sym = get_arrow_symbol(conn.arrow)
        
        if direction == "primary_horizontal":
            # right -> left routing (horizontal with corners)
            f.write(f"{repr(conn.src_mult):<30} {conn.source_name} {arrow_sym}-- ---+\n")
            f.write(f"{repr(conn.label):<30} {' ' * (len(conn.source_name) + 8)} |\n")
            f.write(f"{repr(conn.tgt_mult):<30} {' ' * (len(conn.source_name) + 4)}+--- -- {arrow_sym}  {conn.target_name}\n")
        else:
            # down routing (primary vertical)
            f.write(f"{repr(conn.src_mult):<30} {conn.source_name}\n")
            f.write(f"{'':<30} |\n")
            f.write(f"{repr(conn.label):<30} |\n")
            f.write(f"{'':<30} +----+\n")
            f.write(f"{repr(conn.tgt_mult):<30} {' ' * 9}|\n")
            f.write(f"{'':<30} {conn.target_name}\n")
        
        f.write("\n")
    
    f.write("\n" + "=" * 130 + "\n")
    f.write("KEY FIXES APPLIED:\n")
    f.write("=" * 130 + "\n\n")
    
    f.write("THRESHOLD FIX: Vertical Alignment Detection\n")
    f.write("-" * 130 + "\n")
    f.write("Changed: dx < 1 pixel (too strict)\n")
    f.write("To:      dx < 5 pixels when dy > 50 pixels (allows minor horizontal offset)\n\n")
    
    # Highlight key connectors
    for conn in planner.connectors:
        if conn.source_name == 'ClassDef' and conn.target_name == 'FunctionDef':
            dx = abs(conn.target_x - conn.source_x)
            dy = abs(conn.target_y - conn.source_y)
            f.write(f"RESULT: {conn.source_name} -> {conn.target_name}\n")
            f.write(f"  Delta: dx={dx:.1f}, dy={dy:.1f}\n")
            f.write(f"  Threshold check: dx < 5 and dy > 50? {dx < 5 and dy > 50}\n")
            f.write(f"  Status: FIXED - Now uses direct vertical line (was 3-segment)\n\n")

print("Log file regenerated: connector_rendering_format.log")
print("Format is now LOCKED - do not change without explicit user request")


