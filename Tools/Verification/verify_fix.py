import re

with open('test_class_diagram_fixed.svg', 'r') as f:
    content = f.read()

# Look for the specific FunctionDef to ReturnDef line
print("Lines connecting FunctionDef (center x=100.8) to ReturnDef:")
print("=" * 70)

# Find FunctionDef box bounds in the SVG
func_match = re.search(r'<rect x="40" y="322" width="121\.6[^"]+" height="137"[^>]*>\s*<text[^>]*>FunctionDef</text>', content)
if func_match:
    print("FunctionDef: y=322 to 459 (bottom edge)")

# Find ReturnDef box bounds
ret_match = re.search(r'<rect x="40" y="524" width="121\.6[^"]+" height="83"[^>]*>\s*<text[^>]*>ReturnDef</text>', content)
if ret_match:
    print("ReturnDef: y=524 to 607 (top edge)")

print("\nConnection lines with diamonds:")
print("-" * 70)

# Extract all line elements
lines = re.findall(r'<line[^/]*/?>', content)
for line in lines:
    # Check if it has diamond marker and involves FunctionDef/ReturnDef area
    if 'diamond' in line and ('100.8' in line or 'marker-start' in line):
        # Try to extract y1 and y2
        y1_match = re.search(r'y1="([^"]+)"', line)
        y2_match = re.search(r'y2="([^"]+)"', line)
        x1_match = re.search(r'x1="([^"]+)"', line)
        x2_match = re.search(r'x2="([^"]+)"', line)
        
        if y1_match and y2_match:
            y1, y2 = float(y1_match.group(1)), float(y2_match.group(1))
            x1, x2 = float(x1_match.group(1)), float(x2_match.group(1))
            
            # Check if it's the FunctionDef to ReturnDef line
            if (abs(y1 - 459) < 20 or abs(y2 - 524) < 20) and abs(x1 - 100.8) < 1:
                print(f"Found FunctionDef->ReturnDef line:")
                print(f"  Start: ({x1:.1f}, {y1:.1f})")
                print(f"  End:   ({x2:.1f}, {y2:.1f})")
                
                # Check the actual y1 value
                if abs(y1 - 459.0) < 0.1:
                    print(f"  ✓ FIXED! Start Y is now 459.0 (touching FunctionDef bottom)")
                elif abs(y1 - 466.5) < 0.1:
                    print(f"  ✗ NOT FIXED! Start Y is still 466.5 (floating)")
                else:
                    print(f"  Start Y is {y1:.1f} (offset={y1-459:.1f})")

print("\nAll FunctionDef diamond-connected lines:")
# Find all lines with diamond that connect from FunctionDef
for line in lines:
    if 'diamond-filled' in line and 'marker-start' in line:
        y1_match = re.search(r'y1="([^"]+)"', line)
        y2_match = re.search(r'y2="([^"]+)"', line)
        x1_match = re.search(r'x1="([^"]+)"', line)
        x2_match = re.search(r'x2="([^"]+)"', line)
        
        if y1_match and y2_match and x1_match and x2_match:
            y1, y2 = float(y1_match.group(1)), float(y2_match.group(1))
            x1, x2 = float(x1_match.group(1)), float(x2_match.group(1))
            
            # Check if starts from FunctionDef area
            if 40 <= x1 <= 161.6 and 322 <= y1 <= 459:
                # Target box info
                if 698 <= x2 <= 820:  # ParamDef area
                    target = "ParamDef"
                elif 40 <= x2 <= 161.6 and 524 <= y2 <= 607:  # ReturnDef area
                    target = "ReturnDef"
                else:
                    target = f"({x2:.0f},{y2:.0f})"
                
                print(f"  FunctionDef -> {target}: y1={y1:.1f} (offset from 459: {y1-459:+.1f})")
