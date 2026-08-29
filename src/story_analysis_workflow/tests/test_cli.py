import json
from datetime import timedelta

import pytest

from story_analysis_workflow import cli
from story_analysis_workflow.config import CadenceConfig

from .fake_client import ExecutionResult, FakeClient


def make_config(**overrides):
    defaults = dict(
        domain="story-analysis",
        task_list="story-analysis",
        cadence_target="localhost:7833",
        execution_start_to_close_timeout=timedelta(hours=1),
        task_start_to_close_timeout=timedelta(seconds=10),
        escalation_timeout=timedelta(minutes=5),
    )
    defaults.update(overrides)
    return CadenceConfig(**defaults)


def make_client_factory(client):
    def factory(config):
        return client

    return factory


@pytest.mark.asyncio
async def test_cli_start_subcommand_invokes_starter_and_prints_execution(monkeypatch, capsys):
    client = FakeClient(start_result=ExecutionResult(workflow_id="wf-1", run_id="run-1"))
    calls = []

    async def fake_start(passed_client, story_document, *, workflow_id=None, config=None, **engine_config):
        calls.append((passed_client, story_document, workflow_id, config, engine_config))
        return await passed_client.start_workflow("StoryAnalysisWorkflow", story_document, engine_config)

    monkeypatch.setattr(cli, "start_story_analysis_workflow", fake_start)

    exit_code = await cli.cli_main_async(
        ["start", "docs/reqs/workflow-orchestration/story.md", "--workflow-id", "wf-1"],
        client_factory=make_client_factory(client),
        config=make_config(),
    )

    assert exit_code == 0
    assert calls[0][1] == "docs/reqs/workflow-orchestration/story.md"
    assert calls[0][2] == "wf-1"
    captured = capsys.readouterr()
    assert "wf-1" in captured.out
    assert "run-1" in captured.out


@pytest.mark.asyncio
async def test_cli_signal_subcommand_invokes_send_human_response(monkeypatch, capsys):
    client = FakeClient()
    calls = []

    async def fake_send(passed_client, workflow_id, decision, notes="", *, run_id=""):
        calls.append((workflow_id, decision, notes))

    monkeypatch.setattr(cli, "send_human_response", fake_send)

    exit_code = await cli.cli_main_async(
        ["signal", "wf-1", "accept", "--notes", "Looks good"],
        client_factory=make_client_factory(client),
        config=make_config(),
    )

    assert exit_code == 0
    assert calls == [("wf-1", "accept", "Looks good")]


@pytest.mark.asyncio
async def test_cli_query_subcommand_invokes_get_status_and_prints_json(monkeypatch, capsys):
    client = FakeClient()
    status = {"status": "running", "attempt_count": 1}

    async def fake_get_status(passed_client, workflow_id, *, run_id=""):
        assert workflow_id == "wf-1"
        return status

    monkeypatch.setattr(cli, "get_status", fake_get_status)

    exit_code = await cli.cli_main_async(
        ["query", "wf-1"],
        client_factory=make_client_factory(client),
        config=make_config(),
    )

    assert exit_code == 0
    captured = capsys.readouterr()
    assert json.loads(captured.out) == status


@pytest.mark.asyncio
async def test_cli_register_domain_subcommand_registers_the_domain():
    client = FakeClient()

    exit_code = await cli.cli_main_async(
        ["register-domain", "--retention-days", "3"],
        client_factory=make_client_factory(client),
        config=make_config(),
    )

    assert exit_code == 0
    assert len(client.domain_stub.register_calls) == 1
    request = client.domain_stub.register_calls[0]
    assert request.name == "story-analysis"
    assert request.workflow_execution_retention_period.seconds == 3 * 24 * 3600


@pytest.mark.asyncio
async def test_cli_exits_with_error_on_unknown_subcommand():
    client = FakeClient()

    with pytest.raises(SystemExit) as exc_info:
        await cli.cli_main_async(
            ["unknown-command"],
            client_factory=make_client_factory(client),
            config=make_config(),
        )

    assert exc_info.value.code != 0
