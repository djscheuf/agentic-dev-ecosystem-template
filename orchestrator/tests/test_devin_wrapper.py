import pytest
from unittest.mock import Mock, patch
from orchestrator.devin_wrapper import DevinWrapper
from orchestrator.agent_wrapper import AgentWrapper


class TestDevinWrapperInterface:
    """Test that DevinWrapper implements AgentWrapper interface."""
    
    def test_devin_wrapper_is_agent_wrapper(self):
        """Test that DevinWrapper is an AgentWrapper."""
        wrapper = DevinWrapper()
        assert isinstance(wrapper, AgentWrapper)
    
    def test_devin_wrapper_has_execute_prompt_method(self):
        """Test that DevinWrapper has execute_prompt method."""
        wrapper = DevinWrapper()
        assert hasattr(wrapper, 'execute_prompt')
        assert callable(wrapper.execute_prompt)


class TestDevinWrapperExecutePrompt:
    """Test DevinWrapper.execute_prompt() method."""
    
    def test_execute_prompt_returns_tuple(self):
        """Test that execute_prompt returns (output, session_id) tuple."""
        wrapper = DevinWrapper()
        
        with patch('subprocess.run') as mock_run:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "output"
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            
            result = wrapper.execute_prompt(
                prompt="test prompt",
                agent_config="/tmp/config.json"
            )
            
            assert isinstance(result, tuple)
            assert len(result) == 2
            assert isinstance(result[0], str)  # output
    
    def test_execute_prompt_with_timeout(self):
        """Test that execute_prompt respects timeout parameter."""
        wrapper = DevinWrapper()
        
        with patch('subprocess.run') as mock_run:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "output"
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            
            wrapper.execute_prompt(
                prompt="test prompt",
                agent_config="/tmp/config.json",
                timeout=30
            )
            
            # Verify timeout was passed to subprocess.run
            call_kwargs = mock_run.call_args[1]
            assert call_kwargs['timeout'] == 30
    
    def test_execute_prompt_with_session_id(self):
        """Test that execute_prompt accepts and uses session_id."""
        wrapper = DevinWrapper()
        
        with patch('subprocess.run') as mock_run:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "output"
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            
            output, session_id = wrapper.execute_prompt(
                prompt="test prompt",
                agent_config="/tmp/config.json",
                session_id="existing-session-123"
            )
            
            # Verify session ID was included in command
            call_args = mock_run.call_args[0][0]
            assert "existing-session-123" in call_args
    
    def test_execute_prompt_extracts_session_id_from_output(self):
        """Test that execute_prompt extracts session ID from output."""
        wrapper = DevinWrapper()
        
        with patch('subprocess.run') as mock_run:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "Starting new session: sess_abc123def456"
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            
            output, session_id = wrapper.execute_prompt(
                prompt="test prompt",
                agent_config="/tmp/config.json"
            )
            
            assert session_id == "sess_abc123def456"
    
    def test_execute_prompt_no_session_id_in_output(self):
        """Test that execute_prompt returns None when no session ID found."""
        wrapper = DevinWrapper()
        
        with patch('subprocess.run') as mock_run:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "Task completed successfully"
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            
            output, session_id = wrapper.execute_prompt(
                prompt="test prompt",
                agent_config="/tmp/config.json"
            )
            
            assert session_id is None
    
    def test_execute_prompt_is_stateless(self):
        """Test that execute_prompt does not write files."""
        import os
        import tempfile
        
        wrapper = DevinWrapper()
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            with patch('subprocess.run') as mock_run:
                mock_result = Mock()
                mock_result.returncode = 0
                mock_result.stdout = "output"
                mock_result.stderr = ""
                mock_run.return_value = mock_result
                
                original_cwd = os.getcwd()
                try:
                    os.chdir(tmp_dir)
                    
                    wrapper.execute_prompt(
                        prompt="test prompt",
                        agent_config="/tmp/config.json"
                    )
                    
                    # Verify no files were written
                    files = os.listdir(tmp_dir)
                    assert len(files) == 0
                finally:
                    os.chdir(original_cwd)


