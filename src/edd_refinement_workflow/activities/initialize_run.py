from collections.abc import Callable

from common.mutation_lease_policy import LeaseConflictError, MutationLeasePolicyHandler
from common.mutation_lease_store import get_default_store

from ..candidate_results import EvaluationRunConfiguration


class InitializeRunActivity:
    def __init__(
        self, factory, on_event: Callable[..., None] | None = None
    ) -> None:
        self.factory = factory
        self.on_event = on_event

    def _acquire_lease(self, repo_root: str, run_id: str, lease_ttl: int) -> dict:
        store = get_default_store()
        policy = MutationLeasePolicyHandler(store, on_event=self.on_event)
        handle = policy.lease(repo_root, run_id, lease_ttl)
        token = handle.__enter__()
        return {
            "repo_key": repo_root,
            "run_id": run_id,
            "token": token,
            "ttl": lease_ttl,
            "acquired_at": "now",
        }

    def run(
        self,
        workflow_run_id: str,
        preflight_result,
        profile: dict,
        lease_ttl: int = 1200,
    ) -> dict:
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
            "schema_version": 5,
            "run_id": run_id,
            "workflow_run_id": workflow_run_id,
            "starting_revision": starting_revision,
            "token_usage": 0,
            "budgets": profile.get("limits", {}),
            "logical_iteration_count": 0,
            "cumulative_token_usage": 0,
            "consecutive_confirmed_regressions": 0,
            "pending_evidence_flags": [],
            "attempt_records": [],
            "iteration_history": [],
            "approval_request": None,
            "approval_history": [],
            "candidate": None,
            "candidate_history": [],
            "execution_artifacts": [],
            "evaluation_configuration": evaluation_configuration.to_dict(),
            "candidate_metrics": [],
            "best_accepted_state": None,
            "regression_evidence": [],
            "reverted_proposals": [],
            "recovery_results": [],
            "human_handoff_records": [],
        }

        repo_root = str(preflight_result.target_context.repo_root)
        created = self.factory.create_or_resume(run_id, record)
        created["test_cases"] = profile.get("test_cases")
        created["coverage_metadata_property"] = profile.get(
            "coverage_metadata_property"
        )
        created["inspect_command"] = profile.get("inspect_command")

        if created is record:
            created["mutation_lease"] = self._acquire_lease(
                repo_root, run_id, lease_ttl
            )
            created["target_repository"] = repo_root
            self.factory.store.save(run_id, created)
        else:
            created["target_repository"] = repo_root
            self.factory.store.save(run_id, created)

        event_name = "InitializeRun" if created is record else "ResumeRun"
        if self.on_event is not None:
            self.on_event(event_name, run_id=run_id, workflow_run_id=workflow_run_id)

        return created


from cadence import activity


@activity.defn(name="initialize_run")
async def initialize_run_activity(
    workflow_run_id: str,
    preflight_result,
    profile: dict,
    lease_ttl: int = 1200,
) -> dict:
    from ..progress_record import ProgressRecordFactory, ProgressRecordStore

    repo_root = preflight_result.target_context.repo_root
    store = ProgressRecordStore(repo_root)
    factory = ProgressRecordFactory(store)
    return InitializeRunActivity(factory).run(
        workflow_run_id, preflight_result, profile, lease_ttl
    )
