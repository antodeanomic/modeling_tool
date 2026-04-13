# Copilot Instructions for This Repository

Follow `WORKFLOW.md` as the default operating workflow for all non-trivial tasks.

## Mandatory Behavior
- Treat Markdown process artifacts and CSV UML model artifacts as first-class deliverables.
- Maintain traceability from user intent -> Markdown artifacts -> CSV model -> code.
- Keep changes small and explain mapping between artifacts and implementation.
- Ask for confirmation only when blocked or when requirement ambiguity prevents safe progress.
- For connector routing changes, always validate both `diagonal` and `orthogonal` modes in the same response cycle.
- Treat `mixed` routing mode as optional and out of scope unless the user explicitly requests it.

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
- Before commit-oriented milestones, run all tests.

## Reporting Rules
In final responses, include:
- What artifacts were updated
- What code changed
- What validation ran
- Any residual risks or open questions
