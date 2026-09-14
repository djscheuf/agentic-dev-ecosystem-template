import subprocess
from pathlib import Path

from common.preflight import resolve_and_validate_target_repository


def test_preflight_succeeds_for_clean_target_with_skill(tmp_path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    subprocess.run(
        ["git", "init"],
        cwd=str(target),
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [
            "git",
            "-c",
            "user.email=test@test.com",
            "-c",
            "user.name=Test",
            "commit",
            "--allow-empty",
            "-m",
            "init",
        ],
        cwd=str(target),
        check=True,
        capture_output=True,
        text=True,
    )

    (target / ".devin" / "skills" / "custom").mkdir(parents=True)
    (target / ".devin" / "skills" / "custom" / "SKILL.md").write_text("#")
    (target / "evals" / "custom.tests.yaml").parent.mkdir(parents=True)
    (target / "evals" / "custom.tests.yaml").write_text("tests: []")
    anchor = target / "anchor.json"
    anchor.write_text("{}")
    subprocess.run(
        ["git", "add", "."],
        cwd=str(target),
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [
            "git",
            "-c",
            "user.email=test@test.com",
            "-c",
            "user.name=Test",
            "commit",
            "-m",
            "add files",
        ],
        cwd=str(target),
        check=True,
        capture_output=True,
        text=True,
    )

    result = resolve_and_validate_target_repository(
        anchor_path=str(anchor),
        explicit_root=str(target),
        scoped_paths=[],
        skill_name="custom",
        evaluation_path="evals/custom.tests.yaml",
        run_id="run-1",
        lease_ttl=60,
    )

    assert result.status == "success", result.failed_conditions
    assert result.target_context is not None
    assert result.target_context.repo_root == target.resolve()
    assert result.target_context.branch == "master"
    assert result.failed_conditions == []


def test_preflight_reports_all_failed_conditions(tmp_path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    subprocess.run(
        ["git", "init"],
        cwd=str(target),
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [
            "git",
            "-c",
            "user.email=test@test.com",
            "-c",
            "user.name=Test",
            "commit",
            "--allow-empty",
            "-m",
            "init",
        ],
        cwd=str(target),
        check=True,
        capture_output=True,
        text=True,
    )
    (target / "dirty.txt").write_text("dirty")
    anchor = target / "anchor.json"
    anchor.write_text("{}")

    result = resolve_and_validate_target_repository(
        anchor_path=str(anchor),
        explicit_root=str(target),
        scoped_paths=[],
        skill_name="custom",
        evaluation_path="evals/custom.tests.yaml",
        run_id="run-1",
        lease_ttl=60,
    )

    assert result.status == "failure"
    assert "target worktree has unexpected changes" in result.failed_conditions
    assert "target skill or evaluation suite missing" in result.failed_conditions
