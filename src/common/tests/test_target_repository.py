import subprocess
from pathlib import Path

import pytest
from common.target_repository import TargetRepositoryResolutionError, TargetWorktreeResolver


def test_resolve_anchor_returns_canonical_worktree_root(tmp_path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(
        ["git", "init"],
        cwd=str(repo),
        check=True,
        capture_output=True,
        text=True,
    )
    nested = repo / "nested"
    nested.mkdir()
    anchor = nested / "anchor.json"
    anchor.write_text("{}")

    resolver = TargetWorktreeResolver()
    root = resolver.resolve(str(anchor))

    assert root == repo.resolve()


def test_resolve_anchor_not_in_git_worktree_raises(tmp_path) -> None:
    non_repo = tmp_path / "non_repo"
    non_repo.mkdir()
    anchor = non_repo / "anchor.json"
    anchor.write_text("{}")

    resolver = TargetWorktreeResolver()
    with pytest.raises(TargetRepositoryResolutionError):
        resolver.resolve(str(anchor))


def test_resolve_matching_explicit_root_returns_canonical_worktree_root(tmp_path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(
        ["git", "init"],
        cwd=str(repo),
        check=True,
        capture_output=True,
        text=True,
    )
    nested = repo / "nested"
    nested.mkdir()
    anchor = nested / "anchor.json"
    anchor.write_text("{}")

    resolver = TargetWorktreeResolver()
    root = resolver.resolve(str(anchor), explicit_root=str(repo))

    assert root == repo.resolve()
