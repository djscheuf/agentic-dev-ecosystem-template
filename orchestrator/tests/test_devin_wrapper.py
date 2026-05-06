import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch
from orchestrator.devin_wrapper import StepDefinition, DevinWrapper, load_step_definition


class TestDevinWrapperHappyPath:
    """Happy path tests for devin_wrapper.py (D-H-*)."""
    
    def test_d_h_01_execute_step_successfully(self, tmp_path):
        """D-H-01: Execute step successfully (exit code 0)."""
        step_file = tmp_path / "step.json"
        step_data = {
            "prompt": "test prompt",
            "model": "gpt-4"
        }
        step_file.write_text(json.dumps(step_data))
        
        step_def = load_step_definition(str(step_file))
        wrapper = DevinWrapper(step_def, [])
        
        with patch('subprocess.run') as mock_run:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = ""
            mock_run.return_value = mock_result
            
            exit_code = wrapper.run_devin()
            
            assert exit_code == 0
            mock_run.assert_called_once()
    
    def test_d_h_02_execute_with_verification(self, tmp_path):
        """D-H-02: Execute with verification (both pass)."""
        verify_script = tmp_path / "verify.sh"
        verify_script.write_text("#!/bin/bash\nexit 0")
        verify_script.chmod(0o755)
        
        step_file = tmp_path / "step.json"
        step_data = {
            "prompt": "test prompt",
            "model": "gpt-4",
            "verify": str(verify_script)
        }
        step_file.write_text(json.dumps(step_data))
        
        step_def = load_step_definition(str(step_file))
        wrapper = DevinWrapper(step_def, [])
        
        with patch('subprocess.run') as mock_run:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = ""
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            
            exit_code, session_id = wrapper.execute()
            
            assert exit_code == 0
            assert session_id is None
            assert mock_run.call_count == 2
    
    def test_d_h_03_execute_with_input_files(self, tmp_path):
        """D-H-03: Execute with input files."""
        step_file = tmp_path / "step.json"
        step_data = {
            "prompt": "test prompt",
            "model": "gpt-4"
        }
        step_file.write_text(json.dumps(step_data))
        
        step_def = load_step_definition(str(step_file))
        wrapper = DevinWrapper(step_def, ["file1.txt", "file2.txt"])
        
        cmd = wrapper.build_devin_command()
        
        assert "file1.txt" in cmd[-1]
        assert "file2.txt" in cmd[-1]
    
    def test_d_h_04_execute_without_input_files(self, tmp_path):
        """D-H-04: Execute without input files."""
        step_file = tmp_path / "step.json"
        step_data = {
            "prompt": "test prompt",
            "model": "gpt-4"
        }
        step_file.write_text(json.dumps(step_data))
        
        step_def = load_step_definition(str(step_file))
        wrapper = DevinWrapper(step_def, [])
        
        cmd = wrapper.build_devin_command()
        
        assert cmd[-1] == "test prompt"
    
    def test_d_h_05_prompt_loaded_from_external_file(self, tmp_path):
        """D-H-05: Prompt loaded from external file."""
        prompt_file = tmp_path / "prompt.txt"
        prompt_file.write_text("External prompt content")
        
        step_file = tmp_path / "step.json"
        step_data = {
            "prompt": "prompt.txt",
            "model": "gpt-4"
        }
        step_file.write_text(json.dumps(step_data))
        
        step_def = load_step_definition(str(step_file))
        
        assert step_def.get_prompt_content() == "External prompt content"
    
    def test_d_h_06_prompt_specified_as_string_directly(self, tmp_path):
        """D-H-06: Prompt specified as string directly."""
        step_file = tmp_path / "step.json"
        step_data = {
            "prompt": "Direct string prompt",
            "model": "gpt-4"
        }
        step_file.write_text(json.dumps(step_data))
        
        step_def = load_step_definition(str(step_file))
        
        assert step_def.get_prompt_content() == "Direct string prompt"


