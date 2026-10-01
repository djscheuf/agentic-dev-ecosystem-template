import pytest
import yaml

from edd_refinement_workflow.progress_record import ProgressRecordStore
from edd_refinement_workflow.refinement_log import append_refinement_outcome


def _write_refinement(repo_root, run_id="run-1", iterations=None):
    path = repo_root / ".process" / "edd" / run_id / "refinement.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    document = {
        "schema_version": 1,
        "run_id": run_id,
        "iterations": iterations if iterations is not None else [{"iteration": 1}],
    }
    path.write_text(yaml.safe_dump(document, sort_keys=False))
    return path


def _read(path):
    return yaml.safe_load(path.read_text())


def test_append_refinement_outcome_adds_to_current_iteration_section(tmp_path) -> None:
    path = _write_refinement(
        tmp_path,
        iterations=[{"iteration": 1, "outcomes": [{"event": "planned"}]}, {"iteration": 2}],
    )

    append_refinement_outcome(tmp_path, "run-1", {"event": "accepted", "commit": "abc"})

    document = _read(path)
    assert document["iterations"][0]["outcomes"] == [{"event": "planned"}]
    assert document["iterations"][1]["outcomes"] == [{"event": "accepted", "commit": "abc"}]


def test_append_refinement_outcome_is_noop_without_context_document(tmp_path) -> None:
    append_refinement_outcome(tmp_path, "run-1", {"event": "accepted"})

    assert not (tmp_path / ".process" / "edd" / "run-1" / "refinement.yaml").exists()


@pytest.mark.asyncio
async def test_record_confirmed_regression_appends_outcome_to_refinement_yaml(tmp_path) -> None:
    from edd_refinement_workflow.activities.regression_recovery import (
        record_confirmed_regression_activity,
    )

    path = _write_refinement(tmp_path)
    ProgressRecordStore(tmp_path).create_or_resume("run-1", {})

    result = await record_confirmed_regression_activity(
        "run-1", "candidate-1", {"passing": 4}, {"passing": 4}, 3, str(tmp_path)
    )

    assert result["consecutive_confirmed_regressions"] == 1
    outcomes = _read(path)["iterations"][0]["outcomes"]
    assert outcomes == [
        {
            "event": "regression_confirmed",
            "candidate_id": "candidate-1",
            "consecutive_confirmed_regressions": 1,
        }
    ]


@pytest.mark.asyncio
async def test_commit_accepted_candidate_appends_outcome_to_refinement_yaml(
    tmp_path, monkeypatch
) -> None:
    from edd_refinement_workflow.activities.commit_accepted_candidate import (
        commit_accepted_candidate_activity,
    )

    path = _write_refinement(tmp_path)
    ProgressRecordStore(tmp_path).create_or_resume("run-1", {})
    monkeypatch.setattr(
        "edd_refinement_workflow.activities.commit_accepted_candidate._commit_repository",
        lambda root, message: "commit-1",
    )

    result = await commit_accepted_candidate_activity(
        "run-1", {"candidate_id": "candidate-1", "passing": 6}, str(tmp_path)
    )

    assert result["commit"] == "commit-1"
    outcomes = _read(path)["iterations"][0]["outcomes"]
    assert outcomes == [
        {"event": "accepted", "candidate_id": "candidate-1", "commit": "commit-1"}
    ]


@pytest.mark.asyncio
async def test_record_reverted_proposal_appends_outcome_to_refinement_yaml(tmp_path) -> None:
    from edd_refinement_workflow.activities.regression_recovery import (
        record_reverted_proposal_context_activity,
    )

    path = _write_refinement(tmp_path)
    ProgressRecordStore(tmp_path).create_or_resume("run-1", {})

    await record_reverted_proposal_context_activity(
        "run-1",
        {
            "candidate_id": "candidate-1",
            "recovery_result": {"recovered": True},
        },
        str(tmp_path),
    )

    outcomes = _read(path)["iterations"][0]["outcomes"]
    assert outcomes == [
        {"event": "reverted", "candidate_id": "candidate-1", "recovered": True}
    ]


@pytest.mark.asyncio
async def test_human_handoff_appends_outcome_to_refinement_yaml(tmp_path) -> None:
    from edd_refinement_workflow.activities.regression_recovery import (
        human_handoff_activity,
    )

    path = _write_refinement(tmp_path)
    ProgressRecordStore(tmp_path).create_or_resume("run-1", {})

    await human_handoff_activity(
        "run-1", "unstable_result", {"confirmation": {}}, str(tmp_path)
    )

    outcomes = _read(path)["iterations"][0]["outcomes"]
    assert outcomes == [{"event": "human_handoff", "reason": "unstable_result"}]


