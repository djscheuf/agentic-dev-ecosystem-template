"""Integration test: the grade/repair loop re-grades within the max-attempt bound."""

import json
import uuid
from datetime import timedelta

import pytest

from tests.integration.history import has_activity, wait_for_workflow_close
from tests.integration.worker import run_worker


@pytest.mark.needs_cadence
async def test_grade_repair_loop_repairs_and_passes_within_three_attempts(cadence_client):
    async with run_worker(grade_results=[False, True]):
        execution = await cadence_client.start_workflow(
            "StoryAnalysisWorkflow",
            "As a user, I want a durable workflow so that I can automate multi-step work.",
            {},
            workflow_id=f"grade-repair-integration-test-{uuid.uuid4().hex}",
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
    assert result["attempt_count"] == 1
    assert result["escalated"] is False

    assert has_activity(events, "extract_story_intent")
    assert has_activity(events, "analyze_story")
    assert has_activity(events, "repair_story_analysis")

    grade_scheduled = [
        event
        for event in events
        if event.HasField("activity_task_scheduled_event_attributes")
        and event.activity_task_scheduled_event_attributes.activity_type.name == "grade_story_analysis"
    ]
    assert len(grade_scheduled) == 2
