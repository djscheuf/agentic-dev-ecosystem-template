from common import WorkflowModuleSpec


class RecordingRegistry:
    def __init__(self):
        self.workflows = []
        self.activities = []

    def workflow(self, *, name):
        def register(workflow_type):
            self.workflows.append((name, workflow_type))
            return workflow_type

        return register

    def register_activity(self, activity_type):
        self.activities.append(activity_type)


def test_story_analysis_module_declares_and_registers_accurate_spec():
    from story_analysis_workflow.module import SPEC, register

    registry = RecordingRegistry()
    register(registry)

    assert isinstance(SPEC, WorkflowModuleSpec)
    assert (SPEC.name, SPEC.domain, SPEC.task_list) == (
        "story_analysis",
        "story-analysis",
        "story-analysis",
    )
    assert SPEC.workflow_types == ("StoryAnalysisWorkflow",)
    assert SPEC.activity_types == (
        "extract_story_intent",
        "analyze_story",
        "grade_story_analysis",
        "repair_story_analysis",
    )
    assert [name for name, _ in registry.workflows] == list(SPEC.workflow_types)
    assert [activity.name for activity in registry.activities] == list(SPEC.activity_types)
    assert SPEC.register is register
