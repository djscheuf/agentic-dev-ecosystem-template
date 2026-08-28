"""Cadence Activity wrapping the `analyze-story` SDLC skill."""

import asyncio
import dataclasses

from cadence import activity

from ..skill_activity import SkillActivityInput, run_skill


@activity.defn(name="analyze_story")
async def analyze_story(intent_path: str) -> dict:
    output = await asyncio.to_thread(
        run_skill,
        SkillActivityInput(skill_name="analyze-story", input_paths=[intent_path]),
        output_path_key="analysis_path",
    )
    return dataclasses.asdict(output)
