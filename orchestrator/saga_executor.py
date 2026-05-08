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
    from .models import SagaDefinition, DirectedConnection, BranchingConnection, ConnectionTarget, NodeDefinition, StateEntry, SubSagaEntry, generate_saga_id, EnrichmentDictionary
    from .orchestrator import Orchestrator
    from .saga_state import SagaStateManager
except ImportError:
    from models import SagaDefinition, DirectedConnection, BranchingConnection, ConnectionTarget, NodeDefinition, StateEntry, SubSagaEntry, generate_saga_id, EnrichmentDictionary
    import sys
    import os
    # Import orchestrator module from the same directory
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import orchestrator as orch_module
    Orchestrator = orch_module.Orchestrator
    from saga_state import SagaStateManager


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
    
    def __init__(self, saga: SagaDefinition, steps_dir: Path, sagas_dir: Path, log_path: Path, depth: int = 0, logger: Optional['ExecutionLogger'] = None, saga_path: Optional[str] = None, original_input: Optional[str] = None, orchestrator: Optional[Orchestrator] = None, keep_attempt_logs: bool = False):
        self.saga = saga
        self.steps_dir = steps_dir
        self.sagas_dir = sagas_dir
        self.log_path = log_path
        self.depth = depth
        self.logger = logger if logger else ExecutionLogger(log_path, depth)
        self.tracker = TraversalTracker()
        self.connection_map = self._build_connection_map()
        self.final_outputs: List[str] = []
        self.keep_attempt_logs = keep_attempt_logs
        
        self.state_manager: Optional[SagaStateManager] = None
        if depth == 0 and saga_path is not None:
            saga_id = generate_saga_id(saga.name, original_input or "")
            self.state_manager = SagaStateManager(saga_id)
            self.state_manager.initialize(saga_path, original_input or "", saga.start)
            
            enrichment = EnrichmentDictionary(
                saga_id=saga_id,
                state_storage_location=str(self.state_manager.saga_dir),
                initial_prompt_path=original_input or "",
                custom_variables=saga.enrichment
            )
            self.state_manager.save_enrichment(enrichment)
        
        # Initialize orchestrator with logging directory or use provided one
        if orchestrator is not None:
            self.orchestrator = orchestrator
        else:
            logging_dir = self.state_manager.saga_dir if self.state_manager else None
            self.orchestrator = Orchestrator(logging_dir=logging_dir)
    
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
        node_attempt_counts: Dict[str, int] = {}  # Track attempt number per node
        
        while current_node != "end":
            self.logger.log(f"\n--- Current node: {current_node} ---")
            
            # Increment attempt count for this node
            node_attempt_counts[current_node] = node_attempt_counts.get(current_node, 0) + 1
            attempt_number = node_attempt_counts[current_node]
            
            self._record_step_start(current_node)
            exit_code, outputs, stderr = self._execute_node(current_node, current_inputs, attempt_number)
            self._record_step_completion(current_node, exit_code)
            
            self.logger.log_step_result(current_node, exit_code)
            
            next_node, limit_hit = self._route_to_next_node(current_node, exit_code, stderr)
            
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
    
    def _record_step_start(self, node_name: str) -> None:
        """Record step start in state manager."""
        if self.state_manager is None:
            return
        
        entry = StateEntry(
            node=node_name,
            status="starting",
            started_at=datetime.now().isoformat()
        )
        self.state_manager.append_state_entry(entry)
    
    def _record_step_completion(self, node_name: str, exit_code: int, session_id: Optional[str] = None) -> None:
        """Record step completion in state manager."""
        if self.state_manager is None:
            return
        
        updates = {
            "status": "completed" if exit_code == 0 else "failed",
            "completed_at": datetime.now().isoformat(),
            "exit_code": exit_code,
            "session_id": session_id
        }
        self.state_manager.update_last_state_entry(updates)
    
    def _record_subsaga_start(self, node_name: str, child_saga_id: str) -> None:
        """Record sub-saga invocation in state manager."""
        if self.state_manager is None:
            return
        
        entry = SubSagaEntry(
            node=node_name,
            saga_id=child_saga_id,
            status="in_progress",
            started_at=datetime.now().isoformat()
        )
        self.state_manager.append_subsaga_entry(entry)
    
    def _execute_node(self, node_name: str, inputs: List[str], attempt_number: int = 1) -> Tuple[int, List[str], str]:
        """Execute a node (step or sub-saga). Returns (exit_code, outputs, stderr)."""
        if node_name not in self.saga.nodes:
            self.logger.log(f"ERROR: Node '{node_name}' not found in saga definition")
            return 1, [], ""
        
        node_def = self.saga.nodes[node_name]
        
        if node_def.type == "step":
            return self._execute_step(node_name, node_def, inputs, attempt_number)
        elif node_def.type == "saga":
            return self._execute_subsaga(node_name, node_def, inputs)
        else:
            self.logger.log(f"ERROR: Unknown node type '{node_def.type}' for node '{node_name}'")
            return 1, [], ""
    
    def _execute_step(self, node_name: str, node_def: NodeDefinition, inputs: List[str], attempt_number: int = 1) -> Tuple[int, List[str], str]:
        """Execute a single step. Returns (exit_code, outputs, stderr)."""
        self.logger.log_step_start(node_name, inputs)
        
        step_dir = self.steps_dir / node_def.reference
        step_def_path = step_dir / "step.json"
        
        try:
            # Load step definition to get prompt
            step_def_data = json.loads(step_def_path.read_text())
            prompt_value = step_def_data.get("prompt", "")
            
            # Resolve relative prompt paths to actual content
            prompt = prompt_value
            if prompt_value and not prompt_value.startswith(("{{", "SO THAT", "AS A", "I WANT")):
                # Likely a file path, try to resolve it
                prompt_path = Path(prompt_value)
                if not prompt_path.is_absolute():
                    prompt_path = step_dir / prompt_value
                
                if prompt_path.exists():
                    prompt = prompt_path.read_text()
            
            # Build enrichment dictionary from inputs
            enrichment = self._build_enrichment(node_def.reference, inputs)
            
            # Determine saga context for retry logic
            saga_id = None
            execution_prompt = prompt
            
            if self.state_manager:
                saga_id = self.state_manager.saga_id
                
                # If this is a retry (attempt_number > 1), compose accumulated prompt
                if attempt_number > 1:
                    accumulated_prompt = self.orchestrator._compose_accumulated_prompt(saga_id, node_name)
                    
                    if accumulated_prompt:
                        execution_prompt = accumulated_prompt
                        previous_attempts = attempt_number - 1
                        self.logger.log(f"  Retry detected: attempt {attempt_number}, composing accumulated prompt from {previous_attempts} previous attempt(s)")
                        self.orchestrator._log_attempt_number_determined(node_name, attempt_number, previous_attempts)
                        self.orchestrator._log_accumulated_prompt_composed(node_name, attempt_number, len(execution_prompt), previous_attempts)
            
            # Invoke step through orchestrator
            exit_code, returned_session_id, verification_output = self.orchestrator.invoke_step(
                step_id=node_def.reference,
                steps_dir=self.steps_dir,
                prompt=execution_prompt,
                enrichment=enrichment,
                timeout=node_def.timeout,
                step_name=node_name,
                saga_id=saga_id,
                node_name=node_name,
                attempt_number=attempt_number
            )
            
            # Update enrichment with verification output if step succeeded
            if exit_code == 0 and verification_output and self.state_manager:
                try:
                    persisted_enrichment = self.state_manager.load_enrichment()
                    if persisted_enrichment:
                        persisted_enrichment.previous_step_output = verification_output.strip()
                        self.state_manager.save_enrichment(persisted_enrichment)
                        self.logger.log(f"  Updated enrichment with previous_step_output from verification")
                except Exception as e:
                    self.logger.log(f"  Warning: Could not update enrichment with verification output: {e}")
            
            # Parse outputs
            outputs = self._parse_outputs(node_def.reference, "")
            
            return exit_code, outputs, ""
        
        except Exception as e:
            self.logger.log(f"ERROR executing step '{node_name}': {e}")
            import traceback
            self.logger.log(f"  Traceback: {traceback.format_exc()}")
            return 1, [], ""
    
    def _execute_subsaga(self, node_name: str, node_def: NodeDefinition, inputs: List[str]) -> Tuple[int, List[str], str]:
        """Execute a sub-saga. Returns (exit_code, outputs, stderr)."""
        self.logger.log(f"Entering sub-saga: {node_name}")
        
        saga_path = Path(node_def.reference)
        if not saga_path.is_absolute():
            saga_path = self.sagas_dir / node_def.reference
        
        try:
            sub_saga_data = json.loads(saga_path.read_text())
            sub_saga = SagaDefinition.from_dict(sub_saga_data)
            
            saga_path_abs = str(saga_path.resolve())
            sub_executor = SagaExecutor(
                sub_saga,
                self.steps_dir,
                self.sagas_dir,
                self.log_path,
                depth=self.depth + 1,
                logger=self.logger,
                saga_path=saga_path_abs,
                original_input="",
                orchestrator=self.orchestrator,
                keep_attempt_logs=self.keep_attempt_logs
            )
            
            # Record sub-saga invocation in parent state manager
            if sub_executor.state_manager is not None:
                child_saga_id = sub_executor.state_manager.saga_id
                self._record_subsaga_start(node_name, child_saga_id)
            
            start_time = datetime.now()
            success, outputs = sub_executor.execute(inputs)
            elapsed = (datetime.now() - start_time).total_seconds()
            
            if node_def.timeout and elapsed > node_def.timeout:
                self.logger.log(f"WARNING: Sub-saga '{node_name}' exceeded timeout ({elapsed:.1f}s > {node_def.timeout}s)")
            
            exit_code = 0 if success else 1
            
            self.logger.log(f"Exiting sub-saga: {node_name} (exit code: {exit_code})")
            
            # Sub-sagas don't have stderr (they're composed of steps)
            return exit_code, outputs, ""
        
        except Exception as e:
            self.logger.log(f"ERROR executing sub-saga '{node_name}': {e}")
            return 1, [], ""
    
    def _build_enrichment(self, step_id: str, inputs: List[str]) -> Dict[str, any]:
        """Build enrichment dictionary for step execution.
        
        Args:
            step_id: The step identifier
            inputs: List of input values from previous step
        
        Returns:
            Dict with enrichment variables
        """
        enrichment = {}
        
        # Load persisted enrichment from state manager if available
        if self.state_manager:
            try:
                persisted_enrichment = self.state_manager.load_enrichment()
                if persisted_enrichment:
                    # Convert EnrichmentDictionary to dict
                    enrichment = persisted_enrichment.to_dict()
            except Exception as e:
                self.logger.log(f"  Warning: Could not load persisted enrichment: {e}")
        
        # Add inputs as enrichment variables (override if already present)
        for i, input_val in enumerate(inputs):
            enrichment[f"input_{i}"] = input_val
        
        return enrichment
    
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
        
        # Note: stderr prepending for fail path happens in routing logic
        # This keeps _parse_outputs focused on normal output parsing
        
        return outputs
    
    def _route_to_next_node(self, current_node: str, exit_code: int, stderr: str) -> Tuple[Optional[str], bool]:
        """
        Determine next node based on current node and exit code.
        Returns (next_node, limit_hit).
        
        Routing rules:
        - Directed connection (then only):
          - Exit 0: Follow then path
          - Exit 1: Saga fails (return None)
          - Exit 2: Loop back to current node with stderr feedback
        
        - Branching connection (pass/fail):
          - Exit 0: Follow pass path
          - Exit 1 or 2: Follow fail path with stderr
        """
        if current_node not in self.connection_map:
            return None, False
        
        conn = self.connection_map[current_node]
        
        if isinstance(conn, DirectedConnection):
            if exit_code == 0:
                # Success - follow then path
                target = conn.then.target
                limit = conn.then.traversal_limit
                
                count = self.tracker.increment(current_node, target)
                
                if limit is not None and count >= limit:
                    self.logger.log_traversal_limit_hit(current_node, target, limit)
                    return None, True
                
                self.logger.log_routing(current_node, target, "then", count, limit)
                
                # Clean up session files on success (unless debugging)
                if not self.keep_attempt_logs:
                    self._cleanup_session_files(current_node)
                
                return target, False
            
            elif exit_code == 1:
                # Hard failure with no fail path - saga fails
                self.logger.log(f"Step '{current_node}' failed (exit 1) with no fail path defined")
                return None, False
            
            elif exit_code == 2:
                # Self-correction needed - loop back to same node
                target = current_node
                count = self.tracker.increment(current_node, target)
                
                # Check traversal limit on the 'then' connection
                limit = conn.max_retries
                if limit is not None and count > limit:
                    self.logger.log(f"Self-correction limit exceeded for '{current_node}' (limit: {limit})")
                    return None, True
                
                self.logger.log(f"Self-correction needed for '{current_node}' (attempt {count})")
                
                # Prepare feedback for next iteration
                self._prepare_self_correction_feedback(current_node, stderr)
                
                return target, False
            
            else:
                # Unknown exit code - treat as hard failure
                self.logger.log(f"Step '{current_node}' returned unknown exit code {exit_code}")
                return None, False
        
        elif isinstance(conn, BranchingConnection):
            if exit_code == 0:
                # Success - follow pass path
                target_obj = conn.pass_target
                reason = "pass"
                
                # Clean up session files on success (unless debugging)
                if not self.keep_attempt_logs:
                    self._cleanup_session_files(current_node)
            else:
                # Failure (exit 1 or 2) - follow fail path
                target_obj = conn.fail_target
                reason = "fail"
                
                # Prepend stderr to outputs for fail path
                if stderr:
                    self._prepare_fail_path_stderr(current_node, stderr)
            
            target = target_obj.target
            limit = target_obj.traversal_limit
            
            count = self.tracker.increment(current_node, target)
            
            if limit is not None and count > limit:
                self.logger.log_traversal_limit_hit(current_node, target, limit)
                return None, True
            
            self.logger.log_routing(current_node, target, reason, count, limit)
            return target, False
        
        return None, False
    
    def _prepare_self_correction_feedback(self, node_name: str, stderr: str):
        """Prepare feedback input for self-correction loop."""
        if node_name not in self.saga.nodes:
            return
        
        node_def = self.saga.nodes[node_name]
        if node_def.type != "step":
            return
        
        # Orchestrator already wrote stderr to saga state dir
        # Just log that feedback is available for self-correction
        self.logger.log(f"  Prepared self-correction feedback for '{node_name}'")
        if self.state_manager:
            stderr_file = self.state_manager.saga_dir / f"{node_name}_stderr.txt"
            self.logger.log(f"  Stderr available at: {stderr_file}")
    
    def _prepare_fail_path_stderr(self, node_name: str, stderr: str):
        """Log that stderr will be available for fail path."""
        self.logger.log(f"  Verification error will be available to fail path")
    
    def _cleanup_session_files(self, node_name: str):
        """Clean up session files after successful completion."""
        if node_name not in self.saga.nodes:
            return
        
        node_def = self.saga.nodes[node_name]
        if node_def.type != "step":
            return
        
        # Remove session tracking files
        if self.state_manager:
            # Clean up from saga state directory
            for suffix in ["stdout.txt", "stderr.txt"]:
                file_path = self.state_manager.saga_dir / f"{node_name}_{suffix}"
                if file_path.exists():
                    file_path.unlink()
                    self.logger.log(f"  Cleaned up {node_name}_{suffix}")
        else:
            # Clean up from .process/{step}/ directory
            process_dir = Path.cwd() / ".process" / node_name
            if process_dir.exists():
                for file in ["stdout.txt", "stderr.txt", "session_id.txt"]:
                    file_path = process_dir / file
                    if file_path.exists():
                        file_path.unlink()
                        self.logger.log(f"  Cleaned up {file}")


def execute_saga(saga: SagaDefinition, steps_dir: Path, sagas_dir: Path, log_path: Path, initial_inputs: List[str], saga_path: Optional[str] = None, original_input: Optional[str] = None, keep_attempt_logs: bool = False) -> Tuple[bool, List[str]]:
    """Execute a saga. Returns (success, final_outputs)."""
    executor = SagaExecutor(saga, steps_dir, sagas_dir, log_path, saga_path=saga_path, original_input=original_input, keep_attempt_logs=keep_attempt_logs)
    return executor.execute(initial_inputs)
