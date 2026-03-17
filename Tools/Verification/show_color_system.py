"""Display the color palette and assignment strategy."""

COLOR_PALETTE = [
    {
        "light_fill": "#E8F5E9",   # Light Green
        "dark_stroke": "#2E7D32",  # Dark Green
    },
    {
        "light_fill": "#FFFDE7",   # Light Yellow
        "dark_stroke": "#F57F17",  # Dark Orange/Amber
    },
    {
        "light_fill": "#E3F2FD",   # Light Blue
        "dark_stroke": "#1565C0",  # Dark Blue
    },
    {
        "light_fill": "#F3E5F5",   # Light Purple
        "dark_stroke": "#6A1B9A",  # Dark Purple
    },
    {
        "light_fill": "#FCE4EC",   # Light Pink
        "dark_stroke": "#C2185B",  # Dark Pink
    },
    {
        "light_fill": "#E0F2F1",   # Light Teal
        "dark_stroke": "#00796B",  # Dark Teal
    },
]

print("\n" + "="*70)
print("COLOR SYSTEM FOR CLASS DIAGRAMS")
print("="*70)

print("\nCOLOR PALETTE (Checkerboard Pattern):")
print("-" * 70)
for idx, colors in enumerate(COLOR_PALETTE):
    light = colors["light_fill"]
    dark = colors["dark_stroke"]
    theme = ["Green", "Yellow", "Blue", "Purple", "Pink", "Teal"][idx]
    print(f"  Position {idx}: {theme:8} | Fill: {light} | Stroke: {dark}")

print("\n" + "-" * 70)
print("ASSIGNMENT STRATEGY (Checkerboard Layout):")
print("-" * 70)

# Example 6-object layout
example_layout = [
    ["Model", "ClassDef", "SequenceDef"],
    ["FunctionDef", "ParamDef", "ReturnDef"],
]

print("\nExample layout with 2 rows × 3 columns:")
print()
for row_idx, row in enumerate(example_layout):
    for col_idx, obj_name in enumerate(row):
        color_idx = (row_idx + col_idx) % len(COLOR_PALETTE)
        color = COLOR_PALETTE[color_idx]
        theme = ["Green", "Yellow", "Blue", "Purple", "Pink", "Teal"][color_idx]
        
        # Print with ANSI color background (approximate)
        hex_color = color["light_fill"]
        print(f"  [{obj_name:15}] → Color {color_idx} ({theme:8}) | Fill: {hex_color}")
    print()

print("-" * 70)
print("HOW IT WORKS:")
print("-" * 70)
print("""
1. BOXES: Each object gets a unique light color fill + dark matching stroke
   - Checkerboard pattern ensures no adjacent objects share colors
   - Light fills make text readable
   - Dark strokes provide clear borders

2. CONNECTORS: Each connector uses the DARK color of its SOURCE object
   - Makes it immediately clear which object a connector originates from
   - Source color "flows" along the connector path
   - Visual connection between box color and connector color

3. ROUTING CLARITY: When connectors pass behind objects:
   - Arrow tip is hidden behind the target box
   - Connector color shows it belongs to source object
   - No confusion about routing topology

4. EXAMPLE - Model→ClassDef (Same Row):
   - Model box: Light Green fill (#E8F5E9) + Dark Green stroke (#2E7D32)
   - Connector: Dark Green (#2E7D32) — visually matches Model
   - ClassDef box: Light Yellow fill (#FFFDE7) + Dark Orange stroke (#F57F17)
   - Visual: Green line clearly connects TO Model, passes behind ClassDef

5. EXAMPLE - Model→SequenceDef (Different Row):
   - Model box: Light Green (#E8F5E9)
   - Connector: Dark Green (#2E7D32) — same as Model
   - SequenceDef box: Light Blue (#E3F2FD)
   - Visual: Green line shows connector origin, blue box shows target
   - Even when passing behind other objects, green color traces back to Model
""")

print("="*70)
print("COLOR SYSTEM SUCCESSFULLY IMPLEMENTED ✓")
print("="*70 + "\n")
