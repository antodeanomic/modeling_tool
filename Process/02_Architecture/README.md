# Architecture

High-level diagrams showing internal component interactions and design structure.

## Purpose
This directory captures the **internal architecture** of the system. Diagrams here focus on how components interact, their dependencies, and the overall design structure. These are for architects, engineers, and technical teams.

## Contents

### Sequence Diagrams
- **sequence_parser_flow.csv** - CSV parsing and SVG rendering showing component interactions

### Structure Diagrams
- **architecture_structure.csv** - Package/component dependencies and boundaries (PLACEHOLDER)

### Legacy Architecture Models
The `architecture/` subdirectory contains class diagrams for individual components:
- csv_parser.csv - CSV parsing component design
- svg_renderer.csv - SVG rendering engine design
- data_model.csv - Core data model classes
- test_framework.csv - Testing infrastructure design
- web_server.csv - HTTP server design

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
