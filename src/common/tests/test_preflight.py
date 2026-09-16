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
    (target / "evals" / "custom.tests.yaml").write_text("providers:\n  - openai:gpt-4o\n")
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


def test_preflight_rejects_evaluation_path_outside_target_repository(tmp_path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()

    subprocess.run(["git", "init"], cwd=str(target), check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "-c", "user.email=test@test.com", "-c", "user.name=Test", "commit", "--allow-empty", "-m", "init"],
        cwd=str(target), check=True, capture_output=True, text=True,
    )

    (target / ".devin" / "skills" / "custom").mkdir(parents=True)
    (target / ".devin" / "skills" / "custom" / "SKILL.md").write_text("#")

    outside_eval = outside / "custom.tests.yaml"
    outside_eval.write_text("providers:\n  - openai:gpt-4o\n")

    anchor = target / "anchor.json"
    anchor.write_text("{}")
    subprocess.run(["git", "add", "."], cwd=str(target), check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "-c", "user.email=test@test.com", "-c", "user.name=Test", "commit", "-m", "add files"],
        cwd=str(target), check=True, capture_output=True, text=True,
    )

    result = resolve_and_validate_target_repository(
        anchor_path=str(anchor),
        explicit_root=str(target),
        scoped_paths=[],
        skill_name="custom",
        evaluation_path=str(outside_eval),
        run_id="run-1",
        lease_ttl=60,
    )

    assert result.status == "failure"
    assert any("outside target root" in cond for cond in result.failed_conditions)


def test_preflight_rejects_test_cases_path_outside_target_repository(tmp_path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()

    subprocess.run(["git", "init"], cwd=str(target), check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "-c", "user.email=test@test.com", "-c", "user.name=Test", "commit", "--allow-empty", "-m", "init"],
        cwd=str(target), check=True, capture_output=True, text=True,
    )

    (target / ".devin" / "skills" / "custom").mkdir(parents=True)
    (target / ".devin" / "skills" / "custom" / "SKILL.md").write_text("#")
    (target / "evals" / "custom.tests.yaml").parent.mkdir(parents=True)
    (target / "evals" / "custom.tests.yaml").write_text("providers:\n  - openai:gpt-4o\n")

    outside_cases = outside / "cases.yaml"
    outside_cases.write_text("[]\n")


    anchor = target / "anchor.json"
    anchor.write_text("{}")
    subprocess.run(["git", "add", "."], cwd=str(target), check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "-c", "user.email=test@test.com", "-c", "user.name=Test", "commit", "-m", "add files"],
        cwd=str(target), check=True, capture_output=True, text=True,
    )

    result = resolve_and_validate_target_repository(
        anchor_path=str(anchor),
        explicit_root=str(target),
        scoped_paths=[],
        skill_name="custom",
        evaluation_path="evals/custom.tests.yaml",
        run_id="run-1",
        lease_ttl=60,
        additional_paths=[str(outside_cases)],
    )

    assert result.status == "failure"
    assert any("outside target root" in cond for cond in result.failed_conditions)


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


def test_preflight_emits_instrumentation_events(tmp_path) -> None:
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
    (target / "evals" / "custom.tests.yaml").write_text("providers:\n  - openai:gpt-4o\n")
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

    events = []

    def on_event(name: str, **data) -> None:
        events.append((name, data))

    result = resolve_and_validate_target_repository(
        anchor_path=str(anchor),
        explicit_root=str(target),
        scoped_paths=[],
        skill_name="custom",
        evaluation_path="evals/custom.tests.yaml",
        run_id="run-1",
        lease_ttl=60,
        on_event=on_event,
    )

    assert result.status == "success"
    assert any(name == "ResolveTargetRepository" for name, _ in events)
    assert any(name == "CompletePreflight" for name, _ in events)


def test_preflight_emits_status_and_scoped_path_events(tmp_path) -> None:
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
    (target / "evals" / "custom.tests.yaml").write_text("providers:\n  - openai:gpt-4o\n")
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

    events = []

    def on_event(name: str, **data) -> None:
        events.append((name, data))

    result = resolve_and_validate_target_repository(
        anchor_path=str(anchor),
        explicit_root=str(target),
        scoped_paths=["evals/custom.tests.yaml"],
        skill_name="custom",
        evaluation_path="evals/custom.tests.yaml",
        run_id="run-1",
        lease_ttl=60,
        on_event=on_event,
    )

    assert result.status == "success", result.failed_conditions
    status_events = [(n, d) for n, d in events if n == "CheckRepositoryStatus"]
    assert status_events
    assert all(d["is_clean"] for _, d in status_events)
    assert any(n == "ValidateScopedPaths" for n, _ in events)
