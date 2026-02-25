# Architecture Decision Records (ADRs)

## UML Sequence Diagram Rendering - Spacing & Layout Optimization

### ADR-010: Self-Message Rendering Unification - Spanning Brackets Only
| Aspect | Details |
|--------|---------|
| **Decision** | Render all self-messages using spanning brackets exclusively; no character markers (↩) or explicit 3-segment arrows |
| **Context** | Previous approach attempted three different rendering modes (markers, arrows, brackets), creating complexity and inconsistency. Decision to standardize on spanning brackets for clarity |
| **Single Approach** | All self-messages (simple, nested, or standalone) render as: (1) Spanning bracket rectangle on left side of lane at appropriate nesting depth, (2) Label text positioned to the right of the lane near the bracket start |
| **Visual Indication** | The spanning bracket rectangle itself (gray filled 2px rectangle) indicates the self-message occurrence and span; proportional nesting depth through horizontal offset left |
| **Label Positioning** | Label text placed to the right of the lane (x=lane_x + 10), slightly above the bracket line (y - 2px); positioned like regular messages but anchored to the lane center |
| **Nesting Depth** | Bracket position follows same formula as spanning bracket nesting: `right_edge = lane_x - (2 + n*4)` for depth n |
| **Removes Complexity** | Eliminates need for ↩ character marker function and 3-segment arrow function; single unified rendering path for all self-messages |
| **Benefits** | Consistent visual style across all message types; no special characters in diagrams; spanning brackets provide clear duration/scope indication; cleaner SVG output; easier to maintain |
| **Status** | ✅ Implemented & Tested |

