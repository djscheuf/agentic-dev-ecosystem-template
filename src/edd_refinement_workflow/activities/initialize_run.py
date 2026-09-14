from collections.abc import Callable


class InitializeRunActivity:
    def __init__(
        self, factory, on_event: Callable[..., None] | None = None
    ) -> None:
        self.factory = factory
        self.on_event = on_event

    def run(self, workflow_run_id: str, preflight_result) -> dict:
        if preflight_result.status != "success":
            raise ValueError("preflight did not succeed")

        starting_revision = preflight_result.target_context.starting_revision
        run_id = self.factory.derive_run_id(workflow_run_id, starting_revision)

        record = {
            "schema_version": 1,
            "run_id": run_id,
            "workflow_run_id": workflow_run_id,
            "starting_revision": starting_revision,
            "token_usage": 0,
            "consecutive_confirmed_regressions": 0,
            "iteration_history": [],
        }

        created = self.factory.create_or_resume(run_id, record)

        event_name = "InitializeRun" if created is record else "ResumeRun"
        if self.on_event is not None:
            self.on_event(event_name, run_id=run_id, workflow_run_id=workflow_run_id)

        return created
