# Architecture Decision Records (ADRs)

## UML Sequence Diagram Rendering - Spacing & Layout Optimization

### ADR-001: Loop Height and Bracket Sizing
| Aspect | Details |
|--------|---------|
| **Decision** | Reduce LOOP_HEIGHT from 30px to 15px; use 15px width for all brackets |
| **Context** | Nested message brackets were consuming excessive vertical space, making diagrams visually bloated |
| **Rationale** | 15x15px square brackets provide consistent proportions and professional appearance; reduces vertical waste by 50% |
| **Consequences** | Messages stack more tightly (5-15px gaps); visual hierarchy clearer; all nested levels use same proportions |
| **Status** | ✅ Implemented & Tested |

### ADR-002: Message-to-Text Spacing
| Aspect | Details |
|--------|---------|
| **Decision** | Reduce arrow-to-label gap from 10px to 2px; position text directly above/near arrow |
| **Context** | Large gaps between arrows and their labels wasted vertical space and appeared unprofessional |
| **Rationale** | 1-2px gap maintains readability while eliminating visual clutter; labels stay close to their referents |
| **Consequences** | More compact diagrams; text must not overlap; requires dynamic lane width adjustment for long labels |
| **Status** | ✅ Implemented & Tested |

### ADR-003: Sequential Message Positioning in Spanning Brackets
| Aspect | Details |
|--------|---------|
| **Decision** | Position nested messages sequentially at 15px intervals (not 30px); start from bracket top + 15px |
| **Context** | Messages inside multi-row spanning brackets needed consistent, tight spacing while maintaining visual hierarchy |
| **Rationale** | 15px intervals match LOOP_HEIGHT; predictable, uniform spacing; prevents arbitrary gaps between nested messages |
| **Consequences** | Messages inside spanning brackets use bracket-relative coordinates; enables arbitrary nesting depth; bracket end must account for padding |
| **Status** | ✅ Implemented & Tested |

### ADR-004: Dynamic Lane Width Adjustment
| Aspect | Details |
|--------|---------|
| **Decision** | Automatically increase lane width if message text overlaps arrow endpoints |
| **Context** | Tight 2px text spacing could cause long labels to overlap horizontal arrow segments |
| **Rationale** | Prevents text collision while maintaining tight spacing in normal cases; preserves readability without manual intervention |
| **Consequences** | Lane width varies by diagram complexity; measurement of text width required at render time; adds ~50px when needed |
| **Status** | ✅ Implemented & Tested |

### ADR-005: Bracket Label Positioning
| Aspect | Details |
|--------|---------|
| **Decision** | Position spanning bracket labels at top-right of vertical segment (y_start + 1), top-justified |
| **Context** | Bracket labels need to identify their associated groups without overlapping internal arrows or messages |
| **Rationale** | Top-justification aligns label with bracket opening; label positioned right of vertical line avoids arrow overlap; minimal vertical offset |
| **Consequences** | Label appears at bracket start; clear visual association with bracketed content; requires minimum label text height for visibility |
| **Status** | ✅ Implemented & Tested |

### ADR-006: Return Arrow Spacing (Inside vs Outside Brackets)
| Aspect | Details |
|--------|---------|
| **Decision** | Use 15px spacing for return arrows inside brackets; 30px spacing for return arrows outside brackets |
| **Context** | Response arrows to messages needed to stay contained within their spanning brackets while maintaining readable spacing from preceding messages |
| **Rationale** | 15px accommodates 12px text with proper centering; ROW_HEIGHT (60px) based spacing for non-bracketed ensures standard row alignment |
| **Consequences** | Return arrows inside brackets space tightly (2px message + 2px gap + 11px for arrow+text); outside brackets use full row-based spacing |
| **Status** | ✅ Implemented & Tested |

### ADR-007: Return Arrow Text Centering
| Aspect | Details |
|--------|---------|
| **Decision** | Center return arrow text over the dashed return arrow; position text baseline at y_ret + 4 |
| **Context** | Return value labels needed to be clearly readable without overlap; arrow should pass through visual center of text |
| **Rationale** | Baseline offset of 4px positions 12px-font visual center on dashed arrow line; symmetric appearance; professional typography |
| **Consequences** | 15px minimum spacing required between preceding message and return arrow; all return arrows have consistent text alignment; improves diagram readability |
| **Status** | ✅ Implemented & Tested (Commit: 37fa184) |

### ADR-008: Bracket End Calculation with Return Arrows
| Aspect | Details |
|--------|---------|
| **Decision** | Track return arrows in bracket end calculation; extend bracket to contain all interior return arrows (22px for arrow + centered text) |
| **Context** | Response arrows to bracketed messages must appear visually contained within the bracket vertical segment |
| **Rationale** | Proper containment improves visual hierarchy; prevents arrows from appearing to "escape" the bracket; maintains semantic grouping |
| **Consequences** | Bracket height calculation includes return arrow space (22px when return present, vs 2px for message-only); max_y tracking required during positioning pass |
| **Status** | ✅ Implemented & Tested |

---

## Summary Table: Evolution of Key Constants

| Constant | Phase 1 | Phase 2 | Phase 3+ | Rationale |
|----------|---------|---------|----------|-----------|
| LOOP_HEIGHT | 30px | 15px | 15px | Square brackets (15x15); 50% vertical reduction |
| BASE_LOOP_WIDTH (spanning) | 30px | 15px | 15px | Consistent with nested bracket widths |
| Arrow-text gap | 10px | 2px | 2px | Minimize wasted space; maintain readability |
| Message spacing interval | 30px | 15px | 15px | Match LOOP_HEIGHT; tight sequential positioning |
| Return arrow spacing (inside) | 30px | 4px | 15px | Now accommodates centered text display |
| Return arrow spacing (outside) | 30px | 30px | 30px | Row-based alignment maintained |
| Text baseline offset from arrow | -2px | -2px | +4px | Move from above to centered over arrow |
| Bracket end padding | (varies) | 30px+2px | 22px+2px | Account for centered return text (smaller total) |

## Test Coverage
✅ **All 9 regression tests passing** throughout all phases:
- test_layers
- test_message_nesting (primary focus)
- test_multirow
- test_nested_self_messages
- test_notes
- test_parameters
- test_states
- test_ui_controls
- test_verbosity

## Final Metrics (test_message_nesting.csv)
```
Msg1 bracket:        30px wide, y=120→197 (77px tall, contains all nested content)
Msg1a bracket:       15px wide, y=135→150 (15px tall)
Msg1b message:       y=152 (2px gap from Msg1a end)
Response arrow:      y=167 (15px from Msg1b, centered text at y=171)
Total vertical:      77px (vs 150px+ before optimization)
```

## Decision Status: ✅ COMPLETE
All design decisions implemented, tested, and validated through regression test suite.
