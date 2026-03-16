#!/usr/bin/env python3
"""Enhanced diagnostic tool showing rendered connector text formatting."""

import sys
sys.path.insert(0, 'Scripts')

from parser import parse_csv
from model import Model

# Constants matching class_diagram_renderer.py
CONNECTOR_CHAR_WIDTH = 7.5
ARROW_MARKER_WIDTH = 10
TEXT_SPACING = 2  # spaces

def format_connector_text(src_mult, label, tgt_mult, arrow):
    """Format connector text as it should appear in SVG.
    
    Format: [arrow]  [src_mult]  [label]  [tgt_mult]
    - Arrow marker (ends with --)
    - 2+ spaces (minimum 2, more for marker clearance)
    - Source multiplicity
    - 2 spaces gap
    - Label
    - 2 spaces gap
    - Target multiplicity
    """
    
    # Convert Unicode to ASCII for display
    # ◇-- becomes dia-open--, ◆-- becomes dia-fill--, --> stays -->, ..> stays ..>
    arrow_display = arrow
    arrow_display = arrow_display.replace('◇--', 'dia-open--')
    arrow_display = arrow_display.replace('◆--', 'dia-fill--')
    arrow_display = arrow_display.replace('▷', 'tri-r')
    arrow_display = arrow_display.replace('◁', 'tri-l')
    if not arrow_display:
        arrow_display = "--"
    
    # Build text with required spacing
    src_mult_str = src_mult if src_mult else ""
    tgt_mult_str = tgt_mult if tgt_mult else ""
    label_str = label if label else ""
    
    # Format: arrow + 2+ spaces + src_mult + 2 spaces + label + 2 spaces + tgt_mult
    rendered_text = f"{arrow_display}  {src_mult_str}  {label_str}  {tgt_mult_str}"
    
    return rendered_text

def diagnose_rendered_format(csv_path):
    """Load and show RENDERED format of all connectors."""
    
    model = parse_csv(csv_path)
    
    if not model.class_diagrams:
        print("No class diagrams found")
        return
    
    print("=" * 140)
    print("CONNECTOR TEXT RENDERING FORMAT DIAGNOSTIC")
    print("=" * 140)
    
    for diagram in model.class_diagrams:
        print(f"\nDiagram: {diagram.diagram_id}")
        print(f"Description: {diagram.description}")
        print("-" * 140)
        print(f"{'Source':<15} {'Target':<15} {'RENDERED CONNECTOR TEXT FORMAT':<90}")
        print("-" * 140)
        
        for rel in diagram.relationships:
            rendered = format_connector_text(rel.src_mult, rel.label, rel.tgt_mult, rel.arrow)
            print(f"{rel.source:<15} {rel.target:<15} {rendered:<90}")
        
        print()

def main():
    csv_path = "Process/02_Architecture/class_diagrams.csv"
    
    print("\nLoading:", csv_path)
    diagnose_rendered_format(csv_path)
    
    print("\n" + "=" * 140)
    print("FORMAT SPECIFICATION:")
    print("=" * 140)
    print("""
Pattern: [arrow]  [src_mult]  [label]  [tgt_mult]

Examples:
  dia-open--  1  contains  0.*
  dia-fill--  1  owns  0.*
  -->  1  produces  1
  ..>  (none)  reads  (none)

Spacing Rules:
  - 2 spaces minimum between arrow and src_mult
  - 2 spaces between src_mult and label
  - 2 spaces between label and tgt_mult
  - Extra space for diamond marker width (diameter is 2 chars)
""")
    print("=" * 140)

if __name__ == "__main__":
    main()
