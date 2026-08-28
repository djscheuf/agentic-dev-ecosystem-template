"""Cadence Activity wrapping the `repair-story-analysis` SDLC skill."""

import asyncio
import dataclasses

from cadence import activity

from ..skill_activity import SkillActivityInput, run_skill


@activity.defn(name="repair_story_analysis")
async def repair_story_analysis(analysis_path: str, grade_path: str, notes: str = "") -> dict:
    output = await asyncio.to_thread(
        run_skill,
        SkillActivityInput(
            skill_name="repair-story-analysis",
            input_paths=[analysis_path, grade_path],
            context=notes,
        ),
        output_path_key="analysis_path",
    )
    return dataclasses.asdict(output)
