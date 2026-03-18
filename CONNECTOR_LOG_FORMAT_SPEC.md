# CONNECTOR LOG FORMAT SPECIFICATION - LOCKED

## Format Requirements

### Vertical Routing (Down, Right, Down)
```
Obj1 -> Obj2  (Down, Right, Down)
Text              Routing    
                    ◆         <- endpoint (no text)
'1'                 |         <- first segment with text
'owns'           +--- ---+    <- middle segment with text
'1..*'                   |    <- third segment with text
                         ◆    <- endpoint (no text)
```

### Horizontal Routing (Right, Down, Right)
```
Obj1 -> Obj2  (Right, Down, Right)
Text              Routing                                 
'1'                 ◆-- ---+   <- first segment with text (endpoint shown)
'owns'                       |  <- middle segment (no text)
'1..*'                          +--- ---◆  <- third segment with text (endpoint shown)
```

## Rules
1. Header shows: "Obj1 -> Obj2  (direction, direction, direction)"
2. Two-column table: "Text" column | "Routing" column
3. Text column shows: src_multiplicity, label, tgt_multiplicity (only 3 values)
4. Text position follows the connection segment it represents
5. Endpoints drawn as: ◆ (for composition) or ◇ (for aggregation)
6. Line segments use: | for vertical, -- for horizontal, + for corners, - for bridges
7. Extra segments between key points have NO text (blank left column)

## THIS FORMAT IS NOW LOCKED - DO NOT CHANGE WITHOUT EXPLICIT USER REQUEST
