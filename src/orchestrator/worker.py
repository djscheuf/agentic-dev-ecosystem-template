"""Cadence Worker for the Story Analysis Workflow.

Registers `StoryAnalysisWorkflow` and its four skill Activities, then polls the
`story-analysis` task list. Requires a running Cadence server with the
`story-analysis` domain registered -- see
`docs/reqs/workflow-orchestration/local-dev-prerequisites.md`.

Run with: python -m orchestrator.worker
"""

import asyncio
import os

from cadence.client import Client
from cadence.worker import Worker

from .workflow import registry

CADENCE_TARGET = os.environ.get("CADENCE_TARGET", "localhost:7833")
DOMAIN = os.environ.get("CADENCE_DOMAIN", "story-analysis")
TASK_LIST = os.environ.get("CADENCE_TASK_LIST", "story-analysis")


async def main() -> None:
    async with Client(domain=DOMAIN, target=CADENCE_TARGET) as client:
        print(
            f"Worker running (domain={DOMAIN!r}, task_list={TASK_LIST!r}, "
            f"target={CADENCE_TARGET!r}). Press Ctrl-C to stop."
        )
        async with Worker(client, TASK_LIST, registry):
            await asyncio.Event().wait()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
