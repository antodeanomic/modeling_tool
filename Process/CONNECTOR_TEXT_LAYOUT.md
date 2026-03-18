# Connector Text Layout Requirements

## Diagonal Connectors

### Text Positioning Along Diagonal Line
All text elements are positioned **along or above** the diagonal connector line (from source to target box).

#### Layout Structure (from source to target):
```
[ Source Box ]
        \ S_m              ← Source multiplicity (if High verbosity)
        \                  ← 1 char height gap
         \ Label           ← Connector label text (if present)
          \ more label     ← Wrapped text (if label > 40 chars or has newline)
           \ continued     ← Additional wrapped lines
            \               ← 1 char height gap
             \ T_m          ← Target multiplicity (if High verbosity)
              \             ← 1 char height gap (space for arrowhead)
             [ Target Box ]
```

#### Requirements:
- **Source multiplicity** (S_m): Positioned immediately below where line exits source box
  - Only rendered on "High" verbosity
  - Monospace font for accurate width calculation
  - Offset perpendicular to line to prevent overlap

- **Gap 1**: 1 character height (approximately 11px at 11px font size)

- **Connector label**: Positioned at first gap location
  - Wraps if length > 40 characters
  - Wraps if contains embedded newline (`\n`)
  - Uses standard Arial/Helvetica font (not monospace)
  - Each line positioned 1 character height apart on the diagonal

- **Gap 2**: 1 character height between label and target multiplicity

- **Target multiplicity** (T_m): Positioned after label section
  - Only rendered on "High" verbosity
  - Monospace font
  - Offset perpendicular to line to prevent overlap with arrowhead
  - Further offset (20% along line on diagonal) to avoid arrowhead overlap

- **Gap 3**: 1 character height for arrowhead space (marker size ~10px)

### Text Wrapping Rules
- **Max width per line**: 40 characters
- **Wrap trigger**: Any of:
  - Line length exceeds 40 characters
  - Explicit newline character (`\n`) in label
- **Subsequent lines**: Positioned 1 character height below previous line on diagonal trajectory

### Font Requirements
- **Labels**: Arial, Helvetica, sans-serif (standard font)
- **Multiplicity**: Monospace (for predictable width calculation)
- **Font size**: 11px for both

---

## 2-Segment Connectors  

### Overview
2-segment connectors are simpler than 3-segment (V-H-V) when objects are arranged more compactly. They come in two primary patterns:
- **V-H** (Vertical-Horizontal): Exit source vertically, then horizontal to target
- **H-V** (Horizontal-Vertical): Exit source horizontally, then vertical to target

Text placement depends on available segment length.

### Pattern 1: H-V Path with Long Horizontal Segment

**Condition**: Horizontal segment is long enough (> 40 chars worth of space, ~300px)

**Visual**:
```
Source       S_m  label  T_m
  ├─────────────────────────┐
                            │
                          Target
```

**Text Placement**:
- **Source multiplicity**: LEFT side of horizontal segment, at ~20% along
- **Connector label**: CENTER of horizontal segment
- **Target multiplicity**: RIGHT side of horizontal segment, at ~80% along
- All text positioned ABOVE the horizontal line with 8px vertical offset

**Font & Spacing**:
- Source multiplicity: Monospace, positioned perpendicular to line (left offset)
- Label: Arial, positioned perpendicular to line (above offset)
- Target multiplicity: Monospace, positioned perpendicular to line (right offset)
- Spacing between elements: 2 character widths (~15px with monospace)

### Pattern 2: H-V Path with Short Horizontal Segment

**Condition**: Horizontal segment is short (< 40 chars worth of space, ~300px)

**Visual**:
```
Source
  S_m │
  ├──┤ label
     │
     │     (vertical segment carries text)
     │
     │ T_m
   Target
```

**Text Placement**:
- **Source multiplicity**: LEFT side of short horizontal segment (at start)
- **Connector label**: RIGHT side of vertical segment, at ~40% along vertical
- **Target multiplicity**: RIGHT side of vertical segment, at ~80% along vertical
- Prevent overlap by using perpendicular offset (right side) for vertical segment text

**Font & Spacing**:
- Source multiplicity: On horizontal, monospace, left side
- Label: On vertical, Arial, right side with 8px offset
- Target multiplicity: On vertical, monospace, right side with 8px offset
- Vertical spacing on segment: 2 character heights (~24px) between text elements

### Pattern 3: H-V Path with Both Segments Short

**Condition**: Both horizontal and vertical segments are short (< 20 chars for horizontal, < 2 char heights for vertical)

**Visual**:
```
Source S_m
  │──┤ label
     │
   Target T_m
```

**Text Placement**:
- **Source multiplicity**: LEFT of horizontal segment + RIGHT of vertical segment overlap region
  - Positioned at source box corner, slightly offset (5px left, 0px down)
