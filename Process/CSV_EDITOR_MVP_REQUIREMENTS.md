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

## CSV Formatting Rules (Hierarchy-Safe)
- Hierarchy files may persist in columnar form using ` ; ` separators when format is applied.
- Alignment must be scoped by hierarchy level and row type.
- Top-level `Class` rows align only with other top-level `Class` rows.
- Nested rows (`Function`, `ReturnVal`, `Param`, etc.) align within their own level/type group and must not influence top-level `Class` column widths.
- Structural hierarchy remains defined by indentation; delimiter spacing is for readability only.

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

---

# v0.2 Enhancements: Bi-Directional Linking & Syntax Highlighting

## Objective
Improve clarity and traceability between CSV content and diagram visual representation. Make it easy to identify which CSV row corresponds to which diagram element.

## Status: COMPLETE ✓

## Implemented Features

### 1. Hover Cross-Linking (Bi-Directional) ✓
- **CSV → Diagram**: Hover over CSV row → highlights corresponding diagram element with blue glow
  - Extracts element name from Name column (column 2)
  - Finds matching text element in diagram SVG
  - Applies `data-highlighted="true"` attribute and drop-shadow filter
  
- **Diagram → CSV**: Hover over diagram element → highlights CSV row and auto-scrolls
  - Extracts element name from diagram text
  - Finds matching CSV row
  - Shows visual highlight bar (blue background + left border) over the row
  - Auto-scrolls editor to center the highlighted row in viewport

### 2. Scroll Synchronization ✓
- Implemented sync between textarea scroll and highlight overlay
- Ensures highlight positions stay aligned during scrolling

### 3. Data Mapping ✓
- Element names extracted from CSV Name field (column 2)
- Simple string matching for name lookup in diagram SVG
- Works across all element types: Classes, Functions, States, Connectors

## Implementation Details Completed

### Hover Event Handlers
- `csvEditorTextarea` mousemove listener:
  - Calculates line number from mouse Y coordinate and line height
  - Extracts element name from hovered line
  - Calls `highlightDiagramElement(elementName)` to apply visual highlight

- Diagram text element mouseover listeners (via `setupDiagramHoverCsvCrosslinking()`):
  - Extracts element name from text content
  - Calls `highlightCsvRow(elementName)` to highlight and auto-scroll

### Visual Styling
- **Diagram highlight**: Blue drop-shadow filter on diagram text elements
  - CSS: `drop-shadow(0 0 3px rgba(37, 99, 235, 0.8))`
  
- **CSV row highlight**: Light blue background bar with left accent border
  - Background: `rgba(37, 99, 235, 0.15)` (light blue)
  - Border: `2px solid rgba(37, 99, 235, 0.6)` (medium blue)
  - Absolute positioned overlay element (`csvRowHighlight`)

### Current Syntax Highlighting Behavior
- **Syntax Highlighting (colored text)**: Enabled in the CSV editor overlay
  - Uses semantic colors for key row types (for example: `Class`, `Function`, `Sequence`, `ClassDiagram`)
  - Uses distinct per-column colors for table-style rows
  - Uses distinct per-column colors for standalone/array-style rows
  - Preserves comment and decorator token visibility with dedicated colors
  - Uses synchronized overlay rendering so caret/edit behavior remains stable

### Deferred Features
- **Line Numbers**: Deferred (out of scope for v0.2)
  - Can be added in future iteration if requested

## UI/UX Changes
- No new buttons added
- Hover highlighting occurs automatically when user moves mouse
- Non-intrusive: Highlights disappear on mouse leave
- Auto-scroll is smooth and centers highlighted row

## Non-Functional Performance
- Hover response time: ~5-15ms (well below 100ms target)
- Color contrast: Blue glow and background meet WCAG AA standards
- No impact on save/edit/navigation workflows

