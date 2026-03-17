import sys
sys.path.insert(0, 'Scripts')
from parser import parse_csv

model = parse_csv('Process/02_Architecture/class_diagrams.csv')
diagram = [d for d in model.class_diagrams if d.diagram_id == 'DataModelRelationships'][0]

print("All relationships from FunctionDef:")
print("-" * 60)
func_rels = [r for r in diagram.relationships if r.source == 'FunctionDef']
for i, rel in enumerate(func_rels):
    print(f"{i}: FunctionDef -> {rel.target}: {rel.arrow}")

CONNECTOR_SPACING = 15
if len(func_rels) > 1:
    print(f"\nMultiple connectors ({len(func_rels)}), so offsets will be applied:")
    for i, rel in enumerate(func_rels):
        offset = (i - (len(func_rels) - 1) / 2) * CONNECTOR_SPACING
        print(f"  Rel {i} to {rel.target}: offset = ({i} - {(len(func_rels)-1)/2}) * 15 = {offset:.1f}")
else:
    print(f"\nSingle connector, offset = 0")
