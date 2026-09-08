from common import WorkflowModuleSpec

from .activities.audit_current_reality import audit_current_reality
from .activities.design_story_implementation import design_story_implementation
from .activities.grade_story_design import grade_story_design
from .workflow import StoryDesignWorkflow

WORKFLOW_TYPE = "StoryDesignWorkflow"
ACTIVITY_TYPES = (
    "audit_current_reality",
    "design_story_implementation",
    "grade_story_design",
)
ACTIVITIES = (
    audit_current_reality,
    design_story_implementation,
    grade_story_design,
)


def register(registry) -> None:
    registry.workflow(name=WORKFLOW_TYPE)(StoryDesignWorkflow)
    for activity_type in ACTIVITIES:
        registry.register_activity(activity_type)


SPEC = WorkflowModuleSpec(
    name="story_design",
    domain="story-design",
    task_list="story-design",
    workflow_types=(WORKFLOW_TYPE,),
    activity_types=ACTIVITY_TYPES,
    register=register,
)
