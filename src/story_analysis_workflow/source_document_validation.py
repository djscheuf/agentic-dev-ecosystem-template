import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class SourceDocumentValidationRule(str, Enum):
    VALID = "VALID"
    EMPTY_OR_MISSING = "EMPTY_OR_MISSING"
    INACCESSIBLE_SOURCE = "INACCESSIBLE_SOURCE"
    NON_MARKDOWN_EXTENSION = "NON_MARKDOWN_EXTENSION"


@dataclass(frozen=True)
class SourceDocumentValidationResult:
    valid: bool
    rule: SourceDocumentValidationRule


def validate_source_document(story_document: str | None) -> SourceDocumentValidationResult:
    if story_document is None or not story_document.strip():
        return SourceDocumentValidationResult(False, SourceDocumentValidationRule.EMPTY_OR_MISSING)
    path = Path(story_document)
    if path.suffix.lower() != ".md":
        return SourceDocumentValidationResult(False, SourceDocumentValidationRule.NON_MARKDOWN_EXTENSION)
    try:
        is_file = path.is_file()
        is_readable = os.access(path, os.R_OK)
    except OSError:
        is_file = False
        is_readable = False
    if not is_file or not is_readable:
        return SourceDocumentValidationResult(False, SourceDocumentValidationRule.INACCESSIBLE_SOURCE)
    return SourceDocumentValidationResult(True, SourceDocumentValidationRule.VALID)
