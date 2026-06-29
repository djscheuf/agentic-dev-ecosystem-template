import pytest
import json
from pathlib import Path
from orchestrator.models import SagaDefinition
from orchestrator.saga_validator import SagaValidator, validate_saga


class TestSagaValidatorHappyPath:
    """Happy path tests for saga_validator.py (V-H-*)."""
    
    def test_v_h_01_valid_simple_saga(self, tmp_steps_dir, tmp_sagas_dir, create_step):
        """V-H-01: Valid simple saga (single step → end)."""
        create_step("test")
        
        data = {
            "name": "simple-saga",
            "start": "step1",
            "nodes": {
                "step1": {"type": "step", "reference": "test"}
            },
            "connections": [
                {"node": "step1", "then": "end"}
            ]
        }
        
        saga = SagaDefinition.from_dict(data)
        is_valid, errors, warnings = validate_saga(saga, tmp_steps_dir, tmp_sagas_dir)
        
        assert is_valid
        assert len(errors) == 0
    
    def test_v_h_02_valid_branching_saga(self, tmp_steps_dir, tmp_sagas_dir, create_step):
        """V-H-02: Valid branching saga (pass/fail routes)."""
        create_step("test1")
        create_step("test2")
        create_step("test3")
        
        data = {
            "name": "branching-saga",
            "start": "step1",
            "nodes": {
                "step1": {"type": "step", "reference": "test1"},
                "step2": {"type": "step", "reference": "test2"},
                "step3": {"type": "step", "reference": "test3"}
            },
            "connections": [
                {"node": "step1", "pass": "step2", "fail": "step3"},
                {"node": "step2", "then": "end"},
                {"node": "step3", "then": "end"}
            ]
        }
        
        saga = SagaDefinition.from_dict(data)
        is_valid, errors, warnings = validate_saga(saga, tmp_steps_dir, tmp_sagas_dir)
        
        assert is_valid
        assert len(errors) == 0
    
    def test_v_h_03_valid_retry_saga(self, tmp_steps_dir, tmp_sagas_dir, create_step):
        """V-H-03: Valid retry saga (self-referencing with limit)."""
        create_step("test")
        
        data = {
            "name": "retry-saga",
            "start": "step1",
            "nodes": {
                "step1": {"type": "step", "reference": "test"}
            },
            "connections": [
                {
                    "node": "step1",
                    "pass": "end",
                    "fail": {"target": "step1", "traversal_limit": 3}
                }
            ]
        }
        
        saga = SagaDefinition.from_dict(data)
        is_valid, errors, warnings = validate_saga(saga, tmp_steps_dir, tmp_sagas_dir)
        
        assert is_valid
        assert len(errors) == 0
    
    def test_v_h_04_valid_composite_saga(self, tmp_steps_dir, tmp_sagas_dir, create_step, create_saga):
        """V-H-04: Valid composite saga (steps + sub-sagas)."""
        create_step("test1")
        create_step("test2")
        
        subsaga_data = {
            "name": "sub-saga",
            "start": "substep",
            "nodes": {
                "substep": {"type": "step", "reference": "test2"}
            },
            "connections": [
                {"node": "substep", "then": "end"}
            ]
        }
        create_saga("sub", subsaga_data)
        
        data = {
            "name": "composite-saga",
            "start": "step1",
            "nodes": {
                "step1": {"type": "step", "reference": "test1"},
                "subsaga1": {"type": "saga", "reference": "sub.json"}
            },
            "connections": [
                {"node": "step1", "then": "subsaga1"},
                {"node": "subsaga1", "then": "end"}
            ]
        }
        
        saga = SagaDefinition.from_dict(data)
        is_valid, errors, warnings = validate_saga(saga, tmp_steps_dir, tmp_sagas_dir)
        
        assert is_valid
        assert len(errors) == 0
    
    def test_v_h_05_circular_reference_produces_warning(self, tmp_steps_dir, tmp_sagas_dir, create_saga):
        """V-H-05: Circular reference produces warning (not error)."""
        saga_a_data = {
            "name": "saga-a",
            "start": "saga_b_node",
            "nodes": {
                "saga_b_node": {"type": "saga", "reference": "saga_b.json"}
            },
            "connections": [
                {"node": "saga_b_node", "then": "end"}
            ]
        }
        create_saga("saga_a", saga_a_data)
        
        saga_b_data = {
            "name": "saga-b",
            "start": "saga_a_node",
            "nodes": {
                "saga_a_node": {"type": "saga", "reference": "saga_a.json"}
            },
            "connections": [
                {"node": "saga_a_node", "then": "end"}
            ]
        }
        create_saga("saga_b", saga_b_data)
        
        saga = SagaDefinition.from_dict(saga_a_data)
        validator = SagaValidator(saga, tmp_steps_dir, tmp_sagas_dir)
        is_valid = validator.validate()
        
        assert len(validator.get_warnings()) > 0
        assert any("Circular reference" in w for w in validator.get_warnings())


