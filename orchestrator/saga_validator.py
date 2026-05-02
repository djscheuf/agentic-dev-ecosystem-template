#!/usr/bin/env python3
"""
Saga Validator - Validates saga definitions for correctness.
"""

from pathlib import Path
from typing import Set, Dict, List

try:
    from .saga_models import SagaDefinition, DirectedConnection, BranchingConnection, Connection
except ImportError:
    from saga_models import SagaDefinition, DirectedConnection, BranchingConnection, Connection


class SagaValidator:
    """Validates saga definitions."""
    
    def __init__(self, saga: SagaDefinition, steps_dir: Path):
        self.saga = saga
        self.steps_dir = steps_dir
        self.errors: List[str] = []
    
    def validate(self) -> bool:
        """Run all validations. Returns True if valid, False otherwise."""
        self.errors = []
        
        self._validate_start_exists()
        self._validate_steps_exist()
        self._validate_graph_connectivity()
        
        return len(self.errors) == 0
    
    def get_errors(self) -> List[str]:
        """Get list of validation errors."""
        return self.errors
    
    def _validate_start_exists(self):
        """Ensure start step exists."""
        if self.saga.start == "end":
            self.errors.append("Start cannot be 'end'")
            return
        
        step_path = self.steps_dir / self.saga.start / "step.json"
        if not step_path.exists():
            self.errors.append(f"Start step '{self.saga.start}' does not exist at {step_path}")
    
    def _validate_steps_exist(self):
        """Ensure all referenced steps exist in filesystem."""
        referenced_steps = self._get_all_referenced_steps()
        
        for step_name in referenced_steps:
            if step_name == "end":
                continue
            
            step_path = self.steps_dir / step_name / "step.json"
            if not step_path.exists():
                self.errors.append(f"Step '{step_name}' does not exist at {step_path}")
    
    def _validate_graph_connectivity(self):
        """Ensure graph is closed and all nodes can reach 'end'."""
        # Build adjacency list
        graph = self._build_graph()
        
        # Check that all nodes (except 'end') have outgoing edges
        all_nodes = self._get_all_nodes()
        for node in all_nodes:
            if node == "end":
                continue
            if node not in graph or len(graph[node]) == 0:
                self.errors.append(f"Dead-end node '{node}' has no outgoing connections")
        
        # Check that 'end' is reachable from start
        if not self._can_reach_end(graph):
            self.errors.append("'end' is not reachable from start - graph is not closed")
    
    def _get_all_referenced_steps(self) -> Set[str]:
        """Get all step names referenced in connections."""
        steps = {self.saga.start}
        
        for conn in self.saga.connections:
            steps.add(conn.origin)
            
            if isinstance(conn, DirectedConnection):
                steps.add(conn.then.target)
            elif isinstance(conn, BranchingConnection):
                steps.add(conn.pass_target.target)
                steps.add(conn.fail_target.target)
        
        return steps
    
    def _get_all_nodes(self) -> Set[str]:
        """Get all nodes in the graph (origins + targets)."""
        return self._get_all_referenced_steps()
    
    def _build_graph(self) -> Dict[str, List[str]]:
        """Build adjacency list representation of the graph."""
        graph: Dict[str, List[str]] = {}
        
        for conn in self.saga.connections:
            if conn.origin not in graph:
                graph[conn.origin] = []
            
            if isinstance(conn, DirectedConnection):
                graph[conn.origin].append(conn.then.target)
            elif isinstance(conn, BranchingConnection):
                graph[conn.origin].append(conn.pass_target.target)
                graph[conn.origin].append(conn.fail_target.target)
        
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


def validate_saga(saga: SagaDefinition, steps_dir: Path) -> tuple[bool, List[str]]:
    """Validate a saga definition. Returns (is_valid, errors)."""
    validator = SagaValidator(saga, steps_dir)
    is_valid = validator.validate()
    return is_valid, validator.get_errors()
