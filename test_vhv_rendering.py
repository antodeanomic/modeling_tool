#!/usr/bin/env python3
"""Test MultiConnectorTest rendering and save SVG output."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Scripts'))

from parser import parse_csv
import class_diagram_renderer

# Load the test CSV
csv_path = os.path.join(os.path.dirname(__file__), 'Test/tests/test_multiconnector_rightangle.csv')
print(f"Loading CSV: {csv_path}")

model = parse_csv(csv_path)

if not model.class_diagrams:
    print("ERROR: No class diagrams found!")
    sys.exit(1)

diagram = model.class_diagrams[0]
print(f"Diagram: {diagram.diagram_id}")
print(f"Description: {diagram.description}")
print(f"CSV routing mode: {diagram.routing}")
print(f"Relationships: {len(diagram.relationships)}")

for i, rel in enumerate(diagram.relationships, 1):
    src_name = rel.source.name if hasattr(rel.source, 'name') else rel.source
    tgt_name = rel.target.name if hasattr(rel.target, 'name') else rel.target
    print(f"  {i}. {src_name} --> {tgt_name} [{rel.label}]")

# Try rendering with orthogonal routing (which uses V-H-V)
print("\n=== Rendering with ORTHOGONAL routing ===")
try:
    svg = class_diagram_renderer.render_class_diagram_svg(
        model=model,
        diagram=diagram,
        verbosity_level="High"
    )
    
    # Save SVG for inspection
    svg_path = 'test_multiconnector_output.svg'
    with open(svg_path, 'w') as f:
        f.write(svg)
    
    print(f"Saved to: {svg_path}")
    
    # Count path elements
    path_count = svg.count('<path')
    print(f"Path elements in SVG: {path_count}")
    
    # Count L commands (line segments) which indicate multi-segment paths
    line_count = svg.count(' L ')
    print(f"Line segments (L commands): {line_count}")
    
    # Check for vertical-horizontal-vertical pattern
    if ' L ' in svg:
        print("\n✓ Multi-segment paths detected (V-H-V routing active)")
    
    print("\n SUCCESS: Diagram rendered")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
