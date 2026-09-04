import logging
from types import SimpleNamespace

from common.workflow_logger import (
    WorkflowLoggerConfig,
    activity_log_context,
    get_activity_artifact_dir,
    worker_log_context,
)


def test_worker_logging_includes_generic_route_identity(caplog) -> None:
    with caplog.at_level(logging.INFO, logger="workflow.worker"):
        with worker_log_context(domain="payments", task_list="payment-tasks") as logger:
            logger.info("WorkerStarted")

    record = caplog.records[-1]
    assert record.domain == "payments"
    assert record.task_list == "payment-tasks"
    assert "story" not in record.name.lower()


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
