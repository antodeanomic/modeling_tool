import sys
sys.path.insert(0, 'Scripts')
from parser import parse_csv
from class_diagram_renderer import (
    _layout_classes, _compute_class_box_size, _get_connection_points,
    render_class_diagram_svg
)

# Parse and get diagram
model = parse_csv('Process/02_Architecture/class_diagrams.csv')
diagram = [d for d in model.class_diagrams if d.diagram_id == 'DataModelRelationships'][0]

# Check FunctionDef and ReturnDef sizing
print("Class Box Sizing:")
print("-" * 60)
for class_name in ['FunctionDef', 'ReturnDef', 'ParamDef']:
    class_def = model.get_class(class_name)
    w, h, has_m, has_f = _compute_class_box_size(class_name, class_def, "High", "class")
    print(f"{class_name:15} Width={w:6.1f}  Height={h:6.1f}  Members={has_m}  Functions={has_f}")
    if class_def:
        print(f"  Members count: {len(class_def.members)}")
        print(f"  Functions count: {len(class_def.functions)}")

# Now check the layout
print("\n\nLayout (before title offset):")
print("-" * 60)
boxes = _layout_classes(diagram, model, "High")
for name in ['FunctionDef', 'ReturnDef', 'ParamDef']:
    if name in boxes:
        box = boxes[name]
        print(f"{name:15} x={box['x']:6.1f}  y={box['y']:6.1f}-{box['y']+box['height']:6.1f}  h={box['height']:6.1f}")

# Apply title offset like the renderer does
title_height = 30
for box in boxes.values():
    box['y'] += title_height

print("\nLayout (after title offset of 30):")
print("-" * 60)
for name in ['FunctionDef', 'ReturnDef', 'ParamDef']:
    if name in boxes:
        box = boxes[name]
        print(f"{name:15} x={box['x']:6.1f}  y={box['y']:6.1f}-{box['y']+box['height']:6.1f}  h={box['height']:6.1f}")

# Now check connection points
print("\n\nConnection Points (FunctionDef to ReturnDef):")
print("-" * 60)
if 'FunctionDef' in boxes and 'ReturnDef' in boxes:
    src_box = boxes['FunctionDef']
    tgt_box = boxes['ReturnDef']
    
    print(f"FunctionDef box: center=({src_box['x']+src_box['width']/2:.1f}, {src_box['y']+src_box['height']/2:.1f})")
    print(f"  y={src_box['y']:.1f}, height={src_box['height']:.1f}, bottom={src_box['y']+src_box['height']:.1f}")
    
    print(f"ReturnDef box: center=({tgt_box['x']+tgt_box['width']/2:.1f}, {tgt_box['y']+tgt_box['height']/2:.1f})")
    print(f"  y={tgt_box['y']:.1f}, height={tgt_box['height']:.1f}")
    
    sx, sy = _get_connection_points(src_box, tgt_box)
    tx, ty = _get_connection_points(tgt_box, src_box)
    
    print(f"\nCalculated connection points:")
    print(f"  From FunctionDef: ({sx:.1f}, {sy:.1f})")
    print(f"  To ReturnDef: ({tx:.1f}, {ty:.1f})")
