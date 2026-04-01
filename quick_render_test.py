#!/usr/bin/env python3
"""End-to-end test of routing-aware layout rendering."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Scripts'))

from parser import parse_csv
from class_diagram_renderer import render_class_diagram_svg

# Load and test
csv_path = 'Process/02_Architecture/class_diagrams.csv'
model = parse_csv(csv_path)

if not model.class_diagrams:
    print("[FAIL] No diagrams")
    sys.exit(1)

diagram = model.class_diagrams[0]
print(f"Testing: {diagram.diagram_id} (routing: {diagram.routing})")

# Test rendering with orthogonal routing  
diagram.routing = "orthogonal"
try:
    svg = render_class_diagram_svg(model, diagram, "High")
    print(f"[OK] Orthogonal rendering: {len(svg)} bytes")
    
    # Count connectors
    direct_lines = svg.count('<line')
    multi_paths = svg.count('<path d="M')
    print(f"     - Direct lines: {direct_lines}")
    print(f"     - Multi-segment paths: {multi_paths}")
    
    if multi_paths > 0:
        print("[SUCCESS] Orthogonal layout is working!")
    else:
        print("[WARNING] No multi-segment paths found")
        
except Exception as e:
    print(f"[FAIL] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
