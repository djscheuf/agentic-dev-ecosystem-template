import pytest
import json
from pathlib import Path
from unittest.mock import patch, Mock
from orchestrator.orchestrator import Orchestrator
from orchestrator.devin_wrapper import DevinWrapper


class TestOrchestratorIntegration:
    """Integration tests for Orchestrator with real step definitions."""
    
    def test_full_step_execution_flow(self, tmp_path):
        """Test complete flow: load step -> enrich -> execute -> manage state -> verify."""
        # Setup step directory
        step_dir = tmp_path / "steps" / "integration-test"
        step_dir.mkdir(parents=True)
        
        # Create step definition
        step_def = {
            "prompt": "Process {{input}} with {{config}}",
            "model": "gpt-4",
            "agent_config": ".devin/agent-config.json",
            "verify": "verify.sh"
        }
        step_file = step_dir / "step.json"
        step_file.write_text(json.dumps(step_def))
        
        # Create verification script
        verify_script = step_dir / "verify.sh"
        verify_script.write_text("#!/bin/bash\nexit 0")
        verify_script.chmod(0o755)
        
        # Create agent config
        agent_config_dir = tmp_path / ".devin"
        agent_config_dir.mkdir()
        agent_config_file = agent_config_dir / "agent-config.json"
        agent_config_file.write_text(json.dumps({"permissions": {"allow": [], "deny": []}}))
        
        orchestrator = Orchestrator()
        
        # Mock the wrapper execution
        with patch.object(orchestrator.wrapper, 'execute_prompt') as mock_execute:
            mock_execute.return_value = ("Agent output", "session-abc123")
            
            # Execute step with enrichment
            enrichment = {
                "input": "test-input",
                "config": "production"
            }
            
            exit_code, session_id = orchestrator.invoke_step(
                step_id="integration-test",
                steps_dir=tmp_path / "steps",
                prompt="Process {{input}} with {{config}}",
                enrichment=enrichment
            )
            
            # Verify results
            assert exit_code == 0
            assert session_id == "session-abc123"
            
            # Verify session state files were written
            assert (step_dir / "session_id.txt").exists()
            assert (step_dir / "session_id.txt").read_text() == "session-abc123"
            
            assert (step_dir / "feedback.txt").exists()
            assert (step_dir / "feedback.txt").read_text() == "Agent output"
            
            # Verify wrapper was called with enriched prompt
            call_args = mock_execute.call_args
            assert "test-input" in call_args[1]['prompt']
            assert "production" in call_args[1]['prompt']
    
    def test_session_resumption_flow(self, tmp_path):
        """Test session resumption with existing session ID."""
        step_dir = tmp_path / "steps" / "resume-test"
        step_dir.mkdir(parents=True)
        
        # Create step definition
        step_def = {
            "prompt": "Continue processing",
            "model": "gpt-4"
        }
        step_file = step_dir / "step.json"
        step_file.write_text(json.dumps(step_def))
        
        # Create agent config
        agent_config_file = tmp_path / "agent-config.json"
        agent_config_file.write_text(json.dumps({"permissions": {"allow": [], "deny": []}}))
        
        orchestrator = Orchestrator()
        
        with patch.object(orchestrator.wrapper, 'execute_prompt') as mock_execute:
            mock_execute.return_value = ("Resumed output", "session-abc123")
            
            exit_code, session_id = orchestrator.invoke_step(
                step_id="resume-test",
                steps_dir=tmp_path / "steps",
                prompt="Continue processing",
                session_id="session-abc123"
            )
            
            # Verify session ID was passed to wrapper
            call_kwargs = mock_execute.call_args[1]
            assert call_kwargs['session_id'] == "session-abc123"
    
    def test_timeout_enforcement(self, tmp_path):
        """Test that timeout is enforced at orchestrator level."""
        step_dir = tmp_path / "steps" / "timeout-test"
        step_dir.mkdir(parents=True)
        
        step_def = {
            "prompt": "Long running task",
            "model": "gpt-4"
        }
        step_file = step_dir / "step.json"
        step_file.write_text(json.dumps(step_def))
        
        agent_config_file = tmp_path / "agent-config.json"
        agent_config_file.write_text(json.dumps({"permissions": {"allow": [], "deny": []}}))
        
        orchestrator = Orchestrator()
        
        with patch.object(orchestrator.wrapper, 'execute_prompt') as mock_execute:
            mock_execute.return_value = ("output", "session-123")
            
            orchestrator.invoke_step(
                step_id="timeout-test",
                steps_dir=tmp_path / "steps",
                prompt="Long running task",
                timeout=60
            )
            
            # Verify timeout was passed to wrapper
            call_kwargs = mock_execute.call_args[1]
            assert call_kwargs['timeout'] == 60
    
    def test_verification_failure_handling(self, tmp_path):
        """Test handling of verification script failure."""
        step_dir = tmp_path / "steps" / "verify-fail-test"
        step_dir.mkdir(parents=True)
        
        # Create step definition with verification
        step_def = {
            "prompt": "Test prompt",
            "model": "gpt-4",
            "verify": "verify.sh"
        }
        step_file = step_dir / "step.json"
        step_file.write_text(json.dumps(step_def))
        
        # Create failing verification script
        verify_script = step_dir / "verify.sh"
        verify_script.write_text("#!/bin/bash\nexit 1")
        verify_script.chmod(0o755)
        
        agent_config_file = tmp_path / "agent-config.json"
        agent_config_file.write_text(json.dumps({"permissions": {"allow": [], "deny": []}}))
        
        orchestrator = Orchestrator()
        
        with patch.object(orchestrator.wrapper, 'execute_prompt') as mock_execute:
            mock_execute.return_value = ("output", "session-123")
            
            exit_code, session_id = orchestrator.invoke_step(
                step_id="verify-fail-test",
                steps_dir=tmp_path / "steps",
                prompt="Test prompt"
            )
            
            # Verification failure should result in non-zero exit code
            assert exit_code != 0
    
    def test_enrichment_with_missing_variables(self, tmp_path):
        """Test enrichment behavior with missing variables."""
        step_dir = tmp_path / "steps" / "enrich-test"
        step_dir.mkdir(parents=True)
        
        step_def = {
            "prompt": "Use {{provided}} but not {{missing}}",
            "model": "gpt-4"
        }
        step_file = step_dir / "step.json"
        step_file.write_text(json.dumps(step_def))
        
        agent_config_file = tmp_path / "agent-config.json"
        agent_config_file.write_text(json.dumps({"permissions": {"allow": [], "deny": []}}))
        
        orchestrator = Orchestrator()
        
        with patch.object(orchestrator.wrapper, 'execute_prompt') as mock_execute:
            mock_execute.return_value = ("output", None)
            
            enrichment = {"provided": "value"}
            
            orchestrator.invoke_step(
                step_id="enrich-test",
                steps_dir=tmp_path / "steps",
                prompt="Use {{provided}} but not {{missing}}",
                enrichment=enrichment
            )
            
            # Verify enrichment was applied (provided replaced, missing left as-is)
            call_args = mock_execute.call_args[1]
            prompt = call_args['prompt']
            assert "value" in prompt
            assert "{{missing}}" in prompt


