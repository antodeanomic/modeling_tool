# Routing Guardrail Regression Prevention System

## Purpose
To prevent future regressions in connector routing by automatically scanning all class diagrams for four categories of routing failures:

1. **Diagonal segments** - connectors that include non-orthogonal line segments in orthogonal mode
2. **Under-object routing** - connectors that pass through the interior of other objects
3. **Endpoint orientation mismatch** - final connector segment doesn't approach the target from the declared entry edge
4. **Same-axis segment overlap** - two connector segments occupy the same horizontal or vertical lane for a significant span

## Running the Guardrail Test

```bash
cd Test
python test_class_diagram_routing_guardrails.py
```

## Test Output

The test produces a comprehensive report showing:
- **Total issue count** across all diagrams and routing modes (diagonal + orthogonal)
- **Per-diagram status**: PASSED (clean) or FAILED (contains issues)
- **Issue breakdown**: Lists up to 120 concrete routing failures, grouped by diagram

Example output:
```
FAIL: found 44 routing issue(s) across 33 class diagrams in 11 CSV files

PASSED DIAGRAMS: 30
  [OK] class_diagrams.csv::DataModelRelationships
  [OK] class_diagrams.csv::ParserToModel
  ... (28 more)

FAILED DIAGRAMS: 3
  [FAIL] system_structure.csv::UserInteraction
  [FAIL] test_class_diagram_orthogonal_stress.csv::OrthogonalStressDense  
  [FAIL] test_multiconnector_rightangle.csv::MultiConnectorTest

- [segment_overlap] ... MultiConnectorTest :: diagonal :: CentralHub->Target1 overlaps ...
- [under_object] ... OrthogonalStressDense :: diagonal :: OrderService->InventoryService ...
- [segment_overlap] ... UserInteraction :: diagonal :: User->DiagramPicker overlaps ...
... (41 more issues)
```

## Guardrail Requirements

After any routing logic change:
1. Run the guardrail test before committing
2. The test must show **no increase** in issue count
3. Ideally, each change should reduce the issue count
4. If issues increase, the change has introduced a regression and must be reverted or fixed

## Current Status (2026-04-10)

| Category | Count | Status |
|----------|-------|--------|
| Diagrams with clean routing | 30 / 33 | ✓ Safe |
| Remaining issues | 44 | ⚠ Known failures |
| Diagonal segments | 0 | ✓ Fixed |
| Endpoint orientation errors | 0 | ✓ Fixed |
| Under-object routing | 24 | ⚠ Localized to 3 diagrams |
| Segment overlap | 20 | ⚠ Localized to 3 diagrams |

## Known Problem Diagrams

1. **test_multiconnector_rightangle.csv::MultiConnectorTest** (32 issues)
   - Intentional stress harness: 11 connectors from central hub radiating outward
   - All routing modes generate segment overlap across shared lanes
   - Issue: No optimal single-sort order satisfies lane assignment for all connectors

2. **test_class_diagram_orthogonal_stress.csv::OrthogonalStressDense** (10 issues)
   - Architecture stress case with overlapping object placement
   - Segments occasionally cross objects under heavy rerouting strategies

3. **system_structure.csv::UserInteraction** (2 issues)
   - Light diagram but connectors cross intermediate objects in direct line
   - May benefit from layout adjustment rather than routing tuning

## Future Work

### Priority 1: Track Pre-Reservation
Implement lane pre-allocation before connector routing to reserve horizontal/vertical tracks upfront. This would eliminate post-hoc overlap detection and instead prevent overlaps during planning.

### Priority 2: Per-Diagram Layout Tuning
For the 3 known problem diagrams, manually tune connection point selection or object positioning to improve natural routing separation.

### Priority 3: Segment-Sharing Mode
Investigate intentional segment sharing (e.g., bundling connectors along common paths) as an advanced routing strategy to reduce diagram clutter in dense scenarios.

## Integration

The guardrail test is automatically executed by `Test/run_all_tests_and_view.py` as part of the full test suite. This ensures regressions are caught immediately during development.
