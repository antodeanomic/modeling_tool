#!/usr/bin/env python3
"""Debug grid snapping and connector routing."""
import sys
sys.path.insert(0, 'Scripts')

from class_diagram_renderer import render_class_diagram_svg, _compute_class_box_size
from parser import parse_csv_to_diagram
import csv

# Load diagram
with open('Source/requirements.csv', 'r', encoding='utf-8') as f:
    diagram = parse_csv_to_diagram(csv.reader(f, delimiter=';'))

# Test grid snapping function directly
print("Testing _snap_height_to_grid():")
test_heights = [187.0, 137.0, 95.0, 72.0, 150.0]
for h in test_heights:
    from class_diagram_renderer import _snap_height_to_grid
    snapped = _snap_height_to_grid(h)
    print(f"  {h:6.1f} → {snapped:6.1f} (blocks: {snapped//40})")

# Check that the rendering actually uses grid snapping
print("\nTest box sizing (checking if grid snapping is applied):")
test_class = {'id': 'TestClass', 'type': 'class', 'members': [{'type': 'field', 'name': 'field1'}] * 3}

width, height, has_members, has_functions = _compute_class_box_size(test_class, 'TestClass', 'class')
print(f"  Input: 1 member (should need ~95px)")
print(f"  Output height: {height:.1f}px")
print(f"  Is grid-snapped (multiple of 40): {height % 40 == 0}")

# Check actual diagram rendering
print("\nRendering diagram...")
svg = render_class_diagram_svg(diagram, verbosity='High')

# Save to file for inspection
with open('temp_svg_output.svg', 'w', encoding='utf-8') as f:
    f.write(svg)
print("  Saved to temp_svg_output.svg")

# Extract key info
import re

# Find Model and ClassDef boxes
model_match = re.search(r'id="box_Model"[^>]*>\s*<rect[^>]*x="([\d.]+)"[^>]*y="([\d.]+)"[^>]*width="([\d.]+)"[^>]*height="([\d.]+)"', svg)
classdef_match = re.search(r'id="box_ClassDef"[^>]*>\s*<rect[^>]*x="([\d.]+)"[^>]*y="([\d.]+)"[^>]*width="([\d.]+)"[^>]*height="([\d.]+)"', svg)

if model_match and classdef_match:
    m_x, m_y, m_w, m_h = [float(x) for x in model_match.groups()]
    c_x, c_y, c_w, c_h = [float(x) for x in classdef_match.groups()]
    
    print(f"\nBox Dimensions (from rendered SVG):")
    print(f"  Model:    X={m_x:.1f}, Y={m_y:.1f}, W={m_w:.1f}, H={m_h:.1f}")
    print(f"    Is grid-snapped: {m_h % 40 == 0} ({int(m_h // 40)} blocks)")
    print(f"  ClassDef: X={c_x:.1f}, Y={c_y:.1f}, W={c_w:.1f}, H={c_h:.1f}")
    print(f"    Is grid-snapped: {c_h % 40 == 0} ({int(c_h // 40)} blocks)")
    
    if m_y == c_y:
        print(f"  ✓ Same row: Both at Y={m_y:.1f}")
    else:
        print(f"  ✗ Different rows: Model Y={m_y:.1f}, ClassDef Y={c_y:.1f}")
    
    if m_h == c_h:
        print(f"  ✓ Same height: {m_h:.1f}px")
        print(f"  → Connection points WILL ALIGN → Connector should be DIRECT")
    else:
        print(f"  ✗ Different heights: Model={m_h:.1f}, ClassDef={c_h:.1f}")
        print(f"  → Connection points WON'T ALIGN → Connector may be MULTI-SEGMENT")

# Count connector paths
paths = list(re.finditer(r'<path[^>]*d="([^"]+)"', svg))
direct = sum(1 for m in paths if m.group(1).count('L') == 1 and 'C' not in m.group(1))
multi = len(paths) - direct

print(f"\nConnector Summary:")
print(f"  Total paths: {len(paths)}")
print(f"  Direct (1 segment): {direct}")
print(f"  Multi-segment: {multi}")
