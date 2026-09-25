import dataclasses
from concurrent.futures import ThreadPoolExecutor

import pytest

from edd_refinement_workflow.activities.validate_candidate import ValidateCandidateActivity
from edd_refinement_workflow.candidate_results import ExecutionResult, UsageMetrics
from edd_refinement_workflow.progress_record import ProgressRecordStore


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
        {
            "intended_files": intended_files,
            "modification_scope": ["src/", "README.md"],
        },
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
            "modification_scope": ["tests/"],
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
        {"intended_files": ["src/skill.py"], "modification_scope": ["src/"]},
        execution,
        approved_diff_hash="different",
    )
    malformed = activity.run(
        "run-1",
        {"intended_files": ["src/skill.py"], "modification_scope": ["src/"]},
        dataclasses.replace(
            execution,
            usage_metrics=UsageMetrics(1, 1, 99, 0.01),
        ),
    )

    assert mismatch.rejection_reason == "diff_mismatch"
    assert malformed.rejection_reason == "malformed_metrics"


def test_validate_candidate_rejects_diff_outside_authorized_scope() -> None:
    result = ValidateCandidateActivity().run(
        "run-1",
        {
            "intended_files": ["skill/ok.md", "outside/hack.py"],
            "modification_scope": ["skill/"],
        },
        _execution(["outside/hack.py"]),
    )

    assert result.status == "rejected"
    assert result.rejection_reason == "diff_out_of_scope"
    assert result.out_of_scope_details == {
        "check": "diff",
        "paths": ["outside/hack.py"],
    }


def test_validate_candidate_in_scope_diff_passes_scope_check() -> None:
    result = ValidateCandidateActivity().run(
        "run-1",
        {
            "intended_files": ["skill/ok.md"],
            "modification_scope": ["skill/"],
        },
        _execution(["skill/ok.md"]),
    )

    assert result.status == "scope_valid"
    assert result.rejection_reason is None


def test_validate_candidate_unplanned_but_authorized_change_keeps_out_of_scope_reason() -> None:
    result = ValidateCandidateActivity().run(
        "run-1",
        {
            "intended_files": ["skill/ok.md"],
            "modification_scope": ["skill/"],
        },
        _execution(["skill/extra.md"]),
    )

    assert result.status == "rejected"
    assert result.rejection_reason == "out_of_scope"


def test_concurrent_validations_preserve_independent_candidate_history(tmp_path) -> None:
    store = ProgressRecordStore(tmp_path)
    store.create_or_resume(
        "run-1",
        {"schema_version": 3, "run_id": "run-1", "candidate_history": []},
    )
    activity = ValidateCandidateActivity(store=store)
    executions = [
        dataclasses.replace(_execution(["src/skill.py"]), diff_hash=diff_hash)
        for diff_hash in ("candidate-a", "candidate-b")
    ]

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(
            executor.map(
                lambda execution: activity.run(
                    "run-1",
                    {"intended_files": ["src/skill.py"], "modification_scope": ["src/"]},
                    execution,
                ),
                executions,
            )
        )

    record = store.create_or_resume("run-1", {})
    assert {result.candidate_id for result in results} == {
        "run-1-candidate-a",
        "run-1-candidate-b",
    }
    assert {item["candidate_id"] for item in record["candidate_history"]} == {
        "run-1-candidate-a",
        "run-1-candidate-b",
    }


def test_validate_candidate_emits_rejection_event() -> None:
    events = []
    activity = ValidateCandidateActivity(
        on_event=lambda name, **data: events.append((name, data))
    )

    activity.run(
        "run-1",
        {"intended_files": ["src/skill.py"], "modification_scope": ["src/"]},
        _execution([]),
    )

    assert events[0][0] == "CandidateRejected"
    assert events[0][1]["rejection_reason"] == "no_op"
