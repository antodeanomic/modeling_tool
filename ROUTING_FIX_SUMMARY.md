# Routing Logic Bug Fix & Preference Order Implementation

## Issues Fixed

### 1. Runtime Error: "cannot unpack non-iterable float object"
**Root Cause**: Path construction was mixing floats with tuples
```python
# WRONG (caused error):
[connector.source_x, connector.source_y] + connector.segments
# Results in: [float, float, (x,y), (x,y), ...]

# FIXED:
[(connector.source_x, connector.source_y)] + connector.segments
# Results in: [(x,y), (x,y), (x,y), ...]
```

**Impact**: Class diagrams couldn't load. Fixed in commit 3543fba.

---

## Routing Preference Order Implemented

The connector router now prefers simpler paths when possible:

### 1️⃣ Direct Connection (Simplest - Preferred)
- **What**: Single straight line between source and target
- **When**: Always tried first
- **Usage**: Used immediately if obstacle-free
- **Note**: Can be used even if endpoints aren't geometrically aligned

### 2️⃣ 2-Segment Connector (1 bend)
- **What**: Vertical-Horizontal (V-H) or Horizontal-Vertical (H-V) path
- **When**: Direct line has obstacles
- **Testing**: Both V-H and H-V tested, best selected
- **Usage**: Use if clear or better than direct

### 3️⃣ 3-Segment Connector (V-H-V Orthogonal, 2 bends)
- **What**: Standard multi-segment routing: Vertical → Horizontal → Vertical
- **When**: 2-segment paths have too many obstacles
- **Usage**: Compare with 2-segment, keep better option

### 4️⃣ N-Segment Connector (Advanced, 3+ bends)
- **What**: Route around obstacles with left/right offsets
- **Offsets**: ±150px from center path
- **When**: Simpler strategies all blocked
- **Purpose**: Maximize obstacle avoidance

---

## Algorithm

```
for each connector:
    1. Try direct line
       -> if clear: use it and exit
    
    2. Try 2-segment (V-H and H-V)
       -> pick best (fewest obstacles)
       -> if clear or better than direct: use it and exit
    
    3. Try 3-segment V-H-V orthogonal
       -> compare with best 2-segment
       -> keep better option
    
    4. Fallback to best alternative
       -> route left/right of obstacles
       -> use path with fewest obstacles
```

---

## Benefits

✅ **Simpler diagrams**: Fewer unnecessary bends
✅ **Better readability**: Direct connections easier to follow
✅ **Smart avoidance**: Obstacles still avoided when necessary
✅ **Geometric flexibility**: Direct even if not geometrically aligned
✅ **Progressive complexity**: Only adds complexity when needed

---

## Files Changed

- `Scripts/class_diagram_connectors.py`
  - Fixed path construction bug
  - Implemented 4-priority routing strategy
  - Lines: ~405-430 in `_route_connector()` method

- `CONNECTOR_OBSTACLE_AVOIDANCE.md`
  - Updated to document preference order
  - Added strategy descriptions

---

## Testing

✅ All 11 sequence diagram tests: **PASS**
✅ Class diagram loading: **FIXED** (error gone)
✅ Server operational: **YES**
✅ No regressions: **VERIFIED**

---

## Commits

- **3543fba**: Fix routing logic: correct path construction and implement routing preference order
- **7c8fbff**: Update obstacle avoidance documentation to reflect routing preference order
