import json

import pytest

from common.skill_activity_config import SkillActivityConfig


def test_loads_and_deeply_freezes_colocated_configuration(tmp_path) -> None:
    path = tmp_path / "review.config.json"
    path.write_text(json.dumps({
        "activity": {"skill_name": "review", "output_path_key": "report_path"},
        "harness": {"devin": {"model": "model-a"}},
    }))

    config = SkillActivityConfig.load(path)

    assert config.skill_name == "review"
    assert config.output_path_key == "report_path"
    with pytest.raises(TypeError):
        config.harness["devin"]["model"] = "model-b"  # type: ignore[index]
