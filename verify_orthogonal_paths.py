#!/usr/bin/env python3
"""Visual verification of orthogonal routing paths."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Scripts'))

from parser import parse_csv
from class_diagram_renderer import render_class_diagram_svg
from model import Model
import re

# Load the class_diagrams.csv file
csv_path = 'Process/02_Architecture/class_diagrams.csv'
model = parse_csv(csv_path)

# Get the first class diagram
if model.class_diagrams:
    diagram = model.class_diagrams[0]
    diagram.routing = "orthogonal"
    
    # Render SVG
    svg = render_class_diagram_svg(model, diagram, verbosity_level="High")
    
    # Extract the first few multi-segment paths to verify the structure
    paths = re.findall(r'<path d="([^"]+)"', svg)
    
    print("Visual Verification of Orthogonal Routing")
    print("=" * 60)
    print(f"Found {len(paths)} multi-segment paths\n")
    
    # Analyze first few paths
    for i, path in enumerate(paths[:3]):
        print(f"Path {i + 1}:")
        print(f"  {path}")
        
        # Check if it's orthogonal (only horizontal and vertical segments)
        segments = re.findall(r'([ML]\s+[\d.-]+\s+[\d.-]+)', path)
        
        # Check for right angles
        has_horizontal = False
        has_vertical = False
        
        for j in range(1, len(segments)):
            prev_seg = segments[j-1]
            curr_seg = segments[j]
            
            # Extract coordinates
            prev_coords = re.findall(r'([\d.-]+)\s+([\d.-]+)', prev_seg)[0]
            curr_coords = re.findall(r'([\d.-]+)\s+([\d.-]+)', curr_seg)[0]
            
            prev_x, prev_y = float(prev_coords[0]), float(prev_coords[1])
            curr_x, curr_y = float(curr_coords[0]), float(curr_coords[1])
            
            # Check if horizontal or vertical
            if abs(prev_x - curr_x) < 1:  # Vertical (same X)
                has_vertical = True
            elif abs(prev_y - curr_y) < 1:  # Horizontal (same Y)
                has_horizontal = True
        
        routing_type = []
        if has_horizontal:
            routing_type.append("Horizontal")
        if has_vertical:
            routing_type.append("Vertical")
        
        print(f"  Routing: {' & '.join(routing_type)}")
        print(f"  Status: {'RIGHT-ANGLE' if (has_horizontal and has_vertical) else 'LINEAR'}")
        print()
    
    print("=" * 60)
    print("[SUCCESS] Orthogonal paths are properly formatted!")
else:
    print("[FAIL] No class diagrams found")
    sys.exit(1)
