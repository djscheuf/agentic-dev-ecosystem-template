def compare_candidate_to_best(candidate: dict, best: dict) -> dict:
    passing_delta = candidate["passing"] - best["passing"]
    coverage_delta = {
        case: count - best["required_coverage"].get(case, 0)
        for case, count in candidate["required_coverage"].items()
        if count != best["required_coverage"].get(case, 0)
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
    raise NotImplementedError
