#!/usr/bin/env python3
"""Check all text in SVG to understand structure."""

import sys
sys.path.insert(0, 'Scripts')

from parser import parse_csv
from class_diagram_renderer import render_class_diagram_svg
import re

csv_path = 'Process/02_Architecture/class_diagrams.csv'
diagram_id = 'DataModelRelationships'

model = parse_csv(csv_path)
diagram = [d for d in model.class_diagrams if d.diagram_id == diagram_id][0]
svg = render_class_diagram_svg(model, diagram, verbosity_level='Normal')

# Find text elements
text_pattern = r'<text[^>]*?x="([^"]+?)"[^>]*?y="([^"]+?)"[^>]*?>([^<]+?)</text>'
matches = re.findall(text_pattern, svg)

# Show unique text values to see what's being rendered
text_values = set(t for _, _, t in matches)
print("All unique text values in SVG:")
for t in sorted(text_values):
    count = sum(1 for _, _, text in matches if text == t)
    if '0' in t or '1' in t or any(c in t.lower() for c in ['own', 'contain', 'pars']):
        marker = " <- CONNECTOR"
    else:
        marker = ""
    print(f"  {t:<40} (x{count}){marker}")
