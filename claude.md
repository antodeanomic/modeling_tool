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
- **Delimiter**: All CSV files use **semicolons (`;`)** as delimiters, NOT commas. This avoids conflicts with commas in description text.
- When creating or editing CSV files, always use semicolon delimiters
- CSV files define the requirements/specifications for the tool
- Modifying CSV files changes the requirements themselves, not the implementation
- If a test doesn't pass with the current CSV, fix the CODE, not the CSV
- Never change test cases to match code behavior - change code to match test cases

## Console Output Rules

- Use **ASCII only** in print statements — no Unicode symbols (⚠, ✓, ✕, ℹ, etc.)
- Windows cp1252 codepage does not support many Unicode characters
- Use ANSI color codes for emphasis: `\033[91m` (red), `\033[92m` (green), `\033[0m` (reset)

## Project Overview

This is a Sequence Diagram modeling tool that:
- Parses sequence diagram models from CSV files
- Renders them as interactive SVG diagrams
- Provides a web-based UI for viewing and editing

## Key Files

- `Scripts/server.py` - HTTP web server (SimpleHTTPRequestHandler)
- `Scripts/parser.py` - CSV parser for model definitions
- `Scripts/svg_renderer.py` - SVG rendering engine
- `refresh.bat` - Server restart and refresh script

## Development Workflow

1. Make changes to code or CSV test files
2. Run `refresh.bat` to see changes reflected immediately
3. Server automatically reloads CSV files on each request (no restart needed for CSV changes)
4. **Before every commit**: Run ALL tests with `cd Test; python run_all_tests_and_view.py` and verify exit code 0. Do not commit if tests fail.

## Troubleshooting Agent Behavior

If the agent is behaving unexpectedly (ignoring rules, not loading customizations, consuming too many tokens):
1. Type `#debugEventsSnapshot` in the chat to attach a snapshot of agent debug events
2. Ask the agent to analyze the snapshot for loaded customizations, token usage, or errors
3. Open the **Agent Debug** panel (sparkle icon top-right) to see detailed logs
4. Use snapshots to verify that `claude.md` rules and `PROJECT_GUIDE.md` context are being loaded correctly
