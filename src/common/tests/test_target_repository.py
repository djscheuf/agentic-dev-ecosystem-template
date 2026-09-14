import subprocess
from pathlib import Path

from common.target_repository import TargetWorktreeResolver


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
