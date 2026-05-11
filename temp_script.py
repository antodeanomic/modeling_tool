import sys, xml.etree.ElementTree as ET
sys.path.insert(0, "Scripts")
from parser import parse_csv
from class_diagram_renderer import render_class_diagram_svg
m = parse_csv("Test/tests/test_fanout.csv")
d = next(x for x in m.class_diagrams if x.diagram_id == "FanoutTop")
svg = render_class_diagram_svg(m, d, verbosity_level="High")
root = ET.fromstring(svg)
ns = {"s": "http://www.w3.org/2000/svg"}
rows = []
for g in root.findall(".//s:g[@class='cls-connector']", ns):
    s = g.get("data-source")
    t = g.get("data-target")
    if s != "HubTop": continue
    txt = [( (n.text or "").strip(), float(n.get("x", "0")), float(n.get("y", "0")), n.get("text-anchor", "start"), n.get("font-family", "") ) for n in g.findall("s:text", ns)]
    path_elem = g.find("s:path", ns)
    path_d = path_elem.get("d") if path_elem is not None else ""
    rows.append((t, txt, path_d))
print("COUNT", len(rows))
for t, txt, d in sorted(rows):
    print("TARGET", t)
    print("PATH", d)
    print("TEXT", txt)
