#!/usr/bin/env python3
"""Minimal test to regenerate note ordering diagram."""
import sys
sys.path.insert(0, 'Scripts')

output = []

try:
    output.append("Starting script...")
    from parser import parse_csv
    from svg_renderer import render_diagram
    
    output.append("Parsing test_note_ordering.csv...")
    model = parse_csv('Test/tests/test_note_ordering.csv')
    output.append(f"  Found {len(model.sequences)} sequence(s)")
    
    output.append("Rendering diagram with High verbosity...")
    result = render_diagram(model, 'Test/tests/test_note_ordering.csv', 'High')
    output.append(f"  Rendered SVG, length: {len(result)} bytes")
    
    # Extract Y positions from the SVG
    import re
    
    # Extract Msg2 Y coordinate
    msg2_match = re.search(r'<rect x="419\.0" y="(\d+)"', result)
    if msg2_match:
        msg2_y = int(msg2_match.group(1))
        output.append(f"  Msg2 bracket Y position: {msg2_y}")
    else:
        output.append("  Could not find Msg2 bracket")
    
    # Write SVG to file
    output_path = 'Test/tests/test_note_ordering_NoteOrderTest_High_NEW.svg'
    with open(output_path, 'w') as f:
        f.write(result)
    output.append(f"SVG saved to: {output_path}")
    
    # Get render version from SVG
    version_match = re.search(r'data-render-version="([^"]+)"', result)
    if version_match:
        output.append(f"Render version: {version_match.group(1)}")
    
    output.append("Script completed successfully!")
    
except Exception as e:
    output.append(f"ERROR: {type(e).__name__}: {e}")
    import traceback
    output.append(traceback.format_exc())

# Write output to file
with open('test_note_order_output.txt', 'w') as f:
    f.write('\n'.join(output))

# Also print
print('\n'.join(output))


