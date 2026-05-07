#!/usr/bin/env python3
"""
Saga Validator - Validates saga definitions for correctness.
"""

import json
from pathlib import Path
from typing import Set, Dict, List

try:
    from .saga_models import SagaDefinition, DirectedConnection, BranchingConnection, Connection, NodeDefinition
    from .devin_wrapper import StepDefinition
except ImportError:
    from saga_models import SagaDefinition, DirectedConnection, BranchingConnection, Connection, NodeDefinition
    from devin_wrapper import StepDefinition


class SagaValidator:
    """Validates saga definitions."""
    
    def __init__(self, saga: SagaDefinition, steps_dir: Path, sagas_dir: Path, recursion_depth: int = 0):
        self.saga = saga
        self.steps_dir = steps_dir
        self.sagas_dir = sagas_dir
        self.recursion_depth = recursion_depth
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.visited_sagas: Set[str] = set()
    
    def validate(self) -> bool:
        """Run all validations. Returns True if valid, False otherwise."""
        self.errors = []
        self.warnings = []
        
        self._validate_recursion_depth()
        self._validate_start_exists()
        self._validate_nodes_exist()
        self._validate_agent_configs()
        self._validate_connections_reference_nodes()
        self._validate_graph_connectivity()
        
        return len(self.errors) == 0
    
    def get_errors(self) -> List[str]:
        """Get list of validation errors."""
        return self.errors
    
    def get_warnings(self) -> List[str]:
        """Get list of validation warnings."""
        return self.warnings
    
    def _validate_recursion_depth(self):
        """Check if recursion depth exceeds maximum."""
        if self.recursion_depth > self.saga.max_recursion_depth:
            self.errors.append(
                f"Recursion depth {self.recursion_depth} exceeds maximum {self.saga.max_recursion_depth}"
            )
    
    def _validate_start_exists(self):
        """Ensure start node exists."""
        if self.saga.start == "end":
            self.errors.append("Start cannot be 'end'")
            return
        
        if self.saga.start not in self.saga.nodes:
            self.errors.append(f"Start node '{self.saga.start}' is not defined in nodes")
    
    def _validate_nodes_exist(self):
        """Ensure all defined nodes exist in filesystem."""
        for node_name, node_def in self.saga.nodes.items():
            if node_def.type == "step":
                step_path = self.steps_dir / node_def.reference / "step.json"
                if not step_path.exists():
                    self.errors.append(f"Step node '{node_name}' references '{node_def.reference}' which does not exist at {step_path}")
            
            elif node_def.type == "saga":
                saga_path = Path(node_def.reference)
                if not saga_path.is_absolute():
                    saga_path = self.sagas_dir / node_def.reference
                
                if not saga_path.exists():
                    self.errors.append(f"Saga node '{node_name}' references '{node_def.reference}' which does not exist at {saga_path}")
                else:
                    self._validate_subsaga(node_name, saga_path)
    
    def _validate_agent_configs(self):
        """Validate agent_config files for all step nodes."""
        for node_name, node_def in self.saga.nodes.items():
            if node_def.type == "step":
                step_path = self.steps_dir / node_def.reference / "step.json"
                if step_path.exists():
                    self._validate_step_agent_config(node_name, step_path)
    
    def _validate_step_agent_config(self, node_name: str, step_path: Path):
        """Validate agent_config for a specific step.
        
        Rules:
        - If step specifies agent_config, it MUST exist (error if missing)
        - If step doesn't specify agent_config, global config is optional (no error if missing)
        """
        try:
            step_data = json.loads(step_path.read_text())
            step_def_dir = step_path.parent
            step_def = StepDefinition(step_data, step_def_dir)
            
            # Get the agent config path
            agent_config_path = step_def.get_agent_config_path()
            
            if agent_config_path:
                # Step has explicit agent_config, verify it exists
                if not agent_config_path.exists():
                    self.errors.append(
                        f"Step node '{node_name}' references agent_config '{step_def.agent_config}' "
                        f"which does not exist at {agent_config_path}"
                    )
                elif not agent_config_path.is_file():
                    self.errors.append(
                        f"Step node '{node_name}' agent_config path '{agent_config_path}' is not a file"
                    )
        except Exception as e:
            self.errors.append(f"Failed to validate agent_config for step node '{node_name}': {e}")
    
    def _validate_subsaga(self, node_name: str, saga_path: Path):
        """Recursively validate a sub-saga."""
        if node_name in self.visited_sagas:
            self.warnings.append(f"Circular reference detected: saga node '{node_name}' may cause recursion")
            return
        
        self.visited_sagas.add(node_name)
        
        try:
            sub_saga_data = json.loads(saga_path.read_text())
            sub_saga = SagaDefinition.from_dict(sub_saga_data)
            
            sub_validator = SagaValidator(
                sub_saga,
                self.steps_dir,
                self.sagas_dir,
                recursion_depth=self.recursion_depth + 1
            )
            sub_validator.visited_sagas = self.visited_sagas
            
            if not sub_validator.validate():
                for error in sub_validator.get_errors():
                    self.errors.append(f"In sub-saga '{node_name}': {error}")
            
            for warning in sub_validator.get_warnings():
                self.warnings.append(f"In sub-saga '{node_name}': {warning}")
        
        except Exception as e:
            self.errors.append(f"Failed to load sub-saga '{node_name}': {e}")
    
    def _validate_connections_reference_nodes(self):
        """Ensure all connections reference defined nodes or 'end'."""
        for conn in self.saga.connections:
            node_name = conn.node
            
            if node_name not in self.saga.nodes:
                self.errors.append(f"Connection references undefined node '{node_name}'")
            
            if isinstance(conn, DirectedConnection):
                target = conn.then.target
                if target != "end" and target not in self.saga.nodes:
                    self.errors.append(f"Connection from '{node_name}' references undefined target '{target}'")
            
            elif isinstance(conn, BranchingConnection):
                pass_target = conn.pass_target.target
                fail_target = conn.fail_target.target
                
                if pass_target != "end" and pass_target not in self.saga.nodes:
                    self.errors.append(f"Connection from '{node_name}' pass references undefined target '{pass_target}'")
                
                if fail_target != "end" and fail_target not in self.saga.nodes:
                    self.errors.append(f"Connection from '{node_name}' fail references undefined target '{fail_target}'")
    
    def _validate_graph_connectivity(self):
        """Ensure graph is closed and all nodes can reach 'end'."""
        graph = self._build_graph()
        
        for node_name in self.saga.nodes.keys():
            if node_name not in graph or len(graph[node_name]) == 0:
                self.errors.append(f"Dead-end node '{node_name}' has no outgoing connections")
        
        if not self._can_reach_end(graph):
            self.errors.append("'end' is not reachable from start - graph is not closed")
    
    
    def _build_graph(self) -> Dict[str, List[str]]:
        """Build adjacency list representation of the graph."""
        graph: Dict[str, List[str]] = {}
        
        for conn in self.saga.connections:
            if conn.node not in graph:
                graph[conn.node] = []
            
            if isinstance(conn, DirectedConnection):
                graph[conn.node].append(conn.then.target)
            elif isinstance(conn, BranchingConnection):
                graph[conn.node].append(conn.pass_target.target)
                graph[conn.node].append(conn.fail_target.target)
        
        return graph
    
    def _can_reach_end(self, graph: Dict[str, List[str]]) -> bool:
        """Check if 'end' is reachable from start using BFS."""
        if self.saga.start == "end":
            return True
        
        visited = set()
        queue = [self.saga.start]
        
        while queue:
            node = queue.pop(0)
            
            if node in visited:
                continue
            
            visited.add(node)
            
            if node == "end":
                return True
            
            if node in graph:
                for neighbor in graph[node]:
                    if neighbor not in visited:
                        queue.append(neighbor)
        
        return False


def validate_saga(saga: SagaDefinition, steps_dir: Path, sagas_dir: Path) -> tuple[bool, List[str], List[str]]:
    """Validate a saga definition. Returns (is_valid, errors, warnings)."""
    validator = SagaValidator(saga, steps_dir, sagas_dir)
    is_valid = validator.validate()
    return is_valid, validator.get_errors(), validator.get_warnings()
