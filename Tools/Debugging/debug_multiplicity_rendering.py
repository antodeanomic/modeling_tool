#!/usr/bin/env python3
"""Debug multi-segment rendering to see why multiplicity isn't showing."""

import sys
sys.path.insert(0, 'Scripts')

from parser import parse_csv
from class_diagram_renderer import render_class_diagram_svg
import re

csv_path = 'Process/02_Architecture/class_diagrams.csv'
diagram_id = 'DataModelRelationships'

model = parse_csv(csv_path)
diagram = [d for d in model.class_diagrams if d.diagram_id == diagram_id][0]

# Render with High verbosity
print("Rendering with verbosity_level='High'...")
svg = render_class_diagram_svg(model, diagram, verbosity_level='High')

# Extract ALL text elements including multiplicity
text_pattern = r'<text[^>]*?x="([^"]+?)"[^>]*?y="([^"]+?)"[^>]*?>([^<]+?)</text>'
matches = re.findall(text_pattern, svg)

# Check for multiplicity values (1, 0.*, 1.*, 0..1, etc)
multiplicity_texts = []
for x, y, t in matches:
    # Multiplicity pattern: single digits, dots, or common UML notations
    if re.match(r'^[01](\.\*|\.\.|\.)?(\|[01])?$', t.strip()):
        multiplicity_texts.append((float(x), float(y), t))

print(f"\nTotal text elements: {len(matches)}")
print(f"Multiplicity text elements found: {len(multiplicity_texts)}")

if multiplicity_texts:
    print("\nMultiplicity values in SVG:")
    for x, y, t in multiplicity_texts[:10]:
        print(f"  x={x:<8.1f} y={y:<8.1f} text='{t}'")
else:
    print("\n⚠ NO multiplicity values found in SVG!")
    print("\nPossible causes:")
    print("  1. verbosity_level not being passed correctly")
    print("  2. Segments check failing (len(connector.segments) < 2)")
    print("  3. No src_mult/tgt_mult values in connectors (but we verified they exist)")
    print("  4. Text elements being created but not captured by our regex")

# Check for any numeric text (in case regex is wrong)
numeric_texts = [t for _, _, t in matches if any(c.isdigit() for c in t)]
print(f"\nAll numeric text elements in SVG: {numeric_texts[:20]}")
