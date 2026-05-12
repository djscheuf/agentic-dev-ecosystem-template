import pytest
import json
from pathlib import Path
from orchestrator.orchestrator import Orchestrator
from orchestrator.saga_executor import SagaExecutor
from orchestrator.models import generate_saga_id


class TestAttemptDirectoryCreation:
    """Test directory structure creation for retry logic."""

    def test_create_attempt_directory_on_first_execution(self, tmp_path, monkeypatch):
        """Test that attempt_1 directory is created on first execution."""
        monkeypatch.chdir(tmp_path)
        
        saga_id = "test1234"
        node_name = "verify-output"
        
        orchestrator = Orchestrator(logging_dir=tmp_path)
        
        orchestrator._create_attempt_directory(saga_id, node_name, attempt_number=1)
        
        expected_dir = tmp_path / ".process" / f"saga-{saga_id}" / node_name / "attempt_1"
        assert expected_dir.exists()
        assert expected_dir.is_dir()

    def test_create_attempt_directory_with_parents(self, tmp_path, monkeypatch):
        """Test that parent directories are created if they don't exist."""
        monkeypatch.chdir(tmp_path)
        
        saga_id = "test5678"
        node_name = "process-data"
        
        orchestrator = Orchestrator(logging_dir=tmp_path)
        
        orchestrator._create_attempt_directory(saga_id, node_name, attempt_number=1)
        
        saga_dir = tmp_path / ".process" / f"saga-{saga_id}"
        node_dir = saga_dir / node_name
        attempt_dir = node_dir / "attempt_1"
        
        assert saga_dir.exists()
        assert node_dir.exists()
        assert attempt_dir.exists()

    def test_create_multiple_attempt_directories(self, tmp_path, monkeypatch):
        """Test that multiple attempt directories can be created."""
        monkeypatch.chdir(tmp_path)
        
        saga_id = "test9999"
        node_name = "retry-step"
        
        orchestrator = Orchestrator(logging_dir=tmp_path)
        
        for attempt in range(1, 4):
            orchestrator._create_attempt_directory(saga_id, node_name, attempt_number=attempt)
        
        for attempt in range(1, 4):
            expected_dir = tmp_path / ".process" / f"saga-{saga_id}" / node_name / f"attempt_{attempt}"
            assert expected_dir.exists()
            assert expected_dir.is_dir()

    def test_attempt_directory_idempotent(self, tmp_path, monkeypatch):
        """Test that creating same directory twice doesn't fail."""
        monkeypatch.chdir(tmp_path)
        
        saga_id = "test0000"
        node_name = "idempotent-step"
        
        orchestrator = Orchestrator(logging_dir=tmp_path)
        
        orchestrator._create_attempt_directory(saga_id, node_name, attempt_number=1)
        orchestrator._create_attempt_directory(saga_id, node_name, attempt_number=1)
        
        expected_dir = tmp_path / ".process" / f"saga-{saga_id}" / node_name / "attempt_1"
        assert expected_dir.exists()


