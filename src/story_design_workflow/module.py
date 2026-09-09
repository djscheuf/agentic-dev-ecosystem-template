from common import WorkflowModuleSpec

from .activities.audit_current_reality import audit_current_reality
from .activities.design_story_implementation import design_story_implementation
from .activities.draft_implementation_plan import draft_implementation_plan
from .activities.grade_story_design import grade_story_design
from .activities.publish_story_design_report import publish_story_design_report
from .activities.validate_handoff import validate_handoff_activity
from .activities.validate_source_document import validate_source_document_activity
from .workflow import StoryDesignWorkflow

WORKFLOW_TYPE = "StoryDesignWorkflow"
ACTIVITY_TYPES = (
    "validate_source_document",
    "audit_current_reality",
    "validate_handoff",
    "design_story_implementation",
    "grade_story_design",
    "draft_implementation_plan",
    "publish_story_design_report",
)
ACTIVITIES = (
    validate_source_document_activity,
    audit_current_reality,
    validate_handoff_activity,
    design_story_implementation,
    grade_story_design,
    draft_implementation_plan,
    publish_story_design_report,
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
