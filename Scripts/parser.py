import csv
import os
from difflib import get_close_matches
from model import (
    Model, ClassDef, MemberVar, FunctionDef, ParamDef, ReturnDef,
    SequenceDef, SequenceStep, StateMachineDef, StateDef, NoteDef,
    ClassDiagramDef, ClassRelationship, ELEMENT_TYPES, ROUTING_MODES
)

def clean(s: str) -> str:
    if s is None:
        return ""
    return s.replace("\u00A0", "").replace("\t", "").strip()

def parse_indent(type_field: str) -> tuple[int, str]:
    leading_spaces = len(type_field) - len(type_field.lstrip(" "))
    level = leading_spaces // 4
    return level, type_field.lstrip(" ").strip()

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

def validate_model(model: Model) -> list[str]:
    """Validate sequence steps against class definitions.
    
    Checks that all class and function references in sequence steps
    match defined classes/functions. Returns a list of warning messages
    with suggestions for close matches.
    """
    warnings = []
    class_names = [c.name for c in model.classes]
    
    # Build a map of class -> function names
    class_functions = {}
    for c in model.classes:
        func_names = []
        for f in c.functions:
            base_name = f.name.split('(')[0] if '(' in f.name else f.name
            func_names.append(base_name)
        class_functions[c.name] = func_names
    
    for seq in model.sequences:
        for step in seq.steps:
            # Check source object
            if step.src_obj and model.get_class(step.src_obj) is None:
                matches = get_close_matches(step.src_obj, class_names, n=3, cutoff=0.6)
                if matches:
                    warnings.append(
                        f"[{seq.seq_id}] Class '{step.src_obj}' not found. "
                        f"Did you mean: {', '.join(matches)}?"
                    )
                else:
                    warnings.append(
                        f"[{seq.seq_id}] Class '{step.src_obj}' not found. "
                        f"Available classes: {', '.join(class_names) if class_names else '(none)'}"
                    )
            
            # Check destination object
            if step.dst_obj and step.dst_obj != step.src_obj and model.get_class(step.dst_obj) is None:
                matches = get_close_matches(step.dst_obj, class_names, n=3, cutoff=0.6)
                if matches:
                    warnings.append(
                        f"[{seq.seq_id}] Class '{step.dst_obj}' not found. "
                        f"Did you mean: {', '.join(matches)}?"
                    )
                else:
                    warnings.append(
                        f"[{seq.seq_id}] Class '{step.dst_obj}' not found. "
                        f"Available classes: {', '.join(class_names) if class_names else '(none)'}"
                    )
            
            # Check function exists on source class (caller owns the function)
            if step.function and step.src_obj:
                src_class = model.get_class(step.src_obj)
                if src_class:
                    func_found = model.get_function(step.src_obj, step.function)
                    if not func_found:
                        available = class_functions.get(step.src_obj, [])
                        matches = get_close_matches(step.function, available, n=3, cutoff=0.6)
                        if matches:
                            warnings.append(
                                f"[{seq.seq_id}] Function '{step.function}' not found in class "
                                f"'{step.src_obj}'. Did you mean: {', '.join(matches)}?"
                            )
                        elif available:
                            warnings.append(
                                f"[{seq.seq_id}] Function '{step.function}' not found in class "
                                f"'{step.src_obj}'. Available functions: {', '.join(available)}"
                            )
    
    # Validate class diagram relationships
    for cd in model.class_diagrams:
        for rel in cd.relationships:
            # Check source class exists
            if rel.source and model.get_class(rel.source) is None:
                matches = get_close_matches(rel.source, class_names, n=3, cutoff=0.6)
                if matches:
                    warnings.append(
                        f"[{cd.diagram_id}] Class '{rel.source}' not found. "
                        f"Did you mean: {', '.join(matches)}?"
                    )
                else:
                    warnings.append(
                        f"[{cd.diagram_id}] Class '{rel.source}' not found. "
                        f"Available classes: {', '.join(class_names) if class_names else '(none)'}"
                    )
            # Check target class exists
            if rel.target and model.get_class(rel.target) is None:
                matches = get_close_matches(rel.target, class_names, n=3, cutoff=0.6)
                if matches:
                    warnings.append(
                        f"[{cd.diagram_id}] Class '{rel.target}' not found. "
                        f"Did you mean: {', '.join(matches)}?"
                    )
                else:
                    warnings.append(
                        f"[{cd.diagram_id}] Class '{rel.target}' not found. "
                        f"Available classes: {', '.join(class_names) if class_names else '(none)'}"
                    )
            # Check arrow is valid
            if rel.arrow and rel.arrow not in VALID_ARROWS:
                warnings.append(
                    f"[{cd.diagram_id}] Invalid arrow '{rel.arrow}' for "
                    f"'{rel.source}' -> '{rel.target}'. "
                    f"Valid arrows: {', '.join(sorted(VALID_ARROWS))}"
                )

    return warnings

