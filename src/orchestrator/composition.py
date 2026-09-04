from collections import defaultdict

from common import WorkerSpec, WorkflowModuleSpec

from .catalog import CatalogError


def compose_worker_specs(
    modules: tuple[WorkflowModuleSpec, ...], cadence_target: str
) -> tuple[WorkerSpec, ...]:
    grouped = defaultdict(list)
    for module in modules:
        grouped[(module.domain, module.task_list)].append(module)

    workers = []
    for (domain, task_list), route_modules in sorted(grouped.items()):
        ordered = tuple(sorted(route_modules, key=lambda module: module.name))
        for field_name, error_category in (
            ("workflow_types", "duplicate_workflow_type"),
            ("activity_types", "duplicate_activity_type"),
        ):
            names = [name for module in ordered for name in getattr(module, field_name)]
            if len(names) != len(set(names)):
                raise CatalogError(error_category)
        workers.append(WorkerSpec(domain, task_list, cadence_target, ordered))
    return tuple(workers)