class TestDevinWrapperEdgeCases:
    """Edge case tests for devin_wrapper.py (D-E-*)."""
    
    def test_d_e_01_empty_prompt_file(self, tmp_path):
        """D-E-01: Empty prompt file."""
        prompt_file = tmp_path / "prompt.txt"
        prompt_file.write_text("")
        
        step_file = tmp_path / "step.json"
        step_data = {
            "prompt": "prompt.txt",
            "model": "gpt-4"
        }
        step_file.write_text(json.dumps(step_data))
        
        step_def = load_step_definition(str(step_file))
        
        assert step_def.get_prompt_content() == ""
    
    def test_d_e_02_very_long_prompt_content(self, tmp_path):
        """D-E-02: Very long prompt content."""
        long_prompt = "A" * 5000
        
        prompt_file = tmp_path / "long_prompt.txt"
        prompt_file.write_text(long_prompt)
        
        step_file = tmp_path / "step.json"
        step_data = {
            "prompt": "long_prompt.txt",
            "model": "gpt-4"
        }
        step_file.write_text(json.dumps(step_data))
        
        step_def = load_step_definition(str(step_file))
        wrapper = DevinWrapper(step_def, [])
        
        cmd = wrapper.build_devin_command()
        
        assert len(cmd[-1]) == 5000
        assert long_prompt in cmd[-1]
    
    def test_d_e_03_no_verification_script_specified(self, tmp_path):
        """D-E-03: No verification script specified."""
        step_file = tmp_path / "step.json"
        step_data = {
            "prompt": "test prompt",
            "model": "gpt-4"
        }
        step_file.write_text(json.dumps(step_data))
        
        step_def = load_step_definition(str(step_file))
        wrapper = DevinWrapper(step_def, [])
        
        exit_code, stderr = wrapper.run_verification()
        
        assert exit_code == 0
        assert stderr == ""


class TestDevinWrapperErrorHandling:
    """Critical error handling tests for devin_wrapper.py (D-ER-*)."""
    
    def test_d_er_01_missing_step_definition_file(self):
        """D-ER-01: Missing step definition file (step.json)."""
        with pytest.raises(FileNotFoundError, match="not found"):
            load_step_definition("/nonexistent/step.json")
    
    def test_d_er_02_malformed_step_json(self, tmp_path):
        """D-ER-02: Malformed step.json (invalid JSON)."""
        step_file = tmp_path / "step.json"
        step_file.write_text("{ invalid json")
        
        with pytest.raises(ValueError, match="Invalid JSON"):
            load_step_definition(str(step_file))
    
    def test_d_er_03_missing_prompt_property(self, tmp_path):
        """D-ER-03: Missing 'prompt' property."""
        step_file = tmp_path / "step.json"
        step_data = {
            "model": "gpt-4"
        }
        step_file.write_text(json.dumps(step_data))
        
        with pytest.raises(ValueError, match="must include 'prompt'"):
            load_step_definition(str(step_file))
    
    def test_d_er_04_missing_model_property(self, tmp_path):
        """D-ER-04: Missing 'model' property."""
        step_file = tmp_path / "step.json"
        step_data = {
            "prompt": "test prompt"
        }
        step_file.write_text(json.dumps(step_data))
        
        with pytest.raises(ValueError, match="must include 'model'"):
            load_step_definition(str(step_file))
    
    def test_d_er_05_prompt_file_not_found(self, tmp_path):
        """D-ER-05: Prompt file not found."""
        step_file = tmp_path / "step.json"
        step_data = {
            "prompt": "nonexistent_prompt.txt",
            "model": "gpt-4"
        }
        step_file.write_text(json.dumps(step_data))
        
        step_def = load_step_definition(str(step_file))
        
        prompt_content = step_def.get_prompt_content()
        assert prompt_content == "nonexistent_prompt.txt"
    
    def test_d_er_06_verification_script_not_found(self, tmp_path):
        """D-ER-06: Verification script not found."""
        step_file = tmp_path / "step.json"
        step_data = {
            "prompt": "test prompt",
            "model": "gpt-4",
            "verify": "nonexistent_verify.sh"
        }
        step_file.write_text(json.dumps(step_data))
        
        step_def = load_step_definition(str(step_file))
        wrapper = DevinWrapper(step_def, [])
        
        exit_code, stderr = wrapper.run_verification()
        
        assert exit_code == 1
        assert "Verification script not found" in stderr
    
    def test_d_er_07_verification_script_fails(self, tmp_path):
        """D-ER-07: Verification script fails (non-zero exit)."""
        step_file = tmp_path / "step.json"
        verify_script = tmp_path / "verify.sh"
        verify_script.write_text("#!/bin/bash\nexit 1")
        verify_script.chmod(0o755)
        
        step_data = {
            "prompt": "test prompt",
            "model": "gpt-4",
            "verify": str(verify_script)
        }
        step_file.write_text(json.dumps(step_data))
        
        step_def = load_step_definition(str(step_file))
        wrapper = DevinWrapper(step_def, [])
        
        with patch('subprocess.run') as mock_run:
            mock_result = Mock()
            mock_result.returncode = 1
            mock_result.stderr = "Test error"
            mock_run.return_value = mock_result
            
            exit_code, stderr = wrapper.run_verification()
            
            assert exit_code == 1
            assert stderr == "Test error"
    
    def test_prompt_loaded_from_file(self, tmp_path):
        """Test that prompt content is loaded from external file."""
        prompt_file = tmp_path / "prompt.txt"
        prompt_file.write_text("This is a test prompt from file")
        
        step_file = tmp_path / "step.json"
        step_data = {
            "prompt": "prompt.txt",
            "model": "gpt-4"
        }
        step_file.write_text(json.dumps(step_data))
        
        step_def = load_step_definition(str(step_file))
        
        assert step_def.get_prompt_content() == "This is a test prompt from file"
    
    def test_prompt_specified_as_string(self, tmp_path):
        """Test that prompt can be specified as string directly."""
        step_file = tmp_path / "step.json"
        step_data = {
            "prompt": "Direct prompt string",
            "model": "gpt-4"
        }
        step_file.write_text(json.dumps(step_data))
        
        step_def = load_step_definition(str(step_file))
        
        assert step_def.get_prompt_content() == "Direct prompt string"
    
    def test_no_verification_script_specified(self, tmp_path):
        """Test execution without verification script."""
        step_file = tmp_path / "step.json"
        step_data = {
            "prompt": "test prompt",
            "model": "gpt-4"
        }
        step_file.write_text(json.dumps(step_data))
        
        step_def = load_step_definition(str(step_file))
        wrapper = DevinWrapper(step_def, [])
        
        exit_code, stderr = wrapper.run_verification()
        
        assert exit_code == 0
        assert stderr == ""


