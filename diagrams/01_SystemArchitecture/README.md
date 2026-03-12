# System Architecture Diagrams - Hierarchical Organization

This folder contains all system architecture diagrams organized hierarchically by component and concern.

## Folder Structure

```
01_SystemArchitecture/
├── 10_Packages/                    (High-level application packages)
├── 20_Components/                  (Core system components)
│   ├── 10_Parser/                  (CSV Parser component)
│   │   └── csv_parser.csv
│   ├── 20_Renderer/                (SVG Renderer component)
│   │   └── svg_renderer.csv
│   ├── 30_DataModel/               (Data Model component)
│   │   └── data_model_component.csv
│   └── 40_WebServer/               (Web Server component)
│       └── web_server.csv
│
└── 30_Classes/                     (Detailed class definitions and relationships)
    ├── 10_CoreModel/               (Core data model classes)
    │   └── data_model.csv
    ├── 20_CoreComponents/          (Component-level relationships)
    │   └── class_diagrams.csv
    ├── 30_Infrastructure/          (Infrastructure layers - reserved)
    ├── 40_Testing/                 (Testing framework classes)
    │   └── test_framework.csv
    └── 50_Utilities/               (Utility helper classes)
        └── utilities.csv
```

## Diagram Organization

### Components Folder (`20_Components/`)

Contains class/interface diagrams for individual system components:

- **10_Parser** - CSV parsing engine that reads model definitions
- **20_Renderer** - SVG rendering engine that produces visual diagrams
- **30_DataModel** - Core data structures and domain model
- **40_WebServer** - HTTP server and request handling layer

Each folder represents a distinct architectural component with its own class structure and responsibilities.

### Classes Folder (`30_Classes/`)

Contains class definitions and relationship diagrams organized by concern:

- **10_CoreModel** - The primary data model (Model, ClassDef, SequenceDef, etc.)
- **20_CoreComponents** - Relationship diagrams showing component dependencies
  - `DataModelRelationships` - How data classes relate to each other
  - `ParserToModel` - How parser produces the Model
  - `RendererDependencies` - How renderer consumes the Model
  - `ServerDependencies` - How web server orchestrates components
  - `TestDependencies` - How test framework uses components
  - `UtilityDependencies` - How utilities depend on core components
- **40_Testing** - Test runner and test suite orchestrator classes
- **50_Utilities** - Supporting utilities and helper classes

## How the Hierarchy Works

The numeric prefixes control display order:

| Prefix | Class Order |
|--------|------------|
| `01_` | First |
| `10_` | Second |
| `20_` | Third |
| `30_` | Fourth |
| `40_` | Fifth |
| `50_` | Sixth |

This ensures a logical top-down reading order: System Overview → Components → Core Classes.

## Menu Display Example

When viewing diagrams in the web interface, you'll see:

```
SEQUENCE DIAGRAMS
  (no sequences in architecture diagrams)

CLASS DIAGRAMS
  System Architecture > Packages
    (reserved for future use)
  
  System Architecture > Components > Parser
    csv_parser
  
  System Architecture > Components > Renderer
    svg_renderer
  
  System Architecture > Components > Data Model
    data_model_component
  
  System Architecture > Components > Web Server
    web_server
  
  System Architecture > Classes > Core Model
    data_model
  
  System Architecture > Classes > Core Components
    DataModelRelationships
    ParserToModel
    RendererDependencies
    ServerDependencies
    TestDependencies
    UtilityDependencies
  
  System Architecture > Classes > Testing
    test_framework
  
  System Architecture > Classes > Utilities
    utilities
```

## Include Dependencies

The `class_diagrams.csv` in `20_CoreComponents/` uses Include statements to pull in all component definitions:

```csv
Include;../10_CoreModel/data_model.csv;...
Include;../../../20_Components/10_Parser/csv_parser.csv;...
Include;../../../20_Components/20_Renderer/svg_renderer.csv;...
Include;../../../20_Components/40_WebServer/web_server.csv;...
Include;../40_Testing/test_framework.csv;...
Include;../50_Utilities/utilities.csv;...
```

This creates a comprehensive relationship view of how all components interact.

## Adding New Diagrams

To add a new architecture diagram:

1. **Identify the concern**: Does it belong with Components or Classes?
2. **Choose a folder**: Pick an existing folder or create a new one with a numeric prefix
3. **Name your CSV**: Use a descriptive name (e.g., `performance_metrics.csv`)
4. **Define content**: Add class definitions or relationship diagrams
5. **Menu appears automatically**: The hierarchy folder structure triggers automatic discovery

Example: To add a database schema diagram:
```
diagrams/01_SystemArchitecture/30_Classes/35_DataAccess/
  └── database_schema.csv
```

The menu would show: `System Architecture > Classes > Data Access > database_schema`

## Original Source

These diagrams were reorganized from `Process/architecture/` to use the hierarchical system. The original files remain in Process/ but canonical copies now live here in the diagrams/ folder structure.
