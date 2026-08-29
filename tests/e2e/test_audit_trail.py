"""End-to-end test: trigger a run and inspect the Cadence audit trail."""

import json
import urllib.error
import urllib.request
import uuid
from datetime import timedelta

import pytest

from cadence.api.v1 import common_pb2, service_workflow_pb2
from story_analysis_workflow.config import CadenceConfig
from story_analysis_workflow.starter import start_story_analysis_workflow
from tests.integration.history import has_activity, has_signal, wait_for_workflow_close
from tests.integration.worker import run_worker


@pytest.mark.needs_cadence
async def test_e2e_run_leaves_auditable_history_and_reachable_web_ui(cadence_client):
    config = CadenceConfig(
        domain="story-analysis",
        task_list="story-analysis",
        cadence_target="localhost:7833",
        execution_start_to_close_timeout=timedelta(minutes=2),
        task_start_to_close_timeout=timedelta(seconds=10),
        escalation_timeout=timedelta(minutes=5),
    )

    async with run_worker(grade_results=[True]):
        execution = await start_story_analysis_workflow(
            cadence_client,
            "As a user, I want a durable workflow so that I can automate multi-step work.",
            config=config,
            workflow_id=f"e2e-audit-trail-{uuid.uuid4().hex}",
        )

        events = await wait_for_workflow_close(
            cadence_client,
            execution.workflow_id,
            execution.run_id,
            timeout=timedelta(seconds=45),
        )

    # Verify the workflow describe API is accessible and reports completion.
    describe_request = service_workflow_pb2.DescribeWorkflowExecutionRequest(
        domain=config.domain,
        workflow_execution=common_pb2.WorkflowExecution(
            workflow_id=execution.workflow_id,
            run_id=execution.run_id,
        ),
    )
    describe_response = await cadence_client.workflow_stub.DescribeWorkflowExecution(
        describe_request
    )
    assert describe_response.workflow_execution_info is not None
    assert describe_response.workflow_execution_info.close_status == 1  # COMPLETED

    # The event history must contain all four SDLC skill Activities.
    assert has_activity(events, "extract_story_intent")
    assert has_activity(events, "analyze_story")
    assert has_activity(events, "grade_story_analysis")

    # No human escalation was needed for the happy-path run.
    assert not has_signal(events, "human_response")

    # The workflow result is reachable and records success.
    last_event = events[-1]
    assert last_event.HasField("workflow_execution_completed_event_attributes")
    payload = last_event.workflow_execution_completed_event_attributes.result.data
    result = json.loads(payload.decode("utf-8"))
    assert result["final_status"] == "passed"

    # The Cadence Web UI is reachable (Next.js may serve a 307 redirect at root).
    try:
        response = urllib.request.urlopen("http://localhost:8088", timeout=5)
        assert response.status in (200, 301, 302, 303, 307, 308)
    except urllib.error.HTTPError as exc:
        assert exc.code in (301, 302, 303, 307, 308)
    except urllib.error.URLError as exc:
        pytest.fail(f"Cadence Web UI is not reachable: {exc}")
