#!/usr/bin/env python3
"""Analyze connector directions to understand rendering paths."""

import sys
sys.path.insert(0, 'Scripts')

from parser import parse_csv
from class_diagram_renderer import _layout_classes
from class_diagram_connectors import ConnectorPlanner

def analyze_connector_routing(csv_path):
    """Analyze all connectors to see which rendering path they take."""
    
    model = parse_csv(csv_path)
    diagram = model.class_diagrams[0]  # DataModelRelationships
    
    # Layout to get box positions
    boxes = _layout_classes(diagram, model, "High")
    
    # Create and plan connectors
    planner = ConnectorPlanner()
    for name, box in boxes.items():
        planner.add_rectangle(name, box['x'], box['y'], box['width'], box['height'])
    
    for rel in diagram.relationships:
        planner.add_connector(rel.source, rel.target, rel.arrow,
                            rel.src_mult, rel.tgt_mult, rel.label, rel.layer)
    
    planner.plan_connectors()
    
    # Analyze each connector
    connectors = planner.get_connectors()
    
    print("=" * 140)
    print("CONNECTOR ROUTING ANALYSIS")
    print("=" * 140)
    print(f"{'Source':<18} {'Target':<18} {'Path':<12} {'DX':<10} {'DY':<10} {'Routing':<20} {'Text Position':<30}")
    print("-" * 140)
    
    for c in connectors:
        if c.source_name not in boxes or c.target_name not in boxes:
            continue
        
        dx = abs(c.target_x - c.source_x)
        dy = abs(c.target_y - c.source_y)
        
        # Determine routing
        is_horizontal = abs(c.source_y - c.target_y) < 2
        if c.path_type == "multi_segment":
            routing = "Multi-segment"
            text_pos = "Distributed"
        elif is_horizontal:
            routing = "Horizontal"
            text_pos = "ABOVE (single string)"
        else:
            # Diagonal
            is_vertical_dominant = dy > dx  
            if is_vertical_dominant:
                routing = "Nearly-vertical"
                text_pos = "RIGHT (separate)"
            else:
                routing = "Nearly-horizontal"
                text_pos = "ABOVE (single string)"
        
        print(f"{c.source_name:<18} {c.target_name:<18} {c.path_type:<12} {dx:<10.1f} {dy:<10.1f} {routing:<20} {text_pos:<30}")
    
    print()
    print("=" * 140)
    print("SUMMARY:")
    print("- Nearly-horizontal & Horizontal: Using SINGLE formatted string (FIXED)")
    print("- Nearly-vertical: Using SEPARATE elements positioned to RIGHT (needs individual spacing)")
    print("- Multi-segment: Distributed text across segments (future enhancement)")
    print("=" * 140)

if __name__ == "__main__":
    csv_path = "Process/02_Architecture/class_diagrams.csv"
    analyze_connector_routing(csv_path)
