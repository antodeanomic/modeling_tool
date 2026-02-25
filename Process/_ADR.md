# Architecture Decision Records (ADRs)

## UML Sequence Diagram Rendering - Spacing & Layout Optimization

### ADR-010: Self-Message Rendering Simplification - Three-Tier Approach
| Aspect | Details |
|--------|---------|
| **Decision** | Use three distinct rendering modes for self-messages based on context: small 3-segment arrows for bracketed, ↩ markers for simple, skip for bracket endpoints |
| **Context** | Self-messages can be simple (no nesting), complex (start/end spanning bracket), or nested within another bracket; unified rendering was visually confusing |
| **Three Modes** | **1) Inside spanning bracket:** Compact 3-segment arrow (12px wide, 10px tall) on left of lane, same arrowhead style as message overlays. **2) Simple/outside brackets:** Minimal ↩ character + label. **3) Bracket endpoints:** Skip rendering (spanning bracket rectangle indicates the scope) |
| **Small Arrow Design** | Horizontal segment left from lane, vertical segment down, horizontal return with arrowhead. Uses same arrow marker (#arrow) as other message arrows for visual consistency |
| **Visual Hierarchy** | Spanning bracket rectangle shows scope and duration; contained self-messages have small arrows; outside messages use character marker. Context immediately apparent from rendering style |
| **Benefits** | Eliminates all full 3-segment brackets; deeply nested scenarios stay clean; simple vs complex immediately distinguishable; minimal vertical space |
| **Status** | ✅ Implemented & Tested (Commit: 1be64ed) |

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

## Final Metrics (Rendering Examples - Current Three-Tier Design)

### test_message_nesting.csv (Complex with Nesting)
```
Msg1 (bracket start): Spanning bracket rectangle on left, x=96-98, y=135→182
    └─ Msg1a (inside bracket): ↙-↓-→ small 3-segment arrow, 12px wide, 10px tall
       └─ Msg1b (cross-message): regular arrow to Obj2
       └─ response1b (return): dashed return arrow, centered text
Msg1 (bracket end): Spanning bracket rectangle closes

Layout:
  ┌─[bracket]
  │ → Msg1a()         (small 3-seg arrow)
  │   Msg1b-------->  (regular message)
  │   <--response1b   (return arrow)
  └─[/bracket]
```

### nested_self_messages.csv (All Simple, No Brackets)
```
Msg1() at y=120:  ↩ Msg1()           (simple marker)
Msg1a() at y=135: ↩ Msg1a()          (simple marker)
Msg1b at y=120:   arrow to Obj2
response at y=150: return arrow

All self-messages render as minimal ↩ character since none
are inside spanning brackets.
```

### Design Modes in Action
| Location | Self-Message Type | Rendering | Space Used |
|----------|------------------|-----------|-----------|
| Inside spanning bracket | Nested/complex | Small 3-segment arrow (12×10px) | Minimal |
| Outside all brackets | Simple/standalone | ↩ character + label | Minimal |
| Bracket endpoints | Complex container | Spanning rectangle only | Vertical span only |

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

**Phase 5 (Current - Three-Tier Self-Message Optimization):**
- Inside brackets: compact 3-segment arrow (12×10px) with message overlay arrowhead
- Simple/standalone: minimal ↩ character
- Bracket endpoints: skip rendering (rectangle shows scope)
- Cleaner visual distinction between contexts
- Optimized for readability and vertical space efficiency

## Key Improvements Across Phases

| Aspect | Original | Phase 3 | Phase 4 | Current (Phase 5) |
|--------|----------|---------|---------|-------------------|
| Simple self-messages | 3-segment brackets | 3-segment brackets | ↩ char only | ↩ char only |
| Bracketed self-messages | 3-segment brackets | 3-segment brackets | 3-seg brackets | Small 3-seg arrows |
| Complex self-messages | 3-segment brackets | Left rectangle | Left rectangle | Left rectangle |
| Message gaps | 2px | 10px | 10px | 10px |
| Visual distinction | None | Low | Medium | High |
| Space efficiency | Poor | Good | Very good | Excellent |

## Decision Status: ✅ COMPLETE & EVOLVED
All design decisions implemented, tested, and validated. Latest redesign improves visual clarity while maintaining backward compatibility.