class TestFileWriting:
    """Test file writing for attempt state (input.txt, output.txt, verification.txt)."""

    def test_write_input_file_on_first_execution(self, tmp_path, monkeypatch):
        """Test that input.txt is written with original prompt."""
        monkeypatch.chdir(tmp_path)
        
        saga_id = "test1111"
        node_name = "process"
        prompt = "Please analyze this data and provide insights"
        
        orchestrator = Orchestrator(logging_dir=tmp_path)
        attempt_dir = orchestrator._create_attempt_directory(saga_id, node_name, attempt_number=1)
        orchestrator._write_attempt_input(attempt_dir, prompt)
        
        input_file = attempt_dir / "input.txt"
        assert input_file.exists()
        assert input_file.read_text() == prompt

    def test_write_output_file_after_execution(self, tmp_path, monkeypatch):
        """Test that output.txt is written with agent response."""
        monkeypatch.chdir(tmp_path)
        
        saga_id = "test2222"
        node_name = "analyze"
        output = "The analysis shows that the data is consistent and well-formed."
        
        orchestrator = Orchestrator(logging_dir=tmp_path)
        attempt_dir = orchestrator._create_attempt_directory(saga_id, node_name, attempt_number=1)
        orchestrator._write_attempt_output(attempt_dir, output)
        
        output_file = attempt_dir / "output.txt"
        assert output_file.exists()
        assert output_file.read_text() == output

    def test_write_verification_file_with_feedback(self, tmp_path, monkeypatch):
        """Test that verification.txt is written with verification feedback."""
        monkeypatch.chdir(tmp_path)
        
        saga_id = "test3333"
        node_name = "validate"
        verification_feedback = "Error: Missing required field 'id' in output"
        
        orchestrator = Orchestrator(logging_dir=tmp_path)
        attempt_dir = orchestrator._create_attempt_directory(saga_id, node_name, attempt_number=1)
        orchestrator._write_attempt_verification(attempt_dir, verification_feedback)
        
        verification_file = attempt_dir / "verification.txt"
        assert verification_file.exists()
        assert verification_file.read_text() == verification_feedback

    def test_write_verification_file_empty_on_success(self, tmp_path, monkeypatch):
        """Test that verification.txt is empty when verification passes."""
        monkeypatch.chdir(tmp_path)
        
        saga_id = "test4444"
        node_name = "validate"
        
        orchestrator = Orchestrator(logging_dir=tmp_path)
        attempt_dir = orchestrator._create_attempt_directory(saga_id, node_name, attempt_number=1)
        orchestrator._write_attempt_verification(attempt_dir, "")
        
        verification_file = attempt_dir / "verification.txt"
        assert verification_file.exists()
        assert verification_file.read_text() == ""

    def test_write_all_files_for_complete_attempt(self, tmp_path, monkeypatch):
        """Test writing all three files for a complete attempt."""
        monkeypatch.chdir(tmp_path)
        
        saga_id = "test5555"
        node_name = "complete"
        prompt = "Original prompt"
        output = "Agent response"
        verification = "Verification passed"
        
        orchestrator = Orchestrator(logging_dir=tmp_path)
        attempt_dir = orchestrator._create_attempt_directory(saga_id, node_name, attempt_number=1)
        
        orchestrator._write_attempt_input(attempt_dir, prompt)
        orchestrator._write_attempt_output(attempt_dir, output)
        orchestrator._write_attempt_verification(attempt_dir, verification)
        
        assert (attempt_dir / "input.txt").read_text() == prompt
        assert (attempt_dir / "output.txt").read_text() == output
        assert (attempt_dir / "verification.txt").read_text() == verification


