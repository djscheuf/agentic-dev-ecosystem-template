import json

import pytest

from edd_refinement_workflow.baseline_result import (
    BaselineResult,
    BaselineResultArtifactWriter,
    BaselineResultError,
    BaselineResultParser,
)


def test_baseline_result_parser_extracts_metrics_and_failures() -> None:
    parser = BaselineResultParser()
    raw = {
        "passing": 5,
        "failing": 1,
        "total": 6,
        "percentage": 83.3,
        "coverage": {"required": ["tc1"], "uncovered": []},
        "failures": [{"name": "failing-test"}],
        "duration": 12.0,
        "outcome": "success",
    }

    result = parser.parse(raw)

    assert isinstance(result, BaselineResult)
    assert result.passing == 5
    assert result.failing == 1
    assert result.total == 6
    assert result.percentage == 83.3
    assert result.coverage == {"required": ["tc1"], "uncovered": []}
    assert result.failures == [{"name": "failing-test"}]
    assert result.duration == 12.0
    assert result.outcome == "success"


def test_baseline_result_parser_rejects_missing_fields() -> None:
    parser = BaselineResultParser()
    with pytest.raises(BaselineResultError):
        parser.parse({"passing": 5})


def test_artifact_writer_writes_baseline_result_and_returns_reference(
    tmp_path,
) -> None:
    writer = BaselineResultArtifactWriter(tmp_path)
    result = BaselineResult(
        passing=5,
        failing=1,
        total=6,
        percentage=83.3,
        coverage={"required": ["tc1"], "uncovered": []},
        failures=[{"name": "failing-test"}],
        duration=12.0,
        outcome="success",
    )

    reference = writer.write("run-1", result)

    assert reference == ".process/edd/run-1/baseline.json"
    artifact_path = tmp_path / ".process" / "edd" / "run-1" / "baseline.json"
    assert artifact_path.exists()
    written = json.loads(artifact_path.read_text())
    assert written["passing"] == 5
    assert written["failures"] == [{"name": "failing-test"}]
