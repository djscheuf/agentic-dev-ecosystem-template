import pytest
import json
from pathlib import Path


@pytest.fixture
def tmp_steps_dir(tmp_path):
    """Create a temporary steps directory."""
    steps_dir = tmp_path / "steps"
    steps_dir.mkdir()
    return steps_dir


@pytest.fixture
def tmp_sagas_dir(tmp_path):
    """Create a temporary sagas directory."""
    sagas_dir = tmp_path / "sagas"
    sagas_dir.mkdir()
    return sagas_dir


@pytest.fixture
def tmp_log_path(tmp_path):
    """Create a temporary log file path."""
    return tmp_path / "saga_execution.log"


@pytest.fixture
def create_step(tmp_steps_dir):
    """Factory fixture to create a step definition."""
    def _create_step(name, prompt="test prompt", model="gpt-4", verify=None):
        step_dir = tmp_steps_dir / name
        step_dir.mkdir(parents=True, exist_ok=True)
        
        step_def = {
            "prompt": prompt,
            "model": model
        }
        if verify:
            step_def["verify"] = verify
        
        step_file = step_dir / "step.json"
        step_file.write_text(json.dumps(step_def, indent=2))
        
        return step_dir
    
    return _create_step


@pytest.fixture
def create_saga(tmp_sagas_dir):
    """Factory fixture to create a saga definition."""
    def _create_saga(name, saga_dict):
        saga_file = tmp_sagas_dir / f"{name}.json"
        saga_file.write_text(json.dumps(saga_dict, indent=2))
        return saga_file
    
    return _create_saga
