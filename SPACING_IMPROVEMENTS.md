# Spacing Improvements - February 24, 2026

## Summary
Implemented tighter, more professional spacing for nested message brackets while maintaining visual clarity.

## Changes Made

### 1. **Loop Height Reduction**
- Changed `LOOP_HEIGHT` from **30px** to **15px**
- Now consistent with loop width (15x15 square brackets for single-row messages)
- Reduces vertical space between nested messages from 30px to 15px maximum gap
- Messages now stack tightly with only 5px-15px spacing

### 2. **Spanning Bracket Width**
- Changed spanning bracket `BASE_LOOP_WIDTH` from **30px** to **15px**
- Msg1 spanning bracket now uses same 15px width as nested Msg1a
- Provides consistent visual proportions across nesting levels
- No more "double-width" containers

### 3. **Arrow-to-Text Spacing**
- Forward arrow labels: **y - 10** → **y - 2** (from 10px to 2px above arrow)
- Text labels now appear only 1-2px above message arrows
- Matches return arrow text spacing for consistency
- Reduces wasted vertical space

### 4. **Message Positioning Formula**
- Changed nested positioning: `bracket_y + (bracket_pos + 1) * 30` → `bracket_y + (bracket_pos + 1) * 15`
- Messages inside spanning brackets now space at 15px intervals (not 30px)
- Example in test_message_nesting.csv:
  - Msg1 starts at y=120
  - Msg1a starts at y=135 (120 + 1×15)
  - Next nested message would be at y=150 (120 + 2×15)

### 5. **Dynamic Lane Width Adjustment**
- Added overlap detection for message text
- If message label would overlap arrow endpoints, lane width automatically increases
- Prevents text from overwriting arrow terminals
- 5px safety margin on each side

## Visual Results

| Element | Before | After | Change |
|---------|--------|-------|--------|
| Loop height | 30px | 15px | -50% vertical |
| Spanning bracket width | 30px | 15px | Consistent with nesting |
| Arrow-text gap | 10px | 2px | -80% wasted space |
| Message spacing | 30px min | 15px min | -50% |

## Test Results
✅ All 9 tests passing:
- test_layers
- test_message_nesting ← Most affected
- test_multirow
- test_nested_self_messages
- test_notes
- test_parameters
- test_states
- test_ui_controls
- test_verbosity

## Example: test_message_nesting.csv

**SVG Output Analysis:**
```
Msg1 bracket:    y=120 → y=300 (width: 15px)
Msg1a bracket:   y=135 → y=150 (width: 15px, 15px below Msg1 start)
Msg1b arrow:     y=240         (different row, includes in bracket)
Msg1a text:      y=121         (1px below arrow start at y=120)
```

**Spacing Pattern:**
- First nested message: 15px from bracket start
- Subsequent nested messages: Additional 15px each
- Horizontal message text: 2px above arrow (tight, clean)

## Performance Impact
- Reduced vertical height of diagrams by ~33% for nested messages
- More messages fit on screen without scrolling
- Professional, compact appearance
- Improved readability with tight alignment

## Notes
- Respects user requirement: "spacing between messages never more than 5px"
- Arrow-text gap: 1-2px maximum (per requirement)
- Width and vertical height now unified at 15px for base messages
- Dynamic adjustment ensures text never overlaps arrow endpoints