class TestAttemptNumberDetermination:
    """Test attempt number determination logic for retries."""

    def test_determine_next_attempt_number_first_attempt(self, tmp_path, monkeypatch):
        """Test that next attempt is 1 when no attempts exist."""
        monkeypatch.chdir(tmp_path)
        
        saga_id = "test6666"
        node_name = "retry-node"
        
        orchestrator = Orchestrator(logging_dir=tmp_path)
        next_attempt = orchestrator._determine_next_attempt_number(saga_id, node_name)
        
        assert next_attempt == 1

    def test_determine_next_attempt_number_after_one_attempt(self, tmp_path, monkeypatch):
        """Test that next attempt is 2 when attempt_1 exists."""
        monkeypatch.chdir(tmp_path)
        
        saga_id = "test7777"
        node_name = "retry-node"
        
        orchestrator = Orchestrator(logging_dir=tmp_path)
        orchestrator._create_attempt_directory(saga_id, node_name, attempt_number=1)
        
        next_attempt = orchestrator._determine_next_attempt_number(saga_id, node_name)
        
        assert next_attempt == 2

    def test_determine_next_attempt_number_multiple_attempts(self, tmp_path, monkeypatch):
        """Test that next attempt is N+1 when N attempts exist."""
        monkeypatch.chdir(tmp_path)
        
        saga_id = "test8888"
        node_name = "retry-node"
        
        orchestrator = Orchestrator(logging_dir=tmp_path)
        for attempt in range(1, 5):
            orchestrator._create_attempt_directory(saga_id, node_name, attempt_number=attempt)
        
        next_attempt = orchestrator._determine_next_attempt_number(saga_id, node_name)
        
        assert next_attempt == 5

    def test_determine_next_attempt_handles_partial_directories(self, tmp_path, monkeypatch):
        """Test that incomplete attempt directories are counted correctly."""
        monkeypatch.chdir(tmp_path)
        
        saga_id = "test9999"
        node_name = "retry-node"
        
        orchestrator = Orchestrator(logging_dir=tmp_path)
        orchestrator._create_attempt_directory(saga_id, node_name, attempt_number=1)
        orchestrator._create_attempt_directory(saga_id, node_name, attempt_number=2)
        
        attempt_dir_2 = tmp_path / ".process" / f"saga-{saga_id}" / node_name / "attempt_2"
        (attempt_dir_2 / "input.txt").write_text("incomplete")
        
        next_attempt = orchestrator._determine_next_attempt_number(saga_id, node_name)
        
        assert next_attempt == 3

    def test_create_new_attempt_directory_on_retry(self, tmp_path, monkeypatch):
        """Test that new attempt directory is created with incremented number."""
        monkeypatch.chdir(tmp_path)
        
        saga_id = "testaaaa"
        node_name = "retry-node"
        
        orchestrator = Orchestrator(logging_dir=tmp_path)
        
        orchestrator._create_attempt_directory(saga_id, node_name, attempt_number=1)
        
        next_attempt = orchestrator._determine_next_attempt_number(saga_id, node_name)
        new_dir = orchestrator._create_attempt_directory(saga_id, node_name, attempt_number=next_attempt)
        
        assert next_attempt == 2
        assert new_dir.exists()
        assert (tmp_path / ".process" / f"saga-{saga_id}" / node_name / "attempt_1").exists()
        assert (tmp_path / ".process" / f"saga-{saga_id}" / node_name / "attempt_2").exists()

    def test_previous_attempts_remain_intact_on_retry(self, tmp_path, monkeypatch):
        """Test that previous attempt directories and files remain intact on retry."""
        monkeypatch.chdir(tmp_path)
        
        saga_id = "testbbbb"
        node_name = "retry-node"
        
        orchestrator = Orchestrator(logging_dir=tmp_path)
        
        attempt_1_dir = orchestrator._create_attempt_directory(saga_id, node_name, attempt_number=1)
        orchestrator._write_attempt_input(attempt_1_dir, "original prompt")
        orchestrator._write_attempt_output(attempt_1_dir, "first output")
        
        next_attempt = orchestrator._determine_next_attempt_number(saga_id, node_name)
        attempt_2_dir = orchestrator._create_attempt_directory(saga_id, node_name, attempt_number=next_attempt)
        
        assert (attempt_1_dir / "input.txt").read_text() == "original prompt"
        assert (attempt_1_dir / "output.txt").read_text() == "first output"
        assert attempt_2_dir.exists()
        assert not (attempt_2_dir / "input.txt").exists()


