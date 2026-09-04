import ast
from pathlib import Path


CLIENT_MODULES = (
    "starter.py",
    "cli.py",
    "signals.py",
    "queries.py",
    "run_single_activity.py",
)


def test_story_analysis_clients_do_not_import_orchestrator():
    package_dir = Path(__file__).parents[1]

    imported_modules = {
        imported
        for module_name in CLIENT_MODULES
        for node in ast.walk(ast.parse((package_dir / module_name).read_text()))
        for imported in (
            [node.module] if isinstance(node, ast.ImportFrom) else
            [alias.name for alias in node.names] if isinstance(node, ast.Import) else
            []
        )
        if imported
    }

    assert not {name for name in imported_modules if name == "orchestrator" or name.startswith("orchestrator.")}
