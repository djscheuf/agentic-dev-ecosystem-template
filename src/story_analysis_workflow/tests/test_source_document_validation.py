import dataclasses

import pytest

from story_analysis_workflow.source_document_validation import (
    SourceDocumentValidationResult,
    SourceDocumentValidationRule,
    validate_source_document,
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


@pytest.mark.parametrize(
    ("story_document", "expected_rule"),
    [
        (None, SourceDocumentValidationRule.EMPTY_OR_MISSING),
        ("", SourceDocumentValidationRule.EMPTY_OR_MISSING),
        (" \t", SourceDocumentValidationRule.EMPTY_OR_MISSING),
        ("story.txt", SourceDocumentValidationRule.NON_MARKDOWN_EXTENSION),
        ("story", SourceDocumentValidationRule.NON_MARKDOWN_EXTENSION),
        ("missing.md", SourceDocumentValidationRule.INACCESSIBLE_SOURCE),
    ],
)
def test_validate_source_document_maps_rejected_inputs_to_sanitized_rules(story_document, expected_rule):
    assert validate_source_document(story_document) == SourceDocumentValidationResult(
        valid=False,
        rule=expected_rule,
    )
