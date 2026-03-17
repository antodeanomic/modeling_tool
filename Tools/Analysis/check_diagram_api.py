#!/usr/bin/env python3
"""Check if MultiConnectorTest diagram is in the API response."""

import urllib.request
import json

try:
    response = urllib.request.urlopen('http://localhost:8000/api/all_diagrams', timeout=5)
    data = json.loads(response.read().decode('utf-8'))
    diagrams = data['diagrams']
    
    # Find the MultiConnectorTest diagram
    multiconnector_diagrams = [d for d in diagrams if 'multiconnector' in d['id'].lower()]
    
    print(f"Total diagrams found: {len(diagrams)}")
    print(f"\nMultiConnector diagrams found: {len(multiconnector_diagrams)}")
    
    if multiconnector_diagrams:
        for d in multiconnector_diagrams:
            print(f"  - ID: {d['id']}")
            print(f"    CSV: {d['csv']}")
            print(f"    Type: {d['type']}")
            print(f"    Hierarchy: {d.get('hierarchy', [])}")
    else:
        print("\nNo MultiConnector diagrams found!")
        print("\nAll test diagrams:")
        test_diagrams = [d for d in diagrams if 'test_' in d['csv']]
        for d in test_diagrams:
            print(f"  - {d['id']} ({d['type']}) from {d['csv']}")
            
except Exception as e:
    print(f"Error: {e}")
