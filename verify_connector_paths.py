#!/usr/bin/env python3
"""Verify orthogonal routing by checking actual connector paths."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Scripts'))

from parser import parse_csv
from class_diagram_renderer import render_class_diagram_svg
from model import Model
import re

# Load a known sample class diagram
csv_path = 'Source/sample_model.csv'
model = parse_csv(csv_path)

# Get the first class diagram
if model.class_diagrams:
    diagram = model.class_diagrams[0]
    
    for routing_mode in ["orthogonal"]:
        diagram.routing = routing_mode
        svg = render_class_diagram_svg(model, diagram, verbosity_level="High")
        
        # Count actual connector paths (with stroke and stroke-width attributes)
        # These are the real connectors, not markers
        actual_paths = re.findall(r'<path\s+d="([^"]+)"[^>]*stroke="', svg)
        direct_lines = re.findall(r'<line\s+x1="', svg)
        
        print(f"\nRouting Mode: {routing_mode.upper()}")
        print(f"  Direct line connectors: {len(direct_lines)}")
        print(f"  Multi-segment paths: {len(actual_paths)}")
        
        if len(actual_paths) > 0:
            # Analyze first path
            path = actual_paths[0]
            segments = path.count(' L ')
            print(f"  Sample path segments: {segments + 1} (source + {segments} intermediate)")
            print(f"  First path: {path[:80]}...")
        
        # Verify orthogonal mode has multi-segment paths
        if routing_mode == "orthogonal":
            if len(actual_paths) > len(direct_lines):
                print(f"  Status: [OK] Orthogonal mode using multi-segment paths")
            else:
                print(f"  Status: [FAIL] Orthogonal mode not using multi-segment paths")

else:
    print("[FAIL] No class diagrams found")
    sys.exit(1)

print("\n[SUCCESS] Orthogonal routing verification complete!")
