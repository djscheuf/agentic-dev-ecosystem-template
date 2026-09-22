import dataclasses
import logging


def _get_activity_logger() -> logging.Logger:
    try:
        from common.workflow_logger import get_activity_logger

        return get_activity_logger()
    except Exception:  # pragma: no cover - logging setup may not be present
        return logging.getLogger(__name__)


@dataclasses.dataclass
class PlanningResult:
    action: str
    rationale: str = ""
    evidence: dict | None = None
    intended_files: list | None = None
    expected_effect: str = ""
    requires_approval: bool = False
    stop_recommendation: bool = False
    taxonomy_version: int = 1
    proposal_id: str | None = None
    proposed_diff_hash: str | None = None


class PlanRefinementActivity:
    def __init__(
        self,
        taxonomy: list[str],
        required_test_case_mapping: dict,
        taxonomy_version: int = 1,
    ) -> None:
        self.taxonomy = set(taxonomy)
        self.required_test_case_mapping = required_test_case_mapping
        self.taxonomy_version = taxonomy_version

    def _remaining_iterations(self, budgets: dict, progress_record: dict) -> int | None:
        remaining = budgets.get("remaining_iterations")
        if remaining is not None:
            return remaining
        if "max_iterations" in budgets:
            return budgets["max_iterations"] - progress_record.get(
                "logical_iteration_count", 0
            )
        return None

    def _budget_exhausted(self, progress_record: dict) -> tuple[bool, str]:
        budgets = progress_record.get("budgets", {})
        consecutive_regressions = progress_record.get(
            "consecutive_confirmed_regressions", 0
        )
        if consecutive_regressions >= 3:
            return True, f"regression limit reached ({consecutive_regressions} consecutive)"
        remaining = self._remaining_iterations(budgets, progress_record)
        if remaining is not None and remaining <= 0:
            return True, f"iteration budget exhausted ({remaining} remaining)"
        return False, ""

    def _requires_approval(self, action: str, proposed_diff_hash: str | None) -> bool:
        return action == "propose_evaluation_expectation_change" and bool(
            proposed_diff_hash
        )

    def _is_authorized(self, action: str) -> bool:
        return (
            action in self.taxonomy
            and action in self.required_test_case_mapping
            and action == action.strip().lower()
        )

    def _select_action(
        self, progress_record: dict, baseline: dict
    ) -> tuple[str | None, str]:
        """Choose the next refinement action when none was supplied externally."""
        required_coverage = baseline.get("required_coverage", {})
        failing = baseline.get("failing", 0)
        passing = baseline.get("passing", 0)
        total = baseline.get("total", 0)

        if total == 0:
            return None, "baseline reported no test cases; nothing to refine"

        uncovered = [tc for tc, covered in required_coverage.items() if not covered]
        if uncovered or failing > 0:
            if "add_coverage" in self.taxonomy and "add_coverage" in self.required_test_case_mapping:
                return "add_coverage", f"selected add_coverage (failing={failing}, uncovered={len(uncovered)})"
            return None, "tests are failing but no automatic action is authorized"

        if passing == total:
            return None, f"all {total} tests passing; no refinement needed"

        return None, "no automatic action matches the current baseline state"

    def plan(
        self,
        progress_record: dict,
        baseline: dict,
        proposed_action: str | None = None,
        proposal_id: str | None = None,
        proposed_diff_hash: str | None = None,
    ) -> PlanningResult:
        logger = _get_activity_logger()
        budgets = progress_record.get("budgets", {})
        logical_iterations = progress_record.get("logical_iteration_count", 0)
        consecutive_regressions = progress_record.get(
            "consecutive_confirmed_regressions", 0
        )
        logger.info(
            "planning iteration=%s max_iterations=%s regressions=%s proposed_action=%s",
            logical_iterations,
            budgets.get("max_iterations"),
            consecutive_regressions,
            proposed_action,
        )

        exhausted, reason = self._budget_exhausted(progress_record)
        if exhausted:
            logger.warning("planning stopped: %s", reason)
            remaining_iterations = self._remaining_iterations(budgets, progress_record)
            return PlanningResult(
                action="stop",
                rationale=(
                    f"budget or regression limit exhausted: {reason}; "
                    f"logical_iterations={logical_iterations}, "
                    f"remaining_iterations={remaining_iterations}, "
                    f"consecutive_confirmed_regressions={consecutive_regressions}, "
                    f"budgets={budgets}"
                ),
                stop_recommendation=True,
                taxonomy_version=self.taxonomy_version,
            )

        if proposed_action is None:
            selected_action, selection_rationale = self._select_action(
                progress_record, baseline
            )
            if selected_action is None:
                logger.warning("planning stopped: %s", selection_rationale)
                available = sorted(self.taxonomy & set(self.required_test_case_mapping))
                return PlanningResult(
                    action="stop",
                    rationale=(
                        f"no action proposed and no automatic action selected: {selection_rationale}; "
                        f"available actions are {available}"
                    ),
                    stop_recommendation=True,
                    taxonomy_version=self.taxonomy_version,
                )
            proposed_action = selected_action
            logger.info(
                "planning auto-selected action=%s because %s", proposed_action, selection_rationale
            )

        if not self._is_authorized(proposed_action):
            logger.warning("planning stopped: unauthorized action=%s", proposed_action)
            available = sorted(self.taxonomy & set(self.required_test_case_mapping))
            return PlanningResult(
                action="stop",
                rationale=(
                    f"proposed action {proposed_action!r} is not authorized "
                    f"(available: {available}, required mapping: {self.required_test_case_mapping})"
                ),
                stop_recommendation=True,
                taxonomy_version=self.taxonomy_version,
            )

        logger.info("planning selected action=%s", proposed_action)
        return PlanningResult(
            action=proposed_action,
            rationale=f"selected authorized action {proposed_action}",
            requires_approval=self._requires_approval(
                proposed_action, proposed_diff_hash
            ),
            stop_recommendation=False,
            taxonomy_version=self.taxonomy_version,
            proposal_id=proposal_id,
            proposed_diff_hash=proposed_diff_hash,
        )


from cadence import activity


@activity.defn(name="plan_refinement_action")
async def plan_refinement_action(
    progress_record: dict,
    baseline: dict,
    proposed_action: str | None = None,
    proposal_id: str | None = None,
    proposed_diff_hash: str | None = None,
) -> dict:
    mapping = {
        "add_coverage": "required_test_case",
        "propose_evaluation_expectation_change": "required_test_case",
    }
    result = PlanRefinementActivity(
        taxonomy=[*mapping, "stop"],
        required_test_case_mapping=mapping,
    ).plan(
        progress_record,
        baseline,
        proposed_action,
        proposal_id,
        proposed_diff_hash,
    )
    return dataclasses.asdict(result)
