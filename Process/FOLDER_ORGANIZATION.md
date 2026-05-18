# Folder Organization for Diagrams

This document describes how diagram files should be organized in the Process directory for proper discovery and display in the diagram menu.

## Folder Naming Convention

Use numeric prefixes to control the sort order. The system automatically discovers CSV files and preserves the folder hierarchy when displaying diagrams in the menu.

### Format

```
01_System/
  00_Main/
  10_Diagrams/
  20_Definitions/
02_Architecture/
  10_Diagrams/
  20_Definitions/
03_Design/
  10_Diagrams/
  20_Definitions/
```

### Rules

- **Numeric Prefix**: `01_`, `10_`, `20_`, etc. control sort order (lower numbers first)
- **Folder Names**: Displayed exactly as named (numeric prefix is removed for display)
- **Hierarchy**: Each folder level becomes a breadcrumb in the menu
- **CSV Files**: Placed directly in or within subdirectories, automatically discovered

## Current Structure

```
Process/
├── 01_System/
│   ├── 00_Main/
│   │   └── system_main.csv
│   ├── 10_Diagrams/
│   │   ├── sequence_user_login.csv
│   │   ├── sequence_data_pipeline.csv
│   │   └── system_components.csv
│   ├── 20_Definitions/
│   │   ├── actors.csv
│   │   └── packages.csv
│   └── 40_Tests/
│       ├── 10_Basic/
│       └── 20_Advanced/
├── 02_Architecture/
│   ├── 10_Diagrams/
│   │   ├── architecture_structure.csv
│   │   ├── sequence_parser_flow.csv
│   │   └── *_dependencies.csv and *_to_model.csv
│   └── 20_Definitions/
│       ├── csv_parser.csv
│       ├── data_model.csv
│       ├── svg_renderer.csv
│       ├── web_server.csv
│       ├── test_framework.csv
│       └── utilities.csv
└── 03_Design/
  ├── 10_Diagrams/
  └── 20_Definitions/
```

## Menu Display

Diagram CSV files are displayed with their folder hierarchy in the diagram picker:

```
System
  00_Main
    system_main
  10_Diagrams
    sequence_user_login
    sequence_data_pipeline
    system_components
  40_Tests
    10_Basic
      ...
    20_Advanced
      ...
Architecture
  10_Diagrams
    sequence_parser_flow
    architecture_structure
    parser_to_model
    renderer_dependencies
    server_dependencies
    test_dependencies
    utility_dependencies
    data_model_relationships
  20_Definitions
    csv_parser
    data_model
    ...
```

## Adding New Diagrams

When adding diagrams to the Process directory:

1. Choose the appropriate top-level folder:
   - `01_System` - User-facing interactions and workflows
   - `02_Architecture` - Internal component design and interactions
  - `03_Design` - Detailed design models and reusable definitions
   - Additional folders can be created with higher numbers (`04_`, `05_`, etc.)

2. Use the domain subdirectory convention:
  - `00_Main` (System only) for entrypoint diagrams
  - `10_Diagrams` for composed diagrams
  - `20_Definitions` for reusable Include fragments

3. Place CSV files in the directory structure:
   - Files are automatically discovered at any depth
   - Folder levels create the hierarchy in the menu display

4. Keep CSV style consistent:
  - No leading `#` comment lines
  - Place `Include` lines at top of file
  - Add one blank line between last `Include` and first diagram definition

5. Commit with a clear message indicating which section was extended

## Automatic Discovery

The diagram viewer automatically:
- Scans the Process directory recursively for CSV files
- Removes numeric prefixes from folder names for display
- Preserves the folder hierarchy in the menu structure
- Displays diagrams with proper breadcrumb trails

No configuration files or registration needed - the file system structure automatically determines the menu organization.

## Workspace Hygiene

To keep the repository root focused on durable artifacts:

- Put one-off diagnostic scripts under `Tools/` (or remove them after use).
- Avoid leaving temporary `prove_*.py` scripts in the root directory.
- Keep Process/ and Scripts/ as the primary long-lived documentation/code locations.
