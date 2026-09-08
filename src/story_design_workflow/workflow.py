"""The Story Design Cadence Workflow.

Thin glue: wires ``StoryDesignEngine`` (all the sequencing/decision logic,
unit tested in ``tests/test_design_engine.py``) to real Cadence primitives --
``execute_activity`` for the three design skill Activities.
"""

import dataclasses
from datetime import timedelta
from typing import Any, Optional

from cadence import Registry, workflow
from cadence.error import ActivityFailure as CadenceActivityFailure
from cadence.workflow import RetryPolicy, execute_activity

from .activities.audit_current_reality import audit_current_reality
from .activities.design_story_implementation import design_story_implementation
from .activities.grade_story_design import grade_story_design
from .design_engine import ActivityFailure, StoryDesignEngine
from .workflow_logger import get_workflow_logger, workflow_log_context

registry = Registry()
registry.register_activity(audit_current_reality)
registry.register_activity(design_story_implementation)
registry.register_activity(grade_story_design)

# Cadence-managed retries per Activity attempt.
ACTIVITY_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=5),
    backoff_coefficient=2.0,
    maximum_interval=timedelta(minutes=5),
    maximum_attempts=3,
)
ACTIVITY_START_TO_CLOSE_TIMEOUT = timedelta(minutes=30)


@registry.workflow(name="StoryDesignWorkflow")
class StoryDesignWorkflow:
    async def _execute_skill_activity(self, name: str, *args: Any) -> dict:
        try:
            return await execute_activity(
                name,
                dict,
                *args,
                start_to_close_timeout=ACTIVITY_START_TO_CLOSE_TIMEOUT,
                retry_policy=ACTIVITY_RETRY_POLICY,
            )
        except CadenceActivityFailure as exc:
            raise ActivityFailure(str(exc)) from exc

    async def _audit_current_reality(self, analysis_path: str) -> dict:
        return await self._execute_skill_activity("audit_current_reality", analysis_path)

    async def _design_story_implementation(
        self, analysis_path: str, audit_path: str
    ) -> dict:
        return await self._execute_skill_activity(
            "design_story_implementation", analysis_path, audit_path
        )

    async def _grade_story_design(self, design_path: str) -> dict:
        return await self._execute_skill_activity("grade_story_design", design_path)

    @workflow.run
    async def run(self, analysis_path: str, config: Optional[dict] = None) -> dict:
        config = config or {}
        with workflow_log_context():
            workflow_logger = get_workflow_logger()
            workflow_logger.info("Starting StoryDesignWorkflow for %s", analysis_path)
            engine = StoryDesignEngine(
                execute_audit_current_reality=self._audit_current_reality,
                execute_design_story_implementation=self._design_story_implementation,
                execute_grade_story_design=self._grade_story_design,
                logger=workflow_logger,
            )
            result = await engine.run(analysis_path)
            workflow_logger.info("StoryDesignWorkflow completed with status=%s", result.final_status)
            return dataclasses.asdict(result)
