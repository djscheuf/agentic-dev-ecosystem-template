import json

import pytest

from common.skill_activity import SkillActivityError, SkillActivityOutput
from edd_refinement_workflow.progress_record import ProgressRecordStore
from edd_refinement_workflow.activities.edd_plan import (
    EddPlanRunner,
    PlanningResult,
    edd_plan_action,
)


class FakeSkillActivity:
    def __init__(self, output=None, error=None):
        self.output = output
        self.error = error
        self.calls = []

    def execute(self, skill_input):
        self.calls.append(skill_input)
        if self.error is not None:
            raise self.error
        return self.output


def _write_plan(path, **overrides):
    plan = {
        "iteration_number": 1,
        "action": "repair",
        "rationale": "fixture defect",
        "intended_files": ["skill/_tests/foo.tests.yaml"],
        "expected_effect": "TC-1 passes",
        "iteration_start_baseline": {
            "source": "baseline",
            "passing": 5,
            "failing": 1,
            "total": 6,
        },
        "requires_approval": False,
        "stop_recommendation": False,
    }
    plan.update(overrides)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plan))
    return plan


def test_edd_plan_stops_without_invoking_skill_when_budget_exhausted() -> None:
    skill = FakeSkillActivity()
    runner = EddPlanRunner(skill)
    progress_record = {
        "budgets": {"remaining_iterations": 0},
        "consecutive_confirmed_regressions": 0,
    }

    result = runner.run("run-1", "/repo", progress_record, {"passing": 5})

    assert isinstance(result, PlanningResult)
    assert result.action == "stop"
    assert result.stop_recommendation is True
    assert skill.calls == []


def test_edd_plan_stops_after_three_consecutive_regressions() -> None:
    skill = FakeSkillActivity()
    runner = EddPlanRunner(skill)
    progress_record = {"budgets": {}, "consecutive_confirmed_regressions": 3}

    result = runner.run("run-1", "/repo", progress_record, {"passing": 5})

    assert result.action == "stop"
    assert skill.calls == []


def test_edd_plan_invokes_edd_plan_skill_and_reads_its_plan_json(tmp_path) -> None:
    plan_path = tmp_path / ".process" / "edd" / "run-1" / "iterations" / "1" / "plan.json"
    plan = _write_plan(plan_path)
    relative_plan_path = str(plan_path.relative_to(tmp_path))
    skill = FakeSkillActivity(
        output=SkillActivityOutput(
            status="success",
            output_path=relative_plan_path,
            sentinel_path=".process/edd/run-1/.process/edd-plan.done.json",
            duration_ms=10,
        )
    )
    runner = EddPlanRunner(skill)
    progress_record = {
        "budgets": {"remaining_iterations": 3},
        "consecutive_confirmed_regressions": 0,
    }

    result = runner.run("run-1", str(tmp_path), progress_record, {"passing": 5})

    assert result.action == plan["action"]
    assert result.intended_files == plan["intended_files"]
    assert result.iteration_number == plan["iteration_number"]
    assert result.iteration_start_baseline == plan["iteration_start_baseline"]
    assert result.plan_path == relative_plan_path
    assert result.requires_approval is False
    assert skill.calls[0].input_paths == [
        ".process/edd/run-1/refinement.yaml",
        ".process/edd/run-1/progress.json",
    ]


def test_edd_plan_persists_iteration_start_baseline_into_progress_json(
    tmp_path,
) -> None:
    plan_path = tmp_path / ".process" / "edd" / "run-1" / "iterations" / "1" / "plan.json"
    plan = _write_plan(plan_path)
    skill = FakeSkillActivity(
        output=SkillActivityOutput(
            status="success",
            output_path=str(plan_path.relative_to(tmp_path)),
            sentinel_path=".process/edd/run-1/.process/edd-plan.done.json",
            duration_ms=10,
        )
    )
    store = ProgressRecordStore(tmp_path)
    progress_record = store.create_or_resume(
        "run-1",
        {"budgets": {"remaining_iterations": 3}, "consecutive_confirmed_regressions": 0},
    )
    runner = EddPlanRunner(skill)

    runner.run("run-1", str(tmp_path), progress_record, {"passing": 5})

    persisted = store.create_or_resume("run-1", {})
    assert persisted["iteration_start_baseline"] == plan["iteration_start_baseline"]


def test_edd_plan_only_requires_approval_for_expectation_change_with_diff_hash(
    tmp_path,
) -> None:
    plan_path = tmp_path / "plan.json"
    _write_plan(
        plan_path,
        action="propose_evaluation_expectation_change",
        requires_approval=True,
    )
    skill = FakeSkillActivity(
        output=SkillActivityOutput(
            status="success",
            output_path="plan.json",
            sentinel_path=".process/edd-plan.done.json",
            duration_ms=5,
        )
    )
    runner = EddPlanRunner(skill)
    progress_record = {
        "budgets": {"remaining_iterations": 3},
        "consecutive_confirmed_regressions": 0,
    }

    without_hash = runner.run(
        "run-1", str(tmp_path), progress_record, {"passing": 5}, proposed_diff_hash=""
    )
    assert without_hash.requires_approval is False
    assert without_hash.proposed_diff_hash is None

    with_hash = runner.run(
        "run-1",
        str(tmp_path),
        progress_record,
        {"passing": 5},
        proposal_id="proposal-1",
        proposed_diff_hash="abc123",
    )
    assert with_hash.requires_approval is True
    assert with_hash.proposal_id == "proposal-1"
    assert with_hash.proposed_diff_hash == "abc123"


def test_edd_plan_raises_on_missing_plan_json(tmp_path) -> None:
    skill = FakeSkillActivity(
        output=SkillActivityOutput(
            status="success",
            output_path="missing/plan.json",
            sentinel_path=".process/edd-plan.done.json",
            duration_ms=1,
        )
    )
    runner = EddPlanRunner(skill)
    progress_record = {
        "budgets": {"remaining_iterations": 3},
        "consecutive_confirmed_regressions": 0,
    }

    with pytest.raises(SkillActivityError, match="did not write"):
        runner.run("run-1", str(tmp_path), progress_record, {"passing": 5})


@pytest.mark.asyncio
async def test_edd_plan_activity_entrypoint_runs_configured_runner(monkeypatch) -> None:
    expected = PlanningResult(action="stop", stop_recommendation=True)

    class FakeRunner:
        def run(self, *args, **kwargs):
            return expected

    monkeypatch.setattr(
        "edd_refinement_workflow.activities.edd_plan.EDD_PLAN_RUNNER", FakeRunner()
    )

    result = await edd_plan_action("run-1", "/repo", {}, {})

    assert result["action"] == "stop"
    assert result["stop_recommendation"] is True
