# Traceability Links Example - WORKING IMPLEMENTATION

This document shows how clickable traceability works in practice. **All links below are functional!**

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

---

## Customer Requirements

| ID | Requirement | Satisfies | Rationale |
|---|---|---|---|
| <a id="creq-001"></a>[**CREQ-001**](#creq-001) | **Defined process re-uses existing software processes** | [US-001](#us-001), [US-002](#us-002), [US-003](#us-003), [US-004](#us-004) | Leverage proven workflow patterns |
| <a id="creq-002"></a>[**CREQ-002**](#creq-002) | **Render UML-like diagrams from input .csv files** | [US-001](#us-001), [US-002](#us-002), [US-003](#us-003), [US-004](#us-004) | CSV is human-readable and version-controllable |
| <a id="creq-003"></a>[**CREQ-003**](#creq-003) | **High-level project guide** | [US-001](#us-001), [US-002](#us-002) | Onboard new developers efficiently |
| <a id="creq-004"></a>[**CREQ-004**](#creq-004) | **Preview viewer with instant diagram updates** | [US-003](#us-003), [US-004](#us-004) | Fast feedback during modeling |

---

## User Stories

| ID | Story | Implements | Enabled By |
|---|---|---|---|
| <a id="us-001"></a>[**US-001**](#us-001) | **Give instructions to sequence diagram tool** | [CREQ-001](#creq-001), [CREQ-002](#creq-002) | Parser ([FEAT-001](#feat-001)), Renderer ([FEAT-002](#feat-002)) |
| <a id="us-002"></a>[**US-002**](#us-002) | **View diagram output in interactive web page** | [CREQ-001](#creq-001), [CREQ-002](#creq-002) | Web Viewer ([FEAT-006](#feat-006)), Renderer ([FEAT-002](#feat-002)) |
| <a id="us-003"></a>[**US-003**](#us-003) | **Filter diagram complexity** | [CREQ-001](#creq-001), [CREQ-004](#creq-004) | Verbosity Control ([FEAT-007](#feat-007)), Renderer ([FEAT-006](#feat-006)) |
| <a id="us-004"></a>[**US-004**](#us-004) | **View runtime specs and model metadata** | [CREQ-001](#creq-001), [CREQ-004](#creq-004) | Spec Display ([FEAT-013](#feat-013)), Web Server (FEAT-011) |

---

## Features (MVP)

| ID | Feature | Implements | Test File |
|---|---|---|---|
| <a id="feat-001"></a>[**FEAT-001**](#feat-001) | **CSV Parser** | [US-001](#us-001) | test_code_syntax.csv |
| <a id="feat-002"></a>[**FEAT-002**](#feat-002) | **SVG Renderer** | [US-001](#us-001), [US-002](#us-002) | test_multirow.csv |
| <a id="feat-006"></a>[**FEAT-006**](#feat-006) | **Web Viewer** | [US-001](#us-001), [US-002](#us-002), [US-003](#us-003) | All tests |
| <a id="feat-007"></a>[**FEAT-007**](#feat-007) | **Verbosity Control** | [US-003](#us-003) | test_verbosity.csv |
| <a id="feat-013"></a>[**FEAT-013**](#feat-013) | **Spec Display** | [US-004](#us-004) | test_parameters.csv |

---

## Try It Now

**To test these links in VS Code:**

1. Open this file in markdown preview (Ctrl+Shift+V)
2. Click [CREQ-001](#creq-001) → jumps to Customer Requirements section
3. Click [US-002](#us-002) anywhere it appears → jumps to User Stories section  
4. Click [FEAT-006](#feat-006) in the "Enabled By" column → jumps to Features section
5. **All ID references are clickable** - trace through the entire hierarchy!

**Full bidirectional traceability:**
- ✅ Click any ID in the ID column to jump to that requirement
- ✅ Click referenced IDs in other columns to navigate to them
- ✅ Navigate freely: CREQ→US→FEAT and back again
- ✅ Every identifier reference is clickable and navigable
- ✅ Respects dark mode and your markdown settings
