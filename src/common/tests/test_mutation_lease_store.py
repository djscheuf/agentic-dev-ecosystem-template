from common.mutation_lease_store import MutationLeaseStore
import common.mutation_lease_store as mutation_lease_store


def test_acquire_lease_makes_is_held_true() -> None:
    store = MutationLeaseStore()
    token = store.acquire(repo_key="repo", run_id="run-1", ttl=60)

    assert token is not None
    assert store.is_held("repo") is True


def test_acquire_conflicting_run_returns_none() -> None:
    store = MutationLeaseStore()
    store.acquire(repo_key="repo", run_id="run-1", ttl=60)
    conflict = store.acquire(repo_key="repo", run_id="run-2", ttl=60)

    assert conflict is None
    assert store.is_held("repo") is True


def test_release_lease_makes_is_held_false() -> None:
    store = MutationLeaseStore()
    store.acquire(repo_key="repo", run_id="run-1", ttl=60)
    store.release(repo_key="repo", run_id="run-1")

    assert store.is_held("repo") is False


def test_expired_lease_is_not_held() -> None:
    store = MutationLeaseStore()
    store.acquire(repo_key="repo", run_id="run-1", ttl=0)

    assert store.is_held("repo") is False


def test_file_backed_store_shares_leases_across_instances(tmp_path) -> None:
    path = tmp_path / "leases.json"
    store1 = MutationLeaseStore(path)
    token = store1.acquire(repo_key="repo", run_id="run-1", ttl=60)
    assert token is not None

    store2 = MutationLeaseStore(path)
    assert store2.is_held("repo") is True
    assert store2.acquire(repo_key="repo", run_id="run-2", ttl=60) is None
    assert store2.release(repo_key="repo", run_id="run-1") is True
    assert store1.is_held("repo") is False


def test_file_backed_store_expires_stale_leases(tmp_path) -> None:
    path = tmp_path / "leases.json"
    store = MutationLeaseStore(path)
    store.acquire(repo_key="repo", run_id="run-1", ttl=0)

    assert store.is_held("repo") is False


def test_lease_survives_differing_monotonic_baselines_across_store_instances(
    tmp_path, monkeypatch
) -> None:
    # Simulates a worker process restart: the second store instance's
    # time.monotonic() has a completely different (lower) reference point
    # than the first process that acquired the lease. Liveness must still
    # be correctly recognized because it is a persisted, cross-process
    # store -- so it must not depend on monotonic clock continuity.
    path = tmp_path / "leases.json"

    monkeypatch.setattr(mutation_lease_store.time, "monotonic", lambda: 100_000.0)
    store1 = MutationLeaseStore(path)
    token = store1.acquire(repo_key="repo", run_id="run-1", ttl=60)
    assert token is not None

    monkeypatch.setattr(mutation_lease_store.time, "monotonic", lambda: 5.0)
    store2 = MutationLeaseStore(path)
    assert store2.is_held("repo") is True


def test_lease_expires_based_on_wall_clock_after_ttl_across_process_restart(
    tmp_path, monkeypatch
) -> None:
    path = tmp_path / "leases.json"

    monkeypatch.setattr(mutation_lease_store.time, "monotonic", lambda: 100_000.0)
    monkeypatch.setattr(mutation_lease_store.time, "time", lambda: 1_000.0)
    store1 = MutationLeaseStore(path)
    store1.acquire(repo_key="repo", run_id="run-1", ttl=60)

    # A restarted process: monotonic baseline resets, but wall clock keeps
    # advancing normally past the lease's ttl.
    monkeypatch.setattr(mutation_lease_store.time, "monotonic", lambda: 5.0)
    monkeypatch.setattr(mutation_lease_store.time, "time", lambda: 1_061.0)
    store2 = MutationLeaseStore(path)
    assert store2.is_held("repo") is False
