import pytest

from edd_refinement_workflow.baseline_result import (
    BaselineResult,
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
