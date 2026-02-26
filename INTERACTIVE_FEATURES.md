# Interactive Features Guide

The sequence diagram tool includes two important interactive features that allow you to explore and customize diagrams:

## 1. Hover Tooltips

**Feature**: Hover your mouse over any element in the diagram to see detailed information as a tooltip.

**What has tooltips:**
- **Function calls**: Shows function name, parameters, and descriptions
- **Participant boxes**: Shows class descriptions
- **State boxes**: Shows state descriptions
- **Return arrows**: Shows return value descriptions
- **Notes**: Shows note content and type

**How it works**: 
- The SVG diagrams contain embedded `<title>` elements that display as tooltips
- This works in all standard browsers and SVG viewers
- **No configuration needed** - this feature is automatically included in all generated diagrams

**Example**: Mouse over a function call arrow to see the full function signature and parameter descriptions.

---

## 2. Interactive Menu ("⋯" button)

**Feature**: Control diagram display with an interactive menu for:
- **Verbosity Levels**: Switch between Low, Normal, and High verbosity
- **Layer Filtering**: Check/uncheck specific objects/lanes to display only selected ones

**How to Access**:

1. Start the interactive server:
   ```bash
   python Scripts/server.py
   ```

2. Open your browser to: `http://localhost:8000`

3. Click the "⋯" menu button in the top-right corner

**Verbosity Levels**:
- **Low**: Shows only basic message flows, minimal labels
- **Normal**: Shows messages with function names and basic descriptions
- **High**: Shows all details including parameters, return values, notes, and state changes

**Layer Filtering**:
- Check/uncheck participant objects (lanes) to show only the interactions involving those objects
- Useful for focusing on specific subsystems or participants
- Automatically recalculates the diagram layout

**Example**: 
- Select only "Obj1" and "Obj2" to see just their interactions
- Switch to "Low" verbosity to simplify a complex diagram
- Switch to "High" verbosity to see all parameter and state details

---

## Quick Start

### To view tooltips on generated diagrams:
1. Run tests to generate SVG files:
   ```bash
   cd Test
   python run_all_tests_and_view.py
   ```
2. Open any generated SVG file in a browser
3. Hover over any element to see its tooltip

### To use the interactive menu:
1. Ensure your test data is in `Source/sample_model.csv`
2. Run the server:
   ```bash
   python Scripts/server.py
   ```
3. Open `http://localhost:8000` in your browser
4. Use the "⋯" menu button to control verbosity and layers

---

## Technical Details

### Hover Tooltips Implementation
- Located in: `Scripts/svg_renderer.py`
- Mechanism: SVG `<title>` elements added to all interactive elements
- Tooltip content includes: descriptions, parameters, return values
- Works automatically in all SVG-capable applications (browsers, viewers, Inkscape, etc.)

### Interactive Menu Implementation
- **Server**: `Scripts/server.py` - Provides API endpoints and serves the HTML viewer
- **Client**: `Scripts/diagram_viewer.html` - Interactive UI with menu and event handlers
- **API Endpoints**:
  - `/` - Serves the diagram viewer HTML
  - `/api/lanes` - Returns available lanes and verbosity levels
  - `/api/diagram` - Generates SVG with specified verbosity and lane filters

Both features are **always present** and require no special configuration or installation.
