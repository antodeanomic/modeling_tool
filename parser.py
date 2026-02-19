import csv
from model import (
    Model, ClassDef, MemberVar, FunctionDef, ParamDef, ReturnDef,
    SequenceDef
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
            verbosity = clean(row[3]) if len(row) > 3 else ""

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
                        description=verbosity
                    )
                    model.sequences.append(seq)
                    current_sequence = seq
                    stack.append(seq)

                continue

            # Inside a class
            if isinstance(parent, ClassDef):
                if type_name == "MemberVar":
                    parent.members.append(MemberVar(name, desc, verbosity))

                elif type_name == "Function":
                    visibility = name[0]
                    func_name = name[1:]
                    f = FunctionDef(
                        visibility=visibility,
                        name=func_name,
                        description=desc,
                        verbosity=verbosity
                    )
                    parent.functions.append(f)
                    stack.append(f)

                continue

            # Inside a function
            if isinstance(parent, FunctionDef):
                if type_name == "Param":
                    parent.params.append(ParamDef(name, desc, verbosity))
                elif type_name == "ReturnVal":
                    parent.returns.append(ReturnDef(name, desc, verbosity))
                continue

            # Inside a sequence
            if isinstance(parent, SequenceDef):
                if type_name == "SequenceObjects":
                    parent.lanes = [clean(c) for c in row[1:] if clean(c)]

                elif type_name == "SequenceStep":
                    parent.steps.append([clean(c) for c in row[1:]])

                continue

    return model