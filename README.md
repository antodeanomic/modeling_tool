modeling_tool/
├── Process/              ← Generated outputs
│   ├── *.svg            (diagram outputs)
│   └── ui_data.json
├── Source/              ← Source data
│   ├── sample_model.csv
│   ├── requirements.csv
│   └── temp.csv
├── Scripts/             ← Core functionality
│   ├── main.py
│   ├── parser.py
│   ├── model.py
│   ├── svg_renderer.py
│   ├── server.py
│   ├── convert_requirements.py
│   ├── generate_test_coverage.py
│   ├── diagram_viewer.html
│   └── interactive_ui.py
├── Test/                ← Test infrastructure
│   ├── tests/           (test CSV files)
│   ├── run_test.py
│   └── test_verbosity.py
└── Documentation
    ├── README.md
    ├── REQUIREMENTS.md
    └── TEST_COVERAGE.md