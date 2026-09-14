import dataclasses


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

    def _budget_exhausted(self, progress_record: dict) -> bool:
        budgets = progress_record.get("budgets", {})
        return (
            budgets.get("remaining_iterations", 0) <= 0
            or progress_record.get("consecutive_confirmed_regressions", 0) >= 3
        )

    def plan(self, progress_record: dict, baseline: dict) -> PlanningResult:
        if self._budget_exhausted(progress_record):
            return PlanningResult(
                action="stop",
                rationale="budget or regression limit exhausted",
                stop_recommendation=True,
                taxonomy_version=self.taxonomy_version,
            )
        return PlanningResult(
            action="stop",
            rationale="no further action selected in this cycle",
            stop_recommendation=True,
            taxonomy_version=self.taxonomy_version,
        )
