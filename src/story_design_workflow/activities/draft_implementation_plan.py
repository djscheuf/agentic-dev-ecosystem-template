import asyncio
import dataclasses
from pathlib import Path

from cadence import activity

from common.skill_activity import SkillActivity, SkillActivityError, SkillActivityInput
from .harness_instance import HARNESS, REPO_ROOT


class DraftImplementationPlanSkillActivity(SkillActivity):
    def expected_output_path(self, skill_input: SkillActivityInput) -> Path:
        if not skill_input.input_paths:
            raise SkillActivityError("Cannot derive output path without an input path")
        design_path = Path(skill_input.input_paths[0])
        if design_path.name.endswith(".design.json"):
            return design_path.with_name(
                f"{design_path.name[:-len('.design.json')]}.plan.json"
            )
        return design_path.with_name("plan.json")


DRAFT_IMPLEMENTATION_PLAN_ACTIVITY = DraftImplementationPlanSkillActivity(
    config_path=Path(__file__).with_suffix(".config.json"), harness=HARNESS, repo_root=REPO_ROOT
)


@activity.defn(name="draft_implementation_plan")
async def draft_implementation_plan(design_path: str) -> dict:
    output = await asyncio.to_thread(
        DRAFT_IMPLEMENTATION_PLAN_ACTIVITY.execute,
        SkillActivityInput(
            input_paths=[design_path],
            context="Draft an implementation plan from the approved design document.",
        ),
    )
    return dataclasses.asdict(output)
