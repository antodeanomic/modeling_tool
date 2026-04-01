import sys
sys.path.insert(0, 'Scripts')
from parser import parse_csv
from class_diagram_renderer import render_class_diagram_svg

model = parse_csv('Process/02_Architecture/class_diagrams.csv')
diagram = model.class_diagrams[0]
diagram.routing = 'orthogonal'

svg = render_class_diagram_svg(model, diagram, 'High')

# Count direct lines and multi-segment paths
direct_count = svg.count('<line x1=')
path_count = svg.count('<path d="M')

print(f'Direct lines (<line>): {direct_count}')
print(f'Multi-segment paths (<path>): {path_count}')
print(f'Total connectors: {direct_count + path_count}')

# Look for 'contains' label to find Model->ClassDef connector
import re
lines = svg.split('\n')
for i, line in enumerate(lines):
    if 'contains' in line and '>contains<' in line:
        print(f'\nFound contains label at line {i}')
        # Check previous lines for connector
        for j in range(max(0, i-10), i):
            if '<line' in lines[j]:
                print(f'  Before it: DIRECT LINE ✓')
                break
            elif '<path' in lines[j]:
                print(f'  Before it: MULTI-SEGMENT PATH')
                break
