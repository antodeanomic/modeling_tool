#!/usr/bin/env python3
"""
Diagnose the spanning forest and hierarchy for OrthogonalStressDense
"""
import sys
import os

# Add Scripts directory to path
script_dir = os.path.join(os.path.dirname(__file__), 'Scripts')
sys.path.insert(0, script_dir)

from parser import parse_csv
from class_diagram_renderer import (
    _calculate_abstraction_level,
    _build_spanning_forest,
    _collect_and_size_classes
)
from pathlib import Path

dense_csv = Path("Process/01_System/40_Tests/20_Advanced/test_class_diagram_orthogonal_stress.csv")
if not dense_csv.exists():
    print(f"File not found: {dense_csv}")
    sys.exit(1)

model = parse_csv(str(dense_csv))
diagram = None
for d in model.class_diagrams:
    if d.diagram_id == "OrthogonalStressDense":
        diagram = d
        break

if not diagram:
    print("Diagram not found")
    sys.exit(1)

# Build the hierarchy
class_names, boxes = _collect_and_size_classes(diagram, model, verbosity="High")
levels = _calculate_abstraction_level(diagram)
parent_children, claimed_children = _build_spanning_forest(diagram, levels)

print("=" * 70)
print("HIERARCHY ANALYSIS FOR OrthogonalStressDense")
print("=" * 70)

print("\nAbstraction Levels:")
for lvl in sorted(set(levels.values())):
    nodes = sorted([c for c, l in levels.items() if l == lvl])
    print(f"  Level {lvl}: {nodes}")

print("\nSpanning Forest (parent -> children):")
for parent in sorted(parent_children.keys()):
    children = sorted(parent_children[parent])
    print(f"  {parent}: {children}")

print("\nClaimed Children (nodes with a parent):")
print(f"  {sorted(claimed_children)}")

print("\nOrphaned Nodes (no parent assigned):")
orphans = sorted([c for c in class_names if c not in claimed_children])
print(f"  {orphans}")

# Check the problematic boxes
print("\nProblematic Boxes Analysis:")
for name in ["PaymentService", "InventoryService", "NotificationService"]:
    if name in levels:
        is_claimed = name in claimed_children
        is_orphan = name not in claimed_children
        parent = None
        for p, kids in parent_children.items():
            if name in kids:
                parent = p
                break
        print(f"  {name}:")
        print(f"    Level: {levels[name]}")
        print(f"    Parent: {parent}")
        print(f"    Is claimed: {is_claimed}")

print("=" * 70)
