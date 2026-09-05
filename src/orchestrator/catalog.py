import importlib
import json
from dataclasses import dataclass
from pathlib import Path

from common import WorkflowModuleSpec


class CatalogError(ValueError):
    pass


@dataclass(frozen=True)
class WorkflowCatalog:
    version: int
    workflow_modules: tuple[str, ...]


def load_workflow_catalog(path: str | Path) -> WorkflowCatalog:
    catalog_path = Path(path)
    try:
        data = json.loads(catalog_path.read_text())
    except FileNotFoundError as exc:
        raise CatalogError(f"missing_file: {catalog_path}") from exc
    except json.JSONDecodeError as exc:
        raise CatalogError(f"malformed_json: {catalog_path}") from exc

    if data.get("version") != 1:
        raise CatalogError("unsupported_version")
    module_paths = data.get("workflow_modules")
    if not isinstance(module_paths, list) or any(
        not isinstance(path, str) or not path.strip() or path != path.strip()
        for path in module_paths
    ):
        raise CatalogError("invalid_module_path")
    if len(module_paths) != len(set(module_paths)):
        raise CatalogError("duplicate_module_path")
    return WorkflowCatalog(version=1, workflow_modules=tuple(module_paths))


def load_workflow_modules(module_paths: tuple[str, ...]) -> tuple[WorkflowModuleSpec, ...]:
    specs = []
    for module_path in module_paths:
        try:
            module = importlib.import_module(module_path)
        except ImportError as exc:
            raise CatalogError(f"import_failed: {module_path}") from exc
        if not hasattr(module, "SPEC"):
            raise CatalogError(f"missing_spec: {module_path}")
        if not isinstance(module.SPEC, WorkflowModuleSpec):
            raise CatalogError(f"wrong_spec_type: {module_path}")
        specs.append(module.SPEC)
    names = [spec.name for spec in specs]
    if len(names) != len(set(names)):
        raise CatalogError("duplicate_module")
    return tuple(specs)
