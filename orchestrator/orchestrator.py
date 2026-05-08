#!/usr/bin/env python3
"""
Orchestrator - Manages step execution with instrumentation and state management.

The Orchestrator handles:
- Loading step definitions
- Enriching prompts
- Invoking agent wrappers
- Managing session state
- Running verification scripts
- Enforcing timeouts
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, Optional, Tuple, Any

try:
    from .devin_wrapper import DevinWrapper
    from .models import EnrichmentDictionary
except ImportError:
    from devin_wrapper import DevinWrapper
    from models import EnrichmentDictionary


class Orchestrator:
    """Orchestrates step execution with state management and verification."""
    
    def __init__(self, logging_dir: Optional[Path] = None):
        """Initialize the orchestrator.
        
        Args:
            logging_dir: Optional directory for writing feedback and stderr files.
                        If None, files are written to step directories.
        """
        self.wrapper = DevinWrapper()
        self.logging_dir = logging_dir
    
    def invoke_step(
        self,
        step_id: str,
        steps_dir: Path,
        prompt: str,
        enrichment: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
        session_id: Optional[str] = None,
        step_name: Optional[str] = None,
        saga_id: Optional[str] = None,
        node_name: Optional[str] = None,
        attempt_number: Optional[int] = None
    ) -> Tuple[int, Optional[str]]:
        """Invoke a step with full orchestration.
        
        Args:
            step_id: The step identifier
            steps_dir: Path to the steps directory
            prompt: The prompt to execute
            enrichment: Optional enrichment dictionary for variable substitution
            timeout: Optional timeout in seconds
            session_id: Optional session ID to resume
            step_name: Optional step name for logging (used as prefix for feedback/stderr files)
            saga_id: Optional saga instance identifier for retry logic
            node_name: Optional node name for retry logic
            attempt_number: Optional attempt number for retry logic
        
        Returns:
            Tuple[int, Optional[str]]: (exit_code, session_id)
                - exit_code: 0 for success, non-zero for failure
                - session_id: The session ID (new or resumed)
        
        Raises:
            FileNotFoundError: If step definition not found
        """
        # Load step definition
        step_dir = Path(steps_dir) / step_id
        step_file = step_dir / "step.json"
        
        if not step_file.exists():
            raise FileNotFoundError(f"Step definition not found: {step_file}")
        
        step_def = json.loads(step_file.read_text())
        
        # Check if resuming with verification errors
        verification_errors = enrichment.get('verification_errors') if enrichment else None
        print(f"[Orchestrator] invoke_step: session_id={session_id}, has_enrichment={enrichment is not None}, has_verification_errors={verification_errors is not None}")
        
        # Build the prompt/message to send
        if session_id and verification_errors:
            # Resuming session: send verification errors as continuation message
            execution_prompt = f"Verification failed. Please review and fix the following errors:\n\n{verification_errors}"
            print(f"[Orchestrator] Resuming session with verification errors ({len(verification_errors)} bytes)")
        else:
            # New session or resuming without errors: use normal prompt
            enriched_prompt = prompt
            if enrichment:
                enriched_prompt = self._enrich_prompt(prompt, enrichment)
            execution_prompt = enriched_prompt
            if session_id:
                print(f"[Orchestrator] Resuming session without verification errors")
        
        # Get agent config path
        agent_config = step_def.get("agent_config", ".devin/agent-config.json")
        if not Path(agent_config).is_absolute():
            agent_config = str(step_dir / agent_config)
        
        # Get model
        model = step_def.get("model", "gpt-4")
        
        # Invoke wrapper
        try:
            output, returned_session_id = self._invoke_wrapper(
                prompt=execution_prompt,
                model=model,
                agent_config=agent_config,
                timeout=timeout,
                session_id=session_id
            )
        except Exception as e:
            print(f"[Orchestrator] ERROR: Failed to invoke wrapper: {e}")
            return 1, session_id
        
        # Write session state files
        print(f"[Orchestrator] Writing session state: returned_session_id={returned_session_id}")
        if saga_id and node_name and attempt_number:
            # Write to attempt-specific directory for retry logic
            attempt_dir = self._create_attempt_directory(saga_id, node_name, attempt_number)
            self._write_attempt_input(attempt_dir, execution_prompt)
            self._write_attempt_output(attempt_dir, output)
            self._log_state_files_written(node_name, attempt_number, ["input.txt", "output.txt"], str(attempt_dir))
        else:
            # Legacy behavior: write to step directory or logging directory
            self._write_session_state(step_dir, output, returned_session_id, step_name or step_id)
        
        # Run verification script if specified
        verify_script = step_def.get("verify")
        verification_output = ""
        if verify_script:
            exit_code, verification_output = self._run_verification(step_dir, verify_script, step_name or step_id)
        else:
            exit_code = 0
        
        # Write verification output if using saga context
        if saga_id and node_name and attempt_number:
            attempt_dir = Path.cwd() / ".sagas" / saga_id / node_name / f"attempt_{attempt_number}"
            self._write_attempt_verification(attempt_dir, verification_output)
        
        return exit_code, returned_session_id
    
    def _enrich_prompt(self, prompt: str, enrichment: Dict[str, Any]) -> str:
        """Enrich prompt with variables from enrichment dictionary.
        
        Args:
            prompt: The prompt template
            enrichment: Dictionary of variables to substitute
        
        Returns:
            str: The enriched prompt
        """
        enriched = prompt
        for key, value in enrichment.items():
            placeholder = f"{{{{{key}}}}}"
            enriched = enriched.replace(placeholder, str(value))
        return enriched
    
    def _invoke_wrapper(
        self,
        prompt: str,
        model: str,
        agent_config: str,
        timeout: Optional[int] = None,
        session_id: Optional[str] = None
    ) -> Tuple[str, Optional[str]]:
        """Invoke the agent wrapper.
        
        Args:
            prompt: The prompt to execute
            model: The model to use
            agent_config: Path to agent configuration
            timeout: Optional timeout in seconds
            session_id: Optional session ID to resume
        
        Returns:
            Tuple[str, Optional[str]]: (output, session_id)
        """
        return self.wrapper.execute_prompt(
            prompt=prompt,
            agent_config=agent_config,
            timeout=timeout,
            session_id=session_id
        )
    
    def _write_session_state(
        self,
        step_dir: Path,
        output: str,
        session_id: Optional[str],
        step_name: str
    ) -> None:
        """Write session state files.
        
        Args:
            step_dir: The step directory
            output: The wrapper output (stdout from agent)
            session_id: The session ID
            step_name: The step name for file prefixes
        """
        # Determine output directory
        if self.logging_dir:
            output_dir = self.logging_dir
        else:
            # Fallback to .process/{step}/ to avoid writing to step directory
            output_dir = Path.cwd() / ".process" / step_name
            output_dir.mkdir(parents=True, exist_ok=True)
        
        # Write session ID if available
        if session_id:
            session_file = output_dir / "session_id.txt"
            session_file.write_text(session_id)
        
        # Write agent stdout
        if self.logging_dir:
            stdout_file = output_dir / f"{step_name}_stdout.txt"
        else:
            stdout_file = output_dir / "stdout.txt"
        stdout_file.write_text(output)
    
    def _run_verification(
        self,
        step_dir: Path,
        verify_script: str,
        step_name: str
    ) -> Tuple[int, str]:
        """Run verification script.
        
        Args:
            step_dir: The step directory
            verify_script: Path to verification script (relative or absolute)
            step_name: The step name for file prefixes
        
        Returns:
            Tuple[int, str]: (exit_code, verification_output)
                - exit_code: Exit code from verification script
                - verification_output: stderr from verification script (feedback)
        """
        # Resolve script path
        script_path = Path(verify_script)
        if not script_path.is_absolute():
            script_path = step_dir / verify_script
        
        script_path = script_path.resolve()
        
        if not script_path.exists():
            print(f"[Orchestrator] ERROR: Verification script not found: {script_path}")
            return 1, ""
        
        try:
            result = subprocess.run(
                ["bash", str(script_path)],
                check=False,
                capture_output=True,
                text=True
            )
            
            verification_output = result.stderr if result.stderr else ""
            
            # Write stderr if present
            if result.stderr:
                if self.logging_dir:
                    stderr_file = self.logging_dir / f"{step_name}_stderr.txt"
                else:
                    # Fallback to .process/{step}/ to avoid writing to step directory
                    output_dir = Path.cwd() / ".process" / step_name
                    output_dir.mkdir(parents=True, exist_ok=True)
                    stderr_file = output_dir / "stderr.txt"
                stderr_file.write_text(result.stderr)
            
            return result.returncode, verification_output
        except Exception as e:
            print(f"[Orchestrator] ERROR: Failed to run verification: {e}")
            return 1, ""
    
    def _create_attempt_directory(
        self,
        saga_id: str,
        node_name: str,
        attempt_number: int
    ) -> Path:
        """Create attempt directory for a node.
        
        Args:
            saga_id: The saga instance identifier
            node_name: The name of the node being executed
            attempt_number: The attempt number (1 for first, 2+ for retries)
        
        Returns:
            Path: The created attempt directory
        """
        attempt_dir = Path.cwd() / ".sagas" / saga_id / node_name / f"attempt_{attempt_number}"
        attempt_dir.mkdir(parents=True, exist_ok=True)
        return attempt_dir
    
    def _write_attempt_input(self, attempt_dir: Path, prompt: str) -> None:
        """Write input prompt to attempt directory.
        
        Args:
            attempt_dir: The attempt directory
            prompt: The prompt text to write
        """
        input_file = attempt_dir / "input.txt"
        input_file.write_text(prompt)
    
    def _write_attempt_output(self, attempt_dir: Path, output: str) -> None:
        """Write agent output to attempt directory.
        
        Args:
            attempt_dir: The attempt directory
            output: The agent output text to write
        """
        output_file = attempt_dir / "output.txt"
        output_file.write_text(output)
    
    def _write_attempt_verification(self, attempt_dir: Path, verification: str) -> None:
        """Write verification feedback to attempt directory.
        
        Args:
            attempt_dir: The attempt directory
            verification: The verification feedback text to write (empty if passed)
        """
        verification_file = attempt_dir / "verification.txt"
        verification_file.write_text(verification)
    
    def _determine_next_attempt_number(self, saga_id: str, node_name: str) -> int:
        """Determine the next attempt number for a node.
        
        Scans existing attempt directories and returns the next sequential number.
        
        Args:
            saga_id: The saga instance identifier
            node_name: The name of the node
        
        Returns:
            int: The next attempt number (1 if no attempts exist, N+1 if N attempts exist)
        """
        node_dir = Path.cwd() / ".sagas" / saga_id / node_name
        
        if not node_dir.exists():
            return 1
        
        attempt_dirs = [d for d in node_dir.iterdir() if d.is_dir() and d.name.startswith("attempt_")]
        
        if not attempt_dirs:
            return 1
        
        attempt_numbers = []
        for attempt_dir in attempt_dirs:
            try:
                attempt_num = int(attempt_dir.name.split("_")[1])
                attempt_numbers.append(attempt_num)
            except (ValueError, IndexError):
                continue
        
        if not attempt_numbers:
            return 1
        
        return max(attempt_numbers) + 1
    
    def _compose_accumulated_prompt(self, saga_id: str, node_name: str) -> str:
        """Compose accumulated prompt from all previous attempts.
        
        Loads input, output, and verification files from all previous attempts
        and composes them into a single accumulated prompt.
        
        Args:
            saga_id: The saga instance identifier
            node_name: The name of the node
        
        Returns:
            str: The accumulated prompt containing all previous attempts' context
        """
        node_dir = Path.cwd() / ".sagas" / saga_id / node_name
        
        if not node_dir.exists():
            return ""
        
        attempt_dirs = sorted(
            [d for d in node_dir.iterdir() if d.is_dir() and d.name.startswith("attempt_")],
            key=lambda d: int(d.name.split("_")[1])
        )
        
        accumulated_parts = []
        
        for attempt_dir in attempt_dirs:
            input_file = attempt_dir / "input.txt"
            output_file = attempt_dir / "output.txt"
            verification_file = attempt_dir / "verification.txt"
            
            if input_file.exists():
                accumulated_parts.append(input_file.read_text())
            
            if output_file.exists():
                accumulated_parts.append(output_file.read_text())
            
            if verification_file.exists():
                verification_content = verification_file.read_text()
                if verification_content:
                    accumulated_parts.append(verification_content)
        
        return "\n\n".join(accumulated_parts)
    
    def _log_attempt_number_determined(self, node_name: str, attempt_number: int, existing_attempts: int) -> None:
        """Log attempt_number_determined event.
        
        Args:
            node_name: Name of the node being retried
            attempt_number: The attempt number being executed
            existing_attempts: Count of previously completed attempts
        """
        print(f"[Orchestrator] EVENT: attempt_number_determined - node={node_name}, attempt={attempt_number}, existing={existing_attempts}")
    
    def _log_accumulated_prompt_composed(self, node_name: str, attempt_number: int, prompt_size: int, previous_attempts: int) -> None:
        """Log accumulated_prompt_composed event.
        
        Args:
            node_name: Name of the node
            attempt_number: Current attempt number
            prompt_size: Size in bytes of the accumulated prompt
            previous_attempts: Number of previous attempts included in composition
        """
        print(f"[Orchestrator] EVENT: accumulated_prompt_composed - node={node_name}, attempt={attempt_number}, size={prompt_size}, previous={previous_attempts}")
    
    def _log_state_files_written(self, node_name: str, attempt_number: int, files_written: list, directory_path: str) -> None:
        """Log state_files_written event.
        
        Args:
            node_name: Name of the node
            attempt_number: Attempt number
            files_written: List of files written (input.txt, output.txt, verification.txt)
            directory_path: Full path to attempt directory
        """
        files_str = ", ".join(files_written)
        print(f"[Orchestrator] EVENT: state_files_written - node={node_name}, attempt={attempt_number}, files=[{files_str}], path={directory_path}")
    
    def _log_retry_limit_enforced(self, node_name: str, traversal_limit: int, attempts_made: int) -> None:
        """Log retry_limit_enforced event.
        
        Args:
            node_name: Name of the node
            traversal_limit: The limit that was exceeded
            attempts_made: Number of attempts made before limit
        """
        print(f"[Orchestrator] EVENT: retry_limit_enforced - node={node_name}, limit={traversal_limit}, attempts={attempts_made}")
