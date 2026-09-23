from edd_refinement_workflow.quality_ratchet import (
    compare_candidate_to_best,
    resolve_comparison_baseline,
)


def metric(passing, total, coverage, context="baseline"):
    return {
        "passing": passing,
        "total": total,
        "percentage": passing / total * 100,
        "required_coverage": coverage,
        "measurement_context": context,
    }


def test_compare_candidate_to_best_with_passing_increase_accepts_candidate() -> None:
    best = metric(5, 6, {"required-1": 1})
    candidate = metric(6, 7, {"required-1": 1})

    result = compare_candidate_to_best(candidate, best)

    assert result == {
        "decision": "accept",
        "reason": "passing_count_increased",
        "passing_delta": 1,
        "coverage_delta": {},
    }


def test_compare_candidate_to_best_with_new_required_coverage_accepts_candidate() -> None:
    best = metric(5, 6, {"required-1": 1, "required-2": 0})
    candidate = metric(5, 7, {"required-1": 1, "required-2": 1})

    result = compare_candidate_to_best(candidate, best)

    assert result == {
        "decision": "accept",
        "reason": "required_coverage_added",
        "passing_delta": 0,
        "coverage_delta": {"required-2": 1},
    }


def test_compare_candidate_to_best_with_coverage_loss_rejects_candidate() -> None:
    best = metric(5, 6, {"required-1": 1, "required-2": 1})
    candidate = metric(6, 7, {"required-1": 1, "required-2": 0})

    result = compare_candidate_to_best(candidate, best)

    assert result == {
        "decision": "reject",
        "reason": "required_coverage_reduced",
        "passing_delta": 1,
        "coverage_delta": {"required-2": -1},
    }


def test_compare_candidate_to_best_with_degradation_requests_rerun() -> None:
    best = metric(5, 6, {"required-1": 1})
    candidate = metric(4, 6, {"required-1": 1})

    result = compare_candidate_to_best(candidate, best)

    assert result == {
        "decision": "rerun",
        "reason": "apparent_regression",
        "passing_delta": -1,
        "coverage_delta": {},
    }


def test_compare_candidate_to_best_with_different_measurement_context_escalates() -> None:
    best = metric(5, 6, {"required-1": 1})
    candidate = metric(6, 7, {"required-1": 1}, "human-approved-change-1")

    result = compare_candidate_to_best(candidate, best)

    assert result == {
        "decision": "escalate",
        "reason": "measurement_context_changed",
        "passing_delta": 1,
        "coverage_delta": {},
    }


def test_compare_candidate_to_best_with_no_qualifying_value_rejects_candidate() -> None:
    best = metric(5, 6, {"required-1": 1})
    candidate = metric(5, 7, {"required-1": 1})

    result = compare_candidate_to_best(candidate, best)

    assert result == {
        "decision": "reject",
        "reason": "no_qualifying_value",
        "passing_delta": 0,
        "coverage_delta": {},
    }


def test_resolve_comparison_baseline_prefers_iteration_start_baseline_over_best_state() -> None:
    planning = {
        "iteration_start_baseline": {
            "source": "best_accepted_state",
            "candidate_id": "candidate-2",
            "passing": 9,
            "failing": 3,
            "total": 12,
        }
    }
    best_state = {"metrics": {"passing": 20, "failing": 0, "total": 20}}

    result = resolve_comparison_baseline(planning, best_state, {"passing": 0})

    assert result == planning["iteration_start_baseline"]


def test_resolve_comparison_baseline_falls_back_to_best_accepted_state() -> None:
    best_state = {"metrics": {"passing": 5, "total": 6}}

    result = resolve_comparison_baseline({"action": "repair"}, best_state, {"passing": 0})

    assert result == best_state["metrics"]


def test_resolve_comparison_baseline_falls_back_to_original_baseline_when_never_accepted() -> None:
    baseline = {"passing": 5, "total": 6}

    result = resolve_comparison_baseline(None, None, baseline)

    assert result == baseline
