import dataclasses
import json
import os
from pathlib import Path

import pytest

from story_design_workflow.activities.validate_source_document import validate_source_document_activity
from story_design_workflow.source_document_validation import (
    SourceDocumentValidationResult,
    SourceDocumentValidationRule,
    validate_source_document,
)
from story_design_workflow.workflow import StoryDesignWorkflow


def test_validation_result_is_frozen_and_exposes_stable_rules():
    result = SourceDocumentValidationResult(
        False, SourceDocumentValidationRule.EMPTY_OR_MISSING
    )

    assert dataclasses.asdict(result) == {
        "valid": False,
        "rule": SourceDocumentValidationRule.EMPTY_OR_MISSING,
    }
    assert [rule.value for rule in SourceDocumentValidationRule] == [
        "VALID",
        "EMPTY_OR_MISSING",
        "INACCESSIBLE_SOURCE",
        "NON_JSON_EXTENSION",
        "INVALID_JSON",
    ]
    assert not hasattr(result, "path")


@pytest.mark.parametrize(
    ("analysis_path", "expected_rule"),
    [
        (None, SourceDocumentValidationRule.EMPTY_OR_MISSING),
        ("", SourceDocumentValidationRule.EMPTY_OR_MISSING),
        (" \t", SourceDocumentValidationRule.EMPTY_OR_MISSING),
        ("analysis.md", SourceDocumentValidationRule.NON_JSON_EXTENSION),
        ("analysis", SourceDocumentValidationRule.NON_JSON_EXTENSION),
        ("missing.json", SourceDocumentValidationRule.INACCESSIBLE_SOURCE),
    ],
)
def test_validate_source_document_maps_rejected_inputs_to_sanitized_rules(analysis_path, expected_rule):
    assert validate_source_document(analysis_path) == SourceDocumentValidationResult(
        valid=False,
        rule=expected_rule,
    )


def test_validate_source_document_sanitizes_filesystem_errors(monkeypatch):
    def fail_is_file(_self):
        raise OSError("sensitive filesystem detail")

    monkeypatch.setattr(Path, "is_file", fail_is_file)

    assert validate_source_document("secret.json") == SourceDocumentValidationResult(
        valid=False,
        rule=SourceDocumentValidationRule.INACCESSIBLE_SOURCE,
    )


def test_validate_source_document_rejects_unreadable_regular_file(tmp_path, monkeypatch):
    source = tmp_path / "analysis.json"
    source.write_text("{}")
    monkeypatch.setattr(os, "access", lambda _path, _mode: False)

    assert validate_source_document(str(source)) == SourceDocumentValidationResult(
        valid=False,
        rule=SourceDocumentValidationRule.INACCESSIBLE_SOURCE,
    )


def test_validate_source_document_rejects_malformed_json(tmp_path):
    source = tmp_path / "analysis.json"
    source.write_text("{broken")

    assert validate_source_document(str(source)) == SourceDocumentValidationResult(
        valid=False,
        rule=SourceDocumentValidationRule.INVALID_JSON,
    )


@pytest.mark.asyncio
async def test_validation_activity_returns_serializable_result_for_valid_json(tmp_path):
    source = tmp_path / "analysis.json"
    source.write_text(json.dumps({"story": "validated"}))

    result = await validate_source_document_activity(str(source))

    assert result == {"valid": True, "rule": SourceDocumentValidationRule.VALID}


@pytest.mark.asyncio
async def test_workflow_validation_adapter_schedules_registered_activity():
    workflow = StoryDesignWorkflow()
    calls = []

    async def execute(name, *args):
        calls.append((name, args))
        return {"valid": False, "rule": "EMPTY_OR_MISSING"}

    workflow._execute_validation_activity = execute

    result = await workflow._validate_source_document(None)

    assert calls == [("validate_source_document", (None,))]
    assert result == SourceDocumentValidationResult(
        False, SourceDocumentValidationRule.EMPTY_OR_MISSING
    )
