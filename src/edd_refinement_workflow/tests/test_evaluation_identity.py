import pytest

from edd_refinement_workflow.evaluation_identity import (
    EvaluationIdentityError,
    build_inspect_command,
    extract_evaluation_id,
)


def test_extract_evaluation_id_from_dict() -> None:
    assert extract_evaluation_id({"evaluation_id": "eval-123"}) == "eval-123"
    assert extract_evaluation_id({"id": "eval-456"}) == "eval-456"
    assert extract_evaluation_id({"evaluation_id": "abc", "id": "def"}) == "abc"


def test_extract_evaluation_id_raises_when_missing() -> None:
    with pytest.raises(EvaluationIdentityError, match="evaluation_id"):
        extract_evaluation_id({"passing": 5, "total": 6})


def test_build_inspect_command_replaces_placeholder() -> None:
    assert build_inspect_command(
        ["node", "inspect.js", "--id", "{evaluation_id}"], "eval-123"
    ) == ["node", "inspect.js", "--id", "eval-123"]


def test_build_inspect_command_leaves_static_arguments_unchanged() -> None:
    assert build_inspect_command(
        ["node", "inspect.js"], "eval-123"
    ) == ["node", "inspect.js"]
