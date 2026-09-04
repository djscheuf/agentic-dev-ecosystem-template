import json

import pytest

from orchestrator.worker import inspect_catalog, start


def write_catalog(path, modules):
    path.write_text(json.dumps({"version": 1, "workflow_modules": modules}))


def test_orchestrator_cli_when_inspecting_catalog_reports_machine_readable_topology(tmp_path, caplog):
    catalog_path = tmp_path / "workflow_catalog.json"
    write_catalog(catalog_path, [])

    topology = inspect_catalog(catalog_path, "target")
    result = start(catalog_path, "target")

    assert topology == {"worker_count": 0, "domains": [], "routes": []}
    assert result == 0
    assert "zero configured Workers" in caplog.text
