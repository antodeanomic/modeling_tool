#!/usr/bin/env python3

import sys
sys.path.insert(0, 'Scripts')

from parser import parse_csv
from svg_renderer import detect_spanning_brackets, render_svg

model = parse_csv('Test/tests/test_nested_self_messages.csv')
seq = model.sequences[0]

print("Sequence steps:")
for i, step in enumerate(seq.steps):
    print(f"  {i}: row={step.row}, depth={step.depth}, {step.src_obj}->{step.dst_obj}: {step.function}")

print("\nDetected spanning brackets:")
brackets = detect_spanning_brackets(seq.steps)
ROW_HEIGHT = 20
for start_row, (end_row, func_name, src_obj, dst_obj, depth) in brackets.items():
    y_start = 120 + (start_row - 1) * ROW_HEIGHT
    y_end = 120 + (end_row - 1) * ROW_HEIGHT
    y_with_spacing = y_end + 10
    print(f"  Row {start_row} → Row {end_row}: {src_obj}.{func_name}()")
    print(f"    y_start={y_start}, y_end={y_end}, with_spacing={y_with_spacing}, depth={depth}")

print("\nRendering SVG...")
svg = render_svg(model, seq)

# Look for span heights in the SVG
import re
spans = re.findall(r'<rect x="(\d+)" y="(\d+)" width="2" height="(\d+)"', svg)
print("\nSpanning brackets found in SVG:")
for x, y, height in spans:
    y_int = int(y)
    height_int = int(height)
    print(f"  x={x}, y={y}, height={height} (covers y={y_int} to y={y_int + height_int})")

# Find return arrows
arrows = re.findall(r'<line x1="\d+" y1="(\d+)" x2="\d+" y2="(\d+)" stroke="#000" stroke-dasharray="5,5"', svg)
print("\nReturn arrows found in SVG:")
for y1, y2 in arrows:
    print(f"  Return arrow at y={y1}")
