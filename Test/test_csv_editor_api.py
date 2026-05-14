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
import parser as csv_parser


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
     1. Type;Name;Description headers are removed from both formatted and condensed output,
         including extended headers like Type;Name;Description;Layer.
    2. Single-row ClassDiagram items use table-style separators.
    3. Single-row sequence-step groups also use table-style separators.
    4. Multi-row connector tables get column alignment (fields padded with spaces).
    5. Sequence note-type fields like @Info are left-aligned and not padded.
    6. Leading structural indentation on connector rows is preserved exactly.
    7. Condensing a formatted CSV strips field padding while keeping indentation.
    8. Round-trip (format then condense) is semantically equivalent to the original
         minus the header row.
    """

    import re

    # --- minimal Python re-implementation of the JS formatter logic -----------

    def is_header(line):
        fields = [f.strip().lower() for f in line.split(';')]
        return len(fields) >= 3 and fields[:3] == ['type', 'name', 'description']

    def get_field_count(line):
        return len(line.lstrip().split(';'))

    def condense_line(line):
        m = re.match(r'^(\s*)(.*)', line)
        leading, content = m.group(1), m.group(2)
        return leading + ';'.join(f.strip() for f in content.split(';'))

    def get_type_name(line):
        return line.lstrip().split(';')[0].strip()

    def is_indented_row(line):
        return bool(line[: len(line) - len(line.lstrip(' '))])

    def is_note_token(field):
        return field.strip().startswith('@')

    def classify_sequence_row(fields):
        return 'note' if len(fields) > 1 and is_note_token(fields[1]) else 'step'

    def is_note_type_field(field):
        return field in {'@Info', '@Warning', '@Error', '@Success'}

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
                f if i == len(fields) - 1 or is_note_type_field(f) else f.ljust(widths[i])
                for i, f in enumerate(fields)
            ]
            result.append(leading + ' ; '.join(parts))
        return result

    def format_sequence_rows(group):
        parsed = []
        widths_by_kind = {}

        for line in group:
            m = re.match(r'^(\s*)(.*)', line)
            leading, content = m.group(1), m.group(2)
            fields = [f.strip() for f in content.split(';')]
            kind = classify_sequence_row(fields)
            if kind not in widths_by_kind:
                widths_by_kind[kind] = {'text': [], 'note': []}
            widths = widths_by_kind[kind]

            for idx, f in enumerate(fields):
                if idx == len(fields) - 1:
                    continue
                bucket_name = 'note' if is_note_token(f) else 'text'
                bucket = widths[bucket_name]
                if idx >= len(bucket):
                    bucket.extend([0] * (idx + 1 - len(bucket)))
                bucket[idx] = max(bucket[idx], len(f))

            parsed.append((leading, fields, kind))

        result = []
        for leading, fields, kind in parsed:
            widths = widths_by_kind[kind]
            parts = []
            for idx, f in enumerate(fields):
                if idx == len(fields) - 1:
                    parts.append(f)
                    continue
                bucket = widths['note'] if is_note_token(f) else widths['text']
                width = bucket[idx] if idx < len(bucket) and bucket[idx] > 0 else len(f)
                parts.append(f.ljust(width))
            result.append(leading + ' ; '.join(parts))
        return result

    def format_csv(text):
        lines = text.split('\n')
        result = []
        i = 0
        current_top_level_type = ''
        while i < len(lines):
            line = lines[i]
            if line.strip() and not line.strip().startswith('#') and not is_indented_row(line):
                current_top_level_type = get_type_name(line)
            if line.strip().startswith('#') or not line.strip():
                result.append(line)
                i += 1
                continue
            if is_header(line.strip()):
                i += 1
                continue

            if current_top_level_type == 'Sequence' and is_indented_row(line):
                sequence_rows = []
                while i < len(lines):
                    nxt = lines[i]
                    nxt_trimmed = nxt.strip()
                    if not nxt_trimmed or nxt_trimmed.startswith('#'):
                        break
                    if not is_indented_row(nxt) or is_header(nxt_trimmed):
                        break
                    sequence_rows.append(nxt)
                    i += 1
                result.extend(format_sequence_rows(sequence_rows))
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
            keep_table_format = get_type_name(group[0]) == 'ClassDiagram'
            if len(group) == 1 and not keep_table_format:
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
        "Type;Name;Description;Layer\n"
        "ClassDiagram;SystemLayers;Architectural layers of the system\n"
        "    User;UILayer;-->;1;1;interacts with;UI\n"
        "    UILayer;APISLayer;-->;1;1;calls;API\n"
        "    APISLayer;ProcessingLayer;-->;1;1;delegates to;Processing\n"
        "Sequence;SEQ_001;Example sequence\n"
        "    Client;LoginForm;EnterCredentials;username;password;-;@Info;User enters credentials\n"
        "    LoginForm;APIGateway;Authenticate;username;password;token;@Info;Submit login request\n"
        "    AuthService;UserDB;QueryUser;username;user;@Info;Look up user record\n"
        "    UserDB;AuthService;QueryUser;user\n"
        "    Client;@Warning;Session timeout approaching\n"
    )

    formatted = format_csv(original)
    condensed_back = condense_csv(formatted)

    # Rule 1: header removed in both passes
    for label, text in [('formatted', formatted), ('condensed', condensed_back)]:
        if 'Type;Name;Description' in text or 'Type ; Name ; Description' in text:
            print(f"FAIL [rule 1]: Type;Name;Description header still present in {label} output")
            return 1

    # Rule 2: single-row ClassDiagram rows use table-style separators
    cd_lines = [l for l in formatted.split('\n') if 'ClassDiagram' in l]
    if not cd_lines:
        print("FAIL [rule 2]: ClassDiagram row missing from formatted output")
        return 1
    if ' ; ' not in cd_lines[0]:
        print(f"FAIL [rule 2]: ClassDiagram single row did not use table separators: {cd_lines[0]!r}")
        return 1

    # Rule 3: connector rows are padded with ' ; '
    conn_lines = [l for l in formatted.split('\n') if '-->' in l]
    if not conn_lines:
        print("FAIL [rule 3]: no connector rows found in formatted output")
        return 1
    if not all(' ; ' in l for l in conn_lines):
        print(f"FAIL [rule 3]: some connector rows not column-padded: {conn_lines}")
        return 1

    # Rule 3: mixed sequence rows use table separators and align key columns
    sequence_lines = [l for l in formatted.split('\n') if 'EnterCredentials' in l or 'Authenticate' in l or 'QueryUser' in l]
    if not sequence_lines:
        print("FAIL [rule 3]: no sequence rows found in formatted output")
        return 1
    if not all(' ; ' in l for l in sequence_lines):
        print(f"FAIL [rule 3]: some sequence rows did not use table separators: {sequence_lines}")
        return 1

    def _sep_positions(line):
        positions = []
        start = 0
        while True:
            pos = line.find(' ; ', start)
            if pos == -1:
                break
            positions.append(pos)
            start = pos + 3
        return positions

    step_rows = [
        l for l in formatted.split('\n')
        if l.startswith('    ') and ('EnterCredentials' in l or 'Authenticate' in l or 'QueryUser' in l)
    ]
    if len(step_rows) < 3:
        print(f"FAIL [rule 3]: expected 3+ sequence step rows, got {len(step_rows)}")
        return 1

    expected_positions = _sep_positions(step_rows[0])[:3]
    for row in step_rows[1:]:
        positions = _sep_positions(row)[:3]
        if positions != expected_positions:
            print("FAIL [rule 3]: source/target/function columns are not aligned across sequence steps")
            print("  expected positions:", expected_positions)
            print("  got positions:     ", positions)
            print("  row:", row)
            return 1

    # Rule 5: sequence note type fields are not padded to the width of @Warning/@Success
    info_lines = [l for l in formatted.split('\n') if '@Info' in l]
    if not info_lines:
        print("FAIL [rule 5]: no @Info row found in formatted output")
        return 1
    if any('@Info    ;' in l or '@Info ;' not in l for l in info_lines):
        print(f"FAIL [rule 5]: @Info note type was padded instead of left-aligned: {info_lines}")
        return 1

    # Rule 6: leading indentation preserved on connector rows
    for l in conn_lines:
        if not l.startswith('    '):
            print(f"FAIL [rule 6]: connector row lost its 4-space indent: {l!r}")
            return 1

    # Rule 7: condensing strips field padding while keeping indentation
    for l in condensed_back.split('\n'):
        if '-->' in l:
            if ' ; ' in l:
                print(f"FAIL [rule 7]: condensed connector row still has padding: {l!r}")
                return 1
            if not l.startswith('    '):
                print(f"FAIL [rule 7]: condensed connector row lost indent: {l!r}")
                return 1

    # Rule 8: round-trip semantic equivalence (ignoring removed header)
    original_no_header = condense_csv(original)  # use condense to drop header
    if condensed_back.strip() != original_no_header.strip():
        print("FAIL [rule 8]: round-trip mismatch:")
        print("  expected:", repr(original_no_header.strip()))
        print("  got:     ", repr(condensed_back.strip()))
        return 1

    print("OK: CSV formatter contract: header removal, single-row ClassDiagram table format, "
          "note types left-aligned, multi-row aligned, indentation preserved, safe round-trip")
    return 0


def run_parser_padding_regression_test() -> int:
    """Regression test for padded first-column tokens after visual formatting."""

    formatted_content = (
        "Class        ; Service    ; Service class\n"
        "    Function ; +ping()    ; Simple ping\n"
        "Sequence     ; SeqA       ; Initial sequence\n"
        "    Service ; Service ; ping\n"
        "ClassDiagram ; ServiceMap ; Service relationships\n"
        "    Service ; Service ; --> ; 1 ; 1 ; self\n"
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        csv_path = os.path.join(temp_dir, "formatted_model.csv")
        _write_file(csv_path, formatted_content)
        model = csv_parser.parse_csv(csv_path)

    if len(model.classes) != 1 or model.classes[0].name != "Service":
        print("FAIL: padded Class row did not parse correctly")
        return 1

    if len(model.sequences) != 1 or model.sequences[0].seq_id != "SeqA":
        print("FAIL: padded Sequence row did not parse correctly")
        return 1

    if len(model.class_diagrams) != 1 or model.class_diagrams[0].diagram_id != "ServiceMap":
        print("FAIL: padded ClassDiagram row did not parse correctly")
        return 1

    if len(model.class_diagrams[0].relationships) != 1:
        print("FAIL: padded ClassDiagram relationship row did not parse correctly")
        return 1

    print("OK: parser accepts visually padded first-column tokens from formatted CSV files")
    return 0


if __name__ == "__main__":
    rc = run_test()
    if rc == 0:
        rc = run_formatter_test()
    if rc == 0:
        rc = run_parser_padding_regression_test()
    raise SystemExit(rc)
