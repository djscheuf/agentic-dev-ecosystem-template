import ast
import inspect
import logging
from types import SimpleNamespace

import common.workflow_logger as workflow_logger
from common.workflow_logger import (
    WorkflowLoggerConfig,
    activity_log_context,
    client_log_context,
    get_activity_artifact_dir,
    get_claude_log_path,
    get_client_log_path,
    get_workflow_log_path,
    setup_worker_logging,
    worker_log_context,
    workflow_log_context,
)


def test_no_duplicate_top_level_function_definitions() -> None:
    """workflow_logger-dup: guards against silently shadowed re-definitions."""
    tree = ast.parse(inspect.getsource(workflow_logger))
    names = [
        node.name
        for node in ast.iter_child_nodes(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]

    duplicates = {name for name in names if names.count(name) > 1}

    assert duplicates == set()


def test_get_claude_log_path_reports_activity_scoped_claude_log(tmp_path) -> None:
    config = WorkflowLoggerConfig(log_root=tmp_path / "logs")
    info = SimpleNamespace(
        workflow_id="wf-1",
        workflow_run_id="run-1",
        activity_type="extract_story_intent",
        activity_id="act-1",
        attempt=1,
    )

    with activity_log_context(activity_info=info, config=config):
        claude_log_path = get_claude_log_path()

    assert claude_log_path == str(
        tmp_path
        / "logs"
        / "wf-1"
        / "run-1"
        / "activities"
        / "extract_story_intent_act-1_1"
        / "claude.log"
    )


def test_missing_logging_config_uses_defaults_and_warns(tmp_path, caplog) -> None:
    missing_path = tmp_path / "missing.json"

    with caplog.at_level(logging.WARNING):
        config = WorkflowLoggerConfig.load(missing_path)

    assert config.worker_level == "INFO"
    assert "logging config not found" in caplog.text


def test_setup_worker_logging_uses_supplied_worker_level() -> None:
    root = logging.getLogger()
    original_level = root.level
    try:
        setup_worker_logging(WorkflowLoggerConfig(worker_level="DEBUG"))
        assert root.level == logging.DEBUG
    finally:
        root.setLevel(original_level)


def test_worker_logging_includes_generic_route_identity(caplog) -> None:
    with caplog.at_level(logging.INFO, logger="workflow.worker"):
        with worker_log_context(domain="payments", task_list="payment-tasks") as logger:
            logger.info("WorkerStarted")

    record = caplog.records[-1]
    assert record.domain == "payments"
    assert record.task_list == "payment-tasks"
    assert "story" not in record.name.lower()


def test_workflow_and_client_contexts_expose_created_log_paths(tmp_path) -> None:
    config = WorkflowLoggerConfig(log_root=tmp_path / "logs")
    info = SimpleNamespace(workflow_id="wf-1", workflow_run_id="run-1")

    with workflow_log_context(workflow_info=info, config=config):
        workflow_path = get_workflow_log_path()
    with client_log_context("wf-1", "run-1", config=config):
        client_path = get_client_log_path()

    assert workflow_path == str(config.log_root / "wf-1" / "run-1" / "workflow.log")
    assert client_path == str(config.log_root / "wf-1" / "run-1" / "client.log")
    assert (config.log_root / "wf-1" / "run-1" / "workflow.log").exists()
    assert (config.log_root / "wf-1" / "run-1" / "client.log").exists()


def test_activity_log_context_exposes_attempt_scoped_artifact_directory(tmp_path) -> None:
    config = WorkflowLoggerConfig(log_root=tmp_path / "logs")
    info = SimpleNamespace(
        workflow_id="wf-1",
        workflow_run_id="run-1",
        activity_type="extract_story_intent",
        activity_id="act-1",
        attempt=2,
    )

    with activity_log_context(activity_info=info, config=config):
        artifact_dir = get_activity_artifact_dir()

    assert artifact_dir == (
        tmp_path
        / "logs"
        / "wf-1"
        / "run-1"
        / "activities"
        / "extract_story_intent_act-1_2"
    )
    assert (artifact_dir / "activity.log").exists()
    assert (artifact_dir / "devin.log").exists()


def test_activity_artifact_directory_is_none_without_activity_context() -> None:
    assert get_activity_artifact_dir() is None

    with activity_log_context(activity_info=None):
        assert get_activity_artifact_dir() is None

    assert get_activity_artifact_dir() is None


def test_activity_artifact_directory_sanitizes_path_unsafe_identifiers(tmp_path) -> None:
    config = WorkflowLoggerConfig(log_root=tmp_path / "logs")
    info = SimpleNamespace(
        workflow_id="../wf/文",
        workflow_run_id=".run/../id",
        activity_type="skill/type",
        activity_id="../act.文",
        attempt=1,
    )

    with activity_log_context(activity_info=info, config=config):
        artifact_dir = get_activity_artifact_dir()

    assert artifact_dir == (
        config.log_root / "wf" / "run_id" / "activities" / "skill_type_act_1"
    )
    assert artifact_dir.resolve().is_relative_to(config.log_root.resolve())


def test_activity_artifact_directories_isolate_activities_and_retry_attempts(
    tmp_path,
) -> None:
    config = WorkflowLoggerConfig(log_root=tmp_path / "logs")
    base_info = {
        "workflow_id": "wf-1",
        "workflow_run_id": "run-1",
        "activity_type": "extract_story_intent",
    }
    activity_infos = [
        SimpleNamespace(**base_info, activity_id="act-1", attempt=1),
        SimpleNamespace(**base_info, activity_id="act-2", attempt=1),
        SimpleNamespace(**base_info, activity_id="act-1", attempt=2),
    ]
    artifact_dirs = []

    for info in activity_infos:
        with activity_log_context(activity_info=info, config=config):
            artifact_dirs.append(get_activity_artifact_dir())

    assert len(set(artifact_dirs)) == len(activity_infos)
    assert all((path / "activity.log").exists() for path in artifact_dirs)
    assert all((path / "devin.log").exists() for path in artifact_dirs)
