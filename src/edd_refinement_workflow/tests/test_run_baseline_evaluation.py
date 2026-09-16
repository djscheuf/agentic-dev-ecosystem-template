import pytest
import yaml

from edd_refinement_workflow.activities.run_baseline_evaluation import (
    RunBaselineEvaluationActivity,
    run_baseline_evaluation_activity,
)
from edd_refinement_workflow.progress_record import ProgressRecordStore


def _make_cases(tmp_path, ids):
    path = tmp_path / "cases.yaml"
    path.write_text(
        yaml.safe_dump(
            [
                {
                    "group": "Core",
                    "tests": [{"id": case_id} for case_id in ids],
                }
            ]
        )
    )
    return path


def test_baseline_evaluation_runs_test_and_inspect_commands_and_records_metric(
    tmp_path,
) -> None:
    cases_path = _make_cases(tmp_path, ["TC-001"])
    store = ProgressRecordStore(tmp_path)
    store.create_or_resume(
        "run-1",
        {
            "schema_version": 5,
            "run_id": "run-1",
            "evaluation_configuration": {
                "command": ["promptfoo", "eval"],
                "configuration": "promptfooconfig.yaml",
                "pinned_provider_version": "openai:gpt-5",
                "timeout_seconds": 120,
                "measurement_context": "baseline",
            },
            "test_cases": str(cases_path),
            "coverage_metadata_property": "metadata.covers_test_case_ids",
        },
    )

    invocations = []

    def harness(**kwargs) -> dict:
        invocations.append(kwargs["command"])
        if kwargs["command"] == ["promptfoo", "eval"]:
            return {"evaluation_id": "baseline-eval-123"}
        if kwargs["command"] == ["node", "inspect.js", "--id", "baseline-eval-123"]:
            return {
                "passing": 5,
                "failing": 1,
                "total": 6,
                "percentage": 83.3,
                "metadata": {"covers_test_case_ids": ["TC-001"]},
                "artifact_references": [".process/edd/run-1/baseline.json"],
            }
        return {}

    profile = {
        "command": ["promptfoo", "eval"],
        "inspect_command": ["node", "inspect.js", "--id", "{evaluation_id}"],
        "timeout": 120,
        "test_cases": str(cases_path),
        "coverage_metadata_property": "metadata.covers_test_case_ids",
    }

    activity = RunBaselineEvaluationActivity(store, harness)
    result = activity.run("run-1", profile, str(tmp_path))

    assert invocations == [
        ["promptfoo", "eval"],
        ["node", "inspect.js", "--id", "baseline-eval-123"],
    ]
    assert result["candidate_id"] == "baseline"
    assert result["run_id"] == "run-1"
    assert result["attempt_number"] == 1
    assert result["passing"] == 5
    assert result["failing"] == 1
    assert result["total"] == 6
    assert result["percentage"] == 83.3
    assert result["required_coverage"] == {"TC-001": 1}
    assert result["artifact_references"] == [".process/edd/run-1/baseline.json"]
    assert result["pinned_provider_version"] == "openai:gpt-5"
    assert result["measurement_context"] == "baseline"
    assert result["status"] == "success"
    assert result["failure_reason"] is None
    assert result["usable_for_acceptance"] is True

    record = store.create_or_resume("run-1", {})
    assert record["baseline_metrics"] == result
    assert record["attempts"][0]["provider"] == "openai:gpt-5"


def test_baseline_evaluation_rejects_unknown_test_case_ids(
    tmp_path,
) -> None:
    cases_path = _make_cases(tmp_path, ["TC-001"])
    store = ProgressRecordStore(tmp_path)
    store.create_or_resume(
        "run-1",
        {
            "evaluation_configuration": {
                "command": ["eval"],
                "configuration": "config",
                "pinned_provider_version": "provider@1",
                "timeout_seconds": 10,
                "measurement_context": "baseline",
            },
            "test_cases": str(cases_path),
            "coverage_metadata_property": "metadata.covers_test_case_ids",
        },
    )

    def harness(**kwargs) -> dict:
        if kwargs["command"] == ["eval"]:
            return {"evaluation_id": "e1"}
        return {
            "passing": 1,
            "failing": 1,
            "total": 2,
            "percentage": 50.0,
            "metadata": {"covers_test_case_ids": ["TC-001", "TC-999"]},
        }

    profile = {
        "command": ["eval"],
        "inspect_command": ["inspect", "{evaluation_id}"],
        "timeout": 10,
        "test_cases": str(cases_path),
        "coverage_metadata_property": "metadata.covers_test_case_ids",
    }

    result = RunBaselineEvaluationActivity(store, harness).run(
        "run-1", profile, str(tmp_path)
    )

    assert result["status"] == "rejected"
    assert result["failure_reason"] == "unknown_test_case_ids"
    assert result["required_coverage"] == {"TC-001": 1}


@pytest.mark.asyncio
async def test_run_baseline_evaluation_activity_runs_identity_chain_and_returns_metric(
    tmp_path, monkeypatch
) -> None:
    cases_path = _make_cases(tmp_path, ["TC-002"])
    store = ProgressRecordStore(tmp_path)
    store.create_or_resume(
        "run-1",
        {
            "evaluation_configuration": {
                "command": ["test"],
                "configuration": "c",
                "pinned_provider_version": "p",
                "timeout_seconds": 10,
                "measurement_context": "baseline",
            },
            "test_cases": str(cases_path),
            "coverage_metadata_property": "metadata.covers_test_case_ids",
        },
    )

    def _fake_run(**kwargs):
        if kwargs["command"] == ["test"]:
            return {"evaluation_id": "eval-1"}
        if kwargs["command"] == ["inspect", "eval-1"]:
            return {
                "passing": 2,
                "failing": 0,
                "total": 2,
                "percentage": 100.0,
                "metadata": {"covers_test_case_ids": ["TC-002"]},
            }
        return {}

    monkeypatch.setattr(
        "edd_refinement_workflow.activities.run_baseline_evaluation._run_evaluation_command",
        _fake_run,
    )

    result = await run_baseline_evaluation_activity(
        "run-1",
        {
            "command": ["test"],
            "inspect_command": ["inspect", "{evaluation_id}"],
            "timeout": 10,
            "test_cases": str(cases_path),
            "coverage_metadata_property": "metadata.covers_test_case_ids",
        },
        str(tmp_path),
    )

    assert result["candidate_id"] == "baseline"
    assert result["passing"] == 2
    assert result["required_coverage"] == {"TC-002": 1}
    assert result["status"] == "success"
