# Requirements

This document contains all implemented requirements, constraints, and assumptions.

Requirements are organized by type and linked to related artifacts.


## Requirements

| ID | Description | Linked From | Linked To | Status |
|:---|:---|:---|:---|:---|
| Architecture_0001 | Create a CSV-based DSL for visual sequence diagrams enabling humans to work iteratively with AI | UserStory_0001 | UserInterface_0001 | Implemented |
|     Architecture_0002 | Create api/diagram endpoint with parameters | - | Infrastructure_0001 | Implemented |
|     Architecture_0003 | Create api/lanes endpoint returning participants | - | Infrastructure_0001 | Implemented |
|     Architecture_0004 | Serve HTML viewer at root without listing | - | Infrastructure_0001 | Implemented |
|     Architecture_0005 | Load CSV on request for live updates | - | Infrastructure_0001 | Implemented |
|   Infrastructure_0001 | Build HTTP server for dynamic generation | - | Architecture_0002 | Implemented |
|   Note_0001 | Implement note system with Info, Warning, Error types | UserStory_0003 | Parser_0006;Rendering_0011 | Implemented |
|     Parser_0001 | Parse CSV hierarchical format with indentation into model objects | - | Architecture_0001;Sequence_0001 | Implemented |
|     Parser_0002 | Extract sequence steps with source, destination, function name, return value, parameters | - | Sequence_0001 | Implemented |
|     Parser_0003 | Support function calls with parameters and return values | - | Sequence_0001 | Implemented |
|     Parser_0004 | Parse StateMachine definitions with indentation | - | State_0001 | Implemented |
|     Parser_0005 | Parse State definitions nested within StateMachine | - | State_0001 | Implemented |
|     Parser_0006 | Parse note syntax "@Type, Description" format | - | Note_0001 | Implemented |
|     Parser_0007 | Support lane notes attached to participant lanes | - | Note_0001 | Implemented |
|     Parser_0008 | Support function notes attached to calls | - | Note_0001 | Implemented |
|     Rendering_0001 | Render sequence diagrams as SVG with lanes and arrows | - | Sequence_0001 | Implemented |
|     Rendering_0002 | Display function calls with solid arrows and labels | - | Sequence_0001 | Implemented |
|     Rendering_0003 | Display return values with dashed arrows and labels | - | Sequence_0001 | Implemented |
|     Rendering_0004 | Support multiple sequence steps on same row | - | Sequence_0001 | Implemented |
|     Rendering_0005 | Add parameter and return descriptions as tooltips | - | Sequence_0001 | Implemented |
|     Rendering_0006 | Add participant descriptions as tooltips | - | Sequence_0001 | Implemented |
|     Rendering_0007 | Render UML state boxes with rounded corners | - | State_0001 | Implemented |
|     Rendering_0008 | Display initial states below participant names | - | State_0001 | Implemented |
|     Rendering_0009 | Display state transitions after sequence steps | - | State_0001 | Implemented |
|     Rendering_0010 | Add state descriptions as tooltips | - | State_0001 | Implemented |
|     Rendering_0011 | Render notes as UML boxes with folded corner | - | Note_0001 | Implemented |
|     Rendering_0012 | Apply distinct colors: Info blue, Warning orange, Error red | - | Note_0001 | Implemented |
|     Rendering_0013 | Display note content via hover tooltip | - | Note_0001 | Implemented |
|     Rendering_0014 | Position lane notes below state boxes | - | Note_0001 | Implemented |
|     Rendering_0015 | Position function notes right of parameter text | - | Note_0001 | Implemented |
|     Rendering_0016 | Hide notes in Low/Normal, show in High verbosity | - | Note_0001 | Implemented |
|     Rendering_0017 | Never display note text inline, use tooltip only | - | Note_0001 | Implemented |
|   Sequence_0001 | Parse and render sequence diagrams from CSV format | UserStory_0001 | Parser_0001;Rendering_0001 | Implemented |
|   State_0001 | Implement UML state machine support with rendering | UserStory_0002 | Parser_0004;Rendering_0007 | Implemented |
|   UserInterface_0001 | Provide interactive web-based viewer | UserStory_0004 | UserInterface_0002;UserInterface_0003;UserInterface_0004 | Implemented |
|     UserInterface_0002 | Create menu button with ellipsis in upper-right | - | UserInterface_0001 | Implemented |
|     UserInterface_0003 | Implement verbosity selector Low/Normal/High | - | UserInterface_0001 | Implemented |
|     UserInterface_0004 | Implement layer filtering checkboxes | - | UserInterface_0001 | Implemented |
|     UserInterface_0005 | Enable live CSV reloading without restart | - | UserInterface_0001 | Implemented |
|     UserInterface_0006 | Add cache-busting headers to prevent caching | - | UserInterface_0001 | Implemented |
|     UserInterface_0009 | Support AI-generated problem-focused diagram collections so a human can review only diagrams relevant to a specific code/rendering issue | UserInterface_0001 | UserInterface_0010 | Future |
|     UserInterface_0010 | Support an AI-authored filter configuration artifact (`Process/ai_diagram_filter_config.schema.json`) that defines a diagram collection and per-diagram display settings (verbosity plus selected layers) | UserInterface_0009;UserInterface_0003;UserInterface_0004 | UserInterface_0001 | Future |

## Constraints

| ID | Description | Linked From | Linked To | Status |
|:---|:---|:---|:---|:---|
|   Rendering_0018 | Note boxes approximately 17x13 pixels size | - | Note_0001 | Implemented |
|   Rendering_0019 | Function arrows without overlapping lanes | - | Sequence_0001;Rendering_0002 | Implemented |

