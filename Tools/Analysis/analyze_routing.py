#!/usr/bin/env python3
"""Check box positions to understand routing."""

import sys
sys.path.insert(0, 'Scripts')

from parser import parse_csv
from class_diagram_renderer import _calculate_box_positions

csv_path = 'Process/02_Architecture/class_diagrams.csv'
model = parse_csv(csv_path)
diagram = [d for d in model.class_diagrams if d.diagram_id == 'DataModelRelationships'][0]

boxes = _calculate_box_positions(diagram.get_element_names())

print("Box Positions for DataModelRelationships:")
print("=" * 80)
print(f"{'Element':<25} {'X':<10} {'Y':<10} {'Width':<10} {'Height':<10}")
print("-" * 80)

for name, box in sorted(boxes.items()):
    print(f"{name:<25} {box['x']:<10.1f} {box['y']:<10.1f} {box['width']:<10.1f} {box['height']:<10.1f}")

# Now check relationships to understand routing
print("\n" + "=" * 80)
print("\nRelationships and relative positions:")
print("=" * 80)
print(f"{'Source':<20} {'Target':<20} {'Relative Position':<30}")
print("-" * 80)

for rel in diagram.relationships:
    src_box = boxes[rel.source]
    tgt_box = boxes[rel.target]
    
    src_cx = src_box['x'] + src_box['width'] / 2
    src_cy = src_box['y'] + src_box['height'] / 2
    tgt_cx = tgt_box['x'] + tgt_box['width'] / 2
    tgt_cy = tgt_box['y'] + tgt_box['height'] / 2
    
    dx = tgt_cx - src_cx
    dy = tgt_cy - src_cy
    
    if abs(dx) > abs(dy):
        if dx > 0:
            direction = "RIGHT"
            src_exit = 'right'
            tgt_entry = 'left'
        else:
            direction = "LEFT"
            src_exit = 'left'
            tgt_entry = 'right'
    else:
        if dy > 0:
            direction = "DOWN"
            src_exit = 'bottom'
            tgt_entry = 'top'
        else:
            direction = "UP"
            src_exit = 'top'
            tgt_entry = 'bottom'
    
    # Determine path type
    src_is_horiz = src_exit in ['top', 'bottom']
    tgt_is_horiz = tgt_entry in ['top', 'bottom']
    path_type = "DIRECT" if src_is_horiz != tgt_is_horiz else "MULTI"
    
    print(f"{rel.source:<20} {rel.target:<20} {direction:<8} ({src_exit:>6}→{tgt_entry:<6}) {path_type}")

with open('routing_analysis.txt', 'w') as f:
    f.write("Routing Analysis\n")
    for rel in diagram.relationships:
        src_box = boxes[rel.source]
        tgt_box = boxes[rel.target]
        src_cx = src_box['x'] + src_box['width'] / 2
        src_cy = src_box['y'] + src_box['height'] / 2
        tgt_cx = tgt_box['x'] + tgt_box['width'] / 2
        tgt_cy = tgt_box['y'] + tgt_box['height'] / 2
        dx = tgt_cx - src_cx
        dy = tgt_cy - src_cy
        
        if abs(dx) > abs(dy):
            if dx > 0:
                direction = "RIGHT"
                src_exit = 'right'
                tgt_entry = 'left'
            else:
                direction = "LEFT"
                src_exit = 'left'
                tgt_entry = 'right'
        else:
            if dy > 0:
                direction = "DOWN"
                src_exit = 'bottom'
                tgt_entry = 'top'
            else:
                direction = "UP"
                src_exit = 'top'
                tgt_entry = 'bottom'
        
        src_is_horiz = src_exit in ['top', 'bottom']
        tgt_is_horiz = tgt_entry in ['top', 'bottom']
        path_type = "DIRECT" if src_is_horiz != tgt_is_horiz else "MULTI"
        
        f.write(f"{rel.source:<20} {rel.target:<20} {path_type}\n")

print("\nAnalysis written to routing_analysis.txt")
