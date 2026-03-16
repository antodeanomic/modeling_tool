# Class Diagram Connector Architecture

## Overview

A grid-based connector system for class diagrams that ensures clean, collision-free relationships between elements. The system works in phases:

1. **Phase 1**: Grid-based connection points + distance calculation
2. **Phase 2**: Multi-segment routing (DOWN → RIGHT → UP → RIGHT)
3. **Phase 3**: Collision detection & staggering

## Connection Grid System

### Simplified Connection Points

Each rectangle has connection points on four edges using a simple notation:

```
        Top: 1, 2, 3, 4, 5, 6, 7
        
Left:1                    Right:1
Left:2                    Right:2
Left:3                    Right:3
...
        
        Bottom: 1, 2, 3, 4, 5, 6, 7
```

**Grid Point Calculation:**
- Grid points are spaced evenly around the perimeter
- Number of points scales with rectangle size
- Points are indexed consistently starting from left/top

### Edge Selection

For a given source→target pair:
1. **Primary edge**: Choose based on target direction (right if target.x > source.x, etc.)
2. **Multi-segment routing**: If not on primary edge, use DOWN→RIGHT→UP→RIGHT pattern
3. **Consecutive points**: Assign points sequentially (1, 2, 3, ...) as connectors are added

## Connector Planning Algorithm

### Step 1: Identify All Connections
- Collect all relationships from diagram
- Filter by requested verbosity/layers

### Step 2: Calculate Ideal Paths
- For each connector: calculate distance from source connection point to target connection point
- Consider Manhattan distance for multi-segment paths

### Step 3: Sort by Distance
- Sort all connectors by their ideal path distance (shortest first)

### Step 4: Assign Grid Points
- For each connector (in distance order):
  1. Determine source box exit edge (right/left/down/up based on target direction)
  2. Determine target box entry edge (opposite of exit edge)
  3. Assign consecutive grid points from available pool
  4. Mark as "all layers + high verbosity" for later filtering

### Step 5: Store Connector Data
- Store connector paths in renderer for reuse across different verbosity/layer views
- Filter stored connectors when needed

## Data Structures

### ConnectionGrid
```
{
  'source': str,           # Class name
  'target': str,
  'source_edge': str,      # 'top', 'bottom', 'left', 'right'
  'source_point': int,     # 1-7 depending on edge
  'target_edge': str,
  'target_point': int,
  'path_type': str,        # 'direct', 'multi_segment'
  'segments': [...],       # List of (x, y) coordinates for multi-segment paths
  'arrow': str,            # Arrow type from relationship
  'layer': str,            # Layer filter
}
```

## Multi-Segment Routing

When source and target are not aligned on primary edge:

1. **Exit segment**: Vertical from source connection point
2. **Horizontal segment**: Horizontal to target x-coordinate
3. **Approach segment**: Vertical to target y-coordinate
4. **Entry segment**: Horizontal into target connection point

Pattern ensures:
- Starts vertical (away from source)
- Ends horizontal (into target)
- Minimizes crossings with other connectors

## Layer & Verbosity Handling

- **Calculate once**: Plan all connectors for full diagram (all layers, high verbosity)
- **Filter on render**: Remove connectors based on current layer/verbosity filters
- **No recalculation**: Connection points remain stable across views

## Implementation Files

- `Scripts/class_diagram_connectors.py`: Core connector logic
- `Scripts/class_diagram_renderer.py`: Updated to use connector system
