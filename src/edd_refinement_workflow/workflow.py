import asyncio
import json
from datetime import timedelta

from cadence import workflow
from cadence.workflow import execute_activity, sleep, wait_condition

from common.preflight import PreflightResult, TargetRepositoryContext

from .quality_ratchet import compare_candidate_to_best, resolve_comparison_baseline


class PreflightFailedError(Exception):
    def __init__(self, failed_conditions: list[str]) -> None:
        self.failed_conditions = failed_conditions
        super().__init__(f"preflight failed: {'; '.join(failed_conditions)}")


class OutOfScopeModificationError(Exception):
    def __init__(self, details: dict | None = None) -> None:
        self.details = details or {}
        self.terminal_reason = "out_of_scope_modification"
        super().__init__(
            f"out_of_scope_modification: {json.dumps(self.details, sort_keys=True)}"
        )


class EddRefinementWorkflow:
    def __init__(self) -> None:
        self._approval_request = None
        self._pending_approval_decision = None
        self._candidate = None
        self._regression_status = None

    @workflow.run
    async def run(self, input_document_path: str, workflow_id: str = ""):
        self._record = None
        self._repo_root = None
        self._finalized = False
        self._terminal_reason = None
        try:
            result = await self._run(input_document_path, workflow_id)
        except Exception as exc:
            if (
                self._record is not None
                and self._repo_root is not None
                and not self._finalized
            ):
                try:
                    await self._finalize(
                        self._record["run_id"],
                        getattr(exc, "terminal_reason", "workflow_exception"),
                        self._repo_root,
                    )
                except Exception:
                    pass
            raise
        if (
            self._record is not None
            and self._repo_root is not None
            and not self._finalized
        ):
            result["terminal_result"] = await self._finalize(
                self._record["run_id"],
                self._terminal_reason or "completed",
                self._repo_root,
            )
        return result

    async def _finalize(self, run_id: str, reason: str, repo_root: str) -> dict:
        self._finalized = True
        return await execute_activity(
            "finalize_run",
            dict,
            run_id,
            reason,
            repo_root,
            start_to_close_timeout=timedelta(minutes=5),
        )

    async def _run(self, input_document_path: str, workflow_id: str):
        preflight_output = await execute_activity(
            "preflight",
            dict,
            input_document_path,
            workflow_id,
            start_to_close_timeout=timedelta(minutes=5),
        )
        raw_result = preflight_output["preflight_result"]
        if raw_result["status"] != "success":
            raise PreflightFailedError(raw_result.get("failed_conditions") or [])
        context = raw_result["target_context"]
        preflight_result = PreflightResult(
            status=raw_result["status"],
            target_context=TargetRepositoryContext(**context) if context else None,
            provider=raw_result.get("provider"),
            failed_conditions=raw_result.get("failed_conditions") or [],
        )
        request = preflight_output["request"]

        record = await execute_activity(
            "initialize_run",
            dict,
            request["workflow_run_id"],
            preflight_result,
            request["profile"],
            request.get("edd_input"),
            request.get("input_path"),
            request.get("lease_ttl", 1200),
            start_to_close_timeout=timedelta(minutes=5),
        )
        self._record = record
        repo_root = str(preflight_result.target_context.repo_root)
        self._repo_root = repo_root
        if record.get("candidate") is not None:
            self._candidate = record["candidate"]
            return {"record": record, "candidate": record["candidate"]}

        if "budgets" in record:
            limit_decision = await execute_activity(
                "check_refinement_limits",
                dict,
                record,
                0,
                start_to_close_timeout=timedelta(minutes=5),
            )
            if not limit_decision["schedule_next_step"]:
                terminal_result = await self._finalize(
                    record["run_id"],
                    limit_decision["stop_reason"],
                    repo_root,
                )
                return {
                    "record": record,
                    "limit_decision": limit_decision,
                    "terminal_result": terminal_result,
                }

        baseline = record.get("baseline_metrics")
        if baseline is None:
            baseline = await execute_activity(
                "run_baseline_evaluation",
                dict,
                record["run_id"],
                request["profile"],
                repo_root,
                start_to_close_timeout=timedelta(
                    seconds=request["profile"]["timeout"]
                ),
            )
            record["baseline_metrics"] = baseline

        result = {"record": record, "baseline": baseline}
        lease_ttl = request.get("lease_ttl", 3600)
        while True:
            await execute_activity(
                "renew_mutation_lease",
                dict,
                repo_root,
                record["run_id"],
                lease_ttl,
                start_to_close_timeout=timedelta(minutes=1),
            )
            if "budgets" in record:
                limit_decision = await execute_activity(
                    "check_refinement_limits",
                    dict,
                    record,
                    0,
                    start_to_close_timeout=timedelta(minutes=5),
                )
                if not limit_decision["schedule_next_step"]:
                    result["terminal_result"] = await self._finalize(
                        record["run_id"],
                        limit_decision["stop_reason"],
                        repo_root,
                    )
                    return result

            planning = await execute_activity(
                "edd_plan",
                dict,
                record["run_id"],
                repo_root,
                record,
                baseline,
                request.get("proposal_id"),
                request.get("proposed_diff_hash"),
                request.get("input_path"),
                start_to_close_timeout=timedelta(minutes=5),
            )
            result["planning"] = planning
            if planning.get("rejection_reason") == "plan_out_of_scope":
                raise OutOfScopeModificationError(
                    planning.get("out_of_scope_details")
                )
            if "budgets" in record:
                record, limit_decision = await self._account_and_check_limits(
                    record, planning, "planning", repo_root
                )
                if not limit_decision["schedule_next_step"]:
                    result["terminal_result"] = await self._finalize(
                        record["run_id"],
                        limit_decision["stop_reason"],
                        repo_root,
                    )
                    return result
            if planning.get("action") == "stop":
                result["terminal_result"] = await self._finalize(
                    record["run_id"],
                    planning.get("rationale", "planning_stopped"),
                    repo_root,
                )
                return result

            approved_diff_hash = None
            if planning.get("requires_approval"):
                timeout_seconds = request.get("approval_timeout_seconds", 3600)
                await execute_activity(
                    "renew_mutation_lease",
                    dict,
                    repo_root,
                    record["run_id"],
                    lease_ttl,
                    start_to_close_timeout=timedelta(minutes=1),
                )
                self._approval_request = await execute_activity(
                    "request_human_approval",
                    dict,
                    record["run_id"],
                    planning,
                    timeout_seconds,
                    repo_root,
                    start_to_close_timeout=timedelta(minutes=5),
                )
                decision = await self._await_approval(timedelta(seconds=timeout_seconds))
                approval = await execute_activity(
                    "record_human_approval_decision",
                    dict,
                    record["run_id"],
                    planning["proposal_id"],
                    decision,
                    self._pending_approval_decision.get("notes", "")
                    if self._pending_approval_decision
                    else "",
                    repo_root,
                    start_to_close_timeout=timedelta(minutes=5),
                )
                self._approval_request = approval
                result.update(approval=approval, approved=decision == "approve")
                if decision != "approve":
                    result["next_state"] = request.get(
                        "approval_rejection_policy", "planning"
                    )
                    self._terminal_reason = f"approval_{decision}"
                    return result
                approved_diff_hash = planning["proposed_diff_hash"]
                applied_change = await execute_activity(
                    "record_human_approved_evaluation_change",
                    dict,
                    record["run_id"],
                    request["executed_diff_hash"],
                    repo_root,
                    start_to_close_timeout=timedelta(minutes=5),
                )
                result["applied_change"] = applied_change

            execution = await execute_activity(
                "edd_do",
                dict,
                record["run_id"],
                planning,
                approved_diff_hash,
                repo_root,
                start_to_close_timeout=timedelta(minutes=30),
            )
            result["execution"] = execution
            if "budgets" in record:
                record, limit_decision = await self._account_and_check_limits(
                    record, execution, "execution", repo_root
                )
                if not limit_decision["schedule_next_step"]:
                    result["terminal_result"] = await self._finalize(
                        record["run_id"],
                        limit_decision["stop_reason"],
                        repo_root,
                    )
                    return result
            if execution.get("status") == "failed":
                self._terminal_reason = "execution_failed"
                return result

            candidate = await execute_activity(
                "validate_candidate",
                dict,
                record["run_id"],
                planning,
                execution,
                approved_diff_hash,
                repo_root,
                start_to_close_timeout=timedelta(minutes=5),
            )
            if candidate.get("rejection_reason") == "diff_out_of_scope":
                raise OutOfScopeModificationError(
                    candidate.get("out_of_scope_details")
                )
            if candidate.get("status") != "scope_valid":
                result.update(execution=execution, candidate=candidate)
                self._candidate = candidate
                self._terminal_reason = "candidate_rejected"
                return result

            retry_configuration = request["profile"].get("retry_policy", {})
            retry_policy = {
                "maximum_attempts": retry_configuration.get("maximum_attempts", 3),
                "initial_interval": timedelta(
                    seconds=retry_configuration.get("initial_interval_seconds", 1)
                ),
                "backoff_coefficient": retry_configuration.get(
                    "backoff_coefficient", 2.0
                ),
                "maximum_interval": timedelta(
                    seconds=retry_configuration.get("maximum_interval_seconds", 300)
                ),
            }
            candidate_check = await execute_activity(
                "check_candidate",
                dict,
                record["run_id"],
                candidate["candidate_id"],
                repo_root,
                start_to_close_timeout=timedelta(
                    seconds=request["profile"]["timeout"]
                ),
                retry_policy=retry_policy,
            )
            candidate_evaluation = candidate_check.get("metrics", candidate_check)
            result.update(
                execution=execution,
                candidate=candidate,
                candidate_evaluation=candidate_evaluation,
                candidate_check=candidate_check,
            )
            if "budgets" in record:
                record, limit_decision = await self._account_and_check_limits(
                    record, candidate_evaluation, "evaluation", repo_root
                )
                if not limit_decision["schedule_next_step"]:
                    result["terminal_result"] = await self._finalize(
                        record["run_id"],
                        limit_decision["stop_reason"],
                        repo_root,
                    )
                    return result

            best_state = record.get("best_accepted_state")
            if best_state is not None or "budgets" in record:
                comparison_baseline = candidate_check.get(
                    "baseline"
                ) or resolve_comparison_baseline(planning, best_state, baseline)
                comparison = candidate_check.get("comparison")
                if comparison is None:
                    determination = candidate_check.get("determination")
                    if determination in {"accept", "reject", "rerun", "escalate"}:
                        comparison = {"decision": determination}
                    elif determination is not None:
                        comparison = {
                            "decision": "reject",
                            "reason": determination,
                        }
                    else:
                        comparison = compare_candidate_to_best(
                            candidate_evaluation, comparison_baseline
                        )
                result["comparison"] = comparison
                if comparison["decision"] == "accept":
                    best_state = await execute_activity(
                        "commit_accepted_candidate",
                        dict,
                        record["run_id"],
                        candidate_evaluation,
                        repo_root,
                        start_to_close_timeout=timedelta(minutes=5),
                    )
                    record["best_accepted_state"] = best_state
                    record["consecutive_confirmed_regressions"] = 0
                    record["candidate_history"] = record.get("candidate_history", []) + [
                        {
                            "candidate_id": candidate["candidate_id"],
                            "status": "accepted",
                            "commit": best_state.get("commit"),
                        }
                    ]
                    result["best_accepted_state"] = best_state
                elif comparison["decision"] == "rerun":
                    result["confirmation_rerun"] = await execute_activity(
                        "rerun_degraded_candidate",
                        dict,
                        record["run_id"],
                        candidate["candidate_id"],
                        repo_root,
                        comparison_baseline,
                        start_to_close_timeout=timedelta(
                            seconds=request["profile"]["timeout"]
                        ),
                    )
                    # Preserve best_state's commit (needed by revert_repository_to_best)
                    # but classify/verify against the frozen iteration-start baseline,
                    # not a best_accepted_state that may have advanced mid-iteration.
                    regression_reference_state = (
                        {**best_state, "metrics": comparison_baseline}
                        if best_state is not None
                        else {"metrics": comparison_baseline}
                    )
                    result["regression_recovery"] = await self._handle_regression(
                        record["run_id"],
                        candidate["candidate_id"],
                        candidate_evaluation,
                        result["confirmation_rerun"].get(
                            "result", result["confirmation_rerun"]
                        ),
                        regression_reference_state,
                        repo_root,
                        request.get("regression_stop_threshold", 3),
                    )
                    if result["regression_recovery"]["next_state"] != "planning":
                        self._terminal_reason = "pending_human_review"
                        return result
                    regression = result["regression_recovery"].get("regression", {})
                    record["consecutive_confirmed_regressions"] = regression.get(
                        "consecutive_confirmed_regressions",
                        record.get("consecutive_confirmed_regressions", 0) + 1,
                    )
                else:
                    record["candidate_history"] = record.get("candidate_history", []) + [
                        {
                            "candidate_id": candidate["candidate_id"],
                            "status": "rejected",
                        }
                    ]

            if "budgets" not in record:
                return result

    async def _account_and_check_limits(self, record, result, step, repo_root):
        usage = result.get("usage_metrics")
        attempt = {
            "attempt_id": f"{step}-{record['run_id']}",
            "step": step,
            "logical_iteration_number": result.get("logical_iteration_number", 0),
            "is_retry": result.get("is_retry", False),
            "usage_metrics": usage,
            "status": result.get("status", "success"),
        }
        record = await execute_activity(
            "update_durable_counters",
            dict,
            record["run_id"],
            attempt,
            repo_root,
            start_to_close_timeout=timedelta(minutes=5),
        )
        limit_decision = await execute_activity(
            "check_refinement_limits",
            dict,
            record,
            0,
            start_to_close_timeout=timedelta(minutes=5),
        )
        return record, limit_decision

    async def _handle_regression(self, run_id, candidate_id, original, confirmation, best_state, repo_root, stop_threshold):
        classification = await execute_activity("classify_regression_evidence", dict, original, confirmation, best_state, start_to_close_timeout=timedelta(minutes=5))
        if classification["classification"] != "confirmed_regression":
            handoff = await execute_activity("human_handoff", dict, run_id, classification["classification"], {"original": original, "confirmation": confirmation}, repo_root, start_to_close_timeout=timedelta(minutes=5))
            self._regression_status = {"classification": classification, "human_handoff": handoff, "next_state": "pending_human_review"}
            return self._regression_status
        regression = await execute_activity("record_confirmed_regression", dict, run_id, candidate_id, original, confirmation, stop_threshold, repo_root, start_to_close_timeout=timedelta(minutes=5))
        if regression["threshold_reached"]:
            handoff = await execute_activity("publish_human_handoff", dict, run_id, "regression_threshold", repo_root, start_to_close_timeout=timedelta(minutes=5))
            self._regression_status = {"classification": classification, "regression": regression, "human_handoff": handoff, "next_state": "pending_human_review"}
            return self._regression_status
        restored = await execute_activity("revert_repository_to_best", dict, run_id, repo_root, best_state, start_to_close_timeout=timedelta(minutes=5))
        recovery_metrics = await execute_activity("evaluate_candidate", dict, run_id, "best_accepted_recovery", repo_root, start_to_close_timeout=timedelta(minutes=30))
        recovery = await execute_activity("verify_recovery_metrics", dict, recovery_metrics, best_state["metrics"], start_to_close_timeout=timedelta(minutes=5))
        context = await execute_activity("record_reverted_proposal_context", dict, run_id, {"candidate_id": candidate_id, "observed_degradation": original, "confirmation_result": confirmation, "recovery_result": recovery}, repo_root, start_to_close_timeout=timedelta(minutes=5))
        self._regression_status = {"classification": classification, "regression": regression, "restored": restored, "recovery": recovery, "reverted_proposal": context, "next_state": "planning" if recovery["recovered"] else "pending_human_review"}
        return self._regression_status

    @workflow.query(name="get_regression_status")
    def get_regression_status(self):
        return self._regression_status

    @workflow.query(name="get_candidate_status")
    def get_candidate_status(self):
        return self._candidate

    async def _await_approval(self, timeout: timedelta) -> str:
        wait_task = asyncio.ensure_future(
            wait_condition(lambda: self._pending_approval_decision is not None)
        )
        timer_task = asyncio.ensure_future(sleep(timeout))
        done, pending = await asyncio.wait(
            {wait_task, timer_task}, return_when=asyncio.FIRST_COMPLETED
        )
        for task in pending:
            task.cancel()
        if wait_task in done:
            return self._pending_approval_decision["decision"]
        return "timeout"

    @workflow.signal(name="approve_evaluation_change")
    def approve_evaluation_change(
        self, decision: str, proposal_id: str, notes: str = ""
    ) -> None:
        if self._pending_approval_decision is not None:
            return
        if self._approval_request and self._approval_request.get("status") != "pending":
            return
        if decision not in {"approve", "reject"}:
            raise ValueError("invalid approval decision")
        if not self._approval_request or self._approval_request["proposal_id"] != proposal_id:
            raise ValueError("approval decision does not match pending proposal")
        self._pending_approval_decision = {
            "decision": decision,
            "proposal_id": proposal_id,
            "notes": notes,
        }

    @workflow.query(name="get_approval_status")
    def get_approval_status(self) -> dict | None:
        return self._approval_request