class TestSagaValidatorEdgeCases:
    """Edge case tests for saga_validator.py (V-E-*)."""
    
    def test_v_e_01_empty_saga_no_nodes(self, tmp_steps_dir, tmp_sagas_dir):
        """V-E-01: Empty saga (no nodes defined)."""
        data = {
            "name": "empty-saga",
            "start": "step1",
            "nodes": {},
            "connections": []
        }
        
        saga = SagaDefinition.from_dict(data)
        is_valid, errors, warnings = validate_saga(saga, tmp_steps_dir, tmp_sagas_dir)
        
        assert not is_valid
        assert any("Start node 'step1' is not defined" in err for err in errors)
    
    def test_v_e_02_single_node_saga_start_to_end(self, tmp_steps_dir, tmp_sagas_dir, create_step):
        """V-E-02: Single node saga (start → end)."""
        create_step("test")
        
        data = {
            "name": "single-node-saga",
            "start": "step1",
            "nodes": {
                "step1": {"type": "step", "reference": "test"}
            },
            "connections": [
                {"node": "step1", "then": "end"}
            ]
        }
        
        saga = SagaDefinition.from_dict(data)
        is_valid, errors, warnings = validate_saga(saga, tmp_steps_dir, tmp_sagas_dir)
        
        assert is_valid
        assert len(errors) == 0
    
    def test_v_e_03_max_recursion_depth_at_boundary(self, tmp_steps_dir, tmp_sagas_dir, create_step):
        """V-E-03: Max recursion depth at boundary (exactly 50)."""
        create_step("test")
        
        data = {
            "name": "test-saga",
            "start": "step1",
            "nodes": {
                "step1": {"type": "step", "reference": "test"}
            },
            "connections": [
                {"node": "step1", "then": "end"}
            ],
            "max_recursion_depth": 50
        }
        
        saga = SagaDefinition.from_dict(data)
        validator = SagaValidator(saga, tmp_steps_dir, tmp_sagas_dir, recursion_depth=49)
        
        is_valid = validator.validate()
        
        assert is_valid
        assert len(validator.get_errors()) == 0
    
    def test_v_e_04_deeply_nested_subsagas(self, tmp_steps_dir, tmp_sagas_dir, create_step, create_saga):
        """V-E-04: Deeply nested sub-sagas (multiple levels)."""
        create_step("test")
        
        level3_data = {
            "name": "level3-saga",
            "start": "step1",
            "nodes": {
                "step1": {"type": "step", "reference": "test"}
            },
            "connections": [
                {"node": "step1", "then": "end"}
            ]
        }
        create_saga("level3", level3_data)
        
        level2_data = {
            "name": "level2-saga",
            "start": "subsaga",
            "nodes": {
                "subsaga": {"type": "saga", "reference": "level3.json"}
            },
            "connections": [
                {"node": "subsaga", "then": "end"}
            ]
        }
        create_saga("level2", level2_data)
        
        level1_data = {
            "name": "level1-saga",
            "start": "subsaga",
            "nodes": {
                "subsaga": {"type": "saga", "reference": "level2.json"}
            },
            "connections": [
                {"node": "subsaga", "then": "end"}
            ]
        }
        
        saga = SagaDefinition.from_dict(level1_data)
        is_valid, errors, warnings = validate_saga(saga, tmp_steps_dir, tmp_sagas_dir)
        
        assert is_valid
        assert len(errors) == 0
    
    def test_v_e_05_multiple_paths_to_end(self, tmp_steps_dir, tmp_sagas_dir, create_step):
        """V-E-05: Multiple paths to end (complex convergence)."""
        create_step("test1")
        create_step("test2")
        create_step("test3")
        create_step("test4")
        
        data = {
            "name": "convergent-saga",
            "start": "step1",
            "nodes": {
                "step1": {"type": "step", "reference": "test1"},
                "step2": {"type": "step", "reference": "test2"},
                "step3": {"type": "step", "reference": "test3"},
                "step4": {"type": "step", "reference": "test4"}
            },
            "connections": [
                {"node": "step1", "pass": "step2", "fail": "step3"},
                {"node": "step2", "then": "step4"},
                {"node": "step3", "then": "step4"},
                {"node": "step4", "then": "end"}
            ]
        }
        
        saga = SagaDefinition.from_dict(data)
        is_valid, errors, warnings = validate_saga(saga, tmp_steps_dir, tmp_sagas_dir)
        
        assert is_valid
        assert len(errors) == 0