class TestSessionIDExtraction:
    """Session ID extraction tests (S-E-*)."""
    
    def test_s_e_01_extract_session_id_pattern_1(self, tmp_path):
        """S-E-01: Extract session ID with 'Starting new session:' pattern."""
        step_file = tmp_path / "step.json"
        step_data = {
            "prompt": "test prompt",
            "model": "gpt-4"
        }
        step_file.write_text(json.dumps(step_data))
        
        step_def = load_step_definition(str(step_file))
        wrapper = DevinWrapper(step_def, [])
        
        stdout = "Starting new session: sess_abc123def456"
        wrapper._extract_session_id(stdout)
        
        assert wrapper.session_id == "sess_abc123def456"
        assert wrapper.session_file.exists()
        assert wrapper.session_file.read_text() == "sess_abc123def456"
    
    def test_s_e_02_extract_session_id_pattern_2(self, tmp_path):
        """S-E-02: Extract session ID with 'Session <id> started' pattern."""
        step_file = tmp_path / "step.json"
        step_data = {
            "prompt": "test prompt",
            "model": "gpt-4"
        }
        step_file.write_text(json.dumps(step_data))
        
        step_def = load_step_definition(str(step_file))
        wrapper = DevinWrapper(step_def, [])
        
        stdout = "Session xyz789 started"
        wrapper._extract_session_id(stdout)
        
        assert wrapper.session_id == "xyz789"
        assert wrapper.session_file.read_text() == "xyz789"
    
    def test_s_e_03_extract_session_id_pattern_3(self, tmp_path):
        """S-E-03: Extract session ID with 'session_id:' pattern."""
        step_file = tmp_path / "step.json"
        step_data = {
            "prompt": "test prompt",
            "model": "gpt-4"
        }
        step_file.write_text(json.dumps(step_data))
        
        step_def = load_step_definition(str(step_file))
        wrapper = DevinWrapper(step_def, [])
        
        stdout = "session_id: sess_final_123"
        wrapper._extract_session_id(stdout)
        
        assert wrapper.session_id == "sess_final_123"
        assert wrapper.session_file.read_text() == "sess_final_123"
    
    def test_s_e_04_extract_session_id_case_insensitive(self, tmp_path):
        """S-E-04: Extract session ID with case-insensitive matching."""
        step_file = tmp_path / "step.json"
        step_data = {
            "prompt": "test prompt",
            "model": "gpt-4"
        }
        step_file.write_text(json.dumps(step_data))
        
        step_def = load_step_definition(str(step_file))
        wrapper = DevinWrapper(step_def, [])
        
        stdout = "SESSION_ID: upper_case_id"
        wrapper._extract_session_id(stdout)
        
        assert wrapper.session_id == "upper_case_id"
    
    def test_s_e_05_extract_session_id_with_whitespace(self, tmp_path):
        """S-E-05: Extract session ID with various whitespace patterns."""
        step_file = tmp_path / "step.json"
        step_data = {
            "prompt": "test prompt",
            "model": "gpt-4"
        }
        step_file.write_text(json.dumps(step_data))
        
        step_def = load_step_definition(str(step_file))
        wrapper = DevinWrapper(step_def, [])
        
        stdout = "Starting new session:    sess_with_spaces"
        wrapper._extract_session_id(stdout)
        
        assert wrapper.session_id == "sess_with_spaces"
    
    def test_s_e_06_extract_session_id_in_multiline_output(self, tmp_path):
        """S-E-06: Extract session ID from multiline output."""
        step_file = tmp_path / "step.json"
        step_data = {
            "prompt": "test prompt",
            "model": "gpt-4"
        }
        step_file.write_text(json.dumps(step_data))
        
        step_def = load_step_definition(str(step_file))
        wrapper = DevinWrapper(step_def, [])
        
        stdout = """
        Initializing Devin...
        Starting new session: sess_multiline_123
        Executing task...
        """
        wrapper._extract_session_id(stdout)
        
        assert wrapper.session_id == "sess_multiline_123"
    
    def test_s_e_07_no_session_id_in_output(self, tmp_path):
        """S-E-07: Handle output with no session ID gracefully."""
        step_file = tmp_path / "step.json"
        step_data = {
            "prompt": "test prompt",
            "model": "gpt-4"
        }
        step_file.write_text(json.dumps(step_data))
        
        step_def = load_step_definition(str(step_file))
        wrapper = DevinWrapper(step_def, [])
        
        stdout = "Task completed successfully"
        wrapper._extract_session_id(stdout)
        
        assert wrapper.session_id is None
        assert not wrapper.session_file.exists()
    
    def test_s_e_08_malformed_session_id_no_match(self, tmp_path):
        """S-E-08: Handle malformed session ID output."""
        step_file = tmp_path / "step.json"
        step_data = {
            "prompt": "test prompt",
            "model": "gpt-4"
        }
        step_file.write_text(json.dumps(step_data))
        
        step_def = load_step_definition(str(step_file))
        wrapper = DevinWrapper(step_def, [])
        
        stdout = "session_id: "
        wrapper._extract_session_id(stdout)
        
        assert wrapper.session_id is None
    
    def test_s_e_09_extract_session_id_with_special_chars(self, tmp_path):
        """S-E-09: Extract session ID with special characters."""
        step_file = tmp_path / "step.json"
        step_data = {
            "prompt": "test prompt",
            "model": "gpt-4"
        }
        step_file.write_text(json.dumps(step_data))
        
        step_def = load_step_definition(str(step_file))
        wrapper = DevinWrapper(step_def, [])
        
        stdout = "Starting new session: sess-abc_123.xyz"
        wrapper._extract_session_id(stdout)
        
        assert wrapper.session_id == "sess-abc_123.xyz"


