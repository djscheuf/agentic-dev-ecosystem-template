import pytest
import json
from pathlib import Path
from orchestrator.enrichment import substitute_variables
from orchestrator.saga_state import SagaStateManager
from orchestrator.models import SagaDefinition, StepDefinition, EnrichmentDictionary
from orchestrator.saga_executor import SagaExecutor


class TestEnrichmentDictionaryCreation:
    """Test EnrichmentDictionary creation with saga context."""

    def test_enrichment_dictionary_creation_with_saga_context(self):
        """Test that EnrichmentDictionary can be created with saga context."""
        saga_id = "a1b2c3d4"
        state_storage_location = "/path/to/saga-state"
        initial_prompt_path = "/path/to/initial-prompt.md"
        
        enrichment = EnrichmentDictionary(
            saga_id=saga_id,
            state_storage_location=state_storage_location,
            initial_prompt_path=initial_prompt_path
        )
        
        assert enrichment.saga_id == saga_id
        assert enrichment.state_storage_location == state_storage_location
        assert enrichment.initial_prompt_path == initial_prompt_path
        assert enrichment.custom_variables == {}
        assert enrichment.previous_step_output == ""
        assert enrichment.previous_step_error == ""

    def test_enrichment_dictionary_with_custom_variables(self):
        """Test that EnrichmentDictionary can include custom variables."""
        saga_id = "a1b2c3d4"
        state_storage_location = "/path/to/saga-state"
        custom_vars = {
            "code_directory": "/path/to/code",
            "project_name": "my-project"
        }
        
        enrichment = EnrichmentDictionary(
            saga_id=saga_id,
            state_storage_location=state_storage_location,
            initial_prompt_path="/path/to/prompt.md",
            custom_variables=custom_vars
        )
        
        assert enrichment.custom_variables == custom_vars
        assert enrichment.custom_variables["code_directory"] == "/path/to/code"
        assert enrichment.custom_variables["project_name"] == "my-project"

    def test_enrichment_dictionary_to_dict(self):
        """Test that EnrichmentDictionary can be converted to dict for JSON serialization."""
        saga_id = "a1b2c3d4"
        state_storage_location = "/path/to/saga-state"
        custom_vars = {"code_directory": "/path/to/code"}
        
        enrichment = EnrichmentDictionary(
            saga_id=saga_id,
            state_storage_location=state_storage_location,
            initial_prompt_path="/path/to/prompt.md",
            custom_variables=custom_vars
        )
        enrichment.previous_step_output = "test output"
        
        enrichment_dict = enrichment.to_dict()
        
        assert enrichment_dict["saga_id"] == saga_id
        assert enrichment_dict["state_storage_location"] == state_storage_location
        assert enrichment_dict["initial_prompt_path"] == "/path/to/prompt.md"
        assert enrichment_dict["custom_variables"] == custom_vars
        assert enrichment_dict["previous_step_output"] == "test output"
        assert enrichment_dict["previous_step_error"] == ""

    def test_enrichment_dictionary_from_dict(self):
        """Test that EnrichmentDictionary can be reconstructed from dict."""
        data = {
            "saga_id": "a1b2c3d4",
            "state_storage_location": "/path/to/saga-state",
            "initial_prompt_path": "/path/to/prompt.md",
            "custom_variables": {"code_directory": "/path/to/code"},
            "previous_step_output": "test output",
            "previous_step_error": "test error"
        }
        
        enrichment = EnrichmentDictionary.from_dict(data)
        
        assert enrichment.saga_id == "a1b2c3d4"
        assert enrichment.state_storage_location == "/path/to/saga-state"
        assert enrichment.initial_prompt_path == "/path/to/prompt.md"
        assert enrichment.custom_variables == {"code_directory": "/path/to/code"}
        assert enrichment.previous_step_output == "test output"
        assert enrichment.previous_step_error == "test error"

    def test_enrichment_dictionary_update_previous_step_output(self):
        """Test that previous_step_output can be updated."""
        enrichment = EnrichmentDictionary(
            saga_id="a1b2c3d4",
            state_storage_location="/path/to/saga-state",
            initial_prompt_path="/path/to/prompt.md"
        )
        
        assert enrichment.previous_step_output == ""
        
        enrichment.previous_step_output = "new output"
        assert enrichment.previous_step_output == "new output"

    def test_enrichment_dictionary_update_previous_step_error(self):
        """Test that previous_step_error can be updated."""
        enrichment = EnrichmentDictionary(
            saga_id="a1b2c3d4",
            state_storage_location="/path/to/saga-state",
            initial_prompt_path="/path/to/prompt.md"
        )
        
        assert enrichment.previous_step_error == ""
        
        enrichment.previous_step_error = "error message"
        assert enrichment.previous_step_error == "error message"


