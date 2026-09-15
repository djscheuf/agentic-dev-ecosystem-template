from datetime import datetime, timezone

from ..candidate_results import CandidateValidationResult, ExecutionResult


class ValidateCandidateActivity:
    def run(
        self,
        run_id: str,
        planning: dict,
        execution: ExecutionResult,
    ) -> CandidateValidationResult:
        intended_files = planning.get("intended_files") or []
        if not intended_files:
            reason = "empty_scope"
        elif not execution.changed_files:
            reason = "no_op"
        elif any(path not in intended_files for path in execution.changed_files):
            reason = "out_of_scope"
        else:
            reason = None
        return CandidateValidationResult(
            candidate_id=f"{run_id}-{execution.diff_hash[:12]}",
            run_id=run_id,
            status="rejected" if reason else "scope_valid",
            usage_metrics=execution.usage_metrics,
            changed_files=execution.changed_files,
            diff_hash=execution.diff_hash,
            rejection_reason=reason,
            validated_at=datetime.now(timezone.utc).isoformat(),
        )
