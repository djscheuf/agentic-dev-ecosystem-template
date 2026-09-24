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
    usage_metrics: dict | None = None


class EddPlanSkillActivity(SkillActivity):
    def __init__(self, *, input_parent: str | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.input_parent = input_parent

    def expected_output_path(self, skill_input: SkillActivityInput) -> Path:
        if not skill_input.input_paths:
            raise SkillActivityError("Cannot derive output path without a run directory input path")
        return Path(skill_input.input_paths[0]).with_name("plan.json")

    def modify_sentinel_path(self, sentinel_path: Path) -> Path:
        if self.input_parent:
            return Path(self.input_parent) / ".process" / f"{self.skill_name}.done.json"
        return sentinel_path


EDD_PLAN_ACTIVITY = EddPlanSkillActivity(
    config_path=Path(__file__).with_suffix(".config.json"), harness=HARNESS, repo_root=REPO_ROOT
)


class EddPlanRunner:
    """Deterministic budget/regression gate wrapping the agentic `edd-plan` skill.

    Action *selection* (what to do next) is delegated entirely to the `edd-plan`
    skill, which reads the run's refinement context document (`refinement.yaml`)
    plus `progress.json` and writes a structured `plan.json`. This wrapper only
    enforces the iteration/token/regression limits that must stay outside model
    control (ADR-017's 3-strikes regression stop and the run's iteration/token
    budgets).
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
        input_path: str | None = None,
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
        refinement_path = f"{run_dir}/refinement.yaml"
        progress_path = f"{run_dir}/progress.json"
        input_parent = str(Path(input_path).parent) if input_path else None

        check_paths = sorted(
            (Path(repo_root) / run_dir / "iterations").glob("*/check.json"),
            key=lambda p: int(p.parent.name) if p.parent.name.isdigit() else -1,
            reverse=True,
        )[:2]
        recent_checks = [
            str(path.relative_to(repo_root)) for path in check_paths
        ]

        skill_activity = self.skill_activity
        if isinstance(skill_activity, EddPlanSkillActivity) and input_parent:
            skill_activity = EddPlanSkillActivity(
                input_parent=input_parent,
                config_path=Path(__file__).with_suffix(".config.json"),
                harness=HARNESS,
                repo_root=REPO_ROOT,
            )

        output = skill_activity.execute(
            SkillActivityInput(
                input_paths=[refinement_path, progress_path, *recent_checks]
            )
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

        if plan.get("iteration_start_baseline"):
            from ..progress_record import ProgressRecordStore

            store = ProgressRecordStore(repo_root)
            persisted = store.create_or_resume(run_id, {})
            persisted["iteration_start_baseline"] = plan["iteration_start_baseline"]
            store.save(run_id, persisted)

        usage = output.observation.get("usage") or {}
        prompt_tokens = usage.get("prompt_tokens") or 0
        completion_tokens = usage.get("completion_tokens") or 0
        usage_metrics = {
            "input_tokens": prompt_tokens,
            "output_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "cost_usd": usage.get("cost_usd") or 0.0,
        }

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
            usage_metrics=usage_metrics,
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
    input_path: str | None = None,
) -> dict:
    result = await asyncio.to_thread(
        EDD_PLAN_RUNNER.run,
        run_id,
        repo_root,
        progress_record,
        baseline,
        proposal_id,
        proposed_diff_hash,
        input_path,
    )
    return dataclasses.asdict(result)
