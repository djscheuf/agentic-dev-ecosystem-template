from pathlib import Path

from common.architecture import forbidden_imports


def test_common_does_not_depend_on_orchestrator_or_workflows() -> None:
    common_root = Path(__file__).resolve().parents[1]

    violations = forbidden_imports(
        common_root,
        forbidden_roots={"orchestrator", "story_analysis_workflow"},
    )

    assert violations == []
