# Connector Obstacle Avoidance Strategy

## Overview

The connector router should detect when a proposed connection path passes through (underneath) object boxes and automatically find alternative paths that avoid those obstacles.

## Problem Statement

**Current Behavior**: Connectors sometimes pass underneath object boxes even when alternative paths exist that don't overlap.

**Example**:
```
┌─────────┐
│ ClassA  │
└────┬────┘ 
     │ (connection path goes DOWN through ClassB)
     │
┌─────────┐
│ ClassB  │ (connector line renders UNDER this box)
└────┬────┘
     │
┌─────────┐
│ ClassC  │
└─────────┘
```

## Solution: Obstacle-Aware Routing

### Overview
The routing system uses a **preference cascade** approach:
1. Try simplest path (direct)
2. If blocked, try 2-segment
3. If still blocked, try 3-segment (V-H-V)
4. If still blocked, use advanced alternatives (N-segment)

This ensures diagrams are as readable as possible with minimal connector bends.

---

**Algorithm**:
1. Calculate the proposed connector path (direct line or 2-segment path)
2. Sample the path at regular intervals (e.g., every 16px = 1 grid cell)
3. For each sample point, check if any object box occupies that grid cell
4. Record all obstacles encountered

**Implementation**:
```python
def detect_obstacles_on_path(path_points, grids):
    """
    Detect objects that intersect with proposed connector path.
    
    Args:
        path_points: List of (x, y) coordinates defining the connector path
        grids: Dict of all object boxes {name: RectangleGrid}
    
    Returns:
        List of (grid_name, grid_cell, path_point) tuples for obstacles
    """
    obstacles = []
    grid_system = GridCoordinateSystem()
    
    # Sample every GRID_BLOCK_WIDTH=16px along the path
    SAMPLE_INTERVAL = 16
    
    for i in range(len(path_points) - 1):
        x1, y1 = path_points[i]
        x2, y2 = path_points[i + 1]
        
        # Calculate segment length
        dx = x2 - x1
        dy = y2 - y1
        segment_len = (dx**2 + dy**2) ** 0.5
        
        # Sample points along this segment
        if segment_len > 0:
            samples = int(segment_len / SAMPLE_INTERVAL) + 1
            for sample_idx in range(samples):
                t = sample_idx / max(samples - 1, 1)
                sample_x = x1 + dx * t
                sample_y = y1 + dy * t
                
                # Get grid cell at this point
                grid_x, grid_y = grid_system.svg_to_grid(sample_x, sample_y)
                
                # Check which object boxes occupy this cell
                for obj_name, obj_grid in grids.items():
                    # Skip source and target boxes (connectors must touch them)
                    if obj_name in [connector.source_name, connector.target_name]:
                        continue
                    
                    # Check if object occupies this grid cell
                    if (obj_grid.x <= sample_x <= obj_grid.x + obj_grid.width and
                        obj_grid.y <= sample_y <= obj_grid.y + obj_grid.height):
                        
                        obstacles.append({
                            'object': obj_name,
                            'grid_cell': (grid_x, grid_y),
                            'path_point': (sample_x, sample_y),
                            'segment_idx': i
                        })
    
    return obstacles
```

### Phase 2: Find Alternative Path

When obstacles are detected, try alternative routing strategies in order:

**Strategy 1: 2-Segment Path (if currently using direct line)**
- Exit source perpendicular to direct line
- Bend 90 degrees at midpoint
- Enter target perpendicular to direct line
- Check for obstacles on new path

**Strategy 2: Route Around Obstacle**
- Calculate bounding box of all obstacles
- Route path around the obstacle:
  - Try routing LEFT of obstacle (horizontal offset -100px)
  - Try routing RIGHT of obstacle (horizontal offset +100px)
  - Try routing ABOVE obstacle (vertical offset -100px)
- Select first path with minimal obstacles

**Strategy 3: Adjust Segment Placement**
- For multi-segment paths: move horizontal segment up/down to avoid obstacles
- Test offsets: -50px, +50px, -100px, +100px
- Select offset that minimizes obstacle overlap

**Strategy 4: Fallback - Accept Minimal Overlap**
- If no clear path found, accept the path with fewest obstacles
- Log which obstacles are still being crossed for visual debugging

### Implementation Framework