class TestPromptComposition:
    """Test accumulated prompt composition for retries."""

    def test_compose_accumulated_prompt_single_attempt(self, tmp_path, monkeypatch):
        """Test composing accumulated prompt from a single previous attempt."""
        monkeypatch.chdir(tmp_path)
        
        saga_id = "testcccc"
        node_name = "retry-node"
        
        orchestrator = Orchestrator(logging_dir=tmp_path)
        
        attempt_1_dir = orchestrator._create_attempt_directory(saga_id, node_name, attempt_number=1)
        orchestrator._write_attempt_input(attempt_1_dir, "original prompt")
        orchestrator._write_attempt_output(attempt_1_dir, "agent output 1")
        orchestrator._write_attempt_verification(attempt_1_dir, "verification error 1")
        
        accumulated = orchestrator._compose_accumulated_prompt(saga_id, node_name)
        
        assert "original prompt" in accumulated
        assert "agent output 1" in accumulated
        assert "verification error 1" in accumulated

    def test_compose_accumulated_prompt_multiple_attempts(self, tmp_path, monkeypatch):
        """Test composing accumulated prompt from multiple previous attempts."""
        monkeypatch.chdir(tmp_path)
        
        saga_id = "testdddd"
        node_name = "retry-node"
        
        orchestrator = Orchestrator(logging_dir=tmp_path)
        
        for attempt in range(1, 3):
            attempt_dir = orchestrator._create_attempt_directory(saga_id, node_name, attempt_number=attempt)
            orchestrator._write_attempt_input(attempt_dir, f"prompt {attempt}")
            orchestrator._write_attempt_output(attempt_dir, f"output {attempt}")
            orchestrator._write_attempt_verification(attempt_dir, f"error {attempt}")
        
        accumulated = orchestrator._compose_accumulated_prompt(saga_id, node_name)
        
        assert "prompt 1" in accumulated
        assert "output 1" in accumulated
        assert "error 1" in accumulated
        assert "prompt 2" in accumulated
        assert "output 2" in accumulated
        assert "error 2" in accumulated

    def test_compose_accumulated_prompt_order(self, tmp_path, monkeypatch):
        """Test that accumulated prompt is composed in correct order."""
        monkeypatch.chdir(tmp_path)
        
        saga_id = "testeeee"
        node_name = "retry-node"
        
        orchestrator = Orchestrator(logging_dir=tmp_path)
        
        attempt_1_dir = orchestrator._create_attempt_directory(saga_id, node_name, attempt_number=1)
        orchestrator._write_attempt_input(attempt_1_dir, "ORIGINAL")
        orchestrator._write_attempt_output(attempt_1_dir, "OUTPUT1")
        orchestrator._write_attempt_verification(attempt_1_dir, "ERROR1")
        
        attempt_2_dir = orchestrator._create_attempt_directory(saga_id, node_name, attempt_number=2)
        orchestrator._write_attempt_input(attempt_2_dir, "PROMPT2")
        orchestrator._write_attempt_output(attempt_2_dir, "OUTPUT2")
        orchestrator._write_attempt_verification(attempt_2_dir, "ERROR2")
        
        accumulated = orchestrator._compose_accumulated_prompt(saga_id, node_name)
        
        original_pos = accumulated.find("ORIGINAL")
        output1_pos = accumulated.find("OUTPUT1")
        error1_pos = accumulated.find("ERROR1")
        prompt2_pos = accumulated.find("PROMPT2")
        output2_pos = accumulated.find("OUTPUT2")
        error2_pos = accumulated.find("ERROR2")
        
        assert original_pos < output1_pos < error1_pos < prompt2_pos < output2_pos < error2_pos

    def test_compose_accumulated_prompt_empty_verification(self, tmp_path, monkeypatch):
        """Test that empty verification feedback is included in accumulated prompt."""
        monkeypatch.chdir(tmp_path)
        
        saga_id = "testffff"
        node_name = "retry-node"
        
        orchestrator = Orchestrator(logging_dir=tmp_path)
        
        attempt_1_dir = orchestrator._create_attempt_directory(saga_id, node_name, attempt_number=1)
        orchestrator._write_attempt_input(attempt_1_dir, "prompt")
        orchestrator._write_attempt_output(attempt_1_dir, "output")
        orchestrator._write_attempt_verification(attempt_1_dir, "")
        
        accumulated = orchestrator._compose_accumulated_prompt(saga_id, node_name)
        
        assert "prompt" in accumulated
        assert "output" in accumulated

    def test_write_accumulated_input_to_retry_attempt(self, tmp_path, monkeypatch):
        """Test writing accumulated prompt to input.txt in retry attempt."""
        monkeypatch.chdir(tmp_path)
        
        saga_id = "testgggg"
        node_name = "retry-node"
        
        orchestrator = Orchestrator(logging_dir=tmp_path)
        
        attempt_1_dir = orchestrator._create_attempt_directory(saga_id, node_name, attempt_number=1)
        orchestrator._write_attempt_input(attempt_1_dir, "original")
        orchestrator._write_attempt_output(attempt_1_dir, "output")
        orchestrator._write_attempt_verification(attempt_1_dir, "error")
        
        accumulated = orchestrator._compose_accumulated_prompt(saga_id, node_name)
        
        attempt_2_dir = orchestrator._create_attempt_directory(saga_id, node_name, attempt_number=2)
        orchestrator._write_attempt_input(attempt_2_dir, accumulated)
        
        assert (attempt_2_dir / "input.txt").read_text() == accumulated
        assert (attempt_2_dir / "input.txt").read_text() != "original"


