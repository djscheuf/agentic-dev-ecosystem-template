"""AC-15 / CR-06: external-target proof.

Exercises one full planning + execution iteration against a scratch git
repository that is NOT the orchestration repository, using the real runner
path (EddPlanRunner/EddDoRunner via SkillActivity with a test harness).
Asserts:

- all artifacts resolve inside the target repository;
- the orchestration worktree is untouched;
- `.process/` run artifacts are excludable via `scratch_globs`.
"""

import json
import subprocess
from pathlib import Path

from common.harness import HarnessResult
from common.repository_status import RepositoryStatusInspector
from edd_refinement_workflow.activities.edd_do import EddDoRunner
from edd_refinement_workflow.activities.edd_plan import EddPlanRunner
from edd_refinement_workflow.activities.harness_instance import REPO_ROOT


RUN_ID = "run-ext-1"


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )


def _init_target_repo(tmp_path: Path) -> Path:
    target = tmp_path / "target"
    target.mkdir()
    _git(target, "init")
    (target / "tracked.txt").write_text("v1")
    _git(target, "add", "-A")
    _git(target, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-m", "init")
    return target


def _write_sentinel(path: Path, task: str, plan_path: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"task": task, "verify_params": {"plan_path": plan_path}})
    )


class PlanHarness:
    """Stands in for the agentic edd-plan skill: writes plan.json plus its
    completion sentinel relative to the cwd it is handed."""

    def __init__(self):
        self.calls = []

    def run(self, prompt, *, cwd, config=None):
        cwd = Path(cwd)
        self.calls.append(cwd)
        plan_rel = f".process/edd/{RUN_ID}/iterations/1/plan.json"
        plan_abs = cwd / plan_rel
        plan_abs.parent.mkdir(parents=True, exist_ok=True)
        plan_abs.write_text(
            json.dumps(
                {
                    "iteration_number": 1,
                    "action": "repair",
                    "rationale": "fixture defect",
                    "intended_files": ["tracked.txt"],
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
            )
        )
        _write_sentinel(
            cwd / f".process/edd/{RUN_ID}/.process/edd-plan.done.json",
            "edd-plan",
            plan_rel,
        )
        return HarnessResult(exit_code=0, stdout="", stderr="")


class DoHarness:
    """Stands in for the agentic edd-do skill: mutates a tracked file and
    writes the edd-do sentinel next to the plan, relative to cwd."""

    def __init__(self):
        self.calls = []

    def run(self, prompt, *, cwd, config=None):
        cwd = Path(cwd)
        self.calls.append(cwd)
        (cwd / "tracked.txt").write_text("v2")
        _write_sentinel(
            cwd / f".process/edd/{RUN_ID}/iterations/1/.process/edd-do.done.json",
            "edd-do",
            f".process/edd/{RUN_ID}/iterations/1/plan.json",
        )
        return HarnessResult(exit_code=0, stdout="", stderr="")


def _orchestration_status() -> str:
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "status", "--porcelain", "-uall"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def test_external_target_iteration_leaves_orchestration_tree_unchanged(
    tmp_path,
) -> None:
    target = _init_target_repo(tmp_path)
    (target / ".process" / "edd" / RUN_ID).mkdir(parents=True)
    (target / ".process" / "edd" / RUN_ID / "refinement.yaml").write_text(
        "iterations: []"
    )
    orchestration_before = _orchestration_status()

    # Planning iteration against the external target.
    plan_harness = PlanHarness()
    plan_runner = EddPlanRunner(harness=plan_harness)
    progress_record = {
        "budgets": {"remaining_iterations": 3},
        "consecutive_confirmed_regressions": 0,
        "modification_scope": ["tracked.txt"],
    }
    plan = plan_runner.run(RUN_ID, str(target), progress_record, {"passing": 5})

    # Execution iteration against the same external target.
    do_harness = DoHarness()
    do_runner = EddDoRunner(harness=do_harness)
    execution = do_runner.run(
        RUN_ID,
        {"action": plan.action, "plan_path": plan.plan_path},
        str(target),
    )

    # Every harness invocation ran inside the target, never the orchestration repo.
    assert plan_harness.calls == [target]
    assert do_harness.calls == [target]
    assert target != REPO_ROOT

    # Plan + do artifacts resolved inside the target repository.
    assert (target / plan.plan_path).exists()
    assert (
        target / f".process/edd/{RUN_ID}/.process/edd-plan.done.json"
    ).exists()
    assert (
        target / f".process/edd/{RUN_ID}/iterations/1/.process/edd-do.done.json"
    ).exists()
    assert (target / plan.plan_path).with_name("do.json").exists()
    assert execution.status == "success"
    assert execution.changed_files == ["tracked.txt"]

    # `.process/` artifacts are excludable via scratch_globs: committing the
    # real change leaves a clean tree once scratch paths are ignored.
    _git(target, "add", "tracked.txt")
    _git(
        target, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-m", "candidate"
    )
    inspector = RepositoryStatusInspector()
    status = inspector.inspect(str(target), scratch_globs=[".process/**"])
    assert status.is_clean
    raw = inspector.inspect(str(target))
    assert raw.untracked
    assert all(p.startswith(".process/") for p in raw.untracked)

    # The orchestration worktree is byte-for-byte unchanged by the whole run.
    assert _orchestration_status() == orchestration_before
    assert not (REPO_ROOT / ".process" / "edd" / RUN_ID).exists()
