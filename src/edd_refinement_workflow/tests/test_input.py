import json
from pathlib import Path

import pytest
from edd_refinement_workflow.input import EddRefinementInput, EddRefinementInputError


def test_edd_refinement_input_resolves_relative_paths_and_rejects_invalid_inputs(
    tmp_path,
) -> None:
    parent = tmp_path / "inputs"
    parent.mkdir()

    valid = {
        "skill_folder": "skill",
        "eval_config": "eval.yaml",
        "test_command": ["npm", "test"],
        "inspect_command": ["node", "inspect.js", "{evaluation_id}"],
        "test_cases": "cases.yaml",
        "coverage_metadata_property": "metadata.covers_test_case_ids",
        "modification_scope": ["scope.md", "scope2.md"],
        "limits": {
            "max_iterations": 10,
            "eval_timeout_seconds": 120,
        },
    }

    input_file = parent / "edd-input.json"
    input_file.write_text(json.dumps(valid))

    result = EddRefinementInput.from_path(input_file)

    assert result.input_parent == parent
    assert result.input_path == input_file
    assert result.skill_folder == (parent / "skill").resolve()
    assert result.eval_config == (parent / "eval.yaml").resolve()
    assert result.test_cases == (parent / "cases.yaml").resolve()
    assert result.modification_scope == [
        (parent / "scope.md").resolve(),
        (parent / "scope2.md").resolve(),
    ]
    assert result.test_command == ["npm", "test"]
    assert result.inspect_command == ["node", "inspect.js", "{evaluation_id}"]
    assert result.coverage_metadata_property == "metadata.covers_test_case_ids"
    assert result.limits == {
        "max_iterations": 10,
        "eval_timeout_seconds": 120,
    }

    missing_skill = {**valid}
    del missing_skill["skill_folder"]
    (parent / "missing-skill.json").write_text(json.dumps(missing_skill))
    with pytest.raises(EddRefinementInputError, match="missing required field"):
        EddRefinementInput.from_path(parent / "missing-skill.json")

    malformed = parent / "malformed.json"
    malformed.write_text("{not json")
    with pytest.raises(EddRefinementInputError, match="malformed"):
        EddRefinementInput.from_path(malformed)

    empty_command = {**valid, "test_command": []}
    (parent / "empty-cmd.json").write_text(json.dumps(empty_command))
    with pytest.raises(EddRefinementInputError, match="test_command"):
        EddRefinementInput.from_path(parent / "empty-cmd.json")
