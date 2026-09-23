from typing import Any

import pytest
import yaml
from common.preflight import PreflightResult, TargetRepositoryContext
from edd_refinement_workflow.activities.initialize_run import InitializeRunActivity
from edd_refinement_workflow.progress_record import ProgressRecordFactory, ProgressRecordStore


def _fake_harness(**kwargs) -> dict:
    return {
        "passing": 5,
        "failing": 1,
        "total": 6,
        "percentage": 83.33,
        "required_coverage": {},
    }


def _sample_edd_input(input_path: str = "/repo/edd-input.json") -> dict:
    return {
        "schema_version": 1,
        "skill_folder": "skill",
        "eval_config": "promptfooconfig.yaml",
        "test_command": ["promptfoo", "eval"],
        "inspect_command": ["node", "scripts/inspect-eval.js"],
        "test_cases": "test-cases.yaml",
        "coverage_metadata_property": "metadata.testCase",
        "modification_scope": ["skill"],
        "limits": {"eval_timeout_seconds": 120},
    }


def test_initialize_run_creates_record_and_emits_event(tmp_path) -> None:
    events = []

    def on_event(name: str, **data: Any) -> None:
        events.append((name, data))

    factory = ProgressRecordFactory(ProgressRecordStore(tmp_path))
    activity = InitializeRunActivity(
        factory, on_event=on_event, check_harness=_fake_harness
    )

    preflight = PreflightResult(
        status="success",
        target_context=TargetRepositoryContext(
            repo_root=tmp_path,
            anchor_path="",
            explicit_root=None,
            branch="main",
            starting_revision="abcdef123456",
        ),
    )

    profile = {
        "command": ["promptfoo", "eval", "-c", "promptfooconfig.yaml"],
        "configuration": "promptfooconfig.yaml",
        "provider": "openai:gpt-5@2026-08-07",
        "timeout": 120,
        "measurement_context": "baseline",
    }
    input_path = str(tmp_path / "edd-input.json")
    edd_input = _sample_edd_input(input_path)

    record = activity.run(
        "wf-1",
        preflight,
        profile,
        edd_input=edd_input,
        input_path=input_path,
    )

    assert record["run_id"] == "wf-1-abcdef1"
    assert record["workflow_run_id"] == "wf-1"
    assert record["starting_revision"] == "abcdef123456"
    assert record["token_usage"] == 0
    assert record["consecutive_confirmed_regressions"] == 0
    assert record["iteration_history"] == []
    assert record["schema_version"] == 5
    assert record["regression_evidence"] == []
    assert record["reverted_proposals"] == []
    assert record["recovery_results"] == []
    assert record["human_handoff_records"] == []
    assert record["evaluation_configuration"] == {
        "command": ["promptfoo", "eval", "-c", "promptfooconfig.yaml"],
        "configuration": "promptfooconfig.yaml",
        "pinned_provider_version": "openai:gpt-5@2026-08-07",
        "timeout_seconds": 120,
        "measurement_context": "baseline",
    }
    assert record["candidate_metrics"] == []
    assert record["best_accepted_state"] is None
    assert record["approval_request"] is None
    assert record["approval_history"] == []
    assert record["candidate"] is None
    assert record["candidate_history"] == []
    assert record["execution_artifacts"] == []
    assert record["target_repository"] == str(tmp_path)
    assert record["input_path"] == input_path
    assert record["input_parent"] == str(tmp_path)
    assert record["mutation_lease"]["repo_key"] == str(tmp_path)
    assert record["mutation_lease"]["run_id"] == record["run_id"]
    assert "token" in record["mutation_lease"]
    assert (
        tmp_path / ".process" / "edd" / record["run_id"] / "progress.json"
    ).exists()
    assert record["baseline_metrics"]["passing"] == 5
    assert (
        tmp_path
        / ".process"
        / "edd"
        / record["run_id"]
        / "iterations"
        / "0"
        / "check.json"
    ).exists()
    refinement_path = (
        tmp_path / ".process" / "edd" / record["run_id"] / "refinement.yaml"
    )
    assert refinement_path.exists()
    refinement = yaml.safe_load(refinement_path.read_text())
    assert refinement["edd_input"] == edd_input
    assert refinement["baseline"]["passing"] == 5
    assert refinement["iterations"] == []
    assert any(name == "InitializeRun" for name, _ in events)


def test_initialize_run_with_limit_configuration_seeds_durable_limit_state(
    tmp_path,
) -> None:
    activity = InitializeRunActivity(
        ProgressRecordFactory(ProgressRecordStore(tmp_path)),
        check_harness=_fake_harness,
    )
    preflight = PreflightResult(
        status="success",
        target_context=TargetRepositoryContext(
            repo_root=tmp_path,
            anchor_path="",
            explicit_root=None,
            branch="main",
            starting_revision="abcdef123456",
        ),
    )
    profile = {
        "command": ["promptfoo", "eval"],
        "configuration": "promptfooconfig.yaml",
        "provider": "provider@version",
        "timeout": 120,
        "limits": {
            "max_iterations": 4,
            "token_budget": 1000,
            "hard_token_limit": 1200,
            "regression_stop_threshold": 3,
        },
    }
    input_path = str(tmp_path / "edd-input.json")

    record = activity.run(
        "wf-1",
        preflight,
        profile,
        edd_input=_sample_edd_input(input_path),
        input_path=input_path,
    )

    assert record["budgets"] == profile["limits"]
    assert record["logical_iteration_count"] == 0
    assert record["cumulative_token_usage"] == 0
    assert record["pending_evidence_flags"] == []
    assert record["attempts"] == []


def test_initialize_run_raises_lease_conflict_for_concurrent_run(tmp_path) -> None:
    from common.mutation_lease_policy import LeaseConflictError

    factory = ProgressRecordFactory(ProgressRecordStore(tmp_path))
    activity = InitializeRunActivity(factory, check_harness=_fake_harness)
    preflight = PreflightResult(
        status="success",
        target_context=TargetRepositoryContext(
            repo_root=tmp_path,
            anchor_path="",
            explicit_root=None,
            branch="main",
            starting_revision="abcdef123456",
        ),
    )
    profile = {
        "command": ["promptfoo", "eval"],
        "configuration": "promptfooconfig.yaml",
        "provider": "provider@version",
        "timeout": 120,
    }
    input_path = str(tmp_path / "edd-input.json")

    activity.run(
        "wf-1",
        preflight,
        profile,
        edd_input=_sample_edd_input(input_path),
        input_path=input_path,
    )

    with pytest.raises(LeaseConflictError):
        activity.run(
            "wf-2",
            preflight,
            profile,
            edd_input=_sample_edd_input(input_path),
            input_path=input_path,
        )
