from pathlib import Path

from common.skill_activity import SkillActivity, SkillActivityError, SkillActivityInput


class DraftImplementationPlanSkillActivity(SkillActivity):
    def expected_output_path(self, skill_input: SkillActivityInput) -> Path:
        if not skill_input.input_paths:
            raise SkillActivityError("Cannot derive output path without an input path")
        design_path = Path(skill_input.input_paths[0])
        if design_path.name.endswith(".design.json"):
            return design_path.with_name(
                f"{design_path.name[:-len('.design.json')]}.plan.json"
            )
        return design_path.with_name("plan.json")
