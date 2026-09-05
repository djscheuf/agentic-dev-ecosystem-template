import json
from contextlib import nullcontext
from dataclasses import replace
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


def test_build_prompt_applies_hook_after_output_directory_instruction(tmp_path) -> None:
    config_path = tmp_path / "custom.config.json"
    config_path.write_text(json.dumps({
        "activity": {"skill_name": "custom", "output_path_key": "artifact"},
        "harness": {},
    }))

    class FakeHarness:
        def run(self, prompt, *, cwd, config):
            return HarnessResult(0, "", "")

    class CustomActivity(SkillActivity):
        def expected_output_path(self, skill_input: SkillActivityInput) -> Path:
            return Path("artifacts/custom.json")

        def modify_prompt(self, prompt: str) -> str:
            assert "Write the skill's output file in the same directory" in prompt
            return f"{prompt}\nmodified"

    prompt = CustomActivity(
        config_path=config_path, harness=FakeHarness(), repo_root=tmp_path
    ).build_prompt(SkillActivityInput(input_paths=["inputs/story.json"]))

    assert prompt.endswith("following the skill's naming convention.\nmodified")


def test_execute_applies_lifecycle_extension_hooks(tmp_path) -> None:
    config_path = tmp_path / "custom.config.json"
    config_path.write_text(json.dumps({
        "activity": {"skill_name": "custom", "output_path_key": "artifact"},
        "harness": {"original": True},
    }))
    calls = []

    class FakeHarness:
        def run(self, prompt, *, cwd, config):
            calls.append(config)
            (tmp_path / ".process").mkdir(exist_ok=True)
            (tmp_path / ".process" / "changed.done.json").write_text(json.dumps({
                "task": "custom", "verify_params": {"artifact": "raw.json"}
            }))
            return HarnessResult(0, "", "")

    class CustomActivity(SkillActivity):
        def expected_output_path(self, skill_input: SkillActivityInput) -> Path:
            return Path("unused.json")

        def modify_sentinel_path(self, sentinel_path: Path) -> Path:
            return sentinel_path.with_name("changed.done.json")

        def modify_harness_config(self, config):
            return {"changed": True}

        def modify_invocation_context(self, context):
            return nullcontext()

        def modify_output_path(self, output_path: Path) -> Path:
            return output_path.with_name("changed.json")

        def modify_result(self, result):
            return replace(result, status="modified")

    output = CustomActivity(
        config_path=config_path, harness=FakeHarness(), repo_root=tmp_path
    ).execute(SkillActivityInput())

    assert (output.status, output.output_path, calls) == (
        "modified", "changed.json", [{"changed": True}]
    )
