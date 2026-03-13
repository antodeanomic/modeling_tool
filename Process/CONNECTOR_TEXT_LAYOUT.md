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

## Orthogonal (Right-Angle) Connectors

_To be documented - pending requirements from user_

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
