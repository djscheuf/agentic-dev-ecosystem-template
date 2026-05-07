import pytest
import json
import hashlib
from datetime import datetime
from pathlib import Path
from orchestrator.models import (
    generate_saga_id,
    SagaState,
    StateEntry,
    SubSagaEntry,
)
from orchestrator.saga_state import SagaStateManager


class TestSagaIdGeneration:
    """Test saga ID generation with SHA256 hashing."""

    def test_generate_saga_id_happy_path(self):
        """Test that generate_saga_id produces an 8-character hash."""
        saga_name = "test-saga"
        input_path = "/path/to/input.txt"
        
        saga_id = generate_saga_id(saga_name, input_path)
        
        assert isinstance(saga_id, str)
        assert len(saga_id) == 8
        assert all(c in "0123456789abcdef" for c in saga_id)

    def test_generate_saga_id_deterministic_with_timestamp(self):
        """Test that same inputs at different times produce different IDs (timestamp included)."""
        saga_name = "test-saga"
        input_path = "/path/to/input.txt"
        
        saga_id_1 = generate_saga_id(saga_name, input_path)
        saga_id_2 = generate_saga_id(saga_name, input_path)
        
        assert saga_id_1 != saga_id_2

    def test_generate_saga_id_long_saga_name(self):
        """Test that very long saga name (>1000 chars) still produces 8-char hash."""
        saga_name = "x" * 2000
        input_path = "/path/to/input.txt"
        
        saga_id = generate_saga_id(saga_name, input_path)
        
        assert len(saga_id) == 8
        assert all(c in "0123456789abcdef" for c in saga_id)

    def test_generate_saga_id_unicode_characters(self):
        """Test that unicode characters in saga name/input are handled correctly."""
        saga_name = "тест-сага-🚀"
        input_path = "/path/to/输入.txt"
        
        saga_id = generate_saga_id(saga_name, input_path)
        
        assert isinstance(saga_id, str)
        assert len(saga_id) == 8
        assert all(c in "0123456789abcdef" for c in saga_id)

    def test_generate_saga_id_empty_inputs(self):
        """Test that empty saga name or input path are handled gracefully."""
        saga_id_1 = generate_saga_id("", "/path/to/input.txt")
        saga_id_2 = generate_saga_id("test-saga", "")
        saga_id_3 = generate_saga_id("", "")
        
        assert len(saga_id_1) == 8
        assert len(saga_id_2) == 8
        assert len(saga_id_3) == 8


