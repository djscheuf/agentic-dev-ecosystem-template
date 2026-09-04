import pytest

from common import WorkflowModuleSpec


def _register(registry):
    return None


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("name", " "),
        ("domain", " domain "),
        ("task_list", ""),
    ],
)
def test_workflow_module_spec_rejects_invalid_identity(field, value):
    values = {"name": "module", "domain": "domain", "task_list": "task-list"}
    values[field] = value

    with pytest.raises(ValueError, match=rf"{field} must be a non-empty trimmed string"):
        WorkflowModuleSpec(
            **values,
            workflow_types=("Workflow",),
            activity_types=("activity",),
            register=_register,
        )
