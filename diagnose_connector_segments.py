#!/usr/bin/env python3
"""Enhanced diagnostic showing segment-level connector text formatting."""

import sys
sys.path.insert(0, 'Scripts')

from parser import parse_csv
from model import Model
from class_diagram_renderer import _layout_classes, _calculate_required_spacing
from class_diagram_connectors import ConnectorPlanner

def format_connector_segment_text(src_mult, label, tgt_mult, arrow, segment_number, is_multiline=False):
    """Format connector text for a single segment.
    
    For single-line connectors: shows full text
    For multi-line: shows text appropriate to segment
    """
    
    # Convert Unicode to ASCII for display
    arrow_display = arrow
    arrow_display = arrow_display.replace('◇--', 'dia-open--')
    arrow_display = arrow_display.replace('◆--', 'dia-fill--')
    arrow_display = arrow_display.replace('..>', '..')
    arrow_display = arrow_display.replace('-->', '--')
    
    if not is_multiline:
        # Single segment: show all text
        src_mult_str = src_mult if src_mult else ""
        label_str = label if label else ""
        tgt_mult_str = tgt_mult if tgt_mult else ""
        return f"{arrow_display}  {src_mult_str}  {label_str}  {tgt_mult_str}"
    else:
        # Multi-segment: distribute text
        if segment_number == 1:
            # First segment: source multiplicity
            src_mult_str = src_mult if src_mult else ""
            return f"{arrow_display}  {src_mult_str}"
        elif segment_number == 2:
            # Middle segment: label
            label_str = label if label else ""
            return f"{arrow_display}  {label_str}"
        else:
            # Final segment: target multiplicity
            tgt_mult_str = tgt_mult if tgt_mult else ""
            return f"{arrow_display}  {tgt_mult_str}"

def diagnose_with_segments(csv_path):
    """Load and show connectors with segment information."""
    
    model = parse_csv(csv_path)
    
    if not model.class_diagrams:
        print("No class diagrams found")
        return
    
    print("=" * 160)
    print("CONNECTOR TEXT SEGMENT-LEVEL DIAGNOSTIC")
    print("=" * 160)
    
    for diagram in model.class_diagrams:
        print(f"\nDiagram: {diagram.diagram_id} - {diagram.description}")
        print("-" * 160)
        print(f"{'Source':<18} {'Target':<18} {'Seg':<5} {'RENDERED TEXT':<100}")
        print("-" * 160)
        
        for rel in diagram.relationships:
            # For now, assume all are single-segment (future: check routing_mode)
            # Single segment shows all text on one line
            is_multiline = False  # TODO: detect from diagram routing_mode
            segment_text = format_connector_segment_text(
                rel.src_mult, rel.label, rel.tgt_mult, rel.arrow, 
                segment_number=1, is_multiline=is_multiline
            )
            
            print(f"{rel.source:<18} {rel.target:<18} {'1':<5} {segment_text:<100}")
        
        print()

def main():
    csv_path = "Process/02_Architecture/class_diagrams.csv"
    
    print("\nLoading:", csv_path)
    diagnose_with_segments(csv_path)
    
    print("\n" + "=" * 160)
    print("FORMAT SPECIFICATION:")
    print("=" * 160)
    print("""
SINGLE-SEGMENT CONNECTORS (diagonal, direct):
  Seg1: [arrow]  [src_mult]  [label]  [tgt_mult]
  Example: dia-open--  1  contains  0.*

MULTI-SEGMENT CONNECTORS (orthogonal, V-H-V):
  Seg1: [arrow]  [src_mult]
  Seg2: [arrow]  [label]
  Seg3: [arrow]  [tgt_mult]
  Examples:
    Seg1: dia-fill--  1
    Seg2: dia-fill--  owns
    Seg3: dia-fill--  0.*

SPACING RULES:
  - 2 spaces minimum between arrow and text
  - 2 spaces between separate text elements
  - Multi-segment breaks text across segments (future implementation)
""")
    print("=" * 160)

if __name__ == "__main__":
    main()