class TestDataModels:
    """Test SagaState, StateEntry, and SubSagaEntry dataclasses."""

    def test_state_entry_creation(self):
        """Test StateEntry dataclass creation."""
        entry = StateEntry(
            node="test-node",
            status="completed",
            started_at="2026-05-05T10:00:00",
            completed_at="2026-05-05T10:01:00",
            exit_code=0,
            session_id="session-123",
        )
        
        assert entry.node == "test-node"
        assert entry.status == "completed"
        assert entry.exit_code == 0

    def test_subsaga_entry_creation(self):
        """Test SubSagaEntry dataclass creation."""
        entry = SubSagaEntry(
            node="child-saga",
            saga_id="abc12345",
            status="in_progress",
            started_at="2026-05-05T10:00:00",
        )
        
        assert entry.node == "child-saga"
        assert entry.saga_id == "abc12345"

    def test_saga_state_creation(self):
        """Test SagaState dataclass creation with all required fields."""
        state = SagaState(
            saga_id="a3f2b9c1",
            saga_definition="/path/to/saga.json",
            original_input="/path/to/input.txt",
            created_at="2026-05-05T10:00:00",
            updated_at="2026-05-05T10:00:00",
            status="starting",
            current_node="start",
            state=[],
            subsagas=[],
        )
        
        assert state.saga_id == "a3f2b9c1"
        assert state.status == "starting"
        assert state.current_node == "start"

    def test_saga_state_to_dict(self):
        """Test SagaState.to_dict() preserves all fields."""
        entry = StateEntry(
            node="test",
            status="completed",
            started_at="2026-05-05T10:00:00",
            completed_at="2026-05-05T10:01:00",
        )
        
        state = SagaState(
            saga_id="a3f2b9c1",
            saga_definition="/path/to/saga.json",
            original_input="/path/to/input.txt",
            created_at="2026-05-05T10:00:00",
            updated_at="2026-05-05T10:00:00",
            status="in_progress",
            current_node="test",
            state=[entry],
            subsagas=[],
        )
        
        state_dict = state.to_dict()
        
        assert state_dict["saga_id"] == "a3f2b9c1"
        assert state_dict["status"] == "in_progress"
        assert len(state_dict["state"]) == 1
        assert state_dict["state"][0]["node"] == "test"

    def test_saga_state_from_dict(self):
        """Test SagaState.from_dict() reconstructs object correctly."""
        data = {
            "saga_id": "a3f2b9c1",
            "saga_definition": "/path/to/saga.json",
            "original_input": "/path/to/input.txt",
            "created_at": "2026-05-05T10:00:00",
            "updated_at": "2026-05-05T10:00:00",
            "status": "in_progress",
            "current_node": "test",
            "state": [
                {
                    "node": "test",
                    "status": "completed",
                    "started_at": "2026-05-05T10:00:00",
                    "completed_at": "2026-05-05T10:01:00",
                    "exit_code": None,
                    "session_id": None,
                }
            ],
            "subsagas": [],
        }
        
        state = SagaState.from_dict(data)
        
        assert state.saga_id == "a3f2b9c1"
        assert state.status == "in_progress"
        assert len(state.state) == 1

    def test_saga_state_round_trip(self):
        """Test round-trip conversion: to_dict() → from_dict()."""
        original = SagaState(
            saga_id="a3f2b9c1",
            saga_definition="/path/to/saga.json",
            original_input="/path/to/input.txt",
            created_at="2026-05-05T10:00:00",
            updated_at="2026-05-05T10:00:00",
            status="in_progress",
            current_node="test",
            state=[
                StateEntry(
                    node="test",
                    status="completed",
                    started_at="2026-05-05T10:00:00",
                    completed_at="2026-05-05T10:01:00",
                )
            ],
            subsagas=[],
        )
        
        state_dict = original.to_dict()
        reconstructed = SagaState.from_dict(state_dict)
        
        assert reconstructed.saga_id == original.saga_id
        assert reconstructed.status == original.status
        assert len(reconstructed.state) == len(original.state)
        assert reconstructed.state[0].node == original.state[0].node


