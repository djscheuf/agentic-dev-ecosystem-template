from contextlib import AsyncExitStack
from typing import Callable

from common import WorkerSpec
from common.workflow_logger import get_worker_logger, worker_log_context


def _log_worker_stop(worker_spec: WorkerSpec) -> None:
    with worker_log_context(
        domain=worker_spec.domain, task_list=worker_spec.task_list
    ) as logger:
        logger.info("StopWorkerContext")


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
            with worker_log_context(
                domain=worker_spec.domain, task_list=worker_spec.task_list
            ) as logger:
                logger.info("StartWorkerContext")
            stack.callback(_log_worker_stop, worker_spec)
        get_worker_logger().info(
            "CompleteWorkerTopologyStartup worker_count=%d", len(worker_specs)
        )
        await stop_event.wait()
