#!/usr/bin/env python3
"""Determine routing by analyzing connector edges."""

import sys
sys.path.insert(0, 'Scripts')

from parser import parse_csv
from class_diagram_connectors import ConnectorPlanner

csv_path = 'Process/02_Architecture/class_diagrams.csv'
model = parse_csv(csv_path)
diagram = [d for d in model.class_diagrams if d.diagram_id == 'DataModelRelationships'][0]

print("Analyzing connector routing for DataModelRelationships")
print("=" * 100)
print(f"{'Source':<20} {'Target':<20} {'Src Edge':<12} {'Tgt Edge':<12} {'Path Type':<15}")
print("-" * 100)

planner = ConnectorPlanner(diagram)
connectors = planner.get_connectors()

for conn in connectors:
    src_edge = conn.source_edge if hasattr(conn, 'source_edge') else '?'
    tgt_edge = conn.target_edge if hasattr(conn, 'target_edge') else '?'
    path_type = conn.path_type
    
    print(f"{conn.source_name:<20} {conn.target_name:<20} {src_edge:<12} {tgt_edge:<12} {path_type:<15}")

print("\n" + "=" * 100)
# Count them
direct = sum(1 for c in connectors if c.path_type == 'direct')
multi = sum(1 for c in connectors if c.path_type == 'multi_segment')
print(f"DIRECT (straight line):        {direct}")
print(f"MULTI-SEGMENT (orthogonal):    {multi}")
