#!/usr/bin/env python3
"""Verify actual routing for each connector."""

import sys
sys.path.insert(0, 'Scripts')

from parser import parse_csv
from class_diagram_connectors import ConnectorPlanner

csv_path = 'Process/02_Architecture/class_diagrams.csv'
model = parse_csv(csv_path)
diagram = [d for d in model.class_diagrams if d.diagram_id == 'DataModelRelationships'][0]

# Create planner to get connector routes
planner = ConnectorPlanner(diagram)
connectors = planner.get_connectors()

print("Connector Routing Analysis for DataModelRelationships")
print("=" * 120)
print(f"{'Source':<20} {'Target':<20} {'Path Type':<15} {'Segments':<10} {'Arrow':<10}")
print("-" * 120)

for conn in connectors:
    seg_count = len(conn.segments) if conn.segments else 0
    path_type = conn.path_type if hasattr(conn, 'path_type') else 'unknown'
    arrow = conn.arrow_type if hasattr(conn, 'arrow_type') else '?'
    
    print(f"{conn.source_name:<20} {conn.target_name:<20} {path_type:<15} {seg_count:<10} {arrow:<10}")

print("\n" + "=" * 120)
print("Summary:")
direct_count = sum(1 for c in connectors if c.path_type == "direct")
multi_count = sum(1 for c in connectors if c.path_type == "multi")
print(f"Direct (single-line) connectors: {direct_count}")
print(f"Multi-segment connectors: {multi_count}")
