# Connector Spacing Implementation

## Overview
This implementation addresses the issue of connectors becoming multi-segment due to insufficient space to fit connector text and multiplicity labels on horizontal lines.

## Changes Made

### 1. Spacing Calculator Function
**Location**: `Scripts/class_diagram_renderer.py`

Added `_calculate_required_spacing(diagram, verbosity)` which:
- Analyzes all relationships in a diagram
- Calculates total width needed for connector elements on horizontal lines
- Returns recommended minimum horizontal spacing in pixels

**Calculation includes**:
- Arrow/diamond markers: ~10px (start and end)
- Source multiplicity (worst case "1..*"): ~30px
- 2-space gap: ~15px  
- Connector label text: variable width
- 2-space gap: ~15px
- Target multiplicity: ~30px

### 2. Updated Layout Function
**Function**: `_layout_classes()`

Modified to:
- Call `_calculate_required_spacing()` to get required spacing
- Use calculated spacing instead of fixed `CLASS_SPACING_X`
- Formula: `spacing_x = max(required_spacing, CLASS_SPACING_X + verbosity_adjustment)`

**Result**: Horizontal spacing automatically increases when connector text is longer

### 3. Horizontal Connector Text Placement
**Function**: `_render_relationship()` - Diagonal routing section

New logic for horizontal connectors (when `sy ≈ ty`):
- Detects horizontal lines (Y coordinate variation < 2px)
- Builds centered text string: `"source_mult  connector_label  target_mult"`
- Calculates position to center entire text above the line
- Renders as single horizontal text element

**Benefits**:
- All text elements aligned horizontally above the line
- No more individual offsets causing misalignment
- Consistent spacing between elements

### 4. Diagonal Connector Text Placement
For non-horizontal connectors, uses original perpendicular positioning:
- Source multiplicity positioned near source box
- Target multiplicity positioned near target box
- Label positioned at line midpoint

## Layout Examples

### Horizontal Connector (e.g., Model → ClassDef)
```
    diamond + "1..*" + "  " + "defines" + "  " + "1..*" + diamond
    ├─ All elements centered above the line
    ├─ Spacing calculated to ensure no overlap
    └─ Uses monospace font for accurate width
```

### Vertical Connector (Orthogonal Routing)
```
    ╭─ [Box1]
    │
    ├─ source_mult (positioned right of vertical segment)
    │
    ├─ connector_label (positioned on horizontal segment)
    │
    ├─ target_mult (positioned right of vertical segment)
    │
    └─ [Box2]
```

### Multi-Segment Connector (Already Supported)
Text placement on horizontal segment of V-H-V path:
- Multiplicity labels on vertical segments (sides)
- Connector label on horizontal segment (middle)

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
