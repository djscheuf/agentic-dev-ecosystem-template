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
    from .enrichment import EnrichmentDictionary
except ImportError:
    from devin_wrapper import DevinWrapper
    from enrichment import EnrichmentDictionary


class Orchestrator:
    """Orchestrates step execution with state management and verification."""
    
    def __init__(self):
        """Initialize the orchestrator."""
        self.wrapper = DevinWrapper()
    
    def invoke_step(
        self,
        step_id: str,
        steps_dir: Path,
        prompt: str,
        enrichment: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
        session_id: Optional[str] = None
    ) -> Tuple[int, Optional[str]]:
        """Invoke a step with full orchestration.
        
        Args:
            step_id: The step identifier
            steps_dir: Path to the steps directory
            prompt: The prompt to execute
            enrichment: Optional enrichment dictionary for variable substitution
            timeout: Optional timeout in seconds
            session_id: Optional session ID to resume
        
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
        
        # Enrich prompt if enrichment provided
        enriched_prompt = prompt
        if enrichment:
            enriched_prompt = self._enrich_prompt(prompt, enrichment)
        
        # Get agent config path
        agent_config = step_def.get("agent_config", ".devin/agent-config.json")
        if not Path(agent_config).is_absolute():
            agent_config = str(step_dir / agent_config)
        
        # Get model
        model = step_def.get("model", "gpt-4")
        
        # Invoke wrapper
        try:
            output, returned_session_id = self._invoke_wrapper(
                prompt=enriched_prompt,
                model=model,
                agent_config=agent_config,
                timeout=timeout,
                session_id=session_id
            )
        except Exception as e:
            print(f"[Orchestrator] ERROR: Failed to invoke wrapper: {e}")
            return 1, session_id
        
        # Write session state files
        self._write_session_state(step_dir, output, returned_session_id)
        
        # Run verification script if specified
        verify_script = step_def.get("verify")
        if verify_script:
            exit_code = self._run_verification(step_dir, verify_script)
        else:
            exit_code = 0
        
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
        session_id: Optional[str]
    ) -> None:
        """Write session state files.
        
        Args:
            step_dir: The step directory
            output: The wrapper output
            session_id: The session ID
        """
        # Write session ID if available
        if session_id:
            session_file = step_dir / "session_id.txt"
            session_file.write_text(session_id)
        
        # Write output/feedback
        feedback_file = step_dir / "feedback.txt"
        feedback_file.write_text(output)
    
    def _run_verification(
        self,
        step_dir: Path,
        verify_script: str
    ) -> int:
        """Run verification script.
        
        Args:
            step_dir: The step directory
            verify_script: Path to verification script (relative or absolute)
        
        Returns:
            int: Exit code from verification script
        """
        # Resolve script path
        script_path = Path(verify_script)
        if not script_path.is_absolute():
            script_path = step_dir / verify_script
        
        script_path = script_path.resolve()
        
        if not script_path.exists():
            print(f"[Orchestrator] ERROR: Verification script not found: {script_path}")
            return 1
        
        try:
            result = subprocess.run(
                ["bash", str(script_path)],
                check=False,
                capture_output=True,
                text=True
            )
            
            # Write stderr if present
            if result.stderr:
                stderr_file = step_dir / "stderr.txt"
                stderr_file.write_text(result.stderr)
            
            return result.returncode
        except Exception as e:
            print(f"[Orchestrator] ERROR: Failed to run verification: {e}")
            return 1
