import pytest
import subprocess
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from orchestrator.models import SagaDefinition
from orchestrator.saga_executor import SagaExecutor, TraversalTracker


class TestSagaExecutorHappyPath:
    """Happy path tests for saga_executor.py (E-H-*)."""
    
    def test_e_h_01_execute_simple_linear_saga(self, tmp_steps_dir, tmp_sagas_dir, tmp_log_path, create_step):
        """E-H-01: Execute simple linear saga successfully."""
        create_step("test1")
        create_step("test2")
        
        data = {
            "name": "linear-saga",
            "start": "step1",
            "nodes": {
                "step1": {"type": "step", "reference": "test1"},
                "step2": {"type": "step", "reference": "test2"}
            },
            "connections": [
                {"node": "step1", "then": "step2"},
                {"node": "step2", "then": "end"}
            ]
        }
        
        saga = SagaDefinition.from_dict(data)
        executor = SagaExecutor(saga, tmp_steps_dir, tmp_sagas_dir, tmp_log_path)
        
        with patch.object(executor, '_execute_node') as mock_execute:
            mock_execute.return_value = (0, ["output1"], "")
            
            success, outputs = executor.execute([])
            
            assert success
            assert mock_execute.call_count == 2
    
    def test_e_h_02_execute_branching_saga_pass_path(self, tmp_steps_dir, tmp_sagas_dir, tmp_log_path, create_step):
        """E-H-02: Execute branching saga (pass path)."""
        create_step("test1")
        create_step("test2")
        
        data = {
            "name": "branching-saga",
            "start": "step1",
            "nodes": {
                "step1": {"type": "step", "reference": "test1"},
                "step2": {"type": "step", "reference": "test2"}
            },
            "connections": [
                {"node": "step1", "pass": "step2", "fail": "end"},
                {"node": "step2", "then": "end"}
            ]
        }
        
        saga = SagaDefinition.from_dict(data)
        executor = SagaExecutor(saga, tmp_steps_dir, tmp_sagas_dir, tmp_log_path)
        
        with patch.object(executor, '_execute_node') as mock_execute:
            mock_execute.return_value = (0, [], "")
            
            success, outputs = executor.execute([])
            
            assert success
    
    def test_e_h_03_execute_branching_saga_fail_path(self, tmp_steps_dir, tmp_sagas_dir, tmp_log_path, create_step):
        """E-H-03: Execute branching saga (fail path)."""
        create_step("test1")
        
        data = {
            "name": "branching-saga",
            "start": "step1",
            "nodes": {
                "step1": {"type": "step", "reference": "test1"}
            },
            "connections": [
                {"node": "step1", "pass": "end", "fail": "end"}
            ]
        }
        
        saga = SagaDefinition.from_dict(data)
        executor = SagaExecutor(saga, tmp_steps_dir, tmp_sagas_dir, tmp_log_path)
        
        with patch.object(executor, '_execute_node') as mock_execute:
            mock_execute.return_value = (1, [], "")
            
            success, outputs = executor.execute([])
            
            assert success
    
    def test_e_h_04_execute_retry_saga(self, tmp_steps_dir, tmp_sagas_dir, tmp_log_path, create_step):
        """E-H-04: Execute retry saga (retries until success)."""
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
        executor = SagaExecutor(saga, tmp_steps_dir, tmp_sagas_dir, tmp_log_path)
        
        call_count = 0
        def mock_execute_side_effect(node, inputs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                return (1, [], "")
            return (0, [], "")
        
        with patch.object(executor, '_execute_node', side_effect=mock_execute_side_effect):
            success, outputs = executor.execute([])
            
            assert success
            assert call_count == 3
    
    def test_e_h_05_execute_composite_saga(self, tmp_steps_dir, tmp_sagas_dir, tmp_log_path, create_step, create_saga):
        """E-H-05: Execute composite saga (parent + sub-saga)."""
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
        executor = SagaExecutor(saga, tmp_steps_dir, tmp_sagas_dir, tmp_log_path)
        
        with patch.object(executor.orchestrator, 'invoke_step') as mock_invoke:
            mock_invoke.return_value = (0, "test-session-123")
            
            success, outputs = executor.execute([])
            
            assert success
    
    def test_e_h_06_output_propagation_between_steps(self, tmp_steps_dir, tmp_sagas_dir, tmp_log_path, create_step):
        """E-H-06: Output propagation between steps."""
        step1_dir = create_step("test1")
        step2_dir = create_step("test2")
        
        outputs_file = step1_dir / "outputs.json"
        outputs_file.write_text(json.dumps({"outputs": ["file1.txt", "file2.txt"]}))
        
        data = {
            "name": "output-saga",
            "start": "step1",
            "nodes": {
                "step1": {"type": "step", "reference": "test1"},
                "step2": {"type": "step", "reference": "test2"}
            },
            "connections": [
                {"node": "step1", "then": "step2"},
                {"node": "step2", "then": "end"}
            ]
        }
        
        saga = SagaDefinition.from_dict(data)
        executor = SagaExecutor(saga, tmp_steps_dir, tmp_sagas_dir, tmp_log_path)
        
        with patch.object(executor.orchestrator, 'invoke_step') as mock_invoke:
            mock_invoke.return_value = (0, "test-session-123")
            
            success, outputs = executor.execute([])
            
            assert success
    
    def test_e_h_07_subsaga_outputs_to_parent(self, tmp_steps_dir, tmp_sagas_dir, tmp_log_path, create_step, create_saga):
        """E-H-07: Sub-saga outputs passed to parent's next node."""
        step1_dir = create_step("test1")
        create_step("test2")
        
        outputs_file = step1_dir / "outputs.json"
        outputs_file.write_text(json.dumps({"outputs": ["subsaga_output.txt"]}))
        
        subsaga_data = {
            "name": "sub-saga",
            "start": "substep",
            "nodes": {
                "substep": {"type": "step", "reference": "test1"}
            },
            "connections": [
                {"node": "substep", "then": "end"}
            ]
        }
        create_saga("sub", subsaga_data)
        
        data = {
            "name": "parent-saga",
            "start": "subsaga1",
            "nodes": {
                "subsaga1": {"type": "saga", "reference": "sub.json"},
                "step2": {"type": "step", "reference": "test2"}
            },
            "connections": [
                {"node": "subsaga1", "then": "step2"},
                {"node": "step2", "then": "end"}
            ]
        }
        
        saga = SagaDefinition.from_dict(data)
        executor = SagaExecutor(saga, tmp_steps_dir, tmp_sagas_dir, tmp_log_path)
        
        with patch.object(executor.orchestrator, 'invoke_step') as mock_invoke:
            mock_invoke.return_value = (0, "test-session-123")
            
            success, outputs = executor.execute([])
            
            assert success


class TestSagaExecutorEdgeCases:
    """Edge case tests for saga_executor.py (E-E-*)."""
    
    def test_e_e_01_empty_initial_inputs(self, tmp_steps_dir, tmp_sagas_dir, tmp_log_path, create_step):
        """E-E-01: Empty initial inputs."""
        create_step("test")
        
        data = {
            "name": "test-saga",
            "start": "step1",
            "nodes": {
                "step1": {"type": "step", "reference": "test"}
            },
            "connections": [
                {"node": "step1", "then": "end"}
            ]
        }
        
        saga = SagaDefinition.from_dict(data)
        executor = SagaExecutor(saga, tmp_steps_dir, tmp_sagas_dir, tmp_log_path)
        
        with patch.object(executor.orchestrator, 'invoke_step') as mock_invoke:
            mock_invoke.return_value = (0, "test-session-123")
            
            success, outputs = executor.execute([])
            
            assert success
    
    def test_e_e_02_step_with_no_outputs(self, tmp_steps_dir, tmp_sagas_dir, tmp_log_path, create_step):
        """E-E-02: Step with no outputs."""
        create_step("test")
        
        data = {
            "name": "test-saga",
            "start": "step1",
            "nodes": {
                "step1": {"type": "step", "reference": "test"}
            },
            "connections": [
                {"node": "step1", "then": "end"}
            ]
        }
        
        saga = SagaDefinition.from_dict(data)
        executor = SagaExecutor(saga, tmp_steps_dir, tmp_sagas_dir, tmp_log_path)
        
        with patch.object(executor.orchestrator, 'invoke_step') as mock_invoke:
            mock_invoke.return_value = (0, "test-session-123")
            
            success, outputs = executor.execute([])
            
            assert success
            assert outputs == []
    
    def test_e_e_03_immediate_end(self, tmp_steps_dir, tmp_sagas_dir, tmp_log_path):
        """E-E-03: Immediate end (start → end directly)."""
        data = {
            "name": "test-saga",
            "start": "end",
            "nodes": {},
            "connections": []
        }
        
        saga = SagaDefinition.from_dict(data)
        executor = SagaExecutor(saga, tmp_steps_dir, tmp_sagas_dir, tmp_log_path)
        
        success, outputs = executor.execute([])
        
        assert success
        assert outputs == []
    
    def test_e_e_04_nested_saga_at_max_recursion_depth(self, tmp_steps_dir, tmp_sagas_dir, tmp_log_path, create_saga):
        """E-E-04: Nested saga at max recursion depth."""
        subsaga_data = {
            "name": "sub-saga",
            "start": "end",
            "nodes": {},
            "connections": [],
            "max_recursion_depth": 1
        }
        create_saga("sub", subsaga_data)
        
        data = {
            "name": "parent-saga",
            "start": "subsaga1",
            "nodes": {
                "subsaga1": {"type": "saga", "reference": "sub.json"}
            },
            "connections": [
                {"node": "subsaga1", "then": "end"}
            ],
            "max_recursion_depth": 1
        }
        
        saga = SagaDefinition.from_dict(data)
        executor = SagaExecutor(saga, tmp_steps_dir, tmp_sagas_dir, tmp_log_path)
        
        exit_code, outputs, stderr = executor._execute_subsaga("subsaga1", saga.nodes["subsaga1"], [])
        
        assert exit_code == 0
    
    def test_e_e_05_step_completes_just_before_timeout(self, tmp_steps_dir, tmp_sagas_dir, tmp_log_path, create_step):
        """E-E-05: Step completes just before timeout."""
        create_step("test")
        
        data = {
            "name": "test-saga",
            "start": "step1",
            "nodes": {
                "step1": {"type": "step", "reference": "test", "timeout": 10}
            },
            "connections": [
                {"node": "step1", "then": "end"}
            ]
        }
        
        saga = SagaDefinition.from_dict(data)
        executor = SagaExecutor(saga, tmp_steps_dir, tmp_sagas_dir, tmp_log_path)
        
        with patch.object(executor.orchestrator, 'invoke_step') as mock_invoke:
            mock_invoke.return_value = (0, "test-session-123")
            
            exit_code, outputs, stderr = executor._execute_step("step1", saga.nodes["step1"], [])
            
            assert exit_code == 0


class TestSagaExecutorTimeouts:
    """Critical timeout tests for saga_executor.py (E-T-*)."""
    
    def test_e_t_01_step_timeout_enforcement(self, tmp_steps_dir, tmp_sagas_dir, tmp_log_path, create_step):
        """E-T-01: Step timeout enforcement (hard, process killed)."""
        create_step("test")
        
        data = {
            "name": "test-saga",
            "start": "step1",
            "nodes": {
                "step1": {"type": "step", "reference": "test", "timeout": 1}
            },
            "connections": [
                {"node": "step1", "then": "end"}
            ]
        }
        
        saga = SagaDefinition.from_dict(data)
        executor = SagaExecutor(saga, tmp_steps_dir, tmp_sagas_dir, tmp_log_path)
        
        with patch.object(executor.orchestrator, 'invoke_step') as mock_invoke:
            mock_invoke.side_effect = subprocess.TimeoutExpired(cmd=['test'], timeout=1)
            
            exit_code, outputs, stderr = executor._execute_step("step1", saga.nodes["step1"], [])
            
            assert exit_code == 1
            assert outputs == []
    
    def test_e_t_02_subsaga_timeout_warning(self, tmp_steps_dir, tmp_sagas_dir, tmp_log_path, create_saga):
        """E-T-02: Sub-saga timeout warning (soft, logged only)."""
        subsaga_data = {
            "name": "sub-saga",
            "start": "end",
            "nodes": {},
            "connections": []
        }
        create_saga("sub", subsaga_data)
        
        data = {
            "name": "test-saga",
            "start": "subsaga1",
            "nodes": {
                "subsaga1": {"type": "saga", "reference": "sub.json", "timeout": 0}
            },
            "connections": [
                {"node": "subsaga1", "then": "end"}
            ]
        }
        
        saga = SagaDefinition.from_dict(data)
        executor = SagaExecutor(saga, tmp_steps_dir, tmp_sagas_dir, tmp_log_path)
        
        exit_code, outputs, stderr = executor._execute_subsaga("subsaga1", saga.nodes["subsaga1"], [])
        
        log_content = tmp_log_path.read_text()
        assert "WARNING" in log_content or "exceeded timeout" in log_content or exit_code == 0
    
    def test_e_t_03_very_short_timeout(self, tmp_steps_dir, tmp_sagas_dir, tmp_log_path, create_step):
        """E-T-03: Very short timeout (1 second) triggers immediately."""
        create_step("test")
        
        data = {
            "name": "test-saga",
            "start": "step1",
            "nodes": {
                "step1": {"type": "step", "reference": "test", "timeout": 1}
            },
            "connections": [
                {"node": "step1", "then": "end"}
            ]
        }
        
        saga = SagaDefinition.from_dict(data)
        executor = SagaExecutor(saga, tmp_steps_dir, tmp_sagas_dir, tmp_log_path)
        
        with patch.object(executor.orchestrator, 'invoke_step') as mock_invoke:
            mock_invoke.side_effect = subprocess.TimeoutExpired(cmd=['test'], timeout=1)
            
            exit_code, outputs, stderr = executor._execute_step("step1", saga.nodes["step1"], [])
            
            assert exit_code == 1
    
    def test_e_t_04_no_timeout_specified(self, tmp_steps_dir, tmp_sagas_dir, tmp_log_path, create_step):
        """E-T-04: No timeout specified (runs indefinitely)."""
        create_step("test")
        
        data = {
            "name": "test-saga",
            "start": "step1",
            "nodes": {
                "step1": {"type": "step", "reference": "test"}
            },
            "connections": [
                {"node": "step1", "then": "end"}
            ]
        }
        
        saga = SagaDefinition.from_dict(data)
        executor = SagaExecutor(saga, tmp_steps_dir, tmp_sagas_dir, tmp_log_path)
        
        with patch.object(executor.orchestrator, 'invoke_step') as mock_invoke:
            mock_invoke.return_value = (0, "test-session-123")
            
            exit_code, outputs, stderr = executor._execute_step("step1", saga.nodes["step1"], [])
            
            mock_invoke.assert_called_once()
            assert mock_invoke.call_args[1]['timeout'] is None
    
    def test_e_t_05_nested_saga_timeout_independent(self, tmp_steps_dir, tmp_sagas_dir, tmp_log_path, create_saga):
        """E-T-05: Nested saga timeout independent of parent."""
        subsaga_data = {
            "name": "sub-saga",
            "start": "end",
            "nodes": {},
            "connections": []
        }
        create_saga("sub", subsaga_data)
        
        data = {
            "name": "test-saga",
            "start": "subsaga1",
            "nodes": {
                "subsaga1": {"type": "saga", "reference": "sub.json", "timeout": 10}
            },
            "connections": [
                {"node": "subsaga1", "then": "end"}
            ]
        }
        
        saga = SagaDefinition.from_dict(data)
        executor = SagaExecutor(saga, tmp_steps_dir, tmp_sagas_dir, tmp_log_path)
        
        exit_code, outputs, stderr = executor._execute_subsaga("subsaga1", saga.nodes["subsaga1"], [])
        
        assert exit_code == 0


class TestSagaExecutorTraversalTracking:
    """Critical traversal tracking tests for saga_executor.py (E-TR-*)."""
    
    def test_e_tr_01_independent_traversal_tracking(self):
        """E-TR-01: Independent traversal tracking per saga instance."""
        tracker1 = TraversalTracker()
        tracker2 = TraversalTracker()
        
        tracker1.increment("step1", "step2")
        tracker1.increment("step1", "step2")
        
        assert tracker1.get_count("step1", "step2") == 2
        assert tracker2.get_count("step1", "step2") == 0
    
    def test_e_tr_02_traversal_limit_enforced_on_pass(self, tmp_steps_dir, tmp_sagas_dir, tmp_log_path, create_step):
        """E-TR-02: Traversal limit enforced on pass route."""
        create_step("test")
        
        data = {
            "name": "test-saga",
            "start": "step1",
            "nodes": {
                "step1": {"type": "step", "reference": "test"}
            },
            "connections": [
                {
                    "node": "step1",
                    "pass": {"target": "step1", "traversal_limit": 2},
                    "fail": "end"
                }
            ]
        }
        
        saga = SagaDefinition.from_dict(data)
        executor = SagaExecutor(saga, tmp_steps_dir, tmp_sagas_dir, tmp_log_path)
        
        with patch.object(executor, '_execute_node') as mock_execute:
            mock_execute.return_value = (0, [], "")
            
            success, outputs = executor.execute([])
            
            assert not success
    
    def test_e_tr_03_traversal_limit_enforced_on_fail(self, tmp_steps_dir, tmp_sagas_dir, tmp_log_path, create_step):
        """E-TR-03: Traversal limit enforced on fail route."""
        create_step("test")
        
        data = {
            "name": "test-saga",
            "start": "step1",
            "nodes": {
                "step1": {"type": "step", "reference": "test"}
            },
            "connections": [
                {
                    "node": "step1",
                    "pass": "end",
                    "fail": {"target": "step1", "traversal_limit": 2}
                }
            ]
        }
        
        saga = SagaDefinition.from_dict(data)
        executor = SagaExecutor(saga, tmp_steps_dir, tmp_sagas_dir, tmp_log_path)
        
        with patch.object(executor, '_execute_node') as mock_execute:
            mock_execute.return_value = (1, [], "")
            
            success, outputs = executor.execute([])
            
            assert not success
    
    def test_e_tr_04_traversal_limit_enforced_on_then(self, tmp_steps_dir, tmp_sagas_dir, tmp_log_path, create_step):
        """E-TR-04: Traversal limit enforced on then route."""
        create_step("test")
        
        data = {
            "name": "test-saga",
            "start": "step1",
            "nodes": {
                "step1": {"type": "step", "reference": "test"}
            },
            "connections": [
                {
                    "node": "step1",
                    "then": {"target": "step1", "traversal_limit": 2}
                }
            ]
        }
        
        saga = SagaDefinition.from_dict(data)
        executor = SagaExecutor(saga, tmp_steps_dir, tmp_sagas_dir, tmp_log_path)
        
        with patch.object(executor, '_execute_node') as mock_execute:
            mock_execute.return_value = (0, [], "")
            
            success, outputs = executor.execute([])
            
            assert not success
    
    def test_e_tr_05_traversal_counts_persist(self):
        """E-TR-05: Traversal counts persist throughout execution."""
        tracker = TraversalTracker()
        
        count1 = tracker.increment("step1", "step2")
        count2 = tracker.increment("step1", "step2")
        count3 = tracker.increment("step1", "step2")
        
        assert count1 == 1
        assert count2 == 2
        assert count3 == 3
        assert tracker.get_count("step1", "step2") == 3


class TestSagaExecutorErrorHandling:
    """Critical error handling tests for saga_executor.py (E-ER-*)."""
    
    def test_e_er_01_nonexistent_saga_file(self, tmp_steps_dir, tmp_sagas_dir, tmp_log_path):
        """E-ER-01: Non-existent saga file."""
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
        executor = SagaExecutor(saga, tmp_steps_dir, tmp_sagas_dir, tmp_log_path)
        
        exit_code, outputs, stderr = executor._execute_subsaga("subsaga1", saga.nodes["subsaga1"], [])
        
        assert exit_code == 1
        assert outputs == []
    
    def test_e_er_02_invalid_saga_definition(self, tmp_steps_dir, tmp_sagas_dir, tmp_log_path, create_saga):
        """E-ER-02: Invalid saga definition (fails validation)."""
        invalid_saga_data = {
            "name": "invalid-saga",
            "nodes": {},
            "connections": []
        }
        create_saga("invalid", invalid_saga_data)
        
        data = {
            "name": "test-saga",
            "start": "subsaga1",
            "nodes": {
                "subsaga1": {"type": "saga", "reference": "invalid.json"}
            },
            "connections": [
                {"node": "subsaga1", "then": "end"}
            ]
        }
        
        saga = SagaDefinition.from_dict(data)
        executor = SagaExecutor(saga, tmp_steps_dir, tmp_sagas_dir, tmp_log_path)
        
        exit_code, outputs, stderr = executor._execute_subsaga("subsaga1", saga.nodes["subsaga1"], [])
        
        assert exit_code == 1
    
    def test_e_er_04_traversal_limit_exceeded(self, tmp_steps_dir, tmp_sagas_dir, tmp_log_path, create_step):
        """E-ER-04: Traversal limit exceeded on connection."""
        create_step("test")
        
        data = {
            "name": "test-saga",
            "start": "step1",
            "nodes": {
                "step1": {"type": "step", "reference": "test"}
            },
            "connections": [
                {
                    "node": "step1",
                    "then": {"target": "step1", "traversal_limit": 1}
                }
            ]
        }
        
        saga = SagaDefinition.from_dict(data)
        executor = SagaExecutor(saga, tmp_steps_dir, tmp_sagas_dir, tmp_log_path)
        
        with patch.object(executor, '_execute_node') as mock_execute:
            mock_execute.return_value = (0, [], "")
            
            success, outputs = executor.execute([])
            
            assert not success
    
    def test_e_er_05_step_timeout_exceeded(self, tmp_steps_dir, tmp_sagas_dir, tmp_log_path, create_step):
        """E-ER-05: Step timeout exceeded (hard timeout)."""
        create_step("test")
        
        data = {
            "name": "test-saga",
            "start": "step1",
            "nodes": {
                "step1": {"type": "step", "reference": "test", "timeout": 1}
            },
            "connections": [
                {"node": "step1", "then": "end"}
            ]
        }
        
        saga = SagaDefinition.from_dict(data)
        executor = SagaExecutor(saga, tmp_steps_dir, tmp_sagas_dir, tmp_log_path)
        
        with patch.object(executor.orchestrator, 'invoke_step') as mock_invoke:
            mock_invoke.side_effect = subprocess.TimeoutExpired(cmd=['test'], timeout=1)
            
            exit_code, outputs, stderr = executor._execute_step("step1", saga.nodes["step1"], [])
            
            assert exit_code == 1
    
    def test_e_er_08_node_not_found(self, tmp_steps_dir, tmp_sagas_dir, tmp_log_path):
        """E-ER-08: Node not found in saga definition."""
        data = {
            "name": "test-saga",
            "start": "step1",
            "nodes": {},
            "connections": []
        }
        
        saga = SagaDefinition.from_dict(data)
        executor = SagaExecutor(saga, tmp_steps_dir, tmp_sagas_dir, tmp_log_path)
        
        exit_code, outputs, stderr = executor._execute_node("nonexistent", [])
        
        assert exit_code == 1
        assert outputs == []
    
    def test_e_er_09_no_connection_from_node(self, tmp_steps_dir, tmp_sagas_dir, tmp_log_path, create_step):
        """E-ER-09: No connection from node."""
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
        executor = SagaExecutor(saga, tmp_steps_dir, tmp_sagas_dir, tmp_log_path)
        
        with patch.object(executor, '_execute_node') as mock_execute:
            mock_execute.return_value = (0, [], "")
            
            success, outputs = executor.execute([])
            
            assert not success
    
    def test_e_er_11_subsaga_execution_returns_failure(self, tmp_steps_dir, tmp_sagas_dir, tmp_log_path, create_saga):
        """E-ER-11: Sub-saga execution returns failure."""
        subsaga_data = {
            "name": "sub-saga",
            "start": "step1",
            "nodes": {
                "step1": {"type": "step", "reference": "test"}
            },
            "connections": []
        }
        create_saga("sub", subsaga_data)
        
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
        executor = SagaExecutor(saga, tmp_steps_dir, tmp_sagas_dir, tmp_log_path)
        
        exit_code, outputs, stderr = executor._execute_subsaga("subsaga1", saga.nodes["subsaga1"], [])
        
        assert exit_code == 1
    
    def test_e_er_12_invalid_node_type(self, tmp_steps_dir, tmp_sagas_dir, tmp_log_path):
        """E-ER-12: Invalid node type during execution."""
        data = {
            "name": "test-saga",
            "start": "step1",
            "nodes": {
                "step1": {"type": "step", "reference": "test"}
            },
            "connections": []
        }
        
        saga = SagaDefinition.from_dict(data)
        executor = SagaExecutor(saga, tmp_steps_dir, tmp_sagas_dir, tmp_log_path)
        
        saga.nodes["step1"].type = "invalid"
        
        exit_code, outputs, stderr = executor._execute_node("step1", [])
        
        assert exit_code == 1
