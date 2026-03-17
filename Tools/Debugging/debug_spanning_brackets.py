#!/usr/bin/env python3

import sys
import os

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Scripts'))

from parser import parse_csv
from svg_renderer import render_svg

# Load the nested self messages test case
model = parse_csv('Test/tests/test_nested_self_messages.csv')

# Get sequence
seq = model.sequences[0] if model.sequences else None
if not seq:
    print("No sequence found!")
    sys.exit(1)

# Render to see what we have
svg = render_svg(model, seq, verbosity_level='High')

# Save to file for inspection  
with open('debug_nested.svg', 'w') as f:
    f.write(svg)

print('Saved debug diagram to debug_nested.svg')

# Print some debug info about the structure
print(f'Steps in sequence: {len(seq.steps)}')
for i, step in enumerate(seq.steps):
    print(f'  Step {i}: row={step.row}, depth={step.depth}, {step.src_obj}->{step.dst_obj}: {step.function}')
