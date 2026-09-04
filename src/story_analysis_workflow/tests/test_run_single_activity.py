from datetime import timedelta

import pytest

from story_analysis_workflow.config import CadenceConfig
from story_analysis_workflow.run_single_activity import run_single_activity_main

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


def route_args(activity_name, input_file):
    return [
        "--domain",
        "story-analysis",
        "--task-list",
        "story-analysis",
        activity_name,
        str(input_file),
    ]


@pytest.mark.asyncio
async def test_no_args_prints_usage_and_returns_0(capsys):
    exit_code = await run_single_activity_main([])

    assert exit_code == 0
    assert "Usage: run-single-activity" in capsys.readouterr().out


@pytest.mark.asyncio
@pytest.mark.parametrize("help_flag", ["-h", "--help"])
async def test_help_flag_prints_usage_and_returns_0(capsys, help_flag):
    exit_code = await run_single_activity_main([help_flag])

    assert exit_code == 0
    assert "Usage: run-single-activity" in capsys.readouterr().out


@pytest.mark.asyncio
async def test_wrong_arg_count_returns_1(capsys):
    exit_code = await run_single_activity_main(["extract_story_intent"])

    assert exit_code == 1
    assert "--domain" in capsys.readouterr().err


@pytest.mark.asyncio
async def test_unrecognized_activity_lists_supported_and_returns_1(capsys, tmp_path):
    input_file = tmp_path / "input.md"
    input_file.write_text("hello")

    exit_code = await run_single_activity_main(route_args("not_a_real_activity", input_file))

    assert exit_code == 1
    err = capsys.readouterr().err
    assert "unrecognized activity 'not_a_real_activity'" in err
    assert "analyze_story" in err and "extract_story_intent" in err and "grade_story_analysis" in err
    assert "repair_story_analysis" not in err


@pytest.mark.asyncio
async def test_repair_story_analysis_reports_unsupported_and_returns_1(capsys, tmp_path):
    input_file = tmp_path / "analysis.json"
    input_file.write_text("{}")

    exit_code = await run_single_activity_main(route_args("repair_story_analysis", input_file))

    assert exit_code == 1
    err = capsys.readouterr().err
    assert "not supported by this script" in err
    assert "needs two input files" in err


@pytest.mark.asyncio
async def test_missing_input_file_returns_1(capsys, tmp_path):
    missing_file = tmp_path / "does-not-exist.md"

    exit_code = await run_single_activity_main(route_args("extract_story_intent", missing_file))

    assert exit_code == 1
    assert "input file not found" in capsys.readouterr().err


@pytest.mark.asyncio
async def test_successful_run_starts_workflow_and_polls_until_succeeded(capsys, tmp_path):
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    input_file = docs_dir / "story.md"
    input_file.write_text("As a user...")

    client = FakeClient(
        start_result=ExecutionResult(workflow_id="single-activity-extract_story_intent-abcd1234", run_id="run-1"),
        query_results=[
            {"status": "running"},
            {"status": "succeeded", "activity_name": "extract_story_intent", "result": {"output_path": "x.json"}},
        ],
    )

    exit_code = await run_single_activity_main(
        route_args("extract_story_intent", input_file),
        repo_root=tmp_path,
        config=make_config(),
        client_factory=make_client_factory(client),
        poll_interval_seconds=0,
    )

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "Activity 'extract_story_intent' succeeded" in out
    assert '"output_path": "x.json"' in out

    start_call = client.start_calls[0]
    assert start_call["workflow"] == "SingleActivityWorkflow"
    assert start_call["args"] == ("extract_story_intent", [["docs/story.md"]])

    assert len(client.query_calls) == 2
    assert client.query_calls[0]["query_type"] == "get_result"


@pytest.mark.asyncio
async def test_explicit_route_starts_on_selected_domain_and_task_list(tmp_path):
    input_file = tmp_path / "story.intent.json"
    input_file.write_text("{}")
    client = FakeClient(query_result={"status": "succeeded", "result": {}})
    configs = []

    def client_factory(config):
        configs.append(config)
        return client

    exit_code = await run_single_activity_main(
        [
            "--domain",
            "payments",
            "--task-list",
            "payment-tasks",
            "analyze_story",
            str(input_file),
        ],
        repo_root=tmp_path,
        client_factory=client_factory,
        poll_interval_seconds=0,
    )

    assert exit_code == 0
    assert configs[0].domain == "payments"
    assert client.start_calls[0]["options"]["task_list"] == "payment-tasks"


@pytest.mark.asyncio
async def test_analyze_story_passes_input_path_directly_not_wrapped_in_a_list(tmp_path):
    input_file = tmp_path / "story.intent.json"
    input_file.write_text("{}")

    client = FakeClient(query_result={"status": "succeeded", "result": {}})

    await run_single_activity_main(
        route_args("analyze_story", input_file),
        repo_root=tmp_path,
        config=make_config(),
        client_factory=make_client_factory(client),
        poll_interval_seconds=0,
    )

    assert client.start_calls[0]["args"] == ("analyze_story", ["story.intent.json"])


@pytest.mark.asyncio
async def test_activity_failure_prints_error_and_log_hint_and_returns_1(capsys, tmp_path):
    input_file = tmp_path / "analysis.json"
    input_file.write_text("{}")

    client = FakeClient(
        query_result={
            "status": "failed",
            "activity_name": "grade_story_analysis",
            "error": "boom",
        }
    )

    exit_code = await run_single_activity_main(
        route_args("grade_story_analysis", input_file),
        repo_root=tmp_path,
        config=make_config(),
        client_factory=make_client_factory(client),
        poll_interval_seconds=0,
    )

    assert exit_code == 1
    err = capsys.readouterr().err
    assert "Activity 'grade_story_analysis' failed: boom" in err
    assert "http://localhost:8088" in err
    assert "scripts/.run/worker.log" in err


@pytest.mark.asyncio
async def test_poll_times_out_if_workflow_never_finishes(capsys, tmp_path):
    input_file = tmp_path / "analysis.json"
    input_file.write_text("{}")

    client = FakeClient(query_result={"status": "running"})

    exit_code = await run_single_activity_main(
        route_args("grade_story_analysis", input_file),
        repo_root=tmp_path,
        config=make_config(),
        client_factory=make_client_factory(client),
        poll_interval_seconds=0,
        wait_timeout_seconds=0,
    )

    assert exit_code == 1
    assert "timed_out" in capsys.readouterr().err
