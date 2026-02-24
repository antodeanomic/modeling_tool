#!/usr/bin/env python3
"""
Run all test cases and open test viewer in browser.

This script:
1. Runs all 6 test cases (regenerates SVG outputs)
2. Opens test_viewer.html in the default browser
3. Designed to integrate with VS Code task runner
"""

import subprocess
import sys
from pathlib import Path
import webbrowser
import time
import os

# Force UTF-8 output on Windows
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# Change to Test directory so relative paths work
test_dir = Path(__file__).parent.absolute()
os.chdir(test_dir)

def run_all_tests():
    """Run all test cases."""
    test_cases = [
        'test_layers',
        'test_multirow', 
        'test_notes',
        'test_parameters',
        'test_states',
        'test_ui_controls',
        'test_verbosity'
    ]
    
    print("=" * 60)
    print("Running all test cases...")
    print("=" * 60)
    
    for test in test_cases:
        print(f"\nRunning: {test}...")
        result = subprocess.run(
            [sys.executable, 'run_test.py', test],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"Error running {test}:")
            print(result.stderr)
            return False
        else:
            print(f"[OK] {test} passed")
    
    print("\n" + "=" * 60)
    print("All tests completed successfully!")
    print("=" * 60)
    return True

def open_viewer():
    """Open test_viewer.html in browser."""
    viewer_path = Path("test_viewer.html").resolve()
    viewer_url = viewer_path.as_uri()
    
    print(f"\nOpening test viewer: {viewer_url}")
    time.sleep(1)  # Give browser time to start
    
    try:
        webbrowser.open(viewer_url)
        print("[OK] Test viewer opened in browser")
    except Exception as e:
        print(f"Warning: Could not open browser ({e})")
        print(f"You can manually open: {viewer_path}")
    
    return True

def main():
    """Run all tests and view results."""
    # Run tests
    if not run_all_tests():
        sys.exit(1)
    
    # Open viewer
    if not open_viewer():
        sys.exit(1)
    
    print("\nYou can now review test results in the browser.")
    print("Refresh the page after making code changes to see updated diagrams.")

if __name__ == "__main__":
    main()
