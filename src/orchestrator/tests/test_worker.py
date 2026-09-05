import asyncio
import json
import signal

import pytest

from orchestrator.worker import inspect_catalog, install_shutdown_handlers, start


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


def test_worker_start_when_signalled_requests_coordinated_shutdown():
    callbacks = {}

    class Loop:
        def add_signal_handler(self, signum, callback):
            callbacks[signum] = callback

    stop_event = asyncio.Event()

    install_shutdown_handlers(stop_event, Loop())
    callbacks[signal.SIGTERM]()

    assert set(callbacks) == {signal.SIGINT, signal.SIGTERM}
    assert stop_event.is_set()
