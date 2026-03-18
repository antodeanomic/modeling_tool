# CONNECTOR LOG FORMAT - CORRECT EXAMPLES

ALL 8 THREE-SEGMENT ROUTING COMBINATIONS - GEOMETRY-BASED CORNER ALIGNMENT

Key Principle: The number of dashes between '+' marks reflects actual coordinate distance (dx / 50).
Each '+' is a corner/junction where segments meet. The spacing shows the geometry.

==================================================================================================================================
COMBINATION 1: Down, Right, Down (small offset - dx=31.3 px, 1 dash)
==================================================================================================================================

SequenceStep -> NoteDef  (Down, Right, Down)
Text              Routing
                               ◇
'1'                            |
'function_note'                +-+
'0..1'                          |
                                ◇


==================================================================================================================================
COMBINATION 2: Down, Right, Down (medium offset - dx=126.4 px, 2 dashes)
==================================================================================================================================

ClassDef -> MemberVar  (Down, Right, Down)
Text              Routing
                               ◆
'1'                            |
'owns'                         +--+
'0.*'                             |
                                   ◆


==================================================================================================================================
COMBINATION 3: Down, Right, Down (larger offset - dx=188.5 px, 3 dashes)
==================================================================================================================================

FunctionDef -> ReturnDef  (Down, Right, Down)
Text              Routing
                               ◆
'1'                            |
'owns'                         +---+
'0.*'                              |
                                    ◆


==================================================================================================================================
COMBINATION 4: Right, Down, Right (large offset - dx=396.0 px, 7 dashes)
==================================================================================================================================

ClassDef -> StateMachineDef  (Right, Down, Right)
Text              Routing
'1'                            ◆-------+
'owns'                                 |
'0.*'                                 +-------◆


==================================================================================================================================
COMBINATION 5: Right, Down, Right (very large offset - dx=419.4 px, 8 dashes)
==================================================================================================================================

SequenceDef -> SequenceStep  (Right, Down, Right)
Text              Routing
'1'                            ◆--------+
'owns'                                  |
'1.*'                                  +--------◆


==================================================================================================================================
DOWN-LEFT-DOWN (target below, left offset)
==================================================================================================================================

Obj1 -> Obj2  (Down, Left, Down)
Text              Routing
                               ◆
'1'                            |
'owns'                      +--+
'0.*'                       |
                           ◆


==================================================================================================================================
LEFT-DOWN-LEFT (target left, down offset)
==================================================================================================================================

Obj1 -> Obj2  (Left, Down, Left)
Text              Routing
'1'                      +--◆
'owns'                  |
'0.*'               ◆--+


==================================================================================================================================
UP-RIGHT-UP (target above, right offset)
==================================================================================================================================

Obj1 -> Obj2  (Up, Right, Up)
Text              Routing
                                ◆
'1'                            |
'owns'                         +--+
'0.*'                             |
                                   ◆


==================================================================================================================================
UP-LEFT-UP (target above, left offset)
==================================================================================================================================

Obj1 -> Obj2  (Up, Left, Up)
Text              Routing
                           ◆
'1'                            |
'owns'                      +--+
'0.*'                       |
                           ◆


==================================================================================================================================
KEY RULES ENFORCED:
==================================================================================================================================
1. Text column contains ONLY: src_mult, label, tgt_mult (3 values, no arrow symbols)
2. Routing column is PURE ASCII - no object names, object names shown only in header
3. Endpoints marked with ◆ or ◇ (from relationship arrow type)
4. Text ONLY appears on lines with the 3 key segments (src_mult, label, tgt_mult)
5. Empty text lines (for endpoints and intermediate segments) use blank left column
6. '+' marks show corners and MUST ALIGN with vertical '|' and horizontal '-' lines
7. Alignment is critical: ASCII routing reflects segment positions relative to text

