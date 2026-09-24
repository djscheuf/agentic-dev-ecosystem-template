import asyncio
from datetime import timedelta

from cadence import workflow
from cadence.workflow import execute_activity, sleep, wait_condition

from common.preflight import PreflightResult

from .quality_ratchet import compare_candidate_to_best, resolve_comparison_baseline


class EddRefinementWorkflow:
    def __init__(self) -> None:
        self._approval_request = None
        self._pending_approval_decision = None
        self._candidate = None
        self._regression_status = None

    @workflow.run
    async def run(self, preflight_result: PreflightResult, request: dict):
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
        if record.get("candidate") is not None:
            self._candidate = record["candidate"]
            return {"record": record, "candidate": record["candidate"]}

        repo_root = str(preflight_result.target_context.repo_root)
        if "budgets" in record:
            limit_decision = await execute_activity(
                "check_refinement_limits",
                dict,
                record,
                0,
                start_to_close_timeout=timedelta(minutes=5),
            )
            if not limit_decision["schedule_next_step"]:
                terminal_result = await execute_activity(
                    "finalize_run",
                    dict,
                    record["run_id"],
                    limit_decision["stop_reason"],
                    repo_root,
                    start_to_close_timeout=timedelta(minutes=5),
                )
                return {
                    "record": record,
                    "limit_decision": limit_decision,
                    "terminal_result": terminal_result,
                }

        baseline = record.get("baseline_metrics", {})

        result = {"record": record, "baseline": baseline}
        while True:
            if "budgets" in record:
                limit_decision = await execute_activity(
                    "check_refinement_limits",
                    dict,
                    record,
                    0,
                    start_to_close_timeout=timedelta(minutes=5),
                )
                if not limit_decision["schedule_next_step"]:
                    result["terminal_result"] = await execute_activity(
                        "finalize_run",
                        dict,
                        record["run_id"],
                        limit_decision["stop_reason"],
                        repo_root,
                        start_to_close_timeout=timedelta(minutes=5),
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
            if "budgets" in record:
                record, limit_decision = await self._account_and_check_limits(
                    record, planning, "planning", repo_root
                )
                if not limit_decision["schedule_next_step"]:
                    result["terminal_result"] = await execute_activity(
                        "finalize_run",
                        dict,
                        record["run_id"],
                        limit_decision["stop_reason"],
                        repo_root,
                        start_to_close_timeout=timedelta(minutes=5),
                    )
                    return result
            if planning.get("action") == "stop":
                result["terminal_result"] = await execute_activity(
                    "finalize_run",
                    dict,
                    record["run_id"],
                    planning.get("rationale", "planning_stopped"),
                    repo_root,
                    start_to_close_timeout=timedelta(minutes=5),
                )
                return result

            approved_diff_hash = None
            if planning.get("requires_approval"):
                timeout_seconds = request.get("approval_timeout_seconds", 3600)
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
                    result["terminal_result"] = await execute_activity(
                        "finalize_run",
                        dict,
                        record["run_id"],
                        limit_decision["stop_reason"],
                        repo_root,
                        start_to_close_timeout=timedelta(minutes=5),
                    )
                    return result
            if execution.get("status") == "failed":
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
            if candidate.get("status") != "scope_valid":
                result.update(execution=execution, candidate=candidate)
                self._candidate = candidate
                return result

            retry_configuration = request["profile"].get("retry_policy", {})
            retry_policy = {
                "maximum_attempts": retry_configuration.get("maximum_attempts", 3),
                "initial_interval": timedelta(
                    seconds=retry_configuration.get("initial_interval_seconds", 1)
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
                    result["terminal_result"] = await execute_activity(
                        "finalize_run",
                        dict,
                        record["run_id"],
                        limit_decision["stop_reason"],
                        repo_root,
                        start_to_close_timeout=timedelta(minutes=5),
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
