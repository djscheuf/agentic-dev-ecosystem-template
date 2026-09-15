from edd_refinement_workflow.quality_ratchet import compare_candidate_to_best


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
