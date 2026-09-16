import json
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

import pytest

from edd_refinement_workflow import cli


def make_config(**overrides):
    defaults = dict(
        domain="story-design",
        task_list="story-design",
        cadence_target="localhost:7833",
        execution_start_to_close_timeout=None,
        task_start_to_close_timeout=None,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


@dataclass
class ExecutionResult:
    workflow_id: str
    run_id: str


class FakeClient:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


@pytest.mark.asyncio
async def test_cli_start_subcommand_invokes_starter_and_prints_ids(
    monkeypatch, capsys, tmp_path
):
    parent = tmp_path / "inputs"
    parent.mkdir()
    valid = {
        "skill_folder": "skill",
        "eval_config": "eval.yaml",
        "test_command": ["npm", "test"],
        "inspect_command": ["node", "inspect.js", "{evaluation_id}"],
        "test_cases": "cases.yaml",
        "coverage_metadata_property": "metadata.covers_test_case_ids",
        "modification_scope": ["scope.md"],
        "limits": {
            "max_iterations": 10,
            "eval_timeout_seconds": 120,
        },
    }
    input_file = parent / "edd-input.json"
    input_file.write_text(json.dumps(valid))

    calls = []

    async def fake_start(client, input_path, *, workflow_id=None, config=None):
        calls.append((client, input_path, workflow_id, config))
        return ExecutionResult(workflow_id="wf-1", run_id="run-1")

    monkeypatch.setattr(cli, "start_edd_refinement_workflow", fake_start)

    exit_code = await cli.cli_main_async(
        ["start", str(input_file), "--workflow-id", "wf-1"],
        client_factory=lambda c: FakeClient(),
        config=make_config(),
    )

    assert exit_code == 0
    assert calls[0][1] == str(input_file)
    assert calls[0][2] == "wf-1"
    captured = capsys.readouterr()
    assert "wf-1" in captured.out
    assert "run-1" in captured.out
