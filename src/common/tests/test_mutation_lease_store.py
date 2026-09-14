from common.mutation_lease_store import MutationLeaseStore


def test_acquire_lease_makes_is_held_true() -> None:
    store = MutationLeaseStore()
    token = store.acquire(repo_key="repo", run_id="run-1", ttl=60)

    assert token is not None
    assert store.is_held("repo") is True
