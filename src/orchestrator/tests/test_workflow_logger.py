import logging
from types import SimpleNamespace

import pytest

from orchestrator.workflow_logger import (
    WorkflowLoggerConfig,
    activity_log_context,
    client_log_context,
    get_activity_log_path,
    get_activity_logger,
    get_client_logger,
    get_client_log_path,
    get_devin_log_path,
    get_devin_logger,
    get_workflow_log_path,
    get_workflow_logger,
    setup_worker_logging,
    workflow_log_context,
)


def test_config_load_returns_defaults_when_file_missing(monkeypatch, tmp_path):
    monkeypatch.delenv("STORY_ANALYSIS_LOG_ROOT", raising=False)
    config = WorkflowLoggerConfig.load(tmp_path / "missing.config.json")

    assert config.worker_level == "INFO"
    assert config.workflow_level == "INFO"
    assert config.client_level == "INFO"
    assert config.activity_level == "DEBUG"
    assert config.devin_level == "DEBUG"
    assert config.log_root.name == "logs"
    assert config.log_root.parent.name == ".process"


def test_config_load_reads_levels_and_log_root(monkeypatch, tmp_path):
    monkeypatch.delenv("STORY_ANALYSIS_LOG_ROOT", raising=False)
    config_path = tmp_path / "workflow_logging.config.json"
    custom_log_root = tmp_path / "custom" / "logs"
    config_path.write_text(
        f'{{"log_root": "{custom_log_root}", "levels": {{"activity": "INFO", "devin": "INFO", "worker": "DEBUG"}}}}'
    )

    config = WorkflowLoggerConfig.load(config_path)

    assert config.activity_level == "INFO"
    assert config.devin_level == "INFO"
    assert config.worker_level == "DEBUG"
    assert config.workflow_level == "INFO"  # default
    assert config.log_root == custom_log_root


def test_activity_log_context_creates_activity_and_devin_logs(tmp_path):
    config = WorkflowLoggerConfig(log_root=tmp_path / "logs")
    info = SimpleNamespace(
        workflow_id="wf-1",
        workflow_run_id="run-1",
        activity_type="extract_story_intent",
        activity_id="act-1",
        attempt=2,
    )

    with activity_log_context(activity_info=info, config=config):
        get_activity_logger().debug("activity event")
        get_devin_logger().debug("devin event")
        activity_path = get_activity_log_path()
        devin_path = get_devin_log_path()

    assert activity_path is not None
    assert devin_path is not None
    assert (
        tmp_path / "logs" / "wf-1" / "run-1" / "activities" / "extract_story_intent_act-1_2" / "activity.log"
    ).exists()
    assert (
        tmp_path / "logs" / "wf-1" / "run-1" / "activities" / "extract_story_intent_act-1_2" / "devin.log"
    ).exists()


def test_workflow_log_context_creates_workflow_log(tmp_path):
    config = WorkflowLoggerConfig(log_root=tmp_path / "logs")
    info = SimpleNamespace(workflow_id="wf-1", workflow_run_id="run-1")

    with workflow_log_context(workflow_info=info, config=config):
        get_workflow_logger().info("workflow event")
        path = get_workflow_log_path()

    assert path is not None
    assert (tmp_path / "logs" / "wf-1" / "run-1" / "workflow.log").exists()


def test_client_log_context_creates_client_log_with_run_id(tmp_path):
    config = WorkflowLoggerConfig(log_root=tmp_path / "logs")

    with client_log_context("wf-1", "run-1", config=config):
        get_client_logger().info("client event")
        path = get_client_log_path()

    assert path is not None
    assert (tmp_path / "logs" / "wf-1" / "run-1" / "client.log").exists()


def test_client_log_context_creates_client_log_without_run_id(tmp_path):
    config = WorkflowLoggerConfig(log_root=tmp_path / "logs")

    with client_log_context("wf-1", "", config=config):
        get_client_logger().info("client event")
        path = get_client_log_path()

    assert path is not None
    assert (tmp_path / "logs" / "wf-1" / "client.log").exists()


def test_get_loggers_outside_context_return_silent_fallbacks():
    # Should not raise and should not create log files.
    assert get_activity_logger().debug("ignored") is None
    assert get_devin_logger().debug("ignored") is None
    assert get_workflow_logger().info("ignored") is None
    assert get_client_logger().info("ignored") is None
    assert get_activity_log_path() is None
    assert get_devin_log_path() is None
    assert get_workflow_log_path() is None
    assert get_client_log_path() is None


def test_sanitize_component_replaces_unsafe_characters(tmp_path):
    config = WorkflowLoggerConfig(log_root=tmp_path / "logs")

    with client_log_context("wf!id", "run!id", config=config):
        get_client_logger().info("client event")
        path = get_client_log_path()

    assert path is not None
    assert "wf_id" in path and "run_id" in path


def test_setup_worker_logging_configures_root_logger(tmp_path):
    root = logging.getLogger()
    original_handlers = list(root.handlers)
    original_level = root.level
    try:
        config = WorkflowLoggerConfig(
            log_root=tmp_path / "logs",
            worker_level="DEBUG",
            workflow_level="INFO",
            client_level="INFO",
            activity_level="DEBUG",
            devin_level="DEBUG",
        )
        setup_worker_logging(config)

        assert root.level == logging.DEBUG
    finally:
        for handler in list(root.handlers):
            if handler not in original_handlers:
                root.removeHandler(handler)
                handler.close()
        root.setLevel(original_level)
