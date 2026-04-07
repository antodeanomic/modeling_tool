# Class Diagram Layout Requirements

**Document Status**: Foundational constraints discovered during implementation (Session: Grid Cell Alignment)

## 0. Current Policy Addendum (2026-04)

The current implementation applies the following additional policy constraints:

1. Class-diagram routing is orthogonal-only in production behavior.
2. Domain-layer heavy diagrams may use larger initial vertical spacing to reduce connector overlap pressure.
3. Connector text placement may trade perfect geometric centering for readability via occupancy-aware nudging.
4. Viewer hover interaction highlights related connectors/text using SVG metadata on objects/connectors.

This addendum supersedes older assumptions that diagonal and orthogonal modes are equally active for class-diagram readability tuning.

---

## 1. Fixed 20px × 20px Grid Cell Rule

**Requirement ID**: Structure_0007

Every object's grid must use fixed-size square cells sized at **20 pixels × 20 pixels**.
Each cell represents **2 monospace characters** horizontally and one line vertically.

### Constraint Equations
```
Box Width (px) = 20 × Number of Columns (must be integer)
Box Height (px) = 20 × Number of Rows (must be integer)
```

### Rationale
- Ensures all connection points align naturally when objects are vertically stacked
- Eliminates fractional connection point coordinates that cause misalignment
- Standardizes geometry across all diagram objects

### Verification
All objects in the diagram must satisfy:
- `W / Cols = 20.0` (no decimal places)
- `H / Rows = 20.0` (no decimal places)

---

## 2. Top-Left Anchored Tree-View Layout

**Requirement ID**: Structure_0008

Class diagram layout must use **top-left anchoring** with hierarchical tree-view positioning (not centered).

### Constraints
1. **Root object** positioned at `(40px, 40px)` (top-left + margin)
2. **Parent-child relationships** arranged vertically (children below parents)
3. **Horizontal alignment** within hierarchy levels via left-anchor spacing
4. **Never center** objects in the diagram

### Rationale
- Tree-view format naturally represents class hierarchies and ownership relationships
- Top-left anchoring provides predictable, consistent positioning
- Simplifies connector alignment when all objects are vertically stacked
- Makes diagram layout independent of container size (responsive-friendly)

---

## 3. Hierarchy Connector Alignment

**Requirement ID**: Structure_0009

Connectors between hierarchically-related objects (Model→ClassDef→FunctionDef) must be **vertically aligned at matching X coordinates**.

### Constraints
1. Both diagonal and orthogonal routing modes must preserve vertical alignment
2. Connectors use **non-corner grid cells** for exit/entry points:
   - Avoid grid index 1 (top-left corner area)
   - Avoid grid index N (top-right corner area)  
   - Avoid grid index M×1 (bottom-left corner area)
   - Avoid grid index M×N (bottom-right corner area)
3. For vertical connectors (same source X, different Y):
   - Match X coordinate of connected objects for natural alignment

### Implementation
Source point (bottom edge) and target point (top edge) must have same X coordinate within layout constraints to achieve vertical alignment.

### Rationale
- Prevents visual ambiguity about which objects are connected to which
- Vertical alignment is a UML convention for hierarchy display
- Clear visual flow improves diagram readability

---

## 4. Connection Point Grid Derivation

**Requirement ID**: Implicit (constraint on connection point math)

Connection points around each box must be derived from fixed grid:

### Calculation
```python
# Horizontal points on top/bottom edges
num_horizontal = max(3, round(box_width / 20))
horizontal_spacing = 20  # pixels

# Vertical points on left/right edges  
num_vertical = max(3, round(box_height / 20))
vertical_spacing = 20  # pixels

# Point coordinates (0-indexed from edge)
point_x = box_x + (index - 1) * 20
point_y = box_y + (index - 1) * 20
```

### Rationale
- Grid point count is deterministic, not arbitrary
- Point spacing is uniform and predictable
- Allows connection points to match naturally between adjacent objects

---

## 5. Legacy Confusion: Centered Layout (DEPRECATED)

**Status**: REMOVED (caused misalignment issues)

Old approach attempted to center parent objects over child groups. This was abandoned because:
1. Created fractional connection point X coordinates
2. Made hierarchy connector alignment impossible
3. Conflicted with grid cell sizing rule

**Current approach**: Left-anchor all objects with hierarchical vertical stacking.

---

## 6. Legacy Confusion: Arbitrary Grid Points (DEPRECATED)

**Status**: REMOVED (replaced with fixed cell math)

Old approach:
- Used fixed 7-column grid for all boxes (regardless of content size)
- Calculated point indices using proportional spacing
- Result: Connection points at `x = left + (i/num_points) * width`

**Problems**:
- Different sized boxes had different point horizontal spacing
- Point X coordinates were fractional, causing misalignment
- Width snapping wasn't consistent

**Current approach**: 
- Grid columns derived from `width / 20`
- Point coordinates calculated as `left + (i-1) * 20` (fixed 20px steps)
- All boxes satisfy `W/Cols = 20.0` exactly

---

## Testing & Validation

All class diagrams must pass validation:

```python
# Pseudocode validation
for each_object in diagram:
    cols = box_width / 20
    rows = box_height / 20
    assert cols == int(cols), f"Width {box_width} not divisible by 20"
    assert rows == int(rows), f"Height {box_height} not divisible by 20"
    
for each_hierarchy_connector in diagram:
    source_x = connector.source_point.x
    target_x = connector.target_point.x
    assert abs(source_x - target_x) < 5, "Hierarchy connectors must be vertically aligned"
```

---

## References

- [Scripts/class_diagram_renderer.py](../../Scripts/class_diagram_renderer.py) - Layout engine
- [Scripts/class_diagram_connectors.py](../../Scripts/class_diagram_connectors.py) - Grid + connection points
- Conversation Session: Grid Cell Alignment (latest)
