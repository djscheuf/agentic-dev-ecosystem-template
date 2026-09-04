from pathlib import Path
from typing import Mapping

from common.harness import Harness, HarnessResult


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
