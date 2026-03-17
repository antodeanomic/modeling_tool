#!/usr/bin/env python3
"""Check what the diagram viewer is actually requesting."""

import sys
import urllib.parse
sys.path.insert(0, 'Scripts')

from server import DEFAULT_CSV

# Simulate a request like the diagram_viewer.html would make
# Based on line 1210 in diagram_viewer.html:
# url = `/api/diagram?csv=${csv}&type=class_diagram&diagram_id=${diagram_id}&verbosity=${state.verbosity}&routing=${routing}&lanes=${lanesParam}`;

# Default state from line 481: verbosity: 'High'
default_params = {
    'csv': 'Process/02_Architecture/class_diagrams.csv',
    'type': 'class_diagram',
    'diagram_id': 'DataModelRelationships',
    'verbosity': 'High',
    'routing': 'orthogonal',
    'lanes': ''
}

print("Default diagram request parameters:")
print("=" * 80)
for key, value in default_params.items():
    print(f"  {key:<15} = {repr(value)}")

# Build the URL
query = urllib.parse.urlencode(default_params)
print(f"\nQuery string: {query}")
print(f"\nFull URL: /api/diagram?{query}")

# Now test what the server would do with these parameters
print("\n" + "=" * 80)
print("Rendering diagram with these parameters...")

from parser import parse_csv
from class_diagram_renderer import render_class_diagram_svg

parsed_params = urllib.parse.parse_qs(query, keep_blank_values=True)
csv_name = parsed_params.get('csv', [DEFAULT_CSV])[0]
diagram_id = parsed_params.get('diagram_id', [''])[0]
verbosity = parsed_params.get('verbosity', ['High'])[0]
routing = parsed_params.get('routing', [''])[0]
lanes_str = parsed_params.get('lanes', [''])[0]

print(f"\nParsed parameters:")
print(f"  csv_name = {repr(csv_name)}")
print(f"  diagram_id = {repr(diagram_id)}")
print(f"  verbosity = {repr(verbosity)}")
print(f"  routing = {repr(routing)}")
print(f"  lanes_str = {repr(lanes_str)}")

model = parse_csv(csv_name)
class_diagram = model.get_class_diagram(diagram_id)

if routing:
    class_diagram.routing = routing

layers_filter = None
if 'lanes' in parsed_params:
    if lanes_str != '':
        layers_filter = lanes_str.split(',')
    else:
        layers_filter = []

print(f"\nRendering with:")
print(f"  verbosity_level = {repr(verbosity)}")
print(f"  layers_filter = {repr(layers_filter)}")

svg = render_class_diagram_svg(model, class_diagram, verbosity_level=verbosity, layers_filter=layers_filter)

# Count multiplicity values
import re
text_pattern = r'<text[^>]*?x="([^"]+?)"[^>]*?y="([^"]+?)"[^>]*?>([^<]+?)</text>'
matches = re.findall(text_pattern, svg)
numeric_texts = [t for _, _, t in matches if any(c.isdigit() for c in t)]

print(f"\nSVG generated successfully")
print(f"Total text elements: {len(matches)}")
print(f"Numeric/multiplicity text elements: {len(numeric_texts)} (first 10: {numeric_texts[:10]})")
