#!/usr/bin/env python3
"""Export SVG to file for inspection."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Scripts'))

from parser import parse_csv
from class_diagram_renderer import render_class_diagram_svg

csv_path = 'Process/02_Architecture/class_diagrams.csv'
model = parse_csv(csv_path)

if model.class_diagrams:
    diagram = model.class_diagrams[0]
    diagram.routing = "orthogonal"
    svg = render_class_diagram_svg(model, diagram, verbosity_level="High")
    
    # Save to file
    with open('class_diagram_orthogonal_test.svg', 'w') as f:
        f.write(svg)
    
    print(f"[OK] SVG exported to class_diagram_orthogonal_test.svg")
    print(f"SVG size: {len(svg)} bytes")
    
    # Show first few lines to verify it's valid
    lines = svg.split('\n')
    print(f"\nFirst 20 lines:")
    for i, line in enumerate(lines[:20]):
        print(f"{i+1:3d}: {line[:100]}")
else:
    print("[FAIL] No class diagrams found")
    sys.exit(1)
