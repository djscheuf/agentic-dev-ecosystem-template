from edd_refinement_workflow.plan_refinement import (
    PlanRefinementActivity,
    PlanningResult,
)


def test_plan_refinement_selects_stop_when_budgets_exhausted() -> None:
    activity = PlanRefinementActivity(
        taxonomy=["add_coverage", "stop"],
        required_test_case_mapping={"add_coverage": "tc1"},
    )
    progress_record = {
        "budgets": {"remaining_iterations": 0, "cumulative_tokens": 100},
        "consecutive_confirmed_regressions": 0,
    }
    baseline = {"passing": 5}

    result = activity.plan(progress_record, baseline)

    assert isinstance(result, PlanningResult)
    assert result.action == "stop"
    assert result.stop_recommendation is True
