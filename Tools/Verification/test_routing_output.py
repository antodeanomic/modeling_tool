#!/usr/bin/env python3
import sys
import os

# Add Scripts directory to path FIRST, before any imports
scripts_dir = os.path.join(os.path.dirname(__file__), 'Scripts')
sys.path.insert(0, scripts_dir)

from parser import parse_csv
from class_diagram_renderer import render_class_diagram_svg

# Load the model from the class diagrams CSV
model = parse_csv('Process/02_Architecture/class_diagrams.csv')

# Find DataModelRelationships
for cd in model.class_diagrams:
    if cd.diagram_id == 'DataModelRelationships':
        svg = render_class_diagram_svg(model, cd, 'High')
        
        # Count line vs path elements
        lines = svg.count('<line ')
        paths = svg.count('<path d="M')
        
        print(f"Direct line connectors: {lines}")
        print(f"Multi-segment path connectors: {paths}")
        print(f"Total connectors: ~{lines + paths}")
        break
