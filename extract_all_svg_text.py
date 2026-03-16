#!/usr/bin/env python3
"""Extract ALL SVG text elements to see complete picture."""

import sys
import re
sys.path.insert(0, 'Scripts')

from parser import parse_csv
from class_diagram_renderer import render_class_diagram_svg

def extract_all_text_with_coords(diagram_id, csv_path):
    """Extract all text elements with their x,y coordinates."""
    
    model = parse_csv(csv_path)
    
    # Find the diagram
    diagram = None
    for d in model.class_diagrams:
        if d.diagram_id == diagram_id:
            diagram = d
            break
    
    if not diagram:
        print(f"Diagram {diagram_id} not found")
        return []
    
    # Render it
    svg_content = render_class_diagram_svg(model, diagram, verbosity_level="High")
    
    # Extract all <text> elements with coordinates
    text_elements = []
    
    # Pattern to match <text> tags - more robust parsing
    # Look for x="..." y="..." patterns specifically
    pattern = r'<text[^>]*?x="([^"]+?)"[^>]*?y="([^"]+?)"[^>]*?>([^<]+?)</text>'
    matches = re.findall(pattern, svg_content)
    
    for x, y, text in matches:
        try:
            text_elements.append({'x': float(x), 'y': float(y), 'text': text})
        except ValueError:
            pass  # Skip if x or y couldn't be converted to float
    
    return text_elements

def main():
    csv_path = "Process/02_Architecture/class_diagrams.csv"
    diagram_id = "DataModelRelationships"
    
    print(f"Extracting ALL text elements from {diagram_id}...")
    print("=" * 120)
    
    text_elements = extract_all_text_with_coords(diagram_id, csv_path)
    
    # Filter to connection text (exclude title and class names)
    # Title will be around the top, class names will be inside boxes
    connector_text = [t for t in text_elements if t['y'] > 100 and len(t['text']) < 50]
    
    print(f"\n{'X':<10} {'Y':<10} {'Text':<40} {'Type':<20}")
    print("-" * 120)
    
    for elem in sorted(connector_text, key=lambda e: (e['y'], e['x'])):
        # Classify the text
        if elem['text'] in ['1', '0.*', '1.*', '0..1']:
            text_type = "Multiplicity"
        elif elem['text'] in ['owns', 'contains', 'parses', 'produces', 'reads', 'uses', 'loads', 'orchestrates', 'function_note']:
            text_type = "Label"
        elif elem['text'] in ['Model', 'ClassDef', 'FunctionDef', 'ParamDef', 'ReturnDef', 
                             'StateMachineDef', 'StateDef', 'SequenceDef', 'SequenceStep', 'NoteDef',
                             'ClassDiagramDef', 'ClassRelationship', 'CsvParser', 'SvgRenderer',
                             'DiagramHandler', 'WebServer', 'TestRunner', 'TestSuiteRunner',
                             'MainEntryPoint', 'InteractiveUiGenerator']:
            text_type = "Class Name"
        else:
            text_type = "Other"
        
        print(f"{elem['x']:<10.1f} {elem['y']:<10.1f} {elem['text']:<40} {text_type:<20}")
    
    print("\n" + "=" * 120)
    print(f"Total text elements: {len(text_elements)}")
    print(f"Connector/label elements: {len(connector_text)}")
    print()
    print("OBSERVATION:")
    print("If multiplicity and label are SEPARATE text elements on the same y-coordinate,")
    print("they are being rendered as individual elements (OLD WAY).")
    print()
    print("If they are grouped together as ONE text element with proper spacing,")
    print("they are using the proper formatted approach (NEW WAY).")

if __name__ == "__main__":
    main()
