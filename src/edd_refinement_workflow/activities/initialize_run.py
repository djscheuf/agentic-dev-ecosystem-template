from collections.abc import Callable

from ..candidate_results import EvaluationRunConfiguration


class InitializeRunActivity:
    def __init__(
        self, factory, on_event: Callable[..., None] | None = None
    ) -> None:
        self.factory = factory
        self.on_event = on_event

    def run(self, workflow_run_id: str, preflight_result, profile: dict) -> dict:
        if preflight_result.status != "success":
            raise ValueError("preflight did not succeed")

        starting_revision = preflight_result.target_context.starting_revision
        run_id = self.factory.derive_run_id(workflow_run_id, starting_revision)
        evaluation_configuration = EvaluationRunConfiguration(
            command=profile["command"],
            configuration=profile["configuration"],
            pinned_provider_version=profile["provider"],
            timeout_seconds=profile["timeout"],
            measurement_context=profile.get("measurement_context", "baseline"),
        )

        record = {
            "schema_version": 4,
            "run_id": run_id,
            "workflow_run_id": workflow_run_id,
            "starting_revision": starting_revision,
            "token_usage": 0,
            "consecutive_confirmed_regressions": 0,
            "iteration_history": [],
            "approval_request": None,
            "approval_history": [],
            "candidate": None,
            "candidate_history": [],
            "execution_artifacts": [],
            "evaluation_configuration": evaluation_configuration.to_dict(),
            "candidate_metrics": [],
            "best_accepted_state": None,
        }

        created = self.factory.create_or_resume(run_id, record)

        event_name = "InitializeRun" if created is record else "ResumeRun"
        if self.on_event is not None:
            self.on_event(event_name, run_id=run_id, workflow_run_id=workflow_run_id)

        return created


from cadence import activity


@activity.defn(name="initialize_run")
async def initialize_run_activity(
    workflow_run_id: str, preflight_result, profile: dict
) -> dict:
    from ..progress_record import ProgressRecordFactory, ProgressRecordStore

    repo_root = preflight_result.target_context.repo_root
    store = ProgressRecordStore(repo_root)
    factory = ProgressRecordFactory(store)
    return InitializeRunActivity(factory).run(workflow_run_id, preflight_result, profile)
