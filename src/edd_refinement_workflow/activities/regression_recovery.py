from collections.abc import Callable


class RevertRepositoryToBestActivity:
    def __init__(self, lease_held: Callable[[str, str], bool], reset: Callable[[str, str], None], is_clean: Callable[[str], bool]) -> None:
        self.lease_held = lease_held
        self.reset = reset
        self.is_clean = is_clean

    def run(self, run_id: str, repo_root: str, best_state: dict) -> dict:
        if not self.lease_held(repo_root, run_id):
            raise RuntimeError("mutation lease is not held")
        commit = best_state["commit"]
        self.reset(repo_root, commit)
        clean = self.is_clean(repo_root)
        if not clean:
            raise RuntimeError("repository is not clean after restore")
        return {"restored_commit": commit, "repo_clean": clean}


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


def verify_recovery_metrics(recovery: dict, best: dict) -> dict:
    fields = ["passing", "failing", "total", "required_coverage", "percentage"]
    mismatched = [field for field in fields if (abs(recovery.get(field, 0) - best.get(field, 0)) > 1e-6 if field == "percentage" else recovery.get(field) != best.get(field))]
    matched = [field for field in fields if field not in mismatched]
    recovered = not mismatched
    return {"recovered": recovered, "matched_fields": matched, "mismatched_fields": mismatched, "reason": "recovery metrics match" if recovered else "recovery metrics differ"}
