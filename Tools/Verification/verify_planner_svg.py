import re

with open('test_class_diagram_planner.svg', 'r') as f:
    content = f.read()

# Count lines and paths
lines = len(re.findall(r'<line ', content))
paths = len(re.findall(r'<path ', content))

print(f'Lines: {lines}')
print(f'Paths: {paths}')
print(f'Total connectors rendered: {lines + paths}')

# Extract FunctionDef connection points
print('\nConnectors starting from FunctionDef (y=459 or nearby):')
for match in re.finditer(r'<line x1="([^"]+)" y1="([^"]+)" x2="([^"]+)" y2="([^"]+)"', content):
    x1, y1, x2, y2 = float(match.group(1)), float(match.group(2)), float(match.group(3)), float(match.group(4))
    # FunctionDef is centered at x=100.8, bottom at y=459
    if abs(y1 - 459) < 1 or (y1 > 450 and y1 < 470 and 40 <= x1 <= 162):
        print(f'  ({x1:.1f}, {y1:.1f}) -> ({x2:.1f}, {y2:.1f})')

print('\nFirst 5 connector lines:')
for i, match in enumerate(re.finditer(r'<line [^/]*/?>', content)):
    if i < 5:
        line = match.group(0)
        # Show simplified version
        if 'y1="459"' in line:
            print(f'  ✓ y1=459.0 (FunctionDef bottom edge)')
        elif len(line) > 100:
            print(f'  {line[:90]}...')
        else:
            print(f'  {line}')
