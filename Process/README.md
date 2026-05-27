# Process Documentation

This directory contains requirements and model artifacts used to drive implementation.

## Final Hierarchy

Each domain uses diagram composition plus reusable definitions:

- `01_System/`
	- `00_Main/` (entrypoint diagrams)
	- `10_Diagrams/` (composed diagrams)
	- `20_Definitions/` (reusable classes/actors/packages included by diagrams)
- `02_Architecture/`
	- `10_Diagrams/`
	- `20_Definitions/`
- `03_Design/`
	- `10_Diagrams/`
	- `20_Definitions/`

## Include Workflow

1. Put reusable CSV building blocks in `20_Definitions`.
2. Put renderable composition diagrams in `10_Diagrams` (and `00_Main` for System entrypoints).
3. Use relative `Include` rows from diagram CSVs to definition CSVs.
4. Keep test CSV files unchanged unless explicitly requested.

## CSV Style

Diagram CSVs in this hierarchy are kept comment-free. Use `Include` lines first (when needed), then a blank line, then diagram definitions.

## Requirements Document Index

Before starting any non-trivial implementation task, check the applicable documents below for requirements governing the change. When a chat request touches one of these domains, read the corresponding document before implementing.

| Document | Domain | Requirement ID Prefixes |
|:---------|:-------|:------------------------|
| `_REQUIREMENTS.md` | Sequence Diagrams, State Machines, Parser, UI, Class Diagrams | `Architecture_*`, `Infrastructure_*`, `Note_*`, `Parser_*`, `Rendering_*`, `Sequence_*`, `State_*`, `UserInterface_*`, `ClassRouting_*`, `ClassUI_*`, `Structure_*` |
| `CLASS_DIAGRAM_LAYOUT_REQUIREMENTS.md` | Class Diagram Layout & Routing | `Structure_0007–0009`, `ClassRouting_0001–0012`, `Rendering_0020–0023` |
| `CLASS_DIAGRAM_LAYOUT_ARCHITECTURE_REQUIREMENTS.md` | Class Diagram Layout/Routing Ownership, Column Allocation, Guardrail Precedence | Architectural ownership and precedence rules supplementing `Structure_*`, `ClassRouting_*`, and `Rendering_*` |
| `CONNECTOR_TEXT_LAYOUT.md` | Connector Text Positioning (all diagrams) | (inline text placement rules — no formal IDs) |
| `ROUTER_INCIDENT_WORKFLOW.md` | Router investigation process for complex Diagram Viewer routing problems | Development-process trigger, required routing sequence artifact, note-color semantics |
| `ROUTER_INCIDENT_TEMPLATE.md` | Reusable template for complex Diagram Viewer router investigations | Copy-paste incident scaffold with routing sequence diagram and color-coded note sections |
| `CSV_EDITOR_MVP_REQUIREMENTS.md` | CSV Editor UI | CSV Editor MVP v0.1–v0.3 acceptance criteria |
| `_ADR.md` | Architecture Decision Records | (rationale records — no formal IDs) |
| `_TEST_COVERAGE.md` | Test Traceability | Requirement-to-test mapping |

> **Note**: Root-level `*.md` files in the repository (e.g., `CONNECTOR_ARCHITECTURE.md`, `ROUTING_FIX_SUMMARY.md`) are historical implementation notes, not requirements. Requirements are defined exclusively in the `Process/` documents above.

## Configuration and Requirements Files

- `_REQUIREMENTS.md` - customer and functional requirements with traceability
- `_REQUIREMENTS_FULL.md` - extended requirement context
- `traceability.csv` - requirement-to-implementation mapping
- `_ADR.md` - architecture decision index
- `ROUTER_INCIDENT_WORKFLOW.md` - required analysis workflow for complex router incidents
- `ROUTER_INCIDENT_TEMPLATE.md` - reusable scaffold for router incident analysis packets
- `ui_data.json` - UI configuration and metadata
- `ai_diagram_filter_config.schema.json` - schema for AI-authored diagram collections
- `ai_diagram_filter_config.example.json` - example configuration
