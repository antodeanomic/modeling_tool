#!/usr/bin/env python3
"""Diagnostic server startup to debug responsiveness."""

import sys
import os

# Ensure we can import from Scripts
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Scripts'))

print("=" * 70)
print("DIAGNOSTIC SERVER STARTUP")
print("=" * 70)

# Step 1: Check CSV discovery
print("\n[1/4] Checking CSV discovery...")
try:
    from server import find_csv_files
    csvs = find_csv_files()
    print(f"      ✓ Found {len(csvs)} CSV files")
    
    if 'test_multiconnector_rightangle.csv' in csvs:
        print(f"      ✓ test_multiconnector_rightangle.csv FOUND")
    else:
        print(f"      ✗ test_multiconnector_rightangle.csv NOT FOUND")
except Exception as e:
    print(f"      ✗ ERROR: {e}")
    sys.exit(1)

# Step 2: Check multiconnector parse
print("\n[2/4] Parsing MultiConnectorTest...")
try:
    from parser import parse_csv
    csv_path = csvs.get('test_multiconnector_rightangle.csv')
    model = parse_csv(csv_path)
    print(f"      ✓ Parsed {len(model.classes)} classes, {len(model.class_diagrams)} diagrams")
    
    if model.class_diagrams:
        cd = model.class_diagrams[0]
        print(f"      ✓ Diagram: {cd.diagram_id}")
        print(f"      ✓ Routing: {cd.routing}")
        print(f"      ✓ Relationships: {len(cd.relationships)}")
    else:
        print(f"      ✗ No class diagrams found!")
except Exception as e:
    print(f"      ✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 3: Test server module load
print("\n[3/4] Loading server module...")
try:
    from server import CSV_FILES, DEFAULT_CSV, load_model
    print(f"      ✓ Server module loaded")
    print(f"      ✓ CSV_FILES: {len(CSV_FILES)}")
    print(f"      ✓ DEFAULT_CSV: {DEFAULT_CSV}")
except Exception as e:
    print(f"      ✗ ERROR: {e}")
    sys.exit(1)

# Step 4: Start HTTP server
print("\n[4/4] Starting HTTP server on port 8000...")
try:
    from http.server import HTTPServer
    from server import DiagramHandler
    
    print(f"      Creating HTTPServer...")
    server_address = ('', 8000)
    httpd = HTTPServer(server_address, DiagramHandler)
    
    print(f"      ✓ Server created and listening on :8000")
    print(f"\n" + "=" * 70)
    print("SERVER READY - Open http://localhost:8000 in your browser")
    print("=" * 70)
    print("\nServer running... (Ctrl+C to stop)\n")
    
    httpd.serve_forever()
    
except KeyboardInterrupt:
    print("\nServer stopped by user")
except Exception as e:
    print(f"      ✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
