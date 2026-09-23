import json

from edd_refinement_workflow.activities.check_candidate import (
    CheckCandidateActivity,
)
from edd_refinement_workflow.progress_record import ProgressRecordStore


def _record_with_baseline(baseline_metrics: dict) -> dict:
    return {
        "evaluation_configuration": {
            "command": ["promptfoo", "eval"],
            "configuration": "promptfooconfig.yaml",
            "pinned_provider_version": "provider@1",
            "timeout_seconds": 10,
            "measurement_context": "baseline",
        },
        "candidate_metrics": [],
        "baseline_metrics": baseline_metrics,
    }


def test_check_candidate_returns_metrics_comparison_and_writes_artifacts(tmp_path) -> None:
    store = ProgressRecordStore(tmp_path)
    store.create_or_resume(
        "run-1",
        _record_with_baseline(
            {"passing": 5, "required_coverage": {}, "measurement_context": "baseline"}
        ),
    )

    def harness(**kwargs) -> dict:
        return {
            "passing": 7,
            "failing": 1,
            "total": 8,
            "percentage": 87.5,
            "required_coverage": {},
            "artifact_references": [],
        }

    result = CheckCandidateActivity(
        store, harness, now=lambda: "2026-09-23T12:00:00Z"
    ).run("run-1", "candidate-1", str(tmp_path))

    assert result["metrics"]["passing"] == 7
    assert result["metrics"]["status"] == "success"
    assert result["determination"] == "accept"
    assert result["compared_against"] == "baseline_metrics"
    assert result["comparison"]["decision"] == "accept"
    assert result["comparison"]["reason"] == "passing_count_increased"

    check_path = (
        tmp_path / ".process" / "edd" / "run-1" / "iterations" / "1" / "check.json"
    )
    check = json.loads(check_path.read_text())
    assert check["metrics"]["passing"] == 7
    assert check["determination"] == "accept"
    assert check["compared_against"] == "baseline_metrics"

    sentinel = json.loads(
        (tmp_path / ".process" / "check.done.json").read_text()
    )
    assert sentinel["task"] == "check_candidate"
    assert sentinel["determination"] == "accept"
    assert sentinel["files"] == [str(check_path.relative_to(tmp_path))]
