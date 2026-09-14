from common import WorkflowModuleSpec

from .activities.initialize_run import initialize_run_activity
from .activities.run_baseline_evaluation import run_baseline_evaluation_activity
from .plan_refinement import plan_refinement_action
from .workflow import EddRefinementWorkflow

WORKFLOW_TYPE = "EddRefinementWorkflow"
ACTIVITY_TYPES = (
    "initialize_run",
    "run_baseline_evaluation",
    "plan_refinement_action",
)
ACTIVITIES = (
    initialize_run_activity,
    run_baseline_evaluation_activity,
    plan_refinement_action,
)


def register(registry) -> None:
    registry.workflow(name=WORKFLOW_TYPE)(EddRefinementWorkflow)
    for activity_type in ACTIVITIES:
        registry.register_activity(activity_type)


SPEC = WorkflowModuleSpec(
    name="edd_refinement",
    domain="edd-refinement",
    task_list="edd-refinement",
    workflow_types=(WORKFLOW_TYPE,),
    activity_types=ACTIVITY_TYPES,
    register=register,
)
