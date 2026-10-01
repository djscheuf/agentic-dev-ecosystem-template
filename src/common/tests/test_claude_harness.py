"""Tests for ClaudeHarness adapter implementation."""

import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from common.claude_harness import (
    ClaudeHarness,
    ClaudeHarnessConfig,
    read_claude_usage_result,
)
from common.harness import HarnessUsage
from common.workflow_logger import WorkflowLoggerConfig, activity_log_context


class TestClaudeHarnessConfig:
    """Tests for ClaudeHarnessConfig validation and initialization."""

    def test_valid_model_and_permission_mode_initializes_successfully(self) -> None:
        """config-001: Valid config with model and permission_mode."""
        config = ClaudeHarnessConfig.from_mapping({
            "claude": {
                "model": "claude-opus-5-5",
                "permission_mode": "dontAsk"
            }
        })

        assert config.model == "claude-opus-5-5"
        assert config.permission_mode == "dontAsk"

    def test_defaults_applied_when_fields_omitted(self) -> None:
        """config-002: Defaults applied when fields omitted."""
        config = ClaudeHarnessConfig.from_mapping({})

        assert config.model is not None
        assert config.permission_mode == "dontAsk"

    def test_defaults_applied_with_empty_claude_namespace(self) -> None:
        """config-002: Defaults applied with empty 'claude' namespace."""
        config = ClaudeHarnessConfig.from_mapping({"claude": {}})

        assert config.model is not None
        assert config.permission_mode == "dontAsk"

    def test_invalid_permission_mode_raises_validation_error(self) -> None:
        """config-003: Invalid permission_mode raises validation error."""
        with pytest.raises(ValueError, match="invalid_value: claude.permission_mode"):
            ClaudeHarnessConfig.from_mapping({
                "claude": {"permission_mode": "accept-edits"}  # Devin mode, not Claude's
            })

    def test_invalid_model_non_string_raises_validation_error(self) -> None:
        """config-004: Non-string model raises validation error."""
        with pytest.raises(ValueError, match="invalid_value: claude.model"):
            ClaudeHarnessConfig.from_mapping({
                "claude": {"model": 123}
            })

    def test_invalid_model_blank_raises_validation_error(self) -> None:
        """config-004: Blank model raises validation error."""
        with pytest.raises(ValueError, match="invalid_value: claude.model"):
            ClaudeHarnessConfig.from_mapping({
                "claude": {"model": ""}
            })

    def test_mapping_proxy_type_handled_correctly(self) -> None:
        """config-005: MappingProxyType parsed without dict() copy."""
        from types import MappingProxyType

        proxy = MappingProxyType({
            "claude": {"model": "claude-opus-5-5", "permission_mode": "dontAsk"}
        })
        config = ClaudeHarnessConfig.from_mapping(proxy)

        assert config.model == "claude-opus-5-5"
        assert config.permission_mode == "dontAsk"

    @pytest.mark.parametrize("mode", ["default", "acceptEdits", "plan", "auto", "dontAsk", "bypassPermissions"])
    def test_all_supported_modes_accepted(self, mode: str) -> None:
        """config-006: All six supported modes validate successfully."""
        config = ClaudeHarnessConfig.from_mapping({
            "claude": {"permission_mode": mode}
        })
        assert config.permission_mode == mode

    @pytest.mark.parametrize("devin_mode", ["accept-edits", "dangerous"])
    def test_devin_modes_rejected_never_accepted_as_valid(self, devin_mode: str) -> None:
        """config-007: Devin modes rejected, never accepted."""
        with pytest.raises(ValueError, match="invalid_value: claude.permission_mode"):
            ClaudeHarnessConfig.from_mapping({
                "claude": {"permission_mode": devin_mode}
            })


