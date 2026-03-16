#!/usr/bin/env python3
"""Test parsing each CSV individually."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Scripts'))

from server import find_csv_files
from parser import parse_csv

csv_files = find_csv_files()

print(f"Testing {len(csv_files)} CSV files...\n")

# Test just the multiconnector CSV first
print("="*70)
print("TESTING MULTICONNECTOR CSV:")
print("="*70)

multiconnector_path = csv_files.get('test_multiconnector_rightangle.csv')
if multiconnector_path:
    print(f"Path: {multiconnector_path}")
    try:
        print("Parsing...", end=" ", flush=True)
        model = parse_csv(multiconnector_path)
        print(f"SUCCESS!")
        print(f"  Classes: {len(model.classes)}")
        print(f"  Sequences: {len(model.sequences)}")
        print(f"  Class Diagrams: {len(model.class_diagrams)}")
        if model.class_diagrams:
            for cd in model.class_diagrams:
                print(f"    - {cd.diagram_id}: {len(cd.relationships)} relationships")
    except Exception as e:
        print(f"ERROR: {type(e).__name__}")
        print(f"  {str(e)[:100]}")
        import traceback
        traceback.print_exc()
else:
    print("NOT FOUND!")
