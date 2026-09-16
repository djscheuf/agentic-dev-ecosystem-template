import pytest

from edd_refinement_workflow.git_commit_message import GitCommitMessageBuilder


def test_builder_falls_back_to_conventional_commit_without_skill(tmp_path) -> None:
    builder = GitCommitMessageBuilder(tmp_path)

    assert builder.build("candidate-1") == "feat(edd refinement): accept candidate candidate-1"


def test_builder_uses_template_from_git_commit_skill(tmp_path) -> None:
    skill_dir = tmp_path / ".devin" / "skills" / "git-commit"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: git-commit\n---\n\n"
        "Template: fix(scope): accept {candidate_id}\n"
    )

    builder = GitCommitMessageBuilder(tmp_path)

    assert builder.build("candidate-1") == "fix(scope): accept candidate-1"


def test_builder_ignores_skill_without_template_and_uses_fallback(tmp_path) -> None:
    skill_dir = tmp_path / ".devin" / "skills" / "git-commit"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Git Commit Skill\n\nNo template here.\n")

    builder = GitCommitMessageBuilder(tmp_path)

    assert builder.build("candidate-1") == "feat(edd refinement): accept candidate candidate-1"
