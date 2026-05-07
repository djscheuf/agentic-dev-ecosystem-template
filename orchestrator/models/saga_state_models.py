import hashlib
from datetime import datetime
from dataclasses import dataclass, asdict, field
from typing import Optional, List, Dict, Any


def generate_saga_id(saga_name: str, input_path: str) -> str:
    """
    Generate unique saga ID from name, input path, and timestamp.
    
    Args:
        saga_name: Name of the saga being executed
        input_path: Path to input file or string representation of input
    
    Returns:
        8-character hash prefix (e.g., 'a3f2b9c1')
    """
    timestamp = datetime.now().isoformat()
    content = f"{saga_name}:{input_path}:{timestamp}"
    hash_full = hashlib.sha256(content.encode()).hexdigest()
    return hash_full[:8]


@dataclass
class StateEntry:
    """Single node execution record."""
    node: str
    status: str
    started_at: str
    completed_at: Optional[str] = None
    exit_code: Optional[int] = None
    session_id: Optional[str] = None


@dataclass
class SubSagaEntry:
    """Sub-saga reference in parent saga."""
    node: str
    saga_id: str
    status: str
    started_at: str


@dataclass
class SagaState:
    """Complete saga execution state."""
    saga_id: str
    saga_definition: str
    original_input: str
    created_at: str
    updated_at: str
    status: str
    current_node: str
    state: List[StateEntry] = field(default_factory=list)
    subsagas: List[SubSagaEntry] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "saga_id": self.saga_id,
            "saga_definition": self.saga_definition,
            "original_input": self.original_input,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "status": self.status,
            "current_node": self.current_node,
            "state": [asdict(entry) for entry in self.state],
            "subsagas": [asdict(entry) for entry in self.subsagas],
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "SagaState":
        """Reconstruct from dictionary."""
        state_entries = [
            StateEntry(**entry) for entry in data.get("state", [])
        ]
        subsaga_entries = [
            SubSagaEntry(**entry) for entry in data.get("subsagas", [])
        ]
        return SagaState(
            saga_id=data["saga_id"],
            saga_definition=data["saga_definition"],
            original_input=data["original_input"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            status=data["status"],
            current_node=data["current_node"],
            state=state_entries,
            subsagas=subsaga_entries,
        )

    def count_node_visits(self, node_name: str) -> int:
        """Count how many times a node has been visited."""
        return sum(1 for entry in self.state if entry.node == node_name)
