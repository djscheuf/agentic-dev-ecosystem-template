import asyncio
import dataclasses
from pathlib import Path

from cadence import activity

from common.skill_activity import SkillActivity, SkillActivityError, SkillActivityInput
from .harness_instance import HARNESS


class RepairStoryAnalysisSkillActivity(SkillActivity):
    def expected_output_path(self, skill_input: SkillActivityInput) -> Path:
        if not skill_input.input_paths:
            raise SkillActivityError("Cannot derive output path without an input path")
        return Path(skill_input.input_paths[0])


REPAIR_STORY_ANALYSIS_ACTIVITY = RepairStoryAnalysisSkillActivity(
    config_path=Path(__file__).with_suffix(".config.json"), harness=HARNESS
)


@activity.defn(name="repair_story_analysis")
async def repair_story_analysis(analysis_path: str, grade_path: str, notes: str = "") -> dict:
    output = await asyncio.to_thread(
        REPAIR_STORY_ANALYSIS_ACTIVITY.execute,
        SkillActivityInput(
            skill_name="repair-story-analysis",
            input_paths=[analysis_path, grade_path],
            context=notes,
        ),
    )
    return dataclasses.asdict(output)
