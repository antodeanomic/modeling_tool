#!/usr/bin/env python3
"""Regression checks for explicit class traceability and diagram hierarchy parsing."""

import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(REPO_ROOT, "Scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from parser import parse_csv


def run_test() -> int:
    csv_path = os.path.join(REPO_ROOT, "Source", "sample_model.csv")
    model = parse_csv(csv_path)

    user_class = model.get_class("User")
    display_class = model.get_class("Display")
    keypad_class = model.get_class("Keypad")
    class_diagram = model.get_class_diagram("CalculatorDiagonalArchitecture")
    sequence = model.get_sequence("SoftReq0001")

    if user_class is None or display_class is None or keypad_class is None:
        print("FAIL: expected sample classes were not parsed")
        return 1

    if class_diagram is None or sequence is None:
        print("FAIL: expected sample diagrams were not parsed")
        return 1

    if user_class.trace_requirement_ids != ["Architecture_0001", "UserInterface_0001"]:
        print(f"FAIL: unexpected User requirement IDs: {user_class.trace_requirement_ids}")
        return 1

    if user_class.trace_user_story_ids != ["UserStory_0001"]:
        print(f"FAIL: unexpected User story IDs: {user_class.trace_user_story_ids}")
        return 1

    if user_class.trace_test_case_ids != ["test_interactive_001"]:
        print(f"FAIL: unexpected User test IDs: {user_class.trace_test_case_ids}")
        return 1

    if display_class.trace_requirement_ids != ["Rendering_0001", "Rendering_0007"]:
        print(f"FAIL: unexpected Display requirement IDs: {display_class.trace_requirement_ids}")
        return 1

    if display_class.trace_test_case_ids != ["test_render_001"]:
        print(f"FAIL: unexpected Display test IDs: {display_class.trace_test_case_ids}")
        return 1

    if keypad_class.trace_requirement_ids != ["Parser_0001"]:
        print(f"FAIL: unexpected Keypad requirement IDs: {keypad_class.trace_requirement_ids}")
        return 1

    if keypad_class.trace_feature_ids != ["FEAT-001"]:
        print(f"FAIL: unexpected Keypad feature IDs: {keypad_class.trace_feature_ids}")
        return 1

    if sequence.parent_diagram != "CalculatorDiagonalArchitecture":
        print(f"FAIL: unexpected sequence parent diagram: {sequence.parent_diagram}")
        return 1

    if class_diagram.parent_diagram != "":
        print(f"FAIL: class diagram should not have an explicit parent: {class_diagram.parent_diagram}")
        return 1

    if class_diagram.child_diagrams != []:
        print(f"FAIL: class diagram should not have explicit children: {class_diagram.child_diagrams}")
        return 1

    print("OK: explicit traceability IDs and diagram hierarchy parse correctly")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_test())