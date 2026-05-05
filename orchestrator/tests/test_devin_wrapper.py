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
            
            exit_code = wrapper.execute()
            
            assert exit_code == 0
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