@pytest.mark.asyncio
async def test_edd_plan_activity_appends_atif_observation_to_refinement_yaml(
    tmp_path, monkeypatch
) -> None:
    from edd_refinement_workflow.activities.edd_plan import (
        PlanningResult,
        edd_plan_action,
    )

    path = _write_refinement(tmp_path)
    observation = {
        "workflow_id": "wf-1",
        "run_id": "run-1",
        "activity_id": "act-1",
        "atif_path": ".process/edd/run-1/devin-trajectory.json",
        "usage": {"prompt_tokens": 100, "completion_tokens": 20},
    }
    monkeypatch.setattr(
        "edd_refinement_workflow.activities.edd_plan.EDD_PLAN_RUNNER",
        type(
            "FakeRunner",
            (),
            {"run": lambda self, *a, **k: PlanningResult(action="repair", observation=observation)},
        )(),
    )

    await edd_plan_action("run-1", str(tmp_path), {}, {})

    outcomes = _read(path)["iterations"][0]["outcomes"]
    assert outcomes == [{"event": "agentic_activity_trail", "step": "edd_plan", **observation}]


@pytest.mark.asyncio
async def test_edd_plan_activity_does_not_append_when_skill_was_not_invoked(
    tmp_path, monkeypatch
) -> None:
    from edd_refinement_workflow.activities.edd_plan import (
        PlanningResult,
        edd_plan_action,
    )

    path = _write_refinement(tmp_path)
    monkeypatch.setattr(
        "edd_refinement_workflow.activities.edd_plan.EDD_PLAN_RUNNER",
        type(
            "FakeRunner",
            (),
            {"run": lambda self, *a, **k: PlanningResult(action="stop", stop_recommendation=True)},
        )(),
    )

    await edd_plan_action("run-1", str(tmp_path), {}, {})

    assert _read(path)["iterations"][0].get("outcomes") is None


@pytest.mark.asyncio
async def test_edd_do_activity_appends_atif_observation_to_refinement_yaml(
    tmp_path, monkeypatch
) -> None:
    from edd_refinement_workflow.activities.edd_do import edd_do_action
    from edd_refinement_workflow.candidate_results import ExecutionResult, UsageMetrics

    path = _write_refinement(tmp_path)
    observation = {
        "workflow_id": "wf-1",
        "run_id": "run-1",
        "activity_id": "act-2",
        "atif_path": ".process/edd/run-1/devin-trajectory.json",
        "usage": {"prompt_tokens": 50, "completion_tokens": 10},
    }
    expected = ExecutionResult(
        status="success",
        usage_metrics=UsageMetrics(50, 10, 60, 0.0),
        changed_files=["src/skill.py"],
        diff_hash="abc123",
        failure_reason=None,
        atif_path=observation["atif_path"],
        duration_ms=1,
        observation=observation,
    )
    monkeypatch.setattr(
        "edd_refinement_workflow.activities.edd_do.EDD_DO_RUNNER",
        type("FakeRunner", (), {"run": lambda self, *a: expected})(),
    )

    await edd_do_action("run-1", {"action": "repair"}, str(tmp_path))

    outcomes = _read(path)["iterations"][0]["outcomes"]
    assert outcomes == [{"event": "agentic_activity_trail", "step": "edd_do", **observation}]


@pytest.mark.asyncio
async def test_edd_do_activity_does_not_append_on_harness_failure(tmp_path, monkeypatch) -> None:
    from edd_refinement_workflow.activities.edd_do import edd_do_action
    from edd_refinement_workflow.candidate_results import ExecutionResult, UsageMetrics

    path = _write_refinement(tmp_path)
    failed = ExecutionResult(
        status="failed",
        usage_metrics=UsageMetrics(0, 0, 0, 0.0),
        changed_files=[],
        diff_hash="",
        failure_reason="harness_failure:1",
        atif_path=None,
        duration_ms=0,
        observation=None,
    )
    monkeypatch.setattr(
        "edd_refinement_workflow.activities.edd_do.EDD_DO_RUNNER",
        type("FakeRunner", (), {"run": lambda self, *a: failed})(),
    )

    await edd_do_action("run-1", {"action": "repair"}, str(tmp_path))

    assert _read(path)["iterations"][0].get("outcomes") is None
