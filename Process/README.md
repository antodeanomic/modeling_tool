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

## Configuration and Requirements Files

- `_REQUIREMENTS.md` - customer and functional requirements with traceability
- `_REQUIREMENTS_FULL.md` - extended requirement context
- `traceability.csv` - requirement-to-implementation mapping
- `_ADR.md` - architecture decision index
- `ui_data.json` - UI configuration and metadata
- `ai_diagram_filter_config.schema.json` - schema for AI-authored diagram collections
- `ai_diagram_filter_config.example.json` - example configuration
