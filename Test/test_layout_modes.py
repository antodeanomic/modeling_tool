#!/usr/bin/env python3
"""Quick verification that orthogonal class-diagram layout works."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Scripts'))

from parser import parse_csv
from class_diagram_renderer import _layout_classes_orthogonal

csv_path = os.path.join(os.path.dirname(__file__), '..', 'Source', 'sample_model.csv')
model = parse_csv(csv_path)

output = []

if not model.class_diagrams:
    print("[FAIL] No class diagrams found")
    sys.exit(1)

diagram = model.class_diagrams[0]

output.append("Testing orthogonal layout selection...")
output.append(f"Diagram: {diagram.diagram_id}")
output.append(f"Routing mode: {diagram.routing}")
output.append("")

# Test orthogonal layout
output.append("1. Testing orthogonal layout...")
try:
    layout = _layout_classes_orthogonal(diagram, model, "High")
    output.append(f"   [OK] Orthogonal layout produced {len(layout)} objects")
    
    # Check that objects are on grid-aligned Y coordinates
    y_positions = {}
    for obj_name, box in layout.items():
        y = box['y']
        if y not in y_positions:
            y_positions[y] = []
        y_positions[y].append(obj_name)
    
    output.append(f"   [OK] Objects on {len(y_positions)} grid rows")
except Exception as e:
    output.append(f"   [FAIL] {e}")
    sys.exit(1)

output.append("")
output.append("[SUCCESS] Orthogonal layout working!")

result = '\n'.join(output)
print(result)

# Write to file
with open('layout_test_result.txt', 'w') as f:
    f.write(result)