class TestDevinWrapperStateless:
    """Test that DevinWrapper is truly stateless."""
    
    def test_wrapper_does_not_write_files(self, tmp_path):
        """Test that DevinWrapper does not write any files."""
        import os
        
        work_dir = tmp_path / "work"
        work_dir.mkdir()
        
        wrapper = DevinWrapper()
        
        with patch('subprocess.run') as mock_run:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "Starting new session: test-session-123"
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            
            original_cwd = os.getcwd()
            try:
                os.chdir(work_dir)
                
                wrapper.execute_prompt(
                    prompt="test prompt",
                    agent_config="/tmp/agent-config.json"
                )
                
                # Verify no files were written
                files_created = list(work_dir.glob("*"))
                assert len(files_created) == 0
            finally:
                os.chdir(original_cwd)
    
    def test_wrapper_multiple_invocations_independent(self, tmp_path):
        """Test that multiple wrapper invocations don't interfere."""
        wrapper = DevinWrapper()
        
        with patch('subprocess.run') as mock_run:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "output"
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            
            # First invocation
            output1, session1 = wrapper.execute_prompt(
                prompt="prompt 1",
                agent_config="/tmp/config.json"
            )
            
            # Second invocation
            output2, session2 = wrapper.execute_prompt(
                prompt="prompt 2",
                agent_config="/tmp/config.json"
            )
            
            # Both should succeed independently
            assert output1 == "output"
            assert output2 == "output"
