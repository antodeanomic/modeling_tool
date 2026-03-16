#!/usr/bin/env python3
"""Check the API response for MultiConnectorTest diagram."""

import urllib.request
import json

try:
    response = urllib.request.urlopen('http://localhost:8000/api/all_diagrams', timeout=5)
    data = json.loads(response.read().decode('utf-8'))
    diagrams = data['diagrams']
    
    # Find MultiConnectorTest
    multi = [d for d in diagrams if d['id'] == 'MultiConnectorTest']
    
    if multi:
        print("Found MultiConnectorTest in API!")
        for d in multi:
            print(f"  ID: {d['id']}")
            print(f"  CSV: {d['csv']}")
            print(f"  Type: {d['type']}")
            print(f"  Name: {d['name']}")
            print(f"  Hierarchy: {d.get('hierarchy', [])}")
    else:
        print("MultiConnectorTest NOT found in API")
        print(f"\nTotal diagrams: {len(diagrams)}")
        
        # Check what test diagrams ARE there
        test_diagrams = [d for d in diagrams if 'test_' in d['csv']]
        print(f"\nTest diagrams ({len(test_diagrams)}):")
        for d in sorted(test_diagrams, key=lambda x: x['csv']):
            if d['type'] == 'class_diagram':
                print(f"  [CLS] {d['id']:30} from {d['csv']}")
                
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
