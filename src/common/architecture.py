"""Static Python package dependency checks."""

import ast
from pathlib import Path
from typing import Iterable


def forbidden_imports(
    package_root: Path, *, forbidden_roots: set[str]
) -> list[str]:
    """Return source locations importing any forbidden top-level package."""
    violations: list[str] = []
    for source_path in sorted(package_root.rglob("*.py")):
        if "tests" in source_path.parts:
            continue
        tree = ast.parse(source_path.read_text(), filename=str(source_path))
        for node in ast.walk(tree):
            names: Iterable[str]
            if isinstance(node, ast.Import):
                names = (alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names = (node.module,)
            else:
                continue
            for name in names:
                if name.split(".", 1)[0] in forbidden_roots:
                    relative = source_path.relative_to(package_root)
                    violations.append(f"{relative}:{node.lineno}: {name}")
    return violations
