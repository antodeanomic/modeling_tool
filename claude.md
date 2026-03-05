# Claude Project Configuration

This file contains guidelines and rules for Claude when working in this project.

## Execution Rules

- **After every chat message**: Execute `refresh.bat` to restart the development server and ensure all changes are reflected in the running application.
  - Command: `.\refresh.bat`
  - This will:
    - Stop any existing Python server processes
    - Clear Python cache
    - Start the server on port 8000
    - Open the browser to http://localhost:8000
    - Log all output to `server_output.log`

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
