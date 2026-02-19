from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class ParamDef:
    name: str
    description: str

@dataclass
class ReturnDef:
    name: str
    description: str

@dataclass
class StateDef:
    name: str
    description: str

@dataclass
class StateMachineDef:
    name: str
    description: str
    states: List[StateDef] = field(default_factory=list)

@dataclass
class FunctionDef:
    visibility: str
    name: str
    description: str
    params: List[ParamDef] = field(default_factory=list)
    returns: List[ReturnDef] = field(default_factory=list)

@dataclass
class MemberVar:
    name: str
    description: str

@dataclass
class ClassDef:
    name: str
    description: str
    members: List[MemberVar] = field(default_factory=list)
    functions: List[FunctionDef] = field(default_factory=list)
    state_machines: List[StateMachineDef] = field(default_factory=list)

@dataclass
class SequenceStep:
    """Represents a single step in a sequence diagram.
    
    Attributes:
        depth: Indentation level (0 = top level, increases for nested calls)
        src_obj: Source object/participant
        function: Function name being called
        dst_obj: Destination object/participant
        description: Step description/label
        row: Row number (steps with same row appear at same Y coordinate)
        return_value: Actual return value to display
        param_values: List of actual parameter values to display
        state_changes: Dict mapping object names to new state names after this step
        notes: List of notes to display on lanes during this step
    """
    depth: int
    src_obj: str
    function: str
    dst_obj: str
    description: str
    row: int = 0
    return_value: str = ""
    param_values: List[str] = field(default_factory=list)
    state_changes: dict = field(default_factory=dict)  # Maps lane_name -> state_name
    notes: List[str] = field(default_factory=list)  # Notes to display on lanes

@dataclass
class SequenceDef:
    seq_id: str
    headline: str
    description: str
    steps: List[SequenceStep] = field(default_factory=list)
    
    def get_lanes(self) -> List[str]:
        """Extract unique objects from steps in order of appearance."""
        lanes = []
        for step in self.steps:
            if step.src_obj not in lanes:
                lanes.append(step.src_obj)
            if step.dst_obj not in lanes:
                lanes.append(step.dst_obj)
        return lanes

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
    
    def get_class(self, class_name: str) -> Optional[ClassDef]:
        for c in self.classes:
            if c.name == class_name:
                return c
        return None
    
    def get_state_machine(self, class_name: str, sm_name: str = None) -> Optional[StateMachineDef]:
        """Get a state machine from a class. If sm_name is None, returns the first one."""
        c = self.get_class(class_name)
        if not c:
            return None
        if sm_name is None and c.state_machines:
            return c.state_machines[0]
        for sm in c.state_machines:
            if sm.name == sm_name:
                return sm
        return None