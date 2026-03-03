#!/usr/bin/env python3
import sys
sys.path.insert(0, '/c/Users/antod/OneDrive/Documents/repo/modeling_tool/Scripts')

from parser import parse_csv
from svg_renderer import render_svg

try:
    print("Loading CSV...")
    model = parse_csv('Scripts/parser.py')
    model = parse_csv('Test/tests/test_code_syntax.csv')
    print("CSV loaded successfully")
    
    print("Getting sequence...")
    seq = model.get_sequence('CodeSyntax_TEST')
    print(f"Sequence: {seq}")
    
    if seq:
        print("Rendering SVG...")
        svg = render_svg(model, seq, 'Normal')
        print(f"Success! SVG length: {len(svg)}")
        
        # Write to file for inspection
        with open('test_code_syntax_output.svg', 'w') as f:
            f.write(svg)
        print("Wrote to test_code_syntax_output.svg")
    else:
        print("Sequence not found")
except Exception as e:
    import traceback
    print(f"ERROR: {e}")
    traceback.print_exc()
