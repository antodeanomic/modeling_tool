#!/usr/bin/env python3
"""Minimal server test to see where it hangs."""

import sys
import os

# This must be run from Scripts/ directory
from server import CSV_FILES, DEFAULT_CSV, load_model

print("CSV FILES FOUND:")
if CSV_FILES:
    print(f"  Total: {len(CSV_FILES)}")
    print(f"  Default: {DEFAULT_CSV}")
else:
    print("  NONE!")
    sys.exit(1)

print("\nLoading default CSV...", flush=True)
try:
    print(f"  CSV: {DEFAULT_CSV}")
    print(f"  Attempting parse...", end=" ", flush=True)
    model = load_model(DEFAULT_CSV)
    print(f"SUCCESS!")
    print(f"    Classes: {len(model.classes)}")
    print(f"    Sequences: {len(model.sequences)}")
    print(f"    Class Diagrams: {len(model.class_diagrams)}")
except KeyboardInterrupt:
    print("INTERRUPTED!")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {str(e)[:100]}")
    import traceback
    traceback.print_exc()
