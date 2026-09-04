import pytest

from common import WorkflowModuleSpec


def _register(registry):
    return None


def test_workflow_module_spec_rejects_blank_name():
    with pytest.raises(ValueError, match="name must be a non-empty trimmed string"):
        WorkflowModuleSpec(
            name=" ",
            domain="domain",
            task_list="task-list",
            workflow_types=("Workflow",),
            activity_types=("activity",),
            register=_register,
        )
