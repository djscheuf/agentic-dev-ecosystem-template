import json
import sys
from types import ModuleType

import pytest

from common import WorkflowModuleSpec
from orchestrator.catalog import CatalogError, load_workflow_catalog, load_workflow_modules


def test_workflow_catalog_when_loaded_validates_immutable_module_paths(tmp_path):
    catalog_path = tmp_path / "workflow_catalog.json"
    catalog_path.write_text(
        json.dumps({"version": 1, "workflow_modules": ["alpha.module", "beta.module"]})
    )

    catalog = load_workflow_catalog(catalog_path)

    assert catalog.version == 1
    assert catalog.workflow_modules == ("alpha.module", "beta.module")

    catalog_path.write_text(
        json.dumps({"version": 1, "workflow_modules": ["alpha.module", "alpha.module"]})
    )
    with pytest.raises(CatalogError, match="duplicate_module_path"):
        load_workflow_catalog(catalog_path)


def test_workflow_modules_when_loaded_validate_every_spec_before_runtime():
    first = ModuleType("test_module_first")
    first.SPEC = WorkflowModuleSpec(
        "duplicate", "domain", "task-list", (), (), lambda registry: None
    )
    second = ModuleType("test_module_second")
    second.SPEC = WorkflowModuleSpec(
        "duplicate", "domain", "other-task-list", (), (), lambda registry: None
    )
    sys.modules[first.__name__] = first
    sys.modules[second.__name__] = second

    with pytest.raises(CatalogError, match="duplicate_module"):
        load_workflow_modules((first.__name__, second.__name__))
