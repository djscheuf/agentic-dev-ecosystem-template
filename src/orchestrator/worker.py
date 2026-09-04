"""Cadence Worker for the Story Analysis Workflow.

Registers `StoryAnalysisWorkflow`, the probe `SingleActivityWorkflow` (used
for manual activity-by-activity testing -- see
`orchestrator.single_activity_workflow`), and the four skill Activities,
then polls the `story-analysis` task list. Requires a running Cadence server
with the `story-analysis` domain registered -- see
`docs/reqs/workflow-orchestration/local-dev-prerequisites.md`.

Run with: python -m orchestrator.worker
"""

import asyncio
import os

from cadence.client import Client
from cadence.worker import Worker

from . import single_activity_workflow  # noqa: F401  (registers SingleActivityWorkflow)
from story_analysis_workflow.workflow import registry
from .workflow_logger import get_worker_logger, setup_worker_logging

CADENCE_TARGET = os.environ.get("CADENCE_TARGET", "localhost:7833")
DOMAIN = os.environ.get("CADENCE_DOMAIN", "story-analysis")
TASK_LIST = os.environ.get("CADENCE_TASK_LIST", "story-analysis")


async def main() -> None:
    setup_worker_logging()
    logger = get_worker_logger()
    async with Client(domain=DOMAIN, target=CADENCE_TARGET) as client:
        logger.info(
            "Worker running (domain=%r, task_list=%r, target=%r). Press Ctrl-C to stop.",
            DOMAIN,
            TASK_LIST,
            CADENCE_TARGET,
        )
        async with Worker(client, TASK_LIST, registry):
            await asyncio.Event().wait()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
