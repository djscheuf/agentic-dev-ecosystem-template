from pathlib import Path

from common.skill_and_evaluation_discovery import (
    SkillAndEvaluationDiscovery,
    SkillDiscoveryResult,
)


def test_discover_returns_ok_when_skill_and_evaluation_exist(tmp_path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    skill_dir = target / ".devin" / "skills" / "custom"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Custom")
    eval_file = target / "evals" / "custom.tests.yaml"
    eval_file.parent.mkdir(parents=True)
    eval_file.write_text("providers:\n  - openai:gpt-4o\n")

    discovery = SkillAndEvaluationDiscovery()
    result = discovery.discover(
        skill_name="custom",
        evaluation_path="evals/custom.tests.yaml",
        target_root=str(target),
    )

    assert isinstance(result, SkillDiscoveryResult)
    assert result.ok is True
    assert result.skill_path == skill_dir
    assert result.evaluation_path == eval_file


def test_discover_rejects_zero_or_multiple_providers_and_returns_single(
    tmp_path,
) -> None:
    target = tmp_path / "target"
    target.mkdir()
    skill_dir = target / ".devin" / "skills" / "custom"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Custom")
    eval_file = target / "evals" / "custom.tests.yaml"
    eval_file.parent.mkdir(parents=True)

    eval_file.write_text("providers:\n  - openai:gpt-4o\n")
    discovery = SkillAndEvaluationDiscovery()
    result = discovery.discover(
        skill_name="custom",
        evaluation_path="evals/custom.tests.yaml",
        target_root=str(target),
    )

    assert result.ok is True
    assert result.provider == "openai:gpt-4o"

    eval_file.write_text("providers: []\n")
    result = discovery.discover(
        skill_name="custom",
        evaluation_path="evals/custom.tests.yaml",
        target_root=str(target),
    )
    assert result.ok is False
    assert result.provider is None

    eval_file.write_text("providers:\n  - openai:gpt-4o\n  - localai:llama2\n")
    result = discovery.discover(
        skill_name="custom",
        evaluation_path="evals/custom.tests.yaml",
        target_root=str(target),
    )
    assert result.ok is False
    assert result.provider is None
