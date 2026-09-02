import json
from types import SimpleNamespace

from orchestrator.devin_harness import DevinHarness, DevinHarnessConfig
from orchestrator.workflow_logger import (
    WorkflowLoggerConfig,
    activity_log_context,
    get_activity_log_path,
    get_devin_log_path,
)


def test_devin_harness_config_load_when_file_missing_returns_defaults(tmp_path):
    config = DevinHarnessConfig.load(tmp_path / "missing.config.json")

    assert config.model == "SWE-1.7"
    assert config.permission_mode == "auto"


def test_devin_harness_config_load_reads_values_from_file(tmp_path):
    config_path = tmp_path / "devin_harness.config.json"
    config_path.write_text(json.dumps({"model": "SWE-2.0", "permission_mode": "manual"}))

    config = DevinHarnessConfig.load(config_path)

    assert config.model == "SWE-2.0"
    assert config.permission_mode == "manual"


def test_devin_harness_run_invokes_devin_cli_with_configured_model_and_permission_mode(tmp_path):
    captured = {}

    def runner(command, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    harness = DevinHarness(
        config=DevinHarnessConfig(model="SWE-2.0", permission_mode="manual"),
        runner=runner,
    )

    harness.run("do the thing", cwd=tmp_path)

    command = captured["command"]
    assert command[0] == "devin"
    assert "--model" in command and command[command.index("--model") + 1] == "SWE-2.0"
    assert (
        "--permission-mode" in command
        and command[command.index("--permission-mode") + 1] == "manual"
    )
    assert command[-1] == "do the thing"
    assert captured["kwargs"]["cwd"] == str(tmp_path)


def test_devin_harness_run_returns_harness_result_with_exit_code_and_output(tmp_path):
    def runner(command, **kwargs):
        return SimpleNamespace(returncode=1, stdout="out", stderr="err")

    harness = DevinHarness(runner=runner)

    result = harness.run("do the thing", cwd=tmp_path)

    assert result.exit_code == 1
    assert result.stdout == "out"
    assert result.stderr == "err"


def test_devin_harness_logs_stdout_and_stderr_to_separate_devin_log(tmp_path):
    config = WorkflowLoggerConfig(log_root=tmp_path / "logs")
    activity_info = SimpleNamespace(
        workflow_id="wf-1",
        workflow_run_id="run-1",
        activity_type="extract_story_intent",
        activity_id="act-1",
        attempt=1,
    )

    def runner(command, **kwargs):
        return SimpleNamespace(
            returncode=0,
            stdout="devin stdout line\n",
            stderr="devin stderr line\n",
        )

    harness = DevinHarness(runner=runner)

    with activity_log_context(activity_info=activity_info, config=config):
        result = harness.run("do the thing", cwd=tmp_path)
        devin_log_path = get_devin_log_path()
        activity_log_path = get_activity_log_path()

    assert result.exit_code == 0
    assert devin_log_path is not None
    assert activity_log_path is not None
    devin_log = tmp_path / "logs" / "wf-1" / "run-1" / "activities" / "extract_story_intent_act-1_1" / "devin.log"
    assert devin_log.exists()
    content = devin_log.read_text()
    assert "devin stdout line" in content
    assert "devin stderr line" in content
    assert "Devin output log" in (tmp_path / activity_log_path).read_text()
