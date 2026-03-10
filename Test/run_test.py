#!/usr/bin/env python3
"""
Test runner for Sequence Diagram Tool test cases.

Usage:
    python run_test.py test_notes
    python run_test.py test_states
    python run_test.py test_verbosity
    python run_test.py test_parameters
    python run_test.py test_layers
    python run_test.py test_multirow

Each test generates a test_[name]_output.svg file showing the result.
"""

import sys
import shutil
from pathlib import Path

def run_test(test_name):
    """Run a specific test case."""
    test_dir = Path("tests")
    test_file = test_dir / f"{test_name}.csv"
    
    if not test_file.exists():
        print(f"Error: {test_file} not found")
        print("\nAvailable tests:")
        for f in sorted(test_dir.glob("test_*.csv")):
            print(f"  - {f.stem}")
        return False
    
    print(f"\n{'='*60}")
    print(f"Running test: {test_name}")
    print(f"{'='*60}")
    print(f"Input: {test_file}")
    
    # Backup original from Source/
    backup_file = Path("sample_model.csv.backup")
    source_file = Path("../Source/sample_model.csv")
    # Remove 'test_' prefix if present for output filename
    base_name = test_name.replace("test_", "") if test_name.startswith("test_") else test_name
    output_file = Path(f"tests/{base_name}_output.svg")
    
    if source_file.exists():
        shutil.copy(source_file, backup_file)
    
    # Copy test file
    shutil.copy(test_file, "sample_model.csv")
    
    print(f"Generating diagram...")
    try:
        # Update main.py to use the correct test sequence ID
        # The test files use SoftReq_TEST_XXX naming
        import sys
        sys.path.insert(0, str(Path.cwd().parent / "Scripts"))
        from parser import parse_csv
        from svg_renderer import render_svg
        
        model = parse_csv(str(test_file))
        
        # Get the first sequence (all test files should have one)
        seq = None
        if model.sequences:
            seq = model.sequences[0]
        
        if not seq:
            print("Error: No sequence found in test CSV")
            return False
        
        svg = render_svg(model, seq, verbosity_level="High")
        
        # Write output SVG
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(svg)
        
        print(f"Output: {output_file}")
        print(f"\nTest diagram generated successfully!")
        print(f"This test file will be used when you set the SEQUENCE_ID in server.py")
        
        # Report validation warnings
        if model.warnings:
            print(f"\n\033[91m{'='*60}")
            print(f"VALIDATION ERRORS: {len(model.warnings)} issue(s) found")
            print(f"{'='*60}\033[0m")
            for w in model.warnings:
                print(f"\033[91m  [!] {w}\033[0m")
        else:
            print(f"\n\033[92m[OK] No validation errors\033[0m")
        
    except Exception as e:
        print(f"Error generating diagram: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Restore original
        if backup_file.exists():
            shutil.copy(backup_file, str(source_file))
            backup_file.unlink()
    
    return True

def main():
    if len(sys.argv) < 2:
        print("Test Runner for Sequence Diagram Tool")
        print("\nUsage:")
        print("  python run_test.py <test_name>")
        print("\nAvailable tests:")
        for f in sorted(Path("tests").glob("test_*.csv")):
            test_name = f.stem
            print(f"  - {test_name}")
        return
    
    test_name = sys.argv[1]
    if not test_name.startswith("test_"):
        test_name = f"test_{test_name}"
    
    success = run_test(test_name)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
