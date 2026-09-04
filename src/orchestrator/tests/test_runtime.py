import asyncio

import pytest

from common import WorkerSpec, WorkflowModuleSpec
from orchestrator.runtime import run_worker_topology


class Context:
    def __init__(self, name, events, fail=False):
        self.name = name
        self.events = events
        self.fail = fail

    async def __aenter__(self):
        self.events.append(f"enter:{self.name}")
        if self.fail:
            raise RuntimeError(self.name)
        return self

    async def __aexit__(self, *args):
        self.events.append(f"exit:{self.name}")


def worker_spec(task_list):
    module = WorkflowModuleSpec(task_list, "domain", task_list, (), (), lambda registry: None)
    return WorkerSpec("domain", task_list, "target", (module,))


@pytest.mark.asyncio
async def test_worker_runtime_when_started_manages_topology_transactionally():
    events = []
    specs = (worker_spec("first"), worker_spec("second"))

    with pytest.raises(RuntimeError, match="second-worker"):
        await run_worker_topology(
            specs,
            asyncio.Event(),
            client_factory=lambda spec: Context(f"{spec.task_list}-client", events),
            worker_factory=lambda spec, client: Context(
                f"{spec.task_list}-worker", events, fail=spec.task_list == "second"
            ),
        )

    assert events == [
        "enter:first-client",
        "enter:first-worker",
        "enter:second-client",
        "enter:second-worker",
        "exit:second-client",
        "exit:first-worker",
        "exit:first-client",
    ]
