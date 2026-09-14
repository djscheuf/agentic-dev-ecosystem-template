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
    eval_file.write_text("tests: []")

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
