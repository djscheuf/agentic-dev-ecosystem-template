import json

import pytest

from story_analysis_workflow.handoff_validation import (
    GuardrailRule,
    HandoffValidationRequest,
    validate_handoff,
)


def test_validate_handoff_accepts_readable_schema_valid_artifact(tmp_path):
    artifact_path = tmp_path / "intent.json"
    artifact_path.write_text(json.dumps({"story": "validated"}))
    schema_path = tmp_path / "intent.schema.json"
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
        previous_activity_name="extract_story_intent",
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
        previous_activity_name="extract_story_intent",
        workflow_id="workflow-1",
        run_id="run-1",
        attempt=1,
        schema_path=str(schema_path),
    )

    result = validate_handoff(request)

    assert result.valid is False
    assert result.ambiguity is False
    assert result.rule == expected_rule
