from pathlib import Path

import pytest

from common.skill_activity import SkillActivityInput
from story_design_workflow.activities.draft_implementation_plan import (
    DraftImplementationPlanSkillActivity,
)


@pytest.fixture
def activity(tmp_path):
    config_path = tmp_path / "draft_implementation_plan.config.json"
    config_path.write_text(
        '{"activity": {"skill_name": "draft-implementation-plan", "output_path_key": "plan_path"}, "harness": {}}'
    )
    return DraftImplementationPlanSkillActivity(
        config_path=config_path,
        harness=None,
        repo_root=Path("/tmp"),
    )


def test_expected_output_path_derives_plan_from_design(activity):
    skill_input = SkillActivityInput(input_paths=["docs/foo.design.json"])
    assert activity.expected_output_path(skill_input) == Path("docs/foo.plan.json")
