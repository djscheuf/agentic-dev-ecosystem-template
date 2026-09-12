import json
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class SourceDocumentValidationRule(str, Enum):
    VALID = "VALID"
    EMPTY_OR_MISSING = "EMPTY_OR_MISSING"
    INACCESSIBLE_SOURCE = "INACCESSIBLE_SOURCE"
    NON_JSON_EXTENSION = "NON_JSON_EXTENSION"
    INVALID_JSON = "INVALID_JSON"


@dataclass(frozen=True)
class SourceDocumentValidationResult:
    valid: bool
    rule: SourceDocumentValidationRule


def validate_source_document(analysis_path: str | None) -> SourceDocumentValidationResult:
    if analysis_path is None or not analysis_path.strip():
        return SourceDocumentValidationResult(False, SourceDocumentValidationRule.EMPTY_OR_MISSING)
    path = Path(analysis_path)
    if path.suffix.lower() != ".json":
        return SourceDocumentValidationResult(False, SourceDocumentValidationRule.NON_JSON_EXTENSION)
    try:
        is_file = path.is_file()
        is_readable = os.access(path, os.R_OK)
    except OSError:
        is_file = False
        is_readable = False
    if not is_file or not is_readable:
        return SourceDocumentValidationResult(False, SourceDocumentValidationRule.INACCESSIBLE_SOURCE)
    try:
        json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return SourceDocumentValidationResult(False, SourceDocumentValidationRule.INVALID_JSON)
    return SourceDocumentValidationResult(True, SourceDocumentValidationRule.VALID)
