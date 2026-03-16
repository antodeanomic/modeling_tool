#!/usr/bin/env python3
"""Test the /api/all_diagrams endpoint to verify hierarchy is returned."""

import json
import urllib.request

try:
    print("Testing /api/all_diagrams endpoint...")
    resp = urllib.request.urlopen('http://localhost:8000/api/all_diagrams')
    data = json.loads(resp.read())
    
    diagrams = data.get('diagrams', [])
    print(f"\nTotal diagrams found: {len(diagrams)}")
    
    # Show first 3 diagrams with hierarchy
    print("\nFirst 3 diagrams:")
    for i, d in enumerate(diagrams[:3]):
        print(f"\n  {i+1}. {d['id']}")
        print(f"     Type: {d['type']}")
        print(f"     CSV: {d['csv']}")
        print(f"     Hierarchy: {d.get('hierarchy', [])}")
    
    # Check if any diagrams have hierarchy
    with_hierarchy = [d for d in diagrams if d.get('hierarchy')]
    print(f"\n\nDiagrams with hierarchy: {len(with_hierarchy)}")
    if with_hierarchy:
        print("Sample with hierarchy:")
        for d in with_hierarchy[:2]:
            print(f"  {d['id']} -> {d['hierarchy']}")
    else:
        print("No diagrams with hierarchy found (this is OK if no CSVs in diagrams/ folder)")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
