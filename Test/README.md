# Test Infrastructure

This directory contains all test cases for the Sequence Diagram Tool.

## Quick Start

### View Test Results
Open `test_viewer.html` directly in any browser:
- No server needed
- Works on any browser (Chrome, Firefox, Safari, Edge, etc.)
- Multiple tabs - one for each test case
- Self-contained - all tests load from the `tests/` subdirectory

Simply double-click `test_viewer.html` or navigate to it in your browser.

### Run Tests

To regenerate test SVG outputs, run the test runner from this directory:

```bash
cd Test
python run_test.py test_layers
python run_test.py test_multirow
python run_test.py test_notes
python run_test.py test_parameters
python run_test.py test_states
python run_test.py test_verbosity
```

Or run all tests at once:
```bash
python run_test.py test_layers && python run_test.py test_multirow && python run_test.py test_notes && python run_test.py test_parameters && python run_test.py test_states && python run_test.py test_verbosity
```

Test outputs are generated in the `tests/` subdirectory.

---

# Test CSV Datasets

This directory contains sample CSV files designed to demonstrate and test specific features of the Sequence Diagram Tool.

## Test Files Overview

### 1. test_notes.csv
**Feature Demonstrated:** Rendering_0011, Rendering_0012, Rendering_0013, Rendering_0014, Rendering_0015

**Purpose:** Showcases all three note types (Info, Warning, Error) with proper positioning
- Info notes (blue) on function calls and lanes
- Warning notes (orange) attached to lanes  
- Error notes (red) for critical issues
- Tests lane note positioning below state boxes
- Tests function note positioning to right of parameter text

**Expected Output:**
- Three colors of note boxes visible
- Notes NOT overlapping with function arrows or text
- Hover tooltips show full note content
- Works correctly at all verbosity levels (hidden in Low/Normal, visible in High)

---

### 2. test_states.csv
**Features Demonstrated:** State_0001, Rendering_0007, Rendering_0008, Rendering_0009, Rendering_0010

**Purpose:** Demonstrates UML state machine support with initial and transitional states
- State machine definition with 4 states
- Initial state display (Inactive) below first participant
- State transitions after each step
- State descriptions via hover tooltip
- Multiple state changes in a single sequence

**Expected Output:**
- State boxes with rounded corners and light grey fill
- Initial state "Inactive" appears below Account participant
- States transition after each step: Inactive → Active → Suspended → Active → Closed
- Each state shows description on hover

---

### 3. test_verbosity.csv
**Features Demonstrated:** UserInterface_0003, Rendering_0005, Rendering_0006

**Purpose:** Tests how verbosity levels (Low, Normal, High) affect diagram display
- Functions with parameters and return values
- Function tooltip descriptions
- Parameter and return value descriptions

**Verbosity Behavior:**
- **Low**: Shows only function names, no parameters or return values
- **Normal**: Shows function names with parameters and return values  
- **High**: Normal + descriptions shown in tooltips
- Hover tooltips reveal full descriptions at all levels

**Expected Output:**
- Low mode: `Add()` with no details
- Normal mode: `Add(a=10, b=5)` with `result=sum`
- High mode: Same as Normal + hover tooltips with parameter descriptions

---

### 4. test_parameters.csv
**Features Demonstrated:** Parser_0002, Parser_0003, Rendering_0005, Rendering_0006

**Purpose:** Demonstrates function calls with multiple parameters and return values
- Functions with 2-3 parameters
- Functions with 2 return values
- Parameter descriptions (e.g., "User's email address")
- Return value descriptions (e.g., "Unique identifier")

**Expected Output:**
- Function calls display all parameters: `CreateUser(name, email, role)`
- Return values shown: `userID, status`
- Hover on function text shows full parameter/return descriptions
- Proper alignment without overlapping text

---

### 5. test_layers.csv
**Features Demonstrated:** UserInterface_0004, Rendering_0001

**Purpose:** Tests layer filtering with 6 participants showing complex interactions
- Multiple participants (Client, APIGateway, AuthService, UserService, PermissionService, AuditLog)
- Shows filtering capability - users can toggle participants on/off
- Complex multi-step sequence with parallel authorization

**How to Test Layer Filtering:**
1. Open in interactive viewer
2. Open menu (⋯ button) and checkboxes for "Display Layers"
3. Uncheck individual participants to hide them
4. Sequence diagram updates to show only selected participants
5. Re-check participants to restore them to view

**Expected Output:**
- 6 participant lanes visible
- All interconnections properly routed
- Layer filtering allows selective visibility
- Diagram reflows correctly when participants hidden

---

### 6. test_multirow.csv
**Features Demonstrated:** Rendering_0004, Rendering_0003

**Purpose:** Demonstrates multiple sequence steps on the same row number
- Row 1: Browser request + info note simultaneously
- Row 2: Cache check + DB query at same time
- Row 3: Both operations complete

**Expected Output:**
- Multiple function arrows on same horizontal line
- Return arrows (dashed) also on same line
- Proper spacing prevents overlapping
- Notes positioned correctly alongside multi-step rows
- Sequence logic is clear despite multiple simultaneous operations

---

## How to Use These Tests

### Manual Testing
```
1. Copy test file to sample_model.csv
2. Start server: python server.py 8000
3. Open http://localhost:8000
4. Verify features display correctly at each verbosity level
5. Test interactions (hover tooltips, menu, layer filtering)
6. Commit observations and any bugs found
```

### Automated Testing (Future)
These CSV files are structured to enable automated testing:
- SVG output can be parsed for specific elements
- Can verify text content matches expected values
- Can check styling (colors, positions) programmatically
- Can test responsiveness at different viewport sizes

---

## Test Coverage Matrix

| Requirement ID | Test File | Notes |
|:---|:---|:---|
| Parser_0002 | test_parameters.csv | Multiple parameter extraction |
| Parser_0003 | test_parameters.csv | Function call parameters |
| Rendering_0001-0003 | All files | Basic sequence rendering |
| Rendering_0004 | test_multirow.csv | Multiple steps per row |
| Rendering_0005-0006 | test_verbosity.csv | Tooltips on hover |
| Rendering_0007-0010 | test_states.csv | State box rendering |
| Rendering_0011-0017 | test_notes.csv | Note system |
| UserInterface_0003 | test_verbosity.csv | Verbosity selector |
| UserInterface_0004 | test_layers.csv | Layer filtering |

---

## Adding New Tests

When adding new tests:
1. Create a new test_[feature].csv file
2. Document the features being tested
3. Describe expected visual output
4. List mapped requirements from REQUIREMENTS.md
5. Update this README with test details

## Notes

- All test files follow the standard hierarchical CSV DSL
- Test sequences use descriptive naming (SoftReq_TEST_XXX)
- Participants and functions have descriptions for tooltip testing
- Notes use all three types to test styling and positioning
- Return statements are explicit (use `Return` function) for clarity

