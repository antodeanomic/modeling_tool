#!/usr/bin/env python3
"""Trace through rendering of a specific connector."""

import sys
sys.path.insert(0, 'Scripts')

from parser import parse_csv

csv_path = 'Process/02_Architecture/class_diagrams.csv'
model = parse_csv(csv_path)

# Find the DataModelRelationships diagram
diagram = [d for d in model.class_diagrams if d.diagram_id == 'DataModelRelationships'][0]

# Show connector details
print(f"Diagram: {diagram.diagram_id}")
print(f"Total relationships: {len(diagram.relationships)}")
print("\nRelationship details:")
print("=" * 100)
print(f"{'Src':<20} {'Tgt':<20} {'Label':<15} {'SrcMult':<10} {'TgtMult':<10}")
print("-" * 100)

for conn in diagram.relationships:
    src_name = conn.source.strip() if hasattr(conn, 'source') and conn.source else '?'
    tgt_name = conn.target.strip() if hasattr(conn, 'target') and conn.target else '?'
    label = str(conn.label).strip() if conn.label else '(empty)'
    src_mult = str(conn.src_mult).strip() if conn.src_mult else '(empty)'
    tgt_mult = str(conn.tgt_mult).strip() if conn.tgt_mult else '(empty)'
    
    print(f"{src_name:<20} {tgt_name:<20} {label:<15} {src_mult:<10} {tgt_mult:<10}")

# Check if multiplicity fields are truthy
print("\n" + "=" * 100)
print("\nMultiplicity truthiness check:")
for i, conn in enumerate(diagram.relationships[:3]):
    print(f"\nConnector {i}:")
    print(f"  src_mult = {repr(conn.src_mult)} -> bool = {bool(conn.src_mult)}")
    print(f"  tgt_mult = {repr(conn.tgt_mult)} -> bool = {bool(conn.tgt_mult)}")
    print(f"  label    = {repr(conn.label)} -> bool = {bool(conn.label)}")