# Valid UML class diagram arrow types
VALID_ARROWS = {
    # Solid line (structural)
    '--',     # Association
    '-->',    # Directed Association (left to right)
    '<--',    # Directed Association (right to left)
    '<-->',   # Bidirectional Association
    '--\u25b7',   # Generalization (left extends right)
    '\u25c1--',   # Generalization (right extends left)
    '--\u25c6',   # Composition (right owns left, strong)
    '\u25c6--',   # Composition (left owns right, strong)
    '--\u25c7',   # Aggregation (right contains left, weak)
    '\u25c7--',   # Aggregation (left contains right, weak)
    # Dashed line (behavioral)
    '..>',    # Dependency (left depends on right)
    '<..',    # Dependency (right depends on left)
    '..\u25b7',   # Realization (left implements right)
    '\u25c1..',   # Realization (right implements left)
}

def parse_diagram_relationship_params(row: list[str], start_idx: int) -> tuple[str, list[str]]:
    """Parse optional diagram hierarchy parameters from CSV columns.

    Supported forms:
      - parent=DiagramId
      - children=ChildA,ChildB
      - child=ChildA,ChildB
    """
    parent_diagram = ""
    child_diagrams = []

    for col_idx in range(start_idx, len(row)):
        param = clean(row[col_idx])
        if not param:
            continue

        if param.startswith("parent="):
            parent_diagram = param.split("=", 1)[1].strip()
        elif param.startswith("children=") or param.startswith("child="):
            raw_children = param.split("=", 1)[1].strip()
            if raw_children:
                child_diagrams.extend(
                    child_name.strip()
                    for child_name in raw_children.split(",")
                    if child_name.strip()
                )

    # Preserve order while removing duplicates.
    deduped_children = []
    for child_name in child_diagrams:
        if child_name not in deduped_children:
            deduped_children.append(child_name)

    return parent_diagram, deduped_children

def parse_traceability_params(row: list[str], start_idx: int) -> tuple[list[str], list[str], list[str], list[str]]:
    """Parse explicit traceability IDs from optional CSV parameters.

    Supported forms (comma-separated values):
      - trace_req=...
      - trace_story=...
      - trace_test=...
      - trace_feature=...
    Aliases:
      - req=..., story=..., test=..., feature=...
    """
    req_ids = []
    story_ids = []
    test_ids = []
    feature_ids = []

    def _add_ids(raw_value: str, bucket: list[str]):
        for item in raw_value.split(','):
            item = item.strip()
            if item and item not in bucket:
                bucket.append(item)

    for col_idx in range(start_idx, len(row)):
        param = clean(row[col_idx])
        if not param or '=' not in param:
            continue

        key, value = param.split('=', 1)
        key = key.strip().lower()
        value = value.strip()
        if not value:
            continue

        if key in ('trace_req', 'req'):
            _add_ids(value, req_ids)
        elif key in ('trace_story', 'story'):
            _add_ids(value, story_ids)
        elif key in ('trace_test', 'test'):
            _add_ids(value, test_ids)
        elif key in ('trace_feature', 'feature'):
            _add_ids(value, feature_ids)

    return req_ids, story_ids, test_ids, feature_ids

