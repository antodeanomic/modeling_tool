#!/usr/bin/env python3
"""Diagnostic: Find Model -> ClassDef connector and check if it's direct."""

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

print(f"Diagram: {diagram.diagram_id}")
print(f"Routing: {diagram.routing}")
print()

svg = render_class_diagram_svg(model, diagram, "High")

# Find the class boxes first
model_match = re.search(r'<text[^>]*>Model</text>', svg)
classdef_match = re.search(r'<text[^>]*>ClassDef</text>', svg)

if not model_match or not classdef_match:
    print("[WARNING] Could not find Model or ClassDef text in SVG")
else:
    print("[OK] Found Model and ClassDef classes in SVG")

# Look for the connector with "contains" label (Model -> ClassDef should be labeled "contains")
# Extract all <line> and <path> elements that have stroke="#2E7D32" (first color for composition)

print()
print("Looking for connectors with 'contains' label...")
print()

# Find all text elements with "contains"
contains_matches = list(re.finditer(r'<text[^>]*contains</text>', svg))
print(f"Found {len(contains_matches)} 'contains' labels")

if contains_matches:
    # For each contains label, look backwards to find the connector (line or path)
    for i, match in enumerate(contains_matches[:3]):  # Check first 3
        start_pos = match.start()
        
        # Look backwards from the label to find the connector
        search_area = svg[max(0, start_pos - 500):start_pos]
        
        # Check if there's a <line> or <path> before this label
        line_match = re.search(r'<line\s+x1="([^"]+)"\s+y1="([^"]+)"\s+x2="([^"]+)"\s+y2="([^"]+)"[^>]*stroke="#([0-9A-F]+)"', search_area)
        path_match = re.search(r'<path\s+d="([^"]+)"[^>]*stroke="#([0-9A-F]+)"', search_area)
        
        print(f"\nConnector {i+1} (with 'contains' label):")
        if line_match:
            x1, y1, x2, y2, color = line_match.groups()
            print(f"  Type: DIRECT LINE")
            print(f"  From ({x1}, {y1}) to ({x2}, {y2})")
            print(f"  Color: {color}")
            
            # Check alignment
            dy = abs(float(y1) - float(y2))
            dx = abs(float(x1) - float(x2))
            
            if dy < 1:
                print(f"  [✓] HORIZONTAL aligned (Δy={dy:.2f}px)")
            elif dx < 1:
                print(f"  [✓] VERTICAL aligned (Δx={dx:.2f}px)")
            else:
                print(f"  [!] DIAGONAL (Δx={dx:.2f}, Δy={dy:.2f})")
        elif path_match:
            path_str, color = path_match.groups()
            segments = path_str.count(' L ')
            print(f"  Type: MULTI-SEGMENT PATH")
            print(f"  Segments: {segments}")
            print(f"  Color: {color}")
            print(f"  Path: {path_str[:100]}...")
        else:
            print(f"  [?] Unknown connector type")

print()
print("[DONE] Connector diagnostic complete")
