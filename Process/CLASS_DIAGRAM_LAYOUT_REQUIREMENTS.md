# Class Diagram Layout Requirements

**Document Status**: Foundational constraints discovered during implementation (Session: Grid Cell Alignment)

## 0. Current Policy Addendum (2026-04)

The current implementation applies the following additional policy constraints:

1. Class-diagram routing is orthogonal-only in production behavior.
2. Domain-layer heavy diagrams may use larger initial vertical spacing to reduce connector overlap pressure.
3. Connector text placement may trade perfect geometric centering for readability via occupancy-aware nudging.
4. Viewer hover interaction highlights related connectors/text using SVG metadata on objects/connectors.

This addendum supersedes older assumptions that multiple class-diagram routing modes remain active in production.

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
1. Orthogonal routing must preserve vertical alignment
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

## 7. Fanout (Mode 2 Only) Requirements

**Requirement IDs**: ClassRouting_0005, ClassRouting_0006, ClassRouting_0007, ClassRouting_0009, ClassRouting_0010, ClassRouting_0011, Rendering_0022, Rendering_0023

When multiple connectors leave the same source object from the same side, routing must use **fanout mode** only (Mode 2). Shared-trunk behavior is not allowed.

### 7.1 Allowed Strategy

1. **Mode 2 fanout only**:
   - Distinct source start slots on the source edge
   - One connector per start slot
   - Independent first segments before bends
2. **Mode 1 shared trunk is disallowed**.

### 7.2 Four-Perspective Coverage (Top/Bottom/Left/Right)

Fanout must be explicitly defined for all four source sides:

1. **Top fanout**: branches leave from top slots.
2. **Bottom fanout**: mirrored equivalent of top fanout.
3. **Left fanout**: branches leave from left-wall side points.
4. **Right fanout**: mirrored equivalent of left fanout.

The ASCII reference in `Process/02_Architecture/20_Components/20_Renderer/FanoutExample.txt` is normative for lane intent and side-point alignment.

### 7.3 Mandatory Connector Order (per fanout branch)

Each branch must follow this order:

1. `Object`
2. `ConnectStartPoint` (unique slot on source edge)
3. `Multiplicity` text on first segment
4. `First segment` (orientation depends on side)
5. `Connector label (CXX)` before bend on first segment
6. `Right-angle bend`
7. `Horizontal segment` toward target

### 7.4 First-Segment Orientation Rules

1. **Top/Bottom fanout**:
   - First segment is **vertical**.
   - Multiplicity and connector label are placed on this vertical segment before bend.
2. **Left/Right fanout**:
   - First segment is **horizontal** from aligned `+` side points on CentralHub.
   - Multiplicity and connector label are placed on this horizontal segment before bend.
3. **Direct connectors**:
   - Direct connectors are always **perpendicular to the source object side**.
   - For top/bottom fanout this means direct connectors are vertical.
   - For left/right fanout this means direct connectors are horizontal.

### 7.5 Direct Connector Priority

1. Direct connectors (`T_dir`, `B_dir`, `L_dir`, `R_dir`) are prioritized ahead of non-direct fanout branches.
2. This direct-connector priority applies even if pure distance ordering would place them elsewhere.
3. Direct connectors occupy the center slots for the active fanout side when that side includes designated direct targets.
4. For top/bottom fanout groups that do not include an explicit designated direct target, routing may infer one natural direct branch from a target that is already center-aligned with the source, or otherwise from the connector whose target center is closest to the source center.
5. An inferred natural direct branch must still remain perpendicular to the source side and use the center slot for that fanout side.

### 7.6 Symmetry Rules

Fanout must preserve mirror behavior:

1. **Top vs Bottom**: mirrored lane order and spacing behavior.
2. **Left vs Right**: mirrored lane order and spacing behavior.

For equivalent target distributions, mirrored pairs must remain visually symmetric in lane ordering and spacing behavior.

### 7.7 Side-Point Capacity and Alignment

1. Connection points are spaced at the grid rule of **2 characters per point**.
2. For left/right fanout with many branches, CentralHub vertical walls must be lengthened to provide additional side points.
3. Left/right fanout branches must align on the side-wall `+` connection-point column.
4. Naming in ASCII requirement examples is normalized to uppercase directional labels: `T_*`, `B_*`, `L_*`, `R_*`.

### 7.8 Visibility and Readability Constraints

1. Fanout must be **visibly obvious** (not micro-offset).
2. Adjacent fanout lanes must have distinct bend depths.
3. Multiplicity and connector text on first segments must not overlap each other.
4. Connector text placement must be before bend, not at endpoint.

### 7.9 Acceptance Criteria

A class-diagram fanout group passes only when all are true:

1. At least two connectors from same source side use different start slots.
2. Each branch has a visible right-angle bend after vertical-leg text.
3. Multiplicity appears on first segment according to side orientation rules.
4. Connector label appears on first segment before bend.
5. Top-edge and bottom-edge fanout groups both render correctly when present.
6. Left-edge and right-edge fanout groups both render correctly when present.
7. Left/right branches start horizontally from aligned side `+` points.
8. Direct connectors remain perpendicular to the source object side.
9. Direct connectors preserve center-slot priority when present in the active fanout group.

### 7.10 Non-Fanout Rejection Criteria (Do Not Accept)

The following patterns are explicitly invalid and must be rejected as non-fanout:

1. Multiple connectors leaving the same side but sharing one trunk segment.
2. Connectors that differ only by tiny offsets while visually appearing as one line.
3. Connector text placed only at horizontal endpoints with no vertical-leg text band.
4. Multiplicity not placed on the first segment leaving the source edge.
5. Branches without a visible right-angle bend after first-segment text placement.
6. Mixed branch ordering where farther targets are routed before direct connectors without a collision-avoidance reason.
7. Left/right fanout branches that begin vertical instead of horizontal.
8. Left/right fanout branches that do not originate from aligned side `+` points.
9. Direct connectors that are not perpendicular to the source object side.

### 7.11 Clarification Note: Why Prior Examples Were Incorrect

Earlier draft examples that looked like stacked/near-overlapping lines were not valid fanout because they violated one or more of: distinct lane visibility, first-segment text placement, and bend-before-horizontal branch structure.

This document is authoritative: examples that do not satisfy Sections 7.2 through 7.6 are non-compliant.

---

## References

- [Scripts/class_diagram_renderer.py](../../Scripts/class_diagram_renderer.py) - Layout engine
- [Scripts/class_diagram_connectors.py](../../Scripts/class_diagram_connectors.py) - Grid + connection points
- Conversation Session: Grid Cell Alignment (latest)
