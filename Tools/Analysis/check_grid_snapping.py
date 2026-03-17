#!/usr/bin/env python3
import sys
sys.path.insert(0, 'Scripts')
from class_diagram_renderer import render_class_diagram_svg
from parser import parse_csv_to_diagram
import csv
import re

# Load planner diagram
with open('Source/requirements.csv', 'r', encoding='utf-8') as f:
    diagram = parse_csv_to_diagram(csv.reader(f, delimiter=';'))

# Render
svg = render_class_diagram_svg(diagram, verbosity='High')

# Find all paths and count segment types
line_count = 0
curve_count = 0
direct_count = 0

model_classdef_path = None

for match in re.finditer(r'<path[^>]*d=\"([^\"]+)\"', svg):
    path_data = match.group(1)
    
    # Check for Model->ClassDef connector (contains "owns" in following text)
    start_pos = match.start()
    section = svg[max(0, start_pos-200):start_pos+400]
    is_model_classdef = 'owns' in section and ('Model' in svg[max(0, start_pos-500):start_pos] or 'Model' in svg[start_pos:start_pos+500])
    
    # Count actual line/curve commands
    has_curves = 'C' in path_data or 'Q' in path_data or 'c' in path_data or 'q' in path_data
    
    # Check if it's a simple path (M x y L x y) - direct line
    if path_data.count('L') == 1 and not has_curves and path_data.count('M') == 1:
        direct_count += 1
        if is_model_classdef:
            model_classdef_path = ("DIRECT LINE", path_data[:80])
    elif has_curves:
        curve_count += 1
        if is_model_classdef:
            model_classdef_path = ("CURVE/MULTI-SEGMENT", path_data[:80])
    else:
        line_count += 1
        if is_model_classdef:
            model_classdef_path = ("MULTI-SEGMENT", path_data[:80])

total = direct_count + line_count + curve_count
print(f'Connector path analysis after grid snapping:')
print(f'  Direct lines (1 segment):  {direct_count}')
print(f'  Multi-segment (lines):     {line_count}')
print(f'  Multi-segment (curves):    {curve_count}')
print(f'  Total:                     {total}')
print(f'')
print(f'Model->ClassDef connector: {model_classdef_path[0] if model_classdef_path else "NOT FOUND"}')
if model_classdef_path:
    print(f'  Path snippet: {model_classdef_path[1]}...')
