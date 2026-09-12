import ast
from pathlib import Path


def test_story_design_package_respects_layer_boundary():
    package_dir = Path(__file__).parents[1]

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
        or (name.endswith("_workflow") and name != "story_design_workflow")
    }

    assert disallowed_imports == set(), f"disallowed imports: {disallowed_imports}"
