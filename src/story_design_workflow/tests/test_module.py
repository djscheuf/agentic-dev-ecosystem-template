from common import WorkflowModuleSpec


def test_story_design_module_declares_and_registers_accurate_spec():
    from story_design_workflow.module import SPEC, register

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
        "story_design",
        "story-design",
        "story-design",
    )
    assert SPEC.workflow_types == ("StoryDesignWorkflow",)
    assert SPEC.activity_types == (
        "validate_source_document",
        "audit_current_reality",
        "validate_handoff",
        "design_story_implementation",
        "grade_story_design",
        "draft_implementation_plan",
        "publish_story_design_report",
    )
    assert [name for name, _ in registry.workflows] == list(SPEC.workflow_types)
    assert [activity.name for activity in registry.activities] == list(SPEC.activity_types)
    assert SPEC.register is register
