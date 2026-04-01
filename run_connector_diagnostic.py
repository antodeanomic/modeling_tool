#!/usr/bin/env python3
"""Diagnostic: Find Model -> ClassDef connector and write to file."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Scripts'))

from parser import parse_csv
from class_diagram_renderer import render_class_diagram_svg
import re

output = []

try:
    csv_path = 'Process/02_Architecture/class_diagrams.csv'
    model = parse_csv(csv_path)

    if not model.class_diagrams:
        output.append("[FAIL] No diagrams")
        sys.exit(1)

    diagram = model.class_diagrams[0]
    diagram.routing = "orthogonal"

    output.append(f"Diagram: {diagram.diagram_id}")
    output.append(f"Routing: {diagram.routing}")
    output.append("")

    svg = render_class_diagram_svg(model, diagram, "High")

    # Count connectors
    direct_lines = svg.count('<line x1=')
    multi_paths = svg.count('<path d="M')
    
    output.append(f"SVG Stats:")
    output.append(f"  Direct lines: {direct_lines}")
    output.append(f"  Multi-segment paths (estimated): {multi_paths}")
    output.append("")
    
    # Look for contains labels to find Model -> ClassDef connector
    contains_matches = list(re.finditer(r'<text[^>]*>contains</text>', svg))
    output.append(f"Found {len(contains_matches)} 'contains' labels")
    output.append("")
    
    if contains_matches:
        for i, match in enumerate(contains_matches[:3]):
            start_pos = match.start()
            search_area = svg[max(0, start_pos - 500):start_pos]
            
            line_match = re.search(r'<line\s+x1="([^"]+)"\s+y1="([^"]+)"\s+x2="([^"]+)"\s+y2="([^"]+)"', search_area)
            path_match = re.search(r'<path\s+d="([^"]+)"[^>]*stroke', search_area)
            
            output.append(f"Connector {i+1} near 'contains' label:")
            if line_match:
                x1, y1, x2, y2 = line_match.groups()
                output.append(f"  Type: DIRECT LINE ✓✓✓")
                output.append(f"  From ({x1}, {y1}) to ({x2}, {y2})")
                dy = abs(float(y1) - float(y2))
                if dy < 1:
                    output.append(f"  Alignment: HORIZONTAL (perfect!)")
                else:
                    dx = abs(float(x1) - float(x2))
                    if dx < 1:
                        output.append(f"  Alignment: VERTICAL (perfect!)")
            elif path_match:
                path_str = path_match.group(1)
                segments = path_str.count(' L ')
                output.append(f"  Type: MULTI-SEGMENT PATH")
                output.append(f"  Segments: {segments}")
            else:
                output.append(f"  Type: UNKNOWN")
            output.append("")

    output.append("[DONE] Diagnostic complete")

except Exception as e:
    output.append(f"[ERROR] {e}")
    import traceback
    output.append(traceback.format_exc())

result = '\n'.join(output)
with open('connector_diagnostic_output.txt', 'w') as f:
    f.write(result)

print("Output written to connector_diagnostic_output.txt")
print(result)
