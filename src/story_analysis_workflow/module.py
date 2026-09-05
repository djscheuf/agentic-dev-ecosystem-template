from common import WorkflowModuleSpec

from .activities.analyze_story import analyze_story
from .activities.extract_story_intent import extract_story_intent
from .activities.grade_story_analysis import grade_story_analysis
from .activities.repair_story_analysis import repair_story_analysis
from .workflow import StoryAnalysisWorkflow

WORKFLOW_TYPE = "StoryAnalysisWorkflow"
ACTIVITY_TYPES = (
    "extract_story_intent",
    "analyze_story",
    "grade_story_analysis",
    "repair_story_analysis",
)
ACTIVITIES = (
    extract_story_intent,
    analyze_story,
    grade_story_analysis,
    repair_story_analysis,
)


def register(registry) -> None:
    registry.workflow(name=WORKFLOW_TYPE)(StoryAnalysisWorkflow)
    for activity_type in ACTIVITIES:
        registry.register_activity(activity_type)


SPEC = WorkflowModuleSpec(
    name="story_analysis",
    domain="story-analysis",
    task_list="story-analysis",
    workflow_types=(WORKFLOW_TYPE,),
    activity_types=ACTIVITY_TYPES,
    register=register,
)
