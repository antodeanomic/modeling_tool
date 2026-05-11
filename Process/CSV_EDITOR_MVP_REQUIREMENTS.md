# CSV Editor Pane for Diagram Viewer

## Objective
Add an optional CSV editor pane to the left side of the Diagram Viewer so users can quickly edit diagram source CSV content and immediately re-render the selected diagram on the right.

## Problem Statement
Current workflow requires switching between files/editor and browser repeatedly. This slows iteration when creating and validating alternate test-case scenarios.

## Primary User Workflow
1. User selects a diagram in the palette.
2. Viewer loads the associated CSV file text into a left-side editor pane.
3. User edits CSV content.
4. User saves changes.
5. Server writes file and re-parses model.
6. Diagram on the right reloads using updated CSV.
7. If parse fails, user sees actionable error and file is not silently corrupted.

## Scope
### In Scope (MVP)
- Optional left-side CSV editor pane in `Scripts/diagram_viewer.html`.
- Load selected diagram's source CSV text via API.
- Save edited CSV back to disk via API.
- Manual save trigger (`Save` button + `Ctrl+S`).
- Diagram refresh after successful save.
- Parse/validation error feedback in UI.
- Dirty-state indicator (`Unsaved changes`).

### Out of Scope (MVP)
- Full IDE-grade editor features (folding, linting, semantic intellisense).
- Collaborative editing.
- Multi-file transactional edits.
- Auto-save on every keystroke.
- Arbitrary path editing outside known CSV registry.

## Non-Functional Requirements
- Preserve existing Diagram Viewer behavior when editor is hidden.
- No performance regression for normal diagram browsing.
- Safe file writes (no path traversal; only known CSV files may be read/written).
- Clear error handling for parse errors and file I/O failures.

## UI/UX Requirements
- Split layout: left editor pane, right diagram pane.
- Editor pane toggle (show/hide) with persisted state in local storage.
- Save button with enabled/disabled state based on dirty content.
- Visible status line:
  - `Saved`
  - `Unsaved changes`
  - `Error: <message>`
- On diagram switch with unsaved edits, prompt user:
  - Discard
  - Cancel

## Backend API Requirements
Add endpoints in `Scripts/server.py`:

### `GET /api/csv_text?csv=<id>`
- Returns raw CSV text for a known CSV id.
- Response: `200 text/plain`.
- Errors:
  - `400` unknown csv id
  - `500` read failure

### `POST /api/csv_text`
- Request JSON:
  - `csv`: csv id
  - `content`: full file text
- Behavior:
  1. Validate csv id maps to allowed file path.
  2. Write content atomically (temp file + replace preferred).
  3. Parse CSV using existing parser path to validate.
  4. Return success or parse error details.
- Response:
  - `200` `{ "ok": true }`
  - `400` `{ "ok": false, "error": "..." }`

## Data Safety Rules
- Only allow `csv` values that exist in server CSV registry.
- Reject absolute paths and unknown ids.
- Keep UTF-8 handling consistent with existing parser behavior.
- Preserve semicolon delimiter expectation.

## Error Handling Requirements
- Parse error message must surface in the editor status area.
- Save failure must not clear dirty state.
- Diagram must not auto-refresh on failed save.

## Implementation Approach
### Phase 1: API Layer
1. Add secure CSV read endpoint.
2. Add secure CSV write endpoint.
3. Reuse existing parse/validation path after write.
4. Return concise structured errors.

### Phase 2: Viewer UI
1. Add split-pane container.
2. Add textarea editor (MVP) and controls (`Save`, `Toggle Editor`).
3. Wire load-on-diagram-select.
4. Track dirty state and prompt on navigation.
5. On successful save, reload diagram and metadata.

### Phase 3: Hardening
1. Keyboard shortcut (`Ctrl+S`).
2. Basic resize support for split pane.
3. Improve status/notification messages.
4. Add focused tests.

## Acceptance Criteria
1. Selecting any diagram loads correct CSV text in editor pane.
2. Editing + Save updates file on disk.
3. Diagram re-renders from updated content after save.
4. Invalid CSV save shows parse error and does not silently fail.
5. Hidden editor mode leaves existing viewer workflow unchanged.
6. Unknown/malicious CSV ids are rejected server-side.

## Test Plan (Initial)
- API tests:
  - valid read
  - invalid csv id read
  - valid write
  - invalid write parse failure
- UI tests/manual:
  - load, edit, save, refresh diagram
  - unsaved-change prompt on diagram switch
  - toggle pane persistence

## Suggested Future Enhancements
- Monaco editor integration.
- `Save As` for alternate scenario generation.
- Inline parse error line mapping.
- Optional live preview mode with debounce.

## Estimated Effort
- MVP implementation: 4-8 hours.
- Polished version: 1-2 days.

## Open Decisions for Kickoff
1. Keep MVP editor as `<textarea>` or jump directly to Monaco?
2. Validate-on-save only (recommended) vs optional live validation toggle?
3. Add `Save As` in MVP or defer?
