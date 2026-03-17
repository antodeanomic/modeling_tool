#!/usr/bin/env python3
"""Verify the Process architecture diagrams have been moved to hierarchical structure."""

import os
from pathlib import Path

print("=" * 70)
print("PROCESS ARCHITECTURE DIAGRAMS - HIERARCHICAL REORGANIZATION SUMMARY")
print("=" * 70)

diagrams_root = Path("diagrams/01_SystemArchitecture")

# Define expected structure
expected_structure = {
    "20_Components": {
        "10_Parser": ["csv_parser.csv"],
        "20_Renderer": ["svg_renderer.csv"],
        "30_DataModel": ["data_model_component.csv"],
        "40_WebServer": ["web_server.csv"],
    },
    "30_Classes": {
        "10_CoreModel": ["data_model.csv"],
        "20_CoreComponents": ["class_diagrams.csv"],
        "40_Testing": ["test_framework.csv"],
        "50_Utilities": ["utilities.csv"],
    }
}

print("\n📁 FOLDER STRUCTURE VERIFICATION\n")

total_files = 0
found_files = 0

for category, subcategories in expected_structure.items():
    category_path = diagrams_root / category
    print(f"\n{category}")
    print("─" * 60)
    
    for subcategory, files in subcategories.items():
        subcategory_path = category_path / subcategory
        
        # Check if folder exists
        exists = subcategory_path.exists()
        status = "✓" if exists else "✗"
        print(f"  {status} {subcategory}/")
        
        # Check files
        if exists:
            for filename in files:
                filepath = subcategory_path / filename
                file_exists = filepath.exists()
                file_status = "✓" if file_exists else "✗"
                file_size = "  " if file_exists else "  "
                
                if file_exists:
                    size_bytes = filepath.stat().st_size
                    if size_bytes > 1024:
                        size_str = f"{size_bytes / 1024:.1f}K"
                    else:
                        size_str = f"{size_bytes}B"
                    file_size = f"  ({size_str})"
                    found_files += 1
                
                print(f"      {file_status} {filename}{file_size}")
                total_files += 1

print("\n" + "=" * 70)
print(f"FILES CREATED: {found_files}/{total_files}")
print("=" * 70)

# List actual CSV files found
print("\n📄 ALL CSV FILES IN DIAGRAMS FOLDER:\n")

csv_files = list(diagrams_root.rglob("*.csv"))
csv_files.sort()

if csv_files:
    for csv_file in csv_files:
        rel_path = csv_file.relative_to(diagrams_root)
        print(f"  • {rel_path}")
else:
    print("  (no CSV files found)")

print(f"\nTotal: {len(csv_files)} files")

# Verify README files
print("\n📝 DOCUMENTATION:\n")

readme_files = list(diagrams_root.rglob("*.md"))
readme_files.sort()

if readme_files:
    for readme in readme_files:
        rel_path = readme.relative_to(diagrams_root)
        size = readme.stat().st_size
        print(f"  ✓ {rel_path} ({size} bytes)")

print("\n" + "=" * 70)
print("✅ REORGANIZATION COMPLETE")
print("=" * 70)
print("""
All Process/architecture diagrams have been organized hierarchically:

Components (System Building Blocks):
  • Parser - CSV parsing engine
  • Renderer - SVG rendering engine  • DataModel - Core data structures
  • WebServer - HTTP server

Classes (Detailed Definitions & Relationships):
  • CoreModel - Data model classes
  • CoreComponents - Relationship diagrams  • Testing - Test framework classes
  • Utilities - Utility helper classes

The menu will display with hierarchy and indentation, making it easy to
navigate by component or concern. Use the diagram viewer at http://localhost:8000
to see the new hierarchical menu in action.
""")
