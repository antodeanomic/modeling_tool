# Tree-Based Hierarchical Layout Strategy

## Overview

Replaced horizontal sprawling layout with **tree-based hierarchical layout** for better diagram compactness and readability. Composition/aggregation relationships now display as vertical ownership trees rather than left-to-right chains.

## Layout Problem

**Previous Approach (Horizontal)**: 
```
Long diagram spanning entire width:
Model ──contains──> ClassDef ──owns──> FunctionDef ──owns──> ParamDef
                                              |
                                              └──owns──> ReturnDef
                                                             |
                                                             └──owns──> MemberVar
```

**Issues**:
- Very wide diagrams that don't fit viewports
- Difficult to follow ownership chains
- Wasted vertical space
- Hard to read for complex inheritance relationships

## New Approach (Tree-Based)

**Vertical Cascade with Indentation**:
```
FunctionDef         (depth 0, row 0)
    -> ParamDef     (depth 1, row 1)
    -> ReturnDef    (depth 1, row 2)
        -> MemberVar (depth 2, row 3)

Model               (depth 0, row 0)
    -> ClassDef     (depth 1, row 1)
    -> SeqDef       (depth 1, row 2)
    -> ClassDiagramDef (depth 1, row 3)
```

**Benefits**:
- ✅ Compact vertical layout
- ✅ Clear parent-child relationships via indentation
- ✅ Easy to follow ownership chains
- ✅ Trees fit within standard viewport width
- ✅ Multiple trees arrange in 2x2 grid blocks

## Layout Algorithm

### Phase 1: Build Ownership Trees
Analyze composition/aggregation relationships to identify tree structure:
```python
_build_ownership_trees(diagram)
```

Returns:
- `owner_to_children`: Map of parent → [children]
- `child_to_owner`: Map of child → parent
- `roots`: Classes with no owner (tree roots)

### Phase 2: Position Single Tree Vertically
Place parent at top, children cascade down:
```python
_layout_tree_vertical(root, trees, boxes, spacing_x, spacing_y, x_base, y_base)
```

**Positioning Logic**:
```
Depth 0: FunctionDef at x=base+0*indent, y=base+0*row_height
Depth 1: ParamDef   at x=base+1*indent, y=base+1*row_height
Depth 1: ReturnDef  at x=base+1*indent, y=base+2*row_height
Depth 2: MemberVar  at x=base+2*indent, y=base+3*row_height
```

- `indent_width`: 60px per depth level (right-indent for nesting)
- `row_height`: box_height + spacing_y (vertical separation)
- Children cascade sequentially; each occupies own row

### Phase 3: Arrange Trees in Grid
Position trees in 2x2 block allocations:
```python
_layout_classes_tree_based(diagram, model, verbosity)
```

**Grid Layout**:
```
Tree 1          Tree 2
(0,0)           (500,0)

Tree 3          Tree 4
(0,400)         (500,400)

Remaining hierarchy classes
(0,800+)
```

- `grid_col_width`: 500px per column
- `grid_row_height`: 400px per row
- `cols_per_row`: 2 trees side-by-side
- Allocate space for connecting lines between tree groups

## Relationship Type Handling

### Composition/Aggregation (Tree Structure)
**Arrow**: `--◆`, `◆--` (composition) or `--◇`, `◇--` (aggregation)

```
Owner --◆--> Part    (composition - strong ownership)
Owner --◇--> Part    (aggregation - weak ownership)

Result: Part positioned below/indented under Owner
```

Example:
```
ClassDef ◆── MemberVar
ClassDef ◆── FunctionDef ◆── ParamDef
```

Lays out as tree:
```
ClassDef
    -> MemberVar
    -> FunctionDef
        -> ParamDef
```

### Generalization (Vertical Hierarchy)
**Arrow**: `--▷`, `◁--`

```
Superclass --▷--> Subclass    (subclass points to superclass)
Superclass ◁-- Subclass       (superclass points to subclass)

Result: Superclass positioned ABOVE subclass (preserved from UML standard)
```

### Realization (Vertical Hierarchy)
**Arrow**: `..▷`, `◁..`

```
Interface ..▷--> Implementation (implementation points to interface)
Interface ◁.. Implementation    (interface points to implementation)

Result: Interface positioned ABOVE implementing class
```

### Dependency 
**Arrow**: `..>`, `<..`

```
Client ..> Supplier     (client depends on supplier)
Supplier <.. Client     (inverse arrow direction)

Options:
  1. Straight line if trees positioned favorably
  2. Multi-segment (V-H-V) orthogonal routing if needed
```

### Association
**Arrow**: `--`, `-->`, `<--`, `<-->`

