import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

from common.devin_harness import DevinHarness
from common.harness import HarnessUsage
from common.workflow_logger import WorkflowLoggerConfig, activity_log_context


def test_translates_only_devin_namespace_to_cli() -> None:
    calls = []

    def runner(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0, "done", "")

    result = DevinHarness(runner=runner).run(
        "review this",
        cwd=Path("/repo"),
        config={
            "devin": {"model": "SWE-1.7", "permission_mode": "accept-edits"},
            "other": {"ignored": True},
        },
    )

    assert result.stdout == "done"
    assert calls[0][0][:3] == ["devin", "-p", "--export"]
    assert calls[0][0][4:] == [
        "--permission-mode", "accept-edits", "--model", "SWE-1.7", "--", "review this",
    ]


def test_run_without_activity_context_exports_parses_and_cleans_temporary_trajectory() -> None:
    export_paths = []

    def runner(command, **kwargs):
        export_path = Path(command[command.index("--export") + 1])
        export_paths.append(export_path)
        export_path.write_text(
            json.dumps({"final_metrics": {"total_prompt_tokens": 12}})
        )
        return subprocess.CompletedProcess(command, 0, "done", "")

    result = DevinHarness(runner=runner).run("review this", cwd=Path("/repo"), config={})

    assert result.usage == HarnessUsage(prompt_tokens=12)
    assert export_paths[0].is_absolute()
    assert export_paths[0].name == "devin-trajectory.json"
    assert not export_paths[0].exists()


def test_run_with_activity_context_retains_trajectory_beside_activity_logs(tmp_path) -> None:
    export_paths = []

    def runner(command, **kwargs):
        export_path = Path(command[command.index("--export") + 1])
        export_paths.append(export_path)
        export_path.write_text(
            json.dumps({"final_metrics": {"total_completion_tokens": 4}})
        )
        return subprocess.CompletedProcess(command, 0, "done", "")

    info = SimpleNamespace(
        workflow_id="workflow",
        workflow_run_id="run",
        activity_type="Analyze",
        activity_id="activity",
        attempt=2,
    )
    with activity_log_context(info, WorkflowLoggerConfig(log_root=tmp_path)):
        result = DevinHarness(runner=runner).run("review this", cwd=Path("/repo"), config={})

    assert result.usage == HarnessUsage(completion_tokens=4)
    assert export_paths[0].parent == tmp_path / "workflow" / "run" / "activities" / "Analyze_activity_2"
    assert export_paths[0].exists()
    assert (export_paths[0].parent / "activity.log").exists()
    assert (export_paths[0].parent / "devin.log").exists()


def test_run_with_nonzero_exit_still_returns_available_usage() -> None:
    def runner(command, **kwargs):
        export_path = Path(command[command.index("--export") + 1])
        export_path.write_text(
            json.dumps({"final_metrics": {"total_cached_tokens": 8}})
        )
        return subprocess.CompletedProcess(command, 7, "partial", "failed")

    result = DevinHarness(runner=runner).run("review this", cwd=Path("/repo"), config={})

    assert result.exit_code == 7
    assert result.stdout == "partial"
    assert result.stderr == "failed"
    assert result.usage == HarnessUsage(cached_tokens=8)


def test_run_with_missing_or_malformed_export_preserves_process_result() -> None:
    def missing_runner(command, **kwargs):
        return subprocess.CompletedProcess(command, 0, "done", "")

    def malformed_runner(command, **kwargs):
        Path(command[command.index("--export") + 1]).write_text("not json")
        return subprocess.CompletedProcess(command, 9, "partial", "failed")

    results = [
        DevinHarness(runner=runner).run("review this", cwd=Path("/repo"), config={})
        for runner in (missing_runner, malformed_runner)
    ]

    assert results[0].exit_code == 0
    assert results[0].stdout == "done"
    assert results[0].usage is None
    assert results[1].exit_code == 9
    assert results[1].stdout == "partial"
    assert results[1].stderr == "failed"
    assert results[1].usage is None


def test_run_returns_full_usage_for_complete_atif_metrics(tmp_path) -> None:
    def runner(command, **kwargs):
        export_path = Path(command[command.index("--export") + 1])
        export_path.write_text(
            json.dumps(
                {
                    "final_metrics": {
                        "total_prompt_tokens": 10,
                        "total_completion_tokens": 20,
                        "total_cached_tokens": 30,
                        "total_cost_usd": 4.5,
                        "total_credits": 100,
                    }
                }
            )
        )
        return subprocess.CompletedProcess(command, 0, "done", "")

    result = DevinHarness(runner=runner).run("review this", cwd=Path("/repo"), config={})

    assert result.usage == HarnessUsage(
        prompt_tokens=10,
        completion_tokens=20,
        cached_tokens=30,
        cost_usd=4.5,
    )


def test_run_isolates_retry_attempts_in_same_workflow_run(tmp_path) -> None:
    export_paths = []

    def make_runner(attempt: int):
        def runner(command, **kwargs):
            export_path = Path(command[command.index("--export") + 1])
            export_paths.append(export_path)
            export_path.write_text(
                json.dumps({"final_metrics": {"total_prompt_tokens": attempt}})
            )
            return subprocess.CompletedProcess(command, 0, "done", "")

        return runner

    for attempt in (1, 2):
        info = SimpleNamespace(
            workflow_id="workflow",
            workflow_run_id="run",
            activity_type="Analyze",
            activity_id="activity",
            attempt=attempt,
        )
        with activity_log_context(info, WorkflowLoggerConfig(log_root=tmp_path)):
            result = DevinHarness(runner=make_runner(attempt)).run(
                "review this", cwd=Path("/repo"), config={}
            )

        assert result.usage == HarnessUsage(prompt_tokens=attempt)

    assert len(export_paths) == 2
    assert export_paths[0] != export_paths[1]
    assert all(path.exists() for path in export_paths)


def test_run_logs_sanitized_export_and_usage_outcomes_without_trajectory_content(caplog) -> None:
    caplog.set_level("INFO", logger="workflow.devin")
    marker = "sensitive-trajectory-content"

    def valid_runner(command, **kwargs):
        Path(command[command.index("--export") + 1]).write_text(
            json.dumps(
                {
                    "steps": [{"observation": marker}],
                    "final_metrics": {"total_prompt_tokens": 12},
                }
            )
        )
        return subprocess.CompletedProcess(command, 0, "done", "")

    def malformed_runner(command, **kwargs):
        Path(command[command.index("--export") + 1]).write_text(f"not-json-{marker}")
        return subprocess.CompletedProcess(command, 0, "done", "")

    for runner in (valid_runner, malformed_runner):
        DevinHarness(runner=runner).run("review this", cwd=Path("/repo"), config={})

    messages = [record.getMessage() for record in caplog.records]
    assert any("SelectDevinExportPath" in message and "storage_mode=temporary" in message for message in messages)
    assert any("CompleteDevinInvocation" in message and "usage_available=True" in message for message in messages)
    assert any("RejectAtifTelemetry" in message and "error_category=malformed_json" in message for message in messages)
    assert marker not in caplog.text
