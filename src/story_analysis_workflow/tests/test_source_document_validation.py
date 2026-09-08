import dataclasses
import os
from pathlib import Path

import pytest

from story_analysis_workflow.activities.validate_source_document import validate_source_document_activity
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


def test_validate_source_document_sanitizes_filesystem_errors(monkeypatch):
    def fail_is_file(_self):
        raise OSError("sensitive filesystem detail")

    monkeypatch.setattr(Path, "is_file", fail_is_file)

    assert validate_source_document("secret.md") == SourceDocumentValidationResult(
        valid=False,
        rule=SourceDocumentValidationRule.INACCESSIBLE_SOURCE,
    )


def test_validate_source_document_rejects_unreadable_regular_file(tmp_path, monkeypatch):
    source = tmp_path / "story.md"
    source.write_text("story")
    monkeypatch.setattr(os, "access", lambda _path, _mode: False)

    assert validate_source_document(str(source)) == SourceDocumentValidationResult(
        valid=False,
        rule=SourceDocumentValidationRule.INACCESSIBLE_SOURCE,
    )


@pytest.mark.asyncio
async def test_validation_activity_returns_serializable_result_for_special_markdown_path(tmp_path):
    source = tmp_path / "story ü; name.MD"
    source.write_text("")

    result = await validate_source_document_activity(str(source))

    assert result == {"valid": True, "rule": SourceDocumentValidationRule.VALID}
