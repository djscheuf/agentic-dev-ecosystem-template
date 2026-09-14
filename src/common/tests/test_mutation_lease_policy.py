from common.mutation_lease_policy import MutationLeasePolicyHandler
from common.mutation_lease_store import MutationLeaseStore


def test_lease_handler_releases_on_success() -> None:
    store = MutationLeaseStore()
    handler = MutationLeasePolicyHandler(store)

    with handler.lease(repo_key="repo", run_id="run-1", ttl=60) as token:
        assert token is not None

    assert store.is_held("repo") is False


def test_lease_handler_emits_acquire_and_release_events() -> None:
    store = MutationLeaseStore()
    events = []
    handler = MutationLeasePolicyHandler(
        store, on_event=lambda name, **data: events.append((name, data))
    )

    with handler.lease(repo_key="repo", run_id="run-1", ttl=60) as token:
        assert token is not None

    assert any(name == "AcquireMutationLease" for name, _ in events)
    assert any(name == "ReleaseMutationLease" for name, _ in events)
