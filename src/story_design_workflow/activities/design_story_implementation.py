import asyncio
import dataclasses
from pathlib import Path

from cadence import activity

from common.skill_activity import SkillActivity, SkillActivityError, SkillActivityInput
from .harness_instance import HARNESS, REPO_ROOT


class DesignStoryImplementationSkillActivity(SkillActivity):
    def expected_output_path(self, skill_input: SkillActivityInput) -> Path:
        if not skill_input.input_paths:
            raise SkillActivityError("Cannot derive output path without an input path")
        analysis_path = Path(skill_input.input_paths[0])
        if analysis_path.name.endswith(".analysis.json"):
            return analysis_path.with_name(
                f"{analysis_path.name[:-len('.analysis.json')]}.design.json"
            )
        return analysis_path.with_name("design.json")


DESIGN_STORY_IMPLEMENTATION_ACTIVITY = DesignStoryImplementationSkillActivity(
    config_path=Path(__file__).with_suffix(".config.json"), harness=HARNESS, repo_root=REPO_ROOT
)


@activity.defn(name="design_story_implementation")
async def design_story_implementation(analysis_path: str, audit_path: str) -> dict:
    output = await asyncio.to_thread(
        DESIGN_STORY_IMPLEMENTATION_ACTIVITY.execute,
        SkillActivityInput(
            input_paths=[analysis_path, audit_path],
            context="Design the implementation using the story analysis and the current-reality audit.",
        ),
    )
    return dataclasses.asdict(output)
