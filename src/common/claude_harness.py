"""Harness implementation backed by the Claude CLI."""

import json
import subprocess
import tempfile
import time
from contextlib import ExitStack
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, ClassVar, Mapping

from .harness import HarnessResult, HarnessUsage
from .harness_usage import coerce_cost, coerce_token
from .invocation_context import get_current_skill_name
from .workflow_logger import (
    get_activity_artifact_dir,
    get_activity_logger,
    get_claude_logger,
    get_claude_log_path,
)

DEFAULT_MODEL = "claude-opus-5-5"
DEFAULT_PERMISSION_MODE = "dontAsk"
SUPPORTED_PERMISSION_MODES = frozenset({"default", "acceptEdits", "plan", "auto", "dontAsk", "bypassPermissions"})
_SUPPORTED_KEYS = frozenset({"model", "permission_mode"})


@dataclass(frozen=True)
class ClaudeHarnessConfig:
    model: str = DEFAULT_MODEL
    permission_mode: str = DEFAULT_PERMISSION_MODE

    @classmethod
    def from_mapping(cls, config: Mapping[str, object]) -> "ClaudeHarnessConfig":
        namespace = config.get("claude", {})
        if not isinstance(namespace, Mapping):
            raise ValueError("invalid_namespace_type: claude")
        unknown = set(namespace) - _SUPPORTED_KEYS
        if unknown:
            raise ValueError(f"unknown_key: claude.{sorted(unknown)[0]}")
        model = namespace.get("model", DEFAULT_MODEL)
        permission_mode = namespace.get("permission_mode", DEFAULT_PERMISSION_MODE)
        if not isinstance(model, str) or not model.strip():
            raise ValueError("invalid_value: claude.model")
        if not isinstance(permission_mode, str) or permission_mode not in SUPPORTED_PERMISSION_MODES:
            raise ValueError("invalid_value: claude.permission_mode")
        return cls(model=model, permission_mode=permission_mode)


def read_claude_usage_result(ndjson_text: str) -> tuple[HarnessUsage | None, str | None]:
    """Parse Claude NDJSON output for terminal result event and extract usage."""
    lines = ndjson_text.splitlines()
    last_result_event = None
    has_incomplete_final_line = False

    for i, line in enumerate(lines):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            is_final_line = i == len(lines) - 1
            line_stripped = line.strip()
            if is_final_line and line_stripped and line_stripped.startswith("{") and not line_stripped.endswith("}"):
                has_incomplete_final_line = True
                continue
            return None, "malformed_json"

        if isinstance(event, dict) and event.get("type") == "result":
            last_result_event = event

    if has_incomplete_final_line:
        return None, "truncated_stream"

    if last_result_event is None:
        return None, "missing_result_event"

    usage_obj = last_result_event.get("usage")
    if not isinstance(usage_obj, dict):
        return None, "invalid_document"

    return HarnessUsage(
        prompt_tokens=coerce_token(usage_obj.get("input_tokens")),
        completion_tokens=coerce_token(usage_obj.get("output_tokens")),
        cached_tokens=coerce_token(usage_obj.get("cache_read_input_tokens")),
        cost_usd=coerce_cost(last_result_event.get("total_cost_usd")),
    ), None


class ClaudeHarness:
    config_namespace: ClassVar[str] = "claude"
    default_model: ClassVar[str] = DEFAULT_MODEL
    default_permission_mode: ClassVar[str] = DEFAULT_PERMISSION_MODE

    def __init__(
        self,
        *,
        runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    ) -> None:
        self._runner = runner

    def run(
        self,
        prompt: str,
        *,
        cwd: Path,
        config: Mapping[str, object],
    ) -> HarnessResult:
        profile = ClaudeHarnessConfig.from_mapping(config)
        skill_name = get_current_skill_name() or ""
        with ExitStack() as stack:
            artifact_dir = get_activity_artifact_dir()
            storage_mode = "activity_artifact" if artifact_dir else "temporary"
            export_dir = artifact_dir or Path(stack.enter_context(tempfile.TemporaryDirectory()))
            export_path = export_dir / "claude-trajectory.jsonl"
            activity_logger = get_activity_logger()
            claude_logger = get_claude_logger()
            activity_logger.info(
                "SelectClaudeTelemetrySource storage_mode=%s export_path=%s",
                storage_mode,
                export_path,
            )
            claude_logger.info(
                "SelectClaudeTelemetrySource storage_mode=%s export_path=%s",
                storage_mode,
                export_path,
            )
            command = [
                "claude", "-p",
                "--permission-mode", profile.permission_mode,
                "--model", profile.model,
                "--output-format", "stream-json",
                "--verbose",
                "--", prompt,
            ]
            activity_logger.info(
                "StartClaudeInvocation skill_name=%s model=%s permission_mode=%s",
                skill_name,
                profile.model,
                profile.permission_mode,
            )
            start = time.monotonic()
            try:
                result = self._runner(command, cwd=str(cwd), capture_output=True, text=True)
            except OSError as exc:
                activity_logger.error(
                    "FailClaudeInvocationLaunch skill_name=%s error_category=claude_launch_failed",
                    skill_name,
                )
                claude_logger.error(
                    "FailClaudeInvocationLaunch skill_name=%s error_category=claude_launch_failed",
                    skill_name,
                )
                raise RuntimeError("claude_launch_failed") from exc
            duration_ms = int((time.monotonic() - start) * 1000)
            export_path.write_text(result.stdout)
            usage, error_category = read_claude_usage_result(result.stdout)
            if error_category:
                activity_logger.warning(
                    "RejectClaudeTelemetry storage_mode=%s error_category=%s",
                    storage_mode,
                    error_category,
                )
                claude_logger.warning(
                    "RejectClaudeTelemetry storage_mode=%s error_category=%s",
                    storage_mode,
                    error_category,
                )
            activity_logger.info(
                "CompleteClaudeInvocation exit_code=%s duration_ms=%s usage_available=%s agent_log_path=%s",
                result.returncode,
                duration_ms,
                usage is not None,
                get_claude_log_path() or "unknown",
            )
            claude_logger.info(
                "CompleteClaudeInvocation exit_code=%s duration_ms=%s usage_available=%s",
                result.returncode,
                duration_ms,
                usage is not None,
            )
            if result.stdout:
                claude_logger.debug("--- stdout ---")
                for line in result.stdout.splitlines():
                    claude_logger.debug("%s", line)
            if result.stderr:
                claude_logger.debug("--- stderr ---")
                for line in result.stderr.splitlines():
                    claude_logger.debug("%s", line)
        return HarnessResult(result.returncode, result.stdout, result.stderr, usage)
