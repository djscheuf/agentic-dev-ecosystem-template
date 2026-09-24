from common.mutation_lease_store import MutationLeaseStore


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
