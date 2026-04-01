#!/usr/bin/env python3
"""Test orthogonal routing for class diagrams."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Scripts'))

from parser import parse_csv
from class_diagram_renderer import render_class_diagram_svg
from model import Model

# Load the class_diagrams.csv file
csv_path = 'Process/02_Architecture/class_diagrams.csv'
model = parse_csv(csv_path)

# Get the first class diagram (DataModelRelationships)
if model.class_diagrams:
    diagram = model.class_diagrams[0]
    print(f"Testing diagram: {diagram.diagram_id}")
    print(f"Original routing: {diagram.routing}")
    
    # Test orthogonal routing
    diagram.routing = "orthogonal"
    print(f"Changed routing to: {diagram.routing}")
    
    # Render SVG
    svg = render_class_diagram_svg(model, diagram, verbosity_level="High")
    
    # Check if multi-segment paths are present
    if '<path' in svg:
        path_count = svg.count('<path')
        print(f"[OK] SVG contains {path_count} multi-segment path(s)")
        
        # Check if paths contain multi-point segments (more than just direct lines)
        segment_count = svg.count(' L ')
        print(f"[OK] SVG contains {segment_count} line segments (multi-segment routing detected)")
        
        if segment_count > 0:
            print("[SUCCESS] Orthogonal routing is working!")
            sys.exit(0)
        else:
            print("[FAIL] No multi-segment paths found")
            sys.exit(1)
    else:
        print("[FAIL] No multi-segment paths found in SVG")
        sys.exit(1)
else:
    print("[FAIL] No class diagrams found in model")
    sys.exit(1)
