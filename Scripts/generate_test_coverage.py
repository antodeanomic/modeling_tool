#!/usr/bin/env python3
"""
Generate test coverage documentation from test_mapping.csv.

This script:
1. Reads test_mapping.csv to get test-to-requirement mappings
2. Generates a markdown table showing test coverage
3. Creates a traceability matrix showing test vs requirement
4. Outputs to TEST_COVERAGE.md
"""

import csv
from pathlib import Path
from collections import defaultdict

def read_test_mapping(csv_file):
    """Read test mapping from CSV file."""
    tests_by_file = defaultdict(list)
    requirements_coverage = defaultdict(list)
    
    with open(csv_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            if row and row.get('TestFile'):
                test_file = row['TestFile'].strip()
                req_id = row['RequirementID'].strip()
                description = row['Description'].strip()
                
                tests_by_file[test_file].append({
                    'req_id': req_id,
                    'description': description
                })
                
                requirements_coverage[req_id].append(test_file)
    
    return tests_by_file, requirements_coverage

def read_requirements(csv_file):
    """Read requirements to get descriptions."""
    requirements = {}
    
    with open(csv_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            if row and row.get('ID'):
                req_id = row['ID'].strip()
                description = row['Description'].strip()
                requirements[req_id] = description
    
    return requirements

def generate_test_coverage_markdown(tests_by_file, requirements_coverage, requirements):
    """Generate markdown for test coverage."""
    output = []
    
    output.append("# Test Coverage Documentation")
    output.append("")
    output.append("## Overview")
    output.append("")
    output.append("This document maps test cases to requirements, providing traceability and coverage metrics.")
    output.append("")
    output.append("Each test case validates one or more specific requirements from the system specification.")
    output.append("")
    
    # Test Coverage Table
    output.append("## Test Coverage by File")
    output.append("")
    output.append("| Test File | Requirements Tested | Test Focus |")
    output.append("|:---|:---|:---|")
    
    for test_file in sorted(tests_by_file.keys()):
        reqs = tests_by_file[test_file]
        req_ids = "; ".join([r['req_id'] for r in reqs])
        
        # Determine test focus from filenames
        if "notes" in test_file:
            focus = "Note rendering, positioning, and visibility"
        elif "states" in test_file:
            focus = "State machine definition and transitions"
        elif "verbosity" in test_file:
            focus = "Verbosity level effects on display"
        elif "parameters" in test_file:
            focus = "Function parameters and return values"
        elif "layers" in test_file:
            focus = "Layer filtering and multi-participant interactions"
        elif "multirow" in test_file:
            focus = "Multiple steps per row - parallel operations"
        else:
            focus = "Feature validation"
        
        output.append(f"| {test_file} | {req_ids} | {focus} |")
    
    # Requirement Coverage Table
    output.append("")
    output.append("## Requirement Coverage Map")
    output.append("")
    output.append("| Requirement ID | Tested By | Status |")
    output.append("|:---|:---|:---|")
    
    for req_id in sorted(requirements_coverage.keys()):
        test_files = "; ".join(sorted(requirements_coverage[req_id]))
        description = requirements.get(req_id, "Unknown requirement")
        status = "✓ Covered" if test_files else "○ Not Tested"
        
        output.append(f"| {req_id} | {test_files} | {status} |")
    
    # Coverage Statistics
    output.append("")
    output.append("## Coverage Statistics")
    output.append("")
    total_requirements = len(requirements)
    tested_requirements = len(requirements_coverage)
    coverage_pct = (tested_requirements / total_requirements * 100) if total_requirements > 0 else 0
    
    output.append(f"- **Total Requirements**: {total_requirements}")
    output.append(f"- **Tested Requirements**: {tested_requirements}")
    output.append(f"- **Coverage**: {coverage_pct:.1f}%")
    output.append(f"- **Total Test Cases**: {len(tests_by_file)}")
    output.append("")
    
    # Test Execution Guide
    output.append("## Test Execution Guide")
    output.append("")
    output.append("To run all tests:")
    output.append("")
    output.append("```bash")
    for test_file in sorted(tests_by_file.keys()):
        test_name = test_file.replace('.csv', '')
        output.append(f"python run_test.py {test_name}")
    output.append("```")
    output.append("")
    
    output.append("Each test generates a `test_[name]_output.svg` file that can be inspected for correctness.")
    output.append("")
    
    # Requirements by Type with Test Coverage
    output.append("## Requirements by Type")
    output.append("")
    
    req_types = defaultdict(list)
    for req_id in sorted(requirements.keys()):
        # Infer type from ID prefix
        prefix = req_id.split('_')[0]
        req_types[prefix].append(req_id)
    
    for prefix in sorted(req_types.keys()):
        output.append(f"### {prefix} Requirements")
        output.append("")
        output.append("| ID | Tested By | Description |")
        output.append("|:---|:---|:---|")
        
        for req_id in sorted(req_types[prefix]):
            test_files = ", ".join(sorted(requirements_coverage.get(req_id, ["Not tested"])))
            description = requirements.get(req_id, "Unknown")
            output.append(f"| {req_id} | {test_files} | {description} |")
        
        output.append("")
    
    return "\n".join(output)

def main():
    tests_dir = Path("Test/tests")
    test_map_file = tests_dir / "test_mapping.csv"
    req_file = Path("Source/requirements.csv")
    
    if not test_map_file.exists():
        print(f"Error: {test_map_file} not found")
        return
    
    if not req_file.exists():
        print(f"Error: {req_file} not found")
        return
    
    try:
        tests_by_file, requirements_coverage = read_test_mapping(test_map_file)
        requirements = read_requirements(req_file)
        
        markdown = generate_test_coverage_markdown(tests_by_file, requirements_coverage, requirements)
        
        output_file = Path("TEST_COVERAGE.md")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown)
        
        print(f"Generated {output_file}")
        
        # Print summary
        total_tests = len(tests_by_file)
        total_req_tested = len(requirements_coverage)
        total_req = len(requirements)
        coverage = (total_req_tested / total_req * 100) if total_req > 0 else 0
        
        print(f"\nTest Coverage Summary:")
        print(f"  Test Cases: {total_tests}")
        print(f"  Requirements Tested: {total_req_tested}/{total_req} ({coverage:.1f}%)")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
