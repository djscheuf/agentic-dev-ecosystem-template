import pytest
from edd_refinement_workflow.plan_refinement import (
    PlanRefinementActivity,
    PlanningResult,
    plan_refinement_action,
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


def test_plan_refinement_does_not_gate_an_empty_evaluation_diff() -> None:
    activity = PlanRefinementActivity(
        taxonomy=["propose_evaluation_expectation_change"],
        required_test_case_mapping={"propose_evaluation_expectation_change": "tc2"},
    )
    progress_record = {
        "budgets": {"remaining_iterations": 2},
        "consecutive_confirmed_regressions": 0,
    }

    result = activity.plan(
        progress_record,
        {"passing": 5},
        proposed_action="propose_evaluation_expectation_change",
        proposal_id="proposal-1",
        proposed_diff_hash="",
    )

    assert result.requires_approval is False


@pytest.mark.asyncio
async def test_plan_refinement_activity_entrypoint_returns_bound_approval() -> None:
    result = await plan_refinement_action(
        {
            "budgets": {"remaining_iterations": 2},
            "consecutive_confirmed_regressions": 0,
        },
        {"passing": 5},
        "propose_evaluation_expectation_change",
        "proposal-1",
        "abc123",
    )

    assert result["requires_approval"] is True
    assert result["proposal_id"] == "proposal-1"
    assert result["proposed_diff_hash"] == "abc123"


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


def test_plan_refinement_auto_selects_repair_when_tests_fail() -> None:
    activity = PlanRefinementActivity(
        taxonomy=["repair", "add_coverage", "stop"],
        required_test_case_mapping={"repair": "tc1", "add_coverage": "tc1"},
    )
    progress_record = {
        "budgets": {"max_iterations": 3},
        "logical_iteration_count": 0,
        "consecutive_confirmed_regressions": 0,
    }
    baseline = {"passing": 0, "failing": 18, "total": 18}

    result = activity.plan(progress_record, baseline)

    assert result.action == "repair"
    assert result.stop_recommendation is False


def test_plan_refinement_auto_selects_add_coverage_when_passing_but_uncovered() -> None:
    activity = PlanRefinementActivity(
        taxonomy=["repair", "add_coverage", "stop"],
        required_test_case_mapping={"repair": "tc1", "add_coverage": "tc1"},
    )
    progress_record = {
        "budgets": {"max_iterations": 3},
        "logical_iteration_count": 0,
        "consecutive_confirmed_regressions": 0,
    }
    baseline = {
        "passing": 2,
        "failing": 0,
        "total": 2,
        "required_coverage": {"TC-001": 1, "TC-002": 0},
    }

    result = activity.plan(progress_record, baseline)

    assert result.action == "add_coverage"
    assert result.stop_recommendation is False


def test_plan_refinement_stops_when_all_tests_pass() -> None:
    activity = PlanRefinementActivity(
        taxonomy=["add_coverage", "stop"],
        required_test_case_mapping={"add_coverage": "tc1"},
    )
    progress_record = {
        "budgets": {"max_iterations": 3},
        "logical_iteration_count": 0,
        "consecutive_confirmed_regressions": 0,
    }
    baseline = {"passing": 18, "failing": 0, "total": 18}

    result = activity.plan(progress_record, baseline)

    assert result.action == "stop"
    assert result.stop_recommendation is True
    assert "all 18 tests passing" in result.rationale