class TestDevinWrapperSessionIDExtraction:
    """Test session ID extraction patterns."""
    
    def test_extract_session_id_pattern_1(self):
        """Test extraction with 'Starting new session:' pattern."""
        wrapper = DevinWrapper()
        
        stdout = "Starting new session: sess_abc123def456"
        session_id = wrapper._extract_session_id(stdout)
        
        assert session_id == "sess_abc123def456"
    
    def test_extract_session_id_pattern_2(self):
        """Test extraction with 'Session <id> started' pattern."""
        wrapper = DevinWrapper()
        
        stdout = "Session xyz789 started"
        session_id = wrapper._extract_session_id(stdout)
        
        assert session_id == "xyz789"
    
    def test_extract_session_id_pattern_3(self):
        """Test extraction with 'session_id:' pattern."""
        wrapper = DevinWrapper()
        
        stdout = "session_id: sess_final_123"
        session_id = wrapper._extract_session_id(stdout)
        
        assert session_id == "sess_final_123"
    
    def test_extract_session_id_case_insensitive(self):
        """Test case-insensitive extraction."""
        wrapper = DevinWrapper()
        
        stdout = "SESSION_ID: upper_case_id"
        session_id = wrapper._extract_session_id(stdout)
        
        assert session_id == "upper_case_id"
    
    def test_extract_session_id_with_whitespace(self):
        """Test extraction with various whitespace patterns."""
        wrapper = DevinWrapper()
        
        stdout = "Starting new session:    sess_with_spaces"
        session_id = wrapper._extract_session_id(stdout)
        
        assert session_id == "sess_with_spaces"
    
    def test_extract_session_id_multiline(self):
        """Test extraction from multiline output."""
        wrapper = DevinWrapper()
        
        stdout = """
        Initializing Devin...
        Starting new session: sess_multiline_123
        Executing task...
        """
        session_id = wrapper._extract_session_id(stdout)
        
        assert session_id == "sess_multiline_123"
    
    def test_extract_session_id_no_match(self):
        """Test when no session ID is found."""
        wrapper = DevinWrapper()
        
        stdout = "Task completed successfully"
        session_id = wrapper._extract_session_id(stdout)
        
        assert session_id is None
    
    def test_extract_session_id_special_chars(self):
        """Test extraction with special characters."""
        wrapper = DevinWrapper()
        
        stdout = "Starting new session: sess-abc_123.xyz"
        session_id = wrapper._extract_session_id(stdout)
        
        assert session_id == "sess-abc_123.xyz"


class TestDevinWrapperCommandBuilding:
    """Test Devin CLI command building."""
    
    def test_build_devin_command_basic(self):
        """Test basic command building."""
        wrapper = DevinWrapper()
        
        cmd = wrapper.build_devin_command(
            prompt="test prompt",
            model="gpt-4",
            agent_config="/tmp/config.json"
        )
        
        assert "devin" in cmd
        assert "--model" in cmd
        assert "gpt-4" in cmd
        assert "--agent-config" in cmd
        assert "/tmp/config.json" in cmd
        assert "-p" in cmd
        assert "--" in cmd
        assert "test prompt" in cmd
    
    def test_build_devin_command_with_session_id(self):
        """Test command building with session ID."""
        wrapper = DevinWrapper()
        
        cmd = wrapper.build_devin_command(
            prompt="test prompt",
            model="gpt-4",
            agent_config="/tmp/config.json",
            session_id="sess_123"
        )
        
        assert "sess_123" in cmd
    
    def test_build_devin_command_includes_prompt(self):
        """Test that prompt is included in command."""
        wrapper = DevinWrapper()
        
        prompt = "This is a test prompt with special chars: !@#$%"
        cmd = wrapper.build_devin_command(
            prompt=prompt,
            model="gpt-4",
            agent_config="/tmp/config.json"
        )
        
        assert prompt in cmd
