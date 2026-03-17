#!/usr/bin/env python3
"""Check spacing calculation values."""

import sys
sys.path.insert(0, 'Scripts')
from parser import parse_csv
from class_diagram_renderer import _calculate_required_spacing, CLASS_SPACING_X

model = parse_csv('Process/02_Architecture/class_diagrams.csv')
diagram = model.class_diagrams[0]  # DataModelRelationships

# Check spacing calculation
required = _calculate_required_spacing(diagram, 'High')
print(f'Required spacing: {required}px')
print(f'CLASS_SPACING_X: {CLASS_SPACING_X}px')
print(f'Recommended for High verbosity: {CLASS_SPACING_X + 30}px')

# Show each relationship's connector text width
print(f'\nConnector text requirements:')
for i, rel in enumerate(diagram.relationships[:5]):
    # Estimate width
    arrow_width = 20  # 2 * 10px
    src_mult_width = len(rel.src_mult) * 7.5 if rel.src_mult else 30
    label_width = len(rel.label) * 7.5 if rel.label else 0
    tgt_mult_width = len(rel.tgt_mult) * 7.5 if rel.tgt_mult else 30
    gap_width = 2 * 2 * 7.5  # 2 spaces * 2 gaps
    
    total = arrow_width + src_mult_width + label_width + tgt_mult_width + gap_width
    print(f'  Rel {i}: {rel.source}->{rel.target}')
    print(f'    mult: {rel.src_mult}:{rel.tgt_mult}, label: "{rel.label}"')
    print(f'    arrows={arrow_width:.0f}, src_mult={src_mult_width:.0f}, label={label_width:.0f}, tgt_mult={tgt_mult_width:.0f}, gaps={gap_width:.0f}')
    print(f'    TOTAL: {total:.0f}px')
