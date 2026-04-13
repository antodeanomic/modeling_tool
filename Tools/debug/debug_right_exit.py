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

print('=== RIGHT EXIT GROUP DETAILS ===\n')

hierarchy_order = planner._ordered_hierarchy_connectors()
assignments = planner._precompute_fanout_assignments(hierarchy_order)

# Get all right-exit connectors
right_exit = [c for c in planner.connectors if planner._select_exit_edge(planner.grids[c.source_name], planner.grids[c.target_name]) == 'right']
print(f'Right exit connectors: {len(right_exit)}')
for c in sorted(right_exit, key=lambda x: x.target_name):
    print(f'  {c.target_name}')

print()

# Check which got fanout assignments
fanout_right = [c for c in right_exit if id(c) in assignments]
print(f'Fan-out assigned in right group: {len(fanout_right)}')
for c in fanout_right:
    fa = assignments[id(c)]
    print(f'  {c.target_name}: bend={fa["bend"]:.0f}')
