#!/usr/bin/env python3
"""Diagnose why connectors appear slanted when boxes are vertically aligned.

Tests the Model → ClassDef relationship to understand connector routing.
"""

from Scripts.class_diagram_connectors import ConnectorPlanner, RectangleGrid

# Simulate boxes at same y-level (vertically aligned)
# Model: 600x80, at (50, 100)
# ClassDef: 600x80, at (700, 100)

planner = ConnectorPlanner()

# Register boxes (same y, different x for horizontal alignment)
planner.add_rectangle('Model', x=50, y=100, width=150, height=80)
planner.add_rectangle('ClassDef', x=700, y=100, width=160, height=80)

print("Box Grids:")
print(f"  Model: x=50, y=100, w=150, h=80")
print(f"  ClassDef: x=700, y=100, w=160, h=80")
print()

# Get grids
model_grid = planner.grids['Model']
classdef_grid = planner.grids['ClassDef']

# Show connection points
print("Model Bottom Edge Points (y=180):")
for pt in model_grid.get_points('bottom'):
    is_corner = model_grid.is_corner_point('bottom', pt.index)
    corner_label = " [CORNER]" if is_corner else ""
    print(f"  Index {pt.index}: ({pt.x:.1f}, {pt.y:.1f}){corner_label}")

print()
print("ClassDef Bottom Edge Points (y=180):")
for pt in classdef_grid.get_points('bottom'):
    is_corner = classdef_grid.is_corner_point('bottom', pt.index)
    corner_label = " [CORNER]" if is_corner else ""
    print(f"  Index {pt.index}: ({pt.x:.1f}, {pt.y:.1f}){corner_label}")

print()
print("Model Right Edge Points:")
for pt in model_grid.get_points('right'):
    is_corner = model_grid.is_corner_point('right', pt.index)
    corner_label = " [CORNER]" if is_corner else ""
    print(f"  Index {pt.index}: ({pt.x:.1f}, {pt.y:.1f}){corner_label}")

print()
print("ClassDef Left Edge Points:")
for pt in classdef_grid.get_points('left'):
    is_corner = classdef_grid.is_corner_point('left', pt.index)
    corner_label = " [CORNER]" if is_corner else ""
    print(f"  Index {pt.index}: ({pt.x:.1f}, {pt.y:.1f}){corner_label}")

print()
print("=" * 70)
print("Test Case 1: Model → ClassDef (3 connectors)")
print("=" * 70)

# Add 3 connectors
planner.add_connector('Model', 'ClassDef', '--◆', label='rel1')
planner.add_connector('Model', 'ClassDef', '--◆', label='rel2')
planner.add_connector('Model', 'ClassDef', '--◆', label='rel3')

# Plan
planner.plan_connectors()

print()
print("After Planning:")
for i, connector in enumerate(planner.connectors, 1):
    print(f"\nConnector {i} ({connector.label}):")
    print(f"  Distance: {connector.calculate_distance():.1f}")
    print(f"  Source: {connector.source_name}")
    print(f"    Edge: {connector.source_edge}, Index: {connector.source_point_idx}")
    print(f"    Point: ({connector.source_x:.1f}, {connector.source_y:.1f})")
    print(f"  Target: {connector.target_name}")
    print(f"    Edge: {connector.target_edge}, Index: {connector.target_point_idx}")
    print(f"    Point: ({connector.target_x:.1f}, {connector.target_y:.1f})")
    print(f"  Path Type: {connector.path_type}")
    
    if connector.path_type == "multi_segment":
        print(f"  Segments: {connector.segments}")
    
    # Check if line is horizontal
    if connector.source_y == connector.target_y:
        print(f"  ✓ Perfectly horizontal (y={connector.source_y})")
    else:
        print(f"  ✗ NOT horizontal (source_y={connector.source_y}, target_y={connector.target_y})")

print()
print("=" * 70)
print("Analysis")
print("=" * 70)
print()
print("Question: Why do connectors 2 and 3 appear slanted?")
print()
print("Expected: Since Model and ClassDef are at the same Y (vertically aligned),")
print("all connectors should be perfectly horizontal (same source_y and target_y)")
print()
print("Possible Issues:")
print("1. Exit edge selection might not be choosing 'right' for Model")
print("2. Entry edge selection might not be choosing 'left' for ClassDef")
print("3. Different edges would cause different connection point y-coordinates")
print()
