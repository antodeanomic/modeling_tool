#!/usr/bin/env python3

import sys
sys.path.insert(0, 'Scripts')

from parser import parse_csv
from svg_renderer import detect_spanning_brackets

model = parse_csv('Test/tests/test_message_nesting.csv')
seq = model.sequences[0]

print("Sequence steps:")
for i, step in enumerate(seq.steps):
    print(f"  {i}: row={step.row}, depth={step.depth}, {step.src_obj}->{step.dst_obj}: {step.function}")

print("\nDetected spanning brackets:")
brackets = detect_spanning_brackets(seq.steps)
for start_row, (end_row, func_name, src_obj, dst_obj, depth) in brackets.items():
    print(f"  Row {start_row} → Row {end_row}: {src_obj}.{func_name}() [depth={depth}]")

print("\nY-coordinates (ROW_HEIGHT=20):")
for row in [1, 2, 3]:
    y = 120 + (row - 1) * 20
    print(f"  Row {row}: y={y}")
print(f"  Return arrow spacing: +30px")
