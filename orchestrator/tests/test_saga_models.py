import pytest
from orchestrator.models import SagaDefinition, DirectedConnection, BranchingConnection


class TestSagaModelsHappyPath:
    """Happy path tests for saga_models.py (M-H-*)."""
    
    def test_m_h_01_parse_simple_saga_minimal_fields(self):
        """M-H-01: Parse simple saga with minimal fields."""
        data = {
            "name": "simple-saga",
            "start": "step1",
            "nodes": {
                "step1": {"type": "step", "reference": "test-step"}
            },
            "connections": [
                {"node": "step1", "then": "end"}
            ]
        }
        
        saga = SagaDefinition.from_dict(data)
        
        assert saga.name == "simple-saga"
        assert saga.start == "step1"
        assert len(saga.nodes) == 1
        assert saga.nodes["step1"].type == "step"
        assert saga.nodes["step1"].reference == "test-step"
        assert len(saga.connections) == 1
    
    def test_m_h_02_parse_directed_connection_with_then(self):
        """M-H-02: Parse directed connection with 'then'."""
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
        
        assert len(saga.connections) == 1
        conn = saga.connections[0]
        assert isinstance(conn, DirectedConnection)
        assert conn.node == "step1"
        assert conn.then.target == "end"
        assert conn.then.traversal_limit is None
    
    def test_m_h_03_parse_branching_connection_with_pass_fail(self):
        """M-H-03: Parse branching connection with 'pass'/'fail'."""
        data = {
            "name": "test-saga",
            "start": "step1",
            "nodes": {
                "step1": {"type": "step", "reference": "test"}
            },
            "connections": [
                {"node": "step1", "pass": "end", "fail": "end"}
            ]
        }
        
        saga = SagaDefinition.from_dict(data)
        
        assert len(saga.connections) == 1
        conn = saga.connections[0]
        assert isinstance(conn, BranchingConnection)
        assert conn.node == "step1"
        assert conn.pass_target.target == "end"
        assert conn.fail_target.target == "end"
    
    def test_m_h_04_parse_connection_with_traversal_limit(self):
        """M-H-04: Parse connection with traversal limit."""
        data = {
            "name": "test-saga",
            "start": "step1",
            "nodes": {
                "step1": {"type": "step", "reference": "test"}
            },
            "connections": [
                {"node": "step1", "then": {"target": "step1", "traversal_limit": 3}}
            ]
        }
        
        saga = SagaDefinition.from_dict(data)
        
        conn = saga.connections[0]
        assert isinstance(conn, DirectedConnection)
        assert conn.then.target == "step1"
        assert conn.then.traversal_limit == 3
    
    def test_m_h_05_parse_connection_without_traversal_limit(self):
        """M-H-05: Parse connection without traversal limit (None)."""
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
        
        conn = saga.connections[0]
        assert conn.then.traversal_limit is None
    
    def test_m_h_06_parse_node_with_timeout(self):
        """M-H-06: Parse node with timeout specified."""
        data = {
            "name": "test-saga",
            "start": "step1",
            "nodes": {
                "step1": {"type": "step", "reference": "test", "timeout": 30}
            },
            "connections": [
                {"node": "step1", "then": "end"}
            ]
        }
        
        saga = SagaDefinition.from_dict(data)
        
        assert saga.nodes["step1"].timeout == 30
    
    def test_m_h_07_parse_node_without_timeout(self):
        """M-H-07: Parse node without timeout (None)."""
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
        
        assert saga.nodes["step1"].timeout is None
    
    def test_m_h_08_parse_saga_with_custom_max_recursion_depth(self):
        """M-H-08: Parse saga with custom max_recursion_depth."""
        data = {
            "name": "test-saga",
            "start": "step1",
            "nodes": {
                "step1": {"type": "step", "reference": "test"}
            },
            "connections": [
                {"node": "step1", "then": "end"}
            ],
            "max_recursion_depth": 10
        }
        
        saga = SagaDefinition.from_dict(data)
        
        assert saga.max_recursion_depth == 10
    
    def test_m_h_09_parse_saga_with_default_max_recursion_depth(self):
        """M-H-09: Parse saga with default max_recursion_depth (50)."""
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
        
        assert saga.max_recursion_depth == 50


