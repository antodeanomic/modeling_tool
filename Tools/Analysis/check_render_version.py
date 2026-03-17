#!/usr/bin/env python3
"""Check if render version is in generated SVG."""

import sys
sys.path.insert(0, 'Scripts')

from parser import parse_csv
from svg_renderer import render_svg

model = parse_csv('Test/tests/test_notes.csv')
seq = model.sequences[0]
svg = render_svg(model, seq, 'High')

# Save to file
with open('test_render_output.svg', 'w') as f:
    f.write(svg)

# Check for version markers
has_data_attr = 'data-render-version' in svg
has_comment = '<!-- Render Version:' in svg
has_text = 'v:' in svg

print(f"=== Render Version Check ===")
print(f"Has data-render-version attr: {has_data_attr}")
print(f"Has Render Version comment: {has_comment}")
print(f"Has v: text: {has_text}")

if has_data_attr:
    import re
    match = re.search(r'data-render-version="([^"]+)"', svg)
    if match:
        print(f"Render version value: {match.group(1)}")

# Show last few lines
print(f"\nLast 5 lines of SVG:")
lines = svg.split('\n')
for line in lines[-5:]:
    if line.strip():
        print(f"  {line[:100]}")

print(f"\nSVG saved to test_render_output.svg ({len(svg)} chars)")
