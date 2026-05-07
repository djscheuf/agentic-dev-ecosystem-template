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
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple

try:
    from .agent_wrapper import AgentWrapper
except ImportError:
    from agent_wrapper import AgentWrapper


class StepDefinition:
    """Represents a step definition for Devin execution."""
    
    def __init__(self, data: dict, step_def_dir: Path):
        self.prompt = data.get("prompt")
        self.model = data.get("model")
        self.budget = data.get("budget")
        self.timeout = data.get("timeout")
        self.verify = data.get("verify")
        self.agent_config = data.get("agent_config")
        self.step_def_dir = step_def_dir
        
        if not self.prompt:
            raise ValueError("Step definition must include 'prompt' property")
        if not self.model:
            raise ValueError("Step definition must include 'model' property")
    
    def get_prompt_content(self) -> str:
        """Get prompt content, either directly or from file."""
        # Resolve prompt file path relative to step definition directory
        prompt_path = Path(self.prompt)
        if not prompt_path.is_absolute():
            prompt_path = self.step_def_dir / prompt_path
        
        if prompt_path.exists():
            return prompt_path.read_text()
        return self.prompt
    
    def get_agent_config_path(self) -> Optional[Path]:
        """Get agent config path, resolving relative paths to step directory.
        
        Returns:
            Path: Resolved path to agent config file, or None if not specified.
                  Relative paths are resolved relative to step_def_dir.
                  Absolute paths are returned as-is.
        """
        # Return None if agent_config is not specified, empty, or null
        if not self.agent_config:
            return None
        
        config_path = Path(self.agent_config)
        
        # If absolute path, return as-is
        if config_path.is_absolute():
            return config_path
        
        # Resolve relative path relative to step definition directory
        return self.step_def_dir / config_path


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
        timeout: Optional[int] = None,
        session_id: Optional[str] = None
    ) -> Tuple[str, Optional[str]]:
        """Execute a prompt with Devin.
        
        This is a stateless method that does not manage session files or verification.
        
        Args:
            prompt: The prompt to execute
            agent_config: Path to agent configuration file
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
        cmd = self.build_devin_command(prompt, "gpt-4", agent_config, session_id)
        
        try:
            result = subprocess.run(
                cmd,
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
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
    """Main entry point - now uses Orchestrator for step execution."""
    if len(sys.argv) < 2:
        print("Usage: python devin_wrapper.py <step_definition.json> [input_files...]", file=sys.stderr)
        sys.exit(1)
    
    step_def_path = sys.argv[1]
    input_files = sys.argv[2:]
    
    try:
        # Load step definition
        step_def = load_step_definition(step_def_path)
        
        # Create wrapper and execute
        wrapper = DevinWrapper()
        prompt_content = step_def.get_prompt_content()
        
        if input_files:
            prompt_content += "\n\nInput files:\n"
            for input_file in input_files:
                prompt_content += f"- {input_file}\n"
        
        agent_config_path = step_def.get_agent_config_path()
        if agent_config_path:
            agent_config = str(agent_config_path)
        else:
            agent_config = ".devin/agent-config.json"
        
        output, session_id = wrapper.execute_prompt(
            prompt=prompt_content,
            agent_config=agent_config,
            timeout=step_def.timeout
        )
        
        print(output)
        sys.exit(0)
        
    except Exception as e:
        print(f"[Devin Wrapper] FATAL ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
