from cadence import activity


def check_refinement_limits(progress_record: dict, next_step_estimate: int = 0) -> dict:
    budgets = progress_record.get("budgets", {})
    checks = (
        (
            "iteration_budget",
            "max_iterations" in budgets
            and progress_record.get("logical_iteration_count", 0) >= budgets["max_iterations"],
        ),
        (
            "token_budget",
            "token_budget" in budgets
            and progress_record.get("cumulative_token_usage", 0) >= budgets["token_budget"],
        ),
        (
            "hard_limit",
            "hard_token_limit" in budgets
            and progress_record.get("cumulative_token_usage", 0) + next_step_estimate
            > budgets["hard_token_limit"],
        ),
        (
            "regression_threshold",
            "regression_stop_threshold" in budgets
            and progress_record.get("consecutive_confirmed_regressions", 0)
            >= budgets["regression_stop_threshold"],
        ),
    )
    stop_reason = next((reason for reason, reached in checks if reached), "none")
    return {
        "schedule_next_step": stop_reason == "none",
        "stop_reason": stop_reason,
        "best_accepted_state": progress_record.get("best_accepted_state"),
    }


@activity.defn(name="check_refinement_limits")
async def check_refinement_limits_activity(progress_record: dict, next_step_estimate: int = 0) -> dict:
    return check_refinement_limits(progress_record, next_step_estimate)
