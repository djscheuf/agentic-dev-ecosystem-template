import hashlib
import json
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Optional, List, Dict, Any

try:
    from .enrichment import EnrichmentDictionary
except ImportError:
    from enrichment import EnrichmentDictionary


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


class SagaStateManager:
    """Manages saga state persistence with file-based storage."""

    def __init__(self, saga_id: str):
        """
        Initialize state manager for a saga.
        
        Args:
            saga_id: Unique saga identifier
        """
        self.saga_id = saga_id
        self.saga_dir = Path.cwd() / ".process" / f"saga-{saga_id}"
        self.state_file = self.saga_dir / "saga.json"
        self.enrichment_file = self.saga_dir / "enrichment.json"
        self.state: Optional[SagaState] = None

    def initialize(
        self,
        saga_path: str,
        original_input: str,
        start_node: str,
    ) -> None:
        """
        Create initial saga state and directory.
        
        Args:
            saga_path: Absolute path to saga definition
            original_input: Path to input or content string
            start_node: Name of the starting node
        """
        self.saga_dir.mkdir(parents=True, exist_ok=True)
        
        now = datetime.now().isoformat()
        initial_state_entry = StateEntry(
            node="start",
            status="success",
            started_at=now,
            completed_at=now,
            session_id=None,
        )
        
        self.state = SagaState(
            saga_id=self.saga_id,
            saga_definition=saga_path,
            original_input=original_input,
            created_at=now,
            updated_at=now,
            status="starting",
            current_node=start_node,
            state=[initial_state_entry],
            subsagas=[],
        )
        
        self._write_state()

    def load(self) -> SagaState:
        """Load existing saga state from file."""
        if not self.state_file.exists():
            raise FileNotFoundError(f"State file not found: {self.state_file}")
        
        data = json.loads(self.state_file.read_text())
        self.state = SagaState.from_dict(data)
        return self.state

    def append_state_entry(self, entry: StateEntry) -> None:
        """Add new state entry and persist."""
        if self.state is None:
            raise RuntimeError("State not initialized. Call initialize() first.")
        
        self.state.state.append(entry)
        self.state.updated_at = datetime.now().isoformat()
        self._write_state()

    def update_last_state_entry(self, updates: Dict[str, Any]) -> None:
        """Update most recent state entry."""
        if self.state is None or not self.state.state:
            raise RuntimeError("No state entries to update.")
        
        last_entry = self.state.state[-1]
        for key, value in updates.items():
            if hasattr(last_entry, key):
                setattr(last_entry, key, value)
        
        self.state.updated_at = datetime.now().isoformat()
        self._write_state()

    def append_subsaga_entry(self, entry: SubSagaEntry) -> None:
        """Add sub-saga reference and persist."""
        if self.state is None:
            raise RuntimeError("State not initialized. Call initialize() first.")
        
        self.state.subsagas.append(entry)
        self.state.updated_at = datetime.now().isoformat()
        self._write_state()

    def update_saga_status(
        self,
        status: str,
        current_node: Optional[str] = None,
    ) -> None:
        """Update overall saga status."""
        if self.state is None:
            raise RuntimeError("State not initialized. Call initialize() first.")
        
        self.state.status = status
        if current_node is not None:
            self.state.current_node = current_node
        self.state.updated_at = datetime.now().isoformat()
        self._write_state()

    def count_node_visits(self, node_name: str) -> int:
        """Count how many times a node has been visited."""
        if self.state is None:
            raise RuntimeError("State not initialized. Call initialize() first.")
        
        return sum(1 for entry in self.state.state if entry.node == node_name)

    def _write_state(self) -> None:
        """Write state to file using atomic write strategy."""
        if self.state is None:
            raise RuntimeError("No state to write.")
        
        state_dict = self.state.to_dict()
        state_json = json.dumps(state_dict, indent=2)
        
        temp_file = self.state_file.with_suffix(".tmp")
        temp_file.write_text(state_json)
        temp_file.replace(self.state_file)

    def save_enrichment(self, enrichment: EnrichmentDictionary) -> None:
        """
        Save enrichment dictionary to file using atomic write strategy.
        
        Args:
            enrichment: EnrichmentDictionary to persist
        """
        enrichment_dict = enrichment.to_dict()
        enrichment_json = json.dumps(enrichment_dict, indent=2)
        
        enrichment_file = self.saga_dir / "enrichment.json"
        temp_file = enrichment_file.with_suffix(".tmp")
        temp_file.write_text(enrichment_json)
        temp_file.replace(enrichment_file)

    def load_enrichment(self) -> EnrichmentDictionary:
        """
        Load enrichment dictionary from file.
        
        Returns:
            EnrichmentDictionary loaded from persisted state
            
        Raises:
            FileNotFoundError: If enrichment.json does not exist
            json.JSONDecodeError: If enrichment.json is corrupted
        """
        enrichment_file = self.saga_dir / "enrichment.json"
        if not enrichment_file.exists():
            raise FileNotFoundError(f"Enrichment file not found: {enrichment_file}")
        
        data = json.loads(enrichment_file.read_text())
        return EnrichmentDictionary.from_dict(data)
