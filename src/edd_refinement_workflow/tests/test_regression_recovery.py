import pytest

from edd_refinement_workflow.activities.regression_recovery import (
    HumanHandoffActivity,
    RecordRevertedProposalContextActivity,
    RevertRepositoryToBestActivity,
    classify_regression_evidence,
    record_successful_proposal,
    verify_recovery_metrics,
)


@pytest.mark.parametrize(
    ("confirmation", "expected"),
    [
        ({"status": "success", "passing": 4, "measurement_context": "baseline"}, "confirmed_regression"),
        ({"status": "success", "passing": 5, "measurement_context": "baseline"}, "unstable_result"),
        ({"status": "timeout", "passing": 0, "measurement_context": "baseline"}, "suspected_flakiness"),
        ({"status": "success", "passing": 4, "measurement_context": "changed"}, "suspected_flakiness"),
        ({"status": "success", "measurement_context": "baseline"}, "inconclusive"),
    ],
)
def test_classify_regression_evidence_routes_confirmation_outcomes(confirmation, expected) -> None:
    result = classify_regression_evidence(
        {"status": "success", "passing": 4, "measurement_context": "baseline"},
        confirmation,
        {"metrics": {"passing": 5, "measurement_context": "baseline"}},
    )

    assert result["classification"] == expected


def test_verify_recovery_metrics_reports_exact_matches_and_mismatches() -> None:
    best = {"passing": 5, "failing": 1, "total": 6, "percentage": 83.333333, "required_coverage": {"r1": 1}}

    matched = verify_recovery_metrics(best | {"percentage": 83.3333334}, best)
    mismatched = verify_recovery_metrics(best | {"failing": 2}, best)

    assert matched == {"recovered": True, "matched_fields": ["passing", "failing", "total", "required_coverage", "percentage"], "mismatched_fields": [], "reason": "recovery metrics match"}
    assert mismatched["recovered"] is False
    assert mismatched["mismatched_fields"] == ["failing"]


def test_revert_repository_to_best_requires_lease_and_clean_restore() -> None:
    calls = []
    activity = RevertRepositoryToBestActivity(
        lease_held=lambda repo, run: True,
        reset=lambda repo, commit: calls.append((repo, commit)),
        is_clean=lambda repo: True,
    )

    result = activity.run("run-1", "/repo", {"commit": "accepted-1"})

    assert calls == [("/repo", "accepted-1")]
    assert result == {"restored_commit": "accepted-1", "repo_clean": True}


def test_record_reverted_proposal_appends_redacted_context(tmp_path) -> None:
    from edd_refinement_workflow.progress_record import ProgressRecordStore

    store = ProgressRecordStore(tmp_path)
    store.create_or_resume("run-1", {"reverted_proposals": []})
    activity = RecordRevertedProposalContextActivity(store, now=lambda: "2026-09-15T00:00:00Z")

    result = activity.run("run-1", {"candidate_id": "candidate-1", "change_summary": "uses ${API_TOKEN}", "affected_files": ["src/a.py"]})

    assert result["change_summary"] == "[REDACTED]"
    assert store.create_or_resume("run-1", {})["reverted_proposals"] == [result]


def test_regression_recovery_with_successful_proposal_resets_consecutive_counter(tmp_path) -> None:
    from edd_refinement_workflow.progress_record import ProgressRecordStore

    store = ProgressRecordStore(tmp_path)
    store.create_or_resume("run-1", {"consecutive_confirmed_regressions": 2})

    result = record_successful_proposal(store, "run-1")

    assert result["consecutive_confirmed_regressions"] == 0
    assert store.create_or_resume("run-1", {})["consecutive_confirmed_regressions"] == 0


def test_human_handoff_retries_notification_and_records_result(tmp_path) -> None:
    from edd_refinement_workflow.progress_record import ProgressRecordStore

    store = ProgressRecordStore(tmp_path)
    store.create_or_resume("run-1", {"human_handoff_records": []})
    attempts = []
    activity = HumanHandoffActivity(store, notify=lambda summary: attempts.append(summary) or len(attempts) == 2)

    result = activity.run("run-1", "unstable", {"candidate_id": "candidate-1"}, maximum_attempts=2)

    assert result["notified"] is True
    assert result["retry_count"] == 1
    assert store.create_or_resume("run-1", {})["human_handoff_records"] == [result]