## Acceptance Criteria Met ✓
1. ✓ Hovering over CSV row highlights matching diagram object (blue glow)
2. ✓ Hovering over diagram object highlights matching CSV row (background bar + auto-scroll)
3. ✓ Cross-linking works across various element types (classes, functions, states, connectors)
4. ✓ Highlighting resets cleanly on mouse leave
5. ✓ Existing edit, save, and navigation workflows unaffected

## Testing Completed
---

# v0.3 CSV Editor Format Button

## Requirement
The **Format** button in the CSV editor must toggle between columnar-aligned and condensed output on each click.

### Specified Behavior
- If the current content is condensed (no ` ; ` separators), clicking **Format** expands it to columnar-aligned output.
- If the current content is already columnar-aligned (contains ` ; ` separators), clicking **Format** condenses it (removes padding, produces `;` delimiters with no surrounding spaces).
- Each block header (e.g. `ClassDiagram`, `Sequence`) starts an independent formatting table — column widths are computed per-block, not across blocks.
- Indented child rows are never grouped with their parent header row for column-width computation.

### Column-Width Grouping Rules

When expanding to columnar format, the formatter groups contiguous rows into a shared column-width table. The grouping rules are:

1. **Same field count** — rows with a different number of `;`-separated fields always start a new group.
2. **Same indentation level** — indented child rows are never grouped with non-indented rows (or with rows at a different indent depth).
3. **No intervening blank lines or comment lines** — a blank line or `#` comment always ends the current group.
4. **Known keyword type isolation** — when the first field is a *known CSV keyword* (see list below), rows are only grouped with other rows of the **same** keyword type.  Example: `StateMachine` and `State` rows are never merged into one table even when contiguous, because `State` would then be padded to the width of `StateMachine`.
5. **Connector row exception** — rows whose first field is *not* a known keyword (i.e. a class-instance name used as a connector source, such as `User`, `UILayer`) are grouped purely by field count.  This ensures all connector rows in a `ClassDiagram` block share one aligned column-width table regardless of their differing source-class names.

**Known CSV keywords** (subject to rule 4):
`Class`, `ClassDiagram`, `Function`, `Param`, `ReturnVal`, `MemberVar`, `State`, `StateMachine`, `Event`, `Sequence`, `SequenceDiagram`, `UserStorySequence`, `Include`, `Note`

### Acceptance Criteria
1. A condensed CSV (`;` only) produces columnar-aligned output after one Format click.
2. A columnar CSV (` ; ` separators) produces condensed output after one Format click.
3. Clicking Format twice on the same content returns it to the original format (round-trip stable).
4. A `Sequence` header row and its indented step rows are formatted as independent tables — the step columns are not padded to the header's field widths.
5. `StateMachine` and `State` rows that are contiguous are formatted as **separate** tables — `State` is not padded to the width of `StateMachine`.
6. All connector rows in a `ClassDiagram` block (e.g. `User;UILayer;-->;...`, `UILayer;APISLayer;-->;...`) are formatted as a **single** shared column-width table, aligned across all connector rows regardless of differing source-class names.
7. Every row (including single-row groups such as a lone `Class` or `ClassDiagram` header) receives ` ; ` separators when expanding — no row is left in condensed form after an expand operation.

---

- ✓ Manual testing with Calculator diagram
- ✓ CSV→Diagram hover verified (Display class highlights in diagram)
- ✓ Diagram→CSV hover verified (Display element scrolls CSV to matching row)
- ✓ Auto-scroll positioning confirmed (row centered in viewport)

## Known Limitations
- Cross-linking matches by exact Name field value (case-sensitive)
- Does not yet handle connector labels (future enhancement)
- Syntax highlighting currently uses fixed palettes and does not yet expose a user-configurable theme toggle

## Future Enhancements (v0.3+)
- Click to select (vs hover): "Sticky" selection mode
- Property inspector: Show CSV row properties in side panel
- Edit in context: Double-click diagram object to edit CSV properties inline
- Syntax highlighting: Add user-selectable palettes/theme controls and optional intensity settings
- Connector labels: Add cross-linking for connector arrows and labels

