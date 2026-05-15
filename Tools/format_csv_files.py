#!/usr/bin/env python3
"""Batch-format CSV model files using the Diagram Viewer formatter contract."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKIP_DIR_NAMES = {".git", ".venv", "__pycache__"}
SKIP_PATH_PARTS = {"generated_svgs"}


def is_header_row(line: str) -> bool:
    fields = [field.strip().lower() for field in parse_semicolon_fields(line)]
    return len(fields) >= 3 and fields[0] == "type" and fields[1] == "name" and fields[2] == "description"


def parse_semicolon_fields(line: str) -> list[str]:
    try:
        row = next(csv.reader([line], delimiter=";", quotechar='"', skipinitialspace=True))
        fields = [field.strip() for field in row]
        if fields:
            fields[0] = fields[0].lstrip("\ufeff")
        return fields
    except Exception:
        fields = [field.strip() for field in line.split(";")]
        if fields:
            fields[0] = fields[0].lstrip("\ufeff")
        return fields


def encode_csv_field(value: str) -> str:
    text = "" if value is None else str(value)
    if any(ch in text for ch in (';', '"', '\n', '\r')):
        return '"' + text.replace('"', '""') + '"'
    return text


def join_csv_fields(fields: list[str], separator: str) -> str:
    return separator.join(encode_csv_field(field) for field in fields)


def serialized_field_width(field: str) -> int:
    return len(encode_csv_field(field))


def get_field_count(line: str) -> int:
    return len(parse_semicolon_fields(line.lstrip()))


def split_indent(line: str) -> tuple[str, str]:
    stripped = line.lstrip(" ")
    return line[: len(line) - len(stripped)], stripped


def to_condensed_line(line: str) -> str:
    leading, content = split_indent(line)
    return leading + join_csv_fields(parse_semicolon_fields(content), ";")


def get_type_name(line: str) -> str:
    _, content = split_indent(line)
    parsed = parse_semicolon_fields(content) if content else []
    first_field = parsed[0] if parsed else ""
    return first_field.strip()


def is_indented_row(line: str) -> bool:
    return bool(line[: len(line) - len(line.lstrip(" "))])


def is_note_type_field(field: str) -> bool:
    return field in {"@Info", "@Warning", "@Error", "@Success"}


def is_note_token(field: str) -> bool:
    return field.strip().startswith("@")


def classify_sequence_row(fields: list[str]) -> str:
    return "note" if len(fields) > 1 and is_note_token(fields[1]) else "step"


def format_sequence_rows(group_lines: list[str]) -> list[str]:
    widths_by_kind: dict[str, dict[str, list[int]]] = {}
    parsed: list[tuple[str, list[str], str]] = []

    for line in group_lines:
        leading, content = split_indent(line)
        fields = parse_semicolon_fields(content)
        kind = classify_sequence_row(fields)
        widths = widths_by_kind.setdefault(kind, {"text": [], "note": []})

        for idx, field in enumerate(fields):
            if idx == len(fields) - 1:
                continue
            bucket_name = "note" if is_note_token(field) else "text"
            bucket = widths[bucket_name]
            if idx >= len(bucket):
                bucket.extend([0] * (idx + 1 - len(bucket)))
            bucket[idx] = max(bucket[idx], serialized_field_width(field))

        parsed.append((leading, fields, kind))

    formatted_lines: list[str] = []
    for leading, fields, kind in parsed:
        widths = widths_by_kind[kind]
        padded_serialized: list[str] = []
        for idx, field in enumerate(fields):
            serialized = encode_csv_field(field)
            if idx == len(fields) - 1:
                padded_serialized.append(serialized)
                continue
            bucket = widths["note"] if is_note_token(field) else widths["text"]
            width = bucket[idx] if idx < len(bucket) and bucket[idx] > 0 else serialized_field_width(field)
            padded_serialized.append(serialized.ljust(width))
        formatted_lines.append(leading + " ; ".join(padded_serialized))

    return formatted_lines


def format_group(group_lines: list[str]) -> list[str]:
    column_widths: list[int] = []
    parsed_lines: list[tuple[str, list[str]]] = []

    for line in group_lines:
        leading, content = split_indent(line)
        fields = parse_semicolon_fields(content)
        parsed_lines.append((leading, fields))
        for idx, field in enumerate(fields):
            if idx >= len(column_widths):
                column_widths.append(0)
            column_widths[idx] = max(column_widths[idx], serialized_field_width(field))

    formatted_lines = []
    for leading, fields in parsed_lines:
        padded_serialized = []
        for idx, field in enumerate(fields):
            serialized = encode_csv_field(field)
            if idx == len(fields) - 1 or is_note_type_field(field):
                padded_serialized.append(serialized)
            else:
                padded_serialized.append(serialized.ljust(column_widths[idx]))
        formatted_lines.append(leading + " ; ".join(padded_serialized))
    return formatted_lines


def format_csv_text(text: str) -> str:
    newline = "\r\n" if "\r\n" in text else "\n"
    normalized = text.replace("\r\n", "\n")
    trailing_newline = normalized.endswith("\n")
    lines = normalized.split("\n")
    if trailing_newline:
        lines = lines[:-1]

    result: list[str] = []
    idx = 0
    current_top_level_type = ""
    while idx < len(lines):
        line = lines[idx]
        stripped = line.strip()

        if stripped and not stripped.startswith("#") and not is_indented_row(line):
            current_top_level_type = get_type_name(line)

        if not stripped or stripped.startswith("#"):
            result.append(line)
            idx += 1
            continue

        if is_header_row(stripped):
            idx += 1
            continue

        if current_top_level_type == "Sequence" and is_indented_row(line):
            sequence_rows: list[str] = []
            while idx < len(lines):
                candidate = lines[idx]
                candidate_stripped = candidate.strip()
                if not candidate_stripped or candidate_stripped.startswith("#"):
                    break
                if not is_indented_row(candidate) or is_header_row(candidate_stripped):
                    break
                sequence_rows.append(candidate)
                idx += 1
            result.extend(format_sequence_rows(sequence_rows))
            continue

        group = [line]
        field_count = get_field_count(line)
        idx += 1

        while idx < len(lines):
            next_line = lines[idx]
            next_stripped = next_line.strip()
            if not next_stripped or next_stripped.startswith("#"):
                break
            if is_header_row(next_stripped):
                idx += 1
                continue
            if get_field_count(next_line) != field_count:
                break
            group.append(next_line)
            idx += 1

        keep_table_format = get_type_name(group[0]) == "ClassDiagram"

        if len(group) == 1 and not keep_table_format:
            result.append(to_condensed_line(group[0]))
        else:
            result.extend(format_group(group))

    output = "\n".join(result)
    if trailing_newline:
        output += "\n"
    return output.replace("\n", newline)


def iter_csv_files(root: Path) -> list[Path]:
    csv_files = []
    for path in root.rglob("*.csv"):
        if any(part in SKIP_DIR_NAMES for part in path.parts):
            continue
        if any(part in SKIP_PATH_PARTS for part in path.parts):
            continue
        csv_files.append(path)
    return sorted(csv_files)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Report files that would change without writing them")
    args = parser.parse_args()

    changed_files: list[Path] = []
    for csv_file in iter_csv_files(REPO_ROOT):
        original = csv_file.read_text(encoding="utf-8")
        formatted = format_csv_text(original)
        if formatted == original:
            continue
        changed_files.append(csv_file)
        if not args.check:
            csv_file.write_text(formatted, encoding="utf-8")

    mode = "Would update" if args.check else "Updated"
    print(f"{mode} {len(changed_files)} CSV files")
    for csv_file in changed_files:
        print(csv_file.relative_to(REPO_ROOT).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
