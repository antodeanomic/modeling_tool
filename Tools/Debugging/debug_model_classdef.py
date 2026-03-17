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
        
        print("=" * 100)
        print("LAYOUT ANALYSIS - Object Positions")
        print("=" * 100)
        
        # Show Model and ClassDef specifically
        for name in ['Model', 'ClassDef']:
            box = boxes[name]
            print(f"\n{name}:")
            print(f"  Box position: X={box['x']:.1f}, Y={box['y']:.1f}")
            print(f"  Box size: width={box['width']:.1f}, height={box['height']:.1f}")
            print(f"  Top edge:    Y={box['y']:.1f}")
            print(f"  Bottom edge: Y={box['y'] + box['height']:.1f}")
            print(f"  Middle Y:    Y={box['y'] + box['height']/2:.1f}")
        
        # Create planner
        planner = ConnectorPlanner()
        for name, box in boxes.items():
            planner.add_rectangle(name, box['x'], box['y'], box['width'], box['height'])
        
        for rel in cd.relationships:
            planner.add_connector(rel.source, rel.target, rel.arrow,
                                rel.src_mult, rel.tgt_mult, rel.label)
        
        planner.plan_connectors()
        
        # Find Model->ClassDef connector
        print("\n" + "=" * 100)
        print("CONNECTION POINT ANALYSIS - Model → ClassDef")
        print("=" * 100)
        
        for conn in planner.connectors:
            if conn.source_name == 'Model' and conn.target_name == 'ClassDef':
                print(f"\nConnector: {conn.source_name} → {conn.target_name}")
                print(f"\nSource connection point:")
                print(f"  Box: {conn.source_name}")
                print(f"  Edge: {conn.source_edge}")
                print(f"  Position: X={conn.source_x:.1f}, Y={conn.source_y:.1f}")
                print(f"  Index: {conn.source_point_idx}")
                
                print(f"\nTarget connection point:")
                print(f"  Box: {conn.target_name}")
                print(f"  Edge: {conn.target_edge}")
                print(f"  Position: X={conn.target_x:.1f}, Y={conn.target_y:.1f}")
                print(f"  Index: {conn.target_point_idx}")
                
                y_diff = abs(conn.source_y - conn.target_y)
                print(f"\nVertical alignment:")
                print(f"  Source Y: {conn.source_y:.1f}")
                print(f"  Target Y: {conn.target_y:.1f}")
                print(f"  Difference: {y_diff:.1f} pixels")
                print(f"  Alignment tolerance: 2.0 pixels")
                print(f"  Are they aligned? {y_diff < 2.0}")
                
                print(f"\nRouting decision:")
                print(f"  Path type: {conn.path_type}")
                print(f"  Should be direct? {y_diff < 2.0}")
                
                break
        break