class TestEnrichmentPersistence:
    """Test enrichment dictionary persistence and loading."""

    def test_save_enrichment_to_file(self, tmp_path):
        """Test that enrichment dictionary can be saved to file."""
        saga_id = "a1b2c3d4"
        state_manager = SagaStateManager(saga_id)
        state_manager.saga_dir = tmp_path / f"saga-{saga_id}"
        state_manager.saga_dir.mkdir(parents=True, exist_ok=True)
        
        enrichment = EnrichmentDictionary(
            saga_id=saga_id,
            state_storage_location=str(state_manager.saga_dir),
            initial_prompt_path="/path/to/prompt.md",
            custom_variables={"code_directory": "/path/to/code"}
        )
        
        state_manager.save_enrichment(enrichment)
        
        enrichment_file = state_manager.saga_dir / "enrichment.json"
        assert enrichment_file.exists()
        
        data = json.loads(enrichment_file.read_text())
        assert data["saga_id"] == saga_id
        assert data["custom_variables"]["code_directory"] == "/path/to/code"

    def test_load_enrichment_from_file(self, tmp_path):
        """Test that enrichment dictionary can be loaded from file."""
        saga_id = "a1b2c3d4"
        state_manager = SagaStateManager(saga_id)
        state_manager.saga_dir = tmp_path / f"saga-{saga_id}"
        state_manager.saga_dir.mkdir(parents=True, exist_ok=True)
        
        enrichment_data = {
            "saga_id": saga_id,
            "state_storage_location": str(state_manager.saga_dir),
            "initial_prompt_path": "/path/to/prompt.md",
            "custom_variables": {"code_directory": "/path/to/code"},
            "previous_step_output": "test output",
            "previous_step_error": ""
        }
        
        enrichment_file = state_manager.saga_dir / "enrichment.json"
        enrichment_file.write_text(json.dumps(enrichment_data, indent=2))
        
        loaded_enrichment = state_manager.load_enrichment()
        
        assert loaded_enrichment.saga_id == saga_id
        assert loaded_enrichment.custom_variables["code_directory"] == "/path/to/code"
        assert loaded_enrichment.previous_step_output == "test output"

    def test_load_enrichment_file_not_found(self, tmp_path):
        """Test that loading non-existent enrichment raises error."""
        saga_id = "a1b2c3d4"
        state_manager = SagaStateManager(saga_id)
        state_manager.saga_dir = tmp_path / f"saga-{saga_id}"
        state_manager.saga_dir.mkdir(parents=True, exist_ok=True)
        
        with pytest.raises(FileNotFoundError):
            state_manager.load_enrichment()

    def test_load_enrichment_corrupted_json(self, tmp_path):
        """Test that loading corrupted enrichment.json raises error."""
        saga_id = "a1b2c3d4"
        state_manager = SagaStateManager(saga_id)
        state_manager.saga_dir = tmp_path / f"saga-{saga_id}"
        state_manager.saga_dir.mkdir(parents=True, exist_ok=True)
        
        enrichment_file = state_manager.saga_dir / "enrichment.json"
        enrichment_file.write_text("{ invalid json }")
        
        with pytest.raises(json.JSONDecodeError):
            state_manager.load_enrichment()

    def test_enrichment_persistence_atomic_write(self, tmp_path):
        """Test that enrichment is written atomically (temp file then replace)."""
        saga_id = "a1b2c3d4"
        state_manager = SagaStateManager(saga_id)
        state_manager.saga_dir = tmp_path / f"saga-{saga_id}"
        state_manager.saga_dir.mkdir(parents=True, exist_ok=True)
        
        enrichment = EnrichmentDictionary(
            saga_id=saga_id,
            state_storage_location=str(state_manager.saga_dir),
            initial_prompt_path="/path/to/prompt.md"
        )
        
        state_manager.save_enrichment(enrichment)
        
        enrichment_file = state_manager.saga_dir / "enrichment.json"
        temp_file = enrichment_file.with_suffix(".tmp")
        
        assert enrichment_file.exists()
        assert not temp_file.exists()


