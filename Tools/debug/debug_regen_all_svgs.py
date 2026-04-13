#!/usr/bin/env python3
"""Temporary debug utility: delete/regenerate SVGs and capture full diagnostics."""

from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path
from datetime import datetime

# Ensure local imports resolve when launched from repo root.
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import server  # noqa: E402
from svg_renderer import render_svg  # noqa: E402
from class_diagram_renderer import render_class_diagram_svg  # noqa: E402

REPORT_PATH = REPO_ROOT / "debug_svg_regen_report.txt"
OUTPUT_DIR = REPO_ROOT / "generated_svgs"


def safe_slug(value: str) -> str:
    keep = []
    for ch in value:
        if ch.isalnum() or ch in ("-", "_", "."):
            keep.append(ch)
        else:
            keep.append("_")
    return "".join(keep).strip("_") or "unnamed"


def write_report(lines: list[str]) -> None:
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    lines: list[str] = []
    now = datetime.now().isoformat(timespec="seconds")

    lines.append(f"Debug SVG regeneration report")
    lines.append(f"Timestamp: {now}")
    lines.append(f"Repo root: {REPO_ROOT}")
    lines.append(f"Python: {sys.executable}")
    lines.append("")

    lines.append("Discovery details")
    lines.append("- search logic: server.find_csv_files_hierarchical + server.find_csv_files")
    lines.append("- all_diagrams source: server.CSV_FILES map")

    hierarchical = server.find_csv_files_hierarchical()
    lines.append(f"- hierarchical entries discovered: {len(hierarchical)}")
    lines.append(f"- unique CSV entries in server.CSV_FILES: {len(server.CSV_FILES)}")
    lines.append("")

    if OUTPUT_DIR.exists():
        for svg_path in OUTPUT_DIR.rglob("*.svg"):
            svg_path.unlink()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    counts = {
        "csv_ok": 0,
        "csv_fail": 0,
        "sequence_ok": 0,
        "sequence_fail": 0,
        "class_ok": 0,
        "class_fail": 0,
    }

    failures: list[str] = []

    for csv_key in sorted(server.CSV_FILES.keys()):
        csv_abs_path = server.CSV_FILES[csv_key]
        lines.append(f"CSV_KEY: {csv_key}")
        lines.append(f"CSV_PATH: {csv_abs_path}")
        lines.append("SEARCH_CONTEXT: discovered via server.CSV_FILES traversal")

        try:
            model = server.load_model(csv_key)
            counts["csv_ok"] += 1
            lines.append(
                f"PARSE_OK: sequences={len(model.sequences)} class_diagrams={len(model.class_diagrams)}"
            )
        except Exception as exc:
            counts["csv_fail"] += 1
            err = f"PARSE_FAIL: {type(exc).__name__}: {exc}"
            lines.append(err)
            failures.append(f"{csv_key} :: {err}")
            lines.append("")
            continue

        for seq in model.sequences:
            out_name = f"{safe_slug(csv_key)}__sequence__{safe_slug(seq.seq_id)}__High.svg"
            out_path = OUTPUT_DIR / out_name
            try:
                svg = render_svg(model, seq, verbosity_level="High", lanes_filter=None)
                out_path.write_text(svg, encoding="utf-8")
                counts["sequence_ok"] += 1
                lines.append(
                    f"SEQUENCE_OK: id={seq.seq_id} out={out_path.relative_to(REPO_ROOT)}"
                )
            except Exception as exc:
                counts["sequence_fail"] += 1
                err = f"SEQUENCE_FAIL: id={seq.seq_id} {type(exc).__name__}: {exc}"
                lines.append(err)
                failures.append(f"{csv_key} :: {err}")
                lines.append(traceback.format_exc().rstrip())

        for diag in model.class_diagrams:
            out_name = f"{safe_slug(csv_key)}__class__{safe_slug(diag.diagram_id)}__orthogonal__High.svg"
            out_path = OUTPUT_DIR / out_name
            try:
                # Match server policy used by /api/diagram for class diagrams.
                diag.routing = "orthogonal"
                svg = render_class_diagram_svg(
                    model,
                    diag,
                    verbosity_level="High",
                    layers_filter=None,
                )
                out_path.write_text(svg, encoding="utf-8")
                counts["class_ok"] += 1
                lines.append(
                    f"CLASS_OK: id={diag.diagram_id} name={diag.description or diag.diagram_id} out={out_path.relative_to(REPO_ROOT)}"
                )
            except Exception as exc:
                counts["class_fail"] += 1
                err = (
                    f"CLASS_FAIL: id={diag.diagram_id} name={diag.description or diag.diagram_id} "
                    f"{type(exc).__name__}: {exc}"
                )
                lines.append(err)
                failures.append(f"{csv_key} :: {err}")
                lines.append(traceback.format_exc().rstrip())

        lines.append("")

    lines.append("Summary")
    lines.append(f"- csv_ok: {counts['csv_ok']}")
    lines.append(f"- csv_fail: {counts['csv_fail']}")
    lines.append(f"- sequence_ok: {counts['sequence_ok']}")
    lines.append(f"- sequence_fail: {counts['sequence_fail']}")
    lines.append(f"- class_ok: {counts['class_ok']}")
    lines.append(f"- class_fail: {counts['class_fail']}")

    generated_total = len(list(OUTPUT_DIR.rglob("*.svg")))
    lines.append(f"- generated_svg_files: {generated_total}")

    lines.append("")
    lines.append("Failure list")
    if failures:
        for item in failures:
            lines.append(f"- {item}")
    else:
        lines.append("- none")

    write_report(lines)
    print(f"Wrote report: {REPORT_PATH}")
    print(f"Generated SVG directory: {OUTPUT_DIR}")
    print(f"Generated SVG count: {generated_total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
