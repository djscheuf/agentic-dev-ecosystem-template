import json
import subprocess
from pathlib import Path

from common.devin_harness import DevinHarness
from common.harness import HarnessUsage


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
