# Connector Spacing & Text Layout Implementation

## Overview
Complete implementation of connector spacing calculation and text layout for three connector routing scenarios: horizontal, vertical, and multi-segment paths.

## Problem Addressed
Connectors were rendering as multi-segment due to insufficient space to fit connector text and multiplicity labels on single lines. The renderer now:
1. Pre-calculates required spacing based on connector content
2. Adjusts box spacing to fit all elements naturally
3. Positions text appropriately for each connector type

## Changes Made

### 1. Spacing Calculator Function
**Location**: `Scripts/class_diagram_renderer.py`

Added `_calculate_required_spacing(diagram, verbosity)`:
- Analyzes all relationships in a diagram
- Computes minimum horizontal spacing needed for connector elements
- Returns recommended spacing in pixels

**Calculation includes**:
- Arrow/diamond markers: 10px × 2 (start and end)
- Source multiplicity (worst case "1..*"): ~30px
- 2-space gap: ~15px  
- Connector label text: variable width
- 2-space gap: ~15px
- Target multiplicity: ~30px

### 2. Helper Functions
**`_get_segment_type(x1, y1, x2, y2)`**: Determines if segment is horizontal or vertical
**`_place_text_perpendicular()`**: Generates SVG text positioned relative to segment (reserved for future use)

### 3. Updated Layout Function
**Function**: `_layout_classes()`

- Calls `_calculate_required_spacing()` before positioning boxes
- Uses calculated spacing if larger than default
- Formula: `max(required_spacing, CLASS_SPACING_X + verbosity_adjustment)`

**Result**: Boxes automatically spread further when connectors have long text

### 4. Scenario 1: Horizontal Connector Text Placement
**Applies to**: Diagonal routing where Y coordinates are nearly identical (< 2px variation)

Format: Places all elements centered above the line
```
    "source_mult" + "  " + "connector_label" + "  " + "target_mult"
```

Implementation:
- Builds single text string with proper spacing
- Centers entire string above the connector
- Uses monospace font for accurate positioning

### 5. Scenario 2: Vertical Connector Text Placement (Orthogonal Routing)

#### V-H-V Path (needs_horizontal = true)
Three segments with distributed text:
- **Segment 1 (Vertical sy→mid_y)**: Source multiplicity positioned **to the RIGHT** at 30% along segment
- **Segment 2 (Horizontal mid_y)**: Connector label positioned **ABOVE** the line at midpoint
- **Segment 3 (Vertical mid_y→ty)**: Target multiplicity positioned **to the RIGHT** at 70% along segment

Layout visualization:
```
[Box1]
   │ src_mult on right
   ├─────── label above ───────┐
           │ tgt_mult on right
[Box2]
```

#### V-Only Path (needs_horizontal = false)
Single vertical segment with stacked text:
- **25% along**: Source multiplicity to the RIGHT
- **50% along**: Connector label to the RIGHT  
- **75% along**: Target multiplicity to the RIGHT

Layout:
```
[Box1]
 │ src_mult
 │ label
 │ tgt_mult
[Box2]
```

### 6. Scenario 3: Vertical Diagonal Connectors
For nearly-vertical diagonal lines (dy > dx):
- **20% from source**: Source multiplicity to the RIGHT
- **Line midpoint**: Connector label to the RIGHT
- **20% from target**: Target multiplicity to the RIGHT

For more horizontal diagonal lines (dx > dy):
- Uses perpendicular positioning (below the line)
- Source and target multiplicities positioned below line
- Label positioned at midpoint below

## Text Positioning Summary

| Connector Type | Scenario | Multiplicity | Label | Notes |
|---|---|---|---|---|
| Horizontal | 1 | Above line, spaced | Above line | All centered together |
| Vertical V-H-V | 2a | Right of segments | Above middle segment | Distributed across 3 segments |
| Vertical V-only | 2b | Right of segment | Right of segment | All on single vertical line |
| Vertical diagonal | 3 | Right of line | Right of line | Text to right side |
| Horizontal diagonal | 3 | Below line (perp) | Below line (perp) | Perpendicular offset |

## Constants

| Constant | Value | Purpose |
|----------|-------|---------|
| `CONNECTOR_MULTIPLICITY_MAX` | 4 | Worst-case character count for multiplicity |
| `TEXT_SPACING` | 2 | Spaces between connector elements |
| `ARROW_MARKER_WIDTH` | 10 | Approximate width for arrow/diamond markers |
| `CONNECTOR_CHAR_WIDTH` | 7.5 | Character width at 11px monospace font |

## Testing Recommendations

1. **Horizontal Connectors**: 
   - Create diagram with short labels (fits on one line)
   - Verify text centered above connector

2. **Long Labels**:
   - Test with labels > 20 characters
   - Verify spacing_x increases automatically
   - Confirm text doesn't overlap connectors

3. **Multiplicity Variations**:
   - Test "1", "0..*", "1..1", "1..*"
   - Verify correct width calculations

4. **Mixed Scenarios**:
   - Multiple connectors from single source
   - Different routing types (diagonal, orthogonal)
   - Various verbosity levels

## Backward Compatibility

- All existing tests continue to pass
- Changes are purely layout improvements
- No changes to model structure or SVG format
- Verbosity levels still work (Low, Normal, High)

## Future Enhancements

1. **Vertical Connector Text** (as specified):
   - Position multiplicity to the right of vertical segments
   - Handle left-looping scenarios separately

2. **Multi-Segment Text Distribution**:
   - Separate text placement for first, middle, and final segments
   - Optimize text positioning based on segment type

3. **Dynamic Label Positioning**:
   - Detect conflicts with box positions
   - Adjust label placement (above/below or left/right)
   - Support label wrapping for very long text
