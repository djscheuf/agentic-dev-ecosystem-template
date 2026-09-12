import json
from contextlib import nullcontext
from dataclasses import replace
from pathlib import Path

from types import SimpleNamespace

import pytest

from common.harness import HarnessResult, HarnessUsage
from common.skill_activity import SkillActivity, SkillActivityError, SkillActivityInput
from common.workflow_logger import WorkflowLoggerConfig


def test_sentinel_path_with_relative_input_uses_first_input_parent(tmp_path) -> None:
    config_path = tmp_path / "custom.config.json"
    config_path.write_text(json.dumps({
        "activity": {"skill_name": "custom", "output_path_key": "artifact"},
        "harness": {},
    }))

    class FakeHarness:
        def run(self, prompt, *, cwd, config):
            sentinel = tmp_path / "inputs" / ".process" / "custom.done.json"
            sentinel.parent.mkdir(parents=True)
            sentinel.write_text(json.dumps({
                "task": "custom", "verify_params": {"artifact": "artifact.json"}
            }))
            return HarnessResult(0, "", "")

    class CustomActivity(SkillActivity):
        def expected_output_path(self, skill_input: SkillActivityInput) -> Path:
            return Path("unused.json")

    output = CustomActivity(
        config_path=config_path, harness=FakeHarness(), repo_root=tmp_path
    ).execute(SkillActivityInput(input_paths=["inputs/story.json"]))

    assert output.sentinel_path == "inputs/.process/custom.done.json"
    assert (tmp_path / output.sentinel_path).exists()


def test_missing_sentinel_raises_after_successful_harness_run(tmp_path) -> None:
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

    with pytest.raises(SkillActivityError, match="Missing sentinel"):
        CustomActivity(
            config_path=config_path, harness=FakeHarness(), repo_root=tmp_path
        ).execute(SkillActivityInput(input_paths=["input.txt"]))

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
            assert "inputs/.process/custom.done.json" in prompt
            assert "Create the .process directory if needed" in prompt
            assert "Do not remove the sentinel after verification" in prompt
            return f"{prompt}\nmodified"

    prompt = CustomActivity(
        config_path=config_path, harness=FakeHarness(), repo_root=tmp_path
    ).build_prompt(SkillActivityInput(input_paths=["inputs/story.json"]))

    assert prompt.endswith("Do not remove the sentinel after verification.\nmodified")


def test_execute_returns_paths_for_created_activity_logs(tmp_path, monkeypatch) -> None:
    config_path = tmp_path / "custom.config.json"
    config_path.write_text(json.dumps({
        "activity": {"skill_name": "custom", "output_path_key": "artifact"},
        "harness": {},
    }))
    info = SimpleNamespace(
        workflow_id="wf-1", workflow_run_id="run-1", activity_type="custom",
        activity_id="act-1", attempt=1,
    )
    monkeypatch.setattr(
        "common.workflow_logger._resolve_activity_info", lambda activity_info=None: info
    )
    monkeypatch.setattr(
        WorkflowLoggerConfig,
        "load",
        lambda: WorkflowLoggerConfig(log_root=tmp_path / "logs"),
    )

    class FakeHarness:
        def run(self, prompt, *, cwd, config):
            (tmp_path / ".process").mkdir(exist_ok=True)
            (tmp_path / ".process" / "custom.done.json").write_text(json.dumps({
                "task": "custom", "verify_params": {"artifact": "artifact.json"}
            }))
            return HarnessResult(0, "", "")

    class CustomActivity(SkillActivity):
        def expected_output_path(self, skill_input: SkillActivityInput) -> Path:
            return Path("artifact.json")

    output = CustomActivity(
        config_path=config_path, harness=FakeHarness(), repo_root=tmp_path
    ).execute(SkillActivityInput())

    assert Path(output.activity_log_path).exists()
    assert Path(output.devin_log_path).exists()


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


def test_execute_maps_explicit_ambiguity_sentinel(tmp_path) -> None:
    config_path = tmp_path / "custom.config.json"
    config_path.write_text(json.dumps({
        "activity": {"skill_name": "custom", "output_path_key": "artifact"},
        "harness": {},
    }))

    class FakeHarness:
        def run(self, prompt, *, cwd, config):
            (tmp_path / ".process").mkdir(exist_ok=True)
            (tmp_path / ".process" / "custom.done.json").write_text(json.dumps({
                "task": "custom",
                "status": "ambiguity",
                "ambiguity_reason": "requirements conflict",
                "verify_params": {},
            }))
            return HarnessResult(0, "", "")

    class CustomActivity(SkillActivity):
        def expected_output_path(self, skill_input: SkillActivityInput) -> Path:
            return Path("unused.json")

    output = CustomActivity(
        config_path=config_path, harness=FakeHarness(), repo_root=tmp_path
    ).execute(SkillActivityInput())

    assert output.status == "ambiguity"
    assert output.ambiguity_reason == "requirements conflict"
    assert output.output_path == ""


def test_execute_returns_attempt_observation_with_identity_profile_and_usage(
    tmp_path, monkeypatch
) -> None:
    config_path = tmp_path / "custom.config.json"
    config_path.write_text(json.dumps({
        "activity": {"skill_name": "custom", "output_path_key": "artifact"},
        "harness": {"devin": {"model": "SWE-1.7", "permission_mode": "accept-edits"}},
    }))
    info = SimpleNamespace(
        workflow_id="wf-1",
        workflow_run_id="run-1",
        activity_type="custom",
        activity_id="act-1",
        attempt=2,
    )
    monkeypatch.setattr(
        "common.workflow_logger._resolve_activity_info", lambda activity_info=None: info
    )
    monkeypatch.setattr(
        "common.skill_activity._resolve_activity_info", lambda activity_info=None: info
    )
    monkeypatch.setattr(
        WorkflowLoggerConfig,
        "load",
        lambda: WorkflowLoggerConfig(log_root=tmp_path / "logs"),
    )

    class FakeHarness:
        def run(self, prompt, *, cwd, config):
            (tmp_path / ".process").mkdir(exist_ok=True)
            (tmp_path / ".process" / "custom.done.json").write_text(json.dumps({
                "task": "custom", "verify_params": {"artifact": "artifact.json"}
            }))
            return HarnessResult(0, "", "", HarnessUsage(10, 5, 2, None))

    class CustomActivity(SkillActivity):
        def expected_output_path(self, skill_input: SkillActivityInput) -> Path:
            return Path("artifact.json")

    output = CustomActivity(
        config_path=config_path, harness=FakeHarness(), repo_root=tmp_path
    ).execute(SkillActivityInput())

    assert output.observation == {
        "workflow_id": "wf-1",
        "run_id": "run-1",
        "sequence": 0,
        "step_name": "custom",
        "activity_type": "custom",
        "activity_id": "act-1",
        "attempt": 2,
        "started_at": output.observation["started_at"],
        "duration_ms": output.duration_ms,
        "outcome": "success",
        "model": "SWE-1.7",
        "permission_mode": "accept-edits",
        "output_path": "artifact.json",
        "activity_log_path": output.activity_log_path,
        "devin_log_path": output.devin_log_path,
        "atif_path": output.observation["atif_path"],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "cached_tokens": 2,
            "cost_usd": None,
        },
    }
