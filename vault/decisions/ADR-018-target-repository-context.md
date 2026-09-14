# ADR-018: Explicit Target Repository Context for Agentic Workflows

**Status:** Proposed
**Date:** 2026-09-14
**Author:** Project team

## Bottom line

Repository-mutating workflows resolve one target Git worktree during preflight and pass that immutable context to every Activity. Activities must not infer their operational repository from the orchestration source tree or worker process directory.

## Context

Agentic workflows need to manipulate repositories other than the repository that contains the Cadence worker. The current generic `SkillActivity` accepts a repository root and passes it to the harness, but deployed workflow Activities are instantiated with a root derived from their installed source location. Sentinel, output, grading, and reporting paths also use that fixed root.

The Agentic EDD quality ratchet requires a clean target worktree, target-owned skills and evaluations, deterministic Git operations, and consistent repository access across retries and workers. Changing only subprocess `cwd` does not satisfy those requirements.

## Decision

- Introduce a shared, workflow-independent target repository context.
- Resolve the nearest Git worktree root from a repository-anchored input path, with an optional explicit root for inputs without a natural anchor.
- Reject an explicit root that disagrees with the anchor-derived worktree.
- Canonicalize and validate all repository-scoped paths against the target root.
- Record target root, anchor, branch or detached state, starting commit, and clean-worktree evidence during preflight.
- Require no staged, unstaged, or untracked changes before a mutating workflow begins.
- Acquire a repository-scoped mutation lease so concurrent workflows cannot change the same worktree.
- Snapshot the resolved context in workflow state and pass it explicitly to every repository-scoped Activity.
- Run agent, evaluation, file, sentinel, output, and Git operations relative to the target root.
- Discover repository-owned skills and agent configuration from the target repository without silently falling back to the orchestration repository.
- Validate repository identity and accessibility when Activities execute or retry.
- Release the mutation lease on every terminal path.

## Consequences

### Positive

- One orchestration deployment can operate on multiple local repositories without modifying its own checkout.
- All side effects share a traceable repository and starting revision.
- Clean-worktree and lease checks protect unrelated user changes and concurrent runs.
- The capability is reusable by EDD, Story Analysis, Story Design, and future workflows.

### Negative

- Activity contracts must carry repository context instead of relying on process-global roots.
- Workers executing one run must share access to the same checkout or use a future workspace service.
- Path canonicalization, symlinks, worktrees, leases, and retry idempotency add validation complexity.

### Neutral / Follow-up

- The initial capability targets an existing local worktree; cloning and remote workspace provisioning remain out of scope.
- Decide whether clean caller-selected worktrees are sufficient or dedicated workflow worktrees become mandatory.
- Decide where operational artifacts live when the target differs from the orchestration repository.
- Refactor current Activity singletons and fixed `REPO_ROOT` consumers before implementing the EDD ratchet.

## Alternatives Considered

- **Run only against the orchestration checkout** — rejected because workflows must operate on independently maintained target repositories.
- **Change only the agent subprocess working directory** — rejected because sentinel, output, grading, reporting, and Git paths would remain bound to the wrong root.
- **Trust an arbitrary caller-supplied root without Git discovery** — rejected because anchor-derived validation gives a deterministic repository boundary and catches mismatched paths.
- **Allow dirty worktrees** — rejected because the ratchet could commit, revert, or misattribute unrelated changes.
