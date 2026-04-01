#!/usr/bin/env python3
"""Dump actual connector paths to see what's being generated."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Scripts'))

from parser import parse_csv
from class_diagram_renderer import render_class_diagram_svg
import re

csv_path = 'Process/02_Architecture/class_diagrams.csv'
model = parse_csv(csv_path)

if model.class_diagrams:
    diagram = model.class_diagrams[0]
    diagram.routing = "orthogonal"
    svg = render_class_diagram_svg(model, diagram, verbosity_level="High")
    
    # Extract actual connector paths
    connector_paths_with_stroke = re.findall(r'<path\s+d="([^"]+)"[^>]*stroke="#[0-9a-f]{3,6}"', svg)
    
    print("Sample orthogonal connector paths:")
    print("=" * 80)
    
    for i, path in enumerate(connector_paths_with_stroke[:5]):
        print(f"\nPath {i + 1}:")
        print(f"  Raw: {path}")
        
        # Parse coordinates
        coords = re.findall(r'[ML]\s+([\d.-]+)\s+([\d.-]+)', path)
        print(f"  Points: {len(coords)}")
        
        for j, (x, y) in enumerate(coords):
            if j == 0:
                print(f"    Start: ({x}, {y})")
            elif j < len(coords) - 1:
                print(f"    Point: ({x}, {y})")
            else:
                print(f"    End:   ({x}, {y})")
        
        # Analyze segments
        print(f"  Segments:")
        for j in range(1, len(coords)):
            prev_x, prev_y = float(coords[j-1][0]), float(coords[j-1][1])
            curr_x, curr_y = float(coords[j][0]), float(coords[j][1])
            
            x_diff = abs(prev_x - curr_x)
            y_diff = abs(prev_y - curr_y)
            
            if x_diff < 1:
                seg_type = "VERTICAL"
            elif y_diff < 1:
                seg_type = "HORIZONTAL"
            else:
                seg_type = f"DIAGONAL (Δx={x_diff:.1f}, Δy={y_diff:.1f})"
            
            print(f"    {j}: {seg_type}")

else:
    print("[FAIL] No class diagrams found")
    sys.exit(1)
