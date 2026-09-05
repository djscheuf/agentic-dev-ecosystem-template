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
