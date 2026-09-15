import dataclasses
import threading
from collections.abc import Callable
from datetime import datetime, timezone

from ..candidate_results import CandidateValidationResult, ExecutionResult


class ValidateCandidateActivity:
    def __init__(
        self,
        diff_provider: Callable[[], str] = lambda: "",
        store=None,
    ) -> None:
        self.diff_provider = diff_provider
        self.store = store
        self._store_lock = threading.Lock()

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
        approved_diff_hash: str | None = None,
    ) -> CandidateValidationResult:
        intended_files = planning.get("intended_files") or []
        metrics = execution.usage_metrics
        metric_values = (
            metrics.input_tokens,
            metrics.output_tokens,
            metrics.total_tokens,
            metrics.cost_usd,
        )
        if approved_diff_hash is not None and approved_diff_hash != execution.diff_hash:
            reason = "diff_mismatch"
        elif not all(isinstance(value, (int, float)) and value >= 0 for value in metric_values):
            reason = "malformed_metrics"
        elif metrics.total_tokens != metrics.input_tokens + metrics.output_tokens:
            reason = "malformed_metrics"
        elif not intended_files:
            reason = "empty_scope"
        elif not execution.changed_files:
            reason = "no_op"
        elif any(path not in intended_files for path in execution.changed_files):
            reason = "out_of_scope"
        else:
            reason = self._test_change_reason(planning, execution)
        result = CandidateValidationResult(
            candidate_id=f"{run_id}-{execution.diff_hash[:12]}",
            run_id=run_id,
            status="rejected" if reason else "scope_valid",
            usage_metrics=execution.usage_metrics,
            changed_files=execution.changed_files,
            diff_hash=execution.diff_hash,
            rejection_reason=reason,
            validated_at=datetime.now(timezone.utc).isoformat(),
        )
        if self.store is not None:
            with self._store_lock:
                record = self.store.create_or_resume(run_id, {})
                candidate = dataclasses.asdict(result)
                record["candidate"] = candidate
                record["candidate_history"] = record.get("candidate_history", []) + [candidate]
                self.store.save(run_id, record)
        return result
