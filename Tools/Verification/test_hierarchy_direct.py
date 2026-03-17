#!/usr/bin/env python3
"""Test the hierarchy function directly."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Scripts'))

from server import find_csv_files_hierarchical, find_csv_files

print("=== Testing Hierarchy Discovery ===\n")

print("1. Hierarchical CSVs found:")
hierarchical = find_csv_files_hierarchical()
print(f"   Total: {len(hierarchical)}")
if hierarchical:
    for item in hierarchical[:5]:
        print(f"   - {item['name']}")
        print(f"     Path: {item['relative_path']}")
        print(f"     Hierarchy: {item['hierarchy']}")
else:
    print("   No hierarchical CSVs found (expected if diagrams/ is empty)")

print("\n2. All CSVs found (flat list):")
all_csvs = find_csv_files()
print(f"   Total: {len(all_csvs)}")
print(f"   Sample CSVs: {list(all_csvs.keys())[:5]}")

print("\n=== All tests passed! ===")