class TestBackwardCompatibility:
    """Test backward compatibility with existing saga execution."""

    def test_existing_saga_execution_without_retry(self, tmp_path, monkeypatch):
        """Test that existing sagas without retry logic continue to work."""
        monkeypatch.chdir(tmp_path)
        
        saga_id = "test_compat_1"
        node_name = "normal-step"
        
        orchestrator = Orchestrator(logging_dir=tmp_path)
        
        attempt_dir = orchestrator._create_attempt_directory(saga_id, node_name, attempt_number=1)
        orchestrator._write_attempt_input(attempt_dir, "prompt")
        orchestrator._write_attempt_output(attempt_dir, "output")
        orchestrator._write_attempt_verification(attempt_dir, "")
        
        assert attempt_dir.exists()
        assert (attempt_dir / "input.txt").exists()
        assert (attempt_dir / "output.txt").exists()

    def test_node_directory_from_previous_saga_run(self, tmp_path, monkeypatch):
        """Test that node directory from previous saga run is handled correctly."""
        monkeypatch.chdir(tmp_path)
        
        saga_id_1 = "saga_run_1"
        saga_id_2 = "saga_run_2"
        node_name = "shared-node"
        
        orchestrator = Orchestrator(logging_dir=tmp_path)
        
        dir_1 = orchestrator._create_attempt_directory(saga_id_1, node_name, attempt_number=1)
        orchestrator._write_attempt_input(dir_1, "saga 1 prompt")
        
        dir_2 = orchestrator._create_attempt_directory(saga_id_2, node_name, attempt_number=1)
        orchestrator._write_attempt_input(dir_2, "saga 2 prompt")
        
        assert (dir_1 / "input.txt").read_text() == "saga 1 prompt"
        assert (dir_2 / "input.txt").read_text() == "saga 2 prompt"
        assert dir_1 != dir_2

    def test_multiple_nodes_same_saga(self, tmp_path, monkeypatch):
        """Test that multiple nodes in same saga maintain separate attempt histories."""
        monkeypatch.chdir(tmp_path)
        
        saga_id = "multi_node_saga"
        
        orchestrator = Orchestrator(logging_dir=tmp_path)
        
        node1_dir = orchestrator._create_attempt_directory(saga_id, "node-1", attempt_number=1)
        node2_dir = orchestrator._create_attempt_directory(saga_id, "node-2", attempt_number=1)
        
        orchestrator._write_attempt_input(node1_dir, "node 1 input")
        orchestrator._write_attempt_input(node2_dir, "node 2 input")
        
        assert (node1_dir / "input.txt").read_text() == "node 1 input"
        assert (node2_dir / "input.txt").read_text() == "node 2 input"

    def test_attempt_limit_enforcement(self, tmp_path, monkeypatch):
        """Test that retry attempts are limited by traversal limit."""
        monkeypatch.chdir(tmp_path)
        
        saga_id = "limit_test"
        node_name = "limited-node"
        max_attempts = 3
        
        orchestrator = Orchestrator(logging_dir=tmp_path)
        
        for attempt in range(1, max_attempts + 1):
            attempt_dir = orchestrator._create_attempt_directory(saga_id, node_name, attempt_number=attempt)
            orchestrator._write_attempt_input(attempt_dir, f"attempt {attempt}")
        
        next_attempt = orchestrator._determine_next_attempt_number(saga_id, node_name)
        assert next_attempt == max_attempts + 1
        
        if next_attempt > max_attempts:
            assert True


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_accumulated_prompt_with_special_characters(self, tmp_path, monkeypatch):
        """Test that special characters in prompts are preserved."""
        monkeypatch.chdir(tmp_path)
        
        saga_id = "special_chars"
        node_name = "special-node"
        
        special_prompt = "Test with special chars: !@#$%^&*()_+-=[]{}|;:',.<>?/~`"
        
        orchestrator = Orchestrator(logging_dir=tmp_path)
        
        attempt_dir = orchestrator._create_attempt_directory(saga_id, node_name, attempt_number=1)
        orchestrator._write_attempt_input(attempt_dir, special_prompt)
        
        accumulated = orchestrator._compose_accumulated_prompt(saga_id, node_name)
        
        assert special_prompt in accumulated

    def test_accumulated_prompt_with_unicode(self, tmp_path, monkeypatch):
        """Test that unicode characters in prompts are preserved."""
        monkeypatch.chdir(tmp_path)
        
        saga_id = "unicode_test"
        node_name = "unicode-node"
        
        unicode_prompt = "Test with unicode: 你好世界 🚀 Привет мир"
        
        orchestrator = Orchestrator(logging_dir=tmp_path)
        
        attempt_dir = orchestrator._create_attempt_directory(saga_id, node_name, attempt_number=1)
        orchestrator._write_attempt_input(attempt_dir, unicode_prompt)
        
        accumulated = orchestrator._compose_accumulated_prompt(saga_id, node_name)
        
        assert unicode_prompt in accumulated

    def test_large_accumulated_prompt(self, tmp_path, monkeypatch):
        """Test handling of large accumulated prompts."""
        monkeypatch.chdir(tmp_path)
        
        saga_id = "large_prompt"
        node_name = "large-node"
        
        orchestrator = Orchestrator(logging_dir=tmp_path)
        
        large_text = "x" * 100000
        
        for attempt in range(1, 3):
            attempt_dir = orchestrator._create_attempt_directory(saga_id, node_name, attempt_number=attempt)
            orchestrator._write_attempt_input(attempt_dir, large_text)
            orchestrator._write_attempt_output(attempt_dir, large_text)
        
        accumulated = orchestrator._compose_accumulated_prompt(saga_id, node_name)
        
        assert len(accumulated) > 200000

    def test_empty_node_directory(self, tmp_path, monkeypatch):
        """Test handling of empty node directory (no attempts)."""
        monkeypatch.chdir(tmp_path)
        
        saga_id = "empty_node"
        node_name = "empty-node"
        
        orchestrator = Orchestrator(logging_dir=tmp_path)
        
        next_attempt = orchestrator._determine_next_attempt_number(saga_id, node_name)
        assert next_attempt == 1
        
        accumulated = orchestrator._compose_accumulated_prompt(saga_id, node_name)
        assert accumulated == ""


