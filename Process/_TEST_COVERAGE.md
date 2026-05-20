# Test Coverage Documentation

## Overview

This document maps test cases to requirements, providing traceability and coverage metrics.

Each test case validates one or more specific requirements from the system specification.

## Test Coverage by File

| Test File | Requirements Tested | Test Focus |
|:---|:---|:---|
| test_layers.csv | UserInterface_0004; Rendering_0001; Rendering_0002 | Layer filtering and multi-participant interactions |
| test_multirow.csv | Rendering_0004; Rendering_0003 | Multiple steps per row - parallel operations |
| test_notes.csv | Rendering_0011; Rendering_0012; Rendering_0013; Rendering_0014; Rendering_0015; Rendering_0016; Rendering_0017; Parser_0006; Note_0001 | Note rendering, positioning, and visibility |
| test_parameters.csv | Parser_0002; Parser_0003; Rendering_0001; Rendering_0002; Rendering_0003; Rendering_0005 | Function parameters and return values |
| test_states.csv | State_0001; Rendering_0007; Rendering_0008; Rendering_0009; Rendering_0010; Parser_0004; Parser_0005 | State machine definition and transitions |
| test_verbosity.csv | UserInterface_0003; Rendering_0005; Rendering_0006 | Verbosity level effects on display |

### Python Unit Tests

| Test File | Requirements Tested | Test Focus |
|:---|:---|:---|
| test_class_diagram_connector_routing.py | ClassRouting_0001; ClassRouting_0002 | Connector edge selection and overlap avoidance |
| test_class_diagram_midpoint_simplicity.py | ClassRouting_0001; ClassRouting_0002 | Midpoint defaults and simple-route preference |
| test_class_diagram_multiplicity_guardrails.py | ClassRouting_0007; ClassRouting_0009; Rendering_0022 | Multiplicity placement on connectors |
| test_class_diagram_routing_guardrails.py | ClassRouting_0001; Structure_0009; Rendering_0020 | Orthogonal routing guardrails across all diagrams |
| test_class_diagram_svg_golden.py | Structure_0007; Structure_0008; Structure_0009 | Golden SVG regression for critical scenarios |
| test_class_diagram_title_and_endpoints.py | Structure_0008; Structure_0009 | Title placement and endpoint directions |
| test_class_diagram_two_segment_matrix.py | ClassRouting_0001; ClassRouting_0002 | Two-segment orthogonal elbow routing matrix |
| test_class_diagram_two_segment_orthogonality.py | ClassRouting_0001; ClassRouting_0002 | Two-segment orthogonality guardrails |
| test_class_metadata_traceability.py | Architecture_0001; Parser_0001 | Class traceability and diagram hierarchy parsing |
| test_csv_editor_api.py | UserInterface_0001 | CSV editor API helper functions |
| test_fanout.py | ClassRouting_0005; ClassRouting_0006; ClassRouting_0007; ClassRouting_0009; Rendering_0022; Rendering_0023 | Fanout routing (top/bottom/left/right sides) |
| test_grid_coordinates.py | Structure_0007; Structure_0008 | Grid coordinate validation and overlap detection |
| test_layout_modes.py | Structure_0008; ClassRouting_0001 | Routing-aware layout verification |
| test_verbosity.py | UserInterface_0003; Rendering_0005; Rendering_0006 | Verbosity level display (Python equivalent of test_verbosity.csv) |

## Requirement Coverage Map

| Requirement ID | Tested By | Status |
|:---|:---|:---|
| Note_0001 | test_notes.csv | ✓ Covered |
| Parser_0002 | test_parameters.csv | ✓ Covered |
| Parser_0003 | test_parameters.csv | ✓ Covered |
| Parser_0004 | test_states.csv | ✓ Covered |
| Parser_0005 | test_states.csv | ✓ Covered |
| Parser_0006 | test_notes.csv | ✓ Covered |
| Rendering_0001 | test_layers.csv; test_parameters.csv | ✓ Covered |
| Rendering_0002 | test_layers.csv; test_parameters.csv | ✓ Covered |
| Rendering_0003 | test_multirow.csv; test_parameters.csv | ✓ Covered |
| Rendering_0004 | test_multirow.csv | ✓ Covered |
| Rendering_0005 | test_parameters.csv; test_verbosity.csv | ✓ Covered |
| Rendering_0006 | test_verbosity.csv | ✓ Covered |
| Rendering_0007 | test_states.csv | ✓ Covered |
| Rendering_0008 | test_states.csv | ✓ Covered |
| Rendering_0009 | test_states.csv | ✓ Covered |
| Rendering_0010 | test_states.csv | ✓ Covered |
| Rendering_0011 | test_notes.csv | ✓ Covered |
| Rendering_0012 | test_notes.csv | ✓ Covered |
| Rendering_0013 | test_notes.csv | ✓ Covered |
| Rendering_0014 | test_notes.csv | ✓ Covered |
| Rendering_0015 | test_notes.csv | ✓ Covered |
| Rendering_0016 | test_notes.csv | ✓ Covered |
| Rendering_0017 | test_notes.csv | ✓ Covered |
| State_0001 | test_states.csv | ✓ Covered |
| UserInterface_0003 | test_verbosity.csv | ✓ Covered |
| UserInterface_0004 | test_layers.csv | ✓ Covered |

