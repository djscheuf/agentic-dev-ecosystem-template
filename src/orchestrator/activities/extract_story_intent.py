"""Cadence Activity wrapping the `extract-story-intent` SDLC skill."""

import asyncio
import dataclasses

from cadence import activity

from ..skill_activity import SkillActivityInput, run_skill


@activity.defn(name="extract_story_intent")
async def extract_story_intent(input_paths: list[str], context: str = "") -> dict:
    output = await asyncio.to_thread(
        run_skill,
        SkillActivityInput(
            skill_name="extract-story-intent", input_paths=input_paths, context=context
        ),
        output_path_key="extracted_intent_path",
    )
    return dataclasses.asdict(output)
