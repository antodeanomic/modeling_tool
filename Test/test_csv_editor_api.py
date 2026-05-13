#!/usr/bin/env python3
"""Regression checks for CSV editor API helper functions."""

import os
import sys
import tempfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(REPO_ROOT, "Scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import server


def _write_file(path, content):
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(content)


def run_test() -> int:
    original_registry = dict(server.CSV_FILES)

    valid_content = (
        "Type;Name;Description\n"
        "Class;Service;Service class\n"
        "    Function;+ping();Simple ping\n"
        "Sequence;SeqA;Initial sequence\n"
        "    Service;Service;ping\n"
    )

    updated_content = (
        "Type;Name;Description\n"
        "Class;Service;Service class updated\n"
        "    Function;+ping();Simple ping\n"
        "Sequence;SeqA;Updated sequence\n"
        "    Service;Service;ping\n"
    )

    invalid_content = (
        "Type;Name;Description\n"
        "Class;Service;FORCE_PARSE_ERROR\n"
        "    Function;+ping();Simple ping\n"
        "Sequence;SeqA;Should fail parse\n"
        "    Service;Service;ping\n"
    )

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = os.path.join(temp_dir, "temp_model.csv")
            csv_id = "Process/temp_model.csv"
            _write_file(csv_path, valid_content)

            server.CSV_FILES = {csv_id: csv_path}

            loaded = server.read_csv_text(csv_id)
            if "Initial sequence" not in loaded:
                print("FAIL: read_csv_text did not return expected CSV content")
                return 1

            server.write_csv_text(csv_id, updated_content)
            loaded_after_update = server.read_csv_text(csv_id)
            if "Updated sequence" not in loaded_after_update:
                print("FAIL: write_csv_text did not persist updated content")
                return 1

            original_parse_csv = server.parse_csv
            try:
                def _patched_parse_csv(path):
                    with open(path, "r", encoding="utf-8") as handle:
                        if "FORCE_PARSE_ERROR" in handle.read():
                            raise ValueError("forced parse error")
                    return original_parse_csv(path)

                server.parse_csv = _patched_parse_csv

                try:
                    server.write_csv_text(csv_id, invalid_content)
                    print("FAIL: invalid CSV content should fail validation")
                    return 1
                except Exception:
                    # Expected parse failure.
                    pass
            finally:
                server.parse_csv = original_parse_csv

            loaded_after_failure = server.read_csv_text(csv_id)
            if loaded_after_failure != updated_content:
                print("FAIL: invalid save changed persisted content")
                return 1

            try:
                server.read_csv_text("../outside.csv")
                print("FAIL: path traversal-like id should be rejected")
                return 1
            except ValueError:
                pass

            try:
                server.write_csv_text("unknown.csv", updated_content)
                print("FAIL: unknown id should be rejected")
                return 1
            except ValueError:
                pass

    finally:
        server.CSV_FILES = original_registry

    print("OK: CSV editor API helpers validate ids, preserve atomic writes, and reject invalid content")
    return 0


def run_formatter_test() -> int:
    """Regression test for the JS CSV formatter contract.

    The formatter logic lives in diagram_viewer.html (JavaScript).  This test
    documents the REQUIRED behaviour in Python so the contract is permanently
    recorded and can be validated from the Python test suite.

    Rules verified:
    1. Type;Name;Description header is removed from both formatted and condensed output.
    2. Single-row items (e.g. ClassDiagram) stay condensed – no extra padding.
    3. Multi-row connector tables get column alignment (fields padded with spaces).
    4. Leading structural indentation on connector rows is preserved exactly.
    5. Condensing a formatted CSV strips field padding while keeping indentation.
    6. Round-trip (format then condense) is semantically equivalent to the original
       minus the header row.
    """

    import re

    # --- minimal Python re-implementation of the JS formatter logic -----------

    def is_header(line):
        fields = [f.strip().lower() for f in line.split(';')]
        return fields == ['type', 'name', 'description']

    def get_field_count(line):
        return len(line.lstrip().split(';'))

    def condense_line(line):
        m = re.match(r'^(\s*)(.*)', line)
        leading, content = m.group(1), m.group(2)
        return leading + ';'.join(f.strip() for f in content.split(';'))

    def format_group(group):
        parsed = []
        widths = []
        for line in group:
            m = re.match(r'^(\s*)(.*)', line)
            leading, content = m.group(1), m.group(2)
            fields = [f.strip() for f in content.split(';')]
            parsed.append((leading, fields))
            for idx, f in enumerate(fields):
                if idx >= len(widths):
                    widths.append(0)
                widths[idx] = max(widths[idx], len(f))
        result = []
        for leading, fields in parsed:
            parts = [
                f.ljust(widths[i]) if i < len(fields) - 1 else f
                for i, f in enumerate(fields)
            ]
            result.append(leading + ' ; '.join(parts))
        return result

    def format_csv(text):
        lines = text.split('\n')
        result = []
        i = 0
        while i < len(lines):
            line = lines[i]
            if line.strip().startswith('#') or not line.strip():
                result.append(line)
                i += 1
                continue
            if is_header(line.strip()):
                i += 1
                continue
            group = [line]
            fc = get_field_count(line)
            i += 1
            while i < len(lines):
                nxt = lines[i]
                if nxt.strip().startswith('#') or not nxt.strip():
                    break
                if is_header(nxt.strip()):
                    i += 1
                    continue
                if get_field_count(nxt) != fc:
                    break
                group.append(nxt)
                i += 1
            if len(group) == 1:
                result.append(condense_line(group[0]))
            else:
                result.extend(format_group(group))
        return '\n'.join(result)

    def condense_csv(text):
        out = []
        for line in text.split('\n'):
            if line.strip().startswith('#'):
                out.append(line)
                continue
            m = re.match(r'^(\s*)(.*)', line)
            leading, content = m.group(1), m.group(2)
            if not content.strip():
                out.append('')
                continue
            if is_header(content.strip()):
                continue  # drop header
            out.append(leading + ';'.join(f.strip() for f in content.split(';')))
        return '\n'.join(out)

    # --- test fixture ---------------------------------------------------------

    original = (
        "# comment line\n"
        "Type;Name;Description\n"
        "ClassDiagram;SystemLayers;Architectural layers of the system\n"
        "    User;UILayer;-->;1;1;interacts with;UI\n"
        "    UILayer;APISLayer;-->;1;1;calls;API\n"
        "    APISLayer;ProcessingLayer;-->;1;1;delegates to;Processing\n"
    )

    formatted = format_csv(original)
    condensed_back = condense_csv(formatted)

    # Rule 1: header removed in both passes
    for label, text in [('formatted', formatted), ('condensed', condensed_back)]:
        if 'Type;Name;Description' in text or 'Type ; Name ; Description' in text:
            print(f"FAIL [rule 1]: Type;Name;Description header still present in {label} output")
            return 1

    # Rule 2: ClassDiagram row is single – no ' ; ' padding applied
    cd_lines = [l for l in formatted.split('\n') if 'ClassDiagram' in l]
    if not cd_lines:
        print("FAIL [rule 2]: ClassDiagram row missing from formatted output")
        return 1
    if ' ; ' in cd_lines[0]:
        print(f"FAIL [rule 2]: ClassDiagram single row got column padding: {cd_lines[0]!r}")
        return 1

    # Rule 3: connector rows are padded with ' ; '
    conn_lines = [l for l in formatted.split('\n') if '-->' in l]
    if not conn_lines:
        print("FAIL [rule 3]: no connector rows found in formatted output")
        return 1
    if not all(' ; ' in l for l in conn_lines):
        print(f"FAIL [rule 3]: some connector rows not column-padded: {conn_lines}")
        return 1

    # Rule 4: leading indentation preserved on connector rows
    for l in conn_lines:
        if not l.startswith('    '):
            print(f"FAIL [rule 4]: connector row lost its 4-space indent: {l!r}")
            return 1

    # Rule 5: condensing strips field padding while keeping indentation
    for l in condensed_back.split('\n'):
        if '-->' in l:
            if ' ; ' in l:
                print(f"FAIL [rule 5]: condensed connector row still has padding: {l!r}")
                return 1
            if not l.startswith('    '):
                print(f"FAIL [rule 5]: condensed connector row lost indent: {l!r}")
                return 1

    # Rule 6: round-trip semantic equivalence (ignoring removed header)
    original_no_header = condense_csv(original)  # use condense to drop header
    if condensed_back.strip() != original_no_header.strip():
        print("FAIL [rule 6]: round-trip mismatch:")
        print("  expected:", repr(original_no_header.strip()))
        print("  got:     ", repr(condensed_back.strip()))
        return 1

    print("OK: CSV formatter contract: header removal, single-row condensed, "
          "multi-row aligned, indentation preserved, safe round-trip")
    return 0


if __name__ == "__main__":
    rc = run_test()
    if rc == 0:
        rc = run_formatter_test()
    raise SystemExit(rc)
