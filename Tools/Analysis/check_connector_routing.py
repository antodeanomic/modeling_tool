#!/usr/bin/env python3
"""Check actual routing for each connector."""

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

print("Connector Routing Analysis:")
print("=" * 100)
print(f"{'Source':<20} {'Target':<20} {'Path Type':<15} {'Segments':<10}")
print("-" * 100)

for conn in connectors:
    seg_count = len(conn.segments) if conn.segments else 0
    print(f"{conn.source_name:<20} {conn.target_name:<20} {conn.path_type:<15} {seg_count}")
