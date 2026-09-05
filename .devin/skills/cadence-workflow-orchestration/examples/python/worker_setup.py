"""Minimal Cadence worker for local development.

Registers the workflow/activity from hello_world_workflow.py and polls a task list.
See ../../03-python-client/setup-and-workers.md for the full explanation.

Run with: python worker_setup.py
"""

import asyncio

from cadence.client import Client
from cadence.worker import Worker

from hello_world_workflow import registry

CADENCE_TARGET = "localhost:7833"  # gRPC frontend address for the local SQLite quickstart
DOMAIN = "test-domain"
TASK_LIST = "hello-world-tasklist"


async def main() -> None:
    async with Client(domain=DOMAIN, target=CADENCE_TARGET) as client:
        print(f"Worker running, polling task list '{TASK_LIST}'. Press Ctrl-C to stop.")
        async with Worker(client, TASK_LIST, registry):
            await asyncio.Event().wait()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
