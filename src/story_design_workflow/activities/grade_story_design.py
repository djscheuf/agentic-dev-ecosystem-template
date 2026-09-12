import asyncio
import dataclasses
import json
from pathlib import Path

from cadence import activity

from common.skill_activity import SkillActivity, SkillActivityError, SkillActivityInput
from ..design_scoring import score_design_grade
from .harness_instance import HARNESS, REPO_ROOT


class GradeStoryDesignSkillActivity(SkillActivity):
    def expected_output_path(self, skill_input: SkillActivityInput) -> Path:
        if not skill_input.input_paths:
            raise SkillActivityError("Cannot derive output path without an input path")
        path = Path(skill_input.input_paths[0])
        if path.name.endswith(".design.json"):
            return path.with_name(f"{path.name[:-len('.design.json')]}.design-grade.json")
        return path.with_name("design-grade.json")


GRADE_STORY_DESIGN_ACTIVITY = GradeStoryDesignSkillActivity(
    config_path=Path(__file__).with_suffix(".config.json"), harness=HARNESS, repo_root=REPO_ROOT
)


@activity.defn(name="grade_story_design")
async def grade_story_design(design_path: str) -> dict:
    output = await asyncio.to_thread(
        GRADE_STORY_DESIGN_ACTIVITY.execute,
        SkillActivityInput(input_paths=[design_path]),
    )
    grade_document = json.loads((REPO_ROOT / output.output_path).read_text())
    score_pct, passed = score_design_grade(grade_document)
    return {**dataclasses.asdict(output), "score": score_pct, "passed": passed}
