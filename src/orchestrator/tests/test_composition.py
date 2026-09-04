import pytest
from cadence import workflow

from common import WorkflowModuleSpec
from orchestrator.catalog import CatalogError
from orchestrator.composition import build_worker_registry, compose_worker_specs


def module(name, task_list, workflows, activities):
    return WorkflowModuleSpec(
        name, "domain", task_list, workflows, activities, lambda registry: None
    )


def test_worker_topology_when_composed_groups_routes_and_rejects_conflicts():
    specs = (
        module("beta", "shared", ("BetaWorkflow",), ("beta",)),
        module("alpha", "shared", ("AlphaWorkflow",), ("alpha",)),
        module("other", "other", ("OtherWorkflow",), ("other",)),
    )

    workers = compose_worker_specs(specs, "localhost:7833")

    assert [(worker.task_list, tuple(m.name for m in worker.modules)) for worker in workers] == [
        ("other", ("other",)),
        ("shared", ("alpha", "beta")),
    ]

    conflicting = specs + (module("conflict", "shared", ("AlphaWorkflow",), ()),)
    with pytest.raises(CatalogError, match="duplicate_workflow_type"):
        compose_worker_specs(conflicting, "localhost:7833")


def test_worker_registry_when_built_registers_declared_module_surface():
    class DeclaredWorkflow:
        @workflow.run
        async def run(self):
            return None

    def register(registry):
        registry.workflow(name="DeclaredWorkflow")(DeclaredWorkflow)

    spec = WorkflowModuleSpec(
        "module", "domain", "task-list", ("DeclaredWorkflow",), ("missing_activity",), register
    )
    worker = compose_worker_specs((spec,), "localhost:7833")[0]

    with pytest.raises(CatalogError, match="registration_mismatch"):
        build_worker_registry(worker)
