#!/usr/bin/env python3
"""
Run all test cases and launch interactive diagram viewer.

This script:
1. Runs all test cases (regenerates SVG outputs)
2. Launches the interactive server with full features:
   - Hover tooltips on diagram elements
   - Menu button (...) for verbosity control and layer filtering
3. Opens the viewer in the default browser
4. Designed to integrate with VS Code task runner
"""

import subprocess
import sys
from pathlib import Path
import platform
import shutil
import time
import os
import signal

# Force UTF-8 output on Windows
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# Change to Test directory so relative paths work
test_dir = Path(__file__).parent.absolute()
os.chdir(test_dir)

# Server process handle (for cleanup)
server_process = None

def run_all_tests():
    """Run all test cases."""
    test_cases = [
        'test_layers',
        'test_message_nesting',
        'test_multirow', 
        'test_nested_self_messages',
        'test_notes',
        'test_parameters',
        'test_self_message_label_alignment',
        'test_states',
        'test_ui_controls',
        'test_verbosity',
        'test_comprehensive_nesting'
    ]
    python_regression_tests = [
        'test_class_metadata_traceability.py',
        'test_class_diagram_title_and_endpoints.py',
        'test_class_diagram_connector_routing.py',
        'test_fanout.py',
        'test_class_diagram_routing_guardrails.py',
        'test_class_diagram_multiplicity_guardrails.py',
        'test_class_diagram_svg_golden.py',
    ]
    
    print("=" * 70)
    print("Running all test cases...")
    print("=" * 70)
    
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

    for test_script in python_regression_tests:
        print(f"\nRunning: {test_script}...")
        result = subprocess.run(
            [sys.executable, test_script],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print(f"Error running {test_script}:")
            print(result.stdout)
            print(result.stderr)
            return False
        else:
            output = result.stdout.strip()
            print(output if output else f"[OK] {test_script} passed")
    
    print("\n" + "=" * 70)
    print("All tests completed successfully!")
    print("=" * 70)
    return True

def launch_server():
    """Launch the interactive diagram server."""
    print("\n" + "=" * 70)
    print("Launching interactive diagram viewer...")
    print("=" * 70)
    
    global server_process
    
    server_script = Path("..") / "Scripts" / "server.py"
    
    if not server_script.exists():
        print(f"Error: Server script not found at {server_script}")
        return False
    
    try:
        # Start server in background with output shown
        server_process = subprocess.Popen(
            [sys.executable, str(server_script), "8000"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0
        )
        
        # Wait for server to start (increased from 3 to 5 seconds)
        print("Waiting for server to start...")
        time.sleep(5)
        
        # Check if server is still running (poll returns None if running)
        if server_process.poll() is not None:
            # Server exited, try to get output
            stdout, _ = server_process.communicate()
            print(f"Server failed to start. Output:")
            print(stdout)
            return False
        
        print("[OK] Server started successfully")
        return True
        
    except Exception as e:
        print(f"Error starting server: {e}")
        return False

def find_vscode_executable():
    """Find the VS Code executable path on Windows."""
    import shutil
    
    # Try standard locations on Windows
    possible_paths = [
        shutil.which('code'),  # Try in PATH first
        shutil.which('code.cmd'),  # Try code.cmd
        r'C:\Users\{}\AppData\Local\Programs\Microsoft VS Code\bin\code.cmd'.format(os.getenv('USERNAME', '')),
        r'C:\Program Files\Microsoft VS Code\bin\code.cmd',
        r'C:\Program Files (x86)\Microsoft VS Code\bin\code.cmd',
    ]
    
    for path in possible_paths:
        if path and os.path.exists(path):
            return path
    
    return None

def open_browser():
    """Open the interactive viewer in VS Code's Simple Browser."""
    url = "http://localhost:8000"
    
    print(f"\nOpening in VS Code Simple Browser: {url}")
    time.sleep(1)
    
    try:
        # Find VS Code executable
        code_path = find_vscode_executable()
        
        if code_path:
            # Open in VS Code's Simple Browser
            subprocess.Popen([code_path, '--open-url', url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("[OK] Browser opened in VS Code")
        else:
            print("Warning: VS Code executable not found in PATH")
            print(f"Please manually open in VS Code Simple Browser: {url}")
    except Exception as e:
        print(f"Warning: Could not open in VS Code ({e})")
        print(f"Please manually open in VS Code Simple Browser: {url}")
    
    return True

def cleanup():
    """Clean up: stop the server on exit."""
    global server_process
    if server_process and server_process.poll() is None:
        print("\n\nShutting down server...")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
            print("[OK] Server stopped")
        except subprocess.TimeoutExpired:
            server_process.kill()
            print("[OK] Server force-stopped")

def main():
    """Run all tests and launch interactive viewer."""
    # Register cleanup on exit
    signal.signal(signal.SIGINT, lambda sig, frame: (cleanup(), sys.exit(0)))
    
    # Run tests
    if not run_all_tests():
        cleanup()
        sys.exit(1)
    
    # Launch server
    if not launch_server():
        cleanup()
        sys.exit(1)
    
    # Open browser
    if not open_browser():
        cleanup()
        sys.exit(1)
    
    print("\n" + "=" * 70)
    print("INTERACTIVE FEATURES AVAILABLE:")
    print("=" * 70)
    print("[+] Hover Tooltips: Hover over any diagram element for details")
    print("[+] Menu Button (...): Click to access:")
    print("    - Verbosity levels: Low, Normal, High")
    print("    - Layer filtering: Check/uncheck objects to show only selected ones")
    print("\nPress Ctrl+C to stop the server and exit.")
    print("=" * 70 + "\n")
    
    # Keep the server running
    try:
        while True:
            time.sleep(1)
            if server_process.poll() is not None:
                print("Server stopped unexpectedly")
                break
    except KeyboardInterrupt:
        cleanup()

if __name__ == "__main__":
    main()

