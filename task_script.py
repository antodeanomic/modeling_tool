import sys
import os
import xml.etree.ElementTree as ET
sys.path.insert(0, "Scripts")
from parser import parse_csv
from class_diagram_renderer import ClassDiagramRenderer

def get_text_bounds(text, x, y, anchor):
    width = len(text) * 8
    if anchor == "middle":
        return (x - width/2, x + width/2)
    elif anchor == "end":
        return (x - width, x)
    return (x, x + width)

def run():
    try:
        model = parse_csv("Process/01_System/system_data_flow.csv")
        # model.class_diagrams should contain the parsed diagrams
        if not model.class_diagrams:
            print("No class diagrams found.")
            return
        diagram = model.class_diagrams[0]
    except Exception as e:
        print(f"Parse error: {e}")
        import traceback
        traceback.print_exc()
        return

    try:
        # Check constructor of ClassDiagramRenderer
        # Assuming it takes (diagram, model) or just (diagram)
        try:
            renderer = ClassDiagramRenderer(diagram, model)
        except TypeError:
            renderer = ClassDiagramRenderer(diagram)
        
        svg_content = renderer.render(routing="orthogonal", verbosity="high")
    except Exception as e:
        print(f"Render error: {e}")
        import traceback
        traceback.print_exc()
        return

    root = ET.fromstring(svg_content)
    ns = {"svg": "http://www.w3.org/2000/svg"}
    
    for g in root.findall(".//svg:g[@data-source]", ns):
        src = g.get("data-source")
        tgt = g.get("data-target")
        
        texts = []
        for t in g.findall(".//svg:text", ns):
            txt = t.text or ""
            tx = float(t.get("x", 0))
            ty = float(t.get("y", 0))
            anchor = t.get("text-anchor", "start")
            bounds = get_text_bounds(txt, tx, ty, anchor)
            texts.append({"text": txt, "x": tx, "y": ty, "anchor": anchor, "bounds": bounds})
        
        if texts:
            print(f"Connector {src}->{tgt}:")
            for t in texts:
                print(f"  x={t['x']}, y={t['y']}, text=\"{t['text']}\", anchor={t['anchor']}")
            
            if (src == "CsvParser" and tgt == "DiagramModel") or (src == "DiagramModel" and tgt == "CsvParser"):
                for i in range(len(texts)):
                    for j in range(i + 1, len(texts)):
                        t1, t2 = texts[i], texts[j]
                        if abs(t1["y"] - t2["y"]) <= 1.5:
                            b1, b2 = t1["bounds"], t2["bounds"]
                            if b1[0] < b2[1] and b2[0] < b1[1]:
                                print(f"  !!! Likely overlap between \"{t1['text']}\" and \"{t2['text']}\" at y={t1['y']}")

run()
