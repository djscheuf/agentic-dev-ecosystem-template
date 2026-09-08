import json

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
