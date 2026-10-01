def resolve_comparison_baseline(
    planning: dict | None, best_state: dict | None, baseline: dict
) -> dict:
    """Return the metrics snapshot Check/Regression-Confirm should compare against.

    Prefers the `iteration_start_baseline` that `edd-plan` froze at Plan time
    (`planning["iteration_start_baseline"]`) over the possibly-since-advanced
    `best_accepted_state`, so a candidate is always judged against the target
    the plan believed it was improving on -- not a `best_accepted_state` that
    raced ahead mid-iteration. Falls back to today's behavior
    (`best_state["metrics"]`, or the original `baseline` before any candidate
    has ever been accepted) when Plan did not record one, e.g. mocked/legacy
    callers that predate ADR-017's iteration-start-baseline requirement.
    """
    iteration_start_baseline = (planning or {}).get("iteration_start_baseline")
    if iteration_start_baseline:
        return iteration_start_baseline
    return best_state["metrics"] if best_state is not None else baseline


def compare_candidate_to_best(candidate: dict, best: dict) -> dict:
    candidate_passing = candidate.get("passing", 0)
    best_passing = best.get("passing", 0)
    passing_delta = candidate_passing - best_passing
    best_coverage = best.get("required_coverage", {})
    candidate_coverage = candidate.get("required_coverage", {})
    coverage_delta = {
        case: count - best_coverage.get(case, 0)
        for case, count in candidate_coverage.items()
        if count != best_coverage.get(case, 0)
    }
    if candidate.get("measurement_context", "baseline") != best.get(
        "measurement_context", "baseline"
    ):
        return {
            "decision": "escalate",
            "reason": "measurement_context_changed",
            "passing_delta": passing_delta,
            "coverage_delta": coverage_delta,
        }
    if any(delta < 0 for delta in coverage_delta.values()):
        return {
            "decision": "reject",
            "reason": "required_coverage_reduced",
            "passing_delta": passing_delta,
            "coverage_delta": coverage_delta,
        }
    if passing_delta > 0:
        return {
            "decision": "accept",
            "reason": "passing_count_increased",
            "passing_delta": passing_delta,
            "coverage_delta": coverage_delta,
        }
    if passing_delta == 0 and any(delta > 0 for delta in coverage_delta.values()):
        return {
            "decision": "accept",
            "reason": "required_coverage_added",
            "passing_delta": passing_delta,
            "coverage_delta": coverage_delta,
        }
    if passing_delta < 0:
        return {
            "decision": "rerun",
            "reason": "apparent_regression",
            "passing_delta": passing_delta,
            "coverage_delta": coverage_delta,
        }
    return {
        "decision": "reject",
        "reason": "no_qualifying_value",
        "passing_delta": passing_delta,
        "coverage_delta": coverage_delta,
    }