class TestClaudeHarnessRun:
    """Tests for ClaudeHarness.run() subprocess invocation."""

    def test_valid_prompt_launches_subprocess_with_correct_args(self) -> None:
        """harness-001: Subprocess invoked with correct CLI arguments."""
        calls = []

        def runner(command, **kwargs):
            calls.append((command, kwargs))
            return subprocess.CompletedProcess(command, 0, "", "")

        harness = ClaudeHarness(runner=runner)
        harness.run(
            "test prompt",
            cwd=Path("/repo"),
            config={"claude": {"model": "claude-opus-5-5", "permission_mode": "dontAsk"}}
        )

        assert len(calls) == 1
        command, kwargs = calls[0]
        assert command[:2] == ["claude", "-p"]
        assert "--permission-mode" in command
        assert "dontAsk" in command
        assert "--model" in command
        assert "claude-opus-5-5" in command
        assert "--output-format" in command
        assert "stream-json" in command
        assert "--verbose" in command
        assert "--" in command
        assert "test prompt" == command[-1]

    def test_prompt_with_dashes_treated_as_text_not_flag(self) -> None:
        """harness-002: Prompt starting with '--' not parsed as flag."""
        calls = []

        def runner(command, **kwargs):
            calls.append((command, kwargs))
            return subprocess.CompletedProcess(command, 0, "", "")

        harness = ClaudeHarness(runner=runner)
        harness.run(
            "--flag-like text",
            cwd=Path("/repo"),
            config={}
        )

        command = calls[0][0]
        assert "--" in command
        dash_index = command.index("--")
        assert command[dash_index + 1] == "--flag-like text"

    def test_os_error_on_launch_converted_to_runtime_error(self) -> None:
        """harness-003: OSError converted to RuntimeError('claude_launch_failed')."""
        def runner(command, **kwargs):
            raise OSError("No such file or directory")

        harness = ClaudeHarness(runner=runner)
        with pytest.raises(RuntimeError, match="claude_launch_failed"):
            harness.run("test", cwd=Path("/repo"), config={})

    def test_stdout_preserved_as_full_ndjson(self) -> None:
        """harness-004: Full raw NDJSON preserved in stdout."""
        ndjson_output = '{"type":"content"}\n{"type":"result","usage":{"input_tokens":10}}\n'

        def runner(command, **kwargs):
            return subprocess.CompletedProcess(command, 0, ndjson_output, "")

        harness = ClaudeHarness(runner=runner)
        result = harness.run("test", cwd=Path("/repo"), config={})

        assert result.stdout == ndjson_output

    def test_subprocess_cwd_matches_invocation_cwd(self) -> None:
        """harness-005: subprocess.run called with correct cwd."""
        calls = []

        def runner(command, **kwargs):
            calls.append((command, kwargs))
            return subprocess.CompletedProcess(command, 0, "", "")

        harness = ClaudeHarness(runner=runner)
        harness.run("test", cwd=Path("/custom/path"), config={})

        _, kwargs = calls[0]
        assert kwargs.get("cwd") == str(Path("/custom/path"))

    def test_capture_output_and_text_flags_set(self) -> None:
        """harness-006: subprocess.run called with capture_output=True, text=True."""
        calls = []

        def runner(command, **kwargs):
            calls.append((command, kwargs))
            return subprocess.CompletedProcess(command, 0, "", "")

        harness = ClaudeHarness(runner=runner)
        harness.run("test", cwd=Path("/repo"), config={})

        _, kwargs = calls[0]
        assert kwargs.get("capture_output") is True
        assert kwargs.get("text") is True

    def test_exit_code_and_stderr_preserved_unchanged(self) -> None:
        """harness-007: Exit code and stderr preserved from subprocess."""
        def runner(command, **kwargs):
            return subprocess.CompletedProcess(command, 42, "", "error text")

        harness = ClaudeHarness(runner=runner)
        result = harness.run("test", cwd=Path("/repo"), config={})

        assert result.exit_code == 42
        assert result.stderr == "error text"


