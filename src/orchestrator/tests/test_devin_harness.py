import json
from dataclasses import FrozenInstanceError
from pathlib import Path
from types import MappingProxyType, SimpleNamespace

import pytest

from orchestrator.devin_harness import DevinHarness, DevinHarnessConfig
from orchestrator.invocation_context import skill_invocation_context
from orchestrator.workflow_logger import (
    WorkflowLoggerConfig,
    activity_log_context,
    get_activity_log_path,
    get_devin_log_path,
)


def test_repository_config_grants_story_analysis_writers_explicit_edits():
    config = DevinHarnessConfig.load()

    assert config.resolve("unconfigured-skill").permission_mode == "auto"
    for skill_name in (
        "extract-story-intent",
        "analyze-story",
        "grade-story-analysis",
        "repair-story-analysis",
    ):
        assert config.resolve(skill_name).permission_mode == "accept-edits"


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


def test_config_unknown_keys_do_not_change_resolution_or_command(tmp_path):
    config_path = tmp_path / "devin_harness.config.json"
    config_path.write_text(
        json.dumps(
            {
                "future_top_level": "top-secret-marker",
                "defaults": {"model": "SWE-2.0", "future_default": "ignored"},
                "skills": {
                    "analyze-story": {
                        "permission_mode": "accept-edits",
                        "future_override": "skill-secret-marker",
                    }
                },
            }
        )
    )
    commands = []

    def runner(command, **kwargs):
        commands.append(command)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    harness = DevinHarness(config=DevinHarnessConfig.load(config_path), runner=runner)

    with skill_invocation_context("analyze-story"):
        harness.run("prompt", cwd=tmp_path)

    assert commands == [["devin", "-p", "--permission-mode", "accept-edits", "--model", "SWE-2.0", "--", "prompt"]]


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


def test_harness_run_uses_fresh_profile_command_for_each_invocation(tmp_path):
    config_path = tmp_path / "devin_harness.config.json"
    config_path.write_text(
        json.dumps(
            {
                "defaults": {"model": "SWE-2.0", "permission_mode": "auto"},
                "skills": {
                    "analyze-story": {"permission_mode": "accept-edits"},
                    "grade-story-analysis": {"model": "SWE-2.1"},
                },
            }
        )
    )
    commands = []

    def runner(command, **kwargs):
        commands.append(command)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    harness = DevinHarness(config=DevinHarnessConfig.load(config_path), runner=runner)

    with skill_invocation_context("analyze-story"):
        harness.run("analyze", cwd=tmp_path)
    with skill_invocation_context("grade-story-analysis"):
        harness.run("grade", cwd=tmp_path)

    assert commands[0] is not commands[1]
    assert commands[0][2:7] == ["--permission-mode", "accept-edits", "--model", "SWE-2.0", "--"]
    assert commands[1][2:7] == ["--permission-mode", "auto", "--model", "SWE-2.1", "--"]


def test_harness_run_does_not_escalate_or_retry_restricted_failure(tmp_path):
    commands = []

    def runner(command, **kwargs):
        commands.append(command)
        return SimpleNamespace(returncode=1, stdout="", stderr="write denied")

    harness = DevinHarness(config=DevinHarnessConfig(), runner=runner)

    with skill_invocation_context("analyze-story"):
        result = harness.run("write artifacts", cwd=tmp_path)

    assert result.exit_code == 1
    assert len(commands) == 1
    assert commands[0][commands[0].index("--permission-mode") + 1] == "auto"


def test_devin_harness_run_returns_harness_result_with_exit_code_and_output(tmp_path):
    def runner(command, **kwargs):
        return SimpleNamespace(returncode=1, stdout="out", stderr="err")

    harness = DevinHarness(runner=runner)

    result = harness.run("do the thing", cwd=tmp_path)

    assert result.exit_code == 1
    assert result.stdout == "out"
    assert result.stderr == "err"


