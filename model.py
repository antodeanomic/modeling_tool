from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class ParamDef:
    name: str
    description: str
    verbosity: str

@dataclass
class ReturnDef:
    name: str
    description: str
    verbosity: str

@dataclass
class FunctionDef:
    visibility: str
    name: str
    description: str
    verbosity: str
    params: List[ParamDef] = field(default_factory=list)
    returns: List[ReturnDef] = field(default_factory=list)

@dataclass
class MemberVar:
    name: str
    description: str
    verbosity: str

@dataclass
class ClassDef:
    name: str
    description: str
    members: List[MemberVar] = field(default_factory=list)
    functions: List[FunctionDef] = field(default_factory=list)

@dataclass
class SequenceDef:
    seq_id: str
    headline: str
    description: str
    lanes: List[str] = field(default_factory=list)
    steps: List[List[str]] = field(default_factory=list)

@dataclass
class Model:
    classes: List[ClassDef] = field(default_factory=list)
    sequences: List[SequenceDef] = field(default_factory=list)

    def get_sequence(self, seq_id: str) -> Optional[SequenceDef]:
        for s in self.sequences:
            if s.seq_id == seq_id:
                return s
        return None

    def get_function(self, class_name: str, func_name: str) -> Optional[FunctionDef]:
        for c in self.classes:
            if c.name == class_name:
                for f in c.functions:
                    if f.name == func_name:
                        return f
        return None