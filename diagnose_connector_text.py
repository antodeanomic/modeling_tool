#!/usr/bin/env python3
"""Diagnostic tool to log connector text segments and their positions."""

import sys
sys.path.insert(0, 'Scripts')

from parser import parse_csv
from model import Model

def diagnose_class_diagram(csv_path):
    """Load a class diagram and log all connector segments with their text."""
    
    model = parse_csv(csv_path)
    
    if not model.class_diagrams:
        print("No class diagrams found")
        return
    
    print("=" * 120)
    print("CONNECTOR TEXT DIAGNOSTIC LOG")
    print("=" * 120)
    
    for diagram in model.class_diagrams:
        print(f"\nDiagram: {diagram.diagram_id} - {diagram.description}")
        print("-" * 120)
        print(f"{'Source':<15} {'Target':<15} {'Arrow':<8} {'Src Mult':<12} {'Label':<35} {'Tgt Mult':<12}")
        print("-" * 120)
        
        for rel in diagram.relationships:
            src_mult = rel.src_mult if rel.src_mult else "(none)"
            tgt_mult = rel.tgt_mult if rel.tgt_mult else "(none)"
            label = rel.label if rel.label else "(no label)"
            # Convert Unicode arrows to ASCII for logging
            arrow_display = rel.arrow
            arrow_display = arrow_display.replace('◇--', 'dia-open--')
            arrow_display = arrow_display.replace('◆--', 'dia-fill--')
            arrow_display = arrow_display.replace('▷', 'tri-r')
            arrow_display = arrow_display.replace('◁', 'tri-l') if arrow_display else "--"
            
            print(f"{rel.source:<15} {rel.target:<15} {arrow_display:<8} {src_mult:<12} {label:<35} {tgt_mult:<12}")
        
        print()

def main():
    # Test with the main architecture diagram
    csv_path = "Process/02_Architecture/class_diagrams.csv"
    
    print("\nLoading:", csv_path)
    diagnose_class_diagram(csv_path)
    
    print("\n" + "=" * 120)
    print("END DIAGNOSTIC LOG")
    print("=" * 120)

if __name__ == "__main__":
    main()
