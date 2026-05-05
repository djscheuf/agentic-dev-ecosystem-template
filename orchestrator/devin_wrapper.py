#!/usr/bin/env python3
"""
Devin CLI Wrapper - Orchestrates Devin agent execution with verification.

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


class StepDefinition:
    """Represents a step definition for Devin execution."""
    
    def __init__(self, data: dict, step_def_dir: Path):
        self.prompt = data.get("prompt")
        self.model = data.get("model")
        self.budget = data.get("budget")
        self.timeout = data.get("timeout")
        self.verify = data.get("verify")
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


class DevinWrapper:
    """Wrapper for Devin CLI execution."""
    
    def __init__(self, step_def: StepDefinition, input_files: List[str]):
        self.step_def = step_def
        self.input_files = input_files
        self.session_id = None
        self.session_file = step_def.step_def_dir / "session_id.txt"
        self.feedback_file = step_def.step_def_dir / "feedback.txt"
        self.stderr_file = step_def.step_def_dir / "stderr.txt"
    
    def build_devin_command(self, resume_session: bool = False, feedback: str = None) -> List[str]:
        """Build the Devin CLI command."""
        cmd = ["devin"]
        
        # Add model
        cmd.extend(["--model", self.step_def.model])
        
        # Use print mode for non-interactive execution
        cmd.append("-p")
        
        # Resume existing session if requested
        if resume_session and self.session_id:
            cmd.extend(["--resume", self.session_id])
        
        # Add prompt separator
        cmd.append("--")
        
        # Build prompt content
        if resume_session and feedback:
            # Continuing session with feedback
            prompt_content = feedback
        else:
            # Initial run
            prompt_content = self.step_def.get_prompt_content()
            
            # If there are input files, append them to the prompt
            if self.input_files:
                prompt_content += "\n\nInput files:\n"
                for input_file in self.input_files:
                    prompt_content += f"- {input_file}\n"
        
        # Add the prompt as final argument
        cmd.append(prompt_content)
        
        return cmd
    
    def _load_session_id(self):
        """Load existing session ID if available."""
        if self.session_file.exists():
            self.session_id = self.session_file.read_text().strip()
            print(f"[Devin Wrapper] Loaded session ID: {self.session_id}")
    
    def _extract_session_id(self, stdout: str):
        """Extract session ID from Devin output."""
        # Look for pattern: "Starting new session: <session_id>"
        # or "Session <session_id> started"
        patterns = [
            r'Starting new session:\s+(\S+)',
            r'Session\s+(\S+)\s+started',
            r'session[_\s]id[:\s]+(\S+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, stdout, re.IGNORECASE)
            if match:
                self.session_id = match.group(1)
                self.session_file.write_text(self.session_id)
                print(f"[Devin Wrapper] Session ID: {self.session_id}")
                return
        
        print("[Devin Wrapper] Warning: Could not extract session ID from output")
    
    def run_devin(self, resume_session: bool = False, feedback: str = None) -> int:
        """Execute Devin CLI and return exit code."""
        cmd = self.build_devin_command(resume_session, feedback)
        
        print(f"[Devin Wrapper] Executing Devin with model: {self.step_def.model}")
        if resume_session:
            print(f"[Devin Wrapper] Resuming session: {self.session_id}")
        if self.step_def.budget:
            print(f"[Devin Wrapper] Note: Budget ({self.step_def.budget} ACUs) specified but not enforced by CLI")
            print(f"[Devin Wrapper]       ACU limits are managed at the account level")
        if self.step_def.timeout:
            print(f"[Devin Wrapper] Timeout: {self.step_def.timeout} seconds")
        print(f"[Devin Wrapper] Running in non-interactive mode (-p)")
        
        try:
            result = subprocess.run(
                cmd,
                check=False,
                capture_output=True,
                text=True,
                timeout=self.step_def.timeout if self.step_def.timeout else None
            )
            
            # Extract session ID from output on initial run
            if not resume_session:
                self._extract_session_id(result.stdout)
            
            # Print stdout for visibility
            if result.stdout:
                print(result.stdout)
            
            return result.returncode
        except subprocess.TimeoutExpired:
            print(f"[Devin Wrapper] ERROR: Devin execution timed out after {self.step_def.timeout} seconds", file=sys.stderr)
            print(f"[Devin Wrapper]       Process was forcibly terminated", file=sys.stderr)
            return 124  # Standard timeout exit code
        except FileNotFoundError:
            print("[Devin Wrapper] ERROR: 'devin' command not found", file=sys.stderr)
            return 127
        except Exception as e:
            print(f"[Devin Wrapper] ERROR: Failed to execute Devin: {e}", file=sys.stderr)
            return 1
    
    def run_verification(self) -> Tuple[int, str]:
        """Execute verification script. Returns (exit_code, stderr)."""
        if not self.step_def.verify:
            print("[Devin Wrapper] No verification script specified, skipping")
            return 0, ""
        
        # Resolve verification script path relative to step definition directory
        verify_script = Path(self.step_def.verify)
        if not verify_script.is_absolute():
            verify_script = self.step_def.step_def_dir / verify_script
        
        # Resolve to absolute path
        verify_script = verify_script.resolve()
        
        if not verify_script.exists():
            print(f"[Devin Wrapper] ERROR: Verification script not found: {verify_script}", file=sys.stderr)
            return 1, "Verification script not found"
        
        print(f"[Devin Wrapper] Running verification: {verify_script}")
        
        try:
            # Execute via bash to handle shell scripts
            result = subprocess.run(
                ["bash", str(verify_script)],
                check=False,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("[Devin Wrapper] ✓ Verification passed")
            elif result.returncode == 1:
                print(f"[Devin Wrapper] ✗ Verification failed (hard failure)", file=sys.stderr)
            elif result.returncode == 2:
                print(f"[Devin Wrapper] ⚠ Verification failed (self-correction needed)", file=sys.stderr)
            else:
                print(f"[Devin Wrapper] ✗ Verification failed with exit code {result.returncode}", file=sys.stderr)
            
            return result.returncode, result.stderr
        except Exception as e:
            print(f"[Devin Wrapper] ERROR: Failed to execute verification: {e}", file=sys.stderr)
            return 1, str(e)
    
    def execute(self, resume_session: bool = False) -> int:
        """Execute the full workflow: Devin + verification."""
        # Load session ID if resuming
        if resume_session:
            self._load_session_id()
            
            # Load feedback if available
            feedback = None
            if self.feedback_file.exists():
                feedback = self.feedback_file.read_text()
                print(f"[Devin Wrapper] Loaded feedback for continuation")
            
            # Run Devin with session resumption
            devin_exit_code = self.run_devin(resume_session=True, feedback=feedback)
        else:
            # Initial run
            devin_exit_code = self.run_devin(resume_session=False)
        
        if devin_exit_code != 0:
            print(f"[Devin Wrapper] Devin execution failed with exit code {devin_exit_code}", file=sys.stderr)
            return devin_exit_code
        
        print("[Devin Wrapper] Devin execution completed successfully")
        
        # Run verification
        verify_exit_code, stderr = self.run_verification()
        
        # Write stderr to file for saga consumption
        if stderr:
            self.stderr_file.write_text(stderr)
        
        return verify_exit_code


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
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python devin_wrapper.py <step_definition.json> [--resume-session] [input_files...]", file=sys.stderr)
        sys.exit(1)
    
    step_def_path = sys.argv[1]
    
    # Check for --resume-session flag
    resume_session = False
    input_files = []
    
    for arg in sys.argv[2:]:
        if arg == "--resume-session":
            resume_session = True
        else:
            input_files.append(arg)
    
    try:
        # Load step definition
        step_def = load_step_definition(step_def_path)
        
        # Create wrapper and execute
        wrapper = DevinWrapper(step_def, input_files)
        exit_code = wrapper.execute(resume_session=resume_session)
        
        sys.exit(exit_code)
        
    except Exception as e:
        print(f"[Devin Wrapper] FATAL ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
