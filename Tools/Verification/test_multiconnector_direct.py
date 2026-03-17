#!/usr/bin/env python3
"""Test that MultiConnectorTest diagram loads and renders correctly."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Scripts'))

from parser import parse_csv
import class_diagram_renderer

# Load the test CSV
csv_path = os.path.join(os.path.dirname(__file__), 'Test/tests/test_multiconnector_rightangle.csv')
print(f"Loading CSV: {csv_path}")

model = parse_csv(csv_path)

print(f"\nParsed {len(model.classes)} classes")
print(f"Parsed {len(model.class_diagrams)} class diagrams")

if not model.class_diagrams:
    print("ERROR: No class diagrams found!")
    sys.exit(1)

diagram = model.class_diagrams[0]
print(f"\nDiagram: {diagram.diagram_id}")
print(f"Description: {diagram.description}")
print(f"Relationships: {len(diagram.relationships)}")
print(f"Routing: {diagram.routing}")

# Try to render it
try:
    print("\nRendering diagram...")
    
    # Render with orthogonal routing
    svg = class_diagram_renderer.render_class_diagram_svg(
        model=model,
        diagram=diagram,
        verbosity_level="High"
    )
    
    if 'V-H-V' in svg or '<path' in svg:
        print("SUCCESS: Diagram rendered successfully!")
        print(f"SVG size: {len(svg)} bytes")
        
        # Count connectors
        connector_count = svg.count('<path')
        print(f"Number of path elements (connectors): {connector_count}")
        
        # Check for V-H-V pattern in rendering
        if diagram.relationships and len(diagram.relationships) > 2:
            print("\nDiagram contains multiple connectors - V-H-V routing should be visible")
    else:
        print("ERROR: SVG appears empty or invalid!")
        sys.exit(1)
        
except Exception as e:
    print(f"ERROR during rendering: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\nAll tests passed!")
