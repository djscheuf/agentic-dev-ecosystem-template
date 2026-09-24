import pytest

from common.skill_activity import SkillActivityError, SkillActivityOutput
from edd_refinement_workflow.activities.edd_do import EddDoRunner, edd_do_action
from edd_refinement_workflow.candidate_results import ExecutionResult, UsageMetrics


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


class _CompletedProcess:
    def __init__(self, stdout: str) -> None:
        self.stdout = stdout


def test_edd_do_rejects_unapproved_expectation_change() -> None:
    skill = FakeSkillActivity()
    runner = EddDoRunner(skill)
    planning = {
        "action": "propose_evaluation_expectation_change",
        "requires_approval": True,
        "proposed_diff_hash": "abc123",
        "plan_path": ".process/edd/run-1/iterations/1/plan.json",
    }

    with pytest.raises(ValueError, match="missing_approval"):
        runner.run("run-1", planning, None, "/repo")

    assert skill.calls == []


def test_edd_do_rejects_approval_diff_hash_mismatch() -> None:
    skill = FakeSkillActivity()
    runner = EddDoRunner(skill)
    planning = {
        "action": "propose_evaluation_expectation_change",
        "requires_approval": True,
        "proposed_diff_hash": "abc123",
        "plan_path": ".process/edd/run-1/iterations/1/plan.json",
    }

    with pytest.raises(ValueError, match="diff_hash_mismatch"):
        runner.run("run-1", planning, "different", "/repo")

    assert skill.calls == []


def test_edd_do_reports_missing_plan_path() -> None:
    skill = FakeSkillActivity()
    runner = EddDoRunner(skill)

    with pytest.raises(SkillActivityError, match="plan_path"):
        runner.run("run-1", {"action": "repair"}, None, "/repo")


def test_edd_do_invokes_edd_do_skill_and_measures_the_diff(
    monkeypatch, tmp_path
) -> None:
    plan_path = tmp_path / ".process" / "edd" / "run-1" / "iterations" / "1" / "plan.json"
    plan_path.parent.mkdir(parents=True)
    plan_path.write_text("{}")

    skill = FakeSkillActivity(
        output=SkillActivityOutput(
            status="success",
            output_path=str(plan_path),
            sentinel_path=".process/edd/run-1/iterations/1/.process/edd-do.done.json",
            duration_ms=250,
            observation={
                "usage": {
                    "prompt_tokens": 120,
                    "completion_tokens": 30,
                    "cost_usd": 0.02,
                },
                "atif_path": ".process/edd/run-1/devin-trajectory.json",
            },
        )
    )
    runner = EddDoRunner(skill)

    outputs = iter(
        [_CompletedProcess("diff --git a/x b/x\n"), _CompletedProcess("src/skill.py\n")]
    )
    monkeypatch.setattr(
        "edd_refinement_workflow.activities.edd_do.subprocess.run",
        lambda *args, **kwargs: next(outputs),
    )

    result = runner.run(
        "run-1",
        {"action": "repair", "plan_path": str(plan_path)},
        None,
        str(tmp_path),
    )

    assert isinstance(result, ExecutionResult)
    assert result.status == "success"
    assert result.usage_metrics.total_tokens == 150
    assert result.changed_files == ["src/skill.py"]
    assert result.atif_path == ".process/edd/run-1/devin-trajectory.json"
    assert skill.calls[0].input_paths == [str(plan_path)]


def test_edd_do_writes_do_json_next_to_plan(monkeypatch, tmp_path) -> None:
    import json

    plan_path = tmp_path / ".process" / "edd" / "run-1" / "iterations" / "1" / "plan.json"
    plan_path.parent.mkdir(parents=True)
    plan_path.write_text("{}")

    skill = FakeSkillActivity(
        output=SkillActivityOutput(
            status="success",
            output_path=str(plan_path),
            sentinel_path=None,
            duration_ms=250,
            observation={
                "usage": {
                    "prompt_tokens": 120,
                    "completion_tokens": 30,
                    "cost_usd": 0.02,
                },
                "atif_path": None,
            },
        )
    )
    runner = EddDoRunner(skill)

    outputs = iter(
        [_CompletedProcess("diff --git a/x b/x\n"), _CompletedProcess("src/skill.py\n")]
    )
    monkeypatch.setattr(
        "edd_refinement_workflow.activities.edd_do.subprocess.run",
        lambda *args, **kwargs: next(outputs),
    )

    result = runner.run(
        "run-1",
        {"action": "repair", "plan_path": str(plan_path)},
        None,
        str(tmp_path),
    )

    do_path = plan_path.with_name("do.json")
    assert do_path.exists()
    do = json.loads(do_path.read_text())
    assert do["status"] == result.status
    assert do["changed_files"] == ["src/skill.py"]
    assert do["diff_hash"] == result.diff_hash
    assert do["usage_metrics"]["total_tokens"] == 150
    assert do["duration_ms"] == 250


def test_edd_do_reports_harness_failure_as_failed_result(tmp_path) -> None:
    plan_path = tmp_path / ".process" / "edd" / "run-1" / "iterations" / "1" / "plan.json"
    plan_path.parent.mkdir(parents=True)
    plan_path.write_text("{}")

    skill = FakeSkillActivity(error=SkillActivityError("harness_failure:1"))
    runner = EddDoRunner(skill)

    result = runner.run(
        "run-1",
        {"action": "repair", "plan_path": str(plan_path)},
        None,
        str(tmp_path),
    )

    assert result.status == "failed"
    assert result.changed_files == []
    assert result.failure_reason == "harness_failure:1"


@pytest.mark.asyncio
async def test_edd_do_activity_entrypoint_runs_configured_runner(monkeypatch) -> None:
    expected = ExecutionResult(
        status="success",
        usage_metrics=UsageMetrics(1, 1, 2, 0.01),
        changed_files=["src/skill.py"],
        diff_hash="abc123",
        failure_reason=None,
        atif_path=None,
        duration_ms=1,
    )

    class FakeRunner:
        def run(self, *args):
            return expected

    monkeypatch.setattr(
        "edd_refinement_workflow.activities.edd_do.EDD_DO_RUNNER", FakeRunner()
    )

    result = await edd_do_action("run-1", {"action": "repair"}, None, "/repo")

    assert result["diff_hash"] == "abc123"
