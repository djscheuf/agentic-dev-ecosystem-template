import dataclasses

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


@pytest.mark.parametrize(
    ("diff", "reason"),
    [
        ("deleted file mode 100644", "test_weakening"),
        ("+@pytest.mark.skip", "test_weakening"),
        ("-    assert result == 1\n+    assert True", "test_weakening"),
        ("-def test_required():\n+def test_rewritten():", "test_weakening"),
        ("@@ -1 +1 @@\n-old expectation\n+new expectation", "ambiguous_test_change"),
    ],
)
def test_validate_candidate_rejects_required_test_changes(
    diff: str, reason: str
) -> None:
    result = ValidateCandidateActivity(diff_provider=lambda: diff).run(
        "run-1",
        {
            "intended_files": ["tests/test_required.py"],
            "required_test_files": ["tests/test_required.py"],
        },
        _execution(["tests/test_required.py"]),
    )

    assert result.status == "rejected"
    assert result.rejection_reason == reason


def test_validate_candidate_rejects_diff_mismatch_and_malformed_metrics() -> None:
    activity = ValidateCandidateActivity()
    execution = _execution(["src/skill.py"])

    mismatch = activity.run(
        "run-1",
        {"intended_files": ["src/skill.py"]},
        execution,
        approved_diff_hash="different",
    )
    malformed = activity.run(
        "run-1",
        {"intended_files": ["src/skill.py"]},
        dataclasses.replace(
            execution,
            usage_metrics=UsageMetrics(1, 1, 99, 0.01),
        ),
    )

    assert mismatch.rejection_reason == "diff_mismatch"
    assert malformed.rejection_reason == "malformed_metrics"
