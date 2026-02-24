from parser import parse_csv
from svg_renderer import render_svg

def test_verbosity():
    model = parse_csv("sample_model.csv")
    seq = model.get_sequence("SoftReq0001")

    # Test all three verbosity levels
    for level in ["Low", "Normal", "High"]:
        svg = render_svg(model, seq, verbosity_level=level)
        filename = f"diagram_{level.lower()}.svg"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(svg)
        
        print(f"Generated {filename} with {level} verbosity")
        
        # Show a sample of the content to verify what was generated
        # Extract and display the arrow labels
        lines = svg.split('\n')
        for i, line in enumerate(lines):
            if '<text' in line and 'font-size="12"' in line:
                print(f"  Arrow label: {line.strip()}")

if __name__ == "__main__":
    test_verbosity()
