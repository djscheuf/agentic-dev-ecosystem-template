def classify_regression_evidence(original: dict, confirmation: dict, best_state: dict) -> dict:
    best = best_state["metrics"]
    if confirmation.get("status") in {"error", "timeout", "infrastructure_error"}:
        classification = "suspected_flakiness"
    elif confirmation.get("measurement_context") != best.get("measurement_context"):
        classification = "suspected_flakiness"
    elif "passing" not in confirmation:
        classification = "inconclusive"
    elif confirmation["passing"] < best["passing"]:
        classification = "confirmed_regression"
    else:
        classification = "unstable_result"
    return {"classification": classification, "reason": f"confirmation classified as {classification}"}