class TestSagaModelsEdgeCases:
    """Edge case tests for saga_models.py (M-E-*)."""
    
    def test_m_e_01_traversal_limit_of_zero(self):
        """M-E-01: Traversal limit of 0 (immediate failure)."""
        data = {
            "name": "test-saga",
            "start": "step1",
            "nodes": {
                "step1": {"type": "step", "reference": "test"}
            },
            "connections": [
                {"node": "step1", "then": {"target": "step1", "traversal_limit": 0}}
            ]
        }
        
        saga = SagaDefinition.from_dict(data)
        
        conn = saga.connections[0]
        assert conn.then.traversal_limit == 0
    
    def test_m_e_02_very_large_traversal_limit(self):
        """M-E-02: Very large traversal limit (999999)."""
        data = {
            "name": "test-saga",
            "start": "step1",
            "nodes": {
                "step1": {"type": "step", "reference": "test"}
            },
            "connections": [
                {"node": "step1", "then": {"target": "step1", "traversal_limit": 999999}}
            ]
        }
        
        saga = SagaDefinition.from_dict(data)
        
        conn = saga.connections[0]
        assert conn.then.traversal_limit == 999999
    
    def test_m_e_03_timeout_of_zero(self):
        """M-E-03: Timeout of 0 (immediate timeout)."""
        data = {
            "name": "test-saga",
            "start": "step1",
            "nodes": {
                "step1": {"type": "step", "reference": "test", "timeout": 0}
            },
            "connections": [
                {"node": "step1", "then": "end"}
            ]
        }
        
        saga = SagaDefinition.from_dict(data)
        
        assert saga.nodes["step1"].timeout == 0
    
    def test_m_e_04_very_large_timeout(self):
        """M-E-04: Very large timeout (86400 seconds)."""
        data = {
            "name": "test-saga",
            "start": "step1",
            "nodes": {
                "step1": {"type": "step", "reference": "test", "timeout": 86400}
            },
            "connections": [
                {"node": "step1", "then": "end"}
            ]
        }
        
        saga = SagaDefinition.from_dict(data)
        
        assert saga.nodes["step1"].timeout == 86400


class TestSagaModelsErrorHandling:
    """Critical error handling tests for saga_models.py (M-ER-*)."""
    
    def test_m_er_01_missing_name_raises_error(self):
        """M-ER-01: Missing 'name' property raises ValueError."""
        data = {
            "start": "step1",
            "nodes": {
                "step1": {"type": "step", "reference": "test"}
            },
            "connections": []
        }
        
        with pytest.raises(ValueError, match="must include 'name'"):
            SagaDefinition.from_dict(data)
    
    def test_m_er_02_missing_start_raises_error(self):
        """M-ER-02: Missing 'start' property raises ValueError."""
        data = {
            "name": "test-saga",
            "nodes": {
                "step1": {"type": "step", "reference": "test"}
            },
            "connections": []
        }
        
        with pytest.raises(ValueError, match="must include 'start'"):
            SagaDefinition.from_dict(data)
    
    def test_m_er_03_empty_nodes_section(self):
        """M-ER-03: Empty or missing 'nodes' section."""
        data = {
            "name": "test-saga",
            "start": "step1",
            "connections": []
        }
        
        saga = SagaDefinition.from_dict(data)
        assert saga.nodes == {}
    
    def test_m_er_04_connection_missing_node_property(self):
        """M-ER-04: Connection missing 'node' property."""
        data = {
            "name": "test-saga",
            "start": "step1",
            "nodes": {
                "step1": {"type": "step", "reference": "test"}
            },
            "connections": [
                {"then": "end"}
            ]
        }
        
        with pytest.raises(ValueError, match="must include 'node'"):
            SagaDefinition.from_dict(data)
    
    def test_m_er_05_connection_with_neither_then_nor_pass_fail(self):
        """M-ER-05: Connection with neither 'then' nor 'pass'/'fail'."""
        data = {
            "name": "test-saga",
            "start": "step1",
            "nodes": {
                "step1": {"type": "step", "reference": "test"}
            },
            "connections": [
                {"node": "step1"}
            ]
        }
        
        with pytest.raises(ValueError, match="must have either 'then' or 'pass'/'fail'"):
            SagaDefinition.from_dict(data)
    
    def test_m_er_06_connection_with_only_pass(self):
        """M-ER-06: Connection with only 'pass' (missing 'fail')."""
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
    
    def test_m_er_07_connection_with_only_fail(self):
        """M-ER-07: Connection with only 'fail' (missing 'pass')."""
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
    
    def test_m_er_08_node_missing_type(self):
        """M-ER-08: Node missing 'type'."""
        data = {
            "name": "test-saga",
            "start": "step1",
            "nodes": {
                "step1": {"reference": "test"}
            },
            "connections": []
        }
        
        with pytest.raises(ValueError, match="must include 'type'"):
            SagaDefinition.from_dict(data)
    
    def test_m_er_08_node_missing_reference(self):
        """M-ER-08: Node missing 'reference'."""
        data = {
            "name": "test-saga",
            "start": "step1",
            "nodes": {
                "step1": {"type": "step"}
            },
            "connections": []
        }
        
        with pytest.raises(ValueError, match="must include 'reference'"):
            SagaDefinition.from_dict(data)