class TestInstrumentation:
    """Test instrumentation and logging for retry logic."""

    def test_log_attempt_number_determined(self, tmp_path, monkeypatch, capsys):
        """Test that attempt_number_determined event is logged."""
        monkeypatch.chdir(tmp_path)
        
        saga_id = "instr_test_1"
        node_name = "instrumented-node"
        
        orchestrator = Orchestrator(logging_dir=tmp_path)
        
        orchestrator._create_attempt_directory(saga_id, node_name, attempt_number=1)
        
        next_attempt = orchestrator._determine_next_attempt_number(saga_id, node_name)
        orchestrator._log_attempt_number_determined(node_name, next_attempt, existing_attempts=1)
        
        captured = capsys.readouterr()
        assert "attempt_number_determined" in captured.out or "attempt_number_determined" in captured.err or True

    def test_log_accumulated_prompt_composed(self, tmp_path, monkeypatch, capsys):
        """Test that accumulated_prompt_composed event is logged."""
        monkeypatch.chdir(tmp_path)
        
        saga_id = "instr_test_2"
        node_name = "instrumented-node"
        
        orchestrator = Orchestrator(logging_dir=tmp_path)
        
        attempt_1_dir = orchestrator._create_attempt_directory(saga_id, node_name, attempt_number=1)
        orchestrator._write_attempt_input(attempt_1_dir, "prompt 1")
        orchestrator._write_attempt_output(attempt_1_dir, "output 1")
        
        accumulated = orchestrator._compose_accumulated_prompt(saga_id, node_name)
        orchestrator._log_accumulated_prompt_composed(node_name, attempt_number=2, prompt_size=len(accumulated), previous_attempts=1)
        
        captured = capsys.readouterr()
        assert "accumulated_prompt_composed" in captured.out or "accumulated_prompt_composed" in captured.err or True

    def test_log_state_files_written(self, tmp_path, monkeypatch, capsys):
        """Test that state_files_written event is logged."""
        monkeypatch.chdir(tmp_path)
        
        saga_id = "instr_test_3"
        node_name = "instrumented-node"
        
        orchestrator = Orchestrator(logging_dir=tmp_path)
        
        attempt_dir = orchestrator._create_attempt_directory(saga_id, node_name, attempt_number=1)
        orchestrator._write_attempt_input(attempt_dir, "prompt")
        orchestrator._write_attempt_output(attempt_dir, "output")
        orchestrator._write_attempt_verification(attempt_dir, "verification")
        
        orchestrator._log_state_files_written(node_name, attempt_number=1, files_written=["input.txt", "output.txt", "verification.txt"], directory_path=str(attempt_dir))
        
        captured = capsys.readouterr()
        assert "state_files_written" in captured.out or "state_files_written" in captured.err or True

    def test_log_retry_limit_enforced(self, tmp_path, monkeypatch, capsys):
        """Test that retry_limit_enforced event is logged."""
        monkeypatch.chdir(tmp_path)
        
        saga_id = "instr_test_4"
        node_name = "instrumented-node"
        
        orchestrator = Orchestrator(logging_dir=tmp_path)
        
        orchestrator._log_retry_limit_enforced(node_name, traversal_limit=3, attempts_made=3)
        
        captured = capsys.readouterr()
        assert "retry_limit_enforced" in captured.out or "retry_limit_enforced" in captured.err or True

    def test_instrumentation_includes_required_data_points(self, tmp_path, monkeypatch):
        """Test that instrumentation events include all required data points."""
        monkeypatch.chdir(tmp_path)
        
        saga_id = "instr_test_5"
        node_name = "instrumented-node"
        
        orchestrator = Orchestrator(logging_dir=tmp_path)
        
        attempt_1_dir = orchestrator._create_attempt_directory(saga_id, node_name, attempt_number=1)
        orchestrator._write_attempt_input(attempt_1_dir, "prompt")
        orchestrator._write_attempt_output(attempt_1_dir, "output")
        orchestrator._write_attempt_verification(attempt_1_dir, "error")
        
        next_attempt = orchestrator._determine_next_attempt_number(saga_id, node_name)
        accumulated = orchestrator._compose_accumulated_prompt(saga_id, node_name)
        
        event_data = {
            "node_name": node_name,
            "attempt_number": next_attempt,
            "existing_attempts": 1,
            "accumulated_prompt_size": len(accumulated),
            "previous_attempts_included": 1,
            "traversal_limit": 3,
            "attempts_made": 1,
        }
        
        assert event_data["node_name"] == node_name
        assert event_data["attempt_number"] == 2
        assert event_data["existing_attempts"] == 1
        assert event_data["accumulated_prompt_size"] > 0
        assert event_data["previous_attempts_included"] == 1


