#!/usr/bin/env python3
"""
Convert requirements.csv to markdown tables.
This script reads the requirements.csv and generates properly formatted markdown tables.
"""

import csv
from pathlib import Path

def read_requirements(csv_file):
    """Read requirements from CSV file."""
    requirements = []
    with open(csv_file, 'r', encoding='utf-8-sig') as f:  # utf-8-sig removes BOM
        reader = csv.DictReader(f)
        for row in reader:
            if row and row.get('ID'):
                requirements.append(row)
    return requirements

def generate_markdown_table(requirements):
    """Generate markdown table from requirements."""
    lines = []
    
    lines.append("# Requirements\n")
    lines.append("This document contains all implemented requirements, constraints, and assumptions.\n")
    lines.append("Requirements are organized by type and linked to related artifacts.\n")
    
    # Group by Type
    by_type = {}
    for req in requirements:
        req_type = req.get('Type', '').strip()
        if req_type not in by_type:
            by_type[req_type] = []
        by_type[req_type].append(req)
    
    # Process each type  
    type_order = ['Requirement', 'Constraint', 'Assumption']
    
    for req_type in type_order:
        if req_type not in by_type:
            continue
        
        type_reqs = by_type[req_type]
        
        lines.append(f"\n## {req_type}s\n")
        lines.append("| ID | Description | Linked From | Linked To | Status |")
        lines.append("|:---|:---|:---|:---|:---|")
        
        # Sort by ID 
        sorted_reqs = sorted(type_reqs, key=lambda r: r.get('ID', ''))
        
        for req in sorted_reqs:
            req_id = req.get('ID', '').strip()
            description = req.get('Description', '').strip()
            linked_from = req.get('Linked From', '').strip() or "-"
            linked_to = req.get('Linked To', '').strip() or "-"
            status = req.get('Status', '').strip()
            
            # Use Level to create visual hierarchy
            level = req.get('Level', '').strip()
            level_indent = ""
            if level == 'Component':
                level_indent = "  "
            elif level == 'Feature':
                level_indent = "    "
            
            id_display = f"{level_indent}{req_id}"
            
            lines.append(f"| {id_display} | {description} | {linked_from} | {linked_to} | {status} |")
    
    return "\n".join(lines)

def main():
    csv_file = Path("requirements.csv")
    
    if not csv_file.exists():
        print(f"Error: {csv_file} not found")
        return
    
    try:
        requirements = read_requirements(csv_file)
        if not requirements:
            print("Error: No requirements found in CSV")
            return
            
        markdown = generate_markdown_table(requirements)
        
        # Write to file
        output_file = Path("REQUIREMENTS.md")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown)
        
        print(f"Generated {output_file}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
