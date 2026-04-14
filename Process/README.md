# Process Documentation

This directory contains process documentation, requirements, and design diagrams that define how the system works at multiple levels of abstraction.

## Directory Structure

### `/01_System`
**High-level system diagrams from the user's perspective**

Contains diagrams showing how users interact with the system and how the system integrates with external components.

- **Sequence Diagrams**: User-facing workflows and integration flows
- **Structure Diagrams**: System components and their relationships

Use these diagrams to understand:
- What the user sees and does
- How the system responds
- External system integration points

### `/02_Architecture`
**Technical architecture and component design**

Contains diagrams showing internal component interactions, dependencies, and design structure.

- **Sequence Diagrams**: Component-to-component interactions
- **Structure Diagrams**: Package/component boundaries and dependencies
- **Legacy Architecture Models**: Individual component designs (csv_parser, renderer, etc.)

Use these diagrams to understand:
- How components interact internally
- Architectural layers and responsibilities
- Technical design decisions

### Configuration & Requirements Files

- `_REQUIREMENTS.md` - Customer/functional requirements with traceability
- `_REQUIREMENTS_FULL.md` - Extended requirements with additional context
- `traceability.csv` - Requirement-to-implementation mapping
- `ui_data.json` - UI configuration and metadata
- `ai_diagram_filter_config.schema.json` - Future JSON schema for AI-authored problem-focused diagram collections and per-diagram filter settings
- `ai_diagram_filter_config.example.json` - Example instance of the future AI diagram filter configuration

## Layer-Based Filtering

All sequence diagrams support **layer-based filtering** to control complexity:

**Typical layers:**
- **UI** - User interface components
- **API** - API/Gateway layer
- **Business Logic** - Core processing services
- **Data Access** - Database and storage

Use the "Display Layers" menu in the diagram viewer to:
1. Show only specific layers
2. Hide implementation details
3. Focus on specific architectural concerns

## Class Diagram Interaction and Routing Notes

- Class diagrams use orthogonal connector routing in production behavior.
- Dense domain-layer diagrams use larger vertical spacing to reduce connector overlap pressure.
- Hovering a class object in the viewer highlights related connectors and connector text.
- Hover mode is intentionally transient (no click-to-pin state in the current implementation).

## Metadata Headers

Each diagram file includes metadata comments to identify and document it:

```csv
# DiagramType: Sequence | Class | State
# Purpose: Brief description of what this diagram shows
# Layers: List of architectural layers (if applicable)

Type;Name;Description;...
```

This allows tools to:
- Scan and identify diagram files
- Extract purpose and scope
- Verify diagram types

## Adding New Diagrams

When adding diagrams:

1. Choose the appropriate directory:
   - `/System` for user-facing workflows
   - `/Architecture` for internal component design

2. Include metadata header with DiagramType and Purpose

3. Assign layers to classes for filtering capability

4. Update the relevant README with description

5. Commit with clear message indicating which section was extended

## Design Principles

1. **Separation of Concerns**: System vs Architecture
2. **Multi-layer Design**: UI, API, Logic, Data layers
3. **Complexity Control**: Layer filtering for different audiences
4. **Documentation**: Self-documenting with headers and comments
5. **Traceability**: Link diagrams to requirements and user stories
