import os
import time
from collections.abc import Callable
from pathlib import Path

import yaml

from common.mutation_lease_policy import LeaseConflictError, MutationLeasePolicyHandler
from common.mutation_lease_store import get_default_store
from common.preflight import PreflightResult

from ..candidate_results import EvaluationRunConfiguration


_ACTION_TAXONOMY = [
    {
        "action": "add_coverage",
        "description": (
            "Add a missing required test case, or extend deterministic assertions, "
            "without weakening any existing expectation."
        ),
    },
    {
        "action": "repair",
        "description": (
            "Fix a defect in a scripted assertion, fixture, or evaluation helper "
            "(a fixture bug or helper bug, not a real model gap)."
        ),
    },
    {
        "action": "refine_skill",
        "description": (
            "Modify the target skill's SKILL.md / prompt / instructions to close a "
            "genuine model gap against a rubric the evaluation correctly represents."
        ),
    },
    {
        "action": "refine_supporting_docs",
        "description": (
            "Modify an authorized reference, example, template, or other document the "
            "target skill depends on."
        ),
    },
    {
        "action": "propose_evaluation_expectation_change",
        "description": (
            "Change what an evaluation expects (an LLM rubric, an expected/floor score). "
            "This action requires explicit human approval before edd-do may apply it; "
            "never select it as a first attempt at a failure."
        ),
    },
    {
        "action": "stop",
        "description": (
            "No defensible action remains, the objective is already met, or a "
            "budget/regression limit blocks another safe attempt."
        ),
    },
]


def _resolve_modification_scope(
    edd_input: dict | None, repo_root: str, input_parent: str
) -> list[str]:
    if not edd_input:
        return []
    root = Path(repo_root).resolve()
    canonical = []
    for raw in edd_input.get("modification_scope") or []:
        normalized = str(raw).replace("\\", "/")
        if normalized.startswith("~"):
            normalized = os.path.expanduser(normalized)
        resolved = (Path(input_parent) / normalized).resolve()
        try:
            relative = resolved.relative_to(root)
        except ValueError:
            continue
        entry = relative.as_posix()
        if resolved.is_dir():
            entry += "/"
        canonical.append(entry)
    return canonical


class InitializeRunActivity:
    def __init__(
        self,
        factory,
        on_event: Callable[..., None] | None = None,
        check_harness: Callable[..., dict] | None = None,
    ) -> None:
        self.factory = factory
        self.on_event = on_event
        self.check_harness = check_harness

    def _acquire_lease(self, repo_root: str, run_id: str, lease_ttl: int) -> dict:
        store = get_default_store(Path(repo_root) / ".process" / "mutation-leases.json")
        policy = MutationLeasePolicyHandler(store, on_event=self.on_event)
        handle = policy.lease(repo_root, run_id, lease_ttl)
        token = handle.__enter__()
        acquired_at = time.time()
        return {
            "repo_key": repo_root,
            "run_id": run_id,
            "token": token,
            "ttl": lease_ttl,
            "acquired_at": acquired_at,
            "dead_by": acquired_at + lease_ttl,
        }

    def _run_baseline_check(
        self,
        run_id: str,
        repo_root: str,
    ) -> dict:
        from .check_candidate import CheckCandidateActivity
        from .evaluate_candidate import _run_evaluation_command

        return CheckCandidateActivity(
            self.factory.store,
            self.check_harness or _run_evaluation_command,
        ).run(run_id, "baseline", repo_root)

    def _write_refinement_context(
        self,
        repo_root: str,
        run_id: str,
        workflow_run_id: str,
        edd_input: dict,
        input_parent: str,
        baseline: dict,
    ) -> Path:
        context = {
            "schema_version": 1,
            "run_id": run_id,
            "workflow_run_id": workflow_run_id,
            "input_parent": input_parent,
            "edd_input": edd_input,
            "baseline": baseline,
            "taxonomy": _ACTION_TAXONOMY,
            "iterations": [],
        }
        path = (
            Path(repo_root)
            / ".process"
            / "edd"
            / run_id
            / "refinement.yaml"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump(context, sort_keys=False))
        return path

    def run(
        self,
        workflow_run_id: str,
        preflight_result: PreflightResult,
        profile: dict,
        edd_input: dict | None = None,
        input_path: str | None = None,
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
            "attempts": [],
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
            "modification_scope": [],
            "scope_violations": [],
        }

        repo_root = str(preflight_result.target_context.repo_root)
        created = self.factory.create_or_resume(run_id, record)
        created["test_cases"] = profile.get("test_cases")
        created["coverage_metadata_property"] = profile.get(
            "coverage_metadata_property"
        )
        created["inspect_command"] = profile.get("inspect_command")

        input_parent = str(Path(input_path).parent) if input_path else repo_root

        if created is record:
            created["mutation_lease"] = self._acquire_lease(
                repo_root, run_id, lease_ttl
            )
            created["target_repository"] = repo_root
            created["input_path"] = input_path
            created["input_parent"] = input_parent
            created["modification_scope"] = _resolve_modification_scope(
                edd_input, repo_root, input_parent
            )
            self.factory.store.save(run_id, created)

            baseline_check = self._run_baseline_check(run_id, repo_root)
            created["baseline_metrics"] = baseline_check["metrics"]
            self.factory.store.save(run_id, created)

            if edd_input is not None:
                self._write_refinement_context(
                    repo_root,
                    run_id,
                    workflow_run_id,
                    edd_input,
                    input_parent,
                    baseline_check["metrics"],
                )
        else:
            created["target_repository"] = repo_root
            created["input_path"] = input_path or created.get("input_path")
            created["input_parent"] = input_parent or created.get("input_parent")
            self.factory.store.save(run_id, created)

        event_name = "InitializeRun" if created is record else "ResumeRun"
        if self.on_event is not None:
            self.on_event(event_name, run_id=run_id, workflow_run_id=workflow_run_id)

        return created


from cadence import activity


@activity.defn(name="initialize_run")
async def initialize_run_activity(
    workflow_run_id: str,
    preflight_result: PreflightResult,
    profile: dict,
    edd_input: dict | None = None,
    input_path: str | None = None,
    lease_ttl: int = 1200,
) -> dict:
    from ..progress_record import ProgressRecordFactory, ProgressRecordStore

    repo_root = preflight_result.target_context.repo_root
    store = ProgressRecordStore(repo_root)
    factory = ProgressRecordFactory(store)
    return InitializeRunActivity(factory).run(
        workflow_run_id,
        preflight_result,
        profile,
        edd_input=edd_input,
        input_path=input_path,
        lease_ttl=lease_ttl,
    )
