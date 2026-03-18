"""Class diagram connector system using grid-based connection points.

Provides:
- Grid-based connection point selection on rectangle perimeters
- Multi-segment connector routing (DOWN → RIGHT → UP → RIGHT)
- Collision-aware connector planning with distance-based sorting
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
import math


@dataclass
class ConnectionPoint:
    """A connection point on a rectangle edge."""
    edge: str         # 'top', 'bottom', 'left', 'right'
    index: int        # 1-7 (point number on that edge)
    x: float          # Pixel x coordinate
    y: float          # Pixel y coordinate
    
    def __hash__(self):
        return hash((self.edge, self.index))
    
    def __eq__(self, other):
        if not isinstance(other, ConnectionPoint):
            return False
        return self.edge == other.edge and self.index == other.index


@dataclass
class RectangleGrid:
    """Grid of connection points around a rectangle perimeter."""
    x: float          # Rectangle left edge
    y: float          # Rectangle top edge
    width: float      # Rectangle width
    height: float     # Rectangle height
    name: str         # Rectangle label (for debugging)
    
    # Points per edge (calculated based on rectangle size)
    _points_top: List[ConnectionPoint] = field(default_factory=list)
    _points_bottom: List[ConnectionPoint] = field(default_factory=list)
    _points_left: List[ConnectionPoint] = field(default_factory=list)
    _points_right: List[ConnectionPoint] = field(default_factory=list)
    
    def __post_init__(self):
        """Calculate connection points on rectangle perimeter."""
        self._calculate_points()
    
    def _calculate_points(self):
        """Calculate evenly-spaced connection points on each edge.
        
        Logic:
        - Top/Bottom: 7 points across the width (indices 1-7, corners at 1,7 reserved)
        - Left/Right: Points based on height (corners at first/last reserved)
        
        Corner points (indices 1 and last on each edge) are reserved as non-connector zones.
        """
        # Top edge (y = self.y, x varies)
        # 7 total points, indices 1-7, but corners (1 and 7) are non-connector zones
        num_horizontal = 7
        self._points_top = []
        for i in range(1, num_horizontal + 1):
            x = self.x + (i - 1) * self.width / (num_horizontal - 1)
            pt = ConnectionPoint(edge='top', index=i, x=x, y=self.y)
            self._points_top.append(pt)
        
        # Bottom edge (y = self.y + height, x varies)
        self._points_bottom = []
        for i in range(1, num_horizontal + 1):
            x = self.x + (i - 1) * self.width / (num_horizontal - 1)
            pt = ConnectionPoint(edge='bottom', index=i, x=x, y=self.y + self.height)
            self._points_bottom.append(pt)
        
        # Left edge (x = self.x, y varies)
        num_vertical = max(3, int(self.height / 20))  # ~20px per point
        self._points_left = []
        for i in range(1, num_vertical + 1):
            y = self.y + (i - 1) * self.height / (num_vertical - 1)
            pt = ConnectionPoint(edge='left', index=i, x=self.x, y=y)
            self._points_left.append(pt)
        
        # Right edge (x = self.x + width, y varies)
        self._points_right = []
        for i in range(1, num_vertical + 1):
            y = self.y + (i - 1) * self.height / (num_vertical - 1)
            pt = ConnectionPoint(edge='right', index=i, x=self.x + self.width, y=y)
            self._points_right.append(pt)
    
    def is_corner_point(self, edge: str, index: int) -> bool:
        """Check if a point is at a corner (reserved, non-connector zone).
        
        Corner points are at index 1 and the last index on each edge.
        """
        points = self.get_points(edge)
        if not points:
            return True  # Non-existent points are treated as corners
        last_idx = len(points)
        return index == 1 or index == last_idx
    
    def get_points(self, edge: str) -> List[ConnectionPoint]:
        """Get all connection points for a given edge."""
        if edge == 'top':
            return self._points_top
        elif edge == 'bottom':
            return self._points_bottom
        elif edge == 'left':
            return self._points_left
        elif edge == 'right':
            return self._points_right
        else:
            raise ValueError(f"Invalid edge: {edge}")
    
    def get_point(self, edge: str, index: int) -> Optional[ConnectionPoint]:
        """Get a specific connection point by edge and index."""
        points = self.get_points(edge)
        if 1 <= index <= len(points):
            return points[index - 1]
        return None
    
    def get_center(self) -> Tuple[float, float]:
        """Get the center of the rectangle."""
        return (self.x + self.width / 2, self.y + self.height / 2)


@dataclass
class ConnectorPath:
    """Represents a connector between two rectangles."""
    source_name: str
    target_name: str
    arrow_type: str               # Arrow type (--◆, etc.)
    src_mult: str = ""            # Source multiplicity
    tgt_mult: str = ""            # Target multiplicity
    label: str = ""               # Relationship label
    layer: str = ""               # Layer for filtering
    
    # Connection points assigned
    source_edge: str = ""
    source_point_idx: int = 0
    target_edge: str = ""
    target_point_idx: int = 0
    
    # Computed path
    source_x: float = 0.0
    source_y: float = 0.0
    target_x: float = 0.0
    target_y: float = 0.0
    
    # For multi-segment paths
    segments: List[Tuple[float, float]] = field(default_factory=list)
    path_type: str = "direct"     # 'direct' or 'multi_segment'
    
    def calculate_distance(self) -> float:
        """Calculate Manhattan distance of the connector path."""
        if self.path_type == "direct":
            dx = self.target_x - self.source_x
            dy = self.target_y - self.source_y
            return math.sqrt(dx*dx + dy*dy)
        else:
            # Multi-segment: sum of segment lengths
            total = 0.0
            if self.segments:
                sx, sy = self.source_x, self.source_y
                for tx, ty in self.segments:
                    dx = tx - sx
                    dy = ty - sy
                    total += math.sqrt(dx*dx + dy*dy)
                    sx, sy = tx, ty
            return total


class ConnectorPlanner:
    """Plans and routes connectors for a class diagram."""
    
    def __init__(self, routing_mode: str = "diagonal"):
        self.grids: Dict[str, RectangleGrid] = {}
        self.connectors: List[ConnectorPath] = []
        self.routing_mode = routing_mode  # 'diagonal', 'orthogonal', or 'mixed'
    
    def add_rectangle(self, name: str, x: float, y: float, width: float, height: float):
        """Register a rectangle in the planner."""
        grid = RectangleGrid(x=x, y=y, width=width, height=height, name=name)
        self.grids[name] = grid
    
    def add_connector(self, source: str, target: str, arrow_type: str,
                     src_mult: str = "", tgt_mult: str = "", label: str = "", 
                     layer: str = ""):
        """Add a connector to be routed."""
        if source not in self.grids or target not in self.grids:
            return  # Skip if boxes not registered
        
        connector = ConnectorPath(
            source_name=source,
            target_name=target,
            arrow_type=arrow_type,
            src_mult=src_mult,
            tgt_mult=tgt_mult,
            label=label,
            layer=layer
        )
        self.connectors.append(connector)
    
    def _select_exit_edge(self, source_grid: RectangleGrid, target_grid: RectangleGrid) -> str:
        """Select the primary exit edge based on target direction.
        
        Simple rule: Choose the edge pointing toward the target center.
        """
        src_cx = source_grid.x + source_grid.width / 2
        src_cy = source_grid.y + source_grid.height / 2
        tgt_cx = target_grid.x + target_grid.width / 2
        tgt_cy = target_grid.y + target_grid.height / 2
        
        dx = tgt_cx - src_cx
        dy = tgt_cy - src_cy
        
        # Prioritize horizontal movement, then vertical
        if abs(dx) > abs(dy):
            return 'right' if dx > 0 else 'left'
        else:
            return 'bottom' if dy > 0 else 'top'
    
    def _get_opposite_edge(self, edge: str) -> str:
        """Get the opposite edge."""
        opposites = {'top': 'bottom', 'bottom': 'top', 'left': 'right', 'right': 'left'}
        return opposites.get(edge, 'bottom')
    
    def _get_fallback_edges(self, primary_edge: str) -> list:
        """Get fallback edges when primary edge is exhausted.
        
        Fallback priority:
        - If primary is top/bottom, fallback to same edge (both top or both bottom),
          then try opposite, then try left/right
        - If primary is left/right, fallback to bottom/top
        
        For horizontally adjacent boxes, prefer same-edge fallbacks to maintain
        horizontal connector paths with a small jog.
        """
        if primary_edge in ['top', 'bottom']:
            # Same edge first (both top or both bottom), then opposite, then perpendicular
            return [primary_edge, self._get_opposite_edge(primary_edge), 'left', 'right']
        else:  # left or right
            # Fallback to horizontal edges
            return ['bottom', 'top']
    
    def plan_connectors(self):
        """Plan all connectors: assign connection points and calculate routes.
        
        Algorithm:
        1. Calculate ideal distance for each connector
        2. Sort by distance (shortest first)
        3. Assign connection points (enforcing: one per point max, skip corners)
        4. Calculate routes (direct or multi-segment)
        
        Constraints:
        - Each connection point can have at most one outgoing connector
        - Each connection point can have at most one incoming connector
        - Corner points (index 1 and last on each edge) are reserved (non-connector zones)
        - Use the connection point closest to the object connected to
        """
        # Step 1: Calculate distances (using center-to-center for initial estimate)
        for connector in self.connectors:
            src_grid = self.grids[connector.source_name]
            tgt_grid = self.grids[connector.target_name]
            
            src_cx, src_cy = src_grid.get_center()
            tgt_cx, tgt_cy = tgt_grid.get_center()
            
            dx = tgt_cx - src_cx
            dy = tgt_cy - src_cy
            connector.source_x = src_cx
            connector.source_y = src_cy
            connector.target_x = tgt_cx
            connector.target_y = tgt_cy
        
        # Step 2 & 3: Sort and assign points
        self.connectors.sort(key=lambda c: c.calculate_distance())
        
        # Track used points: (box_name, edge, index) -> ('outgoing'|'incoming')
        used_points: Dict[Tuple[str, str, int], str] = {}
        
        for connector in self.connectors:
            src_grid = self.grids[connector.source_name]
            tgt_grid = self.grids[connector.target_name]
            
            # Get target center to find closest source point
            tgt_cx = connector.target_x
            tgt_cy = connector.target_y
            
            # Get source center to find closest target point
            src_cx = connector.source_x
            src_cy = connector.source_y
            
            # Select exit and entry edges based on target direction
            exit_edge = self._select_exit_edge(src_grid, tgt_grid)
            entry_edge = self._get_opposite_edge(exit_edge)
            
            # Assign outgoing point: find closest to target on exit_edge
            src_pt = None
            best_dist = float('inf')
            for pt in src_grid.get_points(exit_edge):
                if src_grid.is_corner_point(exit_edge, pt.index):
                    continue
                if (connector.source_name, exit_edge, pt.index) in used_points:
                    continue
                # Calculate distance from this point to target center
                dist = (pt.x - tgt_cx)**2 + (pt.y - tgt_cy)**2
                if dist < best_dist:
                    best_dist = dist
                    src_pt = pt
            
            if src_pt:
                connector.source_edge = exit_edge
                connector.source_point_idx = src_pt.index
                connector.source_x = src_pt.x
                connector.source_y = src_pt.y
                used_points[(connector.source_name, exit_edge, src_pt.index)] = 'outgoing'
            
            # Assign incoming point: find closest to source on entry_edge
            tgt_pt = None
            best_dist = float('inf')
            for pt in tgt_grid.get_points(entry_edge):
                if tgt_grid.is_corner_point(entry_edge, pt.index):
                    continue
                if (connector.target_name, entry_edge, pt.index) in used_points:
                    continue
                # Calculate distance from this point to source center
                dist = (pt.x - src_cx)**2 + (pt.y - src_cy)**2
                if dist < best_dist:
                    best_dist = dist
                    tgt_pt = pt
            
            if tgt_pt:
                connector.target_edge = entry_edge
                connector.target_point_idx = tgt_pt.index
                connector.target_x = tgt_pt.x
                connector.target_y = tgt_pt.y
                used_points[(connector.target_name, entry_edge, tgt_pt.index)] = 'incoming'
            
            # Determine if we need multi-segment routing
            # Use multi-segment when source and target are not aligned on primary axis
            self._route_connector(connector)
    
    def _route_connector(self, connector: ConnectorPath):
        """Calculate the path for a connector based on routing mode.
        
        Routing modes:
        - DIAGONAL: Uses simplified paths (Direct -> 2-Segment -> 3-Segment -> N-Segment)
          Allows multi-segment bending for obstacle avoidance
        - ORTHOGONAL: Only horizontal/vertical lines, requires objects pre-aligned
          Only uses direct H or V connections
        - MIXED: Uses diagonal when aligned, orthogonal when offset
        """
        if self.routing_mode == "diagonal":
            self._route_connector_diagonal(connector)
        elif self.routing_mode == "orthogonal":
            self._route_connector_orthogonal(connector)
        else:  # "mixed"
            self._route_connector_mixed(connector)
    
    def _route_connector_diagonal(self, connector: ConnectorPath):
        """Route diagonal connectors: Direct -> 2-Segment -> 3-Segment -> N-Segment.
        
        Uses preference cascade to favor simpler paths.
        """
        # Get source and target grids
        src_grid = self.grids[connector.source_name]
        tgt_grid = self.grids[connector.target_name]
        
        x1, y1 = connector.source_x, connector.source_y
        x2, y2 = connector.target_x, connector.target_y
        
        # Step 1: Try direct line routing
        direct_path = [(x1, y1), (x2, y2)]
        obstacles = self._detect_obstacles_on_path(connector.source_name, connector.target_name, direct_path)
        
        if obstacles == 0:
            # Direct line is clear - use it
            connector.path_type = "direct"
        else:
            # Step 2: Try 2-segment routing (V-H or H-V)
            two_segment_vh = self._try_two_segment_vh(src_grid, tgt_grid)
            two_segment_hv = self._try_two_segment_hv(src_grid, tgt_grid)
            
            obstacles_vh = self._detect_obstacles_on_path(connector.source_name, connector.target_name, two_segment_vh)
            obstacles_hv = self._detect_obstacles_on_path(connector.source_name, connector.target_name, two_segment_hv)
            
            best_2seg = two_segment_vh if obstacles_vh <= obstacles_hv else two_segment_hv
            best_2seg_obstacles = min(obstacles_vh, obstacles_hv)
            
            if best_2seg_obstacles == 0 or best_2seg_obstacles <= obstacles:
                # 2-segment is clear or equal/better than direct
                connector.path_type = "multi_segment"
                connector.segments = best_2seg
            else:
                # Step 3: Try 3-segment V-H-V routing
                self._route_multi_segment(connector)
                
                if connector.segments:
                    path_points = [(connector.source_x, connector.source_y)] + connector.segments
                    obstacles_3seg = self._detect_obstacles_on_path(connector.source_name, connector.target_name, path_points)
                    
                    if obstacles_3seg <= best_2seg_obstacles:
                        # 3-segment is as good or better
                        connector.path_type = "multi_segment"
                    else:
                        # Use best 2-segment
                        connector.segments = best_2seg
                        connector.path_type = "multi_segment"
                else:
                    # Step 4: Fallback to best alternative routing
                    best_path = self._find_best_path(connector.source_name, connector.target_name, src_grid, tgt_grid)
                    connector.segments = best_path
                    connector.path_type = "multi_segment"
    
    def _route_connector_orthogonal(self, connector: ConnectorPath):
        """Route orthogonal connectors: Only horizontal or vertical lines.
        
        For orthogonal routing to work well, objects must be pre-aligned
        so their connection points match on horizontal or vertical axis.
        No intermediate bends are introduced.
        """
        # Simply use direct line for orthogonal routing
        # Objects should already be aligned for this to work
        # If not aligned, we don't introduce bends - just use the direct line
        connector.path_type = "direct"
    
    def _route_connector_mixed(self, connector: ConnectorPath):
        """Route mixed connectors: Diagonal when aligned, orthogonal otherwise."""
        # For now, treat mixed like diagonal (use preference cascade)
        self._route_connector_diagonal(connector)
    
    def _route_multi_segment(self, connector: ConnectorPath):
        """Create a multi-segment path (DOWN → RIGHT → UP → RIGHT or equivalent)."""
        connector.path_type = "multi_segment"
        connector.segments = []
        
        x1, y1 = connector.source_x, connector.source_y
        x2, y2 = connector.target_x, connector.target_y
        
        # Determine routing based on exit/entry edges
        src_edge = connector.source_edge
        tgt_edge = connector.target_edge
        
        # Multi-segment should have 4 segments: exit vertical, horizontal, entry vertical, final horizontal
        # Or: exit horizontal, vertical, entry horizontal, final vertical
        
        margin = 30  # Space to route outside the boxes
        
        if src_edge in ['top', 'bottom']:
            # Exiting horizontally, need vertical at mid-point
            mid_y = (y1 + y2) / 2
            
            if tgt_edge in ['left', 'right']:
                # Entering vertically
                mid_x = x2
                connector.segments = [
                    (x1, y1 + (margin if src_edge == 'bottom' else -margin)),
                    (mid_x, y1 + (margin if src_edge == 'bottom' else -margin)),
                    (mid_x, y2),
                    (x2, y2)
                ]
            else:
                # Entering horizontally
                connector.segments = [
                    (x1, mid_y),
                    (x2, mid_y),
                    (x2, y2)
                ]
        else:
            # Exiting vertically
            mid_x = (x1 + x2) / 2
            
            if tgt_edge in ['top', 'bottom']:
                # Entering vertically (same direction)
                mid_y = y2
                connector.segments = [
                    (x1 + (margin if src_edge == 'right' else -margin), y1),
                    (x1 + (margin if src_edge == 'right' else -margin), mid_y),
                    (x2, mid_y)
                ]
            else:
                # Entering horizontally
                connector.segments = [
                    (mid_x, y1),
                    (mid_x, y2),
                    (x2, y2)
                ]
    
    def _point_in_box(self, point_x: float, point_y: float, box_grid: RectangleGrid) -> bool:
        """Check if a point (x, y) is inside a box (not including edges).
        
        Args:
            point_x, point_y: Point coordinates
            box_grid: RectangleGrid to check
        
        Returns:
            True if point is inside box, False otherwise
        """
        return (box_grid.x < point_x < box_grid.x + box_grid.width and
                box_grid.y < point_y < box_grid.y + box_grid.height)
    
    def _detect_obstacles_on_path(self, source_name: str, target_name: str, 
                                 path_points: List[Tuple[float, float]]) -> int:
        """Detect and count obstacles on a proposed connector path.
        
        Samples the path at grid intervals and counts how many obstacles are hit.
        
        Args:
            source_name: Name of source box (excluded from obstacle check)
            target_name: Name of target box (excluded from obstacle check)
            path_points: List of (x, y) coordinates defining the path
        
        Returns:
            Count of obstacles encountered (0 means clear path)
        """
        SAMPLE_INTERVAL = 16  # Grid block width - sample every block
        obstacle_count = 0
        
        # Build list of obstacle boxes (exclude source and target)
        obstacle_boxes = {
            name: grid for name, grid in self.grids.items()
            if name not in [source_name, target_name]
        }
        
        # Sample each segment of the path
        for i in range(len(path_points) - 1):
            x1, y1 = path_points[i]
            x2, y2 = path_points[i + 1]
            
            # Calculate segment length
            dx = x2 - x1
            dy = y2 - y1
            segment_len = math.sqrt(dx*dx + dy*dy)
            
            if segment_len == 0:
                continue
            
            # Sample points along this segment
            samples = max(int(segment_len / SAMPLE_INTERVAL), 1)
            for sample_idx in range(samples + 1):
                t = sample_idx / max(samples, 1)
                sample_x = x1 + dx * t
                sample_y = y1 + dy * t
                
                # Check which obstacle boxes contain this point
                for box_name, box_grid in obstacle_boxes.items():
                    if self._point_in_box(sample_x, sample_y, box_grid):
                        obstacle_count += 1
                        break  # Count each box only once per segment
        
        return obstacle_count
    
    def _try_direct_line(self, src_grid: RectangleGrid, tgt_grid: RectangleGrid) -> List[Tuple[float, float]]:
        """Try direct line routing."""
        sx = src_grid.x + src_grid.width / 2
        sy = src_grid.y + src_grid.height / 2
        tx = tgt_grid.x + tgt_grid.width / 2
        ty = tgt_grid.y + tgt_grid.height / 2
        return [(sx, sy), (tx, ty)]
    
    def _try_two_segment_vh(self, src_grid: RectangleGrid, tgt_grid: RectangleGrid) -> List[Tuple[float, float]]:
        """Try 2-segment V-H path (vertical then horizontal)."""
        sx = src_grid.x + src_grid.width / 2
        sy = src_grid.y + src_grid.height / 2
        tx = tgt_grid.x + tgt_grid.width / 2
        ty = tgt_grid.y + tgt_grid.height / 2
        mid_y = (sy + ty) / 2
        return [(sx, sy), (sx, mid_y), (tx, ty)]
    
    def _try_two_segment_hv(self, src_grid: RectangleGrid, tgt_grid: RectangleGrid) -> List[Tuple[float, float]]:
        """Try 2-segment H-V path (horizontal then vertical)."""
        sx = src_grid.x + src_grid.width / 2
        sy = src_grid.y + src_grid.height / 2
        tx = tgt_grid.x + tgt_grid.width / 2
        ty = tgt_grid.y + tgt_grid.height / 2
        mid_x = (sx + tx) / 2
        return [(sx, sy), (mid_x, sy), (tx, ty)]
    
    def _try_route_left(self, src_grid: RectangleGrid, tgt_grid: RectangleGrid) -> List[Tuple[float, float]]:
        """Try routing around left side of obstacles."""
        sx = src_grid.x + src_grid.width / 2
        sy = src_grid.y + src_grid.height / 2
        tx = tgt_grid.x + tgt_grid.width / 2
        ty = tgt_grid.y + tgt_grid.height / 2
        offset_x = min(sx, tx) - 150
        return [(sx, sy), (offset_x, sy), (offset_x, ty), (tx, ty)]
    
    def _try_route_right(self, src_grid: RectangleGrid, tgt_grid: RectangleGrid) -> List[Tuple[float, float]]:
        """Try routing around right side of obstacles."""
        sx = src_grid.x + src_grid.width / 2
        sy = src_grid.y + src_grid.height / 2
        tx = tgt_grid.x + tgt_grid.width / 2
        ty = tgt_grid.y + tgt_grid.height / 2
        offset_x = max(sx, tx) + 150
        return [(sx, sy), (offset_x, sy), (offset_x, ty), (tx, ty)]
    
    def _find_best_path(self, source_name: str, target_name: str, 
                       src_grid: RectangleGrid, tgt_grid: RectangleGrid) -> List[Tuple[float, float]]:
        """Find best connector path avoiding obstacles.
        
        Tries multiple routing strategies and selects the one with fewest obstacles.
        
        Args:
            source_name: Name of source box
            target_name: Name of target box
            src_grid: Source RectangleGrid
            tgt_grid: Target RectangleGrid
        
        Returns:
            Best path as list of (x, y) coordinates
        """
        strategies = [
            ("direct", self._try_direct_line),
            ("v-h", self._try_two_segment_vh),
            ("h-v", self._try_two_segment_hv),
            ("left", self._try_route_left),
            ("right", self._try_route_right),
        ]
        
        best_path = None
        best_obstacle_count = float('inf')
        best_strategy_name = None
        
        for strategy_name, strategy_func in strategies:
            path = strategy_func(src_grid, tgt_grid)
            obstacles = self._detect_obstacles_on_path(source_name, target_name, path)
            
            if obstacles < best_obstacle_count:
                best_path = path
                best_obstacle_count = obstacles
                best_strategy_name = strategy_name
            
            # If we find a clear path, use it immediately
            if obstacles == 0:
                break
        
        return best_path or self._try_direct_line(src_grid, tgt_grid)

    def get_connectors(self, layer_filter: Optional[str] = None) -> List[ConnectorPath]:
        """Get connectors, optionally filtered by layer."""
        if layer_filter is None:
            return self.connectors
        
        # Filter by layer
        return [c for c in self.connectors if not c.layer or c.layer == layer_filter]
