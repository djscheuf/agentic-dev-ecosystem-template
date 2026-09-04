import asyncio
import dataclasses
from pathlib import Path

from cadence import activity

from common.skill_activity import SkillActivity, SkillActivityError, SkillActivityInput
from .harness_instance import HARNESS, REPO_ROOT


class ExtractStoryIntentSkillActivity(SkillActivity):
    def expected_output_path(self, skill_input: SkillActivityInput) -> Path:
        if not skill_input.input_paths:
            raise SkillActivityError("Cannot derive output path without an input path")
        path = Path(skill_input.input_paths[0])
        return path.with_name(f"{path.stem}.intent.json")


EXTRACT_STORY_INTENT_ACTIVITY = ExtractStoryIntentSkillActivity(
    config_path=Path(__file__).with_suffix(".config.json"), harness=HARNESS, repo_root=REPO_ROOT
)


@activity.defn(name="extract_story_intent")
async def extract_story_intent(input_paths: list[str], context: str = "") -> dict:
    output = await asyncio.to_thread(
        EXTRACT_STORY_INTENT_ACTIVITY.execute,
        SkillActivityInput(
            skill_name="extract-story-intent", input_paths=input_paths, context=context
        ),
    )
    return dataclasses.asdict(output)