def parse_csv(path: str, _included_paths: set = None) -> Model:
    model = Model()
    stack = []
    current_sequence = None

    # Track included files to prevent circular includes
    abs_path = os.path.abspath(path)
    is_top_level = _included_paths is None
    if _included_paths is None:
        _included_paths = set()
    if abs_path in _included_paths:
        return model  # Skip circular include
    _included_paths.add(abs_path)

    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f, delimiter=';')
        first_row = next(reader, None)

        def _row_stream():
            if first_row is not None:
                first_type = clean(first_row[0]) if len(first_row) > 0 else ""
                first_name = clean(first_row[1]) if len(first_row) > 1 else ""
                has_header = first_type == "Type" and first_name == "Name"
                if not has_header:
                    yield first_row
            for r in reader:
                yield r

        for row in _row_stream():
            if not row or not clean(row[0]):
                continue

            type_field = row[0]
            name = clean(row[1]) if len(row) > 1 else ""
            desc = clean(row[2]) if len(row) > 2 else ""
            layer = clean(row[3]) if len(row) > 3 else ""  # Optional layer assignment

            level, type_name = parse_indent(type_field)

            while len(stack) > level:
                stack.pop()

            parent = stack[-1] if stack else None

            # Top-level
            if level == 0:
                if type_name == "Include":
                    # Include another CSV file - resolve path relative to current file
                    include_path = os.path.join(os.path.dirname(abs_path), name)
                    include_path = os.path.normpath(include_path)
                    if os.path.isfile(include_path):
                        included_model = parse_csv(include_path, _included_paths)
                        model.classes.extend(included_model.classes)
                        model.sequences.extend(included_model.sequences)
                        model.class_diagrams.extend(included_model.class_diagrams)

                elif type_name == "Class":
                    class_layer = ""
                    for col_idx in range(3, len(row)):
                        param = clean(row[col_idx])
                        if not param:
                            continue
                        if param.startswith("layer="):
                            class_layer = param.split("=", 1)[1].strip()
                        elif '=' not in param and not class_layer:
                            # Backward-compatible positional layer assignment.
                            class_layer = param

                    req_ids, story_ids, test_ids, feature_ids = parse_traceability_params(row, 3)
                    c = ClassDef(
                        name=name,
                        description=desc,
                        layer=class_layer,
                        trace_requirement_ids=req_ids,
                        trace_user_story_ids=story_ids,
                        trace_test_case_ids=test_ids,
                        trace_feature_ids=feature_ids
                    )
                    model.classes.append(c)
                    stack.append(c)

                elif type_name == "Sequence":
                    sequence_description = clean(row[3]) if len(row) > 3 else desc
                    parent_diagram, child_diagrams = parse_diagram_relationship_params(row, 4)
                    seq = SequenceDef(
                        seq_id=name,
                        headline=desc,
                        description=sequence_description,
                        parent_diagram=parent_diagram,
                        child_diagrams=child_diagrams
                    )
                    model.sequences.append(seq)
                    current_sequence = seq
                    stack.append(seq)

                elif type_name == "ClassDiagram":
                    # Parse optional parameters from remaining columns
                    routing = "auto"
                    element_types = {}
                    parent_diagram, child_diagrams = parse_diagram_relationship_params(row, 3)
                    for col_idx in range(3, len(row)):
                        param = clean(row[col_idx])
                        if param.startswith("routing="):
                            routing = param.split("=", 1)[1].strip().lower()
                            if routing not in ROUTING_MODES:
                                model.warnings.append(f"Unknown routing mode '{routing}', using 'auto'")
                                routing = "auto"
                        elif param.startswith("element_type="):
                            # Format: element_type=Name:type,Name:type
                            pairs = param.split("=", 1)[1].strip()
                            for pair in pairs.split(","):
                                pair = pair.strip()
                                if ":" in pair:
                                    ename, etype = pair.split(":", 1)
                                    ename = ename.strip()
                                    etype = etype.strip()
                                    if etype in ELEMENT_TYPES:
                                        element_types[ename] = etype
                                    else:
                                        model.warnings.append(f"Unknown element type '{etype}' for '{ename}'")
                    cd = ClassDiagramDef(
                        diagram_id=name,
                        description=desc,
                        routing=routing,
                        element_types=element_types,
                        parent_diagram=parent_diagram,
                        child_diagrams=child_diagrams
                    )
                    model.class_diagrams.append(cd)
                    stack.append(cd)

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

            # Inside a class diagram
            # Row format: Source;Target;Arrow;SrcMult;TgtMult;Label;Layer
            if isinstance(parent, ClassDiagramDef):
                # type_name is the Source class (first column after indent)
                source = type_name
                target = name  # second column
                arrow = desc   # third column
                src_mult = clean(row[3]) if len(row) > 3 else ""
                tgt_mult = clean(row[4]) if len(row) > 4 else ""
                label = clean(row[5]) if len(row) > 5 else ""
                layer = clean(row[6]) if len(row) > 6 else ""

                if source and target and arrow:
                    if arrow not in VALID_ARROWS:
                        # Not a fatal error, just a warning collected later
                        pass
                    rel = ClassRelationship(
                        source=source,
                        target=target,
                        arrow=arrow,
                        src_mult=src_mult,
                        tgt_mult=tgt_mult,
                        label=label,
                        layer=layer
                    )
                    parent.relationships.append(rel)
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

    # Only validate at the top-level call (not during #include processing)
    if is_top_level:
        model.warnings = validate_model(model)
        for w in model.warnings:
            print(f"\033[91m  [!] {w}\033[0m")

    return model