class TestVariableSubstitution:
    """Test variable substitution in prompts."""

    def test_substitute_variables_basic(self):
        """Test basic variable substitution with {{variable}} syntax."""
        enrichment = EnrichmentDictionary(
            saga_id="a1b2c3d4",
            state_storage_location="/path/to/saga-state",
            initial_prompt_path="/path/to/prompt.md"
        )
        
        prompt = "The saga ID is {{saga_id}} and state is at {{state_storage_location}}"
        result = substitute_variables(prompt, enrichment)
        
        assert "a1b2c3d4" in result
        assert "/path/to/saga-state" in result
        assert "{{saga_id}}" not in result

    def test_substitute_variables_with_custom_variables(self):
        """Test variable substitution with custom variables."""
        enrichment = EnrichmentDictionary(
            saga_id="a1b2c3d4",
            state_storage_location="/path/to/saga-state",
            initial_prompt_path="/path/to/prompt.md",
            custom_variables={"code_directory": "/path/to/code", "project_name": "my-project"}
        )
        
        prompt = "Project {{project_name}} is in {{code_directory}}"
        result = substitute_variables(prompt, enrichment)
        
        assert "my-project" in result
        assert "/path/to/code" in result
        assert "{{project_name}}" not in result

    def test_substitute_variables_with_previous_step_output(self):
        """Test variable substitution with previous_step_output."""
        enrichment = EnrichmentDictionary(
            saga_id="a1b2c3d4",
            state_storage_location="/path/to/saga-state",
            initial_prompt_path="/path/to/prompt.md"
        )
        enrichment.previous_step_output = "test output from previous step"
        
        prompt = "Previous step returned: {{previous_step_output}}"
        result = substitute_variables(prompt, enrichment)
        
        assert "test output from previous step" in result
        assert "{{previous_step_output}}" not in result

    def test_substitute_variables_with_previous_step_error(self):
        """Test variable substitution with previous_step_error."""
        enrichment = EnrichmentDictionary(
            saga_id="a1b2c3d4",
            state_storage_location="/path/to/saga-state",
            initial_prompt_path="/path/to/prompt.md"
        )
        enrichment.previous_step_error = "error from previous step"
        
        prompt = "Previous error: {{previous_step_error}}"
        result = substitute_variables(prompt, enrichment)
        
        assert "error from previous step" in result
        assert "{{previous_step_error}}" not in result

    def test_substitute_variables_undefined_variables_remain(self):
        """Test that undefined variables remain as-is."""
        enrichment = EnrichmentDictionary(
            saga_id="a1b2c3d4",
            state_storage_location="/path/to/saga-state",
            initial_prompt_path="/path/to/prompt.md"
        )
        
        prompt = "Known: {{saga_id}}, Unknown: {{undefined_var}}"
        result = substitute_variables(prompt, enrichment)
        
        assert "a1b2c3d4" in result
        assert "{{undefined_var}}" in result

    def test_substitute_variables_empty_prompt(self):
        """Test substitution with empty prompt."""
        enrichment = EnrichmentDictionary(
            saga_id="a1b2c3d4",
            state_storage_location="/path/to/saga-state",
            initial_prompt_path="/path/to/prompt.md"
        )
        
        result = substitute_variables("", enrichment)
        assert result == ""

    def test_substitute_variables_no_variables_in_prompt(self):
        """Test substitution when prompt has no variables."""
        enrichment = EnrichmentDictionary(
            saga_id="a1b2c3d4",
            state_storage_location="/path/to/saga-state",
            initial_prompt_path="/path/to/prompt.md"
        )
        
        prompt = "This is a simple prompt with no variables"
        result = substitute_variables(prompt, enrichment)
        assert result == prompt

    def test_substitute_variables_special_characters_in_values(self):
        """Test substitution with special characters in variable values."""
        enrichment = EnrichmentDictionary(
            saga_id="a1b2c3d4",
            state_storage_location="/path/to/saga-state",
            initial_prompt_path="/path/to/prompt.md",
            custom_variables={"path": "/home/user/my-project/src"}
        )
        
        prompt = "Code is at {{path}}"
        result = substitute_variables(prompt, enrichment)
        
        assert "/home/user/my-project/src" in result

    def test_substitute_variables_multiple_occurrences(self):
        """Test substitution when same variable appears multiple times."""
        enrichment = EnrichmentDictionary(
            saga_id="a1b2c3d4",
            state_storage_location="/path/to/saga-state",
            initial_prompt_path="/path/to/prompt.md"
        )
        
        prompt = "Saga {{saga_id}} is running. Saga {{saga_id}} status is active."
        result = substitute_variables(prompt, enrichment)
        
        assert result.count("a1b2c3d4") == 2
        assert "{{saga_id}}" not in result