class TestReadClaudeUsageResult:
    """Tests for NDJSON usage parsing."""

    def test_valid_terminal_event_extracts_usage_correctly(self) -> None:
        """parse-001: Valid terminal event extracts usage."""
        ndjson = json.dumps({"type": "result", "usage": {
            "input_tokens": 100,
            "output_tokens": 50,
            "cache_read_input_tokens": 10
        }, "total_cost_usd": 0.50}) + "\n"

        usage, error = read_claude_usage_result(ndjson)

        assert error is None
        assert usage is not None
        assert usage.prompt_tokens == 100
        assert usage.completion_tokens == 50
        assert usage.cached_tokens == 10
        assert usage.cost_usd == 0.50

    def test_field_mapping_correct_coercion(self) -> None:
        """parse-002: Field mapping and coercion correct."""
        ndjson = json.dumps({"type": "result", "usage": {
            "input_tokens": 100,
            "output_tokens": 50,
            "cache_read_input_tokens": 10
        }, "total_cost_usd": 0.75}) + "\n"

        usage, error = read_claude_usage_result(ndjson)

        assert error is None
        assert usage.prompt_tokens == 100
        assert usage.completion_tokens == 50
        assert usage.cached_tokens == 10
        assert usage.cost_usd == 0.75

    def test_missing_result_event_returns_error_category(self) -> None:
        """parse-003: Missing result event returns error_category."""
        ndjson = json.dumps({"type": "content", "text": "hello"}) + "\n"

        usage, error = read_claude_usage_result(ndjson)

        assert usage is None
        assert error == "missing_result_event"

    def test_malformed_json_returns_error_category(self) -> None:
        """parse-004: Malformed JSON returns error_category."""
        ndjson = "{invalid json}\n"

        usage, error = read_claude_usage_result(ndjson)

        assert usage is None
        assert error == "malformed_json"

    def test_truncated_stream_returns_error_category(self) -> None:
        """parse-005: Truncated stream returns error_category."""
        ndjson = '{"type":"result","usage":{'  # Incomplete

        usage, error = read_claude_usage_result(ndjson)

        assert usage is None
        assert error == "truncated_stream"

    def test_multiple_result_events_keeps_last_only(self) -> None:
        """parse-006: Multiple result events, keeps last only."""
        ndjson = (
            json.dumps({"type": "result", "usage": {"input_tokens": 10}, "total_cost_usd": 0.10}) + "\n" +
            json.dumps({"type": "result", "usage": {"input_tokens": 100}, "total_cost_usd": 0.50}) + "\n"
        )

        usage, error = read_claude_usage_result(ndjson)

        assert error is None
        assert usage.prompt_tokens == 100
        assert usage.cost_usd == 0.50

    def test_non_result_events_ignored_focus_on_result_only(self) -> None:
        """parse-007: Only result type events processed."""
        ndjson = (
            json.dumps({"type": "content", "text": "hello"}) + "\n" +
            json.dumps({"type": "result", "usage": {"input_tokens": 50}, "total_cost_usd": 0.25}) + "\n"
        )

        usage, error = read_claude_usage_result(ndjson)

        assert error is None
        assert usage.prompt_tokens == 50

    def test_boolean_values_rejected_via_helpers(self) -> None:
        """parse-008: Boolean values rejected by _token() helper."""
        ndjson = json.dumps({"type": "result", "usage": {
            "input_tokens": True,
            "output_tokens": 50
        }, "total_cost_usd": 0.25}) + "\n"

        usage, error = read_claude_usage_result(ndjson)

        assert error is None
        assert usage.prompt_tokens is None
        assert usage.completion_tokens == 50

    def test_cost_coercion_numeric_magnitude_agnostic(self) -> None:
        """parse-009: Cost coercion works with various magnitudes."""
        test_cases = [
            (0.50, 0.50),
            (0.005, 0.005),
            (5.0, 5.0),
            (0, 0.0),
        ]

        for cost_value, expected in test_cases:
            ndjson = json.dumps({"type": "result", "usage": {
                "input_tokens": 10
            }, "total_cost_usd": cost_value}) + "\n"

            usage, error = read_claude_usage_result(ndjson)

            assert error is None, f"Failed for cost_value={cost_value}"
            assert usage.cost_usd == expected, f"Failed for cost_value={cost_value}"
