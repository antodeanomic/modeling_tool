#!/usr/bin/env python3
"""Generate JSON representation of model for interactive UI."""

import json
from parser import parse_csv
from svg_renderer import render_svg

def generate_ui_data():
    """Generate model data and SVG strings as JSON."""
    model = parse_csv("sample_model.csv")
    seq = model.get_sequence("SoftReq0001")
    
    if not seq:
        raise ValueError("Sequence SoftReq0001 not found")
    
    lanes = seq.get_lanes()
    
    # Generate SVGs for all verbosity levels
    svg_data = {}
    for verbosity in ["Low", "Normal", "High"]:
        svg_data[verbosity] = {}
        # All lanes
        svg_data[verbosity]["all"] = render_svg(model, seq, verbosity_level=verbosity)
        # Individual subsets (combinations would be too many, so we just pre-generate common ones)
        for lane in lanes:
            svg_data[verbosity][lane] = render_svg(model, seq, verbosity_level=verbosity, lanes_filter=[lane])
    
    ui_data = {
        "lanes": lanes,
        "verbosity_levels": ["Low", "Normal", "High"],
        "default_verbosity": "High",
        "svg_data": svg_data
    }
    
    with open("ui_data.json", "w", encoding="utf-8") as f:
        json.dump(ui_data, f, indent=2)
    
    print("Generated ui_data.json")

if __name__ == "__main__":
    generate_ui_data()