class TestSagaDefinitionEnrichment:
    """Test enrichment field in saga definitions."""

    def test_saga_definition_with_enrichment_field(self):
        """Test that SagaDefinition can include enrichment configuration."""
        saga_dict = {
            "name": "test-saga",
            "start": "step1",
            "nodes": {
                "step1": {"type": "step", "reference": "step1"}
            },
            "connections": [
                {"node": "step1", "then": "end"}
            ],
            "enrichment": {
                "code_directory": "/path/to/code",
                "project_name": "my-project"
            }
        }
        
        saga = SagaDefinition.from_dict(saga_dict)
        
        assert saga.enrichment == saga_dict["enrichment"]
        assert saga.enrichment["code_directory"] == "/path/to/code"
        assert saga.enrichment["project_name"] == "my-project"

    def test_saga_definition_without_enrichment_field(self):
        """Test that SagaDefinition works without enrichment field."""
        saga_dict = {
            "name": "test-saga",
            "start": "step1",
            "nodes": {
                "step1": {"type": "step", "reference": "step1"}
            },
            "connections": [
                {"node": "step1", "then": "end"}
            ]
        }
        
        saga = SagaDefinition.from_dict(saga_dict)
        
        assert saga.enrichment == {}

    def test_saga_definition_enrichment_empty_dict(self):
        """Test that SagaDefinition handles empty enrichment dict."""
        saga_dict = {
            "name": "test-saga",
            "start": "step1",
            "nodes": {
                "step1": {"type": "step", "reference": "step1"}
            },
            "connections": [
                {"node": "step1", "then": "end"}
            ],
            "enrichment": {}
        }
        
        saga = SagaDefinition.from_dict(saga_dict)
        
        assert saga.enrichment == {}


