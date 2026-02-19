import csv
from model import (
    Model, ClassDef, MemberVar, FunctionDef, ParamDef, ReturnDef,
    SequenceDef, SequenceStep, StateMachineDef, StateDef
)

def clean(s: str) -> str:
    if s is None:
        return ""
    return s.replace("\u00A0", "").replace("\t", "").strip()

def parse_indent(type_field: str) -> tuple[int, str]:
    leading_spaces = len(type_field) - len(type_field.lstrip(" "))
    level = leading_spaces // 4
    return level, type_field.lstrip(" ")

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
                    if name and name[0] in ['+', '-']:
                        visibility = name[0]
                        func_name = name[1:]
                    else:
                        visibility = '+'
                        func_name = name
                    f = FunctionDef(
                        visibility=visibility,
                        name=func_name,
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
                # Parse step: [Row#], Obj1, Obj2, Func, RetVal, ParamVal1, ParamVal2, ...
                # Row# is optional - if first field (column 0, unindented) is a number, it's the row
                if type_name not in ["SequenceObjects", "SequenceStep"]:
                    # Check if type_name (first field) is the row number
                    row_num = 0
                    all_step_data = [type_name] + [clean(c) for c in row[1:] if clean(c)]
                    start_idx = 0
                    
                    try:
                        row_num = int(type_name)
                        start_idx = 1  # Skip the row number, start from Object1
                    except ValueError:
                        # type_name is actually the source object
                        row_num = 0
                        start_idx = 0
                    
                    step_data = all_step_data[start_idx:]
                    
                    # Need at least Obj1, Obj2, Func
                    if len(step_data) < 3:
                        continue
                    
                    src_obj = step_data[0]
                    dst_obj = step_data[1]
                    func = step_data[2]
                    
                    # Optional: RetVal at index 3
                    return_value = ""
                    param_values = []
                    
                    if len(step_data) > 3:
                        return_value = step_data[3]
                    
                    # Remaining elements are parameter values
                    if len(step_data) > 4:
                        param_values = step_data[4:]
                    
                    step = SequenceStep(
                        depth=level - 1,
                        src_obj=src_obj,
                        function=func,
                        dst_obj=dst_obj,
                        description="",
                        row=row_num,
                        return_value=return_value,
                        param_values=param_values
                    )
                    parent.steps.append(step)
                continue

    return model