#!/usr/bin/env python3
"""Analyze actual SVG rendering to determine which connectors are direct vs multi-segment."""

import sys
import re
sys.path.insert(0, 'Scripts')

from parser import parse_csv
from class_diagram_renderer import render_class_diagram_svg

csv_path = 'Process/02_Architecture/class_diagrams.csv'
model = parse_csv(csv_path)
diagram = [d for d in model.class_diagrams if d.diagram_id == 'DataModelRelationships'][0]

# Get all relationships
print("Relationships in diagram:")
print("=" * 80)
for i, rel in enumerate(diagram.relationships, 1):
    print(f"{i:2}. {rel.source:<20} → {rel.target:<20} ({rel.arrow})")

print("\n" + "=" * 80)
print("\nRendering SVG...")
svg = render_class_diagram_svg(model, diagram, verbosity_level='High')

# Extract all <line> elements (direct connectors)
line_pattern = r'<line x1="([^"]+)" y1="([^"]+)" x2="([^"]+)" y2="([^"]+)"[^>]*>'
lines = re.findall(line_pattern, svg)

print(f"\nDirect connectors (<line> elements): {len(lines)}")
for x1, y1, x2, y2 in lines[:20]:
    print(f"  Line from ({float(x1):.1f},{float(y1):.1f}) to ({float(x2):.1f},{float(y2):.1f})")

# Extract all <path> elements (multi-segment connectors)
path_pattern = r'<path d="([^"]+)"[^>]*>'
paths = re.findall(path_pattern, svg)

print(f"\nMulti-segment connectors (<path> elements): {len(paths)}")
for i, path_d in enumerate(paths[:20], 1):
    # Count the number of segments (L = line to segment)
    segments = path_d.count(' L ')
    print(f"  Path {i}: segments={segments+1}, d=\"{path_d[:60]}...\"")

print("\n" + "=" * 80)
