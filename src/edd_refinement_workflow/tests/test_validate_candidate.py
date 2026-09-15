import pytest

from edd_refinement_workflow.activities.validate_candidate import ValidateCandidateActivity
from edd_refinement_workflow.candidate_results import ExecutionResult, UsageMetrics


def _execution(changed_files: list[str]) -> ExecutionResult:
    return ExecutionResult(
        status="success",
        usage_metrics=UsageMetrics(1, 1, 2, 0.01),
        changed_files=changed_files,
        diff_hash="abc123",
        failure_reason=None,
        atif_path=None,
        duration_ms=1,
    )


@pytest.mark.parametrize(
    ("intended_files", "changed_files", "reason"),
    [
        (["src/skill.py"], [], "no_op"),
        (["src/skill.py"], ["README.md"], "out_of_scope"),
        (["src/skill.py"], ["src/skill.py", "README.md"], "out_of_scope"),
        ([], ["src/skill.py"], "empty_scope"),
    ],
)
def test_validate_candidate_rejects_invalid_file_scope(
    intended_files: list[str], changed_files: list[str], reason: str
) -> None:
    result = ValidateCandidateActivity().run(
        "run-1",
        {"intended_files": intended_files},
        _execution(changed_files),
    )

    assert result.status == "rejected"
    assert result.rejection_reason == reason
