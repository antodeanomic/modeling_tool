from parser import parse_csv
from svg_renderer import render_svg

def main():
    model = parse_csv("Source/sample_model.csv")
    seq = model.get_sequence("SoftReq0001")

    svg = render_svg(model, seq, verbosity_level="High")

    with open("Process/diagram.svg", "w", encoding="utf-8") as f:
        f.write(svg)

    print("SVG diagram generated: Process/diagram.svg")

if __name__ == "__main__":
    main()