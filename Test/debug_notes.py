#!/usr/bin/env python3
import sys
sys.path.insert(0, '../Scripts')
from parser import parse_csv
from svg_renderer import render_svg

model = parse_csv('tests/test_notes.csv')
seq = model.get_sequence('SoftReq_TEST_001')

print('=== Step Analysis ===')
for i, step in enumerate(seq.steps):
    print(f'Step {i}: {step.src_obj} -> {step.dst_obj} ({step.function})')
    
    if hasattr(step, 'function_note') and step.function_note:
        print(f'  Function note: {step.function_note.note_type}')
    
    if hasattr(step, 'lane_notes') and step.lane_notes:
        print(f'  Lane notes: {list(step.lane_notes.keys())}')
        for lane, note in step.lane_notes.items():
            print(f'    - {lane}: {note.note_type}')

print('\n=== Rendering SVG ===')
svg = render_svg(model, seq, verbosity_level='High')

# Check for colored boxes
has_info = 'fill="#E3F2FD"' in svg
has_warning = 'fill="#FFF3E0"' in svg  
has_error = 'fill="#FFEBEE"' in svg
has_success = 'fill="#E8F5E9"' in svg

print(f'Info boxes (blue):     {has_info}')
print(f'Warning boxes (orange): {has_warning}')
print(f'Error boxes (red):     {has_error}')
print(f'Success boxes (green):  {has_success}')

total_colored = (has_info or 0) + (has_warning or 0) + (has_error or 0) + (has_success or 0)
print(f'\nTotal colored box types: {total_colored}')

# Look for path elements (note boxes use <path>)
path_count = svg.count('<path')
print(f'Total <path> elements: {path_count}')