class TestSagaStateManager:
    """Test SagaStateManager initialization and persistence."""

    def test_initialize_creates_directory(self, tmp_path, monkeypatch):
        """Test that initialize() creates .process/saga-<hash>/ directory."""
        monkeypatch.chdir(tmp_path)
        
        saga_id = "a3f2b9c1"
        manager = SagaStateManager(saga_id)
        manager.initialize(
            saga_path="/path/to/saga.json",
            original_input="/path/to/input.txt",
            start_node="start",
        )
        
        saga_dir = tmp_path / ".process" / f"saga-{saga_id}"
        assert saga_dir.exists()
        assert saga_dir.is_dir()

    def test_initialize_creates_saga_json(self, tmp_path, monkeypatch):
        """Test that initialize() creates saga.json with correct initial state."""
        monkeypatch.chdir(tmp_path)
        
        saga_id = "a3f2b9c1"
        manager = SagaStateManager(saga_id)
        manager.initialize(
            saga_path="/path/to/saga.json",
            original_input="/path/to/input.txt",
            start_node="step-1",
        )
        
        saga_file = tmp_path / ".process" / f"saga-{saga_id}" / "saga.json"
        assert saga_file.exists()
        
        data = json.loads(saga_file.read_text())
        assert data["saga_id"] == saga_id
        assert data["status"] == "starting"
        assert data["current_node"] == "step-1"

    def test_initialize_contains_required_fields(self, tmp_path, monkeypatch):
        """Test that saga.json contains all required metadata fields."""
        monkeypatch.chdir(tmp_path)
        
        saga_id = "a3f2b9c1"
        manager = SagaStateManager(saga_id)
        manager.initialize(
            saga_path="/path/to/saga.json",
            original_input="/path/to/input.txt",
            start_node="start",
        )
        
        saga_file = tmp_path / ".process" / f"saga-{saga_id}" / "saga.json"
        data = json.loads(saga_file.read_text())
        
        required_fields = [
            "saga_id",
            "saga_definition",
            "original_input",
            "created_at",
            "updated_at",
            "status",
            "current_node",
            "state",
            "subsagas",
        ]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"

    def test_load_existing_state(self, tmp_path, monkeypatch):
        """Test that load() reads saga.json and reconstructs state."""
        monkeypatch.chdir(tmp_path)
        
        saga_id = "a3f2b9c1"
        manager = SagaStateManager(saga_id)
        manager.initialize(
            saga_path="/path/to/saga.json",
            original_input="/path/to/input.txt",
            start_node="start",
        )
        
        manager2 = SagaStateManager(saga_id)
        loaded_state = manager2.load()
        
        assert loaded_state.saga_id == saga_id
        assert loaded_state.status == "starting"
        assert len(loaded_state.state) == 1

    def test_append_state_entry(self, tmp_path, monkeypatch):
        """Test that append_state_entry() adds new entry to state array."""
        monkeypatch.chdir(tmp_path)
        
        saga_id = "a3f2b9c1"
        manager = SagaStateManager(saga_id)
        manager.initialize(
            saga_path="/path/to/saga.json",
            original_input="/path/to/input.txt",
            start_node="start",
        )
        
        entry = StateEntry(
            node="step-1",
            status="starting",
            started_at="2026-05-05T10:00:00",
        )
        manager.append_state_entry(entry)
        
        assert len(manager.state.state) == 2
        assert manager.state.state[-1].node == "step-1"

    def test_update_last_state_entry(self, tmp_path, monkeypatch):
        """Test that update_last_state_entry() modifies most recent entry."""
        monkeypatch.chdir(tmp_path)
        
        saga_id = "a3f2b9c1"
        manager = SagaStateManager(saga_id)
        manager.initialize(
            saga_path="/path/to/saga.json",
            original_input="/path/to/input.txt",
            start_node="start",
        )
        
        entry = StateEntry(
            node="step-1",
            status="starting",
            started_at="2026-05-05T10:00:00",
        )
        manager.append_state_entry(entry)
        
        manager.update_last_state_entry({
            "status": "completed",
            "completed_at": "2026-05-05T10:01:00",
            "exit_code": 0,
        })
        
        assert manager.state.state[-1].status == "completed"
        assert manager.state.state[-1].exit_code == 0

    def test_count_node_visits(self, tmp_path, monkeypatch):
        """Test that count_node_visits() returns correct visit count."""
        monkeypatch.chdir(tmp_path)
        
        saga_id = "a3f2b9c1"
        manager = SagaStateManager(saga_id)
        manager.initialize(
            saga_path="/path/to/saga.json",
            original_input="/path/to/input.txt",
            start_node="start",
        )
        
        for i in range(3):
            entry = StateEntry(
                node="retry-step",
                status="completed" if i == 2 else "failed",
                started_at="2026-05-05T10:00:00",
                completed_at="2026-05-05T10:01:00",
            )
            manager.append_state_entry(entry)
        
        count = manager.count_node_visits("retry-step")
        assert count == 3

    def test_append_subsaga_entry(self, tmp_path, monkeypatch):
        """Test that append_subsaga_entry() adds sub-saga reference."""
        monkeypatch.chdir(tmp_path)
        
        saga_id = "a3f2b9c1"
        manager = SagaStateManager(saga_id)
        manager.initialize(
            saga_path="/path/to/saga.json",
            original_input="/path/to/input.txt",
            start_node="start",
        )
        
        subsaga = SubSagaEntry(
            node="child-saga",
            saga_id="b7e4c2d9",
            status="in_progress",
            started_at="2026-05-05T10:00:00",
        )
        manager.append_subsaga_entry(subsaga)
        
        assert len(manager.state.subsagas) == 1
        assert manager.state.subsagas[0].saga_id == "b7e4c2d9"

    def test_update_saga_status(self, tmp_path, monkeypatch):
        """Test that update_saga_status() changes saga status."""
        monkeypatch.chdir(tmp_path)
        
        saga_id = "a3f2b9c1"
        manager = SagaStateManager(saga_id)
        manager.initialize(
            saga_path="/path/to/saga.json",
            original_input="/path/to/input.txt",
            start_node="start",
        )
        
        manager.update_saga_status("in_progress", "step-1")
        
        assert manager.state.status == "in_progress"
        assert manager.state.current_node == "step-1"

    def test_atomic_write_creates_temp_file(self, tmp_path, monkeypatch):
        """Test that _write_state() uses atomic write strategy."""
        monkeypatch.chdir(tmp_path)
        
        saga_id = "a3f2b9c1"
        manager = SagaStateManager(saga_id)
        manager.initialize(
            saga_path="/path/to/saga.json",
            original_input="/path/to/input.txt",
            start_node="start",
        )
        
        saga_dir = tmp_path / ".process" / f"saga-{saga_id}"
        saga_file = saga_dir / "saga.json"
        
        assert saga_file.exists()
        assert not (saga_dir / "saga.tmp").exists()


