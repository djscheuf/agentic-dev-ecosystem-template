import json
from dataclasses import FrozenInstanceError
from types import SimpleNamespace

import pytest

from orchestrator.devin_harness import DevinHarness, DevinHarnessConfig
from orchestrator.workflow_logger import (
    WorkflowLoggerConfig,
    activity_log_context,
    get_activity_log_path,
    get_devin_log_path,
)


def test_devin_harness_config_load_when_file_missing_returns_defaults(tmp_path):
    config = DevinHarnessConfig.load(tmp_path / "missing.config.json")

    profile = config.resolve("previously-unseen-skill")

    assert profile.model == "SWE-1.7"
    assert profile.permission_mode == "auto"


def test_config_load_with_malformed_json_reports_configuration_path(tmp_path):
    config_path = tmp_path / "devin_harness.config.json"
    config_path.write_text("{")

    with pytest.raises(ValueError, match=rf"malformed_json.*{config_path}"):
        DevinHarnessConfig.load(config_path)


def test_config_load_with_unreadable_file_reports_sanitized_error(tmp_path, monkeypatch):
    config_path = tmp_path / "devin_harness.config.json"
    config_path.write_text("{}")

    def deny_read(path):
        raise PermissionError("sensitive operating-system detail")

    monkeypatch.setattr(type(config_path), "read_text", deny_read)

    with pytest.raises(ValueError, match=rf"unreadable_file.*{config_path}") as error:
        DevinHarnessConfig.load(config_path)

    assert "sensitive operating-system detail" not in str(error.value)


@pytest.mark.parametrize(
    ("data", "setting"),
    [
        ([], "root"),
        ({"defaults": []}, "defaults"),
        ({"skills": []}, "skills"),
        ({"skills": {"analyze-story": []}}, "skills.analyze-story"),
    ],
)
def test_config_load_with_wrong_typed_known_container_rejects_container(
    tmp_path, data, setting
):
    config_path = tmp_path / "devin_harness.config.json"
    config_path.write_text(json.dumps(data))

    with pytest.raises(ValueError, match=rf"invalid_type.*{setting}"):
        DevinHarnessConfig.load(config_path)


@pytest.mark.parametrize(
    ("data", "setting"),
    [
        ({"defaults": {"model": None}}, "defaults.model"),
        ({"defaults": {"model": ""}}, "defaults.model"),
        ({"defaults": {"model": 7}}, "defaults.model"),
        ({"permission_mode": "unsupported-mode"}, "legacy.permission_mode"),
        ({"skills": {"analyze-story": {"permission_mode": None}}}, "skills.analyze-story.permission_mode"),
    ],
)
def test_config_load_with_invalid_known_profile_value_rejects_field(
    tmp_path, data, setting
):
    config_path = tmp_path / "devin_harness.config.json"
    config_path.write_text(json.dumps(data))

    with pytest.raises(ValueError, match=rf"invalid_value.*{setting}"):
        DevinHarnessConfig.load(config_path)


def test_config_resolves_structured_defaults_and_exact_skill_override(tmp_path):
    config_path = tmp_path / "devin_harness.config.json"
    config_path.write_text(
        json.dumps(
            {
                "defaults": {"model": "SWE-2.0", "permission_mode": "auto"},
                "skills": {
                    "extract-story-intent": {"model": "SWE-2.1"},
                    "analyze-story": {"permission_mode": "accept-edits"},
                },
            }
        )
    )

    config = DevinHarnessConfig.load(config_path)

    assert config.resolve("extract-story-intent").model == "SWE-2.1"
    assert config.resolve("extract-story-intent").permission_mode == "auto"
    assert config.resolve("analyze-story").model == "SWE-2.0"
    assert config.resolve("analyze-story").permission_mode == "accept-edits"
    assert config.resolve("unseen-skill").model == "SWE-2.0"


def test_config_partial_override_inherits_each_unspecified_default_field(tmp_path):
    config_path = tmp_path / "devin_harness.config.json"
    config_path.write_text(json.dumps({"defaults": {"model": "SWE-2.0", "permission_mode": "auto"}, "skills": {"analyze-story": {"permission_mode": "accept-edits"}}}))

    profile = DevinHarnessConfig.load(config_path).resolve("analyze-story")

    assert profile.model == "SWE-2.0"
    assert profile.permission_mode == "accept-edits"


def test_config_mixed_format_uses_field_level_precedence(tmp_path):
    config_path = tmp_path / "devin_harness.config.json"
    config_path.write_text(json.dumps({"model": "legacy-model", "permission_mode": "dangerous", "defaults": {"model": "structured-model"}, "skills": {"analyze-story": {"permission_mode": "accept-edits"}}}))

    config = DevinHarnessConfig.load(config_path)

    assert config.resolve("unseen").model == "structured-model"
    assert config.resolve("unseen").permission_mode == "dangerous"
    assert config.resolve("analyze-story").permission_mode == "accept-edits"


def test_config_resolution_returns_fresh_frozen_profiles(tmp_path):
    config = DevinHarnessConfig.load(tmp_path / "missing.json")

    first = config.resolve("analyze-story")
    second = config.resolve("analyze-story")

    assert first == second
    assert first is not second
    with pytest.raises(FrozenInstanceError):
        first.model = "changed"


def test_devin_harness_config_load_reads_values_from_file(tmp_path):
    config_path = tmp_path / "devin_harness.config.json"
    config_path.write_text(json.dumps({"model": "SWE-2.0", "permission_mode": "bypass"}))

    config = DevinHarnessConfig.load(config_path)

    assert config.model == "SWE-2.0"
    assert config.permission_mode == "bypass"


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
