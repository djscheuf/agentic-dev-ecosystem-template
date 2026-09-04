"""Cadence Activity wrapping the `grade-story-analysis` SDLC skill.

In addition to running the skill, this Activity reads the analysis-grade JSON
it produced and scores it against the fixed-floor rubric threshold (ADR-006),
so the Workflow's grade-repair loop can make its proceed/repair/escalate
decision from a plain `passed: bool` without needing to know rubric details.
"""

import asyncio
import dataclasses
import json
from pathlib import Path

from cadence import activity

from ..grade_scoring import score_analysis_grade
from ..skill_activity import REPO_ROOT, SkillActivity, SkillActivityError, SkillActivityInput
from .harness_instance import HARNESS


class GradeStoryAnalysisSkillActivity(SkillActivity):
    def expected_output_path(self, skill_input: SkillActivityInput) -> Path:
        if not skill_input.input_paths:
            raise SkillActivityError("Cannot derive output path without an input path")
        path = Path(skill_input.input_paths[0])
        name = path.name
        return path.with_name(
            f"{name[:-len('.analysis.json')]}.analysis-grade.json"
            if name.endswith(".analysis.json")
            else "analysis-grade.json"
        )


GRADE_STORY_ANALYSIS_ACTIVITY = GradeStoryAnalysisSkillActivity(
    config_path=Path(__file__).with_suffix(".config.json"), harness=HARNESS
)


@activity.defn(name="grade_story_analysis")
async def grade_story_analysis(analysis_path: str) -> dict:
    output = await asyncio.to_thread(
        GRADE_STORY_ANALYSIS_ACTIVITY.execute,
        SkillActivityInput(skill_name="grade-story-analysis", input_paths=[analysis_path]),
    )
    grade_document = json.loads((REPO_ROOT / output.output_path).read_text())
    score_pct, passed = score_analysis_grade(grade_document)
    return {**dataclasses.asdict(output), "score": score_pct, "passed": passed}
