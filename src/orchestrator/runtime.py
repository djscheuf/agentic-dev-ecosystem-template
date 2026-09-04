from contextlib import AsyncExitStack
from typing import Callable

from common import WorkerSpec


async def run_worker_topology(
    worker_specs: tuple[WorkerSpec, ...],
    stop_event,
    *,
    client_factory: Callable,
    worker_factory: Callable,
) -> None:
    async with AsyncExitStack() as stack:
        for worker_spec in worker_specs:
            client = await stack.enter_async_context(client_factory(worker_spec))
            await stack.enter_async_context(worker_factory(worker_spec, client))
        await stop_event.wait()
