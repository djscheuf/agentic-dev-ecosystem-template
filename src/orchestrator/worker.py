import argparse
import asyncio
import json
import logging
import os
import signal
from pathlib import Path

from cadence.client import Client
from cadence.worker import Worker

from .catalog import load_workflow_catalog, load_workflow_modules
from .composition import build_worker_registry, compose_worker_specs
from .runtime import run_worker_topology

DEFAULT_CADENCE_TARGET = os.environ.get("CADENCE_TARGET", "localhost:7833")
DEFAULT_CATALOG_PATH = Path(__file__).with_name("workflow_catalog.json")


def load_worker_specs(catalog_path=DEFAULT_CATALOG_PATH, cadence_target=DEFAULT_CADENCE_TARGET):
    catalog = load_workflow_catalog(catalog_path)
    modules = load_workflow_modules(catalog.workflow_modules)
    return compose_worker_specs(modules, cadence_target)


def inspect_catalog(catalog_path=DEFAULT_CATALOG_PATH, cadence_target=DEFAULT_CADENCE_TARGET):
    worker_specs = load_worker_specs(catalog_path, cadence_target)
    return {
        "worker_count": len(worker_specs),
        "domains": sorted({worker.domain for worker in worker_specs}),
        "routes": [
            {"domain": worker.domain, "task_list": worker.task_list}
            for worker in worker_specs
        ],
    }


def install_shutdown_handlers(stop_event, loop=None):
    event_loop = loop or asyncio.get_running_loop()
    for signum in (signal.SIGINT, signal.SIGTERM):
        event_loop.add_signal_handler(signum, stop_event.set)


async def _run_worker_specs(worker_specs):
    stop_event = asyncio.Event()
    install_shutdown_handlers(stop_event)
    await run_worker_topology(
        worker_specs,
        stop_event,
        client_factory=lambda spec: Client(
            domain=spec.domain, target=spec.cadence_target
        ),
        worker_factory=lambda spec, client: Worker(
            client, spec.task_list, build_worker_registry(spec)
        ),
    )


def start(catalog_path=DEFAULT_CATALOG_PATH, cadence_target=DEFAULT_CADENCE_TARGET):
    worker_specs = load_worker_specs(catalog_path, cadence_target)
    if not worker_specs:
        logging.getLogger(__name__).warning("zero configured Workers; exiting")
        return 0
    asyncio.run(_run_worker_specs(worker_specs))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", nargs="?", choices=("run", "inspect-catalog"), default="run")
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG_PATH)
    parser.add_argument("--cadence-target", default=DEFAULT_CADENCE_TARGET)
    args = parser.parse_args()
    if args.command == "inspect-catalog":
        print(json.dumps(inspect_catalog(args.catalog, args.cadence_target), sort_keys=True))
        return 0
    return start(args.catalog, args.cadence_target)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        pass
