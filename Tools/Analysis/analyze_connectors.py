#!/usr/bin/env python3
import sys
import os

# Add Scripts directory to path
scripts_dir = os.path.join(os.path.dirname(__file__), 'Scripts')
sys.path.insert(0, scripts_dir)

from parser import parse_csv
from class_diagram_renderer import _layout_classes
from class_diagram_connectors import ConnectorPlanner

# Load the model
model = parse_csv('Process/02_Architecture/class_diagrams.csv')

# Find DataModelRelationships
for cd in model.class_diagrams:
    if cd.diagram_id == 'DataModelRelationships':
        # Get layout
        boxes = _layout_classes(cd, model, 'High')
        
        # Create planner
        planner = ConnectorPlanner()
        for name, box in boxes.items():
            planner.add_rectangle(name, box['x'], box['y'], box['width'], box['height'])
        
        for rel in cd.relationships:
            planner.add_connector(rel.source, rel.target, rel.arrow,
                                rel.src_mult, rel.tgt_mult, rel.label)
        
        planner.plan_connectors()
        
        # Show all connectors with their routing type
        print("Connector Routing Analysis")
        print("=" * 100)
        print(f"{'Source':<20} {'Target':<20} {'Path Type':<15} {'Text String':<35} {'Y Diff':<10}")
        print("-" * 100)
        
        for conn in sorted(planner.connectors, key=lambda c: (c.source_name, c.target_name)):
            y_diff = abs(conn.source_y - conn.target_y)
            
            # Determine text string based on path type
            if conn.path_type == 'direct':
                text = f'"{conn.src_mult}  {conn.label or ""}  {conn.tgt_mult}"'
            else:
                text = f'multi-segment (3 parts)'
            
            print(f"{conn.source_name:<20} {conn.target_name:<20} {conn.path_type:<15} {text:<35} {y_diff:<10.0f}")
        
        break
