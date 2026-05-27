# Claude Project Configuration

**📖 START HERE**: Before working on this project, read [PROJECT_GUIDE.md](PROJECT_GUIDE.md) for comprehensive context on:
- What this project does and why it exists
- How the code architecture works
- How to relearn the project after session breaks
- Development workflow and best practices

This file focuses on specific rules and constraints. The guide covers the broader picture.

---

## Execution Rules

- **After each response cycle involving repository work**: Execute `refresh.bat` to reset the local development environment.
  - Command: `.\refresh.bat`
  - This will:
    - Stop any existing Python server processes
    - Clear Python cache
    - **Not** start the server
    - **Not** open any browser
  - Start server manually when needed:
    - `.\.venv\Scripts\python.exe Scripts\server.py 8000`
    - Open VS Code browser to `http://localhost:8000`

## Requirement Authority Rule

- Requirement documents in `Process/` are the source of truth for all behavior. Chat messages may clarify requirements but never override them.
- For complex Diagram Viewer router problems, apply `Process/ROUTER_INCIDENT_WORKFLOW.md` before implementation-heavy changes.
- **Before starting any non-trivial task**: review the applicable requirement documents in `Process/` and identify any way the chat direction diverges from, extends beyond, or contradicts documented requirements.
- Report ALL detected divergences in bold red text **before writing any code** — even when the chat direction seems like a helpful improvement. The threshold is *any* divergence, not just outright contradiction.
- Identify the specific requirement by name or ID: <strong><span style="color:red">Chat direction diverges from requirement XXXX: [specific difference].</span></strong>
- The correct path is: surface the divergence → discuss → update the requirement document → then implement the code.
- **Never implement a change that silently passes a documented requirement.** Silent requirement drift is the primary cause of functional regressions in this project.
- Root-level `*.md` files (e.g., `CONNECTOR_ARCHITECTURE.md`, `ROUTING_FIX_SUMMARY.md`, `VHV_ROUTING_IMPLEMENTATION.md`) are **historical implementation notes, not requirements**. Do not treat them as prescriptive guidance. Requirements are defined exclusively in `Process/` documents.

## CSV File Rules

- **CRITICAL**: Do NOT modify CSV files under `Test/tests/` unless explicitly instructed by the user. These are regression fixtures — they define what correct output looks like.
- CSV files under `Process/` and `Source/` are formattable documents and may be edited freely.
- **Delimiter**: All CSV files use **semicolons (`;`)** as delimiters, NOT commas. This avoids conflicts with commas in description text.
- When creating or editing CSV files, always use semicolon delimiters
- If a test doesn't pass with the current `Test/tests/` CSV, fix the CODE, not the CSV
- Never change test cases to match code behavior - change code to match test cases

## Console Output Rules

- Use **ASCII only** in print statements — no Unicode symbols (⚠, ✓, ✕, ℹ, etc.)
- Windows cp1252 codepage does not support many Unicode characters
- Use ANSI color codes for emphasis: `\033[91m` (red), `\033[92m` (green), `\033[0m` (reset)

## Project Overview

This is a UML modeling tool (Class Diagrams and Sequence Diagrams) that:
- Parses UML model definitions from CSV files
- Renders them as interactive SVG diagrams
- Provides a web-based UI for viewing and editing

## Key Files

- `Scripts/server.py` - HTTP web server (SimpleHTTPRequestHandler)
- `Scripts/parser.py` - CSV parser for model definitions
- `Scripts/svg_renderer.py` - SVG rendering engine
- `refresh.bat` - Environment cleanup/reset script (no launch)
- `start_server.bat` - Manual server start helper (no browser launch)

## Development Workflow

1. Make changes to code or CSV test files
2. Run `refresh.bat` to reset the environment (cleanup only)
3. **After any code change** (`.py`, `.html`, `.js`): restart the server so the new code is active.
   - Run `refresh.bat`, then immediately start the server: `.\.venv\Scripts\python.exe Scripts\server.py 8000`
   - Do NOT leave the server stopped after a code change — always restart it so the viewer reflects the latest code.
4. Open VS Code browser to `http://localhost:8000`
5. Server automatically reloads CSV files on each request (no restart needed for CSV-only changes)
6. **Before every commit**: Run ALL tests with `cd Test; python run_all_tests_and_view.py` and verify exit code 0. Do not commit if tests fail.

## Renderer Change Policy (Generic-First)

- Treat renderer fixes as global behavior changes by default; avoid one-off logic tied to a single diagram.
- Do not add diagram-id-based or scenario-name-based branching in renderer code unless the user explicitly requests a diagram-specific exception.
- If an exception is unavoidable, document the reason in code comments and add regression coverage for:
  - the exceptional diagram, and
  - at least one non-exception diagram to confirm no collateral behavior change.

## Router Investigation Rule

- When a Diagram Viewer router problem is complex, create or update a routing sequence analysis artifact before broad edits.
- The artifact must follow `Process/ROUTER_INCIDENT_WORKFLOW.md` and preserve green, orange, red, and blue note semantics.
- If the live viewer notation cannot express every color directly, carry the missing semantics in companion Markdown within `Process/`.

## Routing Scope Rule

- Class-diagram routing is orthogonal-only.
- Do not preserve or reintroduce diagonal or mixed class-diagram routing behavior unless the requirement artifacts are explicitly changed first.

## Visual Acceptance Rules

See the full rules in [copilot-instructions.md](.github/copilot-instructions.md). Summary:
- For visual layout/routing/spacing tasks, request a current screenshot and any reference image early in the task.
- Treat reference images and ASCII layout examples as normative visual intent when consistent with requirements.
- Do not treat file hashes, coordinate diffs, or SVG regeneration alone as sufficient verification — compare the rendered result against the visual reference.
- When visual output differs from the reference, describe visible differences explicitly before proposing further changes.

## Troubleshooting Agent Behavior

If the agent is behaving unexpectedly (ignoring rules, not loading customizations, consuming too many tokens):
1. Type `#debugEventsSnapshot` in the chat to attach a snapshot of agent debug events
2. Ask the agent to analyze the snapshot for loaded customizations, token usage, or errors
3. Open the **Agent Debug** panel (sparkle icon top-right) to see detailed logs
4. Use snapshots to verify that `claude.md` rules and `PROJECT_GUIDE.md` context are being loaded correctly
