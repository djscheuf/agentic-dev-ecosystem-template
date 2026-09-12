"""Integration test: the Story Analysis Workflow happy path against a real Cadence server."""

import json
import uuid
from datetime import timedelta

import pytest

from tests.integration.history import has_activity, wait_for_workflow_close
from tests.integration.worker import run_worker


@pytest.mark.needs_cadence
async def test_happy_path_workflow_completes_on_first_attempt(cadence_client):
    async with run_worker(grade_results=[True]):
        execution = await cadence_client.start_workflow(
            "StoryAnalysisWorkflow",
            "As a user, I want a durable workflow so that I can automate multi-step work.",
            {},
            workflow_id=f"happy-path-integration-test-{uuid.uuid4().hex}",
            task_list="story-analysis",
            execution_start_to_close_timeout=timedelta(minutes=1),
            task_start_to_close_timeout=timedelta(seconds=10),
        )

        events = await wait_for_workflow_close(
            cadence_client,
            execution.workflow_id,
            execution.run_id,
        )

    last_event = events[-1]
    assert last_event.HasField("workflow_execution_completed_event_attributes")

    payload = last_event.workflow_execution_completed_event_attributes.result.data
    result = json.loads(payload.decode("utf-8"))
    assert result["final_status"] == "passed"
    assert result["passed"] is True
    assert result["attempt_count"] == 0
    assert result["escalated"] is False

    assert has_activity(events, "extract_story_intent")
    assert has_activity(events, "analyze_story")
    assert has_activity(events, "grade_story_analysis")
    assert not has_activity(events, "repair_story_analysis")
