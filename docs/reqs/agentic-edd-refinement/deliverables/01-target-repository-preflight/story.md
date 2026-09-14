# Resolve and Validate the Target Repository

## Story

So that automated refinement never mutates the wrong repository or overwrites unrelated work
As a workflow requester
I want the workflow to resolve exactly one target Git worktree and validate all safety preconditions before refinement begins

## Source Deliverables

- `EDD-001` — Target repository resolution and preflight validation

## Entry Outcome

A workflow request provides a repository anchor or explicit target root, scoped inputs, required test cases, evaluation configuration, and execution limits.

## Scope

### In Scope

- Resolve and record one canonical target Git worktree and starting revision.
- Reconcile anchor-derived and explicitly supplied repository roots.
- Validate every repository-scoped path against the target worktree.
- Require a clean worktree, an existing skill and evaluation suite, deterministic evaluation inputs, one provider, and valid limits.
- Acquire and release a repository-scoped mutation lease.
- Report all failed preconditions without invoking an agent or mutating the worktree.

### Out of Scope

- Initializing progress state or running the baseline evaluation.
- Planning or executing refinement actions.
- Comparing, committing, or reverting candidate changes.

## Acceptance Criteria

- **EDD-001-AC1:** Given a repository anchor path and no explicit target repository root, when preflight runs, then the workflow resolves the nearest containing Git worktree root and records its canonical path and starting revision.
- **EDD-001-AC2:** Given both an anchor-derived root and an explicit root are supplied and they identify different Git worktrees, when preflight runs, then the request is rejected before any agent is invoked.
- **EDD-001-AC3:** Given a scoped input, skill, evaluation, or authorized-scope path resolves outside the target worktree, when preflight validates it, then the request is rejected.
- **EDD-001-AC4:** Given the target worktree has staged, unstaged, or untracked changes, when preflight inspects repository status, then the workflow rejects the request and leaves the worktree unchanged.
- **EDD-001-AC5:** Given another workflow run already holds the mutation lease for the same target repository, when preflight runs, then the workflow rejects or waits according to configured policy without starting refinement.
- **EDD-001-AC6:** Given the target skill does not exist, or exists but has no evaluation suite, in the target repository, when preflight runs, then the workflow rejects the request before refinement begins.
- **EDD-001-AC7:** Given required test cases, a deterministic evaluation command, a single execution provider, and iteration or token limits are all supplied and valid, when preflight runs, then preflight succeeds, acquires the repository mutation lease, and reports no other side effects.
- **EDD-001-AC8:** Given any precondition fails, when preflight completes, then the workflow reports every failed condition and releases any lease it had acquired.

## Dependencies

- Git worktree discovery and repository status inspection.
- Canonical path and authorized-scope validation.
- Repository-scoped mutation lease policy.
- Skill and evaluation-suite discovery in the target repository.

## Exit Outcome

The request is either rejected without side effects and with all failures reported, or it proceeds with one validated, clean, leased target repository and recorded starting revision.
