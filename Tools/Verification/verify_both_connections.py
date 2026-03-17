import re

with open('test_class_diagram_fixed.svg', 'r') as f:
    content = f.read()

print("FunctionDef outgoing connections verification:")
print("=" * 70)
print("FunctionDef box: x=40-161.6, y=322-459 (center at 100.8, 390.5)")
print("  Expected bottom edge for connections: y=459")
print()

# Find all lines with diamond-filled marker-start (connections FROM a box)
lines = re.findall(r'<line[^/]*marker-start="url\(#diamond-filled\)"[^/]*/>', content)

print(f"Found {len(lines)} lines with source diamond markers")
print()

# Track connections from FunctionDef
print("Checking FunctionDef source connections:")
print("-" * 70)

for i, line in enumerate(lines):
    y1_match = re.search(r'y1="([^"]+)"', line)
    y2_match = re.search(r'y2="([^"]+)"', line)
    x1_match = re.search(r'x1="([^"]+)"', line)
    x2_match = re.search(r'x2="([^"]+)"', line)
    
    if y1_match and y2_match and x1_match and x2_match:
        y1 = float(y1_match.group(1))
        y2 = float(y2_match.group(1))
        x1 = float(x1_match.group(1))
        x2 = float(x2_match.group(1))
        
        # Check if starts from FunctionDef (x around 100.8)
        if abs(x1 - 100.8) < 2:
            # Determine target
            if x2 > 600:  # ParamDef is to the right
                target = f"ParamDef at ({x2:.0f}, {y2:.0f})"
            else:
                target = f"Unknown at ({x2:.0f}, {y2:.0f})"
            
            status = "✓" if abs(y1 - 459) < 1 else "✗"
            print(f"{status} Connection to {target}")
            print(f"    Start: ({x1:.1f}, {y1:.1f})")
            if abs(y1 - 459) > 0.1:
                print(f"    ERROR: Y should be 459.0, got {y1:.1f}")
            else:
                print(f"    OK: Diamond touches FunctionDef at bottom edge")
            print()
