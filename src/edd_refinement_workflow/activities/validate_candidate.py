from collections.abc import Callable
from datetime import datetime, timezone

from ..candidate_results import CandidateValidationResult, ExecutionResult


class ValidateCandidateActivity:
    def __init__(self, diff_provider: Callable[[], str] = lambda: "") -> None:
        self.diff_provider = diff_provider

    def _test_change_reason(self, planning: dict, execution: ExecutionResult) -> str | None:
        required_tests = set(planning.get("required_test_files", []))
        if not required_tests.intersection(execution.changed_files):
            return None
        diff = self.diff_provider()
        weakening_patterns = (
            "deleted file mode",
            "+@pytest.mark.skip",
            "+    assert True",
            "-def test_",
        )
        if any(pattern in diff for pattern in weakening_patterns):
            return "test_weakening"
        return "ambiguous_test_change"

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
            reason = self._test_change_reason(planning, execution)
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
