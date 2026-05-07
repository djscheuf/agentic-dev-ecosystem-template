#!/usr/bin/env python3
"""
Devin CLI Wrapper - Thin adapter for Devin CLI execution.

This is a stateless wrapper that only handles CLI invocation.
Session management, enrichment, and verification are handled by the Orchestrator.

Usage:
    python devin_wrapper.py <step_definition.json> [input_files...]
    python devin_wrapper.py <step_definition.json> --resume-session [input_files...]
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple

try:
    from .agent_wrapper import AgentWrapper
    from .models import StepDefinition
except ImportError:
    from agent_wrapper import AgentWrapper
    from models import StepDefinition


class DevinWrapper(AgentWrapper):
    """Thin wrapper for Devin CLI execution.
    
    This wrapper is stateless - it does not manage session files, logging, or verification.
    All state management is handled by the Orchestrator.
    """
    
    def __init__(self):
        """Initialize the wrapper. No state is stored."""
        pass
    
    def build_devin_command(
        self,
        prompt: str,
        model: str,
        agent_config: str,
        session_id: Optional[str] = None
    ) -> List[str]:
        """Build the Devin CLI command.
        
        Args:
            prompt: The prompt to execute
            model: The model to use (e.g., "gpt-4")
            agent_config: Path to agent configuration file
            session_id: Optional session ID to resume
        
        Returns:
            List[str]: The command to execute
        """
        cmd = ["devin"]
        
        # Add model
        cmd.extend(["--model", model])
        
        # Add agent config
        cmd.extend(["--agent-config", agent_config])
        
        # Use print mode for non-interactive execution
        cmd.append("-p")
        
        # Resume existing session if requested
        if session_id:
            cmd.extend(["--resume", session_id])
        
        # Add prompt separator
        cmd.append("--")
        
        # Add the prompt as final argument
        cmd.append(prompt)
        
        return cmd
    
    def _extract_session_id(self, stdout: str) -> Optional[str]:
        """Extract session ID from Devin output.
        
        Args:
            stdout: The stdout from Devin execution
        
        Returns:
            Optional[str]: The extracted session ID, or None if not found
        """
        patterns = [
            r'Starting new session:\s+(\S+)',
            r'Session\s+(\S+)\s+started',
            r'session[_\s]id[:\s]+(\S+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, stdout, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def execute_prompt(
        self,
        prompt: str,
        agent_config: str,
        model: str = "claude-sonnet-4.5",
        timeout: Optional[int] = None,
        session_id: Optional[str] = None
    ) -> Tuple[str, Optional[str]]:
        """Execute a prompt with Devin.
        
        This is a stateless method that does not manage session files or verification.
        
        Args:
            prompt: The prompt to execute
            agent_config: Path to agent configuration file
            model: The model to use (default: claude-sonnet-4.5)
            timeout: Optional timeout in seconds
            session_id: Optional session ID to resume
        
        Returns:
            Tuple[str, Optional[str]]: (output, session_id)
                - output: The Devin output
                - session_id: The session ID (new or resumed)
        
        Raises:
            FileNotFoundError: If 'devin' command is not found
            subprocess.TimeoutExpired: If execution exceeds timeout
        """
        cmd = self.build_devin_command(prompt, model, agent_config, session_id)
        
        try:
            result = subprocess.run(
                cmd,
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            # Check if command failed
            if result.returncode != 0:
                error_msg = f"Devin command failed with exit code {result.returncode}"
                if result.stderr:
                    error_msg += f"\nStderr: {result.stderr}"
                if result.stdout:
                    error_msg += f"\nStdout: {result.stdout}"
                raise RuntimeError(error_msg)
            
            # Extract session ID from output on initial run
            extracted_session_id = self._extract_session_id(result.stdout)
            
            # Use existing session_id if resuming, otherwise use extracted
            final_session_id = session_id if session_id else extracted_session_id
            
            return result.stdout, final_session_id
        
        except subprocess.TimeoutExpired:
            raise
        except FileNotFoundError:
            raise
        except Exception as e:
            raise RuntimeError(f"Failed to execute Devin: {e}") from e




def load_step_definition(path: str) -> StepDefinition:
    """Load and parse step definition JSON file."""
    step_file = Path(path)
    
    if not step_file.exists():
        raise FileNotFoundError(f"Step definition file not found: {path}")
    
    try:
        data = json.loads(step_file.read_text())
        step_def_dir = step_file.parent
        return StepDefinition(data, step_def_dir)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in step definition: {e}")


def main():
    """Main entry point - accepts step name and input file path."""
    if len(sys.argv) < 3:
        print("Usage: python devin_wrapper.py <step_name> <input_file_path>", file=sys.stderr)
        sys.exit(1)
    
    step_name = sys.argv[1]
    input_file_path = sys.argv[2]
    
    try:
        # Load step definition from steps/<step_name>/step.json
        step_def_path = f"steps/{step_name}/step.json"
        print(f"[Devin Wrapper] Loading step definition: {step_def_path}", file=sys.stderr)
        step_def = load_step_definition(step_def_path)
        
        # Create wrapper and execute
        wrapper = DevinWrapper()
        prompt_content = step_def.get_prompt_content()
        
        # Append input file path to prompt
        prompt_content += f"\n\n{input_file_path}"
        
        agent_config_path = step_def.get_agent_config_path()
        if agent_config_path:
            agent_config = str(agent_config_path)
        else:
            agent_config = ".devin/agent-config.json"
        
        print(f"[Devin Wrapper] Using agent config: {agent_config}", file=sys.stderr)
        print(f"[Devin Wrapper] Using model: {step_def.model}", file=sys.stderr)
        print(f"[Devin Wrapper] Executing prompt with timeout: {step_def.timeout}s", file=sys.stderr)
        
        output, session_id = wrapper.execute_prompt(
            prompt=prompt_content,
            agent_config=agent_config,
            model=step_def.model,
            timeout=step_def.timeout
        )
        
        print(f"[Devin Wrapper] Execution completed. Session ID: {session_id}", file=sys.stderr)
        print(output)
        sys.exit(0)
        
    except FileNotFoundError as e:
        print(f"[Devin Wrapper] ERROR: 'devin' command not found. Is Devin CLI installed?", file=sys.stderr)
        print(f"[Devin Wrapper] Details: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[Devin Wrapper] FATAL ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
