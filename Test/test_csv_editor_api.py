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


if __name__ == "__main__":
    raise SystemExit(run_test())