## Coverage Statistics

- **Total Requirements**: 67 (includes Class Diagram requirements added 2026-04)
- **Tested Requirements**: 39
- **Coverage**: 58.2%
- **Total Test Cases**: 20 (6 CSV + 14 Python unit tests)

## Test Execution Guide

To run all tests:

```bash
python run_test.py test_layers
python run_test.py test_multirow
python run_test.py test_notes
python run_test.py test_parameters
python run_test.py test_states
python run_test.py test_verbosity
```

Each test generates a `test_[name]_output.svg` file that can be inspected for correctness.

## Requirements by Type

### Architecture Requirements

| ID | Tested By | Description |
|:---|:---|:---|
| Architecture_0001 | Not tested | Create a CSV-based DSL for visual sequence diagrams enabling humans to work iteratively with AI |
| Architecture_0002 | Not tested | Create api/diagram endpoint with parameters |
| Architecture_0003 | Not tested | Create api/lanes endpoint returning participants |
| Architecture_0004 | Not tested | Serve HTML viewer at root without listing |
| Architecture_0005 | Not tested | Load CSV on request for live updates |
| Architecture_0006 | Not tested | Server uses port 8000 by default |

### Infrastructure Requirements

| ID | Tested By | Description |
|:---|:---|:---|
| Infrastructure_0001 | Not tested | Build HTTP server for dynamic generation |

### Note Requirements

| ID | Tested By | Description |
|:---|:---|:---|
| Note_0001 | test_notes.csv | Implement note system with Info, Warning, Error types |

### Parser Requirements

| ID | Tested By | Description |
|:---|:---|:---|
| Parser_0001 | Not tested | Parse CSV hierarchical format with indentation into model objects |
| Parser_0002 | test_parameters.csv | Extract sequence steps with source, destination, function name, return value, parameters |
| Parser_0003 | test_parameters.csv | Support function calls with parameters and return values |
| Parser_0004 | test_states.csv | Parse StateMachine definitions with indentation |
| Parser_0005 | test_states.csv | Parse State definitions nested within StateMachine |
| Parser_0006 | test_notes.csv | Parse note syntax "@Type, Description" format |
| Parser_0007 | Not tested | Support lane notes attached to participant lanes |
| Parser_0008 | Not tested | Support function notes attached to calls |
| Parser_0009 | Not tested | CSV file at sample_model.csv in work directory |
| Parser_0010 | Not tested | Sequence ID defaults to SoftReq0001 |

### Rendering Requirements

| ID | Tested By | Description |
|:---|:---|:---|
| Rendering_0001 | test_layers.csv, test_parameters.csv | Render sequence diagrams as SVG with lanes and arrows |
| Rendering_0002 | test_layers.csv, test_parameters.csv | Display function calls with solid arrows and labels |
| Rendering_0003 | test_multirow.csv, test_parameters.csv | Display return values with dashed arrows and labels |
| Rendering_0004 | test_multirow.csv | Support multiple sequence steps on same row |
| Rendering_0005 | test_parameters.csv, test_verbosity.csv | Add parameter and return descriptions as tooltips |
| Rendering_0006 | test_verbosity.csv | Add participant descriptions as tooltips |
| Rendering_0007 | test_states.csv | Render UML state boxes with rounded corners |
| Rendering_0008 | test_states.csv | Display initial states below participant names |
| Rendering_0009 | test_states.csv | Display state transitions after sequence steps |
| Rendering_0010 | test_states.csv | Add state descriptions as tooltips |
| Rendering_0011 | test_notes.csv | Render notes as UML boxes with folded corner |
| Rendering_0012 | test_notes.csv | Apply distinct colors: Info blue, Warning orange, Error red |
| Rendering_0013 | test_notes.csv | Display note content via hover tooltip |
| Rendering_0014 | test_notes.csv | Position lane notes below state boxes |
| Rendering_0015 | test_notes.csv | Position function notes right of parameter text |
| Rendering_0016 | test_notes.csv | Hide notes in Low/Normal, show in High verbosity |
| Rendering_0017 | test_notes.csv | Never display note text inline, use tooltip only |
| Rendering_0018 | Not tested | Note boxes approximately 17x13 pixels size |
| Rendering_0019 | Not tested | Function arrows without overlapping lanes |

