import json

import pytest

from story_design_workflow.handoff_validation import (
    FinalArtifactCheck,
    FinalArtifactValidationRequest,
    GuardrailRule,
    HandoffValidationRequest,
    validate_final_artifacts,
    validate_handoff,
)


def test_validate_handoff_accepts_readable_schema_valid_artifact(tmp_path):
    artifact_path = tmp_path / "artifact.json"
    artifact_path.write_text(json.dumps({"story": "validated"}))
    schema_path = tmp_path / "artifact.schema.json"
    schema_path.write_text(
        json.dumps(
            {
                "type": "object",
                "properties": {"story": {"type": "string"}},
                "required": ["story"],
                "additionalProperties": False,
            }
        )
    )
    request = HandoffValidationRequest(
        output_path=str(artifact_path),
        previous_activity_name="audit_current_reality",
        workflow_id="workflow-1",
        run_id="run-1",
        attempt=1,
        schema_path=str(schema_path),
    )

    result = validate_handoff(request)

    assert result.valid is True
    assert result.ambiguity is False
    assert result.rule == GuardrailRule.PASSED
    assert result.artifact_path == str(artifact_path)
    assert result.schema_path == str(schema_path)


@pytest.mark.parametrize(
    ("artifact_content", "schema_content", "expected_rule"),
    [
        (None, {"type": "object"}, GuardrailRule.MISSING_OUTPUT_PATH),
        ("missing", {"type": "object"}, GuardrailRule.INACCESSIBLE_ARTIFACT),
        ("   ", {"type": "object"}, GuardrailRule.EMPTY_ARTIFACT),
        ("{broken", {"type": "object"}, GuardrailRule.MALFORMED_JSON),
        ("{}", {"type": "object", "required": ["story"]}, GuardrailRule.SCHEMA_VIOLATION),
        ("{}", None, GuardrailRule.SCHEMA_UNAVAILABLE),
    ],
)
def test_validate_handoff_returns_stable_rule_for_deterministic_failure(
    tmp_path, artifact_content, schema_content, expected_rule
):
    artifact_path = tmp_path / "artifact.json"
    output_path = ""
    if artifact_content is not None:
        output_path = str(artifact_path)
        if artifact_content != "missing":
            artifact_path.write_text(artifact_content)
    schema_path = tmp_path / "schema.json"
    if schema_content is not None:
        schema_path.write_text(json.dumps(schema_content))
    request = HandoffValidationRequest(
        output_path=output_path,
        previous_activity_name="audit_current_reality",
        workflow_id="workflow-1",
        run_id="run-1",
        attempt=1,
        schema_path=str(schema_path),
    )

    result = validate_handoff(request)

    assert result.valid is False
    assert result.ambiguity is False
    assert result.rule == expected_rule


def test_validate_final_artifacts_checks_every_required_artifact(tmp_path):
    checks = []
    for name in ("audit", "design", "design_grade"):
        artifact_path = tmp_path / f"{name}.json"
        artifact_path.write_text(json.dumps({"name": name}))
        schema_path = tmp_path / f"{name}.schema.json"
        schema_path.write_text(json.dumps({"type": "object", "required": ["name"]}))
        checks.append(FinalArtifactCheck(name, str(artifact_path), str(schema_path)))
    request = FinalArtifactValidationRequest(
        artifact_checks=tuple(checks), workflow_id="workflow-1", run_id="run-1", attempt=1
    )

    result = validate_final_artifacts(request)

    assert result.valid is True
    assert result.failed_artifacts == ()
    assert result.checked_artifacts == tuple(checks)
