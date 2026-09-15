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


def test_plan_refinement_selects_authorized_action_and_sets_approval() -> None:
    activity = PlanRefinementActivity(
        taxonomy=["add_coverage", "propose_evaluation_expectation_change", "stop"],
        required_test_case_mapping={
            "add_coverage": "tc1",
            "propose_evaluation_expectation_change": "tc2",
        },
    )
    progress_record = {
        "budgets": {"remaining_iterations": 2},
        "consecutive_confirmed_regressions": 0,
    }
    baseline = {"passing": 5}

    result = activity.plan(
        progress_record,
        baseline,
        proposed_action="propose_evaluation_expectation_change",
        proposal_id="proposal-1",
        proposed_diff_hash="abc123",
    )

    assert result.action == "propose_evaluation_expectation_change"
    assert result.requires_approval is True
    assert result.proposal_id == "proposal-1"
    assert result.proposed_diff_hash == "abc123"
    assert result.stop_recommendation is False


def test_plan_refinement_rejects_unauthorized_or_unmapped_action() -> None:
    activity = PlanRefinementActivity(
        taxonomy=["add_coverage"],
        required_test_case_mapping={"add_coverage": "tc1"},
    )
    progress_record = {
        "budgets": {"remaining_iterations": 2},
        "consecutive_confirmed_regressions": 0,
    }
    baseline = {"passing": 5}

    result = activity.plan(
        progress_record,
        baseline,
        proposed_action="unknown_action",
    )

    assert result.action == "stop"
    assert result.stop_recommendation is True
