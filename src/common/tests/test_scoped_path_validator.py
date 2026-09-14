from pathlib import Path

import pytest
from common.scoped_path_validator import ScopedPathValidator, TargetScopeError


def test_validate_in_scope_path_returns_canonical_path(tmp_path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    scoped = root / "inputs" / "story.json"
    scoped.parent.mkdir(parents=True)
    scoped.write_text("{}")

    validator = ScopedPathValidator()
    result = validator.validate(str(scoped), str(root))

    assert result == scoped.resolve()


def test_validate_parent_traversal_raises_target_scope_error(tmp_path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    outside = tmp_path / "outside.json"
    outside.write_text("{}")
    scoped = root / ".." / "outside.json"

    validator = ScopedPathValidator()
    with pytest.raises(TargetScopeError):
        validator.validate(str(scoped), str(root))
