from common import WorkflowModuleSpec


def test_edd_refinement_module_declares_and_registers_accurate_spec() -> None:
    from edd_refinement_workflow.module import SPEC, register

    class RecordingRegistry:
        def __init__(self):
            self.workflows = []
            self.activities = []

        def workflow(self, *, name):
            def register_workflow(workflow_type):
                self.workflows.append((name, workflow_type))
                return workflow_type

            return register_workflow

        def register_activity(self, activity_type):
            self.activities.append(activity_type)

    registry = RecordingRegistry()
    register(registry)

    assert isinstance(SPEC, WorkflowModuleSpec)
    assert (SPEC.name, SPEC.domain, SPEC.task_list) == (
        "edd_refinement",
        "edd-refinement",
        "edd-refinement",
    )
    assert SPEC.workflow_types == ("EddRefinementWorkflow",)
    assert SPEC.activity_types == (
        "initialize_run",
        "run_baseline_evaluation",
        "plan_refinement_action",
    )
    assert [name for name, _ in registry.workflows] == list(SPEC.workflow_types)
    assert [activity.name for activity in registry.activities] == list(
        SPEC.activity_types
    )
    assert SPEC.register is register
