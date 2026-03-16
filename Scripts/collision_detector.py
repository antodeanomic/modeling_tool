"""Collision detection and staggering for class diagram connectors.

Detects line crossings and adjusts box positions to eliminate them.
"""

from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import math


@dataclass
class LineSegment:
    """Represents a line segment from (x1,y1) to (x2,y2)."""
    x1: float
    y1: float
    x2: float
    y2: float
    connector_id: str  # For tracking which connector this segment belongs to


@dataclass
class Crossing:
    """Represents a crossing between two line segments."""
    seg1_id: str
    seg2_id: str
    intersection_x: float
    intersection_y: float
    t1: float  # Parameter along seg1 (0-1)
    t2: float  # Parameter along seg2 (0-1)


class CollisionDetector:
    """Detects line crossings in connector layouts."""
    
    def __init__(self):
        self.crossings: List[Crossing] = []
    
    def detect_crossings(self, connector_paths: List) -> List[Crossing]:
        """Detect all line crossings in the connector layout.
        
        Args:
            connector_paths: List of ConnectorPath objects with segments defined
            
        Returns:
            List of Crossing objects representing intersections
        """
        self.crossings = []
        
        # Build list of all line segments
        segments = []
        for i, connector in enumerate(connector_paths):
            if not connector.source_point_idx or not connector.target_point_idx:
                continue  # Skip unassigned connectors
            
            segs = self._get_connector_segments(connector, str(i))
            segments.extend(segs)
        
        # Check all pairs of segments for crossings
        for i in range(len(segments)):
            for j in range(i + 1, len(segments)):
                seg1 = segments[i]
                seg2 = segments[j]
                
                # Skip segments from the same connector (they can touch)
                if seg1.connector_id == seg2.connector_id:
                    continue
                
                crossing = self._check_segment_crossing(seg1, seg2)
                if crossing:
                    self.crossings.append(crossing)
        
        return self.crossings
    
    def _get_connector_segments(self, connector, connector_id: str) -> List[LineSegment]:
        """Extract all line segments from a connector path."""
        segments = []
        
        if connector.path_type == "direct":
            # Single segment from source to target
            seg = LineSegment(
                x1=connector.source_x,
                y1=connector.source_y,
                x2=connector.target_x,
                y2=connector.target_y,
                connector_id=connector_id
            )
            segments.append(seg)
        else:  # multi_segment
            # Multiple segments defined in connector.segments
            if connector.segments:
                # Start from source
                sx, sy = connector.source_x, connector.source_y
                
                for tx, ty in connector.segments:
                    seg = LineSegment(x1=sx, y1=sy, x2=tx, y2=ty, connector_id=connector_id)
                    segments.append(seg)
                    sx, sy = tx, ty
                
                # Last segment to target
                seg = LineSegment(x1=sx, y1=sy, x2=connector.target_x, y2=connector.target_y, 
                                connector_id=connector_id)
                segments.append(seg)
        
        return segments
    
    def _check_segment_crossing(self, seg1: LineSegment, seg2: LineSegment) -> Optional[Crossing]:
        """Check if two line segments cross.
        
        Returns Crossing object if they intersect, None otherwise.
        Uses parametric line intersection algorithm.
        """
        # Using parametric form: P = P1 + t * (P2 - P1)
        # seg1: P = (x1,y1) + t * (x2-x1, y2-y1), t in [0,1]
        # seg2: Q = (x3,y3) + s * (x4-x3, y4-y3), s in [0,1]
        
        x1, y1 = seg1.x1, seg1.y1
        x2, y2 = seg1.x2, seg1.y2
        x3, y3 = seg2.x1, seg2.y1
        x4, y4 = seg2.x2, seg2.y2
        
        denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        
        # Check if lines are parallel
        if abs(denom) < 1e-10:
            return None
        
        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
        s = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom
        
        # Check if intersection is within both segments (excluding endpoints)
        if 0.01 < t < 0.99 and 0.01 < s < 0.99:  # Small margin to ignore touching endpoints
            # Calculate intersection point
            ix = x1 + t * (x2 - x1)
            iy = y1 + t * (y2 - y1)
            
            return Crossing(
                seg1_id=seg1.connector_id,
                seg2_id=seg2.connector_id,
                intersection_x=ix,
                intersection_y=iy,
                t1=t,
                t2=s
            )
        
        return None


class StaggeringStrategy:
    """Strategies for adjusting box positions to eliminate crossings."""
    
    @staticmethod
    def minimum_box_separation(crossings: List[Crossing], 
                               boxes: Dict[str, Dict],
                               min_distance: float = 30) -> Dict[str, Tuple[float, float]]:
        """Suggest box position adjustments to resolve crossings.
        
        Simple strategy: For each crossing, identify which box to move and
        calculate minimum adjustment to separate the lines.
        
        Args:
            crossings: List of detected line crossings
            boxes: Dict of box_name -> {x, y, width, height}
            min_distance: Minimum distance to maintain between crossing lines
            
        Returns:
            Dict of box_name -> (delta_x, delta_y) adjustments
        """
        adjustments = {}
        
        for crossing in crossings:
            # For now, simple strategy: move one box away from crossing
            # Future: implement more sophisticated collision resolution
            pass
        
        return adjustments
