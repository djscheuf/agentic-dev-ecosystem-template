import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import jsonschema


class GuardrailRule(str, Enum):
    PASSED = "PASSED"


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


def validate_handoff(request: HandoffValidationRequest) -> HandoffValidationResult:
    artifact = json.loads(Path(request.output_path).read_text())
    schema = json.loads(Path(request.schema_path).read_text())
    jsonschema.validate(artifact, schema)
    return HandoffValidationResult(
        valid=True,
        ambiguity=False,
        rule=GuardrailRule.PASSED,
        artifact_path=request.output_path,
        schema_path=request.schema_path,
    )
