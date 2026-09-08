import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import jsonschema


class GuardrailRule(str, Enum):
    PASSED = "PASSED"
    MISSING_OUTPUT_PATH = "MISSING_OUTPUT_PATH"
    INACCESSIBLE_ARTIFACT = "INACCESSIBLE_ARTIFACT"
    UNREADABLE_ARTIFACT = "UNREADABLE_ARTIFACT"
    EMPTY_ARTIFACT = "EMPTY_ARTIFACT"
    MALFORMED_JSON = "MALFORMED_JSON"
    SCHEMA_VIOLATION = "SCHEMA_VIOLATION"
    SCHEMA_UNAVAILABLE = "SCHEMA_UNAVAILABLE"


@dataclass(frozen=True)
class HandoffValidationRequest:
    output_path: str
    previous_activity_name: str
    workflow_id: str
    run_id: str
    attempt: int
    schema_path: str


@dataclass(frozen=True)
class HandoffValidationResult:
    valid: bool
    ambiguity: bool
    rule: GuardrailRule
    artifact_path: str
    schema_path: str


def _result(request: HandoffValidationRequest, rule: GuardrailRule) -> HandoffValidationResult:
    return HandoffValidationResult(
        valid=rule == GuardrailRule.PASSED,
        ambiguity=False,
        rule=rule,
        artifact_path=request.output_path,
        schema_path=request.schema_path,
    )


def validate_handoff(request: HandoffValidationRequest) -> HandoffValidationResult:
    if not request.output_path:
        return _result(request, GuardrailRule.MISSING_OUTPUT_PATH)
    artifact_path = Path(request.output_path)
    if not artifact_path.is_file():
        return _result(request, GuardrailRule.INACCESSIBLE_ARTIFACT)
    try:
        content = artifact_path.read_text()
    except OSError:
        return _result(request, GuardrailRule.UNREADABLE_ARTIFACT)
    if not content.strip():
        return _result(request, GuardrailRule.EMPTY_ARTIFACT)
    try:
        artifact = json.loads(content)
    except json.JSONDecodeError:
        return _result(request, GuardrailRule.MALFORMED_JSON)
    try:
        schema = json.loads(Path(request.schema_path).read_text())
    except (OSError, json.JSONDecodeError):
        return _result(request, GuardrailRule.SCHEMA_UNAVAILABLE)
    try:
        jsonschema.validate(artifact, schema)
    except jsonschema.ValidationError:
        return _result(request, GuardrailRule.SCHEMA_VIOLATION)
    return _result(request, GuardrailRule.PASSED)