def test_harness_run_logs_safe_resolved_profile_selection(tmp_path):
    logger_config = WorkflowLoggerConfig(log_root=tmp_path / "logs")
    activity_info = SimpleNamespace(
        workflow_id="wf-profile",
        workflow_run_id="run-profile",
        activity_type="analyze_story",
        activity_id="act-profile",
        attempt=1,
    )
    harness = DevinHarness(
        config=DevinHarnessConfig(
            model="SWE-2.0", permission_mode="accept-edits"
        ),
        runner=lambda command, **kwargs: SimpleNamespace(
            returncode=0, stdout="", stderr=""
        ),
    )

    with activity_log_context(activity_info=activity_info, config=logger_config):
        with skill_invocation_context("analyze-story"):
            harness.run("sensitive-prompt-marker", cwd=tmp_path)
        activity_log_path = get_activity_log_path()

    content = (tmp_path / activity_log_path).read_text()
    assert "skill_name=analyze-story" in content
    assert "model=SWE-2.0" in content
    assert "permission_mode=accept-edits" in content
    assert "sensitive-prompt-marker" not in content


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


def test_devin_harness_run_emits_start_devin_invocation_event(tmp_path):
    config = WorkflowLoggerConfig(log_root=tmp_path / "logs")
    activity_info = SimpleNamespace(
        workflow_id="wf-start",
        workflow_run_id="run-start",
        activity_type="analyze_story",
        activity_id="act-start",
        attempt=1,
    )
    commands = []

    def runner(command, **kwargs):
        commands.append(command)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    harness = DevinHarness(
        config=DevinHarnessConfig(model="SWE-2.0", permission_mode="accept-edits"),
        runner=runner,
    )

    with activity_log_context(activity_info=activity_info, config=config):
        with skill_invocation_context("analyze-story"):
            harness.run("sensitive-prompt-text", cwd=tmp_path)
        activity_log_path = get_activity_log_path()

    content = (tmp_path / activity_log_path).read_text()
    assert "StartDevinInvocation" in content
    assert "skill_name=analyze-story" in content
    assert "model=SWE-2.0" in content
    assert "permission_mode=accept-edits" in content
    assert "sensitive-prompt-text" not in content


def test_config_rejection_logs_sanitized_event_and_hides_raw_value(tmp_path):
    config_path = tmp_path / "devin_harness.config.json"
    config_path.write_text(
        json.dumps({"skills": {"analyze-story": {"permission_mode": "unsupported-secret"}}})
    )
    logger_config = WorkflowLoggerConfig(log_root=tmp_path / "logs")
    activity_info = SimpleNamespace(
        workflow_id="wf-reject",
        workflow_run_id="run-reject",
        activity_type="analyze_story",
        activity_id="act-reject",
        attempt=1,
    )

    with activity_log_context(activity_info=activity_info, config=logger_config):
        with pytest.raises(ValueError, match="invalid_value"):
            DevinHarnessConfig.load(config_path)
        activity_log_path = get_activity_log_path()

    content = (tmp_path / activity_log_path).read_text()
    assert "RejectInvocationConfiguration" in content
    assert "invalid_value" in content
    assert "skills.analyze-story.permission_mode" in content
    assert "unsupported-secret" not in content


def test_devin_harness_run_emits_complete_devin_invocation_event(tmp_path):
    config = WorkflowLoggerConfig(log_root=tmp_path / "logs")
    activity_info = SimpleNamespace(
        workflow_id="wf-complete",
        workflow_run_id="run-complete",
        activity_type="analyze_story",
        activity_id="act-complete",
        attempt=1,
    )
    commands = []

    def runner(command, **kwargs):
        commands.append(command)
        return SimpleNamespace(returncode=0, stdout="out", stderr="err")

    harness = DevinHarness(
        config=DevinHarnessConfig(model="SWE-2.0", permission_mode="accept-edits"),
        runner=runner,
    )

    with activity_log_context(activity_info=activity_info, config=config):
        with skill_invocation_context("analyze-story"):
            harness.run("prompt-text", cwd=tmp_path)
        activity_log_path = get_activity_log_path()

    content = (tmp_path / activity_log_path).read_text()
    assert "CompleteDevinInvocation" in content
    assert "skill_name=analyze-story" in content
    assert "exit_code=0" in content
    assert "duration_ms=" in content
    assert "devin_log_path=" in content


