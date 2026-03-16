# Right-Angle Connector Text Layout Implementation Plan

## Phase 1: Analysis & Pre-calculation (RIGHT ANGLE - ORTHOGONAL)

### Goal
Calculate the layout requirements for all relationships from each source box before rendering.

### Steps
1. **Group relationships by source** - Bundle all relationships exiting from the same source box
2. **Calculate vertical spacing** - Determine Y-offset for each connector (distribute vertically)
3. **Calculate horizontal extension** - How far right should each horizontal segment extend?
4. **Text positioning** - Place multiplicity and labels at mid-point of horizontal segment
5. **Box size adjustment** - May need to expand source/target boxes to accommodate text

### Key Data Structures
```python
class ConnectorGroup:
    source_box: str
    relationships: List[ClassRelationship]
    vertical_positions: Dict[rel_id -> y_offset]
    horizontal_widths: Dict[rel_id -> width_needed]
```

---

## Phase 2: Basic Right-Angle Implementation

### Current Orthogonal Logic (lines ~410-440 in class_diagram_renderer.py)
- Single mid-point X calculation: `mid_x = (sx + tx) / 2`
- Single multiplicity Y: `sy + 12` and `ty + 12`
- Simple label positioning at midpoint

### New Orthogonal Logic
For each relationship in a group:

1. **Exit point** from source → vertical segment starting position
   - Use different Y for each connector from same source
   - Stack vertically with gaps between

2. **Horizontal segment** 
   - From exit point to some mid-point X
   - Width varies based on text length (label + multiplicity)
   - Minimum: 40 characters

3. **Entry point** to target
   - Different Y for each incoming connector
   - Stack vertically to target

4. **Text positioning**
   - Multiplicity: positioned on vertical segment (left side)
   - Label: positioned on horizontal segment (above the line)
   - 2-space gap between multiplicity and label

---

## Phase 3: Test & Validate

### Test File
`Test/tests/test_multiconnector_rightangle.csv` - 11 symmetrical connectors from CentralHub

### Validation Criteria
✓ All 11 connectors render without overlapping text
✓ Text readable (no clipping)
✓ Proper spacing between multiplicity and labels
✓ Consistent vertical stacking
✓ Symmetric layout (if applicable)

---

## Implementation Order

1. **Modify `_layout_classes()`** - Add relationship analysis phase
2. **Modify `_get_connection_points()`** - Account for multi-connector spacing
3. **Modify `_render_relationship()`** - Implement new orthogonal text layout
4. **Test with `test_multiconnector_rightangle.csv`**
5. **Debug & refine spacing**

---

## Known Challenges

1. **Connection point calculation** - Multiple connectors from same box need different Y values
2. **Text wrapping** - Must wrap at 40 chars, maintain 4-space alignment for wrapped lines
3. **Dynamic box sizing** - Source box may need to be taller if many connectors
4. **Gap calculation** - 2-space gap between multiplicity and label, 4-space alignment for wraps
5. **Symmetric layout** - Currently no notion of "left" vs "right" connectors

---

## Success Metrics

- [  ] Commits with working orthogonal multi-connector layout
- [  ] Test diagram renders without errors
- [  ] All 11 connectors visible with readable text
- [  ] Proper spacing between text elements
- [  ] Can switch to diagonal mode for comparison
