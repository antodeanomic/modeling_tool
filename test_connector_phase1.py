"""Test the connector system Phase 1: Grid-based connection points."""

import sys
sys.path.insert(0, 'Scripts')

from class_diagram_connectors import ConnectorPlanner


def test_basic_grid():
    """Test basic grid creation and connection point calculation."""
    planner = ConnectorPlanner()
    
    # Add some rectangles matching the actual diagram
    planner.add_rectangle('Model', x=40, y=70, width=179.2, height=187)
    planner.add_rectangle('ClassDef', x=309.2, y=70, width=143.2, height=137)
    planner.add_rectangle('FunctionDef', x=40, y=322, width=121.6, height=137)
    planner.add_rectangle('ReturnDef', x=40, y=524, width=121.6, height=83)
    planner.add_rectangle('ParamDef', x=698.2, y=322, width=121.6, height=83)
    
    print("=" * 70)
    print("PHASE 1: Grid-Based Connection Points Test")
    print("=" * 70)
    
    # Check grid points
    print("\nModel rectangle connection points:")
    for edge in ['top', 'bottom', 'left', 'right']:
        points = planner.grids['Model'].get_points(edge)
        coords = [(p.index, f"({p.x:.1f}, {p.y:.1f})") for p in points]
        print(f"  {edge:6}: {len(points)} points - {coords[:3]}{'...' if len(coords) > 3 else ''}")
    
    print("\nFunctionDef rectangle connection points:")
    for edge in ['top', 'bottom', 'left', 'right']:
        points = planner.grids['FunctionDef'].get_points(edge)
        coords = [(p.index, f"({p.x:.1f}, {p.y:.1f})") for p in points]
        print(f"  {edge:6}: {len(points)} points - {coords[:3]}{'...' if len(coords) > 3 else ''}")
    
    # Add connectors
    print("\n" + "=" * 70)
    print("Adding connectors:")
    print("=" * 70)
    
    connectors_to_add = [
        ('Model', 'ClassDef', '◇--', '1', '0.*', 'contains', ''),
        ('ClassDef', 'FunctionDef', '◆--', '1', '0.*', 'owns', ''),
        ('FunctionDef', 'ParamDef', '◆--', '1', '0.*', 'owns', ''),
        ('FunctionDef', 'ReturnDef', '◆--', '1', '0.*', 'owns', ''),
    ]
    
    for src, tgt, arrow, src_m, tgt_m, lbl, layer in connectors_to_add:
        planner.add_connector(src, tgt, arrow, src_m, tgt_m, lbl, layer)
        print(f"  {src:15} -> {tgt:15} ({arrow})")
    
    # Plan connectors
    print("\n" + "=" * 70)
    print("Planning connectors:")
    print("=" * 70)
    
    planner.plan_connectors()
    
    for i, connector in enumerate(planner.get_connectors(), 1):
        print(f"\n[{i}] {connector.source_name} -> {connector.target_name}")
        print(f"    Distance: {connector.calculate_distance():.1f}")
        print(f"    Source:   {connector.source_edge:6} point {connector.source_point_idx} @ ({connector.source_x:.1f}, {connector.source_y:.1f})")
        print(f"    Target:   {connector.target_edge:6} point {connector.target_point_idx} @ ({connector.target_x:.1f}, {connector.target_y:.1f})")
        print(f"    Path type: {connector.path_type}")
        if connector.path_type == "multi_segment" and connector.segments:
            print(f"    Segments: {len(connector.segments)} waypoints")
            for j, (x, y) in enumerate(connector.segments[:3], 1):
                print(f"      [{j}] ({x:.1f}, {y:.1f})")
    
    print("\n" + "=" * 70)
    print("✓ Phase 1 test complete!")
    print("=" * 70)


if __name__ == '__main__':
    test_basic_grid()
