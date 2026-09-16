import dataclasses
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any, Optional

from common.repository_status import RepositoryStatusInspector
from common.scoped_path_validator import ScopedPathValidator, TargetScopeError
from common.skill_and_evaluation_discovery import SkillAndEvaluationDiscovery
from common.target_repository import TargetRepositoryResolutionError, TargetWorktreeResolver


@dataclasses.dataclass
class TargetRepositoryContext:
    repo_root: Path
    anchor_path: str
    explicit_root: Optional[str]
    branch: str
    starting_revision: str


@dataclasses.dataclass
class PreflightResult:
    status: str
    target_context: Optional[TargetRepositoryContext] = None
    provider: Optional[str] = None
    failed_conditions: list[str] = dataclasses.field(default_factory=list)


def resolve_and_validate_target_repository(
    anchor_path: str,
    explicit_root: Optional[str] = None,
    scoped_paths: Optional[list[str]] = None,
    skill_name: str = "",
    evaluation_path: str = "",
    additional_paths: Optional[list[str]] = None,
    run_id: str = "",
    lease_ttl: int = 60,
    scratch_globs: Optional[list[str]] = None,
    on_event: Optional[Callable[..., None]] = None,
) -> PreflightResult:
    def _emit(name: str, **data: Any) -> None:
        if on_event is not None:
            on_event(name, **data)

    resolver = TargetWorktreeResolver()
    try:
        repo_root = resolver.resolve(anchor_path, explicit_root)
    except TargetRepositoryResolutionError as exc:
        _emit("ResolveTargetRepository", resolved=False, error=str(exc))
        _emit("CompletePreflight", outcome="failure")
        return PreflightResult(status="failure", failed_conditions=[str(exc)])

    _emit("ResolveTargetRepository", resolved=True, repo_root=str(repo_root))

    failed_conditions: list[str] = []

    inspector = RepositoryStatusInspector()
    status = inspector.inspect(str(repo_root), scratch_globs=scratch_globs)
    _emit(
        "CheckRepositoryStatus",
        repo_root=str(repo_root),
        is_clean=status.is_clean,
        staged=status.staged,
        modified=status.modified,
        untracked=status.untracked,
    )
    if not status.is_clean:
        failed_conditions.append("target worktree has unexpected changes")

    if scoped_paths:
        validator = ScopedPathValidator()
        for path in scoped_paths:
            try:
                validator.validate(str((repo_root / path).resolve()), str(repo_root))
                _emit("ValidateScopedPaths", path=path, valid=True)
            except TargetScopeError as exc:
                _emit("ValidateScopedPaths", path=path, valid=False, error=str(exc))
                failed_conditions.append(str(exc))

    discovery = SkillAndEvaluationDiscovery()
    skill_result = discovery.discover(skill_name, evaluation_path, str(repo_root))
    if not skill_result.ok:
        failed_conditions.append("target skill or evaluation suite missing")

    input_validator = ScopedPathValidator()
    if skill_result.ok and skill_result.skill_path is not None:
        try:
            input_validator.validate(str(skill_result.skill_path), str(repo_root))
            _emit("ValidateInputPaths", path=str(skill_result.skill_path), valid=True)
        except TargetScopeError as exc:
            _emit("ValidateInputPaths", path=str(skill_result.skill_path), valid=False, error=str(exc))
            failed_conditions.append(str(exc))
    if skill_result.ok and skill_result.evaluation_path is not None:
        try:
            input_validator.validate(str(skill_result.evaluation_path), str(repo_root))
            _emit("ValidateInputPaths", path=str(skill_result.evaluation_path), valid=True)
        except TargetScopeError as exc:
            _emit("ValidateInputPaths", path=str(skill_result.evaluation_path), valid=False, error=str(exc))
            failed_conditions.append(str(exc))

    for path in (additional_paths or []):
        try:
            input_validator.validate(str((repo_root / path).resolve()), str(repo_root))
            _emit("ValidateInputPaths", path=path, valid=True)
        except TargetScopeError as exc:
            _emit("ValidateInputPaths", path=path, valid=False, error=str(exc))
            failed_conditions.append(str(exc))

    if failed_conditions:
        _emit(
            "CompletePreflight",
            outcome="failure",
            repo_root=str(repo_root),
            failed_conditions=failed_conditions,
        )
        return PreflightResult(
            status="failure", failed_conditions=failed_conditions
        )

    branch = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    rev = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    _emit(
        "CompletePreflight",
        outcome="success",
        repo_root=str(repo_root),
        branch=branch.stdout.strip(),
        starting_revision=rev.stdout.strip(),
    )
    return PreflightResult(
        status="success",
        target_context=TargetRepositoryContext(
            repo_root=repo_root,
            anchor_path=anchor_path,
            explicit_root=explicit_root,
            branch=branch.stdout.strip(),
            starting_revision=rev.stdout.strip(),
        ),
        provider=skill_result.provider,
    )
