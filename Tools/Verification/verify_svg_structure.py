#!/usr/bin/env python3
"""Verify SVG structure has proper single text elements per connector."""

import sys
import re
sys.path.insert(0, 'Scripts')

from parser import parse_csv
from class_diagram_renderer import render_class_diagram_svg

def count_text_elements_in_regions(svg_content):
    """Count text elements in different regions to verify structure."""
    
    # Extract all text elements
    text_pattern = r'<text[^>]*?x="([^"]+?)"[^>]*?y="([^"]+?)"[^>]*?>([^<]+?)</text>'
    matches = re.findall(text_pattern, svg_content)
    
    print(f"Total text elements in SVG: {len(matches)}\n")
    
    # Group by y-coordinate (roughly by row)
    by_y = {}
    for x, y, text in matches:
        y_key = float(y)
        if y_key not in by_y:
            by_y[y_key] = []
        by_y[y_key].append((float(x), text))
    
    # Show connector text rows (those with arrow symbols)
    print("Connector text rows (sorted by y-coordinate):")
    print("=" * 80)
    print(f"{'Y':<10} {'Count':<8} {'Texts on Row'}")
    print("-" * 80)
    
    connector_y_coords = []
    for y in sorted(by_y.keys()):
        row_texts = by_y[y]
        # Check if this row has arrow symbols
        has_arrow = any(any(c in text for c in ['◇', '◆', '--']) for _, text in row_texts)
        
        if has_arrow:
            connector_y_coords.append((y, len(row_texts)))
            row_texts_sorted = sorted(row_texts, key=lambda x: x[0])
            texts_str = ' | '.join([f"{t}" for _, t in row_texts_sorted])
            print(f"{y:<10.1f} {len(row_texts):<8} {texts_str}")
    
    print("\n" + "=" * 80)
    
    # Analyze pattern
    counts = [count for _, count in connector_y_coords]
    if counts:
        print(f"\nConnector row element counts: {sorted(set(counts))}")
        if 1 in counts:
            single_element_rows = sum(1 for c in counts if c == 1)
            print(f"Rows with single text element: {single_element_rows}/{len(counts)}")
            if single_element_rows == len(counts):
                print("✓ ALL connector rows use single text elements (CORRECT!)")
            else:
                print(f"✗ Some connector rows use multiple text elements (NEEDS FIX)")
        else:
            print(f"✗ No single-element connector rows found (ALL use multiple elements)")


def main():
    csv_path = "Process/02_Architecture/class_diagrams.csv"
    diagram_id = "DataModelRelationships"
    
    print(f"Verifying SVG structure for {diagram_id}...\n")
    
    model = parse_csv(csv_path)
    
    # Find the diagram
    diagram = None
    for d in model.class_diagrams:
        if d.diagram_id == diagram_id:
            diagram = d
            break
    
    if not diagram:
        print(f"Diagram {diagram_id} not found")
        return
    
    # Render it
    print("Rendering diagram...")
    svg_content = render_class_diagram_svg(model, diagram, verbosity_level="Normal")
    print(f"SVG rendered successfully ({len(svg_content)} bytes)\n")
    
    # Count text elements in regions
    count_text_elements_in_regions(svg_content)

if __name__ == "__main__":
    main()
