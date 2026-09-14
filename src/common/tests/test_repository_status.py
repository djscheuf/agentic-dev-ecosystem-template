import subprocess
from pathlib import Path

from common.repository_status import RepositoryStatusInspector


def test_inspect_clean_worktree_reports_clean(tmp_path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(
        ["git", "init"],
        cwd=str(repo),
        check=True,
        capture_output=True,
        text=True,
    )

    inspector = RepositoryStatusInspector()
    status = inspector.inspect(str(repo))

    assert status.is_clean is True
    assert status.staged == []
    assert status.modified == []
    assert status.untracked == []


def test_inspect_scratch_only_worktree_reports_clean(tmp_path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(
        ["git", "init"],
        cwd=str(repo),
        check=True,
        capture_output=True,
        text=True,
    )
    scratch = repo / "scratch"
    scratch.mkdir()
    (scratch / "out.json").write_text("{}")

    inspector = RepositoryStatusInspector()
    status = inspector.inspect(str(repo), scratch_globs=["scratch/*"])

    assert status.is_clean is True
