import pytest
import json
from pathlib import Path
from abc import ABC, abstractmethod
from unittest.mock import Mock, patch


class TestAgentWrapperInterface:
    """Test AgentWrapper abstract base class and interface contract."""
    
    def test_agent_wrapper_is_abstract_base_class(self):
        """Test that AgentWrapper is an abstract base class."""
        from orchestrator.agent_wrapper import AgentWrapper
        
        # AgentWrapper should be abstract and not instantiable
        assert hasattr(AgentWrapper, '__abstractmethods__')
        assert 'execute_prompt' in AgentWrapper.__abstractmethods__
    
    def test_devin_wrapper_implements_agent_wrapper(self):
        """Test that DevinWrapper implements AgentWrapper interface."""
        from orchestrator.agent_wrapper import AgentWrapper
        from orchestrator.devin_wrapper import DevinWrapper
        
        # DevinWrapper should be a subclass of AgentWrapper
        assert issubclass(DevinWrapper, AgentWrapper)
    
    def test_agent_wrapper_execute_prompt_signature(self):
        """Test that AgentWrapper.execute_prompt() has correct signature."""
        from orchestrator.agent_wrapper import AgentWrapper
        import inspect
        
        # Get the abstract method
        sig = inspect.signature(AgentWrapper.execute_prompt)
        params = list(sig.parameters.keys())
        
        # Should have: self, prompt, agent_config, timeout=None, session_id=None
        assert 'prompt' in params
        assert 'agent_config' in params
        assert 'timeout' in params
        assert 'session_id' in params
    
    def test_devin_wrapper_execute_prompt_returns_tuple(self, tmp_path):
        """Test that DevinWrapper.execute_prompt() returns (output, session_id) tuple."""
        from orchestrator.devin_wrapper import DevinWrapper
        
        # Create minimal agent config
        agent_config = tmp_path / "agent-config.json"
        agent_config.write_text(json.dumps({"permissions": {"allow": [], "deny": []}}))
        
        wrapper = DevinWrapper()
        
        with patch('subprocess.run') as mock_run:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "Starting new session: test-session-123"
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            
            output, session_id = wrapper.execute_prompt(
                prompt="test prompt",
                agent_config=str(agent_config)
            )
            
            # Should return tuple of (output, session_id)
            assert isinstance(output, str)
            assert isinstance(session_id, (str, type(None)))
    
    def test_devin_wrapper_execute_prompt_with_timeout(self, tmp_path):
        """Test that DevinWrapper.execute_prompt() respects timeout parameter."""
        from orchestrator.devin_wrapper import DevinWrapper
        
        agent_config = tmp_path / "agent-config.json"
        agent_config.write_text(json.dumps({"permissions": {"allow": [], "deny": []}}))
        
        wrapper = DevinWrapper()
        
        with patch('subprocess.run') as mock_run:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = ""
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            
            wrapper.execute_prompt(
                prompt="test prompt",
                agent_config=str(agent_config),
                timeout=30
            )
            
            # Verify timeout was passed to subprocess.run
            call_kwargs = mock_run.call_args[1]
            assert call_kwargs.get('timeout') == 30
    
    def test_devin_wrapper_execute_prompt_with_session_id(self, tmp_path):
        """Test that DevinWrapper.execute_prompt() accepts session_id parameter."""
        from orchestrator.devin_wrapper import DevinWrapper
        
        agent_config = tmp_path / "agent-config.json"
        agent_config.write_text(json.dumps({"permissions": {"allow": [], "deny": []}}))
        
        wrapper = DevinWrapper()
        
        with patch('subprocess.run') as mock_run:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = ""
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            
            wrapper.execute_prompt(
                prompt="test prompt",
                agent_config=str(agent_config),
                session_id="existing-session-123"
            )
            
            # Verify session_id was used in command
            call_args = mock_run.call_args[0][0]  # Get the command list
            assert "--resume" in call_args
            assert "existing-session-123" in call_args
    
    def test_devin_wrapper_execute_prompt_is_stateless(self, tmp_path):
        """Test that DevinWrapper.execute_prompt() does not write files."""
        from orchestrator.devin_wrapper import DevinWrapper
        
        agent_config = tmp_path / "agent-config.json"
        agent_config.write_text(json.dumps({"permissions": {"allow": [], "deny": []}}))
        
        work_dir = tmp_path / "work"
        work_dir.mkdir()
        
        wrapper = DevinWrapper()
        
        with patch('subprocess.run') as mock_run:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "Starting new session: test-session-123"
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            
            # Change to work directory
            import os
            original_cwd = os.getcwd()
            try:
                os.chdir(work_dir)
                
                wrapper.execute_prompt(
                    prompt="test prompt",
                    agent_config=str(agent_config)
                )
                
                # Verify no session files were written by wrapper
                assert not (work_dir / "session_id.txt").exists()
                assert not (work_dir / "feedback.txt").exists()
                assert not (work_dir / "stderr.txt").exists()
            finally:
                os.chdir(original_cwd)
