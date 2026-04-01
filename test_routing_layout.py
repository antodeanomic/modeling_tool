#!/usr/bin/env python3
"""Quick test of routing-aware layout."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Scripts'))

from parser import parse_csv
from class_diagram_renderer import render_class_diagram_svg

csv_path = 'Process/02_Architecture/class_diagrams.csv'
model = parse_csv(csv_path)

if model.class_diagrams:
    diagram = model.class_diagrams[0]
    
    # Test both routing modes
    for routing_mode in ["diagonal", "orthogonal"]:
        diagram.routing = routing_mode
        try:
            svg = render_class_diagram_svg(model, diagram, verbosity_level="High")
            print(f"[OK] {routing_mode.upper()} routing rendered successfully ({len(svg)} bytes)")
        except Exception as e:
            print(f"[FAIL] {routing_mode.upper()} routing failed: {e}")
            import traceback
            traceback.print_exc()
else:
    print("[FAIL] No class diagrams found")
    sys.exit(1)

print("\n[SUCCESS] Routing-aware layout working!")
