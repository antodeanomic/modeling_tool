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
                        
                        if note_type_str in ["Info", "Warning", "Error", "Success"]:
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
                    
                    # Initialize values
                    return_value = ""
                    param_values = []
                    function_note = None
                    
                    # Check for function note at the end of all values
                    # Function note would be: @NoteType, NoteContent
                    all_values = step_data[3:] if len(step_data) > 3 else []
                    
                    # Look for @ marker indicating a note
                    note_start_idx = None
                    for i, elem in enumerate(all_values):
                        if elem.startswith("@"):
                            note_start_idx = i
                            break
                    
                    # Extract values before the note (if any)
                    values_before_note = all_values[:note_start_idx] if note_start_idx is not None else all_values
                    
                    # Extract note if present
                    if note_start_idx is not None:
                        note_type = all_values[note_start_idx][1:]  # Remove @
                        note_content = " ".join(all_values[note_start_idx + 1:]) if note_start_idx + 1 < len(all_values) else ""
                        
                        if note_type in ["Info", "Warning", "Error", "Success"]:
                            function_note = NoteDef(note_type=note_type, content=note_content)
                    
                    # Now assign params and return values based on function definition
                    # Look up the function to see how many params and returns it has
                    func_def = model.get_function(src_obj, func)
                    
                    if func_def:
                        num_params = len(func_def.params)
                        num_returns = len(func_def.returns)
                        
                        # Assign first N values as params, rest as returns
                        param_values = values_before_note[:num_params]
                        returns_start =  num_params
                        if returns_start < len(values_before_note):
                            return_value = values_before_note[returns_start]  # Take first return value
                    else:
                        # Function not found, use default logic: first value is return, rest are params
                        if len(values_before_note) > 0:
                            return_value = values_before_note[0]
                            param_values = values_before_note[1:]
                    
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
    # but prevent wrapping back (e.g., can't go A->B->C->A without crossing lines)
    for seq in model.sequences:
        # Build a map of participant names to their left-to-right order
        participants = []
        for step in seq.steps:
            if step.src_obj not in participants:
                participants.append(step.src_obj)
            if step.dst_obj not in participants:
                participants.append(step.dst_obj)
        
        next_auto_row = 1  # Start auto-numbering from 1
        prev_direction = None  # Track direction of previous step
        prev_src_obj = None  # Track source object of previous step
        prev_dst_obj = None  # Track destination object of previous step
        row_min_idx = None  # Min participant index in current row
        row_max_idx = None  # Max participant index in current row
        
        for step in seq.steps:
            # If step has no explicit row number (None), auto-assign based on direction and extent
            if step.row is None:
                # Get participant indices
                src_idx = participants.index(step.src_obj) if step.src_obj in participants else -1
                dst_idx = participants.index(step.dst_obj) if step.dst_obj in participants else -1
                
                # Calculate direction and extent
                if step.src_obj == step.dst_obj:
                    direction = ('self', step.depth)
                    extent_min, extent_max = src_idx, src_idx
                else:
                    # For cross-object messages, include depth in the tuple: ('forward'/'backward', depth)
                    direction = ('forward' if src_idx < dst_idx else 'backward', step.depth)
                    extent_min = min(src_idx, dst_idx)
                    extent_max = max(src_idx, dst_idx)
                
                # Extract direction type and depth (all directions now include depth in tuple)
                curr_dir_type = direction[0]
                curr_depth = direction[1]
                
                # Check if we need a new row:
                # 1. Direction type changed (self vs forward vs backward)
                # 2. For self-messages: depth changed (each nesting level gets different row)
                # 3. For cross-object messages: depth decreased (returning from deeper nesting)
                # 4. Source changed on backward messages (context switch)
                # 5. Would wrap around (extend beyond previous range in a way that crosses)
                need_new_row = False
                if prev_direction is not None:
                    prev_dir_type = prev_direction[0]
                    prev_depth = prev_direction[1]
                    
                    if curr_dir_type != prev_dir_type:
                        need_new_row = True
                    else:
                        # Same direction type - check for depth changes and source changes
                        if curr_dir_type == 'self':
                            # For self-messages, any depth change triggers new row
                            if prev_depth != curr_depth:
                                need_new_row = True
                        else:
                            # For cross-object messages, depth decrease triggers new row
                            if curr_depth < prev_depth:
                                need_new_row = True
                            # Also trigger new row if source changed on backward messages
                            # (indicates returning from different call context)
                            elif curr_dir_type == 'backward' and step.src_obj != prev_src_obj:
                                need_new_row = True
                            # For consecutive backward messages from same source, check destination
                            # If destination changes significantly, trigger new row
                            elif curr_dir_type == 'backward' and step.src_obj == prev_src_obj and step.dst_obj != prev_dst_obj:
                                need_new_row = True
                            elif row_min_idx is not None and row_max_idx is not None:
                                # Check if this message would wrap around
                                # Forward direction: extent_min should not go backward
                                # Backward direction: extent_max should not go forward
                                if curr_dir_type == 'forward' and extent_min < row_min_idx:
                                    need_new_row = True
                                elif curr_dir_type == 'backward' and extent_max > row_max_idx:
                                    need_new_row = True
                
                if need_new_row:
                    next_auto_row += 1
                    row_min_idx = None
                    row_max_idx = None
                
                step.row = next_auto_row
                
                # Update row extent (for self-messages, don't expand the range)
                if curr_dir_type != 'self':
                    if row_min_idx is None:
                        row_min_idx = extent_min
                        row_max_idx = extent_max
                    else:
                        row_min_idx = min(row_min_idx, extent_min)
                        row_max_idx = max(row_max_idx, extent_max)
                
                prev_direction = direction
                prev_src_obj = step.src_obj
                prev_dst_obj = step.dst_obj
            else:
                # Explicit row number provided - reset tracking
                prev_direction = None
                prev_src_obj = None
                prev_dst_obj = None
                row_min_idx = None
                row_max_idx = None
                next_auto_row = max(next_auto_row, step.row + 1)

    return model