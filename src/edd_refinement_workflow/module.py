from common import WorkflowModuleSpec

from .activities.execute_refinement_action import execute_refinement_action_activity
from .activities.initialize_run import initialize_run_activity
from .activities.run_baseline_evaluation import run_baseline_evaluation_activity
from .activities.validate_candidate import validate_candidate_activity
from .approval import (
    record_human_approval_decision_activity,
    record_human_approved_evaluation_change_activity,
    request_human_approval_activity,
)
from .plan_refinement import plan_refinement_action
from .workflow import EddRefinementWorkflow

WORKFLOW_TYPE = "EddRefinementWorkflow"
ACTIVITY_TYPES = (
    "initialize_run",
    "run_baseline_evaluation",
    "plan_refinement_action",
    "request_human_approval",
    "record_human_approval_decision",
    "record_human_approved_evaluation_change",
    "execute_refinement_action",
    "validate_candidate",
)
ACTIVITIES = (
    initialize_run_activity,
    run_baseline_evaluation_activity,
    plan_refinement_action,
    request_human_approval_activity,
    record_human_approval_decision_activity,
    record_human_approved_evaluation_change_activity,
    execute_refinement_action_activity,
    validate_candidate_activity,
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