class TestIntegration:
    """Integration tests for full saga lifecycle."""

    def test_full_lifecycle_initialize_to_completion(self, tmp_path, monkeypatch):
        """Test complete saga lifecycle: initialize → append entries → update status → load."""
        monkeypatch.chdir(tmp_path)
        
        saga_id = "a3f2b9c1"
        manager = SagaStateManager(saga_id)
        
        manager.initialize(
            saga_path="/path/to/saga.json",
            original_input="/path/to/input.txt",
            start_node="step-1",
        )
        
        entry1 = StateEntry(
            node="step-1",
            status="starting",
            started_at="2026-05-05T10:00:00",
        )
        manager.append_state_entry(entry1)
        
        manager.update_last_state_entry({
            "status": "completed",
            "completed_at": "2026-05-05T10:01:00",
            "exit_code": 0,
            "session_id": "session-123",
        })
        
        entry2 = StateEntry(
            node="step-2",
            status="starting",
            started_at="2026-05-05T10:01:01",
        )
        manager.append_state_entry(entry2)
        
        manager.update_last_state_entry({
            "status": "completed",
            "completed_at": "2026-05-05T10:02:00",
            "exit_code": 0,
        })
        
        manager.update_saga_status("completed", "end")
        
        manager2 = SagaStateManager(saga_id)
        loaded = manager2.load()
        
        assert loaded.saga_id == saga_id
        assert loaded.status == "completed"
        assert loaded.current_node == "end"
        assert len(loaded.state) == 3
        assert loaded.state[1].session_id == "session-123"

    def test_retry_loop_tracking(self, tmp_path, monkeypatch):
        """Test retry loop with 3 attempts, tracking all visits."""
        monkeypatch.chdir(tmp_path)
        
        saga_id = "retry1234"
        manager = SagaStateManager(saga_id)
        manager.initialize(
            saga_path="/path/to/saga.json",
            original_input="/path/to/input.txt",
            start_node="validate",
        )
        
        for attempt in range(1, 4):
            entry = StateEntry(
                node="validate",
                status="failed" if attempt < 3 else "completed",
                started_at=f"2026-05-05T10:0{attempt}:00",
                completed_at=f"2026-05-05T10:0{attempt}:30",
                exit_code=1 if attempt < 3 else 0,
            )
            manager.append_state_entry(entry)
        
        visit_count = manager.count_node_visits("validate")
        assert visit_count == 3
        
        loaded = manager2 = SagaStateManager(saga_id)
        loaded_state = loaded.load()
        assert loaded_state.count_node_visits("validate") == 3

    def test_multiple_subsagas(self, tmp_path, monkeypatch):
        """Test parent saga tracking multiple child sagas."""
        monkeypatch.chdir(tmp_path)
        
        saga_id = "parent123"
        manager = SagaStateManager(saga_id)
        manager.initialize(
            saga_path="/path/to/saga.json",
            original_input="/path/to/input.txt",
            start_node="start",
        )
        
        for i in range(3):
            subsaga = SubSagaEntry(
                node=f"child-{i}",
                saga_id=f"child{i:04d}",
                status="in_progress",
                started_at="2026-05-05T10:00:00",
            )
            manager.append_subsaga_entry(subsaga)
        
        assert len(manager.state.subsagas) == 3
        
        loaded = SagaStateManager(saga_id)
        loaded_state = loaded.load()
        assert len(loaded_state.subsagas) == 3

    def test_session_id_capture_and_retrieval(self, tmp_path, monkeypatch):
        """Test that session IDs are captured and retrieved correctly."""
        monkeypatch.chdir(tmp_path)
        
        saga_id = "session12"
        manager = SagaStateManager(saga_id)
        manager.initialize(
            saga_path="/path/to/saga.json",
            original_input="/path/to/input.txt",
            start_node="start",
        )
        
        entry = StateEntry(
            node="devin-step",
            status="starting",
            started_at="2026-05-05T10:00:00",
        )
        manager.append_state_entry(entry)
        
        manager.update_last_state_entry({
            "status": "completed",
            "completed_at": "2026-05-05T10:01:00",
            "exit_code": 0,
            "session_id": "devin-session-abc123xyz",
        })
        
        loaded = SagaStateManager(saga_id)
        loaded_state = loaded.load()
        
        devin_entry = [e for e in loaded_state.state if e.node == "devin-step"][0]
        assert devin_entry.session_id == "devin-session-abc123xyz"

    def test_unicode_in_state_preservation(self, tmp_path, monkeypatch):
        """Test that unicode characters in node names/paths are preserved."""
        monkeypatch.chdir(tmp_path)
        
        saga_id = "unicode12"
        manager = SagaStateManager(saga_id)
        manager.initialize(
            saga_path="/path/to/сага.json",
            original_input="/path/to/输入.txt",
            start_node="开始",
        )
        
        entry = StateEntry(
            node="处理-🚀",
            status="completed",
            started_at="2026-05-05T10:00:00",
            completed_at="2026-05-05T10:01:00",
        )
        manager.append_state_entry(entry)
        
        loaded = SagaStateManager(saga_id)
        loaded_state = loaded.load()
        
        assert loaded_state.saga_definition == "/path/to/сага.json"
        assert loaded_state.original_input == "/path/to/输入.txt"
        assert loaded_state.current_node == "开始"
        assert any(e.node == "处理-🚀" for e in loaded_state.state)

    def test_large_state_array(self, tmp_path, monkeypatch):
        """Test handling of large state arrays (many step executions)."""
        monkeypatch.chdir(tmp_path)
        
        saga_id = "large1234"
        manager = SagaStateManager(saga_id)
        manager.initialize(
            saga_path="/path/to/saga.json",
            original_input="/path/to/input.txt",
            start_node="start",
        )
        
        for i in range(100):
            entry = StateEntry(
                node=f"step-{i % 10}",
                status="completed",
                started_at=f"2026-05-05T10:{i:02d}:00",
                completed_at=f"2026-05-05T10:{i:02d}:30",
                exit_code=0,
            )
            manager.append_state_entry(entry)
        
        loaded = SagaStateManager(saga_id)
        loaded_state = loaded.load()
        
        assert len(loaded_state.state) == 101
        assert loaded_state.count_node_visits("step-0") == 10
        assert loaded_state.count_node_visits("step-9") == 10

    def test_state_file_is_valid_json(self, tmp_path, monkeypatch):
        """Test that state file is always valid JSON."""
        monkeypatch.chdir(tmp_path)
        
        saga_id = "json1234"
        manager = SagaStateManager(saga_id)
        manager.initialize(
            saga_path="/path/to/saga.json",
            original_input="/path/to/input.txt",
            start_node="start",
        )
        
        entry = StateEntry(
            node="test",
            status="completed",
            started_at="2026-05-05T10:00:00",
            completed_at="2026-05-05T10:01:00",
        )
        manager.append_state_entry(entry)
        
        saga_file = tmp_path / ".process" / f"saga-{saga_id}" / "saga.json"
        content = saga_file.read_text()
        
        parsed = json.loads(content)
        assert isinstance(parsed, dict)
        assert "saga_id" in parsed
        assert "state" in parsed

    def test_state_file_pretty_printed(self, tmp_path, monkeypatch):
        """Test that state file is pretty-printed JSON (human-readable)."""
        monkeypatch.chdir(tmp_path)
        
        saga_id = "pretty123"
        manager = SagaStateManager(saga_id)
        manager.initialize(
            saga_path="/path/to/saga.json",
            original_input="/path/to/input.txt",
            start_node="start",
        )
        
        saga_file = tmp_path / ".process" / f"saga-{saga_id}" / "saga.json"
        content = saga_file.read_text()
        
        assert "\n" in content
        assert "  " in content
