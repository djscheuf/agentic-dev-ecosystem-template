from pathlib import Path

import pytest
from common.scoped_path_validator import (
    PathScopeChecker,
    ScopedPathValidator,
    TargetScopeError,
)


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


@pytest.mark.parametrize(
    ("candidate", "scope", "expected"),
    [
        ("skill/SKILL.md", ["skill/SKILL.md"], True),
        ("skill/SKILL.md", ["skill/"], True),
        ("skill/references/guide.md", ["skill/"], True),
        ("skill", ["skill/"], False),
        ("skill-extra/x.py", ["skill/"], False),
        ("skill", ["skill/"], False),
        ("skill/other.py", ["skill/SKILL.md"], False),
        ("skill/SKILL.md", ["skill/SKILL.md", "docs/"], True),
        ("docs/guide.md", ["skill/"], False),
        ("skill/SKILL.md", [], False),
        ("skill/sub/../other.py", ["skill/"], True),
        ("skill/../outside.py", ["skill/"], False),
    ],
)
def test_path_scope_checker_authorizes_within_canonical_scope(
    candidate: str, scope: list[str], expected: bool
) -> None:
    checker = PathScopeChecker()

    assert checker.is_authorized(candidate, scope) is expected


def test_path_scope_checker_rejects_every_path_when_scope_empty() -> None:
    checker = PathScopeChecker()

    assert checker.is_authorized("anything/at/all.py", []) is False
