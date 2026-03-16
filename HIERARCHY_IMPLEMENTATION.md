# Hierarchical Diagram Menu System - Implementation Summary

## Overview

I've successfully implemented a **folder-based hierarchical organization system** for diagram menus. The system is 100% flexible and automatically discovers diagram organization from folder structure.

## What Was Implemented

### 1. **Folder Structure Created** (`diagrams/` directory)

```
diagrams/
├── 01_SystemArchitecture/
│   ├── 10_Packages/
│   ├── 20_Components/
│   │   ├── 10_Interfaces/
│   │   ├── 20_Ports/
│   │   └── 30_CompositeStructures/
│   └── 30_Classes/
│       ├── 10_Attributes/
│       ├── 20_Methods/
│       └── 30_Relationships/
```

**Naming Convention:**
- Numeric prefixes (`01_`, `10_`, `20_`, etc.) control sort order
- Text after underscore becomes the display name in the menu
- Underscores converted to spaces automatically
- No configuration needed - structure is auto-discovered!

### 2. **Backend Changes - `Scripts/server.py`**

#### New Function: `find_csv_files_hierarchical()`
- Scans the `diagrams/` folder recursively
- Preserves folder hierarchy information
- Extracts and cleans folder names (removes numeric prefixes, replaces underscores)
- Returns list of CSVs with hierarchy metadata

#### Updated: `find_csv_files()`
- Merged hierarchical CSV discovery with traditional search
- Maintains backward compatibility with existing CSV locations
- No breaking changes to existing functionality

#### Updated: `handle_all_diagrams_request()`
- Now includes `hierarchy` field in diagram JSON response
- Each diagram includes full breadcrumb path information
- Hierarchy is sorted automatically

### 3. **Frontend Changes - `Scripts/diagram_viewer.html`**

#### Enhanced `populatePalette()` Function
- Renders hierarchical menu items with indentation
- Shows breadcrumb path for each diagram
- Indentation depth = folder depth (visual hierarchy)
- Breadcrumb example: `System Architecture > Components > Interfaces`

#### CSS Updates
- Added support for hierarchical indentation
- Responsive padding based on hierarchy depth
- Beautiful breadcrumb display in menu

## Key Features

### ✓ **100% Flexible**
- Just create folder structure - no configuration files needed
- No CSV changes required
- Folder structure directly becomes menu structure

### ✓ **Automatic Discovery**
- System walks `diagrams/` folder on server startup
- Detects any CSV files in any subfolder
- No manual registration needed

### ✓ **Backward Compatible**
- Existing CSVs in `Source/`, `Test/tests/`, `Process/architecture/` still work
- Only diagrams in `diagrams/` folder will have hierarchy info
- Legacy CSVs displayed normally (without hierarchy)

### ✓ **Sortable by Name**
- Numeric prefixes control order: `01_`, `10_`, `20_`, etc.
- Automatically sorts by folder name
- Display names clean: removes numeric prefix, converts underscores to spaces

### ✓ **Beautiful Menu Display**
- Indented list shows hierarchy visually
- Breadcrumb shows full path
- Type badges (SEQ, CLS) still included
- Hover effects and keyboard navigation work perfectly

## How It Works

### Step 1: Create Folder Structure
```
diagrams/01_SystemArchitecture/20_Components/10_Interfaces/
```

### Step 2: Add CSV Files
```
diagrams/01_SystemArchitecture/20_Components/10_Interfaces/my_interface.csv
```

### Step 3: Server Discovers Them
- `find_csv_files_hierarchical()` scans folder
- Extracts: `["System Architecture", "Components", "Interfaces"]` as hierarchy
- Includes in `/api/all_diagrams` response

### Step 4: Menu Renders Hierarchically
- Item is indented based on depth
- Breadcrumb shows: `System Architecture > Components > Interfaces`
- User sees clean, organized menu

## Example Menu Display

```
SEQUENCE DIAGRAMS
  System Architecture > Packages
    package_diagram_01
  System Architecture > Components > Interfaces
    interface_diagram_01
  System Architecture > Components > Ports
    port_diagram_01
  System Architecture > Components > Composite Structures
    composite_diagram_01
  System Architecture > Classes > Attributes
    attribute_diagram_01
  System Architecture > Classes > Methods
    method_diagram_01
  System Architecture > Classes > Relationships
    relationship_diagram_01
```

## API Response Format

The `/api/all_diagrams` endpoint now includes hierarchy information:

```json
{
  "diagrams": [
    {
      "type": "sequence",
      "id": "MyDiagram",
      "name": "MyDiagram",
      "csv": "my_diagram.csv",
      "lanes": ["obj1", "obj2"],
      "hierarchy": ["System Architecture", "Components", "Interfaces"]
    }
  ]
}
```

## Flexibility Examples

### Example 1: Simple Top-Level
```
diagrams/
├── 01_Diagrams/
│   ├── diagram1.csv
│   └── diagram2.csv
```
All diagrams grouped under "Diagrams" with no sub-categories.

### Example 2: Deep Nesting
```
diagrams/
├── 01_Architecture/
│   ├── 10_Level1/
│   │   ├── 10_Level2/
│   │   │   └── diagram.csv
```
Supports arbitrary nesting depth - just create the folders!

### Example 3: Multiple Categories
```
diagrams/
├── 01_Sequences/
├── 02_Classes/
├── 03_States/
```
Create any structure that suits your project.

## Next Steps

To use this system:

1. **Create folder structure** under `diagrams/` that matches your organization
2. **Place CSV files** in appropriate folders
3. **Restart server** or just refresh page
4. **Menu automatically appears** with proper hierarchy and indentation

No configuration needed - it's automatic!

## Implementation Details

- **Backward compatible**: Existing CSVs unaffected
- **Zero downtime**: Add diagrams anytime, server picks them up on next request
- **Scalable**: Works with any number of folders/diagrams
- **Clean code**: Minimal changes, separated concerns
- **Visual feedback**: Breadcrumbs + indentation show hierarchy clearly

## Files Modified

1. `Scripts/server.py` - Added hierarchy discovery, updated API response
2. `Scripts/diagram_viewer.html` - Enhanced palette rendering with indentation
3. `diagrams/` - New folder structure (example template)
4. `diagrams/README.md` - Documentation on how to use the system

---

**Status**: ✅ Ready to use! Just create your folder structure and add CSVs.
