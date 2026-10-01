# ADR-023: Persistent, Process-Safe Mutation Lease for EDD

**Status:** Accepted  
**Date:** 2026-09-24  
**Author:** Project Team

## Bottom line

`MutationLeaseStore` is now file-backed by default in production. Leases are persisted under `<repo_root>/.process/mutation-leases.json` with an advisory file lock, so `initialize_run` and `finalize_run` activities running in different worker processes see the same lease state. The EDD workflow also finalizes (and therefore releases the lease) when an unhandled exception escapes the workflow body.

## Context

A second EDD refinement run failed during `initialize_run` with `LeaseConflictError`, even though the preceding run had already published a terminal report and recorded `lease_released: true`. The worker log showed the first run had completed and `FinalizeRunActivity` had executed, but the in-memory lease store inside the activity process still held the repository key.

The root cause was that `MutationLeaseStore` kept leases in a process-local dictionary. If activities run in different OS processes (or even different Python interpreters), the process that acquires the lease is not the process that releases it. The release becomes a no-op in the releasee's memory, and the next `initialize_run` sees a stale lease.

## Decision

1. `MutationLeaseStore` accepts an optional `store_path`. When a path is provided it persists leases as JSON and uses `fcntl.flock` for exclusive, advisory locking across processes.
2. The in-memory mode is retained for unit tests that instantiate `MutationLeaseStore()` directly without a path.
3. `get_default_store()` returns a path-backed store when called with a `store_path`; the old no-argument singleton remains in-memory for backward compatibility.
4. `initialize_run` and `finalize_run` pass `Path(repo_root) / ".process" / "mutation-leases.json"` as the store path, so every activity for the same repository shares one lease file.
5. `EddRefinementWorkflow.run` wraps the workflow body in a `try/except`. If an unhandled exception escapes after `initialize_run` has produced a record and `repo_root`, it calls `finalize_run` with `terminal_reason="workflow_exception"` before re-raising. This ensures the lease is released even when the workflow fails before reaching a normal terminal path.
6. Leases continue to expire automatically via `time.monotonic()` TTL, so a crash that bypasses the finally block still clears after the TTL.

## Consequences

### Positive

- Consecutive EDD runs no longer collide because of stale in-process leases.
- Lease state survives worker restarts; a fresh worker can see that a previous run is still active or has been released.
- Unhandled workflow failures release the mutation lease instead of leaving it held until TTL expiration.

### Negative

- The lease file is a small amount of I/O per acquire/release, but the operations are infrequent and cheap.
- File locking via `fcntl` is Unix-specific; the current NixOS environment is Linux, so this is acceptable for now.

### Neutral / Follow-up

- Consider a SQLite-backed store if cross-platform locking or richer lease metadata is needed later.
- The worker should be restarted after this change so subsequent activities use the new file-backed store.

## Update (2026-09-26): TTL must use wall clock, not `time.monotonic()`

A lease from a terminated run failed to expire and blocked a fresh run minutes later. Root cause: `MutationLeaseStore` computed and compared deadlines with `time.monotonic()`. That clock's reference point is only guaranteed stable *within one process*; this store is explicitly persisted so **different** processes (a restarted worker) can see it. After a worker restart, the new process's `time.monotonic()` baseline can be lower than the deadline persisted by the previous process, so the deadline compares as still in the future indefinitely — the lease never expires until that same process eventually monotonic-catches-up, which may never happen in practice.

Fix: `MutationLeaseStore.acquire`/`_expire` now store and compare a wall-clock `time.time()` dead-by value. `initialize_run`'s `mutation_lease` record now also carries a real `acquired_at` and `dead_by` epoch timestamp instead of the literal string `"now"`, so a held lease's liveness can be read directly from the progress record for the same repo-key scope.

Lesson: never persist a `time.monotonic()` value for a liveness check that crosses process boundaries. Monotonic clocks are for measuring elapsed time within one process only; persisted deadlines need wall clock.

## Update (2026-09-30): renewal + TTL decoupled from eval timeout

Code review found two gaps: (a) the lease TTL was coupled to `eval_timeout_seconds`, so a long evaluation or approval wait could outlive the lease mid-run; (b) there was no way to extend a held lease.

- `MutationLeaseStore` gained `renew(run_id)` — it extends the wall-clock `dead_by` only for the current lease holder, so it cannot resurrect or steal another run's lease.
- A new `renew_mutation_lease` Cadence activity is scheduled once per loop iteration and before approval waits. The lease TTL is now an independent setting owned by the workflow-owned `preflight` activity, not derived from the evaluation timeout.
- `finalize_run` treats lease-release failure as non-fatal: it records `lease_released: false` plus `lease_release_error` in `terminal.json` instead of aborting the terminal report.
- Finalize-on-exit is now guaranteed for *every* terminal branch (not just exceptions) via a central `_finalize` in `EddRefinementWorkflow`; see the 2026-09-30 section of [[services/edd_refinement.md]].
