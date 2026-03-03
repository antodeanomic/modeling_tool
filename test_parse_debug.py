#!/usr/bin/env python3
"""Debug the Success note parsing."""

import sys
sys.path.insert(0, 'Scripts')

from model import SequenceDef, SequenceStep, NoteDef
from parser import parse_csv

# Load the model
print("Loading test_notes.csv...")
model = parse_csv('Test/tests/test_notes.csv')

# Get the sequence
seq = model.get_sequence('SoftReq_TEST_001')
print(f"\nSequence: {seq.seq_id}")
print(f"Steps: {len(seq.steps)}\n")

# Print all steps and their lane notes
for i, step in enumerate(seq.steps):
    print(f"Step {i}: {step.src_obj} -> {step.dst_obj} ({step.function})")
    
    # Check if it has lane notes
    if hasattr(step, 'lane_notes') and step.lane_notes:
        print(f"  Lane notes found:")
        for lane_name, note in step.lane_notes.items():
            print(f"    - {lane_name}: {note.note_type} - {note.content}")
    else:
        print(f"  No lane notes")
    
    # Check for function notes
    if hasattr(step, 'function_note') and step.function_note:
        print(f"  Function note: {step.function_note.note_type} - {step.function_note.content}")
    
    print()

# Check for unexpected participants
print("\nAll classes in diagram:")
for cls in model.classes:
    print(f"  - {cls.name}")
