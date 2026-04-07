# Class Diagram Connector Architecture

## Overview

A grid-based connector system for class diagrams that ensures clean, collision-aware relationships between elements.

Current production behavior focuses on readable orthogonal routing with interaction support in the viewer.

## Current Architecture (2026-04)

1. Route class-diagram connectors using orthogonal geometry only.
2. Plan connectors in deterministic order with domain-layer prioritization.
3. Avoid obstacle overlap first, then reduce connector-track overlap.
4. Apply domain-focused vertical spacing to unlock additional orthogonal tracks.
5. Expose connector/object metadata in SVG for interactive highlighting.

### Routing Policy

- Class-diagram routing mode is normalized to orthogonal in planner/server flow.
- Diagonal fallback is not used for class-diagram connector paths.
- Preferred path order for orthogonal routing:
  - direct horizontal/vertical when aligned
  - simple elbow when valid
  - constrained multi-segment search as fallback

### Domain Layer Readability Strategy

- Dense domain fan-out introduces higher overlap pressure than other layers.
- Layout uses a larger initial vertical row gap when domain relationships are present.
- Connector text placement uses occupancy-aware row nudging for domain labels.
- The combination reduces severe connector and text stacking while preserving deterministic output.

### SVG Metadata for Interaction

- Each class object renders as an SVG group:
  - `g.cls-object[data-class-name="..."]`
- Each connector renders as an SVG group:
  - `g.cls-connector[data-connector-id="..."][data-source="..."][data-target="..."]`
- Viewer hover logic uses these attributes to highlight related connectors/text and fade unrelated links.

## Legacy Notes

The original phase-based description below remains as historical context:

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
