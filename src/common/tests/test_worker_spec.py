import pytest

from common import WorkerSpec, WorkflowModuleSpec


def _module():
    return WorkflowModuleSpec(
        name="module",
        domain="domain",
        task_list="task-list",
        workflow_types=("Workflow",),
        activity_types=("activity",),
        register=lambda registry: None,
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [("domain", ""), ("task_list", " task-list "), ("cadence_target", " ")],
)
def test_worker_spec_rejects_invalid_route(field, value):
    values = {
        "domain": "domain",
        "task_list": "task-list",
        "cadence_target": "localhost:7933",
        "modules": (_module(),),
    }
    values[field] = value

    with pytest.raises(ValueError, match=rf"{field} must be a non-empty trimmed string"):
        WorkerSpec(**values)
