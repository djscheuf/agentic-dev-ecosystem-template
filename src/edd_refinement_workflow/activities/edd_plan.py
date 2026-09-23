import asyncio
import dataclasses
import json
import logging
from pathlib import Path

from cadence import activity

from common.skill_activity import SkillActivity, SkillActivityError, SkillActivityInput

from .harness_instance import HARNESS, REPO_ROOT


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
    iteration_number: int | None = None
    iteration_start_baseline: dict | None = None
    plan_path: str = ""


class EddPlanSkillActivity(SkillActivity):
    def expected_output_path(self, skill_input: SkillActivityInput) -> Path:
        if not skill_input.input_paths:
            raise SkillActivityError("Cannot derive output path without a run directory input path")
        return Path(skill_input.input_paths[0]).with_name("plan.json")


EDD_PLAN_ACTIVITY = EddPlanSkillActivity(
    config_path=Path(__file__).with_suffix(".config.json"), harness=HARNESS, repo_root=REPO_ROOT
)


class EddPlanRunner:
    """Deterministic budget/regression gate wrapping the agentic `edd-plan` skill.

    Action *selection* (what to do next) is delegated entirely to the `edd-plan`
    skill, which reads the run's guide document / refinement history / latest
    check results and writes a structured `plan.json`. This wrapper only enforces
    the iteration/token/regression limits that must stay outside model control
    (ADR-017's 3-strikes regression stop and the run's iteration/token budgets).
    """

    def __init__(self, skill_activity: SkillActivity | None = None) -> None:
        self.skill_activity = skill_activity or EDD_PLAN_ACTIVITY

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

    def run(
        self,
        run_id: str,
        repo_root: str,
        progress_record: dict,
        baseline: dict,
        proposal_id: str | None = None,
        proposed_diff_hash: str | None = None,
    ) -> PlanningResult:
        logger = _get_activity_logger()
        logical_iterations = progress_record.get("logical_iteration_count", 0)
        consecutive_regressions = progress_record.get(
            "consecutive_confirmed_regressions", 0
        )
        logger.info(
            "planning run_id=%s iteration=%s regressions=%s",
            run_id,
            logical_iterations,
            consecutive_regressions,
        )

        exhausted, reason = self._budget_exhausted(progress_record)
        if exhausted:
            logger.warning("planning stopped: %s", reason)
            return PlanningResult(
                action="stop",
                rationale=(
                    f"budget or regression limit exhausted: {reason}; "
                    f"logical_iterations={logical_iterations}, "
                    f"consecutive_confirmed_regressions={consecutive_regressions}"
                ),
                stop_recommendation=True,
            )

        run_dir = f".process/edd/{run_id}"
        output = self.skill_activity.execute(
            SkillActivityInput(input_paths=[f"{run_dir}/progress.json"])
        )
        if output.status == "ambiguity":
            raise SkillActivityError(f"edd-plan reported ambiguity: {output.ambiguity_reason}")

        plan_path = Path(repo_root) / output.output_path
        try:
            plan = json.loads(plan_path.read_text())
        except FileNotFoundError as exc:
            raise SkillActivityError(f"edd-plan did not write {output.output_path}") from exc
        except json.JSONDecodeError as exc:
            raise SkillActivityError(f"edd-plan wrote malformed JSON to {output.output_path}") from exc

        action = plan.get("action", "stop")
        requires_approval = (
            action == "propose_evaluation_expectation_change" and bool(proposed_diff_hash)
        )
        logger.info("planning selected action=%s (run_id=%s)", action, run_id)
        return PlanningResult(
            action=action,
            rationale=plan.get("rationale", ""),
            evidence=plan.get("evidence"),
            intended_files=plan.get("intended_files"),
            expected_effect=plan.get("expected_effect", ""),
            requires_approval=requires_approval,
            stop_recommendation=plan.get("stop_recommendation", action == "stop"),
            taxonomy_version=plan.get("taxonomy_version", 1),
            proposal_id=proposal_id,
            proposed_diff_hash=proposed_diff_hash if requires_approval else None,
            iteration_number=plan.get("iteration_number"),
            iteration_start_baseline=plan.get("iteration_start_baseline"),
            plan_path=output.output_path,
        )


EDD_PLAN_RUNNER = EddPlanRunner()


@activity.defn(name="edd_plan")
async def edd_plan_action(
    run_id: str,
    repo_root: str,
    progress_record: dict,
    baseline: dict,
    proposal_id: str | None = None,
    proposed_diff_hash: str | None = None,
) -> dict:
    result = await asyncio.to_thread(
        EDD_PLAN_RUNNER.run,
        run_id,
        repo_root,
        progress_record,
        baseline,
        proposal_id,
        proposed_diff_hash,
    )
    return dataclasses.asdict(result)
