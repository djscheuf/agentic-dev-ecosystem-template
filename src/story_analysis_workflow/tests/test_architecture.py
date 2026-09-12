import ast
from pathlib import Path


STALE_ORCHESTRATOR_PATHS = (
    "workflow.py",
    "story_analysis_engine.py",
    "escalation.py",
    "grade_repair.py",
    "grade_scoring.py",
    "activities",
)


def test_story_analysis_package_respects_layer_boundary():
    package_dir = Path(__file__).parents[1]
    src_dir = package_dir.parent

    imported_modules = {
        imported
        for source_path in package_dir.rglob("*.py")
        if "tests" not in source_path.parts
        for node in ast.walk(ast.parse(source_path.read_text()))
        for imported in (
            [node.module] if isinstance(node, ast.ImportFrom) and node.level == 0 else
            [alias.name for alias in node.names] if isinstance(node, ast.Import) else
            []
        )
        if imported
    }
    disallowed_imports = {
        name
        for name in imported_modules
        if name == "orchestrator"
        or name.startswith("orchestrator.")
        or (name.endswith("_workflow") and name != "story_analysis_workflow")
    }
    stale_paths = {
        path
        for relative_path in STALE_ORCHESTRATOR_PATHS
        if (path := src_dir / "orchestrator" / relative_path).exists()
    }

    assert (disallowed_imports, stale_paths) == (set(), set())