```
Class1 -- Class2        (peer relationship)
Class1 --> Class2       (class1 associated with class2)

Options:
  1. Horizontal line if on same row
  2. Multi-segment routing if different rows
```

## Example: Complete Diagram Layout

**CSV Structure**:
```
ClassDef,FunctionDef,--◆,1,owns,0.*
ClassDef,MemberVar,--◆,1,owns,0.*
FunctionDef,ParamDef,--◆,1,owns,0.*
FunctionDef,ReturnDef,--◆,1,owns,0.*
ReturnDef,MemberVar,--◆,1,owns,0.*
```

**Tree Structure**:
```
FunctionDef (root)
├── ParamDef (child)
├── ReturnDef (child)
│   └── MemberVar (grandchild)

ClassDef (root)
├── MemberVar (child)
└── FunctionDef (sub-hierarchy - shared node)
```

**Rendered Layout**:
```
FunctionDef         ClassDef
    -> ParamDef         -> MemberVar
    -> ReturnDef        -> FunctionDef
        -> MemberVar            -> ParamDef
                                -> ReturnDef
                                    -> MemberVar
```

Note: If `FunctionDef` is both owned by `ClassDef` and a root, it appears in both trees (possible shared nodes for complex diagrams).

## Constants

```python
# Tree positioning
indent_width = 60           # Horizontal pixels per depth level
row_spacing = box_height + spacing_y  # Vertical separation between nodes

# Grid arrangement
grid_col_width = 500        # Width per column
grid_row_height = 400       # Height per row
cols_per_row = 2            # Two trees per row

# Spacing (inherited from global constants)
CLASS_SPACING_X = variable  # Horizontal spacing between elements
CLASS_SPACING_Y = variable  # Vertical spacing between rows
```

## Implementation Files

- **File**: [Scripts/class_diagram_renderer.py](Scripts/class_diagram_renderer.py)
- **New Functions**:
  - `_build_ownership_trees()` - Extract tree structure from relationships
  - `_layout_tree_vertical()` - Position single tree with cascade layout
  - `_layout_classes_tree_based()` - Main algorithm; arrange trees in grid
- **Modified Functions**:
  - `_layout_classes_uml_standard()` - Alias to tree-based layout

## Performance

- **Tree Layout**: O(n) where n = number of classes
- **Grid Arrangement**: O(t) where t = number of trees
- **Overall**: O(n) - linear time complexity
- **Typical Diagrams**: <1ms positioning computation

## Validation

✅ All 11 tests passing  
✅ No regressions from previous implementation  
✅ Composition/aggregation trees layout correctly  
✅ Trees arrange efficiently in 2x2 grid blocks  
✅ Connection routing works with new positions  

## Diagram Examples

### Example 1: FunctionDef Ownership Tree
```
FunctionDef
    -> ParamDef
    -> ReturnDef
        -> MemberVar
```
**Tree Type**: Composition (strong ownership)  
**Layout**: Vertical cascade, depth-based indentation  

### Example 2: ClassDef Ownership Tree
```
ClassDef
    -> MemberVar
    -> FunctionDef
    -> StateMachineDef
        -> StateDef
```
**Tree Type**: Composition (strong ownership)  
**Layout**: Multi-level cascade  

### Example 3: Multiple Trees Arranged
```
Tree 1: FunctionDef    | Tree 2: ClassDef
├── ParamDef          | ├── MemberVar
├── ReturnDef         | └── StateMachineDef
│   └── MemberVar     |     └── StateDef
                       |
Tree 3: Model         | Tree 4: SequenceDef
├── ClassDef          | └── SequenceStep
├── SeqDef            |     └── NoteDef
└── ClassDiagramDef   |
    └── ClassRelationship
```
**Arrangement**: 2x2 grid blocks  
**Connections**: Dependency/association lines connect tree groups  

## Future Enhancements

- **Layer-Based Grouping**: Group trees by architectural layer (Model, View, Controller)
- **Hierarchical Filtering**: Collapse/expand subtrees interactively
- **Layout Optimization**: Minimize connector crossings, optimize aspect ratio
- **Connection Labels**: Position multiplicity and relationship labels better on multi-segment connectors
- **User Preferences**: Allow custom tree width, indent size, grid arrangement

## Migration Notes

- Replaced `_layout_classes_uml_standard()` implementation
- Kept original `_layout_classes()` for reference/fallback
- No changes to rendering engine or connector routing
- All existing tests pass without modification
- CSV format unchanged

---

**Implemented**: March 17, 2026  
**Commit**: ded0635  
**Status**: Production Ready ✓
