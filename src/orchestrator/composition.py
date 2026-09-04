from collections import defaultdict

from cadence import Registry

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


def build_worker_registry(worker_spec: WorkerSpec) -> Registry:
    registry = Registry()
    try:
        for module in worker_spec.modules:
            module.register(registry)
    except Exception as exc:
        raise CatalogError(f"registration_failed: {module.name}") from exc

    declared_workflows = {
        name for module in worker_spec.modules for name in module.workflow_types
    }
    declared_activities = {
        name for module in worker_spec.modules for name in module.activity_types
    }
    if set(registry._workflows) != declared_workflows or set(registry._activities) != declared_activities:
        raise CatalogError("registration_mismatch")
    return registry
