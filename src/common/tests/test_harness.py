import typing
from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import Mapping

import pytest

from common.harness import Harness, HarnessResult, HarnessUsage


def test_harness_protocol_declares_skill_activity_required_attributes() -> None:
    """harness-protocol-001: config_namespace/default_model/default_permission_mode
    are part of the structural contract, since SkillActivity.execute() depends on
    them for every harness."""
    hints = typing.get_type_hints(Harness)

    assert hints.get("config_namespace") is str
    assert hints.get("default_model") is str
    assert hints.get("default_permission_mode") is str


def test_harness_protocol_accepts_namespaced_configuration() -> None:
    class FakeHarness:
        def run(
            self,
            prompt: str,
            *,
            cwd: Path,
            config: Mapping[str, object],
        ) -> HarnessResult:
            return HarnessResult(exit_code=0, stdout=prompt, stderr=str(config))

    harness: Harness = FakeHarness()

    result = harness.run("prompt", cwd=Path("."), config={"fake": {"mode": "safe"}})

    assert result.exit_code == 0


def test_harness_result_without_usage_defaults_to_none() -> None:
    result = HarnessResult(exit_code=0, stdout="done", stderr="")

    assert result.usage is None


def test_harness_usage_is_immutable() -> None:
    usage = HarnessUsage(
        prompt_tokens=10,
        completion_tokens=5,
        cached_tokens=3,
        cost_usd=0.25,
    )

    with pytest.raises(FrozenInstanceError):
        usage.prompt_tokens = 11