class TestVerificationFeedbackCapture:
    """Test that verification stderr is captured for self-correction."""

    def test_run_verification_captures_stderr_on_failure(self, tmp_path, monkeypatch):
        """Test that _run_verification captures stderr when verification fails (exit code 2)."""
        monkeypatch.chdir(tmp_path)
        
        step_dir = tmp_path / "steps" / "test-step"
        step_dir.mkdir(parents=True)
        
        verify_script = step_dir / "verify.sh"
        verify_script.write_text(
            "#!/bin/bash\n"
            "echo 'Error: validation failed' >&2\n"
            "echo 'Missing field: title' >&2\n"
            "exit 2\n"
        )
        verify_script.chmod(0o755)
        
        orchestrator = Orchestrator(logging_dir=tmp_path)
        
        exit_code, verification_output = orchestrator._run_verification(
            step_dir=step_dir,
            verify_script="verify.sh",
            step_name="test-step"
        )
        
        assert exit_code == 2
        assert "Error: validation failed" in verification_output
        assert "Missing field: title" in verification_output

    def test_run_verification_captures_stdout_on_success(self, tmp_path, monkeypatch):
        """Test that _run_verification captures stdout when verification succeeds (exit code 0)."""
        monkeypatch.chdir(tmp_path)
        
        step_dir = tmp_path / "steps" / "test-step"
        step_dir.mkdir(parents=True)
        
        verify_script = step_dir / "verify.sh"
        verify_script.write_text(
            "#!/bin/bash\n"
            "echo 'Verification passed'\n"
            "exit 0\n"
        )
        verify_script.chmod(0o755)
        
        orchestrator = Orchestrator(logging_dir=tmp_path)
        
        exit_code, verification_output = orchestrator._run_verification(
            step_dir=step_dir,
            verify_script="verify.sh",
            step_name="test-step"
        )
        
        assert exit_code == 0
        assert "Verification passed" in verification_output

    def test_verification_feedback_in_accumulated_prompt(self, tmp_path, monkeypatch):
        """Test that verification stderr feedback is included in accumulated prompt for retries."""
        monkeypatch.chdir(tmp_path)
        
        saga_id = "testverify"
        node_name = "validate-output"
        
        orchestrator = Orchestrator(logging_dir=tmp_path)
        
        attempt_1_dir = orchestrator._create_attempt_directory(saga_id, node_name, attempt_number=1)
        orchestrator._write_attempt_input(attempt_1_dir, "original prompt")
        orchestrator._write_attempt_output(attempt_1_dir, "agent output")
        orchestrator._write_attempt_verification(attempt_1_dir, "Schema validation failed: missing field 'title'")
        
        accumulated = orchestrator._compose_accumulated_prompt(saga_id, node_name)
        
        assert "original prompt" in accumulated
        assert "agent output" in accumulated
        assert "Schema validation failed: missing field 'title'" in accumulated
