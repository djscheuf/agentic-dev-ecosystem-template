from pathlib import Path

from common import WorkflowModuleSpec
from common.skill_activity_config import SkillActivityConfig


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
        "check_refinement_limits",
        "update_durable_counters",
        "edd_plan",
        "request_human_approval",
        "record_human_approval_decision",
        "record_human_approved_evaluation_change",
        "edd_do",
        "validate_candidate",
        "evaluate_candidate",
        "check_candidate",
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
    assert [name for name, _ in registry.workflows] == list(SPEC.workflow_types)
    assert [activity.name for activity in registry.activities] == list(
        SPEC.activity_types
    )
    assert SPEC.register is register


def test_edd_plan_config_explicitly_accepts_edits() -> None:
    config = SkillActivityConfig.load(
        Path(__file__).parents[1] / "activities" / "edd_plan.config.json"
    )

    assert config.skill_name == "edd-plan"
    assert config.output_path_key == "plan_path"
    assert config.harness["devin"]["permission_mode"] == "accept-edits"


def test_edd_do_config_explicitly_accepts_edits() -> None:
    config = SkillActivityConfig.load(
        Path(__file__).parents[1] / "activities" / "edd_do.config.json"
    )

    assert config.skill_name == "edd-do"
    assert config.output_path_key == "plan_path"
    assert config.harness["devin"]["permission_mode"] == "accept-edits"
