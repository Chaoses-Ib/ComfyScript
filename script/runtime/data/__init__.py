from dataclasses import dataclass

@dataclass
class NodeOutput:
    id: str
    slot: int

__all__ = [
    'NodeOutput',
]