#!/usr/bin/env python3
"""
Saga Executor - Executes saga workflows with step orchestration.
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple

try:
    from .saga_models import SagaDefinition, DirectedConnection, BranchingConnection, ConnectionTarget, NodeDefinition
except ImportError:
    from saga_models import SagaDefinition, DirectedConnection, BranchingConnection, ConnectionTarget, NodeDefinition


class TraversalTracker:
    """Tracks traversal counts for connections."""
    
    def __init__(self):
        self.counts: Dict[str, int] = {}
    
    def increment(self, origin: str, target: str) -> int:
        """Increment traversal count for a connection. Returns new count."""
        key = f"{origin}->{target}"
        self.counts[key] = self.counts.get(key, 0) + 1
        return self.counts[key]
    
    def get_count(self, origin: str, target: str) -> int:
        """Get current traversal count for a connection."""
        key = f"{origin}->{target}"
        return self.counts.get(key, 0)


class ExecutionLogger:
    """Logs saga execution to file."""
    
    def __init__(self, log_path: Path, depth: int = 0):
        self.log_path = log_path
        self.depth = depth
        
        if depth == 0:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.log_path, 'w') as f:
                f.write(f"=== Saga Execution Log ===\n")
                f.write(f"Started at: {datetime.now().isoformat()}\n\n")
    
    def log(self, message: str):
        """Write a log message."""
        timestamp = datetime.now().isoformat()
        indent = "  " * self.depth
        log_line = f"[{timestamp}] {indent}{message}\n"
        
        with open(self.log_path, 'a') as f:
            f.write(log_line)
        
        print(f"[Saga] {indent}{message}")
    
    def log_step_start(self, step_name: str, inputs: List[str]):
        """Log step execution start."""
        self.log(f"Executing step: {step_name}")
        if inputs:
            self.log(f"  Inputs: {', '.join(inputs)}")
    
    def log_step_result(self, step_name: str, exit_code: int):
        """Log step execution result."""
        status = "PASS" if exit_code == 0 else "FAIL"
        self.log(f"Step '{step_name}' completed: {status} (exit code: {exit_code})")
    
    def log_routing(self, origin: str, target: str, reason: str, traversal_count: int, limit: Optional[int]):
        """Log routing decision."""
        limit_str = f" (traversal: {traversal_count}/{limit})" if limit else f" (traversal: {traversal_count})"
        self.log(f"Routing: {origin} -> {target} [{reason}]{limit_str}")
    
    def log_traversal_limit_hit(self, origin: str, target: str, limit: int):
        """Log traversal limit exceeded."""
        self.log(f"ERROR: Traversal limit hit on {origin} -> {target} (limit: {limit})")
    
    def log_saga_result(self, success: bool, reason: str):
        """Log final saga result."""
        status = "SUCCESS" if success else "FAILURE"
        self.log(f"\n=== Saga {status} ===")
        self.log(f"Reason: {reason}")
        self.log(f"Ended at: {datetime.now().isoformat()}")


class SagaExecutor:
    """Executes a saga workflow."""
    
    def __init__(self, saga: SagaDefinition, steps_dir: Path, sagas_dir: Path, log_path: Path, depth: int = 0, logger: Optional['ExecutionLogger'] = None):
        self.saga = saga
        self.steps_dir = steps_dir
        self.sagas_dir = sagas_dir
        self.log_path = log_path
        self.depth = depth
        self.logger = logger if logger else ExecutionLogger(log_path, depth)
        self.tracker = TraversalTracker()
        self.connection_map = self._build_connection_map()
        self.final_outputs: List[str] = []
    
    def _build_connection_map(self) -> Dict[str, any]:
        """Build a map of node -> connection for quick lookup."""
        conn_map = {}
        for conn in self.saga.connections:
            conn_map[conn.node] = conn
        return conn_map
    
    def execute(self, initial_inputs: List[str]) -> Tuple[bool, List[str]]:
        """Execute the saga. Returns (success, final_outputs)."""
        self.logger.log(f"Starting saga: {self.saga.name}")
        self.logger.log(f"Initial inputs: {', '.join(initial_inputs) if initial_inputs else 'none'}")
        
        current_node = self.saga.start
        current_inputs = initial_inputs
        
        while current_node != "end":
            self.logger.log(f"\n--- Current node: {current_node} ---")
            
            exit_code, outputs = self._execute_node(current_node, current_inputs)
            
            self.logger.log_step_result(current_node, exit_code)
            
            next_node, limit_hit = self._route_to_next_node(current_node, exit_code)
            
            if limit_hit:
                self.logger.log_saga_result(False, "Traversal limit exceeded")
                return False, []
            
            if next_node is None:
                self.logger.log_saga_result(False, f"No connection found from node '{current_node}'")
                return False, []
            
            current_node = next_node
            current_inputs = outputs
        
        self.final_outputs = current_inputs
        self.logger.log_saga_result(True, "Reached end successfully")
        return True, self.final_outputs
    
    def _execute_node(self, node_name: str, inputs: List[str]) -> Tuple[int, List[str]]:
        """Execute a node (step or sub-saga). Returns (exit_code, outputs)."""
        if node_name not in self.saga.nodes:
            self.logger.log(f"ERROR: Node '{node_name}' not found in saga definition")
            return 1, []
        
        node_def = self.saga.nodes[node_name]
        
        if node_def.type == "step":
            return self._execute_step(node_name, node_def, inputs)
        elif node_def.type == "saga":
            return self._execute_subsaga(node_name, node_def, inputs)
        else:
            self.logger.log(f"ERROR: Unknown node type '{node_def.type}' for node '{node_name}'")
            return 1, []
    
    def _execute_step(self, node_name: str, node_def: NodeDefinition, inputs: List[str]) -> Tuple[int, List[str]]:
        """Execute a single step. Returns (exit_code, outputs)."""
        self.logger.log_step_start(node_name, inputs)
        
        step_def_path = self.steps_dir / node_def.reference / "step.json"
        
        cmd = [
            sys.executable,
            str(Path(__file__).parent / "devin_wrapper.py"),
            str(step_def_path)
        ] + inputs
        
        try:
            result = subprocess.run(
                cmd,
                check=False,
                capture_output=True,
                text=True,
                timeout=node_def.timeout
            )
            exit_code = result.returncode
            
            outputs = self._parse_outputs(node_def.reference, result.stdout)
            
            return exit_code, outputs
        
        except subprocess.TimeoutExpired:
            self.logger.log(f"ERROR: Step '{node_name}' timed out after {node_def.timeout} seconds")
            return 124, []
        
        except Exception as e:
            self.logger.log(f"ERROR executing step '{node_name}': {e}")
            return 1, []
    
    def _execute_subsaga(self, node_name: str, node_def: NodeDefinition, inputs: List[str]) -> Tuple[int, List[str]]:
        """Execute a sub-saga. Returns (exit_code, outputs)."""
        self.logger.log(f"Entering sub-saga: {node_name}")
        
        saga_path = Path(node_def.reference)
        if not saga_path.is_absolute():
            saga_path = self.sagas_dir / node_def.reference
        
        try:
            sub_saga_data = json.loads(saga_path.read_text())
            sub_saga = SagaDefinition.from_dict(sub_saga_data)
            
            sub_executor = SagaExecutor(
                sub_saga,
                self.steps_dir,
                self.sagas_dir,
                self.log_path,
                depth=self.depth + 1,
                logger=self.logger
            )
            
            start_time = datetime.now()
            success, outputs = sub_executor.execute(inputs)
            elapsed = (datetime.now() - start_time).total_seconds()
            
            if node_def.timeout and elapsed > node_def.timeout:
                self.logger.log(f"WARNING: Sub-saga '{node_name}' exceeded timeout ({elapsed:.1f}s > {node_def.timeout}s)")
            
            exit_code = 0 if success else 1
            
            self.logger.log(f"Exiting sub-saga: {node_name} (exit code: {exit_code})")
            
            return exit_code, outputs
        
        except Exception as e:
            self.logger.log(f"ERROR executing sub-saga '{node_name}': {e}")
            return 1, []
    
    def _parse_outputs(self, step_name: str, stdout: str) -> List[str]:
        """Parse outputs from step execution."""
        outputs = []
        
        output_file = self.steps_dir / step_name / "outputs.json"
        if output_file.exists():
            try:
                data = json.loads(output_file.read_text())
                outputs = data.get("outputs", [])
                self.logger.log(f"  Outputs: {', '.join(outputs) if outputs else 'none'}")
            except Exception as e:
                self.logger.log(f"  Warning: Could not parse outputs.json: {e}")
        
        return outputs
    
    def _route_to_next_node(self, current_node: str, exit_code: int) -> Tuple[Optional[str], bool]:
        """
        Determine next node based on current node and exit code.
        Returns (next_node, limit_hit).
        """
        if current_node not in self.connection_map:
            return None, False
        
        conn = self.connection_map[current_node]
        
        if isinstance(conn, DirectedConnection):
            target = conn.then.target
            limit = conn.then.traversal_limit
            
            count = self.tracker.increment(current_node, target)
            
            if limit is not None and count > limit:
                self.logger.log_traversal_limit_hit(current_node, target, limit)
                return None, True
            
            self.logger.log_routing(current_node, target, "then", count, limit)
            return target, False
        
        elif isinstance(conn, BranchingConnection):
            if exit_code == 0:
                target_obj = conn.pass_target
                reason = "pass"
            else:
                target_obj = conn.fail_target
                reason = "fail"
            
            target = target_obj.target
            limit = target_obj.traversal_limit
            
            count = self.tracker.increment(current_node, target)
            
            if limit is not None and count > limit:
                self.logger.log_traversal_limit_hit(current_node, target, limit)
                return None, True
            
            self.logger.log_routing(current_node, target, reason, count, limit)
            return target, False
        
        return None, False


def execute_saga(saga: SagaDefinition, steps_dir: Path, sagas_dir: Path, log_path: Path, initial_inputs: List[str]) -> Tuple[bool, List[str]]:
    """Execute a saga. Returns (success, final_outputs)."""
    executor = SagaExecutor(saga, steps_dir, sagas_dir, log_path)
    return executor.execute(initial_inputs)
