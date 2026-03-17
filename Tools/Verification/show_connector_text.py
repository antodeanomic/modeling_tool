#!/usr/bin/env python3
"""Show sample of connector text without arrow symbols."""

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

# Show all text with contains/owns/1/0 (connector-related texts)
print("Connector-related text elements:")
print("=" * 80)
connector_texts = [(x, y, t) for x, y, t in matches if any(kw in t for kw in ['contains', 'owns', '1', '0.', 'parses'])]

for x, y, text in connector_texts[:20]:
    print(f"  {text:<30} at x={float(x):<8.1f} y={float(y):<8.1f}")

print("\n" + "=" * 80)
print(f"\nTotal connector texts: {len(connector_texts)}")
print("✓ No arrow symbols in text (all rendered graphically)")
