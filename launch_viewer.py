#!/usr/bin/env python3
"""
Simple launcher for the interactive sequence diagram viewer.

This script starts the HTTP server and opens the viewer in your default browser.
"""

import os
import sys
import time
import webbrowser
import subprocess

def main():
    """Launch the interactive viewer."""
    port = 8000
    url = f"http://localhost:{port}"
    
    print("=" * 60)
    print("Sequence Diagram Viewer")
    print("=" * 60)
    print(f"\nStarting server on {url}...")
    print("\nFeatures:")
    print("  • Hover over any diagram element for detailed tooltips")
    print("  • Click the '⋯' menu button to:")
    print("    - Change verbosity level (Low, Normal, High)")
    print("    - Filter diagram layers/objects")
    print("\nPress Ctrl+C to stop the server")
    print("-" * 60 + "\n")
    
    try:
        # Start the server in a subprocess
        server_process = subprocess.Popen(
            [sys.executable, "Scripts/server.py", str(port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a moment for the server to start
        time.sleep(2)
        
        # Open the browser
        webbrowser.open(url)
        print(f"✓ Browser opened to {url}")
        print("✓ Server is running\n")
        
        # Keep the process alive
        server_process.wait()
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        try:
            server_process.terminate()
            server_process.wait(timeout=5)
        except:
            server_process.kill()
        print("✓ Server stopped")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
