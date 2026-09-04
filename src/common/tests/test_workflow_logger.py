import logging

from common.workflow_logger import worker_log_context


def test_worker_logging_includes_generic_route_identity(caplog) -> None:
    with caplog.at_level(logging.INFO, logger="workflow.worker"):
        with worker_log_context(domain="payments", task_list="payment-tasks") as logger:
            logger.info("WorkerStarted")

    record = caplog.records[-1]
    assert record.domain == "payments"
    assert record.task_list == "payment-tasks"
    assert "story" not in record.name.lower()
