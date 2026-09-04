import json
from pathlib import Path

from common.harness import HarnessResult
from common.skill_activity import SkillActivity, SkillActivityInput


def test_missing_sentinel_uses_concrete_output_resolver(tmp_path) -> None:
    config_path = tmp_path / "custom.config.json"
    config_path.write_text(json.dumps({
        "activity": {"skill_name": "custom", "output_path_key": "artifact"},
        "harness": {"fake": {"mode": "safe"}},
    }))
    calls = []

    class FakeHarness:
        def run(self, prompt, *, cwd, config):
            calls.append(config)
            return HarnessResult(0, "", "")

    class CustomActivity(SkillActivity):
        def expected_output_path(self, skill_input: SkillActivityInput) -> Path:
            return Path("artifacts/custom.json")

    output = CustomActivity(
        config_path=config_path, harness=FakeHarness(), repo_root=tmp_path
    ).execute(SkillActivityInput(input_paths=["input.txt"]))

    assert output.output_path == "artifacts/custom.json"
    assert calls == [{"fake": {"mode": "safe"}}]
