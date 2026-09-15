import pytest

from edd_refinement_workflow.activities.regression_recovery import classify_regression_evidence


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
