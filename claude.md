# Claude Project Configuration

**📖 START HERE**: Before working on this project, read [PROJECT_GUIDE.md](PROJECT_GUIDE.md) for comprehensive context on:
- What this project does and why it exists
- How the code architecture works
- How to relearn the project after session breaks
- Development workflow and best practices

This file focuses on specific rules and constraints. The guide covers the broader picture.

---

## Execution Rules

- **After every chat message**: Execute `refresh.bat` to restart the development server and ensure all changes are reflected in the running application.
  - Command: `.\refresh.bat`
  - This will:
    - Stop any existing Python server processes
    - Clear Python cache
    - Start the server on port 8000
    - Open the browser to http://localhost:8000
    - Log all output to `server_output.log`

## CSV File Rules

- **CRITICAL**: Do NOT modify any `.csv` test files unless explicitly instructed by the user
- CSV files define the requirements/specifications for the tool
- Modifying CSV files changes the requirements themselves, not the implementation
- If a test doesn't pass with the current CSV, fix the CODE, not the CSV
- Never change test cases to match code behavior - change code to match test cases

## Project Overview

This is a Sequence Diagram modeling tool that:
- Parses sequence diagram models from CSV files
- Renders them as interactive SVG diagrams
- Provides a web-based UI for viewing and editing

## Key Files

- `Scripts/server.py` - Flask web server
- `Scripts/parser.py` - CSV parser for model definitions
- `Scripts/svg_renderer.py` - SVG rendering engine
- `refresh.bat` - Server restart and refresh script

## Development Workflow

1. Make changes to code or CSV test files
2. Run `refresh.bat` to see changes reflected immediately
3. Server automatically reloads CSV files on each request (no restart needed for CSV changes)

## Troubleshooting Agent Behavior

If the agent is behaving unexpectedly (ignoring rules, not loading customizations, consuming too many tokens):
1. Type `#debugEventsSnapshot` in the chat to attach a snapshot of agent debug events
2. Ask the agent to analyze the snapshot for loaded customizations, token usage, or errors
3. Open the **Agent Debug** panel (sparkle icon top-right) to see detailed logs
4. Use snapshots to verify that `claude.md` rules and `PROJECT_GUIDE.md` context are being loaded correctly
