import pytest

from edd_refinement_workflow.activities.check_refinement_limits import check_refinement_limits


@pytest.mark.parametrize(
    ("record", "next_step_estimate", "reason"),
    [
        ({"budgets": {"max_iterations": 2}, "logical_iteration_count": 2}, 0, "iteration_budget"),
        ({"budgets": {"token_budget": 100}, "cumulative_token_usage": 100}, 0, "token_budget"),
        ({"budgets": {"hard_token_limit": 110}, "cumulative_token_usage": 100}, 11, "hard_limit"),
        ({"budgets": {"regression_stop_threshold": 3}, "consecutive_confirmed_regressions": 3}, 0, "regression_threshold"),
    ],
)
def test_check_refinement_limits_at_configured_boundary_blocks_with_reason(record, next_step_estimate, reason) -> None:
    record["best_accepted_state"] = {"commit": "best-1"}

    result = check_refinement_limits(record, next_step_estimate)

    assert result == {
        "schedule_next_step": False,
        "stop_reason": reason,
        "best_accepted_state": {"commit": "best-1"},
    }
