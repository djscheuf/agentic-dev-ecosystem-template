import pytest
from cadence import Registry, activity, workflow
from cadence.worker import Worker


def test_registry_supports_named_workflow_class_registration():
    class CharacterizedWorkflow:
        @workflow.run
        async def run(self):
            return None

    registry = Registry()

    registered_type = registry.workflow(name="CharacterizedWorkflow")(CharacterizedWorkflow)

    assert registered_type is CharacterizedWorkflow
    assert set(registry._workflows) == {"CharacterizedWorkflow"}


def test_registry_supports_named_activity_registration():
    @activity.defn(name="characterized_activity")
    async def characterized_activity():
        return None

    registry = Registry()

    registered_type = registry.register_activity(characterized_activity)

    assert registered_type is None
    assert set(registry._activities) == {"characterized_activity"}


@pytest.mark.asyncio
async def test_worker_async_context_runs_and_closes(monkeypatch):
    events = []

    async def run(worker):
        events.append("run")

    async def close(worker):
        events.append("close")

    monkeypatch.setattr(Worker, "run", run)
    monkeypatch.setattr(Worker, "close", close)
    worker = object.__new__(Worker)

    async with worker as entered_worker:
        events.append("entered")

    assert entered_worker is worker
    assert events == ["run", "entered", "close"]