class TestSagaValidatorErrorHandling:
    """Critical error handling tests for saga_validator.py (V-ER-*)."""
    
    def test_v_er_01_missing_start_property(self, tmp_steps_dir, tmp_sagas_dir):
        """V-ER-01: Missing 'start' property."""
        data = {
            "name": "test-saga",
            "nodes": {
                "step1": {"type": "step", "reference": "test"}
            },
            "connections": []
        }
        
        with pytest.raises(ValueError, match="must include 'start'"):
            saga = SagaDefinition.from_dict(data)
    
    def test_v_er_02_start_is_end(self, tmp_steps_dir, tmp_sagas_dir):
        """V-ER-02: Start is 'end' (invalid)."""
        data = {
            "name": "test-saga",
            "start": "end",
            "nodes": {},
            "connections": []
        }
        
        saga = SagaDefinition.from_dict(data)
        validator = SagaValidator(saga, tmp_steps_dir, tmp_sagas_dir)
        
        is_valid = validator.validate()
        assert not is_valid
        assert any("Start cannot be 'end'" in err for err in validator.get_errors())
    
    def test_v_er_03_start_node_not_defined(self, tmp_steps_dir, tmp_sagas_dir):
        """V-ER-03: Start node not defined in nodes section."""
        data = {
            "name": "test-saga",
            "start": "nonexistent",
            "nodes": {
                "step1": {"type": "step", "reference": "test"}
            },
            "connections": []
        }
        
        saga = SagaDefinition.from_dict(data)
        validator = SagaValidator(saga, tmp_steps_dir, tmp_sagas_dir)
        
        is_valid = validator.validate()
        assert not is_valid
        assert any("Start node 'nonexistent' is not defined" in err for err in validator.get_errors())
    
    def test_v_er_04_step_node_references_nonexistent_folder(self, tmp_steps_dir, tmp_sagas_dir):
        """V-ER-04: Step node references non-existent step folder."""
        data = {
            "name": "test-saga",
            "start": "step1",
            "nodes": {
                "step1": {"type": "step", "reference": "nonexistent"}
            },
            "connections": [
                {"node": "step1", "then": "end"}
            ]
        }
        
        saga = SagaDefinition.from_dict(data)
        validator = SagaValidator(saga, tmp_steps_dir, tmp_sagas_dir)
        
        is_valid = validator.validate()
        assert not is_valid
        assert any("does not exist" in err and "nonexistent" in err for err in validator.get_errors())
    
    def test_v_er_05_saga_node_references_nonexistent_file(self, tmp_steps_dir, tmp_sagas_dir):
        """V-ER-05: Saga node references non-existent saga file."""
        data = {
            "name": "test-saga",
            "start": "subsaga1",
            "nodes": {
                "subsaga1": {"type": "saga", "reference": "nonexistent.json"}
            },
            "connections": [
                {"node": "subsaga1", "then": "end"}
            ]
        }
        
        saga = SagaDefinition.from_dict(data)
        validator = SagaValidator(saga, tmp_steps_dir, tmp_sagas_dir)
        
        is_valid = validator.validate()
        assert not is_valid
        assert any("does not exist" in err and "nonexistent.json" in err for err in validator.get_errors())
    
    def test_v_er_06_dead_end_node(self, tmp_steps_dir, tmp_sagas_dir, create_step):
        """V-ER-06: Dead-end node (no outgoing connections)."""
        create_step("test")
        
        data = {
            "name": "test-saga",
            "start": "step1",
            "nodes": {
                "step1": {"type": "step", "reference": "test"}
            },
            "connections": []
        }
        
        saga = SagaDefinition.from_dict(data)
        validator = SagaValidator(saga, tmp_steps_dir, tmp_sagas_dir)
        
        is_valid = validator.validate()
        assert not is_valid
        assert any("Dead-end node 'step1'" in err for err in validator.get_errors())
    
    def test_v_er_07_unreachable_end(self, tmp_steps_dir, tmp_sagas_dir, create_step):
        """V-ER-07: Unreachable end (graph not closed)."""
        create_step("test1")
        create_step("test2")
        
        data = {
            "name": "test-saga",
            "start": "step1",
            "nodes": {
                "step1": {"type": "step", "reference": "test1"},
                "step2": {"type": "step", "reference": "test2"}
            },
            "connections": [
                {"node": "step1", "then": "step2"}
            ]
        }
        
        saga = SagaDefinition.from_dict(data)
        validator = SagaValidator(saga, tmp_steps_dir, tmp_sagas_dir)
        
        is_valid = validator.validate()
        assert not is_valid
        assert any("'end' is not reachable" in err for err in validator.get_errors())
    
    def test_v_er_08_connection_references_undefined_node(self, tmp_steps_dir, tmp_sagas_dir, create_step):
        """V-ER-08: Connection references undefined node."""
        create_step("test")
        
        data = {
            "name": "test-saga",
            "start": "step1",
            "nodes": {
                "step1": {"type": "step", "reference": "test"}
            },
            "connections": [
                {"node": "nonexistent", "then": "end"}
            ]
        }
        
        saga = SagaDefinition.from_dict(data)
        validator = SagaValidator(saga, tmp_steps_dir, tmp_sagas_dir)
        
        is_valid = validator.validate()
        assert not is_valid
        assert any("Connection references undefined node 'nonexistent'" in err for err in validator.get_errors())
    
    def test_v_er_09_branching_without_fail(self, tmp_steps_dir, tmp_sagas_dir):
        """V-ER-09: Branching without 'fail'."""
        data = {
            "name": "test-saga",
            "start": "step1",
            "nodes": {
                "step1": {"type": "step", "reference": "test"}
            },
            "connections": [
                {"node": "step1", "pass": "end"}
            ]
        }
        
        with pytest.raises(ValueError, match="both 'pass' and 'fail' are required"):
            SagaDefinition.from_dict(data)
    
    def test_v_er_10_branching_without_pass(self, tmp_steps_dir, tmp_sagas_dir):
        """V-ER-10: Branching without 'pass'."""
        data = {
            "name": "test-saga",
            "start": "step1",
            "nodes": {
                "step1": {"type": "step", "reference": "test"}
            },
            "connections": [
                {"node": "step1", "fail": "end"}
            ]
        }
        
        with pytest.raises(ValueError, match="both 'pass' and 'fail' are required"):
            SagaDefinition.from_dict(data)
    
    def test_v_er_11_exceeds_max_recursion_depth(self, tmp_steps_dir, tmp_sagas_dir):
        """V-ER-11: Exceeds max recursion depth (> 50 levels)."""
        data = {
            "name": "test-saga",
            "start": "step1",
            "nodes": {
                "step1": {"type": "step", "reference": "test"}
            },
            "connections": [],
            "max_recursion_depth": 5
        }
        
        saga = SagaDefinition.from_dict(data)
        validator = SagaValidator(saga, tmp_steps_dir, tmp_sagas_dir, recursion_depth=10)
        
        is_valid = validator.validate()
        assert not is_valid
        assert any("Recursion depth 10 exceeds maximum 5" in err for err in validator.get_errors())
    
    def test_v_er_12_invalid_node_type(self, tmp_steps_dir, tmp_sagas_dir):
        """V-ER-12: Invalid node type (not 'step' or 'saga')."""
        data = {
            "name": "test-saga",
            "start": "step1",
            "nodes": {
                "step1": {"type": "invalid", "reference": "test"}
            },
            "connections": []
        }
        
        with pytest.raises(ValueError, match="invalid type 'invalid'"):
            SagaDefinition.from_dict(data)
    
    def test_v_er_13_malformed_subsaga_json(self, tmp_steps_dir, tmp_sagas_dir):
        """V-ER-13: Malformed sub-saga JSON file."""
        bad_saga_file = tmp_sagas_dir / "bad.json"
        bad_saga_file.write_text("{ invalid json")
        
        data = {
            "name": "test-saga",
            "start": "subsaga1",
            "nodes": {
                "subsaga1": {"type": "saga", "reference": "bad.json"}
            },
            "connections": [
                {"node": "subsaga1", "then": "end"}
            ]
        }
        
        saga = SagaDefinition.from_dict(data)
        validator = SagaValidator(saga, tmp_steps_dir, tmp_sagas_dir)
        
        is_valid = validator.validate()
        assert not is_valid
        assert any("Failed to load sub-saga" in err for err in validator.get_errors())
    
    def test_v_er_14_subsaga_validation_failure_propagates(self, tmp_steps_dir, tmp_sagas_dir):
        """V-ER-14: Sub-saga validation failure propagates."""
        subsaga_data = {
            "name": "sub-saga",
            "start": "end",
            "nodes": {},
            "connections": []
        }
        subsaga_file = tmp_sagas_dir / "sub.json"
        subsaga_file.write_text(json.dumps(subsaga_data))
        
        data = {
            "name": "test-saga",
            "start": "subsaga1",
            "nodes": {
                "subsaga1": {"type": "saga", "reference": "sub.json"}
            },
            "connections": [
                {"node": "subsaga1", "then": "end"}
            ]
        }
        
        saga = SagaDefinition.from_dict(data)
        validator = SagaValidator(saga, tmp_steps_dir, tmp_sagas_dir)
        
        is_valid = validator.validate()
        assert not is_valid
        assert any("In sub-saga 'subsaga1'" in err and "Start cannot be 'end'" in err for err in validator.get_errors())


