"""
Grid Coordinate System for Class Diagrams

Provides grid-based coordinate tracking and collision detection.
Based on 2x2 character grid blocks (16x32 pixels per block).
"""

class GridCoordinateSystem:
    """Converts SVG coordinates to grid coordinates based on 2x2 character blocks."""
    
    # Grid block dimensions (pixels)
    # Monospace character: ~8px wide, 16px tall
    # 2x2 char block: 16px wide, 32px tall
    GRID_BLOCK_WIDTH = 16    # pixels
    GRID_BLOCK_HEIGHT = 32   # pixels
    
    def __init__(self, margin=20):
        """Initialize grid system with canvas margin."""
        self.margin = margin
    
    def svg_to_grid(self, x, y):
        """Convert SVG pixel coordinates to grid coordinates.
        
        Args:
            x, y: SVG pixel coordinates
            
        Returns:
            (grid_x, grid_y): Grid cell coordinates (0-indexed, as integers)
        """
        grid_x = int((x - self.margin) // self.GRID_BLOCK_WIDTH)
        grid_y = int((y - self.margin) // self.GRID_BLOCK_HEIGHT)
        return (max(0, grid_x), max(0, grid_y))
    
    def grid_to_svg(self, grid_x, grid_y):
        """Convert grid coordinates back to SVG pixel coordinates.
        
        Args:
            grid_x, grid_y: Grid cell coordinates
            
        Returns:
            (x, y): SVG pixel coordinates (top-left corner of grid cell)
        """
        x = self.margin + grid_x * self.GRID_BLOCK_WIDTH
        y = self.margin + grid_y * self.GRID_BLOCK_HEIGHT
        return (x, y)
    
    def get_object_grid_bounds(self, x, y, width, height):
        """Get grid cells occupied by an object.
        
        Args:
            x, y: Top-left corner in SVG coordinates
            width, height: Object dimensions in pixels
            
        Returns:
            GridBounds: Object containing grid cell range
        """
        top_left_grid = self.svg_to_grid(x, y)
        bottom_right_grid = self.svg_to_grid(x + width - 1, y + height - 1)
        
        return GridBounds(
            grid_x1=top_left_grid[0],
            grid_y1=top_left_grid[1],
            grid_x2=bottom_right_grid[0],
            grid_y2=bottom_right_grid[1],
            x=x,
            y=y,
            width=width,
            height=height
        )


class GridBounds:
    """Represents grid cell bounds occupied by an object."""
    
    def __init__(self, grid_x1, grid_y1, grid_x2, grid_y2, x, y, width, height):
        self.grid_x1 = grid_x1  # Min grid x
        self.grid_y1 = grid_y1  # Min grid y
        self.grid_x2 = grid_x2  # Max grid x
        self.grid_y2 = grid_y2  # Max grid y
        
        # SVG coordinates for reference
        self.x = x
        self.y = y
        self.width = width
        self.height = height
    
    @property
    def grid_cells(self):
        """List all grid cells occupied by this object."""
        cells = []
        for gy in range(int(self.grid_y1), int(self.grid_y2) + 1):
            for gx in range(int(self.grid_x1), int(self.grid_x2) + 1):
                cells.append((gx, gy))
        return cells
    
    def overlaps_with(self, other):
        """Check if this bounds overlaps with another."""
        if self.grid_x2 < other.grid_x1 or self.grid_x1 > other.grid_x2:
            return False
        if self.grid_y2 < other.grid_y1 or self.grid_y1 > other.grid_y2:
            return False
        return True
    
    def __repr__(self):
        return f"GridBounds(({self.grid_x1},{self.grid_y1}) to ({self.grid_x2},{self.grid_y2}))"


class GridUsageMap:
    """Tracks usage of grid cells and detects conflicts."""
    
    def __init__(self):
        """Initialize grid usage map."""
        self.grid = {}  # (grid_x, grid_y) -> list of occupants
    
    def mark_used(self, object_name, bounds, object_type="box"):
        """Mark grid cells as used by an object.
        
        Args:
            object_name: Name/ID of object
            bounds: GridBounds object
            object_type: Type of object ("box", "connector_h", "connector_v", "connector_d")
        """
        for cell in bounds.grid_cells:
            if cell not in self.grid:
                self.grid[cell] = []
            self.grid[cell].append({
                'name': object_name,
                'type': object_type,
                'bounds': bounds
            })
    
    def get_cell_usage(self, grid_x, grid_y):
        """Get list of objects occupying a grid cell.
        
        Args:
            grid_x, grid_y: Grid coordinates
            
        Returns:
            List of occupants at this cell
        """
        return self.grid.get((grid_x, grid_y), [])
    
    def check_conflicts(self):
        """Check for invalid overlaps.
        
        Returns:
            List of conflicts: each conflict is (cell, occupants, error_message)
        """
        conflicts = []
        
        for cell, occupants in self.grid.items():
            if len(occupants) <= 1:
                continue  # No conflict
            
            # Check if all occupants are perpendicular connectors
            has_box = any(occ['type'] == 'box' for occ in occupants)
            has_h_connector = any(occ['type'] == 'connector_h' for occ in occupants)
            has_v_connector = any(occ['type'] == 'connector_v' for occ in occupants)
            has_diagonal = any(occ['type'] == 'connector_d' for occ in occupants)
            
            # Rules:
            # 1. Box conflicts with anything
            # 2. Horizontal connector conflicts with other horizontal or diagonal
            # 3. Vertical connector conflicts with other vertical or diagonal
            # 4. Diagonal connector conflicts with anything except perpendicular
            
            error = None
            
            if has_box and len(occupants) > 1:
                error = "Box overlaps with other object(s)"
            elif has_diagonal and (has_h_connector or has_v_connector or len(occupants) > 1):
                if has_diagonal and len([o for o in occupants if o['type'] == 'connector_d']) > 1:
                    error = "Multiple diagonal connectors in same cell"
                elif has_diagonal and (has_h_connector or has_v_connector):
                    error = "Diagonal connector conflicts with non-perpendicular connector"
            elif has_h_connector and has_h_connector:
                if len([o for o in occupants if o['type'] == 'connector_h']) > 1:
                    error = "Multiple horizontal connectors in same cell (not allowed)"
            elif has_v_connector and has_v_connector:
                if len([o for o in occupants if o['type'] == 'connector_v']) > 1:
                    error = "Multiple vertical connectors in same cell (not allowed)"
            
            # Check perpendicular intersection (allowed)
            if has_h_connector and has_v_connector and len(occupants) == 2:
                error = None  # Perpendicular intersection is OK
            
            if error:
                occupant_names = [occ['name'] for occ in occupants]
                conflicts.append((cell, occupant_names, error))
        
        return conflicts
    
    def get_usage_stats(self):
        """Get statistics about grid usage.
        
        Returns:
            Dict with usage statistics
        """
        total_cells = len(self.grid)
        used_cells = len([c for c in self.grid.values() if c])
        boxes = sum(1 for occupants in self.grid.values() 
                   for occ in occupants if occ['type'] == 'box')
        connectors = sum(1 for occupants in self.grid.values() 
                        for occ in occupants if 'connector' in occ['type'])
        conflicts = len(self.check_conflicts())
        
        return {
            'total_cells': total_cells,
            'used_cells': used_cells,
            'boxes_occupying': boxes,
            'connector_segments': connectors,
            'conflicts': conflicts,
        }
    
    def print_grid_map(self, max_x=None, max_y=None):
        """Print ASCII representation of grid usage.
        
        Args:
            max_x, max_y: Maximum grid coordinates to display
        """
        if not self.grid:
            print("Grid is empty")
            return
        
        # Determine bounds
        all_cells = list(self.grid.keys())
        if not all_cells:
            return
        
        actual_max_x = max(c[0] for c in all_cells)
        actual_max_y = max(c[1] for c in all_cells)
        
        max_x = min(max_x or actual_max_x, actual_max_x)
        max_y = min(max_y or actual_max_y, actual_max_y)
        
        print("\nGrid Usage Map:")
        print("Legend: . = empty | B = box | - = horiz connector | | = vert connector | X = conflict")
        print()
        
        for y in range(max_y + 1):
            row = ""
            for x in range(max_x + 1):
                cell = (x, y)
                occupants = self.grid.get(cell, [])
                
                if not occupants:
                    row += ". "
                elif len(occupants) > 1:
                    row += "X "  # Conflict
                else:
                    occ_type = occupants[0]['type']
                    if occ_type == 'box':
                        row += "B "
                    elif occ_type == 'connector_h':
                        row += "- "
                    elif occ_type == 'connector_v':
                        row += "| "
                    elif occ_type == 'connector_d':
                        row += "D "
                    else:
                        row += "? "
            
            print(f"Row {y:2d}:  {row}")


class GridAnalyzer:
    """Analyzes diagram layouts for grid-based correctness."""
    
    def __init__(self, margin=20):
        """Initialize analyzer.
        
        Args:
            margin: Canvas margin in pixels
        """
        self.coord_system = GridCoordinateSystem(margin)
        self.usage_map = GridUsageMap()
    
    def analyze_diagram(self, positions, diagram_name=""):
        """Analyze class positions and track grid usage.
        
        Args:
            positions: Dict of class_name -> {x, y, width, height, ...}
            diagram_name: Optional name for this diagram
            
        Returns:
            Dict with analysis results
        """
        if diagram_name:
            print(f"\n{'='*70}")
            print(f"Grid Analysis: {diagram_name}")
            print(f"{'='*70}")
        
        # Analyze each object
        for class_name, pos in positions.items():
            bounds = self.coord_system.get_object_grid_bounds(
                pos['x'], pos['y'], pos['width'], pos['height']
            )
            self.usage_map.mark_used(class_name, bounds, "box")
            
            # Print object location
            grid_x, grid_y = self.coord_system.svg_to_grid(pos['x'], pos['y'])
            print(f"  {class_name:20s} @ Grid({grid_x:2d},{grid_y:2d}) "
                  f"  SVG({pos['x']:6.1f},{pos['y']:6.1f}) "
                  f"  Size({pos['width']:4.1f}x{pos['height']:4.1f})")
        
        # Check for conflicts
        conflicts = self.usage_map.check_conflicts()
        stats = self.usage_map.get_usage_stats()
        
        print(f"\nStatistics:")
        print(f"  Total grid cells used: {stats['total_cells']}")
        print(f"  Conflicts detected: {stats['conflicts']}")
        
        if conflicts:
            print(f"\nConflicts Found:")
            for cell, occupants, error_msg in conflicts:
                print(f"  Grid cell {cell}: {' + '.join(occupants)}")
                print(f"    Error: {error_msg}")
        
        return {
            'grid_bounds': {name: self.coord_system.get_object_grid_bounds(
                pos['x'], pos['y'], pos['width'], pos['height']
            ) for name, pos in positions.items()},
            'conflicts': conflicts,
            'stats': stats,
        }


# Example test functions

def test_level_based_layout_grid():
    """Test that level-based layout aligns to grid correctly."""
    from Scripts.model import Model
    from Scripts.class_diagram_renderer import ClassDiagramRenderer
    
    # Load diagram
    model = Model()
    model.load_from_csv('Source/requirements.csv')
    
    if not model.class_diagrams:
        print("No diagrams found")
        return False
    
    diagram = model.class_diagrams[0]
    renderer = ClassDiagramRenderer()
    positions = renderer._layout_classes_tree_based(diagram, model, "High")
    
    # Analyze grid
    analyzer = GridAnalyzer(margin=20)
    results = analyzer.analyze_diagram(positions, diagram.name)
    
    # Show grid map
    analyzer.usage_map.print_grid_map(max_x=30, max_y=15)
    
    # Check results
    if results['conflicts']:
        print(f"\nFAIL: Found {len(results['conflicts'])} conflicts")
        return False
    else:
        print(f"\nPASS: No conflicts detected")
        return True


if __name__ == "__main__":
    test_level_based_layout_grid()
