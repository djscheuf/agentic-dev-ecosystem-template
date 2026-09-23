from common import WorkflowModuleSpec

from .activities.check_refinement_limits import check_refinement_limits_activity
from .activities.commit_accepted_candidate import commit_accepted_candidate_activity
from .activities.edd_do import edd_do_action
from .activities.edd_plan import edd_plan_action
from .activities.evaluate_candidate import evaluate_candidate_activity
from .activities.initialize_run import initialize_run_activity
from .activities.rerun_degraded_candidate import rerun_degraded_candidate_activity
from .activities.regression_recovery import (
    classify_regression_evidence_activity,
    human_handoff_activity,
    publish_human_handoff_activity,
    record_confirmed_regression_activity,
    record_reverted_proposal_context_activity,
    revert_repository_to_best_activity,
    verify_recovery_metrics_activity,
)
from .activities.run_baseline_evaluation import run_baseline_evaluation_activity
from .activities.update_durable_counters import update_durable_counters_activity
from .activities.validate_candidate import validate_candidate_activity
from .approval import (
    record_human_approval_decision_activity,
    record_human_approved_evaluation_change_activity,
    request_human_approval_activity,
)
from .finalize_run import finalize_run_activity
from .workflow import EddRefinementWorkflow

WORKFLOW_TYPE = "EddRefinementWorkflow"
ACTIVITY_TYPES = (
    "initialize_run",
    "run_baseline_evaluation",
    "check_refinement_limits",
    "update_durable_counters",
    "edd_plan",
    "request_human_approval",
    "record_human_approval_decision",
    "record_human_approved_evaluation_change",
    "edd_do",
    "validate_candidate",
    "evaluate_candidate",
    "commit_accepted_candidate",
    "rerun_degraded_candidate",
    "classify_regression_evidence",
    "record_confirmed_regression",
    "revert_repository_to_best",
    "verify_recovery_metrics",
    "record_reverted_proposal_context",
    "publish_human_handoff",
    "human_handoff",
    "finalize_run",
)
ACTIVITIES = (
    initialize_run_activity,
    run_baseline_evaluation_activity,
    check_refinement_limits_activity,
    update_durable_counters_activity,
    edd_plan_action,
    request_human_approval_activity,
    record_human_approval_decision_activity,
    record_human_approved_evaluation_change_activity,
    edd_do_action,
    validate_candidate_activity,
    evaluate_candidate_activity,
    commit_accepted_candidate_activity,
    rerun_degraded_candidate_activity,
    classify_regression_evidence_activity,
    record_confirmed_regression_activity,
    revert_repository_to_best_activity,
    verify_recovery_metrics_activity,
    record_reverted_proposal_context_activity,
    publish_human_handoff_activity,
    human_handoff_activity,
    finalize_run_activity,
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
