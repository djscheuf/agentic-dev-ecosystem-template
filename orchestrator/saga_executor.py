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
    from .saga_models import SagaDefinition, DirectedConnection, BranchingConnection, ConnectionTarget
except ImportError:
    from saga_models import SagaDefinition, DirectedConnection, BranchingConnection, ConnectionTarget


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
    
    def __init__(self, log_path: Path):
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.log_path, 'w') as f:
            f.write(f"=== Saga Execution Log ===\n")
            f.write(f"Started at: {datetime.now().isoformat()}\n\n")
    
    def log(self, message: str):
        """Write a log message."""
        timestamp = datetime.now().isoformat()
        log_line = f"[{timestamp}] {message}\n"
        
        with open(self.log_path, 'a') as f:
            f.write(log_line)
        
        print(f"[Saga] {message}")
    
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
    
    def __init__(self, saga: SagaDefinition, steps_dir: Path, log_path: Path):
        self.saga = saga
        self.steps_dir = steps_dir
        self.logger = ExecutionLogger(log_path)
        self.tracker = TraversalTracker()
        self.connection_map = self._build_connection_map()
    
    def _build_connection_map(self) -> Dict[str, any]:
        """Build a map of origin -> connection for quick lookup."""
        conn_map = {}
        for conn in self.saga.connections:
            conn_map[conn.origin] = conn
        return conn_map
    
    def execute(self, initial_inputs: List[str]) -> bool:
        """Execute the saga. Returns True if successful, False otherwise."""
        self.logger.log(f"Starting saga: {self.saga.name}")
        self.logger.log(f"Initial inputs: {', '.join(initial_inputs) if initial_inputs else 'none'}")
        
        current_step = self.saga.start
        current_inputs = initial_inputs
        
        while current_step != "end":
            self.logger.log(f"\n--- Current step: {current_step} ---")
            
            exit_code, outputs = self._execute_step(current_step, current_inputs)
            
            self.logger.log_step_result(current_step, exit_code)
            
            next_step, limit_hit = self._route_to_next_step(current_step, exit_code)
            
            if limit_hit:
                self.logger.log_saga_result(False, "Traversal limit exceeded")
                return False
            
            if next_step is None:
                self.logger.log_saga_result(False, f"No connection found from step '{current_step}'")
                return False
            
            current_step = next_step
            current_inputs = outputs
        
        self.logger.log_saga_result(True, "Reached end successfully")
        return True
    
    def _execute_step(self, step_name: str, inputs: List[str]) -> Tuple[int, List[str]]:
        """Execute a single step. Returns (exit_code, outputs)."""
        self.logger.log_step_start(step_name, inputs)
        
        step_def_path = self.steps_dir / step_name / "step.json"
        
        cmd = [
            sys.executable,
            str(Path(__file__).parent / "devin_wrapper.py"),
            str(step_def_path)
        ] + inputs
        
        try:
            result = subprocess.run(cmd, check=False, capture_output=True, text=True)
            exit_code = result.returncode
            
            outputs = self._parse_outputs(step_name, result.stdout)
            
            return exit_code, outputs
            
        except Exception as e:
            self.logger.log(f"ERROR executing step '{step_name}': {e}")
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
    
    def _route_to_next_step(self, current_step: str, exit_code: int) -> Tuple[Optional[str], bool]:
        """
        Determine next step based on current step and exit code.
        Returns (next_step, limit_hit).
        """
        if current_step not in self.connection_map:
            return None, False
        
        conn = self.connection_map[current_step]
        
        if isinstance(conn, DirectedConnection):
            target = conn.then.target
            limit = conn.then.traversal_limit
            
            count = self.tracker.increment(current_step, target)
            
            if limit is not None and count > limit:
                self.logger.log_traversal_limit_hit(current_step, target, limit)
                return None, True
            
            self.logger.log_routing(current_step, target, "then", count, limit)
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
            
            count = self.tracker.increment(current_step, target)
            
            if limit is not None and count > limit:
                self.logger.log_traversal_limit_hit(current_step, target, limit)
                return None, True
            
            self.logger.log_routing(current_step, target, reason, count, limit)
            return target, False
        
        return None, False


def execute_saga(saga: SagaDefinition, steps_dir: Path, log_path: Path, initial_inputs: List[str]) -> bool:
    """Execute a saga. Returns True if successful."""
    executor = SagaExecutor(saga, steps_dir, log_path)
    return executor.execute(initial_inputs)