class TestAgentConfigValidationHappyPath:
    """Happy path tests for agent_config validation (AV-H-*)."""
    
    def test_av_h_01_step_with_agent_config_file_exists(self, tmp_steps_dir, tmp_sagas_dir, create_step):
        """AV-H-01: Validation passes when step has agent_config and file exists."""
        step_dir = create_step("test")
        config_file = step_dir / "agent-config.json"
        config_file.write_text('{"permissions": {"allow": []}}')
        
        step_file = step_dir / "step.json"
        step_data = json.loads(step_file.read_text())
        step_data["agent_config"] = "agent-config.json"
        step_file.write_text(json.dumps(step_data))
        
        data = {
            "name": "saga-with-config",
            "start": "step1",
            "nodes": {
                "step1": {"type": "step", "reference": "test"}
            },
            "connections": [
                {"node": "step1", "then": "end"}
            ]
        }
        
        saga = SagaDefinition.from_dict(data)
        is_valid, errors, warnings = validate_saga(saga, tmp_steps_dir, tmp_sagas_dir)
        
        assert is_valid
        assert len(errors) == 0
    
    def test_av_h_02_step_without_agent_config_uses_global(self, tmp_steps_dir, tmp_sagas_dir, create_step):
        """AV-H-02: Validation passes when step has no agent_config (uses global)."""
        create_step("test")
        
        global_config = tmp_steps_dir.parent / ".devin" / "agent-config.json"
        global_config.parent.mkdir(parents=True, exist_ok=True)
        global_config.write_text('{"permissions": {"allow": []}}')
        
        data = {
            "name": "saga-no-config",
            "start": "step1",
            "nodes": {
                "step1": {"type": "step", "reference": "test"}
            },
            "connections": [
                {"node": "step1", "then": "end"}
            ]
        }
        
        saga = SagaDefinition.from_dict(data)
        is_valid, errors, warnings = validate_saga(saga, tmp_steps_dir, tmp_sagas_dir)
        
        assert is_valid
        assert len(errors) == 0
    
    def test_av_h_03_absolute_agent_config_path(self, tmp_steps_dir, tmp_sagas_dir, create_step, tmp_path):
        """AV-H-03: Validation passes with absolute agent_config path."""
        step_dir = create_step("test")
        absolute_config = tmp_path / "absolute-config.json"
        absolute_config.write_text('{"permissions": {"allow": []}}')
        
        step_file = step_dir / "step.json"
        step_data = json.loads(step_file.read_text())
        step_data["agent_config"] = str(absolute_config)
        step_file.write_text(json.dumps(step_data))
        
        data = {
            "name": "saga-absolute-config",
            "start": "step1",
            "nodes": {
                "step1": {"type": "step", "reference": "test"}
            },
            "connections": [
                {"node": "step1", "then": "end"}
            ]
        }
        
        saga = SagaDefinition.from_dict(data)
        is_valid, errors, warnings = validate_saga(saga, tmp_steps_dir, tmp_sagas_dir)
        
        assert is_valid
        assert len(errors) == 0


