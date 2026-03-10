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
class ClassRelationship:
    """A relationship between two classes in a class diagram.
    
    Arrow types (solid line = structural):
      --    Association
      -->   Directed Association (left to right)
      <--   Directed Association (right to left)
      <-->  Bidirectional Association
      --▷   Generalization / Inheritance (left extends right)
      ◁--   Generalization / Inheritance (right extends left)
      --◆   Composition (right owns left, strong)
      ◆--   Composition (left owns right, strong)
      --◇   Aggregation (right contains left, weak)
      ◇--   Aggregation (left contains right, weak)
    
    Arrow types (dashed line = behavioral):
      ..>   Dependency (left depends on right)
      <..   Dependency (right depends on left)
      ..▷   Realization / Implementation (left implements right)
      ◁..   Realization / Implementation (right implements left)
    """
    source: str
    target: str
    arrow: str
    src_mult: str = ""
    tgt_mult: str = ""
    label: str = ""

@dataclass
class ClassDiagramDef:
    diagram_id: str
    description: str
    relationships: List[ClassRelationship] = field(default_factory=list)

@dataclass
class NoteDef:
    """Represents a note in a sequence diagram.
    
    Attributes:
        note_type: Type of note - "Info", "Warning", or "Error"
        content: Text content of the note (displayed on hover)
    """
    note_type: str  # "Info", "Warning", or "Error"
    content: str

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
        lane_notes: Dict mapping lane_name -> NoteDef for lane notes
        function_note: Optional NoteDef for a note on the function call
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
    lane_notes: dict = field(default_factory=dict)  # Maps lane_name -> NoteDef
    function_note: Optional['NoteDef'] = None

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
    class_diagrams: List[ClassDiagramDef] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def get_sequence(self, seq_id: str) -> Optional[SequenceDef]:
        for s in self.sequences:
            if s.seq_id == seq_id:
                return s
        return None

    def get_function(self, class_name: str, func_name: str) -> Optional[FunctionDef]:
        for c in self.classes:
            if c.name == class_name:
                for f in c.functions:
                    # Extract base function name from f.name (handles "FuncName() : RetVal" format)
                    base_name = f.name.split('(')[0] if '(' in f.name else f.name
                    if base_name == func_name or f.name == func_name:
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

    def get_class_diagram(self, diagram_id: str) -> Optional[ClassDiagramDef]:
        for d in self.class_diagrams:
            if d.diagram_id == diagram_id:
                return d
        return None