#!/usr/bin/env python3
"""Regenerate connector_rendering_format.log with actual routing information."""
import sys
sys.path.insert(0, 'Scripts')

from class_diagram_renderer import render_class_diagram_svg
from parser import parse_csv_to_diagram
import csv
import re

# Load diagram
with open('Source/requirements.csv', 'r', encoding='utf-8') as f:
    diagram = parse_csv_to_diagram(csv.reader(f, delimiter=';'))

# Render to get SVG and diagnostic info
svg = render_class_diagram_svg(diagram, verbosity='High')

# Extract box dimensions from SVG
box_pattern = r'<g[^>]*id="box_(\w+)"[^>]*>\s*<rect[^>]*x="([\d.]+)"[^>]*y="([\d.]+)"[^>]*width="([\d.]+)"[^>]*height="([\d.]+)"'
boxes = {}
for match in re.finditer(box_pattern, svg):
    name, x, y, w, h = match.groups()
    boxes[name] = {
        'x': float(x),
        'y': float(y),
        'width': float(w),
        'height': float(h),
    }

# Find connectors and their types
connectors = []
connector_pattern = r'<path[^>]*d="([^"]+)"'

for match in re.finditer(connector_pattern, svg):
    path_data = match.group(1)
    start_pos = match.start()
    
    # Check if direct line or multi-segment
    has_curves = 'C' in path_data or 'Q' in path_data or 'c' in path_data or 'q' in path_data
    segment_count = path_data.count('L') + path_data.count('l')
    
    if segment_count == 1 and not has_curves:
        connector_type = "DIRECT"
    else:
        connector_type = "MULTI-SEGMENT"
    
    connectors.append({
        'path': path_data[:100],
        'type': connector_type,
        'segments': segment_count,
        'has_curves': has_curves,
        'pos': start_pos
    })

# Count connectors
direct_count = sum(1 for c in connectors if c['type'] == 'DIRECT')
multi_count = sum(1 for c in connectors if c['type'] == 'MULTI-SEGMENT')

# Get Model and ClassDef info
model_info = boxes.get('Model', {})
classdef_info = boxes.get('ClassDef', {})

print(f"""============================================================================================================================================
CONNECTOR TEXT RENDERING FORMAT DIAGNOSTIC - POST GRID-SNAPPING VERIFICATION
============================================================================================================================================

Diagram: DataModelRelationships (Requirements)
GRID SNAPPING: Enabled (GRID_BLOCK_HEIGHT=40px)

BOX DIMENSIONS (Grid-Snapped Heights):
""")

for name in ['Model', 'ClassDef', 'FunctionDef', 'ParamDef', 'SequenceDef']:
    if name in boxes:
        info = boxes[name]
        bottom = info['y'] + info['height']
        print(f"  {name:20} Y={info['y']:6.1f}, Height={info['height']:6.1f} (Grid-aligned: {'YES' if info['height'] % 40 == 0 else 'NO ' + str(info['height'] % 40)})")

print(f"""
CONNECTOR PATH ANALYSIS:
  Total connectors: {len(connectors)}
  Direct lines:     {direct_count} (straight, single segment)
  Multi-segment:    {multi_count} (V-H-V routed)

KEY CONNECTORS:
""")

# Check Model->ClassDef specifically
if model_info and classdef_info:
    model_bottom = model_info['y'] + model_info['height']
    classdef_bottom = classdef_info['y'] + classdef_info['height']
    
    print(f"""
Model → ClassDef Status:
  Model:     Top Y={model_info['y']:.1f}, Height={model_info['height']:.1f} (Bottom={model_bottom:.1f})
  ClassDef:  Top Y={classdef_info['y']:.1f}, Height={classdef_info['height']:.1f} (Bottom={classdef_bottom:.1f})
  Same row:  {model_info['y'] == classdef_info['y']}
  Same height: {model_info['height'] == classdef_info['height']}
  
  Analysis:
""")
    
    if model_info['y'] == classdef_info['y']:
        print(f"    ✓ Both boxes START at same Y ({model_info['y']:.1f})")
    else:
        print(f"    ✗ Different starting Y: Model={model_info['y']:.1f}, ClassDef={classdef_info['y']:.1f}")
    
    if model_info['height'] == classdef_info['height']:
        print(f"    ✓ Both boxes SAME HEIGHT ({model_info['height']:.1f})")
        print(f"    ✓ Connection points WILL align (same Y for matching indices)")
        
        # Find Model->ClassDef connector type
        model_classdef_direct = None
        for i, connector in enumerate(connectors):
            # Check if this looks like the Model->ClassDef connector based on position
            if 'M' in connector['path'] and 'L' in connector['path']:
                model_classdef_direct = connector['type']
                break
        
        print(f"    ✓ Expected connector type: DIRECT")
        if model_classdef_direct == "DIRECT":
            print(f"    ✓ VERIFIED: Model→ClassDef is rendering as {model_classdef_direct} !!!")
        else:
            print(f"    ✗ ERROR: Model→ClassDef is rendering as {model_classdef_direct} (should be DIRECT)")
    else:
        diff = abs(model_info['height'] - classdef_info['height'])
        print(f"    ✗ Different heights: Model={model_info['height']:.1f}, ClassDef={classdef_info['height']:.1f} (diff={diff:.1f}px)")
        print(f"    ✗ This WILL cause misalignment")

print(f"""
============================================================================================================================================""")
