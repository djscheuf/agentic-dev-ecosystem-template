import asyncio
from datetime import timedelta

from cadence import workflow
from cadence.workflow import execute_activity, sleep, wait_condition


class EddRefinementWorkflow:
    def __init__(self) -> None:
        self._approval_request = None
        self._pending_approval_decision = None

    @workflow.run
    async def run(self, preflight_result, request: dict):
        record = await execute_activity(
            "initialize_run",
            dict,
            request["workflow_run_id"],
            preflight_result,
            start_to_close_timeout=timedelta(minutes=5),
        )
        if record.get("candidate") is not None:
            self._candidate = record["candidate"]
            return {"record": record, "candidate": record["candidate"]}

        baseline = await execute_activity(
            "run_baseline_evaluation",
            dict,
            record["run_id"],
            request["profile"],
            str(preflight_result.target_context.repo_root),
            start_to_close_timeout=timedelta(minutes=30),
        )

        planning = await execute_activity(
            "plan_refinement_action",
            dict,
            record,
            baseline,
            request.get("proposed_action"),
            request.get("proposal_id"),
            request.get("proposed_diff_hash"),
            start_to_close_timeout=timedelta(minutes=5),
        )

        result = {"record": record, "baseline": baseline, "planning": planning}
        if planning.get("action") == "stop":
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
                str(preflight_result.target_context.repo_root),
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
                str(preflight_result.target_context.repo_root),
                start_to_close_timeout=timedelta(minutes=5),
            )
            self._approval_request = approval
            result.update(approval=approval, approved=decision == "approve")
            if decision != "approve":
                result["next_state"] = request.get("approval_rejection_policy", "planning")
                return result
            approved_diff_hash = planning["proposed_diff_hash"]
            applied_change = await execute_activity(
                "record_human_approved_evaluation_change",
                dict,
                record["run_id"],
                request["executed_diff_hash"],
                str(preflight_result.target_context.repo_root),
                start_to_close_timeout=timedelta(minutes=5),
            )
            result["applied_change"] = applied_change

        execution = await execute_activity(
            "execute_refinement_action",
            dict,
            record["run_id"],
            planning,
            approved_diff_hash,
            str(preflight_result.target_context.repo_root),
            start_to_close_timeout=timedelta(minutes=30),
        )
        candidate = await execute_activity(
            "validate_candidate",
            dict,
            record["run_id"],
            planning,
            execution,
            approved_diff_hash,
            str(preflight_result.target_context.repo_root),
            start_to_close_timeout=timedelta(minutes=5),
        )
        result.update(execution=execution, candidate=candidate)
        self._candidate = candidate
        return result

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
