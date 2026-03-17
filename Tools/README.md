# Development Tools

This directory contains utilities, diagnostic scripts, and debug tools created during development for analyzing, verifying, and debugging the modeling tool's features.

## Directory Structure

### `/Analysis`
Analysis and checking utilities for understanding diagram structure, connector routing, spacing, and rendering.

**Tools include:**
- Bracket analysis (height calculations, spanning detection)
- Connector analysis (routing paths, endpoints, conflicts)
- CSV discovery and validation
- Relationship checking
- Grid spacing verification
- Diagram API responses

**Usage:** When investigating layout or rendering issues, check here for diagnostic scripts.

### `/Debugging`
Low-level debugging utilities for tracing execution, inspecting internal state, and analyzing complex issues.

**Tools include:**
- Message nesting and hierarchy debugging
- Model class definition debugging
- Multiconnector parsing analysis
- Multiplicity rendering debugging
- Spanning bracket analysis
- Connector tracing

**Usage:** When tracking down specific bugs or understanding code flow.

### `/Verification`
Verification scripts, visualization tools, and ad-hoc test utilities for validating features.

**Tools include:**
- Color system verification
- Connector text and positioning checks
- Collision detection testing
- CSV parsing validation
- Hierarchy and relationship verification
- SVG structure verification
- Feature-specific tests (multiconnector, VHV routing, etc.)
- Text display and rendering checks

**Usage:** For spot-checking features, generating visual output, and validating fixes.

### `/Temp`
Temporary data files and responses captured during development and testing.

**Usage:** Reference or debugging; safe to delete without affecting functionality.

## Notes

- These scripts are **not part of the product** and are not executed during normal operation
- They are kept for **future maintenance and verification**
- The directory can be removed from the repository at any time without affecting core functionality
- Scripts are organized by purpose for easy discovery and reuse

## Running Tools

Most scripts can be run directly:

```bash
python Tools/Analysis/analyze_connectors.py
python Tools/Debugging/debug_hierarchy_api.py
python Tools/Verification/show_connector_text.py
```

Some scripts require the `Scripts/` directory to be in the Python path:

```bash
cd ../
python Tools/Analysis/check_relationships.py
```

---

**Maintained for:** Documentation, debugging, feature verification, and architecture understanding.
