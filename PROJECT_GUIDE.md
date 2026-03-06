# Sequence Diagram Modeling Tool - Project Guide

<style>
a[href*="#creq-"], a[href*="#us-"], a[href*="#feat-"] {
  cursor: pointer;
}

/* Highlight rows when they're the anchor target */
:target {
  box-shadow: 0 0 0 3px var(--vscode-focusBorder, #0066cc);
  outline: 2px solid var(--vscode-focusBorder, #0066cc);
  outline-offset: -2px;
}
</style>

## Purpose: Problem We're Solving

**Improve process for Human ↔ AI interaction when creating complex software.**

Managing a complex AI project requires structure—both a defined process and clear process artifacts. While AI works well with text files (easy to maintain and diff), humans struggle with pure text and need visual aids like tables, diagrams, charts, and examples.

Markdown and Mermaid partially solve this, but have significant limitations:
- **Mermaid renderer** consumes enormous visual space
- **UML syntax** generates visual noise that makes simple diagrams look overly complex
- **No filtering capability** to show only the elements relevant to specific audiences (e.g., show only components for Feature X, or only interactions for User Story Y)
- **No scaling** for different levels of abstraction

**Solution**: Create a custom diagram renderer that generates UML-like diagrams from simple CSV specifications. This is a **"super Mermaid"** with:
- Simpler, more powerful interface than Mermaid
- Better use of visual space
- Ability to filter complexity for different contexts
- Support for multiple diagram types

**Diagram Types to Support**:
1. Class/Component/Project diagrams
2. Sequence diagrams
3. State diagrams

**Meta-Goal**: This project will define a process for Human-AI collaboration AND use that process to develop itself—making this project a test case for its own methodology.

---

## User Stories & Actors

### Actors

| Actor | Description |
|---|---|
| **Software Engineer** | Creates and maintains software designs. Uses the tool to define architecture, create diagrams, and specify requirements in CSV files. Collaborates with Claude to implement designs. Verifies that rendered diagrams match intended specifications. |
| **Test Engineer** | Validates that implementations match specifications. Uses diagrams filtered to show interactions and objects required for test scenarios. Creates test cases based on interaction diagrams. Verifies that rendered diagrams accurately reflect code behavior. |
| **Manager** | Oversees project progress and resource planning. Uses high-level diagrams and requirement artifacts to understand scope, complexity, and status. Reviews process documentation to track decision-making and rationale. |
| **Claude (AI Assistant)** | Analyzes diagrams and specifications to understand requirements. Implements code changes to match specifications. Maintains process artifacts and documentation. Identifies gaps in specifications and asks clarifying questions through diagrams. Learns project context from structured artifacts when sessions restart. |

### User Stories

| ID | User Story | Actor | Implements | Acceptance Criteria |
|---|---|---|---|---|
| <a id="us-001"></a>[**US-001**](#us-001) | **Give AI concrete instructions on object interactions** | Software Engineer | [CREQ-001](#creq-001), [CREQ-002](#creq-002), [CREQ-003](#creq-003) | Engineer creates a sequence diagram in CSV format showing how objects should interact. Claude can read the diagram and understand the interaction specification. Collaboration happens at the design/diagram level, not in code comments. |
| <a id="us-002"></a>[**US-002**](#us-002) | **Visually show AI work output for design-level collaboration** | Claude (AI Assistant) | [CREQ-001](#creq-001), [CREQ-002](#creq-002), [CREQ-003](#creq-003) | Claude renders diagrams showing implemented interactions. Software Engineer can visually verify that Claude's work matches the specified design. Design feedback happens through diagrams, not code reviews. |
| <a id="us-003"></a>[**US-003**](#us-003) | **Filter away diagram complexity for different audiences** | Software Engineer, Test Engineer, Manager | [CREQ-001](#creq-001), [CREQ-004](#creq-004) | User can apply filters (layers, verbosity levels, future filtering features) to show only relevant elements. Manager sees high-level architecture. Test engineer sees interaction details. Engineer sees full design. Same CSV file, different views. |
| <a id="us-004"></a>[**US-004**](#us-004) | **Visually see objects and interactions required for specs** | Software Engineer, Test Engineer | [CREQ-001](#creq-001), [CREQ-004](#creq-004) | User can filter a diagram to show only the objects, participants, and interactions needed to implement a specific User Story, Feature, or Requirement. Enables traceability and scope clarity. |

---

## Customer Requirements

| ID | Requirement | Satisfies | Rationale |
|---|---|---|---|
| <a id="creq-001"></a>[**CREQ-001**](#creq-001) | **Defined process re-uses existing software processes** | [US-001](#us-001), [US-002](#us-002), [US-003](#us-003), [US-004](#us-004) | **Recommended Process**: Structured Discovery → Specification → Design → Implementation → Verification. Each phase produces text-based artifacts that AI can maintain and humans can verify. **Process Artifacts**: (1) Purpose & Problem Statement (markdown), (2) Customer Requirements table (markdown), (3) User Stories with Acceptance Criteria (markdown), (4) Functional Requirements (markdown), (5) Architecture & Design Decisions (markdown + diagrams), (6) Data Models & Schemas (CSV + diagrams), (7) Test Specifications (CSV with test cases), (8) Implementation Code (Python/HTML/CSS), (9) Test Results & Coverage Reports (markdown). This creates a clear audit trail and enables AI to be reintroduced to the project at any phase without context loss. |
| <a id="creq-002"></a>[**CREQ-002**](#creq-002) | **Render UML-like diagrams from input .csv files** | [US-001](#us-001), [US-002](#us-002), [US-003](#us-003), [US-004](#us-004) | CSV files can be imported/exported into spreadsheets, enabling features like Sort, Filter, Pick lists for easier maintenance. "UML-like" because traditional UML is visually messy on some diagram types. |
| <a id="creq-003"></a>[**CREQ-003**](#creq-003) | **High-level project guide that guides AI to learn projects using structure** | [US-001](#us-001), [US-002](#us-002) | Structure: Purpose → CustomerReq → UserStories → Requirements → Architecture → Design → Code → Test. Without this: AI chat sessions get summarized/cleared, causing AI to be overwhelmed when reintroduced to projects. |
| <a id="creq-004"></a>[**CREQ-004**](#creq-004) | **Preview viewer with instant diagram updates** | [US-003](#us-003), [US-004](#us-004) | User can edit CSV files and immediately see rendered diagram changes in a live preview. Eliminates manual render steps and provides instant feedback loop for design iteration. |

---

## Features

### MVP (Sequence Diagrams - Current Focus)

| ID | Feature | Implements | Description | Status |
|---|---|---|---|---|
| <a id="feat-001"></a>[**FEAT-001**](#feat-001) | **CSV Parser** | [US-001](#us-001), [US-002](#us-002) | Parse sequence diagram specifications from CSV files. Support for participants, sequences, messages, return values, and notes. Validate CSV structure with error reporting. | In Progress |
| <a id="feat-002"></a>[**FEAT-002**](#feat-002) | **Sequence Diagram Rendering** | [US-001](#us-001), [US-002](#us-002) | Render sequence diagrams to interactive SVG format with proper participant lanes, message flows, return arrows, and visual spacing. | In Progress |
| <a id="feat-003"></a>[**FEAT-003**](#feat-003) | **Function Notes** | [US-001](#us-001), [US-002](#us-002) | Support notes attached to specific messages/interactions with customizable styling based on note type (@Info, @Warning, etc.). | In Progress |
| <a id="feat-004"></a>[**FEAT-004**](#feat-004) | **Lane Notes** | [US-001](#us-001), [US-002](#us-002) | Support notes attached to specific participants at specific interaction points. Proper visual positioning and ordering. | In Progress |
| <a id="feat-005"></a>[**FEAT-005**](#feat-005) | **Spanning Brackets** | [US-001](#us-001), [US-002](#us-002) | Visual indicators showing the duration/scope of function calls or parallel processes. | In Progress |
| <a id="feat-006"></a>[**FEAT-006**](#feat-006) | **Web-Based Preview Viewer** | [US-001](#us-001), [US-002](#us-002), [US-003](#us-003), [US-004](#us-004) | Flask-based web server providing live preview of diagrams. Auto-refresh on CSV file changes (instant feedback). Access via `http://localhost:8000`. | In Progress |
| <a id="feat-007"></a>[**FEAT-007**](#feat-007) | **Verbosity Level Filtering** | [US-003](#us-003), [US-004](#us-004) | Support multiple verbosity levels (Low, Normal, High) to control what details are displayed in rendered diagrams. Different audiences see appropriate detail levels. | In Progress |
| <a id="feat-008"></a>[**FEAT-008**](#feat-008) | **Interactive SVG Output** | [US-001](#us-001), [US-002](#us-002) | Rendered diagrams include hover tooltips, clickable elements, and other interactive features for design exploration. | In Progress |
| <a id="feat-009"></a>[**FEAT-009**](#feat-009) | **Test Specifications** | [US-001](#us-001), [US-002](#us-002), [US-003](#us-003), [US-004](#us-004) | CSV test files in `Test/tests/` define diagram specifications. Automated test runner validates rendering against expected output. | In Progress |

### Phase 2 (Planned)

| ID | Feature | Implements | Description |
|---|---|---|---|
| <a id="feat-010"></a>[**FEAT-010**](#feat-010) | **Class/Component Diagrams** | [US-001](#us-001), [US-002](#us-002) | Render class structures, component dependencies, and architecture relationships from CSV specifications. |
| <a id="feat-011"></a>[**FEAT-011**](#feat-011) | **State Diagrams** | [US-001](#us-001), [US-002](#us-002) | Render state machines and state transitions from CSV specifications. |
| <a id="feat-012"></a>[**FEAT-012**](#feat-012) | **Layer Filtering** | [US-003](#us-003), [US-004](#us-004) | Group diagram elements by layer/category and allow filtering to show only relevant layers. Example: Show only authentication layer, or deployment layer. |
| <a id="feat-013"></a>[**FEAT-013**](#feat-013) | **Requirement Traceability** | [US-004](#us-004) | Link diagram elements (messages, interactions, participants) to specific requirements, user stories, or features. Filter to show only elements for a specific requirement. |
| <a id="feat-014"></a>[**FEAT-014**](#feat-014) | **Export Features** | [US-001](#us-001), [US-002](#us-002), [US-003](#us-003) | Export diagrams as standalone SVG, PNG, or PDF. Export project documentation with embedded diagrams. |
| <a id="feat-015"></a>[**FEAT-015**](#feat-015) | **Spreadsheet Integration** | [US-001](#us-001), [US-002](#us-002) | Seamless export to and import from Excel/Google Sheets for CSV editing with UI polish (validation, dropdowns, etc.). |
| <a id="feat-016"></a>[**FEAT-016**](#feat-016) | **Collaborative Comments** | [US-001](#us-001), [US-002](#us-002) | Attach comments to diagram elements for team collaboration and design discussions. |

---

## Traceability Matrix

The complete traceability matrix is maintained in [Process/traceability.csv](Process/traceability.csv) and enables:
- **Requirement Linking**: Trace each Customer Requirement (CREQ-) through User Stories (US-) to Features (FEAT-) and Test Cases
- **Impact Analysis**: See which features implement which requirements, and what test coverage exists
- **Diagram Filtering**: Future versions will use this matrix to filter diagrams by Feature, Requirement, or User Story
- **Change Management**: Understand the impact of changes across the entire requirement hierarchy

**Format**: Each row maps one requirement relationship:
```
Requirement_ID,Requirement_Type,Customer_Req_ID,User_Story_ID,Feature_ID,Feature_Status,Test_Case_ID,Description
```

This allows the diagram tool to provide filtering like:
- "Show me all interactions required for CREQ-002"
- "What test cases cover FEAT-006?"
- "Which requirements does US-001 satisfy?"

---

## How the Project Works

### Input: CSV Files (Requirements)

CSV files in `Source/` and `Test/tests/` define sequence diagrams:

```csv
Type,Name,Description
Class,A,First participant
Class,B,Second participant
Sequence,MySequence,Sequence name
    A,B,FunctionName,ReturnVal,Param1,@Info,Note content
    B,@Warning,Lane note for B
    B,A,ReturnMessage,RetVal
```

**Key Rules:**
- Each row is a step in the sequence
- Format: `Source, Destination, Function, [values], [@NoteType, Note]`
- Lane notes attach to specific participants: `ParticipantName, @NoteType, Content`
- CSV files define the CONTRACT/SPECIFICATION
- **NEVER modify CSV test files unless explicitly instructed by the user**

### Processing Pipeline

1. **Parser** (`Scripts/parser.py`): Parses CSV → Model objects
2. **Renderer** (`Scripts/svg_renderer.py`): Model objects → SVG diagram
3. **Server** (`Scripts/server.py`): Flask web server + interactive UI

### Output: SVG Diagrams

- Rendered in `Test/tests/` as `.svg` files
- Viewable in browser at `http://localhost:8000`
- Interactive features:
  - Hover tooltips
  - Verbosity levels (Low/Normal/High)
  - Layer filtering

## How to Relearn This Project (Session Continuity)

When a session ends or pauses, you can quickly get back up to speed:

### 1. Check the Current State
```bash
cd c:\Users\antod\OneDrive\Documents\repo\modeling_tool
git log --oneline -5  # See recent commits
git status            # See what's changed
```

### 2. Understand Recent Changes
Read commit messages to understand what was attempted.
Check `claude.md` for current interaction rules.

### 3. Review the Test That's Being Fixed
- Current focus test: `Test/tests/test_note_ordering.csv`
- Expected output: `Test/tests/test_note_ordering_NoteOrderTest_High.svg`
- Issue description: Check the conversation or git commit messages

### 4. Start the Development Server
```bash
# Run refresh.bat to start server at http://localhost:8000
# View diagrams in MS Edge
# Check server logs: check server_output.log
```

### 5. Understand the Code Architecture

**Key Files:**
- `Scripts/parser.py` - CSV parsing logic, row numbering, step definition
- `Scripts/svg_renderer.py` - Y-position calculation, note positioning, SVG rendering
- `Scripts/model.py` - Data classes: SequenceStep, NoteDef, etc.
- `Scripts/server.py` - Flask server, CSV loading, request handling

**Key Constants in svg_renderer.py:**
```python
ROW_HEIGHT = 24        # Vertical space per message row
ROW_SPACING = 6        # Extra gap between rows (total 30px per row)
NOTE_SPACING = 25      # Note positioned 25px below message
NOTE_BOX_HEIGHT = 13   # Height of note box
```

## Why This Project Exists

This tool solves a critical communication problem in software engineering:

### The Problem
When designing complex systems, engineers and AI struggle to communicate about:
- Exact timing and ordering of interactions
- Note placement and visual layout
- Message sequencing and dependencies
- Return values and state changes

### The Solution
By using diagrams as the specification language:
- **No ambiguity**: A diagram is unambiguous (unlike English descriptions)
- **Visual clarity**: Both parties see the same picture
- **Testable**: Automated rendering validates against CSV specs
- **Iterable**: Easy to modify specifications and see results

### The Long Vision
This tool becomes the **interface** between human architects and AI developers:
1. Human creates architecture diagrams in the tool
2. AI reads diagrams to understand requirements
3. AI proposes implementation
4. Human and AI refine design collaboratively
5. Final diagrams become authoritative specification

## How I (Claude) Can Help

### My Responsibilities

1. **Implement to Specification**: 
   - Read CSV files (the requirements)
   - Implement code changes to match expected rendering
   - Never modify CSV files - fix the code instead

2. **Use Diagrams for Communication**:
   - Ask you to create diagrams when requirements are unclear
   - Analyze diagrams to understand architectural intent
   - Propose changes through the diagram language

3. **Maintain Code Quality**:
   - Respect the architecture (parser → model → renderer pipeline)
   - Follow the established patterns in the codebase
   - Document assumptions and limitations

4. **Work Within My Constraints**:
   - Don't change requirements (CSV files) to fit code
   - Don't make junior engineer mistakes (hacking, assuming, not asking)
   - Ask for clarification through diagrams when uncertain

### What I Need From You

1. **Clear Visual Specifications**:
   - Use the tool to diagram what you want
   - Create test cases that show expected behavior
   - When something is wrong, create a diagram showing the issue

2. **Constraints and Rules**:
   - Document any special rules (like "don't modify CSV files")
   - Clarify when something is a hard requirement vs. nice-to-have
   - Explain the "why" behind requirements

3. **Feedback Loop**:
   - When I get it wrong, point to the diagram and explain the mismatch
   - Don't expect perfection on first attempt
   - Use diagrams to align on what "done" looks like

## Current Issues

### Note Ordering Problem (Active)
**Status**: In progress, needs architectural review

**Issue**: In `test_note_ordering.csv` with High verbosity:
- Msg1 → B (row 1)
- Note for B should appear below Msg1
- Msg2 → C (row 2) should appear BELOW the B note
- Current: Msg2 appears at same Y position or overlapping with the note

**Root Cause**: Y-position calculation doesn't account for note height when spacing rows.

**Next Approach**: Create a sequence diagram showing the expected layout, then implement renderer changes to match.

## Development Workflow

### Daily Startup
1. Start server: `refresh.bat` (or run Refresh Server task)
2. Open `http://localhost:8000` in MS Edge
3. Check `Test/tests/` for rendered SVG files
4. Review `server_output.log` for any errors

### Making Changes
1. Modify code (Python files in `Scripts/`)
2. Server auto-reloads on next request
3. Browser refresh shows new rendering
4. Check SVG source if needed: `Test/tests/*_High.svg`

### Testing Changes
1. All test CSVs in `Test/tests/` are specifications
2. Run `python Test/run_all_tests_and_view.py` to render all tests
3. Compare rendered SVG against expected behavior

### Committing
```bash
git add <files>
git commit -m "Clear message explaining what changed and why"
```

## Glossary

- **CSV File**: Specification/requirement for a sequence diagram
- **SequenceStep**: Single message/interaction in a diagram
- **Lane/Participant**: Actor in the sequence diagram (A, B, C, etc.)
- **Lane Note**: Note attached to a specific participant at a specific step
- **Function Note**: Note attached to the message/interaction itself
- **Row Number**: Y-position grouping; messages in same row align on same Y
- **Spanning Bracket**: Visual indicator of function scope (duration bar)
- **Verbosity Level**: Low/Normal/High - controls what's displayed

## Resources

- `claude.md` - Rules for Claude's interaction with this project
- `README.md` - Original project documentation
- `Process/` folder - Architecture documents and requirements
- Latest commit messages - Context on what was attempted recently

---

**Last Updated**: March 6, 2026
**Current State**: Note ordering issue in progress, using diagram-based specification approach
