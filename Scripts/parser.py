import csv
from model import (
    Model, ClassDef, MemberVar, FunctionDef, ParamDef, ReturnDef,
    SequenceDef, SequenceStep, StateMachineDef, StateDef, NoteDef
)

def clean(s: str) -> str:
    if s is None:
        return ""
    return s.replace("\u00A0", "").replace("\t", "").strip()

def parse_indent(type_field: str) -> tuple[int, str]:
    leading_spaces = len(type_field) - len(type_field.lstrip(" "))
    level = leading_spaces // 4
    return level, type_field.lstrip(" ")

def parse_note(note_str: str) -> tuple[str, str]:
    """Parse note syntax like @Info,Note content or @Warning,Alert message.
    
    Returns (note_type, content) or (None, None) if not a valid note.
    """
    note_str = note_str.strip()
    if not note_str.startswith("@"):
        return None, None
    
    # Remove @ and split on first comma
    rest = note_str[1:]
    if "," not in rest:
        return None, None
    
    note_type, content = rest.split(",", 1)
    note_type = note_type.strip()
    content = content.strip()
    
    if note_type in ["Info", "Warning", "Error"]:
        return note_type, content
    
    return None, None

def parse_csv(path: str) -> Model:
    model = Model()
    stack = []
    current_sequence = None

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)

        for row in reader:
            if not row or not clean(row[0]):
                continue

            type_field = row[0]
            name = clean(row[1]) if len(row) > 1 else ""
            desc = clean(row[2]) if len(row) > 2 else ""

            level, type_name = parse_indent(type_field)

            while len(stack) > level:
                stack.pop()

            parent = stack[-1] if stack else None

            # Top-level
            if level == 0:
                if type_name == "Class":
                    c = ClassDef(name=name, description=desc)
                    model.classes.append(c)
                    stack.append(c)

                elif type_name == "Sequence":
                    seq = SequenceDef(
                        seq_id=name,
                        headline=desc,
                        description=desc
                    )
                    model.sequences.append(seq)
                    current_sequence = seq
                    stack.append(seq)

                continue

            # Inside a class
            if isinstance(parent, ClassDef):
                if type_name == "MemberVar":
                    parent.members.append(MemberVar(name, desc))

                elif type_name == "Function":
                    # Handle optional visibility prefix (+/-) or use the name as-is
                    # Extract visibility from the name if present
                    visibility = '+'
                    func_name = name
                    if name and name[0] in ['+', '-']:
                        visibility = name[0]
                        func_name = name[1:]
                    
                    # For the FunctionDef.name field, preserve the full function signature
                    # (e.g., "ValidateOrder() : isValid") without the visibility prefix
                    f = FunctionDef(
                        visibility=visibility,
                        name=func_name,  # This preserves the full signature like "ValidateOrder() : isValid"
                        description=desc
                    )
                    parent.functions.append(f)
                    stack.append(f)
                
                elif type_name == "StateMachine":
                    sm = StateMachineDef(name=name, description=desc)
                    parent.state_machines.append(sm)
                    stack.append(sm)

                continue

            # Inside a function
            if isinstance(parent, FunctionDef):
                if type_name == "Param":
                    parent.params.append(ParamDef(name, desc))
                elif type_name == "ReturnVal":
                    parent.returns.append(ReturnDef(name, desc))
                continue
            
            # Inside a state machine
            if isinstance(parent, StateMachineDef):
                if type_name == "State":
                    parent.states.append(StateDef(name=name, description=desc))
                continue

            # Inside a sequence
            if isinstance(parent, SequenceDef):
                # Parse step: [Obj1, Obj2, Func, RetVal, ParamVal1, ..., [@NoteType, NoteContent]]
                # Row number is optional:
                #   - If provided as first field: [Row#, Obj1, Obj2, Func, ...]
                #   - If omitted: [Obj1, Obj2, Func, ...] - auto-assigned later based on direction awareness
                # Lane note: [LaneName, @NoteType, NoteContent]
                # Direction-aware: consecutive messages in same direction can overlap (saves vertical space)
                if type_name not in ["SequenceObjects", "SequenceStep"]:
                    # Check if type_name (first field) is the row number
                    row_num = None  # Will be auto-assigned if not provided
                    all_step_data = [type_name] + [clean(c) for c in row[1:] if clean(c)]
                    start_idx = 0
                    has_explicit_row = False
                    
                    try:
                        row_num = int(type_name)
                        start_idx = 1  # Skip the row number, start from Object1
                        has_explicit_row = True
                    except ValueError:
                        # type_name is actually the source object (no explicit row number)
                        # Will auto-assign later based on direction
                        row_num = None
                        start_idx = 0
                    
                    step_data = all_step_data[start_idx:]
                    
                    # Check if this is a lane note (LaneName, @NoteType, Description...)
                    # A lane note has 2+ elements where element[1] starts with @
                    if len(step_data) >= 2 and step_data[1].startswith("@"):
                        lane_name = step_data[0]
                        note_type_str = step_data[1][1:]  # Remove @
                        # Reconstruct description from remaining elements
                        note_content = " ".join(step_data[2:]) if len(step_data) > 2 else ""
                        
                        if note_type_str in ["Info", "Warning", "Error"]:
                            # This is a lane note
                            if len(parent.steps) > 0:
                                # Add to the last step
                                last_step = parent.steps[-1]
                                last_step.lane_notes[lane_name] = NoteDef(note_type=note_type_str, content=note_content)
                            continue
                    
                    # Need at least Obj1, Obj2, Func for a regular step
                    if len(step_data) < 3:
                        continue
                    
                    src_obj = step_data[0]
                    dst_obj = step_data[1]
                    func = step_data[2]
                    
                    # Optional: RetVal at index 3
                    return_value = ""
                    param_values = []
                    function_note = None
                    
                    if len(step_data) > 3:
                        return_value = step_data[3]
                    
                    # Check for function note at the end
                    # Function note would be: @NoteType, NoteContent
                    remaining = step_data[4:] if len(step_data) > 4 else []
                    
                    # Look for @ marker indicating a note
                    note_start_idx = None
                    for i, elem in enumerate(remaining):
                        if elem.startswith("@"):
                            note_start_idx = i
                            break
                    
                    if note_start_idx is not None:
                        # Note found in remaining data
                        param_values = remaining[:note_start_idx]
                        
                        note_type = remaining[note_start_idx][1:]  # Remove @
                        # Reconstruct note content from remaining elements
                        note_content = " ".join(remaining[note_start_idx + 1:]) if note_start_idx + 1 < len(remaining) else ""
                        
                        if note_type in ["Info", "Warning", "Error"]:
                            function_note = NoteDef(note_type=note_type, content=note_content)
                    else:
                        # No note, all remaining are param values
                        param_values = remaining
                    
                    step = SequenceStep(
                        depth=level - 1,
                        src_obj=src_obj,
                        function=func,
                        dst_obj=dst_obj,
                        description="",
                        row=row_num,
                        return_value=return_value,
                        param_values=param_values,
                        function_note=function_note
                    )
                    parent.steps.append(step)
                continue

    # Post-processing: assign row numbers to steps that don't have explicit ones
    # Use direction-aware assignment: consecutive messages in same direction get same row number
    for seq in model.sequences:
        next_auto_row = 1  # Start auto-numbering from 1
        prev_direction = None  # Track direction of previous step
        
        for step in seq.steps:
            # If step has no explicit row number (None), auto-assign based on direction
            if step.row is None:
                # Calculate direction: either left-to-right, right-to-left, or same (self-message)
                if step.src_obj == step.dst_obj:
                    # Self-message - can overlap with other self-messages at same depth
                    direction = ('self', step.depth)
                else:
                    # Compare object names lexicographically to determine direction
                    # This is consistent and doesn't depend on order in layout
                    direction = ('forward' if step.src_obj < step.dst_obj else 'backward')
                
                # If direction changed from previous step, move to next row
                if prev_direction is not None and direction != prev_direction:
                    next_auto_row += 1
                
                step.row = next_auto_row
                prev_direction = direction
            else:
                # Explicit row number provided - reset tracking
                prev_direction = None
                next_auto_row = max(next_auto_row, step.row + 1)

    return model