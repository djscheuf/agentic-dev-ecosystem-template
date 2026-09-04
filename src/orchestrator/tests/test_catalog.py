import json

import pytest

from orchestrator.catalog import CatalogError, load_workflow_catalog


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
