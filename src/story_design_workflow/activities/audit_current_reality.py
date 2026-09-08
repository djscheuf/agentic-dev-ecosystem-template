import asyncio
import dataclasses
from pathlib import Path

from cadence import activity

from common.skill_activity import SkillActivity, SkillActivityError, SkillActivityInput
from .harness_instance import HARNESS, REPO_ROOT


class AuditCurrentRealitySkillActivity(SkillActivity):
    def expected_output_path(self, skill_input: SkillActivityInput) -> Path:
        if not skill_input.input_paths:
            raise SkillActivityError("Cannot derive output path without an input path")
        path = Path(skill_input.input_paths[0])
        return path.parent / "current-reality.audit.json"


AUDIT_CURRENT_REALITY_ACTIVITY = AuditCurrentRealitySkillActivity(
    config_path=Path(__file__).with_suffix(".config.json"), harness=HARNESS, repo_root=REPO_ROOT
)


@activity.defn(name="audit_current_reality")
async def audit_current_reality(analysis_path: str) -> dict:
    output = await asyncio.to_thread(
        AUDIT_CURRENT_REALITY_ACTIVITY.execute,
        SkillActivityInput(input_paths=[analysis_path]),
    )
    return dataclasses.asdict(output)
