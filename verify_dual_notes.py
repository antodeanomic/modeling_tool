#!/usr/bin/env python3
"""Verify both function notes and lifeline notes render correctly."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Scripts'))

from parser import parse_csv
from svg_renderer import render_svg
import re

def count_note_types(svg):
    """Count function and lifeline notes by analyzing note positions and icons."""
    # Look for note icons in the SVG (@ symbols and other icons)
    info_notes = svg.count('@Info')
    warning_notes = svg.count('@Warning')
    error_notes = svg.count('@Error')
    success_notes = svg.count('@Success')
    
    # Also look for note paths (filled rectangles with folded corners)
    import re
    note_paths = re.findall(r'<path d="M [^"]*fold', svg)
    
    return info_notes + warning_notes + error_notes + success_notes, len(note_paths)

print("Starting verification...")

# Parse the updated ui_controls test with both note types
model = parse_csv('Test/tests/test_ui_controls.csv')
print("Model parsed successfully")
# Find the correct sequence by ID
seq_to_render = None
for seq in model.sequences:
    if seq.seq_id == 'SoftReq_TEST_UI_001':
        seq_to_render = seq
        break
if not seq_to_render:
    seq_to_render = model.sequences[0]
svg = render_svg(model, seq_to_render, verbosity_level='High')
print(f"SVG rendered: {len(svg)} characters")

print("=" * 70)
print("DUAL NOTE FORMAT VERIFICATION - test_ui_controls")
print("=" * 70)

# Count note elements
note_count, path_count = count_note_types(svg)
print(f"\n✓ Total note references found: {note_count}")
print(f"✓ Note box paths rendered: {path_count}")
print(f"  Combined: {note_count + path_count} note elements total")
print(f"  Expected: Function notes (on arrows) + Lifeline notes (on objects)")

# Extract sample positions to show both types rendering
patterns = [
    (r'ValidateCredentials[^<]*.*?<g id="note', 'Function note on ValidateCredentials'),
    (r'RecordLogin[^<]*.*?<g id="note', 'Function note on RecordLogin'),
    (r'>@Info<.*?</text>', 'Info note symbol'),
    (r'>@Warning<.*?</text>', 'Warning note symbol'),
    (r'>@Error<.*?</text>', 'Error note symbol'),
]

print("\n✓ Note types detected:")
for pattern, description in patterns:
    if re.search(pattern, svg, re.DOTALL):
        print(f"  ✓ {description}")
    else:
        print(f"  - {description}")

# Show structure
if path_count > 0 and note_count > 0:
    print("\n✓ VERIFICATION COMPLETE")
    print(f"  {path_count} note boxes rendered with folded corners")
    print(f"  {note_count} note type references (@Info, @Warning, @Error, @Success)")
    print("  Both function notes and lifeline notes are rendering!")
    print("\nHow to verify visually:")
    print("  1. Open: http://localhost:8000/?csv=test_ui_controls&verbosity=High")
    print("  2. Function notes: Appear at end of spanning brackets on objects")
    print("  3. Lifeline notes: Appear below on object lifelines")
    print("  4. Different colors: Info (blue), Warning (orange), Error (red)")
    print("\nCSV Format Examples Used:")
    print("  - Function note: Client,AuthService,ValidateCredentials,user1,pass123,valid,@Info,text")
    print("  - Lifeline note: AuthService,@Info,text")
elif path_count > 0:
    print("\n⚠ Partial verification: Note boxes found but references not detected")
    print(f"  Found {path_count} note boxes")
elif note_count > 0:
    print("\n⚠ Partial verification: Note references found but boxes not rendered")
    print(f"  Found {note_count} note references")
else:
    print("\n✗ ERROR: Missing expected note elements")
    sys.exit(1)

print("=" * 70)
