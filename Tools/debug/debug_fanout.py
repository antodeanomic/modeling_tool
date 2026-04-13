#!/usr/bin/env python3
import sys
sys.path.insert(0, 'Scripts')

from parser import parse_csv
from model import ClassDiagramDef
from class_diagram_renderer import _layout_classes_uml_standard, _optimize_layout_for_grid_collisions
from class_diagram_connectors import FORCED_EDGE_OVERRIDES

csv_path = 'Test/tests/test_multiconnector_rightangle.csv'
model = parse_csv(csv_path)
diagram = model.class_diagrams[0]
boxes = _layout_classes_uml_standard(diagram, model, 'High', routing='orthogonal')
_boxes, planner, _hc, _det = _optimize_layout_for_grid_collisions(diagram, boxes, 'orthogonal', 'High', None)

print('=== DEBUGGING FANOUT ===\n')

# Re-run pre-compute
hierarchy_order = planner._ordered_hierarchy_connectors()
assignments = planner._precompute_fanout_assignments(hierarchy_order)

print(f'Fanout assignments: {len(assignments)} connectors have fan-out routing')
for conn_id, assign in assignments.items():
    for c in planner.connectors:
        if id(c) == conn_id:
            print(f'  {c.source_name}->{c.target_name}: exit={assign["exit_edge"]} bend={assign["bend"]:.0f}')
            break

print()
print('=== GROUPS BY EDGE ===')
group_map = {}
for connector in planner.connectors:
    src_g = planner.grids.get(connector.source_name)
    tgt_g = planner.grids.get(connector.target_name)
    if id(connector) in hierarchy_order:
        exit_edge = 'bottom'
    else:
        forced = FORCED_EDGE_OVERRIDES.get((connector.source_name, connector.target_name))
        exit_edge = forced[0] if forced else planner._select_exit_edge(src_g, tgt_g)
    group_map.setdefault((connector.source_name, exit_edge), []).append(connector)

for (src, edge), group in sorted(group_map.items()):
    print(f'{src} via {edge:6s}: {len(group)} connectors')
    if len(group) >= 2:
        print(f'  -> Eligible for fan-out')
        # Check entry edges
        for conn in group:
            tgt_g = planner.grids[conn.target_name]
            forced = FORCED_EDGE_OVERRIDES.get((conn.source_name, conn.target_name))
            entry_edge = forced[1] if forced else planner._select_entry_edge(planner.grids[conn.source_name], tgt_g, edge)
            compatible = {
                'bottom': 'top', 'top': 'bottom',
                'right': 'left', 'left': 'right',
            }.get(edge)
            is_compatible = entry_edge == compatible
            print(f'    {conn.target_name}: entry={entry_edge} compatible={is_compatible}')

print()
print('=== ACTUAL ROUTED PATHS ===')
for c in sorted(planner.connectors, key=lambda x: x.target_name):
    in_fanout = id(c) in assignments
    pts = [(c.source_x, c.source_y)] + list(c.segments) + [(c.target_x, c.target_y)]
    print(f'{c.target_name:10s}: fanout={str(in_fanout):5s} edge={c.source_edge:6s} segs={len(c.segments):2d}')
