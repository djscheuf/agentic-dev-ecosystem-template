import json
import subprocess
from pathlib import Path

import pytest

from common.harness import HarnessResult
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


def test_edd_do_runs_expectation_change_without_approved_diff_hash(monkeypatch, tmp_path) -> None:
    plan_path = tmp_path / ".process" / "edd" / "run-1" / "iterations" / "1" / "plan.json"
    plan_path.parent.mkdir(parents=True)
    plan_path.write_text("{}")

    skill = FakeSkillActivity(
        output=SkillActivityOutput(
            status="success",
            output_path=str(plan_path),
            sentinel_path=".process/edd/run-1/iterations/1/.process/edd-do.done.json",
            duration_ms=10,
        )
    )
    runner = EddDoRunner(skill)

    outputs = iter(
        [_CompletedProcess("diff --git a/rubric.md b/rubric.md\n"), _CompletedProcess("rubric.md\n")]
    )
    monkeypatch.setattr(
        "edd_refinement_workflow.activities.edd_do.subprocess.run",
        lambda *args, **kwargs: next(outputs),
    )

    planning = {
        "action": "propose_evaluation_expectation_change",
        "requires_approval": True,
        "plan_path": str(plan_path),
    }
    result = runner.run("run-1", planning, str(tmp_path))

    assert result.status == "success"
    assert result.changed_files == ["rubric.md"]
    assert result.diff_hash is not None


def test_edd_do_reports_missing_plan_path() -> None:
    skill = FakeSkillActivity()
    runner = EddDoRunner(skill)

    with pytest.raises(SkillActivityError, match="plan_path"):
        runner.run("run-1", {"action": "repair"}, "/repo")


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


def test_edd_do_roots_harness_sentinel_and_diff_in_target_repository(tmp_path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    subprocess.run(["git", "init"], cwd=target, check=True, capture_output=True)
    (target / "tracked.txt").write_text("v1")
    subprocess.run(["git", "-C", str(target), "add", "-A"], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(target), "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-m", "init"],
        check=True,
        capture_output=True,
    )

    plan_rel = ".process/edd/run-1/iterations/1/plan.json"
    plan_abs = target / plan_rel
    plan_abs.parent.mkdir(parents=True)
    plan_abs.write_text("{}")

    harness_calls = []

    class DoHarness:
        def run(self, prompt, *, cwd, config=None):
            cwd = Path(cwd)
            harness_calls.append(cwd)
            (cwd / "tracked.txt").write_text("v2")
            sentinel = (
                cwd
                / ".process/edd/run-1/iterations/1/.process/edd-do.done.json"
            )
            sentinel.parent.mkdir(parents=True, exist_ok=True)
            sentinel.write_text(
                json.dumps(
                    {"task": "edd-do", "verify_params": {"plan_path": plan_rel}}
                )
            )
            return HarnessResult(exit_code=0, stdout="", stderr="")

    runner = EddDoRunner(harness=DoHarness())
    result = runner.run(
        "run-1",
        {"action": "repair", "plan_path": plan_rel},
        str(target),
    )

    from edd_refinement_workflow.activities.harness_instance import REPO_ROOT

    assert harness_calls == [target]
    assert harness_calls[0] != REPO_ROOT
    assert (
        target / ".process/edd/run-1/iterations/1/.process/edd-do.done.json"
    ).exists()
    assert result.status == "success"
    assert result.changed_files == ["tracked.txt"]
    assert plan_abs.with_name("do.json").exists()


def test_edd_do_reports_harness_failure_as_failed_result(tmp_path) -> None:
    plan_path = tmp_path / ".process" / "edd" / "run-1" / "iterations" / "1" / "plan.json"
    plan_path.parent.mkdir(parents=True)
    plan_path.write_text("{}")

    skill = FakeSkillActivity(error=SkillActivityError("harness_failure:1"))
    runner = EddDoRunner(skill)

    result = runner.run(
        "run-1",
        {"action": "repair", "plan_path": str(plan_path)},
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

    result = await edd_do_action("run-1", {"action": "repair"}, "/repo")

    assert result["diff_hash"] == "abc123"