class TestExecuteMethodReturnValue:
    """Tests for execute method return value contract (E-R-*)."""
    
    def test_e_r_01_execute_returns_tuple(self, tmp_path):
        """E-R-01: execute() returns tuple of (exit_code, session_id)."""
        step_file = tmp_path / "step.json"
        step_data = {
            "prompt": "test prompt",
            "model": "gpt-4"
        }
        step_file.write_text(json.dumps(step_data))
        
        step_def = load_step_definition(str(step_file))
        wrapper = DevinWrapper(step_def, [])
        
        with patch('subprocess.run') as mock_run:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "Starting new session: sess_test_123"
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            
            result = wrapper.execute()
            
            assert isinstance(result, tuple)
            assert len(result) == 2
            assert isinstance(result[0], int)
            assert result[0] == 0
            assert result[1] == "sess_test_123"
    
    def test_e_r_02_execute_returns_none_session_id_when_not_found(self, tmp_path):
        """E-R-02: execute() returns None for session_id when not found."""
        step_file = tmp_path / "step.json"
        step_data = {
            "prompt": "test prompt",
            "model": "gpt-4"
        }
        step_file.write_text(json.dumps(step_data))
        
        step_def = load_step_definition(str(step_file))
        wrapper = DevinWrapper(step_def, [])
        
        with patch('subprocess.run') as mock_run:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "Task completed"
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            
            exit_code, session_id = wrapper.execute()
            
            assert exit_code == 0
            assert session_id is None
    
    def test_e_r_03_execute_returns_nonzero_exit_code(self, tmp_path):
        """E-R-03: execute() returns non-zero exit code on failure."""
        step_file = tmp_path / "step.json"
        step_data = {
            "prompt": "test prompt",
            "model": "gpt-4"
        }
        step_file.write_text(json.dumps(step_data))
        
        step_def = load_step_definition(str(step_file))
        wrapper = DevinWrapper(step_def, [])
        
        with patch('subprocess.run') as mock_run:
            mock_result = Mock()
            mock_result.returncode = 1
            mock_result.stdout = ""
            mock_result.stderr = "Error occurred"
            mock_run.return_value = mock_result
            
            exit_code, session_id = wrapper.execute()
            
            assert exit_code == 1
            assert session_id is None
    
    def test_e_r_04_execute_with_verification_success(self, tmp_path):
        """E-R-04: execute() with verification script success."""
        verify_script = tmp_path / "verify.sh"
        verify_script.write_text("#!/bin/bash\nexit 0")
        verify_script.chmod(0o755)
        
        step_file = tmp_path / "step.json"
        step_data = {
            "prompt": "test prompt",
            "model": "gpt-4",
            "verify": str(verify_script)
        }
        step_file.write_text(json.dumps(step_data))
        
        step_def = load_step_definition(str(step_file))
        wrapper = DevinWrapper(step_def, [])
        
        with patch('subprocess.run') as mock_run:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "Starting new session: sess_verify_123"
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            
            exit_code, session_id = wrapper.execute()
            
            assert exit_code == 0
            assert session_id == "sess_verify_123"
    
    def test_e_r_05_execute_with_verification_failure(self, tmp_path):
        """E-R-05: execute() returns verification failure exit code."""
        verify_script = tmp_path / "verify.sh"
        verify_script.write_text("#!/bin/bash\nexit 1")
        verify_script.chmod(0o755)
        
        step_file = tmp_path / "step.json"
        step_data = {
            "prompt": "test prompt",
            "model": "gpt-4",
            "verify": str(verify_script)
        }
        step_file.write_text(json.dumps(step_data))
        
        step_def = load_step_definition(str(step_file))
        wrapper = DevinWrapper(step_def, [])
        
        with patch('subprocess.run') as mock_run:
            # First call is devin, second is verification
            devin_result = Mock()
            devin_result.returncode = 0
            devin_result.stdout = "Starting new session: sess_fail_123"
            devin_result.stderr = ""
            
            verify_result = Mock()
            verify_result.returncode = 1
            verify_result.stderr = "Verification failed"
            
            mock_run.side_effect = [devin_result, verify_result]
            
            exit_code, session_id = wrapper.execute()
            
            assert exit_code == 1
            assert session_id == "sess_fail_123"
    
    def test_e_r_06_execute_returns_session_id_with_multiple_patterns(self, tmp_path):
        """E-R-06: execute() extracts session ID using multiple patterns."""
        step_file = tmp_path / "step.json"
        step_data = {
            "prompt": "test prompt",
            "model": "gpt-4"
        }
        step_file.write_text(json.dumps(step_data))
        
        step_def = load_step_definition(str(step_file))
        wrapper = DevinWrapper(step_def, [])
        
        with patch('subprocess.run') as mock_run:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "Session sess_pattern2 started"
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            
            exit_code, session_id = wrapper.execute()
            
            assert exit_code == 0
            assert session_id == "sess_pattern2"