class TestAgentConfigValidationEdgeCases:
    """Edge case tests for agent_config validation (AV-E-*)."""
    
    def test_av_e_01_agent_config_file_missing(self, tmp_steps_dir, tmp_sagas_dir, create_step):
        """AV-E-01: Validation fails when agent_config file doesn't exist."""
        step_dir = create_step("test")
        
        step_file = step_dir / "step.json"
        step_data = json.loads(step_file.read_text())
        step_data["agent_config"] = "nonexistent-config.json"
        step_file.write_text(json.dumps(step_data))
        
        data = {
            "name": "saga-missing-config",
            "start": "step1",
            "nodes": {
                "step1": {"type": "step", "reference": "test"}
            },
            "connections": [
                {"node": "step1", "then": "end"}
            ]
        }
        
        saga = SagaDefinition.from_dict(data)
        is_valid, errors, warnings = validate_saga(saga, tmp_steps_dir, tmp_sagas_dir)
        
        assert not is_valid
        assert any("agent_config" in err.lower() and ("not found" in err.lower() or "does not exist" in err.lower()) for err in errors)
    
    def test_av_e_02_global_config_missing_no_agent_config(self, tmp_steps_dir, tmp_sagas_dir, create_step):
        """AV-E-02: Validation passes when global config missing and no agent_config specified (backward compatible)."""
        create_step("test")
        
        data = {
            "name": "saga-no-global-config",
            "start": "step1",
            "nodes": {
                "step1": {"type": "step", "reference": "test"}
            },
            "connections": [
                {"node": "step1", "then": "end"}
            ]
        }
        
        saga = SagaDefinition.from_dict(data)
        is_valid, errors, warnings = validate_saga(saga, tmp_steps_dir, tmp_sagas_dir)
        
        assert is_valid
        assert len(errors) == 0
    
    def test_av_e_03_agent_config_with_relative_traversal(self, tmp_steps_dir, tmp_sagas_dir, create_step):
        """AV-E-03: Validation passes with relative traversal in agent_config path."""
        step_dir = create_step("test")
        shared_dir = step_dir.parent / "shared"
        shared_dir.mkdir(exist_ok=True)
        config_file = shared_dir / "agent-config.json"
        config_file.write_text('{"permissions": {"allow": []}}')
        
        step_file = step_dir / "step.json"
        step_data = json.loads(step_file.read_text())
        step_data["agent_config"] = "../shared/agent-config.json"
        step_file.write_text(json.dumps(step_data))
        
        data = {
            "name": "saga-relative-traversal",
            "start": "step1",
            "nodes": {
                "step1": {"type": "step", "reference": "test"}
            },
            "connections": [
                {"node": "step1", "then": "end"}
            ]
        }
        
        saga = SagaDefinition.from_dict(data)
        is_valid, errors, warnings = validate_saga(saga, tmp_steps_dir, tmp_sagas_dir)
        
        assert is_valid
        assert len(errors) == 0
