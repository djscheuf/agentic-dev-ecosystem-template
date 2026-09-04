import asyncio
import dataclasses
from pathlib import Path

from cadence import activity

from common.skill_activity import SkillActivity, SkillActivityError, SkillActivityInput
from .harness_instance import HARNESS


class AnalyzeStorySkillActivity(SkillActivity):
    def expected_output_path(self, skill_input: SkillActivityInput) -> Path:
        if not skill_input.input_paths:
            raise SkillActivityError("Cannot derive output path without an input path")
        path = Path(skill_input.input_paths[0])
        name = path.name
        return path.with_name(
            f"{name[:-len('.intent.json')]}.analysis.json"
            if name.endswith(".intent.json")
            else "analysis.json"
        )


ANALYZE_STORY_ACTIVITY = AnalyzeStorySkillActivity(
    config_path=Path(__file__).with_suffix(".config.json"), harness=HARNESS
)


@activity.defn(name="analyze_story")
async def analyze_story(intent_path: str) -> dict:
    output = await asyncio.to_thread(
        ANALYZE_STORY_ACTIVITY.execute,
        SkillActivityInput(skill_name="analyze-story", input_paths=[intent_path]),
    )
    return dataclasses.asdict(output)
