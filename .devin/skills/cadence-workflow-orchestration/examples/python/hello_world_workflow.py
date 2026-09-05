"""Minimal hello-world Cadence workflow + activity for Python.

See ../../00-get-started/local-quickstart.md for how to run a local server and domain,
and ../../03-python-client/workflows-and-activities.md for the full explanation of every
piece here.
"""

from datetime import timedelta

from cadence import Registry, activity, workflow
from cadence.workflow import execute_activity

registry = Registry()


@activity.defn()
async def hello_world_activity(name: str) -> str:
    activity.info()  # demonstrates activity context access; see workflows-and-activities.md
    return f"Hello {name}!"


@registry.workflow()
class HelloWorldWorkflow:
    @workflow.run
    async def run(self, name: str) -> str:
        return await execute_activity(
            "hello_world_activity",
            str,
            name,
            start_to_close_timeout=timedelta(minutes=1),
            heartbeat_timeout=timedelta(seconds=20),
        )
