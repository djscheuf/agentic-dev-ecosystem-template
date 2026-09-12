import pytest
from cadence import activity

from common import WorkflowModuleSpec
from orchestrator.composition import build_worker_registry, compose_worker_specs
from orchestrator.single_activity_workflow import WORKFLOW_TYPE, build_single_activity_workflow


@pytest.mark.asyncio
async def test_diagnostic_workflow_when_registered_is_route_scoped():
    AlphaWorkflow = build_single_activity_workflow(frozenset({"alpha"}))
    BetaWorkflow = build_single_activity_workflow(frozenset({"beta"}))

    alpha_result = await AlphaWorkflow().run("beta")
    beta_result = await BetaWorkflow().run("alpha")

    assert alpha_result["status"] == "failed"
    assert "alpha" in alpha_result["error"]
    assert beta_result["status"] == "failed"
    assert "beta" in beta_result["error"]

    @activity.defn(name="alpha")
    async def alpha():
        return None

    spec = WorkflowModuleSpec(
        "alpha", "domain", "alpha", (), ("alpha",), lambda registry: registry.register_activity(alpha)
    )
    registry = build_worker_registry(
        compose_worker_specs((spec,), "localhost:7833")[0]
    )
    assert registry.get_workflow(WORKFLOW_TYPE) is not None
