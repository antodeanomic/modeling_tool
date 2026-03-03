#!/usr/bin/env python3
"""Diagnostic script to test gap calculation directly."""

import sys
import os

# Add Scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Scripts'))

from parser import parse_csv
from svg_renderer import render_svg

# Load the test model
print("=" * 60)
print("DIAGNOSTICS: Gap Calculation Test")
print("=" * 60)

csv_path = r'Test/tests/test_notes.csv'
print(f"\nLoading CSV: {csv_path}")
model = parse_csv(csv_path)

# DEBUG: Print model structure
print("\n" + "=" * 60)
print("MODEL STRUCTURE:")
print("=" * 60)
print(f"Classes: {len(model.classes)}")
for cls in model.classes:
    print(f"  {cls.name}:")
    for func in cls.functions:
        print(f"    - {func.name}")
        if func.returns:
            for ret in func.returns:
                print(f"      Returns: {ret.name} ({ret.description})")

# Get the sequence
seqs = model.sequences
print(f"\nSequences: {[s.seq_id for s in seqs]}\n")

if seqs:
    seq = seqs[0]
    print(f"Testing sequence: {seq.seq_id}")
    print(f"Steps in sequence: {len(seq.steps)}")
    for i, step in enumerate(seq.steps):
        print(f"  Step {i}: {step.src_obj} -> {step.dst_obj}, func={step.function}, ret_val={step.return_value}")
        # Try to find the function
        func_def = model.get_function(step.dst_obj, step.function)
        print(f"    get_function('{step.dst_obj}', '{step.function}') = {func_def}")
    
    print("\n" + "=" * 60)
    print("Rendering SVG (with diagnostic output)...")
    print("=" * 60 + "\n")
    
    # This will print all the diagnostic output
    svg = render_svg(model, seq, verbosity_level="High")
    
    print("\n" + "=" * 60)
    print("SVG rendering complete!")
    print("=" * 60)