## Assumptions

| ID | Description | Linked From | Linked To | Status |
|:---|:---|:---|:---|:---|
|   Architecture_0006 | Server uses port 8000 by default | - | Infrastructure_0001 | Implemented |
|   Parser_0009 | CSV file at sample_model.csv in work directory | - | Architecture_0001 | Implemented |
|   Parser_0010 | Sequence ID defaults to SoftReq0001 | UserStory_0001 | Architecture_0001 | Implemented |

## Class Diagram Requirements (2026-04 Update)

### Class Diagram Structure

| ID | Description | Linked From | Linked To | Status |
|:---|:---|:---|:---|:---|
| Structure_0007 | Every class diagram object's grid must use fixed-size 20px × 20px cells; box width and height must be exact multiples of 20 | UserStory_0004 | ClassRouting_0001 | Implemented |
| Structure_0008 | Class diagram layout uses top-left anchoring with hierarchical tree-view positioning; root at (40px, 40px); objects never centered | UserStory_0004 | Structure_0009 | Implemented |
| Structure_0009 | Connectors between hierarchically-related objects must be vertically aligned at matching X coordinates; hierarchy connectors avoid corner grid cells | Structure_0008 | ClassRouting_0001 | Implemented |

### Class Diagram Routing

| ID | Description | Linked From | Linked To | Status |
|:---|:---|:---|:---|:---|
| ClassRouting_0001 | Class diagrams are rendered with orthogonal routing only | UserStory_0004 | Rendering_0020 | Implemented |
| ClassRouting_0002 | Orthogonal routing prioritizes simple elbows and avoids diagonal fallbacks | ClassRouting_0001 | Rendering_0020 | Implemented |
| ClassRouting_0003 | Domain-layer dense fan-out uses increased vertical spacing during layout to reduce overlap pressure | ClassRouting_0002 | Rendering_0020 | Implemented |
| ClassRouting_0004 | Domain-layer connector text placement uses occupancy-aware lane nudging to reduce stacked text overlap | ClassRouting_0003 | Rendering_0021 | Implemented |
| ClassRouting_0005 | Fanout mode (Mode 2) is the only allowed same-side multi-connector strategy for class diagrams; shared-trunk fanout is out of scope | ClassRouting_0001 | Rendering_0020;Rendering_0022 | Required |
| ClassRouting_0006 | Fanout geometry order is mandatory: Object -> distinct connect-start point -> multiplicity text on vertical leg -> vertical segment -> connector label text before bend -> right-angle bend -> horizontal run | ClassRouting_0005 | Rendering_0022 | Required |
| ClassRouting_0007 | Fanout must be visually explicit for top and bottom source edges and must preserve left/right symmetry across equivalent target groups | ClassRouting_0005 | Rendering_0022 | Required |
| ClassRouting_0008 | Reject non-fanout patterns: shared trunk, micro-offset pseudo-lanes, missing first-segment multiplicity, or label placement only at horizontal endpoints | ClassRouting_0006;ClassRouting_0007 | Rendering_0022 | Required |
| ClassRouting_0009 | Fanout must be defined and validated from all four source sides (top, bottom, left, right) using mirrored lane behavior where applicable | ClassRouting_0005 | Rendering_0022;Rendering_0023 | Required |
| ClassRouting_0010 | Left/right fanout branches must start with a horizontal first segment from side-wall connection points; top/bottom fanout branches start with a vertical first segment | ClassRouting_0006;ClassRouting_0009 | Rendering_0023 | Required |
| ClassRouting_0011 | Side-wall fanout capacity is provided by extending vertical object edges and adding additional side connection points at 2-character spacing | ClassRouting_0009 | Rendering_0023 | Required |
| ClassRouting_0012 | Direct fanout connectors are prioritized ahead of non-direct branches and always remain perpendicular to the source object side | ClassRouting_0009;ClassRouting_0010 | Rendering_0023 | Required |
| ClassUI_0001 | Hovering a class object highlights directly connected connectors and connector text while fading unrelated links | UserInterface_0001 | UserInterface_0007 | Implemented |

## Class Diagram Constraints (2026-04 Update)

| ID | Description | Linked From | Linked To | Status |
|:---|:---|:---|:---|:---|
| Rendering_0020 | Orthogonal connector segments are axis-aligned (horizontal/vertical only) in class diagrams | ClassRouting_0001 | ClassRouting_0002 | Implemented |
| Rendering_0021 | Connector text readability is prioritized via collision-aware placement over exact geometric centering | ClassRouting_0004 | ClassUI_0001 | Implemented |
| Rendering_0022 | Fanout lane spacing must allocate distinct start slots and distinct vertical text bands so multiplicity and connector text are readable on each vertical leg before bend | ClassRouting_0005;ClassRouting_0006 | ClassRouting_0007 | Required |
| Rendering_0023 | Fanout routing must preserve orientation-specific first-segment rules and side-point alignment: top/bottom use vertical-first, left/right use horizontal-first at aligned '+' side points | ClassRouting_0009;ClassRouting_0010;ClassRouting_0011 | ClassRouting_0008 | Required |
| UserInterface_0007 | Hover highlighting is non-destructive: no click/persist state required in hover-only mode | ClassUI_0001 | UserInterface_0001 | Implemented |
| UserInterface_0008 | All user-configurable settings in the `⋯` menu (verbosity, routing, Catalog: Show Test Diagrams) must be retained across page refreshes via localStorage; restoring these settings must happen before the first diagram catalog fetch so the correct catalog scope is used on startup | UserInterface_0002;UserInterface_0003 | UserInterface_0001 | Implemented |