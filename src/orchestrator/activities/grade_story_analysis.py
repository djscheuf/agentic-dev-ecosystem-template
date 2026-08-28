"""Cadence Activity wrapping the `grade-story-analysis` SDLC skill.

In addition to running the skill, this Activity reads the analysis-grade JSON
it produced and scores it against the fixed-floor rubric threshold (ADR-006),
so the Workflow's grade-repair loop can make its proceed/repair/escalate
decision from a plain `passed: bool` without needing to know rubric details.
"""

import asyncio
import dataclasses
import json

from cadence import activity

from ..grade_scoring import score_analysis_grade
from ..skill_activity import REPO_ROOT, SkillActivityInput, run_skill
from .harness_instance import HARNESS


@activity.defn(name="grade_story_analysis")
async def grade_story_analysis(analysis_path: str) -> dict:
    output = await asyncio.to_thread(
        run_skill,
        SkillActivityInput(skill_name="grade-story-analysis", input_paths=[analysis_path]),
        output_path_key="analysis_grade_path",
        harness=HARNESS,
    )
    grade_document = json.loads((REPO_ROOT / output.output_path).read_text())
    score_pct, passed = score_analysis_grade(grade_document)
    return {**dataclasses.asdict(output), "score": score_pct, "passed": passed}
