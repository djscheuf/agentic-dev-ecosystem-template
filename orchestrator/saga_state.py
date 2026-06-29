import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

try:
    from .models import SagaState, StateEntry, SubSagaEntry, generate_saga_id, EnrichmentDictionary
except ImportError:
    from models import SagaState, StateEntry, SubSagaEntry, generate_saga_id, EnrichmentDictionary


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