- **Connector label**: INSIDE the corner region, small offset from intersection
  - Positioned at intersection point, offset right by 8px and up by 5px
- **Target multiplicity**: RIGHT of vertical segment
  - Positioned near target box, right side at ~20% from endpoint

**Font & Spacing**:
- Source multiplicity: Monospace, small (9px if space constrained)
- Label: Minimal Arial, small (9px if space constrained)
- Target multiplicity: Monospace, positioned right of target
- All elements with minimal spacing to fit compact layout

### Pattern 4: V-H Path (Exit Vertically)

**Condition**: Source exits downward (vertical segment first, then horizontal bend)

**Visual**:
```
Source
   │ S_m
   │
   ├─────────────► label
   │
 T_m │
   Target
```

**Text Placement**:
- **Source multiplicity**: RIGHT of vertical segment, at ~25% along
- **Connector label**: ABOVE horizontal segment, at horizontal midpoint
- **Target multiplicity**: RIGHT of vertical segment, at ~75% along
- Text offset perpendicular to segments

---

## Multiplicity Placement Without Endpoints

### Issue Description
When a connector doesn't have endpoint markers (diamond/arrow), the multiplicity text needs to be positioned at the **start and end grid cells** instead of being placed along the middle of the line.

### Current Behavior (INCORRECT)
```
|
│ 1           ← Text in middle (WRONG)
|
│ 1..*        ← Text in middle (WRONG)
|
```

### Required Behavior (CORRECT)
```
| 1           ← Text at start grid cell
│ 
|
│ 
| 1..*        ← Text at end grid cell
```

### Implementation Rules

1. **Detect Endpoint Absence**
   - Check if connector has arrow markers at source or target
   - If either endpoint lacks a marker, apply grid-cell placement

2. **Source Multiplicity Placement**
   - Position in **same grid row** as source box exit point
   - Offset: 1 grid cell width to the LEFT of the connector line
   - Monospace font, right-aligned to connector start

3. **Target Multiplicity Placement**
   - Position in **same grid row** as target box entry point
   - Offset: 1 grid cell width to the LEFT of the connector line
   - Monospace font, right-aligned to connector end

4. **Grid Cell Calculation**
   - Source grid cell: `grid_y = source_box.bottom / GRID_HEIGHT`
   - Target grid cell: `grid_y = target_box.bottom / GRID_HEIGHT`
   - Offset calculations: Use GridCoordinateSystem for consistency

### Example Code Logic

```python
def place_multiplicity_without_endpointer(src_mult, tgt_mult, sx, sy, ty, connector_type):
    """Place multiplicity text at grid cells instead of line midpoint."""
    
    # Grid system constants
    GRID_HEIGHT = 32  # pixels per grid row
    TEXT_OFFSET = 12  # pixels left of connector
    
    if has_arrow_marker(source):
        # Normal placement logic (existing behavior)
        pass
    else:
        # Place at source grid cell (no endpoint)
        src_grid_y = int(sy / GRID_HEIGHT) * GRID_HEIGHT
        src_text_x = sx - TEXT_OFFSET
        src_text_y = src_grid_y + GRID_HEIGHT / 2
        render_text(src_mult, src_text_x, src_text_y)
    
    if has_arrow_marker(target):
        # Normal placement logic (existing behavior)
        pass
    else:
        # Place at target grid cell (no endpoint)
        tgt_grid_y = int(ty / GRID_HEIGHT) * GRID_HEIGHT
        tgt_text_x = tx - TEXT_OFFSET
        tgt_text_y = tgt_grid_y + GRID_HEIGHT / 2
        render_text(tgt_mult, tgt_text_x, tgt_text_y)
```

---

## Orthogonal (Right-Angle, 3-Segment) Connectors

Already fully documented in existing sections. These are V-H-V patterns used when:
- Source and target boxes have horizontal separation (different X coordinates)
- More than 1 grid cell Y-offset between source and target
- Creates 4-segment path for maximum clarity: exit → horizontal bend → vertical → entry

---

## Implementation Notes

### Line Exit Points
**Diagonal connectors** should exit from:
- Source box: **Bottom edge** of the source class box (not side)
- Target box: **Bottom edge** of the target class box entry point

### Perpendicular Offset Calculation
Text positioned perpendicular to connector line:
```python
# For diagonal line from (sx, sy) to (tx, ty):
line_dx = tx - sx
line_dy = ty - sy
line_len = sqrt(line_dx² + line_dy²)

# Perpendicular vector (rotated 90 degrees)
perp_x = -line_dy / line_len
perp_y = line_dx / line_len

# Offset text by 20 pixels perpendicular
label_x = center_x + perp_x * 20
label_y = center_y + perp_y * 20
```

### Verbosity Levels
- **Low**: No multiplicity or labels
- **Normal**: Labels only (no multiplicity)
- **High**: Both multiplicity and labels
