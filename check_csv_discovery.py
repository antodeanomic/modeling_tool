#!/usr/bin/env python3
"""Check what CSV files the server discovers."""

import os
import sys

# Add Scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Scripts'))

from server import find_csv_files, find_csv_files_hierarchical

print("=" * 70)
print("CSV FILES DISCOVERED BY SERVER")
print("=" * 70)

try:
    csv_files = find_csv_files()
    
    print(f"\nTotal CSVs found: {len(csv_files)}")
    
    # Look for multiconnector
    multiconnector_found = False
    for name, path in sorted(csv_files.items()):
        if 'multiconnector' in name.lower():
            print(f"\n>>> FOUND MULTICONNECTOR <<<")
            print(f"Name: {name}")
            print(f"Path: {path}")
            print(f"Exists: {os.path.exists(path)}")
            multiconnector_found = True
    
    if not multiconnector_found:
        print("\n*** MULTICONNECTOR NOT FOUND ***")
        print("\nAll discovered CSVs:")
        for name in sorted(csv_files.keys()):
            print(f"  - {name}")
            
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
