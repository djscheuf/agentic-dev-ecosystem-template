import dataclasses

from story_analysis_workflow.source_document_validation import (
    SourceDocumentValidationResult,
    SourceDocumentValidationRule,
)


def test_validation_result_is_frozen_and_exposes_stable_rules_without_path():
    result = SourceDocumentValidationResult(valid=False, rule=SourceDocumentValidationRule.EMPTY_OR_MISSING)

    assert dataclasses.asdict(result) == {
        "valid": False,
        "rule": SourceDocumentValidationRule.EMPTY_OR_MISSING,
    }
    assert [rule.value for rule in SourceDocumentValidationRule] == [
        "VALID",
        "EMPTY_OR_MISSING",
        "INACCESSIBLE_SOURCE",
        "NON_MARKDOWN_EXTENSION",
    ]
    assert not hasattr(result, "path")
