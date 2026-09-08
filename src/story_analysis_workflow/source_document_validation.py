from dataclasses import dataclass
from enum import Enum


class SourceDocumentValidationRule(str, Enum):
    VALID = "VALID"
    EMPTY_OR_MISSING = "EMPTY_OR_MISSING"
    INACCESSIBLE_SOURCE = "INACCESSIBLE_SOURCE"
    NON_MARKDOWN_EXTENSION = "NON_MARKDOWN_EXTENSION"


@dataclass(frozen=True)
class SourceDocumentValidationResult:
    valid: bool
    rule: SourceDocumentValidationRule
