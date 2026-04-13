#!/usr/bin/env python3
import sys
sys.path.insert(0, 'Scripts')

from parser import parse_csv
from class_diagram_renderer import _layout_classes_uml_standard, _optimize_layout_for_grid_collisions
from class_diagram_connectors import FORCED_EDGE_OVERRIDES

csv_path = 'Test/tests/test_multiconnector_rightangle.csv'
model = parse_csv(csv_path)
diagram = model.class_diagrams[0]
boxes = _layout_classes_uml_standard(diagram, model, 'High', routing='orthogonal')
_boxes, planner, _hc, _det = _optimize_layout_for_grid_collisions(diagram, boxes, 'orthogonal', 'High', None)

print('=== ALL 11 CONNECTIONS ===\n')
for c in sorted(planner.connectors, key=lambda x: x.target_name):
    src_g = planner.grids[c.source_name]
    tgt_g = planner.grids[c.target_name]
    exit_edge = planner._select_exit_edge(src_g, tgt_g)
    entry_edge = planner._select_entry_edge(src_g, tgt_g, exit_edge)
    print(f'{c.target_name:10s}: exit={exit_edge:6s} entry={entry_edge:6s}')
