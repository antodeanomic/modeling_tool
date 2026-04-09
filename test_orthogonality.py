#!/usr/bin/env python3
"""
Test orthogonality of connector paths.

Validates that all connector segments maintain 90-degree angles (orthogonal routing).
A path is orthogonal if each segment is either purely horizontal or purely vertical.
"""

import sys
sys.path.insert(0, r'c:\Users\antod\OneDrive\Documents\repo\modeling_tool\Scripts')

from parser import parse_csv
from class_diagram_connectors import ConnectorPlanner


def is_orthogonal_segment(p1, p2):
    """Check if a single segment between two points is orthogonal (horizontal or vertical)."""
    x1, y1 = p1
    x2, y2 = p2
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    
    # Orthogonal means either dx=0 (vertical) or dy=0 (horizontal), not both non-zero
    is_ortho = (dx < 0.01 or dy < 0.01)
    return is_ortho, dx, dy


def is_orthogonal_path(segments):
    """Check if an entire path is fully orthogonal."""
    if len(segments) < 2:
        return True, []
    
    failures = []
    for i in range(len(segments) - 1):
        is_ortho, dx, dy = is_orthogonal_segment(segments[i], segments[i+1])
        if not is_ortho:
            failures.append({
                'segment_idx': i,
                'from': segments[i],
                'to': segments[i+1],
                'dx': dx,
                'dy': dy
            })
    
    return len(failures) == 0, failures


def test_orthogonality():
    """Test that all connectors in the test diagram have orthogonal routing."""
    
    # Load the test diagram
    model = parse_csv(r'c:\Users\antod\OneDrive\Documents\repo\modeling_tool\Process\01_System\40_Tests\20_Advanced\test_class_diagram_all_connector_combinations.csv')
    
    # Get the diagram with AR probe pairs
    diagram2 = model.class_diagrams[1]  # OrthogonalArrowTypeAndRoutes
    
    # Create planner
    planner = ConnectorPlanner(routing_mode='orthogonal')
    
    # Add test rectangles
    elements = diagram2.get_element_names()
    for elem in elements:
        idx = elements.index(elem)
        x = (idx % 5) * 250
        y = (idx // 5) * 250
        planner.add_rectangle(elem, x, y, 100, 100)
    
    # Add connectors
    for rel in diagram2.relationships:
        planner.add_connector(rel.source, rel.target, rel.arrow,
                             rel.src_mult or "", rel.tgt_mult or "", 
                             rel.label or "", rel.layer or "")
    
    # Plan routing
    planner.plan_connectors()
    
    # Validate orthogonality
    failed_connectors = []
    passed_connectors = []
    
    for conn in planner.connectors:
        is_ortho, failures = is_orthogonal_path(conn.segments)
        
        if is_ortho:
            passed_connectors.append({
                'source': conn.source_name,
                'target': conn.target_name,
                'source_edge': conn.source_edge,
                'target_edge': conn.target_edge,
                'segments': len(conn.segments),
                'path': conn.segments
            })
        else:
            failed_connectors.append({
                'source': conn.source_name,
                'target': conn.target_name,
                'source_edge': conn.source_edge,
                'target_edge': conn.target_edge,
                'segments': len(conn.segments),
                'path': conn.segments,
                'failures': failures
            })
    
    # Report results
    print("=" * 80)
    print("ORTHOGONALITY TEST RESULTS")
    print("=" * 80)
    
    if failed_connectors:
        print(f"\nFAILED: {len(failed_connectors)} connector(s) have non-orthogonal paths\n")
        for conn in failed_connectors:
            print(f"  {conn['source']} -> {conn['target']}")
            print(f"    Edges: {conn['source_edge']} -> {conn['target_edge']}")
            print(f"    Segments: {conn['segments']}")
            print(f"    Path:")
            for i, pt in enumerate(conn['path']):
                print(f"      [{i}] {pt}")
            print(f"    Failures:")
            for fail in conn['failures']:
                print(f"      Segment [{fail['segment_idx']}] -> [{fail['segment_idx']+1}]:")
                print(f"        {fail['from']} -> {fail['to']}")
                print(f"        dx={fail['dx']:.1f}, dy={fail['dy']:.1f} (both non-zero = DIAGONAL)")
            print()
    else:
        print(f"\nPASSED: All {len(planner.connectors)} connectors are fully orthogonal\n")
        for conn in passed_connectors:
            print(f"  [OK] {conn['source']:8} -> {conn['target']:8} | {conn['source_edge']:6} -> {conn['target_edge']:6} | {conn['segments']:2} segments")
    
    print("=" * 80)
    
    return len(failed_connectors) == 0


if __name__ == '__main__':
    success = test_orthogonality()
    sys.exit(0 if success else 1)
