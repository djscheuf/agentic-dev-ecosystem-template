"""Helpers for reading Cadence workflow execution history in tests."""

import asyncio
from datetime import timedelta

from cadence.api.v1 import common_pb2, history_pb2, service_workflow_pb2
from cadence.client import Client


async def wait_for_workflow_close(
    client: Client,
    workflow_id: str,
    run_id: str,
    timeout: timedelta = timedelta(seconds=30),
) -> list:
    """Poll ``GetWorkflowExecutionHistory`` until the workflow closes.

    Returns the full list of ``HistoryEvent`` protobufs.
    """
    deadline = asyncio.get_event_loop().time() + timeout.total_seconds()
    request = service_workflow_pb2.GetWorkflowExecutionHistoryRequest(
        domain=client.domain,
        workflow_execution=common_pb2.WorkflowExecution(
            workflow_id=workflow_id,
            run_id=run_id,
        ),
        page_size=100,
        history_event_filter_type=history_pb2.EVENT_FILTER_TYPE_ALL_EVENT,
    )

    while True:
        response = await client.workflow_stub.GetWorkflowExecutionHistory(request)
        if response.history.events:
            last_event = response.history.events[-1]
            if _is_close_event(last_event):
                return list(response.history.events)

        if asyncio.get_event_loop().time() > deadline:
            raise TimeoutError(
                f"Workflow {workflow_id!r} did not close within {timeout}"
            )

        await asyncio.sleep(0.5)


def _is_close_event(event) -> bool:
    return any(
        event.HasField(field)
        for field in (
            "workflow_execution_completed_event_attributes",
            "workflow_execution_failed_event_attributes",
            "workflow_execution_timed_out_event_attributes",
            "workflow_execution_canceled_event_attributes",
            "workflow_execution_terminated_event_attributes",
        )
    )


def workflow_result(events: list) -> dict | None:
    """Extract the result payload from a completed workflow's history."""
    for event in events:
        if event.HasField("workflow_execution_completed_event_attributes"):
            return event.workflow_execution_completed_event_attributes.result
    return None


def has_activity(events: list, activity_name: str) -> bool:
    """Return ``True`` if the history contains a scheduled task for ``activity_name``."""
    for event in events:
        if event.HasField("activity_task_scheduled_event_attributes"):
            attrs = event.activity_task_scheduled_event_attributes
            if attrs.activity_type.name == activity_name:
                return True
    return False


def has_signal(events: list, signal_name: str) -> bool:
    """Return ``True`` if the history contains a ``WorkflowExecutionSignaled`` event."""
    for event in events:
        if event.HasField("workflow_execution_signaled_event_attributes"):
            attrs = event.workflow_execution_signaled_event_attributes
            if attrs.signal_name == signal_name:
                return True
    return False
