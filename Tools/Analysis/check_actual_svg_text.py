#!/usr/bin/env python3
"""Extract actual SVG text elements to verify rendering."""

import sys
import json
sys.path.insert(0, 'Scripts')

from parser import parse_csv
from model import Model
from class_diagram_renderer import render_class_diagram_svg

def extract_svg_text_elements(diagram_id, csv_path):
    """Load a diagram and extract actual SVG text elements."""
    
    model = parse_csv(csv_path)
    
    # Find the diagram
    diagram = None
    for d in model.class_diagrams:
        if d.diagram_id == diagram_id:
            diagram = d
            break
    
    if not diagram:
        print(f"Diagram {diagram_id} not found")
        return []
    
    # Render it
    svg_content = render_class_diagram_svg(model, diagram, verbosity_level="High")
    
    # Extract all <text> elements
    import re
    text_elements = []
    
    # Pattern to find complete text elements
    pattern = r'<text[^>]*>([^<]+)</text>'
    matches = re.findall(pattern, svg_content)
    
    return matches

def main():
    csv_path = "Process/02_Architecture/class_diagrams.csv"
    diagram_id = "DataModelRelationships"
    
    print(f"Rendering {diagram_id} and extracting text elements...")
    print("=" * 100)
    
    text_elements = extract_svg_text_elements(diagram_id, csv_path)
    
    print(f"\nActual SVG Text Elements (connector text only):\n")
    connector_texts = [t for t in text_elements if any(x in t for x in ['dia-', 'contains', 'owns', 'produces', 'parses', '-->', '..>'])]
    
    for i, text in enumerate(connector_texts, 1):
        print(f"{i:2}. {repr(text)}")
    
    print("\n" + "=" * 100)
    print(f"Total connector text elements found: {len(connector_texts)}")
    print()
    print("If using PROPER formatting, each should be:")
    print("  '◇--  1  contains  0.*'  (with 2 spaces)")
    print()
    print("If using OLD formatting, might see:")
    print("  '1', 'contains', '0.*' (as separate elements with lots of whitespace)")

if __name__ == "__main__":
    main()
