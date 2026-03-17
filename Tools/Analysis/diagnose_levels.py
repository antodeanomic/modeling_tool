#!/usr/bin/env python3
"""Diagnose level-based layout positions."""

import sys
sys.path.insert(0, 'Scripts')

try:
    from model import Model
    from class_diagram_renderer import ClassDiagramRenderer
    
    print("Imported modules successfully")
    
    # Load the model
    model = Model()
    print("Created Model instance")
    model.load_from_csv('Source/requirements.csv')
    print(f"Loaded model with {len(model.dataclasses)} classes")
    
    # Get first class diagram
    diagrams = model.class_diagrams
    print(f"Found {len(diagrams)} class diagrams")
    
    if diagrams:
        diagram = diagrams[0]
        print(f"Diagram: {diagram.name}")
        print(f"Description: {diagram.description}")
        print()
        
        renderer = ClassDiagramRenderer()
        
        # Get level calculations
        levels = renderer._calculate_abstraction_level(diagram)
        print("Abstraction Levels:")
        for cls in sorted(levels.keys(), key=lambda x: levels[x]):
            print(f"  Level {levels[cls]:2d}: {cls}")
        print()
        
        # Get layout positions  
        positions = renderer._layout_classes_tree_based(diagram, model, "High")
        print("Positions (Y coordinate indicates vertical position in SVG):")
        print("(Lower Y = Top of diagram, Higher Y = Bottom of diagram)")
        print()
        sorted_by_y = sorted(positions.items(), key=lambda x: x[1]['y'])
        for cls, pos in sorted_by_y:
            level = levels[cls]
            print(f"  Y={pos['y']:6.1f}  Level {level}  {cls:20s}")
        print()
        
        # Show grouping by level
        print("Layout Visualization (Top to Bottom):")
        for level_num in sorted(set(levels.values())):
            classes_at_level = [c for c, l in levels.items() if l == level_num]
            if classes_at_level:
                y_val = positions[classes_at_level[0]]['y']
                print(f"  Level {level_num} (Y={y_val:.1f}):  {', '.join(classes_at_level)}")
    else:
        print("No diagrams found!")
        
except Exception as e:
    import traceback
    print(f"ERROR: {e}")
    traceback.print_exc()

