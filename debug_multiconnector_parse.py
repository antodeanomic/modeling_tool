#!/usr/bin/env python3
"""Debug script to check if MultiConnectorTest is being parsed."""

import sys
sys.path.insert(0, 'Scripts')

from parser import parse_csv

try:
    model = parse_csv('Test/tests/test_multiconnector_rightangle.csv')
    
    print(f"Classes found: {len(model.classes)}")
    for cls in model.classes:
        print(f"  - {cls.name}")
    
    print(f"\nSequences found: {len(model.sequences)}")
    for seq in model.sequences:
        print(f"  - {seq.seq_id}")
        
    print(f"\nClass diagrams found: {len(model.class_diagrams)}")
    for cd in model.class_diagrams:
        print(f"  - {cd.diagram_id}: {len(cd.relationships)} relationships")
        for rel in cd.relationships:
            print(f"      {rel.source} → {rel.target}")
    
    print(f"\nWarnings/Errors: {len(model.warnings)}")
    for w in model.warnings:
        print(f"  - {w}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
