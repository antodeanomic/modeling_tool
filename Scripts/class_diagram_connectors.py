"""Class diagram connector system using grid-based connection points.

Provides:
- Grid-based connection point selection on rectangle perimeters
- Multi-segment connector routing (DOWN → RIGHT → UP → RIGHT)
- Collision-aware connector planning with distance-based sorting
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Set
import math

GRID_CELL_SIZE_PX = 20


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
        # Grid columns are derived from fixed-size square cells.
        num_horizontal = max(3, int(round(self.width / GRID_CELL_SIZE_PX)))
        self._points_top = []
        for i in range(1, num_horizontal + 1):
            x = self.x + (i - 1) * GRID_CELL_SIZE_PX
            pt = ConnectionPoint(edge='top', index=i, x=x, y=self.y)
            self._points_top.append(pt)
        
        # Bottom edge (y = self.y + height, x varies)
        self._points_bottom = []
        for i in range(1, num_horizontal + 1):
            x = self.x + (i - 1) * GRID_CELL_SIZE_PX
            pt = ConnectionPoint(edge='bottom', index=i, x=x, y=self.y + self.height)
            self._points_bottom.append(pt)
        
        # Left edge (x = self.x, y varies)
        num_vertical = max(3, int(round(self.height / GRID_CELL_SIZE_PX)))
        self._points_left = []
        for i in range(1, num_vertical + 1):
            y = self.y + (i - 1) * GRID_CELL_SIZE_PX
            pt = ConnectionPoint(edge='left', index=i, x=self.x, y=y)
            self._points_left.append(pt)
        
        # Right edge (x = self.x + width, y varies)
        self._points_right = []
        for i in range(1, num_vertical + 1):
            y = self.y + (i - 1) * GRID_CELL_SIZE_PX
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
        # Track-oriented occupancy map for orthogonal connector segments.
        # Key: (grid_x, grid_y, axis) where axis is 'h' or 'v'.
        self._occupied_connector_cells: Dict[Tuple[int, int, str], int] = {}
        self._grid_cell_width = 16
        self._grid_cell_height = 32
    
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
    
    def _select_exit_edge(self, source_grid: RectangleGrid, target_grid: RectangleGrid, arrow_type: str = '') -> str:
        """Select the primary exit edge based on target direction and relationship semantics.
        
        Rules:
        1. For ownership/containment relationships (◆, ◇): prefer vertical routing to show hierarchy
           - If target is below, exit from bottom
           - If target is above, exit from top
        2. For other relationships: choose based on which distance is dominant
           - If vertical distance is larger, exit from top/bottom
           - If horizontal distance is larger, exit from left/right
        """
        src_cx = source_grid.x + source_grid.width / 2
        src_cy = source_grid.y + source_grid.height / 2
        tgt_cx = target_grid.x + target_grid.width / 2
        tgt_cy = target_grid.y + target_grid.height / 2
        
        dx = tgt_cx - src_cx
        dy = tgt_cy - src_cy
        
        # Check if this is an ownership/containment relationship
        is_ownership_relationship = '◆' in arrow_type or '◇' in arrow_type
        
        if is_ownership_relationship and abs(dy) > 0:
            # For ownership relationships, prefer vertical exit if target is notably above or below
            # This shows the parent-child hierarchy more clearly
            if abs(dy) > 50:  # Significant vertical distance
                return 'bottom' if dy > 0 else 'top'
        
        # Default: Prioritize direction with larger distance
        if abs(dy) > abs(dx):
            return 'bottom' if dy > 0 else 'top'
        else:
            return 'right' if dx > 0 else 'left'
    
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
    
    def _find_aligned_connection_points(self, src_grid: RectangleGrid, tgt_grid: RectangleGrid,
                                       exit_edge: str, entry_edge: str, used_points: dict,
                                       src_name: str, tgt_name: str):
        """Find connection points that maintain grid alignment for vertical/horizontal connectors.
        
        When objects are aligned on one axis, find connection points that
        maintain that alignment to enable straight lines.
        
        Handles:
        - Vertical edges (left/right): finds Y-aligned points (dy < 1)
        - Horizontal edges (top/bottom) for X-aligned boxes: finds best X-aligned pair
        
        Returns: (src_point, tgt_point) or (None, None) if no aligned pair found
        """
        src_points = src_grid.get_points(exit_edge)
        tgt_points = tgt_grid.get_points(entry_edge)
        
        # Detect if source and target boxes are X-aligned (left edges)
        dx_left = abs(tgt_grid.x - src_grid.x)
        is_x_aligned = dx_left < 1
        
        # For horizontal edges (top/bottom): look for X-aligned points if boxes are X-aligned
        if exit_edge in ['top', 'bottom'] and entry_edge in ['top', 'bottom'] and is_x_aligned:
            best_src = None
            best_tgt = None
            best_dx = float('inf')
            
            for src_pt in src_points:
                if src_grid.is_corner_point(exit_edge, src_pt.index):
                    continue
                if (src_name, exit_edge, src_pt.index) in used_points:
                    continue
                
                for tgt_pt in tgt_points:
                    if tgt_grid.is_corner_point(entry_edge, tgt_pt.index):
                        continue
                    if (tgt_name, entry_edge, tgt_pt.index) in used_points:
                        continue
                    
                    # Measure X alignment
                    dx = abs(tgt_pt.x - src_pt.x)
                    if dx < best_dx:
                        best_dx = dx
                        best_src = src_pt
                        best_tgt = tgt_pt
            
            # Return if we found reasonable alignment (best match even if > 1px)
            if best_src and best_dx < 20:  # Allow some tolerance for width differences
                return (best_src, best_tgt)
        
        # For vertical edges (left/right): find Y-aligned points
        elif exit_edge in ['left', 'right'] and entry_edge in ['left', 'right']:
            best_src = None
            best_tgt = None
            best_dy = float('inf')
            
            for src_pt in src_points:
                if src_grid.is_corner_point(exit_edge, src_pt.index):
                    continue
                if (src_name, exit_edge, src_pt.index) in used_points:
                    continue
                
                for tgt_pt in tgt_points:
                    if tgt_grid.is_corner_point(entry_edge, tgt_pt.index):
                        continue
                    if (tgt_name, entry_edge, tgt_pt.index) in used_points:
                        continue
                    
                    # Measure Y alignment
                    dy = abs(tgt_pt.y - src_pt.y)
                    if dy < best_dy:
                        best_dy = dy
                        best_src = src_pt
                        best_tgt = tgt_pt
            
            # Return only if significantly aligned (dy < 1 pixel)
            if best_dy < 1:
                return (best_src, best_tgt)
        
        return (None, None)

    def _is_hierarchy_connector(self, connector: ConnectorPath) -> bool:
        """Return True for ownership/composition relationships in downward hierarchy."""
        if '◆' not in connector.arrow_type and '◇' not in connector.arrow_type:
            return False

        src_grid = self.grids.get(connector.source_name)
        tgt_grid = self.grids.get(connector.target_name)
        if not src_grid or not tgt_grid:
            return False

        src_cx, src_cy = src_grid.get_center()
        tgt_cx, tgt_cy = tgt_grid.get_center()
        return tgt_cy > src_cy + 5

    def _ordered_hierarchy_connectors(self) -> Dict[int, Tuple[int, int]]:
        """Return left-to-right sibling order metadata keyed by connector id.

        For each source object, ownership connectors to children below are ordered
        by target X center so connectors are processed left-to-right.
        """
        grouped: Dict[str, List[ConnectorPath]] = {}
        for connector in self.connectors:
            if self._is_hierarchy_connector(connector):
                grouped.setdefault(connector.source_name, []).append(connector)

        metadata: Dict[int, Tuple[int, int]] = {}
        for source_name, items in grouped.items():
            items.sort(key=lambda c: self.grids[c.target_name].get_center()[0])
            total = len(items)
            for idx, connector in enumerate(items):
                metadata[id(connector)] = (idx, total)

        return metadata

    def _build_spaced_indices(self, edge_point_count: int, connector_count: int) -> List[int]:
        """Build evenly spaced non-corner point indices from left to right."""
        usable = list(range(2, edge_point_count))
        if not usable:
            return []

        if connector_count <= 1:
            return [usable[0]]

        if connector_count >= len(usable):
            return usable

        result: List[int] = []
        step = (len(usable) - 1) / (connector_count - 1)
        for i in range(connector_count):
            idx = int(round(i * step))
            idx = max(0, min(idx, len(usable) - 1))
            result.append(usable[idx])

        # De-duplicate while preserving order, then fill any missing slots.
        deduped: List[int] = []
        for idx in result:
            if idx not in deduped:
                deduped.append(idx)

        if len(deduped) < connector_count:
            for idx in usable:
                if idx not in deduped:
                    deduped.append(idx)
                if len(deduped) >= connector_count:
                    break

        return deduped[:connector_count]

    def _select_hierarchy_source_point(self, src_grid: RectangleGrid, sibling_idx: int,
                                       sibling_count: int, used_points: Dict[Tuple[str, str, int], str],
                                       source_name: str) -> Optional[ConnectionPoint]:
        """Select bottom-edge source point for hierarchy connectors, left-to-right."""
        bottom_points = src_grid.get_points('bottom')
        if not bottom_points:
            return None

        candidate_indices = self._build_spaced_indices(len(bottom_points), max(1, sibling_count))
        if not candidate_indices:
            return None

        preferred_index = candidate_indices[min(sibling_idx, len(candidate_indices) - 1)]
        preferred_point = src_grid.get_point('bottom', preferred_index)

        if preferred_point and (source_name, 'bottom', preferred_point.index) not in used_points:
            return preferred_point

        # Fallback: nearest available candidate by index distance.
        available: List[ConnectionPoint] = []
        for idx in candidate_indices:
            pt = src_grid.get_point('bottom', idx)
            if pt and (source_name, 'bottom', pt.index) not in used_points:
                available.append(pt)

        if not available:
            for pt in bottom_points:
                if src_grid.is_corner_point('bottom', pt.index):
                    continue
                if (source_name, 'bottom', pt.index) in used_points:
                    continue
                available.append(pt)

        if not available:
            return None

        return min(available, key=lambda pt: abs(pt.index - preferred_index))
    
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
        # Reset occupancy map each planning run.
        self._occupied_connector_cells = {}

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
        hierarchy_order = self._ordered_hierarchy_connectors()
        self.connectors.sort(
            key=lambda c: (
                0 if id(c) in hierarchy_order else 1,
                c.source_name,
                hierarchy_order.get(id(c), (0, 0))[0],
                c.calculate_distance()
            )
        )
        
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
            is_hierarchy = id(connector) in hierarchy_order
            if is_hierarchy:
                exit_edge = 'bottom'
                entry_edge = 'top'
            else:
                exit_edge = self._select_exit_edge(src_grid, tgt_grid, connector.arrow_type)
                entry_edge = self._get_opposite_edge(exit_edge)
            
            # For orthogonal routing: try to find aligned connection points first
            # Hierarchy connectors intentionally skip this shortcut so left-to-right
            # bottom-edge assignment remains deterministic.
            if self.routing_mode == "orthogonal" and not is_hierarchy:
                src_pt, tgt_pt = self._find_aligned_connection_points(src_grid, tgt_grid, exit_edge, entry_edge, used_points, connector.source_name, connector.target_name)
                
                if src_pt and tgt_pt:
                    # Found aligned points! Use them
                    connector.source_edge = exit_edge
                    connector.source_point_idx = src_pt.index
                    connector.source_x = src_pt.x
                    connector.source_y = src_pt.y
                    used_points[(connector.source_name, exit_edge, src_pt.index)] = 'outgoing'
                    
                    connector.target_edge = entry_edge
                    connector.target_point_idx = tgt_pt.index
                    connector.target_x = tgt_pt.x
                    connector.target_y = tgt_pt.y
                    used_points[(connector.target_name, entry_edge, tgt_pt.index)] = 'incoming'
                    
                    # Route and skip to next connector
                    self._route_connector(connector)
                    self._register_connector_occupancy(connector)
                    continue
            
            # Standard (non-aligned) point selection
            # Assign outgoing point: hierarchy uses deterministic left-to-right bottom points.
            src_pt = None
            best_dist = float('inf')
            if is_hierarchy:
                sibling_idx, sibling_count = hierarchy_order[id(connector)]
                src_pt = self._select_hierarchy_source_point(
                    src_grid,
                    sibling_idx,
                    sibling_count,
                    used_points,
                    connector.source_name
                )
            else:
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
            if is_hierarchy and src_pt is not None:
                # Keep the first branch as vertical as possible by aligning target top point to source X.
                for pt in tgt_grid.get_points(entry_edge):
                    if tgt_grid.is_corner_point(entry_edge, pt.index):
                        continue
                    if (connector.target_name, entry_edge, pt.index) in used_points:
                        continue
                    dist = abs(pt.x - src_pt.x)
                    if dist < best_dist:
                        best_dist = dist
                        tgt_pt = pt
            else:
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
            self._register_connector_occupancy(connector)

    def _to_grid_cell(self, x: float, y: float) -> Tuple[int, int]:
        """Convert SVG coordinates to connector occupancy grid coordinates."""
        gx = int(round(x / self._grid_cell_width))
        gy = int(round(y / self._grid_cell_height))
        return (gx, gy)

    def _collect_segment_cells(self, x1: float, y1: float, x2: float, y2: float, axis: str) -> Set[Tuple[int, int, str]]:
        """Collect occupied grid cells for a segment using axis-aware keys."""
        cells: Set[Tuple[int, int, str]] = set()
        dx = x2 - x1
        dy = y2 - y1
        segment_len = max(abs(dx), abs(dy))
        if segment_len < 0.001:
            gx, gy = self._to_grid_cell(x1, y1)
            cells.add((gx, gy, axis))
            return cells

        sample_step = max(self._grid_cell_width / 2, 8)
        samples = max(int(segment_len / sample_step), 1)
        for idx in range(samples + 1):
            t = idx / samples
            sx = x1 + dx * t
            sy = y1 + dy * t
            gx, gy = self._to_grid_cell(sx, sy)
            cells.add((gx, gy, axis))
        return cells

    def _collect_path_cells(self, path_points: List[Tuple[float, float]]) -> Set[Tuple[int, int, str]]:
        """Collect occupied grid cells for an orthogonal path.

        Same-axis overlap in the same cell is considered a routing conflict.
        Perpendicular intersections remain valid because axis is part of the key.
        """
        cells: Set[Tuple[int, int, str]] = set()
        for idx in range(len(path_points) - 1):
            x1, y1 = path_points[idx]
            x2, y2 = path_points[idx + 1]
            if abs(y2 - y1) <= 1:
                axis = 'h'
            elif abs(x2 - x1) <= 1:
                axis = 'v'
            else:
                # Diagonal fallback: mark both axes to avoid unsafe re-use.
                cells.update(self._collect_segment_cells(x1, y1, x2, y2, 'h'))
                cells.update(self._collect_segment_cells(x1, y1, x2, y2, 'v'))
                continue
            cells.update(self._collect_segment_cells(x1, y1, x2, y2, axis))
        return cells

    def _count_path_overlaps(self, path_points: List[Tuple[float, float]]) -> int:
        """Count how many occupied connector cells this path would re-use."""
        overlaps = 0
        for cell_key in self._collect_path_cells(path_points):
            overlaps += self._occupied_connector_cells.get(cell_key, 0)
        return overlaps

    def _register_connector_occupancy(self, connector: ConnectorPath):
        """Register routed connector cells so later connectors can avoid overlaps."""
        if connector.path_type == "multi_segment" and connector.segments:
            path_points = [(connector.source_x, connector.source_y)] + connector.segments + [(connector.target_x, connector.target_y)]
        else:
            path_points = [(connector.source_x, connector.source_y), (connector.target_x, connector.target_y)]

        for cell_key in self._collect_path_cells(path_points):
            self._occupied_connector_cells[cell_key] = self._occupied_connector_cells.get(cell_key, 0) + 1

    def _choose_best_orthogonal_segments(self, connector: ConnectorPath, mode: str) -> List[Tuple[float, float]]:
        """Pick orthogonal segments that minimize same-axis grid-cell overlap.

        Args:
            connector: Connector being routed
            mode: 'vhv' or 'hvh'
        """
        x1, y1 = connector.source_x, connector.source_y
        x2, y2 = connector.target_x, connector.target_y

        best_segments: List[Tuple[float, float]] = []
        best_score = float('inf')
        track_step = self._grid_cell_height / 2 if mode == 'vhv' else self._grid_cell_width / 2

        for track_idx in [0, 1, -1, 2, -2, 3, -3]:
            if mode == 'vhv':
                mid = (y1 + y2) / 2 + track_idx * track_step
                candidate_segments = [
                    (x1, mid),
                    (x2, mid),
                    (x2, y2)
                ]
            else:
                mid = (x1 + x2) / 2 + track_idx * track_step
                candidate_segments = [
                    (mid, y1),
                    (mid, y2),
                    (x2, y2)
                ]

            path_points = [(x1, y1)] + candidate_segments + [(x2, y2)]
            overlap_penalty = self._count_path_overlaps(path_points)
            obstacle_penalty = self._detect_obstacles_on_path(
                connector.source_name,
                connector.target_name,
                path_points
            )
            score = overlap_penalty * 1000 + obstacle_penalty * 10 + abs(track_idx)

            if score < best_score:
                best_score = score
                best_segments = candidate_segments

            if overlap_penalty == 0 and obstacle_penalty == 0 and track_idx == 0:
                break

        return best_segments
    
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
        """Route orthogonal connectors: Only horizontal or vertical lines with right angles.
        
        Strategy:
        1. FIRST: Check if connection points are already aligned (grid-snapped objects)
           - If Y coordinates match → direct horizontal line
           - If X coordinates match → direct vertical line
        2. ONLY IF NOT ALIGNED: Create V-H-V or H-V-H multi-segment paths
           - CONSTRAINED by source_edge: if exits from top/bottom, must use V-H-V
           - If exits from left/right, must use H-V-H
        
        This ensures grid-aligned objects use direct routing without unnecessary bends.
        """
        x1, y1 = connector.source_x, connector.source_y
        x2, y2 = connector.target_x, connector.target_y
        
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        
        # STEP 1: Check if connection points are already aligned (grid-snapped)
        # Allow tolerance for floating point precision and connection point offset
        # Tolerance increases with larger deltas to allow "nearly aligned" connectors
        if dy < 1:
            # Y coordinates are aligned → use direct HORIZONTAL line
            connector.path_type = "direct"
            return
        
        # For vertical alignment: allow offset up to ~5px when dy is large (>50px)
        # This accounts for connection points not being at exact same x within the box center
        if dx < 5 and dy > 50:
            # X coordinates are effectively aligned → use direct VERTICAL line
            connector.path_type = "direct"
            return
            
        if dx < 1:
            # X coordinates are precisely aligned → use direct VERTICAL line
            connector.path_type = "direct"
            return
        
        # STEP 2: Connection points NOT aligned - create multi-segment routing
        if dx < 10 and dy < 10:
            # Source and target are very close - just use direct diagonal
            connector.path_type = "direct"
        else:
            # CONSTRAIN routing by exit edge
            src_edge = connector.source_edge
            
            # If exiting from top/bottom, MUST use V-H-V routing (vertical first)
            if src_edge in ['top', 'bottom']:
                connector.segments = self._choose_best_orthogonal_segments(connector, 'vhv')
            # If exiting from left/right, MUST use H-V-H routing (horizontal first)
            elif src_edge in ['left', 'right']:
                connector.segments = self._choose_best_orthogonal_segments(connector, 'hvh')
            else:
                # Fallback: use coordinate-based routing
                if dx < dy:
                    connector.segments = self._choose_best_orthogonal_segments(connector, 'vhv')
                else:
                    connector.segments = self._choose_best_orthogonal_segments(connector, 'hvh')
            connector.path_type = "multi_segment"
    
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