### Sequence Requirements

| ID | Tested By | Description |
|:---|:---|:---|
| Sequence_0001 | Not tested | Parse and render sequence diagrams from CSV format |

### State Requirements

| ID | Tested By | Description |
|:---|:---|:---|
| State_0001 | test_states.csv | Implement UML state machine support with rendering |

### UserInterface Requirements

| ID | Tested By | Description |
|:---|:---|:---|
| UserInterface_0001 | test_csv_editor_api.py | Provide interactive web-based viewer |
| UserInterface_0002 | Not tested | Create menu button with ellipsis in upper-right |
| UserInterface_0003 | test_verbosity.csv; test_verbosity.py | Implement verbosity selector Low/Normal/High |
| UserInterface_0004 | test_layers.csv | Implement layer filtering checkboxes |
| UserInterface_0005 | Not tested | Enable live CSV reloading without restart |
| UserInterface_0006 | Not tested | Add cache-busting headers to prevent caching |
| UserInterface_0007 | Not tested | Hover highlighting is non-destructive (no click/persist state) |
| UserInterface_0008 | Not tested | Settings (verbosity, routing, catalog scope) retained across refreshes via localStorage |

### Class Diagram Structure Requirements

| ID | Tested By | Description |
|:---|:---|:---|
| Structure_0007 | test_class_diagram_svg_golden.py; test_grid_coordinates.py | Fixed 20px x 20px grid cell rule for all class diagram objects |
| Structure_0008 | test_class_diagram_svg_golden.py; test_grid_coordinates.py; test_layout_modes.py; test_class_diagram_title_and_endpoints.py | Top-left anchored tree-view layout |
| Structure_0009 | test_class_diagram_routing_guardrails.py; test_class_diagram_svg_golden.py; test_class_diagram_title_and_endpoints.py | Hierarchy connectors vertically aligned at matching X coordinates |

### Class Diagram Routing Requirements

| ID | Tested By | Description |
|:---|:---|:---|
| ClassRouting_0001 | test_class_diagram_connector_routing.py; test_class_diagram_midpoint_simplicity.py; test_class_diagram_routing_guardrails.py; test_class_diagram_two_segment_matrix.py; test_class_diagram_two_segment_orthogonality.py; test_layout_modes.py | Orthogonal-only routing for class diagrams |
| ClassRouting_0002 | test_class_diagram_connector_routing.py; test_class_diagram_midpoint_simplicity.py; test_class_diagram_two_segment_matrix.py; test_class_diagram_two_segment_orthogonality.py | Simple elbow preference, no diagonal fallbacks |
| ClassRouting_0003 | Not tested | Domain-layer dense fan-out uses increased vertical spacing |
| ClassRouting_0004 | Not tested | Occupancy-aware lane nudging for connector text |
| ClassRouting_0005 | test_fanout.py | Mode 2 fanout only — shared trunk disallowed |
| ClassRouting_0006 | test_fanout.py | Mandatory fanout geometry order |
| ClassRouting_0007 | test_class_diagram_multiplicity_guardrails.py; test_fanout.py | Fanout visually explicit for all four source sides |
| ClassRouting_0008 | Not tested | Reject non-fanout patterns (shared trunk, micro-offset, etc.) |
| ClassRouting_0009 | test_class_diagram_multiplicity_guardrails.py; test_fanout.py | Fanout defined from all four source sides |
| ClassRouting_0010 | Not tested | Left/right fanout horizontal-first; top/bottom vertical-first |
| ClassRouting_0011 | Not tested | Side-wall capacity extended for left/right fanout |
| ClassRouting_0012 | Not tested | Direct connectors prioritized and perpendicular to source side |

### Class Diagram Rendering Requirements

| ID | Tested By | Description |
|:---|:---|:---|
| Rendering_0020 | test_class_diagram_routing_guardrails.py | Orthogonal segments axis-aligned in class diagrams |
| Rendering_0021 | Not tested | Collision-aware connector text placement |
| Rendering_0022 | test_class_diagram_multiplicity_guardrails.py; test_fanout.py | Fanout lane spacing — distinct start slots and text bands |
| Rendering_0023 | test_fanout.py | Fanout orientation-specific first-segment and side-point alignment |
