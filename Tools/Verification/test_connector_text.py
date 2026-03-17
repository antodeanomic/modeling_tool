#!/usr/bin/env python3
"""Test script to diagnose connector text rendering."""

import sys
sys.path.insert(0, 'Scripts')
from parser import parse_csv
from class_diagram_renderer import render_class_diagram_svg

model = parse_csv('Process/02_Architecture/class_diagrams.csv')
diagram = model.class_diagrams[0]  # DataModelRelationships

print(f'Diagram ID: {diagram.diagram_id}')
routing = diagram.routing if diagram.routing else "(None - will use default)"
print(f'Routing: {routing}')
print(f'Relationships: {len(diagram.relationships)}')

# Check the first two relationships
for i, rel in enumerate(diagram.relationships[:2]):
    print(f'\nRel {i}: {rel.source} -> {rel.target}')
    print(f'  Arrow: {rel.arrow}')
    print(f'  Multiplicity: {rel.src_mult}:{rel.tgt_mult}')
    print(f'  Label: "{rel.label}"')

# Render and check SVG for text elements
print('\nRendering SVG...')
svg = render_class_diagram_svg(model, diagram, 'High')
text_count = svg.count('<text')
print(f'\nSVG Statistics:')
print(f'  Total text elements: {text_count}')
print(f'  SVG length: {len(svg)} characters')

# Look for text elements related to connectors (multiplicity/labels)
import re
# Find all text elements with their content
all_texts = re.findall(r'<text[^>]*>([^<]*)</text>', svg)
print(f'\nTotal text elements in SVG: {len(all_texts)}')

# Filter for likely connector text (single/double digit numbers, asterisks)
connector_texts = [t for t in all_texts if any(c in t for c in '0123456789.*')]
print(f'Likely connector texts: {len(connector_texts)}')
for i, t in enumerate(connector_texts[:5]):
    print(f'  [{i}] "{t}"')

# Check if multiplicity appears
if '0..*' in svg or '1' in svg:
    print('\nMultiplicity appears in SVG: YES')
else:
    print('\nMultiplicity appears in SVG: NO')

# Look specifically for text elements in path data
print('\n\nConnector path analysis:')
# Extract first relationship's connector
lines = svg.split('\n')
in_connector_section = False
for i, line in enumerate(lines):
    if '<path' in line and 'stroke' in line:
        in_connector_section = True
        print(f'Line {i}: {line[:100]}...')
    elif in_connector_section and '<text' in line:
        print(f'  Text {i}: {line[:120]}...')
    elif in_connector_section and '<' in line and not line.strip().endswith('</text>'):
        if '  <' not in line:
            in_connector_section = False
