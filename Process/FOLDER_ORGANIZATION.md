# Folder Organization for Diagrams

This document describes how diagram files should be organized in the Process directory for proper discovery and display in the diagram menu.

## Folder Naming Convention

Use numeric prefixes to control the sort order. The system automatically discovers CSV files and preserves the folder hierarchy when displaying diagrams in the menu.

### Format

```
01_CategoryName/
  10_SubCategory/
    10_Item/
    20_Item/
  20_SubCategory/
30_Category/
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
│   ├── sequence_user_login.csv
│   ├── sequence_data_pipeline.csv
│   ├── system_structure.csv
│   └── 40_Tests/
│       ├── 10_Basic/
│       │   ├── test_notes.csv
│       │   ├── test_message_nesting.csv
│       │   ├── test_nested_self_messages.csv
│       │   └── ... (more basic tests)
│       └── 20_Advanced/
│           ├── test_comprehensive_nesting.csv
│           ├── test_code_syntax.csv
│           └── ... (more advanced tests)
├── 02_Architecture/
│   ├── sequence_parser_flow.csv
│   ├── architecture_structure.csv
│   ├── 20_Components/
│   │   ├── 10_Parser/
│   │   │   └── csv_parser.csv
│   │   ├── 20_Renderer/
│   │   │   └── svg_renderer.csv
│   │   ├── 30_DataModel/
│   │   │   └── data_model_component.csv
│   │   └── 40_WebServer/
│   │       └── web_server.csv
│   └── 30_Classes/
│       ├── 10_CoreModel/
│       │   └── data_model.csv
│       ├── 20_CoreComponents/
│       │   └── class_diagrams.csv
│       ├── 40_Testing/
│       │   └── test_framework.csv
│       └── 50_Utilities/
│           └── utilities.csv
└── ... (additional directories)
```

## Menu Display

Diagrams are displayed with their folder hierarchy in the diagram picker:

```
System
  sequence_user_login
  sequence_data_pipeline
  system_structure
  40_Tests
    10_Basic
      test_notes
      test_message_nesting
      ... 
    20_Advanced
      test_comprehensive_nesting
      test_code_syntax
      ...
Architecture
  sequence_parser_flow
  architecture_structure
  20_Components
    10_Parser
      csv_parser
    20_Renderer
      svg_renderer
    ...
  30_Classes
    10_CoreModel
      data_model
    ...
```

## Adding New Diagrams

When adding diagrams to the Process directory:

1. Choose the appropriate top-level folder:
   - `01_System` - User-facing interactions and workflows
   - `02_Architecture` - Internal component design and interactions
   - Additional folders can be created with higher numbers (`03_`, `04_`, etc.)

2. Create subdirectories following the numeric prefix convention:
   - Use `10_`, `20_`, `30_`, etc. for category organization
   - Keep related diagrams together in the same subdirectory

3. Place CSV files in the directory structure:
   - Files are automatically discovered at any depth
   - Folder levels create the hierarchy in the menu display

4. Include metadata headers in your CSV files:
   ```csv
   # DiagramType: Sequence | Class
   # Purpose: Brief description
   # Layers: Architectural layers (if applicable)
   
   Type;Name;Description;Layer
   ```

5. Commit with a clear message indicating which section was extended

## Automatic Discovery

The diagram viewer automatically:
- Scans the Process directory recursively for CSV files
- Removes numeric prefixes from folder names for display
- Preserves the folder hierarchy in the menu structure
- Displays diagrams with proper breadcrumb trails

No configuration files or registration needed - the file system structure automatically determines the menu organization.
