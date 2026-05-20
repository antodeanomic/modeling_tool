# Copilot Instructions for This Repository

Follow `WORKFLOW.md` as the default operating workflow for all non-trivial tasks.

## Mandatory Behavior
- Treat Markdown process artifacts and CSV UML model artifacts as first-class deliverables.
- Maintain traceability from user intent -> Markdown artifacts -> CSV model -> code.
- Keep changes small and explain mapping between artifacts and implementation.
- Ask for confirmation only when blocked or when requirement ambiguity prevents safe progress.
- Requirement documents in `Process/` outrank chat at all times. Chat may clarify or revise intent, but it never silently overrides a documented requirement.
- **Before starting any non-trivial task**: review the applicable requirement documents in `Process/` and identify any way the chat direction diverges from, extends beyond, or contradicts documented requirements.
- Report ALL detected divergences in bold red text **before writing any code** — even when the chat direction seems like a helpful improvement. The threshold is *any* divergence, not just outright contradiction.
- Identify the specific requirement by name or ID: <strong><span style="color:red">Chat direction diverges from requirement XXXX: [specific difference].</span></strong>
- The resolution sequence is: surface the divergence → discuss → update the requirement artifact → then implement the code.
- **Never implement a change that silently passes a documented requirement.** Silent requirement drift is the primary cause of functional regressions in this project.
- Root-level `*.md` files (e.g., `CONNECTOR_ARCHITECTURE.md`, `ROUTING_FIX_SUMMARY.md`, `VHV_ROUTING_IMPLEMENTATION.md`) are **historical implementation notes, not requirements**. Do not apply them as authoritative guidance. Requirements are defined exclusively in `Process/` documents.
- For connector routing changes, always validate both `diagonal` and `orthogonal` modes in the same response cycle.
- Treat `mixed` routing mode as optional and out of scope unless the user explicitly requests it.

## Renderer Development Rule (Generic-First)
- All renderer changes must be implemented as generic behavior that applies across diagrams.
- Do not add diagram-specific renderer logic (e.g., checks keyed by diagram name or one-off visual exceptions) unless a specific diagram is proven to be uniquely affected.
- Before any diagram-specific exception is introduced, validate at least one additional representative diagram and document why a generic rule cannot solve the issue safely.
- If a diagram-specific exception is approved, keep it isolated, explicitly commented as an exception, and covered by regression tests for both the exception case and at least one non-exception diagram.

## Visual Acceptance Rules
- For visual layout, routing, spacing, labeling, or readability tasks, prefer screenshots or pasted reference images in addition to text requirements.
- When the acceptance criteria are primarily visual, request a current screenshot of the rendered output and any target/reference image early in the task.
- Treat reference images and ASCII layout examples as normative visual intent when they are consistent with the Markdown requirements.
- Do not treat file hashes, coordinate diffs, or SVG regeneration alone as sufficient verification for visual-layout tasks; compare the rendered result against the visual reference and stated requirements.
- When visual output differs from the reference, describe the visible differences explicitly before proposing or making further routing/layout changes.

## CSV Rules
- Use semicolon (`;`) delimiters.
- Never modify `.csv` test files unless explicitly instructed.

## Execution Rules
- After each response cycle involving repository work, execute `refresh.bat`.
- **After any code change** (`.py`, `.html`, `.js`): always restart the server immediately after `refresh.bat`. Never leave the server stopped after a code change.
- Before commit-oriented milestones, run ALL tests with `cd Test; python run_all_tests_and_view.py` and verify exit code 0. Do not commit if tests fail.

## Reporting Rules
In final responses, include:
- What artifacts were updated
- What code changed
- What validation ran
- Any residual risks or open questions
