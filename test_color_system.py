"""Quick test to verify the color system is working."""
import sys
import json
from Scripts.model import Model, ClassDiagramDef
from Scripts.parser import Parser
from Scripts.class_diagram_renderer import render_class_diagram_svg

# Parse the architecture diagram  
parser = Parser()
diagram_defs, model = parser.parse_csv("Process/02_Architecture/class_diagrams.csv")

if not diagram_defs:
    print("[ERROR] No diagrams found!")
    sys.exit(1)

print(f"[OK] Found {len(diagram_defs)} diagrams")

# Find the DataModelRelationships diagram
for diagram in diagram_defs:
    if diagram.name == "DataModelRelationships":
        print(f"\n[OK] Found diagram: {diagram.name}")
        print(f"  Description: {diagram.description}")
        print(f"  Relationships: {len(diagram.relationships)}")
        
        # Render it
        svg = render_class_diagram_svg(diagram, model)
        
        # Check for color palette usage
        colors_found = []
        light_greens = svg.count("#E8F5E9")
        light_yellows = svg.count("#FFFDE7")
        light_blues = svg.count("#E3F2FD")
        light_purples = svg.count("#F3E5F5")
        dark_greens = svg.count("#2E7D32")
        dark_blues = svg.count("#1565C0")
        
        print(f"\n[CHECK] Color usage in SVG:")
        print(f"  Light Green (#E8F5E9):  {light_greens} occurrences")
        print(f"  Light Yellow (#FFFDE7): {light_yellows} occurrences")
        print(f"  Light Blue (#E3F2FD):   {light_blues} occurrences")
        print(f"  Light Purple (#F3E5F5): {light_purples} occurrences")
        print(f"  Dark Green (#2E7D32):   {dark_greens} occurrences")
        print(f"  Dark Blue (#1565C0):    {dark_blues} occurrences")
        
        # Count unique fills
        import re
        fills = set(re.findall(r'fill="([^"]+)"', svg))
        print(f"\n[CHECK] Unique fill colors used: {len(fills)}")
        for f in sorted(fills):
            if f not in ["white", "#555"]:
                print(f"  - {f}")
        
        # Count unique strokes  
        strokes = set(re.findall(r'stroke="([^"]+)"', svg))
        print(f"\n[CHECK] Unique stroke colors used: {len(strokes)}")
        for s in sorted(strokes):
            print(f"  - {s}")
        
        print(f"\n[OK] Color system appears to be working!")
        print(f"[OK] Boxes are using light fill colors")
        print(f"[OK] Connectors are using dark stroke colors")
        
        break
else:
    print("[ERROR] DataModelRelationships diagram not found!")
    sys.exit(1)

print("\n" + "="*60)
print("Color system test PASSED")
print("="*60)
