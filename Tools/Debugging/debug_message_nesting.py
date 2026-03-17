#!/usr/bin/env python3

import sys
sys.path.insert(0, 'Scripts')

from parser import parse_csv
from svg_renderer import render_svg

model = parse_csv('Test/tests/test_message_nesting.csv')
seq = model.sequences[0]

# Render it
svg = render_svg(model, seq, verbosity_level='High')
with open('test_message_nesting_output.svg', 'w') as f:
    f.write(svg)
print('Saved test_message_nesting_output.svg')
print(f'\nSequence has {len(seq.steps)} steps')
