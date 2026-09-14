from pathlib import Path

from common.scoped_path_validator import ScopedPathValidator


def test_validate_in_scope_path_returns_canonical_path(tmp_path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    scoped = root / "inputs" / "story.json"
    scoped.parent.mkdir(parents=True)
    scoped.write_text("{}")

    validator = ScopedPathValidator()
    result = validator.validate(str(scoped), str(root))

    assert result == scoped.resolve()
