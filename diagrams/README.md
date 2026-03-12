# Hierarchical Diagram Organization

This folder contains diagrams organized in a hierarchical structure. The folder names and naming conventions determine how diagrams are displayed in the menu.

## Structure

The system automatically discovers CSV files in this folder and preserves the folder hierarchy when displaying diagrams in the menu.

### Folder Naming Convention

Use numeric prefixes to control the sort order:

```
01_CategoryName/
  10_SubCategory/
    10_Item/
    20_Item/
  20_SubCategory/
30_Category/
```

- **Numeric Prefix**: `01_`, `10_`, `20_`, etc. control sort order (lower numbers first)
- **Names**: Underscores are converted to spaces in the menu display
- **Hierarchy**: Each folder level becomes a breadcrumb in the menu

## Example Structure

```
diagrams/
├── 01_SystemArchitecture/
│   ├── 10_Packages/
│   │   └── example_pkg.csv
│   ├── 20_Components/
│   │   ├── 10_Interfaces/
│   │   │   └── interface_example.csv
│   │   ├── 20_Ports/
│   │   │   └── port_example.csv
│   │   └── 30_CompositeStructures/
│   │       └── composite_example.csv
│   └── 30_Classes/
│       ├── 10_Attributes/
│       │   └── attributes_example.csv
│       ├── 20_Methods/
│       │   └── methods_example.csv
│       └── 30_Relationships/
│           └── relationships_example.csv
```

## Display Format

In the diagram menu, items will be displayed as:

```
SEQUENCE DIAGRAMS
  System Architecture > Packages
    example_pkg
  System Architecture > Components > Interfaces
    interface_example
  System Architecture > Components > Ports
    port_example
  System Architecture > Components > Composite Structures
    composite_example
  System Architecture > Classes > Attributes
    attributes_example
  System Architecture > Classes > Methods
    methods_example
  System Architecture > Classes > Relationships
    relationships_example
```

The indentation visually shows the nesting level, and the breadcrumb shows the full path.

## Creating New Diagrams

1. Create a folder structure under `diagrams/` following the naming convention
2. Place your CSV files in the appropriate subfolder
3. The system will automatically discover and display them on next refresh
4. No configuration needed - structure is automatically detected!

## Backward Compatibility

CSV files in the traditional locations (`Source/`, `Test/tests/`, `Process/architecture/`) will still be discovered and displayed, but they won't have hierarchy information.
