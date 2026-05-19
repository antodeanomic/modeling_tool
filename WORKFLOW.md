# Lightweight Guided Development Workflow

This workflow is the default operating model for this repository.

## Goal
Enable a no-code guidance model where the user steers design and priorities, and the agent performs implementation work with visible artifacts.

## Working Agreement
- The user guides the software direction and decisions.
- The agent produces and maintains process artifacts and implementation.
- Markdown + CSV-driven UML are first-class deliverables, not side docs.

## Core Loop

### 1) Define Intent in Markdown
Create or update Markdown artifacts that describe:
- requirements
- assumptions
- constraints
- decisions and rationale
- open questions

Preferred locations:
- `Process/` for durable process and traceability artifacts
- root `*.md` files for implementation summaries and technical notes

Definition of done for this step:
- The feature/change intent is clear enough that another person could implement it.

### 2) Model the Design in CSV (Semicolon Delimited)
Create or update CSV model files that represent architecture/design to be rendered as UML.

Rules:
- Use semicolon (`;`) delimiters only.
- Do not modify `.csv` test files unless explicitly requested.
- Keep hierarchy/structure consistent with existing parser expectations.

Definition of done for this step:
- CSV model captures the target structure and can be rendered.

### 3) Render and Review Visual Output
Render diagrams and review for correctness before implementation-heavy changes.

Review checklist:
- object/group boundaries are clear
- relationships are semantically correct
- routing/readability are acceptable
- design matches Markdown intent

Definition of done for this step:
- Visual model is approved or updated with clear feedback items.

### 4) Implement in Small, Traceable Changes
Apply code changes that map back to approved artifacts.

Rules:
- Keep changes scoped and minimal.
- Preserve existing APIs unless a requirement calls for breaking change.
- Add concise comments only when code is non-obvious.

Definition of done for this step:
- Code behavior aligns with artifacts and user guidance.

### 5) Validate and Report
Run relevant tests and summarize outcomes.

Minimum validation:
- targeted tests for the changed area
- full test suite before commit-sensitive milestones

Report format:
- what changed
- what was validated
- any residual risks/open questions

### 6) Keep Artifacts in Sync
After implementation, update Markdown/CSV so documentation and diagrams match actual behavior.

Definition of done for this step:
- artifacts and code are mutually consistent.

## Session Ritual
For each new request:
1. Clarify the intent and expected artifact(s).
2. Decide whether this is documentation-first, model-first, or code-first.
3. Execute the core loop with short progress updates.
4. End with a concise verification summary.

## Priority Rules
When tradeoffs occur, prioritize in this order:
1. Correctness and safety
2. Traceability from intent -> model -> code
3. Diagram readability and maintainability
4. Speed of delivery

## Conflict Handling
- Treat requirements as the authority over chat when they disagree.
- Do not let a chat request silently override an existing requirement.
- If a conflict appears, stop and surface it explicitly in the response using red bold text, then update the requirement before implementing the change.
- Follow the sequence: discuss the change, revise the requirement artifact, then modify code.

## Repository-Specific Constraints
- Run `refresh.bat` after each response cycle involving repository work.
- Before any commit, run full tests via `Test/run_all_tests_and_view.py` and verify success.
- Use ASCII-only console symbols in Python print output.

## Workflow Compliance Statement
Unless explicitly overridden by the user, this workflow is the default process the agent must follow in this repository.
