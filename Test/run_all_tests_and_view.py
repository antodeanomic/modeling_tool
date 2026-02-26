#!/usr/bin/env python3
"""
Run all test cases and launch interactive diagram viewer.

This script:
1. Runs all test cases (regenerates SVG outputs)
2. Launches the interactive server with full features:
   - Hover tooltips on diagram elements
   - Menu button (⋯) for verbosity control and layer filtering
3. Opens the viewer in the default browser
4. Designed to integrate with VS Code task runner
"""

import subprocess
import sys
from pathlib import Path
import webbrowser
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
        # Start server in background
        server_process = subprocess.Popen(
            [sys.executable, str(server_script), "8000"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # Wait for server to start
        print("Waiting for server to start...")
        time.sleep(3)
        
        # Check if server is running
        if server_process.poll() is not None:
            stdout, stderr = server_process.communicate()
            print(f"Server failed to start:")
            print(stderr)
            return False
        
        print("[OK] Server started successfully")
        return True
        
    except Exception as e:
        print(f"Error starting server: {e}")
        return False

def open_browser():
    """Open the interactive viewer in browser."""
    url = "http://localhost:8000"
    
    print(f"\nOpening browser to: {url}")
    time.sleep(1)
    
    try:
        webbrowser.open(url)
        print("[OK] Browser opened")
    except Exception as e:
        print(f"Warning: Could not open browser automatically ({e})")
        print(f"Please manually open: {url}")
    
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
    print("✓ Hover Tooltips: Hover over any diagram element for details")
    print("✓ Menu Button (⋯): Click to access:")
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