def test_run_with_unstartable_devin_process_reports_sanitized_launch_failure(tmp_path):
    config = WorkflowLoggerConfig(log_root=tmp_path / "logs")
    activity_info = SimpleNamespace(
        workflow_id="wf-launch-failure",
        workflow_run_id="run-launch-failure",
        activity_type="analyze_story",
        activity_id="act-launch-failure",
        attempt=1,
    )

    def runner(command, **kwargs):
        raise OSError("sensitive-filesystem-marker")

    harness = DevinHarness(runner=runner)

    with activity_log_context(activity_info=activity_info, config=config):
        with skill_invocation_context("analyze-story"):
            with pytest.raises(RuntimeError, match="devin_launch_failed"):
                harness.run("prompt-text", cwd=tmp_path)
        activity_log_path = get_activity_log_path()

    content = (tmp_path / activity_log_path).read_text()
    assert "FailDevinInvocationLaunch" in content
    assert "skill_name=analyze-story" in content
    assert "sensitive-filesystem-marker" not in content
    assert "CompleteDevinInvocation" not in content


def test_documentation_for_harness_profiles_explains_first_slice_contract():
    documentation = (Path(__file__).parents[1] / "README.md").read_text()

    for required_text in (
        '"defaults"',
        '"skills"',
        "skill override → structured default → legacy flat default",
        "accept-edits",
        "dangerous",
        "bypass",
        "Unknown keys",
        "legacy",
        "activity.log",
        "Activity-start retry snapshot",
    ):
        assert required_text in documentation


def test_run_with_namespaced_devin_config_builds_safe_command(tmp_path):
    calls = []

    def runner(command, **kwargs):
        calls.append((command, kwargs))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    harness = DevinHarness(runner=runner)
    config = MappingProxyType(
        {"devin": MappingProxyType({"model": "SWE-2.0"})}
    )

    harness.run("sensitive prompt", cwd=tmp_path, config=config)

    assert calls == [
        (
            [
                "devin",
                "-p",
                "--permission-mode",
                "auto",
                "--model",
                "SWE-2.0",
                "--",
                "sensitive prompt",
            ],
            {"cwd": str(tmp_path), "capture_output": True, "text": True},
        )
    ]


def test_run_with_unknown_or_invalid_devin_setting_rejects_before_launch(tmp_path):
    calls = []
    harness = DevinHarness(
        runner=lambda command, **kwargs: calls.append((command, kwargs))
    )
    cases = [
        ({"devin": {"permisson_mode": "auto"}}, "unknown_key: devin.permisson_mode"),
        ({"devin": []}, "invalid_namespace_type: devin"),
        ({"devin": {"model": None}}, "invalid_value: devin.model"),
        ({"devin": {"model": ""}}, "invalid_value: devin.model"),
        ({"devin": {"model": 7}}, "invalid_value: devin.model"),
        (
            {"devin": {"permission_mode": "unsupported"}},
            "invalid_value: devin.permission_mode",
        ),
    ]

    errors = []
    for config, expected in cases:
        with pytest.raises(ValueError) as error:
            harness.run("prompt", cwd=tmp_path, config=config)
        errors.append(str(error.value))

    assert errors == [expected for config, expected in cases]
    assert calls == []


def test_run_with_sibling_harness_namespace_ignores_sibling(tmp_path):
    commands = []

    def runner(command, **kwargs):
        commands.append(command)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    sibling = {"unknown": ["preserve", {"nested": True}]}
    config = {
        "devin": {"model": "SWE-2.0", "permission_mode": "accept-edits"},
        "other-agent": sibling,
    }

    DevinHarness(runner=runner).run("prompt", cwd=tmp_path, config=config)

    assert commands == [
        [
            "devin",
            "-p",
            "--permission-mode",
            "accept-edits",
            "--model",
            "SWE-2.0",
            "--",
            "prompt",
        ]
    ]
    assert config["other-agent"] is sibling
    assert sibling == {"unknown": ["preserve", {"nested": True}]}