### ADR-009: Spanning Bracket Visual Redesign - Left-Side Duration Rectangles
| Aspect | Details |
|--------|---------|
| **Decision** | Replace 3-line L-shaped spanning brackets with 2px-wide filled rectangles on left side of lane; each nesting level extends further left |
| **Context** | Nested arrow brackets to the right of lanes created complexity, overlap, and wasted space. Most nested scenarios have a single caller that waits—space on the left can be used effectively |
| **Rationale** | Left-side rectangles indicate bracket duration/scope without adding visual complexity; nesting depth visible through horizontal offset; reduces rightward clutter and arrow overlap |
| **Consequences** | Spanning brackets now stack horizontally to the left (depth 0: x-2 to x-4, depth 1: x-6 to x-8, etc.); cleaner diagram appearance; label moved to tooltip (hover); rectangle height equals bracket duration |
| **Positioning Formula** | For depth n: `right_edge = lane_x - (2 + n*4)`, `left_edge = right_edge - 2`. Clamped to minimum x=20 to keep within diagram bounds |
| **Visual Properties** | Gray fill (#666), 70% opacity, 2px width, semi-transparent; provides subtle visual indicator without dominating the diagram |
| **Bracket Start Alignment** | Bracket rectangle begins at the y position where the first message inside the bracket starts (not before it) |
| **Message Spacing** | 10px gap between consecutive messages within brackets (increased from 2px) for improved readability |
| **Status** | ✅ Implemented & Tested (Commit: 743fa8f) |

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
|--------|---------|⤵
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

### ADR-011: Self-Message Function Name Label Alignment on Spanning Brackets
| Aspect | Details |
|--------|---------|
| **Decision** | For self-messages (src_obj == dst_obj), render function name label to the left of spanning bracket with label top aligned to bracket top (y_start); no label for cross-object messages |
| **Context** | Function names on spanning brackets needed clear positioning convention to avoid confusion about label placement relative to bracket start position |
| **Rationale** | Text top alignment with bracket top provides unambiguous visual relationship; browser-independent (uses SVG text baseline + ascent calculation); self-messages get labels, cross-object messages do not (labels already on message arrows) |
| **Implementation** | Text positioned with baseline at `y_start + ascent` where ascent ≈ 10px for 12px font; x-position at `bracket_left - TEXT_PADDING` (5px left of bracket); text-anchor="end" for right-alignment |
| **Visual Result** | For self-messages: function name appears aligned vertically with the top of the gray spanning bracket rectangle on the left side of the lane; top of text character aligns with top of bracket |
| **Self-Message Check** | Rendered as label only when `src_obj == dst_obj`; cross-object messages (Obj1→Obj2) omit bracket label and show label on message arrow instead |
| **Label Visibility** | Labels positioned left of brackets, text character height: ~10px top margin, ~2px descent; readable and non-overlapping |
| **Test Coverage** | test_self_message_label_alignment.csv: Verifies three nested self-messages (Msg1, Msg1a, Msg1b) all have labels top-aligned to bracket tops at their respective nesting depths |
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

## Final Metrics (Rendering Examples - Spanning Brackets Only for All Self-Messages)

### test_message_nesting.csv (Complex with Spanning Brackets)
```
Msg1 (self-message): Spanning bracket rectangle on left of Obj1, y=135→182
    └─ Msg1a (nested self-message): Spanning bracket at deeper nesting level (further left)
       ├─ Bracket: Gray 2px rectangle at nesting depth 1 (x=92-94)
       ├─ Label: "Msg1a()" positioned right of lane (x=110)
       ├─ Msg1b (cross-message): Regular arrow from Obj1 to Obj2 (different lanes)
       └─ response1b (return): Dashed return arrow, centered text
Msg1b (cross-message): Arrow from Obj1 (x=100) to Obj2 (x=160), y=150

Actual SVG rendering:
  - Msg1a bracket: <rect x="92" y="135" width="2" height="15" fill="#666" opacity="0.7"/>
  - Msg1a label: <text x="110" y="133">Msg1a()</text>
  - Msg1b arrow: <line x1="100" y1="150" x2="160" y2="150" marker-end="url(#arrow)"/>
```

### nested_self_messages.csv (All Simple Self-Messages with Spanning Brackets)
```
Msg1 at y=120:   Spanning bracket (depth 0, x=96-98) + label "Msg1()"
Msg1a at y=135:  Spanning bracket (depth 1, x=92-94) + label "Msg1a()"
Msg1b at y=120:  Regular arrow to Obj2
response at y=150: Return arrow with centered label

All self-messages render as spanning brackets - no character markers,
no 3-segment arrows. The bracket rectangle indicates message occurrence
and span; label appears to the right of the lane.
```


## Design Evolution Summary

**Phase 1-2 (Initial Spacing Optimization):**
- Reduced vertical spacing and standardized sizing
- Used traditional 3-line L-shaped brackets for multi-row messages

**Phase 3 (Rectangle-Based Left-Side Indicators):**
- Replaced complex 3-line brackets with simple 2px-wide left-side rectangles
- Nesting depth indicated by horizontal offset from lane
- Eliminates visual clutter and rightward overlap

**Phase 4 (Two-Tier Self-Message Simplification):**
- Simple self-messages: minimal ↩ character + label
- Complex self-messages: left-side duration rectangles
- Dramatic reduction in visual clutter and vertical space usage

**Phase 5 (Unified Spanning Bracket Approach - Current):**
- All self-messages use spanning brackets exclusively
- No character markers (↩); no explicit 3-segment arrows
- Left-side duration rectangles for all self-messages
- Nesting depth shown through horizontal offset
- Unified, consistent visual approach across all message types

## Key Improvements Across Phases

| Aspect | Original | Phase 3 | Phase 4 | Current (Phase 5) |
|--------|----------|---------|---------|-------------------|
| Simple self-messages | 3-segment brackets | 3-segment brackets | ↩ char only | Spanning bracket |
| Bracketed self-messages | 3-segment brackets | 3-segment brackets | 3-seg brackets | Spanning bracket |
| Complex self-messages | 3-segment brackets | Left rectangle | Left rectangle | Spanning bracket |
| Message gaps | 2px | 10px | 10px | 10px |
| Visual distinction | None (all same) | Low | Medium | High (bracket depth) |
| Space efficiency | Poor | Good | Very good | Excellent |
| Rendering complexity | High | Medium | Medium | Low (unified) |

## Decision Status: ✅ COMPLETE & FINALIZED
All design decisions implemented, tested, and validated. Final redesign unifies all self-message rendering to spanning brackets only, eliminating special character markers and explicit arrow overlays for maximum clarity and consistency.