```python
class ObstacleAwareRouter:
    """Routes connectors while avoiding object boxes."""
    
    def __init__(self, grids, connector):
        self.grids = grids
        self.connector = connector
        self.grid_system = GridCoordinateSystem()
    
    def find_best_path(self, source_grid, target_grid):
        """
        Find optimal connector path avoiding obstacles.
        
        Returns: (path_points, strategy_used, obstacles_count)
        """
        strategies = [
            self.try_direct_line,           # Strategy 0: Try direct
            self.try_two_segment,            # Strategy 1: Try 2-segment
            self.try_route_around_left,      # Strategy 2: Route left
            self.try_route_around_right,     # Strategy 3: Route right
            self.try_multi_segment_adjusted, # Strategy 4: Adjust V-H-V
        ]
        
        best_path = None
        best_obstacles = float('inf')
        best_strategy = -1
        
        for strategy_idx, strategy_func in enumerate(strategies):
            path = strategy_func(source_grid, target_grid)
            if path is None:
                continue
            
            obstacles = self.count_obstacles_on_path(path)
            
            if obstacles < best_obstacles:
                best_path = path
                best_obstacles = obstacles
                best_strategy = strategy_idx
            
            # If no obstacles found, use this path immediately
            if obstacles == 0:
                break
        
        return best_path, best_strategy, best_obstacles
    
    def count_obstacles_on_path(self, path_points):
        """Count how many obstacles block this path."""
        obstacles = self.detect_obstacles_on_path(path_points, self.grids)
        return len(obstacles)
    
    def try_direct_line(self, source_grid, target_grid):
        """Strategy 0: Direct line between source and target."""
        sx = source_grid.get_center()[0]
        sy = source_grid.get_center()[1]
        tx = target_grid.get_center()[0]
        ty = target_grid.get_center()[1]
        return [(sx, sy), (tx, ty)]
    
    def try_two_segment(self, source_grid, target_grid):
        """Strategy 1: Simple 2-segment L-shaped path."""
        sx = source_grid.get_center()[0]
        sy = source_grid.get_center()[1]
        tx = target_grid.get_center()[0]
        ty = target_grid.get_center()[1]
        
        # Try V-H pattern
        return [(sx, sy), (sx, (sy + ty) / 2), (tx, ty)]
    
    def try_route_around_left(self, source_grid, target_grid):
        """Strategy 2: Route around left side of obstacles."""
        sx = source_grid.get_center()[0]
        sy = source_grid.get_center()[1]
        tx = target_grid.get_center()[0]
        ty = target_grid.get_center()[1]
        
        # Add horizontal offset to the left
        offset_x = sx - 100
        return [(sx, sy), (offset_x, sy), (offset_x, ty), (tx, ty)]
    
    def try_route_around_right(self, source_grid, target_grid):
        """Strategy 3: Route around right side of obstacles."""
        sx = source_grid.get_center()[0]
        sy = source_grid.get_center()[1]
        tx = target_grid.get_center()[0]
        ty = target_grid.get_center()[1]
        
        # Add horizontal offset to the right
        offset_x = min(sx, tx) + 100
        return [(sx, sy), (offset_x, sy), (offset_x, ty), (tx, ty)]
    
    def try_multi_segment_adjusted(self, source_grid, target_grid):
        """Strategy 4: Adjust V-H-V path to avoid obstacles."""
        sx = source_grid.get_center()[0]
        sy = source_grid.get_center()[1]
        tx = target_grid.get_center()[0]
        ty = target_grid.get_center()[1]
        
        # Test different vertical offsets for the horizontal segment
        offsets_to_try = [-100, -50, 50, 100]
        
        for offset in offsets_to_try:
            mid_y = (sy + ty) / 2 + offset
            path = [(sx, sy), (sx, mid_y), (tx, mid_y), (tx, ty)]
            obstacles = self.count_obstacles_on_path(path)
            
            if obstacles == 0:
                return path
        
        # Return standard V-H-V if all offsets have obstacles
        mid_y = (sy + ty) / 2
        return [(sx, sy), (sx, mid_y), (tx, mid_y), (tx, ty)]
```

## Path Selection Logic

**When to trigger obstacle avoidance**:
1. **Always when**: Any connector path (checking for obstacles is automatic)
2. **Routing Preference Order**:
   1. **Direct connection** (preferred - simplest)
      - Straight line between source and target
      - Used even if endpoints aren't geometrically aligned
      - Only rejected if blocked by obstacles
   2. **2-Segment connector** (alternative - 1 bend)
      - V-H or H-V paths (vertical-horizontal or horizontal-vertical)
      - Try both orientations, pick best (fewest obstacles)
      - Use if clear or better than direct
   3. **3-Segment connector** (V-H-V orthogonal - 2 bends)
      - Standard multi-segment for maximum clarity
      - Use when 2-segment path has too many obstacles
      - Compare with 2-segment, keep better option
   4. **N-Segment connector** (advanced alternatives - 3+ bends)
      - Route left/right of obstacles (+/- 150px offset)
      - Used only as fallback when simpler paths blocked
      - Maximizes obstacle avoidance but adds complexity

**Skip obstacle avoidance for**:
- Self-loops (source == target)
- Already direct connections without alternatives

---

## Grid-Based Routing

This strategy uses the existing `GridCoordinateSystem` for:
- Converting SVG pixel coordinates to grid cells
- Sampling paths at grid intervals
- Detecting occupied cells

### Grid Cell Dimensions
- Width: 16px (2 monospace characters)
- Height: 32px (2 monospace lines)
- Margin: 20px

---

## Implementation Priority

**Phase 1** (Immediate):
- Implement `detect_obstacles_on_path()` 
- Implement `count_obstacles_on_path()`
- Add to `_route_connector()` in `class_diagram_connectors.py`

**Phase 2** (Next):
- Implement alternative routing strategies
- Select best path based on obstacle count

**Phase 3** (Future):
- Optimize cost function based on user feedback
- Add visual debugging (highlight tested paths)
- Consider connector group balancing

---

## Testing Strategy

**Test Cases**:
1. Connector passing through obstacle → Should route around
2. Connector aligned (no obstacle) → Should use direct line
3. Multiple obstacles → Should find path through gaps
4. No valid path exists → Should use path with minimal overlap

**Verification**:
- Visual inspection: Connectors should not render under object boxes
- Grid analysis: Use `GridAnalyzer` to detect remaining overlaps
- Performance: Routing should complete in < 100ms per connector
