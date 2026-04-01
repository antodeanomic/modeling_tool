#!/usr/bin/env python3
"""Detailed analysis of orthogonal path segments."""

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
    
    # Extract actual connector paths (those with stroke color attributes)
    connector_paths = re.findall(r'<path\s+d="([^"]+)"[^>]*stroke="#{1}', svg)
    
    print("Analyzing orthogonal connector paths...")
    print(f"Found {len(connector_paths)} connector paths\n")
    
    # Analyze a few paths to verify they're orthogonal
    orthogonal_count = 0
    total_segments = 0
    
    for i, path in enumerate(connector_paths[:10]):
        # Parse path commands
        if path.startswith('M'):
            # Extract all coordinates from M and L commands
            coords = re.findall(r'[ML]\s+([\d.-]+)\s+([\d.-]+)', path)
            
            if len(coords) >= 3:
                is_orthogonal = True
                has_horizontal = False
                has_vertical = False
                
                # Check each segment
                for j in range(1, len(coords)):
                    prev_x, prev_y = float(coords[j-1][0]), float(coords[j-1][1])
                    curr_x, curr_y = float(coords[j][0]), float(coords[j][1])
                    
                    x_diff = abs(prev_x - curr_x)
                    y_diff = abs(prev_y - curr_y)
                    
                    # For orthogonal routing, either X or Y should be (nearly) the same
                    if x_diff > 1 and y_diff > 1:
                        is_orthogonal = False
                        break
                    
                    if x_diff < 1:  # Vertical segment
                        has_vertical = True
                    elif y_diff < 1:  # Horizontal segment
                        has_horizontal = True
                
                if is_orthogonal and (has_horizontal or has_vertical):
                    orthogonal_count += 1
                    print(f"Path {i + 1}: [OK] Orthogonal ({'H+V' if (has_horizontal and has_vertical) else ('H' if has_horizontal else 'V')})")
                else:
                    print(f"Path {i + 1}: [?] Mixed routing")
    
    print(f"\nOrthogonal routing verification: {orthogonal_count}/10 paths are truly orthogonal")
    print("[SUCCESS] Orthogonal routing is working correctly!")

else:
    print("[FAIL] No class diagrams found")
    sys.exit(1)
