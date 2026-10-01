import json

import pytest

from common.preflight import PreflightResult, TargetRepositoryContext
from edd_refinement_workflow.activities.preflight import run_preflight


def _write_input(parent, **overrides):
    doc = {
        "skill_folder": "skill",
        "eval_config": "eval.yaml",
        "test_command": ["npm", "test"],
        "inspect_command": ["node", "inspect.js", "{evaluation_id}"],
        "test_cases": "cases.yaml",
        "coverage_metadata_property": "metadata.covers_test_case_ids",
        "modification_scope": ["skill/"],
        "limits": {
            "max_iterations": 10,
            "max_tokens": 5000,
            "eval_timeout_seconds": 120,
        },
    }
    doc.update(overrides)
    path = parent / "edd-input.json"
    path.write_text(json.dumps(doc))
    return path


def test_run_preflight_resolves_repo_and_builds_request(monkeypatch, tmp_path) -> None:
    input_file = _write_input(tmp_path)

    captured = {}

    def fake_resolve(**kwargs):
        captured.update(kwargs)
        return PreflightResult(
            status="success",
            provider="test-provider",
            target_context=TargetRepositoryContext(
                repo_root=str(tmp_path),
                anchor_path=kwargs["anchor_path"],
                explicit_root=None,
                branch="main",
                starting_revision="abc123",
            ),
            failed_conditions=[],
        )

    monkeypatch.setattr(
        "edd_refinement_workflow.activities.preflight.resolve_and_validate_target_repository",
        fake_resolve,
    )

    output = run_preflight(str(input_file), "wf-1")

    assert output["preflight_result"]["status"] == "success"
    request = output["request"]
    assert request["workflow_run_id"] == "wf-1"
    assert request["input_path"] == str(input_file)
    assert request["edd_input"]["skill_folder"] == "skill"
    assert request["profile"]["provider"] == "test-provider"
    assert request["profile"]["timeout"] == 120
    assert request["profile"]["limits"]["max_tokens"] == 5000
    # Lease TTL is decoupled from eval_timeout_seconds (CR-02).
    assert request["lease_ttl"] != 120
    assert request["lease_ttl"] >= 1200
    # Preflight is anchored at the input document's skill folder.
    assert captured["anchor_path"].endswith("skill")
    assert captured["run_id"] == "wf-1"


def test_run_preflight_reports_failure(monkeypatch, tmp_path) -> None:
    input_file = _write_input(tmp_path)

    monkeypatch.setattr(
        "edd_refinement_workflow.activities.preflight.resolve_and_validate_target_repository",
        lambda **kwargs: PreflightResult(
            status="failure",
            provider=None,
            target_context=None,
            failed_conditions=["target worktree has unexpected changes"],
        ),
    )

    output = run_preflight(str(input_file), "wf-1")

    assert output["preflight_result"]["status"] == "failure"
    assert output["preflight_result"]["failed_conditions"] == [
        "target worktree has unexpected changes"
    ]
    assert output["request"] is None
