#!/usr/bin/env python3
"""Test parsing test_notes.csv specifically."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Scripts'))

from server import find_csv_files
from parser import parse_csv

csv_files = find_csv_files()

test_notes_path = csv_files.get('test_notes.csv')
if test_notes_path:
    print(f"Testing test_notes.csv")
    print(f"Path: {test_notes_path}\n")
    
    try:
        print("Parsing...", end=" ", flush=True)
        model = parse_csv(test_notes_path)
        print(f"SUCCESS!")
        print(f"  Classes: {len(model.classes)}")
        print(f"  Sequences: {len(model.sequences)}")
        print(f"  Class Diagrams: {len(model.class_diagrams)}")
        print(f"  Warnings: {len(model.warnings)}")
        
        if model.warnings:
            print(f"\nFirst 5 warnings:")
            for w in model.warnings[:5]:
                print(f"  - {w}")
                
    except KeyboardInterrupt:
        print("INTERRUPTED (likely hanging)")
    except Exception as e:
        print(f"ERROR: {type(e).__name__}")
        print(f"  {str(e)}")
        import traceback
        traceback.print_exc()
else:
    print("test_notes.csv NOT FOUND!")
