#!/usr/bin/env python3
import sys
sys.path.insert(0, 'Scripts')

from parser import parse_csv
from class_diagram_renderer import _layout_classes_uml_standard, _optimize_layout_for_grid_collisions

csv_path = 'Test/tests/test_multiconnector_rightangle.csv'
model = parse_csv(csv_path)
diagram = model.class_diagrams[0]
boxes = _layout_classes_uml_standard(diagram, model, 'High', routing='orthogonal')
_boxes, planner, _hc, _det = _optimize_layout_for_grid_collisions(diagram, boxes, 'orthogonal', 'High', None)

hierarchy_order = planner._ordered_hierarchy_connectors()
assignments = planner._precompute_fanout_assignments(hierarchy_order)

print('=== FANOUT SEGMENTS ===\n')
for c in sorted(planner.connectors, key=lambda x: x.target_name):
    if id(c) in assignments:
        pts = [(c.source_x, c.source_y)] + list(c.segments) + [(c.target_x, c.target_y)]
        print(f'{c.target_name}:')
        print(f'  source: ({c.source_x:.0f}, {c.source_y:.0f}) edge={c.source_edge}')
        print(f'  target: ({c.target_x:.0f}, {c.target_y:.0f}) edge={c.target_edge}')
        print(f'  segments list: {c.segments}')
        print(f'  full path:')
        for i, (x, y) in enumerate(pts):
            print(f'    pt{i}: ({x:.0f}, {y:.0f})')
        fa = assignments[id(c)]
        print(f'  fanout bend={fa["bend"]:.0f}')
        print()
