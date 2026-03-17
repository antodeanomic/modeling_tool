#!/usr/bin/env python3
"""Test collision detection system."""

from Scripts.class_diagram_connectors import ConnectorPlanner
from Scripts.collision_detector import CollisionDetector

# Create test scenario with crossing connectors
p = ConnectorPlanner()

# Simple 2x2 grid of boxes
p.add_rectangle('A', 0, 0, 100, 80)
p.add_rectangle('B', 200, 0, 100, 80)
p.add_rectangle('C', 0, 150, 100, 80)
p.add_rectangle('D', 200, 150, 100, 80)

# Create connectors that will cross
# A->D and C->B will cross diagonally
p.add_connector('A', 'D', '--O', label='A-D')
p.add_connector('C', 'B', '--O', label='C-B')
p.add_connector('A', 'B', '--O', label='A-B')
p.add_connector('C', 'D', '--O', label='C-D')

print("Test Scenario: 2x2 grid with diagonal crossings")
print("=" * 60)
print()
print("Boxes:")
print("  A (0,0)      B (200,0)")
print("  C (0,150)    D (200,150)")
print()
print("Connectors:")
print("  A -> D (should cross C -> B)")
print("  C -> B (should cross A -> D)")
print("  A -> B (horizontal)")
print("  C -> D (horizontal)")
print()

# Plan connectors
p.plan_connectors()

print("After planning - connector assignments:")
for i, c in enumerate(p.connectors):
    if c.source_point_idx > 0:
        print(f"  {c.label}: {c.source_edge}({c.source_point_idx}) -> {c.target_edge}({c.target_point_idx})")
        print(f"           type={c.path_type}")
    else:
        print(f"  {c.label}: NOT ASSIGNED")

print()
print("=" * 60)
print("Detecting crossings...")
print("=" * 60)

detector = CollisionDetector()
crossings = detector.detect_crossings(p.connectors)

print(f"\nFound {len(crossings)} crossing(s):")
for i, crossing in enumerate(crossings, 1):
    print(f"\n  Crossing {i}:")
    print(f"    Segments: {crossing.seg1_id} x {crossing.seg2_id}")
    print(f"    Location: ({crossing.intersection_x:.1f}, {crossing.intersection_y:.1f})")
    print(f"    Parameters: t1={crossing.t1:.2f}, t2={crossing.t2:.2f}")

if len(crossings) == 0:
    print("\n  No crossings detected!")

print()
print("=" * 60)
print("Test Complete")
print("=" * 60)
