import subprocess
from pathlib import Path

from common.devin_harness import DevinHarness


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
    assert calls[0][0] == [
        "devin", "-p", "--permission-mode", "accept-edits",
        "--model", "SWE-1.7", "--", "review this",
    ]
