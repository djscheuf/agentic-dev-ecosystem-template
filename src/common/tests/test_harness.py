from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import Mapping

import pytest

from common.harness import Harness, HarnessResult, HarnessUsage


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
