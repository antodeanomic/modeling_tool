import xml.etree.ElementTree as ET

tree = ET.parse('test_class_diagram.svg')
root = tree.getroot()

ns = {'svg': 'http://www.w3.org/2000/svg'}

# Get class box coordinates
boxes = {}
for rect in root.findall('.//svg:rect[@fill="#FAFAFA"]', ns):
    x = float(rect.get('x', 0))
    y = float(rect.get('y', 0))
    w = float(rect.get('width', 0))
    h = float(rect.get('height', 0))
    # Find the text label for this box
    for text in root.findall('.//svg:text', ns):
        txt_y = float(text.get('y', 0))
        txt_x = float(text.get('x', 0))
        if abs(txt_y - (y + 23)) < 5 and abs(txt_x - (x + w/2)) < 5:
            label = text.text
            boxes[label] = {'x': x, 'y': y, 'w': w, 'h': h, 'bottom': y + h}
            print(f'{label}: x={x:.1f}, y={y:.1f}-{y+h:.1f}, w={w:.1f}')

print("\nLines with diamond markers:")
for line in root.findall('.//svg:line', ns):
    marker_start = line.get('marker-start', '')
    marker_end = line.get('marker-end', '')
    if 'diamond' in marker_start or 'diamond' in marker_end:
        x1 = float(line.get('x1', 0))
        y1 = float(line.get('y1', 0))
        x2 = float(line.get('x2', 0))
        y2 = float(line.get('y2', 0))
        
        # Try to identify source and target boxes
        src = None
        tgt = None
        for name, box in boxes.items():
            if abs(x1 - (box['x'] + box['w']/2)) < 10 and abs(y1 - (box['y'] + box['h']/2)) < 10:
                src = name
            if abs(x2 - (box['x'] + box['w']/2)) < 10 and abs(y2 - (box['y'] + box['h']/2)) < 10:
                tgt = name
        
        marker_info = ""
        if 'diamond-filled' in marker_start:
            marker_info += "◆ at start"
        if 'diamond-filled' in marker_end:
            marker_info += "◆ at end"
        if 'diamond-open' in marker_start:
            marker_info += "◇ at start"
        if 'diamond-open' in marker_end:
            marker_info += "◇ at end"
            
        print(f"  {src} -> {tgt}: ({x1:.1f},{y1:.1f}) to ({x2:.1f},{y2:.1f}) [{marker_info.strip()}]")

print("\nFunctionDef details:")
if 'FunctionDef' in boxes:
    box = boxes['FunctionDef']
    print(f"  Top: y={box['y']}, Bottom: y={box['bottom']}")
    print(f"  Left: x={box['x']}, Right: x={box['x'] + box['w']}")
