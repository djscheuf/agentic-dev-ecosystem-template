import pytest

from edd_refinement_workflow.activities.regression_recovery import (
    classify_regression_evidence,
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