class TestSagaExecutorEnrichment:
    """Test enrichment initialization in SagaExecutor."""

    def test_saga_executor_initializes_enrichment_on_start(self, tmp_path):
        """Test that SagaExecutor initializes enrichment during saga initialization."""
        saga_dict = {
            "name": "test-saga",
            "start": "step1",
            "nodes": {
                "step1": {"type": "step", "reference": "step1"}
            },
            "connections": [
                {"node": "step1", "then": "end"}
            ],
            "enrichment": {
                "code_directory": "/path/to/code",
                "project_name": "my-project"
            }
        }
        
        saga = SagaDefinition.from_dict(saga_dict)
        steps_dir = tmp_path / "steps"
        sagas_dir = tmp_path / "sagas"
        log_path = tmp_path / "saga.log"
        
        saga_path = str(tmp_path / "test-saga.json")
        original_input = "test input"
        
        executor = SagaExecutor(
            saga,
            steps_dir,
            sagas_dir,
            log_path,
            depth=0,
            saga_path=saga_path,
            original_input=original_input
        )
        
        assert executor.state_manager is not None
        assert executor.state_manager.state is not None
        
        enrichment_file = executor.state_manager.saga_dir / "enrichment.json"
        assert enrichment_file.exists()
        
        enrichment = executor.state_manager.load_enrichment()
        assert enrichment.saga_id == executor.state_manager.saga_id
        assert enrichment.custom_variables["code_directory"] == "/path/to/code"
        assert enrichment.custom_variables["project_name"] == "my-project"

    def test_saga_executor_enrichment_includes_saga_context(self, tmp_path):
        """Test that enrichment includes saga ID and state location."""
        saga_dict = {
            "name": "test-saga",
            "start": "step1",
            "nodes": {
                "step1": {"type": "step", "reference": "step1"}
            },
            "connections": [
                {"node": "step1", "then": "end"}
            ]
        }
        
        saga = SagaDefinition.from_dict(saga_dict)
        steps_dir = tmp_path / "steps"
        sagas_dir = tmp_path / "sagas"
        log_path = tmp_path / "saga.log"
        
        saga_path = str(tmp_path / "test-saga.json")
        original_input = "test input"
        
        executor = SagaExecutor(
            saga,
            steps_dir,
            sagas_dir,
            log_path,
            depth=0,
            saga_path=saga_path,
            original_input=original_input
        )
        
        enrichment = executor.state_manager.load_enrichment()
        
        assert enrichment.saga_id == executor.state_manager.saga_id
        assert str(executor.state_manager.saga_dir) == enrichment.state_storage_location
        assert enrichment.initial_prompt_path == original_input


class TestStepPromptEnrichment:
    """Test enrichment of step prompts before execution."""

    def test_step_definition_with_enrichment_variables(self, tmp_path):
        """Test that step prompts can include enrichment variables."""
        step_dir = tmp_path / "test-step"
        step_dir.mkdir()
        
        prompt_content = "Process {{code_directory}} for project {{project_name}}. Saga: {{saga_id}}"
        prompt_file = step_dir / "prompt.md"
        prompt_file.write_text(prompt_content)
        
        step_def_data = {
            "prompt": "prompt.md",
            "model": "gpt-4"
        }
        
        step_def = StepDefinition(step_def_data, step_dir)
        prompt = step_def.get_prompt_content()
        
        enrichment = EnrichmentDictionary(
            saga_id="a1b2c3d4",
            state_storage_location="/path/to/saga-state",
            initial_prompt_path="/path/to/prompt.md",
            custom_variables={"code_directory": "/path/to/code", "project_name": "my-project"}
        )
        
        enriched_prompt = substitute_variables(prompt, enrichment)
        
        assert "/path/to/code" in enriched_prompt
        assert "my-project" in enriched_prompt
        assert "a1b2c3d4" in enriched_prompt
        assert "{{" not in enriched_prompt

    def test_step_prompt_with_previous_step_output(self, tmp_path):
        """Test that step prompts can reference previous step output."""
        step_dir = tmp_path / "test-step"
        step_dir.mkdir()
        
        prompt_content = "Based on previous result: {{previous_step_output}}"
        prompt_file = step_dir / "prompt.md"
        prompt_file.write_text(prompt_content)
        
        step_def_data = {
            "prompt": "prompt.md",
            "model": "gpt-4"
        }
        
        step_def = StepDefinition(step_def_data, step_dir)
        prompt = step_def.get_prompt_content()
        
        enrichment = EnrichmentDictionary(
            saga_id="a1b2c3d4",
            state_storage_location="/path/to/saga-state",
            initial_prompt_path="/path/to/prompt.md"
        )
        enrichment.previous_step_output = "The code analysis found 3 issues"
        
        enriched_prompt = substitute_variables(prompt, enrichment)
        
        assert "The code analysis found 3 issues" in enriched_prompt
        assert "{{previous_step_output}}" not in enriched_prompt
