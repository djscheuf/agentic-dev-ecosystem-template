import logging
from pathlib import Path

from .catalog import load_workflow_catalog, load_workflow_modules
from .composition import compose_worker_specs

DEFAULT_CADENCE_TARGET = "localhost:7833"
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


def start(catalog_path=DEFAULT_CATALOG_PATH, cadence_target=DEFAULT_CADENCE_TARGET):
    topology = inspect_catalog(catalog_path, cadence_target)
    if topology["worker_count"] == 0:
        logging.getLogger(__name__).warning("zero configured Workers; exiting")
        return 0
    return topology["worker_count"]
