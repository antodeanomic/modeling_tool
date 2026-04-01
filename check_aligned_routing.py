#!/usr/bin/env python3
"""Test if orthogonal routing recognizes aligned connection points."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Scripts'))

from parser import parse_csv
from class_diagram_renderer import render_class_diagram_svg
import re

csv_path = 'Process/02_Architecture/class_diagrams.csv'
model = parse_csv(csv_path)

if not model.class_diagrams:
    print("[FAIL] No diagrams")
    sys.exit(1)

diagram = model.class_diagrams[0]
diagram.routing = "orthogonal"

print(f"Testing: {diagram.diagram_id} with orthogonal routing")
print()

svg = render_class_diagram_svg(model, diagram, "High")

# Find Model -> ClassDef connector
# Look for connectors that connect Model to ClassDef
# They should be marked with specific arrow types

# Count different connector types
direct_lines = svg.count('<line ')
multi_paths = svg.count('<path d="M')

print(f"Results:")
print(f"  Direct line connectors: {direct_lines}")
print(f"  Multi-segment paths: {multi_paths}")
print()

# Extract and examine first few connectors
lines = svg.split('\n')
connector_count = 0
for i, line in enumerate(lines):
    if '<line x1=' in line or ('<path d="M' in line and 'stroke=' in line):
        connector_count += 1
        if connector_count <= 5:
            # Show connector info
            if '<line' in line:
                # Extract coordinates
                import re
                match = re.search(r'x1="([^"]+)" y1="([^"]+)" x2="([^"]+)" y2="([^"]+)"', line)
                if match:
                    x1, y1, x2, y2 = match.groups()
                    print(f"Connector {connector_count}: LINE")
                    print(f"  From ({x1}, {y1}) to ({x2}, {y2})")
                    
                    # Check alignment
                    y_match = abs(float(y1) - float(y2)) < 1
                    x_match = abs(float(x1) - float(x2)) < 1
                    if y_match:
                        print(f"  [ALIGNED] Horizontal line (Y match)")
                    elif x_match:
                        print(f"  [ALIGNED] Vertical line (X match)")
                    else:
                        print(f"  [NOT ALIGNED] Diagonal line")
            elif '<path d="M' in line:
                # Multi-segment
                match = re.search(r'd="([^"]+)"', line)
                if match:
                    path = match.group(1)
                    # Count segments
                    segments = path.count(' L ')
                    print(f"Connector {connector_count}: MULTI-SEGMENT PATH")
                    print(f"  Segments: {segments + 1}")
                    print(f"  Path: {path[:80]}...")
            print()

print()
print("[SUCCESS] Orthogonal routing check complete!")
