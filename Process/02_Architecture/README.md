# Architecture

High-level diagrams showing internal component interactions and design structure.

## Purpose
This directory captures the **internal architecture** of the system. Diagrams here focus on how components interact, their dependencies, and the overall design structure. These are for architects, engineers, and technical teams.

## Contents

### Sequence Diagrams
- **10_Diagrams/sequence_parser_flow.csv** - CSV parsing and SVG rendering showing component interactions

### Structure Diagrams
- **10_Diagrams/architecture_structure.csv** - Package/component dependencies and boundaries
- **10_Diagrams/data_model_relationships.csv** - Data model relationship overview
- **10_Diagrams/parser_to_model.csv** - Parser-to-model dependency view
- **10_Diagrams/renderer_dependencies.csv** - Renderer dependency map
- **10_Diagrams/server_dependencies.csv** - Server dependency map
- **10_Diagrams/test_dependencies.csv** - Test-related dependency map
- **10_Diagrams/utility_dependencies.csv** - Utility dependency map

### Reusable Definitions
Definition CSVs used through `Include` are in `20_Definitions/`:
- `20_Definitions/csv_parser.csv`
- `20_Definitions/data_model.csv`
- `20_Definitions/data_model_component.csv`
- `20_Definitions/svg_renderer.csv`
- `20_Definitions/web_server.csv`
- `20_Definitions/test_framework.csv`
- `20_Definitions/utilities.csv`

## Layer Filtering
Sequence diagrams organize components by architectural layers:
- **User** - External actors
- **UI** - User interface layer
- **API** - API/gateway layer
- **Business Logic** - Core processing components
- **Data Access** - Database and persistence layer

Use the "Display Layers" filter to focus on specific layers or interactions.

## Design Principles
1. Show **component relationships** and **dependencies**
2. Emphasize **architectural layers** and **separation of concerns**
3. Demonstrate **interaction patterns** and **data flow**
4. Document **technical decisions** and **design rationale**
