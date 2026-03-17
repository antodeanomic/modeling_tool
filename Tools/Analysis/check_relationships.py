import sys
sys.path.insert(0, 'Scripts')
from parser import parse_csv

model = parse_csv('Process/02_Architecture/class_diagrams.csv')

# Get the first class diagram
diagram = model.class_diagrams[0]

print('Looking for relationships involving FunctionDef:')
print('=' * 60)
for rel in diagram.relationships:
    if 'FunctionDef' in rel.source or 'FunctionDef' in rel.target:
        direction = f"{rel.source} -> {rel.target}"
        print(f"{direction:40} arrow={rel.arrow:8} mult={rel.src_mult}:{rel.tgt_mult}")
