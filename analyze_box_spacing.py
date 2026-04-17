#!/usr/bin/env python3
"""
Compare actual spacing (in pixels) between class boxes in minimal vs dense diagrams.
This helps identify if objects are positioned too close together.
"""
import sys
import os
import math

# Add Scripts directory to path
script_dir = os.path.join(os.path.dirname(__file__), 'Scripts')
sys.path.insert(0, script_dir)

from parser import parse_csv
from class_diagram_renderer import _collect_and_size_classes, _layout_classes_uml_standard, _layout_classes_orthogonal
from pathlib import Path

def measure_spacing(diagram_name, csv_file):
    """Compute layout and measure pixel spacing between objects."""
    
    model = parse_csv(csv_file)
    diagram = None
    for d in model.class_diagrams:
        if d.diagram_id == diagram_name:
            diagram = d
            break
    
    if not diagram:
        print(f"  Diagram not found: {diagram_name}")
        return
    
    # Compute layout using orthogonal routing
    positions = _layout_classes_orthogonal(diagram, model, verbosity="High")
    
    if not positions:
        print(f"  No positions returned")
        return
    
    print(f"\nDiagram: {diagram_name}")
    print(f"Classes: {len(positions)}")
    
    # Sort by (y, x) to identify nearby boxes
    sorted_pos = sorted(positions.items(), key=lambda p: (p[1]['y'], p[1]['x']))
    
    # Calculate distances between consecutive boxes
    print("\nBox positions (sorted top-to-bottom, left-to-right):")
    print("  Class Name          | X       | Y       | Width | Height")
    print("  " + "-" * 57)
    for name, pos in sorted_pos:
        print(f"  {name:18s} | {pos['x']:6.0f} | {pos['y']:6.0f} | {pos['width']:5.0f} | {pos['height']:6.0f}")
    
    # Calculate minimum distances
    print("\nClosest pairs (measured edge-to-edge in pixels):")
    min_distances = []
    
    box_list = list(positions.items())
    for i, (name1, box1) in enumerate(box_list):
        for name2, box2 in box_list[i+1:]:
            # Calculate edge-to-edge distance
            # Horizontal distance
            if box1['x'] + box1['width'] <= box2['x']:
                h_dist = box2['x'] - (box1['x'] + box1['width'])
            elif box2['x'] + box2['width'] <= box1['x']:
                h_dist = box1['x'] - (box2['x'] + box2['width'])
            else:
                h_dist = 0  # Overlapping or same region
            
            # Vertical distance
            if box1['y'] + box1['height'] <= box2['y']:
                v_dist = box2['y'] - (box1['y'] + box1['height'])
            elif box2['y'] + box2['height'] <= box1['y']:
                v_dist = box1['y'] - (box2['y'] + box2['height'])
            else:
                v_dist = 0  # Overlapping or same region
            
            # Use minimum as the "closest" distance
            min_dist = min(h_dist, v_dist) if h_dist and v_dist else max(h_dist, v_dist)
            min_distances.append((min_dist, name1, name2))
    
    min_distances.sort()
    for dist, n1, n2 in min_distances[:5]:
        print(f"  {n1:18s} <-> {n2:18s}: {dist:6.1f}px")
    
    # Summary statistics
    all_dists = [d[0] for d in min_distances if d[0] > 0]
    if all_dists:
        print(f"\nSpacing statistics:")
        print(f"  Minimum edge-to-edge: {min(all_dists):.1f}px")
        print(f"  Average edge-to-edge: {sum(all_dists) / len(all_dists):.1f}px")
    
    return positions

# Run diagnostics
print("=" * 70)
print("CLASS DIAGRAM SPACING ANALYSIS")
print("=" * 70)

# Test minimal case
minimal_csv = Path("Test/tests/test_spacing_minimal.csv")
if minimal_csv.exists():
    measure_spacing("SimpleFourBox", str(minimal_csv))
else:
    print(f"Minimal test file not found: {minimal_csv}")

# Test dense case
print("\n" + "=" * 70)
dense_csv = Path("Process/01_System/40_Tests/20_Advanced/test_class_diagram_orthogonal_stress.csv")
if dense_csv.exists():
    measure_spacing("OrthogonalStressDense", str(dense_csv))
else:
    print(f"Dense test file not found: {dense_csv}")

print("\n" + "=" * 70)
print("SPACING COMPARISON COMPLETE")
print("=" * 70)
