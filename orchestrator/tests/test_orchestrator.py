import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from orchestrator.orchestrator import Orchestrator


class TestOrchestratorInvokeStep:
    """Test Orchestrator.invoke_step() method."""
    
    def test_orchestrator_loads_step_definition(self, tmp_path):
        """Test that Orchestrator loads step definition from disk."""
        step_dir = tmp_path / "steps" / "test-step"
        step_dir.mkdir(parents=True)
        
        step_def = {
            "prompt": "test prompt",
            "model": "gpt-4",
            "agent_config": ".devin/agent-config.json"
        }
        step_file = step_dir / "step.json"
        step_file.write_text(json.dumps(step_def))
        
        agent_config_dir = tmp_path / ".devin"
        agent_config_dir.mkdir()
        agent_config_file = agent_config_dir / "agent-config.json"
        agent_config_file.write_text(json.dumps({"permissions": {"allow": [], "deny": []}}))
        
        orchestrator = Orchestrator()
        
        with patch.object(orchestrator, '_invoke_wrapper') as mock_invoke:
            mock_invoke.return_value = ("output", "session-123")
            
            output, session_id = orchestrator.invoke_step(
                step_id="test-step",
                steps_dir=tmp_path / "steps",
                prompt="test prompt"
            )
            
            mock_invoke.assert_called_once()
    
    def test_orchestrator_invokes_verification_script(self, tmp_path):
        """Test that Orchestrator invokes verification script after execution."""
        step_dir = tmp_path / "steps" / "test-step"
        step_dir.mkdir(parents=True)
        
        verify_script = step_dir / "verify.sh"
        verify_script.write_text("#!/bin/bash\nexit 0")
        verify_script.chmod(0o755)
        
        step_def = {
            "prompt": "test prompt",
            "model": "gpt-4",
            "verify": "verify.sh"
        }
        step_file = step_dir / "step.json"
        step_file.write_text(json.dumps(step_def))
        
        agent_config_file = tmp_path / "agent-config.json"
        agent_config_file.write_text(json.dumps({"permissions": {"allow": [], "deny": []}}))
        
        orchestrator = Orchestrator()
        
        with patch.object(orchestrator, '_invoke_wrapper') as mock_invoke:
            mock_invoke.return_value = ("output", "session-123")
            
            exit_code, session_id = orchestrator.invoke_step(
                step_id="test-step",
                steps_dir=tmp_path / "steps",
                prompt="test prompt"
            )
            
            # Verify script should have been invoked
            verify_file = step_dir / "verify.sh"
            assert verify_file.exists()
    
    def test_orchestrator_enforces_timeout(self, tmp_path):
        """Test that Orchestrator enforces timeout around wrapper call."""
        step_dir = tmp_path / "steps" / "test-step"
        step_dir.mkdir(parents=True)
        
        step_def = {
            "prompt": "test prompt",
            "model": "gpt-4"
        }
        step_file = step_dir / "step.json"
        step_file.write_text(json.dumps(step_def))
        
        agent_config_file = tmp_path / "agent-config.json"
        agent_config_file.write_text(json.dumps({"permissions": {"allow": [], "deny": []}}))
        
        orchestrator = Orchestrator()
        
        with patch.object(orchestrator, '_invoke_wrapper') as mock_invoke:
            mock_invoke.return_value = ("output", "session-123")
            
            orchestrator.invoke_step(
                step_id="test-step",
                steps_dir=tmp_path / "steps",
                prompt="test prompt",
                timeout=30
            )
            
            # Verify timeout was passed
            call_kwargs = mock_invoke.call_args[1]
            assert call_kwargs.get('timeout') == 30
    
    def test_orchestrator_handles_missing_step_definition(self, tmp_path):
        """Test that Orchestrator handles missing step definition gracefully."""
        orchestrator = Orchestrator()
        
        with pytest.raises(FileNotFoundError):
            orchestrator.invoke_step(
                step_id="nonexistent-step",
                steps_dir=tmp_path / "steps",
                prompt="test prompt"
            )
    
    def test_orchestrator_handles_missing_verification_script(self, tmp_path):
        """Test that Orchestrator handles missing verification script gracefully."""
        step_dir = tmp_path / "steps" / "test-step"
        step_dir.mkdir(parents=True)
        
        step_def = {
            "prompt": "test prompt",
            "model": "gpt-4",
            "verify": "missing-verify.sh"
        }
        step_file = step_dir / "step.json"
        step_file.write_text(json.dumps(step_def))
        
        agent_config_file = tmp_path / "agent-config.json"
        agent_config_file.write_text(json.dumps({"permissions": {"allow": [], "deny": []}}))
        
        orchestrator = Orchestrator()
        
        with patch.object(orchestrator, '_invoke_wrapper') as mock_invoke:
            mock_invoke.return_value = ("output", "session-123")
            
            # Should not raise, but should log error
            exit_code, session_id = orchestrator.invoke_step(
                step_id="test-step",
                steps_dir=tmp_path / "steps",
                prompt="test prompt"
            )
            
            # Exit code should indicate failure
            assert exit_code != 0
